# chief-of-staff v0.4 — honest recipes, structure-only sharing

Date: 2026-10-29. Status: approved in chat (structure only by default, text
opt-in; "go ahead with v0.4").

## Why

A review of v0.3's `learn` skill (from a separate Claude session, verified
against the skill text) found:

1. **Recipes fire too often.** The trigger "the task took several tool calls or
   multiple steps" covers almost every agent task, so one-off tasks become
   recipes, and *Before a task* lists `recipes/` before most multi-step chats.
2. **Silence counts as success.** A use with no correction in the same
   conversation is a success; users often just leave, so three silences pass a
   mediocre recipe.
3. **Matching won't scale.** Reading every recipe's *When to use* works at ~10
   recipes, not ~50. The weekly review merges duplicate lessons, not recipes.
4. **Sharing is the biggest trust risk.** Free text in the user's words
   (narrative, and also title, when-to-use, step notes, pitfalls) leaves the
   registry before the server masks it, and the masker admits a residual
   class. For EU business clients this is a GDPR conversation.
5. **`learn` does too much.** Lessons, recipes, signals and sharing with exact
   ordering rules (`shared_version`, `blocked_version`, one document per run);
   the more fiddly rules, the more a model skips one.

Lessons are the strongest part and stay as they are.

## Goals

- Recipes exist only for tasks that recur, and count success only on evidence.
- *Before a task* costs one small read, and matching works at 50 recipes.
- Sharing sends **structure only** by default: no free text of any kind leaves
  the registry unless the user opted in, in setup, by answering a question.
- `learn` handles lessons and private recipes only; signals and sharing move
  to one weekly batch.

## Non-goals

- Changing lessons (format, scope, reading).
- Hosting the nuvel connector, or any server-side deployment.
- Backwards compatibility with `nuvel.recipe/2` or `nuvel.recipe_signal/1`: no
  hosted server ever accepted them, so no client depends on them.

## Anti-goals

- Any path where text in the user's words is sent without `sharing.recipe_text:
  on` written in `config` after the user said yes.
- Recipes that silently pile up: every draft is either promoted or expires.

## 1. Recipe lifecycle (plugin)

**States:** `draft` → `active` → `retired`.

- **Draft.** After a complex or multi-step task that no recipe (active or
  draft) matches, `learn` writes the recipe with `status: draft`. Drafts are
  never read by *Before a task* and never shared or signalled.
- **Promote.** After a later complex task, before creating a draft, `learn`
  compares the task with the drafts' *When to use*. A match → a new version of
  that recipe with `status: active`, steps refined from both runs. This
  comparison happens after the task, so it never delays the user.
- **Direct active.** If the user says the task will recur ("cada mes", "every
  Monday", "lo haremos más veces"), `learn` writes it `active` straight away.
- **Expire.** The weekly review retires drafts whose `last_used` is more than
  60 days old.
- **Retire.** "Bórrala" / "esa no" → `status: retired`, as today.

**Stats** (in the recipe's `## Stats`): `uses`, `successes`, `corrections`,
`days_used`, `last_used`, `last_outcome`, plus `recipe_id`, `category`,
`status`, `version`, `shared_version`, `blocked_version` as in v0.3.

- `uses` +1 on every use; `days_used` +1 when the use is on a different date
  from `last_used`; then `last_used` = today.
- **Success = explicit approval only.** In an interactive run the user says the
  result worked ("perfecto", "esto es lo que quería", "this worked", "great,
  thanks" about the result) → `successes` +1, `last_outcome: success`.
  Silence, leaving, or a scheduled run → `last_outcome: silent`, no success.
- A correction → `corrections` +1, `last_outcome: corrected`, fix folded into
  *Steps* or *Pitfalls*. A correction after an approval in the same
  conversation does not undo the success; it sets `last_outcome: corrected`.
  (v0.3's "move the success" rule is removed.)
- **Quality bar** (for sharing, §3): `status: active`, `successes` ≥ 1,
  `days_used` ≥ 3, `last_outcome` ≠ `corrected`.
- One recipe document per recipe per run stays (names have minute precision).

**Migration** of a v0.3 recipe on its next write: missing `days_used` → `1` if
`uses` > 0 else `0`; missing `last_outcome` → `silent`; status is unchanged.

## 2. Recipe index (plugin)

`recipes/YYYY-MM-DD HHMM index` is the full list of **active** recipes, newest
wins, like `lessons`:

```markdown
# Recipes index

## <category>
- <slug> — <When to use, one line>
```

- **Before a task** reads only the newest index (one read). No index → no
  recipe lookup at all (no listing of `recipes/`). Match the task against the
  one-line *When to use* under the likeliest category first, then the rest;
  open only the matched recipe's newest version.
- `learn` writes a new index in the same run whenever the set of active
  recipes or an active recipe's *When to use* changes (promote, direct active,
  retire, text change). Stats-only updates do not touch the index.
- The weekly review rebuilds it (§4) and so heals any drift.
- `index` is added to the document kinds in `registry-layout.md`.

## 3. Sharing (server schema `nuvel.recipe/3`, plugin procedure)

### Settings (`config`)

| key | default | meaning |
|---|---|---|
| `telemetry` | `on` | traces and recipe signals (content-free) |
| `sharing.recipes` | `on` | share the **structure** of recipes that pass the quality bar |
| `sharing.recipe_text` | `off` | also share the text, masked on the server |

- `sharing.recipe_text` is `on` **only** when the user answered yes to setup's
  question 6. A missing key means `off`. Reconfigure never turns it on without
  asking; an older `config` without it gets `- sharing.recipe_text: off`.
- `sharing.recipes: off` → nothing is shared, regardless of `recipe_text`.

### Setup question 6 (plugin)

Setup's §2 gets a sixth question, in plain words, default no:

> Cuando una forma de trabajar te funciona varias veces, puedo enviar a nuvel su esquema (qué pasos, en qué orden, sin ningún texto tuyo) para mejorar el producto. ¿Quieres que además envíe la descripción en tus palabras, con los nombres y las cifras sustituidos? Por defecto, no.

Structure sharing itself is still told, not asked (wrap-up notice updated:
"solo el esquema, nunca tu texto").

### `nuvel.recipe/3` (server)

```json
{
  "schema": "nuvel.recipe/3",
  "recipe_id": "<uuid4>",
  "install_id": "<uuid4>",
  "plugin": {"name": "chief-of-staff", "version": "0.4.0"},
  "version": 3,
  "category": "client-proposal",
  "steps": [{"action": "search", "tool_kind": "email", "slots": ["person", "company"]}],
  "stats": {"uses": 7, "successes": 2, "corrections": 1, "days_used": 4},
  "text": {
    "language": "es",
    "title": "...", "when_to_use": "...",
    "step_notes": ["..."], "pitfalls": ["..."], "narrative": "..."
  }
}
```

- Required: everything except `text`. `steps` 1–15 of `{action, tool_kind,
  slots}` with the v2 enums; **no `note` in steps** (notes moved to
  `text.step_notes`). `stats` integers 0–100000, `successes` and
  `corrections` ≤ `uses`, `days_used` ≤ `uses`.
- `text` optional. Inside it, `language` required; `title` ≤ 80,
  `when_to_use` ≤ 200, `step_notes` ≤ 15 × 160 and no longer than `steps`,
  `pitfalls` ≤ 5 × 160, `narrative` ≤ 2000, all optional. The v2 masking
  pipeline applies unchanged to every `text` string (mask → invariant →
  re-validate → stamp `masking` → store); the drop rule and unmaskable
  languages drop fields as today; `dropped` pointers become `/text/...`.
- A recipe with no `text` skips masking entirely and is stored with
  `masking: {"lexicon": null, "masked": 0, "words": 0, "dropped": []}`.
- `tenant` and `masking` from the client → rejected, as in v2.
- `nuvel.recipe/2` is removed (schema file, validators, tests), as /1 was.
- Reply unchanged: `recorded` (with `masked`, `words`, `dropped`),
  `duplicate`, `rejected` (field paths only, client keys as `*`).

### Plugin procedure (`references/recipe-sharing.md`, new)

Run by the weekly review (§4), never by `learn`. For each recipe that passes
the quality bar and whose `version` > `shared_version` and > `blocked_version`:

1. Build `steps` (action, tool_kind, slots) and `stats` from the private
   recipe.
2. Only if `sharing.recipe_text: on`: build `text` exactly as v0.3 built its
   free text (placeholders, `owner.language`, examples carried over), with the
   step notes in `text.step_notes`.
3. Call `share_recipe`, read the reply as in v0.3 (`recorded` / `duplicate` →
   `shared_version`; `rejected` → `blocked_version`; error → retry once, journal
   the class). The outcome goes into the one new recipe version the weekly
   review writes for that recipe this run.

## 4. Weekly batch (plugin + server)

The weekly review gains one step, after *Merge duplicate lessons*, running in
this order and writing at most one new version per recipe:

1. **Expire drafts** (§1).
2. **Merge duplicate recipes.** Two active recipes for the same task → keep the
   one with more `successes` (tie: newer `last_used`); its new version folds in
   the other's *Pitfalls* and sums `uses`, `successes`, `corrections`,
   `days_used`; the other gets `status: retired`.
3. **Rebuild the index** (§2) from the result: one new `index` document if it
   differs from the newest.
4. **Signals** (only with `record_recipe_signal`, `telemetry: on`,
   `install_id`): one `nuvel.recipe_signal/2` per recipe whose stats or status
   changed since the last weekly review (a recipe document newer than the last
   `weekly-review` run).
5. **Share** (`recipe-sharing.md`).

Counts for the trace: `drafts_expired`, `recipes_merged`, `index_written`,
`signals_sent`, `signals_failed`, `shares_sent`, `shares_blocked`,
`shares_failed`, `shares_with_text` on new step ids
`weekly-review.recipes` and `weekly-review.share`.

### `nuvel.recipe_signal/2` (server)

A weekly snapshot, content-free:

```json
{"schema": "nuvel.recipe_signal/2", "signal_id": "<uuid4>", "recipe_id": "<uuid4>",
 "install_id": "<uuid4>", "plugin": {"name": "chief-of-staff", "version": "0.4.0"},
 "category": "client-proposal", "status": "draft|active|retired",
 "at": "2026-11-06T17:00:00Z",
 "uses": 7, "successes": 2, "corrections": 1, "days_used": 4}
```

Same validation style as /1 (dedupe on `signal_id`, `tenant` rejected); the
`event` enum is gone. `/1` is removed. The dashboard and `nuvel traces
recipes` read /2 snapshots (latest per `recipe_id`).

## 5. `learn` after v0.4

`learn` keeps: *Before a task* (index only), lessons (unchanged), recipes
(draft/promote/active/retire, stats, index write), journal and the one-line
reply. It loses §4 *Signals* and §5 *Sharing*, the `record_recipe_signal` and
`share_recipe` tools, and every `shared_version` / `blocked_version` rule
(those fields are carried forward unchanged by `learn`; only the weekly
review changes them). Trace steps `learn.signal` and `learn.share` are
removed from its catalog.

## 6. Skill size (best practice, user requirement)

- Every `SKILL.md` stays within **500 lines** (hard cap, tested), aiming for
  200–300: the skill body says *what* to do and *when*; long procedures,
  formats and tables live in `references/` (one topic per file) and are cited
  by relative path. v0.4 moves `learn`'s sharing and signal procedure out to
  `references/recipe-sharing.md` and the recipe lifecycle details (stats rules,
  migration, index format) to `references/recipes.md`, so `learn` shrinks.
- Deterministic helpers (e.g. UUIDv4 generation, timestamp format) may ship as
  `scripts/` in the plugin, but every skill must still work on hosts without a
  code tool (Cowork, cloud routines), so a script is always optional.
- New and edited reference files stay focused; any reference over ~300 lines
  is split by topic.

## 7. Docs and tests

- Plugin: `learn`, `weekly-review`, `setup` SKILL.md; `registry-layout.md`
  (recipe stats, `index` kind, settings); `telemetry.md` (recipe/3, signal/2,
  switches table with `sharing.recipe_text`); new `recipe-sharing.md`; README,
  CHANGELOG 0.4.0; all three manifests 0.4.0; trace catalogs.
- Server: `recipes.py`, schemas, `server.py` pipeline, local store, dashboard
  recipes view and `nuvel traces recipes`, `docs/reference/skill-run-traces.md`,
  CHANGELOG.
- A test caps every `SKILL.md` at 500 lines.
- Tests that pin the anti-goals: no `share_recipe` / `record_recipe_signal` in
  `learn`; setup has exactly 6 questions and question 6 defaults to no; text
  is built only under `sharing.recipe_text: on`; server stores a text-free
  recipe with zero masking work and rejects `steps[].note`, `tenant`,
  `masking`, oversized `step_notes`.

## Left to the builder

Exact wording of user-facing lines (in the plugin's existing style, Spanish
examples first); test names; whether the dashboard shows a "text shared"
badge.
