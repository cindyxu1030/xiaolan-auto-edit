# Cut logic — how /xiaolan-aroll decides what to remove

The job: turn an unedited talking-head recording into a tight cut by removing three things,
in priority order of *certainty*:

1. **Silences / pauses** — always safe to tighten.
2. **卡-flubbed takes** — a standalone spoken 「卡 / 咔 / cut」 marks the take before it as bad.
3. **Repeated retakes** — the same line said twice (with or without a 卡); keep the cleaner one.

The **reference script is ground truth**. Everything below uses it to (a) fix whisper
homophones before comparing, and (b) pick which competing take to keep (closest to script).

---

## 1. Pipeline data flow

```
input.mp4 ──ffmpeg──> audio.wav (16k mono)
audio.wav ──transcribe.py──> transcript.json   {duration, segments[{start,end,text,words[]}], words[]}
transcript WORD-GAPS + script.txt ──find-cuts.py──> edl.json {keep[], cuts[], stats, review[]} + edl.md
input.mp4 + edl.json ──apply-cuts.py──> <name>-edit.mp4      (select/aselect, CFR, synced)
```

## 2. Units (takes)

`find-cuts.py` uses the **whisper SEGMENTS as units** (one per `transcript.segments[]`), each
keeping its `words` for char→time mapping. Why segments and NOT a word-gap re-segmentation
(an earlier design that backfired on a real recording, 2026-06-16):
- Whisper already isolates a standalone **卡** as its own segment (so the cue is found for
  free), and never makes `卡片` a whole segment (so the homophone is safe).
- Whisper keeps a sentence that has an internal hesitation pause as ONE segment (e.g.
  "我每次……发视频…赠品…拿走"), whereas re-splitting on a `> 0.6 s` gap shattered the redo into
  fragments ("我每次" | "发视频…") and then mis-cut the fragment as a "repeat". Segments avoid that.

A unit is a **cue** iff its whole normalized text ∈ `CUE_TOKENS`. Each non-cue unit also carries
its best-matching **script sentence index** (`sidx`) + **similarity** (`sr`) — used for the
surgical prefix test, NOT for repeat detection (see §4). `difflib.SequenceMatcher` on
punctuation-stripped character sequences (works for Chinese).

## 3. The 卡 cue

A unit is a cue when its whole text is a cue token `{卡, 咔, 咔嚓, cut, カット}` (configurable
`CUE_TOKENS`). Because units are whole whisper segments, `卡片 / 卡顿 / 卡住` (卡 fused into a
longer word) are never a cue unit — the homophone is safe by construction.

**Cue-driven retake resolution** (Xiaolan's main mechanism — "compare before and after the 卡"):
- `pre` = nearest non-cue unit *before* the cue; `post` = nearest non-cue unit *after*.
- If `pre` and `post` are the **same line** — mutual similarity ≥ `min(--sim, 0.40)` (the cue is
  strong evidence, so the bar is relaxed) — then drop the flub:
  - **Surgical** (in-segment flub): if only the TAIL of `pre` repeats `post` and the head before
    it is a script-backed clause (`len(prefix)≥4` and `best_script(prefix).sr ≥ 0.55`), cut just
    `[start-of-repeated-tail … cue.end]` and KEEP the setup head. (Handles "setup + false start"
    glued in one segment.)
  - **Whole-unit** otherwise: cut `[pre.start … cue.end]`.
- If they are NOT clearly the same line: cut only the cue word, **keep both** pre and post, add
  to `review[]`. Never silently delete a real line on an ambiguous cue.
- **Limitation:** if the false start is its OWN tiny segment ("用") rather than glued to the
  setup, `pre` is just that fragment and won't match `post` → it lands in `review[]`; finish it
  by hand-editing `edl.json` (trim the prior keep span to end at the setup). This happened once
  on 2026-06-16 and was a one-line `keep[]` fix.

## 4. Repeated retakes (no cue)

After cue handling, walk the remaining kept non-cue units in time order. For each adjacent pair
`(prev, cur)` with **high MUTUAL similarity** `ratio(prev, cur) ≥ --sim` (default 0.55), cut the
**earlier** one (`prev`) — keep the later/cleaner take (Xiaolan's rule "keep the second version").
Chains of 3+ resolve pairwise, so only the last take of a line survives.

**Critical guard — similarity, NOT shared script line.** An earlier version treated "same
`sidx`" as a repeat; that catastrophically over-cut, because one long script sentence is often
SPOKEN as several segments (e.g. script "但长文……我高中……配图……" delivered as 3 segments). Those
are consecutive PARTS of one line, not repeats — they share `sidx` but have low mutual
similarity. Repeat detection therefore uses mutual `ratio` ONLY. (Script `sidx`/`sr` is still
used for the §3 surgical prefix check.)

## 5. Pause trimming — SILENCE-FIRST + TWO-TIER (Xiaolan, 2026-07-05)

**Why silence-first (the 2026-07-05 lesson):** whisper word TIMINGS lie around pauses — tail
words stretch far into the silence and next-segment onsets get timed early into it. Measured
on 32529: a real 1.10 s pause showed up as a 0.22 s word-gap ("力" claimed 14.52→15.24 while
actual speech ended at 14.51). So word-gap-based trimming (the 2026-06-27 design) UNDERCUT
pauses badly — most real pauses were invisible to it. Pauses are now FOUND on the audio:
`prep_audio()` builds a 10 ms RMS envelope of `--audio` (the same 16 k wav fed to whisper) and
`quiet_runs()` finds sub-threshold runs, `quiet_th = max(2.5×noise-floor, 10 % of speech RMS)`
(≈ −45 dBFS on a typical recording — silence + soft breaths are cuttable, anything voiced is
not).

**Two tiers.** Each quiet run is classified by the unit (whisper segment) it follows:
- **intra-sentence** (same unit, or the left unit doesn't end a sentence): runs > `--min-pause`
  (0.15) collapse to a `--beat` (0.10 s) residual. Xiaolan's rule: the presenter should never
  pause mid-sentence — the flow stays intact.
- **sentence boundary** (left unit ends 。！？!?…): runs > `--boundary-pause` (0.25) collapse
  to `--boundary-beat` (0.20 s) — keeps the sentence rhythm breathing.

**Word-safety now lives in the ONSET TRUST rule.** Whisper words still define the kept takes,
and the cut interval must end before the next word's onset. But a claimed word start INSIDE a
quiet run is only trusted if there is real energy just after it (checked in a window clamped
inside the run, so the previous word's decay can't fake it). A start timed into dead silence
is a timing artifact and is skipped. The residual beat always sits BEFORE the true onset
(cut starts at run-start + 0.02), so onsets keep breathing room. The 2026-06-26 关注/如果
protection carries over: speech whisper transcribed has energy at its true onset, which ends
the quiet run — the run never covers audible speech. Only a held onset quieter than
~10 % of speech RMS could be nibbled; if a redo onset reads clipped, re-transcribe that
window VAD-off (§7 finalize step) — same fix as before.

**No `--audio` → fallback:** word-gap trimming (two-tier, `place_cut()`), which undercounts
pauses for the reason above. Always pass `--audio`. `--noise`/`silencedetect` core-removal
stays retired; `--noise` is accepted-but-ignored.

**Re-tightening an existing edit:** `--silence-only --audio audio.wav` on the already-cut
video re-transcribes cleanly and applies ONLY the pause pass (no take re-judging). This is how
32529-edit.mp4 went 133.3 s → 110.0 s with zero silences ≥ 0.3 s remaining.

Tuning cheatsheet:
- Want tighter mid-sentence flow → lower `--beat` (0.06–0.08); looser → raise it (0.15).
- Sentence breaks feel rushed → raise `--boundary-beat` (0.25–0.30).
- Small hesitations surviving → lower `--min-pause` (0.12); cutting real micro-gaps → raise it.
- Soft speech getting nibbled → raise the quiet threshold guard (`prep_audio`) or fix that
  splice by hand in `edl.json`.
- Over-cutting real lines (repeats) → raise `--sim` (0.7) and check `review[]`.

## 6. Rendering the cut (apply-cuts.py)

Uses one **select/aselect** pass so video and audio cut on identical ranges (stays synced):

```
[0:v]select='between(t,S1,E1)+between(t,S2,E2)+...',setpts=N/FRAME_RATE/TB[v];
[0:a]aselect='between(t,S1,E1)+between(t,S2,E2)+...',asetpts=N/SR/TB[a]
```

- The filter is written to a **filter-script file** and passed via `-filter_complex_script`
  so a long keep-list never blows the Windows command-line length limit.
- Output is **re-encoded CFR**: `-r <fps> -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p
  -c:a aac -b:a 192k`. CFR (`-r`) is required — VFR input + frame-select drifts A/V.
- `--audio-only` renders just the cleaned `.wav`/`.m4a` (uses `aselect` only) for a fast listen.
- select-based jump cuts don't crossfade; tiny clicks are possible at audio splices but are
  fine for a rough cut (refined later in CapCut). For a click-free result, switch to the
  per-segment `atrim + afade(6ms) + concat` method (heavier filter, same ranges).

## 7. Gotchas (don't repeat)

- **卡 homophones** (卡片/卡顿/卡住/卡路里) are content — the standalone + pause-bounded test is
  what protects them. If whisper glued a real 卡-word into a one-word segment, the gap test
  still saves it (no surrounding silence).
- **Whisper vs script:** decide repeats on text *normalized and compared to the script*, not
  raw whisper output. A mis-heard word can make one take look unlike its retake (→ missed cut)
  or make two different lines look alike (→ wrong cut). The script breaks both ties.
- **Don't strip fillers or denoise** — out of scope, changes the presenter's voice. Only remove
  pause/flub/repeat.
- **A/V sync:** identical ranges for `select` and `aselect`; always force CFR `-r` on output;
  if source is VFR, that's mandatory.
- **Keep padding + don't over-tighten:** a fully butt-spliced cut with zero pad clips plosives
  and reads as robotic. Default pad 0.10 s, min-pause 0.25 s (cut silence > 0.25 s → ~0.20 s
  beat) is a natural-sounding start.
- **Never delete on doubt:** an ambiguous 卡 or a low-similarity "repeat" goes to `review[]`
  and is KEPT. Over-keeping is recoverable in CapCut; over-cutting loses a take forever.
- **Verify against the script:** after find-cuts, every script line should appear once in the
  surviving transcript. If a line vanished, the heuristic over-cut — fix `edl.json` by hand.
- **Rhetorical echo is NOT a repeat (2026-07-09, first real false positive):** Xiaolan's scripts
  echo a statement as a rhetorical question ("……它替我回答。问题来了，它怎么能替我回答呢？"). Mutual
  ratio cleared `--sim` and the auto pass cut the statement, deleting a real script line. Verify
  EVERY [repeat] cut against the script: if the cut text and the kept text align to two
  DIFFERENT script sentences that BOTH exist in the script, restore the cut.
- **Throat-clears (咳/咳咳) can terminate a flubbed take instead of 卡 (2026-07-09):** no cue
  fires, and multi-segment takes evade the adjacent-pair walk. Anomaly-scan tell: a KEEP segment
  that is PURE 咳/咳咳 marks a take seam — grep for it alongside the cue tokens, and hand-cut the
  cough seam with its flub cluster. A sub-threshold (−35dB) stray syllable absorbed by the
  silence trim afterwards is acceptable.
- **After hand cuts, finish with `--silence-only` on the render (temp file → verify → replace):**
  conservative mid-silence subtract edges leave 0.4–0.6 s beats at the hand-cut joins, over the
  §5 boundary bar even when the structure is correct. The silence-only pass normalizes every
  join; replace the deliverable only after duration (= keep-sum ±0.2s), silencedetect (zero
  ≥0.3s), join-onset, and char-diff (0 deletions) checks all pass.
