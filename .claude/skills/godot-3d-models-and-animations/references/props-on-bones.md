# Props on bones: holding a weapon

A weapon is a separate static model that rides on a bone. `scripts/bone_prop.gd` (`BoneProp.attach`)
puts it under a `BoneAttachment3D` on the skeleton, with an offset `Transform3D`:

```gdscript
BoneProp.attach(skeleton, &"mixamorig_RightHand", axe_scene, offset)
```

The attachment follows the bone through every clip, and the model's scale applies to the prop too
(a prop under a model scaled x5 is five times bigger; give the offset the scale you want **relative to
the model**, not in metres). Vendor characters with hand-slot bones need no offset (section 4 of
`SKILL.md`); a model with plain `RightHand` bones does, because the bone's axes point anywhere.

## Placing a grip

Guessing a rotation and checking by eye wastes many rounds. Compute it, then look:

1. **Know the prop's axes.** Its AABB (or a front-view render) tells the long axis (the shaft) and
   where its origin is (usually the grip point, made for a hand slot).
2. **Decide the pose in model space**, not in the bone's axes: for a weapon carried at the side, the
   shaft points forward and a little up (30 degrees looks relaxed; level looks stiff; 60 covers the
   face), the blades up and down so a chop swings them along the swing.
3. **Find the fist.** Pose the model in its idle clip, frame 0. The bone line runs through the
   wrist; the **hollow of the fist is lower and to the palm side**. Estimate it from the bones: the
   palm centroid (the mesh vertices weighted to the hand bone, skinned with `bone_pose * bind_pose`)
   and the finger and thumb tips; the middle of that group is where a handle crosses. A hand hanging
   with the palm toward the thigh and the fingers curled forward holds a handle running **front to
   back**, like a bag handle. A first guess halfway to the middle finger put the shaft through the wrist,
   about 7% of the model's height too high.
4. **Solve the offset**: `offset = hand_global_pose.affine_inverse() * Transform3D(prop_basis.scaled(S),
   grip_point)` with `prop_basis` built from the wanted axes (`Basis(x, y, x.cross(y))`, columns) and
   `S` the prop's scale. Print it as `Transform3D(xx, yx, zx, xy, yy, zy, xz, yz, zz, ox, oy, oz)`
   (rows, as `var_to_str` writes it) for the `.tscn`.
5. **Look**, from close: focus the camera on the fist, not the wrist (a crop centred on the wrist
   hid the fist off the bottom of the picture and made every variant look wrong). Compare variants in
   one contact sheet (`testing-recipes.md`): front, outer side and a three-quarter view.
6. **Try it in the other clips**: the swing, the bite, the hit reaction, the death and the taunt.
   An empty hand pose holds the prop loosely; a clip made for a weapon may pass it through the
   body. Fix the worst with the offset or choose another clip; do not edit the bone.

Keep the offset and the prop scene as exports on the visual (`right_hand_prop`,
`right_hand_prop_transform`, `right_hand_bone`) so every character sets only data.

## Size

A prop made for a 1.8 m character looks small on a 5 m one. Scale it by the model ratio, then by eye:
a weapon about two thirds of the wielder's height reads as huge without looking absurd.
