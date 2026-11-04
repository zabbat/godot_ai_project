# Blender 5.x Python API: rules and changes

Read before writing `bpy` code, and again when code fails with `AttributeError`, `KeyError` or "context is incorrect". Checked on Blender 5.1.2 in the sandbox unless marked. When in doubt, ask the MCP: `search_api_docs` / `get_python_api_docs`.

## Changed or removed (4.x → 5.x)

| Old | Now | Notes |
|---|---|---|
| `action.fcurves`, `action.groups` | **gone**. Layered actions: `action.layers[].strips[].channelbags[].fcurves`, one channelbag per **slot** | Use `bpy_extras.anim_utils.action_get_channelbag_for_slot(action, slot)` or `animdata_get_channelbag_for_assigned_slot(obj.animation_data)`. See `animation.md`. |
| `fcurves.new(...)` on an action | `anim_utils.action_ensure_channelbag_for_slot(action, slot)` then `channelbag.fcurves.ensure(data_path, index=, group_name=)` | `keyframe_insert()` creates action, slot and channelbag for you — the easy path. |
| `material.use_nodes = True` | New materials already have nodes (Principled BSDF + Material Output); the flag is deprecated | Just use `mat.node_tree`. |
| `nodes["Principled BSDF"]` | Find by type: `next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')` | Node names are translated when the UI language is not English; types and socket names are not. |
| Principled inputs `"Emission"`, `"Specular"`, `"Subsurface"`, ... | `"Emission Color"`, `"Specular IOR Level"`, `"Subsurface Weight"`, `"Coat Weight"`, `"Transmission Weight"` | Changed in 4.0. Print `[s.name for s in bsdf.inputs]` when unsure. |
| `BLENDER_EEVEE_NEXT` | `BLENDER_EEVEE` | Engines: `BLENDER_EEVEE`, `CYCLES`, `BLENDER_WORKBENCH`. EEVEE needs a GPU: not in the Docker sandbox. |
| `mesh.use_auto_smooth`, `calc_normals()` | Removed (4.1). Use `bpy.ops.object.shade_smooth_by_angle(angle=0.52)` (works headless on the selected/active object; smooths faces and marks sharp edges in the `sharp_edge` attribute), or `polygons.foreach_set("use_smooth", ...)` | Sharp edges and smooth flags export to glTF as normals. |
| Bone layers | Bone collections: `arm.collections.new("Deform")`, `coll.assign(bone)` | |
| `bl_info` add-ons | Extensions with `blender_manifest.toml` | Only matters for add-on work. |
| Boolean solver `FAST` | `FLOAT` (also `EXACT`, `MANIFOLD`) | Read valid values: `bpy.types.BooleanModifier.bl_rna.properties["solver"].enum_items.keys()`. |
| `bgl` | gone; use `gpu` | |

## Data API over operators

- Prefer `bpy.data`, object/mesh properties, `bmesh`, `mesh.attributes`, and `foreach_get`/`foreach_set` (fast, no context). Operators depend on the active object, selection, mode and editor; background mode has **no 3D View**, so view operators (`view3d.*`, `camera_to_view_selected`, most `uv.*` projections from view) fail.
- When an operator is needed: set mode to OBJECT, deselect all, select the objects, set the active one, or wrap it:
  ```python
  with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob], selected_editable_objects=[ob]):
      ret = bpy.ops.object.modifier_apply(modifier="Bevel")
  assert ret == {'FINISHED'}, ret
  ```
- Check the return value (`{'FINISHED'}` vs `{'CANCELLED'}`): a cancelled operator does not raise.
- Never call operators per vertex/face in a loop; use bmesh.

## Edit mode

- `obj.data` is stale while the object is in Edit Mode. Either work in Object Mode with `bmesh.new(); bm.from_mesh(me) ... bm.to_mesh(me); me.update()`, or in Edit Mode with `bmesh.from_edit_mesh(me)` + `bmesh.update_edit_mesh(me)`.
- End every call in Object Mode (`bpy.ops.object.mode_set(mode='OBJECT')`) — files saved in Edit Mode reopen there and confuse the next call.

## References that go stale

- Removing an object/mesh/material, **applying a modifier**, or undo frees the data: an old Python variable then points to freed memory (crash or `ReferenceError`). Store names, look up again with `bpy.data.objects[name]`.
- After changing transforms or parenting, call `bpy.context.view_layer.update()` before reading `matrix_world`.
- Evaluated geometry (with modifiers): `ob.evaluated_get(depsgraph).to_mesh()` … always `ob_eval.to_mesh_clear()`.
- Default names get suffixes (`Cube.001`) when the name exists: keep the object returned by the call and rename it immediately; never find objects by assuming a default name.

## Enums

- Valid values: `type(obj).bl_rna.properties["prop"].enum_items.keys()`.
- Dynamic enums (`render.engine`, `view_settings.view_transform`, `look`) list fewer values than they accept: set them in `try/except TypeError` — the error message lists the valid ones.

## Units, scale, paths

- 1 Blender unit = 1 m (`scene.unit_settings.scale_length = 1.0`). Model at real size.
- Apply rotation and scale (`transform_apply`) **before** bevels, solidify and other distance-based modifiers, rigging, physics, baking and export — modifiers work in object space, so a scaled object gets uneven bevels.
- `bpy.path.abspath("//textures/x.png")` resolves paths relative to the `.blend`. Backups: `bpy.ops.wm.save_as_mainfile(filepath=..., copy=True)`.

## Sandbox (Docker) specifics

- Each `_for_cli` call is a new process with a fresh namespace: re-import, look objects up by name, save at the end.
- `bpy.ops.wm.read_factory_settings(use_empty=True)` is fine in a `_for_cli` call (the process is thrown away). **Never** call it through `execute_blender_code` in a live (VM) Blender — it wipes the user's open scene.
- Never delete data you did not create unless the user asked.
- `EGL Error` lines on stderr are harmless; there is no GPU.
- A call is killed after ~120 s.
