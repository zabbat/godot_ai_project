# Godot AI project template

A template for starting Godot 4 games that are built together with an AI agent (Claude Code). It holds the shared `.claude/` folder (skills and agents), including the starting template for a new game repository.

## What a project built from this looks like

The repo has five working areas. The Godot project can be rebuilt from the other four: nothing about the game may exist only in Godot.

```
<repo>/
  AGENTS.md          repo map, project paths (incl. each tool's folder), rules
  docs/              the game design, for people (+ style/, references/, optional characters/)
  prototype/         the build spec: how it is built in Godot, exact game data, asset map
                     (+ optional characters/: one resource sheet per character)
  assets/            source resources (images, models, sounds, character voice references)
                     + provenance; no code
  tools/             one folder per tool:
    godot-sync/        export_assets.py, check_sync.py
    comfy-ui/          templates/images/, templates/sound-effects/  (the project's own workflow templates, committed);
                       output/images/, output/sound-effects/  (generated takes, git-ignored);
                       ComfyUI/ only if installed for the project (usually an existing install is used)
    chatterbox/        settings/, voices/, output/
    kokoro/            settings/, output/  (voice design, take check)
    blender/           config/, models/
  godot/<project>/   the Godot project
  export/            built game exports (git-ignored)
  downloads/         personal inbox for raw downloads (git-ignored)
  .claude/           skills and agents
```

Flow: `docs/` → `prototype/` → `godot/`, and `downloads/` or a tool's `output/` → `assets/` → asset map → `godot/`. Every folder has an `AGENTS.md` index. Tool skills read their folder from the "Project paths" table in the root `AGENTS.md`; if a project has no row for one, the skill asks once and adds it.

## Start a new project

In Claude Code, from this repo, ask to start a new Godot project (the `godot-ai-architecture` skill, [references/new_project.md](.claude/skills/godot-ai-architecture/references/new_project.md)). It asks for the destination folder, game name, renderer and window size, then:

1. copies `.claude/`,
2. creates all repo and Godot folders,
3. writes the `AGENTS.md` files, standard docs and a minimal `project.godot` / `main.tscn`,
4. copies `export_assets.py`, `check_sync.py` into `tools/godot-sync/` and the asset-map starter files.

The destination must be empty or not exist yet. Tools (Chatterbox, Kokoro, Blender) are set up later by their own skills, into `tools/` ("init chatterbox", "init kokoro", ...).

To bring an existing project up to date with the template, ask to migrate it ([references/migrate.md](.claude/skills/godot-ai-architecture/references/migrate.md)).

## Contents of `.claude/`

| Name | Kind | Purpose |
|---|---|---|
| `godot-ai-architecture` | skill | How the repo is organized (areas, tools, project paths, asset map); starting a new project and migrating an old one; holds the canonical `export_assets.py`, `check_sync.py`, asset-map starters and the repo template |
| `game-character` | skill | Optional, for games with characters: a bible per character (`docs/characters/<type>/<name>/`: by default Appearance, Voice and Background) and a resource sheet (`prototype/characters/<type>/<name>.md`: portraits, model, voice reference, lines, sounds, each with its status); interviews the user, generates what is missing through the tool skills, marks resources outdated when the design changes |
| `godot-development` | skill | Working inside the Godot project: layout, scenes, Resources, shaders and materials, audio, signals, scripts, testing exports |
| `godot-shader-effects` | skill | Writing shaders and visual effects, with example `.gdshader` files |
| `glb-3d-model-and-animations` | skill | Bringing rigged glTF/GLB models and animations into Godot |
| `blender-3d-modeling` | skill | Modeling, animating and exporting in Blender through the Blender MCP, sandboxed in Docker or a VM; sets a project up with its own `.mcp.json` and Blender folder (Dockerfile and launcher in its `assets/docker/`) |
| `comfy-ui-connection` | skill | The one place that knows how to reach ComfyUI, through Comfy-Org's `comfy-cli` (local only, no Comfy Cloud): installs comfy-cli (`uv tool`), picks the ComfyUI install (an existing one, or a new one in `tools/comfy-ui/ComfyUI/`), starts and checks the server, runs graphs, uploads and downloads, fixes failed runs; `scripts/comfy_graph.py` reads the last run and edits API graphs (prompt, seed, size, adding LoRAs); hands a graph to the user to edit on the canvas. The two skills below build on it |
| `comfy-ui-images` | skill | Generating images (and cutting characters out) from workflow templates: bundled `z-image-turbo` (default, built-in nodes only) and `z-image-turbo-res4lyf`, or the project's own; adds LoRAs on request; "save this" makes a take into a project template, linked from the 2D style doc |
| `comfy-ui-sound-effects` | skill | Generating sound effects from workflow templates: bundled `stable-audio-3-sfx` (Stable Audio 3 + an LLM prompt enhancer), or the project's own |
| `chatterbox-text-to-speech` | skill | Local voice lines with Chatterbox: emotional styles, cloned character voices, batches; `init chatterbox` installs it with uv into the project's Chatterbox folder (locked Python 3.11 in `settings/`, git-ignored `voices/`) |
| `generate-voice-lines` | skill | A character's voice and lines: designs the voice with Qwen3-TTS VoiceDesign (one calm default reference clip, master in `assets/audio/voice/<name>/`) and clones it for every line, 3 takes each, Whisper word check; `init qwen` installs Qwen in Docker (asked first). When an emotion does not come through it suggests Chatterbox (English: intensity dial; Turbo: exact tags, limited) and asks whether to keep the result as an extra tone reference. For simple characters or small machines the reference can be a Kokoro blend with Chatterbox lines (`init kokoro`, local or Docker) |
| `godot-resource-manager` | agent | Syncs assets into Godot and updates the docs from the Godot project |

## ComfyUI images and sounds

`comfy-ui-images` and `comfy-ui-sound-effects` say *what* to make and where to keep it;
`comfy-ui-connection` is the only skill that talks to ComfyUI (through `comfy-cli`).

- **Templates, not "run it first".** Each generation starts from a saved workflow template (an
  API-format graph plus a `.md` saying which node holds the prompt, seed, size...). The skills
  bundle defaults; a project adds its own in `tools/comfy-ui/templates/`. Make one by exporting
  from ComfyUI (File → Export (API)), from one run, or from a take you like ("save this as
  fantasy-portrait").
- **Every take keeps its graph** (`<xxx>-asset-<nr>-<desc>.api.json` next to the image and its
  `.md`), so any take can be rerun or turned into a template.
- **The style doc decides.** `docs/style/2d_style.md` names the template, prompt keywords and
  size per kind of art (portraits, icons, UI); the image skill follows it.
- **Use an existing ComfyUI** when there is one (models are large). comfy-cli only sends it
  jobs; it never launches, updates or installs nodes into it. On Windows with Smart App Control
  on, a fresh install is blocked at start; the skill checks before offering one.

## Character voices

Spoken lines keep one voice per character by cloning one reference clip (`generate-voice-lines`):

1. **Qwen3-TTS VoiceDesign designs the voice** from a text description: the user chooses one calm
   **default reference** clip from a few candidates. The master is kept in `assets/audio/voice/<name>/`
   with its description and transcript; the engine uses a git-ignored copy.
2. **Qwen3-TTS (Base model) clones that clip for every line**, 3 takes each, with a Whisper word check;
   the user picks. Qwen runs in Docker on the NVIDIA GPU (installed on request).
3. **Specific emotions** that do not come through in Qwen are made with Chatterbox from the default
   reference: the English model (intensity and pace dials) or Turbo (exact emotion and sound tags, but
   only its fixed tag list). The user is asked whether such a take should also become a **tone reference**
   that Qwen clones for more lines in that tone.
4. **Lightweight route:** for a simple character, or when Qwen is too heavy for the machine, the reference
   is a Kokoro blend of built-in voices and Chatterbox makes the lines (speech, battle and laugh modes).

The Chatterbox/Kokoro tests and lessons behind the lightweight route are in [voice_gen_context.md](voice_gen_context.md).

## Requirements

- Claude Code
- Godot 4 (GDScript only)
- Python 3.11+ with Pillow, and `ffmpeg`, to run the export and sync scripts
- ComfyUI and `comfy-cli` (installed with `uv tool install comfy-cli`), only for the ComfyUI skills; the `comfy-ui-connection` skill offers to install both, or uses an existing ComfyUI. The default templates need these models: images `z_image_turbo_bf16.safetensors`, `qwen_3_4b.safetensors`, `ae.safetensors` (ComfyUI's Z-Image Turbo template downloads them); sounds `stable_audio_3_medium_base.safetensors`, `t5gemma_b_b_ul2.safetensors`, `qwen3.5_2b_bf16.safetensors`. Cut-outs need Impact Pack + Subpack with the YOLO person and SAM models
- Docker with an NVIDIA GPU (8 GB was enough), only for the default Qwen3-TTS route of `generate-voice-lines` (~19 GB image, ~4 GB per model: VoiceDesign and Base)
- `uv` and `git`, only for `chatterbox-text-to-speech` and the Kokoro route of `generate-voice-lines` (an NVIDIA GPU is recommended; Kokoro and the Whisper check also run on CPU). First use downloads the models (Chatterbox several GB, Kokoro ~330 MB, Whisper ~460 MB) into the shared Hugging Face cache. Docker is optional there, only when Kokoro runs in a container (~7.8 GB image)
- Docker and `uv`, only for `blender-3d-modeling`

## Changing the template

Skills and agents are shared between projects, so improve them here first and then copy them into projects. Existing projects are not updated automatically; use the migrate steps.
