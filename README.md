# Godot AI project template

A template for starting Godot 4 games that are built together with an AI agent (Claude Code). It holds the shared `.claude/` folder (skills and agents) and a skill that scaffolds a new game repository from it.

## What a project built from this looks like

The repo has an **AI side** (design docs, build notes, source assets, tools) and a **Godot side** (the game). The Godot project can be rebuilt from the AI side alone: nothing about the game may exist only in Godot.

```
<repo>/
  AGENTS.md          repo map, project paths, rules
  docs/              the game design (+ style/, references/)
  prototype/         how it is built in Godot, exact game data, asset map
  assets/            source resources (images, models, sounds) + provenance
  downloads/         raw downloads (git-ignored)
  <workshop>/        generation scratch (git-ignored)
  tools/             export_assets.py, check_sync.py
  .claude/           skills and agents
  godot/<project>/   the Godot project
```

Flow: `docs/` → `prototype/` → `godot/`, and `assets/` → asset map → `godot/`. Every folder has an `AGENTS.md` index.

## Start a new project

In Claude Code, from this repo, run the `init-godot-project` skill:

```
/init-godot-project
```

It asks for the destination folder, game name, renderer and window size, then:

1. copies `.claude/` (without the init skill itself),
2. creates all repo and Godot folders,
3. writes the `AGENTS.md` files, standard docs and a minimal `project.godot` / `main.tscn`,
4. copies `export_assets.py`, `check_sync.py` and the asset-map starter files.

The destination must be empty or not exist yet.

## Contents of `.claude/`

| Name | Kind | Purpose |
|---|---|---|
| `init-godot-project` | skill | Scaffold a new Godot AI project (template in its `assets/repo_template/`) |
| `godot-development` | skill | Repo and Godot project conventions; holds the canonical `export_assets.py`, `check_sync.py` and asset-map starters |
| `godot-shader-effects` | skill | Writing shaders and visual effects, with example `.gdshader` files |
| `glb-3d-model-and-animations` | skill | Bringing rigged glTF/GLB models and animations into Godot |
| `comfy-ui-asset-generation` | skill | Generating images with a local ComfyUI server |
| `comfy-ui-audio-generation` | skill | Generating sounds with a local ComfyUI Stable Audio graph |
| `godot-resource-manager` | agent | Syncs assets into Godot and updates the docs from the Godot project |

## Requirements

- Claude Code
- Godot 4 (GDScript only)
- Python 3.11+ with Pillow, and `ffmpeg`, to run the export and sync scripts
- A local ComfyUI server, only for the generation skills

## Changing the template

Skills and agents are shared between projects, so improve them here first and then copy them into projects. Existing projects are not updated automatically.
