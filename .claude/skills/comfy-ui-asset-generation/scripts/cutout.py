"""Cut a person or character out of an image with a local ComfyUI, saving a PNG with a
transparent background.

How: YOLO person segmentation (Impact Pack) finds the figure, SAM refines the outline, the
mask is shrunk 1 px (drops a fringe of background colour) and slightly blurred (soft edge),
then joined to the image as its alpha. Everything runs locally; no model is downloaded.

usage (run with ComfyUI's embedded Python, `-I`):
  python cutout.py <input image> <output.png> [--graph-out graph.json]
                   [--shrink 1] [--blur 1.0] [--server http://127.0.0.1:8188]

Works best on a figure drawn on a plain background in a colour the figure doesn't have.
"""
import argparse, json, os, sys, time, urllib.parse, urllib.request, uuid

YOLO_MODEL = "segm/person_yolov8m-seg.pt"
SAM_MODEL = "sam_vit_h_4b8939.pth"
NEEDED_NODES = ["UltralyticsDetectorProvider", "SAMLoader", "ImpactSimpleDetectorSEGS",
                "SegsToCombinedMask", "GrowMask", "MaskToImage", "ImageBlur", "ImageToMask",
                "InvertMask", "JoinImageWithAlpha", "LoadImage", "SaveImage"]


def get(base, path):
    with urllib.request.urlopen(base + path, timeout=60) as r:
        return r.read()


def check_setup(base):
    """Exits with a clear message when a node or model the graph needs is missing."""
    info = json.loads(get(base, "/object_info"))
    missing = [n for n in NEEDED_NODES if n not in info]
    if missing:
        sys.exit(f"Missing ComfyUI nodes: {missing} (Impact Pack and Impact Subpack provide the detector nodes)")
    yolo = info["UltralyticsDetectorProvider"]["input"]["required"]["model_name"][0]
    sam = info["SAMLoader"]["input"]["required"]["model_name"][0]
    if YOLO_MODEL not in yolo:
        sys.exit(f"Missing model {YOLO_MODEL} in models/ultralytics/ (found: {yolo})")
    if SAM_MODEL not in sam:
        sys.exit(f"Missing model {SAM_MODEL} in models/sams/ (found: {sam})")


def upload(base, path):
    boundary = uuid.uuid4().hex
    name = os.path.basename(path)
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{name}\"\r\n"
            "Content-Type: application/octet-stream\r\n\r\n").encode() + open(path, "rb").read() + \
        (f"\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"overwrite\"\r\n\r\ntrue"
         f"\r\n--{boundary}--\r\n").encode()
    req = urllib.request.Request(base + "/upload/image", body,
                                 {"Content-Type": f"multipart/form-data; boundary={boundary}"})
    return json.loads(urllib.request.urlopen(req, timeout=60).read())["name"]


def graph(image_name, shrink, blur):
    return {
        "1": {"class_type": "LoadImage", "inputs": {"image": image_name}},
        "2": {"class_type": "UltralyticsDetectorProvider", "inputs": {"model_name": YOLO_MODEL}},
        "3": {"class_type": "SAMLoader", "inputs": {"model_name": SAM_MODEL, "device_mode": "AUTO"}},
        "4": {"class_type": "ImpactSimpleDetectorSEGS",
              "inputs": {"bbox_detector": ["2", 0], "image": ["1", 0], "bbox_threshold": 0.5,
                         "bbox_dilation": 0, "crop_factor": 3.0, "drop_size": 10,
                         "sub_threshold": 0.5, "sub_dilation": 0, "sub_bbox_expansion": 0,
                         "sam_mask_hint_threshold": 0.7, "post_dilation": 0,
                         "sam_model_opt": ["3", 0], "segm_detector_opt": ["2", 1]}},
        "5": {"class_type": "SegsToCombinedMask", "inputs": {"segs": ["4", 0]}},
        # Shrink the mask to drop a fringe of background colour, then soften the hard edge.
        "9": {"class_type": "GrowMask", "inputs": {"mask": ["5", 0], "expand": -shrink,
                                                    "tapered_corners": True}},
        "10": {"class_type": "MaskToImage", "inputs": {"mask": ["9", 0]}},
        "11": {"class_type": "ImageBlur", "inputs": {"image": ["10", 0], "blur_radius": 1,
                                                     "sigma": blur}},
        "12": {"class_type": "ImageToMask", "inputs": {"image": ["11", 0], "channel": "red"}},
        # JoinImageWithAlpha turns 1 - mask into the alpha, so the figure must be 0 in it.
        "6": {"class_type": "InvertMask", "inputs": {"mask": ["12", 0]}},
        "7": {"class_type": "JoinImageWithAlpha", "inputs": {"image": ["1", 0], "alpha": ["6", 0]}},
        "8": {"class_type": "SaveImage", "inputs": {"images": ["7", 0], "filename_prefix": "cutout/cutout"}},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument("--graph-out", help="also write the API graph used here")
    parser.add_argument("--shrink", type=int, default=1, help="pixels to shrink the mask (0: none)")
    parser.add_argument("--blur", type=float, default=1.0, help="edge blur sigma (0.1 = nearly hard)")
    parser.add_argument("--server", default="http://127.0.0.1:8188")
    args = parser.parse_args()

    check_setup(args.server)
    g = graph(upload(args.server, args.input), args.shrink, args.blur)
    if args.graph_out:
        json.dump(g, open(args.graph_out, "w", encoding="utf-8"), indent=2)
    req = urllib.request.Request(args.server + "/prompt", json.dumps({"prompt": g}).encode(),
                                 {"Content-Type": "application/json"})
    pid = json.loads(urllib.request.urlopen(req, timeout=60).read())["prompt_id"]
    for _ in range(600):
        h = json.loads(get(args.server, "/history/" + pid))
        if pid in h and (h[pid].get("outputs") or h[pid].get("status", {}).get("status_str") == "error"):
            break
        time.sleep(1)
    else:
        sys.exit("timed out waiting for ComfyUI")
    status = h[pid].get("status", {})
    if status.get("status_str") == "error":
        sys.exit("ComfyUI error: " + json.dumps(status.get("messages"))[:2000])
    img = next(i for o in h[pid]["outputs"].values() for i in o.get("images", []))
    q = urllib.parse.urlencode({"filename": img["filename"], "subfolder": img["subfolder"], "type": "output"})
    open(args.output, "wb").write(get(args.server, "/view?" + q))
    print("saved", args.output)


main()
