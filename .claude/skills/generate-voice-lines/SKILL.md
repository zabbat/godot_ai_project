---
name: generate-voice-lines
description: Make a game character's spoken lines so every line sounds like the same person and fits the moment. Designs the character's voice once with Kokoro (blending its built-in voices into one calm 6-8 s reference clip), then generates each line with Chatterbox from that one clip, with the delivery chosen by the kind of line (speech - greetings, dialogue, blessings; battle - spell calls, battle cries, commands; laugh - with Turbo's laugh sound). Makes 5 takes per line, checks every take's words automatically with Whisper, can cut a short line out of a longer one, and lets the user choose. Reads who the character is and how they talk from the game-character bible (Voice section), or asks and offers to write it down. Installs Kokoro and the checker ("init kokoro") into the project's Kokoro folder, locally or with Kokoro in a Docker container (asked at install; suggested when Windows Smart App Control or another policy blocks Python packages with permission errors). Use when the user asks for voice lines, dialogue, a greeting, a laugh, a spell call, a battle cry or barks for a character, wants to create, redo or change a character's voice or voice reference, or says "init kokoro".
---

# Generate voice lines

Makes a character's spoken lines in two steps, because no single local tool does both:

1. **Kokoro designs the voice.** It cannot act, but it blends its 54 built-in voices into a new,
   stable voice. It renders one **calm 6-8 s reference clip** per character.
2. **Chatterbox acts the lines.** It clones the reference clip and adds the emotion. Every line of
   the character is generated **from that one clip**, with the English model (laughs: the Turbo
   model and its `[laugh]` tag); the kind of line (its **mode**) only changes the settings and the wording.

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
| [references/line_modes.md](references/line_modes.md) | The modes (speech, battle, laugh) with their settings, how to write the text, short lines (long + cut). **Read before generating lines.** |
| `assets/scripts/kokoro_reference.py` | Render a reference clip: voice blend + text parts with speed and pause; checks 6-8 s; writes the recipe `.json`. |
| `assets/scripts/kokoro_samples.py` | Audition voices and blends on one line. |
| `assets/scripts/kokoro_docker.py` | The same two jobs (`samples`, `reference`) through a Kokoro server in Docker, same output and `.json`. For a project whose Kokoro runs in Docker. |
| `assets/scripts/check_takes.py` | Whisper word check of Chatterbox takes (+ pitch against the reference), and `--keep` cuts a line out of a longer take. |
| `assets/scripts/cut_take.py` | Prints a take's loudness over time and cuts a part out of it with fades (one laugh out of two). For sounds Whisper cannot place; only when the user asks. |
| `assets/project/` | Copied into the project's Kokoro folder by "init kokoro" (locked uv environment, `.gitignore`, `AGENTS.md`). |
| `assets/docker/compose.yaml` | Template copied to `<kok>/docker/compose.yaml` when Kokoro runs in Docker: the pinned Kokoro-FastAPI server image, local port 8880. |

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

0. **Ask: local or Docker?** (AskUserQuestion, local first as the default.) Explain in one or two
   lines: *local* installs Kokoro in the project's Python environment, the normal way; *Docker* runs
   Kokoro as a small server in a Linux container instead, which **helps against permission
   problems**: Windows security features such as Smart App Control, or antivirus and company
   policies that block Python packages, do not check what runs inside the container. Docker costs a
   ~7.8 GB image and needs Docker Desktop (or another Docker engine) installed; it runs on the CPU,
   which is fast enough for short clips. Recommend Docker when the machine is known to block files
   (see "Permission errors"). Write the choice in `<kok>/AGENTS.md` ("Kokoro runs: local" or
   "Kokoro runs: Docker") so later sessions use the right scripts. Docker: do steps 1-3 below as
   well (the local environment still runs the Whisper check and the pitch measure, which do not
   import Kokoro), then "Kokoro in Docker" instead of step 4.
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

### Kokoro in Docker

When the user chose Docker, or the local Kokoro is blocked (see "Permission errors"):

1. **Check Docker:** `docker --version`, then `docker info` (the engine must answer). If it does
   not, ask the user to start Docker Desktop (on Windows you may offer to start
   `C:\Program Files\Docker\Docker\Docker Desktop.exe`) and wait until `docker info` answers. No
   Docker installed: tell the user where to get Docker Desktop; installing it is their decision.
2. **Copy** `assets/docker/compose.yaml` to `<kok>/docker/compose.yaml` (never overwrite) and add
   the folder to `<kok>/AGENTS.md`. The image tag is pinned there; keep it pinned.
3. **Start:** `docker compose -f <kok>/docker/compose.yaml up -d`. The first start pulls the image
   (~7.8 GB, several minutes: run it in the background and tell the user). Wait until
   `curl -s http://127.0.0.1:8880/v1/audio/voices` returns the voice list (a few seconds after
   the container starts).
4. **Smoke test:** `kokoro_docker.py reference --voice af_heart "Hello there.|1.0|0" -o <kok>/output/smoke-test/test.wav`
   (it WARNs about the length; fine for a test).
5. **Use** `kokoro_docker.py samples` and `kokoro_docker.py reference` wherever this skill says
   `kokoro_samples.py` / `kokoro_reference.py`: same arguments, same output and `.json` (it adds
   the image tag). Run them with the same `uv run --project <kok>/settings` line. Voices, blends,
   speeds and the 6-8 s rule are unchanged.
6. **Stop** the container when the voice work is done: `docker compose -f <kok>/docker/compose.yaml down`
   (it keeps the image, so the next start is quick). Start it again before the next reference.

Port 8880 taken: change the left side of the `ports` line (e.g. `127.0.0.1:8881:8880`) and set
`KOKORO_URL=http://127.0.0.1:8881` for the script.

### Permission errors

If a Kokoro, Whisper or Chatterbox command fails with a permission error, **suggest running Kokoro
in Docker** (and, if more than Kokoro is blocked, the other voice tools too: see below). Signs:
- `ImportError: DLL load failed ...: An Application Control policy has blocked this file.`
- "Access is denied" / `PermissionError` while importing a package (not while writing a file);
- the user sees a Windows notification that something Python-related was blocked.

On Windows check Smart App Control, read-only:
`(Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\CI\Policy').VerifiedAndReputablePolicyState`
(1 = on, 2 = evaluation, 0 = off). Smart App Control has **no per-app allowlist**: the only switch
is off for the whole machine, and on many Windows builds it cannot be turned back on without
resetting Windows. So offer the user:
1. **Kokoro in Docker** (recommended when only Kokoro is blocked): nothing on Windows changes.
2. Turning the blocking feature off: their decision for the whole machine; never suggest it as the
   default.

**Never work around the block** (renaming, re-signing, swapping package versions until one loads,
editing policy). Test what still loads before deciding: in one case only Kokoro's text front-end
(`srsly`, under spaCy) was blocked, while Whisper, librosa and Chatterbox kept working, so Docker was
needed for Kokoro alone. A day later the same machine blocked `_ctypes` in the uv-managed Python
itself, which stops `soundfile` and so **every** local script (Chatterbox, Whisper, even the
`kokoro_docker.py` client).

**Everything blocked: run the voice tools in Docker too.** The Chatterbox skill's "Chatterbox in
Docker" builds one GPU image with both locked environments (`<cbx>/docker/`). Then every command of
this skill runs through it, from the project root, with the same arguments:

```
docker compose -f <cbx>/docker/compose.yaml run --rm voice kok-python .claude/skills/generate-voice-lines/assets/scripts/<script>.py ...   # kokoro_docker.py, check_takes.py, cut_take.py
docker compose -f <cbx>/docker/compose.yaml run --rm voice cbx-python .claude/skills/chatterbox-text-to-speech/assets/scripts/speak.py ...
```

The Kokoro speech server still runs in its own container (`<kok>/docker/compose.yaml up -d`); the
image reaches it at `host.docker.internal:8880` (`KOKORO_URL` is set in the compose file). Write
"Voice scripts run: Docker" in `<kok>/AGENTS.md` so later sessions use these commands.

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
(the user's words, the bible, or the resource sheet row); a laugh is its own kind. The kind picks the **mode** in
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
   Offer auditions (`kokoro_samples.py`, Docker: `kokoro_docker.py samples`, into `<kok>/output/samples/<name>/`) if the user wants to
   listen first.
2. Write **two calm reference texts** (two sentences, ~16 words each, in the character's normal
   tone and way of talking, using their favourite phrases).
3. Render both with `kokoro_reference.py` (Docker: `kokoro_docker.py reference`) into `<kok>/output/references/<name>/<name>_ref-<nr>.wav`
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
   **always** `"model": "english"` (laugh mode: `"model": "turbo"`, see line_modes.md "Laughs"), `"voice": "<name>"`, the mode's `exaggeration` and `cfg_weight`,
   `"takes": 5`. Names: `<name>_<line>` in snake_case (`defender_spell_light`); for long + cut:
   `<name>_<line>_long`.
2. Short battle lines (about 5 words or fewer): add the **long + cut** version next to the short one
   (line_modes.md), unless the project's Findings already say which works.
3. Run it with `--out <cbx>/output/<name>`; redirect stdout/stderr to files and read the `{` lines
   (Chatterbox skill). A normal request (2-4 lines x 5 takes) needs no confirmation; ask first
   above ~10 lines (50+ takes), since it uses the GPU for a while.

## 5. Check, show, choose

1. **Word check** every line folder with `check_takes.py <folder> --ref <cbx>/voices/<name>.wav`
   (for laughs only its length and pitch count, not the words: line_modes.md "Laughs");
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
- **English model for every line**, except laughs (Turbo + `[laugh]`); the mode sets exaggeration/cfg. No Turbo style tags for delivery.
- **5 takes per line**; the user chooses; never delete or pick takes silently.
- **Reference master in `assets/`**, never in `docs/`; `voices/` holds only git-ignored copies.
- Kokoro voices are Apache-2.0 and Chatterbox output carries Resemble's PerTh watermark: both are fine
  for games. Never clone a real person's voice without their permission.
- This skill's references are shared between projects: ask before changing them; project findings go
  in `<cbx>/AGENTS.md`.
