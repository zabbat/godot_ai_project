"""Change only a patch of a character's face (an expression) with Flux Fill inpainting.

Crops a window around the face, repaints the masked boxes in it with a prompt, and pastes the
result back through the feathered mask, so everything outside the masks stays pixel-identical
to the source (the outline does not move and the cut-out's alpha can be reused).

Run with ComfyUI's Python:
  python.exe -I face_inpaint.py <src.png> <out.png> --crop x0 y0 x1 y1 \
      --box x0 y0 x1 y1 [--box ...] --prompt "..." [--seed N] [--feather 6] [--steps 28]
Coordinates are in the source image's pixels. ComfyUI must be running (127.0.0.1:8188).
"""
import argparse, io, json, random, time, urllib.request, uuid
from PIL import Image, ImageDraw, ImageFilter

URL = "http://127.0.0.1:8188"


def post(path, data, headers):
    req = urllib.request.Request(URL + path, data=data, headers=headers)
    return json.load(urllib.request.urlopen(req))


def upload(img, name):
    buf = io.BytesIO()
    img.save(buf, "PNG")
    b = uuid.uuid4().hex
    body = (f'--{b}\r\nContent-Disposition: form-data; name="image"; filename="{name}"\r\n'
            f'Content-Type: image/png\r\n\r\n').encode() + buf.getvalue() + \
           (f'\r\n--{b}\r\nContent-Disposition: form-data; name="overwrite"\r\n\r\ntrue\r\n--{b}--\r\n').encode()
    post("/upload/image", body, {"Content-Type": "multipart/form-data; boundary=" + b})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("out")
    ap.add_argument("--crop", nargs=4, type=int, required=True)
    ap.add_argument("--box", nargs=4, type=int, action="append", required=True)
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--feather", type=float, default=6)
    ap.add_argument("--steps", type=int, default=28)
    ap.add_argument("--guidance", type=float, default=30)
    a = ap.parse_args()
    seed = a.seed if a.seed is not None else random.randint(0, 2**31)

    src = Image.open(a.src).convert("RGB")
    cx0, cy0, cx1, cy1 = a.crop
    crop = src.crop(a.crop)
    mask = Image.new("L", src.size, 0)
    d = ImageDraw.Draw(mask)
    for b in a.box:
        d.rounded_rectangle(b, radius=14, fill=255)
    mask_crop = mask.crop(a.crop)
    upload(crop, "face_inpaint_in.png")
    upload(mask_crop.convert("RGB"), "face_inpaint_mask.png")

    g = {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "flux1-fill-dev.safetensors", "weight_dtype": "default"}},
        "2": {"class_type": "DualCLIPLoader", "inputs": {"clip_name1": "clip_l.safetensors", "clip_name2": "t5xxl_fp8_e4m3fn_scaled.safetensors", "type": "flux"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
        "4": {"class_type": "LoadImage", "inputs": {"image": "face_inpaint_in.png"}},
        "5": {"class_type": "LoadImageMask", "inputs": {"image": "face_inpaint_mask.png", "channel": "red"}},
        "6": {"class_type": "GrowMask", "inputs": {"mask": ["5", 0], "expand": 4, "tapered_corners": True}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": a.prompt}},
        "8": {"class_type": "FluxGuidance", "inputs": {"conditioning": ["7", 0], "guidance": a.guidance}},
        "9": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["7", 0]}},
        "10": {"class_type": "InpaintModelConditioning", "inputs": {"positive": ["8", 0], "negative": ["9", 0], "vae": ["3", 0], "pixels": ["4", 0], "mask": ["6", 0], "noise_mask": True}},
        "11": {"class_type": "DifferentialDiffusion", "inputs": {"model": ["1", 0]}},
        "12": {"class_type": "KSampler", "inputs": {"model": ["11", 0], "positive": ["10", 0], "negative": ["10", 1], "latent_image": ["10", 2], "seed": seed, "steps": a.steps, "cfg": 1.0, "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0}},
        "13": {"class_type": "VAEDecode", "inputs": {"samples": ["12", 0], "vae": ["3", 0]}},
        "14": {"class_type": "SaveImage", "inputs": {"images": ["13", 0], "filename_prefix": "face_inpaint"}},
    }
    pid = post("/prompt", json.dumps({"prompt": g}).encode(), {"Content-Type": "application/json"})["prompt_id"]
    t0 = time.time()
    while True:
        h = json.load(urllib.request.urlopen(f"{URL}/history/{pid}"))
        if pid in h:
            break
        if time.time() - t0 > 600:
            raise SystemExit("timeout")
        time.sleep(1.5)
    if h[pid]["status"]["status_str"] != "success":
        raise SystemExit("failed: " + json.dumps(h[pid]["status"])[:1500])
    im = h[pid]["outputs"]["14"]["images"][0]
    q = f"filename={im['filename']}&subfolder={im['subfolder']}&type={im['type']}"
    res = Image.open(io.BytesIO(urllib.request.urlopen(f"{URL}/view?{q}").read())).convert("RGB")
    soft = mask_crop.filter(ImageFilter.GaussianBlur(a.feather))
    merged = Image.composite(res, crop, soft)
    out = src.copy()
    out.paste(merged, (cx0, cy0))
    out.save(a.out)
    print("seed", seed, "->", a.out)


main()
