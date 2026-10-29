# Shared recipes v2 (structure + masked narrative) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace v0.3's blocklist-screened free-text recipes with
`nuvel.recipe/2`. The new format has closed structure and typed placeholders,
plus one narrative field. Every free-text field is masked on the server by a
deterministic allowlist before anything is stored, relayed or logged.

**Architecture:** A new stdlib-only module, `nuvel_mcp.masking`, holds the
masker. It takes per-language lexicons, which are package data built by a
committed script from permissive sources. A test corpus with marked secrets
measures leaks and readability, and has a held-out split. `share_recipe`
becomes validate → mask → invariant check → stamp → store → relay. The plugin's
`learn` skill sends structure, placeholders and a narrative; the dashboard
shows them.

**Tech Stack:** Python 3.11 stdlib (re, unicodedata, importlib.resources),
JSON Schema subset validator in `nuvel_mcp.traces`, pytest, Markdown skills.

**Spec:** `docs/superpowers/specs/2026-10-27-recipe-masking-design.md`, in the
nuvel-plugins repo.

**Repos:**
- **P** = `/Users/albertfolch/Documents/Cursor/nuvel-plugins`, branch
  `feat/chief-of-staff-v0.3`. Tests: `uvx pytest tests -q`.
- **N** = `/Users/albertfolch/Documents/Cursor/nuvel/.claude/worktrees/chief-of-staff-plugin-a09233`.
  Tests: `.venv/bin/python -m pytest packages/nuvel-mcp/tests tests -q`.
  Docs: `.venv/bin/mkdocs build --strict`.

## Global Constraints

- `nuvel-mcp` keeps **zero runtime dependencies**. Stdlib only. Python ≥ 3.11.
- **Licence rule** for any lexicon source: public domain or CC0, MIT, BSD, ISC,
  Apache-2.0, CC-BY (no SA, no NC), or another OSI-approved licence with no
  copyleft. **No CC-BY-SA, GPL, LGPL or MPL.** Each source's URL, licence and
  the date it was checked go in `nuvel_mcp/lexicon/SOURCES.md`.
- Raw (unmasked) client text never reaches disk, the relay, `log(...)`, an
  exception message, or a response. Errors are JSON-pointer paths only.
  `masking` functions never raise on `str` input.
- The schema id is `nuvel.recipe/2`; `/1` is removed. Resource:
  `schemas/recipe.v2.schema.json`.
- **Action catalogue (exact, in order):** `search`, `read`, `summarise`,
  `extract`, `compare`, `check`, `calculate`, `list`, `draft`, `edit`,
  `translate`, `create`, `update`, `file`, `propose_slot`, `schedule`, `send`,
  `reply`, `forward`, `share`, `remind`, `follow_up`, `ask`, `decide`, `wait`,
  `other`.
- **Placeholder types (exact, in order):** `person`, `company`, `team`,
  `product`, `project`, `document`, `file`, `folder`, `amount`, `number`,
  `date`, `time`, `period`, `place`, `email`, `phone`, `url`, `id`, `topic`,
  `other`. The server-only mask token is `{?}`.
- **Limits:**
  - `title` ≤ 80
  - `when_to_use` ≤ 200
  - `steps`: 1–15 items
  - `slots`: 0–4 items, unique
  - `note` ≤ 160
  - `pitfalls`: ≤ 5 items of ≤ 160
  - `narrative` ≤ 2000
- **Constants in `masking.py`:**
  - `DROP_THRESHOLD = 0.40`
  - `READABILITY_TARGET = 0.85`
  - `READABILITY_FLOOR = 0.75`
- Zero leaks is the hard constraint. Readability below 75 % for a language
  means that language ships no lexicon (structure only), and this is reported.
- Words removed because they appear in a name, place or brand list are never
  added back. Nothing is added to or removed from a lexicon by hand because of
  a corpus secret.
- Commits: author Folken2 <folkenai21@gmail.com>, conventional prefixes,
  trailer exactly `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
  Never push.

## Review Focus

1. **A recipe in a language with no lexicon** (`pt`, or `ca` if it ships
   structure-only). Expected: it is recorded, every free-text field is dropped
   and listed in `masking.dropped`, and the structure is kept. *Test: Task 5,
   `test_share_unknown_language_drops_text`.*
2. **Empty, all-placeholder or absent free text.** Expected: no division by
   zero; a field with `words == 0` is never dropped. *Test: Task 3,
   `test_zero_word_field_not_dropped`.*
3. **Hostile Unicode:** zero-width joiners inside a name, combining accents,
   fullwidth letters, RTL marks, a 2000-character single token. Expected: the
   masker never raises, and the name is masked. *Test: Task 3,
   `test_hostile_unicode`.*
4. **Client-supplied `tenant`, `masking` or literal `{?}`.** Expected: `tenant`
   and `masking` are rejected by the schema; `{?}` is masked as non-lexicon
   text. *Test: Task 5, `test_client_cannot_send_server_fields`.*
5. **Store or relay failure after masking.** Expected: the logs contain no raw
   text. *Test: Task 5, `test_no_raw_text_on_failure_paths`.*

---

### Task 1: Corpus format, evaluator and the `tune` split

**Files:**
- Create: `packages/nuvel-mcp/tests/masking_corpus.py` (test helper, not shipped)
- Create: `packages/nuvel-mcp/tests/fixtures/masking/tune/{es,en,ca}.jsonl`
- Create: `packages/nuvel-mcp/tests/fixtures/masking/README.md`
- Test: `packages/nuvel-mcp/tests/test_masking_corpus_format.py`

**Interfaces:**
- Produces:
  - `load_corpus(split: str, lang: str) -> list[Case]`, where
    `Case(text: str, secrets: list[str], category: str)`. `text` has the
    `[[…]]` markers removed; `secrets` holds the word tokens inside markers.
  - `evaluate(cases, mask_fn) -> Report(leaks: list[tuple[int, str]], kept: int, total: int)`,
    where `mask_fn(text) -> str`.
  - `fold(s) -> str`: casefold plus strip combining marks (accents).

**Corpus line format:**

```json
{"category": "invoicing", "text": "Hablé con [[Pedro Martínez]] de [[Acme]] sobre la factura de [[veinte mil euros]]."}
```

- [ ] **Step 1: Write failing tests.**
  - `test_markers_parse`: "a [[B c]] d" gives text "a B c d" and secrets
    ["B","c"].
  - `test_every_line_valid`: every line has a category from
    `recipe-categories.md` (the 23 categories plus `other`, listed in the test)
    and at least one secret. No nested or unbalanced markers.
  - `test_tune_size`: at least 90 lines per language.
  - `test_evaluate_counts`: a fake `mask_fn` that keeps everything gives
    leaks == every secret, and kept == total.
  - A leak is a folded secret token that equals a folded word token of the
    output.
- [ ] **Step 2:** Run the tests and confirm they fail.
- [ ] **Step 3:** Implement the helper and write the `tune` corpus.
  - Write ≥ 90 realistic business sentences per language (es, en, ca), spread
    over the categories.
  - Mark only identifying tokens, per spec §6:
    - names and surnames;
    - proper names of companies, products, projects and places;
    - emails, phones, URLs and ids;
    - exact amounts and dates, in digits or in words.
  - Generic nouns are never marked.
  - Cover all of these:
    - lowercase names;
    - names that are common words ("Rosa", "Mercedes", "Pilar", "Bill",
      "Rose");
    - hyphenated and apostrophised surnames;
    - names after `:`, at sentence start, and after a newline or bullet;
    - typos of names;
    - amounts and dates in words;
    - emails, including fullwidth ＠;
    - bare domains;
    - IBAN-like ids.
- [ ] **Step 4:** Run the tests and confirm they pass.
- [ ] **Step 5:** Commit in N: `test(mcp): masking corpus format, evaluator and tune split`.

### Task 2: The `holdout` split (written blind)

The dispatch for this task must be a **separate subagent** that does **not**
read `masking.py`, the lexicon directory or the build script. Those don't exist
yet, and the subagent must not wait for them.

**Files:**
- Create: `packages/nuvel-mcp/tests/fixtures/masking/holdout/{es,en,ca}.jsonl`
- Modify: `packages/nuvel-mcp/tests/test_masking_corpus_format.py`. Add
  `test_holdout_size` (≥ 60 lines per language) and run the line-validity test
  over the holdout split too.

**Interfaces:**
- Consumes: the Task 1 line format and the `load_corpus` helper.

- [ ] **Step 1:** Write ≥ 60 new sentences per language. Use the same marking
  rules and coverage list as Task 1. Use different names, companies and
  phrasing; do not copy from `tune/`.
- [ ] **Step 2:** Run `pytest packages/nuvel-mcp/tests/test_masking_corpus_format.py -q`.
  Expect PASS.
- [ ] **Step 3:** Commit in N: `test(mcp): held-out masking corpus`.
  This commit must come before Task 4.

### Task 3: `nuvel_mcp.masking` (the masker)

**Files:**
- Create: `packages/nuvel-mcp/src/nuvel_mcp/masking.py`
- Modify: `packages/nuvel-mcp/src/nuvel_mcp/recipes.py`. Expose the typed
  regexes for reuse; nothing else changes yet.
- Test: `packages/nuvel-mcp/tests/test_masking.py`

**Interfaces:**
- Consumes: the regexes in `recipes.py` (email, URL, bare domain, phone,
  IBAN, digit run, currency).
- Produces:
  - `Lexicon(words: frozenset[str], numbers: frozenset[str], dates: frozenset[str], currency: frozenset[str], version: str)`.
  - `load_lexicon(language: str) -> Lexicon | None`. Reads package data
    `lexicon/{lang}.txt` (Task 4) with `importlib.resources`, and is cached.
  - `ABBREVIATIONS: frozenset[str]`, loaded from `lexicon/abbreviations.txt`.
  - `mask_text(text: str, lexicon: Lexicon) -> MaskResult(text: str, masked: int, words: int)`.
  - `mask_recipe(recipe: dict, lexicon: Lexicon | None) -> tuple[dict, dict]`.
    It returns the masked copy and `{"lexicon": str|None, "masked": int, "words": int, "dropped": list[str]}`.
    The `dropped` entries are JSON pointers such as `/narrative` or
    `/steps/2/note`.
  - `invariant_hits(recipe: dict) -> list[str]`, returning paths.
  - Constants `DROP_THRESHOLD`, `READABILITY_TARGET` and `READABILITY_FLOOR`,
    with the Global values.

**Algorithm.** Follow spec §4.1 exactly, in this order:
1. Normalise with NFKC, then remove characters in Unicode category `Cf` and
   control characters.
2. Replace typed regexes, in the spec order: `{email}`, `{url}`, `{phone}`,
   `{id}`, `{amount}`, then digit-containing runs → `{number}`.
3. Number words next to a currency word → `{amount}`. Two or more number words
   → `{number}`. A month or weekday next to a number or number word → `{date}`.
4. Tokenise.
5. Known `{type}` placeholders pass as they are.
6. A word passes only if every `-`/`'`/`’` part is in `lexicon.words` (folded)
   **and** it is not Capitalised outside a sentence start.
   - A sentence start is the first word, or the first word after `.`, `!`,
     `?`, `:` or a newline, where a bullet (`-`, `*`, `•`) may come between.
   - Exceptions: `I`, and all-caps words of ≤ 4 letters in `ABBREVIATIONS`.
7. Anything else becomes `{?}`. Consecutive `{?}` collapse into one.

**Counting and dropping.**
- `masked` counts replaced word tokens. `words` counts word tokens plus
  replaced spans.
- Drop a field when `words > 0 and masked / words > DROP_THRESHOLD`.
- `lexicon is None` → drop every free-text field.
- Free-text fields are `title`, `when_to_use`, `steps[].note`, `pitfalls[]` and
  `narrative`.
  - A dropped `title` becomes `""`, because it is required.
  - A dropped `when_to_use` also becomes `""`.
  - Any other dropped field is removed (for a pitfall, the item is removed).
  - Record each one in `dropped`.

**`invariant_hits`** reruns the typed regexes plus rule 6's capitalisation
check over every masked free-text field. It does **not** use
`_capitalised_run`.

- [ ] **Step 1:** Write failing tests. Each test uses an injected tiny
  `Lexicon`; none uses package data.
  - `test_lowercase_name_masked`: "hablé con pedro" gives "hablé con {?}"
    when "pedro" is not in the words.
  - `test_capitalised_common_word_masked_mid_sentence`: "el informe de Rosa"
    gives "el informe de {?}" even when "rosa" is in the words.
  - `test_sentence_start_passes`: "Hecho. El CEO revisa" stays as it is, with
    the words {hecho, el, revisa} and the abbreviation CEO.
  - `test_typed_patterns`: covers the email, URL, phone, IBAN, currency and
    digit cases, and the fullwidth ＠.
  - `test_number_and_date_words`: "veinte mil euros" gives `{amount}`, "dos
    opciones" stays, and "15 de marzo" gives `{date}`.
  - `test_hyphen_parts_all_checked`: "García-López" is masked when either part
    is unknown.
  - `test_client_mask_token_masked`: a literal `{?}` from the client counts as
    masked.
  - `test_unknown_placeholder_masked`: `{foo}` gives `{?}`.
  - `test_collapse`: "a X Y b" gives "a {?} b".
  - `test_drop_rule`: 3 of 5 words masked drops the field; 2 of 5 keeps it.
  - `test_zero_word_field_not_dropped`: an empty string or only placeholders
    is kept, with words == 0.
  - `test_no_lexicon_drops_all_text`.
  - `test_hostile_unicode`: covers ZWJ inside a name, combining accents,
    fullwidth letters, RTL marks, and a 2000-character token. It never
    raises, and the name is masked.
  - `test_invariant_clean_on_masker_output`: property-style; for every
    `tune` corpus line, masked with a small lexicon, `invariant_hits` returns
    [].
  - `test_invariant_flags_planted`: a hand-built masked recipe with an email
    in `/narrative` gives `["/narrative"]`.
- [ ] **Step 2:** Run `pytest packages/nuvel-mcp/tests/test_masking.py -q`.
  Expect FAIL.
- [ ] **Step 3:** Implement `masking.py`.
- [ ] **Step 4:** Run it again. Expect PASS. Run the whole nuvel-mcp suite and
  expect it green.
- [ ] **Step 5:** Commit in N: `feat(mcp): allowlist masker for recipe free text`.

### Task 4: Lexicons from permissive sources, and the corpus gates

**Files:**
- Create: `packages/nuvel-mcp/scripts/build_lexicon.py`. It is not shipped
  and may download sources.
- Create: `packages/nuvel-mcp/scripts/lexicon_src/`, holding
  `business-{lang}.txt`, `numbers-{lang}.txt`, `dates-{lang}.txt` (months and
  weekdays), `currency-{lang}.txt`, `abbreviations.txt` and `sources.json`
  (URL, sha256, licence and checked date per source).
- Create: `packages/nuvel-mcp/src/nuvel_mcp/lexicon/{lang}.txt` for each
  language that passes, plus `abbreviations.txt` and `SOURCES.md`.
- Modify: `packages/nuvel-mcp/pyproject.toml`, where package-data gains
  `"lexicon/*.txt"` and `"lexicon/*.md"`.
- Test: `packages/nuvel-mcp/tests/test_masking_corpus.py` and
  `packages/nuvel-mcp/tests/test_packaging.py` (the lexicon files are in the
  wheel).

**Interfaces:**
- Consumes: `load_lexicon` and the file format from Task 3, and
  `load_corpus` and `evaluate` from Task 1.
- Produces the lexicon file format.
  - Header lines start with `# `:
    - `# version: <lang>-<YYYY.MM.N>`
    - `# sources: <ids>`
    - then sections `# [words]`, `# [numbers]`, `# [dates]` and
      `# [currency]`.
  - After the header, one folded entry per line.
  - **Languages shipped:** each language in `{es, en, ca}` that meets the
    gates. The others ship no file.

**Build** (`python -I scripts/build_lexicon.py --lang es --size N --cache <dir>`):
1. Download each source into a cache directory outside the repo, and verify its
   sha256.
2. Take the base words: the top-N frequency entries, or else a permissive
   lowercase dictionary list.
3. Fold them and keep only alphabetic entries.
4. Subtract every entry found in that language's given-name, surname, place and
   brand lists.
5. Add `business-{lang}.txt`. A business entry is dropped if it is in a name
   list. The script must enforce this.
6. Write the output. Its version id is deterministic.

Pick sources that meet the Global licence rule (for example, government name
statistics released as open data, or SCOWL-style permissive word lists).
Verify each licence at the source page. Never use a CC-BY-SA source, even if
it is convenient.

- [ ] **Step 1: Write the failing gates.** In `test_masking_corpus.py`,
  parametrised over `es`, `en` and `ca` and over both splits:
  - `test_zero_leaks`: `evaluate(...).leaks == []`, using
    `mask_text(text, load_lexicon(lang))`, or, when the lexicon is `None`,
    the drop path, which gives no leaks.
  - `test_readability`: for languages with a lexicon, `kept/total >=
    READABILITY_FLOOR`, and a warning is printed below `READABILITY_TARGET`.
  - `test_lexicon_sources_permissive`: every source in `SOURCES.md` lists a
    licence from an allowlist of SPDX-style ids; `CC-BY-SA*`, `GPL*`, `LGPL*`
    and `MPL*` fail.
  - `test_no_name_list_word_in_lexicon`: a sample of the name lists recorded in
    `sources.json` does not appear in the lexicon (the build writes
    `lexicon_src/removed-sample-{lang}.txt`, the first 500 removed entries).
- [ ] **Step 2:** Run them and expect FAIL (no lexicons yet).
- [ ] **Step 3:** Build, tuning `--size` and the business list against `tune/`
  only.
- [ ] **Step 4:** Run against **both** splits. If `holdout` leaks:
  - fix the masker's rules or the source lists, never by hand-editing for that
    secret;
  - re-run;
  - record each iteration in the task report.

  If a language cannot reach the floor with zero leaks, it ships no lexicon,
  and the report says why.
- [ ] **Step 5:** Run the full nuvel-mcp suite and expect it green.
- [ ] **Step 6:** Commit in N: `feat(mcp): permissive-source lexicons and corpus gates`.

### Task 5: `nuvel.recipe/2` and the `share_recipe` pipeline

**Files:**
- Create: `packages/nuvel-mcp/src/nuvel_mcp/schemas/recipe.v2.schema.json`
- Delete: `packages/nuvel-mcp/src/nuvel_mcp/schemas/recipe.v1.schema.json`
- Modify: `packages/nuvel-mcp/src/nuvel_mcp/recipes.py`. Set
  `RECIPE_SCHEMA_ID = "nuvel.recipe/2"` and
  `RECIPE_RESOURCE = "schemas/recipe.v2.schema.json"`. `screen_recipe` is
  removed, and its callers use `masking.invariant_hits`.
  `screen_signal` stays.
- Modify: `packages/nuvel-mcp/src/nuvel_mcp/server.py`:
  - `tool_share_recipe`;
  - the tool description;
  - the generic `Internal error in {method}` log, which must not include
    exception text for `share_recipe`; log the exception type only.
- Modify: `packages/nuvel-mcp/tests/test_recipe_schema.py` and
  `test_recipe_tools.py`.
- Modify: `packages/nuvel-mcp/tests/fixtures/chief_of_staff/recipe.json`,
  re-made for `/2`. It includes a `narrative` with placeholders and one
  lowercase name, which gets masked.
- Modify: `packages/nuvel-mcp/tests/test_plugin_trace_fixtures.py`.

**Interfaces:**
- Consumes: `masking.mask_recipe`, `masking.invariant_hits` and
  `masking.load_lexicon`.
- Produces the `share_recipe` responses (spec §5):
  - stored → `{"status":"recorded","recipe_id","version","masked":N,"words":M,"dropped":[...]}`;
  - already stored → `{"status":"duplicate","recipe_id","version"}`;
  - errors → `ToolInputError(paths)`, as today.
- The stored record is the masked copy plus `tenant` (when present) plus
  `masking`.

**Schema.** Closed at every level, with the spec §1 fields and the Global
limits and enums. `steps[].slots` has `uniqueItems: true`; add that keyword
to the `traces` validator if it is missing, with a test. `masking` and
`tenant` are **not** in `properties`, so `additionalProperties: false`
rejects them.

**Pipeline:**
```
validate_recipe
  → mask_recipe(recipe, load_lexicon(recipe["language"]))
  → invariant_hits
  → stamp tenant + masking
  → put_recipe
  → relay the stored record
```
The raw `recipe` is never passed to `log`, the store or the relay, and is not
kept on `self`.

- [ ] **Step 1:** Write failing tests.
  - `test_v2_schema_accepts_fixture`.
  - `test_v1_shape_rejected`: a step with `text` and without `slots` is
    rejected.
  - `test_action_enum_exact`: the enum equals the Global list, in order.
  - `test_placeholder_enum_exact`.
  - `test_client_cannot_send_server_fields`: `tenant` → rejected;
    `masking` → rejected; `{?}` in the narrative → recorded, with that token
    counted as masked.
  - `test_share_masks_before_store`: a narrative containing
    "pedro" and "Acme S.L." produces a stored file and relay payload (with
    the relay stubbed via `NUVEL_FEEDBACK_URL` and a monkeypatched
    `_relay_feedback`) that contain neither name, and the response carries
    `masked >= 2`.
  - `test_share_unknown_language_drops_text`: `language: "pt"` → recorded,
    with every free-text field in `dropped`.
  - `test_invariant_hit_rejects`: monkeypatch `mask_recipe` to return text
    with an email → `ToolInputError` with the paths, and nothing stored.
  - `test_no_raw_text_on_failure_paths`: in three cases (the store raises
    `OSError`, the relay raises, `mask_recipe` raises), use `capsys` or a
    patched `log` and assert that no secret appears in any log line or
    response.
  - The duplicate path is unchanged.
- [ ] **Step 2:** Run and expect FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run the full nuvel-mcp suite and expect it green.
- [ ] **Step 5:** Commit in N: `feat(mcp)!: nuvel.recipe/2 with server-side masking`.

### Task 6: Dashboard and CLI view

**Files:**
- Modify: `nuvel/recipes_view.py`. `latest` exposes the actions sequence,
  slots, the masked narrative and `mask_ratio`. Files whose `schema` is not
  `nuvel.recipe/2` are skipped and counted in a new `skipped_v1: int` on the
  result.
- Modify: the dashboard `/recipes` template (`recipes.html`).
  - Render `search → summarise → draft`.
  - Render `{type}` and `{?}` as visually marked chips.
  - Render the narrative inside a `<details>` block.
  - Show the mask ratio as a percentage.
  - Escape all text.
- Modify: the `nuvel traces recipes` output, which gains one line of action
  sequence per category.
- Test: `tests/test_recipes_view.py` and `tests/test_dashboard_recipes.py`.

**Interfaces:**
- Consumes: the stored `/2` record shape (Task 5).

- [ ] **Step 1:** Write failing tests.
  - `test_latest_has_structure_and_narrative`.
  - `test_v1_files_skipped`.
  - `test_dashboard_escapes_narrative`: a narrative containing `<script>`
    is escaped.
  - `test_non_list_steps_do_not_500`: covers the deferred v0.3 minor; a
    malformed file is skipped.
- [ ] **Step 2:** Run and expect FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run and expect PASS.
- [ ] **Step 5:** Commit in N: `feat(dashboard): recipe structure and masked narrative`.

### Task 7: Plugin `learn`, the action catalogue and the docs (P), plus the nuvel docs (N)

**Files (P):**
- Create: `plugins/chief-of-staff/references/recipe-actions.md`. It holds the
  Global action list with one plain line each, and the placeholder list.
- Modify: `plugins/chief-of-staff/skills/learn/SKILL.md`, rewriting the share
  section per spec §7. Specifically:
  - remove the self-check-and-block step and `share: blocked (pii)`;
  - give the new field table;
  - journal lines `share: recorded (masked N/M)` and
    `share: recorded, <fields> dropped`;
  - keep `blocked_version` only for `"rejected"`.
- Modify: `plugins/chief-of-staff/references/telemetry.md`, wherever recipe
  fields are described.
- Modify: `plugins/chief-of-staff/README.md`, the root `README.md` and
  `CHANGELOG.md`. The privacy wording is spec §7's sentence.
- Modify: `plugins/chief-of-staff/skills/learn/trace-steps.json` only if its
  counts change. The `shares_blocked` count now means "rejected"; keep the key.
- Test: `tests/test_plugins.py` gains:
  - `test_recipe_actions_catalogue`: the action identifiers in
    `recipe-actions.md`, in order, equal the Global list, hardcoded in the
    test.
  - `test_learn_share_table_v2`: the learn SKILL.md mentions `nuvel.recipe/2`,
    `slots` and `narrative`, and does not mention `share: blocked (pii)`.

**Files (N):**
- Modify: `packages/nuvel-mcp/tests/fixtures/chief_of_staff/learn.json`, if
  the trace counts changed.
- Modify: `docs/reference/skill-run-traces.md` (the recipe section → `/2`,
  masking, lexicons and licence rule), `docs/.../deploy-skills-mcp.md` (if it
  names recipe fields), and the N `CHANGELOG.md` (a breaking-change note).
- Test: in N, add an optional cross-repo check,
  `test_actions_match_plugin_catalogue`. It runs only when the env var
  `NUVEL_PLUGINS_DIR` is set, and compares the schema enum with
  `recipe-actions.md`. Otherwise it is skipped with a reason.

- [ ] **Step 1:** Write the failing P tests and run `uvx pytest tests -q`.
  Expect FAIL.
- [ ] **Step 2:** Implement the P changes and run again. Expect PASS.
- [ ] **Step 3:** Implement the N docs and test, then run the N suite with
  `NUVEL_PLUGINS_DIR=/Users/albertfolch/Documents/Cursor/nuvel-plugins`.
  Expect PASS. Run `mkdocs build --strict` and expect it to pass.
- [ ] **Step 4:** Commit in P:
  `feat(chief-of-staff): share recipes as structure plus masked narrative`.
  Commit in N: `docs: recipe v2 masking`.
