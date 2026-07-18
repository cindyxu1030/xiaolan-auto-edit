# 金句 Lottie lane — trace-fill-snap (the second 金句 register)

Validated 2026-07-01 (A/B vs the GSAP slam: `<your-workspace>/jinju-lottie-test/`).
A second treatment for 金句 hero text, built as a Lottie asset and seeked by the
HyperFrames lottie adapter. Adds motion vocabulary GSAP-on-HTML-text can't do
(glyph outline draw-on), while the FINAL STILL stays identical to the johnbucog
lockup — same 思源宋体 Heavy, same palette, same size-to-fit.

## Pick the register per 金句 (semantics decide)
- **GSAP johnbucog slam (default)** — shock beats: 天价账单, big numbers, hard
  punchlines. Instant impact; no build-up.
- **Lottie trace-fill-snap (this lane)** — rules / warnings / build-anticipation
  beats: 先不要碰, 判断-type verdicts. Klein stroke traces the glyph outlines →
  ink fills flood in reading order → the active glyph punches (scale overshoot)
  **staying KLEIN**. ~1.7s of anticipation before the hit.
- **KLEIN ONLY by default — Xiaolan's rule (2026-07-01): warning 金句 don't use
  red.** The build script's red flip is opt-in (`--red`), reserved for a shock
  beat that genuinely owns a slot in the ≤3-red budget; when in doubt, don't.
- Never both registers on the same 金句.

## Pipeline (all local, deterministic)
1. **Extract glyph outlines** (思源宋体 Heavy, from the project's Google-Fonts
   woff2 slices — the same fonts the HTML text uses, so shapes match 1:1):
   `PYTHONIOENCODING=utf-8 python assets/glyph2lottie.py "<金句>" <workdir>`
   → `<workdir>/glyphs.json`. Reads `fonts.css` unicode-ranges to find each
   glyph's slice; outputs Lottie-ready beziers (y-down, 1000-unit em).
   The FONTS_DIR constant points at `agentloop-broll/fonts` — update if that
   project moves.
2. **Build the Lottie:**
   `python assets/build-jinju-lottie.py <workdir>/glyphs.json assets/<name>.json
    --text <金句> --active <红字> --start <comp-sec> --dur <window-sec>`
   Defaults: 30fps, 84-frame choreography, 235px glyphs (≤4 chars fits ≤950px;
   for 5+ chars pass `--size` smaller so total = chars×size ≤ 950).
3. **(optional) Author/edit by hand via the `text-to-lottie` skill** — the
   official Skottie player lives at `<your-workspace>/lottie-player/` (degit of
   diffusionstudio/lottie; scene under `public/projects/<p>/<scene-N>/lottie.json`,
   `npm run dev` → `?frame=N` pinning). Use it to iterate on choreography beyond
   what the build script parameterizes.
4. **Embed in the composition** (lottie-web, svg renderer):
   ```html
   <div class="jb-lottie" id="jbL1"></div>
   <script src="https://cdnjs.cloudflare.com/ajax/libs/bodymovin/5.12.2/lottie.min.js"></script>
   <script>
     const jbAnim = lottie.loadAnimation({ container: document.getElementById("jbL1"),
       renderer: "svg", loop: false, autoplay: false, path: "assets/<name>.json" });
     window.__hfLottie = window.__hfLottie || [];
     window.__hfLottie.push(jbAnim);
   </script>
   ```
   CSS: position the container exactly like a `.jb` band (top:382 height:440 by
   default — same head-clearance rules as any johnbucog beat).
5. **Verify in the cream-bg proxy render like everything else.** The Skottie
   player is for authoring iteration; the HyperFrames frames are the
   authoritative check (renderer parity: lottie-web ≠ Skottie on exotic
   features — this lane uses only shapes/trim/stroke/fill, safe in both).

## Gotchas (learned building this)
- **Adapter timing:** `__hfLottie` players are seeked to COMPOSITION time.
  A 金句 at comp t=X MUST be built with `--start X` (keyframes offset, layers
  hidden before X). One Lottie file per 金句; leave the karaoke gap over the
  window as usual.
- **Never tween Klein→Red inside the Lottie either** — same purple-midpoint ban
  as GSAP. The build script uses HOLD keyframes (`h:1`) for the flip.
- **Trace stroke width ≥26** (glyph units) at 235px glyphs — thinner reads as
  wireframe CAD, not calligraphy (the w16 first attempt failed the frame check).
- **Fill ramp ≤4 frames** — a slow opacity fade passes through a muddy grey
  stage over cream (ink at ~40% on cream = grey mud; caught in A/B v1).
- **Glyphs are baked outlines** — no Lottie font loading, no subsetted-woff2
  missing-glyph risk (个→↑ class bugs can't happen), renders identically in
  Skottie / lottie-web / HyperFrames.
- Emphasis-in-motion is already loud; do NOT add an underline/badge/glow to a
  trace-fill-snap 金句. The trace IS the flourish (one flourish per beat).
