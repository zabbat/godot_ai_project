"""Export source assets into the Godot project, following the asset map.

Generic script from the `godot-ai-architecture` skill (assets/export_assets.py).
Projects keep a copy in tools/godot-sync/; improve the skill's version, then copy it.

Reads every `<area>.toml` in the asset map folder, converts each entry's
`source` (under the assets folder) with its profile from `profiles.toml`, and
writes the result to `target` (under the Godot project). Paths come from
`settings.toml` in the asset map folder. See the `godot-ai-architecture` skill.

The repo root is the nearest folder, from the working directory up, that has
`prototype/asset_map/settings.toml` (or pass --repo).

Usage (Python 3.11+ with Pillow; ffmpeg on PATH for audio profiles):
    python tools/godot-sync/export_assets.py              # export everything that changed
    python tools/godot-sync/export_assets.py --dry-run    # only report what would change
    python tools/godot-sync/export_assets.py portraits    # only these areas (toml names)
    python tools/godot-sync/export_assets.py --force      # rewrite every target

Profile kinds:
    copy    copy the file or folder tree unchanged
    image   resize (cover crop to `size`, never upscale) and save as `format`;
            metadata such as embedded ComfyUI prompts is dropped
    ffmpeg  run ffmpeg with `args` and write `format`

A profile or entry may add `import = { key = value }`: Godot import settings
written into the target's `.import` file. If Godot has not created that file
yet, open the project in Godot once and export again.
"""

import argparse
import fnmatch
import filecmp
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

MAP_SUBDIR = Path("prototype") / "asset_map"


def find_repo(start: Path | None = None) -> Path:
	"""The nearest folder at or above `start` (default: working directory) with an asset map."""
	start = (start or Path.cwd()).resolve()
	for folder in (start, *start.parents):
		if (folder / MAP_SUBDIR / "settings.toml").exists():
			return folder
	raise SystemExit(f"no {MAP_SUBDIR.as_posix()}/settings.toml found at or above {start}")


def main() -> int:
	parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
	parser.add_argument("areas", nargs="*", help="asset map files to export, without .toml (default: all)")
	parser.add_argument("--dry-run", action="store_true", help="report changes without writing")
	parser.add_argument("--force", action="store_true", help="rewrite targets even if up to date")
	parser.add_argument("--repo", type=Path, help="repo root (default: found from the working directory)")
	args = parser.parse_args()

	repo = find_repo(args.repo)
	map_dir = repo / MAP_SUBDIR
	settings = load_toml(map_dir / "settings.toml")
	assets_root = repo / settings["assets"]
	godot_root = repo / settings["godot_project"]
	profiles = load_toml(map_dir / "profiles.toml")["profile"]

	areas = area_files(map_dir)
	if args.areas:
		areas = [p for p in areas if p.stem in args.areas]
		missing = set(args.areas) - {p.stem for p in areas}
		if missing:
			print(f"unknown area(s): {', '.join(sorted(missing))}")
			return 1

	counts = {"written": 0, "unchanged": 0, "errors": 0}
	for area in areas:
		for entry in load_toml(area).get("asset", []):
			profile = profiles.get(entry["profile"])
			if profile is None:
				_report("error", area.stem, entry["source"], f"unknown profile '{entry['profile']}'")
				counts["errors"] += 1
				continue
			for source, target in entry_pairs(entry, assets_root, godot_root):
				status, note = _export(source, target, profile, entry, args)
				_report(status, area.stem, source.relative_to(assets_root).as_posix(), note)
				counts["errors" if status == "error" else "unchanged" if status == "ok" else "written"] += 1

	print(f"\n{counts['written']} written, {counts['unchanged']} unchanged, {counts['errors']} errors"
			+ (" (dry run)" if args.dry_run else ""))
	return 1 if counts["errors"] else 0


def area_files(map_dir: Path) -> list[Path]:
	return sorted(p for p in map_dir.glob("*.toml") if p.stem not in ("profiles", "settings"))


def load_toml(path: Path) -> dict:
	with path.open("rb") as f:
		return tomllib.load(f)


def entry_pairs(entry: dict, assets_root: Path, godot_root: Path):
	"""(source, target) file pairs of an entry; a folder entry expands to its files."""
	source = assets_root / entry["source"]
	target = godot_root / entry["target"]
	if not entry["source"].endswith("/"):
		yield source, target
		return
	exclude = entry.get("exclude", [])
	for path in sorted(source.rglob("*")):
		relative = path.relative_to(source)
		if path.is_file() and not any(fnmatch.fnmatch(relative.as_posix(), p) for p in exclude):
			yield path, target / relative


def _export(source: Path, target: Path, profile: dict, entry: dict, args) -> tuple[str, str]:
	if not source.exists():
		return "error", "source missing"
	kind = profile.get("kind", "copy")
	try:
		if kind == "copy":
			changed = args.force or not target.exists() or not filecmp.cmp(source, target, shallow=False)
			if changed and not args.dry_run:
				target.parent.mkdir(parents=True, exist_ok=True)
				shutil.copyfile(source, target)
		elif kind == "image":
			changed = _export_image(source, target, profile, args)
		elif kind == "ffmpeg":
			changed = args.force or not target.exists() or source.stat().st_mtime > target.stat().st_mtime
			if changed and not args.dry_run:
				target.parent.mkdir(parents=True, exist_ok=True)
				command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(source),
						*profile.get("args", "").split(), str(target)]
				subprocess.run(command, check=True)
		else:
			return "error", f"unknown profile kind '{kind}'"
	except (OSError, subprocess.CalledProcessError, ValueError) as error:
		return "error", str(error)

	import_settings = {**profile.get("import", {}), **entry.get("import", {})}
	import_note = ""
	if import_settings and not args.dry_run:
		import_note = _apply_import_settings(target, import_settings)
	return ("write" if changed else "ok"), import_note


def _export_image(source: Path, target: Path, profile: dict, args) -> bool:
	from PIL import Image, ImageChops, ImageOps

	image = Image.open(source)
	image.load()
	width, height = profile.get("size", image.size)
	if image.width < width or image.height < height:
		raise ValueError(f"source {image.size} is smaller than {width}x{height}")
	if image.size != (width, height):
		image = ImageOps.fit(image, (width, height), Image.Resampling.LANCZOS)
	image.info = {}

	if target.exists() and not args.force:
		existing = Image.open(target)
		if existing.size == image.size and existing.mode == image.mode \
				and ImageChops.difference(existing, image).getbbox() is None:
			return False
	if not args.dry_run:
		target.parent.mkdir(parents=True, exist_ok=True)
		image.save(target, format=profile.get("format", target.suffix[1:]).upper(), optimize=True)
	return True


def _apply_import_settings(target: Path, settings: dict) -> str:
	"""Sets keys in the [params] section of the target's .import file."""
	import_file = target.with_name(target.name + ".import")
	if not import_file.exists():
		return "no .import yet: open Godot, then export again"
	lines = import_file.read_text(encoding="utf-8").splitlines()
	try:
		start = lines.index("[params]") + 1
	except ValueError:
		return "no [params] in .import"
	end = next((i for i in range(start, len(lines)) if lines[i].startswith("[")), len(lines))
	changed = False
	for key, value in settings.items():
		line = f"{key}={_godot_value(value)}"
		index = next((i for i in range(start, end) if lines[i].split("=", 1)[0] == key), None)
		if index is None:
			lines.insert(end, line)
			end += 1
			changed = True
		elif lines[index] != line:
			lines[index] = line
			changed = True
	if changed:
		import_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
		return "import settings updated"
	return ""


def _godot_value(value) -> str:
	if isinstance(value, bool):
		return "true" if value else "false"
	if isinstance(value, str):
		return f'"{value}"'
	return str(value)


def _report(status: str, area: str, source: str, note: str) -> None:
	if status == "ok" and not note:
		return
	label = {"write": "WRITE", "ok": "ok", "error": "ERROR"}[status]
	print(f"{label:5}  {area:10}  {source}" + (f"  ({note})" if note else ""))


if __name__ == "__main__":
	sys.exit(main())
