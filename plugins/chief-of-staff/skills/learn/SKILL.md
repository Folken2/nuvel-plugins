---
name: learn
description: Let the chief of staff learn from the user. Use before starting a multi-step or recurring task, to look for a matching recipe in the registry and follow it; right after the user corrects the assistant ("no, así no", "a Marta de usted", "eso no me interesa", "don't put newsletters in my brief"), at the end of a complex or multi-step task or one the user says will recur ("prepare a client proposal", "do the month-end check"), when a routine sees a new lasting preference in handoffs or config, and when the user says to drop something it learned ("bórrala", "esa no"). Writes lessons and recipes (lightweight reusable how-tos) to the registry, acts on its own and tells the user afterwards in one line. Never blocks the user's task.
---

# Learn

The chief of staff improves by keeping two things in its registry:

- **Lessons** — short rules from the user's corrections ("write to Marta
  formally"). Every skill reads them at the start.
- **Recipes** — lightweight skills: how a complex or recurring task was done
  well, so the next time follows the same steps. Skills check them before a
  task.

It **acts on its own and tells the user afterwards**, in one line at the end of
the reply. It never asks first, and it never delays, blocks or changes the
result of the task the user asked for: learning happens after the work.

Registry contract (the `lessons` and `recipe <slug>` documents are defined
there): `../../references/registry-layout.md`. Rules:
`../../references/safety.md`. Host memory: `../../references/memory.md`.
Signals and sharing: `../../references/telemetry.md`. Categories:
`../../references/recipe-categories.md`.

## Tools you may use

Read, list and search the registry. Create, never edit or delete (OneDrive:
OneDrive create file):
- new documents in `lessons/`, `recipes/` and `runs/`;
- on a registry made before v0.3 only, the two folders `lessons/` and
  `recipes/` inside the registry root, and one new `config` that lists them
  (§1).

When the nuvel connector is added: `record_run_trace`, `record_recipe_signal`
and `share_recipe`. Nothing else: no source reads are needed, and never any send, reply, share,
event change or file change outside the registry.

## 0. Before a task

When the user asks for a multi-step or recurring task in any conversation
("prepara la propuesta para el cliente", "do the month-end check"), look for a
recipe before starting, even if no routine skill is running:

1. Find the registry and read the newest `config` (§1, steps 1-2). None, or
   `paused: true` → carry on with the task normally.
2. List `recipes/` and keep the newest version per slug with `status: active`.
3. If one's *When to use* matches the task, follow its *Steps* and *Pitfalls*,
   and remember it was used: after the task, §3 *Update* records the use.
4. No match → do the task normally; after it, §3 *Create* may write a recipe.

This is read-only and never delays the task.

## When to run

- **Correction.** The user corrects the assistant's output, tone, ranking or
  approach. One correction = one lesson (or one recipe correction, below).
- **Complex task done.** The task took several tool calls or multiple steps,
  or the user says it will recur. Create or update a recipe.
- **Recipe used.** A task followed a recipe. Update its stats (below).
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
3. Read the newest document in `lessons/` and list `recipes/` (newest version
   per slug wins). An older registry may lack these folders (not in
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
(`learn.recipe`).

**Create** after a complex task when no active recipe's *When to use* matches:
slug in lowercase ASCII with hyphens (`propuesta-cliente`); `recipe_id` a new
random UUIDv4 (format in `telemetry.md` *Formats*); `category` exactly one identifier from `recipe-categories.md`
(closest fit, else `other`); stats `uses: 0`, `successes: 0`,
`corrections: 0`, `last_used` = today, `version: 1`, `shared_version: 0`,
`blocked_version: 0`, `status: active` (only later tasks that follow it count as uses). Write
the steps as they actually worked, folding in what the user corrected along the
way. The private recipe may name people and tools; it lives in the user's own
registry.

**One document per recipe per run.** Work out the new version in memory
first (the stats below, the sharing decision in §5), then write **one**
recipe document that already carries the updated stats and the resulting
`shared_version` / `blocked_version`, and only then send signals (§4). Never
write a second version of the same recipe in the same run: registry names have
minute precision and the registry never overwrites.

**Update** after a task that used a recipe, in a new version with the stats
carried forward and changed:

- `uses` +1 and `last_used` = today, every time.
- **Successful use** = the task the recipe was used for finished, the user saw
  the result in an interactive run, and did not correct it in that conversation
  → `successes` +1. In a **scheduled** run nobody sees the result, so a use
  counts `uses` +1 only, never a success; nor does a scheduled run count a
  correction.
- A correction instead → `corrections` +1 (not a success), and fold the fix
  into *Steps* or *Pitfalls*. If the correction arrives later in the same
  conversation, after a success was already counted, write a new version that
  moves it: `successes` −1, `corrections` +1, `uses` unchanged.
- `version` +1 only when *When to use*, *Steps* or *Pitfalls* changed; a
  stats-only update keeps it.

**Retire** on "bórrala" / "esa no": a new version with `status: retired`.
Skills ignore retired recipes. A recipe without `recipe_id` or `category`
(written without this skill) gets them now and counts as created. A recipe
written through the Project-instructions fallback has no counters: a missing
`version` is 1, and a missing `shared_version` or `blocked_version` is 0.

## 4. Signals to nuvel

Only when the tool `record_recipe_signal` is available, `telemetry` is `on`
and `config` has `telemetry.install_id` (otherwise skip, as in
`telemetry.md`). One call per recipe event, **after** that recipe's single
document for this run is written (`learn.signal`), formats as in
`telemetry.md` *Formats*, with the argument `{"signal": {...}}`:

| field | value |
|---|---|
| `schema` | `nuvel.recipe_signal/1` |
| `signal_id` | a new UUIDv4 for this signal |
| `recipe_id` | the recipe's `recipe_id` |
| `install_id` | `telemetry.install_id` from `config` |
| `plugin` | `{"name": "chief-of-staff", "version": <plugin version, `telemetry.md` *Formats*>}` |
| `category` | the recipe's `category` |
| `event` | `created`, `used`, `succeeded`, `corrected` or `retired` |
| `at` | the time as `YYYY-MM-DDTHH:MM:SSZ`, e.g. `2026-10-27T09:30:00Z` (seconds and `Z` are required) |
| `uses`, `successes`, `corrections` | the counters **after** this event |

A use sends `used`, then `succeeded` or `corrected` (an interactive run only; a scheduled run sends `used` alone). A late correction that
moves an already counted success sends one `corrected` signal only, carrying
the cumulative counters after the move (`successes` one lower, `corrections`
one higher); no `used` and no `succeeded` follow it. Nothing else goes in the
object: no title, slug, step or name, and never a `tenant` field. A
`"duplicate"` status is fine. On error retry once, then journal
`signal: not sent (<class>)` (classes as in `telemetry.md`) and carry on.

## 5. Sharing recipes with nuvel

nuvel collects good recipes, anonymised, to turn the best into real skills for
everyone. Sharing is automatic (the user is told once, at setup) and happens
only when **all** hold:

- `share_recipe` is available, `telemetry` is `on`, `telemetry.install_id`
  exists, and `config` does not say `- sharing.recipes: off` (missing = `on`);
- the recipe is `active` with `successes` ≥ 3 (at least three of its uses
  were a successful use, §3);
- its `version` is greater than both `shared_version` and `blocked_version`
  (first share, or a later version with new text that has not been blocked).
  A stats-only update never re-attempts a blocked version.

Then (`learn.share`), **before** the recipe document is written (§3), so that
its outcome goes into that same document:

1. **Rewrite a generic copy from scratch** — never edit the private text. In
   `owner.language`, in sentence case. Roles, not names ("el cliente", "el
   socio", "la gestoría"). No people, companies, products or brands, amounts or
   currencies (symbols, codes or words), dates, places, emails, phone numbers,
   URLs or domains, file or folder names, and no quotes. No digits at all: a
   small count is written in words ("dos opciones"). Put a space after every
   period.
2. **Self-check** a second time against that same list, field by field. Also
   reject any run of two or more Capitalised words not at the start of the
   text, any digit, any `@`, and any word with a dot inside it. Any hit → do
   not send: journal `share: blocked (pii)` and write the recipe document with
   `blocked_version` = `version`, so it is tried again only when the recipe's
   `version` next goes up.
3. Call `share_recipe` with `{"recipe": {...}}`:

| field | value |
|---|---|
| `schema` | `nuvel.recipe/1` |
| `recipe_id`, `install_id`, `plugin`, `category` | as in the signal |
| `version` | the recipe's `version` |
| `language` | two lowercase letters from `owner.language` (`es`, `ca`, `en`) |
| `title` | ≤ 80 characters |
| `when_to_use` | ≤ 200 characters |
| `steps` | 1–15 items `{"action": <lowercase verb identifier, letters and underscores only, e.g. draft_reply>, "tool_kind": email\|calendar\|chat\|docs\|storage\|tasks\|web\|none, "text": ≤ 160 characters}` |
| `pitfalls` | optional, ≤ 5 strings of ≤ 160 characters |

No other fields, never `tenant`.

4. `"recorded"` or `"duplicate"` → write the recipe document with
   `shared_version` = `version`. A rejection (`"rejected"`, it names field
   paths only; it can be a PII hit or a format problem such as a malformed
   `install_id`) → journal `share: rejected (<paths>)` and write the recipe
   document with `blocked_version` = `version`; never retry it.
   Any other error → retry once, then journal `share: not sent (<class>)` and
   write the recipe document without changing `shared_version`.

Formats for `recipe_id`, `install_id` and `plugin.version` are in
`telemetry.md` *Formats*.

## 6. Journal and tell the user

Write one `runs/YYYY-MM-DD HHMM learn` document (*Other runs* contract in
`registry-layout.md`, in `owner.language`; `learn.write`): `## Journal` with
the lessons added or dropped, the recipes created, updated or retired (slug and
version), and the signal and share lines; then `## Trace`.

Then add **one line** at the end of the reply, after the task's own answer, in
the user's language:

> He apuntado 1 corrección y he creado la receta *Preparar propuesta de cliente*. Dime si alguna sobra.

Add the «Recuerda que…» offer when a stable fact was learnt. Never mention
signals or sharing in that line. In a scheduled run there is no one to tell:
the journal is enough, and the weekly review reports it.

## Trace

Last, follow `../../references/telemetry.md`: if `record_run_trace` is
available and `telemetry` is on, send one content-free trace right before
saving the `learn` document, and end that document with a `## Trace` section
mirroring it. Report only these steps: `learn.load-state`, `learn.lesson`,
`learn.recipe`, `learn.signal`, `learn.share` (`skipped` when not due or not
allowed) and `learn.write`. If nothing was worth learning, write nothing and
send nothing.

- **Counts:** `lessons_added`, `lessons_dropped` and `lessons_total` on
  `learn.lesson`; `recipes_created`, `recipes_updated` and `recipes_retired` on
  `learn.recipe`; `signals_sent` and `signals_failed` on `learn.signal`;
  `shares_sent`, `shares_blocked` and `shares_failed` on `learn.share`.
- **Routing:** what triggered each change: `correction`, `complex_task`,
  `recipe_use`, `routine_preference`, `removal`.
- **Outcome:** `partial` if a lesson or recipe could not be written; `blocked`
  if the registry could not be found.
- Counts and identifiers only — never a rule, recipe title, slug or name.
