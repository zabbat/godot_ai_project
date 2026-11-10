"""Draw inpaint boxes (red), the crop window (blue) and a labelled pixel grid on a copy of a
picture, to check the boxes before running an edit.

  python.exe -I draw_boxes.py <src.png> <out.png> --box x0 y0 x1 y1 [--box ...]
      [--crop x0 y0 x1 y1] [--grid 64] [--view x0 y0 x1 y1]

Coordinates are in the source's pixels. --view crops the output to that area (at full
resolution, so the grid labels stay readable).
"""
import argparse
from PIL import Image, ImageDraw


def main():
	ap = argparse.ArgumentParser()
	ap.add_argument("src"); ap.add_argument("out")
	ap.add_argument("--box", nargs=4, type=int, action="append", default=[])
	ap.add_argument("--crop", nargs=4, type=int)
	ap.add_argument("--grid", type=int, default=64)
	ap.add_argument("--view", nargs=4, type=int)
	a = ap.parse_args()
	im = Image.open(a.src).convert("RGB")
	d = ImageDraw.Draw(im)
	w, h = im.size
	if a.grid > 0:
		for x in range(0, w, a.grid):
			d.line((x, 0, x, h), fill=(255, 255, 0))
			for y in range(0, h, a.grid * 4):
				d.text((x + 2, y + 2), str(x), fill=(255, 255, 0))
		for y in range(0, h, a.grid):
			d.line((0, y, w, y), fill=(255, 255, 0))
			for x in range(0, w, a.grid * 4):
				d.text((x + 2, y + 12), str(y), fill=(0, 255, 255))
	if a.crop:
		d.rectangle(a.crop, outline=(0, 0, 255), width=3)
	for b in a.box:
		d.rectangle(b, outline=(255, 0, 0), width=3)
	if a.view:
		im = im.crop(a.view)
	im.save(a.out)
	print("saved", a.out)


if __name__ == "__main__":
	main()
