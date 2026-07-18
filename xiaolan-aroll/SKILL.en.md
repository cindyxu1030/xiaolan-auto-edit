---
name: xiaolan-aroll
description: >-
  Auto-edit a Xiaolan (小蓝)-style talking-head A-ROLL recording: remove silences/pauses,
  cut the flubbed takes the presenter marks with a spoken "卡 / cut" cue, and drop repeated
  retakes (keeping the cleaner one), then RENDER the edited video back — A/V in sync. Input
  is the unedited A-roll VIDEO (audio is the detection signal) plus a reference SCRIPT
  (ground truth for which take to keep and to fix whisper homophones). Output is a tightened
  rough-cut VIDEO to refine in CapCut. Runs FULL AUTO (applies all cuts) but always emits
  a keep/cut EDL log to scan. Use whenever the user wants: "edit my a-roll", "cut my talking
  head", "remove the pauses and retakes", "clean up my recording", "去掉停顿和重复/废话",
  "口播剪辑", "cut where I said 卡", "give me the edited video". This is the FRONT half of the
  content pipeline — it cleans the talking head; `xiaolan-broll` then dresses it with b-roll
  + karaoke. NOT for b-roll/captions (use `xiaolan-broll`), NOT for a hook opener
  (use `xiaolan-hook-broll`, not included in this repo).
---

# xiaolan-aroll

Take the **unedited A-roll video** + the matching **reference script**, and return a **tightened
edited video**: pauses removed, the takes killed with a spoken **「卡 / cut」** cue
dropped, and repeated retakes collapsed to the cleanest take. Full auto, but you leave a
reviewable cut log. This is the front half of the pipeline that feeds `xiaolan-broll`.

## How Xiaolan records — adopt the same convention when you record
- The presenter talks straight through, **unedited**. On a flubbed line the presenter says a
  standalone **「卡」**(kǎ) or **「cut」**, pauses, and **redoes the line**. So a cue means:
  *the take just before me is bad; the take just after me is the keeper.*
- The presenter **repeats sentences** even without a 卡 — same line twice (often slightly
  reworded). Keep the later/cleaner one, drop the earlier.
- Every recording comes with a **matching script** = what the final should say. It is GROUND
  TRUTH: when two takes compete, keep the one closest to the script; and use the script to fix
  words whisper mis-hears so you never cut on a mishearing.

## Read first
1. `references/cut-logic.md` — the exact detection + decision algorithm, the cue rules, the
   pause/repeat handling, the ffmpeg render (select/aselect, A/V sync), and every gotcha.
2. Your own decision log — the gotchas already hit on past runs (strongly recommended: build
   a mistake-book file for your AI employee).
3. Sibling skill: `xiaolan-broll` (b-roll + karaoke overlay) consumes the video this produces.

## The non-negotiables
- **Edit the VIDEO, keep A/V in sync.** Input video in → edited video out. Cuts found in the
  audio apply to video+audio on the SAME timestamps. Never desync.
- **Never change the presenter's words or voice.** Only remove: silences, 卡-flubbed takes,
  repeated takes. NO filler-word stripping (嗯/呃/那个), NO pitch/speed/denoise — that's the
  presenter's voice.
- **The script is ground truth — for correctness, not for cutting.** Use it to fix whisper
  homophones and to verify every script line survives exactly once. Detect a repeat by HIGH
  MUTUAL similarity between two takes — NEVER by "they map to the same script line" (consecutive
  segments of one long sentence share a line but are NOT repeats). On a genuine repeat, keep the
  LATER/cleaner take (your "keep the second version" rule).
- **「卡 / 咔 / cut」 is a cue ONLY when standalone** (a short utterance between pauses).
  「卡」inside a real word (卡片, 卡顿, 卡住) is CONTENT — never cut it. Flag ambiguous ones.
- **When unsure, KEEP and flag.** Full auto means render without a gate — but if a 卡 has no
  clear retake nearby, or a "repeat" is low-confidence, keep the content and list it in the
  EDL `REVIEW` section rather than risk deleting a real line.
- **Self-verify before delivering.** Read the EDL against the script (did total runtime / line
  count come out right?), then spot-check the actual splice points in the rendered video.

## Workflow
1. **Inspect** the input (`ffprobe`): confirm it's the A-roll video, get duration + fps +
   that it has an audio track. Note variable-frame-rate (force CFR on output if so).
2. **Extract audio** for analysis: `ffmpeg -i <in> -ac 1 -ar 16000 -vn audio.wav`.
3. **Transcribe** word-level: `python assets/transcribe.py audio.wav transcript`
   (faster-whisper medium, zh, word_timestamps, int8 CPU, `PYTHONIOENCODING=utf-8`).
4. **Get the script** (a `.txt`/paste). Save as `script.txt`. If the user didn't send
   one, ask for it (or fall back to "keep the later take" — note the downgrade).
5. **Find cuts**: `python assets/find-cuts.py --transcript transcript.json --media <in>
   --script script.txt --audio audio.wav --out edl.json --report edl.md`. This detects 卡
   cues, resolves flubs/repeats against the script, and removes pauses **silence-first and
   two-tier** (2026-07-05): pauses are FOUND on the RMS envelope of `--audio` (whisper word
   timings stretch into silence, so word-gaps undercount pauses badly — see cut-logic.md §5);
   whisper words only define the kept takes and protect onsets. Mid-sentence pauses >
   `--min-pause` (0.15 s) collapse to a `--beat` (0.10 s) residual; sentence-boundary pauses
   (segment ends 。！？!?…) > `--boundary-pause` (0.25 s) collapse to `--boundary-beat`
   (0.20 s). **Always pass `--audio`** — without it the trim falls back to word-gaps and
   misses most real pauses. The report lists every pause cut (gap → residual).
6. **Verify the EDL (mandatory even in full-auto).** Read `edl.md`: scan every CUT reason and
   the `REVIEW` section. Cross-check against the script — every script line should survive
   exactly once. Hand-edit `edl.json` `keep[]` if the heuristic mis-cut a real line.
7. **Render** the edited video: `python assets/apply-cuts.py --media <in> --edl edl.json
   --out <name>-edit.mp4`. (select/aselect on identical ranges → synced; re-encodes CFR.)
8. **Spot-check** the render: probe duration (matches EDL sum), and eyeball/listen at 3-4
   splice points — clean cuts, no clipped syllables, lips match audio.
9. **Deliver** the edited video **beside the source** as `<source-stem>-edit.mp4` — no "ask
   where" gate (Xiaolan's standing rule, 2026-06-26: stop asking, default beside source; only ask
   if the source location is genuinely ambiguous). Keep the project in
   `<your-workspace>/<name>-aroll/`. Never overwrite the user's source.
10. **Log** what you learned to your own decision log (build a mistake-book file for your AI
    employee).

## The gotchas that bite (full list in cut-logic.md)
- **卡 homophones are content** (卡片/卡顿/卡住). Only a standalone, pause-bounded 卡/咔/cut is a cue.
- **Whisper mishears → use the script.** Two takes that look different may be the same line
  (and vice-versa). Normalize + compare against script lines, not raw whisper text.
- **Two-tier pause rule (Xiaolan, 2026-07-05):** mid-sentence pauses > 0.15s collapse to a
  ~0.10s beat; sentence-boundary pauses > 0.25s collapse to ~0.20s. Pauses are measured on
  the AUDIO (RMS quiet runs), not on whisper word-gaps — whisper stretches word timings
  across silence (a real 1.10s pause once measured as a 0.22s word-gap) so word-gaps miss
  most pauses. Claimed word onsets inside a quiet run are trusted only if there's real
  energy after them. Don't butt-splice to zero.
- **VFR input desyncs select-cutting** — force constant fps (`-r <fps>`) on output.
- **select/aselect must use IDENTICAL ranges** for video and audio, or A/V drifts.
- **Don't drop a real line.** If runtime collapses way more than the script implies, you
  over-cut — re-check the REVIEW items and similarity threshold.
- **For a frame-precise splice near a retake, re-transcribe the WINDOW with VAD off.** The main
  pass (`vad_filter=True`) DROPS short connectors (就想/呢/吧) and COLLAPSES stutters (我我→我).
  When you finalize a cut boundary, re-transcribe just that 4–6 s window with
  `vad_filter=False, condition_on_previous_text=False` to recover the real word timings, then
  set the `keep[]` boundary on those. Xiaolan expects in-take stutters de-duped and dropped
  connectors kept — not only flubs/repeats removed.
- **Rhetorical echo ≠ repeat.** Xiaolan's scripts echo a statement as a rhetorical question
  (它替我回答 → 问题来了，它怎么能替我回答呢) and the repeat test WILL cut the statement. Check
  every [repeat] cut against the script: if both takes map to different script sentences that
  both exist in the script, RESTORE the cut.
- **咳/咳咳 can end a flubbed take instead of 卡.** Grep the keeps for pure-cough segments as
  take-seam tells and hand-cut those clusters like 卡 flubs.
- **Finish hand-cut runs with `--silence-only` on the render** (temp → verify → replace): the
  hand-cut joins otherwise keep 0.4–0.6 s beats over the two-tier bar. Replace the deliverable
  only after duration / silencedetect-zero / join-onset / char-diff (0 deletions) all pass.

## Assets
- `assets/transcribe.py` — faster-whisper → word-level JSON (words nested in segments + flat).
- `assets/find-cuts.py` — silence map + 卡-cue + repeat/retake resolution (script-aligned) → keep/cut EDL.
- `assets/apply-cuts.py` — render the edited video (or audio) from the EDL, A/V synced, CFR.
