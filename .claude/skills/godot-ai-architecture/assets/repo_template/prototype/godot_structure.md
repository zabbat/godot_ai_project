# Godot structure

Map of the Godot project: where it is, what each folder holds, and the key
files in it. Skills and docs look up Godot paths here instead of hard-coding
them. General rules for where things go are in the `godot-development`
skill; this file records how they are applied in this project.

**Keep it current**: update this file in the same step as creating, moving,
renaming or removing a folder or a key file in the Godot project.

Last checked: {{DATE}}.

## Project

| | |
|---|---|
| Project folder | `godot/{{GODOT_PROJECT}}/` (holds `project.godot`; `res://` points here) |
| Engine | Godot {{ENGINE_VERSION}}, {{RENDERER_NAME}} renderer |
| Godot executable | {{GODOT_EXE}} |
| Window | {{VIEWPORT_W}}x{{VIEWPORT_H}}, stretch `canvas_items`, aspect `expand` |
| Main scene | `res://main.tscn` (`main.gd`): the entry point; will swap screens and levels |
| Autoloads | none yet |
| Audio buses | none yet (`default_bus_layout.tres` with `Music`, `SFX`, `Ambience`, `UI` once audio arrives) |

## Folders

Paths are relative to the project folder.

| Folder | Holds | Key files |
|---|---|---|
| `autoload/` | Global singletons (event bus, game state, audio) | |
| `common/` | Code and scenes shared by several features | |
| `common/components/` | Reusable node groups (health, hitbox, hurtbox...) | |
| `common/ui/` | Shared themes, buttons, popups | |
| `common/effects/` | Reusable effects, one folder per effect with its scene, script and shader | |
| `common/shaders/` | Shaders and `.gdshaderinc` helpers used by several features | |
| `entities/` | Things in the game world, one folder per type | |
| `levels/` | One folder per level or map, with shaders only it uses | |
| `ui/` | Screens: main menu, HUD, ... | |
| `resources/` | Shared `.tres` data not tied to one entity | |
| `assets/` | Exported files no single entity owns (see [asset_map/](asset_map/AGENTS.md)). Never edit them here. | |
| `assets/art/`, `assets/fonts/` | Exported art and fonts | |
| `assets/third_party/<pack>/` | Vendor models, original names | |
| `assets/audio/music/`, `ambience/` | Music and ambience (exported) | |
| `assets/audio/sfx/` | Sound effects by category (`ui/`, `impacts/`, ...) (exported) | |

Root files: `project.godot`, `main.tscn`, `main.gd`, `icon.svg`.
