# AGENTS.md

The generic scripts that build the Godot side from the AI side. They are
copies of the scripts in the `godot-ai-architecture` skill's `assets/`
folder: project paths come from
[prototype/asset_map/settings.toml](../../prototype/asset_map/settings.toml),
not from the code. To improve a script, change the skill's version (ask the
user first: skills are shared between projects), then copy it here.

- [export_assets.py](export_assets.py) — Exports source assets from `assets/`
  into the Godot project, following the [asset map](../../prototype/asset_map/AGENTS.md)
  (entries, conversion profiles, import settings). Only writes targets that
  changed.
- [check_sync.py](check_sync.py) — Reports where the Godot project and the AI
  side disagree: targets not exported (and whether the master or the Godot
  copy is newer), takes in the tools' output folders newer than a master's
  chosen take, unmapped Godot media, unused masters, Godot folders missing
  from `prototype/godot_structure.md`, AGENTS.md indexes missing files or
  with broken links, and Godot data or code changed after the docs. Used by
  the `godot-resource-manager` agent.

## Running

Needs Python 3.11+ with Pillow, and `ffmpeg` on the PATH for audio profiles.
If `python` is not on the PATH, use any interpreter that has Pillow (for
example ComfyUI's embedded Python) and note its path here.

```bash
PY=python
$PY -I tools/godot-sync/export_assets.py --dry-run   # what would change
$PY -I tools/godot-sync/export_assets.py             # export everything that changed
$PY -I tools/godot-sync/export_assets.py portraits   # one area only
$PY -I tools/godot-sync/export_assets.py --force     # rewrite every target
$PY -I tools/godot-sync/check_sync.py                # every check; exit code 1 if anything is reported
$PY -I tools/godot-sync/check_sync.py structure index  # only some checks
```

Run the export from the repo root (or any folder inside it) after changing a
master, an entry or a profile, then open Godot so it reimports the changed
files. A new target gets its `.import` file only when Godot first sees it:
if the export reports "no .import yet", open Godot and run the export again
to apply the profile's import settings.
