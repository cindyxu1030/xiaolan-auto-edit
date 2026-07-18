# -*- coding: utf-8 -*-
"""Extract glyph outlines for given CJK chars from Google-Fonts woff2 slices
(Noto Serif SC 900) and emit Lottie-ready bezier shapes (one JSON per char).

Output JSON per char: {"char", "adv", "contours": [{"v":[[x,y]..],"i":..,"o":..,"c":true}]}
Coordinates are y-DOWN, scaled to a 1000-unit em, origin at glyph left/baseline.
"""
import io, json, re, sys, os
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen

FONTS_DIR = r"./fonts"  # 改成你自己的字体目录（woff2/otf 所在处）
CSS = os.path.join(FONTS_DIR, "fonts.css")
OUT_DIR = sys.argv[2] if len(sys.argv) > 2 else "."
TEXT = sys.argv[1] if len(sys.argv) > 1 else "先不要碰"

# --- parse fonts.css: blocks of (family, weight, url, unicode-range) ---
css = io.open(CSS, encoding="utf-8").read()
blocks = re.findall(r"@font-face\s*\{(.*?)\}", css, re.S)
slices = []
for b in blocks:
    fam = re.search(r"font-family:\s*'([^']+)'", b)
    wgt = re.search(r"font-weight:\s*(\d+)", b)
    url = re.search(r"url\(([^)]+\.woff2)\)", b)
    ur = re.search(r"unicode-range:\s*([^;]+);", b)
    if fam and wgt and url and ur:
        slices.append((fam.group(1), int(wgt.group(1)), url.group(1).strip("'\""), ur.group(1)))

def ranges(urange):
    out = []
    for part in urange.split(","):
        part = part.strip().upper().replace("U+", "")
        if "-" in part:
            a, b = part.split("-"); out.append((int(a, 16), int(b, 16)))
        elif "?" in part:
            lo = int(part.replace("?", "0"), 16); hi = int(part.replace("?", "F"), 16)
            out.append((lo, hi))
        else:
            v = int(part, 16); out.append((v, v))
    return out

def find_slice(ch, family="Noto Serif SC", weight=900):
    cp = ord(ch)
    for fam, wgt, url, ur in slices:
        if fam == family and wgt == weight:
            for lo, hi in ranges(ur):
                if lo <= cp <= hi:
                    return url
    return None

def quad_to_cubic(p0, p1, p2):
    c1 = (p0[0] + 2.0 / 3 * (p1[0] - p0[0]), p0[1] + 2.0 / 3 * (p1[1] - p0[1]))
    c2 = (p2[0] + 2.0 / 3 * (p1[0] - p2[0]), p2[1] + 2.0 / 3 * (p1[1] - p2[1]))
    return c1, c2

def glyph_contours(font, ch):
    """Return list of contours as lists of (pt, in_tangent, out_tangent) abs points, y-down, em=1000."""
    cmap = font.getBestCmap()
    if ord(ch) not in cmap:
        return None, None
    gname = cmap[ord(ch)]
    gs = font.getGlyphSet()
    pen = RecordingPen()
    gs[gname].draw(pen)
    upem = font["head"].unitsPerEm
    s = 1000.0 / upem
    adv = gs[gname].width * s

    def T(p):  # scale + flip y (font y-up -> screen y-down, baseline at y=0)
        return (round(p[0] * s, 2), round(-p[1] * s, 2))

    contours, cur, start, last = [], None, None, None
    for op, args in pen.value:
        if op == "moveTo":
            cur = {"pts": [], "closed": False}
            start = last = T(args[0])
            cur["pts"].append({"p": start, "i": start, "o": start})
            contours.append(cur)
        elif op == "lineTo":
            p = T(args[0])
            cur["pts"].append({"p": p, "i": p, "o": p})
            last = p
        elif op == "curveTo":
            c1, c2, p = (T(a) for a in args)
            cur["pts"][-1]["o"] = c1
            cur["pts"].append({"p": p, "i": c2, "o": p})
            last = p
        elif op == "qCurveTo":
            # TrueType: sequence of off-curve pts, maybe implied on-curves; final pt may be None (closed)
            pts = list(args)
            if pts[-1] is None:
                pts[-1] = tuple(x / s if False else x for x in ())  # not expected for CFF; guard below
                raise SystemExit("qCurveTo with None endpoint not handled (TrueType closed contour)")
            # expand implied on-curve points
            segs, prev_off = [], None
            for q in pts[:-1]:
                if prev_off is not None:
                    mid = ((prev_off[0] + q[0]) / 2.0, (prev_off[1] + q[1]) / 2.0)
                    segs.append((prev_off, mid)); prev_off = q
                else:
                    prev_off = q
            segs.append((prev_off, pts[-1]))
            for off, end in segs:
                p0 = (cur["pts"][-1]["p"][0], cur["pts"][-1]["p"][1])
                c1, c2 = quad_to_cubic(p0, T(off), T(end))
                cur["pts"][-1]["o"] = (round(c1[0], 2), round(c1[1], 2))
                pe = T(end)
                cur["pts"].append({"p": pe, "i": (round(c2[0], 2), round(c2[1], 2)), "o": pe})
        elif op == "closePath":
            cur["closed"] = True
    return contours, adv

def to_lottie_shape(contours):
    """Lottie path: v=vertices, i/o = RELATIVE tangents."""
    out = []
    for c in contours:
        pts = c["pts"]
        # drop duplicated last==first point on closed contours
        if len(pts) > 1 and pts[0]["p"] == pts[-1]["p"]:
            pts[0]["i"] = pts[-1]["i"]
            pts = pts[:-1]
        v = [[p["p"][0], p["p"][1]] for p in pts]
        i = [[round(p["i"][0] - p["p"][0], 2), round(p["i"][1] - p["p"][1], 2)] for p in pts]
        o = [[round(p["o"][0] - p["p"][0], 2), round(p["o"][1] - p["p"][1], 2)] for p in pts]
        out.append({"v": v, "i": i, "o": o, "c": c["closed"]})
    return out

os.makedirs(OUT_DIR, exist_ok=True)
result = {}
for ch in TEXT:
    url = find_slice(ch)
    if not url:
        print("NO SLICE for", repr(ch)); continue
    path = os.path.join(FONTS_DIR, os.path.basename(url))
    font = TTFont(path)
    contours, adv = glyph_contours(font, ch)
    if contours is None:
        print("NO GLYPH for", repr(ch), "in", os.path.basename(url)); continue
    result[ch] = {"adv": adv, "contours": to_lottie_shape(contours)}
    npts = sum(len(c["v"]) for c in result[ch]["contours"])
    print(f"{ch}: slice={os.path.basename(url)} contours={len(result[ch]['contours'])} pts={npts} adv={adv}")

out = os.path.join(OUT_DIR, "glyphs.json")
io.open(out, "w", encoding="utf-8").write(json.dumps(result, ensure_ascii=False))
print("wrote", out)
