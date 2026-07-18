---
name: xiaolan-aroll
description: >-
  自动剪辑「小蓝」式口播 A-roll（口播原片）视频：去掉静音/停顿，剪掉口头喊
  「卡 / cut」标记的废 take，去掉重复的 retake（保留更干净的那条），然后把剪好的视频
  渲染（RENDER）回来——音画同步。输入是未剪辑的 A-roll 视频（音频是检测信号）加一份
  参考脚本（SCRIPT，判断保留哪条 take、修 whisper 同音字错误的 ground truth）。
  输出是收紧后的粗剪视频，后续进 CapCut 精修。全自动（FULL AUTO，所有剪切直接应用），
  但一定输出一份 keep/cut 的 EDL 日志供扫查。触发场景："edit my a-roll"、
  "cut my talking head"、"remove the pauses and retakes"、"clean up my recording"、
  "去掉停顿和重复/废话"、"口播剪辑"、"cut where I said 卡"、"give me the edited video"。
  这是内容流水线的前半段——先把口播剪干净；`xiaolan-broll` 再往上叠 b-roll +
  卡拉OK字幕。不管 b-roll/字幕（用 `xiaolan-broll`），不管开场 hook
  （用 `xiaolan-hook-broll`，未包含在本仓库）。
---

# xiaolan-aroll

拿到一条**未剪辑的 A-roll（口播原片）视频** + 对应的**参考脚本**，交回一条**收紧后的
成片**：停顿删掉、口头喊**「卡 / cut」**毙掉的 take 剪掉、重复的 retake 合并成最干净的
那条。全自动，但要留一份可复查的剪切日志。这是流水线的前半段，产出直接喂给
`xiaolan-broll`。

## 小蓝怎么录（用这套 skill 你也要按这个约定录）
- 一条讲到底，**不剪**。说错一句就单独喊一声**「卡」**（kǎ）或**「cut」**，停一下，
  **重说这句**。所以一个 cue 的意思是：*cue 前面那条 take 是废的，cue 后面那条是要保的。*
- 没喊卡也会**重复句子**——同一句说两遍（经常略微换个说法）。保留后面/更干净的那条，
  删掉前面的。
- 录完配一份**对应的脚本** = 成片应该说的话。这是 GROUND TRUTH：两条 take 竞争时，
  保留和脚本最接近的那条；并且用脚本修 whisper 听错的词，绝不能在听错的字上下剪刀。

## 先读这些
1. `references/cut-logic.md` — 精确的检测+决策算法、cue 规则、停顿/重复的处理、
   ffmpeg 渲染（select/aselect、音画同步），以及所有的坑。
2. 你自己的决策日志——之前踩过的坑先过一遍（强烈建议给 AI 员工建一个错题本文件）。
3. 兄弟 skill：`xiaolan-broll`（b-roll + 卡拉OK字幕叠加）吃这里产出的视频。

## 铁律
- **剪的是视频，音画必须同步。** 视频进 → 剪好的视频出。在音频里找到的剪切点，
  视频+音频用同一时间戳一起剪。绝不允许音画错位。
- **绝不改博主的话和声音。** 只删：静音、被卡毙掉的 take、重复的 take。不删口头语
  （嗯/呃/那个），不做变调/变速/降噪——那是博主的声音。
- **脚本是 ground truth——用来保证正确性，不是用来下剪刀。** 用它修 whisper 同音字、
  核对每一句脚本都恰好存活一次。判断重复要靠两条 take 之间的高互相相似度——绝不能用
  「它们对到同一句脚本」来判（一个长句的连续 segments 共享同一句脚本，但不是重复）。
  确认是真重复时，保留后面/更干净的那条（你的「保第二遍」规则）。
- **「卡 / 咔 / cut」只有单独出现时才是 cue**（前后有停顿的短促发声）。词里的「卡」
  （卡片、卡顿、卡住）是内容——绝不能剪。拿不准的标记出来。
- **拿不准就保留并标记。** Full auto 意味着不设审核门直接渲染——但如果一个卡附近没有
  明确的 retake，或某个「重复」置信度低，保留内容并列进 EDL 的 `REVIEW` 区，
  别冒险删掉真句子。
- **交付前自检。** 对着脚本读一遍 EDL（总时长/句数对不对？），再去渲染好的成片里
  抽查实际的接缝点。

## 工作流
1. **看片**（`ffprobe`）：确认是口播 A-roll 视频，拿 duration + fps + 确认有音轨。
   注意可变帧率（VFR）——是的话输出强制 CFR。
2. **抽音频**做分析：`ffmpeg -i <in> -ac 1 -ar 16000 -vn audio.wav`。
3. **转写**到词级：`python assets/transcribe.py audio.wav transcript`
   （faster-whisper medium、zh、word_timestamps、int8 CPU、`PYTHONIOENCODING=utf-8`）。
4. **拿脚本**（`.txt`/直接粘贴）。存成 `script.txt`。没给就问用户要
   （或降级为「保后面那条」——注明降级了）。
5. **找剪切点**：`python assets/find-cuts.py --transcript transcript.json --media <in>
   --script script.txt --audio audio.wav --out edl.json --report edl.md`。它检测卡 cue、
   对着脚本解析废 take/重复，并按**静音优先 + 双档**（2026-07-05）删停顿：停顿是在
   `--audio` 的 RMS 包络上找的（whisper 的词时间会往静音里伸，用词间隙数停顿会严重
   漏——见 cut-logic.md §5）；whisper 词只用来划定保留的 take 和保护起音。句中停顿 >
   `--min-pause`（0.15 s）压到 `--beat`（0.10 s）残留；句末停顿（segment 以 。！？!?…
   结尾）> `--boundary-pause`（0.25 s）压到 `--boundary-beat`（0.20 s）。
   **永远要传 `--audio`**——不传就回退到词间隙，会漏掉大部分真停顿。
   报告会列出每一处停顿剪切（原间隙 → 残留）。
6. **核 EDL（哪怕 full-auto 也是必做）。** 读 `edl.md`：扫每一条 CUT 的理由和 `REVIEW`
   区。对着脚本交叉核对——每句脚本都应该恰好存活一次。启发式误剪了真句子就手改
   `edl.json` 的 `keep[]`。
7. **渲染**成片：`python assets/apply-cuts.py --media <in> --edl edl.json
   --out <name>-edit.mp4`。（select/aselect 用完全一致的区间 → 同步；重编码 CFR。）
8. **抽查**成片：probe 时长（和 EDL 求和一致），在 3-4 个接缝处看+听——切口干净、
   没吞字、口型对得上声音。
9. **交付**：成片放在**源文件旁边**，命名 `<source-stem>-edit.mp4`——不设「问放哪」的门
   （小蓝定的规矩，2026-06-26：别再问了，默认放源文件旁边；只有源文件位置真的模糊时
   才问）。工程目录固定在 `<你的工作目录>/<项目名>-aroll/`。绝不覆盖用户的源文件。
10. **记录**：把这次学到的坑记进你自己的决策日志（强烈建议给 AI 员工建一个错题本文件）。

## 会咬人的坑（完整清单见 cut-logic.md）
- **卡的同音词是内容**（卡片/卡顿/卡住）。只有单独出现、前后有停顿的 卡/咔/cut 才是 cue。
- **Whisper 听错 → 用脚本。** 两条 take 看着不一样，可能其实是同一句（反过来也一样）。
  归一化后和脚本句子比，别拿 whisper 原文直接比。
- **双档停顿规则（小蓝，2026-07-05）：** 句中停顿 > 0.15s 压到 ~0.10s 的 beat；
  句末停顿 > 0.25s 压到 ~0.20s。停顿在音频上量（RMS 静音段），不用 whisper 词间隙——
  whisper 会把词的时间拉伸进静音（一个真实 1.10s 的停顿曾被量成 0.22s 的词间隙），
  所以词间隙会漏掉大部分停顿。静音段里 whisper 声称的词起点，只有其后确有真实能量
  才可信。别把接缝压到零。
- **VFR 输入会让 select 剪辑音画漂移**——输出强制固定帧率（`-r <fps>`）。
- **select/aselect 必须用完全一致的区间**，视频音频各一套就会音画漂。
- **别删真句子。** 如果成片时长比脚本推算的收缩得多得多，就是过剪了——回头查 REVIEW
  项和相似度阈值。
- **retake 附近要帧级精确的接缝时，把那个窗口关掉 VAD 重转写。** 主转写
  （`vad_filter=True`）会丢短连接词（就想/呢/吧）、合并结巴（我我→我）。定稿一个剪切
  边界时，只把那 4–6 s 的窗口用 `vad_filter=False, condition_on_previous_text=False`
  重转写，拿回真实词时间，再把 `keep[]` 边界定在上面。小蓝的预期是：take 内的结巴
  要去重、被丢的连接词要保回来——不是只删废 take/重复就完事。
- **修辞性重复 ≠ repeat。** 小蓝的脚本会把一句陈述复述成反问（它替我回答 → 问题来了，
  它怎么能替我回答呢），repeat 检测一定会把陈述句剪掉。每个 [repeat] 剪切都要对脚本核：
  如果两条 take 对到脚本里两个都存在的不同句子，恢复这刀。
- **咳/咳咳可能代替「卡」终结一条废 take。** 在 keeps 里 grep 纯咳嗽 segment，
  当 take 接缝的信号用，把那一簇像卡废 take 一样手动剪掉。
- **手动剪完，渲染上补一遍 `--silence-only`**（临时文件 → 验证 → 替换）：手动剪的接缝处
  会留 0.4–0.6 s 的 beat，超过双档标准。只有 时长 / silencedetect 零命中 / 接缝起音 /
  字符 diff（0 删除）全部通过之后，才替换交付文件。

## Assets
- `assets/transcribe.py` — faster-whisper → 词级 JSON（words 嵌在 segments 里 + 平铺一份）。
- `assets/find-cuts.py` — 静音图 + 卡 cue + 重复/retake 解析（对齐脚本）→ keep/cut EDL。
- `assets/apply-cuts.py` — 按 EDL 渲染剪好的视频（或音频），音画同步、CFR。
