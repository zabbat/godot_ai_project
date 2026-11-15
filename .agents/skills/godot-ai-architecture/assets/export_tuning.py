"""Turn the hand-edited tuning file into a GDScript file for the Godot project.

Generic script from the `godot-ai-architecture` skill (assets/export_tuning.py).
Projects keep a copy in tools/godot-sync/; improve the skill's version, then copy it.

Reads `tuning` (a TOML file of [section] name = value) and writes `tuning_target`
(a .gd file under the Godot project) with one `const VALUES` dictionary keyed
"section.name". Both paths are in `prototype/asset_map/settings.toml`. A GDScript
file (not a .cfg) is used so it is always packed into an export. Only writes if
the content changed.

Usage:
    python tools/godot-sync/export_tuning.py            # write if changed
    python tools/godot-sync/export_tuning.py --check    # exit 1 if the .gd is out of date
"""

import argparse
import sys
import tomllib
from pathlib import Path

HEADER = """\
# GENERATED from {source} by tools/godot-sync/export_tuning.py. Do not edit here.
class_name TuningValues
extends RefCounted
## Every tuning value, keyed "section.name". Read through Tuning.

const VALUES := {{
{rows}
}}
"""


def find_repo(start: Path | None = None) -> Path:
	start = (start or Path.cwd()).resolve()
	for folder in (start, *start.parents):
		if (folder / "prototype" / "asset_map" / "settings.toml").exists():
			return folder
	raise SystemExit(f"no prototype/asset_map/settings.toml found at or above {start}")


def gd_literal(value) -> str:
	if isinstance(value, bool):
		return "true" if value else "false"
	if isinstance(value, int):
		return str(value)
	if isinstance(value, float):
		return repr(value)
	if isinstance(value, str):
		return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
	raise SystemExit(f"unsupported value {value!r}: use a number, bool or string")


def render(repo: Path, settings: dict) -> tuple[Path, str]:
	source = settings["tuning"]
	data = tomllib.loads((repo / source).read_text(encoding="utf-8"))
	rows = []
	for section, values in data.items():
		if not isinstance(values, dict):
			raise SystemExit(f"{source}: '{section}' must be a [section] of name = value lines")
		for name, value in values.items():
			rows.append(f'\t"{section}.{name}": {gd_literal(value)},')
	target = repo / settings["godot_project"] / settings["tuning_target"]
	return target, HEADER.format(source=source, rows="\n".join(rows))


def main() -> int:
	parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
	parser.add_argument("--check", action="store_true", help="only report whether the .gd is up to date")
	parser.add_argument("--repo", type=Path)
	args = parser.parse_args()
	repo = find_repo(args.repo)
	settings = tomllib.loads((repo / "prototype/asset_map/settings.toml").read_text(encoding="utf-8"))
	if "tuning" not in settings or "tuning_target" not in settings:
		print("settings.toml has no `tuning` / `tuning_target`: nothing to do")
		return 0
	target, text = render(repo, settings)
	current = target.read_text(encoding="utf-8") if target.exists() else None
	if current == text:
		print(f"up to date: {target.relative_to(repo).as_posix()}")
		return 0
	if args.check:
		print(f"out of date: {target.relative_to(repo).as_posix()} (run export_tuning.py)")
		return 1
	target.parent.mkdir(parents=True, exist_ok=True)
	target.write_text(text, encoding="utf-8", newline="\n")
	print(f"wrote {target.relative_to(repo).as_posix()}")
	return 0


if __name__ == "__main__":
	sys.exit(main())
