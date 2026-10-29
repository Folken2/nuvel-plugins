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
    assert len(questions) == 6


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
    for token in ("recipe-categories.md", "../../references/recipes.md", "lessons", "## Trace",
                  "draft", "active", "retired", "index", "explicit approval"):
        assert token in text, token
    # learn never changes the sharing fields; it only carries them forward.
    assert "`shared_version` and `blocked_version` forward unchanged" in " ".join(text.split())


def test_learn_has_no_sharing_tools() -> None:
    text = (COS / "skills/learn/SKILL.md").read_text(encoding="utf-8")
    for token in ("share_recipe", "record_recipe_signal", "nuvel.recipe/", "nuvel.recipe_signal/"):
        assert token not in text, token
    cat = _json(COS / "skills/learn/trace-steps.json")
    assert "learn.signal" not in cat["steps"] and "learn.share" not in cat["steps"]
    for count in ("signals_sent", "signals_failed", "shares_sent", "shares_blocked", "shares_failed"):
        assert count not in cat["counts"], count
    for count in ("drafts_created", "recipes_promoted", "index_written"):
        assert count in cat["counts"], count


def test_learn_reads_index_only_before_a_task() -> None:
    sec = _section((COS / "skills/learn/SKILL.md").read_text(encoding="utf-8"), "## 0. Before a task")
    assert "`index`" in sec and "newest" in sec
    assert "List `recipes/`" not in sec and "list `recipes/`" not in sec


def test_recipes_reference_contract() -> None:
    text = " ".join((COS / "references/recipes.md").read_text(encoding="utf-8").split())
    for token in ("`draft`", "`active`", "`retired`", "`days_used`", "`last_outcome`", "60 days",
                  "`successes` ≥ 1", "`days_used` ≥ 3", "# Recipes index",
                  "`learn` writes the first `index` when none exists and active recipes do"):
        assert token in text, token


def test_success_is_explicit_approval() -> None:
    text = " ".join((COS / "references/recipes.md").read_text(encoding="utf-8").split())
    assert "`last_outcome: silent`" in text
    assert "Silence is not a success" in text
    assert "move the success" not in text and "successes` −1" not in text


def test_use_is_written_once() -> None:
    """The use is written at task end; a later approval or correction is a separate
    run that never touches uses or days_used (no double counting)."""
    text = " ".join((COS / "references/recipes.md").read_text(encoding="utf-8").split())
    for token in ("**1. The use, written once, at the end of the task**",
                  "a later run never adds to `uses` or `days_used` for the same use",
                  "triggers a separate `learn` run",
                  "changes only `successes` or `corrections` and `last_outcome`, never `uses` or `days_used`",
                  "Two runs, one document each",
                  "an approval after a correction sets it back to `success`",
                  "The task that promotes it counts as a use",
                  "A correction after an approval keeps the success",
                  "it never counts in `recipes_created`"):
        assert token in text, token
    skill = " ".join((COS / "skills/learn/SKILL.md").read_text(encoding="utf-8").split())
    for token in ("**Use**, written once, at the end of a task", "No later run adds to `uses` or `days_used`",
                  "a correction after an approval keeps the success", "any run that finds active recipes but no `index`"):
        assert token in skill, token


def test_registry_layout_index_and_text_switch() -> None:
    text = (COS / "references/registry-layout.md").read_text(encoding="utf-8")
    for token in ("- days_used:", "- last_outcome:", "draft|active|retired", "index`",
                  "# Recipes index", "sharing.recipe_text"):
        assert token in text, token
    assert "list `recipes/`" not in text


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


def test_recipe_text_guidance() -> None:
    """v0.3's free-text guidance lives in recipe-sharing.md, under the text opt-in."""
    text = (COS / "references/recipe-sharing.md").read_text(encoding="utf-8")
    sec = _section(text, "## Text (only with `sharing.recipe_text: on`)")
    for token in ("recipe-actions.md", "Propuesta para {company}", "Seguimiento de una reunión con {person}",
                  "`title`, `when_to_use` and `pitfalls`", "`step_notes`", "Never write `{?}`"):
        assert token in sec, token
    for name in ("references/recipe-sharing.md", "skills/learn/SKILL.md"):
        doc = (COS / name).read_text(encoding="utf-8")
        assert "share: blocked (pii)" not in doc and "nuvel.recipe/1" not in doc, name
        assert "`note`" not in doc, name


SPEC_QUESTION_SIX = (
    "Cuando una forma de trabajar te funciona varias veces, puedo enviar a nuvel su esquema "
    "(qué pasos, en qué orden, sin ningún texto tuyo) para mejorar el producto. ¿Quieres que "
    "además envíe la descripción en tus palabras, con los nombres y las cifras sustituidos? "
    "Por defecto, no."
)


def test_setup_question_six_text_opt_in_defaults_no() -> None:
    sec = _section((COS / "skills/setup/SKILL.md").read_text(encoding="utf-8"), "## 2. Questions")
    q6 = " ".join(sec[sec.index("\n6. "):].split())
    assert SPEC_QUESTION_SIX in q6
    assert "descripción" in q6 and "Por defecto, no" in q6
    flat = " ".join((COS / "skills/setup/SKILL.md").read_text(encoding="utf-8").split())
    assert "solo el esquema, nunca tu texto" in flat


def test_recipe_text_off_unless_asked() -> None:
    share = " ".join((COS / "references/recipe-sharing.md").read_text(encoding="utf-8").split())
    assert "A missing `sharing.recipe_text` counts as `off`" in share
    assert "Build `text` only when `config` says `- sharing.recipe_text: on`" in share
    setup = (COS / "skills/setup/SKILL.md").read_text(encoding="utf-8")
    assert "- sharing.recipe_text: off" in setup
    assert "never turns it on without asking" in " ".join(setup.split())


def test_sharing_procedure_v3() -> None:
    text = (COS / "references/recipe-sharing.md").read_text(encoding="utf-8")
    for token in ("nuvel.recipe/3", "nuvel.recipe_signal/2", "`step_notes`", "`days_used`", "`slots`",
                  "`stats`", "^\\d{1,2}\\.\\d{1,2}\\.\\d{1,2}$", "recipe-actions.md", "`shared_version`",
                  "`blocked_version`", "`recorded`", "`duplicate`", "`rejected`", "`record_recipe_signal`",
                  "`share_recipe`", "`successes` ≥ 1", "`days_used` ≥ 3", "## Switches"):
        assert token in text, token
    for token in ("nuvel.recipe/2", "nuvel.recipe/1", "nuvel.recipe_signal/1", '"event"', "`event`"):
        assert token not in text, token


def test_telemetry_names_v3_schemas() -> None:
    tele = (COS / "references/telemetry.md").read_text(encoding="utf-8")
    for token in ("nuvel.recipe/3", "nuvel.recipe_signal/2", "recipe-sharing.md", "`sharing.recipe_text`",
                  "`sharing.recipes`", "`telemetry`"):
        assert token in tele, token
    stale = re.compile(r"nuvel\.recipe/[12]\b|nuvel\.recipe_signal/1\b")
    for path in COS.rglob("*"):
        if path.suffix in {".md", ".json"}:
            assert not stale.search(path.read_text(encoding="utf-8")), path.relative_to(ROOT)
    sched = " ".join((COS / "references/scheduling.md").read_text(encoding="utf-8").split())
    assert "`record_recipe_signal`" in sched and "`share_recipe`" in sched
    assert "used by the weekly review" in sched


def test_weekly_review_recipe_batch_order() -> None:
    text = (COS / "skills/weekly-review/SKILL.md").read_text(encoding="utf-8")
    marks = ["**Merge duplicate lessons.**", "**Expire drafts.**", "**Merge duplicate recipes.**",
             "**Rebuild the index.**", "**Signals.**", "**Share.**"]
    pos = [text.index(m) for m in marks]
    assert pos == sorted(pos), pos
    assert "at most one new version per recipe" in " ".join(text.split())
    tools = _section(text, "## Tools you may use")
    assert "`record_recipe_signal`" in tools and "`share_recipe`" in tools
    cat = _json(COS / "skills/weekly-review/trace-steps.json")
    assert {"weekly-review.recipes", "weekly-review.share"} <= set(cat["steps"])
    for count in ("drafts_expired", "recipes_merged", "index_written", "signals_sent", "signals_failed",
                  "shares_sent", "shares_blocked", "shares_failed", "shares_with_text"):
        assert count in cat["counts"], count
    assert "../../references/recipe-sharing.md" in text


def test_no_skill_lists_recipes_folder_to_match() -> None:
    for skill in _skills(COS):
        text = " ".join((skill / "SKILL.md").read_text(encoding="utf-8").split())
        if skill.name in {"weekly-review", "learn"}:
            continue
        assert "list `recipes/`" not in text.lower(), skill.name
        if skill.name != "setup":
            assert "newest `index`" in text, skill.name
    tmpl = (COS / "templates/project-instructions.md").read_text(encoding="utf-8")
    assert "newest note ending in \"index\"" in " ".join(tmpl.split())
    # weekly-review reads the index to match, and lists recipes/ only for its batch.
    wr = _section((COS / "skills/weekly-review/SKILL.md").read_text(encoding="utf-8"), "## Lessons and recipes")
    wr = " ".join(wr.split())
    assert "newest `index`" in wr and "list `recipes/`" not in wr.lower()


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


# Every place that lists the masked languages, with the phrase that must name
# Catalan (whitespace is normalised, so wrapped lines match).
MASKED_LANGUAGE_LISTS = {
    "CHANGELOG.md": "Spanish, English and Catalan descriptions are masked",
    "plugins/chief-of-staff/README.md": "Descriptions in Spanish, English and Catalan are masked",
    "plugins/chief-of-staff/references/telemetry.md":
        "Spanish (`es`), English (`en`) and Catalan (`ca`) free text is masked",
    "plugins/chief-of-staff/references/recipe-sharing.md":
        "The server masks free text in Spanish (`es`), English (`en`) and Catalan (`ca`)",
}


@pytest.mark.parametrize("name, phrase", sorted(MASKED_LANGUAGE_LISTS.items()))
def test_masked_language_lists_name_catalan(name: str, phrase: str) -> None:
    text = " ".join((ROOT / name).read_text(encoding="utf-8").split())
    assert phrase in text, name


def test_residual_privacy_examples() -> None:
    """The privacy wording's example words (March, Sala) are pinned against the
    masker by nuvel's tests/test_docs_catalan_masked.py; a word the masker
    masks (e.g. Baker) must not come back."""
    for name in MASKED_LANGUAGE_LISTS:
        text = " ".join((ROOT / name).read_text(encoding="utf-8").split())
        assert "e.g. March, or Sala" in text, name
        assert "Baker" not in text, name


def test_skill_md_line_cap() -> None:
    """Every SKILL.md stays within 500 lines; long procedures go to references/."""
    for skill in SKILLS:
        lines = (skill / "SKILL.md").read_text(encoding="utf-8").count("\n") + 1
        assert lines <= 500, f"{skill.name}: {lines} lines"
