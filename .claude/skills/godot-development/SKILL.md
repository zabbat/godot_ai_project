---
name: godot-development
description: How to build inside a Godot 4 project with GDScript - the folder layout by feature, scene composition and modularity, custom Resources for data, shaders and materials (where they live, sharing), audio (where sounds live, randomizers, buses, pooled playback), autoloads, signals and naming, script style, and testing the exported build (APK) as well as the editor. Use when writing or changing game code, scenes, Resources, shaders, materials or audio playback in Godot, deciding where a file goes inside the Godot project, or testing an export or a bug seen only on a device. How the repo around the Godot project is organized (docs, prototype, assets, tools, asset map) is the godot-ai-architecture skill.
---

# Godot development

Conventions for working inside a Godot 4 project. GDScript only, no C#. This skill is generic: the project's paths inside Godot (folders, key files, engine version, Godot executable) are in its `prototype/godot_structure.md`; look them up there.

The repository around the Godot project (the design docs, the build spec in `prototype/`, source assets, tools, the asset map and the export/sync scripts) is the **`godot-ai-architecture` skill**. Two of its rules apply to every change made here:
- **Nothing about the game may exist only in Godot.** A change to game data or behavior updates `prototype/` in the same step; a new, moved or removed folder or key file updates `prototype/godot_structure.md`.
- **Images, models and sounds come in through the repo's `assets/` and the asset map**, exported by `tools/godot-sync/export_assets.py`. Never drop a file straight into the Godot project, and never edit an exported file here.

Specialist skills: `godot-shader-effects` (writing shaders and effects) and `glb-3d-model-and-animations` (rigged models, animations, props).

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
- Source art, raw downloads, tool output and docs stay outside the Godot project (repo `assets/`, `tools/`, `docs/`); if something must sit inside it without being imported, add a `.gdignore` file to its folder.
- Record every folder and key file in `prototype/godot_structure.md` when you add, move or remove it (`godot-ai-architecture` skill).
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

Where sound files live in the Godot project and how they are played. The project's exact folders, event names and import steps are in its prototype audio doc (listed in `prototype/AGENTS.md`); read it before adding a sound. Making sounds is the `comfy-ui-sound-effects` and `chatterbox-text-to-speech` skills; masters go to the repo's `assets/audio/` and reach Godot through the asset map (`godot-ai-architecture` skill).

**Where files go** (same ownership rule: a sound lives with the thing that makes it):

| What | Where | Example |
|---|---|---|
| A character's voice (idle, hurt, death) | its entity folder | `entities/mobs/zombie/zombie_death_1.wav` |
| Weapon, spell element, skill (shared by any unit that uses it) | `assets/audio/sfx/weapons/<weapon>/`, `spells/<element>/`, `skills/<skill>/` | `assets/audio/sfx/weapons/bow/bow_release_1.wav` |
| Generic impacts, UI, battle events | `assets/audio/sfx/impacts/`, `ui/`, `battle/` | `assets/audio/sfx/ui/button_tap_1.wav` |
| Sound a reusable effect plays | next to the effect | `common/effects/rain/rain_loop.ogg` |
| Music, level-wide ambience | `assets/audio/music/`, `assets/audio/ambience/` | `assets/audio/music/battle_theme_1.mp3` |
| Work-in-progress renders | the tool's `output/` in the repo's `tools/`, outside the Godot project; chosen masters in the repo's `assets/audio/` | |

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
- Never `preload` a resource whose script depends back on the script doing the preloading (directly, or through classes it uses). The editor resolves the cycle; an exported build does not, the script fails to compile, and everything built on it breaks on the device only. `load()` it at run time instead (for example a static getter that loads on first use).
- Give an exported packed array its default through its constructor, never a bare `[...]` literal: `@export var options: PackedStringArray = PackedStringArray(["OK"])`, not `= ["OK"]`. With the literal, Godot 4.7's export drops the value a scene sets for it when it converts scenes to binary, so the device silently uses the default (a dialog showed "OK" instead of the scene's "No", "Yes"). `Array[String] = ["OK"]` and a packed array with no default are safe.

## Testing the exported build

The editor and headless runs with `--path` use the project's text scripts and resources. An export ships binary scripts and resources, and those can fail where the editor works. **When the user asks to test for export (or "on the phone", "the APK", a build), or reports a bug only seen on a device, also test the exported version**, not only the project:

1. **The build the user has**: an APK (or other export) is a zip. Find it at the preset's `export_path` in `export_presets.cfg`, extract its `assets/` folder to a scratch folder, and run it headless with a test script: `"$GODOT" --headless --path <extracted>/assets -s <test.gd>`. This runs exactly the files the device runs.
2. **A fresh build of the current code**: `"$GODOT" --headless --path <project> --export-pack "<preset>" <out.pck>`, then run it from an empty folder with `"$GODOT" --headless --main-pack <out.pck> -s <test.gd>`. For a full APK, use `--export-debug "<preset>" <out.apk>` and test it as in step 1. **After a fix that changes only a script** (not the scene or resource it affects), delete the project's `.godot/exported/` folder first: Godot caches each converted scene there and reuses it while the `.tscn`/`.tres` is unchanged, so the old, broken conversion ships again. The folder is generated; deleting it is always safe. Tell the user to do the same before building the APK.
3. **A device over USB** (if `adb devices` lists one): `adb install -r <apk>`, start the app, and read `adb logcat -s godot` for script errors.
4. Treat any `SCRIPT ERROR` or failed resource load in these runs as a failure, even if the editor run was clean. Fix it, export again and re-run before reporting the build as working.

**Some export bugs are silent**: no error, just a wrong value on the device (a scene's setting replaced by the script's default). An error-free run proves nothing about those, so the test script also checks values: load the scene or resource involved, print the properties the bug touches, and compare the output of the same script run on the project (`--path <project>`) and on the export. To see what the exported file really stores, read `load(path).get_state()` (`SceneState.get_node_property_name()` / `get_node_property_value()`): a property missing there was dropped by the export, not by game code. To find the trigger, make a minimal project in a scratch folder (one script, one scene, the project's `export_presets.cfg` without its keystore lines), declare the property several ways side by side, export it with `--export-pack` and compare. It exports in seconds instead of minutes.

Test scripts follow the same rules as any headless run: a real-time watchdog that quits, no project class names in the test script (use duck typing), and stopping at the first error. Typical export-only failures: preload cycles (see Scripts), scene values of exported packed arrays with a bare `[...]` default dropped (see Scripts), a stale `.godot/exported/` cache shipping an old conversion (step 2), files left out by the export filter, listing `res://` folders with `DirAccess` (exported files are renamed `.remap`/`.import`), wrong upper/lower case in paths (Android is case-sensitive), and editor-only classes used in game code.

## Checklist when adding something new

1. Is it described outside Godot, and does its master (image, model, sound) come through `assets/` and the asset map? Follow the `godot-ai-architecture` skill's checklist first, or in the same step.
2. Is it data (stats, text, a list of options)? Add or extend a Resource class and make a `.tres`; record its values in the prototype's game data doc.
3. Is it an entity with behavior? Create a folder under `entities/`, with `thing.tscn`, `thing.gd`, art, and its data `.tres`.
4. Does it appear in more than one place? Make it its own scene/file and reference it; move it to `common/` or `resources/` if shared by multiple features. Never copy-paste nodes, scripts, or data between scenes.
5. Is it a visual effect or shader? Put the shader next to its only user, or in `common/effects/` / `common/shaders/` if shared; reuse one shader across materials; follow the `godot-shader-effects` skill for writing it.
6. Is it a sound? Put it with its owner (character folder) or in `assets/audio/sfx/<category>/` if weapons, spells or skills share it; wrap its variations in an `AudioStreamRandomizer` `.tres` and link that from the data Resource. Follow the project's prototype audio doc.
7. Does it need to tell others something? Emit a signal rather than calling upward.
8. Run the scene alone (F6) to verify it works without its parent.
9. Keep names consistent with the design docs. Did you add, move or remove a folder or key file? Update `prototype/godot_structure.md`.
10. Is it going onto a device, or did the user ask to test the export? Test the exported build too (see [Testing the exported build](#testing-the-exported-build)).
