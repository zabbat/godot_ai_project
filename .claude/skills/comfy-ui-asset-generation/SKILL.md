---
name: comfy-ui-asset-generation
description: Drive a local ComfyUI server — save the current workflow + prompt to local files, generate images on request, and cut a character out of an image (transparent background). Use when the user says "save" (a ComfyUI setup), "generate image", "generate new image", "cut out", "remove the background" or "make it transparent", or otherwise asks to capture/run ComfyUI prompts, LoRAs, or settings.
---

# ComfyUI support

Helps run and archive image generation for the current project. ComfyUI runs locally and
holds the creative settings (model, LoRAs, sampler, seed, prompt) as a node graph
("workflow"). This skill saves that workflow + prompt to readable local files,
generates images on command, and cuts characters out of images (transparent background,
see "cut out").

Files in this skill's folder: `scripts/cutout.py` (the cut-out run) and
`templates/cutout_transparent.json` (the same graph as a ComfyUI canvas workflow).

If the project has a 2D style doc (`docs/style/2d_style.md`), follow it when writing prompts:
it holds the style keywords, LoRA and settings for each kind of 2D art. If the part you need
says "No style defined yet", ask the user for the style instead of inventing one.

## Server

- Base URL: `http://127.0.0.1:8188`
- Confirm it's up: `GET /system_stats`.
- Key endpoints:
  - `GET /history?max_items=1` — the most recent run. `prompt[1]` = API graph (executable),
    `prompt[3].extra_pnginfo.workflow` = UI graph (the reloadable canvas), `outputs` = saved
    image filenames.
  - `POST /prompt` with `{"prompt": <API graph>}` — queue a render; returns `{"prompt_id": ...}`.
  - `GET /history/{prompt_id}` — poll until it appears (= done); read `outputs`.
  - `GET /view?filename=<f>&subfolder=<s>&type=output` — download a generated image's bytes.
- If the server is unreachable, tell the user to start ComfyUI and stop.

## Source of truth = latest ComfyUI history

The server cannot see the *unsaved* browser canvas. So the rule the user follows:

> **After changing anything in ComfyUI, Queue Prompt once.** That run becomes the latest
> history entry — the current setup I read from.

Whenever a command needs "the current setup," read it from `GET /history?max_items=1`.
If history is empty, ask the user to Queue Prompt once in ComfyUI first.

## Files & naming

Everything lives under a `test-shot/` directory at the root of the current project (create it
if it doesn't exist). **Each asset gets its own subfolder** inside `test-shot/`, and that
subfolder holds all of the asset's files — the images, the `.json`, and the `.md`:

```
test-shot/
  <xxx>-asset-<description>/          ← one folder per asset
    <xxx>-asset-<description>.json
    <xxx>-asset-<description>.md
    <xxx>-asset-<nr>-<description>.png
    <xxx>-asset-<nr>-<description>.md
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
| `<xxx>-asset-<description>.json` | no | the reloadable UI workflow; **updated in place** each generate |
| `<xxx>-asset-<description>.md` | no | the user's `Asset:` / `Notes:` prose; **updated in place**, prose preserved |
| `<xxx>-asset-<nr>-<description>.png` | yes (`nr`) | one per generation, never overwritten |
| `<xxx>-asset-<nr>-<description>.md` | yes (`nr`) | the exact prompt/settings that produced that `nr`'s image — **written once, never overwritten** |

> Why two `.md` kinds: the asset-level one holds the user's evolving description/notes, which
> aren't tied to any one render. The per-image one is a frozen record of what actually produced
> that specific `.png` — so "use image 3's setup but add y" is answerable by reading
> `<xxx>-asset-3-<description>.md` directly, instead of only ever having the latest generation's
> settings.

### Determining numbers

Scan the asset subfolders under `test-shot/`. Folder names match
`^(\d{3})-asset-(.+)$`; per-image files within match
`^(\d{3})-asset-(\d+)-(.+)\.(png|md)$`.
- **Current asset** = the highest `xxx` folder present (the one most recently worked on).
- **Next version** for an asset = (max `nr` seen among that asset's `.png`/per-image `.md` files) + 1.
- **New asset** = (max `xxx`) + 1 → create a new `test-shot/<xxx>-asset-<description>/` folder,
  `nr` resets to 1.

## Commands

### "save"
Capture the current ComfyUI setup without rendering.
1. Read latest history → UI workflow + API graph.
2. Determine asset: if continuing the current asset, reuse its `xxx`/`description`; if it's a
   fresh concept, treat as a new asset (see "generate new image" numbering). Ask the user for
   a short description if it isn't obvious.
3. Write `<xxx>-asset-<description>.json` (the UI workflow) and `<xxx>-asset-<description>.md`
   into the asset's folder `test-shot/<xxx>-asset-<description>/` (create it if new).

### "generate image"  → render into the **current** asset
1. Read latest history → API graph + UI workflow.
2. **Randomize the seed** in the API graph (set `seed`/`noise_seed` on KSampler-type nodes to a
   fresh random int) so you get a new variation rather than a cached repeat — unless the user
   says to keep the seed.
3. `POST /prompt`, poll `GET /history/{prompt_id}` until complete.
4. Download the output via `/view` and save into the asset's folder as
   `test-shot/<xxx>-asset-<description>/<xxx>-asset-<nr>-<description>.png` (next `nr`).
5. **Update in place** the asset's `.json` (current UI workflow) — reloadable canvas state.
6. **Write** (don't overwrite anything) a new per-image
   `<xxx>-asset-<nr>-<description>.md` with that `nr`'s exact prompt/settings — see template
   below. This file is a frozen record; it is never edited again once written.
7. **Display the image** (see below) so the user sees it without clicking.

If the user asks to reuse an earlier version's setup (e.g. "use image 3's prompt but add
y"), read that `nr`'s per-image `.md` for the exact prompt/settings to start from, rather than
assuming the latest generation's settings still apply.

### "generate new image"  → start a **new** asset
Same as "generate image" but: `xxx` = max + 1, `nr` = 1, create a fresh
`test-shot/<xxx>-asset-<description>/` folder, and write a fresh asset-level `.json` + `.md`
(the `Asset:`/`Notes:` file) plus the first per-image `<xxx>-asset-1-<description>.md`.
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
2. **Run** `scripts/cutout.py` (in this skill's folder) with ComfyUI's Python:
   ```
   <python.exe> -I <skill>/scripts/cutout.py <source.png> <out.png> --graph-out <graph.json>
   ```
   Options: `--shrink N` (px the mask shrinks to drop a fringe of background colour,
   default 1), `--blur S` (edge blur sigma, default 1.0; lower = harder edge).
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
user wants it in ComfyUI's workflow list and it isn't there yet, copy it to
`ComfyUI/user/default/workflows/` (load an image in its Load Image node before running).

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

Prompt: <positive prompt text>
LoRAs: <name @ strength, …>
Model: <unet/checkpoint>   VAE: <vae>
Sampler: <sampler> / <scheduler>   Steps: <n>   CFG: <n>   Seed: <n>
Image: <xxx>-asset-<nr>-<description>.png
```

## Constraints
- Can't operate the ComfyUI canvas like a mouse user, and can only use models/LoRAs already
  installed.
- The reloadable `.json` is the **UI workflow** graph (drag it onto the canvas to restore it),
  not the API graph.
- Generations use the user's GPU — confirm before kicking off batches.
