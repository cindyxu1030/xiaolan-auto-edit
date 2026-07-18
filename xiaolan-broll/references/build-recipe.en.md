# Build recipe — full-length 小蓝 b-roll + karaoke transparent overlay

## Architecture (the pattern that works)
- **NO base video/audio.** The output is a transparent overlay; her A-roll is composited
  UNDER it later. So the composition has only graphics + captions on a transparent stage.
  ```
  html,body{ background:transparent; }
  .stage{ background:transparent; }          /* root data-composition-id, full duration */
  ```
  Set `data-duration` to the A-roll length (e.g. 166.9). No `<video>`/`<audio>` clips.
- **Three layers, all in the root, by z-index:**
  - `.broll` (z 15, top:248 height:520) — the object-first hero scenes, each `.scene`
    `opacity:0`, shown/hidden by the timeline.
  - `.kband` (z 20) — the word-pop karaoke, lines injected by JS. Position it from the
    MEASURED head: band bottom ~35–50px above head-top (e.g. head y1088 → `top:935
    height:115`) — Xiaolan's 2026-06-17 rule; the template's `top:800` is a placeholder.
  - `.jb` (z 25, top:382 height:440) — the johnbucog 金句 bands (one per 金句), `opacity:0`.
- **One paused GSAP timeline** registered on `window.__timelines["main"]`. Deterministic
  only (no Math.random / Date.now). Build all DOM + tweens synchronously at script load.

## Check the A-roll for ALREADY-baked b-roll (do this during Inspect)
Some A-rolls are WIP and already have screen recordings / cutaways baked into the top zone at
certain beats. Sample a contact sheet across the WHOLE clip (every ~10s), not just a few
frames. Where the top is already occupied, LEAVE THAT WINDOW'S TOP CLEAR in your overlay
(karaoke continues, no graphics) so you don't collide. NOTE: `measure-head.py` false-positives
on baked content (reads it as a high "head") — eyeball the frames; don't trust a lone outlier.

## Zones (1080×1920, cutout-on-cream, head-top ≈ y988 — ALWAYS measure)
| Layer | y range | notes |
|---|---|---|
| top platform chrome | 0–230 | keep clear of key content |
| b-roll hero (`.broll`) | 248–768 | one concrete object + ≤6-word label |
| johnbucog 金句 (`.jb`) | 382–822 | replaces b-roll for the 金句 beat |
| karaoke band (`.kband`) | head-top −150 → −35 | just above the presenter's head, ~35–50px gap (e.g. head y1088 → 935–1050); lower `.broll` to fill the freed middle |
| her cutout | 988+ | NOTHING legible here |
Keep ≥100px blank at the left+right edges (platforms crop vertical edges).

## Transparent MOV pipeline (the delivery)
- Render: `npx hyperframes render --format mov -o renders/<name>-overlay.mov`
  → ProRes 4444, `pix_fmt=yuva444p12le` (HAS alpha). This is the **archival master**; keep it
  in `renders/`, do NOT ship it. It's ~1GB for ~2:47 — and that size is from the CODEC
  (near-lossless intra-frame + 12-bit alpha ≈ 700–900 Mbps), NOT the resolution. Compressing
  does not touch 1080p.
- **hyperframes `--format webm` flattened alpha to `yuv420p` — don't use it for transparency.**
- **DELIVER A COMPRESSED ALPHA `.mov` — transcode the ProRes master to `qtrle` (Xiaolan's pick).**
  QuickTime Animation (RLE) is LOSSLESS, keeps 1080×1920 + alpha (argb), stays a `.mov` so
  CapCut imports it identically (no relink), and is **~6× smaller** (1GB → ~170MB) because
  flat-color-on-transparent graphics RLE-compress brilliantly:
  ```
  ffmpeg -i renders/<name>-overlay.mov -c:v qtrle -pix_fmt argb -an renders/<name>-qtrle.mov
  ```
  Ship the qtrle `.mov` under the delivery name; keep the ProRes as the archival master.
  (PNG-in-mov `-c:v png -pix_fmt rgba` is also lossless but ~2× the qtrle size.)
- **Smallest = VP9 alpha webm (~12MB) but lossy + CapCut-risky.** `ffmpeg -i master.mov
  -c:v libvpx-vp9 -pix_fmt yuva420p -auto-alt-ref 0 -row-mt 1 -an out.webm`. ffmpeg stores
  the alpha in an `alpha_mode=1` side-channel — `ffprobe` shows `yuv420p` on the main plane
  but alpha IS there; to decode/verify it you MUST force `-c:v libvpx-vp9` on the INPUT
  (the default vp9 decoder ignores alpha → renders transparent areas BLACK, a false alarm).
  Some CapCut builds flatten webm alpha on import — only offer it if Xiaolan accepts that risk.
- Verify alpha over her real A-roll (single frame):
  ```
  ffmpeg -ss <t> -i aroll.mp4 -ss <t> -i <overlay> \
    -filter_complex "[0:v][1:v]overlay=format=auto" -frames:v 1 chk.jpg
  ```

## Verify loop (cream-bg proxy — fast + faithful)
Charcoal karaoke is invisible on the transparent/black draft. Her bg IS cream and all
graphics live in the top zone, so a cream-bg draft is a faithful preview:
```
sed 's/background:transparent/background:#F5EFE2/g' _src/full.html > index.html
npx hyperframes render --quality draft -o renders/verify.mp4
# one frame per section:
ffmpeg -ss <t> -i renders/verify.mp4 -frames:v 1 -q:v 3 verify/<sec>.jpg
```
LOOK at every section frame. Check: legibility, head/edge clearance, glyph correctness,
color discipline (no purple, ≤3 red), transition cleanliness. Fix in `_src/full.html`,
re-render. Only render the real transparent MOV once the cream proxy is clean.

## Render times (this box, 6 workers)
- ~167s draft mp4 ≈ 1m53s.  ProRes MOV ≈ ~8min + ~1GB.  Iterate on draft, render MOV once.

## Gotchas (don't repeat)
- **NEVER tween Klein blue (#002FA7) → Risk Red (#D84A3A) directly** — RGB interpolation
  passes through PURPLE (a 风格禁区 banned color) at the midpoint. Snap with
  `tl.set(el,{fill:"#D84A3A"})` at the target moment, or stay one color. (The draining-battery
  bug.)
- **Seek-safe only.** The renderer seeks frame-by-frame, so `tl.to(el,{textContent})` and
  `tl.call()` do NOT fire. Number rolls/counters MUST use a proxy obj + tween `onUpdate`
  writing textContent:
  ```
  const sc={v:3}; tl.to(sc,{v:5,duration:8,ease:"none",
    onUpdate:()=>{el.textContent=Math.round(sc.v);}}, at);
  ```
  Color / width / `attr:{}` / opacity / transform tweens ARE seek-safe.
- **SERIALIZE transitions.** Each scene fully EXITS (`opacity→0`) BEFORE the next ENTERS;
  leave a brief beat where only the bridging karaoke carries. Never cross-dissolve two busy
  hero-zone elements (Xiaolan rejected that as "not clean").
- **NO caption-only GAPS, and every beat is its OWN real scene.** Two Xiaolan rejections:
  (1) a ~4.8s span had karaoke but NO b-roll object up top → "这一块没有 B-roll 的动画." Cross-
  check the timeline for ANY gap between a `hide` and the next `show` and fill it (even short
  connective lines). (2) a beat was faked by re-`show`ing an earlier scene with parts opacity'd
  out → left an orphaned label floating (no object, no animation, and the label was nonsense
  over that caption). Every narration beat gets a dedicated `.scene` with a real animated
  object — never a leftover sub-element. Scan the cream-bg verify for any lone label floating.
- **Proper nouns often need a 2nd pass.** Xiaolan re-corrects names after review (Ravi→Riley
  Brown, Agent→Agentic Payment, 基木→积木, Superbase→Supabase, Mitro→Mitchell Hashimoto). A
  one-word karaoke fix in `_src/full.html` = a full re-render; batch them. Cross-check names
  against any on-screen text in her own A-roll screen-recs (the Lovable rec literally showed
  "Riley").
- **johnbucog CJK sizing:** 235px fits ~950px for 4 chars. Pure edge-bleed works for NUMBERS
  only — 4 CJK glyphs bled cut 先/碰 in half. Size to fit; slight bleed OK.
- **Local Noto Sans SC woff2 is subsetted** — missing some heavy CJK glyphs (个 → bogus ↑).
  The local Noto Serif SC subset has them. Render small CJK in the SERIF face, or verify
  every 字 in a frame.
- **Rotating an SVG element (clock hand, dial, etc.) around a point: use `svgOrigin:"x y"`
  (absolute SVG user-space coords), NOT `transformOrigin:"Npx Npx"`.** GSAP reads
  `transformOrigin` px relative to the ELEMENT'S bounding box, so a clock hand (a thin off-center
  `<line>`) pivots way outside the face and orbits/vanishes — looked broken until switched to
  `svgOrigin:"60 60"` (the viewBox center). 2026-06-18, the 花几倍时间 clock. (The template's
  deskSvg `clkH` rotation is fixed to `svgOrigin:"64 60"` as of 2026-07-01.)
- **`<body>` must never appear in a CSS/JS comment** (the linter regex-scans for the first
  `<body>` → false root errors). No `<br>` in content text.
- **Whisper vs script:** caption the ACTUAL VO; use the script only to fix proper nouns
  whisper mangled (names, product names, tech terms). Numbers/wording follow whisper unless
  Xiaolan says otherwise. A separate "opener" line in a script may belong to a different clip.
- **Lint warnings that are benign:** `composition_file_too_large`, `font_family_without_font_face`
  (CSS vars — the real @font-face is in fonts.css), `overlapping_gsap_tweens` on
  `__unresolved__`, `gsap_studio_edit_blocked`. 0 ERRORS is the bar.

## Embedding Xiaolan-supplied videos (real product demos / her own clips) — 2026-06-17
When Xiaolan hands you MP4s to drop into a scene (a tool's showreel, a phone with a clip, etc.):
- Each video is a `<video class="clip vvid" data-start="<comp s>" data-duration="<s>"
  data-media-start="<in-point s>" data-track-index="<unique N>" src="assets/clips/x.mp4" muted
  playsinline>` — a **DIRECT child of `#root`**, positioned with CSS (left/top/width/height +
  border-radius). Clip elements are timed by the data attrs, **NOT** the GSAP timeline. Root is
  track 0; give each video its **own** `data-track-index` (1,2,3…); same-track clips can't overlap.
- Pre-process each: `ffmpeg -i src.mp4 -an -vf scale=960:540 -r 30 assets/clips/x.mp4` — strip
  audio (the overlay ships `-an`), scale to the card size. Trim long clips with `-ss <in> -t <len>`
  so `data-media-start=0` maps to your in-point. (The 53s HeyGen reel → a 7.8s segment.)
- The logo chip / phone frame / label = a SEPARATE GSAP-toggled `.vchrome` div (opacity 0→1 at
  the scene window), absolutely positioned (logo chip at the top "red box", label below the video).
  For a PHONE mock (大佬头像 clip): a dark rounded `.phonebody` (z-index 15) BEHIND the video
  (z 16) + a `.phonenotch` (z 18) on top — all GSAP-opacity-toggled; the `<video>` inset inside
  the phone screen. Viewer sees her profile-pic clip playing in a phone.
- If a clip is SHORTER than its window it freezes on the last frame (set `data-duration` = window
  length; freeze is cleaner than the card going empty). Mixing clip videos + a registered
  `window.__timelines.main` GSAP timeline renders fine.
- **Videos enlarge the qtrle** (photographic regions don't RLE-compress): the 一键剪辑 build with
  4 embedded clips → **528MB** qtrle vs 345MB graphics-only. Still ships fine to CapCut.
