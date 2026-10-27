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
registry's `runs/` folder. Nothing else: no sending mail, drafts, calendar event
changes, Teams messages, or file changes outside the registry.

## Steps

1. Find the registry and read the newest `config` (stop if `paused: true`).
2. Read this ISO week's runs in `runs/` (radars, briefs, preps), the newest radar,
   open handoffs, and next week's calendar (Outlook or Google).
3. Create `runs/YYYY-MM-DD HHMM weekly-review` (in the registry language) with
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

## Registry health
- <sources failing, routines that didn't run (gaps between radars), priorities
  with no activity for 3 weeks — ask the user, don't change `config` yourself>
```

4. Reply with the review, or a short notification with the link when scheduled.

## Trace

Last, follow `../../references/telemetry.md`: if `record_run_trace` is available
and `telemetry` is on, send one content-free trace right before saving the
review, and end the document with a `## Trace` section mirroring it. Report only
these steps: `weekly-review.load-state`, `weekly-review.read-runs`,
`weekly-review.read-calendar` and `weekly-review.write`.

- **Counts:** `runs_read` on `weekly-review.read-runs`; `loops_closed`,
  `loops_open`, `overdue`, `decide_pending` and `priorities_at_risk` on
  `weekly-review.write`.
- **Outcome:** `partial` if the calendar could not be read; `blocked` if the
  registry could not be found.
- Counts and identifiers only — never a priority, name or link.
