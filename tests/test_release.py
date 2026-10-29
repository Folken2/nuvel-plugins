"""The release helper: tags match manifests and every current version has a CHANGELOG entry."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import release  # noqa: E402

PLUGINS = sorted(p for p in (ROOT / "plugins").iterdir() if p.is_dir())


def _version(plugin: Path) -> str:
    return json.loads((plugin / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))["version"]


@pytest.mark.parametrize("plugin", PLUGINS, ids=lambda p: p.name)
def test_current_version_is_releasable(plugin: Path) -> None:
    release.check(f"{plugin.name}-v{_version(plugin)}")


@pytest.mark.parametrize("tag", ["v0.3.0", "chief-of-staff-0.3.0", "chief-of-staff-v0.3", "Chief-v1.0.0"])
def test_bad_tags_are_refused(tag: str) -> None:
    with pytest.raises(ValueError, match="not <plugin>-v"):
        release.parse_tag(tag)


def test_unknown_plugin_is_refused() -> None:
    with pytest.raises(ValueError, match="no plugin named"):
        release.check("no-such-plugin-v1.0.0")


def test_version_mismatch_is_refused() -> None:
    plugin = PLUGINS[0]
    with pytest.raises(ValueError, match="tag says 99.0.0"):
        release.check(f"{plugin.name}-v99.0.0")


def test_missing_changelog_entry_is_refused(tmp_path: Path) -> None:
    plugin = PLUGINS[0]
    shutil.copytree(plugin, tmp_path / "plugins" / plugin.name)
    (tmp_path / "CHANGELOG.md").write_text("# Changelog\n", encoding="utf-8")
    with pytest.raises(ValueError, match="no '## "):
        release.check(f"{plugin.name}-v{_version(plugin)}", tmp_path)


def test_notes_stop_at_the_next_entry(tmp_path: Path) -> None:
    (tmp_path / "CHANGELOG.md").write_text(
        "# Changelog\n\n## p 1.1.0 - 2026-10-29\n\nNew.\n\n## p 1.0.0 - 2026-10-01\n\nOld.\n",
        encoding="utf-8",
    )
    assert release.changelog_section("p", "1.1.0", tmp_path) == "New."
    assert release.changelog_section("p", "1.0.0", tmp_path) == "Old."
