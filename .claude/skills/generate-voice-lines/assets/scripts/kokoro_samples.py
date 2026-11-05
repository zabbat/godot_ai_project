"""Audition Kokoro voices: render one line in several voices (or blends) and speeds, so the user can
listen and choose before a reference clip is made.

  uv run --project <kok>/settings .claude/skills/generate-voice-lines/assets/scripts/kokoro_samples.py ^
      "af" "May the light shine on you." -s 0.85 1.0 -o <kok>/output/samples/defender

voices    a prefix ("a" all US, "af" US female, "bm" UK male), a voice name, or a ;-separated
          list of voices and blends: "af_heart;af_heart:0.6,af_kore:0.4;af_aoede"
-s        one or more speeds (default 1.0)
Output: <out>/<voice-or-blend>_<speed>.wav, plus line.txt with the text.
"""
import argparse
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from huggingface_hub import hf_hub_download, list_repo_files
from kokoro import KPipeline

REPO = "hexgrad/Kokoro-82M"

ap = argparse.ArgumentParser()
ap.add_argument("voices")
ap.add_argument("text")
ap.add_argument("-s", "--speeds", type=float, nargs="+", default=[1.0])
ap.add_argument("-o", "--out", required=True)
args = ap.parse_args()

if ";" in args.voices or "," in args.voices or ":" in args.voices:
    specs = [v.strip() for v in args.voices.split(";") if v.strip()]
else:
    specs = sorted(f[7:-3] for f in list_repo_files(REPO)
                   if f.startswith(f"voices/{args.voices}") and f.endswith(".pt"))


def pack(spec: str):
    parts = [p.split(":") for p in spec.split(",")]
    w = np.array([float(p[1]) if len(p) > 1 else 1.0 for p in parts])
    w = w / w.sum()
    label = "+".join(f"{p[0]}{round(x * 100)}" if len(parts) > 1 else p[0] for p, x in zip(parts, w))
    return sum(x * torch.load(hf_hub_download(REPO, f"voices/{p[0]}.pt"), weights_only=True)
               for p, x in zip(parts, w)), label


out = Path(args.out)
out.mkdir(parents=True, exist_ok=True)
(out / "line.txt").write_text(f"{args.text}\nspeeds: {args.speeds}\n", encoding="utf-8")
pipes: dict = {}
for spec in specs:
    voice, label = pack(spec)
    lang = spec[0]
    pipe = pipes.setdefault(lang, KPipeline(lang_code=lang, repo_id=REPO))
    for s in args.speeds:
        audio = np.concatenate([a.numpy() for _, _, a in pipe(args.text, voice=voice, speed=s)])
        path = out / f"{label}_{s:.2f}.wav"
        sf.write(path, audio, 24000)
        print(f"{path.name:40s} {len(audio) / 24000:5.2f}s")
print("->", out)
