"""Check that the Godot project and the AI side of the repo agree.

Generic script from the `godot-ai-architecture` skill (assets/check_sync.py).
Projects keep a copy in tools/godot-sync/ next to export_assets.py; improve the
skill's version, then copy it. Reads the same `prototype/asset_map/settings.toml`.

Reports only problems, as short lines, so an agent can act on them cheaply:

  export     targets that differ from what the asset map would produce; a
             target newer than its master is flagged as edited in Godot
  outputs    newer takes in the tools' output folders (`outputs` in settings.toml)
             than the one a master was chosen from (the master's .md names its
             take: "Image: <file>" / "Audio: <file>").
             List takes reviewed and not wanted in the .md ("Rejected: <file>, ...")
             to stop reporting them.
  unmapped   media files in Godot that no asset map entry produces
  unused     resources in assets/ that no entry uses
  structure  Godot folders missing from the structure doc, and paths the doc
             names that no longer exist
  index      files or folders an AGENTS.md does not list, and broken links in it
  changed    Godot data and code changed after the game data / structure doc
             (by git commit time, plus uncommitted changes)

Usage: python tools/godot-sync/check_sync.py [--repo PATH] [section ...]
Exit code 1 when something is reported.
"""

import argparse
import fnmatch
import re
import subprocess
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import export_assets  # noqa: E402

MEDIA = {".png", ".jpg", ".jpeg", ".webp", ".svg", ".wav", ".ogg", ".mp3", ".ttf", ".otf",
		".glb", ".gltf", ".bin", ".exr", ".hdr", ".fbx", ".obj"}
DATA_AND_CODE = {".tres", ".tscn", ".gd", ".gdshader", ".godot"}
SKIP_DIRS = {".godot", ".git", ".import", "android", "__pycache__"}
LINK = re.compile(r"\]\(([^)#\s]+)(?:#[^)]*)?\)")
SECTIONS = ["export", "outputs", "unmapped", "unused", "structure", "index", "changed"]
TAKE_LINE = re.compile(r"^(?:Image|Audio): (\S+)", re.MULTILINE)


def main() -> int:
	parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
	parser.add_argument("sections", nargs="*", help=f"sections to run: {', '.join(SECTIONS)} (default: all)")
	parser.add_argument("--repo", type=Path, help="repo root (default: found from the working directory)")
	args = parser.parse_args()
	unknown = set(args.sections) - set(SECTIONS)
	if unknown:
		parser.error(f"unknown section(s): {', '.join(sorted(unknown))}")

	repo = export_assets.find_repo(args.repo)
	settings = export_assets.load_toml(repo / export_assets.MAP_SUBDIR / "settings.toml")
	ctx = types.SimpleNamespace(
		repo=repo,
		settings=settings,
		map_dir=repo / export_assets.MAP_SUBDIR,
		assets=repo / settings["assets"],
		godot=repo / settings["godot_project"],
	)
	ctx.pairs = list(_all_pairs(ctx))

	problems = 0
	for section in args.sections or SECTIONS:
		lines = globals()[f"check_{section}"](ctx)
		for line in lines:
			print(f"{section:9}  {line}")
		problems += len(lines)
	print(f"\n{problems} problem(s)" if problems else "all in sync")
	return 1 if problems else 0


def _all_pairs(ctx):
	"""(source, target, profile name) for every file the asset map produces."""
	for area in export_assets.area_files(ctx.map_dir):
		for entry in export_assets.load_toml(area).get("asset", []):
			for source, target in export_assets.entry_pairs(entry, ctx.assets, ctx.godot):
				yield source, target, entry["profile"]


def _walk(root: Path):
	for path in sorted(root.rglob("*")):
		if not any(part in SKIP_DIRS for part in path.relative_to(root).parts):
			yield path


def check_export(ctx) -> list[str]:
	result = subprocess.run(
			[sys.executable, "-I", str(Path(export_assets.__file__)), "--dry-run", "--repo", str(ctx.repo)],
			capture_output=True, text=True)
	targets = {s.relative_to(ctx.assets).as_posix(): t for s, t, _ in ctx.pairs}
	lines = []
	for line in result.stdout.splitlines():
		if line.startswith("ERROR"):
			lines.append(line.strip())
		elif line.startswith("WRITE"):
			source = line.split()[2]
			target = targets.get(source)
			if target is not None and target.exists() 					and target.stat().st_mtime > (ctx.assets / source).stat().st_mtime:
				note = "Godot copy is newer than the master: edited in Godot? Check before exporting"
			elif target is not None and target.exists():
				note = "master changed: export"
			else:
				note = "not exported yet"
			lines.append(f"{source}  ({note})")
	return lines


def output_folders(settings: dict) -> list[str]:
	"""The tools' output folders from settings.toml (`outputs`; the older `workshop` key still works)."""
	folders = settings.get("outputs", [])
	if isinstance(folders, str):
		folders = [folders]
	if settings.get("workshop"):
		folders = [*folders, settings["workshop"]]
	return folders


def check_outputs(ctx) -> list[str]:
	takes = {}
	for folder in output_folders(ctx.settings):
		root = ctx.repo / folder
		if not root.is_dir():
			continue
		for path in root.rglob("*"):
			if path.is_file():
				takes.setdefault(path.name, path)
	if not takes:
		return []
	lines = []
	for record in sorted(ctx.assets.rglob("*.md")):
		text = record.read_text(encoding="utf-8")
		for take_name in TAKE_LINE.findall(text):
			take = takes.get(take_name)
			if take is None:
				continue
			newer = sorted(p.name for p in take.parent.iterdir()
					if p.is_file() and p.suffix == take.suffix and p.stat().st_mtime > take.stat().st_mtime
					and p.name not in text)
			if newer:
				lines.append(f"{record.relative_to(ctx.assets).as_posix()}  (chosen take {take_name}; "
						f"newer in {take.parent.relative_to(ctx.repo).as_posix()}: {', '.join(newer)})")
	return lines


def check_unmapped(ctx) -> list[str]:
	targets = {t.resolve() for _, t, _ in ctx.pairs}
	ignored = ctx.settings.get("not_exported", [])
	lines = []
	for path in _walk(ctx.godot):
		relative = path.relative_to(ctx.godot).as_posix()
		if path.is_file() and path.suffix.lower() in MEDIA and path.resolve() not in targets \
				and not any(fnmatch.fnmatch(relative, p) for p in ignored):
			lines.append(f"{relative}  (in Godot, not produced by the asset map)")
	return lines


def check_unused(ctx) -> list[str]:
	sources = {s.resolve() for s, _, _ in ctx.pairs}
	records = ctx.settings.get("asset_records", [])
	lines = []
	for path in _walk(ctx.assets):
		if path.is_file() and path.resolve() not in sources \
				and not any(fnmatch.fnmatch(path.name, p) for p in records):
			lines.append(f"{path.relative_to(ctx.assets).as_posix()}  (in assets/, no map entry)")
	return lines


def check_structure(ctx) -> list[str]:
	doc_path = ctx.repo / ctx.settings["godot_structure"]
	if not doc_path.exists():
		return [f"{ctx.settings['godot_structure']} missing"]
	doc = doc_path.read_text(encoding="utf-8")
	named = set(re.findall(r"`([A-Za-z0-9_./<>-]+/)`", doc))
	patterns = [_pattern_regex(n) for n in named if "<" in n]
	lines = []
	for path in _walk(ctx.godot):
		if not path.is_dir():
			continue
		relative = path.relative_to(ctx.godot).as_posix() + "/"
		documented_below = any(n.startswith(relative) for n in named)
		if relative in named or path.name + "/" in named or documented_below 				or any(p.match(relative) for p in patterns):
			continue
		empty = "" if any(path.iterdir()) else ", empty"
		lines.append(f"{relative}  (folder not in the structure doc{empty})")
	for folder in sorted(named):
		# Only full paths whose top folder exists; other names are planned or short names.
		top = ctx.godot / folder.split("/")[0]
		if "<" not in folder and folder.count("/") > 1 and top.is_dir() and not (ctx.godot / folder).exists():
			lines.append(f"{folder}  (named in the structure doc, not in Godot; planned?)")
	return lines


def _pattern_regex(pattern: str) -> re.Pattern:
	"""`entities/heroes/<name>/` matches `entities/heroes/knight/` and everything below it."""
	parts = [("[^/]+" if part.startswith("<") else re.escape(part)) for part in re.split(r"(<[^>]+>)", pattern)]
	return re.compile("^" + "".join(parts))


def check_index(ctx) -> list[str]:
	lines = []
	for index in sorted(ctx.repo.rglob("AGENTS.md")):
		parts = index.relative_to(ctx.repo).parts[:-1]
		if any(part.startswith(".") or part in SKIP_DIRS for part in parts) or index.is_relative_to(ctx.godot):
			continue
		text = index.read_text(encoding="utf-8")
		folder = index.parent
		for link in LINK.findall(text):
			if not link.startswith(("http:", "https:")) and not (folder / link).exists():
				lines.append(f"{index.relative_to(ctx.repo).as_posix()}  broken link {link}")
		if folder == ctx.repo:
			continue
		for child in sorted(folder.iterdir()):
			if child.name == "AGENTS.md" or child.name.startswith(".") or child.name in SKIP_DIRS:
				continue
			if child.is_file() and child.suffix != ".md" and folder.relative_to(ctx.repo).parts[0] == "assets":
				continue
			name = child.name + ("/" if child.is_dir() else "")
			if child.name not in text:
				lines.append(f"{index.relative_to(ctx.repo).as_posix()}  does not list {name}")
	return lines


def check_changed(ctx) -> list[str]:
	docs = [ctx.settings[k] for k in ("game_data", "godot_structure") if k in ctx.settings]
	doc_time = max((_commit_time(ctx.repo, d) for d in docs), default=0)
	godot_rel = ctx.godot.relative_to(ctx.repo).as_posix()
	lines = []
	status = _git(ctx.repo, "status", "--porcelain", "--", godot_rel)
	for line in status.splitlines():
		path = line[3:].strip().strip('"')
		if Path(path).suffix in DATA_AND_CODE:
			lines.append(f"{path}  (uncommitted change: check the docs)")
	if doc_time:
		log = _git(ctx.repo, "log", f"--since={doc_time + 1}", "--name-only", "--format=", "--", godot_rel)
		for path in sorted(set(log.split())):
			if Path(path).suffix in DATA_AND_CODE and (ctx.repo / path).exists():
				lines.append(f"{path}  (committed after the docs were last changed)")
	return lines


def _commit_time(repo: Path, path: str) -> int:
	out = _git(repo, "log", "-1", "--format=%ct", "--", path).strip()
	return int(out) if out else 0


def _git(repo: Path, *args: str) -> str:
	return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True).stdout


if __name__ == "__main__":
	sys.exit(main())
