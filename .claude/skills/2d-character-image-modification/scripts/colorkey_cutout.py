"""Colour-key cut-out for a figure drawn on a plain flat background (the Necromancer's half portrait: ochre).

Usage: python -I colorkey_cutout.py <source.png> <out.png> [--tol 38] [--soft 14]
The background colour is the median of the image border. Pixels within `tol` (RGB distance)
of it that connect to the image border (flood fill, so same-coloured spots inside the figure
stay) become transparent; pixels between tol and tol+soft get partial alpha, and their colour
is un-mixed from the background so no ochre fringe remains. Keeps what a person mask drops
(staffs, flames held away from the body).
"""
import argparse
from collections import deque

import numpy as np
from PIL import Image, ImageFilter

ap = argparse.ArgumentParser()
ap.add_argument("src")
ap.add_argument("out")
ap.add_argument("--tol", type=float, default=38)
ap.add_argument("--soft", type=float, default=14)
ap.add_argument("--holes", type=int, default=0,
                help="also clear enclosed background gaps (e.g. between hair and arm) of at least this many pixels")
a = ap.parse_args()

rgb = np.asarray(Image.open(a.src).convert("RGB")).astype(np.float32)
h, w, _ = rgb.shape
border = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
bg = np.median(border, axis=0)
dist = np.linalg.norm(rgb - bg, axis=2)
near = dist < a.tol + a.soft

# Flood fill from the border over near-background pixels.
outside = np.zeros((h, w), bool)
q = deque()
for y in range(h):
    for x in (0, w - 1):
        if near[y, x] and not outside[y, x]:
            outside[y, x] = True
            q.append((y, x))
for x in range(w):
    for y in (0, h - 1):
        if near[y, x] and not outside[y, x]:
            outside[y, x] = True
            q.append((y, x))
while q:
    y, x = q.popleft()
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        ny, nx = y + dy, x + dx
        if 0 <= ny < h and 0 <= nx < w and near[ny, nx] and not outside[ny, nx]:
            outside[ny, nx] = True
            q.append((ny, nx))

# Enclosed gaps of background colour (not reached from the border) of at least --holes pixels.
if a.holes > 0:
    from scipy import ndimage
    labels, count = ndimage.label((dist < a.tol) & ~outside)
    if count:
        sizes = ndimage.sum(np.ones((h, w)), labels, range(1, count + 1))
        for i, size in enumerate(sizes, start=1):
            if size >= a.holes:
                outside |= labels == i

alpha = np.ones((h, w), np.float32)
ramp = np.clip((dist - a.tol) / a.soft, 0, 1)
alpha[outside] = ramp[outside]
# Un-mix the background from partly transparent pixels: c = a*f + (1-a)*bg.
safe = np.maximum(alpha, 1e-3)[..., None]
fg = np.clip((rgb - (1 - alpha[..., None]) * bg) / safe, 0, 255)
out = np.where(alpha[..., None] > 0, fg, 0)
a_img = Image.fromarray((alpha * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))
img = Image.fromarray(out.astype(np.uint8)).convert("RGBA")
img.putalpha(a_img)
img.save(a.out)
print("saved", a.out, "bg", bg.round().tolist())
