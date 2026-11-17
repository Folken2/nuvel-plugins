"""The task-ID checker against shared fixtures (also meant for the board)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins/chief-of-staff/scripts/check_task_ids.py"
FIXTURES = ROOT / "tests/fixtures/task-ids"
CASES = json.loads((FIXTURES / "cases.json").read_text(encoding="utf-8"))


def test_every_fixture_dir_has_a_case() -> None:
    dirs = {p.name for p in FIXTURES.iterdir() if p.is_dir()}
    assert dirs == set(CASES)


@pytest.mark.parametrize("name", sorted(CASES))
def test_case(name: str) -> None:
    case, folder = CASES[name], FIXTURES / name
    args = [sys.executable, str(SCRIPT)]
    if (folder / "previous.md").is_file():
        args += ["--previous", str(folder / "previous.md")]
    out = subprocess.run([*args, str(folder / "new.md")], capture_output=True, text=True)
    lines = out.stdout.splitlines()
    errors = [l for l in lines if l.startswith("error: ")]
    warnings = [l for l in lines if l.startswith("warning: ")]
    assert out.returncode == case["exit"], out.stdout
    for want in case["errors"]:
        assert any(want in l for l in errors), (want, errors)
    if not case["errors"]:
        assert not errors, errors
    for want in case["warnings"]:
        assert any(want in l for l in warnings), (want, warnings)
    if not case["warnings"]:
        assert not warnings, warnings
    for key, value in case["counts"].items():
        assert f"{key}: {value}" in lines, (key, lines)
    assert lines[-1] == ("result: ok" if case["exit"] == 0 else "result: failed")


def test_usage_error_exits_2(tmp_path: Path) -> None:
    out = subprocess.run([sys.executable, str(SCRIPT), str(tmp_path / "missing.md")], capture_output=True, text=True)
    assert out.returncode == 2
