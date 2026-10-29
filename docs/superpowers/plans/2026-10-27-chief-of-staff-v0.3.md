# chief-of-staff v0.3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the chief-of-staff plugin a 10–15 minute, business-friendly setup on Microsoft 365 or Google, emit a content-free trace from every skill, and add a `learn` skill whose recipe signals and anonymised recipes reach the open-source nuvel MCP and `nuvel dashboard`.

**Architecture:** The plugin stays Markdown skills plus references (no code); structural pytest checks guard the contracts (step catalogs, question count, jargon, cited paths). Server work lives in `nuvel-mcp` (stdlib only): two new closed schemas on the existing validator, a `RecipeStore` beside `TraceStore`, a PII screen and two tools. `nuvel` (cli) reads `_recipes/` for a dashboard view and `nuvel traces recipes`.

**Tech Stack:** Markdown skills (Anthropic SKILL.md + Codex `agents/openai.yaml`), pytest; Python 3.11+ stdlib (`nuvel-mcp`), FastAPI + Jinja (`nuvel` dashboard).

**Spec:** `docs/superpowers/specs/2026-10-27-chief-of-staff-v0.3-design.md` (this repo). Earlier context: `docs/superpowers/specs/2026-10-20-monorepo-mcp-run-traces-design.md` in the nuvel repo.

## Repos and branches

- **P** = `~/Documents/Cursor/nuvel-plugins`. Create branch `feat/chief-of-staff-v0.3` from `main` before Task 1. Tests: `uvx --with pytest pytest tests -q`.
- **N** = `~/Documents/Cursor/nuvel/.claude/worktrees/chief-of-staff-plugin-a09233`, branch `claude/chief-of-staff-plugin-a09233` (continue on it; it holds the trace store and remote mode these tasks extend). Tests: `uv run pytest packages/nuvel-mcp/tests tests -q`.
- **Never push either repo** and open no PR; nuvel decides when (PyPI `nuvel-mcp` registration is still pending).

## Global Constraints

- Every commit authored `Folken2 <folkenai21@gmail.com>` (check `git config user.email` and `gh api user -q .login` before the first commit in each repo); message ends with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Conventional prefixes (`feat:`, `fix:`, `docs:`, `test:`).
- No credentials, DSNs or tokens as literals anywhere — `$ENV_VAR` placeholders only.
- No real LLM spend unsupervised: manual end-to-end steps run only with the user present.
- Skills and references are written in English; user-facing phrases are produced in the user's language at run time. Spanish examples in blockquotes are fine.
- Registry is **append-only on every backend**; skills are **read-only on sources**.
- `nuvel-mcp` keeps **zero runtime dependencies**; Python `>=3.11`.
- Identifiers: `^[a-z0-9][a-z0-9_.:-]{0,79}$`. `tenant` is set by the server only and rejected from clients.
- Plugin tests use only stdlib + pytest.
- Microsoft 365 behaviour is written from docs and marked `**Unverified (no tenant yet)**` in references until a real tenant check.
- Plugin version becomes `0.3.0` only in Task 13 (all three manifests).

## Review Focus

1. **nuvel connector missing or failing** → the skill finishes its run normally and its journal says `trace: not sent (<class>)`; never a failed run. (Test: Task 6.)
2. **Storage connector can read but not create** (Microsoft write scopes not consented) → setup stops at the folder step with one sentence, writes nothing anywhere else, resumes on "continúa". (Test: Task 3.)
3. **Recipe text with a planted person name, amount, email, phone or URL** → rejected by the server screen with field paths only. (Test: Task 8.)
4. **Same signal or recipe version sent twice** (retry after a timeout) → stored once, response says `duplicate`, counters not doubled in the dashboard. (Tests: Tasks 9, 10, 11.)
5. **A newer plugin sends a category the server has never seen** → accepted (identifier regex only) and grouped under that category. (Tests: Tasks 8, 11.)

---

## Phase 1 — business setup, Microsoft 365, host memory (repo P)

### Task 1: Verify host capabilities and record them

**Files:**
- Create: `docs/research/2026-10-27-host-capabilities.md`
- Create: `plugins/chief-of-staff/references/memory.md`

**Interfaces:**
- Produces: `references/memory.md` sections `## What goes where`, `## Writing to host memory` (one subsection per host: `### Claude chat and Projects`, `### Cowork`, `### ChatGPT`), `## Fallback`. Later tasks cite it by file name.

- [ ] **Step 1:** Research (official docs only: support.claude.com, claude.com/docs, help.openai.com) and record, with URL and date per claim: (a) whether installed plugin skills load in Claude chat, Projects and Cowork; (b) how a conversation can write to host memory in each surface (tool, phrase, or none); (c) the Microsoft 365 connector's tool names for mail search/get, calendar list, Teams read, file list/create/read, and which are writes. Mark each claim *confirmed* or *unconfirmed*.
- [ ] **Step 2:** Write `memory.md` from the spec §1.3 table and the findings: ≤ 10 facts, never anything from `safety.md` §3, the exact "where my notes live" fact, and the fallback (tell the user the one sentence to say, or put the facts in the project instructions).
- [ ] **Step 3:** Run `uvx --with pytest pytest tests -q` → all pass (the cited-reference check covers `memory.md`).
- [ ] **Step 4:** Commit `docs: host capabilities research and memory reference`.

If finding (a) is "skills don't load in chat/Projects", Task 3's project-instructions template must embed compact `recall` (and later `learn`) procedures — note this at the top of the research doc.

### Task 2: Microsoft-first sources, storage, registry and safety references

**Files:**
- Modify: `plugins/chief-of-staff/references/sources.md`, `storage.md`, `registry-layout.md`, `safety.md`
- Test: `tests/test_plugins.py`

- [ ] **Step 1: Write the failing tests**

```python
COS = ROOT / "plugins/chief-of-staff"

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
        assert "**Unverified (no tenant yet)**" in (COS / "references" / name).read_text(encoding="utf-8"), name
```

- [ ] **Step 2:** Run `uvx --with pytest pytest tests -q -k "microsoft or composio"` → FAIL.
- [ ] **Step 3:** Edit the references per spec §1.2: Microsoft 365 connector first for email/calendar/chat/docs; Outlook triage rules (Focused/Other, categories, `isRead`, conversation IDs as opaque `seen` IDs); OneDrive storage steps (root folder, `.md`, round trip); Microsoft equivalents in *Finding the registry* / *Finding the newest* (list children, sort by name); Microsoft write tools listed in `safety.md` §1 as never-call on sources. Keep Composio only as one line starting "For builders:" in `sources.md`. Use tool names from Task 1 where confirmed.
- [ ] **Step 4:** Run the full suite → PASS.
- [ ] **Step 5:** Commit `feat(chief-of-staff): Microsoft 365 first-class in references`.

### Task 3: Setup rewrite for business users + project instructions template

**Files:**
- Modify: `plugins/chief-of-staff/skills/setup/SKILL.md`, `skills/setup/agents/openai.yaml` (prompt wording only)
- Create: `plugins/chief-of-staff/templates/project-instructions.md`
- Test: `tests/test_plugins.py`

**Interfaces:**
- Consumes: `references/memory.md` (Task 1).
- Produces: setup sections `## 1. Detect`, `## 2. Questions`, `## 3. Folder`, `## 4. Memory and project`, `## 5. Routines`, `## 6. First radar`, `## 7. Wrap-up`, `## Read-only storage`; template placeholders `{{registry}}`, `{{owner_name}}`, `{{language}}`. User-facing example phrases in SKILL.md are Markdown blockquotes (`> `).

- [ ] **Step 1: Write the failing tests**

```python
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
```

- [ ] **Step 2:** Run `-k "setup or project_instructions"` → FAIL.
- [ ] **Step 3:** Rewrite setup per spec §1.1 (detect ecosystem with one tiny read per source and a one-line status table; missing connector → official host connector named in host words, admin sentence, never third-party; the 5 questions; inferred timezone/hours/contacts confirmed in one message; folder created without asking where; `## Read-only storage` = stop at folder step with the spec's sentence, write nothing elsewhere, resume on "continúa"; seed host memory via `memory.md`; generate project instructions from the template and tell the user where to paste them; one yes schedules all three routines; first radar live with a 7-day window; wrap-up ≤ 6 lines; the recipe-sharing disclosure line is added in Task 12). Technical details only in the `config` and `setup` documents.
- [ ] **Step 4:** Write `project-instructions.md` (≤ 40 lines): who the assistant works for, where the registry is, use `recall` before answering about the day/clients/topics, read-only rule, language. If Task 1 found skills don't load in chat/Projects, embed a compact recall procedure.
- [ ] **Step 5:** Run the full suite → PASS. Commit `feat(chief-of-staff): business-friendly setup and project instructions`.

### Task 4: Radar and the other skills on Microsoft sources

**Files:**
- Modify: `plugins/chief-of-staff/skills/{radar,brief,prep,weekly-review,recall}/SKILL.md`

- [ ] **Step 1:** Replace Gmail-only wording with ecosystem-neutral steps plus a Microsoft line next to every Gmail example (Outlook search window by `receivedDateTime`, Focused inbox, conversation IDs in `seen`; Teams mentions/DMs under chat; OneDrive search for recall). Tool allow-lists name both ecosystems' read tools (from Task 1).
- [ ] **Step 2:** Run the full suite → PASS (cited paths, frontmatter lengths 50–1024).
- [ ] **Step 3:** Commit `feat(chief-of-staff): Microsoft sources in radar, brief, prep, review, recall`.

### Task 5 (manual, with the user): Phase 1 check on Google

- [ ] **Step 1:** In Claude (chat or Cowork) with the plugin from branch `feat/chief-of-staff-v0.3`, run setup as a business user in Spanish against a **new** test folder name (e.g. "Chief of Staff v03") so the live registry is untouched. Time it.
- [ ] **Step 2:** Record in `docs/test-runs/2026-10-2X-v03-setup.md`: minutes taken, user answers needed (≤ 6), any technical term the assistant used, first radar quality, friction items.
- [ ] **Step 3:** Fix friction in the skills; rerun the suite; commit `docs: v0.3 setup test run` (+ `fix(...)` commits as needed).

---

## Phase 2 — traces from every skill (repo P, then N)

### Task 6: Telemetry reference, step catalogs, Trace sections

**Files:**
- Create: `plugins/chief-of-staff/references/telemetry.md`
- Create: `plugins/chief-of-staff/skills/<skill>/trace-steps.json` for setup, radar, brief, prep, weekly-review, recall
- Modify: every `skills/<skill>/SKILL.md` (new final section `## Trace`), `references/registry-layout.md` (config keys `telemetry`, `telemetry.install_id`; `## Trace` section in run contracts)
- Test: `tests/test_plugins.py`

**Interfaces:**
- Produces: catalog shape `{"skill": str, "steps": [str], "counts": [str], "routing": [str]}`; step ids `<skill>.<name>`; SKILL.md cites step ids as backticked `` `<skill>.<name>` ``. `telemetry.md` defines how to build a `nuvel.skill_run/1` object (fields, `install_id` from config, new `run_id` per run, `host`/`mode` values, one call, one retry, then `trace: not sent (<class>)` in the journal; skip silently when no `record_run_trace` tool; `telemetry: off` → skip).

- [ ] **Step 1: Write the failing tests**

```python
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
```

- [ ] **Step 2:** Run `-k trace` → FAIL.
- [ ] **Step 3:** Write `telemetry.md`, the six catalogs (radar's starts from the spec §2.2 example; counts/routing keys mirror what each skill already counts), the `## Trace` sections (which step ids, counts and routing keys to report, mirror the sent object in the run document's `## Trace`), setup generating `telemetry.install_id` (UUIDv4) and `telemetry: on`.
- [ ] **Step 4:** Run the full suite → PASS. Commit `feat(chief-of-staff): content-free run traces with step catalogs`.

### Task 7 (repo N): Plugin trace fixtures validate on the server

**Files:**
- Create: `packages/nuvel-mcp/tests/fixtures/chief_of_staff/<skill>.json` (one sample trace per skill, built from P's catalogs; plugin version `0.3.0`)
- Create: `packages/nuvel-mcp/tests/test_plugin_trace_fixtures.py`

- [ ] **Step 1: Write the test**

```python
@pytest.mark.parametrize("path", sorted(FIXTURES.glob("*.json")), ids=lambda p: p.stem)
def test_chief_of_staff_fixture_validates(path):
    trace = json.loads(path.read_text())
    assert traces.validate_skill_run(trace) == []
    assert all(s["id"].startswith(trace["skill"]["name"] + ".") for s in trace.get("steps", []))

def test_unknown_step_names_still_valid_identifiers(server):
    # Review Focus 5 analogue for traces: a step id from a newer catalog is accepted
    trace = load("radar") | {"run_id": str(uuid.uuid4())}
    trace["steps"] = trace["steps"] + [{"id": "radar.future-step", "status": "ok"}]
    assert call(server, "record_run_trace", {"trace": trace})["status"] == "recorded"
```

(`server`, `call`, `load` follow the helpers in `test_record_run_trace.py`.)

- [ ] **Step 2:** Run `uv run pytest packages/nuvel-mcp/tests/test_plugin_trace_fixtures.py -v` → PASS (fixtures are data; a failure means a catalog/schema mismatch to fix in P's catalogs).
- [ ] **Step 3:** Manual smoke: `uv run nuvel-mcp serve --transport http --no-auth --feedback-dir "$SCRATCH/fb"`, POST the radar fixture via `tools/call`, then `uv run nuvel traces list --source "$SCRATCH/fb"` shows it. Record the command output in the commit body.
- [ ] **Step 4:** Commit `test(mcp): chief-of-staff trace fixtures validate`.

---

## Phase 3 — learn, recipe signals, anonymised recipes

### Task 8 (repo N): Recipe schemas and validator keywords

**Files:**
- Modify: `packages/nuvel-mcp/src/nuvel_mcp/traces.py`
- Create: `packages/nuvel-mcp/src/nuvel_mcp/schemas/recipe_signal.v1.schema.json`, `recipe.v1.schema.json`
- Create: `packages/nuvel-mcp/src/nuvel_mcp/recipes.py`
- Test: `packages/nuvel-mcp/tests/test_recipe_schema.py`

**Interfaces:**
- Produces in `traces.py`: `VALIDATION_KEYWORDS` += `"maxLength"`, `"minItems"`; `load_schema(resource: str = SCHEMA_RESOURCE) -> dict`; `validate(document: object, resource: str) -> list[str]` (paths only); `validate_skill_run` unchanged in behaviour (delegates).
- Produces in `recipes.py`: `SIGNAL_SCHEMA_ID = "nuvel.recipe_signal/1"`, `RECIPE_SCHEMA_ID = "nuvel.recipe/1"`, `validate_signal(doc) -> list[str]`, `validate_recipe(doc) -> list[str]`, `screen_recipe(recipe: dict) -> list[str]` (JSON-pointer paths of text fields that match a PII pattern; values never returned).

Schemas (closed, `additionalProperties: false` everywhere, all listed fields required unless noted):
- `nuvel.recipe_signal/1`: `schema` const; `signal_id`, `recipe_id`, `install_id` uuid; `plugin {name, version}` as in skill_run; `category` identifier; `event` enum `created|used|succeeded|corrected|retired`; `at` date-time; `uses`, `successes`, `corrections` integer 0–100000.
- `nuvel.recipe/1`: `schema` const; `recipe_id`, `install_id` uuid; `plugin`; `version` integer 1–1000; `category` identifier; `language` pattern `^[a-z]{2}$`; `title` string maxLength 80; `when_to_use` maxLength 200; `steps` array minItems 1 maxItems 15 of `{action: identifier, tool_kind: enum email|calendar|chat|docs|storage|tasks|web|none, text: maxLength 160}`; `pitfalls` array maxItems 5 of string maxLength 160 (optional).

- [ ] **Step 1: Write the failing tests**

```python
def test_signal_valid(): assert recipes.validate_signal(SIGNAL) == []
def test_signal_rejects_tenant(): assert recipes.validate_signal(SIGNAL | {"tenant": "x"}) == ["/tenant"]  # path only
def test_new_category_accepted(): assert recipes.validate_signal(SIGNAL | {"category": "brand-new-thing"}) == []
def test_recipe_title_too_long(): assert "/title" in recipes.validate_recipe(RECIPE | {"title": "x" * 81})
def test_recipe_needs_a_step(): assert "/steps" in recipes.validate_recipe(RECIPE | {"steps": []})
def test_skill_run_still_validates(): assert traces.validate_skill_run(SKILL_RUN) == []

@pytest.mark.parametrize("text", [
    "Enviar a Marta García el resumen", "Escribir a marta@acme.com", "Pagar 1.250 €",
    "Llamar al +34 600 123 456", "Abrir https://acme.com/x", "IBAN ES9121000418450200051332",
])
def test_screen_blocks(text):
    assert recipes.screen_recipe(RECIPE | {"steps": [{"action": "draft", "tool_kind": "email", "text": text}]}) == ["/steps/0/text"]

@pytest.mark.parametrize("text", ["Revisar la propuesta con el cliente", "Preparar el resumen de la reunión"])
def test_screen_allows_generic(text):
    assert recipes.screen_recipe(RECIPE | {"steps": [{"action": "draft", "tool_kind": "email", "text": text}]}) == []
```

(Fixtures `SIGNAL`, `RECIPE`, `SKILL_RUN` defined at the top of the test file with valid UUIDs; screen also covers `title`, `when_to_use`, `pitfalls/<i>`.)

- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Implement. Screen patterns: email, `https?://|www\.`, phone (`\+?\d[\d\s().-]{7,}\d`), IBAN-like (`\b[A-Z]{2}\d{2}[A-Z0-9 ]{10,}`), long digit runs (≥ 6 digits ignoring spaces), currency (`[€$£]\s?\d` or `\d[\d.,]*\s?(€|EUR|USD|\$|£)`), and two or more consecutive capitalised words (Unicode letters) not at the start of the text.
- [ ] **Step 4:** Run full N suite → PASS. Commit `feat(mcp): nuvel.recipe_signal/1 and nuvel.recipe/1 schemas with PII screen`.

### Task 9 (repo N): Recipe store

**Files:**
- Modify: `packages/nuvel-mcp/src/nuvel_mcp/recipes.py`, `cli.py` (`--recipe-store`, default `local`)
- Test: `packages/nuvel-mcp/tests/test_recipe_store.py`

**Interfaces:**
- Produces: `class RecipeStore(Protocol)`: `append_signal(signal: dict) -> bool`, `put_recipe(recipe: dict) -> bool` (False = duplicate). `LocalRecipeStore(feedback_dir: Path)`: signals at `{feedback_dir}/_recipes/signals/{YYYY-MM-DD}.jsonl` (UTC day of `at`), dedupe on `(tenant, signal_id)`; recipes at `{feedback_dir}/_recipes/recipes/{tenant_key}/{recipe_id}/v{version}.json`, written atomically (temp + `os.replace`), duplicate when the file exists; `tenant_key = sha256(tenant or "_local")[:16]`. `load_recipe_store(spec: str, feedback_dir: Path) -> RecipeStore` mirrors `load_trace_store`.

- [ ] **Step 1: Write the failing tests:** `test_signal_dedup_same_tenant` (second append → False, one line on disk), `test_signal_same_id_other_tenant_kept`, `test_recipe_version_written_once`, `test_recipe_paths_hide_tenant` (the raw tenant string does not appear in any path), `test_load_recipe_store_rejects_bad_spec`.
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implement (reuse the striped-lock approach from `LocalTraceStore`). **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit `feat(mcp): local recipe store`.

### Task 10 (repo N): `record_recipe_signal` and `share_recipe` tools

**Files:**
- Modify: `packages/nuvel-mcp/src/nuvel_mcp/server.py`
- Test: `packages/nuvel-mcp/tests/test_recipe_tools.py`

**Interfaces:**
- Consumes: Task 8 validators/screen, Task 9 store.
- Produces: tools `record_recipe_signal {signal}` and `share_recipe {recipe}`; both added to `HTTP_DEFAULT_TOOLS`; tenant from `current_principal`; responses `{"status": "recorded"|"duplicate", ...id}`; rejections via `ToolInputError(paths)`; screen hits → `ToolInputError` with the screen's paths; relay types `"recipe_signal"` / `"recipe"` to `$NUVEL_FEEDBACK_URL` after the local write, same failure handling as `record_run_trace`. Tool descriptions state: content-free signals; recipe must be generic, no names/companies/amounts/dates/places/contacts/URLs; `tenant` never sent.

- [ ] **Step 1: Write the failing tests:** `test_signal_recorded_then_duplicate`, `test_signal_tenant_from_principal` (stored line has the principal's client_id), `test_client_tenant_rejected`, `test_share_recipe_screen_rejects_with_paths_only` (error text has `/steps/0/text`, not the value), `test_tools_served_in_remote_mode` (both in `tools/list` after `enable_remote_mode()`), `test_store_error_is_generic` (OSError → generic message).
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implement. **Step 4:** Run full N suite → PASS.
- [ ] **Step 5:** Commit `feat(mcp): record_recipe_signal and share_recipe tools`.

### Task 11 (repo N): Recipe candidates in `nuvel traces` and `nuvel dashboard`

**Files:**
- Create: `nuvel/recipes_view.py`
- Modify: `nuvel/traces_cli.py` (subcommand `recipes`), `nuvel/dashboard/app.py` (route `GET /recipes`), `nuvel/dashboard/templates/base.html` (nav link), create `nuvel/dashboard/templates/recipes.html`
- Modify docs: `docs/reference/skill-run-traces.md` (two schemas, tools, storage layout), `docs/reference/cli.md`, `CHANGELOG.md`
- Test: `tests/test_recipes_view.py`, `tests/test_dashboard_recipes.py`

**Interfaces:**
- Produces: `@dataclass RecipeCandidate(category: str, recipes: int, tenants: int, uses: int, successes: int, corrections: int, success_rate: float, latest: dict | None)`; `load_recipe_candidates(roots: list[Path]) -> list[RecipeCandidate]` — finds `_recipes/` at or under each root; per `(tenant, recipe_id)` takes the signal with the greatest `at` (counters are cumulative) and sums those; `latest` = highest-version recipe JSON in that category by file mtime; sorted by `uses` desc.

- [ ] **Step 1: Write the failing tests:** `test_counters_use_latest_signal_per_recipe` (two signals uses=1 then uses=3 → 3, not 4), `test_duplicate_signal_lines_not_double_counted`, `test_groups_unknown_category`, `test_cli_recipes_lists_categories` (output has category and uses), `test_dashboard_recipes_page` (200, shows category and the latest recipe title; HTML-escaped).
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implement (dashboard uses the same roots it already passes as `skill_roots`). **Step 4:** Run full N suite + `uv run mkdocs build --strict` → PASS.
- [ ] **Step 5:** Commit `feat(dashboard): recipe candidates view and nuvel traces recipes`.

### Task 12 (repo P): `learn` skill, lessons and recipes in the registry

**Files:**
- Create: `plugins/chief-of-staff/skills/learn/{SKILL.md,agents/openai.yaml,trace-steps.json}`
- Create: `plugins/chief-of-staff/references/recipe-categories.md`
- Modify: `references/registry-layout.md` (folders `lessons/`, `recipes/`; contracts `lessons`, `recipe <slug>`; config `sharing.recipes`), `references/telemetry.md` (recipe signals, share rules), every other skill's SKILL.md (read newest `lessons` at start; check `recipes/` before a task), `skills/weekly-review/SKILL.md` ("What I learned this week" + duplicate-lesson consolidation), `skills/setup/SKILL.md` (`sharing.recipes: on`, disclosure line), `templates/project-instructions.md` (run `learn` after corrections and complex tasks)
- Test: `tests/test_plugins.py`

**Interfaces:**
- Consumes: Task 10 tool names and argument shapes; Task 8 schema fields.
- Produces: categories as a Markdown list of backticked identifiers in `recipe-categories.md` (≈ 20 + `other`); recipe document sections `## When to use`, `## Steps`, `## Pitfalls`, `## Stats` with keys `uses`, `successes`, `corrections`, `last_used`, `recipe_id`, `category`, `status`.

- [ ] **Step 1: Write the failing tests**

```python
def test_recipe_categories() -> None:
    cats = re.findall(r"^- `([a-z0-9-]+)`", (COS / "references/recipe-categories.md").read_text(encoding="utf-8"), flags=re.M)
    assert 15 <= len(cats) <= 30 and "other" in cats and len(set(cats)) == len(cats)

def test_learn_contract() -> None:
    text = (COS / "skills/learn/SKILL.md").read_text(encoding="utf-8")
    for token in ("record_recipe_signal", "share_recipe", "recipe-categories.md", "sharing.recipes",
                  "successful use", "share: blocked (pii)", "lessons", "## Trace"):
        assert token in text, token

def test_registry_layout_has_learning_folders() -> None:
    text = (COS / "references/registry-layout.md").read_text(encoding="utf-8")
    for token in ("lessons/", "recipes/", "## When to use", "## Stats", "sharing.recipes"):
        assert token in text, token

def test_every_skill_reads_lessons() -> None:
    for skill in SKILLS:
        if skill.name not in {"learn"}:
            assert "lessons" in (skill / "SKILL.md").read_text(encoding="utf-8"), skill.name
```

- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Write `learn` per spec §3.1–3.3: triggers; act-then-tell line; lessons as a full newest-wins list (stable facts also to host memory via `memory.md`); recipes as newest-wins versions per slug; successful use = task finished with no correction in that conversation; signal on every recipe event; after ≥ 3 successes, rewrite a generic copy (roles not names; no companies, amounts, dates, places, contacts, URLs, file names, quotes), self-check against that list, send `share_recipe` or log `share: blocked (pii)`; respect `sharing.recipes` and `telemetry`; never block the user's task. Update the other files listed.
- [ ] **Step 4:** Run the full suite → PASS. Commit `feat(chief-of-staff): learn skill with lessons, recipes and sharing`.

### Task 13 (repo P, manual parts with the user): Release prep 0.3.0

**Files:**
- Modify: three `plugin.json` manifests (`0.3.0`, descriptions mention Microsoft 365 first), `plugins/chief-of-staff/README.md` and root `README.md` (business-reader rewrite), `CHANGELOG.md`, `.codex-plugin` interface prompts if wording changed; `packages/nuvel-mcp/tests/fixtures/chief_of_staff/*.json` in N already say `0.3.0`.

- [ ] **Step 1:** Bump versions; run P suite → PASS (manifests agree).
- [ ] **Step 2 (with the user):** In Claude, correct the assistant once in a chat → a new `lessons` document appears and the next brief applies it; do a multi-step task three times → recipe created, three signals and one shared recipe visible in `nuvel traces recipes` against a local `nuvel-mcp serve --transport http` (Cowork/chat can only reach it once deployed; if not deployed, verify signals through the tool from a Claude Code session instead and note it). Record in `docs/test-runs/`.
- [ ] **Step 3:** Commit `chore(chief-of-staff): release 0.3.0`. Do not push.

---

## Execution notes

- Order: Tasks 1→5, 6→7, 8→11, 12→13. Tasks 8–11 (N) and Task 12 (P) may run in parallel once Task 10's tool shapes are fixed (they are in this plan).
- Microsoft verification on a real tenant stays open after Task 13 (spec Phase 1 "done when").
