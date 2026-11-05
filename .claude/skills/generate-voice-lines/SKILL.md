---
name: generate-voice-lines
description: Make a game character's spoken lines so every line sounds like the same person and fits the moment. Designs the character's voice once with Kokoro (blending its built-in voices into one calm 6-8 s reference clip), then generates each line with Chatterbox from that one clip, with the delivery chosen by the kind of line (speech - greetings, dialogue, blessings; battle - spell calls, battle cries, commands). Makes 5 takes per line, checks every take's words automatically with Whisper, can cut a short line out of a longer one, and lets the user choose. Reads who the character is and how they talk from the game-character bible (Voice section), or asks and offers to write it down. Installs Kokoro and the checker ("init kokoro") into the project's Kokoro folder. Use when the user asks for voice lines, dialogue, a greeting, a spell call, a battle cry or barks for a character, wants to create, redo or change a character's voice or voice reference, or says "init kokoro".
---

# Generate voice lines

Makes a character's spoken lines in two steps, because no single local tool does both:

1. **Kokoro designs the voice.** It cannot act, but it blends its 54 built-in voices into a new,
   stable voice. It renders one **calm 6-8 s reference clip** per character.
2. **Chatterbox acts the lines.** It clones the reference clip and adds the emotion. Every line of
   the character is generated **from that one clip**, with the English model; the kind of line
   (its **mode**) only changes the settings and the wording.

Why it is done this way (all from tests; details in the references):
- One calm reference, intensity added **once**, in the settings. A reference that is already intense
  plus high exaggeration sounds mechanical and sped up.
- Every round of cloning loses quality: lines are generated from the Kokoro clip, never from another
  Chatterbox take.
- 5 takes per line; for battle lines only 1-2 are good. The user always chooses by ear.

The engine is the `chatterbox-text-to-speech` skill (install, `speak.py`, batch format, models):
this skill uses it, it does not replace it. Characters are the `game-character` skill; where files
go in the repo is the `godot-ai-architecture` skill.

| File | What |
|---|---|
| [references/voice_design.md](references/voice_design.md) | Kokoro: every voice with grade and description, blend recipes, auditions, the reference clip rules. **Read before making a reference.** |
| [references/line_modes.md](references/line_modes.md) | The modes (speech, battle) with their settings, how to write the text, short lines (long + cut). **Read before generating lines.** |
| `assets/scripts/kokoro_reference.py` | Render a reference clip: voice blend + text parts with speed and pause; checks 6-8 s; writes the recipe `.json`. |
| `assets/scripts/kokoro_samples.py` | Audition voices and blends on one line. |
| `assets/scripts/check_takes.py` | Whisper word check of Chatterbox takes (+ pitch against the reference), and `--keep` cuts a line out of a longer take. |
| `assets/project/` | Copied into the project's Kokoro folder by "init kokoro" (locked uv environment, `.gitignore`, `AGENTS.md`). |

## Where things live

Paths come from the root `AGENTS.md` "Project paths" table (`godot-ai-architecture` skill):

| Name below | What | Default |
|---|---|---|
| `<kok>` | Kokoro folder: settings, samples and reference takes | `tools/kokoro/` (row "Kokoro") |
| `<cbx>` | Chatterbox folder: `voices/`, line takes in `output/` | `tools/chatterbox/` (row "Chatterbox") |
| reference master | the chosen reference clip + its record (the Kokoro recipe) | `assets/audio/voice/<name>/<name>_voice_reference.wav` + `.md` |
| line masters | chosen takes of each line | `assets/audio/voice/<name>/<name>_<line>/` |

If a row is missing, ask once (suggest the default) and add it; never write to the repo root. The
reference clip is a resource, not documentation: **its master lives in `assets/`, never in `docs/`**.
It is not exported to Godot (no asset map entry); Chatterbox uses a copy at `<cbx>/voices/<name>.wav`
(git-ignored).

Run every script from the project root with the project's environment:

```
uv run --project <kok>/settings .claude/skills/generate-voice-lines/assets/scripts/<script>.py ...
uv run --project <cbx>/settings .claude/skills/chatterbox-text-to-speech/assets/scripts/speak.py ...
```

## "init kokoro" - install

Also run it when `<kok>/settings/.venv` is missing and a reference or a take check is needed.

1. **Check:** `uv` installed (the Chatterbox skill's install section says how to get it), NVIDIA GPU
   (`nvidia-smi`; driver >= 570 for cu128). Kokoro and Whisper also run on CPU: without an NVIDIA
   GPU switch the torch backend in `settings/pyproject.toml` as its comment says, then `uv lock`.
2. **Copy** `assets/project/` to `<kok>/` (never overwrite existing files), replace `<kok>` in its
   `AGENTS.md` with the real folder. Add the "Kokoro" row to the root `AGENTS.md` Project paths, a line
   to the parent index (`tools/AGENTS.md`), and `<kok>/output` to the asset map's `outputs` list
   (`prototype/asset_map/settings.toml`) if the project has one.
3. **Install:** `uv sync --project <kok>/settings` (PyTorch is ~3 GB: run it in the background and
   tell the user). Verify:
   `uv run --project <kok>/settings python -c "import kokoro, faster_whisper, torch; print(torch.__version__, torch.cuda.is_available())"`
4. **Smoke test:** render a short reference with `kokoro_reference.py` (it will WARN about the
   length; that is fine for a test) into `<kok>/output/smoke-test/`. The first run downloads the
   Kokoro model (~330 MB); the first `check_takes.py` run downloads Whisper `small.en` (~460 MB).
   Both go to the user's Hugging Face cache, shared by all projects.
5. Chatterbox must be installed too: if `<cbx>/settings/.venv` is missing, run the
   `chatterbox-text-to-speech` skill's "init chatterbox".

Windows: "To support symlinks on Windows..." warnings from Hugging Face are harmless.

## 1. The character

Lines need to know who speaks. Find the character in this order:

1. **The game-character bible**: `docs/characters/<type>/<name>/<name>.md` (path from "Character
   bibles" in Project paths). Read its **Voice** section (pitch, energy, way of talking, favourite
   phrases, greeting, voice reference) and **Background** (personality, role). Also read the
   resource sheet (`prototype/characters/<type>/<name>.md`): rows like "Voice reference", "Greeting
   line", "Spell calls" say what is needed and what exists.
2. **Nothing found, or the Voice section is thin** (pitch or way of talking `(open)`): ask. Needed:
   age and gender, role, pitch (low / mid / high for their gender), energy and mood, how they talk
   (formal, casual, rough...), favourite phrases, accent (US or UK English), and their **main
   emotional mode** (when are they intense: battle, anger, fear?). Offer concrete suggestions from
   the game design. Then **offer to write it down**:
   - the project has character bibles: write the answers into the bible's Voice section (create
     the character with the `game-character` skill if it has none);
   - no character structure: suggest "set up characters" (`game-character`), or a voice profile
     `docs/characters/<name>/<name>.md` with only a Voice section.
   Never invent silently: proposals are marked `(proposed)`.

## 2. The line

Get the **text** and the **kind of line**: greeting, dialogue, spell call, battle cry, hurt...
(the user's words, the bible, or the resource sheet row). The kind picks the **mode** in
[references/line_modes.md](references/line_modes.md); ask when it is unclear ("Is this said in
battle or in the city?"). Read line_modes.md's writing rules and adjust the text only where they say
so (one CAPITAL peak, "begone" as one word); say what you changed. A kind with no mode yet: say it is
untested and use line_modes.md's "Kinds not tested yet".

## 3. The voice reference

Look for it: the bible's "Voice reference" line, the sheet's "Voice reference" row, or
`assets/audio/voice/<name>/<name>_voice_reference.wav`. Make sure the copy `<cbx>/voices/<name>.wav`
exists (copy it from the master if not; register it in `<cbx>/AGENTS.md` voices table).

**No reference yet: make it first** (tell the user that is the first step), following
[references/voice_design.md](references/voice_design.md):

1. Propose a **blend of 2-4 voices** from the description, anchored on a good voice; say why each.
   Offer auditions (`kokoro_samples.py` into `<kok>/output/samples/<name>/`) if the user wants to
   listen first.
2. Write **two calm reference texts** (two sentences, ~16 words each, in the character's normal
   tone and way of talking, using their favourite phrases).
3. Render both with `kokoro_reference.py` into `<kok>/output/references/<name>/<name>_ref-<nr>.wav`
   (each sentence a part with a 0.5 s pause, speed 0.82-0.85). Re-render any that is not 6-8 s.
4. Open them for the user (`code -r "<path>"`) and **let them choose**.
5. Save the chosen one:
   - master: `assets/audio/voice/<name>/<name>_voice_reference.wav`, and its record
     `<name>_voice_reference.md` (first line `Audio: <take file name>`, which the sync check reads;
     then from the take's `.json`: Kokoro model, blend, every part's text, speed and pause, length,
     pitch, license Apache-2.0, date, "reference for Chatterbox, not used in the game"); add the
     folder to `assets/AGENTS.md` if new. The asset map settings list `*_voice_reference.wav` under
     `asset_records` so the sync check does not call it unused (add it if the project's
     `settings.toml` lacks it);
   - copy to `<cbx>/voices/<name>.wav`, register it in `<cbx>/AGENTS.md` (character, description,
     source "Kokoro blend ..., see assets record");
   - bible Voice section: `Voice reference: [<name>_voice_reference.wav](<relative path>)` + the
     blend in one line; resource sheet row "Voice reference" -> `chosen` with Master and Take.

Changing the reference later changes every line: lines made from the old one become `outdated` on
the sheet (game-character rule), so ask before replacing it.

## 4. Generate the lines

1. Build a batch for `speak.py` (scratch file or `<cbx>/lines.json`), one entry per line version,
   **always** `"model": "english"`, `"voice": "<name>"`, the mode's `exaggeration` and `cfg_weight`,
   `"takes": 5`. Names: `<name>_<line>` in snake_case (`defender_spell_light`); for long + cut:
   `<name>_<line>_long`.
2. Short battle lines (about 5 words or fewer): add the **long + cut** version next to the short one
   (line_modes.md), unless the project's Findings already say which works.
3. Run it with `--out <cbx>/output/<name>`; redirect stdout/stderr to files and read the `{` lines
   (Chatterbox skill). A normal request (2-4 lines x 5 takes) needs no confirmation; ask first
   above ~10 lines (50+ takes), since it uses the GPU for a while.

## 5. Check, show, choose

1. **Word check** every line folder with `check_takes.py <folder> --ref <cbx>/voices/<name>.wav`;
   for long + cut add `--keep "<the line>"` (writes `_cut.wav` next to each take). Whisper writes
   "begone" as "be gone" sometimes; the script joins split words back.
2. **Report** in one table per line: take, length, pitch (x reference), flag, what Whisper heard.
   Takes flagged `WORDS` (wrong or missing words) or `FAIL` are listed as "probably bad, listen to
   confirm"; never delete takes. For long + cut, the takes to listen to are the `_cut.wav` files.
3. **Open the folder or the takes** for the user (`code -r`, or the file explorer) and let them
   choose. You cannot hear audio: report only measurements, never "sounds great".
4. Write what the user says works or fails into `<cbx>/AGENTS.md` **Findings** (which mode/settings,
   short vs cut, words that sound synthetic). That is how the modes improve over time.
5. **Chosen takes** go to `assets/audio/voice/<name>/<name>_<line>/` with their `.json` as the record
   (Chatterbox skill "Handing a take to the game"), then the asset map and export
   (`godot-ai-architecture`). Update the resource sheet row (`takes` -> `chosen` -> `in game`).

## Rules

- **One reference per character**, calm, from Kokoro, 6-8 s. Never use a Chatterbox take or an
  intense clip as a reference.
- **English model for every line**; the mode sets exaggeration/cfg. No Turbo style tags for delivery.
- **5 takes per line**; the user chooses; never delete or pick takes silently.
- **Reference master in `assets/`**, never in `docs/`; `voices/` holds only git-ignored copies.
- Kokoro voices are Apache-2.0 and Chatterbox output carries Resemble's PerTh watermark: both are fine
  for games. Never clone a real person's voice without their permission.
- This skill's references are shared between projects: ask before changing them; project findings go
  in `<cbx>/AGENTS.md`.
