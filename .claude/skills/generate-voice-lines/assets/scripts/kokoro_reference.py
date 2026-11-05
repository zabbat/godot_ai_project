"""Render a character's voice reference clip with Kokoro: a blend of built-in voices, the text in
parts, each part with its own speed and the silence after it.

  uv run --project <kok>/settings .claude/skills/generate-voice-lines/assets/scripts/kokoro_reference.py ^
      --voice "af_heart:0.5,af_aoede:0.3,af_kore:0.2" ^
      "Peace be with you, traveler.|0.85|0.5" ^
      "May the light shine on you, and may God bless your path.|0.82|0" ^
      -o <kok>/output/references/defender/defender_ref-1.wav

--voice   one voice ("af_heart"), an equal blend ("af_heart,af_kore") or weighted
          ("af_heart:0.5,af_kore:0.2"; weights are normalised). The first letter is the language
          (a = US English, b = UK English).
parts     "text|speed|pause_seconds"; speed and pause are optional (1.0, 0.25).
          Stress markup works inside text: [word](-2) removes stress, [word](/phonemes/) sets it.
-o        output .wav; a .json with the full recipe is written next to it.

Prints the length and median pitch. Exit code 2 (and a WARN line) if the clip is outside 6-8 s,
the length a Chatterbox reference must have.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from huggingface_hub import hf_hub_download
from kokoro import KPipeline

REPO = "hexgrad/Kokoro-82M"
SR = 24000
MIN_S, MAX_S = 6.0, 8.0


def parse_blend(spec: str) -> list[tuple[str, float]]:
    parts = [p.split(":") for p in spec.split(",") if p.strip()]
    w = np.array([float(p[1]) if len(p) > 1 else 1.0 for p in parts])
    w = w / w.sum()
    return [(p[0].strip(), round(float(x), 4)) for p, x in zip(parts, w)]


def voice_pack(blend: list[tuple[str, float]]) -> torch.Tensor:
    return sum(w * torch.load(hf_hub_download(REPO, f"voices/{n}.pt"), weights_only=True) for n, w in blend)


def median_pitch(y: np.ndarray) -> float:
    import librosa
    f0, voiced, _ = librosa.pyin(y, fmin=60, fmax=500, sr=SR)
    f0 = f0[voiced & ~np.isnan(f0)]
    return float(np.median(f0)) if len(f0) else 0.0


ap = argparse.ArgumentParser()
ap.add_argument("--voice", required=True)
ap.add_argument("parts", nargs="+")
ap.add_argument("-o", "--out", required=True)
args = ap.parse_args()

blend = parse_blend(args.voice)
pipe = KPipeline(lang_code=blend[0][0][0], repo_id=REPO)
pack = voice_pack(blend)
chunks, recipe = [], []
for part in args.parts:
    text, speed, pause = (part.split("|") + ["1.0", "0.25"])[:3]
    for _, _, a in pipe(text, voice=pack, speed=float(speed)):
        chunks.append(a.numpy())
    chunks.append(np.zeros(int(float(pause) * SR), dtype=np.float32))
    recipe.append({"text": text, "speed": float(speed), "pause_s": float(pause)})
y = np.concatenate(chunks)
# drop the trailing pause of the last part and any trailing silence
nz = np.nonzero(np.abs(y) > 1e-3)[0]
y = y[: nz[-1] + int(0.05 * SR)] if len(nz) else y

out = Path(args.out)
out.parent.mkdir(parents=True, exist_ok=True)
sf.write(out, y, SR)
secs = len(y) / SR
pitch = median_pitch(y)
out.with_suffix(".json").write_text(json.dumps({
    "tool": "kokoro", "model": REPO, "voice_blend": [{"voice": n, "weight": w} for n, w in blend],
    "parts": recipe, "seconds": round(secs, 2), "median_pitch_hz": round(pitch),
    "license": "Kokoro-82M weights and voices: Apache-2.0"}, indent=2), encoding="utf-8")

ok = MIN_S <= secs <= MAX_S
print(f"{'ok  ' if ok else 'WARN'} {out.name}  {secs:.2f}s  pitch {pitch:.0f} Hz"
      + ("" if ok else f"  (needs {MIN_S:.0f}-{MAX_S:.0f} s: change the text or the speeds)"))
sys.exit(0 if ok else 2)
