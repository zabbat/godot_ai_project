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
    comfy-ui/          output/images/, output/sound-effects/  (generated takes, git-ignored);
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
| `comfy-ui-connection` | skill | The one place that knows how to reach ComfyUI, through Comfy-Org's `comfy-cli`: installs comfy-cli (`uv tool`), picks the ComfyUI install (an existing one, or a new one in `tools/comfy-ui/ComfyUI/`), starts and checks the server, reads the current setup, runs graphs, uploads and downloads; `scripts/comfy_graph.py` edits API graphs. The two skills below build on it |
| `comfy-ui-images` | skill | Generating images (and cutting characters out) with ComfyUI, through `comfy-ui-connection` |
| `comfy-ui-sound-effects` | skill | Generating sound effects with a ComfyUI Stable Audio graph, through `comfy-ui-connection` |
| `chatterbox-text-to-speech` | skill | Local voice lines with Chatterbox: emotional styles, cloned character voices, batches; `init chatterbox` installs it with uv into the project's Chatterbox folder (locked Python 3.11 in `settings/`, git-ignored `voices/`) |
| `generate-voice-lines` | skill | A character's voice and lines: designs the voice with Kokoro (one calm 6-8 s reference clip, master in `assets/audio/voice/<name>/`), generates lines by kind (speech, battle) with Chatterbox from it, 5 takes each, Whisper word check and cutting; `init kokoro` installs Kokoro + Whisper into the project's Kokoro folder |
| `godot-resource-manager` | agent | Syncs assets into Godot and updates the docs from the Godot project |

## Character voices

Spoken lines are made in two steps, because no single local tool does both (`generate-voice-lines`):

1. **Kokoro designs the voice.** It blends its built-in voices into one calm 6-8 s **reference clip**
   per character, chosen by the user. The master is kept in `assets/audio/voice/<name>/` with its
   recipe; Chatterbox uses a git-ignored copy.
2. **Chatterbox acts the lines.** Every line is cloned from that one clip with the English model; the
   kind of line (speech: greetings, dialogue; battle: spells, battle cries) only changes the
   settings. 5 takes per line, a Whisper word check, and the user picks.

One calm reference with the intensity added once, in the settings, gave by far the best results in
testing. The tests and lessons behind it are in [voice_gen_context.md](voice_gen_context.md).

## Requirements

- Claude Code
- Godot 4 (GDScript only)
- Python 3.11+ with Pillow, and `ffmpeg`, to run the export and sync scripts
- ComfyUI and `comfy-cli` (installed with `uv tool install comfy-cli`), only for the ComfyUI skills; the `comfy-ui-connection` skill offers to install both, or uses an existing ComfyUI
- `uv` and `git`, only for `chatterbox-text-to-speech` and `generate-voice-lines` (an NVIDIA GPU is recommended; Kokoro and the Whisper check also run on CPU). First use downloads the models (Chatterbox several GB, Kokoro ~330 MB, Whisper ~460 MB) into the shared Hugging Face cache
- Docker and `uv`, only for `blender-3d-modeling`

## Changing the template

Skills and agents are shared between projects, so improve them here first and then copy them into projects. Existing projects are not updated automatically; use the migrate steps.
