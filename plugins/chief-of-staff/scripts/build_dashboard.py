#!/usr/bin/env python3
"""Build the chief-of-staff dashboard page from the newest `config` document.

    python3 build_dashboard.py --config CONFIG --out dashboard.html [--manifest capabilities.json]

CONFIG is the text of the registry's newest `config` document (Markdown, or the
plain text a storage connector returns for a Google Doc). The page is always the
same template (templates/dashboard/) with one settings block filled in from the
config: no task, email or calendar data is ever written into it; the page reads
those live through the viewer's own connectors. Same config in, same page out.

Prints `version: ...`, `capabilities: {...}` (pass it unchanged to the Artifact
publish) and `result: ok`. Exit codes: 0 ok, 1 the config is missing something
(each problem printed as `error: ...`), 2 bad usage, 3 storage not supported by
the dashboard yet (Microsoft 365). Standard library only; Python 3.8+.
Contract: references/dashboard.md.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
TEMPLATE = PLUGIN / "templates" / "dashboard"
LANGUAGES = ("en", "ca", "es")  # UI strings; any other owner.language shows English UI

# Exact upstream tool names the page calls. Microsoft 365: fill in once the names are known.
GOOGLE = {
    "drive": ("Google Drive", ["search_files", "read_file_content", "create_file"]),
    "mail": ("Gmail", ["get_thread", "create_draft"]),
    "calendar": ("Google Calendar", ["list_events", "create_event"]),
}
MICROSOFT = None

BULLET_RE = re.compile(r"^\s*[-*•]\s+([A-Za-z_.]+):\s*(.*?)\s*$")
HEADING_RE = re.compile(r"^\s*#{1,6}\s*(.+?)\s*$")
FOLDER_ID_RE = re.compile(r"^[A-Za-z0-9_-]{10,}$")
MD_ESCAPE_RE = re.compile(r"\\([\\`*_{}\[\]()#+\-.!<>|])")  # Google Docs exports `working\_hours`, `1ow\_DSN…`


def plugin_version() -> str:
    return json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]


def parse_config(text: str) -> tuple[dict[str, str], dict[str, str]]:
    """Top-level `- key: value` bullets, plus the `## Sources` bullets."""
    keys: dict[str, str] = {}
    sources: dict[str, str] = {}
    section = ""
    for line in MD_ESCAPE_RE.sub(r"\1", text).splitlines():
        heading = HEADING_RE.match(line)
        if heading and not BULLET_RE.match(line):
            section = heading.group(1).strip().lower()
            continue
        m = BULLET_RE.match(line)
        if not m:
            continue
        key, value = m.group(1), m.group(2)
        if section == "sources":
            sources[key.lower()] = value
        elif section in ("", "chief of staff configuration"):
            keys.setdefault(key, value)
    return keys, sources


def settings_from(text: str) -> tuple[dict, list[str]]:
    keys, sources = parse_config(text)
    errors: list[str] = []
    folders = dict(
        part.strip().split("=", 1) for part in keys.get("storage.folders", "").split(",") if "=" in part
    )
    for name in ("owner.timezone", "storage.kind", "storage.root"):
        if not keys.get(name):
            errors.append(f"config has no '- {name}: ...'")
    for name in ("runs", "handoff"):
        if not folders.get(name):
            errors.append(f"storage.folders has no {name}=<folder id>")
        elif not FOLDER_ID_RE.match(folders[name]):
            errors.append(f"storage.folders {name} is not a folder id: {folders[name]!r}")
    if keys.get("paused", "false").lower() == "true":
        errors.append("the chief of staff is paused (paused: true): resume it before building the dashboard")
    language = (keys.get("owner.language") or "en").split("-")[0].lower()
    email = sources.get("email", "").lower()
    calendar = sources.get("calendar", "").lower()
    settings = {
        "template": plugin_version(),
        "owner": {
            "name": keys.get("owner.name", ""),
            "language": language if language in LANGUAGES else "en",
            "timezone": keys.get("owner.timezone", ""),
            "working_hours": keys.get("owner.working_hours", "09:00-19:00 Mon-Fri"),
        },
        "storage": {
            "kind": keys.get("storage.kind", ""),
            "root": keys.get("storage.root", ""),
            "runs": folders.get("runs", ""),
            "handoff": folders.get("handoff", ""),
            "lessons": folders.get("lessons", "") if FOLDER_ID_RE.match(folders.get("lessons", "")) else "",
        },
        "email": "gmail" if "gmail" in email else ("other" if email else "none"),
        "calendar": "google" if "google" in calendar else ("other" if calendar else "none"),
    }
    return settings, errors


def capabilities(settings: dict) -> dict:
    servers = [GOOGLE["drive"]]
    if settings["email"] == "gmail":
        servers.append(GOOGLE["mail"])
    if settings["calendar"] == "google":
        servers.append(GOOGLE["calendar"])
    return {"mcp": {"servers": [{"server": s, "tools": list(tools)} for s, tools in servers]}}


def render(settings: dict) -> str:
    def part(name: str) -> str:
        return (TEMPLATE / name).read_text(encoding="utf-8").strip("\n")

    blob = json.dumps(settings, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    blob = blob.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    page = part("index.html")
    for token, value in (
        ("@@VERSION@@", settings["template"]),
        ("@@CSS@@", part("app.css")),
        ("@@SETTINGS@@", blob),
        ("@@STRINGS@@", part("strings.js")),
        ("@@RADAR@@", part("radar.js")),
        ("@@APP@@", part("app.js")),
    ):
        assert page.count(token) == 1, token
        page = page.replace(token, value)
    for script in re.findall(r"<script[^>]*>(.*?)</script>", page, flags=re.DOTALL):
        assert "</script" not in script.lower()
    return page + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--config", type=Path, required=True, help="text of the newest config document")
    parser.add_argument("--out", type=Path, required=True, help="where to write the page")
    parser.add_argument("--manifest", type=Path, help="also write the capabilities JSON here")
    args = parser.parse_args(argv)
    try:
        text = args.config.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    settings, errors = settings_from(text)
    kind = settings["storage"]["kind"]
    if kind and kind != "google-drive":
        if re.search(r"onedrive|sharepoint|microsoft", kind) and MICROSOFT is None:
            print(f"unsupported: storage.kind {kind} — the dashboard supports Google Drive only for now")
            print("result: unsupported")
            return 3
        errors.append(f"storage.kind {kind!r} has no dashboard (local folders can't be read from a page)")
    if errors:
        for line in errors:
            print(f"error: {line}")
        print("result: failed")
        return 1
    caps = capabilities(settings)
    args.out.write_text(render(settings), encoding="utf-8")
    if args.manifest:
        args.manifest.write_text(json.dumps(caps, indent=2) + "\n", encoding="utf-8")
    print(f"version: {settings['template']}")
    print(f"capabilities: {json.dumps(caps, separators=(',', ':'))}")
    print("result: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
