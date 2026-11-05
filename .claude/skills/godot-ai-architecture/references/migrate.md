# Migrate an existing project to the current layout

Brings a project made from an older version of the template up to date. Existing projects are never updated automatically, so run this when the template changes. Work on a branch, move with `git mv` so history follows the files, and check at the end that the project still exports and syncs.

## 0. Look first

1. Read the project's root `AGENTS.md`, `tools/` (or `tools/AGENTS.md`), `prototype/asset_map/settings.toml`, `.gitignore` and `.mcp.json`, and run `git status` (start from a clean tree).
2. Compare the project with the current layout (this skill's "Repository layout" and "Tools", and `assets/repo_template/`). Write the list of differences, and show it to the user before moving anything. Ask about anything that is not clearly a template folder (a folder only this project has stays where it is unless the user says otherwise).
3. Check that no tool is running from a folder you will move (Blender sandbox containers, a ComfyUI save in progress).

## 1. Refresh `.claude/`

Copy the current skills and agents from the template over the project's `.claude/` (keep `settings.local.json`). Remove skills the template no longer has: renamed ones leave their old folder behind (for example `comfy-ui-asset-generation` → `comfy-ui-images`, `comfy-ui-audio-generation` → `comfy-ui-sound-effects`, `init-godot-project` merged into `godot-ai-architecture`). Show the user which skills changed.

## 2. Move the tools into `tools/`

Old layout → new layout (only what exists):

| Old | New |
|---|---|
| `tools/export_assets.py`, `tools/check_sync.py`, `tools/AGENTS.md` | `tools/godot-sync/` (refresh both scripts from this skill's `assets/`) |
| `test-shot/<xxx>-asset-<desc>/` (images; or the project's workshop folder) | `tools/comfy-ui/output/images/<xxx>-asset-<desc>/` |
| `test-shot/sound/<xxx>-sound-<desc>/` | `tools/comfy-ui/output/sound-effects/<xxx>-sound-<desc>/` |
| `chatterbox/` | `tools/chatterbox/` |
| `blender/` | `tools/blender/` |

- Git-ignored folders (`test-shot/`, outputs) are moved with plain `mv`, not `git mv`.
- **Never rename the takes themselves**: asset records name them by file name.
- Chatterbox: after moving, the `.venv` inside `settings/` has absolute paths baked in. Delete `tools/chatterbox/settings/.venv` and run `uv sync --project tools/chatterbox/settings` (the lock file is kept, so it is the same environment).
- Blender: update `.mcp.json` from the skill's `assets/project/mcp.json` (it passes `--config tools/blender/config/sandbox.toml`), change every `[[share]]` `path` in `sandbox.toml` (`blender/models` → `tools/blender/models`), and run the launcher's `--check`. The user must restart Claude Code afterwards.

## 3. Update the project's files

- **Root `AGENTS.md`**: the layout table (five areas + `export/`, `downloads/`, `.claude/`), the "Project paths" table (tool rows: ComfyUI images output, ComfyUI sound effects output, Chatterbox, Blender, asset export and sync check), the flow line and the rules, following `assets/repo_template/AGENTS.md`. Keep the project's own text (game summary, extra rows, project-specific rules).
- **`tools/AGENTS.md`**: the tool index from the template, with one line per tool folder present. Each tool folder keeps its own `AGENTS.md` (fix paths in them: `chatterbox/settings` → `tools/chatterbox/settings`, etc.).
- **`tools/godot-sync/AGENTS.md`**: from the template, keeping project notes (which Python to use).
- **`prototype/asset_map/settings.toml`**: replace `workshop = "..."` with `outputs = [...]` listing the tool output folders. Fix `tools/export_assets.py` mentions in `profiles.toml` and `asset_map/AGENTS.md`.
- **`.gitignore`**: `tools/*/output/` instead of the workshop folder; move tool-specific lines to their new paths (`tools/blender/models/**/*.blend`, `tools/blender/models/_previews/`); keep `downloads/`, `export/`, `__pycache__/`, `*.blend1`.
- **Every other doc** that names an old path: `grep -rn "test-shot\|tools/export_assets\|tools/check_sync\|chatterbox/\|blender/\|comfy-ui-asset-generation\|comfy-ui-audio-generation\|init-godot-project" --exclude-dir=.git --exclude-dir=.claude --exclude-dir=godot .` and fix each hit (records in `assets/` that only name a take's file name need no change).

- **Characters (optional)**: if the design docs describe characters but there is no `docs/characters/`, offer the `game-character` skill's "Set up characters" (it can bring the existing characters in). Only if the user wants it; it is not part of the layout change.

## 4. Check

1. `tools/godot-sync/export_assets.py --dry-run`: nothing should change (the Godot files did not move).
2. `tools/godot-sync/check_sync.py`: fix what it reports (typical: an `AGENTS.md` index that still lists an old folder).
3. Open the Godot project (or run it headless) to confirm it still loads; build an export if the user asks.
4. Show the user `git status` and a summary of what moved, and commit only when asked.
