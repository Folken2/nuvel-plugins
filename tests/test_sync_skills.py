"""The agent-builder plugin republishes skills from the nuvel repo; keep the copy honest."""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/agent-builder"
OWN_SKILLS = {"build-agent"}

_spec = importlib.util.spec_from_file_location("sync_skills", ROOT / "scripts/sync_skills.py")
sync_skills = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sync_skills)


def _source() -> dict:
    return json.loads((PLUGIN / "source.json").read_text(encoding="utf-8"))


def test_source_pins_a_commit() -> None:
    assert re.fullmatch(r"[0-9a-f]{40}", _source()["commit"])


def test_every_skill_is_synced_or_owned() -> None:
    on_disk = {p.name for p in (PLUGIN / "skills").iterdir() if p.is_dir()}
    assert on_disk == set(_source()["skills"]) | OWN_SKILLS


def _fake_checkout(tmp_path: Path) -> Path:
    """A nuvel-shaped tree built from the plugin's own copy."""
    for name, rel in _source()["skills"].items():
        shutil.copytree(PLUGIN / "skills" / name, tmp_path / rel, ignore=shutil.ignore_patterns("agents"))
    return tmp_path


def test_drift_none_when_identical(tmp_path: Path) -> None:
    assert sync_skills.drift(PLUGIN, _fake_checkout(tmp_path)) == []


def test_drift_reports_changed_added_and_removed(tmp_path: Path) -> None:
    source = _fake_checkout(tmp_path)
    rel = Path(_source()["skills"]["adk-tool-creation"])
    (source / rel / "SKILL.md").write_text("changed", encoding="utf-8")
    (source / rel / "references/new.md").write_text("new", encoding="utf-8")
    (source / rel / "references/tool-patterns.md").unlink()
    problems = sync_skills.drift(PLUGIN, source)
    assert "adk-tool-creation: differs SKILL.md" in problems
    assert "adk-tool-creation: missing references/new.md" in problems
    assert "adk-tool-creation: extra references/tool-patterns.md" in problems
