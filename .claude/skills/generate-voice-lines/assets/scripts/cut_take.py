"""Show the loudness of a take over time, and cut a part out of it (one laugh out of two, a stray
breath at the end). For sounds the Whisper word check cannot place (laughs, sighs); spoken words are
cut with check_takes.py --keep instead. Cut only when the user asks: never trim a take on your own.

  uv run --project <kok>/settings .claude/skills/generate-voice-lines/assets/scripts/cut_take.py ^
      <cbx>/output/<name>/<name>_laugh/<name>_laugh-3.wav

      prints one line per 20 ms: time, RMS and a bar. Silences (rows near 0) between the sounds are
      where to cut: pick a time inside the gap, not at the edge of a sound.

  ... cut_take.py <take.wav> --start 0 --end 0.92

      writes <take>_cut.wav next to the take (or -o FILE): the part from --start to --end seconds,
      with a short fade-in (if it does not start at 0) and fade-out, so it starts and ends cleanly.
      Prints the new length and median pitch (0 Hz = unvoiced/breathy, normal for a laugh).
"""
import argparse
from pathlib import Path

import numpy as np
import soundfile as sf

STEP = 0.02
FADE = 0.02

ap = argparse.ArgumentParser()
ap.add_argument("take")
ap.add_argument("--start", type=float)
ap.add_argument("--end", type=float)
ap.add_argument("-o", "--out")
args = ap.parse_args()

y, sr = sf.read(args.take, dtype="float32")
if y.ndim > 1:
    y = y.mean(axis=1)

if args.start is None and args.end is None:
    h = int(STEP * sr)
    print(f"{Path(args.take).name}  {len(y) / sr:.2f} s")
    for i in range(0, len(y), h):
        r = float(np.sqrt(np.mean(y[i:i + h] ** 2)))
        print(f"{i / sr:5.2f}  {r:.4f}  " + "#" * int(r * 300))
    raise SystemExit(0)

a = int((args.start or 0.0) * sr)
b = int(args.end * sr) if args.end is not None else len(y)
c = y[a:b].copy()
f = min(int(FADE * sr), len(c) // 4)
if a > 0:
    c[:f] *= np.linspace(0, 1, f)
c[-f:] *= np.linspace(1, 0, f)
out = Path(args.out) if args.out else Path(args.take).with_name(Path(args.take).stem + "_cut.wav")
sf.write(out, c, sr)
try:
    import librosa
    f0, voiced, _ = librosa.pyin(c, fmin=60, fmax=500, sr=sr)
    f0 = f0[voiced & ~np.isnan(f0)]
    pitch = float(np.median(f0)) if len(f0) else 0.0
except ImportError:
    pitch = float("nan")
print(f"{out.name}  {len(c) / sr:.2f} s  ({args.start or 0:.2f}-{b / sr:.2f} s of the take)  pitch {pitch:.0f} Hz")
