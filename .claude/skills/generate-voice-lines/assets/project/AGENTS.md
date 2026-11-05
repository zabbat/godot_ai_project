# Kokoro - voice design and take checking

Kokoro-82M (Apache-2.0) designs the characters' voices: it blends its built-in voices and renders
each character's calm **voice reference clip**, which Chatterbox then clones for every line. The same
environment runs the Whisper word check that tests Chatterbox takes. How-to is in the skill
`.claude/skills/generate-voice-lines/` - read it before generating.

```
<kok>/
  AGENTS.md          this file
  .gitignore         ignores output/, settings/.venv
  settings/          the locked toolchain
    pyproject.toml   uv project: Python 3.11 + kokoro + faster-whisper + librosa + torch
    .python-version  3.11
    uv.lock          exact package versions (committed)
    .venv/           the environment (git-ignored)
  output/            generated samples and reference takes (git-ignored)
    samples/<name>/      voice auditions
    references/<name>/   reference clip takes (+ .json recipe)
```

Run (from the project root):

```
uv run --project <kok>/settings .claude/skills/generate-voice-lines/assets/scripts/kokoro_reference.py --voice "af_heart:0.5,af_kore:0.5" "Text.|0.85|0.5" "More text.|0.82|0" -o <kok>/output/references/NAME/NAME_ref-1.wav
```

A chosen reference clip leaves `output/`: its master goes to `assets/audio/voice/<name>/` with its
record (the Kokoro recipe), and a copy to the Chatterbox `voices/` folder.
