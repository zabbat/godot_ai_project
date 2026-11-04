# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Start the Blender MCP sandbox for one project.

Claude Code runs this from the project's .mcp.json. It reads the project's
sandbox.toml (--config, relative to the project root; default
tools/blender/config/sandbox.toml, else blender/config/sandbox.toml), checks
every shared folder, and runs the
blender-mcp-sandbox Docker image with --network none and only those folders
mounted. stdin/stdout are passed straight through (they carry the MCP protocol),
so this script prints nothing to stdout except in --check mode.

    uv run run_sandbox.py --config tools/blender/config/sandbox.toml           # used by .mcp.json
    uv run run_sandbox.py --config tools/blender/config/sandbox.toml --check   # validate, print the docker command

The project root is CLAUDE_PROJECT_DIR (set by Claude Code), else --project, else
the current directory.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import NoReturn

# Tried in order when --config is not given (relative to the project root).
DEFAULT_CONFIGS = [Path("tools") / "blender" / "config" / "sandbox.toml",
                   Path("blender") / "config" / "sandbox.toml"]

# Never shared: code or settings that run on the host, the Godot project. Also blocked (see
# blocked_paths): the sandbox's own config folder, the other tools next to the Blender folder,
# and tools/ as a whole.
BLOCKED = [".git", ".claude", ".mcp.json", ".vscode", "godot"]

# Container paths a share may not use.
RESERVED_MOUNTS = {"bin", "boot", "dev", "etc", "home", "lib", "lib64", "media", "mnt", "opt",
                   "proc", "root", "run", "sbin", "srv", "sys", "tmp", "usr", "var"}

DEFAULTS = {"image": "blender-mcp-sandbox", "memory": "8g", "cpus": ""}


def fail(msg: str) -> NoReturn:
    print("blender sandbox: " + msg, file=sys.stderr)
    sys.exit(1)


def is_within(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def blocked_paths(root: Path, cfg_path: Path) -> list[Path]:
    """Folders a share may not be, contain or be inside."""
    config_dir = cfg_path.parent                  # <blender>/config
    blender_dir = config_dir.parent               # e.g. tools/blender
    blocked = [(root / b).resolve() for b in BLOCKED] + [config_dir]
    tools = (root / "tools").resolve()
    if blender_dir.parent != root:
        # Blender lives in a tools folder: every sibling tool is off limits (their scripts and
        # environments run on the host); sharing the parent would contain them.
        blocked += [p.resolve() for p in blender_dir.parent.iterdir() if p.resolve() != blender_dir]
    if not is_within(blender_dir, tools):
        blocked.append(tools)
    return blocked


def load_shares(root: Path, cfg: dict, cfg_path: Path) -> list[tuple[Path, str, bool]]:
    shares = cfg.get("share", [])
    if not shares:
        fail("no [[share]] entries in {} - share at least one folder".format(cfg_path))
    blocked = blocked_paths(root, cfg_path)
    mounts: set[str] = set()
    out = []
    for i, s in enumerate(shares, 1):
        rel, mount, access = s.get("path"), s.get("mount"), s.get("access", "rw")
        where = "share #{} ({!r})".format(i, rel)
        if not isinstance(rel, str) or not rel.strip():
            fail(where + ": 'path' is required")
        if Path(rel).is_absolute() or rel.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", rel):
            fail(where + ": 'path' must be relative to the project root")
        host = (root / rel).resolve()
        if not is_within(host, root) or host == root:
            fail(where + ": must be a folder inside the project, not the project root or outside it")
        for b in blocked:
            if is_within(host, b) or is_within(b, host):
                fail(where + ": may not be, contain or be inside '{}'".format(b.relative_to(root).as_posix()))
        if not isinstance(mount, str) or not re.fullmatch(r"/[a-z0-9][a-z0-9_-]*", mount):
            fail(where + ": 'mount' must look like /models (one level, lowercase)")
        if mount[1:] in RESERVED_MOUNTS:
            fail(where + ": mount {} is a system path inside the container".format(mount))
        if mount in mounts:
            fail(where + ": mount {} is used twice".format(mount))
        if access not in ("rw", "ro"):
            fail(where + ": 'access' must be rw or ro")
        mounts.add(mount)
        if host.exists() and not host.is_dir():
            fail(where + ": {} is a file, not a folder".format(host))
        out.append((host, mount, access == "ro"))
    for host, _, _ in out:  # only once every share is valid
        host.mkdir(parents=True, exist_ok=True)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="validate and print the docker command")
    ap.add_argument("--project", help="project root (default: CLAUDE_PROJECT_DIR or cwd)")
    ap.add_argument("--config", help="sandbox.toml relative to the project root "
                    "(default: tools/blender/config/sandbox.toml, else blender/config/sandbox.toml)")
    args = ap.parse_args()

    root = Path(args.project or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()).resolve()
    if args.config:
        rel = Path(args.config)
        if rel.is_absolute():
            fail("--config must be relative to the project root")
        candidates = [rel]
    else:
        candidates = DEFAULT_CONFIGS
    cfg_path = next(((root / c).resolve() for c in candidates if (root / c).is_file()), None)
    if cfg_path is None:
        fail("no {} in {} - run the blender-3d-modeling skill's project setup".format(
            " or ".join(c.as_posix() for c in candidates), root))
    if not is_within(cfg_path, root) or cfg_path.parent.name != "config":
        fail("{}: the config must be <blender folder>/config/sandbox.toml inside the project".format(cfg_path))
    try:
        # utf-8-sig: tolerate a BOM (Notepad, PowerShell 5).
        cfg = tomllib.loads(cfg_path.read_text(encoding="utf-8-sig"))
    except tomllib.TOMLDecodeError as ex:
        fail("{}: {}".format(cfg_path, ex))
    opts = {**DEFAULTS, **{k: v for k, v in cfg.items() if k in DEFAULTS}}

    docker = shutil.which("docker")
    if not docker:
        fail("docker not found - install and start Docker Desktop")

    cmd = [docker, "run", "-i", "--rm", "--network", "none", "--cap-drop", "ALL",
           "--security-opt", "no-new-privileges", "--memory", str(opts["memory"])]
    if opts["cpus"]:
        cmd += ["--cpus", str(opts["cpus"])]
    for host, mount, ro in load_shares(root, cfg, cfg_path):
        cmd += ["-v", "{}:{}{}".format(host, mount, ":ro" if ro else "")]
    cmd.append(str(opts["image"]))

    if args.check:
        print("project: {}".format(root))
        print("config:  {}".format(cfg_path))
        print("command: " + subprocess.list2cmdline(cmd))
        return
    sys.exit(subprocess.run(cmd).returncode)


if __name__ == "__main__":
    main()
