# godot-ai-architecture assets

The canonical versions of everything a project starts from. Projects copy
them; improvements are made here first (ask the user: skills are shared
between projects), then copied to each project.

| Path | Copy to | Purpose |
|---|---|---|
| `export_assets.py` | `tools/godot-sync/export_assets.py` | Exports `assets/` into the Godot project following `prototype/asset_map/` (copy, image resize, ffmpeg; import settings). |
| `export_tuning.py` | `tools/godot-sync/export_tuning.py` | Optional: turns `prototype/tuning.toml` into a generated GDScript file (`--check`: is it up to date). |
| `check_sync.py` | `tools/godot-sync/check_sync.py` (needs `export_assets.py` beside it) | Reports where Godot and the AI side disagree (export with newer-side note, tool-output takes newer than a master's, unmapped, unused, structure, index, changed). |
| `project_template/settings.toml` | `prototype/asset_map/settings.toml` | Repo paths and options for both scripts; set `godot_project` and `outputs`. |
| `project_template/profiles.toml` | `prototype/asset_map/profiles.toml` | Starter conversion profiles; fill in each `spec` doc and adjust sizes. |
| `repo_template/` | the new repo's root | The folder tree of a new project (`docs/`, `prototype/`, `assets/`, `tools/`, `godot/` with their `AGENTS.md` files and standard docs, `gitignore.template`), with `{{PLACEHOLDERS}}`. See [references/new_project.md](../references/new_project.md). |
| `repo_template/godot/PROJECT/` | `godot/<GODOT_PROJECT>/` | The Godot project: `project.godot`, `main.tscn`, `main.gd`, `icon.svg`. |
| `repo_template/gitignore.template` | `.gitignore` | Renamed on copy so it is not a git-ignore file inside the template. |

Placeholders: `{{GAME_NAME}}`, `{{GAME_SUMMARY}}`, `{{GODOT_PROJECT}}`,
`{{RENDERER_ID}}`, `{{RENDERER_NAME}}`, `{{VIEWPORT_W}}`, `{{VIEWPORT_H}}`,
`{{ORIENTATION}}`, `{{ENGINE_VERSION}}`, `{{GODOT_EXE}}`, `{{DATE}}`.

The scripts and asset-map starter files are not duplicated inside
`repo_template/`: they are copied from this folder, their only canonical
version.

Both scripts need Python 3.11+ (for `tomllib`), Pillow for image profiles,
and `ffmpeg` on the PATH for audio profiles. They find the repo root from
the working directory (the folder holding `prototype/asset_map/settings.toml`)
or from `--repo`.

When a project copy differs from the version here, compare them: either the
project has an improvement that belongs here (ask the user before changing
the skill), or the copy is outdated and should be refreshed.
