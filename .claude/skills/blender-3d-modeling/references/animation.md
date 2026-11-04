# Animation in Blender 5 (for games)

Tested on Blender 5.1.2 in the sandbox. Basic keyframing and the clip/NLA helper are in `bpy_recipes.md`; this file is the model behind them, rules for game clips, and the harder cases.

## How Blender 5 stores animation

```
Object.animation_data
  .action          the assigned Action (one clip)
  .action_slot     which slot of that action animates this object   (identifier e.g. "OBRig", "KEKey" for shape keys)
  .nla_tracks[]    stacked strips, each pointing to an action (+ strip.action_slot)

Action
  .slots[]         one per animated ID (an action can animate several objects)
  .layers[].strips[].channelbags[]   one channelbag per slot
        .fcurves[]                   the curves (data_path, array_index, keyframe_points)
```

- `action.fcurves` does **not** exist any more. Get the curves of what an object plays:
  ```python
  from bpy_extras import anim_utils
  cb = anim_utils.animdata_get_channelbag_for_assigned_slot(obj.animation_data)
  # or: anim_utils.action_get_channelbag_for_slot(action, obj.animation_data.action_slot)
  for fc in cb.fcurves: ...
  ```
- All curves of an action, whatever the slot: `for l in a.layers: for s in l.strips: for cb in s.channelbags: cb.fcurves`.
- Create curves by hand (rarely needed; `keyframe_insert` does all of this):
  ```python
  obj.animation_data_create()
  act = bpy.data.actions.new("Wave"); obj.animation_data.action = act
  slot = obj.animation_data.action_slot or act.slots.new(id_type='OBJECT', name=obj.name)
  obj.animation_data.action_slot = slot
  cb = anim_utils.action_ensure_channelbag_for_slot(act, slot)
  fc = cb.fcurves.ensure('pose.bones["Arm"].rotation_quaternion', index=0, group_name="Arm")
  fc.keyframe_points.insert(1, 1.0)
  ```
- Shape keys animate the **Key** datablock, not the object: `obj.data.shape_keys.animation_data`. Key a value with `key_block.keyframe_insert("value", frame=f)`.

## Rules for game clips

- **One action per clip**, named for the engine: `Walk-loop`, `Idle-loop`, `Attack`, `Death`. Godot loops clips whose name starts or ends with `loop` or `cycle`. Keep names unique and ASCII.
- **Keep every clip**: `action.use_fake_user = True` and push it to an NLA track (`make_clip` in `bpy_recipes.md`). An action with no user is dropped on save. Muted NLA tracks still export (`export_animation_mode='ACTIONS'`).
- **Frame rate**: set `scene.render.fps` (24 or 30) before keying; Godot reads time in seconds, so changing fps later changes clip speed.
- **Frame range**: `action.frame_range` comes from the keys. For an exact range set `action.use_frame_range = True; action.frame_start, action.frame_end = 1, 30`.
- **Bones: quaternions.** `pb.rotation_mode = 'QUATERNION'` and key `rotation_quaternion` — they blend and interpolate without gimbal flips. Euler is fine for a single-axis object spin. Do not switch modes inside a clip.
- **Do not animate bone scale** unless needed (it propagates to children and costs channels).
- **Connected bones cannot move** (`use_connect = True` locks their head to the parent's tail). The hips/pelvis must not be connected to the root if they translate.
- **Root motion vs in-place**: in-place clips keep the root bone at the origin (the game moves the character). Root-motion clips put forward travel and turning on the root bone only, while the hips keep bob and sway. Ask which one the game wants; Godot's AnimationTree reads root motion from a chosen root bone.
- **Rest pose = bind pose**: skin in the rest pose (T or A pose); clips only rotate from it.

## Loops

- The **last key must equal the first** (and sit one frame after the last unique pose if the engine plays frames 1..N). The `CYCLES` F-curve modifier is **preview-only**: glTF samples the keys, so a loop made only by the modifier pops.
- Full turns are fine: a rotation from 0 to 2π is seamless even though the numbers differ.
- Check and fix a loop (copies first-frame values onto the last frame):
  ```python
  a = bpy.data.actions["Walk-loop"]; f0, f1 = a.frame_range; fixed = []
  for l in a.layers:
      for s in l.strips:
          for cb in s.channelbags:
              for fc in cb.fcurves:
                  v0, v1 = fc.evaluate(f0), fc.evaluate(f1)
                  if abs(v0 - v1) > 1e-4:
                      fc.keyframe_points.insert(f1, v0, options={'REPLACE'}); fixed.append(fc.data_path)
  result = {"fixed": fixed}
  ```
  Also check the speed across the seam: the tangent at the last key should match the first (`kp.interpolation = 'LINEAR'` on both ends, or matching Bezier handles), otherwise the loop "hitches".
- `godot_export.py` reports loop clips whose first and last frames differ.

## Posing by matrix

Setting `pose_bone.matrix` (world-ish pose) depends on the parent's current pose: call `bpy.context.scene.frame_set(f)` first, set matrices **parent before child**, then key. Setting `rotation_quaternion`/`location` directly does not need this.

## Baking (constraints, IK, drivers, simulations → plain keys)

glTF and Godot only see keys. Anything driven by constraints (IK, Track To, Child Of), drivers or physics must be **baked** into a clip first:

```python
from bpy_extras import anim_utils
rig = bpy.data.objects["Rig"]
opts = anim_utils.BakeOptions(only_selected=False, do_pose=True, do_object=False, do_visual_keying=True,
                              do_constraint_clear=False, do_parents_clear=False, do_clean=True,
                              do_location=True, do_rotation=True, do_scale=False, do_bbone=False,
                              do_custom_props=False)
act = bpy.data.actions.new("Reach")
anim_utils.bake_action_objects([(rig, act)], frames=range(1, 31), bake_options=opts)
for pb in rig.pose.bones:
    for c in pb.constraints: c.mute = True        # or the constraints keep overriding the baked keys
act.use_fake_user = True
```

- `do_visual_keying=True` records the evaluated (constrained) pose. Object-level animation: `do_object=True`.
- Bake each clip separately (assign its source action, bake into a new action, push to NLA).
- Exclude helpers from the export: an animated IK target empty exports its own clip (e.g. `IKTargetAction`). Use `godot_export.py` with `objects=[rig]`, or delete the helper's animation after baking.

## Export

- `export_animation_mode='ACTIONS'` (default): each action used by an exported object becomes one glTF animation → one Godot clip.
- `export_force_sampling=True` (default): curves are sampled per frame, so modifiers and non-linear interpolation survive.
- `export_def_bones=True` for games: control/IK bones are dropped (bake first).
- Shape-key clips export as morph-target animations (`export_morph=True`).
- In Godot, each clip appears in the `AnimationPlayer`; loop clips by name suffix or in the import dock. See the `glb-3d-model-and-animations` skill for the Godot side.
