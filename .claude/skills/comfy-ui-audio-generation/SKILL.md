---
name: comfy-ui-audio-generation
description: Drive a local ComfyUI server running a Stable Audio graph — generate sound effects, one-shots, instrument loops and music, and save each sound with an .md of its prompt and settings. Use when the user says "generate sound", "generate new sound", "make a sound effect", "save" (a ComfyUI audio setup), or otherwise asks to create or capture game audio with ComfyUI.
---

# ComfyUI audio generation

Generates and archives game audio for the current project. ComfyUI runs locally and holds a
Stable Audio graph (model, text encoders, sampler, seed, prompt, length). This skill reads that
graph, sets the prompt and settings, renders the sound, and saves it with a readable record of
what produced it. It is the audio twin of the `comfy-ui-asset-generation` skill.

## Server

- Base URL: `http://127.0.0.1:8188`
- Confirm it's up: `GET /system_stats`.
- Key endpoints:
  - `GET /history?max_items=1` — the most recent run. `prompt[2]` = API graph (executable),
    `prompt[3].extra_pnginfo.workflow` = UI graph (the reloadable canvas), `outputs` = saved
    files.
  - `POST /prompt` with `{"prompt": <API graph>}` — queue a render; returns `{"prompt_id": ...}`.
  - `GET /history/{prompt_id}` — poll until it appears (= done); read `outputs`.
  - `GET /view?filename=<f>&subfolder=<s>&type=output` — download a generated file's bytes.
- If the server is unreachable, tell the user to start ComfyUI and stop.
- Use ComfyUI's own Python for scripts that read and post graphs (`python` is not on the PATH):
  `C:\ai\ComfyUI_windows_portable\python_embeded\python.exe` (from Git Bash:
  `/c/ai/ComfyUI_windows_portable/python_embeded/python.exe`). The standard library
  (`json`, `urllib.request`, `random`) is enough. Run it with `-I` and keep scripts in the
  scratchpad, not in the ComfyUI folder.

## Source of truth = latest ComfyUI history

The server cannot see the *unsaved* browser canvas. So the rule the user follows:

> **After changing anything in ComfyUI, Queue Prompt once.** That run becomes the latest
> history entry — the current setup I read from.

Whenever a command needs "the current setup," read it from `GET /history?max_items=1`. If
history is empty, or the latest entry is not the audio graph (no `SaveAudio*` node, for example
because an image was generated since), ask the user to Queue the audio workflow once in ComfyUI.

## The graph

Node ids below are from the user's current Stable Audio workflow (the nodes sit inside a
subgraph, so ids look like `52:31`). Find nodes by `class_type` and role, not by id, in case the
graph changes; the ids are a guide.

| Role | Node (id) | Inputs that matter |
|------|-----------|--------------------|
| User's description | `PrimitiveStringMultiline` (`52:31`) | `value` — plain description, e.g. "The sound of a bowstring letting loose an arrow" |
| Length in seconds | `PrimitiveFloat` (`52:36`) | `value` — feeds `EmptyLatentAudio.seconds` and the enhancer text |
| Category | `CustomCombo` (`52:43`) | `choice` = `Music` / `Instrument` / `SFX` / `One-shot` — picks the enhancer's system prompt |
| Prompt enhancer on/off | `PrimitiveBoolean` (`52:35`) → `ComfySwitchNode` (`52:34`) | `true` = an LLM expands the description; `false` = the description goes to the encoder as-is |
| Prompt enhancer | `TextGenerate` (`52:28`), CLIP `qwen3.5_2b_bf16.safetensors` | `sampling_mode.seed`, `sampling_mode.temperature`, `max_length` |
| Positive encode | `CLIPTextEncode` (`52:6`) | text comes from the switch |
| Negative encode | `CLIPTextEncode` (`52:7`) | `text` — empty by default |
| Model | `CheckpointLoaderSimple` (`52:25`) | `stable_audio_3_medium_base.safetensors` |
| Text encoder | `CLIPLoader` (`52:26`) | `t5gemma_b_b_ul2.safetensors`, type `stable_audio` |
| Sampler | `KSampler` (`52:3`) | `seed`, `steps`, `cfg`, `sampler_name`, `scheduler` |
| Output | `SaveAudioMP3` (`19`) | writes `audio/stable_audio_3_XXXXX.mp3` |

### Capturing the enhanced prompt

When the enhancer is on, the text that actually reaches the sampler is generated inside the run
and does not appear in `outputs`. Before posting, **add a preview node** to the API graph so the
text comes back:

```json
"900": { "class_type": "PreviewAny", "inputs": { "source": ["52:28", 0] } }
```

After the run, read it from `outputs["900"].text[0]` and record it in the per-sound `.md`. Use
an id that isn't already in the graph. Don't add this node to the saved UI workflow.

## Files & naming

Sounds live under `test-shot/sound/` at the project root (create it if missing), next to the
image assets in `test-shot/`. **Each sound gets its own subfolder** holding all its files:

```
test-shot/
  sound/
    <xxx>-sound-<description>/          ← one folder per sound
      <xxx>-sound-<description>.json
      <xxx>-sound-<description>.md
      <xxx>-sound-<nr>-<description>.mp3
      <xxx>-sound-<nr>-<description>.md
    <yyy>-sound-<description>/          ← the next sound, its own folder
      …
```

Example: `test-shot/sound/001-sound-bow-string/001-sound-1-bow-string.mp3`.

`test-shot/sound/` is the workshop. Moving a chosen take into the Godot project (target folder,
in-game name, WAV conversion, `AudioStreamRandomizer`) is described in
`prototype/audio_files.md`, under "Bringing a generated sound into the game".

- **`xxx`** — sound number, zero-padded: `001`, `002`, … Increments on **"generate new sound"**.
- **`nr`** — version within a sound: `1`, `2`, … Increments each **"generate sound"** so earlier
  renders are never overwritten.
- **`description`** — 2–3 word kebab slug, e.g. `bow-string`. Fixed for the life of a sound.

| File | Versioned? | Behavior |
|------|-----------|----------|
| `<xxx>-sound-<description>.json` | no | the reloadable UI workflow; **updated in place** each generate |
| `<xxx>-sound-<description>.md` | no | the user's `Sound:` / `Notes:` prose; **updated in place**, prose preserved |
| `<xxx>-sound-<nr>-<description>.mp3` | yes (`nr`) | one per generation, never overwritten |
| `<xxx>-sound-<nr>-<description>.md` | yes (`nr`) | the exact prompt/settings that produced that `nr`'s sound — **written once, never overwritten** |

Keep the file extension the save node produced (`.mp3` from `SaveAudioMP3`; `.flac`, `.wav`
or `.opus` if the user switches the save node).

### Determining numbers

Scan the subfolders of `test-shot/sound/`. Folder names match `^(\d{3})-sound-(.+)$`; per-sound
files within match `^(\d{3})-sound-(\d+)-(.+)\.(mp3|flac|wav|opus|md)$`.
- **Current sound** = the highest `xxx` folder present.
- **Next version** for a sound = (max `nr` among its audio / per-sound `.md` files) + 1.
- **New sound** = (max `xxx`) + 1 → new folder, `nr` resets to 1.

## Commands

### "save"
Capture the current ComfyUI audio setup without rendering.
1. Read latest history → UI workflow + API graph.
2. Decide the sound: continue the current one, or a new one if it's a fresh concept. Ask for a
   short description if it isn't obvious.
3. Write `<xxx>-sound-<description>.json` (UI workflow) and `<xxx>-sound-<description>.md` into
   `test-shot/sound/<xxx>-sound-<description>/` (create it if new).

### "generate sound"  → render into the **current** sound
1. Read latest history → API graph + UI workflow.
2. Apply what the user asked for: description (`52:31`), length (`52:36`), category (`52:43`),
   enhancer on/off (`52:35`), negative text (`52:7`), steps/CFG. If the user gives no length
   or category, **guess them from the sound** (see "Guessing length and category") and say what
   you picked.
3. **Randomize the KSampler `seed`** to a fresh int so you get a new variation instead of a
   cached repeat — unless the user says to keep it. The enhancer seed (`sampling_mode.seed`)
   stays fixed by default, so the same description gives the same enhanced prompt; randomize it
   too when the user wants a different interpretation of the description.
4. Add the `PreviewAny` node (see "Capturing the enhanced prompt").
5. `POST /prompt`, poll `GET /history/{prompt_id}` until complete.
6. Download the audio from the save node's output via `/view` and save it as
   `test-shot/sound/<xxx>-sound-<description>/<xxx>-sound-<nr>-<description>.mp3` (next `nr`).
7. **Update in place** the sound's `.json` (current UI workflow).
8. **Write** a new per-sound `<xxx>-sound-<nr>-<description>.md` (template below). It is a
   frozen record and is never edited again.
9. **Play the sound** (see below).

If the user asks to reuse an earlier version's setup ("take version 3 but make it longer"), read
that `nr`'s per-sound `.md` for the exact prompt and settings to start from. To reproduce it
exactly, turn the enhancer **off** and send the recorded *encoded prompt* directly, with the
recorded seed.

### "generate new sound"  → start a **new** sound
Same as "generate sound" but: `xxx` = max + 1, `nr` = 1, create a fresh
`test-shot/sound/<xxx>-sound-<description>/` folder, and write a fresh sound-level `.json` +
`.md` plus the first per-sound `<xxx>-sound-1-<description>.md`. Derive a 2–3 word slug from the
description and tell the user (they can rename).

If the user asks for several sounds or variations at once, confirm the count first — renders
use their GPU.

## Play the finished sound

Open the saved file in the user's VS Code window; VS Code's built-in media preview plays it:

```
code -r "<path to the saved .mp3>"
```

Do this as the final step of every render.

## Writing the description

- **Pick the category first.** `SFX` for actions and impacts (bow release, sword hit, door),
  `One-shot` for a single short hit or note (UI click, coin pickup, drum hit), `Instrument` for
  a solo instrument part or loop, `Music` for a full track. The category changes how the
  enhancer expands the description.
- **Keep the description short and concrete** when the enhancer is on: what makes the sound,
  what it hits or moves through, and the space ("in a small stone room", "outdoors, dry").
  The enhancer adds the detail.
- **Set the length to fit the sound** (see the table below). Stable Audio fills the whole
  length, so a 10 s render of a 1 s sound comes back with a tail or repeats.

### Guessing length and category

When the user doesn't give a length (or category), don't reuse whatever is in the graph. Pick
one from how long the sound really lasts in the game, including its natural tail:

| Kind of sound | Examples | Category | Length |
|---------------|----------|----------|--------|
| UI and pickups | button click, coin, menu open, level-up chime | One-shot | 0.5–1.5 s |
| Single hits and releases | gunshot, bow release, sword swing, punch, arrow impact | SFX | 1–2 s |
| Hits with a tail | explosion, cannon, thunder crack, big door slam, spell burst | SFX | 2–4 s |
| Voices and creatures | grunt, death cry, monster roar, skeleton rattle | SFX | 1–3 s |
| Short actions | reload, footsteps run, chest opening, building placed, gate opening | SFX | 2–4 s |
| Ambience and loops | wind, rain, campfire, battlefield, crowd | SFX | 10–30 s |
| Stingers and jingles | victory fanfare, defeat, wave start | Music | 3–8 s |
| Instrument parts | drum loop, lute melody | Instrument | 8–20 s |
| Music tracks | menu theme, battle music | Music | 30–120 s |

Pick the short end for snappy game feedback. Tell the user the length and category you chose
so they can correct it.
- **Describe what you want to hear, in positive words.** Like the image model, the encoder
  reacts to words it sees, so "no music" can pull music in. Use the negative prompt (`52:7`)
  for sounds to avoid instead; this graph runs real CFG (7.0), so negatives do apply.
- **For game use:** ask for a dry, clean sound with a quick start ("tight, close-miked, dry,
  sharp attack") so it sits well in the mix and lines up with the animation.

## `.md` templates

### Sound-level `.md` (`<xxx>-sound-<description>.md`) — updated in place

Holds only the user's prose. Create it for a new sound; otherwise touch it only when the user
edits their own text.

```markdown
# <xxx> — <Description Title>

Sound: <user writes/expands what the sound should be and where it's used in the game>

Notes:
- <user's space>
```

### Per-sound `.md` (`<xxx>-sound-<nr>-<description>.md`) — written once, never edited again

```markdown
# <xxx>-<nr> — <Description Title>

Description: <text of the user-input node>
Category: <SFX / One-shot / Instrument / Music>   Enhancer: <on / off>
Encoded prompt: <the enhanced text from the PreviewAny node, or the description if the enhancer is off>
Negative: <negative text, or "none">
Length: <seconds> s
Model: <checkpoint>   Text encoder: <clip>   Enhancer LLM: <clip of TextGenerate, if on>
Sampler: <sampler> / <scheduler>   Steps: <n>   CFG: <n>   Seed: <n>   Enhancer seed: <n>
Audio: <xxx>-sound-<nr>-<description>.mp3
```

## Constraints
- Can't operate the ComfyUI canvas like a mouse user, and can only use models already installed.
- The reloadable `.json` is the **UI workflow** graph (drag it onto the canvas to restore it),
  not the API graph.
- Generations use the user's GPU — confirm before kicking off batches.
