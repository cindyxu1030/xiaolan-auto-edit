# 金句 Lottie 赛道 — trace-fill-snap（金句的第二种 register）

2026-07-01 验证通过（和 GSAP slam 做过 A/B：`<你的工作目录>/jinju-lottie-test/`）。
这是金句主视觉文字的第二种处理方式：做成一个 Lottie 素材，由 HyperFrames 的
lottie adapter 按帧 seek。它补上了 GSAP 直接驱动 HTML 文字做不到的动效词汇
（字形轮廓 draw-on），而**最终定格**和 johnbucog 版式完全一致 —— 同样的
思源宋体 Heavy、同样的色板、同样的 size-to-fit。

## 每条金句选 register（语义说了算）
- **GSAP johnbucog slam（默认）** —— 冲击型节拍：天价账单、大数字、狠的
  punchline。瞬间砸下来，不做铺垫。
- **Lottie trace-fill-snap（本赛道）** —— 规则 / 警告 / 蓄势型节拍：先不要碰、
  判断这类裁定。克莱因蓝描边先沿字形轮廓描一遍 → 墨色按阅读顺序灌入 →
  当前字形 punch（scale 过冲），**全程保持克莱因蓝**。命中前约 1.7s 的蓄势。
- **默认只用克莱因蓝 —— 小蓝的规矩（小蓝，2026-07-01）：警告类金句不用红色。**
  构建脚本的变红是 opt-in（`--red`），只留给真正配得上 ≤3 次红色预算的冲击
  节拍；拿不准，就不用。
- 同一条金句绝不同时上两种 register。

## 管线（全本地、确定性）
1. **提取字形轮廓**（思源宋体 Heavy，来自项目里 Google-Fonts 的 woff2 分片 ——
   和 HTML 文字用的是同一批字体文件，所以形状 1:1 对齐）：
   `PYTHONIOENCODING=utf-8 python assets/glyph2lottie.py "<金句>" <workdir>`
   → `<workdir>/glyphs.json`。脚本读 `fonts.css` 的 unicode-range 找到每个字形
   所在的分片；输出 Lottie 直接能用的贝塞尔（y 朝下，1000 单位 em）。
   FONTS_DIR 常量指向 `agentloop-broll/fonts` —— 项目挪窝了记得改。
2. **构建 Lottie：**
   `python assets/build-jinju-lottie.py <workdir>/glyphs.json assets/<name>.json
    --text <金句> --active <红字> --start <comp-sec> --dur <window-sec>`
   默认值：30fps、84 帧编排、字形 235px（≤4 个字放得进 ≤950px；5 个字以上把
   `--size` 调小，让 总宽 = 字数×size ≤ 950）。
3. **（可选）用 `text-to-lottie` skill 手工编排/改稿** —— 官方 Skottie 播放器在
   `<你的工作目录>/lottie-player/`（degit 自 diffusionstudio/lottie；scene 放在
   `public/projects/<p>/<scene-N>/lottie.json`，`npm run dev` → 用 `?frame=N`
   钉住某一帧）。构建脚本参数覆盖不到的编排，就用它来迭代。
4. **嵌入合成**（lottie-web，svg renderer）：
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
   CSS：容器的定位和 `.jb` 字幕带完全一样（默认 top:382 height:440 —— 头部
   避让规则和任何 johnbucog 节拍相同）。
5. **和其他所有东西一样，在奶油底的 proxy render 里验证。** Skottie 播放器只管
   编排迭代；HyperFrames 出的帧才是权威校验（渲染器一致性：lottie-web ≠ Skottie，
   冷门特性上表现不同 —— 本赛道只用 shapes/trim/stroke/fill，两边都安全）。

## 坑（做这条赛道时踩出来的）
- **Adapter 计时：** `__hfLottie` 里的播放器是按**合成时间**被 seek 的。合成
  t=X 处的金句必须用 `--start X` 构建（keyframe 整体偏移，X 之前图层隐藏）。
  一条金句一个 Lottie 文件；照常在这个窗口上给卡拉OK留空。
- **Lottie 内部同样绝不能把克莱因蓝 tween 成红** —— 和 GSAP 一样的"紫色中间态"
  禁令。构建脚本用 HOLD keyframe（`h:1`）做颜色切换。
- **描边宽度 ≥26**（字形单位）@ 235px 字形 —— 再细就读成线框 CAD，不是书法
  （第一版 w16 就没过帧检查）。
- **灌墨渐变 ≤4 帧** —— 慢速的透明度渐变会在奶油底上经过一段脏灰阶段
  （墨色 ~40% 叠在奶油上 = 灰泥；A/B v1 抓出来的）。
- **字形是烤好的轮廓** —— 不加载 Lottie 字体、没有子集 woff2 缺字风险
  （个→↑ 这类 bug 不可能发生），在 Skottie / lottie-web / HyperFrames 里渲染
  完全一致。
- 动起来的强调本身已经够响了；trace-fill-snap 的金句**不要**再加下划线/徽章/
  光晕。描边就是那一下 flourish（一个节拍只许一个 flourish）。
