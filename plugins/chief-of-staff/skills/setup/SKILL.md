---
name: setup
description: Guided onboarding for the AI chief of staff. Use when the user installs or asks to set up, configure, reconfigure, move, pause or remove their chief of staff — e.g. "set up my chief of staff", "configura mi chief of staff", "connect my inbox and calendar so you keep me up to date", "change how often radar runs". Interviews the user, checks their email/calendar/storage connectors, creates the registry folder in Google Drive, OneDrive, SharePoint or a local folder, schedules the radar, brief and weekly-review routines, and runs the first sweep.
---

# Set up the chief of staff

You are onboarding the user's AI chief of staff. By the end they have a profile,
working sources, a registry folder in their own storage, scheduled routines, and
a first radar document they can read. Keep it conversational and short — **one
question per message**, sensible defaults offered out loud, the user decides.

Read first (paths relative to this skill's folder):
`../../references/registry-layout.md`, `../../references/storage.md`,
`../../references/sources.md`, `../../references/scheduling.md`,
`../../references/safety.md`.

Talk to the user in the language they write in. The registry may use another
language — ask (step 1).

## 0. Is there already a registry?

Look for one (*Finding the registry* in `registry-layout.md`). If found, read the
newest `config`, summarise the setup in 3–4 lines, and ask what to change:
profile, sources, storage, routines, pause, or remove. Jump to that step.

## 1. Who you're working for

One question per message; fill the `config` fields:

1. Name, role, organisation.
2. Confirm inferred defaults in one message: timezone (from the calendar or
   system), working hours (09:00–19:00 Mon–Fri), and **the language for the
   registry notes** — say it can differ from the chat language.
3. "What are the 3–5 things that matter most to you this quarter?" Push gently
   for specifics.
4. "Whose messages should never slip?" (VIPs: name + email or domain + why).
   Starting with none is fine; say radar will then rank by priorities and by
   whether someone asks for something.

## 2. Sources

1. Find which kinds (email, calendar, chat, tasks, meetings, docs) have a
   working tool. Prove each with one tiny read (1 thread, the calendar list).
2. Show a short table: kind → tool → ✅ / missing (optional).
3. Email + calendar are the minimum. Offer to connect missing ones through the
   host's connector settings; never install or authorise anything without a yes.
4. Point out, once, that these connectors can also send/delete/share and that
   the chief of staff will never use those tools.

## 3. Storage — create the registry

Follow `../../references/storage.md`:

1. Recommend the storage connector (works from chat, Cowork and cloud
   routines); a synced/local folder only if everything will run on one computer.
2. Ask to confirm the location (default `Chief of Staff` in the root, private).
3. Create the root and `config/`, `runs/`, `handoff/`. Do the round-trip test
   and pick the document type.
4. Create the human README (`LLEGEIX-ME`, `README`, `LÉAME`… in the registry
   language) from `../../templates/README.md`, translated.
5. Create the first `config` document (`config/YYYY-MM-DD HHMM config`) from
   the contract in `registry-layout.md`, with folder IDs and `## Routines` still
   empty if step 4 hasn't happened — or, better, create it after step 4 so the
   first version is complete.

## 4. Routines

Follow `../../references/scheduling.md`:

1. Say which mechanism fits (Cowork scheduled tasks → cloud routines → desktop
   tasks) and what it implies (runs with the app closed or not). Propose the
   default schedule in their timezone; adjust to their answer.
2. Create each routine only after a clear yes, with the self-contained prompt
   template. Record mechanism + schedule + ID in `config`.
3. If you can't create it yourself, give the user the exact name, prompt and
   schedule to paste, and record `manual`.

## 5. First sweep

Ask the user to press **Run now** on the radar routine (it pre-approves the
connector tools and is the real fresh-session test). Tell them to approve only
read/search tools and "create file" on storage, and to reject anything that
sends, deletes, shares or changes events. If there is no routine to run, run the
radar skill here instead. The first radar uses a 7-day window.

Then read the new radar document with the user: walk through *Needs you now*,
*Decide* and *Open loops*, and ask "Is anything here wrong or missing?". Turn
corrections into a new `config` (priorities, VIPs, "How I work").

## 6. Wrap up

In a few lines: where the folder is and which document to open (the newest
radar in `runs/`); when routines run and that they only notify for *Needs you
now*; that it never sends or changes anything; that from any conversation they
can ask "what did my chief of staff see today?" or "tell radar to watch for X"
(recall); and that setup can change anything later.

Write one `runs/YYYY-MM-DD HHMM setup` document with a short journal of what was
configured.

## Pause or remove

- **Pause:** disable each routine listed in `config`; write a new `config` with
  `paused: true`. All skills refuse to run while paused.
- **Remove:** delete the routines (with the user's yes). Never delete the
  registry folder — tell the user where it is and that deleting it is their call.
