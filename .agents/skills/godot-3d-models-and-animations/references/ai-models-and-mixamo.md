# AI-made models and Mixamo animations

For a character that is **not** from a vendor pack: made by an image-to-3D tool (Tripo Studio, with its
auto-rig) and animated with clips from a free library (Mixamo). Same rules as the rest of the skill
(never edit the master, wrap it in a visual scene); what differs is where the files come from and what
to check.

## Getting the model

1. Make a clean source picture: a flat, smooth **A- or T-pose**, no weapon in the hands (add it as a
   prop, `props-on-bones.md`), plain background, no film grain or speckles (a texture-heavy style LoRA
   gave noisy skin and armour in the 3D result; a weak LoRA or none was cleaner).
2. Image to 3D, then **auto-rig** in the same tool, then export `.glb`. Ask for a lower polycount
   if the export offers it (a general on screen can take about 12,000 triangles; a mob should stay near
   the vendor models, about 5,000), and keep the rig.
3. The export is one mesh and one material with embedded textures; the size is **normalized** (about
   1.0 tall, origin at the feet), so scale it in the wrapper scene.
4. Record in the asset's `.md`: the source picture, the tool and its settings (write down the export
   dialog's polycount, topology and texture size, they are easy to lose), the file's real triangle
   count, the clips it came with, and **the plan's commercial-use terms** (read them before the model
   ships: a paid plan and a free plan differ).

Inspect it with the script in section 1 of `SKILL.md`: bone count and names (a Tripo rig has 65
`mixamorig:...` joints, which Godot imports as `mixamorig_...`), the clips inside it, and the facing.

## Mixamo downloads

Mixamo's animations are made for one humanoid skeleton (`mixamorig:Hips`, `...Spine`, ...), and
an auto-rig that names its bones the same way can play them, **after retargeting** (`retargeting.md`):
the names match, the bone axes and rest pose do not.

Download settings (the editor's sliders change the file you get, not only the preview):

| Setting | Use |
|---|---|
| Format | FBX Binary (`.fbx`); Mixamo has no glTF export. Godot 4.3+ imports FBX itself. |
| Skin | **Without Skin**: you have the model already; "With Skin" adds a second mesh. |
| Frames per second | 30 |
| Keyframe reduction | none |
| **In Place** | on, for walks, runs and idles (the game moves the unit) |
| Overdrive | 0 unless you want the clip faster and more exaggerated; change the speed in Godot instead |
| Character Arm-Space | 0 by default; raise it only if the arms clip a bulky model |
| Trim | the exported range; keep the start and end poses matching for loops |

Write the settings in the clip's record (`.md` next to the `.fbx`): they are not stored in the file.
Check each file after importing: one `AnimationPlayer`, one clip, the same bone count as the model,
and **no mesh** (a "With Skin" download has one). Mixamo's licence (royalty-free in projects with an
Adobe ID, not redistributable on its own) and Adobe's current terms go in the record too.

## Choosing clips

Search by what the action looks like, not by the name you want (names are odd): an idle "Orc Idle",
a walk "Orc Walk", a heavy strike "Standing Melee Attack Downward", a bite "Vampiric Bite" (a lunge
with the head), a taunt "Standing Taunt Chest Thump", a death "Dying Backwards", a flinch
"Standing React Large From ...", a run "Unarmed Run Forward". Heavy, slow clips suit a big creature.
Look at the **length and the moment of impact** before you pick (`tuning-clips.md`), and at whether
the clip carries a weapon pose (a two-hand swing with an empty hand looks fine on a huge unit holding
one weapon in one hand; a precise grip does not).
