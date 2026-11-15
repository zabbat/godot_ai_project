"""Small helpers for ComfyUI graphs that comfy-cli does not cover.

comfy-cli runs, uploads and downloads; this script reads the current setup from the
server's history and edits API-format graphs (comfy-cli's own `comfy workflow` editors
only work on UI-format files). Standard library only.

usage (run with `uv run --no-project --python 3.12 python -I comfy_graph.py ...`):
  comfy_graph.py latest <dir>                  write <dir>/api.json (+ ui.json) of the latest
                                               history entry; print a node summary
  comfy_graph.py nodes  <api.json>             print id, class_type, title and plain inputs
  comfy_graph.py set    <api.json> ID.INPUT=VALUE ...
                                               set inputs in place (VALUE parsed as JSON,
                                               else used as a string)
  comfy_graph.py seed   <api.json> [--node ID ...]
                                               randomize every int `seed` / `noise_seed`
                                               (or only on the given nodes); prints them
  comfy_graph.py preview <api.json> SRC_ID[:SLOT] [--id 900]
                                               add a PreviewAny node fed by SRC_ID, so a
                                               text value comes back in the run's outputs
  comfy_graph.py lora   <api.json> <lora file name> [--strength 0.8] [--after ID] [--id ID]
                                               insert a LoraLoaderModelOnly after the model
                                               loader (or after the last LoRA already chained
                                               there, or after node --after); everything that
                                               used that model now uses the LoRA's output
  comfy_graph.py loras  <api.json>             list the LoRA nodes: id, file, strength

The server is $COMFY_LOCAL_URL (http://host:port) or http://127.0.0.1:8188; --server overrides.
"""
import argparse, json, os, random, sys, urllib.request


def server_url(arg):
    url = arg or os.environ.get("COMFY_LOCAL_URL") or "http://127.0.0.1:8188"
    if not url.startswith("http"):
        url = "http://" + url
    return url.rstrip("/")


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def summary(api):
    rows = []
    for nid, node in api.items():
        plain = {k: v for k, v in node.get("inputs", {}).items() if not isinstance(v, list)}
        title = node.get("_meta", {}).get("title")
        rows.append({"id": nid, "class_type": node.get("class_type"), "title": title, "inputs": plain})
    return rows


def cmd_latest(a):
    url = server_url(a.server) + "/history?max_items=1"
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            hist = json.loads(r.read())
    except OSError as e:
        sys.exit(f"ComfyUI not reachable at {url}: {e}")
    if not hist:
        sys.exit("History is empty: queue the workflow once in ComfyUI first.")
    pid, entry = next(iter(hist.items()))
    # entry["prompt"] = [number, prompt_id, api_graph, extra_data, outputs_to_execute]
    api = entry["prompt"][2]
    extra = entry["prompt"][3] if len(entry["prompt"]) > 3 else {}
    ui = (extra or {}).get("extra_pnginfo", {}).get("workflow")
    os.makedirs(a.dir, exist_ok=True)
    save(os.path.join(a.dir, "api.json"), api)
    if ui:
        save(os.path.join(a.dir, "ui.json"), ui)
    print(json.dumps({"prompt_id": pid, "status": entry.get("status", {}).get("status_str"),
                      "api": os.path.join(a.dir, "api.json"),
                      "ui": os.path.join(a.dir, "ui.json") if ui else None,
                      "outputs": entry.get("outputs", {}),
                      "nodes": summary(api)}, indent=1, ensure_ascii=False))


def cmd_nodes(a):
    print(json.dumps(summary(load(a.api)), indent=1, ensure_ascii=False))


def cmd_set(a):
    api = load(a.api)
    for item in a.assign:
        addr, _, raw = item.partition("=")
        nid, _, key = addr.partition(".")
        if not _ or nid not in api:
            sys.exit(f"bad address or unknown node: {addr}")
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            value = raw
        api[nid].setdefault("inputs", {})[key] = value
    save(a.api, api)


def cmd_seed(a):
    api = load(a.api)
    done = {}
    for nid, node in api.items():
        if a.node and nid not in a.node:
            continue
        for key in ("seed", "noise_seed"):
            if isinstance(node.get("inputs", {}).get(key), int):
                node["inputs"][key] = random.randint(1, 2**50)
                done[f"{nid}.{key}"] = node["inputs"][key]
    save(a.api, api)
    print(json.dumps(done))


def cmd_preview(a):
    api = load(a.api)
    src, _, slot = a.source.partition(":")
    if src not in api:
        sys.exit(f"unknown node: {src}")
    if a.id in api:
        sys.exit(f"node id {a.id} already used; pass --id")
    api[a.id] = {"class_type": "PreviewAny", "inputs": {"source": [src, int(slot or 0)]}}
    save(a.api, api)


MODEL_LOADERS = ("UNETLoader", "CheckpointLoaderSimple", "CheckpointLoader", "UnetLoaderGGUF",
                 "DiffusionModelLoader", "ImageOnlyCheckpointLoader")


def consumers(api, src):
    """(node id, input name) pairs that read output 0 of node src."""
    return [(nid, k) for nid, n in api.items() for k, v in n.get("inputs", {}).items()
            if v == [src, 0]]


def is_lora(node):
    return node.get("class_type", "").startswith("LoraLoader")


def cmd_lora(a):
    api = load(a.api)
    if a.after:
        if a.after not in api:
            sys.exit(f"unknown node: {a.after}")
        src = a.after
    else:
        loaders = [nid for nid, n in api.items() if n.get("class_type") in MODEL_LOADERS]
        if len(loaders) != 1:
            sys.exit(f"found {len(loaders)} model loaders {loaders}; pass --after <node id>")
        src = loaders[0]
        # Chain after LoRAs that already sit right behind the loader.
        while True:
            nxt = [nid for nid, _ in consumers(api, src) if is_lora(api[nid])]
            if len(nxt) != 1:
                break
            src = nxt[0]
    new_id = a.id or str(max([int(k) for k in api if k.isdigit()] + [0]) + 1000)
    if new_id in api:
        sys.exit(f"node id {new_id} already used; pass --id")
    users = consumers(api, src)
    if not users:
        sys.exit(f"nothing reads the model from node {src}")
    for nid, key in users:
        api[nid]["inputs"][key] = [new_id, 0]
    api[new_id] = {"class_type": "LoraLoaderModelOnly",
                   "inputs": {"lora_name": a.name, "strength_model": a.strength,
                              "model": [src, 0]},
                   "_meta": {"title": "Load LoRA"}}
    save(a.api, api)
    print(json.dumps({"lora_node": new_id, "after": src,
                      "now_feeds": [f"{n}.{k}" for n, k in users]}))


def cmd_loras(a):
    api = load(a.api)
    print(json.dumps([{"id": nid, "lora_name": n["inputs"].get("lora_name"),
                       "strength_model": n["inputs"].get("strength_model"),
                       "strength_clip": n["inputs"].get("strength_clip")}
                      for nid, n in api.items() if is_lora(n)], indent=1))


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--server")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("latest"); s.add_argument("dir"); s.set_defaults(f=cmd_latest)
    s = sub.add_parser("nodes"); s.add_argument("api"); s.set_defaults(f=cmd_nodes)
    s = sub.add_parser("set"); s.add_argument("api"); s.add_argument("assign", nargs="+"); s.set_defaults(f=cmd_set)
    s = sub.add_parser("seed"); s.add_argument("api"); s.add_argument("--node", nargs="*"); s.set_defaults(f=cmd_seed)
    s = sub.add_parser("preview"); s.add_argument("api"); s.add_argument("source")
    s.add_argument("--id", default="900"); s.set_defaults(f=cmd_preview)
    s = sub.add_parser("lora"); s.add_argument("api"); s.add_argument("name")
    s.add_argument("--strength", type=float, default=0.8); s.add_argument("--after")
    s.add_argument("--id"); s.set_defaults(f=cmd_lora)
    s = sub.add_parser("loras"); s.add_argument("api"); s.set_defaults(f=cmd_loras)
    a = p.parse_args()
    a.f(a)


main()
