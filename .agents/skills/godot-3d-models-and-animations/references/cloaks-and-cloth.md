# Cloaks, capes, ponytails and other hanging parts

How to make a modelled cloak (or cape, long coat tail, loose skirt panel) or a ponytail on a rigged
character hang right standing and move without the body poking through it, in Godot 4.5+
(built-in spring bones). Written from a chibi Tripo model with a long cloak and a ponytail; the
numbers are examples from it (1.0 tall in its own units). Bundled scripts:
`scripts/split_part.py` and `scripts/add_bone_chains.py` (plain Python with numpy on the `.glb`),
`scripts/spring_chains.gd` (the Godot side) and `scripts/spring_measure.gd` (numbers).

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
   `split_part.py in.glb --list` lists the pieces (number, triangles, bounds);
   `split_part.py in.glb out.glb Cloak "id:13846,13837" --mask` splits them (or boxes
   `"x0,x1,y0,y1,z0,z1"`). To find the pieces, split each candidate into its own node and render
   them in colours (`GLTFDocument` loads the file in a test script; `material_override` per node),
   from every side: thin strands and small shells are easy to miss.
2. **Add bone chains in the `.glb`** with `add_bone_chains.py in.glb out.glb --preset cloak`
   (no Blender); it prints each joint's position, check them against the part's bounds:
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
   `set_enable_all_child_collisions` true. `spring_chains.gd` (`SpringChains`) does this
   (`chain_roots()`, `setup_chains()`); extend it once per part (`CloakBones`, `HairBones`) with
   the part's values and colliders. Values that looked right on a 1.0-tall model:
   stiffness 3, drag 0.75, gravity 1.5 down, joint radius 0.03. Stiffness 1.2 / drag 0.5 let the cloak
   fly up like wings and wrap round to the front on a turn.
   - **Centre the simulation on the skeleton**: `set_center_from(i, CENTER_FROM_NODE)` and
     `set_center_node(i, get_path_to(skeleton))` for every setting. By default it simulates in world
     space, so a unit walking through the level at game speed and turning drags every joint: the
     cloak flaps like in a storm, while in a viewer where the model walks in place it looks fine.
     Centred, only the animation swings it, the same in place, moving or turned (measured).
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

## Hair (a ponytail)

The same steps with one chain. An auto-rig usually skins a ponytail 100% to the head, so it is
rigid: it never swings and can cut into the back when the head tilts.

1. **Split it** (`split_part.py ... Ponytail "id:..." --mask`). A ponytail is many shells: big
   locks, thin strands, an arc over the hair tie (34 pieces, 3,011 triangles on the chibi). Leave the
   hair tie on the head.
2. **One chain under the head**: `add_bone_chains.py in.glb out.glb --preset ponytail` (bones
   `ponytail_a_0..3` under the Head, at heights 0.2 / 0.42 / 0.64 / 0.86 of the ponytail, each joint
   the mean of its height slice). Put the first joint **below** the arc over the tie, so the arc
   blends into the head and the ponytail stays tied on when it swings.
3. **Spring bones, looser than a cloak**: stiffness 1.2, drag 0.4, gravity 0.8, joint radius 0.025,
   tip 0.05. The walk's own head and hip sway then swings it side to side (about 14 degrees).
4. **Colliders**: a sphere on the Head (fit a sphere to the head's vertices; centre slightly back,
   radius 0.11) and an upright capsule on Spine2 over the upper back and hood (radius 0.11, length
   0.2). Check that the rest pose is outside both (joint distance > collider radius + joint radius).
5. **Flow back while walking**: ease `external_force` in when the unit starts walking and out when it
   stops (0.5 s tween). **`external_force` is in the centre's space** (the skeleton's, when centred
   as above), not world space: a fixed model-space vector, (0, 0, -0.5) for a model whose front is
   +z, is her back whichever way she faces. A world vector rotated by the skeleton's basis came out
   sideways (measured). 0.5 leaned the ponytail about 23 degrees back; 1.5 about 48.

Use a separate simulator per part (`CloakBones`, `HairBones`): `external_force` is one value for the
whole simulator, so a push for the hair would also push the cloak.

## Checking it

- **Read spring-bone results inside `Skeleton3D.skeleton_updated`.** Modifier results are only in
  the bone poses during that signal; after the frame the poses are back to the animation's, so a
  measurement there shows the bones not moving at all (a test that compared a moving and a still
  unit gave identical numbers until it read the poses in the signal).
- **Measure angles in the skeleton's axes**, with the parent bone's turn taken out (pose basis x
  inverse rest basis). Mixamo-named bones have rotated rest bases, so "the head bone's own axes"
  are not up/front/side.
- `scripts/spring_measure.gd` does both: `-- <visual.tscn> <chain root> <chain last bone>
  <reference bone>` prints the lean back and the side swing (min, mean, max) standing, walking in
  place, walking while moving through the world, and the same turned. The last three must match
  (centred), standing should be near 0.
- Spring bones need real time: **play** the clip and capture at moments of it; seeking a paused
  player jumps the bones and shows nothing useful.
- Shoot the idle and 6 moments of an arm-heavy clip from behind, front, left and right, with the
  camera following the hips (clips like a slash travel). Then zoom on the busiest frames: a crouch
  shows the waist and the skirt, a kick the thighs.
- Check the walk too, and the game itself (the City or level), where the unit really travels and
  turns: if the cloth or hair whips about there but not in a viewer, the simulation is not centred
  on the skeleton (step 4).
- Known leftover: between two joints the cloth is only interpolated, so a deep crouch can still
  show a sliver. More joint rows or a bigger capsule there fix it.
