---
name: comfy-ui-images
description: Make images with a local ComfyUI (through the comfy-ui-connection skill) — save the current workflow + prompt to local files, generate images on request, and cut a character out of an image (transparent background). Starts from saved workflow templates (no need to run the graph in ComfyUI first). Use when the user says "save" (a ComfyUI setup), "save template", "generate image", "generate new image", "cut out", "remove the background" or "make it transparent", or otherwise asks to capture/run ComfyUI prompts, LoRAs, or settings.
---

# ComfyUI images

Helps run and archive image generation for the current project. ComfyUI runs locally and
holds the creative settings (model, LoRAs, sampler, seed, prompt) as a node graph
("workflow"). This skill saves that workflow + prompt to readable local files,
generates images on command, and cuts characters out of images (transparent background,
see "cut out").

Files in this skill's folder: `templates/` (bundled workflow templates, see "Templates"),
`scripts/cutout.py` (writes the cut-out graph) and `templates/cutout_transparent.json` (the
same graph as a ComfyUI canvas workflow).

If the project has a 2D style doc (`docs/style/2d_style.md`), it decides the template, style
keywords and size for each kind of 2D art; see "The project's style doc".

## Talking to ComfyUI: the `comfy-ui-connection` skill

**Load the `comfy-ui-connection` skill first.** It covers everything about reaching ComfyUI: comfy-cli
itself, which install to use, starting the server, reading the current setup, editing and
running a graph, uploading and downloading files. This skill only uses its steps:

- **last run** = `comfy_graph.py latest` → `api.json` (to run) + `ui.json` (to keep). Only
  used when the user says so, or to save a template (see "Which graph to start from").
- **edit** = `comfy_graph.py set` / `seed` / `lora`; **run** = `comfy run --wait`; **fetch** =
  `comfy download <prompt_id>` into a scratch dir, then move the file to its name below.
- **hand it to the user** = "Let the user edit the graph in ComfyUI" in that skill: whenever a
  change is unclear or isn't in the template's roles table, or the user wants to tweak it
  themselves.

Always copy a graph to a scratch work dir before editing it; never edit a template or an
asset's saved graph in place except where a step below says so.

## Which graph to start from

The user doesn't have to run anything in ComfyUI first. Pick the starting graph in this
order:

1. **The user names one**: "with the pixel-art template" → that template; "use my current
   setup" / "what I just ran" → the last run (`comfy_graph.py latest`).
2. **Continuing an asset** ("generate image", "another one") → that asset's own
   `<xxx>-asset-<description>.api.json` (the graph of its latest take). "Use image 3's
   setup" → that take's frozen `<xxx>-asset-3-<description>.api.json`.
3. **A new asset of a kind the style doc covers** (a portrait, an item icon...) → the template
   its row names (see "The project's style doc").
4. **Any other new asset** → the **default template** (the project's default if it has one,
   else the bundled `z-image-turbo`). If the request clearly doesn't fit it (e.g. a photo, a
   different style), say so and ask whether to use it anyway, another template, or the last run.

### Templates

A template is a saved, reusable image workflow with a note saying which node does what, so
any prompt, seed and size can be set without reading the graph again.

Templates live in two places, each with an `AGENTS.md` index that marks the default:

- **Bundled with this skill**: `templates/` in this skill's folder, so they work in every
  project. Default: **`z-image-turbo`** (general 2D game art; ComfyUI's own Z-Image Turbo
  template, built-in nodes only, no LoRA, 480x480). Also `z-image-turbo-res4lyf` (same with
  the RES4LYF ClownsharK sampler; needs that node pack).
- **The project's own** (`<templates>`): the "Project paths" row **"ComfyUI image templates"**
  in the root `AGENTS.md` (suggest `tools/comfy-ui/templates/images/`). Templates are tool
  settings, so they are **committed** (not git-ignored).

Look in the project's folder first: a project template with the same name, or one marked
default there, wins over the bundled one. "save template" writes to the project's folder (ask
once for the row if it's missing). Write into this skill's `templates/` only when the user
says it's for all projects.

```
<templates>/
  AGENTS.md                 index: one line per template; marks the default
  <name>/
    <name>.api.json         the graph to run (API format)
    <name>.json             the canvas workflow (drag onto ComfyUI to edit it), if available
    <name>.md               what it is for + the roles table
```

`<name>.md`:

```markdown
# <name>

For: <what it makes, e.g. "2D game art, flat colours, Z-Image Turbo">
Model: <unet/checkpoint>   LoRAs: <name @ strength, or none>   Size: <w>x<h>   Steps: <n>

| Role | Node.input | Default |
|---|---|---|
| Prompt | 57:27.text | (filled in per image) |
| Seed | 57:3.seed | random each run |
| Width / Height | 57:13.width / 57:13.height | 1024 / 1024 |
| Batch | 57:13.batch_size | 1 |
| LoRA strength | 60.strength_model | 0.8 |
```

**"save template [name]"** (also "make this a template", "save as template", "save this
setup for portraits"):
1. Get the graph, one of these ways:
   - **From a take** ("save this", "save image 3 as fantasy-portrait"): copy that take's
     `<xxx>-asset-<nr>-<description>.api.json` (the current asset's latest take when the user
     just says "this") to `<name>.api.json`, and the asset's `.json` canvas workflow if it has
     one. This keeps exactly what made the image, including LoRAs added on request.
   - **From a run**: the user queues the workflow once in ComfyUI → `comfy_graph.py latest
     <templates>/<name>/` and rename its `api.json` / `ui.json` to `<name>.api.json` / `<name>.json`.
   - **Without running**: in ComfyUI, **File → Export (API)** saves the API graph (usually to
     Downloads). Copy it to `<name>.api.json`. **File → Export** (or Save) gives the canvas
     `.json`. Ask for it too, but it is optional.
2. Find the roles from the node summary (`comfy_graph.py nodes`), by `class_type`: the text
   node feeding the sampler's `positive` (prompt), `seed`/`noise_seed` on the samplers,
   `width`/`height`/`batch_size` on the `Empty*LatentImage` node, LoRA loaders. Show the
   table to the user and write `<name>.md`.
3. Clear the prompt text in `<name>.api.json` (`comfy_graph.py set ... text=""`), so an old
   prompt can't leak into a new image.
4. Add the line to `<templates>/AGENTS.md`. If it's the first template, or the user says so,
   mark it **default**.
5. **Ask what kind of art it is for** (portraits, item icons, UI...) and offer to name it in
   that row of the project's style doc, with the prompt keywords and size that went with it
   (see "The project's style doc"). A template only says *how* an image is made; the style doc
   says *which* template and words the game uses for each kind of art.

Check a template still runs after ComfyUI or model changes with
`comfy workflow validate --workflow <name>.api.json` (it names a missing model or node).

### Size

When the user gives a size ("480x480", "portrait 2:3", "wide"), set the template's Width /
Height roles. Without one, keep the template's default. Use multiples of 16 (round and say so:
500 → 496). Very small sizes (under ~512) can look worse with models trained at 1024; if a
small image looks muddy, suggest rendering larger and scaling down afterwards.

### LoRAs

"Add the X LoRA", "use my fantasy LoRA at 0.7", "less LoRA":
1. Find the exact file on the server: `comfy --json model search -t "<words>" --type lora`.
   One clear match → use it; several or none → show the candidates and ask. Never guess a
   file name.
2. Add it to the run copy: `comfy_graph.py lora api.json <file> --strength <s>` (default 0.8;
   0.6-1.0 is the usual range). A second LoRA chains after the first. Change a strength with
   `set <lora id>.strength_model=<s>`; `comfy_graph.py loras` lists them. To drop one, hand
   the graph to the user to edit (or start again from the template).
3. A LoRA usually wants its **trigger words** in the prompt. Ask the user if they know them,
   or check the LoRA's page. Don't invent them.
4. Model match: a LoRA works only with the model family it was trained for (a Z-Image LoRA on
   Z-Image, an SDXL LoRA on SDXL). If the name or the user says otherwise, warn before running.
   LoRAs that also patch the text encoder (SD1.5/SDXL `LoraLoader` with CLIP) are added on
   the canvas: hand the graph to the user.
5. `comfy workflow validate` before the run catches a wrong name. The per-image `.md` records
   every LoRA and strength, and the take's `.api.json` keeps them, so "save this as a template"
   keeps the LoRA.

## The project's style doc

`docs/style/2d_style.md` (see the project's `AGENTS.md`) has one row per kind of 2D art. A
row that defines a style names the **template**, the **prompt keywords** and the **size**:

| 2D art | Template | Style |
|---|---|---|
| Characters (portraits) | `fantasy-portrait` | "80s fantasy film still, painted, warm rim light", 720x720, face centred, plain dark background |

- When the user asks for that kind of art, start from the row's template, put the row's
  keywords in the prompt, and use its size, unless the user says otherwise for this image.
- A row that says "No style defined yet": ask for the style instead of inventing one, and use
  the default template meanwhile if the user says go.
- After "save template" for a kind of art, offer to fill or update its row (template name,
  keywords used, size). Ask first: the style doc is the game's design and is read by people
  too.
- The template must exist (in the project or bundled). If the row names one that's missing,
  say so and ask.

## Where the output goes

The project decides, not this skill. Before the first save or render of a session, find the
**output folder** (`<out>` below):

1. Look in the project's root `AGENTS.md` for a "Project paths" row named like
   **"ComfyUI images output"** and use that path.
2. If there is no such row, **ask the user** where image takes should go. Suggest
   `tools/comfy-ui/output/images/` when the project has a `tools/` folder (the
   `godot-ai-architecture` layout); otherwise suggest a folder they name. Then add the row to the
   "Project paths" table (create the table if the `AGENTS.md` has none), so the question is never
   asked again. Make sure the folder is git-ignored if it is inside a git repo (ask first).
3. Never write takes to the project root or anywhere else without a row.

Create `<out>` if it doesn't exist.

## Files & naming

**Each asset gets its own subfolder** inside `<out>`, and that subfolder holds all of the
asset's files — the images, the `.json`, and the `.md`:

```
<out>/
  <xxx>-asset-<description>/          ← one folder per asset
    <xxx>-asset-<description>.json
    <xxx>-asset-<description>.api.json
    <xxx>-asset-<description>.md
    <xxx>-asset-<nr>-<description>.png
    <xxx>-asset-<nr>-<description>.md
    <xxx>-asset-<nr>-<description>.api.json
  <yyy>-asset-<description>/          ← the next asset, its own folder
    …
```

- **`xxx`** — asset number, zero-padded: `001`, `002`, … Increments on **"new image"**.
- **`nr`** — image version within an asset: `1`, `2`, … Increments each **"generate image"**
  so earlier renders are never overwritten.
- **`description`** — 2–3 word kebab slug, e.g. `walking-road`. Fixed for the life of an asset.

The asset folder name is `<xxx>-asset-<description>`. Per asset you maintain, **inside that
folder**:

| File | Versioned? | Behavior |
|------|-----------|----------|
| `<xxx>-asset-<description>.json` | no | the reloadable UI workflow, if one is known (from the template or the last run); **updated in place** each generate |
| `<xxx>-asset-<description>.api.json` | no | the API graph of the latest take (prompt, seed, size as run); **updated in place** each generate; the start for the next take |
| `<xxx>-asset-<description>.md` | no | the user's `Asset:` / `Notes:` prose; **updated in place**, prose preserved |
| `<xxx>-asset-<nr>-<description>.png` | yes (`nr`) | one per generation, never overwritten |
| `<xxx>-asset-<nr>-<description>.md` | yes (`nr`) | the exact prompt/settings that produced that `nr`'s image — **written once, never overwritten** |
| `<xxx>-asset-<nr>-<description>.api.json` | yes (`nr`) | the exact graph that produced that `nr`'s image (rerun it, or save it as a template) — **written once, never overwritten** |

> Why two `.md` kinds: the asset-level one holds the user's evolving description/notes, which
> aren't tied to any one render. The per-image one is a frozen record of what actually produced
> that specific `.png` — so "use image 3's setup but add y" is answerable by reading
> `<xxx>-asset-3-<description>.md` directly, instead of only ever having the latest generation's
> settings.

### Determining numbers

Scan the asset subfolders under `<out>`. Folder names match
`^(\d{3})-asset-(.+)$`; per-image files within match
`^(\d{3})-asset-(\d+)-(.+)\.(png|md|api\.json)$`.
- **Current asset** = the highest `xxx` folder present (the one most recently worked on).
- **Next version** for an asset = (max `nr` seen among that asset's `.png`/per-image `.md` files) + 1.
- **New asset** = (max `xxx`) + 1 → create a new `<out>/<xxx>-asset-<description>/` folder,
  `nr` resets to 1.

## Commands

### "save"
Capture the current ComfyUI setup (the last run) into an asset without rendering. To keep
a workflow for reuse, that's "save template" (see "Templates").
1. Read the last run (`comfy_graph.py latest`) → UI workflow + API graph.
2. Determine asset: if continuing the current asset, reuse its `xxx`/`description`; if it's a
   fresh concept, treat as a new asset (see "generate new image" numbering). Ask the user for
   a short description if it isn't obvious.
3. Write `<xxx>-asset-<description>.json` (UI workflow), `.api.json` (API graph) and
   `<xxx>-asset-<description>.md` into the asset's folder `<out>/<xxx>-asset-<description>/`
   (create it if new).

### "generate image"  → render into the **current** asset
1. Copy the starting graph (see "Which graph to start from": normally the asset's `.api.json`)
   to a scratch `api.json`. Apply the user's changes (prompt, size, LoRA strength...) with
   `comfy_graph.py set`, using the roles from the template's `.md` (or, for a last run, the
   node summary); add LoRAs as in "LoRAs". Anything else, or anything unclear: hand the graph
   to the user to edit in ComfyUI.
2. **Randomize the seed** (`comfy_graph.py seed`: every `seed`/`noise_seed` on the samplers)
   so you get a new variation rather than a cached repeat — unless the user says to keep it.
3. Run it: `comfy run --workflow api.json --wait`.
4. `comfy download <prompt_id>` and move the image into the asset's folder as
   `<out>/<xxx>-asset-<description>/<xxx>-asset-<nr>-<description>.png` (next `nr`).
5. **Write** the take's frozen `<xxx>-asset-<nr>-<description>.api.json` (the graph just
   run), and **update in place** the asset's `.api.json` (same graph: the start for the next
   take) and, if a UI workflow is known, its `.json`.
6. **Write** (don't overwrite anything) a new per-image
   `<xxx>-asset-<nr>-<description>.md` with that `nr`'s exact prompt/settings — see template
   below. This file is a frozen record; it is never edited again once written.
7. **Display the image** (see below) so the user sees it without clicking.

If the user asks to reuse an earlier version's setup (e.g. "use image 3's prompt but add
y"), start from that take's `<xxx>-asset-3-<description>.api.json` (its per-image `.md` says
the same in words), rather than assuming the latest generation's settings still apply.

### "generate new image"  → start a **new** asset
Same as "generate image" but: start from the template the user names, else the one the style
doc names for this kind of art, else the **default template**; `xxx` = max + 1, `nr` = 1, create a fresh `<out>/<xxx>-asset-<description>/` folder,
and write a fresh asset-level `.json` (copy of the template's canvas workflow, if it has one)
+ `.api.json` + `.md` (the `Asset:`/`Notes:` file) plus the first per-image
`<xxx>-asset-1-<description>.md`.
Derive a 2–3 word `description` slug from the prompt/asset and tell the user (they can rename).
End by **displaying the image** (see below).

### "cut out"  → transparent background for a character
Removes the background around a person or character, giving a PNG with alpha (for art
placed straight on a game screen). Fully local; it uses nodes and models that must already
be installed (the script checks and names anything missing):
- Impact Pack + Impact Subpack nodes (`UltralyticsDetectorProvider`, `SAMLoader`,
  `ImpactSimpleDetectorSEGS`, `SegsToCombinedMask`) and core mask nodes.
- `models/ultralytics/segm/person_yolov8m-seg.pt` and `models/sams/sam_vit_h_4b8939.pth`.

1. **Pick the source** — usually a take of the current asset ("cut out image 2" →
   `<xxx>-asset-2-<description>.png`). It cuts best when the figure was drawn on a **plain
   flat background in a colour the figure doesn't have** (e.g. dark slate blue behind white
   clothes); when generating art meant for cutting out, say so in the prompt (see the
   project's style doc, if any, for its cut-out rules).
2. **Run** it with comfy-cli (commands as in the `comfy-ui-connection` skill):
   1. `comfy upload <source.png>` → the image's name on the server.
   2. Write the graph with `scripts/cutout.py` (in this skill's folder):
      ```
      uv run --no-project --python 3.12 python -I <skill>/scripts/cutout.py <name> <graph.json>
      ```
      Options: `--shrink N` (px the mask shrinks to drop a fringe of background colour,
      default 1), `--blur S` (edge blur sigma, default 1.0; lower = harder edge).
   3. `comfy workflow validate --workflow <graph.json>`: names a missing node or model.
   4. `comfy run --workflow <graph.json> --wait`, then `comfy download <prompt_id>`.

   The graph: YOLO person segmentation → SAM refines the outline → combined mask → shrink
   1 px → slight blur → invert (JoinImageWithAlpha turns `1 - mask` into alpha) → join
   with the image as alpha → save PNG.
3. **Save it as the next take** of the same asset: `<xxx>-asset-<nr>-<description>.png`,
   with a per-image `.md` naming the source take, the script options and the steps (the
   template below, with `Source:` and `Cutout:` lines instead of the prompt). Keep the
   graph next to it as `<xxx>-asset-<description>-cutout_api.json` (drag it onto the canvas
   to load it).
4. **Check the edge**: composite the PNG over a bright colour (e.g. red) and zoom on the
   hair. A visible ring of the old background colour → raise `--shrink` to 2; a jagged edge
   → raise `--blur`; missing thin strands are expected with this method.
5. **Display** it (see below).

The same graph is saved as a canvas workflow in `templates/cutout_transparent.json`. If the
user wants it in ComfyUI's workflow list and it isn't there yet, save it there with
`comfy workflow save --where local` (see `comfy workflow save --help`), or copy it to
`<install>/user/default/workflows/`. Load an image in its Load Image node before running.

For finer hair edges ComfyUI's built-in **RemoveBackground** node (BiRefNet) is better, but
it needs a BiRefNet model in `models/background_removal/`; ask the user before downloading
one.

## Display the finished image

After any generation completes, open the saved PNG in the user's VS Code window so it shows
automatically — they should not have to click the file:

```
code -r "<path to the saved .png>"
```

`-r` reuses the current window. The `code` CLI is available on this machine. Do this as the
final step of every render.

## Writing the prompt

- **Never describe what should be absent.** Do not write "no helm", "no helmet", "no lower
  body", "no legs", "without X", or put those words in a negative prompt. The model reads the
  words themselves and pulls the thing into the image: "no helmet" produces a helmet.
- **Describe what should be visible, in positive words.** Name the framing, the visible parts
  and their look instead: "portrait, head and shoulders", "visible hair", "bare head with short
  dark hair", "face fully visible", "close-up bust".
- **Avoid words that pull in the thing you want gone.** If an object keeps appearing, replace
  its name with a neutral one. For example, "knight" and "armour" bring in helmets, so describe
  the outfit directly ("steel shoulder plates", "red cape", "leather collar") instead.
- **Don't write a negative prompt.** The Z-Image Turbo graph uses zero-out conditioning, so a
  negative prompt has no effect. Leave the negative text node empty.

## Prompt / settings extraction (for the `.md`)

From the workflow graph:
- **Positive prompt** = the text node feeding the sampler's `positive` input. Flux/Z-Image
  graphs often have a single text node — use it. Negative prompts are not used (see
  "Writing the prompt").
- **LoRAs** = `LoraLoader`-type nodes → name + strength.
- **Model/UNet** = checkpoint or `UNETLoader`; **VAE** = `VAELoader`.
- **Sampler/scheduler/steps/CFG/seed** = the KSampler-type node.

## `.md` templates

Two different `.md` files, two different templates.

### Asset-level `.md` (`<xxx>-asset-<description>.md`) — updated in place

Holds only the user's prose. Never touch it except to create it (new asset) or when the user
edits their own text.

```markdown
# <xxx> — <Description Title>

Asset: <user writes/expands what the asset should be>

Notes:
- <user's space>
```

### Per-image `.md` (`<xxx>-asset-<nr>-<description>.md`) — written once, never edited again

A frozen record of exactly what produced that `nr`'s image. Write it fresh each generate;
never update an earlier `nr`'s file.

```markdown
# <xxx>-<nr> — <Description Title>

Template: <template name, "asset <xxx>-<nr>" or "last run">
Prompt: <positive prompt text>
Size: <w>x<h>
LoRAs: <name @ strength, …>
Model: <unet/checkpoint>   VAE: <vae>
Sampler: <sampler> / <scheduler>   Steps: <n>   CFG: <n>   Seed: <n>
Image: <xxx>-asset-<nr>-<description>.png   Graph: <xxx>-asset-<nr>-<description>.api.json
```

## Bringing a take into the game

Takes stay in `<out>` (they are never edited or renamed). When the user picks one for the game,
the project's own rules say where its master goes (in a Godot AI repo: copy the `.png` with its
per-image `.md` and the workflow `.json` to `assets/`, per the `godot-ai-architecture` skill).
Keep the `Image: <file>` line in the copied `.md`: it names the take it came from.

## Constraints
- Can't operate the ComfyUI canvas like a mouse user, and can only use models/LoRAs already
  installed.
- The reloadable `.json` is the **UI workflow** graph (drag it onto the canvas to restore it),
  not the API graph.
- Generations use the user's GPU — confirm before kicking off batches.
