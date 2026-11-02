# godot-development assets

Generic scripts and starter files for the repo layout this skill describes.
These are the canonical versions: projects copy them, and improvements are
made here first, then copied to each project.

| File | Copy to | Purpose |
|---|---|---|
| `export_assets.py` | `tools/export_assets.py` | Exports `assets/` into the Godot project following `prototype/asset_map/` (copy, image resize, ffmpeg; import settings). |
| `check_sync.py` | `tools/check_sync.py` (needs `export_assets.py` beside it) | Reports where Godot and the AI side disagree (export with newer-side note, workshop takes newer than a master's, unmapped, unused, structure, index, changed). |
| `project_template/settings.toml` | `prototype/asset_map/settings.toml` | Repo paths and options for both scripts; set `godot_project`. |
| `project_template/profiles.toml` | `prototype/asset_map/profiles.toml` | Starter conversion profiles; fill in each `spec` doc and adjust sizes. |

Both scripts need Python 3.11+ (for `tomllib`), Pillow for image profiles,
and `ffmpeg` on the PATH for audio profiles. They find the repo root from
the working directory (the folder holding `prototype/asset_map/settings.toml`)
or from `--repo`.

When a project copy differs from the version here, compare them: either the
project has an improvement that belongs here (ask the user before changing
the skill), or the copy is outdated and should be refreshed.
