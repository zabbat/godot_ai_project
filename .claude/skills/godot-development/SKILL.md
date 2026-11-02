---
name: godot-development
description: How to structure a Godot 4 game repository and project - the split between the AI side (docs, prototype, source assets, skills) and the Godot side, keeping every game fact in the docs so the Godot project can be rebuilt, the asset map from source assets to Godot files, and inside Godot the folder layout, scene composition, custom Resources, shaders and materials, audio, autoloads, signals and naming. Use when adding or reorganizing anything in the repo or the Godot project, adding an image, model or sound, changing game data, or deciding where a new file or fact belongs.
---

# Godot development

Conventions for a Godot 4 game repository and the Godot project inside it. GDScript only, no C#. This skill is generic: the project's own paths are in the repository's root `AGENTS.md` (repo folders) and `prototype/godot_structure.md` (folders and key files inside the Godot project, engine version, Godot executable). Look paths up there; never hard-code them in a skill.

## Repository layout: AI side and Godot side

```
<repo>/
  AGENTS.md          map of the repo, project paths, rules (every folder has its own AGENTS.md index)
  docs/              the game: what it is and why. Design only, no engine details.
    game_design/     systems and features (+ standard audio.md, menus.md)
    style/           standard 2d_style.md, 3d_style.md
    references/      what we aim for (style images, mood clips); never used in the game
  prototype/         the bridge from design to Godot: how each feature is built, exact game data,
                     decided rules, file conventions
    godot_structure.md  map of the Godot project's folders and key files
    asset_map/       which source asset becomes which Godot file, and how (TOML)
  assets/            source resources (images, models, sounds) + where each came from. No usage.
  downloads/         raw downloads as received: vendor zips, original files (git-ignored)
  <workshop>/        generation scratch: every render and take (git-ignored, e.g. test-shot/)
  tools/             scripts (export, convert); generic
  .claude/           skills and agents; generic
  godot/<project>/   the Godot project: code, scenes, data, and files exported from assets/
```

- **AI side** = everything except `godot/`. **Godot side** = `godot/`. Information flows one way: `docs/` → `prototype/` → `godot/`, and `downloads/` or the workshop → `assets/` → (asset map) → `godot/`. Godot never reads from the AI side, and nothing raw (zips, downloads, takes) goes inside the Godot project.
- **The Godot project must be rebuildable** from the AI side alone. Delete `godot/`, hand an agent the docs, prototype and assets, and it should produce a similar game (not identical code, the same game). Git history is for exact restores.
- **Project-specific paths live in the root `AGENTS.md` and `prototype/godot_structure.md`**, not in skills, so skills stay reusable across projects.
- **Keep `prototype/godot_structure.md` current**: update it in the same step as creating, moving, renaming or removing a folder or key file in the Godot project, and when refactoring the structure.

### Standard docs

Every project has these, created at the start with a placeholder line ("No style defined yet." / "Not designed yet.") and filled as decisions are made. Other docs are specific to the game.

| Doc | Covers |
|---|---|
| `docs/game_design/audio.md` | Music, sound effects, voices: what plays when, principles, open questions |
| `docs/game_design/menus.md` | Screens and menus, how they connect, HUD |
| `docs/style/2d_style.md` | 2D art style (characters, UI, icons), prompt keywords for generation |
| `docs/style/3d_style.md` | 3D art style (characters, props, buildings, environment) |
| `prototype/godot_structure.md` | Map of the Godot project |
| `prototype/game_data.md` | Exact game data |

Read the matching style doc before generating, choosing or making art. If the part you need says "No style defined yet", ask the user before inventing one, then write the decision into the doc.

### Where an outside file goes

| It is... | Goes to |
|---|---|
| A raw download as received (vendor zip, original file from a site or tool) | `downloads/` (git-ignored) |
| Something that shows what we want, not used in the game ("draw like this", "sound like this") | `docs/references/`, listed with what it is a reference for and where it came from |
| A resource the game uses (extracted from a zip, a chosen generated take) | `assets/`, with its source or license recorded |

## Keeping the docs complete

Nothing about the game may exist only in Godot. Every fact has a home on the AI side:

| Kind of fact | Lives in | Example |
|---|---|---|
| Design: what a feature is, why, open questions | `docs/` | "Mobs come in packs that share a lane" |
| How a feature is built in Godot, rules the build decided | `prototype/<feature>.md` | "Heroes on the ground sortie to hunt ranged mobs" |
| Exact game data: stats, attacks, skills, waves, structure HP, combat constants, layout positions | `prototype/` (a game data doc) | "Knight: HP 160, Cleave cooldown 5, area 2.5" |
| File conventions: where files go, naming, linking | `prototype/` | "portrait at `entities/heroes/<name>/<name>_portrait.png`" |
| Godot folders and key files | `prototype/godot_structure.md` | "`resources/encounters/`: nights and their waves" |
| What we aim for (style, mood) | `docs/references/` + the design doc that links it | a drawing-style image |
| Which asset is used where, converted how, with which import settings | `prototype/asset_map/` | `knight_portrait.png` → profile `portrait` |
| Where a resource came from (prompt, seed, license) | next to it in `assets/` | `knight_portrait.md` |

Rules:
- **Same step, both sides.** When you change a value or behavior in Godot (a `.tres`, a scene property, a constant, a rule in a script), update the prototype doc in the same change, and the other way around. Doc first is better: write the change, then build it.
- **Write behavior, not just numbers.** Targeting rules, triggers, priorities, spawn patterns and fall-backs in scripts are game facts too; describe them in words.
- **Say where each value lives in Godot** (file and field), so the two can be checked against each other.
- Before finishing a task, ask: *could someone rebuild this from the docs?* If not, write down what's missing.

## Source assets and the asset map

`assets/` holds the **chosen masters** at the best quality available, organized by type, then subject:

```
assets/
  2d/portraits/<unit>/        <unit>_portrait.png, .md (prompt, seed), _workflow.json
  3d/third_party/<pack>/      files taken out of the pack (original names), License.txt
  3d/third_party/sources.md   download page and license of every pack (zips stay in downloads/)
  audio/music/                tracks + sources.md (tool, prompt, link)
  audio/sfx/<category>/<event>/
```

- Work in progress stays in the workshop; a take is copied to `assets/` once it is picked. Never edit a master; a change is a new take.
- `assets/` says nothing about usage: no Godot paths, `.import` files or game data.

`prototype/asset_map/` maps sources to Godot files: one TOML file per area (`portraits.toml`, `models.toml`, `music.toml`, `sounds.toml`), `profiles.toml` with the conversion recipes, and `settings.toml` with the repo paths (`assets`, `godot_project`). An area is a file, not a folder, unless it needs files of its own.

Each piece of information has one home:

| Information | Where |
|---|---|
| Which source goes to which target | the area's `.toml` entries |
| How it is converted (size, format, ffmpeg args, import settings) | a profile in `profiles.toml` |
| Why the profile has those values, what the asset must look like | the prototype doc named in the profile's `spec` |



```toml
[[asset]]
source = "2d/portraits/knight/knight_portrait.png"     # relative to assets/
target = "entities/heroes/knight/knight_portrait.png"  # relative to the Godot project
profile = "portrait"                                   # recipe in profiles.toml
import = { loop = true }                               # optional: non-default import settings
import_notes = "prototype/models.md#animations"        # optional: settings too complex to list
```

- A `source` ending in `/` maps a whole folder (`exclude = ["*.psd"]` to skip files).
- Profiles have a `kind`: `copy`, `image` (Pillow: `format`, `size` with cover crop, never upscale, metadata dropped) or `ffmpeg` (`format`, `args`), plus optional `import` and `spec`. Typical ones: `copy`; `portrait` (square PNG at a size with ~2x headroom over its on-screen size); `sfx` (trim silence, normalize loudness, mono 16-bit WAV); `loop` (Ogg, untrimmed, loop on); `music`.
- Masters stay at full quality; the game size lives only in the profile, so changing it is one edit and one export.
- **Exported files are generated: never edit them in Godot.** Change the master or the entry and export again.
- **Targets are stable**, so Godot's `.import` and `.uid` files next to them stay valid across exports.
- **Non-default import settings** (loop, compression, animation library, loop modes) go in the profile or entry (`import`, as `[params]` keys of the `.import` file) or a linked doc; otherwise a rebuild loses them.
- **Export with `tools/export_assets.py`** (a copy of this skill's script, see below) (generic: reads `settings.toml`, writes only targets that changed, `--dry-run` to preview, area names to limit). Run it after changing a master, an entry or a profile, then let Godot reimport. Run `--dry-run` first and check that only the expected targets change.

### Scripts and setting up a new project

The generic scripts live in this skill's [assets/](assets/README.md) folder and are **copied** into each project's `tools/`; the skill's version is the canonical one.

| Script | Does |
|---|---|
| `export_assets.py` | Exports `assets/` into Godot following the asset map: `copy`, `image` (resize to a profile size, e.g. 720 masters → 480 portraits), `ffmpeg` (trim, normalize, convert audio), and writes import settings. |
| `check_sync.py` | Reports, one short line per problem: targets not exported (and whether the master or the Godot copy is newer, by file time), workshop takes newer than the take a master was chosen from (its `.md` names the take; `Rejected: ...` silences reviewed ones), Godot media no entry produces, masters no entry uses, Godot folders missing from `godot_structure.md`, `AGENTS.md` indexes missing files or with broken links, Godot data and code changed after the game data / structure docs. |

To set up the pipeline in a project:
1. Copy `export_assets.py` and `check_sync.py` to `tools/`, and add `tools/AGENTS.md` saying they are copies of this skill's scripts.
2. Copy `assets/project_template/settings.toml` and `profiles.toml` to `prototype/asset_map/`; set `godot_project` and the profile sizes, and write each profile's `spec` doc.
3. Add one `<area>.toml` per kind of asset and an `AGENTS.md` index in `prototype/asset_map/`.
4. Run `export_assets.py --dry-run`, then `check_sync.py`, and fix what they report.

When a recurring job would cost many reads (checking dozens of files against a doc, converting a batch), add it to a script instead of doing it by hand each time. Write it generic (paths from `settings.toml`) so it can join this skill's `assets/`. Changing the skill's scripts is a skill change: ask the user first.

## Core principles

1. **One scene = one self-contained unit** (a hero, a mob, a HUD panel, a level). It should work when run alone with F6.
2. **Data lives in Resources, behavior lives in scenes/scripts.** Stats, definitions, and tuning values go in custom `Resource` files, not hard-coded in scripts or baked into scene properties.
3. **Call down, signal up.** A parent may call methods on its children. A child never reaches up to its parent; it emits a signal and the parent (or an event bus) reacts.
4. **Compose, don't inherit deeply.** Prefer small child scenes/nodes (e.g. `HealthComponent`, `Hitbox`) added to an entity over deep script inheritance chains.
5. **Keep the node tree shallow and named for meaning**, and reference children through `@onready` typed variables or `%UniqueName` nodes, not long `get_node` paths.

## Modularity and sharing

Every scene must be modular: it does one job, has no hard dependency on a specific parent or sibling, and can be dropped into another scene or run alone.

- **Never duplicate.** If two scenes need the same node setup, script, texture, theme, shader, or data, extract it into its own file and reference it from both.
- **Extract shared pieces into separate files** under `common/` (or `resources/` for data):
  - reusable node groups as their own scenes (`health_component.tscn`, `hurtbox.tscn`, `health_bar.tscn`)
  - shared logic as standalone scripts with a `class_name`
  - shared data as `.tres` Resources (stats, damage types, upgrade definitions)
  - shared look as a single `Theme`, shared materials/shaders, shared sprite frames
  - shared audio, fonts, and textures in `assets/`
- **Reference, don't copy.** Instance the shared scene or load the shared resource by path. Changing the shared file then updates every user of it.
- **Parameterize via exports and signals**, not by editing the shared file per use. If one user needs a variation, use an exported property, a `.tres` override, or an inherited scene.
- **Rule of three**: the second use is a warning; by the third use, a shared piece must live in its own file in `common/`.
- **No cross-feature imports of private internals.** A feature folder may depend on `common/`, `resources/`, `assets/` and autoloads, but not reach into another feature's folder. If two features need the same thing, move it to `common/`.

## Godot project layout

Inside the Godot project, organize by feature/entity, keeping a scene next to its script and its own assets. Shared things go in `common/`. The Godot project's `assets/` (`res://assets/`) holds exported files that no single entity owns; it is not the repo's source `assets/`.

```
godot/<project>/
  project.godot
  autoload/            # global singletons (event bus, game state, audio)
  common/              # reusable pieces shared by many features
    components/        # health_component.tscn/.gd, hitbox, hurtbox...
    ui/                # shared themes, buttons, popups
    effects/           # reusable effect scenes (rain/, hit_spark/), each with its own shader
    shaders/           # shaders and .gdshaderinc helpers used by several features
  entities/
    heroes/
      archer/          # archer.tscn, archer.gd, archer.png, archer_data.tres
      hero_data.gd     # class_name HeroData extends Resource
    mobs/
      goblin/
      mob_data.gd
  levels/              # one scene per map / battle arena (+ shaders only that level uses)
  ui/                  # screens: main_menu, hud, night_battle_ui
  resources/           # shared .tres data not tied to one entity
    heroes/ mobs/ upgrades/
  assets/              # exported art, audio, fonts not owned by a single entity
    art/ fonts/
    third_party/<pack>/  # vendor models, original names (exported from the repo's assets/3d/third_party/)
    audio/
      music/ ambience/
      sfx/             # weapons/<weapon>/, spells/<element>/, skills/<skill>/, impacts/, ui/ ...
```

Rules:
- Folders and files: `snake_case`. Node names and `class_name`: `PascalCase`.
- A scene and its main script share a name: `goblin.tscn` + `goblin.gd`.
- Don't create a catch-all `scripts/` folder separate from scenes; it splits things that change together.
- Source art, raw downloads and docs stay outside the Godot project (repo `assets/`, workshop, `docs/`); if something must sit inside it without being imported, add a `.gdignore` file to its folder.
- Don't hand-edit `.godot/` (generated cache); keep it out of version control.

## Scenes

- **Entry point**: set `run/main_scene` to a small `main.tscn` that swaps screens/levels, rather than a gameplay scene.
- **Instancing**: expose a scene's parts through exported variables and signals, then instance it from the parent:
  ```gdscript
  const GOBLIN := preload("res://entities/mobs/goblin/goblin.tscn")

  func spawn_goblin(pos: Vector2) -> void:
  	var mob := GOBLIN.instantiate()
  	mob.global_position = pos
  	add_child(mob)
  ```
- **Inherited scenes** (`New Inherited Scene`) are good for variants that differ only in data or a few nodes (e.g. `goblin_archer.tscn` from `goblin.tscn`). Don't use them as the main reuse tool.
- **Changing scenes**: `get_tree().change_scene_to_packed()` for full screen swaps, or a manager in `main.tscn` that adds/removes children when you need to keep persistent state (HUD, music).
- Use `preload` for constant paths known at parse time, `load` / `ResourceLoader.load_threaded_request` for big or optional assets.
- Avoid hardcoded scene paths scattered through code; put them in constants, or better, in a Resource (see below).

## Resources

Define a typed data class, then author instances as `.tres` files in the editor Inspector.

```gdscript
# entities/mobs/mob_data.gd
class_name MobData
extends Resource

@export var display_name: String
@export var max_health: int = 10
@export var move_speed: float = 60.0
@export var scene: PackedScene
@export var icon: Texture2D
```

```gdscript
# entities/mobs/goblin/goblin.gd
extends CharacterBody2D

@export var data: MobData
var health: int

func _ready() -> void:
	health = data.max_health
```

Guidelines:
- One `.tres` per distinct thing (`goblin.tres`, `orc.tres`), stored beside the entity or in `resources/<kind>/`.
- Always type `@export` fields (`@export var data: MobData`) so the Inspector restricts what can be assigned.
- Resources are **shared by reference**. If an instance must mutate its own copy at runtime (current health, cooldowns), copy the needed values into the node or call `data.duplicate()`. Never mutate a shared `.tres` at runtime.
- Use `@export_group` / `@export_range` / `@export_enum` to keep Inspectors readable.
- For collections (all heroes, all upgrades), use a registry Resource holding `Array[HeroData]`, or load a directory with `DirAccess` at startup, instead of long `preload` lists.
- Prefer `.tres` (text) over `.res` (binary) so diffs and merges stay readable.
- Save/load player progress with a dedicated Resource (`SaveData extends Resource`) and `ResourceSaver` to `user://`, never to `res://`.

## Shaders and materials

Where shader files live and how materials are shared. How to *write* shaders and effects (searching online first, techniques, performance, verification) is in the `godot-shader-effects` skill.

**Where files go** (same ownership rule as scenes: a file lives with the thing that owns it, shared things go in `common/`):

| What | Where | Example |
|---|---|---|
| Shader used by one scene only | next to that scene | `levels/night_battle/dark_mist.gdshader` |
| Reusable effect (scene + its shader + its script) | its own folder in `common/effects/` | `common/effects/rain/rain.tscn`, `rain.gd`, `rain_streak.gdshader` |
| Shader used by several features | `common/shaders/` | `common/shaders/hit_flash.gdshader` |
| Shared shader helper functions (noise, hashing, remap) | `common/shaders/*.gdshaderinc`, pulled in with `#include` | `common/shaders/noise.gdshaderinc` |
| Shared material (same shader *and* same settings in several places) | `.tres` next to its shader | `common/shaders/hit_flash_material.tres` |
| Image textures a shader samples | the owner's folder, or `assets/` if shared | `assets/textures/noise_soft.png` |
| Third-party shader packs | `assets/third_party/<pack>/`, untouched; adapt copies elsewhere | |

Rules:
- Name shaders after the effect, `snake_case`, extension `.gdshader` (`dark_mist.gdshader`, not `shader1.gdshader` or `mist_shader.gdshader`). A material saved as a file is `<effect>_material.tres`.
- **One shader file, many materials.** Never copy a `.gdshader` to make a variant. Variants are different `ShaderMaterial`s (or `.tres` files) pointing at the same shader with different parameter values.
- **Inline vs. saved material**: a `ShaderMaterial` used by one node can stay embedded in the scene as a sub-resource (like `DarkMist`). Save it as a `.tres` as soon as a second user needs the same settings.
- **Generated textures** (`NoiseTexture2D`, `GradientTexture1D`) can stay embedded as sub-resources of the material that uses them. Image files go in a folder.
- **Per-object values** (flash amount on one mob, tint per hero) go in an `instance uniform`, set with `set_instance_shader_parameter()`. Never duplicate the material per object (it also breaks batching). If the value comes from game data, expose it as an `@export` on the scene's script, which sets the parameter.
- **Project-wide values** (storm intensity, wind, lightning flash) use `global uniform`s defined in Project Settings > Shader Globals and are set from **one** owner script (for example the level's weather controller), not from many places.
- **Shader parameters are set from the owning scene's script**, following "call down": other scenes ask that script (method or signal), and never reach into another scene's material.
- **Material resources are shared by reference** like any Resource: changing a parameter on a shared material at runtime changes it for every user. Use `instance uniform`s, or `material.duplicate()` only when a node truly needs its own copy.
- Third-party or adapted shaders keep a credit comment (source, author, license) at the top of the file.
- If an effect is described in `docs/`, the doc names the shader file and its tuning parameters.

## Audio

Where sound files live in the Godot project and how they are played. The project's exact folders, event names and import steps are in its prototype audio doc (listed in `prototype/AGENTS.md`); read it before adding a sound. Generating sounds is the `comfy-ui-audio-generation` skill; masters go to the repo's `assets/audio/` and reach Godot through the asset map.

**Where files go** (same ownership rule: a sound lives with the thing that makes it):

| What | Where | Example |
|---|---|---|
| A character's voice (idle, hurt, death) | its entity folder | `entities/mobs/zombie/zombie_death_1.wav` |
| Weapon, spell element, skill (shared by any unit that uses it) | `assets/audio/sfx/weapons/<weapon>/`, `spells/<element>/`, `skills/<skill>/` | `assets/audio/sfx/weapons/bow/bow_release_1.wav` |
| Generic impacts, UI, battle events | `assets/audio/sfx/impacts/`, `ui/`, `battle/` | `assets/audio/sfx/ui/button_tap_1.wav` |
| Sound a reusable effect plays | next to the effect | `common/effects/rain/rain_loop.ogg` |
| Music, level-wide ambience | `assets/audio/music/`, `assets/audio/ambience/` | `assets/audio/music/battle_theme_1.mp3` |
| Work-in-progress renders | the workshop, outside the Godot project; chosen masters in the repo's `assets/audio/` | |

Rules:
- Name files `<owner>_<event>_<n>`: `bow_release_2.wav`, `zombie_idle_1.wav`. Variations are numbered from 1, even when there is only one.
- **One `AudioStreamRandomizer` `.tres` per event** (`bow_release.tres`) holding the variations, with a little random pitch and volume. Data and code point at that `.tres`, never at a single `.wav`, so variations can be added without changing anything else.
- **Link sounds through Resources**, like portraits and visuals: `@export var hit_sound: AudioStream` on the data class (`AttackData`, `MobData`...), grouped under `@export_group("Audio")`. Never build sound paths from names; an empty field means silence, not an error.
- **Formats**: short effects as mono 16-bit `.wav` (instant start, cheap on mobile; QOA compression on import); loops and ambience as `.ogg`; music `.ogg`/`.mp3`. Set looping in the import settings, not in code. Avoid `.mp3` for hits: its start padding makes them feel late.
- **Buses**: route every player to a named bus (`Music`, `SFX`, `Ambience`, `UI`) from `default_bus_layout.tres`; volume sliders and ducking work on buses, never on individual players.
- **Playback**: positional battle sounds go through one pooled player (an `Sfx` autoload with `play_at(stream, position)`) instead of an `AudioStreamPlayer3D` in every unit. Pooling survives units being freed mid-sound and lets you cap copies of the same sound, which matters with dozens of mobs. Music and UI use plain `AudioStreamPlayer`s.
- Balance loudness in the files (the `sfx` export profile normalizes) and in the randomizer's per-stream volume, not with `volume_db` scattered through scripts.
- Commit the `.import` file next to each sound. If audio is described in `docs/`, keep the doc's names in line with the files.

## Communication between scenes

| Need | Use |
|---|---|
| Child informs parent | Signal on the child, parent connects to it |
| Parent controls child | Direct method call or property set |
| Siblings / distant scenes | Parent mediates, or a signal on an **event bus** autoload |
| Global state (gold, day count, current run) | Autoload `GameState` |
| Shared tuning data | Resource |

Event bus example:

```gdscript
# autoload/events.gd  (registered as autoload "Events")
extends Node

signal mob_died(mob: Node, gold_reward: int)
signal night_started
signal night_ended(survived: bool)
```

Keep autoloads few (event bus, game state, audio, scene manager). Don't put per-level logic in them, and don't let them hold references to nodes that get freed.

## Scripts

- Static type everything: `var speed: float = 10.0`, `func take_damage(amount: int) -> void`.
- Order inside a file: `class_name`, `extends`, doc comment, signals, enums, constants, `@export` vars, public vars, private vars (`_name`), `@onready` vars, built-in callbacks (`_ready`, `_process`...), public methods, private methods.
- Give reusable scripts a `class_name` so they can be used as types; don't give one to every script.
- Declare signals with typed arguments and past-tense names (`died`, `health_changed(new, max)`).
- Use groups (`add_to_group("mobs")`) for cheap "find all of kind X" queries and collision layers/masks (named in Project Settings) for physics interactions.
- Prefer `_physics_process` for movement and `_process` for visuals; disable processing (`set_process(false)`) on idle nodes.

## Checklist when adding something new

1. Is it described on the AI side? Write the design in `docs/` and the exact values and behavior in `prototype/` first (or in the same step). Nothing may exist only in Godot.
2. Is it data (stats, text, a list of options)? Add or extend a Resource class and make a `.tres`; record its values in the prototype's game data doc.
3. Is it an entity with behavior? Create a folder under `entities/`, with `thing.tscn`, `thing.gd`, art, and its data `.tres`.
4. Is it an image, model or sound? Put the master in the repo's `assets/` with its provenance, add an entry to `prototype/asset_map/`, and export it into the Godot project; never drop files straight into Godot.
5. Does it appear in more than one place? Make it its own scene/file and reference it; move it to `common/` or `resources/` if shared by multiple features. Never copy-paste nodes, scripts, or data between scenes.
6. Is it a visual effect or shader? Put the shader next to its only user, or in `common/effects/` / `common/shaders/` if shared; reuse one shader across materials; follow the `godot-shader-effects` skill for writing it.
7. Is it a sound? Put it with its owner (character folder) or in `assets/audio/sfx/<category>/` if weapons, spells or skills share it; wrap its variations in an `AudioStreamRandomizer` `.tres` and link that from the data Resource. Follow the project's prototype audio doc.
8. Does it need to tell others something? Emit a signal rather than calling upward.
9. Run the scene alone (F6) to verify it works without its parent.
10. Keep names consistent with the design docs, and update the `AGENTS.md` index of any folder where you added or renamed a file.
11. Did you add, move or remove a folder or key file in the Godot project? Update `prototype/godot_structure.md`.
