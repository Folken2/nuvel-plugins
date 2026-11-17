"""The whole-radar checker against shared fixtures: one sample per rule it enforces."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins/chief-of-staff/scripts/check_radar.py"
FIXTURES = ROOT / "tests/fixtures/radar"
CASES = json.loads((FIXTURES / "cases.json").read_text(encoding="utf-8"))


def test_every_fixture_dir_has_a_case() -> None:
    assert {p.name for p in FIXTURES.iterdir() if p.is_dir()} == set(CASES)


@pytest.mark.parametrize("name", sorted(CASES))
def test_case(name: str) -> None:
    case, folder = CASES[name], FIXTURES / name
    out = subprocess.run([sys.executable, str(SCRIPT), "--previous", str(folder / "previous.md"), str(folder / "new.md")],
                         capture_output=True, text=True)
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
    assert lines[-1] == ("result: ok" if case["exit"] == 0 else "result: failed")
    assert any(l.startswith("id_errors: ") for l in lines)


def test_task_id_fixtures_still_fail_the_same_way() -> None:
    """check_radar runs every task-ID rule: each task-ID error fixture is still an error here."""
    cases = json.loads((ROOT / "tests/fixtures/task-ids/cases.json").read_text(encoding="utf-8"))
    for name, case in cases.items():
        if case["exit"] == 0 or not case["errors"]:
            continue
        folder = ROOT / "tests/fixtures/task-ids" / name
        args = [sys.executable, str(SCRIPT)]
        if (folder / "previous.md").is_file():
            args += ["--previous", str(folder / "previous.md")]
        out = subprocess.run([*args, str(folder / "new.md")], capture_output=True, text=True)
        assert out.returncode == 1, name
        for want in case["errors"]:
            assert want in out.stdout, (name, want)


def test_radar_skill_runs_the_whole_radar_check() -> None:
    radar = (ROOT / "plugins/chief-of-staff/skills/radar/SKILL.md").read_text(encoding="utf-8")
    assert "`python3 ../../scripts/check_radar.py --previous" in radar
