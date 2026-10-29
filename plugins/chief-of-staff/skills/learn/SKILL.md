---
name: learn
description: Let the chief of staff learn from the user. Use before starting a multi-step or recurring task, to look for a matching recipe in the registry and follow it; right after the user corrects the assistant ("no, así no", "a Marta de usted", "eso no me interesa", "don't put newsletters in my brief"), at the end of a complex or multi-step task or one the user says will recur ("prepare a client proposal", "do the month-end check"), when the user approves or corrects the result of a task that followed a recipe, when a routine sees a new lasting preference in handoffs or config, and when the user says to drop something it learned ("bórrala", "esa no"). Writes lessons and private recipes (lightweight reusable how-tos) to the registry, acts on its own and tells the user afterwards in one line. Never blocks the user's task.
---

# Learn

The chief of staff improves by keeping two things in its registry:

- **Lessons** — short rules from the user's corrections ("write to Marta
  formally"). Every skill reads them at the start.
- **Recipes** — lightweight skills: how a recurring task was done well, so the
  next time follows the same steps. They start as a `draft` and become
  `active` once the task comes back. Skills find them through the `index`.

It **acts on its own and tells the user afterwards**, in one line at the end of
the reply. It never asks first, and it never delays, blocks or changes the
result of the task the user asked for: learning happens after the work.

Registry contract (the `lessons`, `recipe <slug>` and `index` documents):
`../../references/registry-layout.md`. Recipe states, stats, migration and the
index: `../../references/recipes.md`. Rules: `../../references/safety.md`.
Host memory: `../../references/memory.md`. Categories:
`../../references/recipe-categories.md`. Formats and traces:
`../../references/telemetry.md`.

## Tools you may use

Read, list and search the registry. Create, never edit or delete (OneDrive:
OneDrive create file):
- new documents in `lessons/`, `recipes/` and `runs/`;
- on a registry made before v0.3 only, the two folders `lessons/` and
  `recipes/` inside the registry root, and one new `config` that lists them
  (§1).

When the nuvel connector is added: `record_run_trace` only. Nothing else: no
source reads are needed, and never any send, reply, share, event change or
file change outside the registry. Sharing recipes with nuvel is the weekly
review's job, never this skill's.

## 0. Before a task

When the user asks for a multi-step or recurring task in any conversation
("prepara la propuesta para el cliente", "do the month-end check"), look for a
recipe before starting, even if no routine skill is running:

1. Find the registry and read the newest `config` (§1, steps 1-2). None, or
   `paused: true` → carry on with the task normally.
2. Read the newest `index` in `recipes/` (one read). No `index` → no recipe
   lookup at all; carry on with the task normally.
3. Match the task against the one-line *When to use* lines, under the
   likeliest category first, then the rest. A match → open only that recipe's
   newest version, follow its *Steps* and *Pitfalls*, and remember it was
   used: after the task, §3 *Use* records it.
4. No match → do the task normally; after it, §3 may write a draft.

This is read-only, costs one small read, and never delays the task. Drafts are
not in the `index`, so they are never followed.

## When to run

- **Correction.** The user corrects the assistant's output, tone, ranking or
  approach. One correction = one lesson (or one recipe correction, below).
- **Complex task done.** The task took several tool calls or multiple steps
  and no recipe was followed → write a draft, or promote the draft it matches
  (§3).
- **Recurring task.** The user says the task will recur ("cada mes", "every
  Monday", "lo haremos más veces") → write the recipe `active` straight away.
- **Recipe used.** A task followed a recipe. At the end of the task, record
  the use (§3 *Use*).
- **Outcome.** Later in the same conversation the user approves or corrects
  the result of a task that followed a recipe. Record the outcome in a
  separate run (§3 *Outcome*).
- **Routine preference.** In a scheduled run, an open handoff or a `config`
  change shows a lasting preference ("from now on ignore X"). Add it as a
  lesson.
- **Removal.** "Bórrala", "esa no", "forget that rule" → retire that recipe
  or drop that lesson.

Skip one-off facts about a single item, anything the user did not actually
correct, and anything `safety.md` §3 forbids (secrets, codes, bank or ID
numbers, health details) — those are never written.

## 1. Load state

1. Find the registry (*Finding the registry* in `registry-layout.md`). None →
   write nothing and say nothing (unless the user asked to remember something:
   then one line saying the notes folder is not set up).
2. Read the newest `config`. `paused: true` → do nothing.
3. Read the newest document in `lessons/`. List `recipes/` (newest version
   per slug wins, drafts included) and read the newest `index`, only to know
   whether this run must write one (§3 *Index*). An older registry may lack these folders (not in
   `storage.folders`): create `lessons/` and `recipes/` inside the registry
   root and write a new `config` that lists them, carrying everything else
   forward unchanged.

Report this as `learn.load-state`.

## 2. Lessons

The newest `lessons` document is the full current list; nothing is edited in
place. To add or drop a lesson, write a **new** `lessons/YYYY-MM-DD HHMM
lessons` document holding the previous list with the change applied
(`learn.lesson`):

- One line per lesson: `- <rule> — scope: <skill or "all"> — since <date>`.
  The rule is short, imperative, in `owner.language`, and says what to do next
  time ("Escribir a Marta de usted"), not what went wrong.
- Scope is the skill the correction was about (`radar`, `brief`, `prep`,
  `weekly-review`, `recall`, `setup`) or `all`.
- Same rule already there → keep one, with the newer date. A new rule that
  contradicts an old one replaces it. Keep the list under ~40 lines; the
  weekly review merges duplicates.

**Stable facts** (a changed priority, a new key person, a tone preference;
`memory.md` *What goes where*) are also worth keeping in host memory. No host
lets a skill write memory, so never claim it was saved: offer the user the one
sentence to send, in the afterwards line («Si quieres que lo recuerde en
cualquier conversación, dime: "Recuerda que…"»).

## 3. Recipes

A recipe is one document per version, `recipes/YYYY-MM-DD HHMM recipe <slug>`;
the newest version per slug wins and keeps the same `recipe_id` forever
(`learn.recipe`). Every rule below is spelled out in `recipes.md`.

- **Draft** after a complex task that no recipe matches, active or draft:
  a new recipe with `status: draft` (slug, `recipe_id`, `category` and
  starting stats as in `recipes.md` *Create*). Write the steps as they
  actually worked, folding in what the user corrected along the way.
- **Promote** when a later complex task matches a draft's *When to use*: a
  new version with `status: active`, steps refined from both runs, and that
  task counted as a use (*Use*). Compare only after the task, never before it.
- **Active** straight away when the user says the task will recur (a new
  recipe, or the matching draft promoted).
- **Use**, written once, at the end of a task that followed a recipe:
  `uses` +1, `days_used` +1 on a new date, `last_used` = today,
  `last_outcome: silent`. No later run adds to `uses` or `days_used` for
  that use.
- **Outcome**, when the user reacts later in the same conversation: a
  separate run whose new version changes only `successes` or `corrections`
  and `last_outcome`. **Success is explicit approval only**: the user says
  the result worked ("perfecto", "esto es lo que quería") → `successes` +1,
  `last_outcome: success`. A correction → `corrections` +1, `last_outcome:
  corrected`, the fix folded into *Steps* or *Pitfalls*; a correction after
  an approval keeps the success. `last_outcome` is always the latest
  outcome. Silence, leaving or a scheduled run → nothing more; the use
  stays `silent`, no success.
- **Retire** on "bórrala" / "esa no": a new version with `status: retired`.
- **Migrate** a recipe written before v0.4 on its next write (`recipes.md`
  *Migration*).

Carry `shared_version` and `blocked_version` forward unchanged on every
version you write; only the weekly review changes them.

**One document per recipe per run.** Work out the new version in memory
first, then write **one** recipe document. Never write a second version of
the same recipe in the same run: registry names have minute precision and
the registry never overwrites. The use and its later outcome are two runs,
so two versions (example in `recipes.md` *Stats*).

**Index.** Write a new `recipes/YYYY-MM-DD HHMM index` (format in
`recipes.md` *Index*, active recipes only) in the same run whenever the set of
active recipes or an active recipe's *When to use* changed (promote, direct
active, retire, a new *When to use*), and also in any run that finds active
recipes but no `index` (a registry from v0.3). Stats-only updates never touch
it.

## 4. Journal and tell the user

Write one `runs/YYYY-MM-DD HHMM learn` document (*Other runs* contract in
`registry-layout.md`, in `owner.language`; `learn.write`): `## Journal` with
the lessons added or dropped, the recipes drafted, promoted, updated or
retired (slug, status and version) and whether the `index` was written; then
`## Trace`.

Then add **one line** at the end of the reply, after the task's own answer, in
the user's language:

> He apuntado 1 corrección y he guardado un borrador de receta para *Preparar propuesta de cliente*. Dime si alguna sobra.

When a recipe becomes active, say so in the same line («…y la receta
*Preparar propuesta de cliente* ya está lista para la próxima vez»). Add the
«Recuerda que…» offer when a stable fact was learnt. Never mention the
`index`, stats or nuvel in that line. In a scheduled run there is no one to
tell: the journal is enough, and the weekly review reports it.

## Trace

Last, follow `../../references/telemetry.md`: if `record_run_trace` is
available and `telemetry` is on, send one content-free trace right before
saving the `learn` document, and end that document with a `## Trace` section
mirroring it. Report only these steps: `learn.load-state`, `learn.lesson`,
`learn.recipe` and `learn.write` (`skipped` when not due). If nothing was
worth learning, write nothing and send nothing.

- **Counts:** `lessons_added`, `lessons_dropped` and `lessons_total` on
  `learn.lesson`; `drafts_created`, `recipes_promoted`, `recipes_created`
  (written `active` straight away), `recipes_updated`, `recipes_retired` and
  `index_written` on `learn.recipe`.
- **Routing:** what triggered each change: `correction`, `complex_task`,
  `recipe_use`, `routine_preference`, `removal`.
- **Outcome:** `partial` if a lesson, recipe or index could not be written;
  `blocked` if the registry could not be found.
- Counts and identifiers only — never a rule, recipe title, slug or name.
