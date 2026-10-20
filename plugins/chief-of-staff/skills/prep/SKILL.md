---
name: prep
description: Prepare the user for an upcoming meeting or call using their chief-of-staff registry, calendar, recent email/chat threads and past meeting notes — who's attending, history, open loops with them, and what to get out of it. Use when the user says "prep me for my 3pm", "prepara la reunión con Acme", "what do I need to know before meeting Ana", or names an upcoming meeting.
---

# Meeting prep

Rules: `../../references/safety.md`. Registry: `../../references/registry-layout.md`.

## Steps

1. Find the registry and read `config.md`.
2. Identify the meeting. If the user didn't name one, take the next meeting on
   today's calendar and confirm in one line. Read its title, time, attendees,
   description and attachments list.
3. Gather context, in this order, stopping when you have enough:
   1. `people/<slug>.md` for each attendee, `projects/<slug>.md` for the topic.
   2. `loops.md` rows involving any attendee.
   3. The last 2–3 journal (`log/`) bullets mentioning them, and any open
      `handoff.md` item about them.
   4. Recent email/chat threads with the attendees (last 30 days, metadata
      first, open only the most relevant 3–5).
   5. Notes or transcripts from the previous meeting in the series, if a meetings
      source is connected.
4. Write `prep/YYYY-MM-DD-<meeting-slug>.md` (in `owner.language`):

```markdown
# Prep — <meeting title> · <date time>

**Goal:** <what the user should walk out with — one line; ask if unclear>

## Who
- <name> — <role/company>, <last interaction>, <what they care about>

## Where things stand
- <3–6 bullets: history, decisions so far, numbers that matter>

## Open loops with them
- I owe: … / Waiting on: …

## Suggested agenda / questions
1. …

## Watch out for
- <risks, sensitivities, anything unresolved>
```

5. Reply with the prep. Mention anything you couldn't find (no notes from last
   time, attendee unknown) rather than inventing it.

## Leave a trace

Before replying, append a section to the journal `log/YYYY/MM/YYYY-MM-DD.md`
(heading format in `../../references/registry-layout.md`), e.g.
`## 14:40 prep · interactive · codex — ok (Acme QBR)` — with the file you wrote and anything you couldn't find. The main
agent and later routines rely on it to know this ran.

Facts only from sources you read — label inferences as such ("likely", "seems").
