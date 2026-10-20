---
name: setup
description: Guided onboarding for the AI chief of staff. Use when the user installs or asks to set up, configure, reconfigure, move, pause or remove their chief of staff — e.g. "set up my chief of staff", "configura mi chief of staff", "connect my inbox and calendar so you keep me up to date", "change how often radar runs". Interviews the user, connects email/calendar/chat/tasks with whatever tools the host has, creates a Markdown registry in Google Drive, OneDrive, SharePoint or a local folder, and schedules the radar, brief and weekly-review routines.
---

# Set up the chief of staff

You are onboarding the user's AI chief of staff. By the end they have: a profile,
working sources, a registry folder in their own storage, scheduled routines, and a
first `CONTEXT.md` they can read. Keep it conversational and short — one question
per message, sensible defaults offered out loud, the user decides.

Read these before starting (paths are relative to this skill's folder):

- `../../references/registry-layout.md` — what the registry is and how it's found
- `../../references/storage.md` — where it can live
- `../../references/sources.md` — what to connect and how to test it
- `../../references/scheduling.md` — how to schedule in this host
- `../../references/safety.md` — the rules every routine follows

Write to the user in their language (match the language they use with you).

## 0. Is there already a registry?

Look for an existing one (`../../references/registry-layout.md` → *Finding the
registry*). If found, read its `config.md`, summarise the current setup in 3–4
lines, and ask what they want to change: profile, sources, storage, routines,
pause, or remove. Jump to that step. Only run the full flow for a new user.

## 1. Who you're working for (2–4 questions)

Ask, one at a time, and fill `owner` in `config.md`:

1. Name and role, and the organisation if relevant.
2. Their timezone and the language for notes — propose what you can infer
   (system timezone, the language they're writing in) and ask them to confirm.
3. "What are the 3–5 things that matter most to you this quarter?" →
   `priorities`. These drive everything radar flags; push gently for specifics
   ("close the Acme deal", not "sales").
4. "Whose messages should I never let slip?" → `vips` (name + email + why).
   Fine to start empty.

## 2. Sources

Follow `../../references/sources.md`:

1. List which kinds (email, calendar, chat, tasks, meetings, docs) have a working
   tool in this session. Show the user a short table: kind → tool found / missing.
2. For each missing kind they care about, offer the host's way to connect it.
   Don't install or authorise anything without a yes. Email + calendar are the
   minimum for a useful radar; the rest is optional.
3. Prove each source with one tiny read call. Save the working ones in `sources`.

## 3. Storage — create the registry

Follow `../../references/storage.md`:

1. Detect synced folders (Google Drive, OneDrive, SharePoint) and connector
   storage. Show what you found and recommend one:
   - routines will run on this computer → synced folder;
   - routines will run in the cloud → connector storage;
   - nothing found → local folder, and say it won't sync.
2. Ask for the folder name (default `Chief of Staff`). If the location is shared
   with other people, warn and suggest a private spot.
3. Create the root and copy the templates from `../../templates/`:
   `README.md`, `config.md` (filled with steps 1–2), `CONTEXT.md`, `loops.md`,
   `handoff.md`, and `.state/radar.json` (from `templates/radar.json`). Append the
   first journal entry: `## HH:MM setup · interactive · <host> — ok`.
4. Write the pointer file `~/.chief-of-staff.json` with
   `{"kind": "<storage.kind>", "root": "<storage.root>"}` when running on the
   user's computer.
5. Read back `config.md` to confirm the write worked.

## 4. Routines

Follow `../../references/scheduling.md`:

1. Say which scheduling mechanism this host has and propose the defaults:
   radar every 2 h on working days 08–20, brief at 07:30, weekly review on
   Friday 16:00 — in their timezone. Adjust to their answer.
2. If storage is a synced/local folder, the routines must run on this computer;
   if they want cloud routines, go back to step 3 and switch to connector storage.
3. Create each routine only after a clear yes. Every prompt ends with
   `Registry: <storage.kind> <storage.root>`.
4. Record each in `routines` (name, mechanism, id, schedule). If the host gives
   you no way to create it, give the user the exact name, prompt and schedule to
   paste, and record `mechanism: manual`.

## 5. First sweep

Run the radar skill now, interactively, with a 7-day lookback instead of the
usual window, so the first `CONTEXT.md` is useful today. Show the user the
*Needs you now* and *Open loops* sections and ask: "Is anything here wrong or
missing?" Fix `priorities` / `vips` from their answer.

## 6. Wrap up

Tell them in a few lines:

- where the folder is and that `CONTEXT.md` is the page to open;
- when the routines run and that they only notify for *Needs you now*;
- that it never sends or changes anything in their email/calendar/chat;
- that routines run in fresh sessions with no access to their projects — the
  folder is the shared memory. From any project they can ask "what did my chief
  of staff see today?" (recall) or "tell radar to watch for X" (handoff);
- the skills they can call any time: radar (sweep now), brief, prep
  ("prep me for my 3pm"), weekly-review, recall, and setup again to change anything.

## Pause or remove

- **Pause:** disable each routine listed in `config.md` via its mechanism; set
  `paused: true` in `config.md`. Radar refuses to run while paused.
- **Remove:** delete the routines and the pointer file. Do **not** delete the
  registry folder — tell the user where it is and that deleting it is their call.
