# Build recipe — 小蓝整片 b-roll（配图动画层）+ 卡拉OK透明叠加层

## 架构（验证过的模式）
- **不放底层视频/音频。** 产出是透明叠加层；她的 A-roll 是之后压在它**下面**的。
  所以合成里只有图形 + 字幕，站在一个透明舞台上。
  ```
  html,body{ background:transparent; }
  .stage{ background:transparent; }          /* root data-composition-id, full duration */
  ```
  `data-duration` 设成 A-roll 的时长（如 166.9）。不放 `<video>`/`<audio>` clip。
- **三层，全在 root 里，靠 z-index 分：**
  - `.broll`（z 15，top:248 height:520）— object-first 主角场景，每个 `.scene`
    `opacity:0`，由 timeline 控制显隐。
  - `.kband`（z 20）— 逐词弹出卡拉OK，行由 JS 注入。位置按**实测**头顶来定：
    带底边在头顶上方 ~35–50px（如头顶 y1088 → `top:935 height:115`）——小蓝
    2026-06-17 的规矩；模板里的 `top:800` 只是占位。
  - `.jb`（z 25，top:382 height:440）— johnbucog 金句带（每个金句一条），`opacity:0`。
- **一条暂停的 GSAP timeline** 注册在 `window.__timelines["main"]`。必须完全确定性
  （不许 Math.random / Date.now）。所有 DOM + tween 在脚本加载时同步建好。

## 检查 A-roll 里有没有已经烧好的 b-roll（Inspect 阶段做）
有些 A-roll 是半成品，某些节拍的顶区已经烧进去了录屏/切镜。contact sheet 要横跨
**全片**抽帧（约每 10s 一张），别只看几帧。顶区已被占的时间窗，你的叠加层在那一段
**顶区留空**（卡拉OK照走，不放图形），免得撞车。注意：`measure-head.py` 会把烧进
去的内容误判成很高的"头"——肉眼看帧，别信孤零零的离群值。

## 分区表（1080×1920，奶油底抠像，头顶 ≈ y988——但永远要实测）
| 层 | y 范围 | 说明 |
|---|---|---|
| 顶部平台 UI 区 | 0–230 | 关键内容避开 |
| b-roll 主角区（`.broll`） | 248–768 | 一个具体物件 + ≤6 词标签 |
| johnbucog 金句（`.jb`） | 382–822 | 金句节拍时顶替 b-roll |
| 卡拉OK带（`.kband`） | 头顶 −150 → −35 | 贴在头顶上方，留 ~35–50px 缝（如头顶 y1088 → 935–1050）；同时把 `.broll` 下移填中段 |
| 她的抠像 | 988+ | 这里不放任何要读的东西 |
左右边缘各留 ≥100px 空白（平台会裁竖屏边）。

## 透明 MOV 管线（交付物）
- 渲染：`npx hyperframes render --format mov -o renders/<name>-overlay.mov`
  → ProRes 4444，`pix_fmt=yuva444p12le`（**有** alpha）。这是**存档母版**；留在
  `renders/`，不要拿去交付。~2:47 大约 1GB——这个体积是**编码**造成的
  （近无损帧内压缩 + 12-bit alpha ≈ 700–900 Mbps），跟分辨率无关。压缩动不到 1080p。
- **hyperframes 的 `--format webm` 把 alpha 拍平成了 `yuv420p`——做透明别用它。**
- **交付一个压缩过的 alpha `.mov`——把 ProRes 母版转成 `qtrle`（小蓝拍板的方案）。**
  QuickTime Animation (RLE) 是**无损**的，保住 1080×1920 + alpha（argb），后缀还是
  `.mov`，所以 CapCut 导入方式完全不变（不用重新 relink），而且**小约 6 倍**
  （1GB → ~170MB），因为透明底上的平涂色图形用 RLE 压缩效果极好：
  ```
  ffmpeg -i renders/<name>-overlay.mov -c:v qtrle -pix_fmt argb -an renders/<name>-qtrle.mov
  ```
  qtrle `.mov` 按交付名发出去；ProRes 留作存档母版。
  （PNG-in-mov `-c:v png -pix_fmt rgba` 也无损，但体积约是 qtrle 的 2 倍。）
- **最小的是 VP9 alpha webm（~12MB），但有损 + CapCut 有风险。** `ffmpeg -i master.mov
  -c:v libvpx-vp9 -pix_fmt yuva420p -auto-alt-ref 0 -row-mt 1 -an out.webm`。ffmpeg 把
  alpha 存在 `alpha_mode=1` 侧通道里——`ffprobe` 主平面显示 `yuv420p`，但 alpha
  其实在；想解码/验证它，必须在**输入端**强制 `-c:v libvpx-vp9`（默认的 vp9 解码器
  忽略 alpha → 透明区域渲成黑色，纯属虚惊）。有些 CapCut 版本导入时会把 webm 的
  alpha 拍平——只有小蓝明确接受这个风险才提供这条路。
- 叠在她的真 A-roll 上验证 alpha（单帧）：
  ```
  ffmpeg -ss <t> -i aroll.mp4 -ss <t> -i <overlay> \
    -filter_complex "[0:v][1:v]overlay=format=auto" -frames:v 1 chk.jpg
  ```

## 验证循环（奶油底代理——又快又准）
炭黑卡拉OK在透明/黑底 draft 上是隐形的。她的背景**就是**奶油色，而且所有图形都在
顶区，所以奶油底 draft 就是一份忠实预览：
```
sed 's/background:transparent/background:#F5EFE2/g' _src/full.html > index.html
npx hyperframes render --quality draft -o renders/verify.mp4
# one frame per section:
ffmpeg -ss <t> -i renders/verify.mp4 -frames:v 1 -q:v 3 verify/<sec>.jpg
```
每个 section 的帧都要 LOOK。检查：可读性、头部/边缘净空、字形正确性、颜色纪律
（无紫、红 ≤3 次）、转场干净度。在 `_src/full.html` 里改，重渲。奶油底代理全部
干净了，才去渲真正的透明 MOV。

## 渲染耗时（这台机器，6 个 worker）
- ~167s 的 draft mp4 ≈ 1m53s。ProRes MOV ≈ ~8min + ~1GB。在 draft 上迭代，MOV 只渲一次。

## 坑（别再踩）
- **绝不把克莱因蓝 (#002FA7) 直接 tween 到 Risk Red (#D84A3A)**——RGB 插值在中点
  会路过紫色（风格禁区的封禁色）。到点用 `tl.set(el,{fill:"#D84A3A"})` 直接切，
  或者干脆全程一个色。（掉电电池那次的 bug。）
- **只写 seek-safe。** 渲染器是逐帧 seek 的，所以 `tl.to(el,{textContent})` 和
  `tl.call()` 根本不会触发。数字滚动/计数器必须用代理对象 + tween 的 `onUpdate`
  去写 textContent：
  ```
  const sc={v:3}; tl.to(sc,{v:5,duration:8,ease:"none",
    onUpdate:()=>{el.textContent=Math.round(sc.v);}}, at);
  ```
  颜色 / 宽度 / `attr:{}` / opacity / transform 这些 tween 是 seek-safe 的。
- **转场串行。** 每个场景完全**退场**（`opacity→0`）之后，下一个才能**进场**；
  中间留一小拍，只靠承上启下的卡拉OK撑着。绝不让两个繁忙的主区元素交叉溶解
  （小蓝打回过，评价是"不干净"）。
- **不许出现"只有字幕"的空窗，而且每个节拍都得有自己真正的场景。** 小蓝打回过
  两次：(1) 有个约 4.8s 的段落只有卡拉OK、顶上没有 b-roll 物件 → "这一块没有
  B-roll 的动画。" 排查 timeline 上任何一个 `hide` 到下一个 `show` 之间的空窗并
  填上（哪怕填个很短的衔接场景）。(2) 有个节拍是把早前的场景重新 `show` 一遍、
  再把一部分元素 opacity 掉来凑数 → 结果留下一个孤零零漂着的标签（没物件、
  没动画，而且那个标签配那句字幕完全是胡话）。每个叙事节拍都要有专属的 `.scene`
  和真正会动的物件——绝不拿残余的子元素凑数。奶油底自检时扫一遍有没有孤立漂浮
  的标签。
- **专有名词经常要过第二遍。** 小蓝 review 之后会再改名（Ravi→Riley Brown、
  Agent→Agentic Payment、基木→积木、Superbase→Supabase、Mitro→Mitchell Hashimoto）。
  在 `_src/full.html` 里改一个词 = 整片重渲；所以攒一批一起改。名字要跟她 A-roll
  录屏里的屏幕文字交叉核对（Lovable 那段录屏画面里明晃晃写着 "Riley"）。
- **johnbucog CJK 字号：** 235px 时 4 个字约占 950px。纯出血只对**数字**成立——
  4 个 CJK 字出血，把 先/碰 切了一半。缩放到放得下；轻微出血 OK。
- **本地 Noto Sans SC woff2 是子集化的**——缺一些 heavy CJK 字形（个 → 变成
  莫名其妙的 ↑）。本地 Noto Serif SC 子集里反而有。小号 CJK 用衬线（SERIF）字体
  渲，或者逐字在帧里核对。
- **SVG 元素绕某个点旋转（表针、旋钮之类）：用 `svgOrigin:"x y"`（SVG 用户空间的
  绝对坐标），不是 `transformOrigin:"Npx Npx"`。** GSAP 把 `transformOrigin` 的 px
  当成相对元素自身 bounding box 的坐标，所以一根表针（细长且偏心的 `<line>`）会绕
  到表盘外面公转/直接消失——一直像坏了一样，换成 `svgOrigin:"60 60"`（viewBox 中心）
  才正常。2026-06-18，"花几倍时间"那个钟。（模板里 deskSvg 的 `clkH` 旋转已于
  2026-07-01 修正为 `svgOrigin:"64 60"`。）
- **CSS/JS 注释里绝不能出现 `<body>`**（linter 用正则扫第一个 `<body>` → 误报 root
  错误）。内容文字里不要用 `<br>`。
- **Whisper vs 脚本：** 字幕以**实际 VO** 为准；脚本只用来修 whisper 打错的专有
  名词（人名、产品名、技术词）。数字/措辞跟 whisper 走，除非小蓝另有说法。
  脚本里单独的一句"opener"可能属于另一个片段。
- **无害的 lint warning：** `composition_file_too_large`、`font_family_without_font_face`
  （CSS 变量——真正的 @font-face 在 fonts.css 里）、`__unresolved__` 上的
  `overlapping_gsap_tweens`、`gsap_studio_edit_blocked`。标准是 0 ERRORS。

## 嵌入小蓝提供的视频（真实产品 demo / 她自己的片段）— 2026-06-17
小蓝递给你几个 MP4 让放进场景（某工具的 showreel、手机里播一段之类）时：
- 每个视频是一个 `<video class="clip vvid" data-start="<comp s>" data-duration="<s>"
  data-media-start="<in-point s>" data-track-index="<unique N>" src="assets/clips/x.mp4" muted
  playsinline>` —— **`#root` 的直接子元素**，用 CSS 定位（left/top/width/height +
  border-radius）。clip 元素的时序由 data 属性决定，**不走** GSAP timeline。root 是
  track 0；每个视频给一个**独立的** `data-track-index`（1,2,3…）；同一 track 上的
  clip 不能重叠。
- 每个都先预处理：`ffmpeg -i src.mp4 -an -vf scale=960:540 -r 30 assets/clips/x.mp4`
  ——去掉音频（叠加层本来就 `-an` 交付），缩放到卡片尺寸。长片段用 `-ss <in> -t <len>`
  先剪好，让 `data-media-start=0` 正好对上你的入点。（53s 的 HeyGen reel → 7.8s 片段。）
- Logo chip / 手机边框 / 标签 = 一个**独立的**、由 GSAP 控制显隐的 `.vchrome` div
  （在场景窗口内 opacity 0→1），绝对定位（logo chip 放顶部"红框"位，标签放视频
  下方）。手机 mock（大佬头像那个片段）：深色圆角 `.phonebody`（z-index 15）垫在
  视频（z 16）后面 + `.phonenotch`（z 18）盖在最上——全部走 GSAP opacity 控制；
  `<video>` 内嵌在手机屏幕里。观众看到的效果就是她的头像片段在一部手机里播放。
- clip 比它的时间窗短时会定格在最后一帧（把 `data-duration` 设成窗口长度；定格比
  卡片突然变空干净）。clip 视频 + 注册好的 `window.__timelines.main` GSAP timeline
  混用，渲染没有问题。
- **嵌视频会把 qtrle 撑大**（摄影类画面 RLE 压不动）：一键剪辑那集嵌了 4 段视频 →
  qtrle **528MB**，纯图形版只有 345MB。照样能顺利发进 CapCut。
