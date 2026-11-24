# Dashboard

A private web page (a claude.ai artifact) where the user works through the
chief of staff's to-dos without opening a chat: what needs them, decisions,
what they owe, what others owe them, today's calendar, and things worth
knowing. It reads the registry **live**, through the viewer's own connectors,
every time it opens. Created by the `dashboard` skill (setup runs it).

## Always built the same way

The page is never written by hand, by Claude or anyone else. It is always:

1. the template in `templates/dashboard/` (`index.html`, `app.css`,
   `strings.js`, `radar.js`, `app.js`), shipped with the plugin version;
2. filled in by `scripts/build_dashboard.py` with one settings block taken from
   the newest `config`;
3. published with exactly the capabilities the script prints.

Same config and plugin version in, same page out. The page holds **no task,
email or calendar data**: only the settings below. To change the page, change
the template in this repository; to refresh a user's page, rebuild and
republish it (the `dashboard` skill, to the same link).

### Settings block

| key | from `config` |
|---|---|
| `template` | plugin version that built the page |
| `owner.name`, `owner.language`, `owner.timezone`, `owner.working_hours` | same keys (`language` outside en/ca/es shows the English interface; radar text stays as written) |
| `storage.kind`, `storage.root` | same keys |
| `storage.runs`, `storage.handoff` | the `runs` and `handoff` ids in `storage.folders` |
| `email` | `gmail` when the `## Sources` email line names Gmail, else `other` / `none` |
| `calendar` | `google` when the calendar line names Google Calendar, else `other` / `none` |

### Capabilities

Only the `mcp` capability, with these connectors and **exact** tool names:

| connector | tools | why |
|---|---|---|
| `Google Drive` | `search_files`, `read_file_content`, `create_file` | find and read the newest radar and brief; write close handoffs |
| `Gmail` | `get_thread`, `create_draft` | reply in the right thread; save a draft (never send) |
| `Google Calendar` | `list_events`, `create_event` | today's meetings; add a busy block |

Gmail and Google Calendar are left out when the config's sources aren't
Gmail / Google Calendar; their features then don't show.

**Microsoft 365: not yet.** The page needs exact tool names, and the Microsoft
connector's aren't confirmed. `build_dashboard.py` stops with exit code 3 for
OneDrive / SharePoint storage; the `dashboard` skill tells the user in one
sentence and setup carries on without it. To add it, fill in `MICROSOFT` in the
script and the matching calls in `app.js`.

Local or synced folders can't be read from a web page: no dashboard (exit 1).

## Data (what the page shows)

From the newest `radar` in `runs/` and its month folders (searched with
`'<runs id>' in ancestors`, picked by name, never by search order; window 3
days, then 14, then everything):

| view | radar sections |
|---|---|
| Today · *Needs you* | top 3 open to-dos, overdue first |
| To-do | *Needs you now* (`needs`), *Decide* (`decide`), *I owe* (`owe`); one row per task ID — a task in *Needs you now* and *I owe* is one row; *Done* = closed in the last 7 days |
| Delegated | *Waiting on*; "overdue or waiting a week" when `due` passed or *since* ≥ 7 days |
| Nice to know | *Watching* and *Moving*, grouped by `[project]` tag |
| Calendar | today's events from Google Calendar (declined and all-day left out); free gaps ≥ 45 min in `owner.working_hours`, labelled with the brief's *Free blocks* |
| Focus | `**Focus today:**` of today's brief, when there is one |
| *Draft ready* | the newest `prepared T-<n>` document in `runs/` for an open task |
| *Looks done?* | a task whose line ends with `— looks done: …`: the evidence, its link, and the user's two choices |
| *Snoozed* (To-do tab) | tasks marked `— snoozed until <date>` (or snoozed on this page and not yet applied), with their date |
| *Suggestions* (Today) | the `## Proposed` lines of the newest `lessons` document (needs the `lessons` folder in `config`) |

Item fields follow the radar contract (`T-<n> — <what> — … — due … — <link> —
since …`); `since` / `closed` dates are read whatever word precedes them
(radars write them in `owner.language`). *Stale* = the newest radar is more than
18 hours old and from an earlier day.

## Actions (what the page writes)

Only on the viewer's click, with the viewer's own connectors:

| action | writes |
|---|---|
| **Done** (status ring, or *Done* in the sheet) | after a 6-second undo window, one `handoff/YYYY-MM-DD HHMM handoff` with `instruction: close — done` and `task: T-<n>` (contract in `registry-layout.md`); the next radar moves the task to *Closed* |
| **Not mine** | the same, with `close — not mine` |
| **Yes, it's done** (on a task marked `looks done`) | the same `close — done` handoff: the user confirms what the radar suggested |
| **Not yet** (on a task marked `looks done`) | a `keep open` handoff; the radar drops the mark and suggests it again only on new evidence |
| **Review the draft** (a task with a `prepared` document) | nothing by itself: it opens the prepared reply in the editor; saving it is the same Gmail draft as *Reply*, plus a `learn — draft edited` note (both texts) or `learn — draft used` in the registry |
| **Remind me** (Tomorrow / Monday / Next week) | after the undo window, a `snooze until <date>` handoff; the task moves to the *Snoozed* tab until then |
| **Keep / Dismiss** on a suggestion | a `lesson — keep P-<n>` or `lesson — drop P-<n>` handoff; only a kept suggestion ever changes anything |
| **Reply / Follow up / Accept / Decline / Ask for more time** | one Gmail **draft** (`create_draft`), in the thread when the link is a Gmail thread; the user edits and sends it from Gmail. Never sent. |
| **Block time** | one busy event on the user's own calendar (`create_event`, no attendees, no notifications) |
| In progress, *Got it*, sidebar | nothing: kept in the viewer's browser only |

Rules the page keeps:

- Handoff names never repeat: if the name exists, the next minute is used.
- A handoff write that failed ambiguously (timeout, upstream error) is looked
  for before it is written again, so a task is never closed twice.
- A close the viewer made but the page couldn't save (the page was closed
  during the undo window) is saved the next time the page opens, and never
  silently: a note names the task while it is saved, its row reads
  *Closing…*, and a toast confirms it with the task's title.
- Items without a task ID (radars before 0.5) can't be closed from the page
  until the next radar numbers them.
- Every text from the registry is shown as text, never as HTML; only `https`
  links open.
- Saving a draft that still has `[placeholders]` asks once ("Some parts in
  [brackets] still need you") and saves on the second press.
- The user decides: nothing on the page closes a task or sends anything
  without a click, and the page says so where it matters ("Is it done? You
  decide; nothing closes on its own.").

## States

Each section shows its own failure, by error code: Drive unreadable (reconnect,
add, allow for this page, organization policy, try again), calendar unavailable,
drafts not allowed (Gmail tool missing or blocked: *Open in Gmail* instead),
first day (no radar yet), stale radar, opened outside Claude (no connector
access), Microsoft 365 storage.

## Updating

`config` records `- dashboard: <artifact link>` and `- dashboard.version:
<plugin version>`. When the plugin is newer than `dashboard.version`, or the
config's language, timezone, working hours, folders or sources changed, run the
`dashboard` skill again: it republishes to the same link.

## Safety

The dashboard is the one place where the plugin writes outside the registry,
and only because the user clicked: a draft they will send themselves, a busy
block on their own calendar. Skills and routines stay read-only on every source
(`safety.md` §1).
