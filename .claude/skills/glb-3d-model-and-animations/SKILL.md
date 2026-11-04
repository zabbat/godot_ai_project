---
name: glb-3d-model-and-animations
description: How to bring rigged glTF/GLB character models, separate animation files, and attachable props (weapons) into a Godot 4 project, and drive them from game code. Covers inspecting a downloaded pack, folder layout for vendor assets, import settings (Animation Library import, loop modes), shared animation libraries for characters on the same rig, wrapper visual scenes with BoneAttachment3D, animation playback patterns, verification, and mobile performance. Use when adding or changing 3D models, animations, or weapons, or when replacing placeholder visuals with models.
---

# GLB 3D models and animations

How to add rigged `.glb`/`.gltf` characters, their animations and props to a Godot 4 project so they are easy to find, reuse and swap. Builds on the `godot-development` skill (folder layout, Resources, signals). GDScript only.

## Project-specific information

This skill is generic. Everything specific to this project lives in **`prototype/models.md`**: which packs, rigs and files are used and where they are, the visual interface units call and the shared visual scripts that already exist, library names, clip choices per character, scale for the game camera, game timing, and known gotchas.

- **Read `models.md` before starting**, and reuse what it lists instead of building a second version.
- **Check the 3D style** in `docs/style/3d_style.md` before choosing or adding models. If it says "No style defined yet", match the models already in the game and mention that no style is defined.
- **Write new findings back to `models.md`** (new packs, rigs, clips, conventions, problems solved), not into this skill.

## Core principles

1. **Never edit vendor files.** Keep downloaded models in one vendor folder with their original names and wrap them in your own scenes. Re-importing or updating a pack then never destroys your work.
2. **Models and animations are separate.** Import animation files as an `AnimationLibrary` and share one library across every character on the same rig.
3. **Game code talks to an interface, not to a model.** Units call a small visual interface (e.g. "moving", "attack", "hit", "fall"); only the visual scene knows clip names, bones and props. Swapping a placeholder for a model then needs no game-logic changes.
4. **Configure in import settings, not in code.** Loop modes, import type and texture handling belong in the `.import` file (via the Import dock), so every user of the asset gets them.
5. **Only import what is used.** Raw zips and unused formats stay outside the Godot project, in the repo's git-ignored `downloads/` folder; only the files in use are copied to `assets/` and exported (see the `godot-ai-architecture` skill).

## 1. Inspect a pack before importing

Unzip into a temporary folder **outside** the project so Godot does not import hundreds of files. Then:

- Read the license and keep its file with the assets.
- Prefer **glTF** (`.glb`/`.gltf`) over FBX/OBJ: it is Godot's preferred 3D format.
- Find which files are characters, which are animations, and which are props.
- Check what is really inside with Godot itself. This headless script loads a file without importing it into a project (run with `godot --headless --path <any project> -s inspect.gd`):

```gdscript
extends SceneTree

func _initialize() -> void:
	var doc := GLTFDocument.new()
	var state := GLTFState.new()
	if doc.append_from_file("C:/path/to/Character.glb", state) != OK:
		quit()
		return
	print("images: ", state.get_images().size(), " skins: ", state.get_skins().size())
	var scene := doc.generate_scene(state)
	for skeleton: Skeleton3D in scene.find_children("*", "Skeleton3D", true, false):
		var bones := []
		for i in skeleton.get_bone_count():
			bones.append(skeleton.get_bone_name(i))
		print("bones: ", bones)
	var player := scene.find_child("AnimationPlayer", true, false) as AnimationPlayer
	if player:
		for anim_name in player.get_animation_list():
			var anim := player.get_animation(anim_name)
			print(anim_name, " ", anim.length, "s loop=", anim.loop_mode)
	scene.free()
	quit()
```

Find out and record in `models.md`:

- **Rig name and bone names**, including any bones meant for props (hand slots). Characters can only share animations if bone names, bone rests, and the node path to the skeleton match.
- **Track paths** in the animations (e.g. `<Rig>/Skeleton3D:hips`). The model's node hierarchy must give the same path from the AnimationPlayer's root node.
- **Facing direction.** Godot's forward is -Z (`Basis.looking_at` points -Z at the target). Many packs face +Z; those need a 180 degree turn inside the visual scene. Compare the position of a face part (visor, nose) with the head's centre to tell.
- **Size** (bounding box) compared with the game's scale and camera.
- **Root motion.** Check whether the hips/root move forward in walk/run clips. In-place clips suit code-driven movement.
- **Loop flags.** glTF clips often come without loop flags; these must be set at import.
- **Embedded vs external textures.** `.glb` files usually embed textures; `.gltf` + `.bin` files reference image files by name.
- **Missing clips** (e.g. attacks). Look for a companion animation pack for the same rig before improvising; character packs often ship only general and movement clips.

## 2. Folder layout

Vendor files in one third-party folder per pack, your own scenes next to the entity that uses them:

```
<project>/
  assets/third_party/<pack_name>/        # vendor files, ORIGINAL names, never edited
    License.txt
    characters/   <Character>.glb ...
    props/        <prop>.gltf, <prop>.bin, <texture>.png ...
  assets/third_party/<animation_pack>/   # an animation-only pack gets its own folder
    License.txt
    animations/<rig>/   <clip set>.glb ...   # imported as AnimationLibrary
  common/visuals/
    <visual interface script>            # what units call
    <rig>_visual.gd                      # shared script for every model on one rig
  entities/<kind>/<entity>/
    <entity>.tres                        # data; points at the visual scene
    <entity>_visual.tscn                 # your wrapper scene
```

Rules:

- **Keep original file names.** A `.gltf` references its `.bin` and textures by file name; renaming breaks it. A `.glb` is self-contained, but keep its name too so it matches the pack and future updates.
- Keep a `.gltf`, its `.bin` and the textures it references **in the same folder**.
- Use project vocabulary (snake_case) for your scenes and scripts, even when the vendor's name differs or clashes with a term the game already uses.
- **One copy of each file.** Packs from the same author often ship identical animation files. Compare sizes or hashes and import each file once, from the most complete pack.
- **Only the rig you use.** Skip files for other rigs, FBX/OBJ duplicates, sample renders, and clip sets with no use in the game.
- **Commit the `.import` files.** They hold the importer type and loop settings; without them a fresh checkout imports the files as plain scenes with no loops.

## 3. Import settings

Change import settings in the editor (select the file, **Import** dock, or double-click for **Advanced Import Settings**), then **Reimport**. The settings are saved in `<file>.import`. Hand-editing `.import` files works with the editor closed; Godot rewrites them with all defaults on the next import.

### Character models (`importer="scene"`)

- Keep the default **Scene** import. Do not open the imported scene to change it; instance it inside a wrapper scene instead (section 4). Inherited scenes are possible but cannot remove nodes and make vendor updates harder.
- `skins/use_named_skins=true` (default): skins reference bones by name.
- `meshes/generate_lods`: on by default. Low-poly stylized models gain little; turning it off reduces file size and import time.
- `meshes/ensure_tangents`: only needed for normal/height maps.
- Textures: `gltf/embedded_image_handling` decides whether embedded textures are extracted to files (more control over their import settings) or kept embedded.
- Materials: leave them embedded unless you need to change them. To edit one, use **Advanced Import Settings > material > Use External** and save it as a `.tres`, so the change survives reimports.

### Animation files (`importer="animation_library"`)

For files that only hold animations (no character you want to show):

1. Select the file, and in the Import dock set **Import As: Animation Library**. Reimport (restart the editor if asked).
2. In **Advanced Import Settings**, select each looping clip and set **Loop Mode** to Linear. Reimport.
3. Leave `animation/remove_immutable_tracks=true` (default) for smaller files.

Verified with Godot 4.7: the resulting `.import` looks like this, and `load()` returns an `AnimationLibrary` whose clips have the loop modes set (0 = none, 1 = linear, 2 = ping-pong):

```
importer="animation_library"
type="AnimationLibrary"
...
_subresources={
"animations": {
"Idle_A": {
"settings/loop_mode": 1
}
}
}
```

Naming a clip with a `-loop` / `_loop` suffix in the source file also marks it as looping on import, but vendor files rarely do this; set loop modes in the import settings instead.

**Which clips loop.** Loop the continuous states: idles, walk/run cycles, held poses (`*_Pose`, `*_Idle`), and "-ing" clips meant to repeat (blocking, spellcasting, shooting, aiming). Leave one-shots (attacks, hits, deaths, jumps, spawns, start/end transitions) non-looping, so `animation_finished` fires and the code can return to the base state.

**Setting this up without the editor** (from a script or the command line; verified with Godot 4.7):

1. Copy the files in and run `godot --headless --path <project> --import` once. This creates a `<file>.import` per file with `importer="scene"`.
2. In each `.import`: change `importer="scene"` to `importer="animation_library"` and `type="PackedScene"` to `type="AnimationLibrary"`, delete the `path=` and `dest_files=` lines, and replace `_subresources={}` with the looping clips (format above). Keep the `uid=` line. (If you script this with `sed`, the `/` in `settings/loop_mode` needs a different delimiter, e.g. `s#...#...#`.)
3. Run `--import` again. Godot rewrites the files with all defaults filled in.
4. Verify: `load()` each file, check `get_class() == "AnimationLibrary"` and the clips' `loop_mode`.

**Library names.** In the `AnimationPlayer`, add each library under a short snake_case name for its file's topic (e.g. `general`, `movement`, `combat_melee`) and play clips as `"library/clip"`. Use the same names for every character so clip names stored in data stay valid for all of them. Record the names in `models.md`.

**Choosing clips.** List every clip with its length first (the inspection script prints them). Prefer clips whose length is close to the game action they show, or play them faster with the `custom_speed` argument of `play()`. Check whether a clip moves the hips away from the origin (deaths, sit-downs, "awaken" clips): the visual then ends up offset from the unit's position.

### Sharing animations between characters

- **Same rig** (identical bone names, rests and skeleton node path): no retargeting needed. One library works for every character.
- **Different rigs**: use Godot's retargeting. In the model's Advanced Import Settings, select the Skeleton3D, add a **BoneMap** with `SkeletonProfileHumanoid`, and enable the Retarget options (**Bone Renamer > Rename Bones**, **Unique Node > Make Unique** with a skeleton name so track paths do not depend on the hierarchy, and **Rest Fixer > Overwrite Axis**). Do the same for the animation files. Expect tuning; non-humanoid rigs need matching skeletons instead.
- A common failure: the library "does nothing" because the AnimationPlayer's `root_node` or the skeleton's node path differs from the track paths. Compare a track path with the model's tree.

## 4. The wrapper visual scene

One small scene per character, whose root script implements the project's visual interface:

```
<Character>Visual (Node3D, script: shared <rig>_visual.gd)
  Model (instance of the character .glb; rotated 180 degrees if the pack faces +Z; scaled to game size)
    <Rig>/Skeleton3D
      (BoneAttachment3D nodes for props, created in code or via Editable Children)
  AnimationPlayer (root_node = ../Model, with the shared libraries)
```

- **BoneAttachment3D** under the Skeleton3D makes a prop follow a bone. Create it in code from exported prop scenes (keeps `.tscn` files small and avoids editable-children paths) or add it with **Editable Children**; either way the vendor file stays untouched. Give each prop an optional offset `Transform3D` export, and adjust that offset, never the bone.
- **Check a prop in an attack pose before "fixing" it.** Packs with hand-slot bones usually author props to sit at the slot with no offset; one-handed props may point down in idle and swing up in attacks, which is intended. Measure the prop's mesh AABB (its long axis) and look at an attack frame before adding a rotation.
- **AnimationPlayer** lives in your scene, not in the model, with `root_node` pointing at the model so track paths resolve. Add the libraries in the Inspector (Animation > Manage Animations > Load Library) or in code with `add_animation_library()`.
- **Scale and facing** are set on the `Model` node only, so the unit's own transform and the game logic stay unchanged.
- The entity's data Resource points at the wrapper scene; an empty value falls back to the placeholder visual.
- **One shared script per rig.** Expose per-character choices as exports (clip names, clip speeds, prop scenes and offsets, model height), and make each character scene only set those exports:

```gdscript
extends <VisualInterface>
## Visual for any character on <rig>.

@export var idle_clip: StringName = &"general/Idle"
@export var move_clip: StringName = &"movement/Run"
@export var attack_clip: StringName = &"combat/Attack"
@export var attack_clip_speed: float = 1.0
@export var hit_clip: StringName = &"general/Hit"
## Played in order; the last one (a held pose) stays.
@export var death_clips: Array[StringName] = [&"general/Death", &"general/Death_Pose"]
## Skill/ability cue -> clip, for actions with their own animation.
@export var skill_clips: Dictionary = {}
@export var blend_time: float = 0.15
@export var right_hand_prop: PackedScene
@export var right_hand_prop_transform: Transform3D = Transform3D.IDENTITY
## Height of the scaled model, so health bars and labels can sit above it.
@export var height: float = 2.0
```

- Useful interface methods beyond move/attack/hit/fall: a **height** query (for health bars, labels and projectile origins) and a **skill/ability** call with a cue name that falls back to the attack animation.

## 5. Driving animations from code

- **Looping base state** (idle or move) plus **one-shot overlays** (attack, hit). Track the base state; after a one-shot finishes (`animation_finished`), cross-fade back to it:

```gdscript
var _moving := false
var _one_shot: StringName = &""   # the one-shot clip playing, if any
var _fallen := false

@onready var _player: AnimationPlayer = $AnimationPlayer


func _ready() -> void:
	_player.animation_finished.connect(_on_animation_finished)


func set_moving(moving: bool) -> void:
	if moving == _moving:
		return   # callers may report movement every frame
	_moving = moving
	_play_base()


func play_attack(_target_position: Vector3) -> void:
	_play_once(attack_clip, attack_clip_speed)


func play_hit() -> void:
	if _one_shot == &"":   # a flinch never cancels an attack
		_play_once(hit_clip, 1.0)


func play_fall() -> void:
	_fallen = true
	_one_shot = &""
	_player.play(death_clips[0], blend_time)
	for i in range(1, death_clips.size()):
		_player.queue(death_clips[i])   # hold the final pose


func _play_base() -> void:
	if _one_shot == &"" and not _fallen:
		_player.play(move_clip if _moving else idle_clip, blend_time)


func _play_once(clip: StringName, speed: float) -> void:
	if _fallen:
		return
	_one_shot = clip
	_player.play(clip, blend_time, speed)
	_player.seek(0.0, true)  # restart if the same clip was already playing


func _on_animation_finished(clip: StringName) -> void:
	if clip == _one_shot:
		_one_shot = &""
		_play_base()
```

- **Do not call `play()` every frame** with the same clip; only on state changes. Game code often reports movement every physics frame, so the visual must ignore calls that do not change the state, or the clip restarts constantly.
- **Never use a looping clip as a one-shot.** A looping clip never emits `animation_finished`, so the visual stays stuck in it. Pick a non-looping clip for one-shot actions.
- **Match animation speed to movement** to avoid foot sliding: `_player.speed_scale = current_speed / authored_move_speed` while moving, `1.0` otherwise.
- **Fit one-shots to game timing.** If an action lasts a fixed time in the game, play longer clips faster (`play(clip, blend_time, speed)`). `Engine.time_scale` speeds animations up together with the game.
- **Hit timing.** If damage should land at the impact frame, add a **Call Method** track at that frame (or a timer of the same delay) rather than applying damage when the swing starts. Keep combat rules in game code; the visual only reports the moment.
- **AnimationPlayer first, AnimationTree later.** A plain AnimationPlayer with cross-fades covers idle/move/attack/hit/death. Switch to an `AnimationTree` (state machine, blend spaces, one-shot nodes) when you need blending between many states or upper-body/lower-body layering.
- **Death and removal.** If a unit is freed shortly after dying, make sure the death clip is shorter than the corpse time (or lengthen the corpse time).
- **Projectiles from hands.** Expose a marker (e.g. a `Node3D` under a BoneAttachment3D) so ranged attacks can start at the weapon instead of above the unit.

## 6. Mobile performance

- Each **MeshInstance3D is at least one draw call**. Modular characters are often split into 8-10 parts; 50 such characters means 400-500 draw calls. Hide unused parts, and test on a real phone before committing to many animated characters.
- **Skinning and animation cost scale with the number of characters.** Ideas when there are many:
  - Pause animation for characters off screen (`VisibleOnScreenEnabler3D`).
  - Lower the update rate for distant or background characters (`AnimationMixer.callback_mode_process = MANUAL` and `advance()` on a timer).
  - Keep simpler visuals (fewer parts, no props) for crowds; full models for important characters.
- Disable **cast shadows** on small props and on crowds if shadows are expensive. Make it a per-visual export (e.g. `cast_shadows`) so important characters keep shadows while crowd visuals turn them off. When walking a visual's meshes to change settings, call `find_children("*", "GeometryInstance3D", true, false)`: the last argument (`owned = false`) is needed because meshes inside an instanced `.glb` are not owned by your scene's root.
- Keep textures small (stylized packs often use palette textures of 1024x1024 or less) and enable mobile VRAM compression (ETC2/ASTC).
- Use `speed_scale` with slight random variation per unit so crowds do not animate in lockstep.

## 7. Verify

- Run the inspection script (section 1) on new files, and watch for importer errors (`godot --headless --path <project> --import`).
- After importing, check in a headless script that each library loads and loop modes are set:

```gdscript
var lib: AnimationLibrary = load("res://assets/third_party/<pack>/animations/<rig>/<clip set>.glb")
print(lib.get_class(), " ", lib.get_animation("<looping clip>").loop_mode)  # expect AnimationLibrary 1
```

- **Look at it from the real game camera**: scale, facing, prop placement, health bar height and lighting. A `SceneTree` script run **without** `--headless` (e.g. `godot --path <project> --resolution <phone size> -s shot.gd`) can instance the main scene, wait some frames, and save `root.get_viewport().get_texture().get_image().save_png(path)` to a temp folder. For close-ups, add a temporary `Camera3D`, `look_at_from_position()` it at a unit, and make it `current`.
- **Size for the game camera.** Stylized models often read small from a high, distant camera; scale the `Model` node up until characters stay readable on the target screen, and update the height export to match.
- **Test-script pitfalls.** In a `SceneTree` script, a scene added in `_initialize()` is not ready yet (its `@onready` variables are null); call into it from `_process()` after the first frame. Disabling a node's processing (`process_mode = DISABLED`) also pauses its `AnimationPlayer`, so characters freeze in T-pose; to pose units for a screenshot, let them run a few frames instead.
- **Single screenshots cannot prove an animation plays** (a frame may land on a blend or a pose similar to idle). Log state changes instead: in a headless run, print each visual's `AnimationPlayer.current_animation` and `get_playing_speed()` whenever they change, and check that every action and the return to idle appear.

## Checklist when adding a model pack

1. Read `models.md` for what already exists.
2. Unzip outside the project, read the license, inspect with Godot (section 1). Record rig, facing, size, clips and gaps in `models.md`.
3. Copy only the needed glTF files into the vendor folder with original names; keep `.gltf` + `.bin` + textures together; copy the license.
4. Import animation files as **Animation Library**; set loop modes.
5. Reuse the shared visual script for the rig if one exists (see `models.md`), or write one; create one `<entity>_visual.tscn` per character (model instance, facing/scale, props, AnimationPlayer with the libraries).
6. Point the entity's data Resource at the new scene.
7. Tune scale, height, animation speed and attack timing; verify (section 7).
8. Check performance if many instances will be on screen at once.
9. Update `models.md` with what was added, clip choices, and anything learned.

## Sources

- Godot docs, Import configuration (import options, Animation Library import, import scripts): https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/importing_3d_scenes/import_configuration.html
- Godot docs, Retargeting 3D skeletons (BoneMap, Rename Bones, Unique Node, Overwrite Axis, remove-tracks options): https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/retargeting_3d_skeletons.html
- Godot forum, managing character animations long term (separate model and animation-library files): https://forum.godotengine.org/t/advise-for-managing-characters-animations-in-the-long-run/86404
- Godot forum, library not applying when node names differ: https://forum.godotengine.org/t/exporting-animation-from-glb-and-applying-it-to-another-glb/138134
- KidsCanCode, Importing assets (loop mode in the Advanced Import window, `-loop` suffix): https://kidscancode.org/godot_recipes/4.x/3d/assets/importing_assets/index.html
