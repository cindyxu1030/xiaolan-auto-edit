#!/usr/bin/env python
# apply-cuts.py — render the edited media from a keep-list EDL (A/V synced, CFR).
#
# Usage:
#   python apply-cuts.py --media input.mp4 --edl edl.json --out name-edit.mp4
#   python apply-cuts.py --media input.mp4 --edl edl.json --out name-edit.m4a --audio-only
import os, sys, json, argparse, subprocess
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass

def probe_fps(media):
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=r_frame_rate", "-of", "default=nk=1:nw=1", media],
            capture_output=True, text=True).stdout.strip()
        num, den = out.split("/") if "/" in out else (out, "1")
        fps = float(num) / float(den or 1)
        return fps if fps > 0 else 30.0
    except Exception:
        return 30.0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--media", required=True)
    ap.add_argument("--edl", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--audio-only", action="store_true")
    ap.add_argument("--crf", default="18")
    ap.add_argument("--fps", type=float, default=0.0)
    a = ap.parse_args()

    edl = json.load(open(a.edl, encoding="utf-8"))
    keep = edl["keep"]
    if not keep:
        print("ERROR: empty keep-list", file=sys.stderr); sys.exit(1)

    expr = "+".join(f"between(t,{s:.3f},{e:.3f})" for s, e in keep)
    fps = a.fps or probe_fps(a.media)

    filt = os.path.splitext(a.out)[0] + ".filter.txt"
    if a.audio_only:
        with open(filt, "w", encoding="utf-8") as f:
            f.write(f"[0:a]aselect='{expr}',asetpts=N/SR/TB[a]")
        cmd = ["ffmpeg", "-hide_banner", "-y", "-i", a.media,
               "-filter_complex_script", filt, "-map", "[a]",
               "-c:a", "aac", "-b:a", "192k", a.out]
    else:
        with open(filt, "w", encoding="utf-8") as f:
            f.write(f"[0:v]select='{expr}',setpts=N/FRAME_RATE/TB[v];"
                    f"[0:a]aselect='{expr}',asetpts=N/SR/TB[a]")
        cmd = ["ffmpeg", "-hide_banner", "-y", "-i", a.media,
               "-filter_complex_script", filt, "-map", "[v]", "-map", "[a]",
               "-r", f"{fps:.5f}", "-c:v", "libx264", "-crf", str(a.crf),
               "-preset", "medium", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "192k", a.out]

    kept = sum(e - s for s, e in keep)
    print(f"rendering {len(keep)} segments -> {kept:.1f}s @ {fps:.2f}fps ...", flush=True)
    r = subprocess.run(cmd)
    if r.returncode == 0:
        print(f"DONE -> {a.out}")
    else:
        print(f"ffmpeg failed (code {r.returncode}); filter at {filt}", file=sys.stderr)
        sys.exit(r.returncode)

if __name__ == "__main__":
    main()
