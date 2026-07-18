# Custom green-screen b-roll assets — illustrated cutouts via Codex imagegen

**THIS IS THE DEFAULT PATH FOR EVERY EPISODE (Xiaolan, 2026-07-06).** The scene-library
(`scene-library.md`) is inline **SVG line-art** — fast, deterministic, cold. The b-roll reads
far warmer as **hand-drawn illustrated cutouts** that HyperFrames animates by **pose-swap**,
and Xiaolan (小蓝) expects the illustrated look: an SVG-only b-roll track is a rejected
pattern. This is the same recipe that produced the cartoon 片尾 and the 夜班内容生产线 eps.
Generate the cutouts with **Codex CLI imagegen** (GPT Image), driven by an **asset manifest
doc**.

## What gets a cutout vs what stays SVG
- **Default: every scene HERO object gets an illustrated cutout** — cast poses (小蓝, the
  robot), and STANDALONE THINGS the narration names: tools, coins/chips, doors, buildings,
  phones, lighthouses, briefcases, props of any kind. If the beat's subject is a noun you can
  draw, it's a cutout.
- A recurring **character or prop** across many beats (the robot as "digital employee",
  a signature prop) → illustrated, for consistency — reuse the locked designs.
- SVG line-art (`scene-library.md`) is ONLY for the inherently graphic layer: counters,
  terminals/UI mockups, % donuts, diagrams, arrows/connectors, small chips/labels, the loop ⟳
  glyph motif, caption accents — don't illustrate what a glyph says better, and don't glyph
  what a drawing says warmer.
- **The two layers compose in one video:** illustrated heroes + live SVG UI/motion accents.

## REUSE FIRST — you likely already have a cutout that fits
Before generating anything, list your own green-screen cutout library folder. After a few
episodes it should already hold clean **RGBA** cutouts: 小蓝 poses (`xiaolan-idle/point/present/
think/press/night-type/review-tablet/sleep/stretch-wake`), robot poses (`robot-idle/clipboard/
magnifier/stamp/receive/deliver/talk/type/walk-A/walk-B/headphones`), and dozens of props
(`prop-laptop/folder-doc/shared-list/desk-monitor/brand-kit/coffee-mug/whiteboard/
video-clip-card/…`). **Mark every manifest row ✅ reuse or 🆕 generate; only generate the 🆕.**
Regenerating an existing pose wastes ~95k tokens AND risks design drift from the locked cast.

## The asset manifest doc (author this from the script)
Write an `assets-EP-<slug>.md` per episode in your own asset-manifest doc folder — once the
first episode is proven, use it as the template for every later one. Sections:
1. **Format & layout** — 1080×1920; cartoon stage in the top zone (clear of the presenter's
   low head); flat cream `#F5EFE2` bg is filled LIVE in HyperFrames, **do NOT generate a
   background**.
2. **How motion works — pose-swap tiers** (read this first): Tier 0 = single cutout (I move the
   whole thing); Tier 1 = 2-pose gesture set (crossfade); Tier 2 = 2-3 pose cycle (walk). The
   make-or-break is **registration** — across frames that animate together keep cell size,
   character height, foot/baseline Y, camera, light, line weight, colors, hair IDENTICAL; ONLY
   the moving limb changes, or the swap "jumps."
3. **Locked design** — the cast + palette, "match existing cutouts, do not redesign." 小蓝: long
   brown wavy hair, Klein-blue zip hoodie, white tee, light-blue rolled jeans, white sneakers.
   Robot: rounded white body, Klein-blue eyes/antenna/joints, one robot — role = the prop it
   holds. Palette: Klein `#002FA7`, deep `#001A5E`, mint `#8ACAB1`, cream `#F5EFE2`, charcoal
   `#1F1F1D`, red `#D84A3A` (alerts only). Hand-drawn line, NOT SVG-flat / 3D / neon.
4. **Shopping list** — grouped sprite sheets (小蓝 poses · robot poses · props), each row = file /
   pose / tier / ✅|🆕 / used-for.
5. **Scene → asset coverage** — every beat maps to cast+props; every 🆕 asset is used ≥1×.
6. **Generation prompt template** (per sheet) — see below.
7. **Deliver-back** — `<sheet>-green.png` + `<sheet>-alpha.png` + cut individual cutouts + a
   contact sheet; drop in the shared `assets/`. **Props are AUTO-APPROVED (Xiaolan, 2026-07-06):**
   self-QC the contact sheet (style match, registration, fringe, bans) and proceed straight to
   the build — no human gate. Include the contact sheet in the delivery report so Xiaolan can
   spot drift after the fact and order redraws.
8. **What I build LIVE (do NOT generate):** all text/captions, arrows/connectors, speech
   bubbles, ✓ ticks, counters/donuts, highlight sweeps, glows — HyperFrames renders those.

## The generation prompt (per sheet)
```
A sprite sheet of ONE character in [N] labeled poses in a clean grid.
Hand-drawn cartoon illustration, soft fill + ink line. Flat chroma-green #00B140 behind every
pose (for clean cutout). No ground shadow, no text labels, no background scene.
Character (IDENTICAL across poses — match the attached reference EXACTLY): [design].
Poses (same height, same foot baseline, same camera, same light, ONLY the limb changes):
  1.[pose] 2.[pose] 3.[pose] …
Palette: Klein #002FA7, deep #001A5E shadow, mint #8ACAB1, charcoal ink. Each pose ≥1000px tall.
```
Props sheet: "objects on flat green, hand-drawn to match the cast line, no text." Attach existing
cutouts as **reference images** (tell Codex to READ them and match) so new art matches the lock.

## Running Codex imagegen (headless, confirmed working)
Codex's desktop binary may be **off-PATH** (`which codex` failing doesn't mean it's not
installed — find it in the install directory). It has both file access and GPT-Image
generation. Invoke per sheet:
```
codex exec --skip-git-repo-check \
  -C "<assets-dir>" "<prompt: READ ref PNGs X,Y; generate sheet Z on green; cut each pose to a
  named RGBA cutout; write a contact sheet>" < /dev/null
```
- `--skip-git-repo-check` REQUIRED outside a trusted/git dir (else "Not inside a trusted directory").
- `< /dev/null` REQUIRED — `codex exec` reads stdin; a non-tty pipe never EOFs → hangs forever at
  0% CPU. (A pitfall worth recording in your own decision log — don't hit it twice.)
- Set the config to `approval=never`, `sandbox=danger-full-access`, model `gpt-5.5` → runs
  unattended, ~1-2 min + ~95k tokens per image. Output also lands in `~/.codex/generated_images/`.
- **Verify the pipeline with ONE sheet before the full batch** (these binaries drift; a 5-day-old
  memory is not live state). Then generate the rest.

## Keying + QC
- If Codex hands back a flat-green sheet (not alpha), key it: `ffmpeg -i sheet-green.png -vf
  "chromakey=0x00B140:0.30:0.10,despill" sheet-alpha.png` (tune similarity/blend per hair edges),
  then crop each cell. Cleanest is when Codex outputs the cut RGBA cutouts directly.
- **Build a contact sheet and LOOK** for registration drift (feet not landing on one Y, height
  jitter, hair/color shift between poses, baked shadows/text). Report it to Xiaolan for sign-off
  before locking beat timing — a drifting swap pair ruins the animation.

## Using the cutouts in HyperFrames
Each cutout is an `<img class="cut" src="assets/<name>.png">` positioned in the b-roll zone, shown
via the timeline `show/hide` helpers; a **pose swap** = crossfade two cutouts of the same
character at the same x/baseline (Tier 1), a **walk** = alternate walk-A/walk-B while translating x
(Tier 2). CJK cutout gotcha: `robot-walk-A`/`-B` are horizontal MIRRORS (A faces left, B faces
right) — never alternate a mirror pair as a walk cycle; use ONE facing pose + a vertical bob
(record this fix in your own decision log — it came out of the cartoon 片尾 episode).
