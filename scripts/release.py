"""Release helper for the plugins in this marketplace.

Tags are per plugin: ``<plugin>-v<version>``, e.g. ``chief-of-staff-v0.3.0``.

    python scripts/release.py check <tag>   # tag matches every manifest and the CHANGELOG
    python scripts/release.py notes <tag>   # print that version's CHANGELOG section
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = (".claude-plugin/plugin.json", ".codex-plugin/plugin.json", "plugin.json")
TAG_RE = re.compile(r"^(?P<plugin>[a-z0-9]([a-z0-9-]*[a-z0-9])?)-v(?P<version>\d+\.\d+\.\d+)$")


def parse_tag(tag: str) -> tuple[str, str]:
    match = TAG_RE.match(tag)
    if not match:
        raise ValueError(f"tag {tag!r} is not <plugin>-v<major.minor.patch>")
    return match["plugin"], match["version"]


def changelog_section(plugin: str, version: str, root: Path = ROOT) -> str:
    """The body under ``## <plugin> <version> - <date>``, up to the next ``## ``."""
    text = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    head = re.compile(rf"^## {re.escape(plugin)} {re.escape(version)} - \d{{4}}-\d{{2}}-\d{{2}}$", re.M)
    match = head.search(text)
    if not match:
        raise ValueError(f"CHANGELOG.md has no '## {plugin} {version} - YYYY-MM-DD' entry")
    rest = text[match.end():]
    end = re.search(r"^## ", rest, re.M)
    return rest[: end.start() if end else len(rest)].strip()


def check(tag: str, root: Path = ROOT) -> None:
    plugin, version = parse_tag(tag)
    plugin_dir = root / "plugins" / plugin
    if not plugin_dir.is_dir():
        raise ValueError(f"no plugin named {plugin!r} under plugins/")
    for manifest in MANIFESTS:
        found = json.loads((plugin_dir / manifest).read_text(encoding="utf-8"))["version"]
        if found != version:
            raise ValueError(f"{plugin}/{manifest} is at {found}, tag says {version}")
    if not changelog_section(plugin, version, root):
        raise ValueError(f"CHANGELOG.md entry for {plugin} {version} is empty")


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[0] not in ("check", "notes"):
        print(__doc__, file=sys.stderr)
        return 2
    command, tag = argv
    try:
        if command == "check":
            check(tag)
            print(f"{tag}: manifests and CHANGELOG agree")
        else:
            print(changelog_section(*parse_tag(tag)))
    except (ValueError, OSError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
