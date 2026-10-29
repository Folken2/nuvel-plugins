# Recipes

How a private recipe lives in the registry: its states, its stats, when it
counts a success, and the `index` that *Before a task* reads. The document
format is in `registry-layout.md` (*`recipe <slug>`* and *`index`*). Written
by `learn` (create, promote, update, retire, index) and by `weekly-review`
(expire, merge, rebuild the index, share). Sharing is in `recipe-sharing.md`.

## States: `draft` → `active` → `retired`

- **Draft.** After a complex or multi-step task that no recipe matches (active
  or draft), `learn` writes the recipe with `status: draft`. A draft is a
  guess that the task may come back. Drafts are never read by *Before a task*,
  never put in the `index`, and never shared or signalled.
- **Promote.** After a later complex task, before creating a draft, compare
  the task with the drafts' *When to use*. A match → a new version of that
  recipe with `status: active`, steps refined from both runs, `version` +1.
  This comparison happens after the task, so it never delays the user.
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

After a task that followed a recipe, write a new version with the stats
carried forward and changed:

- `uses` +1, every time. `days_used` +1 when today is a different date from
  `last_used`. Then `last_used` = today.
- **Success = explicit approval only.** In an interactive run the user says
  the result worked ("perfecto", "esto es lo que quería", "this worked",
  "great, thanks" about the result) → `successes` +1, `last_outcome: success`.
- **Silence is not a success.** No reply, the user leaving, a change of
  subject or a scheduled run (nobody sees the result) → `last_outcome:
  silent`, no success and no correction.
- **Correction** → `corrections` +1, `last_outcome: corrected`, and fold the
  fix into *Steps* or *Pitfalls*. A correction after an approval in the same
  conversation keeps the success and sets `last_outcome: corrected`.
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
overwrites.

## Migration of older recipes

A recipe written before v0.4 (or through the Project-instructions fallback)
gets the missing fields on its next write, and its status is unchanged:

- missing `days_used` → `1` if `uses` > 0, else `0`;
- missing `last_outcome` → `silent`;
- missing `recipe_id` or `category` → set them now (counts as created);
- missing `version` → `1`; missing `shared_version` or `blocked_version` → `0`.

## Index

`recipes/YYYY-MM-DD HHMM index` is the full list of **active** recipes; the
newest `index` wins, like `lessons`. Drafts and retired recipes are not in it.

```markdown
# Recipes index

## client-proposal
- propuesta-cliente — Cuando un cliente pide una propuesta o presupuesto nuevo.

## month-end
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
so a registry from v0.3 gets one at the next `learn` run. The weekly review
rebuilds it every week and so heals any drift.
