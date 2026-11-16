# Cloaks, capes and other hanging cloth

How to make a modelled cloak (or cape, long coat tail, loose skirt panel) on a rigged character
hang right standing and move without the body poking through it, in Godot 4.5+ (built-in spring
bones). Written from a chibi Tripo model with a long cloak; the numbers are examples from it.

## Why an AI auto-rig breaks a cloak

An auto-rig (Tripo's, Mixamo's) skins every vertex to the bones that are **near it in the
A-pose**. A cloak hangs next to the arms in that pose, so it gets skinned mostly to the arms
(85% of the weight on upper arms, forearms and shoulders, measured). In the A-pose it looks
perfect; in any other pose it follows the arms like two sleeves: in the idle the arms come down and
in, so the cloak's sides pull in and the skirt shows through; in an attack it flies up with the
raised arm. A new generation of the model has the same problem (same auto-rig, same pose), so it is
not worth paying for one. Measure before guessing: sum each bone's weight over the cloak's vertices
(read JOINTS_0/WEIGHTS_0 of its vertices from the `.glb`).

Look for it with a clip that moves the arms far from the body (a slash, a spell), from **behind
and in front**, not only the side; the walk can hide it.

## How games handle it (pick a combination)

| Technique | Use | Limit |
|---|---|---|
| Delete the body under the cloth | Parts that are covered in every pose (a torso under a fixed coat) | Not for a cloak that moves: the gap shows when it swings |
| Re-skin the cloth to the body under it | Always: spine and hips, never the arms | Alone, any pose not planned for still clips |
| **Bone chains + spring bones + capsule colliders** | The usual way for capes, skirts and hair in stylized games: cheap (bones, not vertices), reacts to every pose | Only the joints collide: cloth between two joints can still cut an edge |
| Design the cloth away from the body | A cape that flares and does not wrap the sides | Needs a new model |
| Full cloth simulation | Rarely on phones | Expensive, still clips in fast motion |

## The recipe

1. **Split the cloak into its own node** (the export is one mesh made of separate shells): move the
   cloak's shells into a new mesh node with the same skin, vertices and material, and bake vertex
   colours on it: red = how far down the cloak (0 top edge, 1 hem), green = which side. The colours
   give the re-skin (and any shader) a pose-free "height" and "side".
2. **Add bone chains in the `.glb`** (plain Python on the glTF JSON and binary is enough; no Blender):
   - 5 chains at angles around the back (e.g. -80, -40, 0, 40, 80 degrees; 0 = middle of the back),
     4 joints each at heights 0.12 / 0.37 / 0.62 / 0.87 of the cloak, named `cloak_<chain>_<n>`.
   - Each joint sits on the cloak surface (mean of the cloak vertices near that angle and height),
     rotated like the armature (identity in model space). The first is a child of the upper spine
     bone (Mixamo `Spine2`), each next one a child of the one above.
   - Append the joints to the skin's `joints` and their inverse bind matrices
     (`inverse(global rest matrix)`) to a new accessor; check `IBM * global = identity` for every joint.
3. **Re-skin the cloak**: each vertex blends the two nearest chains (by angle) and, in each, the
   two nearest joints (by height): at most 4 influences. Above the first joint, blend to the upper
   spine and, on the sides, that side's shoulder. No arm weight at all. If the cloak's vertices are
   only its own (separate shells), its rows of the shared JOINTS_0/WEIGHTS_0 can be rewritten in
   place; assert that no other primitive's indices use them.
4. **Swing the chains in Godot** with a `SpringBoneSimulator3D` child of the `Skeleton3D` (it is a
   `SkeletonModifier3D`), built in code from the bone names: one setting per chain
   (`set_root_bone_name` = `..._0`, `set_end_bone_name` = the last, `set_extend_end_bone` true,
   `BONE_DIRECTION_FROM_PARENT`, `set_end_bone_length` to reach the hem), and
   `set_enable_all_child_collisions` true. Values that looked right on a 1.0-tall model:
   stiffness 3, drag 0.75, gravity 1.5 down, joint radius 0.03. Stiffness 1.2 / drag 0.5 let the cloak
   fly up like wings and wrap round to the front on a turn.
5. **Colliders**: `SpringBoneCollisionCapsule3D` children of the simulator, each on a body bone
   (`bone`), placed from the rest pose: for a capsule from bone A's head to bone B's head,
   `offset = skeleton.get_bone_global_rest(A).affine_inverse() * Transform3D(Basis(Quaternion(Vector3.UP, dir)), midpoint)`,
   then `position_offset = offset.origin`, `rotation_offset = offset.basis.get_rotation_quaternion()`,
   `height = length + 2 * radius` (the height includes the caps). Shapes used:
   - the skirt: one capsule **across** the hips (axis along x), so its round ends cover the sides;
   - waist (Hips to Spine1) and torso (Spine1 to Neck);
   - thighs **as thick as the skirt over them** (the skirt flares back over them in a crouch or a
     kick), shins, upper arms, forearms, hands.
   Measure the gap between cloak and body by height and angle first, so the rest pose is not
   already inside a capsule (that would push the standing cloak out of its modelled shape).
6. Leave parts that ride on the shoulders (a hood, shoulder pads) on their own weights.

A vertex shader on the same part (e.g. a walk swing) still works on top: Godot skins before
`vertex()`. Turn it on only while needed (`material_override` swapped in and out) so the standing
cloak is the modelled one.

## Checking it

- Spring bones need real time: **play** the clip and capture at moments of it; seeking a paused
  player jumps the bones and shows nothing useful.
- Shoot the idle and 6 moments of an arm-heavy clip from behind, front, left and right, with the
  camera following the hips (clips like a slash travel). Then zoom on the busiest frames: a crouch
  shows the waist and the skirt, a kick the thighs.
- Check the walk too, and the game itself (the City or level), where real movement adds inertia.
- Known leftover: between two joints the cloth is only interpolated, so a deep crouch can still
  show a sliver. More joint rows or a bigger capsule there fix it.
