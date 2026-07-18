# Xiaolan's AI Auto-Edit Skills (xiaolan-auto-edit)

[中文](README.md) | English

The "employee handbook" I wrote for my AI video editor — now open source.

Two skills forming an auto-editing pipeline for talking-head videos:

| Stage | Skill | What it does |
|---|---|---|
| 1 — Rough cut | [`xiaolan-aroll`](xiaolan-aroll/SKILL.en.md) | Takes the unedited A-roll + a reference script: removes pauses, cuts takes killed with a spoken 「卡 / cut」 cue, collapses repeated takes to the cleanest one, and renders a tightened video (A/V in sync) with a reviewable keep/cut log (EDL). |
| 2 — Dressing | [`xiaolan-broll`](xiaolan-broll/SKILL.en.md) | Takes the full talking-head video: builds brand-locked b-roll animations + word-pop karaoke captions, delivered as a transparent ProRes MOV overlay you composite over your high-quality A-roll. Giant-hero type is reserved for punchlines; regular lines get regular captions. |

## Why "employee handbook"

The dozens of dated rules in these SKILL.md files were all written after my AI editor messed up and got scolded:

- Captions sit just above the presenter's head, never floating mid-frame (2026-06-17)
- White text is banned — invisible on the cream background
- Red appears at most three times per video; more reads cheap
- Measure the presenter's head height before drawing; graphics never cover the face
- Never skip the illustration step; self-check every frame before delivering

Scold an AI in chat and it forgets by tomorrow. Rules written into the handbook get read before every shift — those it obeys.

## Install

Copy the two skill folders into your coding agent's skills directory (check your agent's docs; commonly `~/.codex/skills/` or equivalent):

```
<your-skills-dir>/xiaolan-aroll/
<your-skills-dir>/xiaolan-broll/
```

Trigger phrases live in each skill's frontmatter `description` — Chinese and English both work ("剪我的口播" / "edit my a-roll").

Chinese docs are the canonical filenames (`SKILL.md`); English versions sit alongside as `*.en.md`.

## Requirements

- A coding agent that supports the SKILL.md skill format (Codex CLI, GLM-family agents, etc.)
- `ffmpeg` (cutting + rendering)
- Python 3 + `faster-whisper` (transcription); `rembg` (green-screen matting)
- HyperFrames CLI (`npx hyperframes`) for the b-roll overlay renders

## Layout

Each skill is the standard trio:

- `SKILL.md` / `SKILL.en.md` — entry point (the handbook itself: frontmatter + workflow + non-negotiables)
- `references/` — detailed algorithms and recipes, loaded on demand
- `assets/` — Python helpers and templates the skill runs

## Make it yours

The rules are my taste; the pipeline is generic. Recommended path:

1. Run one video through as-is
2. Every time a delivery disappoints you, don't just say it in chat — write it as a dated rule into SKILL.md
3. Keep a "mistake book" file for your AI employee; log every lesson
4. Reuse-first asset library: archive every green-screen cutout you generate, check the library before generating new

One mistake is on them. The same mistake twice is on you — you didn't write the rule down.

## License

MIT
