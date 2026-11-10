"""Show what an edit changed: the share of changed pixels, their bounding box, and a picture
with every changed pixel in magenta over the original (the edit's boxes in yellow), next to
before/after crops of the changed area.

  python.exe -I diff_check.py <before.png> <after.png> <out.png> [--box x0 y0 x1 y1 ...]
      [--threshold 0]

Compares RGB only (alpha is ignored: a variant may share the original's alpha). Both pictures
must have the same size. With --box, also reports changed pixels outside all boxes (should be
none, apart from the feathered edge of a few pixels).
"""
import argparse
import numpy as np
from PIL import Image, ImageDraw


def main():
	ap = argparse.ArgumentParser()
	ap.add_argument("before"); ap.add_argument("after"); ap.add_argument("out")
	ap.add_argument("--box", nargs=4, type=int, action="append", default=[])
	ap.add_argument("--threshold", type=int, default=0)
	a = ap.parse_args()
	before = Image.open(a.before).convert("RGB")
	after = Image.open(a.after).convert("RGB")
	if before.size != after.size:
		raise SystemExit(f"sizes differ: {before.size} vs {after.size}")
	b = np.asarray(before, int)
	diff = np.abs(b - np.asarray(after, int)).sum(2) > a.threshold
	if not diff.any():
		print("no change")
		return
	ys, xs = np.nonzero(diff)
	bbox = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
	print(f"changed: {100 * diff.mean():.1f}% of the picture, bbox {bbox}")
	if a.box:
		inside = np.zeros_like(diff)
		for x0, y0, x1, y1 in a.box:
			inside[max(0, y0 - 16):y1 + 16, max(0, x0 - 16):x1 + 16] = True
		outside = int((diff & ~inside).sum())
		print(f"changed outside the boxes (+16 px feather margin): {outside} px")

	view = np.asarray(before).copy()
	view[diff] = (view[diff] * 0.4 + np.array([255, 0, 255]) * 0.6).astype("uint8")
	overlay = Image.fromarray(view)
	d = ImageDraw.Draw(overlay)
	for box in a.box:
		d.rectangle(box, outline=(255, 255, 0), width=3)

	side = 640
	scale = side / max(before.size)
	overlay = overlay.resize((round(before.width * scale), round(before.height * scale)))
	pad = 24
	crop = (max(0, bbox[0] - pad), max(0, bbox[1] - pad),
			min(before.width, bbox[2] + pad), min(before.height, bbox[3] + pad))
	cw, ch = crop[2] - crop[0], crop[3] - crop[1]
	cs = min(side / 2 / cw, side / ch)
	size = (max(1, round(cw * cs)), max(1, round(ch * cs)))
	sheet = Image.new("RGB", (overlay.width + 2 * size[0], max(overlay.height, size[1])))
	sheet.paste(overlay, (0, 0))
	sheet.paste(before.crop(crop).resize(size), (overlay.width, 0))
	sheet.paste(after.crop(crop).resize(size), (overlay.width + size[0], 0))
	sheet.save(a.out)
	print("saved", a.out, "(left: changes in magenta; right: before | after)")


if __name__ == "__main__":
	main()
