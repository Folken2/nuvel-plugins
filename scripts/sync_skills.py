"""Copy knowledge skills from a nuvel checkout into a plugin, or check the copy.

A plugin that republishes skills from the nuvel repo lists them in
``plugins/<plugin>/source.json``::

    {"repo": "https://github.com/Folken2/nuvel",
     "commit": "<sha the copy was taken from>",
     "skills": {"adk-tool-creation": "nuvel/backends/adk/skills/adk-tool-creation", ...}}

The copy is byte-for-byte; the only file the plugin adds to a synced skill is
``agents/openai.yaml`` (Codex UI metadata), which this script never touches.

    python scripts/sync_skills.py agent-builder --from ../nuvel           # copy, pin HEAD
    python scripts/sync_skills.py agent-builder --from ../nuvel --check   # CI: fail on drift
"""

from __future__ import annotations

import argparse
import filecmp
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_OWNED = {Path("agents/openai.yaml")}
IGNORED_PARTS = {"__pycache__", ".DS_Store"}


def _files(directory: Path) -> set[Path]:
    if not directory.is_dir():
        return set()
    return {
        p.relative_to(directory)
        for p in directory.rglob("*")
        if p.is_file() and not IGNORED_PARTS.intersection(p.parts)
    }


def _head(checkout: Path) -> str:
    out = subprocess.run(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    )
    return out.stdout.strip()


def drift(plugin_dir: Path, source: Path) -> list[str]:
    """Differences between the plugin's copy and the nuvel checkout, as messages."""
    spec = json.loads((plugin_dir / "source.json").read_text(encoding="utf-8"))
    problems: list[str] = []
    for name, rel in spec["skills"].items():
        src, dst = source / rel, plugin_dir / "skills" / name
        if not (src / "SKILL.md").is_file():
            problems.append(f"{name}: {rel}/SKILL.md not found in the nuvel checkout")
            continue
        src_files, dst_files = _files(src), _files(dst) - PLUGIN_OWNED
        for f in sorted(src_files - dst_files):
            problems.append(f"{name}: missing {f}")
        for f in sorted(dst_files - src_files):
            problems.append(f"{name}: extra {f}")
        for f in sorted(src_files & dst_files):
            if not filecmp.cmp(src / f, dst / f, shallow=False):
                problems.append(f"{name}: differs {f}")
    return problems


def sync(plugin_dir: Path, source: Path) -> None:
    spec_path = plugin_dir / "source.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    for name, rel in spec["skills"].items():
        src, dst = source / rel, plugin_dir / "skills" / name
        if not (src / "SKILL.md").is_file():
            raise SystemExit(f"{name}: {rel}/SKILL.md not found in {source}")
        for f in _files(dst) - PLUGIN_OWNED - _files(src):
            (dst / f).unlink()
        for f in _files(src):
            (dst / f).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src / f, dst / f)
    spec["commit"] = _head(source)
    spec_path.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("plugin", help="plugin folder name under plugins/")
    parser.add_argument("--from", dest="source", required=True, type=Path, help="path to a nuvel checkout")
    parser.add_argument("--check", action="store_true", help="report drift and exit 1 instead of copying")
    args = parser.parse_args(argv)
    plugin_dir = ROOT / "plugins" / args.plugin
    if not (plugin_dir / "source.json").is_file():
        parser.error(f"plugins/{args.plugin}/source.json not found")
    if args.check:
        problems = drift(plugin_dir, args.source)
        for p in problems:
            print(p, file=sys.stderr)
        if problems:
            print(f"\n{len(problems)} difference(s); run without --check to resync.", file=sys.stderr)
            return 1
        print("in sync")
        return 0
    sync(plugin_dir, args.source)
    print(f"synced from {_head(args.source)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
