# Retargeting a clip onto another rig

You have a clip made for one skeleton (a Mixamo `.fbx`) and a model with another skeleton that
**names its bones the same way** (an auto-rigged model). Copying the clip's tracks does not work, even
though the names match. Godot's own retargeting (BoneMap + `SkeletonProfileHumanoid`, section 3 of
`SKILL.md`) is the official route and changes the model's import; this page is the other route, in
code at load time, which leaves every file as it is. Use the code route for a handful of clips on a
test or AI-made model; use the import route when many models share a profile.

## Why copying fails

A rotation track says "set this bone's local rotation to Q". Q only means the same thing if the bone
has the same local axes and the same rest pose. Compare the two skeletons' **rest rotations by bone
name** (`get_bone_rest(i).basis`): on a Mixamo clip and an auto-rig they differ by 90 to 180 degrees
at the hips, upper legs and shoulders, and by tens of degrees at arms, feet and fingers. The model
twists. The rest poses differ too (a T-pose and an A-pose), so even "apply the same change from rest"
swings the arms about 45 degrees too far.

Check first: `find_bone(name)` finds every bone on both sides, and each bone has the same parent. If
the hierarchies differ, this method does not apply.

## The method (what `scripts/clip_retarget.gd` does)

For every frame (sampled at 30 fps over the clip's length):

1. Pose the **source** skeleton: from each bone's source rotation (or its rest rotation if the clip
   has no track for it), compute its model-space rotation by walking the parents.
2. For every **target** bone that has a child to point at (the "guide" child: the longest child,
   skipping `Left`/`Right` children when a centre child exists, so the hips point at the spine):
   - turn the bone so that its guide direction (model space) points where the source's does
     (`Quaternion(arc_from, arc_to)` on the direction at rest and the direction in the pose);
   - then add the source's **twist** around that bone (the part of the source's rest-to-pose rotation
     around its rest direction: `angle = 2 * atan2(dot(axis, q.xyz), q.w)`).
3. Convert to the target's local rotation: `parent_pose.inverse() * pose`.
4. Bones with no guide child (finger tips, "end" bones) keep their rest rotation.
5. The root bone's **position** track is scaled by the ratio of the two rest heights (a Mixamo hips
   are about 1.0 up, a normalized model's about 0.5); other bones have no position tracks.
6. Track paths are rewritten to the target skeleton's path (`Armature/Skeleton3D:mixamorig_Hips`
   instead of `Skeleton3D:mixamorig_Hips`).

Result: bone directions match the source in every frame, whatever the axes or rest pose.

```gdscript
# Once per model, at load time. `player` is the model's AnimationPlayer.
ClipRetarget.add_clip(player, model, preload("res://.../orc_walk.fbx"), &"orc_walk", true)  # loops
```

## Verify numerically, then look

Pose both skeletons at the same times and compare each bone's direction in model space (world
direction from the bone to its child). The error should be a fraction of a degree. Then take a
screenshot (`testing-recipes.md`): the numbers prove the directions, not that the model looks right
(a hand turned the wrong way around its axis would still pass).

## Pitfalls

- **Names collide silently.** An imported model often has clips named `run`, `walk`, `idle`. Adding a
  retargeted clip under the same name used to return the model's own clip, and everything measured or
  played afterwards was the wrong clip (a run clip's speed was measured on the model's own run). The
  script now refuses and logs an error; give retargeted clips their own names (`orc_walk`,
  `unarmed_run`).
- **The animation library is shared by every instance** of the model scene. The script adds a clip
  once and reuses it (it marks the clip with metadata), and loop modes and root-travel fixes are
  applied to that shared clip once. Do not hand-edit a clip per instance.
- **Loops.** Imported clips do not loop; set `loop_mode` on the clips that must (`add_clip(...,
  loop)` for the retargeted ones, in code for the model's own).
- **`.tscn` syntax** for an exported typed dictionary of clips: `Dictionary[StringName, PackedScene]({
  &"name": ExtResource("id"), ... })`.
- **Cost.** About 50 frames x 65 bones per second of clip, at load, once per clip and model; the
  result is a plain `Animation`. If load time ever matters on a phone, bake each result to a `.res`
  with a headless script that calls the same function, and load that instead.
- A different humanoid with other bone names (KayKit's `Rig_Medium`) needs the bone names mapped
  first; this script only matches by name.
