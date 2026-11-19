# chief-of-staff 0.6 — tasks arrive prepared; looks done, you decide

Date: 2026-11-19. Status: decided in chat ("tasks that arrive prepared and
tasks closed from evidence — but we need to let the user know: human in the
loop always").

## Principle

The chief of staff prepares and suggests; the user decides. Nothing is sent
or closed without them, and every message says which it is ("ready for you to
review", "looks done — confirm?"), never "sent" or "closed" for something the
user didn't do. Written into `safety.md` §1b.

## 1. Prepared replies

- **Who:** a new `prepare` skill. The radar runs it after saving, in
  scheduled runs; the user can run it on demand ("draft T-42").
- **What:** up to 3 tasks per run, *Needs you now* first then *I owe*, where
  someone asked the user something by email, with no `prepared` document since
  the task's last change. Never:
  - prompt-injection threads, or payment, bank, password or access requests;
  - *Decide* tasks (the user hasn't chosen yet);
  - *Waiting on* tasks (someone else owes the reply);
  - tasks marked `looks done`, or closed tasks.
- **Draft:** in the thread's language and the user's voice (lessons, earlier
  sent mail), under ~120 words, facts only from the thread, the radar and
  `config`. What only the user knows becomes a `[placeholder]`; no invented
  numbers, dates, promises or attachments, and no codes or account numbers.
- **Where:** `runs/YYYY-MM-DD HHMM prepared T-<n>` (contract in
  `registry-layout.md`). It is never a mail draft: unattended runs stay
  read-only on sources. The newest one per task wins.
- **Dashboard:**
  - the task shows *Draft ready*;
  - *Review the draft* loads the document into the editor with its notes;
  - saving with `[placeholders]` left asks once;
  - saving is the existing Gmail draft, never a send.
- **Brief:** a *Ready for you* section.

## 2. Looks done, never closed

- **Evidence marks a task, never closes it.** Evidence is the other person
  saying it's done, the user's own reply already sent, or a Linear issue
  moved to Done. The radar keeps the task in its section and ends its line
  with `— looks done: <what shows it> (<date>) <evidence link>`.
- **The user confirms or rejects:**
  - *Yes, it's done* (dashboard) or "T-4 is done" (chat) → the usual `close —
    done` handoff;
  - *Not yet*, or "it's not done" in chat → a new `keep open` handoff. The
    radar drops the mark, writes `kept open <date>`, and suggests again only
    on newer evidence.
- **Closing reasons:** a task is closed only by the user's own close (`done`,
  `not mine`) or by `expired` (a *Decide* item untouched for 14 days, a notice
  past its date). `resolved` is gone. `check_radar.py` errors on a task newly
  closed with any other reason, and on a closed task still marked `looks done`.

## Verification

- `tests/fixtures/radar/`: `closed-on-evidence` (error), `looks-done` (ok),
  `looks-done-no-date` (warning).
- **Evals on Haiku, 2 runs each, all 1.0:**
  - `radar-sweep` and `radar-linear` now require `looks done` instead of a
    close;
  - `prepare-replies` (new) requires a draft for the VIP's request, none for
    the injection, and no approval given on the user's behalf.
- **Dashboard in headless Chromium:**
  - *Draft ready* shows on the task;
  - the prepared draft loads with its subject;
  - the placeholder warning appears once, then the Gmail draft is saved;
  - *Not yet* writes `keep open` for the task.
