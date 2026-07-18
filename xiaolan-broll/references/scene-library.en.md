# Object-first b-roll scene library

Every scene's subject is a **concrete animated object** (the "object-first rule" in your brand
spec), never a text box. One visual verb per scene; a ≤6-word `.label` beside it. The **loop ⟳
glyph is the recurring motif** — reuse it for cohesion. All built as inline `<svg>` line-art
(stroke ~3–4% of viewBox, rounded caps) in the brand palette, animated by the shared timeline
helpers (`show/hide/breathe/spin/drawOn/pop/counter`). Full working code for ALL of these is in
`assets/full-template.html` — clone the closest one and re-content.

## Brand palette (locked)
```
cream #F5EFE2  panel #FBF7EE  ink #1F1F1D  klein #002FA7  deep #001A5E
mint #8ACAB1   mintdeep #4E9278  gray #5A5A56  rail #C9BFA6  red #D84A3A (≤3/video)
```

## Scenes in the template (reuse these)
| Scene | Object | Verb / motion |
|---|---|---|
| editor card | macOS-ish panel, traffic dots, mono prompt line | prompt typed → red strike-through (划掉) |
| loop glyph | klein circular arrow ⟳ + arrowhead | draw-on (stroke-dashoffset) + spin; the motif |
| burning ¥ | banknote with ¥, two flames | deterministic flame flicker (keyframed x/scaleY) |
| intern@desk | person glyph at laptop + crescent moon + clock | laptop glow pulse, moon rises, clock hand sweeps (一整夜) |
| two-things | bolt (触发) + bullseye (目标) with "+" | each pops in (back.out) |
| trigger trio | event-node · clock · cursor-tap | sequential pop, one per kind |
| test panel | card with rows + green ✓ circles | rows tick in left-to-right (机器判断) |
| cron-vs-loop | clock with red strike ✗ vs loop with "?" | stop appears; loop spins (自问达标没) |
| draining battery | battery outline + klein fill + $$$ | fill width drains; **snap fill→red at empty** (NOT a tween!) |
| review dial | loop ⟳ + score N/5 + gate | score count 3→5 (onUpdate), round 1/5→5/5, gate ✓ draws at 5 |
| experiment | big counter + sparkline | counter 0→700 (onUpdate), sparkline draws on |
| big code block | code-lines card + magnifier | shake (1000+ 行 too big, 永远到不了 5 分) |
| to-do gate | to-do card + 90% ✓ badge | badge pops, next row un-greys |
| target hit | bullseye + flying arrow + mint ✓ | arrow flies to center, ✓ pops (有标准答案) |
| human-in-loop | loop ⟳ with a person glyph at center + mint ✓ | circle draws, dot orbits, person pops |
| checkpoint rail | rail + person checkpoint + blocked "下一步" node | klein token travels in, red ✗, back-arc returns it (回去重改) |
| 关注 CTA | klein follow pill + doc glyph | pill pops + pulses, doc slides in |
| **logo chip** | a REAL brand logo (brand color) in a soft white/panel rounded card + 思源黑体 name | chip pops in (back.out), mint underline draws on |

## Density — ONE animated beat per SENTENCE (Xiaolan (小蓝)'s bar)
Do NOT park one object for a whole multi-sentence section. EVERY karaoke phrase should
trigger a visual change. After authoring, sweep each section: count animation events vs
phrases — if events < phrases, add beats. A section >~6s with 1–2 events is too sparse.
Cheap density toolkit (all seek-safe): `rollNum` counters; a **% donut** (`rollNum` + arc
`strokeDashoffset` to `circ*(1-pct)`); staggered `pop`s of N elements (buyer dots, bricks,
module tiles); a lock/barrier that swings open (`rotation` on a shackle path); an object or
recipient SWAP (人→Agent, software→brick, db→donut); a badge (热卖); a two-arrow feedback
loop; a "?" hook over the opening line. Two reusable patterns proven this lane:
- **% donut** — "六成由 AI 创建": a track circle + a klein arc that draws to the % + a rolling
  `0→N%` number inside.
- **hot-selling cluster** — "酱料热卖/日活几百万": a sales `rollNum` + 3–4 staggered buyer-dot
  `pop`s + a mintdeep 热卖 badge popping with overshoot. Conveys "selling fast, lots of buyers".

## Real brand logos (when the VO names companies, e.g. Supabase / YC / HashiCorp)
Fetch official single-path SVGs: `curl -s -o <slug>.svg https://cdn.simpleicons.org/<slug>`
(slugs: `supabase`, `ycombinator`, `hashicorp`, …; some brands 404 — then grab from the
brand's site or skip if it's already in Xiaolan's footage). Inline the path with its brand `fill`.
Xiaolan-approved presentation = **brand-color mark in a soft chip** (panel bg + #E6DEC9 border +
shadow, mark ~96px + name + a mint scaleX underline). YC's simpleicons path is monochrome
(square+Y same color → Y invisible) — rebuild it: orange `#F0652F` rounded rect + cream serif
`<text>Y</text>`. Place each chip at the moment the name is spoken; reprise for callbacks.

## Translating a new concept (when it's not in the table)
Ask "what physical object would a viewer recognize instantly performing this idea?" Draw that.
If truly abstract, mock the actual product UI (your coding agent's terminal, a phone screen,
your note system).
Avoid: text-bearing rectangles as the subject, gradient orbs, neon/cyberpunk, grids/dot-grids,
emoji as the hero (emoji OK as a small accent label), red+green compare (use grey vs mint).

## Helpers (defined in the template)
```
show(sel,at,d) / hide(sel,at,d)     opacity in/out (serialize: hide before next show)
breathe(sel,at)                     subtle scale yoyo for ambient life
spin(sel,at,dur)                    rotation 360 (loop glyphs)
drawOn(sel,at,dur)                  stroke-dashoffset draw-on (sets hidden at load)
pop(sel,at,from,origin)             back.out scale+fade entrance (badges/icons)
counter(obj,sel,to,at,dur,suffix)   seek-safe number roll via proxy + onUpdate
```
Risk Red budget ≤3/video: spend on the 天价账单 金句 + at most two accents (a strike-through
划掉, the cron-stop ✗). Count them before rendering.
