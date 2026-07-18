# 自制绿幕 b-roll 素材 — 用 Codex imagegen 出插画 cutout

**这是每一集的默认路径（小蓝，2026-07-06）。** 场景库（`scene-library.md`）是内联
**SVG 线稿** —— 快、确定性强，但冷。b-roll 做成**手绘插画 cutout** 观感温暖得多，
由 HyperFrames 用 **pose-swap（换姿势）** 驱动动画，而且小蓝要的就是插画质感：
纯 SVG 的 b-roll 轨道是已经被毙掉的方案。这套配方就是当年做出卡通片尾和
夜班内容生产线那几集的同一套。cutout 用 **Codex CLI imagegen**（GPT Image）生成，
由一份**素材清单文档（asset manifest）**来驱动。

## 哪些做 cutout、哪些留 SVG
- **默认：每个场景的 HERO 物体都做插画 cutout** —— 角色姿势（小蓝、机器人），
  以及旁白点名的独立物件：工具、硬币/筹码、门、建筑、手机、灯塔、公文包，
  各种道具。只要这个节拍的主角是一个画得出来的名词，它就是 cutout。
- 在很多节拍里反复出现的**角色或道具**（当"数字员工"的机器人、标志性道具）→
  走插画，为了一致性 —— 复用已锁定的设计。
- SVG 线稿（`scene-library.md`）只留给天生就属于图形层的东西：计数器、终端/UI
  mockup、% donut、示意图、箭头/连接线、小芯片卡/label、loop ⟳ motif、字幕点缀 ——
  符号讲得更清楚的别硬画插画，插画讲得更温暖的也别硬用符号。
- **两层在同一条视频里叠加：插画 hero + 实时 SVG UI/动效点缀。**

## 先复用 —— 库里很可能已经有现成的 cutout
生成任何东西之前，先 list 一遍你自己的绿幕素材库文件夹。做过几集之后，里面应该
已经攒下干净的 **RGBA** cutout，比如：小蓝姿势（`xiaolan-idle/point/present/think/press/
night-type/review-tablet/sleep/stretch-wake`）、机器人姿势（`robot-idle/clipboard/magnifier/
stamp/receive/deliver/talk/type/walk-A/walk-B/headphones`）、几十个道具（`prop-laptop/
folder-doc/shared-list/desk-monitor/brand-kit/coffee-mug/whiteboard/video-clip-card/…`）。
**清单里每一行都标 ✅ 复用 或 🆕 生成；只生成 🆕 的。** 重新生成一个已有姿势不但
白烧约 95k token，还会让设计从已锁定的角色上漂走。

## 素材清单文档（照着脚本写）
给每一集写一份 `assets-EP-<slug>.md`，放进你自己的素材清单文档目录 —— 第一集
验证过之后，就拿它当后续每集的模板。分这几部分：
1. **画幅与布局** —— 1080×1920；卡通舞台放在画面上部区域（避开出镜人压得比较低的
   头部）；平铺奶油色 `#F5EFE2` 背景由 HyperFrames 实时填充，**不要生成背景**。
2. **动效原理 —— pose-swap 分档**（先读这条）：Tier 0 = 单张 cutout（我整体移动它）；
   Tier 1 = 2 姿势手势组（crossfade）；Tier 2 = 2-3 姿势循环（走路）。成败全在
   **registration（对位）** —— 会一起做动画的几帧之间，格子尺寸、角色身高、脚底/
   基线 Y、镜头、光线、线条粗细、配色、发型必须完全一致；只有在动的那条肢体
   可以变，否则一换就"跳"。
3. **锁定设计** —— 角色 + 色板，"匹配现有 cutout，不要重新设计。"小蓝：棕色长卷发、
   克莱因蓝拉链连帽衫、白 T、浅蓝卷边牛仔裤、白球鞋。机器人：圆润白色机身、
   克莱因蓝眼睛/天线/关节，全片只有一个机器人 —— 角色身份 = 它手里拿的道具。
   色板：克莱因蓝 `#002FA7`、深蓝 `#001A5E`、薄荷绿 `#8ACAB1`、奶油色 `#F5EFE2`、
   炭黑 `#1F1F1D`、红 `#D84A3A`（只用于警示）。手绘线条，不要 SVG 扁平风 / 3D / 霓虹。
4. **购物清单** —— 按组分的 sprite sheet（小蓝姿势 · 机器人姿势 · 道具），
   每行 = 文件 / 姿势 / tier / ✅|🆕 / 用在哪。
5. **场景 → 素材覆盖表** —— 每个节拍都映射到角色+道具；每个 🆕 素材至少用 1 次。
6. **生成 prompt 模板**（每张 sheet 一份）—— 见下文。
7. **交付回传** —— `<sheet>-green.png` + `<sheet>-alpha.png` + 切好的单个 cutout +
   一张 contact sheet；丢进共享的 `assets/`。**道具自动过审（小蓝，2026-07-06）：**
   自查 contact sheet（风格匹配、registration、边缘 fringe、禁区项），然后直接进搭建 ——
   不设人工关卡。交付报告里附上 contact sheet，方便小蓝事后发现走形、下令重画。
8. **实时搭建的部分（不要生成）：** 所有文字/字幕、箭头/连接线、对话气泡、✓ 勾、
   计数器/donut、高亮扫光、光晕 —— 这些统统由 HyperFrames 渲染。

## 生成 prompt（每张 sheet）
```
A sprite sheet of ONE character in [N] labeled poses in a clean grid.
Hand-drawn cartoon illustration, soft fill + ink line. Flat chroma-green #00B140 behind every
pose (for clean cutout). No ground shadow, no text labels, no background scene.
Character (IDENTICAL across poses — match the attached reference EXACTLY): [design].
Poses (same height, same foot baseline, same camera, same light, ONLY the limb changes):
  1.[pose] 2.[pose] 3.[pose] …
Palette: Klein #002FA7, deep #001A5E shadow, mint #8ACAB1, charcoal ink. Each pose ≥1000px tall.
```
道具 sheet 用："objects on flat green, hand-drawn to match the cast line, no text."
（平铺绿底上的物件，手绘风匹配角色线条，不带文字。）把现有 cutout 作为
**参考图**附上（明确让 Codex 去读它们并对齐），新画的才贴得住锁定设计。

## 跑 Codex imagegen（无头模式，已确认可用）
Codex 桌面版的可执行文件可能**不在 PATH 里**（`which codex` 失败不代表没装 ——
去安装目录里把它找出来）。它既有文件访问也有 GPT-Image 生成能力。每张 sheet 调一次：
```
codex exec --skip-git-repo-check \
  -C "<assets-dir>" "<prompt: READ ref PNGs X,Y; generate sheet Z on green; cut each pose to a
  named RGBA cutout; write a contact sheet>" < /dev/null
```
- `--skip-git-repo-check` 必加，只要不在受信任/git 目录里（否则报 "Not inside a trusted
  directory"）。
- `< /dev/null` 必加 —— `codex exec` 会读 stdin；非 tty 的管道永远不会 EOF → 卡死在
  0% CPU，永远挂着。（这个坑值得记进你自己的决策日志，别踩第二次。）
- 配置要设成 `approval=never`、`sandbox=danger-full-access`，模型 `gpt-5.5` → 可以
  无人值守跑，每张图约 1-2 分钟 + 约 95k token。产物同时会落一份在
  `~/.codex/generated_images/`。
- **先用一张 sheet 把整条管线验证通了，再跑全量批次**（这些二进制会漂移；5 天前的
  记忆不等于当前的实际状态）。验证过了再生成剩下的。

## 抠像 + QC
- 如果 Codex 交回来的是平铺绿底 sheet（不带 alpha），自己 key：`ffmpeg -i sheet-green.png -vf
  "chromakey=0x00B140:0.30:0.10,despill" sheet-alpha.png`（similarity/blend 照发丝边缘微调），
  再逐格裁切。最省事的情况是 Codex 直接输出切好的 RGBA cutout。
- **拼一张 contact sheet，用眼睛看**有没有 registration 漂移（脚不落在同一条 Y 上、
  身高抖动、姿势之间发型/颜色变了、烤死在图里的阴影/文字）。锁定节拍时间之前
  报给小蓝签字确认 —— 一对会漂的 swap 姿势能毁掉整段动画。

## 在 HyperFrames 里用 cutout
每个 cutout 就是一个 `<img class="cut" src="assets/<name>.png">`，摆进 b-roll 区域，
由 timeline 的 `show/hide` helper 控制出现；**pose swap** = 同一角色的两张 cutout 在
同一 x/基线上 crossfade（Tier 1），**走路** = walk-A/walk-B 交替 + x 位移（Tier 2）。
cutout 的镜像坑：`robot-walk-A`/`-B` 是水平**镜像**（A 朝左、B 朝右）—— 镜像对
绝不能当走路循环来交替；改用单一朝向的姿势 + 垂直 bob（这条修复记在你自己的
决策日志里，出处是卡通片尾那一集）。
