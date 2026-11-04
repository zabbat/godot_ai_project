#!/usr/bin/env python3
"""Generate speech lines with Chatterbox for a game project.

Run it through the locked environment, from the project root:

    uv run --project chatterbox/settings .claude/skills/chatterbox-text-to-speech/assets/scripts/speak.py \
        --style angry --voice orc_captain --name orc-taunt "You dare enter my hall?"

    uv run --project chatterbox/settings .../speak.py --batch chatterbox/lines.json
    uv run --project chatterbox/settings .../speak.py --list        # voices, styles, models

Each take is written as  chatterbox/output/<name>/<name>-<nr>.<fmt>  plus a  <name>-<nr>.json
sidecar holding every setting and the seed, so the take can be reproduced or tweaked. A batch
file is a JSON list of objects using the same keys as the sidecar (text, name, style, voice,
model, seed, exaggeration, ...); a sidecar can be passed back in as a one-line batch.

Prints one JSON object per take on stdout (path, seconds, seed); progress goes to stderr.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

# Keep stderr readable: no progress bars, no Windows symlink nag. Must be set before imports.
for _k, _v in (("TQDM_DISABLE", "1"), ("HF_HUB_DISABLE_PROGRESS_BARS", "1"),
               ("HF_HUB_DISABLE_SYMLINKS_WARNING", "1"), ("PYTHONWARNINGS", "ignore")):
    os.environ.setdefault(_k, _v)

AUDIO_EXT =(".wav", ".mp3", ".flac", ".ogg", ".m4a")
MODELS = ("turbo", "english", "multilingual", "nano")
# Parameters each model's generate() accepts (others are dropped, not errors).
MODEL_PARAMS = {
    "turbo": {"temperature", "top_p", "top_k", "repetition_penalty"},
    "nano": {"temperature", "top_p", "top_k", "repetition_penalty"},
    "english": {"exaggeration", "cfg_weight", "temperature", "top_p", "min_p", "repetition_penalty"},
    "multilingual": {"exaggeration", "cfg_weight", "temperature", "top_p", "min_p", "repetition_penalty"},
}
TAG_MODELS = ("turbo", "nano")


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def find_root(start: Path) -> Path:
    """Project root = the folder that contains chatterbox/settings."""
    for p in [start, *start.parents]:
        if (p / "chatterbox" / "settings").is_dir():
            return p
    sys.exit("Cannot find chatterbox/settings above the current folder. Run from the project root.")


def load_toml(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("rb") as f:
        return tomllib.load(f)


def slugify(text: str, words: int = 4) -> str:
    keep = "".join(c.lower() if c.isalnum() else " " for c in text).split()
    return "-".join(keep[:words]) or "line"


def resolve_voice(voices_dir: Path, voice: str | None) -> str | None:
    if not voice:
        return None
    p = Path(voice)
    if p.is_file():
        return str(p)
    for ext in AUDIO_EXT:
        cand = voices_dir / f"{voice}{ext}"
        if cand.is_file():
            return str(cand)
    if (voices_dir / voice).is_file():
        return str(voices_dir / voice)
    sys.exit(f"Voice '{voice}' not found in {voices_dir} (put a clean 6-15 s clip there).")


def pick_device(want: str) -> str:
    import torch

    if want != "auto":
        return want
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


class ModelCache:
    """Holds one model at a time so VRAM is not doubled when a batch mixes models."""

    def __init__(self, device: str):
        self.device = device
        self.key = None
        self.model = None

    def get(self, name: str):
        if name == self.key:
            return self.model
        import gc

        import torch

        self.model = None
        gc.collect()
        if self.device == "cuda":
            torch.cuda.empty_cache()
        log(f"[speak] loading model '{name}' on {self.device} (first run downloads weights)...")
        if name in ("turbo", "nano"):
            from chatterbox.tts_turbo import ChatterboxTurboTTS

            self.model = ChatterboxTurboTTS.from_pretrained(device=self.device, nano=(name == "nano"))
        elif name == "english":
            from chatterbox.tts import ChatterboxTTS

            self.model = ChatterboxTTS.from_pretrained(device=self.device)
        elif name == "multilingual":
            from chatterbox.mtl_tts import ChatterboxMultilingualTTS

            self.model = ChatterboxMultilingualTTS.from_pretrained(device=self.device, t3_model="v3")
        else:
            sys.exit(f"Unknown model '{name}'. Choose from: {', '.join(MODELS)}")
        self.key = name
        return self.model


def build_text(text: str, model: str, preset: dict) -> str:
    """Apply a style preset's tag/prefix/suffix. Tags only exist on Turbo/Nano."""
    out = text.strip()
    if model not in TAG_MODELS:
        return out  # English/Multilingual have no tags; emotion comes from exaggeration/cfg
    # A line that already starts with its own [tag] keeps it; the preset adds no second one.
    if preset.get("tag") and not out.startswith("["):
        out = f"{preset['tag']} {out}"
    return preset.get("prefix", "") + out + preset.get("suffix", "")


def trim_silence(wav, sr: int, db: float, pad_ms: int):
    import numpy as np

    a = wav.squeeze(0).cpu().numpy() if hasattr(wav, "cpu") else wav
    thr = 10 ** (db / 20)
    loud = np.where(np.abs(a) > thr)[0]
    if loud.size == 0:
        return a
    pad = int(sr * pad_ms / 1000)
    return a[max(0, loud[0] - pad): min(len(a), loud[-1] + pad + 1)]


def peak_normalize(a, peak_db: float):
    import numpy as np

    if peak_db == 0:
        return a
    peak = float(np.max(np.abs(a))) if a.size else 0.0
    if peak <= 0:
        return a
    return a * (10 ** (peak_db / 20) / peak)


def write_audio(a, sr: int, path: Path, fmt: str):
    import soundfile as sf

    path.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "wav":
        sf.write(str(path), a, sr, subtype="PCM_16")
        return
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        sys.exit(f"--format {fmt} needs ffmpeg on PATH (or use --format wav).")
    tmp = path.with_suffix(".tmp.wav")
    sf.write(str(tmp), a, sr, subtype="PCM_16")
    codec = ["-c:a", "libvorbis", "-q:a", "6"] if fmt == "ogg" else ["-c:a", "libmp3lame", "-q:a", "2"]
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", str(tmp), *codec, str(path)], check=True)
    tmp.unlink()


def next_take(folder: Path, name: str) -> int:
    nrs = [0]
    for f in folder.glob(f"{name}-*.json"):
        tail = f.stem[len(name) + 1:]
        if tail.isdigit():
            nrs.append(int(tail))
    return max(nrs) + 1


def run_line(spec: dict, cfg: dict, styles: dict, cache: ModelCache, voices_dir: Path, out_root: Path):
    import torch

    d = {**cfg, **{k: v for k, v in spec.items() if v is not None}}
    model_name = d["model"]  # the line's own model, else config.toml's default
    text = d["text"]
    style = d.get("style") or ""
    preset = {}
    if style:
        if style not in styles:
            sys.exit(f"Unknown style '{style}'. Known: {', '.join(sorted(styles))}")
        preset = styles[style]

    # Precedence: explicit value on the line/CLI  >  style preset  >  model default (omitted).
    params = {}
    for k in ("exaggeration", "cfg_weight", "temperature", "top_p", "top_k", "min_p", "repetition_penalty"):
        v = spec.get(k)
        if v is None:
            v = preset.get(k)
        if v is not None and k in MODEL_PARAMS[model_name]:
            params[k] = v

    final_text = build_text(text, model_name, preset)
    voice_path = resolve_voice(voices_dir, d.get("voice"))
    name = d.get("name") or slugify(text)
    folder = out_root / name
    takes = int(d.get("takes") or 1)
    base_seed = spec.get("seed")
    model = cache.get(model_name)

    for i in range(takes):
        seed = int(base_seed) + i if base_seed is not None else random.randint(0, 2**31 - 1)
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        kwargs = dict(params)
        if voice_path:
            kwargs["audio_prompt_path"] = voice_path
        if model_name == "multilingual":
            kwargs["language_id"] = d.get("language") or "en"
        wav = model.generate(final_text, **kwargs)

        a = trim_silence(wav, model.sr, d["trim_db"], d["trim_pad_ms"]) if d.get("trim") else wav.squeeze(0).cpu().numpy()
        a = peak_normalize(a, d["peak_db"])
        nr = next_take(folder, name)
        fmt = d["format"]
        audio_path = folder / f"{name}-{nr}.{fmt}"
        write_audio(a, model.sr, audio_path, fmt)

        record = {
            "text": text, "sent_text": final_text, "name": name, "style": style or None,
            "model": model_name, "voice": d.get("voice") or None,
            "language": d.get("language") if model_name == "multilingual" else None,
            **params, "seed": seed, "format": fmt, "trim": bool(d.get("trim")),
            "sample_rate": model.sr, "seconds": round(len(a) / model.sr, 2),
            "file": audio_path.name,
        }
        (folder / f"{name}-{nr}.json").write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps({"path": str(audio_path), "seconds": record["seconds"], "seed": seed,
                          "sent_text": final_text}, ensure_ascii=False), flush=True)


def list_things(voices_dir: Path, styles: dict):
    voices = sorted(p.stem for p in voices_dir.glob("*") if p.suffix.lower() in AUDIO_EXT)
    print("models:", ", ".join(MODELS))
    print("voices:", ", ".join(voices) if voices else "(none: built-in voice only)")
    print("styles:")
    for k, v in styles.items():
        print(f"  {k:12s} {v.get('description', '')}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("text", nargs="?", help="the line to speak")
    ap.add_argument("--batch", help="JSON file: a list of line objects")
    ap.add_argument("--list", action="store_true", help="list models, voices and styles, then exit")
    ap.add_argument("--model", choices=MODELS)
    ap.add_argument("--style")
    ap.add_argument("--voice", help="clip name in chatterbox/voices/, or a path")
    ap.add_argument("--language", help="multilingual model: ar da de el en es fi fr he hi it ja ko ms nl no pl pt ru sv sw tr zh")
    ap.add_argument("--name", help="output folder / file stem (default: first words of the text)")
    ap.add_argument("--takes", type=int)
    ap.add_argument("--seed", type=int, help="fixed seed (take i uses seed+i); default random")
    ap.add_argument("--exaggeration", type=float)
    ap.add_argument("--cfg-weight", dest="cfg_weight", type=float)
    ap.add_argument("--temperature", type=float)
    ap.add_argument("--top-p", dest="top_p", type=float)
    ap.add_argument("--min-p", dest="min_p", type=float)
    ap.add_argument("--repetition-penalty", dest="repetition_penalty", type=float)
    ap.add_argument("--format", choices=("wav", "ogg", "mp3"))
    ap.add_argument("--no-trim", action="store_true")
    ap.add_argument("--out", help="output root (default chatterbox/output)")
    args = ap.parse_args()

    root = find_root(Path.cwd())
    cbx = root / "chatterbox"
    settings = cbx / "settings"
    voices_dir = cbx / "voices"
    styles = load_toml(settings / "styles.toml")
    if args.list:
        return list_things(voices_dir, styles)

    cfg = {
        "model": "turbo", "device": "auto", "voice": "", "language": "en", "format": "wav", "takes": 1,
        "trim": True, "trim_db": -45, "trim_pad_ms": 40, "peak_db": -1.0,
    }
    cfg.update(load_toml(settings / "config.toml").get("defaults", {}))

    cli = {k: getattr(args, k) for k in (
        "model", "style", "voice", "language", "name", "takes", "seed", "exaggeration", "cfg_weight",
        "temperature", "top_p", "min_p", "repetition_penalty", "format")}
    if args.no_trim:
        cli["trim"] = False

    if args.batch:
        lines = json.loads(Path(args.batch).read_text(encoding="utf-8"))
        if isinstance(lines, dict):
            lines = [lines]
        # CLI options act as defaults for every line that does not set its own.
        specs = [{**{k: v for k, v in cli.items() if v is not None}, **l} for l in lines]
    elif args.text:
        specs = [{**{k: v for k, v in cli.items() if v is not None}, "text": args.text}]
    else:
        ap.error("give a line of text, or --batch FILE, or --list")

    out_root = Path(args.out) if args.out else cbx / "output"
    cache = ModelCache(pick_device(cfg["device"]))
    # Group by model so each model loads once.
    specs.sort(key=lambda s: s.get("model") or cfg["model"])
    for spec in specs:
        spec.setdefault("model", cfg["model"])
        if "text" not in spec:
            sys.exit(f"Batch entry has no 'text': {spec}")
        run_line(spec, cfg, styles, cache, voices_dir, out_root)


if __name__ == "__main__":
    main()
