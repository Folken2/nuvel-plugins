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
COS = ROOT / "plugins/chief-of-staff"
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
            if cited in {"README.md"}:
                continue  # the registry README, not a reference doc
            assert cited in names, f"{doc.name} cites missing reference {cited}"


@pytest.mark.parametrize("plugin", PLUGINS, ids=lambda p: p.name)
def test_no_stray_skill_dirs(plugin: Path) -> None:
    """Every folder under skills/ must be a real skill — hosts list them all."""
    stray = [p.name for p in (plugin / "skills").iterdir() if p.is_dir() and not (p / "SKILL.md").is_file()]
    assert not stray, f"folders without SKILL.md: {stray}"


def test_sources_lists_microsoft_first() -> None:
    text = (COS / "references/sources.md").read_text(encoding="utf-8")
    for kind in ("`email`", "`calendar`", "`chat`", "`docs`"):
        row = next(l for l in text.splitlines() if l.startswith(f"| {kind}"))
        assert "Microsoft 365" in row, kind
        if "Google" in row:
            assert row.index("Microsoft 365") < row.index("Google"), kind


def test_composio_not_in_user_flow() -> None:
    for path in [*(COS / "skills").glob("*/SKILL.md"), *(COS / "references").glob("*.md")]:
        text = path.read_text(encoding="utf-8")
        hits = [l for l in text.splitlines() if "omposio" in l and "builder" not in l.lower()]
        assert not hits, f"{path.name}: {hits}"


def test_microsoft_sections_marked_unverified() -> None:
    for name in ("sources.md", "storage.md", "registry-layout.md"):
        text = (COS / "references" / name).read_text(encoding="utf-8")
        assert "**Unverified (no tenant yet)**" in text, name


JARGON = ("MCP", "cron", "scope", "OAuth", "Entra", "API", "token", "folder ID", "connector ID", "JSON")


def _section(text: str, heading: str) -> str:
    start = text.index(heading)
    nxt = text.find("\n## ", start + len(heading))
    return text[start: nxt if nxt != -1 else None]


def test_setup_asks_at_most_six_questions() -> None:
    text = (COS / "skills/setup/SKILL.md").read_text(encoding="utf-8")
    questions = re.findall(r"^\d+\. ", _section(text, "## 2. Questions"), flags=re.M)
    assert 1 <= len(questions) <= 6


def test_setup_user_phrases_have_no_jargon() -> None:
    text = (COS / "skills/setup/SKILL.md").read_text(encoding="utf-8")
    quoted = [l for l in text.splitlines() if l.lstrip().startswith(">")]
    assert quoted, "setup must show user-facing phrases as blockquotes"
    bad = [l for l in quoted for w in JARGON if re.search(rf"\b{re.escape(w)}\b", l)]
    assert not bad, bad


def test_setup_read_only_storage_stops_without_fallback() -> None:
    sec = _section((COS / "skills/setup/SKILL.md").read_text(encoding="utf-8"), "## Read-only storage")
    assert "continúa" in sec and "never" in sec.lower() and "elsewhere" in sec.lower()


def test_project_instructions_template() -> None:
    text = (COS / "templates/project-instructions.md").read_text(encoding="utf-8")
    for token in ("{{registry}}", "{{owner_name}}", "{{language}}", "recall", "read-only"):
        assert token in text, token


ID_RE = re.compile(r"^[a-z0-9][a-z0-9_.:-]{0,79}$")


@pytest.mark.parametrize("skill", SKILLS, ids=lambda s: s.name)
def test_trace_catalog(skill: Path) -> None:
    cat = _json(skill / "trace-steps.json")
    assert cat["skill"] == skill.name
    for key in ("steps", "counts", "routing"):
        assert all(ID_RE.match(x) for x in cat[key]), key
    assert all(s.startswith(f"{skill.name}.") for s in cat["steps"])
    text = (skill / "SKILL.md").read_text(encoding="utf-8")
    cited = set(re.findall(rf"`({re.escape(skill.name)}\.[a-z0-9_.:-]+)`", text))
    assert cited and cited <= set(cat["steps"]), cited - set(cat["steps"])
    assert "## Trace" in text and "telemetry.md" in text


def test_trace_failure_never_fails_run() -> None:
    text = (COS / "references/telemetry.md").read_text(encoding="utf-8")
    assert "trace: not sent" in text and "never" in text.lower()


def test_trace_docs_match_schema_types() -> None:
    tele = (COS / "references/telemetry.md").read_text(encoding="utf-8")
    assert not re.search(r"injection_suspected\W+bool", tele)
    outcomes = {"success", "partial", "failure", "blocked", "skipped"}
    for name in ("references/telemetry.md", "references/registry-layout.md"):
        text = (COS / name).read_text(encoding="utf-8")
        for m in re.finditer(r"^- outcome: (\w+)", text, flags=re.MULTILINE):
            assert m.group(1) in outcomes, (name, m.group(1))


def test_recipe_categories() -> None:
    cats = re.findall(r"^- `([a-z0-9-]+)`", (COS / "references/recipe-categories.md").read_text(encoding="utf-8"), flags=re.M)
    assert 15 <= len(cats) <= 30 and "other" in cats and len(set(cats)) == len(cats)


def test_learn_contract() -> None:
    text = (COS / "skills/learn/SKILL.md").read_text(encoding="utf-8")
    for token in ("record_recipe_signal", "share_recipe", "recipe-categories.md", "sharing.recipes",
                  "successful use", "lessons", "## Trace"):
        assert token in text, token


GLOBAL_ACTIONS = [
    "search", "read", "summarise", "extract", "compare", "check", "calculate", "list", "draft",
    "edit", "translate", "create", "update", "file", "propose_slot", "schedule", "send", "reply",
    "forward", "share", "remind", "follow_up", "ask", "decide", "wait", "other",
]
GLOBAL_PLACEHOLDERS = [
    "person", "company", "team", "product", "project", "document", "file", "folder", "amount",
    "number", "date", "time", "period", "place", "email", "phone", "url", "id", "topic", "other",
]


def test_recipe_actions_catalogue() -> None:
    text = (COS / "references/recipe-actions.md").read_text(encoding="utf-8")
    actions = re.findall(r"^- `([a-z_]+)` — ", _section(text, "## Actions"), flags=re.M)
    assert actions == GLOBAL_ACTIONS
    placeholders = re.findall(r"^- `\{([a-z]+)\}` — ", _section(text, "## Placeholders"), flags=re.M)
    assert placeholders == GLOBAL_PLACEHOLDERS


def test_learn_share_table_v2() -> None:
    text = (COS / "skills/learn/SKILL.md").read_text(encoding="utf-8")
    for token in ("nuvel.recipe/2", "slots", "narrative", "recipe-actions.md", "^\\d{1,2}\\.\\d{1,2}\\.\\d{1,2}$"):
        assert token in text, token
    assert "share: blocked (pii)" not in text
    assert "nuvel.recipe/1" not in text
    for token in ("Propuesta para {company}", "Seguimiento de una reunión con {person}",
                  "`title`, `when_to_use` and `pitfalls`"):
        assert token in text, token
    tele = (COS / "references/telemetry.md").read_text(encoding="utf-8")
    assert "nuvel.recipe/2" in tele and "share: blocked (pii)" not in tele and "nuvel.recipe/1" not in tele


def test_registry_layout_has_learning_folders() -> None:
    text = (COS / "references/registry-layout.md").read_text(encoding="utf-8")
    for token in ("lessons/", "recipes/", "## When to use", "## Stats", "sharing.recipes"):
        assert token in text, token


def test_every_skill_reads_lessons() -> None:
    for skill in SKILLS:
        if skill.name not in {"learn"}:
            assert "lessons" in (skill / "SKILL.md").read_text(encoding="utf-8"), skill.name


def test_telemetry_formats_pin_plugin_version() -> None:
    text = (COS / "references/telemetry.md").read_text(encoding="utf-8")
    assert "### Formats" in text
    match = re.search(r"currently `(\d+\.\d+\.\d+)`", text)
    assert match, "telemetry.md must state the plugin version literal"
    for manifest in MANIFESTS:
        assert _json(COS / manifest)["version"] == match.group(1), manifest


def test_project_instructions_have_handoff_and_facts_slot() -> None:
    text = (COS / "templates/project-instructions.md").read_text(encoding="utf-8")
    assert "{{facts}}" in text and "handoff" in text and "HHMM" in text


def test_no_catalan_structure_only():
    """Catalan recipes are masked like es and en; no text may say otherwise."""
    files = [p for p in (ROOT / "plugins").rglob("*") if p.suffix in {".md", ".json"}]
    files += [ROOT / "README.md", ROOT / "CHANGELOG.md"]
    claim = re.compile(r"catalan|\(`ca`\)", re.I)
    stale = re.compile(
        r"structure.only|dropped|drops|cannot be masked|can mask free text only", re.I
    )
    bad = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        for para in re.split(r"\n\s*\n", text):
            for clause in re.split(r"[.;]\s", " ".join(para.split())):
                if claim.search(clause) and stale.search(clause):
                    bad.append(f"{path.relative_to(ROOT)}: {clause[:60]}")
    assert not bad, bad
