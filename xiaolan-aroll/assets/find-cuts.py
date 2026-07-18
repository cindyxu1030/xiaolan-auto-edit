#!/usr/bin/env python
# find-cuts.py — detect pauses, 卡/cut cues, and repeated takes; emit a keep/cut EDL.
#
# Usage:
#   python find-cuts.py --transcript transcript.json --media input.mp4 \
#       --script script.txt --out edl.json --report edl.md
#
# Output edl.json: {duration, fps_hint, keep:[[s,e]...], cuts:[{s,e,reason,text}...],
#                   review:[...], stats:{...}}
import os, sys, re, json, argparse, subprocess
from difflib import SequenceMatcher
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass

CUE_TOKENS = ["卡", "咔", "咔嚓", "卡卡", "cut", "カット", "card", "咖"]
# "card": zh-whisper consistently mis-hears the spoken cut cue as the English word
# "card" (seen 2026-06-19). Safe because units = whole whisper segments, so only a
# standalone-segment "card" between pauses fires; "或者card" / "card片" never do.
# "咖": zh-whisper also mis-hears the spoken cue (kǎ) as 咖 (kā, coffee char) — seen
# 2026-07-01. Same guarantee: a bare "咖" segment is never real content (咖啡/咖喱 come
# out as multi-char segments), so only a standalone cue fires.

PUNCT = r"[\s,.;:!?，。、；：！？…“”\"'‘’（）()\[\]【】\-—~·]+"

def norm(s):
    return re.sub(PUNCT, "", (s or "").lower())

def ratio(a, b):
    a, b = norm(a), norm(b)
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()

CUE_SET = {norm(t) for t in CUE_TOKENS}
def is_cue_text(t):
    return norm(t) in CUE_SET

def raw_text(unit):
    return "".join(w["word"] for w in unit["words"])

def time_at_char(unit, ci):
    t = unit["words"][0]["start"] if unit["words"] else unit["start"]
    idx = 0
    for w in unit["words"]:
        if idx <= ci:
            t = w["start"]
        else:
            break
        idx += len(w["word"])
    return t

def longest_repeat_block(pre, post, minsize=3):
    rp, rq = raw_text(pre), raw_text(post)
    blocks = [b for b in SequenceMatcher(None, rp, rq).get_matching_blocks() if b.size >= minsize]
    if not blocks:
        return None
    blk = max(blocks, key=lambda b: (b.size, -b.a))   # longest; tie -> earliest in pre
    return blk.a, rp[:blk.a]                           # (cut-from char index in pre, prefix before it)

def run_silencedetect(media, noise, dmin):
    cmd = ["ffmpeg", "-hide_banner", "-i", media,
           "-af", f"silencedetect=noise={noise}:d={dmin}", "-f", "null", "-"]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    sils, cur = [], None
    for line in p.stderr.splitlines():
        m = re.search(r"silence_start:\s*(-?[\d.]+)", line)
        if m:
            cur = max(0.0, float(m.group(1))); continue
        m = re.search(r"silence_end:\s*([\d.]+)", line)
        if m and cur is not None:
            e = float(m.group(1))
            if e > cur:
                sils.append((cur, e))
            cur = None
    return sils

GUARD_TAIL, GUARD_HEAD = 0.02, 0.04   # never cut closer than this to a word edge

def prep_audio(path, hop_s=0.010):
    """RMS envelope (10 ms frames) + quiet threshold, for amplitude-verified pause cuts.
    Threshold = max(2.5x the noise floor, 10% of speech level): silence and soft breaths
    are cuttable, anything remotely voiced is not."""
    import wave
    import numpy as np
    wf = wave.open(path, "rb")
    if wf.getsampwidth() != 2:
        raise ValueError("need 16-bit PCM wav")
    sr, nch = wf.getframerate(), wf.getnchannels()
    data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    wf.close()
    if nch > 1:
        data = data.reshape(-1, nch).mean(axis=1)
    hop = max(1, int(sr * hop_s))
    n = len(data) // hop
    if n < 10:
        raise ValueError("audio too short")
    rms = np.sqrt((data[:n * hop].reshape(n, hop) ** 2).mean(axis=1))
    nz = rms[rms > 1e-6]
    if not len(nz):
        raise ValueError("silent file")
    floor, speech = float(np.percentile(nz, 5)), float(np.percentile(nz, 90))
    return rms, hop / sr, max(floor * 2.5, speech * 0.10)

def place_cut(e0, s1, amount, rms, hop_s, quiet_th):
    """Timing-only fallback (no --audio): pick the interval to remove inside the
    word-gap [e0, s1] so `amount` seconds go away, residual biased 40/60 toward
    protecting the next word's onset. The amplitude path lives in the quiet_runs pass."""
    if amount < 0.03:
        return None
    if (s1 - GUARD_HEAD) - (e0 + GUARD_TAIL) < 0.03:
        return None
    res = (s1 - e0) - amount
    return (e0 + 0.4 * res, s1 - 0.6 * res)

def quiet_runs(rms, hop_s, th, min_len):
    """Contiguous sub-threshold runs of the RMS envelope, at least min_len long."""
    out, n, k = [], len(rms), 0
    while k < n:
        if rms[k] <= th:
            j = k
            while j < n and rms[j] <= th:
                j += 1
            if (j - k) * hop_s >= min_len:
                out.append((k * hop_s, j * hop_s))
            k = j
        else:
            k += 1
    return out

def load_script(path):
    if not path or not os.path.exists(path):
        return []
    txt = open(path, encoding="utf-8").read()
    parts = re.split(r"[。！？\n!?]+", txt)
    return [p.strip() for p in parts if norm(p)]

def build_units(segments, pause_break=0.6, cue_gap=0.20):
    # Units = whisper SEGMENTS (clean sentence-level takes; whisper already isolates a
    # standalone 卡 as its own segment, and won't make 卡片 a whole segment). Each unit keeps
    # its words for surgical char->time mapping.
    units = []
    for s in segments:
        text = (s.get("text") or "").strip()
        units.append({"words": s.get("words") or [], "text": text,
                      "start": float(s["start"]), "end": float(s["end"]),
                      "is_cue": is_cue_text(text)})
    return units

def best_script(text, script):
    best = (-1, 0.0)
    for i, s in enumerate(script):
        r = ratio(text, s)
        if r > best[1]:
            best = (i, r)
    return best

def subtract(span, cores):
    s, e = span
    out = [(s, e)]
    for ca, cb in cores:
        nxt = []
        for a, b in out:
            if cb <= a or ca >= b:
                nxt.append((a, b))
            else:
                if a < ca: nxt.append((a, ca))
                if cb < b: nxt.append((cb, b))
        out = nxt
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--transcript", required=True)
    ap.add_argument("--media", required=True)
    ap.add_argument("--script", default="")
    ap.add_argument("--out", default="edl.json")
    ap.add_argument("--report", default="edl.md")
    ap.add_argument("--noise", default="-30dB")   # (unused since the word-gap silence trim; kept for compat)
    ap.add_argument("--min-pause", type=float, default=0.15,
                    help="INTRA-SENTENCE trigger: cut any mid-sentence word-gap longer "
                         "than this (seconds). Default 0.15.")
    ap.add_argument("--beat", "--target-gap", dest="beat", type=float, default=0.10,
                    help="residual pause left after an intra-sentence cut. Default 0.10.")
    ap.add_argument("--boundary-pause", type=float, default=0.25,
                    help="SENTENCE-BOUNDARY trigger (left segment ends 。！？!?…). Default 0.25.")
    ap.add_argument("--boundary-beat", type=float, default=0.20,
                    help="residual pause left after a sentence-boundary cut. Default 0.20.")
    ap.add_argument("--audio", default="",
                    help="16k mono wav of the media (the transcribe input). When given, cut "
                         "intervals are amplitude-verified: only measurably quiet audio is "
                         "removed, so speech whisper missed can never be cut.")
    ap.add_argument("--pad", type=float, default=0.10)
    ap.add_argument("--pause-break", type=float, default=0.6)
    ap.add_argument("--cue-gap", type=float, default=0.20)
    ap.add_argument("--sim", type=float, default=0.55)
    ap.add_argument("--silence-only", action="store_true",
                    help="ONLY trim silences > --min-pause; skip all cue/flub/repeat "
                         "detection. Use to re-tighten an ALREADY-cut edit without "
                         "re-judging takes (avoids false repeats from re-segmentation).")
    a = ap.parse_args()

    data = json.load(open(a.transcript, encoding="utf-8"))
    dur = float(data.get("duration") or 0.0)
    script = load_script(a.script)
    units = build_units(data["segments"], a.pause_break, a.cue_gap)
    n = len(units)
    keep = [not u.get("is_cue") for u in units]
    reason = ["cue (卡/cut marker)" if u.get("is_cue") else "" for u in units]
    review = []
    extra_cuts = []   # surgical (partial-unit) cuts: {s,e,reason,text}

    # --silence-only: skip ALL take-judging (cue/flub/repeat) — keep every content unit
    # (standalone 卡 still dropped) and let only the word-gap pause trim run. Re-running
    # repeat detection on an already-cut edit FALSE-POSITIVES (whisper re-segments, so two
    # distinct-but-similar adjacent lines like "一个有我和小机器人" / "一个只有我自己…没有机器人"
    # look like a repeat and a real line gets deleted). Pause-tightening must not re-judge takes.
    if not a.silence_only:
        for u in units:
            u["sidx"], u["sr"] = (best_script(u["text"], script) if not u.get("is_cue") else (-2, 0.0))

        def nn(i, step):
            j = i + step
            while 0 <= j < n and units[j].get("is_cue"):
                j += step
            return j if 0 <= j < n else -1

        def same_line(x, y, th):
            # A real retake/repeat = the two takes SAY nearly the same words (high mutual
            # similarity). Do NOT use shared script-line index — consecutive segments that are
            # different PARTS of one long script sentence share a line but are not repeats.
            return ratio(units[x]["text"], units[y]["text"]) >= th

        # --- cue-driven retakes: cut the flub before each standalone 卡 ---
        # Surgical: if the pre-unit starts with a script-backed setup clause and only its TAIL
        # repeats the redo, cut just that repeated tail (+ the 卡), keeping the setup.
        for i, u in enumerate(units):
            if not u.get("is_cue"):
                continue
            pre, post = nn(i, -1), nn(i, +1)
            if pre < 0 or post < 0:
                review.append(f"卡 @ {u['start']:.2f}s — at clip edge (only the cue removed)")
                continue
            if not (keep[pre] and same_line(pre, post, min(a.sim, 0.40))):
                review.append(f"卡 @ {u['start']:.2f}s — no clear retake nearby (kept both sides)")
                continue
            blk = longest_repeat_block(units[pre], units[post])
            if blk is not None and len(norm(blk[1])) >= 4 and best_script(blk[1], script)[1] >= 0.55:
                tstart = time_at_char(units[pre], blk[0])
                extra_cuts.append({"s": round(tstart, 3), "e": round(u["end"], 3),
                                   "reason": "flub before 卡 (surgical: kept the setup, dropped the repeated start)",
                                   "text": raw_text(units[pre])[blk[0]:][:42]})
            else:
                keep[pre] = False
                reason[pre] = "flub before 卡 (kept the redo)"

        # --- general repeats among remaining kept non-cue units ---
        prev = None
        for i in range(n):
            if units[i].get("is_cue") or not keep[i]:
                continue
            if prev is not None and same_line(prev, i, a.sim):
                # genuine repeat (no 卡) — keep the LATER/cleaner take (小蓝的规矩)
                keep[prev] = False
                reason[prev] = "repeat (kept the later/cleaner take)"
                prev = i
            else:
                prev = i

    # --- compose keep-list: TWO-TIER word-safe pause trim (2026-07-05) ---
    # Keep units are WHISPER WORDS, not amplitude (faint speech whisper transcribed is
    # never clipped — its onset IS a word, so there's no gap to cut). Trigger and
    # residual are per gap CLASS:
    #   intra-sentence   (same segment, or next segment when the left one doesn't end a
    #                     sentence): gaps > --min-pause collapse to a --beat residual.
    #   sentence boundary (left segment ends 。！？!?…): gaps > --boundary-pause collapse
    #                     to a --boundary-beat residual (keeps her sentence rhythm).
    # The residual is DECOUPLED from --pad (which only pads the clip edges now): cut
    # edges are placed INSIDE the gap by place_cut(), amplitude-verified when --audio is
    # given — only measurably quiet audio is removed, so a soft word whisper missed
    # entirely still survives (strictly safer than the old blind 2*pad butt-splice).
    SENT_END = re.compile(r"[。！？!?…]\s*$")
    ends_sentence = [bool(SENT_END.search(u["text"] or "")) for u in units]

    rms, hop_s, quiet_th = None, 0.010, 0.0
    if a.audio:
        try:
            rms, hop_s, quiet_th = prep_audio(a.audio)
        except Exception as ex:
            print(f"WARN: --audio unusable ({ex}); timing-only cut placement", file=sys.stderr)

    toks = []                                   # (start, end, unit-idx) of every KEPT word
    for i, u in enumerate(units):
        if not keep[i]:
            continue
        ws = u.get("words") or []
        if ws:
            for w in ws:
                toks.append((float(w["start"]), float(w["end"]), i))
        else:                                   # segment had no word timings -> whole-unit token
            toks.append((float(u["start"]), float(u["end"]), i))
    toks.sort()

    pause_cuts = []                             # {s,e,gap,kind} for the report
    qcuts = []                                  # amplitude-found pause cut intervals
    merged = []                                 # keep spans (ordered, disjoint)
    if toks and rms is not None:
        # SILENCE-FIRST pause pass. Whisper word ENDS overshoot far into silence (measured
        # 2026-07-05 on 32529: a 1.10s real pause showed as a 0.22s word-gap), so word-gaps
        # UNDERCOUNT pauses badly. Pauses are therefore FOUND on the RMS envelope; whisper
        # words only (a) define the kept takes and (b) protect the next word's onset.
        # Base spans: one span per stretch of kept words, split only where dropped
        # material (flub/cue/repeat) sits between them.
        dropped = [(units[i]["start"], units[i]["end"]) for i in range(n) if not keep[i]]
        cur_s = max(0.0, toks[0][0] - a.pad)
        cur_e = toks[0][1]
        for s1, e1, u1 in toks[1:]:
            if (s1 - a.pad > cur_e + a.pad and
                    any(ds < s1 and de > cur_e for ds, de in dropped)):
                merged.append([cur_s, min(dur, cur_e + a.pad)])
                cur_s = s1 - a.pad
            cur_e = max(cur_e, e1)
        merged.append([cur_s, min(dur, cur_e + a.pad)])

        import bisect

        def has_energy(t0, t1):
            i0 = max(0, int(t0 / hop_s))
            i1 = min(len(rms), int(t1 / hop_s) + 1)
            return any(v > quiet_th for v in rms[i0:i1])

        tok_starts = [t[0] for t in toks]
        for qs, qe in quiet_runs(rms, hop_s, quiet_th,
                                 min(a.min_pause, a.boundary_pause)):
            k = bisect.bisect_right(tok_starts, qs) - 1
            lu = toks[k][2] if k >= 0 else -1
            k = bisect.bisect_left(tok_starts, qe - 0.05)
            ru = toks[k][2] if k < len(toks) else -1
            boundary = (lu != ru) and (0 <= lu) and ends_sentence[lu]
            trig = a.boundary_pause if boundary else a.min_pause
            beat = a.boundary_beat if boundary else a.beat
            run = qe - qs
            if run <= trig:
                continue
            # Onset to protect = the next word start we can TRUST. Whisper stretches tail
            # words INTO the pause and times next-segment onsets EARLY into it, so a
            # claimed start inside the run only counts if there is real energy just after
            # it (window clamped inside the run, so the previous word's decay can't fake
            # it). A start timed into dead silence is a timing artifact, not speech.
            k = bisect.bisect_left(tok_starts, qs + 0.01)
            nxt = None
            while k < len(tok_starts):
                p = tok_starts[k]
                w0 = max(p, qs + 0.01)
                if p >= qe or has_energy(w0, w0 + 0.12):
                    nxt = p
                    break
                k += 1
            cs = qs + GUARD_TAIL
            ce_max = qe if nxt is None else min(qe, nxt - GUARD_HEAD)
            cut_len = min(run - beat, ce_max - cs)
            if cut_len < 0.03:
                continue
            qcuts.append({"s": round(cs, 3), "e": round(cs + cut_len, 3),
                          "gap": round(run, 2),
                          "kind": "boundary" if boundary else "intra"})
        pause_cuts = qcuts
    elif toks:
        # No usable audio: fall back to word-gap detection (undercounts pauses when
        # whisper word-ends overshoot — pass --audio whenever possible).
        cur_s = max(0.0, toks[0][0] - a.pad)
        cur_e, cur_u = toks[0][1], toks[0][2]
        for s1, e1, u1 in toks[1:]:
            gap = s1 - cur_e
            boundary = (u1 != cur_u) and ends_sentence[cur_u]
            trig = a.boundary_pause if boundary else a.min_pause
            beat = a.boundary_beat if boundary else a.beat
            if gap > trig:
                cut = place_cut(cur_e, s1, gap - beat, None, hop_s, quiet_th)
                if cut:
                    cs, ce = cut
                    merged.append([cur_s, cs])
                    cur_s = ce
                    pause_cuts.append({"s": round(cs, 3), "e": round(ce, 3),
                                       "gap": round(gap, 2),
                                       "kind": "boundary" if boundary else "intra"})
            if e1 > cur_e:
                cur_e, cur_u = e1, u1
        merged.append([cur_s, min(dur, cur_e + a.pad)])

    final = []
    for s, e in merged:
        cores = []
        for ec in extra_cuts + qcuts:           # surgical flub cuts + amplitude pause cuts
            lo, hi = max(s, ec["s"]), min(e, ec["e"])
            if hi - lo > 0.02:
                cores.append((lo, hi))
        for seg in subtract((s, e), cores):
            if seg[1] - seg[0] > 0.05:
                final.append([round(seg[0], 3), round(seg[1], 3)])

    cuts = [{"s": round(units[i]["start"], 3), "e": round(units[i]["end"], 3),
             "reason": reason[i], "text": units[i]["text"][:60]}
            for i in range(n) if not keep[i]]
    cuts += extra_cuts
    cuts.sort(key=lambda c: c["s"])
    kept_dur = sum(e - s for s, e in final)
    stats = {"in_dur": round(dur, 2), "out_dur": round(kept_dur, 2),
             "removed": round(dur - kept_dur, 2),
             "n_cues": sum(1 for u in units if u.get("is_cue")),
             "n_flubs": sum(1 for r in reason if r.startswith("flub")) + len(extra_cuts),
             "n_repeats": sum(1 for r in reason if r.startswith("repeat")),
             "n_pause_cuts": len(pause_cuts),
             "n_pause_boundary": sum(1 for p in pause_cuts if p["kind"] == "boundary"),
             "pause_removed": round(sum(p["e"] - p["s"] for p in pause_cuts), 2),
             "amplitude_verified": rms is not None,
             "n_keep_segments": len(final), "has_script": bool(script)}

    json.dump({"duration": round(dur, 3), "keep": final, "cuts": cuts,
               "review": review, "stats": stats},
              open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    with open(a.report, "w", encoding="utf-8") as f:
        f.write(f"# A-roll cut EDL\n\n")
        f.write(f"- in: **{stats['in_dur']}s** → out: **{stats['out_dur']}s** "
                f"(removed {stats['removed']}s)\n")
        f.write(f"- cues: {stats['n_cues']} · flubs cut: {stats['n_flubs']} · "
                f"repeats cut: {stats['n_repeats']} · keep-segments: {stats['n_keep_segments']} · "
                f"script: {'yes' if stats['has_script'] else 'NO (kept later takes)'}\n")
        f.write(f"- pauses cut: {stats['n_pause_cuts']} "
                f"({stats['n_pause_boundary']} at sentence boundaries) "
                f"= {stats['pause_removed']}s removed · "
                f"cut placement: {'amplitude-verified' if stats['amplitude_verified'] else 'timing-only'}\n\n")
        if pause_cuts:
            f.write("## Pause cuts (gap -> residual)\n")
            for p in pause_cuts:
                res = round(p["gap"] - (p["e"] - p["s"]), 2)
                f.write(f"- `{p['s']:7.2f}` {p['kind']:8s} {p['gap']:.2f}s -> {res:.2f}s\n")
            f.write("\n")
        if review:
            f.write("## REVIEW (kept — confirm these)\n")
            for r in review:
                f.write(f"- {r}\n")
            f.write("\n")
        if extra_cuts:
            f.write("## Surgical (partial-unit) cuts\n")
            for ec in extra_cuts:
                f.write(f"- `{ec['s']:.2f}-{ec['e']:.2f}` {ec['reason']}  ·  \"{ec['text']}\"\n")
            f.write("\n")
        f.write("## Timeline (all units in order)\n\n")
        for i, u in enumerate(units):
            mark = "KEEP" if keep[i] else "CUT "
            part = "  [partial cut inside]" if (keep[i] and any(
                u["start"] - 0.2 <= ec["s"] <= u["end"] + 0.2 for ec in extra_cuts)) else ""
            why = "" if keep[i] else f"  <- {reason[i]}"
            f.write(f"`{u['start']:7.2f}-{u['end']:7.2f}` [{mark}] {u['text'][:48]}{why}{part}\n")
    print(f"DONE: {stats['in_dur']}s -> {stats['out_dur']}s, "
          f"{stats['n_flubs']} flubs + {stats['n_repeats']} repeats cut, "
          f"{len(review)} to review. Wrote {a.out} + {a.report}")

if __name__ == "__main__":
    main()
