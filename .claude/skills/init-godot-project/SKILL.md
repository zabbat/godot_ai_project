---
name: init-godot-project
description: Set up a new Godot 4 AI project (a game repository) in an empty destination folder - copies the shared .claude folder (skills and agents), creates every repo folder and the Godot project folders, writes a minimal project.godot and all the AGENTS.md index files and standard docs, and copies the export/sync scripts and asset-map starter files. Use when the user wants to start a new Godot game project, "init", "scaffold" or "bootstrap" a Godot AI repo, or copy the template into a new folder.
---

# Init Godot project

Creates the repository described by the `godot-development` skill in a new folder. Read that skill's "Repository layout" and "Godot project layout" sections if anything below is unclear; this skill only automates the setup.

Everything the new project starts from lives next to this file in [assets/](assets/README.md): `repo_template/` is the folder tree with `{{PLACEHOLDERS}}`. The scripts and asset-map starter files are **not duplicated** here: they are copied from the `godot-development` skill, the canonical version.

## 1. Gather the details

Ask the user (one question block, with defaults) for what you cannot infer:

| Detail | Placeholder | Default |
|---|---|---|
| Destination folder (absolute path; must be empty or not exist) | `DEST` | none: required |
| Game name | `{{GAME_NAME}}` | the destination folder's name |
| One or two sentences on the game (genre, platform) | `{{GAME_SUMMARY}}` | "A Godot 4 game. Not designed yet." |
| Godot project folder name inside `godot/` (`snake_case` or `kebab-case`, no spaces) | `{{GODOT_PROJECT}}` | the game name, lowercased |
| Workshop folder (generation scratch, git-ignored) | `{{WORKSHOP}}` | `test-shot` |
| Renderer: `mobile`, `forward_plus` or `gl_compatibility` | `{{RENDERER_ID}}` / `{{RENDERER_NAME}}` (`Mobile` / `Forward Plus` / `GL Compatibility`) | `mobile` |
| Window: viewport width x height, orientation (portrait = 1, landscape = 0) | `{{VIEWPORT_W}}`, `{{VIEWPORT_H}}`, `{{ORIENTATION}}` | 1280 x 720 landscape (0) |
| Godot version and executable path | `{{ENGINE_VERSION}}`, `{{GODOT_EXE}}` | `4.x` and `(not set yet)` |

Stop if `DEST` exists and is not empty: never overwrite a project. Say so and ask for another folder.

## 2. Copy

`SRC` = the `.claude` folder this skill sits in (two levels above this file). `TPL` = `SRC/skills/init-godot-project/assets/repo_template`. Shell is Git Bash; use forward slashes.

```bash
mkdir -p "$DEST"

# 1. Shared skills and agents. Leave this skill out: it only serves to start projects.
mkdir -p "$DEST/.claude"
cp -r "$SRC/." "$DEST/.claude/"
rm -rf "$DEST/.claude/skills/init-godot-project"
rm -f  "$DEST/.claude/settings.local.json"          # machine-specific permissions, if present

# 2. The repo tree (docs, prototype, assets, tools, godot) with placeholders
cp -r "$TPL/." "$DEST/"
mv "$DEST/godot/PROJECT" "$DEST/godot/<GODOT_PROJECT>"
mv "$DEST/gitignore.template" "$DEST/.gitignore"

# 3. Scripts and asset-map starter files, from the godot-development skill
GD="$SRC/skills/godot-development/assets"
cp "$GD/export_assets.py" "$GD/check_sync.py" "$DEST/tools/"
cp "$GD/project_template/settings.toml" "$GD/project_template/profiles.toml" "$DEST/prototype/asset_map/"
```

## 3. Create the folders

Empty folders are not kept by git, so each gets a `.gitkeep` (not the git-ignored ones).

```bash
cd "$DEST"
# AI side
mkdir -p docs/game_design docs/style docs/references prototype/asset_map \
  assets/2d assets/3d/third_party assets/audio/music assets/audio/sfx tools
mkdir -p downloads "<WORKSHOP>"            # git-ignored: no .gitkeep
# Godot side (paths relative to godot/<GODOT_PROJECT>/)
cd "godot/<GODOT_PROJECT>"
mkdir -p autoload common/components common/ui common/effects common/shaders \
  entities levels ui resources \
  assets/art assets/fonts assets/third_party assets/audio/music assets/audio/ambience \
  assets/audio/sfx/ui assets/audio/sfx/impacts
cd "$DEST"
find assets godot/<GODOT_PROJECT> -type d -empty -exec touch {}/.gitkeep \;
```

## 4. Fill the placeholders

Replace every `{{...}}` in the destination (not in `.claude/`), using a delimiter that cannot appear in the values (`|`; escape `&` and `|` in free text):

```bash
cd "$DEST"
grep -rl '{{' --exclude-dir=.claude --exclude-dir=.git . | while read -r f; do
  sed -i \
    -e 's|{{GAME_NAME}}|<value>|g' \
    -e 's|{{GAME_SUMMARY}}|<value>|g' \
    -e 's|{{GODOT_PROJECT}}|<value>|g' \
    -e 's|{{WORKSHOP}}|<value>|g' \
    -e 's|{{RENDERER_ID}}|<value>|g' -e 's|{{RENDERER_NAME}}|<value>|g' \
    -e 's|{{VIEWPORT_W}}|<value>|g' -e 's|{{VIEWPORT_H}}|<value>|g' -e 's|{{ORIENTATION}}|<value>|g' \
    -e 's|{{ENGINE_VERSION}}|<value>|g' -e 's|{{GODOT_EXE}}|<value>|g' \
    -e 's|{{DATE}}|<today, YYYY-MM-DD>|g' "$f"
done
```

Then set the two values in the copied `prototype/asset_map/settings.toml`, which the generic template leaves as `<...>`:

- `godot_project = "godot/<GODOT_PROJECT>"`
- `workshop = "<WORKSHOP>"`

Finally check that no `{{` or `<project>`/`<workshop folder>` is left: `grep -rn '{{\|<project>\|<workshop folder>' . --exclude-dir=.claude --exclude-dir=.git`. In `prototype/asset_map/profiles.toml` the `spec = "prototype/<... doc>.md"` lines stay until those docs exist; mention them to the user.

## 5. Finish

- If `git` is available and the user wants it: `git init` in `DEST` (do not commit unless asked).
- Do **not** run `export_assets.py` or `check_sync.py`: there is nothing to export yet. Both need Python 3.11+ (Pillow for images, `ffmpeg` for audio); `python` may not be on the PATH, in which case say so and note it in `tools/AGENTS.md`.
- Report to the user: where the project is, the choices made (defaults taken), what was left out of `.claude/` (this skill), and the next steps: write the game idea in `docs/game_design/`, fill `docs/style/`, open `godot/<GODOT_PROJECT>/project.godot` in Godot once (it generates `.godot/` and `.uid` files), and set the Godot executable in `prototype/godot_structure.md` if it was left blank.

## What the setup creates

```
<DEST>/
  AGENTS.md                      repo map, project paths, rules
  .gitignore                     workshop, downloads/, __pycache__/, .godot/
  .claude/                       skills + agents, copied from the template
  docs/                          AGENTS.md; game_design/ (audio.md, menus.md); style/ (2d, 3d); references/
  prototype/                     AGENTS.md, godot_structure.md, game_data.md; asset_map/ (AGENTS.md, settings.toml, profiles.toml)
  assets/                        AGENTS.md; 2d/, 3d/third_party/, audio/{music,sfx}/
  downloads/  <WORKSHOP>/        git-ignored
  tools/                         AGENTS.md, export_assets.py, check_sync.py
  godot/AGENTS.md
  godot/<GODOT_PROJECT>/         project.godot, main.tscn, main.gd, icon.svg + the folder layout
```

The Godot folder layout is the generic part of the `godot-development` skill's "Godot project layout"; add feature folders (`entities/heroes/`, `levels/<level>/`, ...) when the first feature needs them, and record each in `prototype/godot_structure.md`.

## Changing the template

The template is shared by every new project: ask the user before changing `assets/repo_template/`. Existing projects are not updated by it. Keep the wording in the template files generic (no game-specific content), and keep `tools/` and `asset_map` starter files out of it (they come from `godot-development`).
