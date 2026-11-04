# Exporting from Blender to Godot 4

Blender has a built-in glTF 2.0 exporter (`bpy.ops.export_scene.gltf`); GLB is its single-file form and Godot's preferred 3D format. No converter is needed. Use the bundled **`assets/scripts/godot_export.py`**: it checks the scene, exports with Godot settings, then reads the GLB back and reports what is in it.

## Running godot_export.py

Read the script and send it as the `code` of `execute_blender_code_for_cli`, with an `EXPORT` dict first:

```python
EXPORT = {"out": "/export/props/crate/crate.glb", "objects": ["Crate"]}
# ...then the full contents of assets/scripts/godot_export.py
```

| Key | Default | Meaning |
|---|---|---|
| `out` | — | GLB path in a shared folder (required unless `check_only`) |
| `objects` | all | export these objects and all their children (e.g. `["Rig"]` = rig + skinned meshes) |
| `collection` | — | export every object of this collection instead |
| `apply_modifiers` | `True` | bake modifiers into the mesh. `False` for heavy Array/instancing setups you rebuild in Godot |
| `animations` | `True` | export actions (one glTF animation per action) |
| `deform_bones_only` | `True` | drop control/IK bones — bake their effect first (`animation.md`) |
| `check_only` | `False` | only run the checks |
| `strict` | `False` | do not export when a check reports an error |
| `max_tris` | — | triangle budget; over it is an error |

It never saves the `.blend`. The `result` has `errors` (fix before handing over), `warnings` (fix or tell the user why not), `info`, and `glb` (bytes, nodes, meshes, materials, images, skins, animations with channel counts, triangles). Always show the user the errors/warnings and the GLB summary.

What it checks: default/duplicate/unsafe names, negative or unapplied scale, triangle count, loose geometry, non-manifold edges, n-gons, missing UVs, empty material slots, props not on z=0, unweighted vertices and >4 bone influences, non-Principled and procedural materials, missing image files, wrong colour space on data/colour textures, loop clips that pop, Cycles-modifier-only loops, Euler bone rotation, actions with no users, and after export: clips or objects missing from the GLB.

## Before exporting (checklist)

1. **Real size, scale applied.** 1 unit = 1 m, `transform_apply(scale=True)` (and rotation for props). Godot scale 1 must look right next to a 1.8 m capsule.
2. **Origin.** Props: bottom centre at the world origin (`bpy_recipes.md` → origin at bottom). Characters: origin between the feet, facing **-Y** in Blender (front view) — the exporter turns that into Godot's forward.
3. **Names.** Every object, mesh, material and action named; ASCII, no spaces, no `. : @ / " %` (Godot node names cannot contain them and get renamed). The Godot node, material and clip names come from these.
4. **Materials.** Principled BSDF only, fed by image textures or flat values. Procedural textures, Color Ramps, Mix/Add Shader are **lost** — bake them to images. Data maps (normal, roughness, metallic, AO) **Non-Color**; base colour/emission **sRGB**. Normal maps are OpenGL style (Blender's default, and what glTF and Godot expect). Packed ORM: occlusion R, roughness G, metallic B.
5. **Geometry.** No loose verts/edges, normals facing out (`normals_make_consistent`), UV map present, sharp edges marked or smooth by angle. glTF triangulates everything.
6. **Rig and clips.** Deform bones only, rest pose = bind pose, ≤4 influences per vertex, one named action per clip with a fake user, loops seamless, constraints/IK baked (`animation.md`).
7. **Only the asset.** Export the asset's objects, not helpers, cameras, lights or reference images.

## Godot import hints in object names

Godot 4 reads suffixes on node/object names (case-insensitive; `-name`, `_name` or `$name` all work) and on clip names:

| Suffix | Effect in Godot |
|---|---|
| `-col` | keep the mesh, add a static trimesh collision (exact, slow — level geometry) |
| `-convcol` | keep the mesh, add a convex collision (simple or moving objects) |
| `-colonly` | replace the mesh with a static trimesh collision (separate low-poly collision mesh) |
| `-convcolonly` | replace the mesh with a convex collision |
| `-rigid` | import as a RigidBody3D |
| `-occ` / `-occonly` | add an occluder from the mesh / replace the mesh with one |
| `-navmesh` | replace the mesh with a navigation mesh |
| `-vehicle`, `-wheel` | VehicleBody3D / VehicleWheel3D |
| `-noimp` | skip on import (handy for reference objects you keep in the file) |
| `-alpha` (material) | alpha transparency |
| `-vcol` (material) | use vertex colours as albedo |
| `loop` / `cycle` at the start or end of a **clip** name | import the animation looping |

Simple collision: model a box/low-poly hull named `Crate-convcolonly` or `Crate-colonly` next to the visual mesh `Crate`. Primitive-shaped collision is fastest; many convex pieces beat one trimesh for moving objects.

## Exporter settings (what the script uses)

```python
bpy.ops.export_scene.gltf(
    filepath=out, export_format='GLB', use_selection=True,
    export_apply=True,            # modifiers baked in (default is False)
    export_yup=True,              # Blender +Z up -> glTF/Godot +Y up
    export_extras=True,           # custom properties -> Godot node metadata (default False)
    export_animations=True, export_animation_mode='ACTIONS',
    export_force_sampling=True, export_nla_strips=True,
    export_skins=True, export_influence_nb=4, export_def_bones=True,
    export_morph=True,            # shape keys -> blend shapes
    export_cameras=False, export_lights=False,
)
```

- Custom properties (`obj["hp"] = 10`) arrive in Godot as node metadata with `export_extras=True`.
- Draco/meshopt compression is for the web; leave it off for Godot (Godot compresses on import).
- LODs: Godot generates them on import (`meshes/generate_lods`); do not model LOD levels unless the game needs hand-made ones.
- Lightmaps: Godot can unwrap UV2 on import (light baking "Static Lightmaps") or use a second UV map you make in Blender.

## Budgets (rough, per asset)

| Target | Hero character | Prop | Materials | Bones | Max texture |
|---|---|---|---|---|---|
| Mobile | 5–15k tris | 0.3–3k | 1–2 | ≤ 75 | 1024 |
| Desktop | 30–100k | 2–20k | 2–4 | 100–200 | 2048–4096 |

Each material on a mesh is roughly one draw call; share materials (atlas/trim sheet) across props seen together. Ask for the target platform if the user says "low poly" without a number; in a Godot AI repo use `docs/style/3d_style.md`.

## After exporting

- Read the GLB summary: triangle count, materials, clips and their channel counts as expected; no stray objects.
- Optional: import it into an empty scene (`bpy_recipes.md` → verify) and render a preview.
- In a Godot AI repo the GLB goes to `assets/3d/...` with a `.md` naming the source `.blend`; the asset map copies it into Godot, and the `glb-3d-model-and-animations` skill covers import settings and use.
