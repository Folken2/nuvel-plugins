---
name: weekly-review
description: Write the user's weekly review from their chief-of-staff registry — progress against priorities, decisions, loops closed and still open, people to follow up with, and a proposed plan for next week. Use for the scheduled Friday routine and when the user asks for a "weekly review", "revisión semanal", "how did my week go", or "plan next week".
---

# Weekly review

Rules: `../../references/safety.md`. Registry: `../../references/registry-layout.md`.

## Tools you may use

Read/search/list on the registry and the calendar (Outlook calendar list events
or Google Calendar; OneDrive or Drive for the registry; discover Microsoft tools
by function, `sources.md` *Microsoft 365*). Create one new document in the
registry's `runs/` folder, plus one new `lessons` document when duplicate
lessons are merged (step 3), plus what the `learn` skill writes when it runs.
Nothing else: no sending mail, drafts, calendar event
changes, Teams messages, or file changes outside the registry.

## Lessons and recipes

Right after reading `config`, read the newest document in the registry's
`lessons/` folder and apply every lesson scoped to `weekly-review` or `all`;
they override this skill's defaults but never `safety.md`. Then list `recipes/`
(newest version per slug, `status: active`) and, if one's *When to use* matches
this review, follow its *Steps* and *Pitfalls*. No `lessons/` or `recipes/`
folder yet → carry on without them (`registry-layout.md`).

Afterwards, if the user corrected the result or a recipe was used, run the
`learn` skill (it acts on its own and adds one line to the reply).

## Steps

1. Find the registry and read the newest `config` (stop if `paused: true`).
2. Read this ISO week's runs in `runs/` (radars, briefs, preps, learn runs), the
   newest radar, open handoffs, and next week's calendar (Outlook or Google).
   List this week's documents in `lessons/` and `recipes/`.
3. **Merge duplicate lessons.** If the newest `lessons` list has two lines
   that say the same thing, or one that a newer line contradicts, write a new
   `lessons/YYYY-MM-DD HHMM lessons` document with them merged (keep the newer
   wording and date; drop nothing else). No duplicates → write nothing there.
4. Create `runs/YYYY-MM-DD HHMM weekly-review` (in the registry language) with
   the *Other runs* journal header, then:

```markdown
## Priorities
| priority | this week | status (on track / at risk / stalled) |
|---|---|---|

## Decisions and wins
- …

## Loops
- Closed: <n> · Still open: <n> · Overdue: <list>
- Waiting on for > 1 week: <who, what — suggest a nudge>
- Decide items still pending: <list — suggest yes/no/ignore>

## People
- <who you owe a follow-up or haven't heard from but should>

## Next week
- Big rocks: <2–3, tied to priorities>
- Calendar: <heavy days, conflicts, prep needed>
- Suggested blocks: <focus time to protect>

## What I learned this week
- Lessons: <added, dropped or merged this week, one line each>
- Recipes: <created, changed or retired — title, uses, successes, corrections>

## Registry health
- <sources failing, routines that didn't run (gaps between radars), priorities
  with no activity for 3 weeks — ask the user, don't change `config` yourself>
```

   Drop *What I learned this week* when nothing changed.
5. Reply with the review, or a short notification with the link when scheduled.

## Trace

Last, follow `../../references/telemetry.md`: if `record_run_trace` is available
and `telemetry` is on, send one content-free trace right before saving the
review, and end the document with a `## Trace` section mirroring it. Report only
these steps: `weekly-review.load-state`, `weekly-review.read-runs`,
`weekly-review.read-calendar`, `weekly-review.merge-lessons` (`skipped` when
there were no duplicates) and `weekly-review.write`.

- **Counts:** `runs_read` on `weekly-review.read-runs`; `lessons_merged` on
  `weekly-review.merge-lessons`; `loops_closed`, `loops_open`, `overdue`,
  `decide_pending`, `priorities_at_risk`, `lessons_learned` and
  `recipes_changed` on `weekly-review.write`.
- **Outcome:** `partial` if the calendar could not be read; `blocked` if the
  registry could not be found.
- Counts and identifiers only — never a priority, name or link.
