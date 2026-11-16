"""Gives a split hanging part (a node made by split_part.py --mask: a cloak, a ponytail) its own
bone chains and re-skins it to them, so Godot's spring bones can swing it. Plain Python + numpy,
patches the glb.

  python -I add_bone_chains.py in.glb out.glb [--preset cloak|ponytail]
         [--part Cloak] [--parent mixamorig:Spine2] [--prefix cloak] [--axis 0.006,0.085]

Presets (the other options override them; the numbers were chosen on a 1.0-tall chibi Tripo model
with Mixamo bone names: check the printed joint positions on another model):
- `cloak` (default): an auto-rig skinned the cloak 85% to the arms; 5 chains x 4 bones around the
  back, under Spine2, the top band shared with the shoulders on the sides.
- `ponytail`: one chain of 4 bones down the ponytail, under the Head (the auto-rig had skinned it
  100% to the Head, so it was rigid); the first joint below the arc over the hair tie.

`--axis x,z`: the vertical line (model space) the chain angles are measured around, near the
spine; it only matters with more than one chain.

How it works:
- One chain per angle in `angles` around her (0 = middle of the back, + = her left), each with
  one bone per height in `heights` (the part's baked "how far down" colour, COLOR_0.r: 0 top
  edge, 1 lowest). Bones are named `<prefix>_<chain>_<n>` (chain a, b, c, ... from her right to
  her left) and parented to `--parent` (the first) and to each other. Each joint sits on the
  part's surface (mean of its nearby vertices; with one chain, of the whole height slice),
  rotated as the armature (identity in model space). Godot's SpringBoneSimulator3D swings them
  (`common/effects/cloak/cloak_bones.gd`).
- Each vertex blends the two nearest chains (by angle) and, in each, the two nearest bones (by
  height), so up to 4 influences. Above the first joint it blends to the parent and, on the sides,
  by `shoulder_share` to that side's shoulder (the cloak, like the hood above it).

The part's vertices are only its own (it is separate shells of the mesh), so its rows of the
shared JOINTS_0/WEIGHTS_0 are rewritten in place; the rest of the mesh is untouched.
"""
import json, struct, sys
import numpy as np

NP = {5121: "u1", 5123: "<u2", 5125: "<u4", 5126: "<f4"}
PRESETS = {
    "cloak": dict(part="Cloak", parent="mixamorig:Spine2", prefix="cloak",
                  angles=[-80.0, -40.0, 0.0, 40.0, 80.0], heights=[0.12, 0.37, 0.62, 0.87],
                  shoulder_share=0.5, axis=(0.006, 0.085)),
    # The first joint below the arc on top of the hair tie: the arc stays on the head.
    "ponytail": dict(part="Ponytail", parent="mixamorig:Head", prefix="ponytail",
                     angles=[0.0], heights=[0.2, 0.42, 0.64, 0.86], shoulder_share=0.0,
                     axis=(0.006, 0.085)),
}
TIP_HEIGHT = 1.0
SHOULDERS = {-1: "mixamorig:RightShoulder", 1: "mixamorig:LeftShoulder"}


def trs_matrix(nd):
    if "matrix" in nd:
        return np.array(nd["matrix"]).reshape(4, 4).T
    t = np.array(nd.get("translation", [0, 0, 0]), float)
    x, y, z, w = nd.get("rotation", [0, 0, 0, 1])
    s = np.array(nd.get("scale", [1, 1, 1]), float)
    R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                  [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                  [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    M = np.eye(4)
    M[:3, :3] = R * s
    M[:3, 3] = t
    return M


def quat_from_matrix(R):
    R = R / np.linalg.norm(R, axis=0)
    tr = R.trace()
    if tr > 0:
        s = np.sqrt(tr + 1.0) * 2
        q = [(R[2, 1] - R[1, 2]) / s, (R[0, 2] - R[2, 0]) / s, (R[1, 0] - R[0, 1]) / s, 0.25 * s]
    else:
        i = int(np.argmax(np.diag(R)))
        if i == 0:
            s = np.sqrt(1 + R[0, 0] - R[1, 1] - R[2, 2]) * 2
            q = [0.25 * s, (R[0, 1] + R[1, 0]) / s, (R[0, 2] + R[2, 0]) / s, (R[2, 1] - R[1, 2]) / s]
        elif i == 1:
            s = np.sqrt(1 + R[1, 1] - R[0, 0] - R[2, 2]) * 2
            q = [(R[0, 1] + R[1, 0]) / s, 0.25 * s, (R[1, 2] + R[2, 1]) / s, (R[0, 2] - R[2, 0]) / s]
        else:
            s = np.sqrt(1 + R[2, 2] - R[0, 0] - R[1, 1]) * 2
            q = [(R[0, 2] + R[2, 0]) / s, (R[1, 2] + R[2, 1]) / s, 0.25 * s, (R[1, 0] - R[0, 1]) / s]
    q = np.array(q)
    return list(map(float, q / np.linalg.norm(q)))


def main(src, dst, part, parent, prefix, angles, heights, shoulder_share, axis):
    parent_name = parent
    AXIS_X, AXIS_Z = axis
    CHAIN_DEGREES, JOINT_HEIGHTS, SHOULDER_SHARE = angles, heights, shoulder_share
    single = len(CHAIN_DEGREES) == 1
    d = bytearray(open(src, "rb").read())
    n = struct.unpack_from("<I", d, 12)[0]
    j = json.loads(d[20:20 + n])
    bin0 = 20 + n + 8
    binlen = struct.unpack_from("<I", d, 20 + n)[0]

    def view(ai, writable=False):
        a = j["accessors"][ai]
        bv = j["bufferViews"][a["bufferView"]]
        assert bv.get("byteStride") is None, "interleaved buffers are not handled"
        off = bin0 + bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        nc = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}[a["type"]]
        return np.frombuffer(d, NP[a["componentType"]], a["count"] * nc, off).reshape(-1, nc)

    parents = {c: i for i, nd in enumerate(j["nodes"]) for c in nd.get("children", [])}

    def global_matrix(i):
        M = trs_matrix(j["nodes"][i])
        while i in parents:
            i = parents[i]
            M = trs_matrix(j["nodes"][i]) @ M
        return M

    names = [nd.get("name", "") for nd in j["nodes"]]
    assert not any(nm.startswith(prefix + "_") for nm in names), f"this file already has {prefix} bones"
    mesh_i = next(i for i, m in enumerate(j["meshes"]) if m["name"] == part)
    prim = j["meshes"][mesh_i]["primitives"][0]
    attrs = prim["attributes"]
    assert "COLOR_0" in attrs, "the part needs the --mask colours of split_part.py"
    P = view(attrs["POSITION"]).astype(float)
    red = view(attrs["COLOR_0"])[:, 0].astype(float) / 255.0
    verts = np.unique(view(prim["indices"]).ravel())
    # The part's vertices must be its own: no other primitive may use them.
    for m in j["meshes"]:
        for p in m["primitives"]:
            if p is prim or p["attributes"].get("JOINTS_0") != attrs["JOINTS_0"]:
                continue
            assert not np.isin(view(p["indices"]).ravel(), verts).any(), "the part shares vertices"

    theta = np.degrees(np.arctan2(P[verts, 0] - AXIS_X, -(P[verts, 2] - AXIS_Z)))
    h = red[verts]

    # Joint positions: the mean of the part's vertices near each (angle, height); one chain: the
    # whole height slice.
    def surface_point(t, r):
        for wt, wr in ((10, 0.04), (16, 0.06), (25, 0.1)):
            s = (np.abs(h - r) < wr) & (single or (np.abs(theta - t) < wt))
            if s.sum() >= 3:
                return P[verts[s]].mean(0)
        raise SystemExit(f"no {part} vertices near angle {t} height {r}")

    skin_i = next(i for i, nd in enumerate(j["nodes"]) if nd.get("mesh") == mesh_i)
    skin = j["skins"][j["nodes"][skin_i]["skin"]]
    parent_node = names.index(parent_name)
    shoulder_nodes = {s: names.index(nm) for s, nm in SHOULDERS.items()} if SHOULDER_SHARE > 0 else {}
    print(f"{part}: {len(verts)} vertices, rest weights so far: " + ", ".join(
        f"{names[skin['joints'][jj]].replace('mixamorig:', '')} {w:.0%}" for jj, w in
        weight_share(view(attrs["JOINTS_0"]), view(attrs["WEIGHTS_0"]), verts)))
    joints = skin["joints"]
    ibm_old = view(skin["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
    new_ibms = []
    chain_joint = []  # [chain][k] -> joint index in the skin
    letters = "abcdefghij"
    for c, t in enumerate(CHAIN_DEGREES):
        prev_node, prev_global = parent_node, global_matrix(parent_node)
        idx = []
        for k, r in enumerate(JOINT_HEIGHTS):
            G = np.eye(4)
            G[:3, 3] = surface_point(t, r)
            L = np.linalg.inv(prev_global) @ G
            node = {"name": f"{prefix}_{letters[c]}_{k}", "translation": list(map(float, L[:3, 3])),
                    "rotation": quat_from_matrix(L[:3, :3])}
            j["nodes"].append(node)
            ni = len(j["nodes"]) - 1
            j["nodes"][prev_node].setdefault("children", []).append(ni)
            joints.append(ni)
            new_ibms.append(np.linalg.inv(G))
            idx.append(len(joints) - 1)
            prev_node, prev_global = ni, G
        tip = surface_point(t, TIP_HEIGHT * 0.97)
        print(f"chain {letters[c]} ({t:+.0f} deg): joints " + ", ".join(
            f"({x:.3f},{y:.3f},{z:.3f})" for x, y, z in
            [np.linalg.inv(m)[:3, 3] for m in new_ibms[-len(JOINT_HEIGHTS):]])
            + f", tip ({tip[0]:.3f},{tip[1]:.3f},{tip[2]:.3f})")
        chain_joint.append(idx)
    parent_joint = joints.index(parent_node)
    shoulder_joint = {s: joints.index(nd) for s, nd in shoulder_nodes.items()}

    # New weights for the part's vertices.
    J = view(attrs["JOINTS_0"])
    W = view(attrs["WEIGHTS_0"])
    assert j["accessors"][attrs["JOINTS_0"]]["componentType"] == 5121 and len(joints) <= 255
    newJ = np.zeros((len(verts), 4), np.int64)
    newW = np.zeros((len(verts), 4))
    T = np.array(CHAIN_DEGREES)
    H = np.array(JOINT_HEIGHTS)
    if single:
        chain_joint.append(chain_joint[0])  # the "next chain" of a lone chain is itself
    for row, (t, r) in enumerate(zip(theta, h)):
        if single:
            c, fc = 0, 0.0
        else:
            t = np.clip(t, T[0], T[-1])
            c = min(int(np.searchsorted(T, t, side="right")) - 1, len(T) - 2)
            fc = (t - T[c]) / (T[c + 1] - T[c])
        infl = {}
        def add(joint, w):
            if w > 1e-4:
                infl[joint] = infl.get(joint, 0.0) + w
        if r <= H[0]:
            # Above the first joint: from the parent (and the shoulder on the sides) to bone 0.
            f = (r / H[0]) ** 2
            side = 1 if t > 0 else -1
            sh = SHOULDER_SHARE * min(abs(t) / 90.0, 1.0)
            add(parent_joint, (1 - f) * (1 - sh))
            if sh > 0:
                add(shoulder_joint[side], (1 - f) * sh)
            add(chain_joint[c][0], f * (1 - fc))
            add(chain_joint[c + 1][0], f * fc)
        else:
            k = min(int(np.searchsorted(H, r, side="right")) - 1, len(H) - 1)
            fk = 0.0 if k == len(H) - 1 else (r - H[k]) / (H[k + 1] - H[k])
            for cc, wc in ((c, 1 - fc), (c + 1, fc)):
                add(chain_joint[cc][k], wc * (1 - fk))
                if fk > 0:
                    add(chain_joint[cc][k + 1], wc * fk)
        top = sorted(infl.items(), key=lambda kv: -kv[1])[:4]
        total = sum(w for _, w in top)
        for i, (jj, w) in enumerate(top):
            newJ[row, i] = jj
            newW[row, i] = w / total
    # The views write straight into the file's bytes (np.frombuffer over a bytearray).
    J[verts] = newJ.astype("u1")
    W[verts] = newW.astype("<f4")

    # The inverse bind matrices, old and new, in a new accessor.
    allibm = np.concatenate([ibm_old, np.array(new_ibms)]).transpose(0, 2, 1).astype("<f4")
    data = allibm.tobytes()
    j["bufferViews"].append({"buffer": 0, "byteOffset": binlen, "byteLength": len(data)})
    j["accessors"].append({"bufferView": len(j["bufferViews"]) - 1, "componentType": 5126,
                           "count": len(joints), "type": "MAT4"})
    skin["inverseBindMatrices"] = len(j["accessors"]) - 1
    old_end = bin0 + binlen
    binlen += len(data)
    j["buffers"][0]["byteLength"] = binlen
    js = json.dumps(j, separators=(",", ":")).encode()
    js += b" " * (-len(js) % 4)
    bin_new = bytes(d[bin0:old_end]) + data
    bin_new += b"\0" * (-len(bin_new) % 4)
    j["buffers"][0]["byteLength"] = len(bin_new)
    js = json.dumps(j, separators=(",", ":")).encode()
    js += b" " * (-len(js) % 4)
    out = bytearray(b"glTF" + struct.pack("<II", 2, 0))
    out += struct.pack("<I", len(js)) + b"JSON" + js
    out += struct.pack("<I", len(bin_new)) + b"BIN\0" + bin_new
    struct.pack_into("<I", out, 8, len(out))
    open(dst, "wb").write(out)
    print(f"{len(CHAIN_DEGREES)} chains x {len(JOINT_HEIGHTS)} bones added; {len(verts)} '{part}' vertices re-skinned")


def weight_share(J, W, verts):
    """[(joint, share of the vertices' total weight)], largest first."""
    out = {}
    for v in verts:
        for k in range(4):
            if W[v, k] > 0:
                out[int(J[v, k])] = out.get(int(J[v, k]), 0.0) + float(W[v, k])
    total = sum(out.values())
    return sorted(((jj, w / total) for jj, w in out.items()), key=lambda kv: -kv[1])[:5]


if __name__ == "__main__":
    a = sys.argv[1:]
    preset = "cloak"
    if "--preset" in a:
        i = a.index("--preset")
        preset = a[i + 1]
        del a[i:i + 2]
    opts = dict(PRESETS[preset])
    for key in ("--part", "--parent", "--prefix", "--axis"):
        if key in a:
            i = a.index(key)
            opts[key[2:]] = a[i + 1]
            del a[i:i + 2]
    if isinstance(opts["axis"], str):
        opts["axis"] = tuple(float(v) for v in opts["axis"].split(","))
    main(a[0], a[1], **opts)
