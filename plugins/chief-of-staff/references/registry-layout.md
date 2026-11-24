# Registry layout

The registry is a folder in the user's own storage (Google Drive, OneDrive,
SharePoint, or a local/synced folder). It is the chief of staff's only memory
**and** its logbook.

## Why it exists: two kinds of session that never share context

1. **Routines** (radar, brief, weekly-review) run on a schedule, each in a
   brand-new session with no memory of previous runs and no access to the
   project the user is working in. Everything a routine knows comes from the
   registry; everything it learns goes back into it before it ends.
2. **The main agent** — the Claude / Cowork (or Codex) conversation where the
   user is working. It never saw the routines run. When it needs to know what
   happened ("did Ana answer?", "what's on today?"), it reads the registry
   through the `recall` skill.

The registry is the only bridge between them, in both directions:
routines → main agent through `runs/`; main agent → routines through `handoff/`.
Every document must make sense to a reader with zero prior context.

## The one rule: every run writes one new document; the newest wins

Storage connectors (e.g. the Google Drive connector) can create files but often
cannot edit them. So the registry is **append-only**: nothing is ever edited in
place. Each skill run creates exactly one new document; "the current X" is
always the newest document of that kind. This also means concurrent runs never
conflict and the full history comes for free.

```
Chief of Staff/
├── LLEGEIX-ME / README      # for humans, written once by setup (in owner.language)
├── config/
│   └── 2026-10-20 1935 config            # newest = configuration in force
├── runs/                                 # one folder per month (see *Month folders*)
│   ├── 2026-10/
│   │   ├── 2026-10-20 1940 radar         # journal of that run + full state snapshot
│   │   ├── 2026-10-21 0730 brief
│   │   ├── 2026-10-21 1100 prep acme-qbr
│   │   ├── 2026-10-24 1600 weekly-review
│   │   └── 2026-10-28 1013 learn         # what learn changed
│   └── 2026-11/
│       └── 2026-11-02 0807 radar
├── handoff/
│   └── 2026-10-20 1945 handoff           # one instruction from the main agent / user
├── lessons/
│   └── 2026-10-28 1012 lessons           # full list of lessons; newest wins
└── recipes/
    ├── 2026-10-28 1130 recipe propuesta-cliente
    ├── 2026-11-02 0915 recipe propuesta-cliente   # newer version wins per slug
    └── 2026-11-02 0916 index                      # active recipes; newest wins
```

Folder names (`config`, `runs`, `handoff`, `lessons`, `recipes`) are fixed and in English so every
skill finds them; document **content** is in `owner.language`.

### Document names

`YYYY-MM-DD HHMM <kind>[ <slug>]`, in the owner's timezone, 24 h. Names sort
chronologically, so the newest is the greatest name. `<kind>` is one of
`config`, `radar`, `brief`, `prep`, `weekly-review`, `recall`, `setup`,
`learn`, `prepared` (always followed by its task ID: `prepared T-42`),
`handoff`, `lessons`, `recipe` (always followed by its slug), `index`.

The registry never overwrites. If a document with the intended name already
exists (two writes in the same minute), use the next minute instead; never
replace or write a second file with the same name.

### Month folders in `runs/`

`runs/` holds one folder per month, named `YYYY-MM` (the month in the
document's own name). Wherever a skill says "create `runs/<name>`", the
document goes in `runs/<YYYY-MM of name>/<name>`, **unless** the newest
`config` has a `dashboard` whose `dashboard.version` is older than 0.8.0: that
page only reads documents directly in `runs/`, so keep writing there (flat)
until the `dashboard` skill republishes it and records a newer version. No
`dashboard` line → month folders.

1. Look for the month folder among the direct children of `runs/` (Drive:
   `parentId = '<runs id>' and title = '2026-11' and mimeType =
   'application/vnd.google-apps.folder'`; OneDrive: list the children of
   `runs/`; local: the path).
2. None → create it (a folder named `YYYY-MM` inside `runs/`, nothing else),
   then create the document in it. Two folders with the same month (two runs
   racing on the 1st) are harmless: write into either, reads cover both.
3. Never move older documents. Registries made before 0.8.0 keep their flat
   documents directly in `runs/`; every read below still finds them.

Only `runs/` uses month folders. `config/`, `handoff/`, `lessons/` and
`recipes/` stay flat.

### Formats by storage

| Storage | Document type | Why |
|---|---|---|
| Google Drive connector | **Google Doc** (upload Markdown with conversion on) | The connector reads Docs as text; plain `.md` files come back empty or as base64. |
| OneDrive / SharePoint connector | `.md` if the connector reads it back as text, else `.docx` — check with one write + read at setup | Same reason. |
| Synced or local folder | `.md` | Plain files. |

Google Docs mangle YAML frontmatter, so **no document uses frontmatter**:
structured data is written as `- key: value` bullet lists (see `config`).

## Finding the registry

Every skill locates it the same way, stopping at the first hit:

1. **The prompt.** Routines created by `setup` always end with
   `Registry: <storage.kind> <folder id or path>` — use it.
2. **Search the storage** for a folder titled `Chief of Staff` (Drive:
   `title = 'Chief of Staff' and mimeType = 'application/vnd.google-apps.folder'`;
   OneDrive: list the children of the drive root and match the folder name
   `Chief of Staff`) that contains a `config` folder. On a computer, `~/.chief-of-staff.json`
   (`{"kind": "...", "root": "..."}`) may also point to it.
3. **Ask the user** — only in an interactive session. In an unattended run,
   stop and report that the registry could not be found; never create one.

Then resolve the subfolder IDs (`config`, `runs`, `handoff`, `lessons`,
`recipes`) — they are listed in the newest `config` under `storage.folders`.

**Tested on a real tenant (2026-11)**: on Microsoft 365 use whatever the connector
offers by function ("OneDrive search by name", "list folder children"); no
Drive query syntax applies. Listing the children of a known folder is the
most dependable path.

## Finding "the newest"

List the folder restricted to a recent window and take the greatest name, e.g.
on Drive: `'<runs id>' in ancestors and title contains 'radar' and createdTime > '<now − 3 days, RFC 3339>'`.
For `runs/` always use `'<runs id>' in ancestors` (it covers every month
folder and older flat documents), never `parentId`; the other folders are flat,
so `parentId` is fine there. A document created a moment ago is found at once
(tested 2026-11). On OneDrive / SharePoint and in local folders, **list the
children** of the target folder; for `runs/`, list the greatest month folder,
then the one before it, then the documents directly in `runs/` (older
registries), stopping at the first that has the kind. Keep the names that
contain the kind (`radar`), and take the greatest name. Sort by name yourself; never by the order returned, by
modified time, or by a search ranking. On Microsoft 365, page until the list
is exhausted when a window is not available.
If nothing comes back, widen the window (14 days, then no limit). Never rely on
the order a search returns.

## Document contracts

### `config` — the configuration in force

```markdown
# Chief of staff configuration

- version: 1
- paused: false
- owner.name: …
- owner.role: …
- owner.timezone: Europe/Madrid
- owner.language: ca
- owner.working_hours: 09:00-19:00 Mon-Fri
- storage.kind: google-drive
- storage.root: <folder id or path>
- storage.folders: config=<id>, runs=<id>, handoff=<id>, lessons=<id>, recipes=<id>
- quiet_hours: 20:00-08:00
- notify: needs-you-now
- telemetry: on
- telemetry.install_id: <uuid4, generated once by setup, never changed>
- sharing.recipes: on
- sharing.recipe_text: off
- dashboard: <artifact link>          (once the dashboard exists)
- dashboard.version: <plugin version that built it>

## Priorities
1. …

## VIPs
- <name> <email> — <why>        (or "none yet")

## Sources
- email: <tool/connector> — <scope>
- calendar: …

## Routines
- routines.model: claude-haiku-5-5
- routines.connectors: <plain names, e.g. Gmail, Google Calendar, Google Drive, Nuvel>
- radar: <mechanism> — <schedule> — <id or "manual">

## How I work
<free text>
```

`dashboard` and `dashboard.version` are written by the `dashboard` skill
(`dashboard.md`); every later `config` copies them. `telemetry` is `on` or `off` (default `on`); `telemetry.install_id` is a random
UUIDv4 that setup generates once and every later `config` copies unchanged
(`telemetry.md`). `sharing.recipes` (missing = `on`) lets the weekly review
share the **structure** of good recipes with nuvel; `sharing.recipe_text`
(missing = `off`, `on` only after a yes to setup's question 6) also shares
their text, masked on nuvel's server (`recipe-sharing.md` *Switches*).
Registries made before v0.3 have no `lessons`/`recipes` in `storage.folders`;
`learn` creates both folders once and writes a new `config` listing them.

Headings and keys stay in English (skills parse them); values and free text are
in `owner.language`. Changing anything = writing a new `config` document with
the full content (copy the previous one, change what's needed).

### `radar` run — journal + state snapshot

The newest `radar` run **is** the current picture. It always carries the full
state forward, even when nothing changed.

```markdown
# Radar · 2026-10-20 19:40 · scheduled · claude — ok

## Owner
- <owner.name from config>

## Journal
- Window: email since 2026-10-20 17:40 · calendar today + 2 working days
- Read: 14 emails (3 relevant), 2 calendar changes.
- [nuvel-0.5] … what changed, with link.
- Handoff: "watch for Acme's reply" — not yet.
- Errors: none.

## Needs you now
- T-<n> — <what> — <why it matters> — due <YYYY-MM-DD> — <link>        (max 5)

## Decide
- T-<n> — <unsolicited proposal / invitation / opportunity> — <who> — <why it may matter> — due <YYYY-MM-DD> — <link> — since <date>

## Today
- 11:00 <meeting> — <one-line context>

## Open loops
### I owe
- T-<n> — <what> — <who> — due <date> — <link> — since <date>
### Waiting on
- T-<n> — <what> — <who> — due <YYYY-MM-DD> — <link> — since <date>
- T-<n> — <what> — <who> — <link> — since <date> — looks done: <what shows it> (<date>) <evidence link>
- T-<n> — <what> — <who> — <link> — since <date> — snoozed until <YYYY-MM-DD>
### Closed (last 14 days)
- T-<n> — <what> — <who> — closed <date> — <done | not mine | expired>

## Moving
- [project] <what changed recently>

## Watching
- T-<n> — <slow signals; dated notices with their date/amount: renewals, expiries, invoices>

## Handoff
- open: <handoff doc name> — <instruction>
- done: <handoff doc name> — <outcome> (<date>)

## Cursors
- email: 2026-10-20T19:39:00+02:00 — ok
- calendar: 2026-10-20T19:39:10+02:00 — ok
- seen: <opaque source ids logged in the last ~3 runs, comma-separated>
- next_task: T-<n>

## Trace
- outcome: success · steps: radar.load-state ok, radar.sweep.email ok (read 14, relevant 3) …
- routing: priority 2, ask 1
- errors: none
```

Rules:
- `## Owner` holds one bullet: `owner.name` from the newest `config`, copied
  as written. It lets readers of the run (the dashboard, a brief) greet the
  user by name. No name in the config → leave the section out.
- **Deadlines:** an item with a deadline carries `due YYYY-MM-DD` (the word
  `due` in English whatever `owner.language` is, the date in
  `owner.timezone`). Turn relative dates into a date ("by Friday" → that
  Friday; "end of month" → its last day; "today" → today). No deadline → leave
  `due` out; never invent one. It goes in *Needs you now*, *Decide*, *I owe*
  and *Waiting on*, and is carried forward unchanged unless the source moves it.
- **Task IDs:** see *Task IDs* below. Every item in *Needs you now*,
  *Decide*, *I owe*, *Waiting on*, *Watching* and *Closed* starts with its
  `T-<n> — `; *Today*, *Moving* and *Journal* items have none (the journal may
  mention IDs: "T-42 new", "T-17 closed").
- `## Trace` is the last section of every run document: exactly what was sent to
  `record_run_trace` (ids, counts, outcome) or one line saying why nothing was
  sent (`telemetry.md`). It never contains content.
- Section headings stay in English (other skills and runs parse them); the
  bullets are in `owner.language`.
- `Cursors`: a failed source keeps its previous cursor (copied from the
  previous radar) with `— error: <reason>`.
- `seen` holds raw opaque item IDs (e.g. Gmail thread IDs) — never subjects,
  names or addresses — so overlapping windows don't log an item twice.
- `Closed` keeps 14 days; older items drop off the snapshot (they stay in history).
  An open task never just disappears: it moves to `Closed` first, with one of
  the reasons above (`expired` for a *Decide* item left 14 days without action
  or a *Watching* notice whose date has passed).
- **The user closes tasks, never the radar.** A task moves to *Closed* as
  `done` or `not mine` only because of the user's own `close` handoff (chat,
  dashboard). Evidence that a task is finished (a reply saying it's done, a
  Linear issue moved to Done, the user's own sent reply) never closes it:
  the radar keeps the task where it is and adds a last field `— looks done:
  <what shows it> (<date>) <evidence link>` (the words `looks done` in English
  whatever `owner.language` is, the rest in it). The user confirms (`close —
  done`) or says it isn't (`keep open`). `expired` is the only reason the
  radar applies by itself.
- **Kept open:** after a `keep open` handoff the radar drops the `looks done`
  field and writes `— kept open <date>` instead, and suggests closing that task
  again only on evidence newer than that date.
- `I owe` is only for real commitments: something the user promised, or a
  direct ask from someone they work with. Inbound the user never asked for
  (cold proposals, partnership offers, invitations) goes to `Decide`; items
  there move to `Closed` as `expired` after 14 days without action.

### Task IDs

A task ID names one task for as long as it exists, in every section and every
run, so the user, the main agent and any other reader can point at it
("T-42 is done") without describing it again.

- **Format:** `T-<n>`, a positive integer with no padding (`T-1`, `T-42`). It
  is the first field of the bullet: `- T-42 — <what> — …`; readers match
  `^- (T-\d+) — `. The same in every `owner.language`.
- **One task, one ID.** A task keeps its ID when it moves between sections
  (Waiting on → Needs you now → Closed). *Needs you now* is a ranked view, so a
  task there may also be listed in *I owe* or *Waiting on* with the **same**
  ID; two different tasks never share one.
- **Match before allocating.** A new finding belongs to a carried task when it
  is the same source thread (thread / conversation ID or link) or the same
  commitment with the same person: update that task's line. Only a new task
  gets a new ID. When unsure, keep the existing task and note the merge in the
  journal.
- **Only radar allocates.** New task → the previous radar's `next_task`, then
  +1. Each radar writes `next_task` as the greater of the previous
  `next_task` and (the highest ID in the previous radar + 1).
- **Never reused.** A closed task stays in *Closed* with its ID for 14 days and
  then drops off; its number is never given out again.
- **First run, or a radar from before 0.5** (no `next_task`): number the
  carried items in section order (*Needs you now*, *Decide*, *I owe*,
  *Waiting on*, *Watching*, *Closed*) from `T-1`, the same task once, and say
  so in the journal ("Task IDs assigned: T-1…T-12").
- IDs are local counters: never sent in telemetry (`telemetry.md`).
- **Checked by a script** where code can run: `scripts/check_task_ids.py` in
  the plugin compares the new radar with the previous one before it is saved
  (radar skill, *Check the radar*, which runs these rules inside `scripts/check_radar.py`). The same sample radars in the repo's
  `tests/fixtures/task-ids/` let any other reader (e.g. a board) run the same
  checks.

### Other runs (`brief`, `prep`, `weekly-review`, `recall`, `setup`, `learn`)

```markdown
# Brief · 2026-10-21 07:30 · scheduled · claude — ok

## Journal
- Based on: radar 2026-10-21 0600. Read: calendar today.
- Notes: <anything missing or odd>

<the brief / prep / review itself>

## Trace
- outcome: success · steps: brief.load-state ok, brief.write ok (meetings 4) …
- errors: none
```

They don't carry state; the newest `radar` stays the current picture. Any
item they copy from the radar keeps its `T-<n>`, so the user can reply with it.

### `lessons` — what the user has corrected

One document holds the **full current list** (like `config`):
`lessons/YYYY-MM-DD HHMM lessons`. Adding or dropping a lesson = a new
document with the previous list and the change; the newest wins.

```markdown
# Lessons

- Escribir a Marta de usted — scope: all — since 2026-10-28
- No poner boletines en el resumen — scope: brief — since 2026-10-29

## Proposed
- P-3 — Firmar los correos «Abrazo, Ana» — scope: prepare — from: 2 drafts edited the same way (2026-11-18, 2026-11-19) — proposed 2026-11-19

## Dismissed
- P-1 — No listar avisos de GitHub — dismissed 2026-11-12
```

Each line is `- <rule> — scope: <skill or "all"> — since <date>`, the rule in
`owner.language`. **Every skill reads the newest `lessons` at the start** and
applies the lines whose scope is itself or `all`; lessons rank above the
skill's own defaults but never above `safety.md`. A lesson that asks for a
forbidden action (send, reply, delete…) is ignored. Written only by `learn`
(and by `weekly-review` when it merges duplicates).

**Proposed lessons** come from the user's decisions, not from something they
said (`learn` *From decisions*). They sit under `## Proposed` with an ID
(`P-<n>`, numbered after the highest P in the document) and what they came
from, and **no skill applies them**. The user keeps one (`lesson — keep P-3`,
from the dashboard or chat) → `learn` moves it to the main list with `since
<today>`; dismisses it (`lesson — drop P-3`) → it moves to `## Dismissed` for
30 days, and the same pattern isn't proposed again in that time. Proposals
nobody answers drop off after 30 days.

### `recipe <slug>` and `index` — recipes

`recipe <slug>` is one version of a lightweight skill (*When to use*, *Steps*,
*Pitfalls*, *Stats*), newest per slug wins; `index` lists the active recipes,
newest wins. Before a task, skills read only the newest `index`. A use is two
`learn` runs: the use, written once at the end of the task, then a separate
outcome run when the user approves or corrects. `version` goes up only when
*When to use*, *Steps* or *Pitfalls* change, or the status changes. Formats,
stats (`draft|active|retired`) and index rules: `recipes.md`.

### `prepared T-<n>` — work prepared for a task, for the user to review

Written by the `prepare` skill in `runs/`, one per task; the newest per task
wins. Never sent anywhere: the user reads it (in the registry or on the
dashboard), edits it and sends it themselves.

```markdown
# Prepared · T-42 · 2026-11-18 09:15

- task: T-42
- kind: reply
- for: Joan Serra (Lumen Logistics)
- source: <link to the thread>
- based on: radar 2026-11-18 0907

## Subject
Re: Renewal — signed copy

## Draft
Hi Joan,

Thanks, glad legal is happy. I'll send you the signed renewal [confirm: by Friday?].

Best,
Ana

## Notes
- Placeholder: the date you commit to.

## Trace
- not sent: telemetry off
```

`kind` is `reply` for now. Placeholders are in square brackets. Headings stay
in English; the draft is in the thread's language.

### Snoozed tasks

`snooze until <date>` (a handoff, from the dashboard or chat) hides a task
until that day: the radar ends its line with `— snoozed until YYYY-MM-DD`
(English keywords), takes it out of *Needs you now* and keeps it in its loop
section. On that date it drops the mark, ranks the task again (it can go back
to *Needs you now*) and says so in the journal ("T-42 back from snooze").

### `handoff` — instructions to future runs

```markdown
# Handoff · 2026-10-20 19:45

- instruction: Watch for Acme's reply on the pricing proposal; put it in Needs you now.
- task: T-42
- from: main agent (on behalf of the user)
- until: 2026-10-24
```

`from` is `main agent (on behalf of the user)`, or `dashboard (on behalf of
the user)` for a `close` the user clicked on the dashboard (`dashboard.md`).

A handoff is open until a `radar` run lists it under `## Handoff` as `done`
(or `until` has passed — then `done: expired`). Handoffs may only ask routines
to **watch, rank, ignore, remind, close, keep open, snooze**, or pass a note
to `learn` — never to send, reply, accept or delete. `task` is optional: with it, the instruction applies to that task only.
`close` needs a `task` and a reason — `- instruction: close — done` or
`close — not mine` — and the next radar moves the task to *Closed* with that
reason; it changes only the registry. `keep open` needs a `task`: the user
says a task the radar thinks looks done isn't (*Kept open* above). `snooze
until YYYY-MM-DD` needs a `task` (*Snoozed tasks* above).

Notes for `learn` (the radar marks them `done` once `learn` has run):

- `lesson — keep P-<n>` / `lesson — drop P-<n>`: the user's answer to a
  proposed lesson.
- `learn — draft edited` (with `task`): written by the dashboard when the user
  saves a prepared reply after changing it. Two sections follow the bullets,
  `## Prepared` and `## Saved`, each the text (at most ~2,000 characters). It
  stays in the user's own registry; it is never sent anywhere.
- `learn — draft used` (with `task`): saved without changes. No text. A `task` that is no longer in the newest
radar → the radar marks the handoff `done: task not found`.

## Searching history

History is all of `runs/`, month folders included. To answer "what happened
with X", search the runs folder's full text (Drive: `'<runs id>' in ancestors
and fullText contains 'Acme'`; OneDrive / local: the connector's search or a
recursive search under `runs/`)
and quote the matching run's name as the "when".

## Writing rules

- Write in `owner.language`. Dates `YYYY-MM-DD`, times in `owner.timezone`.
- Link to the source instead of copying it. Quote at most one line of any email.
- Never write secrets, one-time codes, passwords, bank or ID numbers, or health
  details, even when they appear in a source. See `safety.md`.
- Keep a radar snapshot under ~150 lines: summarise, link, drop stale items.
