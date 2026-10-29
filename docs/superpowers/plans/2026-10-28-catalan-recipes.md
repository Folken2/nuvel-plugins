# Catalan recipe masking Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Ship a `ca` lexicon so Catalan recipes share a masked narrative, and
add a fresh blind held-out corpus as the acceptance gate for all three
languages.

**Architecture:** Add a new general Wikidata source class (regional
companies) and Catalan clitic elisions to the existing build and masker. Then
build `ca.txt`, gate it on tune, holdout and holdout2, and update the plugin
and docs.

**Tech Stack:** Python 3.11 stdlib, pytest, Markdown skills.

**Spec:** `docs/superpowers/specs/2026-10-27-recipe-masking-design.md`, the
"Addendum 2026-10-28: Catalan support" section.

**Repos:**
- **P** = `/Users/albertfolch/Documents/Cursor/nuvel-plugins`
  (`uvx pytest tests -q`).
- **N** = `/Users/albertfolch/Documents/Cursor/nuvel/.claude/worktrees/chief-of-staff-plugin-a09233`
  (`.venv/bin/python -m pytest packages/nuvel-mcp/tests tests -q`;
  `.venv/bin/mkdocs build --strict`).

## Global Constraints

- All constraints of `docs/superpowers/plans/2026-10-27-recipe-masking.md`
  still apply: the licence rule, stdlib only, no raw text in
  logs/errors/responses, zero leaks is hard, no per-entry hand edits, Folken2
  plus the Opus 5.5 trailer, never push.
- `holdout2/` is written blind and committed before Task 2 starts.
  - It is measured exactly once, at the end of Task 2, reporting counts only,
    and nobody opens it.
  - Any change after a holdout2 leak is general, and the report records that
    holdout2 was used.
- `holdout/` stays as a regression gate.

## Review Focus

1. **A clitic chain spelling a name** (`envia'l'm'n`, `fes-me-li-ho`):
   masked, with at most one suffix clitic group. *Test: Task 2,
   `test_ca_clitic_chains`.*
2. **A lowercase regional brand that is a common word**, e.g. "arc": masked
   via the new source class. *Test: Task 2, the corpus gates.*
3. **es and en regressions** from the shared sources: zero leaks on all
   splits. *Test: Task 2, the gates.*
4. **The `ca` reader:** `load_lexicon("ca")` returns a Lexicon with
   `language == "ca"`. *Test: Task 2.*
5. **No stale "structure only" text** for Catalan in either repo. *Test:
   Task 3, the grep test.*

---

### Task 1: Blind `holdout2` corpus (es, en, ca)

The subagent must NOT read `masking.py`, `lexicon/`, `lexicon_src/`,
`build_lexicon.py`, `tune/` or `holdout/`.

**Files:**
- Create: `packages/nuvel-mcp/tests/fixtures/masking/holdout2/{es,en,ca}.jsonl`
- Create: `packages/nuvel-mcp/tests/test_masking_holdout2_format.py`
- Modify: `packages/nuvel-mcp/tests/fixtures/masking/README.md`, adding
  one paragraph.

**Interfaces:** consumes `masking_corpus.load_corpus` and `evaluate`, and
follows the README marking rules exactly.

- [ ] **Step 1:** Write ≥ 60 lines per language, following the README rules.
  - Cover the README coverage list.
  - Catalan-specific cases:
    - lowercase local brands and companies that are also common words;
    - clitics such as "envia-li", "fes-ho" and "recorda'm";
    - elisions (l', d');
    - names that are common words (Rosa, Pilar, Mercè, Jordi, Pau).
- [ ] **Step 2:** Add format tests: size ≥ 60, line validity, secrets are
  tokens of the text, and an oracle masker scores 0 leaks.
- [ ] **Step 3:** Run them, expecting PASS, then commit in N:
  `test(mcp): blind holdout2 masking corpus`.

### Task 2: Catalan lexicon and clitics

**Files:**
- Modify: `packages/nuvel-mcp/scripts/build_lexicon.py`, the
  `scripts/lexicon_src/sources.json` and `SOURCES.md` generation, and the ca
  input files under `lexicon_src`.
- Modify: `packages/nuvel-mcp/src/nuvel_mcp/masking.py` (ca suffix and
  hyphen clitics, per the addendum), and the invariant independently.
- Create: `packages/nuvel-mcp/src/nuvel_mcp/lexicon/ca.txt`
- Modify: `packages/nuvel-mcp/tests/test_masking.py` and
  `test_masking_corpus.py`, parametrising over holdout2 as well.
- Modify: the ca guard in `build_lexicon.py`; remove it if ca ships.

**Interfaces:** consumes the Task 1 holdout2 files, and the existing
build and masker APIs.

- [ ] **Step 1:** Write failing tests:
  - `test_ca_clitics_pass`: "envia'l", "fes-ho", "recorda'm", "dona-li"
    pass with a tiny ca lexicon.
  - `test_ca_clitic_chains`: masked, per Review Focus 1.
  - `test_ca_lexicon_loads`: skipped if `ca.txt` is absent.
- [ ] **Step 2:** Add the source class from the addendum. Verify its licence
  at the source and record it in `sources.json`. Rebuild ca, plus es and en if
  the shared source affects them. Tune on `tune/` only; holdout is a
  regression gate, read as counts.
- [ ] **Step 3:** Run holdout2 once, as counts only, for es, en and ca.
  - If anything leaks, make general fixes only, and record that holdout2 was
    used.
  - If ca cannot reach zero leaks on all three splits with readability
    ≥ 75 %, ship no ca.txt and report exactly what is missing.
- [ ] **Step 4:** Run the full suite and the packaging test (ca.txt is in the
  wheel). Commit in N: `feat(mcp): Catalan lexicon and clitics`.

### Task 3: Plugin and docs say Catalan is masked

**Files:**
- In P:
  - `plugins/chief-of-staff/skills/learn/SKILL.md`
  - `plugins/chief-of-staff/references/telemetry.md`
  - the READMEs and `CHANGELOG.md`
- In N:
  - `docs/reference/skill-run-traces.md`
  - `CHANGELOG.md`
  - any other docs that say ca is structure only

**Interfaces:** consumes Task 2's outcome. If ca did not ship, this task only
records the outcome in the CHANGELOG.

- [ ] **Step 1:** Write the failing tests:
  - P: `test_no_catalan_structure_only`, a grep over plugins/ and the READMEs;
  - N: the same grep over docs/ and packages/nuvel-mcp/src.
- [ ] **Step 2:** Update the wording. Add a learn example note in Catalan.
- [ ] **Step 3:** Run both suites and mkdocs. Commit in P and in N:
  `docs: Catalan recipes are masked like es and en`.
