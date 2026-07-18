# 卡拉OK引擎 — word-pop 弹词、锁定 VO、auto-fit

验证过的引擎完整代码原样躺在 `assets/full-template.html` 里。这份文档是规格说明，
方便你正确地往里换内容。

## 视觉效果（小蓝的 word-pop 风格）
- 一次只上屏一个短语，居中放在字幕带里，思源黑体 (Noto Sans SC) 800，
  约 62px，炭黑 `#1F1F1D`。
- **字幕带位置（小蓝，2026-06-17）：紧贴出镜人实测头顶的正上方，留 ~35–50px 间隙** ——
  比如头顶 y1088 → 字幕带 `top:935 height:115`（底边约 y1050）。旧的 y800–950 默认值
  悬在画面中部，太高了 —— 没实测过就绝不许上线。字幕带下移之后，把 b-roll 物体
  也往下放，填掉腾出来的中间区域（见 SKILL.md 的硬性规则）。
- **当前激活的 unit** 变成**克莱因蓝 `#002FA7`**，带一个快速的 1.13 scale 弹跳；上一个
  unit 变回炭黑。
- **强调 unit** 保持克莱因蓝不变，并画上一条**薄荷绿手绘下划线**（子级 `.ul` span，
  `transform:scaleX(0)→1` 画出来）。该标强调的关键词：loop / 触发 / 验证 / 判断 / 震撼数字。
- 短语在自己的 start 前约 0.04s 入场（fade + y 上移），在 end 处退场（fade）。

## 短语数据 — 两种格式（`unitsOf()` 都支持）
```js
const PH = [
  // explicit word times (hand-tuned regions — hook, ending):
  {w:[["不写",2.60],["prompt",2.88,"le"],["了",3.24],["loop",3.76,"le"]], s:2.22, e:4.04},
  // interpolated units (the body — fast to author):
  {u:"loop* 就像 你招了个 很聪明的 实习生*", s:15.42, e:17.62},
];
```
- `w` 格式：`[[text, activationTime, flags]]`。flags：`l`=latin（加左右边距），`e`=强调。
- `u` 格式：空格分隔的 units；`*` 后缀 = 强调；latin 自动识别。激活时间在 `[s, e]` 区间内
  **均匀插值** —— 正文用这个足够快、足够好；短语的时间窗口（`s`、`e`）始终锁定
  whisper 给的 VO 时间。
- 中文 unit 切 1–3 个字（自然的阅读断句）。latin token 保持完整（"cron"、"loop"）。

## Auto-fit（硬性要求 —— 防止文字出血到边缘）
每行构建完之后，量 `inner.getBoundingClientRect().width`；如果 `> 905`，就设
`inner.style.transform = scale(905/width)`。平台会裁掉竖屏两侧边缘，所以一行就算在
1080 全宽里放得下，照样会被切 —— 905 能保证留在约 100px 的安全边距内。超过约 9 个
unit 的短语要**拆成两个窗口**，让 auto-fit 的缩放尽量贴近 1（字号保持一致）；
auto-fit 是兜底安全网，不是主要的排版手段。

## 构建循环（每个短语）— 精确的 tween 参数看模板
```
fromTo(line, opacity/y in)   @ s-0.04
to(line, opacity 0)          @ e
per unit:
  set(unit, color klein)     @ t
  fromTo/to scale pop        @ t
  if emph: to(.ul scaleX 1)  @ t+0.02       // stays klein
  else:    to(unit color ink)@ next.t        // reverts
```

## 跳过 johnbucog 的时间窗
金句不走卡拉OK —— 在 `PH` 里给每个金句窗口**留空**（比如 先不要碰、判断、
天价账单、英文 payoff 那句）。这些节拍由 johnbucog 字幕带接管；金句过完，
卡拉OK再接着走。

## VO 时间来源
短语窗口取 whisper 的 SEGMENT 边界；`w` 格式短语的逐字时间取 whisper 的 WORD
时间戳（`transcribe.py` 会把两者都写进 `transcript.json`）。显示文本要改成简体、
修正同音字和专有名词，但时间戳原封不动。
