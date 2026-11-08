"""Kokoro through Docker: the same jobs and output as kokoro_samples.py and kokoro_reference.py, but
the speech comes from a Kokoro-FastAPI server running in a Linux container. Used when the project's
Kokoro runs in Docker (SKILL.md "Kokoro in Docker"), for example because Windows Smart App Control
blocks the local install's DLLs.

Start the server first (template: assets/docker/compose.yaml, copied to <kok>/docker/):
  docker compose -f <kok>/docker/compose.yaml up -d

Auditions (one line, several voices or blends, several speeds):
  uv run --project <kok>/settings .claude/skills/generate-voice-lines/assets/scripts/kokoro_docker.py samples ^
      "am_michael:0.6,am_onyx:0.4;am_puck" "Hello, my child." -s 0.82 -o <kok>/output/samples/<name>

Reference clip (parts "text|speed|pause_seconds", 6-8 s, .json recipe written next to it):
  uv run --project <kok>/settings .claude/skills/generate-voice-lines/assets/scripts/kokoro_docker.py reference ^
      --voice "am_michael:0.6,am_onyx:0.4" "Hello, my child.|0.82|0.5" "May the light shine on you.|0.82|0" ^
      -o <kok>/output/references/<name>/<name>_ref-1.wav

Blends: "a:0.6,b:0.4" (weights normalised here, sent to the server as "a(0.6)+b(0.4)").
Needs only numpy, soundfile and librosa (pitch); the Kokoro package itself is never imported.
Server address: KOKORO_URL (default http://127.0.0.1:8880). Exit code 2 if a reference is not 6-8 s.
"""
import argparse
import io
import json
import os
import sys
import urllib.request
from pathlib import Path

import numpy as np
import soundfile as sf

URL = os.environ.get("KOKORO_URL", "http://127.0.0.1:8880")
IMAGE = "ghcr.io/remsky/kokoro-fastapi-cpu:v0.2.4"
SR = 24000
MIN_S, MAX_S = 6.0, 8.0


def parse_blend(spec: str) -> list[tuple[str, float]]:
    parts = [p.split(":") for p in spec.split(",") if p.strip()]
    w = np.array([float(p[1]) if len(p) > 1 else 1.0 for p in parts])
    w = w / w.sum()
    return [(p[0].strip(), round(float(x), 4)) for p, x in zip(parts, w)]


def api_voice(blend: list[tuple[str, float]]) -> str:
    if len(blend) == 1:
        return blend[0][0]
    return "+".join(f"{n}({w})" for n, w in blend)


def speak(text: str, blend, speed: float) -> np.ndarray:
    body = json.dumps({"model": "kokoro", "input": text, "voice": api_voice(blend), "speed": speed,
                       "response_format": "wav", "stream": False}).encode()
    req = urllib.request.Request(f"{URL}/v1/audio/speech", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        y, sr = sf.read(io.BytesIO(r.read()), dtype="float32")
    if y.ndim > 1:
        y = y.mean(axis=1)
    if sr != SR:
        sys.exit(f"unexpected sample rate {sr}")
    return y


def trim(y: np.ndarray) -> np.ndarray:
    nz = np.nonzero(np.abs(y) > 1e-3)[0]
    return y[: nz[-1] + int(0.05 * SR)] if len(nz) else y


def median_pitch(y: np.ndarray) -> float:
    import librosa
    f0, voiced, _ = librosa.pyin(y, fmin=60, fmax=500, sr=SR)
    f0 = f0[voiced & ~np.isnan(f0)]
    return float(np.median(f0)) if len(f0) else 0.0


def samples(args) -> None:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "line.txt").write_text(args.text, encoding="utf-8")
    for spec in [v.strip() for v in args.voices.split(";") if v.strip()]:
        blend = parse_blend(spec)
        for speed in args.speeds:
            y = trim(speak(args.text, blend, speed))
            name = "+".join(f"{n}-{w:g}" for n, w in blend) if len(blend) > 1 else blend[0][0]
            f = out / f"{name}_{speed:g}.wav"
            sf.write(f, y, SR)
            print(f"{f.name}  {len(y) / SR:.2f}s  pitch {median_pitch(y):.0f} Hz")


def reference(args) -> int:
    blend = parse_blend(args.voice)
    chunks, recipe = [], []
    for part in args.parts:
        text, speed, pause = (part.split("|") + ["1.0", "0.25"])[:3]
        chunks.append(trim(speak(text, blend, float(speed))))
        chunks.append(np.zeros(int(float(pause) * SR), dtype=np.float32))
        recipe.append({"text": text, "speed": float(speed), "pause_s": float(pause)})
    y = trim(np.concatenate(chunks))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(out, y, SR)
    secs, pitch = len(y) / SR, median_pitch(y)
    out.with_suffix(".json").write_text(json.dumps({
        "tool": "kokoro (Kokoro-FastAPI in Docker)", "image": IMAGE, "model": "hexgrad/Kokoro-82M",
        "voice_blend": [{"voice": n, "weight": w} for n, w in blend], "api_voice": api_voice(blend),
        "parts": recipe, "seconds": round(secs, 2), "median_pitch_hz": round(pitch),
        "license": "Kokoro-82M weights and voices: Apache-2.0"}, indent=2), encoding="utf-8")
    ok = MIN_S <= secs <= MAX_S
    print(f"{'ok  ' if ok else 'WARN'} {out.name}  {secs:.2f}s  pitch {pitch:.0f} Hz"
          + ("" if ok else f"  (needs {MIN_S:.0f}-{MAX_S:.0f} s: change the text or the speeds)"))
    return 0 if ok else 2


ap = argparse.ArgumentParser()
sub = ap.add_subparsers(dest="cmd", required=True)
s = sub.add_parser("samples")
s.add_argument("voices")
s.add_argument("text")
s.add_argument("-s", "--speeds", type=float, nargs="+", default=[1.0])
s.add_argument("-o", "--out", required=True)
r = sub.add_parser("reference")
r.add_argument("--voice", required=True)
r.add_argument("parts", nargs="+")
r.add_argument("-o", "--out", required=True)
args = ap.parse_args()
if args.cmd == "samples":
    samples(args)
else:
    sys.exit(reference(args))
