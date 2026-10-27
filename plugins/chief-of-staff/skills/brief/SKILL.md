---
name: brief
description: Write the user's morning brief from their chief-of-staff registry and today's calendar — the day's meetings with context, what needs them, open loops due, and a suggested focus. Use for the scheduled morning routine and when the user asks "brief me", "what's my day", "resumen de hoy", "morning brief", or "what should I focus on today".
---

# Morning brief

A one-screen plan for the day, readable in two minutes. It builds on what radar
already knows; it is not a second sweep of the inbox.

Rules: `../../references/safety.md`. Registry contract:
`../../references/registry-layout.md`.

## Tools you may use

Read/search/list tools on email and calendar: Outlook mail search and Outlook
calendar list events, or Gmail and Google Calendar (discover Microsoft tools by
function, `sources.md` *Microsoft 365*). Create one new document in the
registry's `runs/` folder. Nothing else — no sending mail, drafts, replies or
calendar event create/update/delete/respond, no Teams messages, no file changes
outside the registry.

## Steps

1. Find the registry and read the newest `config` (stop if `paused: true`).
2. Read the newest `radar` in `runs/`. If it is older than 3 hours (or there is
   none), run the radar skill first so the brief starts from fresh data.
3. Read open handoffs (see `registry-layout.md`) and yesterday's runs.
4. Read today's calendar in full (Outlook or Google). For each meeting, find context in the newest
   radar and by searching `runs/` for the attendees' names or the meeting topic.
5. Create `runs/YYYY-MM-DD HHMM brief` (in `owner.language`), with the journal
   header from the *Other runs* contract, then:

```markdown
**Focus today:** <one sentence, tied to a priority>

## Needs you now
- <from the newest radar, re-ranked for today>

## Your day
| time | meeting | why it matters / what to bring |
|---|---|---|

## Due or overdue
- <open loops due today or overdue — I owe first>

## Waiting on
- <items older than 3 working days: suggest a nudge, don't send it>

## Free blocks
- <gaps ≥ 45 min in working hours, with what to use them for>
```

6. Flag conflicts (overlaps, back-to-backs, meetings the user organises without
   an agenda) inside *Your day*.
7. Reply with the brief (interactive) or a short notification with the focus line
   and the link (scheduled).

Keep it short: drop empty sections. Suggest, never act.

## Trace

Last, follow `../../references/telemetry.md`: if `record_run_trace` is available
and `telemetry` is on, send one content-free trace right before saving the
brief, and end the document with a `## Trace` section mirroring it. Report only
these steps: `brief.load-state`, `brief.refresh-radar` (`skipped` when the
newest radar was fresh), `brief.read-calendar` and `brief.write`.

- **Counts:** `meetings` on `brief.read-calendar`; `needs_you_now`,
  `due_or_overdue`, `waiting_on`, `free_blocks` and `conflicts` on
  `brief.write`.
- **Outcome:** `partial` if the calendar could not be read; `blocked` if the
  registry could not be found.
- Counts and identifiers only — never a meeting title, name or link.
