"""
Check a Blender scene and export it as GLB for Godot 4, then read the GLB back and report.

Runs inside Blender. Send it as the code of execute_blender_code_for_cli (or execute_blender_code),
with an EXPORT dict defined first:

    EXPORT = {
        "out": "/export/props/crate/crate.glb",   # required unless check_only
        "objects": ["Crate"],          # optional: these objects + all their children
        "collection": None,            # optional: every object in this collection (and its children collections)
                                       # neither given: all mesh/armature/empty/curve objects in the scene
        "apply_modifiers": True,       # bake modifiers into the mesh (False keeps e.g. Array cheap: replicate in Godot)
        "animations": True,
        "deform_bones_only": True,     # drop control/IK bones (bake their effect into the clips first)
        "check_only": False,          # True: run the checks, export nothing
        "strict": False,               # True: do not export if a check reports an error
        "max_tris": None,              # optional triangle budget for the whole export
    }
    <contents of this file>

It never saves the .blend (it may select/unhide objects to export them). result = {ok, errors, warnings,
info, exported, glb: {...}}. Tested on Blender 5.1.2.
"""

import bpy, bmesh, json, math, os, re, struct

cfg = dict(globals().get("EXPORT") or {})
errors, warnings, info = [], [], []

DEFAULT_NAME = re.compile(r"^(Cube|Sphere|Cylinder|Plane|Cone|Torus|Icosphere|Suzanne|Circle|Grid|Mesh|Object|"
                          r"Armature|Bone|Material|Empty|Curve|BezierCurve|NurbsPath|Text|Action)(\.\d+)?$")
PROCEDURAL = {"TEX_NOISE", "TEX_VORONOI", "TEX_WAVE", "TEX_MAGIC", "TEX_GRADIENT", "TEX_BRICK", "TEX_CHECKER",
              "TEX_WHITE_NOISE", "TEX_GABOR", "VALTORGB", "MIX_SHADER", "ADD_SHADER", "SHADER_TO_RGB"}
DATA_INPUTS = {"Roughness", "Metallic", "Normal", "Alpha", "Specular IOR Level", "Coat Weight", "Transmission Weight"}
COLOR_INPUTS = {"Base Color", "Emission Color"}
GODOT_BAD = set('.:@/"%')   # not allowed in Godot node names
LOOP_NAME = re.compile(r"^(loop|cycle)|(loop|cycle)$", re.I)


def gather():
    scene = bpy.context.scene
    names, coll = cfg.get("objects"), cfg.get("collection")
    if names:
        missing = [n for n in names if n not in bpy.data.objects]
        if missing:
            errors.append("objects not found: {}".format(missing))
        roots = [bpy.data.objects[n] for n in names if n in bpy.data.objects]
        objs = set()
        for r in roots:
            objs.add(r)
            objs.update(r.children_recursive)
        return sorted(objs, key=lambda o: o.name)
    if coll:
        if coll not in bpy.data.collections:
            errors.append("collection not found: {}".format(coll))
            return []
        return sorted(bpy.data.collections[coll].all_objects, key=lambda o: o.name)
    keep = {"MESH", "ARMATURE", "EMPTY", "CURVE"}
    return sorted((o for o in scene.objects if o.type in keep and not o.name.startswith("PreviewCam")),
                  key=lambda o: o.name)


def check_names(objs):
    seen = {}
    datablocks = list(objs) + [s.material for o in objs for s in o.material_slots if s.material]
    for idb in datablocks:
        n = idb.name
        if DEFAULT_NAME.match(n):
            warnings.append("default name '{}': give it a real name (Godot node/material names come from it)".format(n))
        if not n.isascii() or " " in n:
            warnings.append("'{}': use ASCII without spaces (renamed on export/import)".format(n))
        elif any(c in n for c in GODOT_BAD) and isinstance(idb, bpy.types.Object):
            warnings.append("'{}': Godot node names cannot contain {} - Godot renames it on import".format(
                n, " ".join(sorted(c for c in GODOT_BAD if c in n))))
    for o in objs:
        key = re.sub(r"[^A-Za-z0-9_-]", "", o.name).lower()
        if key in seen and seen[key] != o.name:
            warnings.append("'{}' and '{}' look the same after import name clean-up".format(seen[key], o.name))
        seen[key] = o.name


def check_transforms(objs):
    for o in objs:
        if o.type not in {"MESH", "ARMATURE", "CURVE"}:
            continue
        s = o.scale
        if any(v < 0 for v in s):
            errors.append("'{}': negative scale {} flips normals - apply scale".format(o.name, tuple(round(v, 3) for v in s)))
        elif any(abs(v - 1) > 1e-4 for v in s):
            warnings.append("'{}': unapplied scale {} - apply it (Ctrl+A) so Godot sees real size".format(
                o.name, tuple(round(v, 3) for v in s)))


def mesh_stats(o, depsgraph):
    src = o.evaluated_get(depsgraph) if cfg.get("apply_modifiers", True) else o
    me = src.to_mesh()
    try:
        me.calc_loop_triangles()
        tris = len(me.loop_triangles)
        ngons = sum(1 for p in me.polygons if len(p.vertices) > 4)
        bm = bmesh.new()
        bm.from_mesh(me)
        loose_v = sum(1 for v in bm.verts if not v.link_edges)
        loose_e = sum(1 for e in bm.edges if not e.link_faces)
        nonman = sum(1 for e in bm.edges if e.link_faces and len(e.link_faces) > 2)
        holes = sum(1 for e in bm.edges if e.is_boundary)
        bm.free()
        zmin = min(((o.matrix_world @ v.co).z for v in me.vertices), default=0.0)
        return dict(tris=tris, ngons=ngons, loose_verts=loose_v, loose_edges=loose_e, nonmanifold=nonman,
                    boundary_edges=holes, zmin=zmin, has_uv=bool(me.uv_layers))
    finally:
        src.to_mesh_clear()


def check_meshes(objs):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    total, per = 0, {}
    for o in objs:
        if o.type != "MESH":
            continue
        st = mesh_stats(o, depsgraph)
        total += st["tris"]
        per[o.name] = st["tris"]
        if st["loose_verts"] or st["loose_edges"]:
            warnings.append("'{}': {} loose verts / {} loose edges (delete loose)".format(
                o.name, st["loose_verts"], st["loose_edges"]))
        if st["nonmanifold"]:
            warnings.append("'{}': {} edges with 3+ faces (non-manifold)".format(o.name, st["nonmanifold"]))
        if st["ngons"]:
            info.append("'{}': {} n-gons (triangulated on export; check shading)".format(o.name, st["ngons"]))
        if not st["has_uv"]:
            warnings.append("'{}': no UV map (textures and Godot lightmaps need one)".format(o.name))
        if not o.material_slots or any(s.material is None for s in o.material_slots):
            warnings.append("'{}': empty or missing material slot".format(o.name))
        if o.parent is None and abs(st["zmin"]) > 0.01:
            info.append("'{}': lowest point at z={:.3f} (props usually sit on z=0)".format(o.name, st["zmin"]))
        skinned = any(m.type == "ARMATURE" for m in o.modifiers)
        if skinned:
            check_weights(o)
    mx = cfg.get("max_tris")
    if mx and total > mx:
        errors.append("{} triangles, over the budget of {}".format(total, mx))
    return total, per


def check_weights(o):
    rig = next((m.object for m in o.modifiers if m.type == "ARMATURE" and m.object), None)
    if rig is None:
        warnings.append("'{}': Armature modifier without an armature".format(o.name))
        return
    deform = {b.name for b in rig.data.bones if b.use_deform}
    gi = {g.index: g.name for g in o.vertex_groups if g.name in deform}
    unweighted = over4 = 0
    for v in o.data.vertices:
        ws = [g.weight for g in v.groups if g.group in gi and g.weight > 0]
        if not ws:
            unweighted += 1
        elif len(ws) > 4:
            over4 += 1
    if unweighted:
        warnings.append("'{}': {} vertices with no bone weight (they will not move)".format(o.name, unweighted))
    if over4:
        info.append("'{}': {} vertices with >4 bone influences (exporter keeps the 4 strongest)".format(o.name, over4))


def downstream_inputs(node, depth=3):
    out, frontier = set(), [node]
    for _ in range(depth):
        nxt = []
        for n in frontier:
            for sock in n.outputs:
                for link in sock.links:
                    if link.to_node.type == "BSDF_PRINCIPLED":
                        out.add(link.to_socket.name)
                    elif link.to_node.type == "NORMAL_MAP":
                        out.add("Normal")
                    else:
                        nxt.append(link.to_node)
        frontier = nxt
    return out


def check_materials(objs):
    mats = {s.material for o in objs for s in o.material_slots if s.material}
    for m in sorted(mats, key=lambda m: m.name):
        if not m.node_tree:
            continue
        nodes = m.node_tree.nodes
        if not any(n.type == "BSDF_PRINCIPLED" for n in nodes):
            warnings.append("material '{}': no Principled BSDF - glTF/Godot only understand Principled".format(m.name))
        proc = sorted({n.type for n in nodes if n.type in PROCEDURAL})
        if proc:
            warnings.append("material '{}': procedural nodes {} are lost in glTF - bake to textures or use flat values"
                            .format(m.name, proc))
        for n in nodes:
            if n.type != "TEX_IMAGE" or not n.image:
                continue
            img = n.image
            if img.source == "FILE" and not img.packed_file and not os.path.exists(bpy.path.abspath(img.filepath)):
                errors.append("material '{}': image file missing: {}".format(m.name, img.filepath))
            used = downstream_inputs(n)
            cs = img.colorspace_settings.name
            if used & DATA_INPUTS and cs != "Non-Color":
                warnings.append("material '{}': '{}' drives {} but is '{}' - set Non-Color".format(
                    m.name, img.name, sorted(used & DATA_INPUTS), cs))
            if used & COLOR_INPUTS and cs == "Non-Color":
                warnings.append("material '{}': '{}' drives a colour but is Non-Color - set sRGB".format(m.name, img.name))


def action_fcurves(act):
    for layer in act.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                yield from cb.fcurves


def check_animation(objs):
    clips = []
    for o in objs:
        ad = o.animation_data
        if not ad:
            continue
        acts = []
        if ad.action:
            acts.append(ad.action)
        for t in ad.nla_tracks:
            for s in t.strips:
                if s.action and s.action not in acts:
                    acts.append(s.action)
        for a in acts:
            clips.append(a.name)
            if any(m.type == "CYCLES" for fc in action_fcurves(a) for m in fc.modifiers):
                info.append("action '{}': Cycles F-curve modifier is preview-only; the loop must be in the keys".format(a.name))
            if LOOP_NAME.search(a.name):
                f0, f1 = a.frame_range
                pops = []
                for fc in action_fcurves(a):
                    d = fc.evaluate(f1) - fc.evaluate(f0)
                    if fc.data_path.endswith("rotation_euler"):
                        d = math.remainder(d, math.tau)   # a full turn is seamless
                    d = abs(d)
                    if d > 1e-3:
                        pops.append("{}[{}] {:.4f}".format(fc.data_path, fc.array_index, d))
                if pops:
                    warnings.append("loop '{}': last frame differs from first ({}) - it will pop".format(
                        a.name, ", ".join(pops[:5]) + (" ..." if len(pops) > 5 else "")))
    if o_eulers := [o.name for o in objs if o.type == "ARMATURE"
                    and any(pb.rotation_mode not in ("QUATERNION",) for pb in o.pose.bones)]:
        info.append("armatures with Euler bone rotation {} (fine for simple clips; quaternions blend better)".format(o_eulers))
    for a in bpy.data.actions:
        if a.users == 0:
            warnings.append("action '{}' has no users - it will be lost on save and not exported".format(a.name))
    return clips


def read_glb(path):
    with open(path, "rb") as f:
        data = f.read()
    magic, _, _ = struct.unpack_from("<4sII", data, 0)
    if magic != b"glTF":
        raise ValueError("not a GLB file")
    clen, _ = struct.unpack_from("<II", data, 12)
    g = json.loads(data[20:20 + clen])
    acc = g.get("accessors", [])
    tris = 0
    for m in g.get("meshes", []):
        for p in m.get("primitives", []):
            if p.get("mode", 4) == 4:
                tris += (acc[p["indices"]]["count"] if "indices" in p else acc[p["attributes"]["POSITION"]]["count"]) // 3
    return {
        "bytes": len(data),
        "nodes": [n.get("name", "") for n in g.get("nodes", [])],
        "meshes": len(g.get("meshes", [])),
        "materials": [m.get("name", "") for m in g.get("materials", [])],
        "images": len(g.get("images", [])),
        "skins": len(g.get("skins", [])),
        "animations": [{"name": a.get("name", ""), "channels": len(a.get("channels", []))} for a in g.get("animations", [])],
        "triangles": tris,
        "extensions": g.get("extensionsUsed", []),
    }


objs = gather()
if not objs and not errors:
    errors.append("nothing to export")
check_names(objs)
check_transforms(objs)
total_tris, tris_per_object = check_meshes(objs)
check_materials(objs)
clips = check_animation(objs) if cfg.get("animations", True) else []

result = {"ok": not errors, "objects": [o.name for o in objs], "triangles": total_tris,
          "tris_per_object": tris_per_object, "clips": clips,
          "errors": errors, "warnings": warnings, "info": info, "exported": None}

if not cfg.get("check_only") and not (errors and cfg.get("strict")):
    out = cfg.get("out")
    if not out:
        errors.append("EXPORT['out'] is required")
    else:
        os.makedirs(os.path.dirname(out), exist_ok=True)
        if bpy.context.object and bpy.context.object.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        vl = bpy.context.view_layer
        for o in vl.objects:
            o.select_set(False)
        for o in objs:
            if o.name in vl.objects:
                o.hide_set(False)
                o.hide_viewport = False
                o.select_set(True)
            else:
                warnings.append("'{}' is not in the view layer (excluded collection?) - not exported".format(o.name))
        ret = bpy.ops.export_scene.gltf(
            filepath=out, export_format="GLB", use_selection=True,
            export_apply=bool(cfg.get("apply_modifiers", True)), export_yup=True,
            export_extras=True,                      # custom properties -> Godot node metadata
            export_animations=bool(cfg.get("animations", True)), export_animation_mode="ACTIONS",
            export_force_sampling=True, export_nla_strips=True,
            export_skins=True, export_influence_nb=4, export_def_bones=bool(cfg.get("deform_bones_only", True)),
            export_morph=True, export_cameras=False, export_lights=False,
        )
        if "FINISHED" not in ret:
            errors.append("export failed: {}".format(ret))
        else:
            glb = read_glb(out)
            result["exported"] = out
            result["glb"] = glb
            renamed = sorted(set(o.name for o in objs) - set(glb["nodes"]))
            if renamed:
                info.append("not found by name in the GLB (renamed or merged): {}".format(renamed))
            missing = sorted(set(clips) - {a["name"] for a in glb["animations"]})
            if missing:
                warnings.append("clips not in the GLB: {}".format(missing))
result["ok"] = not errors
