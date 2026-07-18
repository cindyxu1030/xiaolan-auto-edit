# 物体优先的 b-roll 场景库

每个场景的主角都是一个**具体的、会动的物体**（品牌视觉规范里的「物体优先」规则），
绝不能是文字框。一个场景只做一个视觉动词；旁边配一个 ≤6 个字的 `.label`。**loop ⟳
符号是贯穿全片的 motif** —— 反复复用它来保持整体感。所有场景都是内联 `<svg>` 线稿
（stroke 约为 viewBox 的 3–4%，圆头端点），走品牌色板，由共享的 timeline helper
（`show/hide/breathe/spin/drawOn/pop/counter`）驱动动画。以下所有场景的完整可用代码
都在 `assets/full-template.html` —— 挑最接近的那个克隆一份，换掉内容就行。

## 品牌色板（锁死）
```
cream #F5EFE2  panel #FBF7EE  ink #1F1F1D  klein #002FA7  deep #001A5E
mint #8ACAB1   mintdeep #4E9278  gray #5A5A56  rail #C9BFA6  red #D84A3A (≤3/video)
```

## 模板里现成的场景（直接复用）
| 场景 | 物体 | 动词 / 动效 |
|---|---|---|
| 编辑器卡片 | 类 macOS 面板、红绿灯圆点、等宽字体 prompt 行 | prompt 打字出现 → 红色删除线（划掉） |
| loop 符号 | 克莱因蓝圆形箭头 ⟳ + 箭头头部 | draw-on（stroke-dashoffset）+ 旋转；全片 motif |
| 燃烧的 ¥ | 印着 ¥ 的钞票 + 两簇火苗 | 确定性的火苗抖动（keyframe 的 x/scaleY） |
| 实习生@工位 | 笔记本前的小人 + 月牙 + 时钟 | 笔记本屏幕光晕呼吸、月亮升起、时针扫过（一整夜） |
| 两件事 | 闪电（触发）+ 靶心（目标），中间一个"+" | 各自弹入（back.out） |
| 触发三件套 | 事件节点 · 时钟 · 光标点击 | 依次弹入，一类一个 |
| 测试面板 | 带行的卡片 + 绿色 ✓ 圆圈 | 各行从左到右依次打勾（机器判断） |
| cron-vs-loop | 打红色 ✗ 的时钟 vs 挂着"?"的 loop | 停止标志出现；loop 旋转（自问达标没） |
| 掉电电池 | 电池轮廓 + 克莱因蓝填充 + $$$ | 填充宽度往下掉；**耗空瞬间填充 snap 变红（绝不能 tween！）** |
| review 转盘 | loop ⟳ + 分数 N/5 + 关卡 | 分数滚动 3→5（onUpdate），轮次 1/5→5/5，到 5 分关卡 ✓ 画出 |
| 实验 | 大计数器 + 迷你折线图 | 计数器 0→700（onUpdate），折线 draw-on |
| 大代码块 | 代码行卡片 + 放大镜 | 抖动（1000+ 行 too big，永远到不了 5 分） |
| to-do 关卡 | 待办卡片 + 90% ✓ 徽章 | 徽章弹入，下一行解除置灰 |
| 命中靶心 | 靶心 + 飞入的箭 + 薄荷绿 ✓ | 箭飞向靶心，✓ 弹出（有标准答案） |
| human-in-loop | 圆心有小人的 loop ⟳ + 薄荷绿 ✓ | 圆圈画出，圆点绕圈，小人弹入 |
| 检查点轨道 | 轨道 + 小人检查点 + 被拦住的"下一步"节点 | 克莱因蓝 token 驶入，红 ✗，弧线把它送回去（回去重改） |
| 关注 CTA | 克莱因蓝关注按钮 + 文档图标 | 按钮弹入 + 脉冲，文档滑入 |
| **logo 芯片卡** | 真实品牌 logo（品牌色）放在柔白/panel 圆角卡里 + 思源黑体名称 | 卡片弹入（back.out），薄荷绿下划线画出 |

## 密度 — 每个句子一个动画节拍（小蓝的标准）
别让一个物体在一整段好几句话里干杵着。每个卡拉OK短语都应该触发一次视觉变化。
写完之后逐段扫一遍：数动画事件数 vs 短语数 —— 事件 < 短语就补节拍。一段超过约 6 秒
却只有 1–2 个事件，就是太稀。低成本密度工具箱（全部 seek 安全）：`rollNum` 计数器；
**% donut**（`rollNum` + 圆弧 `strokeDashoffset` 走到 `circ*(1-pct)`）；N 个元素的错峰
`pop`（买家圆点、砖块、模块瓷片）；一把摆开的锁/栅栏（shackle path 的 `rotation`）；
物体或接收方 SWAP（人→Agent、软件→砖块、db→donut）；一个徽章（热卖）；双箭头
反馈环；开场句上方挂一个"?"钩子。这条赛道验证过的两个复用套路：
- **% donut** —— "六成由 AI 创建"：一个轨道圆 + 一条克莱因蓝圆弧画到目标百分比 +
  内部一个 `0→N%` 滚动数字。
- **热卖集群** —— "酱料热卖/日活几百万"：一个销量 `rollNum` + 3–4 个错峰弹入的买家
  圆点 + 一个 mintdeep 热卖徽章带过冲弹出。传达"卖得快、买的人多"。

## 真实品牌 logo（VO 点名公司时，比如 Supabase / YC / HashiCorp）
去拉官方的单 path SVG：`curl -s -o <slug>.svg https://cdn.simpleicons.org/<slug>`
（slug：`supabase`、`ycombinator`、`hashicorp`……；有些品牌会 404 —— 那就去官网抓，
或者小蓝的实拍素材里已经有就直接跳过）。把 path 内联进来，`fill` 用品牌色。
小蓝认可的呈现方式 = **品牌色 logo 放进柔和芯片卡**（panel 底色 + #E6DEC9 描边 +
阴影，logo 约 96px + 名称 + 一条薄荷绿 scaleX 下划线）。YC 在 simpleicons 的 path 是
单色的（方块和 Y 同色 → Y 直接隐形）—— 得重画：橙色 `#F0652F` 圆角矩形 + 奶油色衬线
`<text>Y</text>`。每个芯片卡在名字被念到的那一刻出现；后面再提到就 reprise 一次。

## 翻译新概念（表里没有的时候）
先问自己："观众一眼就能认出来、正在演这个概念的实体物件是什么？"画那个。
实在太抽象，就直接 mock 真实产品的 UI（一个 coding agent 的终端、一块手机屏幕、
你的笔记系统）。禁区：拿带字的矩形当主角、渐变光球、霓虹/赛博朋克、网格/点阵、
emoji 当主角（emoji 当小的点缀 label 可以）、红绿对比（用灰 vs 薄荷绿）。

## Helpers（模板里已定义）
```
show(sel,at,d) / hide(sel,at,d)     opacity in/out (serialize: hide before next show)
breathe(sel,at)                     subtle scale yoyo for ambient life
spin(sel,at,dur)                    rotation 360 (loop glyphs)
drawOn(sel,at,dur)                  stroke-dashoffset draw-on (sets hidden at load)
pop(sel,at,from,origin)             back.out scale+fade entrance (badges/icons)
counter(obj,sel,to,at,dur,suffix)   seek-safe number roll via proxy + onUpdate
```
红色预算 ≤3 次/条视频：花在 天价账单 金句 + 最多两个点缀（一条删除线 划掉、
cron 的停止 ✗）。渲染前先数一遍。
