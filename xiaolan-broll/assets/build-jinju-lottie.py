# -*- coding: utf-8 -*-
"""Build a trace-fill-snap 金句 Lottie from glyphs.json (see glyph2lottie.py).

Usage:
  python glyph2lottie.py "<金句 text>" <workdir>          # -> <workdir>/glyphs.json
  python build-jinju-lottie.py <workdir>/glyphs.json <out.json> \
      --text 先不要碰 --active 碰 --start 0 --dur 2.8

Choreography (30fps, 84 frames from --start):
  per glyph, staggered 7f in reading order:
    trace: Klein stroke (w26) trim 0->100 (entrance-sharp anchor)
    fill:  ink floods FAST (4f, no grey mud stage), trace stroke fades out
  --active glyph: fills KLEIN and punches at ~f50 (scale overshoot, settle-back).
    DEFAULT IS KLEIN THROUGHOUT — 小蓝的规矩 (2026-07-01): warning-register
    金句 don't use red. Pass --red to opt back in (hold-flip, never a tween:
    Klein->Red interpolation passes through banned purple); a red flip counts
    toward the <=3 red budget.
  Holds to --start + --dur. Transparent background.

Embed contract (HyperFrames): the lottie adapter seeks players to COMPOSITION
time, so a 金句 at comp t=X must be built with --start X (all keyframes are
offset; layers are hidden before X). --dur = window end (comp seconds from 0).
"""
import json, io, sys, argparse

ap = argparse.ArgumentParser()
ap.add_argument("glyphs")
ap.add_argument("out")
ap.add_argument("--text", default="先不要碰")
ap.add_argument("--active", default=None, help="glyph that punches (default: last)")
ap.add_argument("--red", action="store_true",
                help="OPT-IN: active glyph hold-flips Risk Red at the punch. Default is KLEIN "
                     "throughout (小蓝 2026-07-01: warning-register 金句不用红色).")
ap.add_argument("--start", type=float, default=0.0, help="comp seconds where the 金句 begins")
ap.add_argument("--dur", type=float, default=2.8, help="seconds from --start to hold until")
ap.add_argument("--size", type=float, default=235.0, help="glyph px (fit total <=950px)")
args = ap.parse_args()

GLYPHS = json.load(io.open(args.glyphs, encoding="utf-8"))
TEXT = args.text
ACTIVE = args.active or TEXT[-1]
FR = 30
SF = int(round(args.start * FR))            # start frame offset
OP = SF + max(84, int(round(args.dur * FR)))
W, H = 1080, 440
SCALE = args.size / 10.0                    # % of the 1000-unit em
ADV = args.size
X0 = (W - ADV * len(TEXT)) / 2.0
BASELINE = 310
INK   = [0x1F/255, 0x1F/255, 0x1D/255, 1]
KLEIN = [0x00/255, 0x2F/255, 0xA7/255, 1]
RED   = [0xD8/255, 0x4A/255, 0x3A/255, 1]

ENTRANCE_SHARP = (0.20, 0.75, 0.34, 0.94)
SETTLE_SOFT    = (0.00, 0.65, 0.51, 0.99)
EXPRESSIVE_POP = (0.94, 0.75, 0.34, 0.94)

def kf(t, v, ease=None, hold=False):
    k = {"t": SF + t, "s": v if isinstance(v, list) else [v]}
    if hold:
        k["h"] = 1
    elif ease:
        x1, y1, x2, y2 = ease
        k["o"] = {"x": [x1], "y": [y1]}
        k["i"] = {"x": [x2], "y": [y2]}
    return k

def anim(frames): return {"a": 1, "k": frames}
def static(v):    return {"a": 0, "k": v}

def shape_items(contours):
    return [{"ty": "sh", "ks": static({"v": c["v"], "i": c["i"], "o": c["o"], "c": c["c"]})}
            for c in contours]

layers = []
for idx, ch in enumerate(TEXT):
    g = GLYPHS[ch]
    d = idx * 7
    active = (ch == ACTIVE)
    t_trace0, t_trace1 = d, d + 16
    t_fill0, t_fill1 = d + 15, d + 19       # fast fill: no grey mid-state on cream
    t_st0, t_st1 = d + 18, d + 24

    trace_group = {"ty": "gr", "nm": "trace", "it": shape_items(g["contours"]) + [
        {"ty": "tm", "s": static(0),
         "e": anim([kf(t_trace0, 0, ENTRANCE_SHARP), kf(t_trace1, 100)]),
         "o": static(0), "m": 1},
        {"ty": "st", "c": static(KLEIN[:3] + [1]), "o": anim([
            kf(t_st0, 100, SETTLE_SOFT), kf(t_st1, 0)]),
         "w": static(26), "lc": 2, "lj": 2},   # w<20 reads wireframe at 235px
        {"ty": "tr", "p": static([0, 0]), "a": static([0, 0]), "s": static([100, 100]),
         "r": static(0), "o": static(100)},
    ]}

    if active and args.red:
        fill_color = anim([kf(t_fill0, KLEIN, hold=True), kf(50, RED, hold=True)])
    elif active:
        fill_color = static(KLEIN)
    else:
        fill_color = static(INK)
    fill_group = {"ty": "gr", "nm": "fill", "it": shape_items(g["contours"]) + [
        {"ty": "fl", "c": fill_color, "o": anim([
            kf(t_fill0, 0, SETTLE_SOFT), kf(t_fill1, 100)]), "r": 1},
        {"ty": "tr", "p": static([0, 0]), "a": static([0, 0]), "s": static([100, 100]),
         "r": static(0), "o": static(100)},
    ]}

    ax, ay = 500, -380                      # em-box optical center -> punch scales in place
    px = X0 + idx * ADV + ax * SCALE / 100.0
    py = BASELINE + ay * SCALE / 100.0
    if active:
        s = anim([kf(48, [SCALE, SCALE], EXPRESSIVE_POP),
                  kf(51, [SCALE * 1.18, SCALE * 1.18], SETTLE_SOFT),
                  kf(58, [SCALE, SCALE])])
    else:
        s = static([SCALE, SCALE])

    layers.append({
        "ddd": 0, "ind": idx + 1, "ty": 4, "nm": f"glyph-{ch}",
        "ks": {"o": static(100), "r": static(0),
               "p": static([px, py]), "a": static([ax, ay]), "s": s},
        "ao": 0, "shapes": [trace_group, fill_group],
        "ip": SF, "op": OP, "st": SF, "bm": 0,
    })

doc = {"v": "5.9.6", "fr": FR, "ip": 0, "op": OP, "w": W, "h": H,
       "nm": f"xiaolan-jinju {TEXT}", "ddd": 0, "assets": [], "layers": layers}
io.open(args.out, "w", encoding="utf-8").write(json.dumps(doc, ensure_ascii=False))
print("wrote", args.out, "layers:", len(layers), "ip/op:", 0, OP)
