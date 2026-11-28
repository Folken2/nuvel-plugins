"""scripts/bundle.py: every skill as a self-contained folder (a skills hub).

A host serving skills through the MCP Skills extension may read only files
inside a skill's own folder, so a bundled skill must reach everything it cites
without leaving it, and must otherwise be the skill as written.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import bundle  # noqa: E402

COS = ROOT / "plugins/chief-of-staff"
SKILLS = sorted(p.name for p in (COS / "skills").iterdir() if (p / "SKILL.md").is_file())


@pytest.fixture(scope="module")
def hub(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("bundle") / "skills-hub"
    bundle.build(out)
    return out


def test_the_index_lists_every_skill_under_its_plugin(hub: Path) -> None:
    index = json.loads((hub / "index.json").read_text())
    assert [e["name"] for e in index["themes"]["chief-of-staff"]] == SKILLS
    version = json.loads((COS / "plugin.json").read_text())["version"]
    assert index["plugins"]["chief-of-staff"]["version"] == version
    for entry in index["themes"]["chief-of-staff"]:
        assert 50 <= len(entry["description"]) <= 1024


@pytest.mark.parametrize("skill", SKILLS)
def test_no_citation_leaves_the_skill(hub: Path, skill: str) -> None:
    assert bundle.escaping_citations(hub / "chief-of-staff", skill, set(SKILLS)) == []
    assert "../../" not in (hub / "chief-of-staff" / skill / "SKILL.md").read_text()


@pytest.mark.parametrize("skill", SKILLS)
def test_the_skill_is_unchanged_but_for_its_paths(hub: Path, skill: str) -> None:
    source = (COS / "skills" / skill / "SKILL.md").read_text()
    bundled = (hub / "chief-of-staff" / skill / "SKILL.md").read_text()
    assert bundled == re.sub(r"\.\./\.\./(?=(references|templates|scripts|assets|plugin\.json))",
                             "", source)
    assert bundled.split("\n---\n", 1)[0] == source.split("\n---\n", 1)[0]  # frontmatter as is


@pytest.mark.parametrize("skill", SKILLS)
def test_vendored_files_are_byte_for_byte_copies(hub: Path, skill: str) -> None:
    root = hub / "chief-of-staff" / skill
    entry = next(e for e in json.loads((hub / "index.json").read_text())["themes"]["chief-of-staff"]
                 if e["name"] == skill)
    for name in entry["vendored"]:
        for copy in [root / name] if (root / name).is_file() else (root / name).rglob("*"):
            if copy.is_file():
                assert copy.read_bytes() == (COS / copy.relative_to(root)).read_bytes()


def test_nothing_hidden_or_compiled_is_bundled(hub: Path) -> None:
    names = {p.name for p in hub.rglob("*")}
    assert not [n for n in names if n.startswith(".") or n == "__pycache__" or n.endswith(".pyc")]
    assert not list(hub.rglob("evals"))


def test_the_bundled_dashboard_builder_finds_its_template(hub: Path, tmp_path: Path) -> None:
    """build_dashboard.py locates templates/ and plugin.json from its own folder:
    from inside the bundle it must build the same page as from the plugin."""
    config = ROOT / "tests/fixtures/dashboard/config-google.md"
    pages = []
    for where in (COS, hub / "chief-of-staff" / "dashboard"):
        out = tmp_path / f"{len(pages)}.html"
        run = subprocess.run([sys.executable, str(where / "scripts/build_dashboard.py"),
                              "--config", str(config), "--out", str(out),
                              "--manifest", str(tmp_path / f"{len(pages)}.json")],
                             capture_output=True, text=True)
        assert run.returncode == 0, run.stderr
        pages.append(out.read_text())
    assert pages[0] == pages[1]


def test_a_citation_that_leaves_the_skill_fails_the_build(tmp_path: Path, monkeypatch) -> None:
    plugin = tmp_path / "plugins" / "demo"
    (plugin / "skills" / "one").mkdir(parents=True)
    (plugin / "plugin.json").write_text(json.dumps({"name": "demo", "version": "1.0.0"}))
    (plugin / "skills" / "one" / "SKILL.md").write_text(
        "---\nname: one\ndescription: x\n---\nSee `../../../outside.md`.\n")
    monkeypatch.setattr(bundle, "PLUGINS", tmp_path / "plugins")
    with pytest.raises(bundle.BundleError, match="outside.md"):
        bundle.build(tmp_path / "out")


def test_the_cli_writes_the_hub(tmp_path: Path) -> None:
    run = subprocess.run([sys.executable, str(ROOT / "scripts/bundle.py"), "--out",
                          str(tmp_path / "hub")], capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    assert f"{len(SKILLS)} skills from 1 plugin(s)" in run.stdout
    assert (tmp_path / "hub" / "index.json").is_file()
