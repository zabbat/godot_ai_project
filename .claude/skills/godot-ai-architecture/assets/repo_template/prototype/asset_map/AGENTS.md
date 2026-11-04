# Asset map

Which file in the repo's `assets/` becomes which file in the Godot project,
and how it is converted on the way. `assets/` only describes the resources
themselves; how the game uses them is recorded here.

`tools/godot-sync/export_assets.py` reads these files and does the export (see
[tools/godot-sync/AGENTS.md](../../tools/godot-sync/AGENTS.md)). Rebuilding the Godot project's
resources is one run of it.

## Where each piece of information lives

| Information | Where | Example |
|---|---|---|
| Which source goes to which target | `<area>.toml` entries | a portrait master → `entities/heroes/knight/knight_portrait.png` |
| How it is converted (size, format, ffmpeg args, import settings) | a profile in `profiles.toml` | `portrait`: PNG, 480x480 |
| Why the profile has those values, and what the asset must look like | the doc named in the profile's `spec` | a prototype doc |
| The repo paths the script uses | `settings.toml` | `godot_project = "godot/{{GODOT_PROJECT}}"` |

An area gets one `.toml` file, not a folder. Make it a folder only if an
area needs files of its own beyond its entries.

## Files

| File | Covers |
|---|---|
| [settings.toml](settings.toml) | Paths of `assets/`, the Godot project and the tools' output folders, for the scripts. |
| [profiles.toml](profiles.toml) | Conversion recipes (`copy`, `portrait`, `sfx`, `loop`, `music`), referenced by name from the entries. Fill each `spec` doc and adjust sizes. |

Add a new `<area>.toml` (for example `portraits.toml`, `models.toml`,
`music.toml`, `sounds.toml`) when a new kind of asset arrives and list it
above. If it needs a new conversion, add a profile with a `spec` doc that
explains its values.

## Entry format

```toml
[[asset]]
source = "2d/portraits/knight/knight_portrait.png"   # relative to assets/
target = "entities/heroes/knight/knight_portrait.png"  # relative to the Godot project
profile = "portrait"                                   # a name from profiles.toml
import = { loop = true }      # optional: Godot import settings, added to the profile's
import_notes = "prototype/models.md#animations"        # optional: settings too complex to list
```

- A `source` ending in `/` is a folder: its whole tree is converted into the
  `target` folder, keeping relative paths. `exclude` lists glob patterns to
  skip.
- One source can have several entries. A source with no entry is simply unused.
- **Targets are stable.** Exporting again writes to the same paths, so
  Godot's `.import` and `.uid` files next to the targets stay valid.
- **Never edit a target in Godot.** Change the source, the entry or the
  profile, and export again; anything edited only in `godot/` is lost on the
  next export.
- **Import settings** that differ from Godot's defaults must be written in
  the profile or entry (`import`, as `[params]` keys of the `.import` file)
  or in a linked doc (`import_notes`), otherwise a rebuild loses them.
- Keep entries in the same order as the folders in `assets/`.

## Profile format

```toml
[profile.portrait]
kind = "image"            # copy | image | ffmpeg
description = "..."
spec = "prototype/<doc>.md#portraits"   # why these values
format = "png"            # image, ffmpeg: output format
size = [480, 480]         # image: cover-crop to this size, never upscale
args = "..."              # ffmpeg: arguments between input and output
import = { loop = true }  # optional: Godot import settings
```
