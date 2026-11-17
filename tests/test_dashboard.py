"""The dashboard is always built the same way: template + settings from config."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
COS = ROOT / "plugins/chief-of-staff"
BUILD = COS / "scripts/build_dashboard.py"
TEMPLATE = COS / "templates/dashboard"
FIX = ROOT / "tests/fixtures/dashboard"
NODE = shutil.which("node")

EXPECTED_CAPS = {"mcp": {"servers": [
    {"server": "Google Drive", "tools": ["search_files", "read_file_content", "create_file"]},
    {"server": "Gmail", "tools": ["get_thread", "create_draft"]},
    {"server": "Google Calendar", "tools": ["list_events", "create_event"]},
]}}


def build(config: Path, tmp: Path, name: str = "page") -> tuple[int, str, Path, Path]:
    out, caps = tmp / f"{name}.html", tmp / f"{name}.json"
    res = subprocess.run([sys.executable, str(BUILD), "--config", str(config), "--out", str(out), "--manifest", str(caps)],
                         capture_output=True, text=True)
    return res.returncode, res.stdout, out, caps


def settings_of(page: str) -> dict:
    m = re.search(r'<script type="application/json" id="cos-settings">(.*?)</script>', page, flags=re.DOTALL)
    assert m
    return json.loads(m.group(1))


def test_google_build(tmp_path: Path) -> None:
    code, out, page, caps = build(FIX / "config-google.md", tmp_path)
    assert code == 0, out
    assert json.loads(caps.read_text()) == EXPECTED_CAPS
    assert f"capabilities: {json.dumps(EXPECTED_CAPS, separators=(',', ':'))}" in out
    html = page.read_text()
    version = json.loads((COS / ".claude-plugin/plugin.json").read_text())["version"]
    s = settings_of(html)
    assert s == {
        "template": version,
        "owner": {"name": "Ana Ferrer", "language": "ca", "timezone": "Europe/Madrid", "working_hours": "09:00-19:00 Mon-Fri"},
        "storage": {"kind": "google-drive", "root": "1RootFolderExample000000000", "runs": "1RunsFolderExample000000",
                    "handoff": "1HandoffFolderExample000"},
        "email": "gmail", "calendar": "google",
    }
    assert "@@" not in html and html.startswith("<title>Chief of Staff</title>")
    assert f'<meta name="cos-dashboard" content="{version}">' in html
    for script in re.findall(r"<script[^>]*>(.*?)</script>", html, flags=re.DOTALL):
        assert "</script" not in script.lower()
    assert "alert(1)" not in html, "config free text (priorities) never reaches the page"


def test_build_is_deterministic(tmp_path: Path) -> None:
    a = build(FIX / "config-google.md", tmp_path, "a")[2].read_bytes()
    b = build(FIX / "config-google.md", tmp_path, "b")[2].read_bytes()
    assert a == b


def test_page_holds_only_the_template_and_settings(tmp_path: Path) -> None:
    html = build(FIX / "config-google.md", tmp_path)[2].read_text()
    for part in ("app.css", "strings.js", "radar.js", "app.js"):
        assert (TEMPLATE / part).read_text().strip("\n") in html, part


def test_microsoft_is_refused_with_exit_3(tmp_path: Path) -> None:
    code, out, page, _ = build(FIX / "config-microsoft.md", tmp_path)
    assert code == 3 and "result: unsupported" in out and not page.exists()


def test_incomplete_config_lists_each_problem(tmp_path: Path) -> None:
    code, out, page, _ = build(FIX / "config-incomplete.md", tmp_path)
    assert code == 1 and not page.exists()
    for want in ("owner.timezone", "no runs=", "no handoff="):
        assert want in out, want


def test_sources_decide_the_connectors(tmp_path: Path) -> None:
    cfg = tmp_path / "config.md"
    cfg.write_text((FIX / "config-google.md").read_text()
                   .replace("- email: Gmail connector", "- email: Outlook")
                   .replace("- calendar: Google Calendar connector", "- calendar: Outlook calendar"))
    code, _, page, caps = build(cfg, tmp_path)
    assert code == 0
    assert [s["server"] for s in json.loads(caps.read_text())["mcp"]["servers"]] == ["Google Drive"]
    s = settings_of(page.read_text())
    assert (s["email"], s["calendar"]) == ("other", "other")


def test_page_calls_only_declared_tools() -> None:
    app = (TEMPLATE / "app.js").read_text()
    servers = {"drive": "Google Drive", "mail": "Gmail", "cal": "Google Calendar"}
    declared = {(s["server"], t) for s in EXPECTED_CAPS["mcp"]["servers"] for t in s["tools"]}
    called = {(servers[k], t) for k, t in re.findall(r'(?:call|callTool)\(SRV\.(\w+), "(\w+)"', app)}
    assert called == declared, called ^ declared
    # every connector call names its server and tool literally: nothing computed, nothing else reachable
    sites = re.findall(r"\bcall(?:Tool)?\(", app)
    literal = re.findall(r'\bcall(?:Tool)?\(SRV\.\w+, "\w+"', app)
    assert len(sites) - 2 == len(literal), "only the call() helper itself (definition + forwarding) is not literal"


def test_page_renders_text_never_html() -> None:
    app = (TEMPLATE / "app.js").read_text()
    assert app.count("innerHTML") == 1 and "s.innerHTML = path" in app  # only the fixed SVG icons
    assert "safeUrl" in app and "^https:" in app


def test_dashboard_contract_names_every_tool() -> None:
    doc = (COS / "references/dashboard.md").read_text()
    for server in EXPECTED_CAPS["mcp"]["servers"]:
        assert f"`{server['server']}`" in doc
        for tool in server["tools"]:
            assert f"`{tool}`" in doc, tool
    assert "never written by hand" in doc
    safety = (COS / "references/safety.md").read_text()
    assert "The dashboard is the one exception, and only on the user's click" in safety


def test_setup_runs_the_dashboard_skill() -> None:
    setup = (COS / "skills/setup/SKILL.md").read_text()
    assert "## 7. Dashboard" in setup and "`dashboard` skill" in setup
    skill = (COS / "skills/dashboard/SKILL.md").read_text()
    assert "`python3 ../../scripts/build_dashboard.py --config" in skill
    assert "Never write the page yourself" in skill and "**unchanged**" in skill


def node(script: str) -> str:
    res = subprocess.run([NODE, "-e", script], capture_output=True, text=True, cwd=ROOT)
    assert res.returncode == 0, res.stderr
    return res.stdout


@pytest.mark.skipif(not NODE, reason="node not installed")
def test_parser_reads_the_radar_contract() -> None:
    out = json.loads(node(
        'const R=require("./plugins/chief-of-staff/templates/dashboard/radar.js");'
        'const t=require("fs").readFileSync("tests/fixtures/dashboard/radar.md","utf8");'
        'console.log(JSON.stringify(R.parseRadar(t)));'))
    todo = {x["id"]: x for x in out["todo"]}
    assert list(todo) == ["T-12", "T-14", "T-15", "T-16"]
    lumen = todo["T-12"]  # in Needs you now and I owe: one task, details merged
    assert (lumen["kind"], lumen["who"], lumen["due"], lumen["since"]) == ("needs", "Joan Serra (Lumen)", "2026-11-17", "2026-11-13")
    assert lumen["threadId"] == format(1880414779648821934, "x")
    assert (todo["T-15"]["kind"], todo["T-15"]["who"], todo["T-15"]["due"]) == ("decide", "Retail Summit", "2026-11-20")
    dele = {x["id"]: x for x in out["dele"]}
    assert dele["T-9"]["since"] == "2026-10-29" and dele["T-9"]["due"] == "2026-11-15"  # "des del <date>"
    assert dele["T-11"]["threadId"] is None  # thread-a links have no convertible id
    closed = {x["id"]: (x["reason"], x["closedOn"]) for x in out["closed"]}
    assert closed == {"T-7": ("done", "2026-11-16"), "T-3": ("expired", "2026-11-05")}
    assert {(i["topic"], i["id"]) for i in out["info"]} == {("finance", "T-13"), ("web", None)}
    assert out["owner"] == "Ana Ferrer" and out["at"] == "2026-11-17T11:00"


@pytest.mark.skipif(not NODE, reason="node not installed")
def test_parser_handoff_matches_the_registry_contract() -> None:
    text = json.loads(node(
        'const R=require("./plugins/chief-of-staff/templates/dashboard/radar.js");'
        'console.log(JSON.stringify(R.handoff("T-42","not mine","2026-11-17 14:05")));'))
    assert text == ("# Handoff · 2026-11-17 14:05\n\n- instruction: close — not mine\n- task: T-42\n"
                    "- from: dashboard (on behalf of the user)\n")
    layout = (COS / "references/registry-layout.md").read_text()
    assert "close — not mine" in layout and "dashboard (on behalf of\nthe user)" in layout


@pytest.mark.skipif(not NODE, reason="node not installed")
def test_parser_picks_newest_by_name() -> None:
    out = node(
        'const R=require("./plugins/chief-of-staff/templates/dashboard/radar.js");'
        'const f=[{title:"2026-11-17 0900 radar"},{title:"2026-11-17 1100 radar"},{title:"2026-11-17 1200 prep radar-sync"},'
        '{title:"2026-11-17 0730 brief"}];console.log(R.newest(f,"radar").title+"|"+R.newest(f,"brief").title);')
    assert out.strip() == "2026-11-17 1100 radar|2026-11-17 0730 brief"


@pytest.mark.skipif(not NODE, reason="node not installed")
def test_parser_agrees_with_checker_on_task_ids() -> None:
    """The board and check_task_ids.py read the same IDs from every task-ID fixture."""
    sys.path.insert(0, str(COS / "scripts"))
    import check_task_ids  # noqa: E402

    for new in sorted((ROOT / "tests/fixtures/task-ids").glob("*/new.md")):
        py = set(check_task_ids.parse(new.read_text(), "new").tasks)
        js = json.loads(node(
            'const R=require("./plugins/chief-of-staff/templates/dashboard/radar.js");'
            f'const m=R.parseRadar(require("fs").readFileSync({json.dumps(str(new))},"utf8"));'
            'console.log(JSON.stringify([...m.todo,...m.dele,...m.closed,...m.info].map(x=>x.id).filter(Boolean)));'))
        assert {int(i[2:]) for i in js} <= py, new.parent.name


def test_google_doc_export_of_config(tmp_path: Path) -> None:
    """Configs read back from Google Docs escape underscores (`working\\_hours`, `1ow\\_DSN…`) and indent bullets."""
    code, out, page, _ = build(FIX / "config-google-doc.md", tmp_path)
    assert code == 0, out
    s = settings_of(page.read_text())
    assert s["storage"]["runs"] == "1Runs_Folder_Example0000"
    assert s["owner"]["working_hours"] == "09:00-19:00 Mon-Fri"
    assert (s["email"], s["calendar"]) == ("gmail", "google")


def test_closes_from_earlier_are_never_silent() -> None:
    """A close saved on a later visit is shown while pending and announced when written."""
    app = (TEMPLATE / "app.js").read_text()
    assert "writeClose(id, true)" in app and "announceResumed(id)" in app
    assert 'notice("calm", t("pendingT")' in app and 't("closing") + "…"' in app
    strings = (TEMPLATE / "strings.js").read_text()
    data = json.loads(strings.split("var COS_STRINGS = ", 1)[1].rstrip().rstrip(";"))
    for lang in ("en", "ca", "es"):
        for key in ("resumedOne", "resumedMany", "pendingT", "pendingP", "closing"):
            assert data["S"][lang].get(key), (lang, key)
