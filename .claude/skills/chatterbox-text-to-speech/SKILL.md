---
name: chatterbox-text-to-speech
description: Generate game voice lines locally with Chatterbox text-to-speech - emotional and styled delivery (angry, afraid, happy, whispering, sarcastic, dramatic, crying, laughing, sighing...), character voices cloned from a short reference clip, variants and takes, batches of dialogue, many languages - saved with a reproducible .json per take. Installs and locks Chatterbox with uv ("init chatterbox") into a chatterbox/ folder with settings/ (locked Python 3.11, packages, defaults, style presets) and a git-ignored voices/ folder. Use when the user says "init chatterbox", wants to install or set up Chatterbox, or asks to generate speech, a voice line, dialogue, NPC barks, narration, a battle cry or a character voice with Chatterbox or local TTS.
---

# Chatterbox text-to-speech for game dev

Generates spoken lines on the user's own machine with **Chatterbox** (Resemble AI, MIT license, no
API key, no per-line cost). Built for game work: many emotions and delivery styles, a few cloned
character voices, several takes per line, batches of dialogue.

Bundled with this skill:
- `assets/project/` — copied into the project as `chatterbox/` by **"init chatterbox"**:
  `settings/pyproject.toml` (locks Python 3.11 + packages), `settings/.python-version`,
  `settings/config.toml` (defaults), `settings/styles.toml` (emotion/delivery presets),
  `voices/.gitkeep`, `.gitignore`, `AGENTS.md`.
- `assets/scripts/speak.py` — the generator (CLI, batch mode). Run it with `uv run`; never with a system Python.
- `references/game_voice_styles.md` — **read before writing lines or choosing a style**: tags,
  exaggeration/cfg tables, how to type text that performs, line types for games, reference-clip
  rules, troubleshooting a bad take.

## Layout in the project

```
<project>/
  chatterbox/
    AGENTS.md            index + this game's voices and pronunciation respellings
    .gitignore           voices/*, output/, settings/.venv/
    settings/            the locked toolchain and the knobs (everything here is committed except .venv)
      pyproject.toml     uv project: requires-python ==3.11.*, chatterbox-tts (git, pinned commit), torch 2.8.0 (cu128)
      .python-version    3.11
      uv.lock            exact versions (tested set, shipped with the template; re-created by `uv lock` if the backend changes)
      config.toml        default model, device, format, trim, loudness
      styles.toml        presets: --style angry | fear | happy | whisper | ...
      .venv/             the environment (git-ignored)
    voices/              reference clips (git-ignored)
    output/              generated lines: output/<name>/<name>-<nr>.wav + .json (git-ignored workshop)
```

Everything runs through the project, from the project root, so the locked Python is always used:

```
uv run --project chatterbox/settings .claude/skills/chatterbox-text-to-speech/assets/scripts/speak.py [options] "text"
```

(Shortened to `speak.py` below.)

## "init chatterbox" — install

Triggered by "init chatterbox", "set up / install chatterbox", or when `chatterbox/settings/.venv` is missing and the user wants speech.

### 1. Check what is there (PowerShell on Windows)

```powershell
(Get-Command uv  -ErrorAction SilentlyContinue).Source     # uv  (also check ~\.local\bin\uv.exe)
(Get-Command git -ErrorAction SilentlyContinue).Source     # git (Chatterbox installs from GitHub)
nvidia-smi --query-gpu=name,driver_version,compute_cap --format=csv   # NVIDIA GPU?
Test-Path chatterbox\settings\pyproject.toml, chatterbox\settings\.venv
```

| Finding | What to do |
|---|---|
| **uv missing** | Tell the user it is required (it fetches Python 3.11 itself, no system Python needed). Offer to run the installer: Windows `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 \| iex"`, macOS/Linux `curl -LsSf https://astral.sh/uv/install.sh \| sh`. Claude Code must be restarted afterwards to see the new PATH. |
| **git missing** | Tell the user: <https://git-scm.com/downloads>. |
| `chatterbox/settings/pyproject.toml` exists | Do not re-copy. If `.venv` is missing, go to step 3. |
| NVIDIA GPU, driver >= 570 | Default backend (cu128) is right. It also covers RTX 50xx (Blackwell), which needs cu128. |
| NVIDIA GPU, driver < 570 | Ask the user to update the driver; cu128 wheels need it. |
| No NVIDIA GPU (AMD/Intel, CPU only) | Use the **CPU** backend (step 2). Turbo/Nano are usable on CPU, but slowly; Nano is the CPU model. |
| macOS (Apple Silicon) | Use the **mac** backend (step 2); `device = "mps"` or `auto`. |

### 2. Copy the template into the project

Copy `assets/project/` to `<project>/chatterbox/` (create the folder; **never overwrite** files that
already exist, the user may have edited `styles.toml` or `config.toml`). Make sure `voices/.gitkeep`
and `chatterbox/.gitignore` are there: **`voices/` must be git-ignored.**

Switch the torch backend in `chatterbox/settings/pyproject.toml` only if step 1 says so:
- **CPU:** in `[tool.uv.sources]` and `[[tool.uv.index]]` replace `pytorch-cu128` with `pytorch-cpu`
  and `.../whl/cu128` with `.../whl/cpu`.
- **macOS:** delete the two `torch`/`torchaudio` lines in `[tool.uv.sources]` and the whole
  `[[tool.uv.index]]` block (the default PyPI wheels support MPS).

Do **not** replace this with `uv pip install chatterbox-tts` followed by `uv pip install torch ... --index-url`.
`chatterbox-tts` pins `torch==2.6.0`, which has no cu128 build and no support for RTX 50xx GPUs, and
the PyPI release (0.1.7) lacks Nano and Multilingual V3. The pyproject here overrides the pin (torch
2.8.0), installs Chatterbox from GitHub at a pinned commit, and `uv.lock` records all of it.

Add one line for `chatterbox/` to the project's root `AGENTS.md` index if it has one.

### 3. Install

```powershell
uv sync --project chatterbox/settings
```

This downloads Python 3.11 (if absent), PyTorch (~3 GB), and the packages into
`chatterbox/settings/.venv`, from the shipped `uv.lock` (after a backend change, `uv sync` re-locks; commit `uv.lock`). It takes several minutes: run it in the
background and tell the user. Then verify:

```powershell
uv run --project chatterbox/settings python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```

Expect `2.8.0+cu128 True` on NVIDIA. If CUDA is `False` on an NVIDIA machine, the driver is too old
or the CPU backend was installed: fix that before generating.

### 4. Smoke test

```powershell
speak.py --style happy --name smoke-test "Chatterbox is ready."
```

**The first run downloads the model weights from Hugging Face** (several GB for Turbo; it took ~6
minutes on a good connection) into the user's HF cache (`~/.cache/huggingface`), shared by all
projects. Tell the user it is a one-time wait. Later runs skip the download, and a short line takes
seconds to generate on a GPU (about 1000 sampling steps at ~70 it/s on an RTX 5070). Then play the result (see "Show the result").

Report what was installed (Python, torch, GPU, model) and that `voices/` is git-ignored.

## Generating speech

### The three things to ask for

Every line is defined by three controls. When the user asks for a line, get these (infer what is
obvious from the request, ask only what blocks you, and state what you chose):

1. **Voice**: a reference clip in `voices/` (`--voice NAME`), or none for the model's built-in
   voice. Chatterbox **cannot invent a voice from a description**. If the user describes one
   ("old gravelly wizard"), match it against the descriptions in the voices table in
   `chatterbox/AGENTS.md` and pick the closest clip; if none fits, say so and ask for a clip.
2. **Exaggeration** (`--exaggeration`): emotional intensity. 0.25 flat, 0.5 normal, 0.7 warm, 1.0+ theatrical.
3. **CFG** (`--cfg-weight`): roughly pace. Lower is slower and more deliberate (0.2-0.3), 0.5 is
   normal, higher is faster. Note that high exaggeration also speeds speech up, so intense lines usually want a lower CFG.

These two numbers only exist on the **`english`** and **`multilingual`** models. `turbo`/`nano` ignore them. Everything
else (temperature, seed, takes, the wording of the text) is secondary tuning.

### Which model runs: the routing rule

By default (`model = "auto"` in `config.toml`), `speak.py` picks the model **per line** from what
the user wrote. This is the user's rule; keep it exactly:

| The user's request has | Model | Why |
|---|---|---|
| **markers** in the text (`[laugh]`, `[angry]`, `[sigh]`...) and **no** exaggeration/pace | `turbo` | only Turbo understands markers |
| **exaggeration and/or pace** (cfg) and **no** markers | `english` | only English uses those numbers |
| **both** markers and exaggeration/pace | **stop and ask the user** | Turbo ignores the numbers; English cannot use markers |
| neither | `english` (`multilingual` if `--language` is not `en`) | default |
| `--model X` named | X | an explicit choice always wins |

Only what the user put on that line counts as "given". A `--style` preset or `config.toml` does not
count (a preset carries both a tag and numbers; it alone means `english`).

**On a conflict the script exits with code 2 and generates nothing.** Then ask the user, in plain
words, which to keep: (A) keep the markers, run Turbo, pace/exaggeration are ignored; or (B) keep
the numbers, run English, markers are removed from the text. Then rerun with `--model turbo` or
`--model english`. Do not choose for them. In a batch, every line is checked first, so one conflict stops the whole run before any audio is made.

Before running, tidy the markers the user typed: Turbo only knows the **exact** names
`[angry] [fear] [surprised] [whispering] [dramatic] [narration] [advertisement] [happy] [crying]
[sarcastic] [laugh] [chuckle] [sigh] [gasp] [groan] [cough] [clear throat] [sniff] [shush]`.
A near-miss such as `[laughter]` or `[shouting]` is still a "marker" for routing (it selects Turbo or
causes the conflict), but Turbo may read it aloud, so map obvious ones to the exact tag
(`[laughter]` -> `[laugh]`) and tell the user; for one with no equivalent (`[shouting]`), say so
and suggest CAPITALS or `[angry]`. The script warns about unknown markers on stderr, and records
`unknown_markers`, `model_reason` and (when English strips markers) `stripped_markers` in each take's `.json`.

### Choosing a model (`--model`)

| Model | Use for | Emotion controls | Notes |
|---|---|---|---|
| `english` (auto picks it by default) | English game dialogue where you want to set exaggeration and CFG yourself | `exaggeration`, `cfg_weight`, temperature | 500M, original model. |
| `turbo` | English lines that need sounds (`[laugh]`, `[sigh]`, `[gasp]`) or tag-driven emotion; faster | **style tags** + sound tags in the text, voice clip, temperature | 350M. Tags: see the style reference. **Ignores `exaggeration`/`cfg_weight`.** |
| `multilingual` | Other languages (23) and localisation: `--language fr` | `exaggeration`, `cfg_weight` | V3, 500M. Reference clip should match the language, or set `--cfg-weight 0`. |
| `nano` | CPU-only machines, quick drafts | tags like Turbo | 110M, smaller and lower quality. |

All models run without a reference clip (built-in voice). To fix a character's voice, pass `--voice`; Turbo/Nano need a clip longer than 5 s.

Leave the model on `auto` (the routing rule above) unless the user names one. `multilingual` is
chosen for any language other than `en`. Each model downloads its own weights on first use.

### One line

```powershell
speak.py --style angry --voice orc_captain --name orc-taunt --takes 3 "You dare enter my hall?"
```

Options (all optional; command-line values beat the style preset, which beats the model default):

| Option | Meaning |
|---|---|
| `--style NAME` | preset from `settings/styles.toml` (`--list` shows them) |
| `--voice NAME` | clip in `chatterbox/voices/` (no extension) or a file path; omit for the model's built-in voice |
| `--model`, `--language` | `auto` by default (routing rule above); name a model to force it |
| `--name SLUG` | output folder and file stem; default: first words of the text. Use short kebab-case |
| `--takes N` | N different takes of the same line (seeds differ) |
| `--seed N` | fixed seed to reproduce a take (take *i* uses N+*i*) |
| `--exaggeration`, `--cfg-weight` | English/Multilingual only |
| `--temperature`, `--top-p`, `--min-p`, `--repetition-penalty` | sampling; temperature 0.6-1.0 |
| `--format wav|ogg|mp3` | wav default; ogg/mp3 need ffmpeg on PATH |
| `--no-trim` | keep leading/trailing silence (trim is on: right for barks and UI) |
| `--out DIR` | output root instead of `chatterbox/output` |
| `--list` | print models, voices in `voices/`, and styles |

Output: `chatterbox/output/<name>/<name>-<nr>.wav` and `<name>-<nr>.json` (text, the tag-expanded
text that was sent, model, style, voice, all parameters, **seed**, seconds). `<nr>` counts up, so
nothing is overwritten. stdout gets one JSON line per take with the path (plus a few plain library
lines: keep only lines starting with `{`); progress goes to stderr. For a batch, redirect stdout
to a file (`> gen.log 2> gen.err`) instead of piping it to a script that could crash and kill the run.

### Many lines (batch) — the normal way for dialogue

Write a JSON list to a scratch file (or `chatterbox/lines.json`) and run `speak.py --batch FILE`. The
model loads once; a batch of 30 lines costs little more than one. Each entry uses the same keys as the sidecar `.json`:

```json
[
  {"name": "guard-greet-1", "text": "Halt. State your business.", "style": "neutral", "voice": "guard"},
  {"name": "guard-greet-2", "text": "Hold there, traveller.",     "style": "neutral", "voice": "guard", "takes": 2},
  {"name": "guard-hit-1",   "text": "Argh!",                      "style": "pain",    "voice": "guard", "takes": 4},
  {"name": "boss-phase2",   "text": "[laugh] Now you will KNEEL!", "style": "furious", "voice": "boss", "seed": 12}
]
```

Command-line options act as defaults for every entry. To redo or tweak a take, pass its sidecar
`.json` as a one-line batch after editing it.

### How to work (the loop)

1. **Understand the line**: who speaks, to whom, in what state, where in the game (bark, cutscene, UI). If
   the user gives only text, pick the style yourself from `references/game_voice_styles.md` and say which.
2. **Settle the three controls** (voice, exaggeration, CFG; see above). Take values the user gives
   literally. If they give none, pick from a style preset or the table in the style reference and
   say the numbers. Ask only if the voice is unclear and several clips exist; otherwise proceed
   with the built-in voice.
3. **Generate 2-3 takes** of anything that matters; one for quick tests. **Variants** for anything players hear often: 4-8 different wordings and seeds (see the reference).
4. **Show the result**, say what you chose (model, style, voice, seed) and offer the next
   adjustment in plain words ("angrier", "slower", "less theatrical", "another take").
5. **Iterate on the right knob** (reference: "Judging and fixing a take"). Change one thing at a time; keep the seed when comparing a setting, change it when you want a different performance. To compare settings fairly, run the same text and `--seed` with different `--exaggeration` / `--cfg-weight` values and name each take (`--name line-ex08-cfg03`).

Generation uses the user's GPU: confirm before running big batches (roughly more than 20 lines).

### Show the result

Open the take in the user's VS Code window; its media preview plays audio:

```
code -r "<path to the .wav>"
```

For several takes, open each (or list the paths) and ask which one to keep. You cannot hear audio
yourself: never claim a take "sounds right". Report only what you can measure (duration, that it
ran) and let the user judge delivery.

### Voices (cloning)

A character voice is a 6-15 s clean reference clip in `chatterbox/voices/<name>.wav`. See "Reference clips" in the style
reference for what makes a good one. When the user adds a clip, register it in the voices table in `chatterbox/AGENTS.md` (character, notes, and
where the clip came from). **Voices are git-ignored**, because they can be recordings of real people. Only clone voices the user has the rights to (their own, a hired actor, a licensed set);
decline to clone a real person's voice without their permission. Generated audio carries Resemble's PerTh watermark; that is built in.

To create characters without any recording: make a few lines with the built-in voice, keep a good
take of 6+ seconds (or concatenate a few) as `voices/<name>.wav`, and reuse it. That fixes the
voice, so the same character stays consistent across all later lines.

### Styles

`settings/styles.toml` holds presets (neutral, happy, excited, sad, crying, angry, furious, fear,
terrified, surprised, whisper, sarcastic, dramatic, narration, announcer, tired, villain,
evil-laugh, battle-cry, pain, dying). One preset serves every model: tag for Turbo/Nano,
exaggeration/cfg_weight for English/Multilingual. Add a project-specific preset there when a
delivery recurs ("old-wizard", "radio-operator"); do not edit presets the user did not ask about. Raw tags work too:
`[sigh]`, `[laugh]`, `[gasp]` inside the text on Turbo/Nano.

## Handing a take to the game

`output/` is a git-ignored workshop. When the user picks a take:
1. Copy it to the project's source assets (`assets/...` per the repo's AGENTS.md / the `godot-development` skill), with its `.json` next to it as provenance, named by the in-game line id.
2. WAV is fine for short lines; for long lines or size budgets convert with `--format ogg` (Godot imports `.wav` and `.ogg`).
3. Register it in the asset map and let the export script carry it into Godot; use an `AudioStreamRandomizer` for variants. Do not copy into the Godot folder by hand.

## Gotchas

- **Chatterbox is archived** (Resemble AI retired it in August 2026): no updates are coming, so the commit pin in
  `pyproject.toml` is intentional and stable. Do not "upgrade" it.
- **Windows**: a message "To support symlinks on Windows, you either need to activate Developer Mode" is harmless (the script mutes it).
- **First run is slow** (weights). A hang after "loading model" for minutes is the download, not a crash.
- **Out of GPU memory**: lower to one model at a time (the script does), close other GPU apps, or use `nano`/`--device cpu` via `config.toml`.
- **Turbo ignores** `exaggeration` and `cfg_weight`; passing them logs a warning. Use a tag, wording, voice, temperature.
- **Markers only exist on Turbo/Nano.** When English/Multilingual is chosen explicitly (`--model english`) and the text has `[markers]`, the script strips them (with a note) instead of speaking them. Auto routing never gets there: markers mean Turbo or a conflict.
- **Long text drifts**: split above ~40 words, one line per sentence.
- **Run with the project's environment only** (`uv run --project chatterbox/settings`). Do not `pip install` into any other Python, and do not edit `uv.lock` by hand.
- After changing dependencies or the backend, run `uv lock` then `uv sync` in the same way and commit the new `uv.lock`.
