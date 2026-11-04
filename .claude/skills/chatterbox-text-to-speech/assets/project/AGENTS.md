# chatterbox/ — local text-to-speech for game voices

Index and project notes for generating speech with Chatterbox. How-to is in the skill
`.claude/skills/chatterbox-text-to-speech/` — read it before generating.

```
chatterbox/
  AGENTS.md          this file: index + this game's voice notes
  .gitignore         ignores voices/, output/, settings/.venv
  settings/          the locked toolchain and the knobs
    pyproject.toml   uv project: Python 3.11 + chatterbox-tts + torch (CUDA/CPU backend)
    .python-version  3.11
    uv.lock          exact package versions (committed)
    config.toml      defaults: model, device, format, trimming
    styles.toml      emotion / delivery presets (--style NAME)
  voices/            reference clips, one per character voice (git-ignored)
  output/            generated lines, one folder per line name (git-ignored workshop)
```

Run (from the project root):

```
uv run --project chatterbox/settings .claude/skills/chatterbox-text-to-speech/assets/scripts/speak.py --style angry --voice NAME --name LINE-NAME "text"
```

Chosen takes leave `output/`: copy them into `assets/` (source sounds) and let the asset map
carry them into Godot. `output/` is a workshop and may be deleted at any time.

## Voices (fill in as clips are added)

Chatterbox cannot make a voice from a description, so each clip's **description** below is what
lets Claude pick the right one when you ask for "a gravelly old wizard".

| Voice file | Character | What it sounds like (age, gender, pitch, accent, energy) | Source / rights |
|---|---|---|---|
| _(none yet: the model's built-in voice is used)_ | | | |

## Pronunciation respellings

Names the model gets wrong, and the spelling that works. Use these in every line.

| Written | Say it as |
|---|---|

## Notes

- _Findings about what works in this game's voices go here, not in the skill._
