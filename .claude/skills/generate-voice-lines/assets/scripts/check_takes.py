"""Check generated voice takes, and cut a line out of a longer one, using Whisper word timestamps.

  uv run --project <kok>/settings .claude/skills/generate-voice-lines/assets/scripts/check_takes.py ^
      <cbx>/output/defender/defender_spell_light [--keep "let there be light"] [--ref <ref.wav>]

For every take (*.wav with a Chatterbox .json next to it; *_cut.wav files are skipped) in FOLDER
and its subfolders:
  1. transcribe it with word timestamps (faster-whisper small.en, CPU; downloaded on first use),
  2. compare the words heard with the take's text from its .json (tags like [angry] ignored),
  3. with --keep: find those words at the end and cut just before them (padding, never into the
     previous word, short fade-in) -> <take>_cut.wav + <take>_cut.json,
  4. with --ref: compare the take's median pitch with the reference clip's.

One line per take:  ok | WORDS (wrong or missing words) | PITCH (over 1.7x the reference) | FAIL
The audio never enters the conversation: only these lines are read.
"""
import argparse
import json
import re
from difflib import SequenceMatcher
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel

PAD, FADE = 0.08, 0.015
MATCH_OK, PITCH_HIGH = 85, 1.7


def words_of(text: str) -> list[str]:
    text = re.sub(r"\[[^\]]*\]", " ", text.lower())
    return re.findall(r"[a-z']+", text)


def merge_compounds(words: list[tuple], wanted: set[str]) -> list[tuple]:
    """Whisper may split a word the text writes as one ("begone" -> "be gone"): join them back."""
    out = []
    for w in words:
        if out and (out[-1][0] + w[0]) in wanted:
            out[-1] = (out[-1][0] + w[0], out[-1][1], w[2])
        else:
            out.append(w)
    return out


def median_pitch(y: np.ndarray, sr: int) -> float:
    f0, voiced, _ = librosa.pyin(y, fmin=70, fmax=600, sr=sr)
    f0 = f0[voiced & ~np.isnan(f0)]
    return float(np.median(f0)) if len(f0) else 0.0


ap = argparse.ArgumentParser()
ap.add_argument("folder")
ap.add_argument("--keep", help="words to keep at the end; the take is cut just before them")
ap.add_argument("--ref", help="reference clip, for the pitch comparison")
args = ap.parse_args()

keep = words_of(args.keep) if args.keep else []
ref_pitch = 0.0
if args.ref:
    y, sr = sf.read(args.ref, dtype="float32")
    ref_pitch = median_pitch(y if y.ndim == 1 else y.mean(axis=1), sr)
    print(f"reference pitch {ref_pitch:.0f} Hz")
model = WhisperModel("small.en", device="cpu", compute_type="int8")

for wav in sorted(Path(args.folder).rglob("*.wav")):
    meta_file = wav.with_suffix(".json")
    if wav.stem.endswith("_cut") or not meta_file.exists():
        continue
    meta = json.loads(meta_file.read_text(encoding="utf-8"))
    expected = words_of(meta.get("text") or meta.get("sent_text", ""))
    y, sr = sf.read(wav, dtype="float32")
    if y.ndim > 1:
        y = y.mean(axis=1)
    segs, _ = model.transcribe(librosa.resample(y, orig_sr=sr, target_sr=16000), language="en",
                               word_timestamps=True, beam_size=5)
    heard = [(w, s.start, s.end) for seg in segs for s in seg.words for w in words_of(s.word)]
    heard = merge_compounds(heard, set(expected))
    heard_words = [w for w, _, _ in heard]
    match = SequenceMatcher(None, expected, heard_words).ratio() * 100
    said = " ".join(heard_words)

    part, info = y, ""
    if keep:
        n = min(2, len(keep))
        idx = next((i for i in range(len(heard_words) - 1, -1, -1) if heard_words[i:i + n] == keep[:n]), None)
        if idx is None:
            print(f"FAIL  {wav.name:44s} kept words not found   heard: {said}")
            continue
        t0 = heard[idx][1]
        prev_end = heard[idx - 1][2] if idx > 0 else 0.0
        cut = max(t0 - PAD, (prev_end + t0) / 2) if idx > 0 else 0.0
        part = y[int(cut * sr):].copy()
        k = int(FADE * sr)
        part[:k] *= np.linspace(0, 1, k, dtype=np.float32)
        out = wav.with_name(wav.stem + "_cut.wav")
        sf.write(out, part, sr)
        out.with_suffix(".json").write_text(json.dumps({
            "source": wav.name, "cut_at_s": round(cut, 3), "kept_s": round(len(part) / sr, 2),
            "kept_words_ok": heard_words[idx:] == keep, "heard": said, "match_pct": round(match),
            "source_meta": meta}, indent=2), encoding="utf-8")
        info = f"cut {cut:4.2f}s -> {len(part) / sr:4.2f}s  "
        if heard_words[idx:] != keep:
            match = min(match, MATCH_OK - 1)

    pitch = median_pitch(part, sr)
    ratio = pitch / ref_pitch if ref_pitch else 0.0
    flag = "ok   "
    if match < MATCH_OK:
        flag = "WORDS"
    elif ratio > PITCH_HIGH:
        flag = "PITCH"
    pitch_txt = f"{pitch:4.0f} Hz" + (f" ({ratio:.2f}x)" if ratio else "")
    print(f"{flag} {wav.name:44s} {len(y) / sr:5.2f}s  {info}{pitch_txt}  words {match:3.0f}%  heard: {said}")
