# init-godot-project assets

| Path | Purpose |
|---|---|
| `repo_template/` | The folder tree copied into a new project (`docs/`, `prototype/`, `assets/`, `tools/`, `godot/` with their `AGENTS.md` files and standard docs, `gitignore.template`). Contains `{{PLACEHOLDERS}}` that the skill fills in. |
| `repo_template/godot/PROJECT/` | The Godot project; renamed to `godot/<GODOT_PROJECT>/` on copy. Holds `project.godot`, `main.tscn`, `main.gd`, `icon.svg`. |
| `repo_template/gitignore.template` | Renamed to `.gitignore` on copy (so it is not a git-ignore file inside the template). |

Placeholders: `{{GAME_NAME}}`, `{{GAME_SUMMARY}}`, `{{GODOT_PROJECT}}`, `{{WORKSHOP}}`, `{{RENDERER_ID}}`, `{{RENDERER_NAME}}`, `{{VIEWPORT_W}}`, `{{VIEWPORT_H}}`, `{{ORIENTATION}}`, `{{ENGINE_VERSION}}`, `{{GODOT_EXE}}`, `{{DATE}}`.

Not here on purpose: `export_assets.py`, `check_sync.py`, `settings.toml` and `profiles.toml` are copied straight from the `godot-development` skill's `assets/`, which stays their only canonical version.
