# AGENTS.md

This is a Godot game project: {{GAME_SUMMARY}}

Use GDScript only for game logic. Avoid C#.

## Layout

The repo has five working areas. The Godot project must be rebuildable from
the other four, so **nothing about the game may exist only in Godot**. The
`godot-ai-architecture` skill has the full conventions of the repo; the
`godot-development` skill those inside the Godot project.

| Folder | Contents |
|---|---|
| [docs/](docs/AGENTS.md) | The game design, for people: what the game is and why, characters, story, style. No engine details. Includes [references/](docs/references/AGENTS.md) (style and mood references, never used in the game). |
| [prototype/](prototype/AGENTS.md) | The build spec: how each feature is built in Godot, the exact game data, file conventions, the [Godot structure](prototype/godot_structure.md) and the [asset map](prototype/asset_map/AGENTS.md). |
| [assets/](assets/AGENTS.md) | Source resources the game uses (images, 3D packs, music, sounds), each with where it came from. Only resources and their records: no code, no usage. |
| [tools/](tools/AGENTS.md) | One folder per tool: its settings, its scripts and its generated output (`output/`, git-ignored). `godot-sync/` exports `assets/` into Godot and checks the sync. |
| [godot/](godot/AGENTS.md) | The Godot project: code, scenes, data, and files exported from `assets/`. |

Not working areas:

| Folder | Contents |
|---|---|
| `export/` | Built game exports (APK etc.), written by Godot through `export_presets.cfg` (git-ignored). |
| `downloads/` | Personal inbox for raw downloads (vendor zips, original files); git-ignored, not needed to build the game. |
| `.claude/` | Skills and agents, shared between projects. |

Flow: `docs/` → `prototype/` → `godot/`, and `downloads/` or a tool's
`output/` → `assets/` → `prototype/asset_map/` → `godot/`.

## Project paths

Skills are generic and read these paths from here. A tool skill that finds
no row for its folder asks the user once and adds the row. Paths inside the
Godot project (folders, key files, engine version, Godot executable) are in
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
| Asset map | `prototype/asset_map/` (paths for the scripts in `settings.toml`) |
| Asset export and sync check | `tools/godot-sync/` (see [tools/godot-sync/AGENTS.md](tools/godot-sync/AGENTS.md)) |
| Source assets | `assets/` |
| Raw downloads | `downloads/` |
| Game builds | `export/` |
| ComfyUI images output | `tools/comfy-ui/output/images/` |
| ComfyUI sound effects output | `tools/comfy-ui/output/sound-effects/` |
| Chatterbox (text-to-speech) | `tools/chatterbox/` |
| Kokoro (voice design, take check) | `tools/kokoro/` |
| Blender | `tools/blender/` |

## Rules

- **Docs and Godot change together.** A change to game data or behavior in
  Godot updates `prototype/` (and `docs/` if the design changes) in the same
  step. A new, moved or removed Godot folder or key file updates
  `prototype/godot_structure.md`.
- **Resources enter through `assets/`.** Never put an image, model or sound
  straight into Godot: store the master in `assets/`, add an entry to the
  asset map, then export it with `tools/godot-sync/export_assets.py`.
- **Outside files**: raw downloads go to `downloads/`; things that only show
  what we want (a drawing style) go to `docs/references/`; resources the game
  uses go to `assets/`.
- **Tools live in `tools/<tool>/`.** A tool's settings, its own scripts and
  its `output/` (generated takes, git-ignored) stay in its folder; working
  files keep their own folder names (for example Blender's `models/`).
  Generic scripts get their own folder (`tools/godot-sync/`). No code in
  `assets/`.
- **Never edit an exported file in Godot**; change the master or the map.
- **Every folder with docs has an `AGENTS.md` index.** Update it when adding,
  renaming or removing a file.
- **Skills and agents are shared between projects**: ask the user before
  changing anything in `.claude/` or the script copies in `tools/godot-sync/`.
  Docs and `AGENTS.md` files can be changed freely.
- **Check the sync** with the `godot-resource-manager` agent (or
  `tools/godot-sync/check_sync.py`) after asset or Godot changes and before
  committing.
- Resources are stored twice (in `assets/` and exported in `godot/`); that is
  accepted for now. Revisit (e.g. Git LFS) before pushing to a remote.
