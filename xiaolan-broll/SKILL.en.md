---
name: xiaolan-broll
description: >-
  Turn a FULL-LENGTH Xiaolan (小蓝) talking-head video into a brand-locked b-roll +
  word-pop karaoke caption layer, delivered as a TRANSPARENT overlay (ProRes MOV with
  alpha) that Xiaolan composites over her own high-quality A-roll — the A-roll is NEVER baked
  in. For cutout-on-cream verticals (9:16) where the presenter sits lower-center and the
  top half is empty. Builds object-first b-roll (one concrete animated object per beat, the
  loop-glyph motif), VO-locked word-pop karaoke (active word Klein blue + mint underline),
  and reserves the johnbucog giant-hero treatment for 金句 only. Use whenever the user wants:
  "make b-roll and karaoke captions for this video / a-roll", "整条视频的 b-roll 和字幕",
  "口播配图", "full b-roll", "动图 + 字幕 for my talking head", "transparent overlay I'll
  composite myself", or to add/restyle the graphics+captions across a whole 小蓝 explainer.
  Handles VO transcription, head measurement, section/金句 planning, the karaoke engine, the
  object-first scene build, self-verification, the transparent MOV render, and delivery.
  NOT for a short hook/opener with captions baked over the clip (use `xiaolan-hook-broll`,
  not included in this repo), and NOT for a bottom-right-corner talking head (use
  `shorts-hyperframe`, not included in this repo).
---

# xiaolan-broll

Build the **b-roll + karaoke caption layer** for a full-length 小蓝 talking-head video and
deliver it as a **transparent overlay** Xiaolan drops on top of her own A-roll. This is the
workflow that produced `agentloop-broll-overlay.mov` (a 2:47 Agent Loop explainer).

The layout is **cutout-on-cream, presenter lower-center, top half empty cream** — your
graphics + captions live in that empty top zone and must never touch her cutout or run off
the cropped vertical edges.

## How this differs from the neighbors (pick the right skill)
- **`xiaolan-broll` (this)** — FULL video. b-roll + word-pop karaoke the whole way, johnbucog
  only on 金句. Output = **transparent MOV** (alpha), A-roll NOT baked in. Cutout lower-center.
- **`xiaolan-hook-broll` (not included in this repo)** — a SHORT opener/hook. Kinetic captions
  BAKED over the clip (MP4 with her footage in it). johnbucog or editorial, every beat.
- **`shorts-hyperframe` (not included in this repo)** — b-roll graphics for a BOTTOM-RIGHT
  corner talking head.

## Read first (authoritative, in order)
1. Brand canon (supersedes everything): your own brand spec — palette, fonts, the
   **object-first rule**; the non-negotiables section below covers the core.
2. Lane memory: your own decision log / mistake book — every gotcha learned the hard way
   should live there; skim it before you start.
3. `references/build-recipe.md` — architecture, the exact workflow, the transparent-MOV
   pipeline, and all the gotchas.
4. `references/karaoke-engine.md` — the word-pop engine, the `w`/`u` phrase formats, auto-fit.
5. `references/scene-library.md` — the object-first b-roll scene catalog (reuse, don't reinvent).
6. `references/asset-generation.md` — when a beat is a CAST acting out a story (小蓝 + her robot
   in poses, signature props) rather than an abstract/UI concept, build ILLUSTRATED green-screen
   cutouts via **Codex imagegen** (driven by an asset-manifest doc) instead of SVG line-art.
7. `references/jinju-lottie.md` — the SECOND 金句 register: Lottie trace-fill-snap
   (Klein outline draw-on → ink fill → Klein punch; NO red — Xiaolan, 2026-07-01) for
   warning/rule/anticipation 金句; the GSAP johnbucog slam stays the default for shock beats.

## The non-negotiables
- **Transparent overlay, A-roll NEVER baked in (Xiaolan's rule).** Composition background
  `transparent`; no base `<video>`/`<audio>`. Render `--format mov` → ProRes 4444
  `yuva444p12le` (has alpha). `--format webm` came out `yuv420p` (NO alpha) — don't trust it.
- **VO-locked captions, segmented by SPEECH PAUSE.** Transcribe the actual audio
  (faster-whisper). Caption what she SAID; use any script only to fix proper nouns whisper
  mangled. Phrase-level word-pop, never free-float. **One short line per pause — when she
  pauses, start a NEW caption line. Build the `PH` array 1:1 from whisper SEGMENTS (split any
  segment >~13字); never merge segments into one long line that auto-shrinks. Font must stay
  large.** If the b-roll visual already conveys a word, drop it from the caption (e.g. the
  before→after frames carry "从这样" — don't also caption it). (Xiaolan, 2026-06-17.)
- **Brand lock on cream:** charcoal / Klein-blue / Risk-Red type, 思源宋体 Heavy display.
  **White text BANNED** (invisible on cream). Risk Red ≤3 uses — the shock 金句 is the one.
- **Giant-hero treatment for 金句 ONLY.** The rest is karaoke + object-first b-roll. Two
  registers, picked per 金句 semantics: the GSAP **johnbucog slam** (default — shock beats,
  numbers) or the **Lottie trace-fill-snap** (warnings/rules/anticipation —
  `references/jinju-lottie.md`). Either way: size to fit ~950px for CJK (pure-bleed is for
  numbers only), never both registers on one 金句.
- **Clear the head.** Measure head-top (`assets/measure-head.py`); all graphics live in the
  top zone above it. b-roll ~y248–768, johnbucog band ~y382–822.
- **Karaoke band sits JUST ABOVE her head (~35–50px gap), NOT floating mid-frame.** Xiaolan's
  rule (2026-06-17): subtitles should be close to her head — no big empty gap between the
  b-roll and the caption. The default y800–950 floats too high. With a low head-top (e.g.
  measured y1088) put the band bottom ~y1050 (band `top:935 height:115`). Then **lower the
  b-roll objects to fill the freed middle** (e.g. `.broll top:300`) so object scenes don't
  look top-heavy. This is the "green box" position from her layout mockup.
- **Object-first, ILLUSTRATED-first (Xiaolan, 2026-07-06).** Every scene's subject is a concrete
  animated object, never a text box — and by default that object is an **illustrated
  green-screen cutout** (Codex imagegen, step 5b), NOT SVG line-art. SVG is reserved for
  inherently graphic elements only: counters, terminals/UI mockups, donuts/diagrams, arrows,
  chips/labels, the recurring **loop ⟳ glyph** motif, and caption accents. If the scene's hero
  is a THING (tool, coin, door, building, phone, lighthouse…), it gets a cutout. Shipping an
  SVG-only b-roll track is a REJECTED pattern. ≤6 words of label beside the object.
- **Self-verify every section frame-by-frame before delivering.** Xiaolan expects you to catch
  ugliness yourself.

## Workflow
1. **Scaffold** `<your-workspace>/<name>-broll/`: copy a prior project's `fonts/` dir
   (local Noto Serif/Sans SC woff2 + `fonts.css`) and `hyperframes.json` / `meta.json` /
   `package.json`. Start `index.html` from `assets/full-template.html`.
2. **Inspect** the A-roll (`ffprobe` + a contact sheet): confirm 9:16 cutout-on-cream,
   presenter lower-center, top half empty, no pre-baked text.
3. **Transcribe the VO** → word timings + readable transcript: `assets/transcribe.py`
   (faster-whisper medium, `--language zh`, word_timestamps, int8 CPU, `PYTHONIOENCODING=utf-8`).
4. **Measure the head:** `python assets/measure-head.py <aroll.mp4> <t0 t1 …>`. Confirm the
   ceiling across the WHOLE clip (cutouts drift); set the band tops accordingly.
5. **Plan** a section map: one object-first b-roll scene per narrative beat + the karaoke
   phrase windows + which lines are 金句, and per 金句 which register — johnbucog slam or
   Lottie trace-fill-snap (`references/jinju-lottie.md`). Confirm the 金句 list, registers,
   and scope with Xiaolan; for a long video, build a short PROOF segment (hook + the ending
   金句) first and get look approval before the full render.
5b. **Generate green-screen props — MANDATORY, every episode** (Xiaolan, 2026-07-06 — this step
   was being skipped; never skip it again). See `references/asset-generation.md`. EVERY scene's
   hero object from the step-5 section map gets an illustrated cutout unless it is pure
   UI/counter/typography: (a) **Reuse first** — go through your own green-screen cutout library
   folder (build one if it doesn't exist yet; archive every cutout you generate into it — the
   library compounds, and you likely already have a matching cutout; reuse always beats
   generating new); (b) author an asset-manifest doc with a row for EVERY scene hero, marked
   ✅ reuse / 🆕 generate; (c) generate the 🆕 rows with Codex imagegen (`codex exec
   --skip-git-repo-check -C <assets> "…green sprite sheet, cut cutouts…" < /dev/null` — verify
   ONE sheet before the batch); (d) key → cut → contact sheet → **self-QC and AUTO-APPROVE**
   (Xiaolan, 2026-07-06: no human gate on props — LOOK at the contact sheet yourself: style match
   with the library, registration, no fringe/text/red/purple; regenerate failures; include the
   contact sheet in the delivery report so Xiaolan can spot drift after the fact). SVG stays only
   for counters/terminals/donuts/arrows/chips/loop-glyph/caption accents. The build (step 6)
   does not start scene authoring until the manifest's cutouts are on disk.
6. **Build** `index.html`: paste the karaoke `PH` array (VO-locked), author/clone the
   object-first scenes (`references/scene-library.md`), place the 金句 beats (johnbucog
   divs; for Lottie-register 金句 build the asset with `assets/glyph2lottie.py` +
   `assets/build-jinju-lottie.py --start <comp-sec>` and register the player on
   `window.__hfLottie`). One paused timeline registered on `window.__timelines["main"]`.
   SERIALIZE transitions.
7. **Lint** `npx hyperframes lint` → 0 errors. (`composition_file_too_large`, CSS-var-font,
   overlapping-tween, gsap-studio warnings are benign.)
8. **SELF-VERIFY (mandatory, cream-bg proxy).** Her bg is cream, so a cream-bg draft is a
   faithful top-zone preview AND makes charcoal karaoke visible (it's invisible on the
   transparent/black draft):
   `sed 's/background:transparent/background:#F5EFE2/g' _src/full.html > index.html`,
   `npx hyperframes render --quality draft -o renders/verify.mp4`, extract one frame per
   section (`ffmpeg -ss <t> -frames:v 1`), LOOK at every one, fix, repeat.
9. **Final render** the real transparent build: `npx hyperframes render --format mov -o
   renders/<name>-overlay.mov`. Spot-check by compositing over her real A-roll:
   `ffmpeg -ss <t> -i aroll.mp4 -ss <t> -i overlay.mov -filter_complex "[0:v][1:v]overlay=format=auto" -frames:v 1 chk.jpg`.
10. **Compress, then deliver.** The ProRes master is ~1GB (codec, not resolution). Transcode
    it to a LOSSLESS `qtrle` `.mov` (same 1080p + alpha, still `.mov`, ~6× smaller):
    `ffmpeg -i renders/<name>-overlay.mov -c:v qtrle -pix_fmt argb -an renders/<name>-qtrle.mov`.
    Ship the **qtrle `.mov`** into your footage folder under the delivery name; keep the
    ProRes master in `<your-workspace>/<name>/renders/`. Don't bake or overwrite her A-roll.
    (Details + the webm option: `build-recipe.md`.)
11. **Log:** append technique/decisions to your own decision log / mistake book; if anything
    was rejected, write a separate entry — what it was and why it was rejected.

## The gotchas that bite (full list in build-recipe.md)
- **Never tween Klein blue → Risk Red** (RGB passes through banned PURPLE) — `tl.set` snap.
- **Seek-safe only:** `tl.to({textContent})` / `tl.call()` don't fire on frame-seek — number
  rolls/counters MUST use a proxy obj + tween `onUpdate` writing textContent.
- **Auto-fit every karaoke line ≤905px** (measure scrollWidth → scale) or it bleeds the
  cropped edges. 金句 CJK heroes: size to fit, don't pure-bleed (cuts glyphs in half).
- **Serialize scene transitions** — each scene fully exits before the next enters; never
  cross-dissolve two busy hero-zone elements (Xiaolan rejected that as "not clean").
- **Local Noto Sans SC woff2 is subsetted** — some heavy CJK glyphs missing (个→↑). Verify
  every 字 in a frame, or render small CJK in the SERIF face.

## Assets
- `assets/full-template.html` — the proven full-length build (karaoke engine + helpers +
  object-first scene library + 4 johnbucog beats). Clone and re-content.
- `assets/transcribe.py` — faster-whisper → word-level JSON + readable transcript.
- `assets/measure-head.py` — head-top measurement across beats.
- `assets/glyph2lottie.py` + `assets/build-jinju-lottie.py` — the Lottie 金句 lane:
  思源宋体 Heavy glyph outlines → trace-fill-snap Lottie (`references/jinju-lottie.md`).
- (fonts + Cormorant woff2: copy from a prior `<your-workspace>/*/fonts/` dir.)
- `references/asset-generation.md` — the illustrated green-screen cutout recipe via Codex
  imagegen; drive it with an asset-manifest doc (one row per scene hero, marked
  ✅ reuse / 🆕 generate); the shared cutout library is your own green-screen cutout library
  folder (reuse before generating).
