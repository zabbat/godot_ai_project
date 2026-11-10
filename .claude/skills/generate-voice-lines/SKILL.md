---
name: generate-voice-lines
description: Make a game character's spoken lines so every line sounds like the same person and fits the moment. Default engine is Qwen3-TTS in Docker - it designs the character's voice once from a text description (VoiceDesign) into one calm default reference clip, then clones that clip for every line (Base model), 3 takes per line, word-checked with Whisper. Not installed yet -> asks to install it in Docker ("init qwen"). When a specific emotion does not come through in Qwen, suggests Chatterbox (English model with exaggeration/pace, or Turbo with exact emotion/sound tags, which is more exact but limited) and asks whether the result should be saved as an extra tone reference for Qwen. For simple characters, or when Qwen is too heavy for the machine, the default reference can be a calm Kokoro voice blend instead, with lines made by Chatterbox (modes speech, battle, laugh). Reads who the character is and how they talk from the game-character bible (Voice section), or asks and offers to write it down. Use when the user asks for voice lines, dialogue, a greeting, a laugh, a spell call, a battle cry or barks for a character, wants to create, redo or change a character's voice or voice reference, or says "init qwen" or "init kokoro".
---

# Generate voice lines

Makes a character's spoken lines so that **every line is the same person**. The voice is fixed once,
in a **default reference clip**; every line is then generated from that clip.

| Route | Reference made by | Lines made by | Use when |
|---|---|---|---|
| **Qwen (default)** | Qwen3-TTS **VoiceDesign**: a voice from a text description | Qwen3-TTS **Base** clones the reference | always, unless one of the other two applies |
| **+ Chatterbox tones** | (same default reference) | **Chatterbox** from the default reference, for one specific emotion | the emotion does not come through in Qwen |
| **Lightweight (Kokoro)** | Kokoro blend of built-in voices | Chatterbox English / Turbo (modes below) | a simple character, or Qwen is too heavy for the machine (no NVIDIA GPU, little VRAM or disk) |

Why it works this way:
- A TTS model that invents a voice from a description invents a **new** one on every call. Consistency
  comes from cloning one chosen clip, not from repeating the description.
- Qwen's clone has **no emotion setting**: it copies the reference's delivery. So the default
  reference is the character's calm, normal tone, and a strong emotion is either wording in Qwen
  or, when that is not enough, a Chatterbox take (exaggeration/pace or exact tags) - optionally saved
  as an extra **tone reference** that Qwen then clones for lines of that tone.
- Every extra round of cloning costs quality: tone references are made from the **default**
  reference, never from another generated take; the user always chooses by ear.

The Chatterbox engine is the `chatterbox-text-to-speech` skill (install, `speak.py`, models, tags). Characters are the
`game-character` skill; where files go in the repo is the `godot-ai-architecture` skill.

| File | What |
|---|---|
| [references/qwen_voices.md](references/qwen_voices.md) | Qwen: VoiceDesign vs clone, writing the voice description and reference text, cloning batches, emotion, checks. **Read before making a Qwen reference or lines.** |
| [references/line_modes.md](references/line_modes.md) | Chatterbox modes (speech, battle, laugh): settings and text writing. **Read before generating lines with Chatterbox** (tone references, or the Kokoro route). |
| [references/voice_design.md](references/voice_design.md) | Kokoro: every voice with grade and description, blend recipes, auditions, reference clip rules. **Read before making a Kokoro reference.** |
| `assets/scripts/qwen_voice.py` | Runs in the Qwen container: `design` (candidate references from a description) and `clone` (lines from a reference, batch, takes, `.json` per take). |
| `assets/qwen/` | `Dockerfile` + `compose.yaml` for the Qwen image, copied to `<qwen>/docker/` by "init qwen". |
| `assets/qwen_project/` | Copied into the project's Qwen folder by "init qwen": `AGENTS.md` (voices table, findings), `.gitignore`, `voices/`. |
| `assets/scripts/check_takes.py` | Whisper word check of takes (+ pitch against the reference), and `--keep` cuts a line out of a longer take. Runs in the Qwen container (CPU). |
| `assets/scripts/cut_take.py` | Prints a take's loudness over time and cuts a part out of it with fades. For sounds Whisper cannot place; only when the user asks. |
| `assets/scripts/kokoro_reference.py`, `kokoro_samples.py`, `kokoro_docker.py` | Kokoro route: render a reference clip / audition voices (locally or through the Kokoro Docker server). |
| `assets/project/`, `assets/docker/compose.yaml` | Kokoro route: copied into the project's Kokoro folder by "init kokoro" (locked uv environment) / the Kokoro server compose file. |

## Where things live

Paths come from the root `AGENTS.md` "Project paths" table (`godot-ai-architecture` skill):

| Name below | What | Default |
|---|---|---|
| `<qwen>` | Qwen3-TTS folder: Docker files, `voices/`, candidates and line takes in `output/` | `tools/qwen3-tts/` (row "Qwen3-TTS") |
| `<cbx>` | Chatterbox folder: `voices/`, line takes in `output/` (tone references, Kokoro route) | `tools/chatterbox/` (row "Chatterbox") |
| `<kok>` | Kokoro folder: settings, samples and reference takes (Kokoro route only) | `tools/kokoro/` (row "Kokoro") |
| reference master | the chosen reference clip + its record (the Kokoro recipe) | `assets/audio/voice/<name>/<name>_voice_reference.wav` + `.md` |
| line masters | chosen takes of each line | `assets/audio/voice/<name>/<name>_<line>/` |

If a row is missing, ask once (suggest the default) and add it; never write to the repo root. The
reference clip is a resource, not documentation: **its master lives in `assets/`, never in `docs/`**.
It is not exported to Godot (no asset map entry); the engines use copies (git-ignored):
`<qwen>/voices/<name>.wav` **with its `<name>.json` transcript next to it**, and `<cbx>/voices/<name>.wav`.

Run every script from the project root with the project's environment:

```
docker compose -f <qwen>/docker/compose.yaml run --rm qwen python .claude/skills/generate-voice-lines/assets/scripts/qwen_voice.py ...   # also check_takes.py
uv run --project <cbx>/settings .claude/skills/chatterbox-text-to-speech/assets/scripts/speak.py ...                                       # or in Docker, see Permission errors
uv run --project <kok>/settings .claude/skills/generate-voice-lines/assets/scripts/<kokoro script>.py ...                                  # Kokoro route
```

## "init qwen" - install (Qwen3-TTS in Docker)

Qwen runs **only in Docker** (a Linux container using the NVIDIA GPU); nothing is installed in the host
Python. Run this when the user asks for voice lines or a voice reference and the image `qwen3-tts:1`
or `<qwen>/docker/` does not exist, or says "init qwen". **If it is not installed, ask first**
(AskUserQuestion): install Qwen in Docker (recommended), or the lightweight Kokoro route (for a simple
character, or a machine too small for Qwen). Tell the user what Qwen costs: ~19 GB image, ~4 GB per
model (two models), ~10 min first build, an NVIDIA GPU (it ran on 8 GB).

0. **Reuse an existing Docker first.** Before building anything, look for a Qwen image or container
   the user already has (any project, any tag): `docker images --format '{{.Repository}}:{{.Tag}} {{.Size}}'`
   and `docker ps -a --format '{{.Names}} {{.Image}}'` - names containing `qwen`. Probe each
   candidate: `docker run --rm --gpus all <image> python -c "import qwen_tts; print('ok')"`
   (the image must also have a GPU torch). If one works (several: show them and let the user pick),
   **use it and skip steps 2-3**: run every script in it with the project mounted at `/work`, plus
   the weights cache so the models are not downloaded again (find where: `docker image inspect -f
   '{{.Config.Env}}' <image>` for `HF_HOME`, and `docker volume ls` / the old project's folder for the
   cache that holds `models--Qwen--Qwen3-TTS-*`; mount it at that `HF_HOME`; no cache found: say
   the weights download again, ~4 GB each):
   ```
   docker run --rm --gpus all -v "<project, Windows path>:/work" -v "<weights cache>:<HF_HOME>" -w /work <image> python .claude/skills/generate-voice-lines/assets/scripts/qwen_voice.py ...
   ```
   (Git Bash on Windows: `export MSYS_NO_PATHCONV=1` and write the project path as `$(pwd -W)`.) If the
   image lacks `faster-whisper`/`librosa`, run the word check as
   `sh -c "pip install -q faster-whisper librosa && python .../check_takes.py ..."`.
   Write "Qwen runs: existing image `<image>`" and the exact `docker run` prefix into `<qwen>/AGENTS.md`
   (create the folder from `assets/qwen_project/` as in step 2, without the Docker files) so later
   sessions use it. Only when nothing usable exists, **ask** before building a new image (steps 2-3).
1. **Check:** `docker --version`, `docker info` (the engine must answer; if not, ask the user to
   start Docker Desktop and wait), and the GPU in Docker:
   `docker run --rm --gpus all ubuntu:24.04 nvidia-smi -L` must list it. No Docker or no NVIDIA GPU:
   say Qwen cannot run here and offer the Kokoro route. Installing Docker is the user's decision.
2. **Copy** `assets/qwen/Dockerfile` and `compose.yaml` to `<qwen>/docker/`, and `assets/qwen_project/`
   to `<qwen>/` (never overwrite existing files; replace `<qwen>` in `AGENTS.md` and in the compose
   comments). Add the "Qwen3-TTS" row to the root `AGENTS.md` Project paths, a line to the parent
   index (`tools/AGENTS.md`), and `<qwen>/output` to the asset map's `outputs` list if the project has
   one. Keep `voices/` git-ignored.
3. **Build** once: `docker compose -f <qwen>/docker/compose.yaml build` (~10 min: run it in the
   background and tell the user). The compose file mounts the project at `/work`, so every path in
   the commands is project-relative.
4. **Smoke test:** a `design` run with one short sentence (`--takes 1`) into `<qwen>/output/smoke-test/`.
   The first run downloads the VoiceDesign model (~4 GB, a few minutes) into the volume
   `qwen-hf-cache`; the first clone downloads the Base model the same way. Tell the user it is one-time.
5. Report what was installed or which existing image is used. Chatterbox (tone references) is installed later by the
   `chatterbox-text-to-speech` skill, only when it is needed.

(Step 0 is the rule for any Docker: Qwen, and Chatterbox - the `chatterbox-text-to-speech` skill's
"Chatterbox in Docker" says the same - reuse what exists before creating new images.)

## Lightweight route: Kokoro

Only when the character is simple, or Qwen is too heavy for the machine. Kokoro (82M) blends its built-in voices into the default reference and runs on the CPU; the lines are then made by Chatterbox (section 4, modes).

### "init kokoro" - install

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
5. Chatterbox must be installed for the Kokoro route (it makes the lines): if `<cbx>/settings/.venv` is missing, run the
   `chatterbox-text-to-speech` skill's "init chatterbox".

Windows: "To support symlinks on Windows..." warnings from Hugging Face are harmless.

#### Kokoro in Docker

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

## Permission errors

Qwen already runs in Docker, so it is not affected. If a Kokoro, Whisper or Chatterbox command fails with a permission error, **suggest running Kokoro
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
(the user's words, the bible, or the resource sheet row); a laugh is its own kind. Note the **tone the
user wants** (calm, irritated, shouting...): in Qwen it can only come from the reference and the wording
(section 5 covers what to do when it is missing). On the Chatterbox paths (Kokoro route, tone
references) the kind picks the **mode** in [references/line_modes.md](references/line_modes.md); ask
when it is unclear ("Is this said in battle or in the city?"), read its writing rules and adjust the text
only where they say so (one CAPITAL peak, "begone" as one word); say what you changed. A kind with no
mode yet: say it is untested and use line_modes.md's "Kinds not tested yet".

## 3. The default reference

Look for it: the bible's "Voice reference" line, the sheet's "Voice reference" row, or
`assets/audio/voice/<name>/<name>_voice_reference.wav`. Make sure the engine copies exist
(`<qwen>/voices/<name>.wav` + `<name>.json`, `<cbx>/voices/<name>.wav`; copy them from the master if
not, and register them in the `<qwen>/AGENTS.md` / `<cbx>/AGENTS.md` voices tables).

**No reference yet: make it first** (tell the user that is the first step). Pick the route:

- **Qwen (default).** Needs "init qwen" done (ask to install if not). Follow
  [references/qwen_voices.md](references/qwen_voices.md): propose 2-3 voice descriptions from the
  character's Voice section (new character: let the user pick or edit one), write one calm reference
  text (two sentences, 6-10 s spoken, in the character's way of talking), generate **3 candidates**
  with `qwen_voice.py design`, word-check them, open them (`code -r "<path>"`) and **let the user
  choose**.
- **Kokoro (lightweight)**, when the user chose it or Qwen cannot run here. Needs "init kokoro". Follow
  [references/voice_design.md](references/voice_design.md): propose a **blend of 2-4 voices** from the
  description (offer auditions with `kokoro_samples.py` / `kokoro_docker.py samples`), write **two
  calm reference texts**, render both with `kokoro_reference.py` / `kokoro_docker.py reference` into
  `<kok>/output/references/<name>/<name>_ref-<nr>.wav` (each sentence a part with a 0.5 s pause, speed
  0.82-0.85; re-render any that is not 6-8 s), open them, let the user choose.

Save the chosen one:
- master: `assets/audio/voice/<name>/<name>_voice_reference.wav`, and its record
  `<name>_voice_reference.md` (first line `Audio: <take file name>`, which the sync check reads; then
  the take's `.json` content: Qwen description + text + seed + models, or Kokoro blend + parts; the
  transcript; length; license Apache-2.0; date; "reference for voice cloning, not used in the game").
  Add the folder to `assets/AGENTS.md` if new. The asset map settings list `*_voice_reference*.wav`
  under `asset_records` so the sync check does not call it unused (add it if the project's
  `settings.toml` lacks it);
- copies: Qwen route -> `<qwen>/voices/<name>.wav` **and the take's `.json` as `<qwen>/voices/<name>.json`**
  (its `text` is the transcript cloning needs), plus `<cbx>/voices/<name>.wav` if Chatterbox is or will
  be installed (tone references); Kokoro route -> `<cbx>/voices/<name>.wav`. Register each in the
  voices table of its `AGENTS.md` (character, kind `default`, source);
- bible Voice section: `Voice reference: [<name>_voice_reference.wav](<relative path>)` + the
  description or blend in one line; resource sheet row "Voice reference" -> `chosen` with Master and Take.

Changing the reference later changes every line: lines made from the old one become `outdated` on
the sheet (game-character rule), so ask before replacing it.

## 4. Generate the lines

**Qwen route (default):**
1. Build `lines.json` (scratch file or `<qwen>/lines.json`): one entry per line version,
   `{"name": "<name>_<line>", "text": "...", "takes": 3}` (snake_case names, e.g. `wizard_greet`);
   `"ref"` selects a tone reference (section 5). Write the text as qwen_voices.md says. Say what you
   changed in the user's text.
2. Run `qwen_voice.py clone --ref <qwen>/voices/<name>.wav --out <qwen>/output/<name> --batch <lines.json>`
   (redirect stdout/stderr to files and read the `{` lines). A normal request (a few lines x 3 takes)
   needs no confirmation; ask first above ~10 lines, since it uses the GPU for a while.
3. Check, show and choose (section 6).

**Kokoro route:** Chatterbox makes the lines from the Kokoro reference, by mode. Read
[references/line_modes.md](references/line_modes.md); the kind of line (speech, battle, laugh) picks the
mode - ask when it is unclear ("Is this said in battle or in the city?"), a kind with no mode yet: say it
is untested and use line_modes.md's "Kinds not tested yet". Build a batch for `speak.py`, **always**
`"model": "english"` (laugh mode: `"model": "turbo"`), `"voice": "<name>"`, the mode's `exaggeration` and
`cfg_weight`, `"takes": 5`. Names `<name>_<line>`; short battle lines (about 5 words or fewer) also get the
**long + cut** version (line_modes.md). Run with `--out <cbx>/output/<name>`.

## 5. When the emotion does not come through (Chatterbox, tone references)

Qwen follows the reference's delivery and cannot be told an emotion. When the user says a Qwen take is
missing the feeling (angrier, laughing, crying, whispering, a battle shout...), do not keep re-rolling
Qwen. **Suggest Chatterbox for that line**, and name the two options:

| Chatterbox model | Control | Strength | Limit |
|---|---|---|---|
| **English** | `--exaggeration` (intensity) and `--cfg-weight` (pace) | any emotion by numbers, an intensity dial, longer lines | less exact: the feeling comes from the numbers and the wording |
| **Turbo** | tags in the text: `[angry]`, `[crying]`, `[laugh]`, `[sigh]`... | **the exact emotion or sound**, e.g. a real laugh | limited to Turbo's fixed tag list; no intensity dial; needs a reference clip longer than 5 s; English only |

Use Turbo when the user wants a specific named emotion or sound that has a tag; English when they want
a degree of an emotion or no tag fits. (Markers and numbers on the same line conflict: the Chatterbox
skill's routing rule applies; ask, do not choose.) Generate from the **default reference**
(`<cbx>/voices/<name>.wav`), 3 takes, with `speak.py` (needs "init chatterbox" if missing), and let the
user choose.

Then **ask whether the chosen take should also be added as a reference** (a *tone reference*). Offer
both uses: the take can simply be the final line, or it becomes a reference so that more lines in that
tone are made in Qwen with the same voice. If yes:
- name it `<name>_<tone>` (`wizard_irritated`); master `assets/audio/voice/<name>/<name>_voice_reference_<tone>.wav`
  + `.md` record (the Chatterbox `.json`: model, text, exaggeration/cfg or tag, seed, source default reference);
- copy to `<qwen>/voices/<name>_<tone>.wav` with its `.json` (Chatterbox's sidecar has the `text` Qwen needs;
  tell the user the transcript is the intended text, so a mispronounced word makes the clone prompt
  slightly off - run the word check on it); register it in the `<qwen>/AGENTS.md` voices table as kind `tone`;
- lines of that tone then use `"ref": "<qwen>/voices/<name>_<tone>.wav"` in `lines.json`;
- always make tone references from the **default** reference, never from another tone reference or a Qwen take.
- After the user listens to the Qwen lines made from it, write in the `<qwen>/AGENTS.md` Findings whether the
  tone carried over. This is how the approach is learned; it has not been judged for every emotion.

If the user does not want it saved, the Chatterbox take is just that line's take (section 6).

## 6. Check, show, choose

1. **Word check** every line folder with `check_takes.py <folder> --ref <reference.wav>` (Qwen: in the
   container, `docker compose -f <qwen>/docker/compose.yaml run --rm qwen python .claude/skills/generate-voice-lines/assets/scripts/check_takes.py ...`;
   Kokoro route: `uv run --project <kok>/settings ...` as before). For laughs only length and pitch
   count, not the words; for long + cut add `--keep "<the line>"` (writes `_cut.wav` next to each take).
   Whisper writes "begone" as "be gone" sometimes; the script joins split words back.
2. **Report** in one table per line: take, length, pitch (x reference), flag, what Whisper heard. Takes
   flagged `WORDS` (wrong or missing words), `PITCH` (far from the reference) or `FAIL` are "probably
   bad, listen to confirm"; never delete takes.
3. **Open the folder or the takes** for the user (`code -r`, or the file explorer) and let them
   choose. You cannot hear audio: report only measurements, never "sounds great".
4. Write what the user says works or fails into the `<qwen>/AGENTS.md` **Findings** (Kokoro route:
   `<cbx>/AGENTS.md`): which descriptions gave a stable voice, which emotions needed Chatterbox,
   short vs cut, words that sound synthetic. That is how the skill improves over time.
5. **Chosen takes** go to `assets/audio/voice/<name>/<name>_<line>/` with their `.json` as the record
   (Chatterbox skill "Handing a take to the game"), then the asset map and export
   (`godot-ai-architecture`). Update the resource sheet row (`takes` -> `chosen` -> `in game`).

## Rules

- **One default reference per character**, calm, 6-10 s (Kokoro: 6-8 s). Tone references are extra and
  made from the default one. Never use an intense take as the default reference.
- **Qwen is the default engine; install it in Docker (ask first) when missing.** Offer Kokoro + Chatterbox
  only for simple characters or when Qwen is too heavy for the machine.
- **Suggest Chatterbox only when an emotion does not come through in Qwen**, and ask whether the result
  becomes a tone reference. Turbo is exact but limited to its tags; English has the intensity dial.
- Qwen cloning needs the reference's **transcript** (`<ref>.json`, key `text`) to match the audio.
- **3 takes per Qwen line** (5 per Chatterbox line); the user chooses; never delete or pick takes silently.
- **Reference masters in `assets/`**, never in `docs/`; the engines' `voices/` folders hold only git-ignored copies.
- Qwen3-TTS and Kokoro are Apache-2.0 and Chatterbox output carries Resemble's PerTh watermark: all fine
  for games. Never clone a real person's voice without their permission.
- This skill's references are shared between projects: ask before changing them; project findings go
  in the `<qwen>/AGENTS.md` (or `<cbx>/AGENTS.md`).
