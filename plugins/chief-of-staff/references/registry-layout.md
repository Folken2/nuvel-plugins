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
├── runs/
│   ├── 2026-10-20 1940 radar             # journal of that run + full state snapshot
│   ├── 2026-10-21 0730 brief
│   ├── 2026-10-21 1100 prep acme-qbr
│   └── 2026-10-24 1600 weekly-review
└── handoff/
    └── 2026-10-20 1945 handoff           # one instruction from the main agent / user
```

Folder names (`config`, `runs`, `handoff`) are fixed and in English so every
skill finds them; document **content** is in `owner.language`.

### Document names

`YYYY-MM-DD HHMM <kind>[ <slug>]`, in the owner's timezone, 24 h. Names sort
chronologically, so the newest is the greatest name. `<kind>` is one of
`config`, `radar`, `brief`, `prep`, `weekly-review`, `recall`, `setup`,
`handoff`.

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
   `title = 'Chief of Staff' and mimeType = 'application/vnd.google-apps.folder'`)
   that contains a `config` folder. On a computer, `~/.chief-of-staff.json`
   (`{"kind": "...", "root": "..."}`) may also point to it.
3. **Ask the user** — only in an interactive session. In an unattended run,
   stop and report that the registry could not be found; never create one.

Then resolve the subfolder IDs (`config`, `runs`, `handoff`) — they are listed
in the newest `config` under `storage.folders`.

## Finding "the newest"

List the folder restricted to a recent window and take the greatest name, e.g.
on Drive: `parentId = '<runs id>' and title contains 'radar' and createdTime > '<now − 3 days, RFC 3339>'`.
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
- storage.folders: config=<id>, runs=<id>, handoff=<id>
- quiet_hours: 20:00-08:00
- notify: needs-you-now

## Priorities
1. …

## VIPs
- <name> <email> — <why>        (or "none yet")

## Sources
- email: <tool/connector> — <scope>
- calendar: …

## Routines
- radar: <mechanism> — <schedule> — <id or "manual">

## How I work
<free text>
```

Headings and keys stay in English (skills parse them); values and free text are
in `owner.language`. Changing anything = writing a new `config` document with
the full content (copy the previous one, change what's needed).

### `radar` run — journal + state snapshot

The newest `radar` run **is** the current picture. It always carries the full
state forward, even when nothing changed.

```markdown
# Radar · 2026-10-20 19:40 · scheduled · claude — ok

## Journal
- Window: email since 2026-10-20 17:40 · calendar today + 2 working days
- Read: 14 emails (3 relevant), 2 calendar changes.
- [nuvel-0.5] … what changed, with link.
- Handoff: "watch for Acme's reply" — not yet.
- Errors: none.

## Needs you now
- <what> — <why it matters> — <link>        (max 5)

## Decide
- <unsolicited proposal / invitation / opportunity> — <who> — <why it may matter> — <link> — since <date>

## Today
- 11:00 <meeting> — <one-line context>

## Open loops
### I owe
- <what> — <who> — due <date> — <link> — since <date>
### Waiting on
- …
### Closed (last 14 days)
- <what> — <who> — closed <date>

## Moving
- [project] <what changed recently>

## Watching
- <slow signals; dated notices with their date/amount: renewals, expiries, invoices>

## Handoff
- open: <handoff doc name> — <instruction>
- done: <handoff doc name> — <outcome> (<date>)

## Cursors
- email: 2026-10-20T19:39:00+02:00 — ok
- calendar: 2026-10-20T19:39:10+02:00 — ok
- seen: <opaque source ids logged in the last ~3 runs, comma-separated>
```

Rules:
- Section headings stay in English (other skills and runs parse them); the
  bullets are in `owner.language`.
- `Cursors`: a failed source keeps its previous cursor (copied from the
  previous radar) with `— error: <reason>`.
- `seen` holds raw opaque item IDs (e.g. Gmail thread IDs) — never subjects,
  names or addresses — so overlapping windows don't log an item twice.
- `Closed` keeps 14 days; older items drop off the snapshot (they stay in history).
- `I owe` is only for real commitments: something the user promised, or a
  direct ask from someone they work with. Inbound the user never asked for
  (cold proposals, partnership offers, invitations) goes to `Decide`; items
  there drop off after 14 days without action (they stay in history).

### Other runs (`brief`, `prep`, `weekly-review`, `recall`, `setup`)

```markdown
# Brief · 2026-10-21 07:30 · scheduled · claude — ok

## Journal
- Based on: radar 2026-10-21 0600. Read: calendar today.
- Notes: <anything missing or odd>

<the brief / prep / review itself>
```

They don't carry state; the newest `radar` stays the current picture.

### `handoff` — instructions to future runs

```markdown
# Handoff · 2026-10-20 19:45

- instruction: Watch for Acme's reply on the pricing proposal; put it in Needs you now.
- from: main agent (on behalf of the user)
- until: 2026-10-24
```

A handoff is open until a `radar` run lists it under `## Handoff` as `done`
(or `until` has passed — then `done: expired`). Handoffs may only ask routines
to **watch, rank, ignore or remind** — never to send, reply, accept or delete.

## Searching history

History is all of `runs/`. To answer "what happened with X", search the runs
folder's full text (Drive: `parentId = '<runs id>' and fullText contains 'Acme'`)
and quote the matching run's name as the "when".

## Writing rules

- Write in `owner.language`. Dates `YYYY-MM-DD`, times in `owner.timezone`.
- Link to the source instead of copying it. Quote at most one line of any email.
- Never write secrets, one-time codes, passwords, bank or ID numbers, or health
  details, even when they appear in a source. See `safety.md`.
- Keep a radar snapshot under ~150 lines: summarise, link, drop stale items.
