---
name: prep
description: Prepare the user for an upcoming meeting or call using their chief-of-staff registry, calendar, recent email threads and past meeting notes — who's attending, history, open loops with them, and what to get out of it. Use when the user says "prep me for my 3pm", "prepara la reunión con Acme", "what do I need to know before meeting Ana", or names an upcoming meeting.
---

# Meeting prep

Rules: `../../references/safety.md`. Registry: `../../references/registry-layout.md`.

## Tools you may use

Read/search/list on email, calendar, chat and docs: Outlook mail search,
Outlook calendar list events, Teams chat read, OneDrive search / list / read
file, or the Gmail, Google Calendar and Drive equivalents (discover Microsoft
tools by function, `sources.md` *Microsoft 365*). Create one new document in the
registry's `runs/` folder. Never send mail, create drafts, reply, create /
update / delete / respond-to calendar events, post Teams messages, or change
files outside the registry.

## Lessons and recipes

Right after reading `config`, read the newest document in the registry's
`lessons/` folder and apply every lesson scoped to `prep` or `all`; they
override this skill's defaults but never `safety.md`. Then list `recipes/`
(newest version per slug, `status: active`) and, if one's *When to use* matches
this preparation, follow its *Steps* and *Pitfalls*. No `lessons/` or `recipes/`
folder yet → carry on without them (`registry-layout.md`).

Afterwards, if the user corrected the result or a recipe was used, run the
`learn` skill (it acts on its own and adds one line to the reply).

## Steps

1. Find the registry and read the newest `config`.
2. Identify the meeting. If none was named, take the next one on today's
   calendar and confirm in one line. Read title, time, attendees, description,
   attachments list.
3. Gather context, stopping when you have enough:
   1. The newest `radar`: open loops, *Decide* and *Watching* items involving
      any attendee or the topic.
   2. Full-text search of `runs/` for attendee names, their company and the topic.
   3. Open handoffs about them.
   4. Recent email threads with the attendees (last 30 days; metadata first,
      open only the 3–5 most relevant). Outlook: search by attendee address and
      `receivedDateTime`; Gmail: `from:`/`to:` with `newer_than:30d`. Teams DMs
      or chats with them, if the chat source is Teams.
   5. Notes or transcripts from the previous meeting in the series, if a meetings
      source is connected (Teams recordings, OneDrive or Drive notes included).
4. Create `runs/YYYY-MM-DD HHMM prep <meeting-slug>` (in the registry language)
   with the *Other runs* journal header, then:

```markdown
**Goal:** <what the user should walk out with — ask if unclear>

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

5. Reply with the prep and its link. Say what you couldn't find instead of
   inventing it; label inferences ("likely", "seems").

## Trace

Last, follow `../../references/telemetry.md`: if `record_run_trace` is available
and `telemetry` is on, send one content-free trace right before saving the prep
document, and end it with a `## Trace` section mirroring it. Report only these
steps: `prep.load-state`, `prep.identify-meeting`, `prep.gather-context` and
`prep.write`.

- **Counts:** `attendees` on `prep.identify-meeting`; `open_loops`, `handoffs`,
  `threads_read` and `runs_searched` on `prep.gather-context`.
- **Outcome:** `partial` if a context source failed; `blocked` if the registry
  could not be found.
- Counts and identifiers only — never a meeting title, attendee name or link.
