"""Qwen3-TTS for the generate-voice-lines skill. Runs INSIDE the Qwen Docker container
(see assets/qwen/), from the project root (mounted at /work).

  design  - VoiceDesign: a voice from a text description -> candidate reference clips
  clone   - Base model: speak lines in the voice of a reference clip (batch or one line)

  qwen_voice.py design --instruct "old gravelly wizard, calm" --takes 3 -o tools/qwen3-tts/output/references/wizard/wizard_ref "Reference sentence one. Sentence two."
  qwen_voice.py clone --ref tools/qwen3-tts/voices/wizard.wav --out tools/qwen3-tts/output/wizard --batch lines.json
  qwen_voice.py clone --ref tools/qwen3-tts/voices/wizard.wav --out tools/qwen3-tts/output/wizard --name greet --takes 3 "Welcome, traveler."

lines.json: [{"name": "greet", "text": "...", "takes": 3, "ref": "optional other reference", "language": "English"}]
A reference's transcript is read from its sidecar <ref>.json ("text"), which design and Chatterbox's
speak.py both write; --ref-text overrides it. Every take gets a .json (text, ref, seed, model, seconds).
"""
import argparse, json, sys, time
from pathlib import Path

import soundfile as sf
import torch
from qwen_tts import Qwen3TTSModel

MODELS = {"design": "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign", "clone": "Qwen/Qwen3-TTS-12Hz-1.7B-Base"}


def load(kind):
    t = time.time()
    m = Qwen3TTSModel.from_pretrained(MODELS[kind], device_map="cuda:0", dtype=torch.bfloat16,
                                      attn_implementation="sdpa")
    print(f"loaded {MODELS[kind]} in {time.time() - t:.0f}s", file=sys.stderr, flush=True)
    return m


def next_nr(folder, stem):
    nrs = [int(p.stem.rsplit("-", 1)[1]) for p in folder.glob(f"{stem}-*.wav") if p.stem.rsplit("-", 1)[1].isdigit()]
    return max(nrs, default=0) + 1


def save(folder, stem, wav, sr, meta):
    folder.mkdir(parents=True, exist_ok=True)
    nr = next_nr(folder, stem)
    path = folder / f"{stem}-{nr}.wav"
    sf.write(path, wav, sr)
    meta["seconds"] = round(len(wav) / sr, 2)
    path.with_suffix(".json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"path": str(path), "seconds": meta["seconds"], "seed": meta["seed"]}), flush=True)


def seeded(seed):
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def cmd_design(a):
    model = load("design")
    out = Path(a.o)
    base = a.seed if a.seed is not None else int(torch.randint(0, 2**31 - 1, (1,)))
    for i in range(a.takes):
        seed = base + i
        seeded(seed)
        wavs, sr = model.generate_voice_design(text=a.text, instruct=a.instruct, language=a.language)
        save(out.parent, out.name, wavs[0], sr, {"kind": "design", "model": MODELS["design"], "text": a.text,
                                                 "instruct": a.instruct, "language": a.language, "seed": seed})


def ref_text_for(ref, override):
    if override:
        return override
    side = Path(ref).with_suffix(".json")
    if side.exists():
        return json.loads(side.read_text(encoding="utf-8"))["text"]
    sys.exit(f"no transcript for {ref}: give --ref-text or put the text in {side}")


def cmd_clone(a):
    if a.batch:
        lines = json.loads(Path(a.batch).read_text(encoding="utf-8"))
    else:
        if not (a.text and a.name):
            sys.exit("clone needs --batch, or --name and a text")
        lines = [{"name": a.name, "text": a.text}]
    model = load("clone")
    prompts = {}
    for ln in lines:
        ref = ln.get("ref", a.ref)
        if not ref:
            sys.exit(f"line {ln['name']}: no reference (--ref or \"ref\")")
        if ref not in prompts:
            rt = ref_text_for(ref, None if ln.get("ref") else a.ref_text)
            prompts[ref] = (model.create_voice_clone_prompt(ref_audio=ref, ref_text=rt), rt)
        prompt, rt = prompts[ref]
        base = ln.get("seed", a.seed if a.seed is not None else int(torch.randint(0, 2**31 - 1, (1,))))
        lang = ln.get("language", a.language)
        for i in range(ln.get("takes", a.takes)):
            seed = base + i
            seeded(seed)
            wavs, sr = model.generate_voice_clone(text=ln["text"], language=lang, voice_clone_prompt=prompt)
            save(Path(a.out) / ln["name"], ln["name"], wavs[0], sr,
                 {"kind": "clone", "model": MODELS["clone"], "text": ln["text"], "ref": ref, "ref_text": rt,
                  "language": lang, "seed": seed})


p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
sub = p.add_subparsers(dest="cmd", required=True)
d = sub.add_parser("design")
d.add_argument("text")
d.add_argument("--instruct", required=True, help="the voice description")
d.add_argument("-o", required=True, help="output stem, e.g. dir/wizard_ref -> dir/wizard_ref-<nr>.wav")
d.add_argument("--takes", type=int, default=3)
d.add_argument("--language", default="English")
d.add_argument("--seed", type=int)
d.set_defaults(fn=cmd_design)
c = sub.add_parser("clone")
c.add_argument("text", nargs="?")
c.add_argument("--ref")
c.add_argument("--ref-text")
c.add_argument("--out", required=True, help="output root; takes go to <out>/<name>/<name>-<nr>.wav")
c.add_argument("--batch")
c.add_argument("--name")
c.add_argument("--takes", type=int, default=3)
c.add_argument("--language", default="English")
c.add_argument("--seed", type=int)
c.set_defaults(fn=cmd_clone)
a = p.parse_args()
a.fn(a)
