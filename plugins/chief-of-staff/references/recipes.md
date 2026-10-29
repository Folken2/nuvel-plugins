# Recipes

How a private recipe lives in the registry: its document, its states, its
stats, when it counts a success, and the `index` that *Before a task* reads.
The registry's general rules (append-only, names, folders) are in
`registry-layout.md`. Written by `learn` (create, promote, update, retire,
index) and by `weekly-review` (expire, merge, rebuild the index, share).
Sharing is in `recipe-sharing.md`.

## Document: `recipe <slug>`

How a complex or recurring task was done well: a lightweight skill. One
document per version, `recipes/YYYY-MM-DD HHMM recipe <slug>`; the newest
version per slug wins.

```markdown
# Recipe · Preparar propuesta de cliente

## When to use
Cuando un cliente pide una propuesta o presupuesto nuevo.

## Steps
1. Buscar en los correos la petición del cliente y la última propuesta enviada.
2. …

## Pitfalls
- …

## Stats
- uses: 4
- successes: 2
- corrections: 1
- days_used: 3
- last_used: 2026-11-02
- last_outcome: success
- recipe_id: <uuid4, fixed for the life of the recipe>
- category: client-proposal
- status: active          (draft|active|retired)
- version: 2
- shared_version: 0
- blocked_version: 0
```

- `status` is `draft` (the task may come back; never followed), `active` (in
  the `index`, followed before a task) or `retired` (ignored).
- `last_outcome` is `success` (the user approved the result), `silent` (no
  approval) or `corrected`.
- `category` is one identifier from `recipe-categories.md`.
- `shared_version` is the last `version` shared with nuvel (0 = never);
  `blocked_version` is the last `version` whose share the server rejected
  (0 = never).
- A recipe is private to the user's registry and may name people; only its
  structure (and, with `sharing.recipe_text: on`, its masked text) ever leaves
  it (`recipe-sharing.md`).

## States: `draft` → `active` → `retired`

- **Draft.** After a complex or multi-step task that no recipe matches (active
  or draft), `learn` writes the recipe with `status: draft`. A draft is a
  guess that the task may come back. Drafts are never read by *Before a task*,
  never put in the `index`, and never shared or signalled.
- **Promote.** After a later complex task, before creating a draft, compare
  the task with the drafts' *When to use*. A match → a new version of that
  recipe with `status: active`, steps refined from both runs, `version` +1.
  The task that promotes it counts as a use (*Stats*: the use). This
  comparison happens after the task, so it never delays the user.
- **Direct active.** The user says the task will recur ("cada mes", "every
  Monday", "lo haremos más veces") → write it `active` straight away (new
  recipe, or a draft promoted).
- **Expire.** The weekly review retires drafts whose `last_used` is more than
  60 days old.
- **Retire.** "Bórrala" / "esa no" → a new version with `status: retired`.
  Skills ignore retired recipes.

Nothing else creates an active recipe. A one-off task, however long, stays a
draft until it comes back or the user says it will.

## Create

- slug in lowercase ASCII with hyphens (`propuesta-cliente`);
- `recipe_id` a new random UUIDv4 (format in `telemetry.md` *Formats*), fixed
  for the life of the recipe;
- `category` exactly one identifier from `recipe-categories.md` (closest fit,
  else `other`);
- stats `uses: 0`, `successes: 0`, `corrections: 0`, `days_used: 0`,
  `last_used` = today, `last_outcome: silent`, `version: 1`,
  `shared_version: 0`, `blocked_version: 0`, `status: draft` (or `active`, as
  above). The run that wrote it is not a use; only later tasks that follow it
  count.

Write the steps as they actually worked, folding in what the user corrected
along the way. The private recipe may name people and tools; it lives in the
user's own registry.

## Stats

Kept in the recipe's `## Stats`: `uses`, `successes`, `corrections`,
`days_used`, `last_used`, `last_outcome` (`success`, `silent` or
`corrected`), plus `recipe_id`, `category`, `status`, `version`,
`shared_version`, `blocked_version`.

A use is recorded in two steps, each its own `learn` run with its own new
version.

**1. The use, written once, at the end of the task** that followed the recipe
(or promoted the draft), with the stats carried forward and changed:

- `uses` +1. `days_used` +1 when today is a different date from `last_used`.
  Then `last_used` = today.
- `last_outcome: silent`. Nobody has reacted yet.

The use is written once: a later run never adds to `uses` or `days_used` for
the same use.

**2. The outcome, written when the user reacts** later in the same
conversation. That reaction triggers a separate `learn` run, whose new version
changes only `successes` or `corrections` and `last_outcome` (plus, for a
correction, its fix in *Steps* or *Pitfalls*), never `uses` or `days_used`:

- **Success = explicit approval only.** In an interactive run the user says
  the result worked ("perfecto", "esto es lo que quería", "this worked",
  "great, thanks" about the result) → `successes` +1, `last_outcome: success`.
- **Silence is not a success.** No reply, the user leaving, a change of
  subject or a scheduled run (nobody sees the result) → nothing more is
  written; the use stays `last_outcome: silent`, no success and no correction.
- **Correction** → `corrections` +1, `last_outcome: corrected`, and fold the
  fix into *Steps* or *Pitfalls*, so `version` +1. A correction after an approval keeps the
  success (`successes` is never lowered).
- `last_outcome` is always the latest outcome: an approval after a correction
  sets it back to `success`.

Example: the user asks for a proposal and the recipe `propuesta-cliente` is
followed. At the end of the task, `learn` writes version A: `uses` 4 → 5,
`days_used` 3 → 4, `last_outcome: silent`. Ten minutes later the user says
"perfecto": a new `learn` run writes version B from A: `successes` 2 → 3,
`last_outcome: success`, `uses` and `days_used` unchanged. Two runs, one
document each.

In both steps:

- `version` +1 only when *When to use*, *Steps* or *Pitfalls* change (or the
  status changes); a stats-only update keeps it.
- `shared_version` and `blocked_version` are carried forward unchanged. Only
  the weekly review changes them (`recipe-sharing.md`).

## Quality bar

A recipe is good enough to share when all hold: `status: active`,
`successes` ≥ 1, `days_used` ≥ 3 and `last_outcome` is not `corrected`. The
weekly review applies it (`recipe-sharing.md`); `learn` never does.

## One document per recipe per run

Work out the new version in memory first (state, stats, steps), then write
**one** recipe document. Never write a second version of the same recipe in
the same run: registry names have minute precision and the registry never
overwrites. The rule is per run: the use and a later approval or correction
are two runs, so two versions (example above).

## Migration of older recipes

A recipe written before v0.4 (or through the Project-instructions fallback)
gets the missing fields on its next write, and its status is unchanged:

- missing `days_used` → `1` if `uses` > 0, else `0`;
- missing `last_outcome` → `silent`;
- missing `recipe_id` or `category` → set them now. A migrated recipe is not
  a new recipe: it never counts in `recipes_created` or `drafts_created`;
- missing `version` → `1`; missing `shared_version` or `blocked_version` → `0`.

## Index

One document, `recipes/YYYY-MM-DD HHMM index`, holds the full list of
**active** recipes; the newest `index` wins, like `lessons`. Drafts and
retired recipes are not in it.

```markdown
# Recipes index

## client-proposal
- propuesta-cliente — Cuando un cliente pide una propuesta o presupuesto nuevo.

## monthly-close
- cierre-mes — Al acabar el mes, para revisar facturas y cobros pendientes.
```

One `## <category>` per category with at least one active recipe, then one
line per recipe: `- <slug> — <When to use, on one line>`.

**Reading it** (*Before a task*): read only the newest `index`, one read. No
index → no recipe lookup at all; never list `recipes/` to look for one.
Match the task against the one-line *When to use* under the likeliest
category first, then the rest; open only the matched recipe's newest
version.

**Writing it.** `learn` writes a new `index` in the same run whenever the set
of active recipes or an active recipe's *When to use* changes (promote,
direct active, retire, a new *When to use*). Stats-only updates never touch
it. `learn` writes the first `index` when none exists and active recipes do,
so a registry from v0.3 gets one at the next `learn` run, whatever triggered
that run. Until then *Before a task* finds no index and does no lookup. The weekly review
rebuilds it every week and so heals any drift.
