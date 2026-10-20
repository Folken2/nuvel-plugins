---
name: weekly-review
description: Write the user's weekly review from their chief-of-staff registry — progress against priorities, decisions, loops closed and still open, people to follow up with, and a proposed plan for next week; also tidies the registry. Use for the scheduled Friday routine and when the user asks for a "weekly review", "revisión semanal", "how did my week go", or "plan next week".
---

# Weekly review

Rules: `../../references/safety.md`. Registry: `../../references/registry-layout.md`.

## Steps

1. Find the registry and read `config.md` (stop if `paused: true`).
2. Read this ISO week's journal (`log/`), `handoff.md`, briefs, `loops.md`, `CONTEXT.md`, and the
   `people/` / `projects/` notes touched this week. Read next week's calendar.
3. Write `reviews/YYYY-Www.md` (in `owner.language`):

```markdown
# Week <YYYY-Www> review

## Priorities
| priority | this week | status (on track / at risk / stalled) |
|---|---|---|

## Decisions and wins
- …

## Loops
- Closed: <n> · Still open: <n> · Overdue: <list>
- Waiting on for > 1 week: <who, what — suggest a nudge>

## People
- <who you owe a follow-up or haven't heard from but should>

## Next week
- Big rocks: <2–3, tied to priorities>
- Calendar: <heavy days, conflicts, prep needed>
- Suggested blocks: <focus time to protect>

## Registry health
- <sources failing, stale notes, priorities that no longer match reality>
```

4. Housekeeping (registry only, never sources):
   - In `people/` and `projects/` notes, compress timeline entries older than 30
     days into a one-paragraph summary.
   - If a priority had no activity for 3 weeks, ask the user (interactive) or note
     it under *Registry health* (scheduled) — don't change `priorities` yourself.
5. Before replying, append a section to the journal `log/YYYY/MM/YYYY-MM-DD.md`
   (heading format in `../../references/registry-layout.md`), e.g.
   `## 16:00 weekly-review · scheduled · claude — ok` — with the file you wrote and anything you couldn't find. The main
   agent and later routines rely on it to know this ran.
6. Reply with the review, or a short notification with the path/link when
   scheduled.
