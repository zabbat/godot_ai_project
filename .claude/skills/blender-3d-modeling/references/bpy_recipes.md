# bpy recipes (Blender 5.1)

Snippets for `execute_blender_code_for_cli(blend_file, code)` (or `execute_blender_code` in a VM). Each call is a fresh Blender process with `blend_file` open: **end every changing call with a save**, and assign a dict to `result`. All snippets were run headless in the Docker sandbox on Blender 5.1.2. Paths are sandbox paths: `/models/...` is the default share (`blender/models/`); `/export` and `/refs` are examples of extra shares from `blender/config/sandbox.toml`.

When something here fails on a newer Blender, check `search_api_docs` and fix this file.

## Create a new file

`blend_file` must be an existing file — Blender quits on a path that does not exist. In the Docker sandbox open the built-in empty scene **`/opt/empty.blend`** and save under the new path (it never changes, since you save *as*). In a VM, use `execute_blender_code` in the open Blender, or create an `empty.blend` there once.

```python
# execute_blender_code_for_cli(blend_file="/opt/empty.blend", code=...)
import bpy, os
path = "/models/crate/crate.blend"
os.makedirs(os.path.dirname(path), exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)   # empty scene, metric units
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0
bpy.ops.wm.save_as_mainfile(filepath=path)
result = {"saved": path}
```

## Inspect

```python
import bpy
def tris(o):
    if o.type != 'MESH': return 0
    m = o.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
    n = sum(len(p.vertices) - 2 for p in m.polygons); o.to_mesh_clear(); return n
result = {
    "file": bpy.data.filepath,
    "objects": [{"name": o.name, "type": o.type, "parent": o.parent.name if o.parent else None,
                 "loc": [round(v, 3) for v in o.location], "dims": [round(v, 3) for v in o.dimensions],
                 "materials": [s.material.name for s in o.material_slots if s.material],
                 "modifiers": [m.type for m in getattr(o, "modifiers", [])],
                 "tris": tris(o)} for o in bpy.data.objects],
    "materials": [m.name for m in bpy.data.materials],
    "actions": [{"name": a.name, "range": list(a.frame_range)} for a in bpy.data.actions],
    "frame_range": [bpy.context.scene.frame_start, bpy.context.scene.frame_end],
}
```

## Build meshes

Primitives (operators need nothing selected in background mode; the new object becomes active):

```python
import bpy
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.5))
crate = bpy.context.active_object
crate.name = crate.data.name = "Crate"
```

Exact geometry with bmesh (no operators, no context):

```python
import bpy, bmesh
mesh = bpy.data.meshes.new("Wedge")
bm = bmesh.new()
v = [bm.verts.new(p) for p in [(0,0,0), (1,0,0), (1,1,0), (0,1,0), (0,0,1), (0,1,1)]]
for f in [(0,1,2,3), (0,4,1), (3,2,5), (0,3,5,4), (1,4,5,2)]:
    bm.faces.new([v[i] for i in f])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(mesh); bm.free()
obj = bpy.data.objects.new("Wedge", mesh)
bpy.context.scene.collection.objects.link(obj)
```

Edit an existing mesh (extrude the top face up):

```python
import bpy, bmesh
obj = bpy.data.objects["Crate"]
bm = bmesh.new(); bm.from_mesh(obj.data)
top = max(bm.faces, key=lambda f: f.calc_center_median().z)
ret = bmesh.ops.extrude_face_region(bm, geom=[top])
verts = [e for e in ret["geom"] if isinstance(e, bmesh.types.BMVert)]
bmesh.ops.translate(bm, verts=verts, vec=(0, 0, 0.3))
bm.to_mesh(obj.data); bm.free(); obj.data.update()
```

## Modifiers, smoothing

```python
import bpy
obj = bpy.data.objects["Crate"]
bev = obj.modifiers.new("Bevel", 'BEVEL'); bev.width = 0.03; bev.segments = 2
sub = obj.modifiers.new("Subdiv", 'SUBSURF'); sub.levels = 1; sub.render_levels = 2
mir = obj.modifiers.new("Mirror", 'MIRROR'); mir.use_axis = (True, False, False)
obj.data.polygons.foreach_set("use_smooth", [True] * len(obj.data.polygons)); obj.data.update()
```

Apply a modifier (only when asked, or before export if the exporter should not do it):

```python
import bpy
obj = bpy.data.objects["Crate"]
bpy.context.view_layer.objects.active = obj
with bpy.context.temp_override(object=obj, active_object=obj):
    bpy.ops.object.modifier_apply(modifier="Bevel")
```

## Transforms, origin, apply scale

```python
import bpy
obj = bpy.data.objects["Crate"]
obj.location = (0, 0, 0); obj.rotation_euler = (0, 0, 0.785); obj.scale = (2, 2, 2)
for o in bpy.context.selected_objects: o.select_set(False)
obj.select_set(True); bpy.context.view_layer.objects.active = obj
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
```

Put the origin at the bottom centre (good for props that stand on the ground):

```python
import bpy, mathutils
obj = bpy.data.objects["Crate"]
bb = [obj.matrix_world @ mathutils.Vector(c) for c in obj.bound_box]
bottom = mathutils.Vector((sum(v.x for v in bb)/8, sum(v.y for v in bb)/8, min(v.z for v in bb)))
offset = obj.matrix_world.inverted() @ bottom
obj.data.transform(mathutils.Matrix.Translation(-offset))
obj.matrix_world.translation = bottom
obj.location.z = 0          # then stand it on the ground
```

`bound_box` includes modifier results (Subdivision, Mirror, ...).

## Materials

```python
import bpy
def material(name, color, metallic=0.0, roughness=0.5, emission=None, strength=1.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)   # comes with Principled + Output nodes
    bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')   # by type: names are translated
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    mat.diffuse_color = (*color, 1.0)        # viewport/Workbench colour (previews show this)
    mat.metallic, mat.roughness = metallic, roughness
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = strength
    return mat
obj = bpy.data.objects["Crate"]
obj.data.materials.clear()
obj.data.materials.append(material("Wood", (0.45, 0.28, 0.12), roughness=0.8))
```

Image texture (file must be in a shared folder):

```python
import bpy
mat = bpy.data.materials["Wood"]
nt = mat.node_tree
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = bpy.data.images.load("/refs/wood_albedo.png")   # colour map: keep sRGB
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
# data maps (roughness, metallic, normal, AO): tex.image.colorspace_settings.name = 'Non-Color'
# normal map: image -> ShaderNodeNormalMap "Color" -> bsdf "Normal"
```

Per-face materials: append several materials, then set `polygon.material_index`.

## Animation (object transforms)

Keyframes with `keyframe_insert` work as before; Blender 5 stores them in a **layered action with slots**, so reach F-curves through the channelbag:

```python
import bpy
from bpy_extras import anim_utils
scene = bpy.context.scene
scene.render.fps = 24; scene.frame_start = 1; scene.frame_end = 48
obj = bpy.data.objects["Crate"]
obj.rotation_euler = (0, 0, 0);       obj.keyframe_insert("rotation_euler", frame=1)
obj.rotation_euler = (0, 0, 6.28319); obj.keyframe_insert("rotation_euler", frame=49)
obj.location.z = 0.0; obj.keyframe_insert("location", index=2, frame=1)
obj.location.z = 0.3; obj.keyframe_insert("location", index=2, frame=25)
obj.location.z = 0.0; obj.keyframe_insert("location", index=2, frame=49)
action = obj.animation_data.action
action.name = "Spin-loop"
cb = anim_utils.action_get_channelbag_for_slot(action, obj.animation_data.action_slot)
for fc in cb.fcurves:
    for kp in fc.keyframe_points:
        kp.interpolation = 'LINEAR' if fc.data_path == "rotation_euler" else 'BEZIER'
    fc.modifiers.new('CYCLES')          # repeats in Blender's preview only - NOT exported
action.use_fake_user = True
result = {"action": action.name, "fcurves": [(fc.data_path, fc.array_index) for fc in cb.fcurves]}
```

For a seamless loop the last key equals the first (a full 0→2π turn counts) and sits one frame **after** `frame_end` (key 49, range 1–48). The `CYCLES` modifier only makes Blender's timeline repeat; glTF/Godot get the keys, so the loop must be in the keys. Rules for game clips, loops, baking and slots: `animation.md`.

## Armature, skinning, pose animation

Create an armature with bones (edit mode needs the armature active):

```python
import bpy
arm_data = bpy.data.armatures.new("RigData")
rig = bpy.data.objects.new("Rig", arm_data)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
root = arm_data.edit_bones.new("Root");  root.head = (0, 0, 0);   root.tail = (0, 0, 0.5)
mid  = arm_data.edit_bones.new("Mid");   mid.head = (0, 0, 0.5);  mid.tail = (0, 0, 1.0); mid.parent = root; mid.use_connect = True
top  = arm_data.edit_bones.new("Top");   top.head = (0, 0, 1.0);  top.tail = (0, 0, 1.5); top.parent = mid;  top.use_connect = True
bpy.ops.object.mode_set(mode='OBJECT')
```

Skin a mesh with automatic weights (mesh selected, armature active):

```python
import bpy
mesh, rig = bpy.data.objects["Pillar"], bpy.data.objects["Rig"]
for o in bpy.context.view_layer.objects: o.select_set(False)
mesh.select_set(True); rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
result = {"groups": [g.name for g in mesh.vertex_groups], "parent": mesh.parent.name}
```

Bone heat can fail on bad geometry ("Bone Heat Weighting: failed") — check that `vertex_groups` are non-empty; fix by merging doubles / recalculating normals, or fall back to `ARMATURE_ENVELOPE`.

One named action per clip, pushed to the NLA so every clip survives saving and is exported:

```python
import bpy, mathutils
rig = bpy.data.objects["Rig"]
def make_clip(name, keys):            # keys: {frame: {bone: (x, y, z) euler radians}}
    rig.animation_data_create()
    rig.animation_data.action = bpy.data.actions.new(name)
    for frame, pose in keys.items():
        for bone, rot in pose.items():
            pb = rig.pose.bones[bone]; pb.rotation_mode = 'QUATERNION'      # quaternions blend cleanly in games
            pb.rotation_quaternion = mathutils.Euler(rot).to_quaternion()
            pb.keyframe_insert("rotation_quaternion", frame=frame, group=bone)
    act = rig.animation_data.action
    act.use_fake_user = True                                          # survives saving even if unused
    track = rig.animation_data.nla_tracks.new(); track.name = name
    track.strips.new(name, int(act.frame_range[0]), act)
    rig.animation_data.action = None
    return act
make_clip("Sway-loop", {1: {"Mid": (0, 0, 0), "Top": (0, 0, 0)},
                         13: {"Mid": (0.3, 0, 0), "Top": (0.4, 0, 0)},
                         25: {"Mid": (0, 0, 0), "Top": (0, 0, 0)}})
make_clip("Bow", {1: {"Mid": (0, 0, 0)}, 10: {"Mid": (1.2, 0, 0)}, 20: {"Mid": (0, 0, 0)}})
result = {"actions": [a.name for a in bpy.data.actions], "tracks": [t.name for t in rig.animation_data.nla_tracks]}
```

Names: Godot imports clips whose name starts or ends with `loop` (or `cycle`) as looping. Baking IK/constraints into clips, root motion, loop checks: `animation.md`.

## Preview render (check your work)

Workbench, small, camera framed on everything; then Read the PNG through its host path:

```python
import bpy, mathutils, math, os
scene = bpy.context.scene
out = "/models/_previews/crate.png"; os.makedirs(os.path.dirname(out), exist_ok=True)
objs = [o for o in scene.objects if o.type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT'}]
pts = [o.matrix_world @ mathutils.Vector(c) for o in objs for c in o.bound_box]
center = sum(pts, mathutils.Vector()) / len(pts)
radius = max((p - center).length for p in pts)
cam = scene.camera
if cam is None:
    cam = bpy.data.objects.new("PreviewCam", bpy.data.cameras.new("PreviewCam"))
    scene.collection.objects.link(cam); scene.camera = cam
direction = mathutils.Vector((1.0, -1.2, 0.8)).normalized()      # 3/4 view from front-right, above
cam.location = center + direction * radius * 3.2
cam.rotation_euler = (center - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 50; cam.data.clip_end = radius * 20
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'; scene.display.shading.color_type = 'MATERIAL'
scene.render.resolution_x = scene.render.resolution_y = 512; scene.render.resolution_percentage = 100
scene.render.film_transparent = False
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
result = {"preview": out}
```

- `EGL Error (0x3009)` lines on stderr in Docker are harmless; the PNG is still written.
- Workbench shows `material.diffuse_color`, not node colours or textures — the material recipe sets both. For textures use `scene.display.shading.color_type = 'TEXTURE'`.
- Do **not** save after a preview unless the user wants the camera kept (or delete `PreviewCam` first). Because of that, a later call has no camera: create one in the same call as any render.
- Animation check: set `scene.frame_set(n)` before rendering, render 3–4 frames to `..._f<n>.png`.
- Nicer render: `scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = 32` — watch the ~120 s timeout. Add a light if the scene has none (`bpy.data.lights.new("Key", 'SUN')`).

## Clean up and export glTF / GLB

```python
import bpy, os
out = "/export/props/crate/crate.glb"; os.makedirs(os.path.dirname(out), exist_ok=True)
for o in [o for o in bpy.data.objects if o.name.startswith("PreviewCam")]:
    bpy.data.objects.remove(o)
bpy.data.orphans_purge(do_recursive=True)
bpy.ops.export_scene.gltf(
    filepath=out, export_format='GLB',
    use_selection=False,            # True + select objects to export only some
    export_apply=True,              # apply modifiers
    export_yup=True,                # Blender +Z up -> glTF +Y up
    export_animations=True, export_animation_mode='ACTIONS',
    export_cameras=False, export_lights=False,
)
result = {"exported": out, "bytes": os.path.getsize(out)}
```

Verify by importing into an empty scene (no save):

```python
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath="/export/props/crate/crate.glb")
result = {"objects": [(o.name, o.type) for o in bpy.data.objects],
          "actions": [a.name for a in bpy.data.actions]}
```

An `Icosphere` in the `glTF_not_exported` collection is the importer's bone display shape, not part of the export — ignore it.

Other formats: `bpy.ops.wm.obj_export(filepath=...)`, `bpy.ops.wm.stl_export(filepath=...)` (3D print), `bpy.ops.export_scene.fbx(filepath=...)`.

## Import

```python
import bpy
bpy.ops.import_scene.gltf(filepath="/refs/model.glb")      # .glb/.gltf
bpy.ops.wm.obj_import(filepath="/refs/model.obj")
bpy.ops.import_scene.fbx(filepath="/refs/model.fbx")
bpy.ops.wm.save_mainfile()
```
