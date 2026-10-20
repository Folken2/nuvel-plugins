# Registry layout

The registry is a plain folder of Markdown files that lives wherever the user
keeps their work: Google Drive, OneDrive, SharePoint, or a local folder. It is
the chief of staff's only memory **and** its logbook.

## Why it exists: two kinds of session that never share context

1. **Routines** (radar, brief, weekly-review) run on a schedule, each in a
   brand-new session with no memory of previous runs and no access to the
   project the user is working in. Everything a routine knows comes from the
   registry; everything it learns goes back into it before it ends.
2. **The main agent** — the Claude or Codex session in whatever project the
   user is working on. It never saw the routines run. When it needs to know what
   happened ("did Ana answer?", "what's on today?"), it reads the registry: the
   `recall` skill answers from it, and in Claude a session-start hook injects a
   short summary automatically.

The registry is the only bridge between them, in both directions:
routines → main agent through `CONTEXT.md`, `loops.md` and `log/`;
main agent → routines through `handoff.md`. So every file must make sense to a
reader with zero prior context.

Default root folder name: `Chief of Staff/` (the user may rename it during setup;
the real path is stored in `config.md`).

```
Chief of Staff/
├── README.md              # what this folder is, for humans (from templates/README.md)
├── config.md              # who the user is + which sources, storage and routines are on
├── CONTEXT.md             # the living snapshot — rewritten by every radar run
├── loops.md               # open commitments: what I owe, what I'm waiting on
├── handoff.md             # notes from the main agent / the user to the next routine runs
├── log/
│   └── YYYY/MM/YYYY-MM-DD.md   # append-only journal: one section per routine run
├── briefs/YYYY-MM-DD.md   # morning briefs
├── prep/YYYY-MM-DD-<meeting-slug>.md   # meeting prep notes
├── reviews/YYYY-Www.md    # weekly reviews (ISO week)
├── people/<person-slug>.md    # one note per recurring person
├── projects/<project-slug>.md # one note per active project / deal / thread
└── .state/
    └── radar.json         # cursors, so sweeps are incremental and idempotent
```

Create folders lazily: `setup` creates the root, `README.md`, `config.md`,
`CONTEXT.md`, `loops.md`, `handoff.md` and `.state/`. The other folders appear the first time a
skill needs them.

## Finding the registry

Scheduled runs start in a clean session with no memory, so every skill locates
the registry the same way, stopping at the first hit:

1. **The prompt.** Routines created by `setup` always end with
   `Registry: <storage.kind> <storage.root>` — use it.
2. **The pointer file** `~/.chief-of-staff.json` on this computer
   (`{"kind": "...", "root": "..."}`), written by `setup`. Absent in cloud runs.
3. **Ask the user** — only in an interactive session. In an unattended run,
   stop and report that the registry could not be found; never create a new one.

Then read `config.md` and treat it as the source of truth (it may say the
registry moved).

## File contracts

### `config.md`

YAML frontmatter is the machine-readable part; the body is free text the user can
edit. Start from `templates/config.md`. Required keys:

| Key | Meaning |
|---|---|
| `version` | Registry format version. Currently `1`. |
| `owner.name`, `owner.role`, `owner.timezone` | Who this chief of staff serves. Timezone is IANA (`Europe/Madrid`). |
| `owner.language` | Language every note and brief is written in. |
| `storage.kind` | `synced-folder` \| `google-drive` \| `onedrive` \| `sharepoint` \| `local` (see `storage.md`). |
| `storage.root` | Absolute path (synced/local) or the folder ID/URL (connector). |
| `sources` | List of `{kind, via, scope}` — e.g. `{kind: email, via: gmail-connector, scope: "inbox, last 2h"}`. |
| `vips` | People whose messages are always surfaced. |
| `priorities` | The 3–5 things that matter this quarter. Radar ranks everything against these. |
| `routines` | What is scheduled, where, and its ID in that scheduler (so it can be changed later). |
| `quiet_hours` | When radar should log but never notify. |

### `CONTEXT.md`

The single page the user (or any agent) reads to know "what is going on right
now". **Rewritten in full** on every radar run, never appended to. Sections, in
this order, each kept short:

1. `Updated:` timestamp + which sources were swept (and which failed).
2. `## Needs you now` — at most 5 items, each with why + link to the source.
3. `## Today` — remaining meetings with one-line context each.
4. `## Open loops` — top items from `loops.md` that are due or overdue.
5. `## Moving` — what changed since the last sweep, grouped by project.
6. `## Watching` — slow signals: a thread going quiet, a deadline approaching.

### `loops.md`

Two tables — `## I owe` and `## Waiting on` — with columns
`| what | who | due | source | since |`. Radar adds, updates and closes rows; a
closed row moves to `## Closed (last 14 days)` and is dropped after 14 days.
Every row links to its source (email permalink, event link, message link).

### `log/YYYY/MM/YYYY-MM-DD.md` — the journal

Append-only, shared by **every** skill run (scheduled or interactive), so the
main agent can reconstruct what happened and why. One section per run:

```markdown
## 10:02 radar · scheduled · claude — ok (chat ✗ auth expired)
- Swept: 14 emails (3 relevant), 2 calendar changes, chat skipped.
- [project-x] Ana confirmed the pilot start for 03/11 → loops: closed "confirm pilot date".
- [hiring] New candidate packet from recruiting, interview Thu 16:00.
- Handoff: "watch for Acme's reply" — not yet, kept open.
```

Heading format: `## HH:MM <skill> · <scheduled|interactive> · <claude|codex|other> — <ok|partial|failed> (<short note>)`.
Then bullets: what was read, what changed in which file, what was handed back
(`handoff.md` items done or still open), and errors. A run that changes
nothing still writes its heading with `— ok (nothing new)`.

Never rewrite earlier sections. If a run fails half-way, the next run appends its
own section; the cursors in `.state/radar.json` make that safe.

### `handoff.md`

The channel from the main agent (or the user) to future routine runs. Each item
is a checkbox with who/when/until:

```markdown
## Open
- [ ] Watch for Acme's reply on the pricing proposal; flag it in Needs you now. — main agent, 2026-10-20, until 2026-10-24
- [ ] Ignore the "Q4 offsite" thread, it's handled. — user, 2026-10-20

## Done
- [x] Tell me when the contract is signed. — done 2026-10-21 10:02 radar (signed by Luis)
```

Every routine reads `## Open` before working and applies it. Items with a past
`until` date are moved to `## Done` as expired. A routine marks an item done
only when it has actually happened, and logs that in the journal. Keep `## Done`
to the last 14 days.

### `people/<slug>.md` and `projects/<slug>.md`

Short, factual, dated bullets under `## Timeline`, newest first, plus a
`## Now` paragraph that radar keeps current. Slugs are lowercase-hyphenated
(`ana-garcia`, `project-x`). Only create a note for a person or project that
shows up in at least two sweeps or is a VIP/priority — not for every sender.

### `.state/radar.json`

```json
{
  "version": 1,
  "last_run": "2026-10-20T10:02:00+02:00",
  "sources": {
    "email":    {"cursor": "2026-10-20T10:01:40+02:00", "status": "ok"},
    "calendar": {"cursor": "2026-10-20T10:01:52+02:00", "status": "ok"},
    "chat":     {"cursor": "2026-10-20T08:00:11+02:00", "status": "error", "error": "auth expired"}
  },
  "seen": ["<sha1 of source id>", "..."]
}
```

- `cursor` per source: only advance it after that source's findings are written.
- `seen`: hashes of the last ~500 item IDs, so overlapping windows never log an
  item twice. Store hashes, not raw IDs or subjects.
- A source in `error` keeps its old cursor, so the next run retries the gap.

## Writing rules

- Write in `owner.language`. Dates as `YYYY-MM-DD`, times in `owner.timezone`.
- Link to the source instead of copying it. Quote at most one line from any email.
- Never write secrets, one-time codes, passwords, bank or ID numbers, or health
  details into the registry, even when they appear in a source. See `safety.md`.
- Keep every file small enough to read in one go: `CONTEXT.md` under ~150 lines,
  person/project notes under ~100 lines (summarise older timeline entries).
