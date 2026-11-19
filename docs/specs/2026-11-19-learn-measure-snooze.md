# chief-of-staff 0.7 — learn from decisions, measure, snooze

Date: 2026-11-19. Status: decided in chat ("start 0.7"), following the 0.6
principle: the chief of staff prepares and suggests; the user decides.

## 1. Learn from decisions, as suggestions

- **Signals:**
  - **Draft edits:** the dashboard writes `learn — draft edited` with the
    prepared text and the saved text, or `learn — draft used`, after the user
    saves a prepared reply.
  - **`close — not mine`.**
  - **`keep open`.**
- **Pattern:** at least 2 decisions of the same kind in 30 days:
  - the same change to drafts (greeting, sign-off, formality, length);
  - the same sender, domain or kind of item marked not mine;
  - the same kind of evidence rejected.

  One-off facts typed into a draft are not a pattern.
- **Proposed, never applied:** a pattern becomes `P-<n>` under `## Proposed`
  in the lessons document, with what it came from; no skill applies it.
  - *Keep* (dashboard, chat) → `lesson — keep P-n` → `learn` moves it to the
    main list.
  - *Dismiss* → `## Dismissed` for 30 days, and the pattern isn't proposed
    again in that time.
  - Unanswered proposals drop after 30 days.
- **Where they show:** the dashboard's Today view (*Suggestions*) and the
  weekly review (*Suggested rules*).
- **Privacy:** the draft texts stay in the user's registry. The trace counts
  only `lessons_proposed`, `lessons_kept` and `lessons_dismissed`.

## 2. Measure

Weekly review, *How it went*, computed from the week's handoffs and radars:
- closed by the user (dashboard vs chat), and expired;
- `looks done` confirmed vs kept open;
- replies prepared vs used vs edited;
- median days from first seen to the user's close;
- snoozes, and suggested rules still open.

The same as content-free counts in the weekly-review trace. The radar trace
adds `closed_done`, `closed_not_mine`, `kept_open`, `looks_done_marked` and
`snoozed`.

## 3. Snooze

- **Handoff:** `snooze until YYYY-MM-DD` with a task, from the dashboard
  (Tomorrow / Monday / Next week) or chat.
- **Radar:** marks the task `— snoozed until <date>` and keeps it out of
  *Needs you now* until then. On the date it drops the mark, re-ranks the task
  and notes "back from snooze" in the journal.
- **Checker:** errors on a malformed date, and on a snoozed task in *Needs you
  now*.

## Verification

- `tests/fixtures/radar/`: `snoozed` (ok), `snoozed-in-needs` (error),
  `snoozed-not-a-date` (error).
- **Evals on Haiku:**
  - `learn-decisions` (new): 1.0 on both runs. The kept P-2 moved into the
    lessons; sign-off and Hetzner rules proposed, not applied; no rule from a
    single "not mine" or from facts typed into drafts.
  - `radar-sweep`, `radar-linear`: 1.0.
  - `prepare-replies`: 5 of 6 runs (one judge fail, model variation; the
    drafts in the other runs leave every commitment as a placeholder).
- **Dashboard in headless Chromium:**
  - *Keep* writes `lesson — keep P-3`;
  - saving an edited prepared draft writes `learn — draft edited` with both
    texts;
  - *Remind me → Monday* writes `snooze until <Monday>` and the task appears
    under *Snoozed*;
  - three handoffs in one minute get three different names;
  - no script errors.
