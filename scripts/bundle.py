"""Build self-contained skill bundles: a skills hub that any MCP server can serve.

In this repository a skill cites files it shares with the plugin's other skills
(``../../references/safety.md``, ``../../scripts/check_radar.py``). An MCP
host loading a skill through the Skills extension may read only the files
inside that skill's own folder, so here each skill becomes a folder that holds
everything it reaches, with its citations rewritten to point inside it:

    dist/skills-hub/
    ├── index.json                        # {"themes": {plugin: [...]}, "plugins": {...}}
    └── chief-of-staff/
        └── radar/
            ├── SKILL.md                  # ../../references/x.md -> references/x.md
            ├── references/ …             # the shared folders it reaches, whole
            └── scripts/ …

A skill reaches a shared folder (or a root file such as ``plugin.json``) when
it or anything already vendored into it names that folder: as a relative path
(``../../templates/``) or, in a script, as a quoted name (``"templates"``).
Citations of a sibling skill (``../learn/SKILL.md``) stay as they are: in the
bundle that is another skill of the same plugin. The build fails on any
citation that would still leave the skill.

    python3 scripts/bundle.py [--out dist/skills-hub] [plugin ...]
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGINS = ROOT / "plugins"
SKIP_DIRS = {"skills", "evals", "__pycache__"}
# A relative citation: one or more ../ then a path, up to a delimiter.
CITATION = re.compile(r"(?<![\w./-])((?:\.\./)+[A-Za-z0-9_.][A-Za-z0-9_./-]*)")
DESCRIPTION = re.compile(r"^description:[ \t]*(.+)$", re.M)


class BundleError(Exception):
    pass


def _ignored(name: str) -> bool:
    return name.startswith(".") or name == "__pycache__"


def _text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


def _mentions(text: str, name: str) -> bool:
    """*text* names *name* as a relative path or a quoted path component."""
    word = re.escape(name)
    return bool(re.search(rf"(?:\.\./)+{word}(?![\w.-])", text)
                or re.search(rf"[\"']{word}[\"']", text))


def _copy(src: Path, dest: Path) -> None:
    if src.is_dir():
        shutil.copytree(src, dest, ignore=lambda d, names: [n for n in names if _ignored(n)])
    else:
        shutil.copy2(src, dest)


def shared_items(plugin: Path) -> dict[str, Path]:
    """What a skill may reach at the plugin's root: folders and files, no dotfiles."""
    return {p.name: p for p in sorted(plugin.iterdir())
            if not _ignored(p.name) and p.name not in SKIP_DIRS}


def bundle_skill(plugin: Path, skill: Path, dest: Path) -> list[str]:
    """Write *skill* as a self-contained folder at *dest*; the shared items vendored."""
    _copy(skill, dest)
    shared = shared_items(plugin)
    own = {p.name for p in dest.iterdir()}
    vendored: list[str] = []
    while True:
        texts = [t for f in sorted(dest.rglob("*")) if f.is_file() and (t := _text(f)) is not None]
        new = [name for name in shared if name not in vendored
               and any(_mentions(text, name) for text in texts)]
        if not new:
            break
        for name in new:
            if name in own:
                raise BundleError(f"{skill.name}: has its own {name!r}, which would hide the shared one")
            _copy(shared[name], dest / name)
            vendored.append(name)
    # The skill's own files cite the plugin root as ../../ ; inside the bundle it is ./
    for path in sorted(dest.rglob("*")):
        relative = path.relative_to(dest).parts
        if not path.is_file() or relative[0] in vendored or (text := _text(path)) is None:
            continue
        rewritten = text
        for name in vendored:
            rewritten = re.sub(rf"(?<![\w./-])\.\./\.\./(?={re.escape(name)}(?![\w.-]))", "", rewritten)
        if rewritten != text:
            path.write_text(rewritten, encoding="utf-8")
    return sorted(vendored)


def escaping_citations(bundle: Path, skill: str, siblings: set[str]) -> list[str]:
    """Citations in the bundled skill that don't land inside it (a sibling
    skill's SKILL.md from the skill's root excepted)."""
    root = (bundle / skill).resolve()
    bad = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or (text := _text(path)) is None:
            continue
        for cited in CITATION.findall(text):
            target = (path.parent / cited.rstrip(".,;:")).resolve()
            sibling = (path.parent == root and target.parent.parent == root.parent
                       and target.parent.name in siblings and target.name == "SKILL.md")
            if not sibling and root not in (target, *target.parents):
                bad.append(f"{path.relative_to(root)}: {cited}")
            elif not sibling and not target.exists():
                bad.append(f"{path.relative_to(root)}: {cited} (missing)")
    return bad


def build(out: Path, names: list[str] | None = None) -> dict:
    plugins = [PLUGINS / n for n in names] if names else sorted(
        p for p in PLUGINS.iterdir() if p.is_dir() and not _ignored(p.name))
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    index: dict = {"themes": {}, "plugins": {}}
    errors: list[str] = []
    for plugin in plugins:
        manifest = json.loads((plugin / "plugin.json").read_text(encoding="utf-8"))
        skills = sorted(p for p in (plugin / "skills").iterdir() if (p / "SKILL.md").is_file())
        entries = []
        for skill in skills:
            vendored = bundle_skill(plugin, skill, out / plugin.name / skill.name)
            match = DESCRIPTION.search((skill / "SKILL.md").read_text(encoding="utf-8"))
            entries.append({"name": skill.name, "description": match.group(1) if match else "",
                            "vendored": vendored})
        siblings = {s.name for s in skills}
        for skill in skills:
            errors += [f"{plugin.name}/{skill.name}/{e}"
                       for e in escaping_citations(out / plugin.name, skill.name, siblings)]
        index["themes"][plugin.name] = entries
        index["plugins"][plugin.name] = {"version": manifest["version"],
                                         "description": manifest.get("description", "")}
    if errors:
        raise BundleError("citations that leave their skill:\n  " + "\n  ".join(errors))
    (out / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n",
                                    encoding="utf-8")
    return index


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", type=Path, default=ROOT / "dist" / "skills-hub")
    parser.add_argument("plugins", nargs="*", help="plugin names (default: all)")
    args = parser.parse_args(argv)
    try:
        index = build(args.out, args.plugins or None)
    except BundleError as exc:
        print(f"bundle: {exc}", file=sys.stderr)
        return 1
    count = sum(len(entries) for entries in index["themes"].values())
    print(f"bundle: {count} skills from {len(index['plugins'])} plugin(s) in {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
