---
name: comfy-ui-sound-effects
description: Use a local ComfyUI (through the comfy-ui-connection skill) running a Stable Audio graph to make game sound effects — impacts, weapon and spell sounds, creature grunts and cries, UI clicks and pickups, short actions, ambience loops — and save each sound with an .md of its prompt and settings. Starts from saved workflow templates (no need to run the graph in ComfyUI first). Use when the user says "generate sound", "generate new sound", "make a sound effect", "save" (a ComfyUI audio setup), "save template", or otherwise asks to create or capture sound effects with ComfyUI. Not for music or spoken voice lines (chatterbox-text-to-speech does speech).
---

# ComfyUI sound effects

Generates and archives game sound effects for the current project. ComfyUI runs locally and
holds a Stable Audio graph (model, text encoders, sampler, seed, prompt, length). This skill reads
that graph, sets the prompt and settings, renders the sound, and saves it with a readable record
of what produced it. It is the sound twin of the `comfy-ui-images` skill.

**Scope: sound effects.** Hits, releases, impacts, spells, creature sounds, UI and pickups, short
actions, ambience and effect loops. Music and instrument parts are out of scope: the graph has
`Music`/`Instrument` categories, but if the user asks for music, say this skill is tuned for
sound effects and ask whether to try anyway. Spoken lines are the `chatterbox-text-to-speech`
skill.

## Talking to ComfyUI: the `comfy-ui-connection` skill

**Load the `comfy-ui-connection` skill first.** It covers everything about reaching ComfyUI: comfy-cli
itself, which install to use, starting the server, reading the current setup, editing and
running a graph, uploading and downloading files. This skill only uses its steps:

- **last run** = `comfy_graph.py latest` → `api.json` (to run) + `ui.json` (to keep). Only
  used when the user says so, or to save a template. If the latest entry is not an audio
  graph (no `SaveAudio*` node), ask the user to queue the audio workflow once.
- **edit** = `comfy_graph.py set` / `seed` / `preview`; **run** = `comfy run --wait`;
  **fetch** = `comfy download <prompt_id>` into a scratch dir, then move the file to its name
  below; **text outputs** = `comfy jobs status <prompt_id>` → `data.text_outputs`.

Always copy a graph to a scratch work dir before editing it; never edit a template or a
sound's saved graph in place except where a step below says so.

## Which graph to start from

The user doesn't have to run anything in ComfyUI first. In this order:

1. **The user names one**: a template by name, or "use my current setup" → the last run.
2. **Continuing a sound** ("generate sound", "another take", "use version 3 but longer") →
   that sound's own `<xxx>-sound-<description>.api.json` (the graph of its latest take). For
   an earlier take, its frozen `<xxx>-sound-<nr>-<description>.api.json`.
3. **A new sound** → the **default template**: the project's default if it has one, else the
   bundled `stable-audio-3-sfx`.

### Templates

A template is a saved audio workflow (API format) with a `.md` whose roles table says which
node does what. Same layout and "save template [name]" steps as in the `comfy-ui-images`
skill (export with File → Export (API), or `comfy_graph.py latest` after one run; find the
roles; clear the description; add it to the index), with these places:

- **Bundled with this skill**: `templates/` in this skill's folder, index `templates/AGENTS.md`.
  Default: **`stable-audio-3-sfx`**; its `.md` has the node ids and defaults.
- **The project's own**: the "Project paths" row **"ComfyUI sound templates"** (suggest
  `tools/comfy-ui/templates/sound-effects/`, committed). Looked in first; a project template
  with the same name or marked default there wins. "save template" writes here; into the
  skill only when the user says it's for all projects.

## The graph

Node ids below are from the bundled `stable-audio-3-sfx` template (the nodes sit inside a
subgraph, so ids look like `52:31`). Another template has its own ids in its `.md`; with a
last run, find nodes by `class_type` and role.

| Role | Node (id) | Inputs that matter |
|------|-----------|--------------------|
| User's description | `PrimitiveStringMultiline` (`52:31`) | `value` — plain description, e.g. "The sound of a bowstring letting loose an arrow" |
| Length in seconds | `PrimitiveFloat` (`52:36`) | `value` — feeds `EmptyLatentAudio.seconds` and the enhancer text |
| Category | `CustomCombo` (`52:43`) | `choice` = `SFX` / `One-shot` (the graph also has `Music` / `Instrument`, out of scope here) — picks the enhancer's system prompt |
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
and is not a saved file. Before running, **add a preview node** to the API graph so the text
comes back:

```bash
comfy_graph.py preview api.json 52:28 --id 900
```

After the run, read it from `comfy jobs status <prompt_id>` → `data.text_outputs["900"]` and
record it in the per-sound `.md`. Use an id that isn't already in the graph. Don't add this
node to the saved UI workflow.

## Where the output goes

The project decides, not this skill. Before the first save or render of a session, find the
**output folder** (`<out>` below):

1. Look in the project's root `AGENTS.md` for a "Project paths" row named like
   **"ComfyUI sound effects output"** and use that path.
2. If there is no such row, **ask the user** where sound takes should go. Suggest
   `tools/comfy-ui/output/sound-effects/` when the project has a `tools/` folder (the
   `godot-ai-architecture` layout); otherwise suggest a folder they name. Then add the row to the
   "Project paths" table (create the table if the `AGENTS.md` has none), so the question is never
   asked again. Make sure the folder is git-ignored if it is inside a git repo (ask first).
3. Never write takes to the project root or anywhere else without a row.

Create `<out>` if it doesn't exist.

## Files & naming

**Each sound gets its own subfolder** inside `<out>`, holding all its files:

```
<out>/
  <xxx>-sound-<description>/          ← one folder per sound
    <xxx>-sound-<description>.json
    <xxx>-sound-<description>.api.json
    <xxx>-sound-<description>.md
    <xxx>-sound-<nr>-<description>.mp3
    <xxx>-sound-<nr>-<description>.md
    <xxx>-sound-<nr>-<description>.api.json
  <yyy>-sound-<description>/          ← the next sound, its own folder
    …
```

Example: `<out>/001-sound-bow-string/001-sound-1-bow-string.mp3`.

Takes stay in `<out>` (never edited or renamed). When the user picks one for the game, the
project's own docs say where its master goes and how it reaches the game (in a Godot AI repo:
copy the take with its per-sound `.md` and the workflow `.json` to `assets/audio/sfx/...`, then
the asset map, per the `godot-ai-architecture` skill; the project's prototype audio doc has the
in-game names and folders). Keep the `Audio: <file>` line in the copied `.md`: it names the take
it came from.

- **`xxx`** — sound number, zero-padded: `001`, `002`, … Increments on **"generate new sound"**.
- **`nr`** — version within a sound: `1`, `2`, … Increments each **"generate sound"** so earlier
  renders are never overwritten.
- **`description`** — 2–3 word kebab slug, e.g. `bow-string`. Fixed for the life of a sound.

| File | Versioned? | Behavior |
|------|-----------|----------|
| `<xxx>-sound-<description>.json` | no | the reloadable UI workflow, if one is known (from the template or the last run); **updated in place** each generate |
| `<xxx>-sound-<description>.api.json` | no | the API graph of the latest take (as run, without the added PreviewAny); **updated in place** each generate; the start for the next take |
| `<xxx>-sound-<description>.md` | no | the user's `Sound:` / `Notes:` prose; **updated in place**, prose preserved |
| `<xxx>-sound-<nr>-<description>.mp3` | yes (`nr`) | one per generation, never overwritten |
| `<xxx>-sound-<nr>-<description>.md` | yes (`nr`) | the exact prompt/settings that produced that `nr`'s sound — **written once, never overwritten** |
| `<xxx>-sound-<nr>-<description>.api.json` | yes (`nr`) | the exact graph of that take (without the added PreviewAny): rerun it, or "save take N as template" — **written once, never overwritten** |

Keep the file extension the save node produced (`.mp3` from `SaveAudioMP3`; `.flac`, `.wav`
or `.opus` if the user switches the save node).

### Determining numbers

Scan the subfolders of `<out>`. Folder names match `^(\d{3})-sound-(.+)$`; per-sound
files within match `^(\d{3})-sound-(\d+)-(.+)\.(mp3|flac|wav|opus|md|api\.json)$`.
- **Current sound** = the highest `xxx` folder present.
- **Next version** for a sound = (max `nr` among its audio / per-sound `.md` files) + 1.
- **New sound** = (max `xxx`) + 1 → new folder, `nr` resets to 1.

## Commands

### "save"
Capture the current ComfyUI audio setup (the last run) into a sound without rendering. To keep
a workflow for reuse, that's "save template" (see "Templates").
1. Read the last run (`comfy_graph.py latest`) → UI workflow + API graph.
2. Decide the sound: continue the current one, or a new one if it's a fresh concept. Ask for a
   short description if it isn't obvious.
3. Write `<xxx>-sound-<description>.json` (UI workflow), `.api.json` (API graph) and
   `<xxx>-sound-<description>.md` into `<out>/<xxx>-sound-<description>/` (create it if new).

### "generate sound"  → render into the **current** sound
1. Copy the starting graph (see "Which graph to start from": normally the sound's `.api.json`)
   to a scratch `api.json`.
2. Apply what the user asked for with `comfy_graph.py set`: description (`52:31`), length
   (`52:36`), category (`52:43`), enhancer on/off (`52:35`), negative text (`52:7`),
   steps/CFG. If the user gives no length
   or category, **guess them from the sound** (see "Guessing length and category") and say what
   you picked.
3. **Randomize the KSampler `seed`** (`comfy_graph.py seed --node 52:3`) so you get a new
   variation instead of a cached repeat — unless the user says to keep it. The enhancer seed
   (`sampling_mode.seed`) stays fixed by default, so the same description gives the same
   enhanced prompt; set a new one (`comfy_graph.py set`) when the user wants a different
   interpretation of the description.
4. Save a copy of the graph as it is now: that's the sound's next `.api.json` (step 7).
   Then add the `PreviewAny` node to the run copy (see "Capturing the enhanced prompt").
5. Run it: `comfy run --workflow api.json --wait`.
6. `comfy download <prompt_id>` and move the audio into
   `<out>/<xxx>-sound-<description>/<xxx>-sound-<nr>-<description>.mp3` (next `nr`).
7. **Write** the take's frozen `<xxx>-sound-<nr>-<description>.api.json` and **update in
   place** the sound's `.api.json` (both the copy from step 4, without the preview node) and,
   if a UI workflow is known, its `.json`.
8. **Write** a new per-sound `<xxx>-sound-<nr>-<description>.md` (template below). It is a
   frozen record and is never edited again.
9. **Play the sound** (see below).

If the user asks to reuse an earlier version's setup ("take version 3 but make it longer"), read
that `nr`'s per-sound `.md` for the exact prompt and settings to start from. To reproduce it
exactly, turn the enhancer **off** and send the recorded *encoded prompt* directly, with the
recorded seed.

### "generate new sound"  → start a **new** sound
Same as "generate sound" but: start from the **default template** (or the one the user
names), `xxx` = max + 1, `nr` = 1, create a fresh `<out>/<xxx>-sound-<description>/` folder,
and write a fresh sound-level `.json` (if the template has a canvas workflow) + `.api.json` +
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

- **Pick the category first.** `SFX` for actions, impacts, creatures and ambience (bow release,
  sword hit, door, roar, wind), `One-shot` for a single short hit or blip (UI click, coin
  pickup, chime). The category changes how the enhancer expands the description.
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

Template: <template name, "sound <xxx>-<nr>" or "last run">
Description: <text of the user-input node>
Category: <SFX / One-shot>   Enhancer: <on / off>
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
