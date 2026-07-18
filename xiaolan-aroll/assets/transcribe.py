#!/usr/bin/env python
# transcribe.py — faster-whisper word-level transcription for A-roll cut detection.
# Usage: python transcribe.py audio.wav transcript
#   -> transcript.json  {language, duration, segments[{start,end,text,words[]}], words[]}
#   -> transcript.txt   human-readable segment list
import os, json, sys
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
from faster_whisper import WhisperModel

src = sys.argv[1] if len(sys.argv) > 1 else "audio.wav"
out = sys.argv[2] if len(sys.argv) > 2 else "transcript"

model = WhisperModel("medium", device="cpu", compute_type="int8")
segments, info = model.transcribe(
    src, language="zh", word_timestamps=True,
    vad_filter=True, vad_parameters=dict(min_silence_duration_ms=250),
)

seg_list, word_list, lines = [], [], []
for s in segments:
    sw = []
    if s.words:
        for w in s.words:
            wd = {"start": round(w.start, 3), "end": round(w.end, 3), "word": w.word}
            sw.append(wd)
            word_list.append(wd)
    seg_list.append({"start": round(s.start, 3), "end": round(s.end, 3),
                     "text": s.text, "words": sw})
    lines.append(f"[{s.start:7.2f} - {s.end:7.2f}] {s.text}")
    print(lines[-1], flush=True)

with open(out + ".json", "w", encoding="utf-8") as f:
    json.dump({"language": info.language, "duration": round(info.duration, 3),
               "segments": seg_list, "words": word_list}, f, ensure_ascii=False, indent=1)
with open(out + ".txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"\nDONE: {len(seg_list)} segments, {len(word_list)} words, "
      f"{info.duration:.1f}s -> {out}.json / {out}.txt", flush=True)
