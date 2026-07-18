# Karaoke engine — word-pop, VO-locked, auto-fit

The proven engine lives verbatim in `assets/full-template.html`. This is the spec so you can
re-content it correctly.

## Look (the 小蓝 word-pop lane)
- One phrase on screen at a time, centered in the band, 思源黑体 (Noto Sans SC) 800,
  ~62px, charcoal `#1F1F1D`.
- **Band position (Xiaolan, 2026-06-17): sits JUST ABOVE the presenter's measured head-top,
  ~35–50px gap** — e.g. head-top y1088 → band `top:935 height:115` (bottom ~y1050). The old
  y800–950 default floats too high mid-frame — never ship it unmeasured. When the band drops,
  lower the b-roll objects to fill the freed middle (see SKILL.md non-negotiables).
- The **active unit** turns **Klein blue `#002FA7`** with a quick 1.13 scale pop; the previous
  unit reverts to charcoal.
- An **emphasis** unit STAYS klein and gets a **mint hand-drawn underline** (a child `.ul` span,
  `transform:scaleX(0)→1` draw-on). Mark keywords: loop / 触发 / 验证 / 判断 / the shock numbers.
- Phrase enters (fade + y up) ~0.04s before its start, exits (fade) at its end.

## Phrase data — two formats (both supported by `unitsOf()`)
```js
const PH = [
  // explicit word times (hand-tuned regions — hook, ending):
  {w:[["不写",2.60],["prompt",2.88,"le"],["了",3.24],["loop",3.76,"le"]], s:2.22, e:4.04},
  // interpolated units (the body — fast to author):
  {u:"loop* 就像 你招了个 很聪明的 实习生*", s:15.42, e:17.62},
];
```
- `w` form: `[[text, activationTime, flags]]`. flags: `l`=latin (adds side margin), `e`=emphasis.
- `u` form: space-separated units; `*` suffix = emphasis; latin auto-detected. Activation
  times are **interpolated** evenly across `[s, e]` — good enough for the body; the phrase
  WINDOW (`s`,`e`) stays VO-locked to whisper.
- CJK units are 1–3 chars (natural reading chunks). Keep latin tokens whole ("cron", "loop").

## Auto-fit (non-negotiable — stops edge bleed)
After building each line, measure `inner.getBoundingClientRect().width`; if `> 905`, set
`inner.style.transform = scale(905/width)`. Platforms crop the vertical edges, so a line that
fits the full 1080 still gets clipped — 905 keeps it inside the safe ~100px margins. SPLIT
phrases longer than ~9 units into two windows so the auto-fit scale stays near 1 (consistent
text size); auto-fit is the safety net, not the primary sizing.

## Build loop (per phrase) — see the template for exact tweens
```
fromTo(line, opacity/y in)   @ s-0.04
to(line, opacity 0)          @ e
per unit:
  set(unit, color klein)     @ t
  fromTo/to scale pop        @ t
  if emph: to(.ul scaleX 1)  @ t+0.02       // stays klein
  else:    to(unit color ink)@ next.t        // reverts
```

## Excluding johnbucog windows
The 金句 are NOT karaoke — leave a GAP in `PH` over each 金句 window (e.g. 先不要碰, 判断,
天价账单, the English payoff). The johnbucog band handles those beats; the karaoke resumes
after.

## VO timing source
Get phrase windows from the whisper SEGMENT boundaries; get explicit word times (for `w`
phrases) from the whisper WORD timestamps (`transcribe.py` writes both to `transcript.json`).
Correct the display text to Simplified + fix homophones/proper-nouns, but keep the timings.
