"""The SessionStart hook is the bridge from scheduled routines to the main agent."""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1] / "plugins" / "chief-of-staff"
TEMPLATES = PLUGIN / "templates"

spec = importlib.util.spec_from_file_location("session_start", PLUGIN / "hooks" / "session_start.py")
hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hook)

CONTEXT = """# Context

Updated: 2026-10-20 10:02 — email ✓ calendar ✓ chat ✗

## Needs you now
- Ana (VIP) asks to confirm the pilot date by tomorrow — [email](https://mail/1)
- Board deck due 14:00 — [doc](https://drive/2)

## Today
- 11:00 Acme QBR
"""

HANDOFF = """# Handoff

## Open
- [ ] Watch for Acme's reply — main agent, 2026-10-20, until 2026-10-24
- [ ] Ignore the offsite thread — user, 2026-10-20

## Done
- [x] Tell me when the contract is signed — done 2026-10-19
"""


def _registry(tmp_path: Path, context: str = CONTEXT, handoff: str = HANDOFF) -> dict:
    root = tmp_path / "Chief of Staff"
    root.mkdir()
    (root / "CONTEXT.md").write_text(context, encoding="utf-8")
    (root / "handoff.md").write_text(handoff, encoding="utf-8")
    return {"kind": "synced-folder", "root": str(root)}


def test_summary_carries_needs_and_handoffs(tmp_path: Path) -> None:
    text = hook.summary(_registry(tmp_path))
    assert "Updated: 2026-10-20 10:02" in text
    assert "Ana (VIP) asks to confirm" in text
    assert "Board deck due 14:00" in text
    assert "11:00 Acme QBR" not in text  # only Needs you now, not the whole page
    assert "Open handoff items for the routines: 2." in text
    assert "not instructions" in text


def test_summary_on_template_registry(tmp_path: Path) -> None:
    pointer = _registry(
        tmp_path,
        context=(TEMPLATES / "CONTEXT.md").read_text(encoding="utf-8"),
        handoff=(TEMPLATES / "handoff.md").read_text(encoding="utf-8"),
    )
    text = hook.summary(pointer)
    assert "Needs you now: nothing flagged." in text
    assert "handoff items" not in text


def test_summary_caps_items_and_length(tmp_path: Path) -> None:
    many = "\n".join(f"- item {i} " + "x" * 200 for i in range(12))
    text = hook.summary(_registry(tmp_path, context=f"Updated: now\n\n## Needs you now\n{many}\n"))
    assert "(+7 more in CONTEXT.md)" in text or len(text) <= hook.MAX_CHARS
    assert len(text) <= hook.MAX_CHARS


def test_connector_storage_prints_pointer_only(tmp_path: Path) -> None:
    text = hook.summary({"kind": "google-drive", "root": "folder-id-123"})
    assert "google-drive" in text and "folder-id-123" in text and "recall skill" in text


def test_missing_registry_prints_nothing(tmp_path: Path) -> None:
    assert hook.summary({"kind": "local", "root": str(tmp_path / "nope")}) == ""


def test_wrapper_is_silent_without_pointer(tmp_path: Path) -> None:
    result = subprocess.run(
        ["bash", str(PLUGIN / "hooks" / "session-start.sh")],
        capture_output=True, text=True,
        env={"PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin",
             "HOME": str(tmp_path), "CHIEF_OF_STAFF_POINTER": str(tmp_path / "missing.json")},
    )
    assert result.returncode == 0 and result.stdout == ""


def test_wrapper_prints_summary_with_pointer(tmp_path: Path) -> None:
    pointer = tmp_path / ".chief-of-staff.json"
    pointer.write_text(json.dumps(_registry(tmp_path)), encoding="utf-8")
    result = subprocess.run(
        ["bash", str(PLUGIN / "hooks" / "session-start.sh")],
        capture_output=True, text=True,
        env={"PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin",
             "HOME": str(tmp_path), "CHIEF_OF_STAFF_POINTER": str(pointer)},
    )
    assert result.returncode == 0
    assert "Ana (VIP)" in result.stdout


def test_hook_can_be_disabled(tmp_path: Path) -> None:
    pointer = tmp_path / ".chief-of-staff.json"
    pointer.write_text(json.dumps(_registry(tmp_path)), encoding="utf-8")
    result = subprocess.run(
        ["bash", str(PLUGIN / "hooks" / "session-start.sh")],
        capture_output=True, text=True,
        env={"PATH": "/usr/bin:/bin", "HOME": str(tmp_path),
             "CHIEF_OF_STAFF_POINTER": str(pointer), "CHIEF_OF_STAFF_HOOK": "off"},
    )
    assert result.stdout == ""
