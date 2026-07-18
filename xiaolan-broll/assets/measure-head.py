#!/usr/bin/env python
"""Measure the talking-head cutout's head-top y across beats so captions can be
placed a known distance above it. Cream background is detected as "blank".

Usage:  python measure-head.py <opener.mp4> [t0 t1 t2 ...]
Default samples 7 times across the clip. Prints head-top y (px) and % of 1920.
Requires: PIL (pillow) + ffmpeg on PATH. (faster-whisper env already has PIL.)
"""
import sys, os, subprocess, tempfile
from PIL import Image

def is_cream(p):
    r, g, b = p
    return r > 225 and g > 218 and b > 200 and abs(r - g) < 28

def head_top(img):
    W, H = img.size
    # scan center columns for the first clearly non-cream row from y=380 down
    for y in range(380, H, 4):
        cnt = sum(0 if is_cream(img.getpixel((x, y))) else 1
                  for x in range(int(W*0.33), int(W*0.67), 6))
        if cnt > 10:
            return y, H
    return None, H

def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    src = sys.argv[1]
    times = [float(t) for t in sys.argv[2:]] or [0.4, 1.3, 2.3, 3.3, 4.4, 5.3, 6.4]
    tops = []
    with tempfile.TemporaryDirectory() as d:
        for t in times:
            f = os.path.join(d, f"f_{t}.png")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(t),
                            "-i", src, "-frames:v", "1", f], check=True)
            y, H = head_top(Image.open(f).convert("RGB"))
            tops.append(y)
            print(f"t={t:>4}s  head_top y{y}  ({round(y/H*100)}%)" if y else f"t={t}s none")
    valid = [y for y in tops if y]
    if valid:
        hi = min(valid)  # highest head across beats = the safe ceiling for text
        print(f"\nSAFE head ceiling (min across beats): y{hi} ({round(hi/1920*100)}%)")
        print(f"To leave 10% (192px) gap: caption band BOTTOM should be y{hi-192}.")

if __name__ == "__main__":
    main()
