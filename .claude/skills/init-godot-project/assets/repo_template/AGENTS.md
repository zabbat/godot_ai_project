# AGENTS.md

This is a Godot game project: {{GAME_SUMMARY}}

Use GDScript only for game logic. Avoid C#.

## Layout

The repo has an **AI side** (everything that describes the game and holds
its source resources) and a **Godot side** (the game built from it). The
Godot project must be rebuildable from the AI side alone, so **nothing about
the game may exist only in Godot**. The `godot-development` skill has the
full conventions.

| Folder | Side | Contents |
|---|---|---|
| [docs/](docs/AGENTS.md) | AI | The game design: what the game is and why. No engine details. Includes [references/](docs/references/AGENTS.md) (style and mood references, never used in the game). |
| [prototype/](prototype/AGENTS.md) | AI | The bridge from design to Godot: how each feature is built, the exact game data, file conventions, the [Godot structure](prototype/godot_structure.md) and the [asset map](prototype/asset_map/AGENTS.md). |
| [assets/](assets/AGENTS.md) | AI | Source resources the game uses (images, 3D packs, music, sounds), each with where it came from. Says nothing about usage. |
| `downloads/` | AI | Raw downloads as received: vendor zips, original files (git-ignored). |
| `{{WORKSHOP}}/` | AI | The workshop: every generated render and sound take (git-ignored). Chosen takes are copied to `assets/`. |
| [tools/](tools/AGENTS.md) | AI | Copies of the `godot-development` skill's scripts: `export_assets.py` (export `assets/` into Godot) and `check_sync.py` (find where Godot and the docs disagree). |
| `.claude/skills/` | AI | Reusable skills (Godot development, shaders, 3D models, ComfyUI image and audio generation). |
| `.claude/agents/` | AI | `godot-resource-manager`: syncs resources into Godot and updates the docs from Godot. |
| [godot/](godot/AGENTS.md) | Godot | The Godot project: code, scenes, data, and files exported from `assets/`. |

Flow: `docs/` → `prototype/` → `godot/`, and `downloads/` or `{{WORKSHOP}}/` →
`assets/` → `prototype/asset_map/` → `godot/`.

## Project paths

Skills are generic and read these paths from here. Paths inside the Godot
project (folders, key files, engine version, Godot executable) are in
[prototype/godot_structure.md](prototype/godot_structure.md).

| What | Path |
|---|---|
| Godot project (`project.godot`) | `godot/{{GODOT_PROJECT}}/` |
| Godot structure | `prototype/godot_structure.md` |
| Game design docs | `docs/game_design/` (standard: `audio.md`, `menus.md`) |
| Visual style | `docs/style/2d_style.md`, `docs/style/3d_style.md` |
| Design references | `docs/references/` |
| Prototype docs | `prototype/` |
| Exact game data | `prototype/game_data.md` |
| Asset map | `prototype/asset_map/` (paths for the export script in `settings.toml`) |
| Asset export | `tools/export_assets.py` (see [tools/AGENTS.md](tools/AGENTS.md)) |
| Source assets | `assets/` |
| Raw downloads | `downloads/` |
| Workshop (images) | `{{WORKSHOP}}/<xxx>-asset-<description>/` |
| Workshop (sounds) | `{{WORKSHOP}}/sound/<xxx>-sound-<description>/` |

## Rules

- **Docs and Godot change together.** A change to game data or behavior in
  Godot updates `prototype/` (and `docs/` if the design changes) in the same
  step. A new, moved or removed Godot folder or key file updates
  `prototype/godot_structure.md`.
- **Resources enter through `assets/`.** Never put an image, model or sound
  straight into Godot: store the master in `assets/`, add an entry to the
  asset map, then export it with `tools/export_assets.py`.
- **Outside files**: raw downloads go to `downloads/`; things that only show
  what we want (a drawing style) go to `docs/references/`; resources the game
  uses go to `assets/`.
- **Never edit an exported file in Godot**; change the master or the map.
- **Every folder with docs has an `AGENTS.md` index.** Update it when adding,
  renaming or removing a file.
- **Skills and agents are shared between projects**: ask the user before
  changing anything in `.claude/` or the script copies in `tools/`. Docs and
  `AGENTS.md` files can be changed freely.
- **Check the sync** with the `godot-resource-manager` agent (or
  `tools/check_sync.py`) after asset or Godot changes and before committing.
- Resources are stored twice (in `assets/` and exported in `godot/`); that is
  accepted for now. Revisit (e.g. Git LFS) before pushing to a remote.
