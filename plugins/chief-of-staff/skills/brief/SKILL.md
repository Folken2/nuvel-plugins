---
name: brief
description: Write the user's morning brief from their chief-of-staff registry and today's calendar — the day's meetings with context, what needs them, open loops due, and a suggested focus. Use for the scheduled morning routine and when the user asks "brief me", "what's my day", "resumen de hoy", "morning brief", or "what should I focus on today".
---

# Morning brief

A one-screen plan for the day, readable in two minutes. It builds on what radar
already knows; it is not a second sweep of the inbox.

Rules: `../../references/safety.md`. Registry: `../../references/registry-layout.md`.

## Steps

1. Find the registry and read `config.md` (stop if `paused: true`).
2. If `.state/radar.json` → `last_run` is older than 3 hours, run the radar skill
   first so the brief starts from fresh data.
3. Read `CONTEXT.md`, `loops.md`, `handoff.md` (`## Open`), and yesterday's
   journal in `log/`.
4. Read today's calendar in full. For each meeting, pull context from
   `people/` and `projects/` notes and the latest related journal bullets.
5. Write `briefs/YYYY-MM-DD.md` (in `owner.language`):

```markdown
# Brief — <weekday> <YYYY-MM-DD>

**Focus today:** <one sentence, tied to a priority>

## Needs you now
- <from CONTEXT.md, re-ranked for today>

## Your day
| time | meeting | why it matters / what to bring |
|---|---|---|

## Due or overdue
- <loops.md rows due today or overdue — I owe first>

## Waiting on
- <rows older than 3 working days: suggest a nudge, don't send it>

## Free blocks
- <gaps ≥ 45 min in working hours, with what to use them for>
```

6. Flag conflicts (overlaps, back-to-backs with no travel time, meetings without
   an agenda when the user is the organiser) inside *Your day*.
7. Reply with the brief's content (interactive) or a short notification with
   the focus line and the path/link (scheduled).

## Leave a trace

Before replying, append a section to the journal `log/YYYY/MM/YYYY-MM-DD.md`
(heading format in `../../references/registry-layout.md`), e.g.
`## 07:30 brief · scheduled · claude — ok` — with the file you wrote and anything you couldn't find. The main
agent and later routines rely on it to know this ran.

Keep it short: if a section is empty, drop it. Suggest, never act — no drafting
or sending replies, no calendar changes.
