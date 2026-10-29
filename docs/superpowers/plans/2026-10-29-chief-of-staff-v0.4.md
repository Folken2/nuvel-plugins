# chief-of-staff v0.4 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Recipes only for recurring tasks with honest success counts, an index for cheap matching, and recipe sharing that sends structure only unless the user opted in to text.

**Architecture:** Server (`nuvel-mcp`, repo N) replaces `nuvel.recipe/2` with `/3` (structure required, optional `text` subtree masked as before) and `nuvel.recipe_signal/1` with a weekly snapshot `/2`. Plugin (repo P) slims `learn` to lessons + private recipes, moves sharing and signals into a weekly batch in `weekly-review`, and moves procedures into references.

**Tech Stack:** Python 3.11+ stdlib (nuvel-mcp), JSON Schema subset validated by `nuvel_mcp.traces`, Markdown skills (Anthropic skills format), pytest.

**Spec:** `docs/superpowers/specs/2026-10-29-chief-of-staff-v0.4-design.md` (repo P).

Repos:
- **P** = `/Users/albertfolch/Documents/Cursor/nuvel-plugins`, branch `feat/chief-of-staff-v0.4`.
- **N** = `/Users/albertfolch/Documents/Cursor/nuvel/.claude/worktrees/chief-of-staff-plugin-a09233`, branch `feat/recipe-v3`.

## Global Constraints

- Commits as Folken2 <folkenai21@gmail.com>, conventional prefixes, trailer `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. No push.
- `nuvel-mcp` stays stdlib-only, no new dependencies.
- Every `SKILL.md` ≤ 500 lines (aim 200–300); procedures, formats and tables live in `references/` (one topic per file, split above ~300 lines). Scripts are optional helpers only.
- `sharing.recipe_text` is `on` only after the user said yes in setup question 6; missing = `off`. No text in the user's words is sent otherwise.
- Quality bar: `status: active`, `successes` ≥ 1, `days_used` ≥ 3, `last_outcome` ≠ `corrected`.
- Drafts expire after 60 days without use. Success = explicit approval in an interactive run only.
- `nuvel.recipe/2` and `nuvel.recipe_signal/1` are removed (no hosted server ever accepted them).
- Never send `tenant` or `masking`; rejections name field paths only, client keys as `*`.
- Plugin version `0.4.0` in all three manifests and the `telemetry.md` literal.
- User-facing lines in the plugin's existing style: Spanish examples first, plain words, no jargon (setup's jargon test applies).

## Review Focus

1. A v0.3 registry with active recipes and no `index`: *Before a task* would find nothing until the first weekly review. Expected: `learn` writes the first index at its next run when none exists and active recipes do; the plugin test pins that sentence (Task 4).
2. `config` without `sharing.recipe_text` (every v0.3 registry): text must never be built. Expected: missing = off in `recipe-sharing.md`, setup reconfigure adds `- sharing.recipe_text: off`; test pins both (Tasks 4, 5).
3. A `text` object that carries only `language`, or `step_notes` longer than `steps`: expected rejection with a path, never a stored half-recipe (Task 1 tests).
4. Stats that cannot be true after a merge (`successes` > `uses`, `days_used` > `uses`): expected rejection `stats/successes` / `stats/days_used` (Task 1 tests).
5. A text-free recipe must not touch the masker at all (no lexicon load needed) and must still be stored with a zero `masking` stamp: Task 1 test with lexicons unavailable.

---

### Task 1: `nuvel.recipe/3` on the server (N)

**Files:**
- Create: `packages/nuvel-mcp/src/nuvel_mcp/schemas/recipe.v3.schema.json`
- Delete: `packages/nuvel-mcp/src/nuvel_mcp/schemas/recipe.v2.schema.json`
- Modify: `packages/nuvel-mcp/src/nuvel_mcp/recipes.py` (`RECIPE_SCHEMA_ID`, `RECIPE_RESOURCE`, `validate_recipe`)
- Modify: `packages/nuvel-mcp/src/nuvel_mcp/masking.py` (`mask_recipe`, `invariant_hits`: text fields now under `/text`)
- Modify: `packages/nuvel-mcp/src/nuvel_mcp/server.py` (`_masked_recipe`, `share_recipe` tool description/input schema)
- Test: `packages/nuvel-mcp/tests/test_recipe_schema.py`, `test_recipe_tools.py`, `test_masking.py` (recipe-level tests), `test_packaging.py` (schema file list)

**Interfaces:**
- Produces: `recipes.RECIPE_SCHEMA_ID == "nuvel.recipe/3"`; `recipes.validate_recipe(doc) -> list[str]` (paths); `masking.mask_recipe(recipe, lexicon, abbreviations) -> (dict, info)` where text fields are `/text/title`, `/text/when_to_use`, `/text/step_notes/<i>`, `/text/pitfalls/<i>`, `/text/narrative`; stored recipe carries `masking: {"lexicon": str|None, "masked": int, "words": int, "dropped": [pointer,...]}`.

Schema (exact): required `schema, recipe_id, install_id, plugin, version, category, steps, stats`; `steps` 1–15 items with required `action, tool_kind, slots` and **no other keys**; `stats` object with required `uses, successes, corrections, days_used`, integers 0–100000; optional `text` object, required `language` (`^[a-z]{2}$`), plus at least one of `title` (≤80), `when_to_use` (≤200), `step_notes` (array ≤15 of strings ≤160), `pitfalls` (≤5 × ≤160), `narrative` (≤2000); no other keys anywhere.

- [ ] **Step 1: Write failing tests** in `test_recipe_schema.py`:
  - `test_v3_structure_only_is_valid` — minimal recipe without `text` → `validate_recipe(...) == []`.
  - `test_v3_rejects_step_note` — `steps[0]["note"] = "x"` → `"steps/0/*"` in errors.
  - `test_v3_text_needs_more_than_language` — `text={"language": "es"}` → errors non-empty, path starts `text`.
  - `test_v3_step_notes_not_longer_than_steps` — 1 step, 2 notes → `"text/step_notes"` in errors.
  - `test_v3_stats_consistency` (parametrized) — `successes=5, uses=3` → `"stats/successes"`; `days_used=4, uses=3` → `"stats/days_used"`; `corrections=9, uses=3` → `"stats/corrections"`.
  - `test_v2_schema_is_gone` — `RECIPE_SCHEMA_ID == "nuvel.recipe/3"` and the v2 resource no longer exists in the package.
  The cross-field rules (`step_notes` length, stats ≤ `uses`, text non-empty) live in `validate_recipe` after the schema check, returning these exact paths.
- [ ] **Step 2: Write failing tool tests** in `test_recipe_tools.py`:
  - `test_share_structure_only_skips_masker` — monkeypatch the lexicon loader to raise; share a text-free recipe → `status == "recorded"`, `masked == 0`, `words == 0`, `dropped == []`, stored `masking["lexicon"] is None`.
  - `test_share_text_is_masked_under_text` — es text with a name in `narrative` → stored `text.narrative` contains `{?}`, `masking["lexicon"].startswith("es-")`.
  - `test_share_dropped_pointers_under_text` — an unmaskable-language text → `dropped` entries all start with `/text/`.
  - Update every existing /2 fixture in N tests to /3 (move notes into `text.step_notes`, add `stats`).
- [ ] **Step 3: Run** `.venv/bin/python -m pytest packages/nuvel-mcp/tests -q -k "recipe or masking"` → new tests FAIL.
- [ ] **Step 4: Implement** schema, `validate_recipe` cross-field checks, `mask_recipe` / `invariant_hits` walking only the `text` subtree (structure keys are closed enums, so the invariant on them stays as in v2), `_masked_recipe` short-circuit when `"text"` is absent, tool description text.
- [ ] **Step 5: Run** full `.venv/bin/python -m pytest packages/nuvel-mcp/tests tests -q` → PASS (the 2 strict xfails remain).
- [ ] **Step 6: Commit** `feat(mcp)!: nuvel.recipe/3, structure required and text optional`.

### Task 2: `nuvel.recipe_signal/2` weekly snapshot, dashboard, CLI and docs (N)

**Files:**
- Create: `packages/nuvel-mcp/src/nuvel_mcp/schemas/recipe_signal.v2.schema.json`; Delete: `recipe_signal.v1.schema.json`
- Modify: `recipes.py` (`SIGNAL_SCHEMA_ID`, `SIGNAL_RESOURCE`, `validate_signal`, `screen_signal`), `server.py` (`record_recipe_signal` description), `nuvel/recipes_view.py`, `nuvel/traces_cli.py`, `nuvel/dashboard/app.py` + recipes template, `docs/reference/skill-run-traces.md`, `docs/how-to/deploy-skills-mcp.md`, `CHANGELOG.md`, `tests/test_docs_catalan_masked.py` (only if a phrase it checks moved)
- Test: `packages/nuvel-mcp/tests/test_recipe_schema.py`, `test_recipe_tools.py`, `tests/test_recipes_view.py`, `tests/test_dashboard_recipes.py`

**Interfaces:**
- Consumes: Task 1 stored recipe shape (`steps` without notes, `stats`, optional `text`, `masking`).
- Produces: `SIGNAL_SCHEMA_ID == "nuvel.recipe_signal/2"`; signal fields exactly `schema, signal_id, recipe_id, install_id, plugin, category, status (draft|active|retired), at, uses, successes, corrections, days_used`; the view's per-recipe row uses the **latest signal per `recipe_id`** (by `at`).

- [ ] **Step 1: Failing tests:**
  - `test_signal_v2_valid_snapshot`; `test_signal_v2_rejects_event_key` (`"event"` → `"*"` path); `test_signal_v2_status_enum` (`"paused"` rejected at `status`); `test_signal_v2_stats_consistency` (same three cases as Task 1).
  - `test_recipes_view_latest_snapshot_wins` — two signals for one `recipe_id`, older `at` with uses 2, newer with uses 5 → row shows 5 and the newer status.
  - `test_recipes_view_structure_only_recipe` — recipe without `text` renders its steps (action · tool_kind · slots) and shows no narrative block; dashboard HTML contains no `None`.
  - `test_recipes_view_shows_text_when_present` — recipe with `text.narrative` renders it.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement** schema + validators, view/CLI/dashboard on /3 recipes and /2 snapshots (a "text shared" badge is the builder's call), docs say: recipes are shared as structure; text only when the user opted in, masked on the server; signals are weekly snapshots.
- [ ] **Step 4: Run** `.venv/bin/python -m pytest packages/nuvel-mcp/tests tests -q` and `.venv/bin/mkdocs build --strict -q` → PASS.
- [ ] **Step 5: Commit** `feat(mcp)!: weekly recipe_signal/2 snapshots; dashboard and docs on recipe/3`.

### Task 3: `learn` slimmed, recipe references (P)

**Files:**
- Create: `plugins/chief-of-staff/references/recipes.md` (lifecycle draft/active/retired, promote, direct active, stats rules, success = explicit approval, quality bar, migration of v0.3 recipes, index format and when `learn` writes it, one document per recipe per run)
- Create: `plugins/chief-of-staff/references/recipe-sharing.md` (Task 4 fills the weekly procedure; this task moves the v0.3 *placeholders, examples, language* guidance there under a "Text (only with `sharing.recipe_text: on`)" heading)
- Modify: `plugins/chief-of-staff/skills/learn/SKILL.md` (drop §4 *Signals*, §5 *Sharing*, the two tools, `shared_version`/`blocked_version` rules except "carry forward unchanged"; *Before a task* reads the newest `index` only; *When to run* trigger becomes: complex task → draft or promote; user says it recurs → active), `skills/learn/trace-steps.json` (remove `learn.signal`, `learn.share` and their counts; add counts `drafts_created`, `recipes_promoted`, `index_written` on `learn.recipe`)
- Modify: `plugins/chief-of-staff/references/registry-layout.md` (recipe `## Stats` example with `days_used`, `last_outcome`, `status: draft|active|retired`; `index` document kind and contract; config keys `sharing.recipes`, `sharing.recipe_text`)
- Test: `tests/test_plugins.py`

**Interfaces:**
- Produces: document kind `index` at `recipes/YYYY-MM-DD HHMM index`, format `# Recipes index` / `## <category>` / `- <slug> — <When to use, one line>` (active recipes only); recipe stats keys `uses, successes, corrections, days_used, last_used, last_outcome (success|silent|corrected), recipe_id, category, status, version, shared_version, blocked_version`.

- [ ] **Step 1: Failing tests** in `tests/test_plugins.py`:
  - `test_learn_has_no_sharing_tools` — `learn/SKILL.md` contains neither `share_recipe` nor `record_recipe_signal`; its trace catalog has no `learn.signal`/`learn.share`.
  - `test_learn_reads_index_only_before_a_task` — the *Before a task* section mentions `index` and does not say "List `recipes/`".
  - `test_recipes_reference_contract` — `references/recipes.md` contains `draft`, `days_used`, `last_outcome`, `60 days`, `successes` ≥ 1 wording of the quality bar (`days_used` ≥ 3), and the sentence that `learn` writes the first `index` when none exists and active recipes do.
  - `test_success_is_explicit_approval` — `recipes.md` says silence is not a success (`silent`).
  - Rewrite `test_learn_contract` and `test_learn_share_table_v2` tokens for v0.4 (move share-table checks to Task 4's test).
- [ ] **Step 2: Run** `uvx --with pytest pytest tests -q` (from P) → FAIL.
- [ ] **Step 3: Implement** the files above. `learn/SKILL.md` target ≤ 200 lines.
- [ ] **Step 4: Run** tests → PASS; `wc -l plugins/chief-of-staff/skills/learn/SKILL.md` ≤ 250.
- [ ] **Step 5: Commit** `feat(chief-of-staff): learn keeps lessons and private recipes; drafts, honest success, index`.

### Task 4: weekly batch, sharing procedure, setup question 6 (P)

**Files:**
- Modify: `plugins/chief-of-staff/references/recipe-sharing.md` (full weekly procedure: eligibility, structure build, text build only with `sharing.recipe_text: on`, `share_recipe` call table for `nuvel.recipe/3`, reply handling recorded/duplicate/rejected/error, `nuvel.recipe_signal/2` table, switches table)
- Modify: `plugins/chief-of-staff/references/telemetry.md` (replace the v0.3 *Recipe signals and recipe sharing* section with a short pointer to `recipe-sharing.md` and the three-key switches table; approvals list unchanged)
- Modify: `plugins/chief-of-staff/skills/weekly-review/SKILL.md` (new step after *Merge duplicate lessons*: expire drafts → merge duplicate recipes → rebuild index → signals → share, at most one new version per recipe; tools list adds `record_recipe_signal`, `share_recipe` and recipe/index writes), `skills/weekly-review/trace-steps.json` (steps `weekly-review.recipes` with counts `drafts_expired`, `recipes_merged`, `index_written`; `weekly-review.share` with `signals_sent`, `signals_failed`, `shares_sent`, `shares_blocked`, `shares_failed`, `shares_with_text`)
- Modify: `plugins/chief-of-staff/skills/setup/SKILL.md` (§2 question 6 = the spec's text-opt-in question verbatim, default no; first `config` writes `- sharing.recipe_text: <on|off>`; reconfigure adds `- sharing.recipe_text: off` when missing and never turns it on without asking; wrap-up notice says structure only, never your text, unless they said yes)
- Modify: `skills/{brief,prep,radar,recall}/SKILL.md` and `templates/` project instructions: wherever they list `recipes/` to find a recipe, read the newest `index` instead (one line each).
- Test: `tests/test_plugins.py`

**Interfaces:**
- Consumes: Task 1 `/3` field names; Task 2 `/2` signal fields; Task 3 stats keys and `index` contract.

- [ ] **Step 1: Failing tests:**
  - `test_setup_asks_at_most_six_questions` still passes with exactly 6; new `test_setup_question_six_text_opt_in_defaults_no` — question 6 mentions text/description and "Por defecto, no".
  - `test_recipe_text_off_unless_asked` — `recipe-sharing.md` states missing `sharing.recipe_text` = `off` and builds `text` only under `on`; `setup/SKILL.md` contains `- sharing.recipe_text: off` for reconfigure.
  - `test_sharing_procedure_v3` — `recipe-sharing.md` contains `nuvel.recipe/3`, `nuvel.recipe_signal/2`, `step_notes`, `days_used`, and not `nuvel.recipe/2`, `"event"`.
  - `test_weekly_review_recipe_batch_order` — the five sub-steps appear in order: expire, merge, index, signal, share.
  - `test_no_skill_lists_recipes_folder_to_match` — no `SKILL.md` except `weekly-review` and `learn` contains "list `recipes/`".
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement.** **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `feat(chief-of-staff): weekly recipe batch, structure-only sharing, text opt-in at setup`.

### Task 5: release 0.4.0, size cap, docs (P)

**Files:**
- Modify: the three manifests (`version: 0.4.0`), `references/telemetry.md` version literal, `CHANGELOG.md` (`## chief-of-staff 0.4.0 - <date>` with Changed/Removed sections), `plugins/chief-of-staff/README.md` and root `README.md` privacy wording (structure only by default; text opt-in), `templates/README.md` if it describes recipes.
- Test: `tests/test_plugins.py`, `tests/test_release.py` (already checks releasability)

- [ ] **Step 1: Failing tests:** `test_skill_md_line_cap` — every `skills/*/SKILL.md` ≤ 500 lines; existing `test_telemetry_formats_pin_plugin_version` and `test_current_version_is_releasable` fail until the bump.
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement** (bump, CHANGELOG, README wording; the Catalan/residual-privacy tests must keep passing with the new wording).
- [ ] **Step 4: Run** `uvx --with pytest pytest tests -q`, `claude plugin validate --strict .`, `claude plugin validate --strict plugins/chief-of-staff`, `python3 scripts/release.py check chief-of-staff-v0.4.0` → all PASS.
- [ ] **Step 5: Commit** `chore(chief-of-staff): release 0.4.0`.
