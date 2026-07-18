---
name: xiaolan-broll
description: >-
  把一条完整长度的小蓝口播视频做成品牌锁定的 b-roll（配图动画层）+
  逐词弹出卡拉OK字幕层，以透明叠加层（带 alpha 的 ProRes MOV）交付，
  由小蓝自己叠在她的高清 A-roll 上——A-roll 永远不烧进成片。
  适用于 cream（奶油底）+ cutout（绿幕抠像素材）的 9:16 竖屏：
  人物坐在画面中下方，上半屏是空的。产出 object-first 的 b-roll
  （每个叙事节拍一个具体的动画物件，循环 glyph 母题）、锁 VO 的逐词弹出卡拉OK
  （当前词 Klein blue（克莱因蓝）+ 薄荷绿下划线），johnbucog 巨字主角处理只留给金句。
  触发场景："make b-roll and karaoke captions for this video / a-roll"、
  "整条视频的 b-roll 和字幕"、"口播配图"、"full b-roll"、
  "动图 + 字幕 for my talking head"、"transparent overlay I'll composite myself"，
  或给一整条小蓝讲解视频加/重做图形+字幕。
  覆盖 VO 转写、头顶测量、分段/金句规划、卡拉OK引擎、object-first 场景搭建、
  自检、透明 MOV 渲染和交付。
  不适用于：字幕直接烧在片段上的短 hook/开场（用 `xiaolan-hook-broll`，
  未包含在本仓库），也不适用于人物在右下角的口播（用 `shorts-hyperframe`，
  未包含在本仓库）。
---

# xiaolan-broll

给一条完整长度的小蓝口播视频搭 **b-roll + 卡拉OK字幕层**，以**透明叠加层**交付，
小蓝自己把它压在她的 A-roll 上面。`agentloop-broll-overlay.mov`
（2:47 的 Agent Loop 讲解片）就是这套流程做出来的。

版式是**奶油底 + 人物抠像、人物在中下、上半屏整片空白奶油色**——你的图形和字幕
全部住在那块空的顶区，绝不能碰到她的抠像，也不能出裁切后的竖屏边缘。

## 跟隔壁 skill 的区别（先选对工具）
- **`xiaolan-broll`（本篇）** — 整条视频。全程 b-roll + 逐词弹出卡拉OK，johnbucog
  只用在金句。产出 = **透明 MOV**（带 alpha），A-roll 不烧进去。人物抠像在中下。
- **`xiaolan-hook-broll`（未包含在本仓库）** — 短开场/hook。动态字幕直接**烧**在
  片段上（含她画面的 MP4）。johnbucog 或 editorial 风格，每一拍都上。
- **`shorts-hyperframe`（未包含在本仓库）** — 人物在**右下角**的口播配图。

## 开工前必读（权威文档，按顺序）
1. 品牌规范（压倒一切）：你自己的品牌规范文档（配色/字体/object-first 规则——
   本文件的"死规矩"一节已把核心讲全）。
2. 你自己的决策日志/错题本——所有用血泪换来的坑都该记在那里，开工前翻一遍。
3. `references/build-recipe.md` — 架构、完整工作流、透明 MOV 管线、全部坑点。
4. `references/karaoke-engine.md` — 逐词弹出引擎、`w`/`u` 短语格式、自动缩放。
5. `references/scene-library.md` — object-first b-roll 场景库（能复用就复用，别重新发明）。
6. `references/asset-generation.md` — 当一个节拍是"一组角色演故事"（小蓝 + 她的机器人
   摆姿势、招牌道具）而不是抽象/UI 概念时，用 **Codex imagegen**（由素材清单文档驱动）
   生成插画风绿幕 cutout，而不是画 SVG 线稿。
7. `references/jinju-lottie.md` — 金句的第二套打法：Lottie 描边-填色-定格
   （克莱因蓝描边画出 → 墨色填实 → 克莱因蓝 punch 定格；不许用红——小蓝
   2026-07-01），用于警告/规则/铺垫型金句；震撼节拍默认还是 GSAP johnbucog 砸字。

## 死规矩
- **透明叠加层，A-roll 永远不烧进去（小蓝的规矩）。** 合成背景
  `transparent`；不放底层 `<video>`/`<audio>`。渲染 `--format mov` → ProRes 4444
  `yuva444p12le`（带 alpha）。`--format webm` 出来是 `yuv420p`（没有 alpha）——别信它。
- **字幕锁 VO，按说话停顿分行。** 转写真实音频（faster-whisper）。字幕写她实际
  说出来的话；脚本只用来修 whisper 打错的专有名词。短语级逐词弹出，绝不自由漂浮。
  **一次停顿一短行——她一停顿，就起新的一行。`PH` 数组从 whisper 的 SEGMENTS
  一比一构建（超过约 13字 的 segment 要拆）；绝不把几个 segment 合并成一条会自动
  缩小的长行。字号必须保持大。** 如果 b-roll 画面已经把某个词表达出来了，字幕里就
  把它删掉（比如 before→after 画面已经承载了"从这样"——别再写进字幕）。
  （小蓝，2026-06-17）
- **奶油底上的品牌锁：** 炭黑 / 克莱因蓝 / Risk Red 三色文字，思源宋体 Heavy 做大字。
  **白字禁用**（奶油底上看不见）。Risk Red 全片 ≤3 次——留给那个震撼金句。
- **巨字主角处理只给金句。** 其余全是卡拉OK + object-first b-roll。两套打法
  （register），按金句语义选：GSAP **johnbucog 砸字**（默认——震撼节拍、数字）
  或 **Lottie 描边-填色-定格**（警告/规则/铺垫——`references/jinju-lottie.md`）。
  无论哪套：CJK 按放得进 ~950px 的字号来缩（纯出血只给数字），一个金句绝不同时上两套。
- **让开头部。** 先测头顶（`assets/measure-head.py`）；所有图形都住在头顶以上的
  顶区。b-roll 约 y248–768，johnbucog 带约 y382–822。
- **卡拉OK字幕带贴在她头顶正上方（留 ~35–50px 缝），不许浮在半空。** 小蓝的规矩
  （2026-06-17）：字幕要贴着头——b-roll 和字幕之间不能空一大块。默认的 y800–950
  浮得太高。头顶低的时候（比如实测 y1088），字幕带底边放到 ~y1050（带
  `top:935 height:115`）。然后**把 b-roll 物件整体下移去填空出来的中段**（比如
  `.broll top:300`），免得物件场景头重脚轻。这就是她版式 mockup 里的"绿框"位。
- **Object-first，插画优先（小蓝，2026-07-06）。** 每个场景的主角都必须是一个
  具体的动画物件，绝不是文本框——而且默认这个物件是**插画风绿幕 cutout**
  （Codex imagegen，见步骤 5b），不是 SVG 线稿。SVG 只留给天生就是图形的东西：
  计数器、终端/UI mockup、环形图/图表、箭头、chip/标签、复用的**循环 ⟳ glyph**
  母题、字幕点缀。只要场景主角是个"东西"（工具、硬币、门、楼、手机、灯塔……），
  就该上 cutout。交出一条全是 SVG 的 b-roll 轨是被打回过的模式。物件旁的标签
  ≤6 个词。
- **交付前每个 section 逐帧自检。** 小蓝期待你自己把丑的地方揪出来。

## 工作流
1. **搭架子** `<你的工作目录>/<项目名>-broll/`：从之前的项目复制 `fonts/` 目录
   （本地 Noto Serif/Sans SC woff2 + `fonts.css`）和 `hyperframes.json` /
   `meta.json` / `package.json`。`index.html` 从 `assets/full-template.html` 起手。
2. **检查 A-roll**（`ffprobe` + 一张 contact sheet 抽帧总览图）：确认 9:16
   奶油底抠像、人物中下、上半屏空、没有预先烧进去的文字。
3. **转写 VO** → 逐词时间戳 + 可读文稿：`assets/transcribe.py`
   （faster-whisper medium，`--language zh`，word_timestamps，int8 CPU，
   `PYTHONIOENCODING=utf-8`）。
4. **测头顶：** `python assets/measure-head.py <aroll.mp4> <t0 t1 …>`。要确认
   **整条片**的天花板（抠像会飘）；据此定各条带的 top。
5. **规划** section map：每个叙事节拍配一个 object-first b-roll 场景 + 卡拉OK
   短语窗口 + 哪些行是金句，以及每个金句用哪套——johnbucog 砸字还是 Lottie
   描边-填色-定格（`references/jinju-lottie.md`）。金句清单、打法、范围先跟小蓝
   确认；长视频先做一小段 PROOF（开场 hook + 结尾金句），拿到 look 认可再全量渲染。
5b. **生成绿幕道具——强制，每集都做**（小蓝，2026-07-06——这一步之前老被跳过；
   以后绝不再跳）。见 `references/asset-generation.md`。步骤 5 的 section map 里
   每个场景主角都要有插画 cutout，除非它是纯 UI/计数器/排版类：(a) **先复用**——
   先翻一遍你自己的绿幕素材库文件夹（没有就先建一个；每次生成的 cutout 都归档
   进去，库会越攒越厚——复用永远排在新画前面）；(b) 写一份素材清单文档：每个
   场景主角一行，标 ✅复用 / 🆕新画；(c) 🆕 的行用 Codex imagegen 生成
   （`codex exec --skip-git-repo-check -C <assets>
   "…green sprite sheet, cut cutouts…" < /dev/null`——先验证一张 sheet 再批量）；
   (d) 抠绿 → 裁切 → contact sheet → **自查并自动放行**（小蓝，2026-07-06：道具
   不设人工关卡——contact sheet 你自己 LOOK：跟素材库的风格是否统一、
   registration（对位）是否准、无绿边/文字/红/紫；不合格的重新生成；contact sheet
   附进交付报告，方便小蓝事后抽查风格漂移）。SVG 仍然只留给计数器/终端/环形图/
   箭头/chip/循环 glyph/字幕点缀。清单里的 cutout 没落盘之前，步骤 6 不许开始写场景。
6. **搭建** `index.html`：贴入卡拉OK `PH` 数组（锁 VO），编写/克隆 object-first
   场景（`references/scene-library.md`），放置金句节拍（johnbucog div；Lottie 版
   金句用 `assets/glyph2lottie.py` + `assets/build-jinju-lottie.py --start <comp-sec>`
   构建素材，播放器注册到 `window.__hfLottie`）。一条暂停的 timeline 注册在
   `window.__timelines["main"]`。转场必须串行。
7. **Lint** `npx hyperframes lint` → 0 errors。（`composition_file_too_large`、
   CSS-var-font、overlapping-tween、gsap-studio 这几类 warning 无害。）
8. **自检（强制，奶油底代理）。** 她的背景就是奶油色，所以奶油底 draft 既是顶区的
   忠实预览，又能让炭黑卡拉OK显形（在透明/黑底 draft 上根本看不见）：
   `sed 's/background:transparent/background:#F5EFE2/g' _src/full.html > index.html`，
   `npx hyperframes render --quality draft -o renders/verify.mp4`，每个 section
   抽一帧（`ffmpeg -ss <t> -frames:v 1`），一张一张地 LOOK，修，再来一轮。
9. **正式渲染**真正的透明版本：`npx hyperframes render --format mov -o
   renders/<name>-overlay.mov`。叠在她的真 A-roll 上抽帧验证：
   `ffmpeg -ss <t> -i aroll.mp4 -ss <t> -i overlay.mov -filter_complex "[0:v][1:v]overlay=format=auto" -frames:v 1 chk.jpg`。
10. **先压缩，再交付。** ProRes 母版约 1GB（是编码的锅，不是分辨率）。转成
    **无损**的 `qtrle` `.mov`（同样 1080p + alpha，仍是 `.mov`，小约 6 倍）：
    `ffmpeg -i renders/<name>-overlay.mov -c:v qtrle -pix_fmt argb -an renders/<name>-qtrle.mov`。
    把 **qtrle `.mov`** 按交付名放进你的素材文件夹；ProRes 母版留在
    `<你的工作目录>/<项目名>/renders/`。别烧、别覆盖她的 A-roll。
    （细节 + webm 选项见 `build-recipe.md`。）
11. **记录：** 把本次的技巧/决策记进你自己的决策日志/错题本；有东西被打回的话，
    单独记一条，写清是什么、为什么被打回。

## 最容易咬人的坑（完整清单见 build-recipe.md）
- **绝不从克莱因蓝 tween 到 Risk Red**（RGB 插值中途会路过被禁的紫色）——
  用 `tl.set` 直接切。
- **只写 seek-safe 的动画：** `tl.to({textContent})` / `tl.call()` 在逐帧 seek 时
  不会触发——数字滚动/计数器必须用代理对象 + tween 的 `onUpdate` 去写 textContent。
- **每行卡拉OK自动缩放到 ≤905px**（量 scrollWidth → scale），否则会出裁切边。
  金句 CJK 大字：缩放到放得下，别纯出血（会把字切一半）。
- **场景转场必须串行**——上一个场景完全退场，下一个才能进；绝不让两个繁忙的
  主区元素交叉溶解（小蓝打回过，评价是"不干净"）。
- **本地 Noto Sans SC woff2 是子集化的**——部分 heavy CJK 字形缺失（个→↑）。
  帧里逐字核对，或者小号 CJK 用衬线（SERIF）字体渲。

## Assets
- `assets/full-template.html` — 验证过的整片模板（卡拉OK引擎 + 辅助函数 +
  object-first 场景库 + 4 个 johnbucog 节拍）。克隆后换内容。
- `assets/transcribe.py` — faster-whisper → 逐词 JSON + 可读文稿。
- `assets/measure-head.py` — 跨节拍的头顶测量。
- `assets/glyph2lottie.py` + `assets/build-jinju-lottie.py` — Lottie 金句通道：
  思源宋体 Heavy 字形轮廓 → 描边-填色-定格 Lottie（`references/jinju-lottie.md`）。
- （字体 + Cormorant woff2：从你之前项目的 `fonts/` 目录复制。）
- `references/asset-generation.md` — Codex imagegen 插画绿幕 cutout 配方；配套
  写一份素材清单文档（每个场景主角一行，标 ✅复用 / 🆕新画）；共享 cutout 库
  就是你自己的绿幕素材库文件夹（先复用，再生成）。
