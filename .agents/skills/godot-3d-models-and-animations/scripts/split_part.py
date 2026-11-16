"""Splits some connected pieces of a single-mesh glb into their own node, so Godot can hide or
restyle them (a ponytail, a cloak's collar...). Plain Python + numpy, patches the glb in place:
the chosen pieces' triangles move into a new mesh node (same skin, same vertices, same material);
the original mesh keeps the rest.

  python -I split_part.py in.glb out.glb NodeName "x0,x1,y0,y1,z0,z1" ["x0,...", ...] [--mask]

Each box selects the connected pieces (shells of the mesh) whose bounding box lies inside it;
"id:14736,14479" selects pieces by the numbers `--list` prints.
`python -I split_part.py in.glb --list` prints every piece's bounds instead.

`--mask` also bakes the new node's vertex colours (COLOR_0, which a shader reads as `COLOR`) so a
shader does not depend on the pose: red = how far down the part a vertex is (0 at its top edge,
1 at its lowest edge), green = which side it is on ((x / widest x + 1) / 2). Seen by shaders that
move a hanging cloth (`common/effects/cloak/cloak.gdshader`); both halves of a cloak get the same
values, so a shader that moves them as a function of these stays closed along the seam.
"""
import json, struct, sys
import numpy as np

NP = {5121: "u1", 5123: "<u2", 5125: "<u4", 5126: "<f4"}


def pieces(P, T):
    parent = np.arange(len(P))
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for a, b, c in T:
        ra = find(a)
        parent[find(b)] = ra
        parent[find(c)] = ra
    root = np.array([find(i) for i in range(len(P))])
    return root


def main(src, dst, name, boxes, mask=False):
    d = bytearray(open(src, "rb").read())
    n = struct.unpack_from("<I", d, 12)[0]
    j = json.loads(d[20:20 + n])
    bin0 = 20 + n + 8
    binlen = struct.unpack_from("<I", d, 20 + n)[0]
    prim = j["meshes"][0]["primitives"][0]

    def read(ai):
        a = j["accessors"][ai]
        bv = j["bufferViews"][a["bufferView"]]
        off = bin0 + bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        nc = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[a["type"]]
        return np.frombuffer(d, NP[a["componentType"]], a["count"] * nc, off).reshape(-1, nc)

    P = read(prim["attributes"]["POSITION"]).astype(float)
    T = read(prim["indices"]).reshape(-1, 3).astype(np.int64)
    root = pieces(P, T)
    tri_root = root[T[:, 0]]
    info = {}
    for r in np.unique(tri_root):
        v = np.where(root == r)[0]
        info[r] = (P[v].min(0), P[v].max(0), int((tri_root == r).sum()))
    if name == "--list":
        for r, (lo, hi, t) in sorted(info.items(), key=lambda kv: -kv[1][2]):
            print(f"piece {r:6d} tris {t:5d} x {lo[0]:.3f}..{hi[0]:.3f} y {lo[1]:.3f}..{hi[1]:.3f} z {lo[2]:.3f}..{hi[2]:.3f}")
        return
    chosen = []
    ids = {int(v) for bx in boxes if isinstance(bx, str) for v in bx[3:].split(",")}
    boxes = [bx for bx in boxes if not isinstance(bx, str)]
    for r, (lo, hi, t) in info.items():
        if r in ids:
            chosen.append(r)
            continue
        for bx in boxes:
            x0, x1, y0, y1, z0, z1 = bx
            if lo[0] >= x0 and hi[0] <= x1 and lo[1] >= y0 and hi[1] <= y1 and lo[2] >= z0 and hi[2] <= z1:
                chosen.append(r)
                break
    take = np.isin(tri_root, chosen)
    print(f"{len(chosen)} pieces, {int(take.sum())} of {len(T)} triangles go to '{name}'")

    def add_indices(tris):
        nonlocal binlen
        data = tris.astype("<u4").tobytes()
        pad = -len(data) % 4
        off = binlen
        d.extend(b"\0" * 0)
        newbin.extend(data + b"\0" * pad)
        bvi = len(j["bufferViews"])
        j["bufferViews"].append({"buffer": 0, "byteOffset": off, "byteLength": len(data), "target": 34963})
        ai = len(j["accessors"])
        j["accessors"].append({"bufferView": bvi, "componentType": 5125, "count": int(tris.size), "type": "SCALAR"})
        binlen += len(data) + pad
        return ai

    newbin = bytearray()
    rest_ai = add_indices(T[~take].ravel())
    part_ai = add_indices(T[take].ravel())
    color_ai = None
    if mask:
        used = np.unique(T[take])
        ys, xs = P[used, 1], P[used, 0]
        colors = np.zeros((len(P), 4), dtype="u1")
        colors[used, 0] = np.round((ys.max() - ys) / (ys.max() - ys.min()) * 255)
        colors[used, 1] = np.round((xs / np.abs(xs).max() + 1.0) / 2.0 * 255)
        colors[used, 3] = 255
        data = colors.tobytes()
        off = binlen
        newbin.extend(data)
        j["bufferViews"].append({"buffer": 0, "byteOffset": off, "byteLength": len(data), "target": 34962})
        j["accessors"].append({"bufferView": len(j["bufferViews"]) - 1, "componentType": 5121,
                               "normalized": True, "count": int(len(P)), "type": "VEC4"})
        color_ai = len(j["accessors"]) - 1
        binlen += len(data)
    prim["indices"] = rest_ai
    part_prim = dict(prim)
    part_prim["indices"] = part_ai
    if color_ai is not None:
        part_prim["attributes"] = dict(prim["attributes"], COLOR_0=color_ai)
    j["meshes"].append({"name": name, "primitives": [part_prim]})
    mesh_node = next(i for i, x in enumerate(j["nodes"]) if x.get("mesh") == 0)
    node = {"name": name, "mesh": len(j["meshes"]) - 1}
    if "skin" in j["nodes"][mesh_node]:
        node["skin"] = j["nodes"][mesh_node]["skin"]
    j["nodes"].append(node)
    new_i = len(j["nodes"]) - 1
    placed = False
    for sc in j["scenes"]:
        if mesh_node in sc["nodes"]:
            sc["nodes"].append(new_i)
            placed = True
    for x in j["nodes"]:
        if mesh_node in x.get("children", []):
            x["children"].append(new_i)
            placed = True
    assert placed
    old_bin_end = bin0 + struct.unpack_from("<I", d, 20 + n)[0]
    j["buffers"][0]["byteLength"] = binlen
    js = json.dumps(j, separators=(",", ":")).encode()
    js += b" " * (-len(js) % 4)
    bin_old = bytes(d[bin0:old_bin_end])
    bin_new = bin_old + bytes(newbin)
    out = bytearray(b"glTF" + struct.pack("<II", 2, 0))
    out += struct.pack("<I", len(js)) + b"JSON" + js
    out += struct.pack("<I", len(bin_new)) + b"BIN\0" + bin_new
    struct.pack_into("<I", out, 8, len(out))
    open(dst, "wb").write(out)


if __name__ == "__main__":
    args = sys.argv[1:]
    mask = "--mask" in args
    args = [a for a in args if a != "--mask"]
    if len(args) == 2 and args[1] == "--list":  # python split_part.py in.glb --list
        main(args[0], None, "--list", [])
        sys.exit()
    main(args[0], args[1], args[2],
         [b if b.startswith("id:") else tuple(float(v) for v in b.split(",")) for b in args[3:]], mask)
