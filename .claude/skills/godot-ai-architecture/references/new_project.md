# Start a new project

Creates the repository described in the skill's "Repository layout" in a new folder, from this skill's [assets/](../assets/README.md): `repo_template/` is the folder tree with `{{PLACEHOLDERS}}`; the scripts and asset-map starter files are copied from `assets/` directly (their only canonical version).

## 1. Gather the details

Ask the user (one question block, with defaults) for what you cannot infer:

| Detail | Placeholder | Default |
|---|---|---|
| Destination folder (absolute path; must be empty or not exist) | `DEST` | none: required |
| Game name | `{{GAME_NAME}}` | the destination folder's name |
| One or two sentences on the game (genre, platform) | `{{GAME_SUMMARY}}` | "A Godot 4 game. Not designed yet." |
| Godot project folder name inside `godot/` (`snake_case` or `kebab-case`, no spaces) | `{{GODOT_PROJECT}}` | the game name, lowercased |
| Renderer: `mobile`, `forward_plus` or `gl_compatibility` | `{{RENDERER_ID}}` / `{{RENDERER_NAME}}` (`Mobile` / `Forward Plus` / `GL Compatibility`) | `mobile` |
| Window: viewport width x height, orientation (portrait = 1, landscape = 0) | `{{VIEWPORT_W}}`, `{{VIEWPORT_H}}`, `{{ORIENTATION}}` | 1280 x 720 landscape (0) |
| Godot version and executable path | `{{ENGINE_VERSION}}`, `{{GODOT_EXE}}` | `4.x` and `(not set yet)` |
| Does the game have characters (heroes, enemies, a player character, NPCs)? | (none: a yes runs the `game-character` skill's "Set up characters" after step 5) | ask; "not yet" is fine (it can be set up later) |

Stop if `DEST` exists and is not empty: never overwrite a project. Say so and ask for another folder.

## 2. Copy

`SRC` = the `.claude` folder this skill sits in (two levels above the skill folder). `ARCH` = `SRC/skills/godot-ai-architecture/assets`. Shell is Git Bash; use forward slashes.

```bash
mkdir -p "$DEST"

# 1. Shared skills and agents
mkdir -p "$DEST/.claude"
cp -r "$SRC/." "$DEST/.claude/"
rm -f "$DEST/.claude/settings.local.json"          # machine-specific permissions, if present

# 2. The repo tree (docs, prototype, assets, tools, godot) with placeholders
cp -r "$ARCH/repo_template/." "$DEST/"
mv "$DEST/godot/PROJECT" "$DEST/godot/<GODOT_PROJECT>"
mv "$DEST/gitignore.template" "$DEST/.gitignore"

# 3. Scripts and asset-map starter files
cp "$ARCH/export_assets.py" "$ARCH/check_sync.py" "$DEST/tools/godot-sync/"
cp "$ARCH/project_template/settings.toml" "$ARCH/project_template/profiles.toml" "$DEST/prototype/asset_map/"
```

## 3. Create the folders

Empty folders are not kept by git, so each gets a `.gitkeep` (not the git-ignored ones). Tool folders other than `godot-sync/` are **not** created here: each tool's skill creates its folder when the tool is first set up (the paths are already in the root `AGENTS.md`).

```bash
cd "$DEST"
mkdir -p docs/game_design docs/style docs/references prototype/asset_map \
  assets/2d assets/3d/third_party assets/audio/music assets/audio/sfx tools/godot-sync
mkdir -p downloads export                  # git-ignored: no .gitkeep
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
    -e 's|{{RENDERER_ID}}|<value>|g' -e 's|{{RENDERER_NAME}}|<value>|g' \
    -e 's|{{VIEWPORT_W}}|<value>|g' -e 's|{{VIEWPORT_H}}|<value>|g' -e 's|{{ORIENTATION}}|<value>|g' \
    -e 's|{{ENGINE_VERSION}}|<value>|g' -e 's|{{GODOT_EXE}}|<value>|g' \
    -e 's|{{DATE}}|<today, YYYY-MM-DD>|g' "$f"
done
```

Then set `godot_project = "godot/<GODOT_PROJECT>"` in the copied `prototype/asset_map/settings.toml` (the generic template leaves `<project>`). `outputs` already lists the default tool output folders.

Finally check that nothing is left: `grep -rn '{{\|<project>' . --exclude-dir=.claude --exclude-dir=.git`. In `prototype/asset_map/profiles.toml` the `spec = "prototype/<... doc>.md"` lines stay until those docs exist; mention them to the user.

## 5. Finish

- If `git` is available and the user wants it: `git init` in `DEST` (do not commit unless asked).
- Do **not** run `export_assets.py` or `check_sync.py`: there is nothing to export yet. Both need Python 3.11+ (Pillow for images, `ffmpeg` for audio); `python` may not be on the PATH, in which case say so and note it in `tools/godot-sync/AGENTS.md`.
- Report to the user: where the project is, the choices made (defaults taken), and the next steps: write the game idea in `docs/game_design/`, fill `docs/style/`, open `godot/<GODOT_PROJECT>/project.godot` in Godot once (it generates `.godot/` and `.uid` files), set the Godot executable in `prototype/godot_structure.md` if it was left blank, and set up tools when needed ("init chatterbox", "set up my project to use blender"; ComfyUI needs no setup), and "set up characters" if the game has characters and it was not done yet.

## What the setup creates

```
<DEST>/
  AGENTS.md                      repo map, project paths (incl. tool rows), rules
  .gitignore                     tools/*/output/, downloads/, export/, __pycache__/, .godot/
  .claude/                       skills + agents, copied from the template
  docs/                          AGENTS.md; game_design/ (audio.md, menus.md); style/ (2d, 3d); references/
  prototype/                     AGENTS.md, godot_structure.md, game_data.md; asset_map/ (AGENTS.md, settings.toml, profiles.toml)
  assets/                        AGENTS.md; 2d/, 3d/third_party/, audio/{music,sfx}/
  tools/                         AGENTS.md; godot-sync/ (AGENTS.md, export_assets.py, check_sync.py)
  godot/AGENTS.md
  godot/<GODOT_PROJECT>/         project.godot, main.tscn, main.gd, icon.svg + the folder layout
  downloads/  export/            git-ignored
```

The Godot folder layout is the generic part of the `godot-development` skill's "Godot project layout"; add feature folders (`entities/heroes/`, `levels/<level>/`, ...) when the first feature needs them, and record each in `prototype/godot_structure.md`.

## Changing the template

The template is shared by every new project: ask the user before changing `assets/repo_template/`. Existing projects are not updated by it (see [migrate.md](migrate.md)). Keep the wording in the template files generic (no game-specific content), and keep the scripts and asset-map starter files out of it (they are copied from `assets/`).
