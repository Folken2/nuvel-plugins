"""Structural checks for every plugin in this marketplace.

Each plugin ships one skills tree to several hosts (Claude, Codex, nuvel's
agent-plugins loader), so the manifests must agree with each other and every
path a skill cites must exist on disk.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PLUGINS = sorted(p for p in (ROOT / "plugins").iterdir() if p.is_dir())
MANIFESTS = (".claude-plugin/plugin.json", ".codex-plugin/plugin.json", "plugin.json")
AGENT_PLUGINS_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
NAME_RE = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$")
CITED_PATH_RE = re.compile(r"`((?:\.\./)+[^`\s]+)`")


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
    assert match, f"{path} has no frontmatter"
    fields = {}
    for line in match.group(1).splitlines():
        key, _, value = line.partition(":")
        if value:
            fields[key.strip()] = value.strip()
    return fields


def _skills(plugin: Path) -> list[Path]:
    return sorted(p for p in (plugin / "skills").iterdir() if (p / "SKILL.md").is_file())


SKILLS = [s for p in PLUGINS for s in _skills(p)]


@pytest.mark.parametrize("plugin", PLUGINS, ids=lambda p: p.name)
def test_manifests_agree(plugin: Path) -> None:
    manifests = {m: _json(plugin / m) for m in MANIFESTS}
    names = {m: d["name"] for m, d in manifests.items()}
    versions = {m: d["version"] for m, d in manifests.items()}
    assert set(names.values()) == {plugin.name}, names
    assert len(set(versions.values())) == 1, versions
    assert NAME_RE.match(plugin.name)
    assert manifests["plugin.json"]["$schema"] == AGENT_PLUGINS_SCHEMA


@pytest.mark.parametrize("plugin", PLUGINS, ids=lambda p: p.name)
def test_codex_interface(plugin: Path) -> None:
    interface = _json(plugin / ".codex-plugin/plugin.json")["interface"]
    for key in ("displayName", "shortDescription", "longDescription", "category", "defaultPrompt"):
        assert interface.get(key), f"missing interface.{key}"


def test_marketplaces_list_every_plugin() -> None:
    claude = _json(ROOT / ".claude-plugin/marketplace.json")
    codex = _json(ROOT / ".agents/plugins/marketplace.json")
    expected = {p.name for p in PLUGINS}
    assert {p["name"] for p in claude["plugins"]} == expected
    assert {p["name"] for p in codex["plugins"]} == expected
    for entry in claude["plugins"]:
        assert (ROOT / entry["source"] / ".claude-plugin/plugin.json").is_file()
    for entry in codex["plugins"]:
        assert (ROOT / entry["source"]["path"] / ".codex-plugin/plugin.json").is_file()


@pytest.mark.parametrize("skill", SKILLS, ids=lambda s: f"{s.parents[1].name}:{s.name}")
def test_skill_frontmatter(skill: Path) -> None:
    meta = _frontmatter(skill / "SKILL.md")
    assert meta.get("name") == skill.name
    assert 50 <= len(meta.get("description", "")) <= 1024
    assert (skill / "agents/openai.yaml").is_file(), "Codex UI metadata missing"


@pytest.mark.parametrize("skill", SKILLS, ids=lambda s: f"{s.parents[1].name}:{s.name}")
def test_cited_paths_exist(skill: Path) -> None:
    text = (skill / "SKILL.md").read_text(encoding="utf-8")
    cited = CITED_PATH_RE.findall(text)
    missing = [c for c in cited if not (skill / c).resolve().exists()]
    assert not missing, f"{skill.name} cites missing paths: {missing}"


@pytest.mark.parametrize("plugin", PLUGINS, ids=lambda p: p.name)
def test_references_cited_by_name_exist(plugin: Path) -> None:
    """Reference docs point at each other by bare file name — keep them real."""
    refs = plugin / "references"
    if not refs.is_dir():
        pytest.skip("no references/")
    names = {p.name for p in refs.iterdir()}
    for doc in refs.glob("*.md"):
        for cited in re.findall(r"`([a-z-]+\.md)`", doc.read_text(encoding="utf-8")):
            if cited in {"README.md", "CONTEXT.md", "config.md", "loops.md", "handoff.md"}:
                continue  # registry files, not reference docs
            assert cited in names, f"{doc.name} cites missing reference {cited}"


@pytest.mark.parametrize("plugin", PLUGINS, ids=lambda p: p.name)
def test_no_stray_skill_dirs(plugin: Path) -> None:
    """Every folder under skills/ must be a real skill — hosts list them all."""
    stray = [p.name for p in (plugin / "skills").iterdir() if p.is_dir() and not (p / "SKILL.md").is_file()]
    assert not stray, f"folders without SKILL.md: {stray}"
