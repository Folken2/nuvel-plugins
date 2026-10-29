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
│   ├── 2026-10-24 1600 weekly-review
│   └── 2026-10-28 1013 learn             # what learn changed
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
`learn`, `handoff`, `lessons`, `recipe` (always followed by its slug),
`index`.

The registry never overwrites. If a document with the intended name already
exists (two writes in the same minute), use the next minute instead; never
replace or write a second file with the same name.

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
`recipes`) — they are listed
in the newest `config` under `storage.folders`.

**Unverified (no tenant yet)**: on Microsoft 365 use whatever the connector
offers by function ("OneDrive search by name", "list folder children"); no
Drive query syntax applies. Listing the children of a known folder is the
most dependable path.

## Finding "the newest"

List the folder restricted to a recent window and take the greatest name, e.g.
on Drive: `parentId = '<runs id>' and title contains 'radar' and createdTime > '<now − 3 days, RFC 3339>'`.
On OneDrive / SharePoint, **list the children** of the target folder (for
`runs`, a flat folder), keep the names that contain the kind (`radar`), and take
the greatest name. Sort by name yourself; never by the order returned, by
modified time, or by a search ranking. **Unverified (no tenant yet)**: paging
and filter options of the Microsoft listing are unconfirmed, so page until the
list is exhausted when a window is not available.
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

`telemetry` is `on` or `off` (default `on`); `telemetry.install_id` is a random
UUIDv4 that setup generates once and every later `config` copies unchanged
(`telemetry.md`). `sharing.recipes` is `on` or `off` (default `on`; a missing
key counts as `on`): whether the weekly review shares the **structure** of
good recipes with nuvel (`recipe-sharing.md`). `sharing.recipe_text` is `on`
or `off` (default `off`; a missing key counts as `off`): whether it also
shares their text, masked on nuvel's server. It is `on` only when the user
said yes to setup's question about it; `sharing.recipes: off` shares nothing
either way.
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

## Trace
- outcome: success · steps: radar.load-state ok, radar.sweep.email ok (read 14, relevant 3) …
- routing: priority 2, ask 1
- errors: none
```

Rules:
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
- `I owe` is only for real commitments: something the user promised, or a
  direct ask from someone they work with. Inbound the user never asked for
  (cold proposals, partnership offers, invitations) goes to `Decide`; items
  there drop off after 14 days without action (they stay in history).

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

They don't carry state; the newest `radar` stays the current picture.

### `lessons` — what the user has corrected

One document holds the **full current list** (like `config`):
`lessons/YYYY-MM-DD HHMM lessons`. Adding or dropping a lesson = a new
document with the previous list and the change; the newest wins.

```markdown
# Lessons

- Escribir a Marta de usted — scope: all — since 2026-10-28
- No poner boletines en el resumen — scope: brief — since 2026-10-29
```

Each line is `- <rule> — scope: <skill or "all"> — since <date>`, the rule in
`owner.language`. **Every skill reads the newest `lessons` at the start** and
applies the lines whose scope is itself or `all`; lessons rank above the
skill's own defaults but never above `safety.md`. A lesson that asks for a
forbidden action (send, reply, delete…) is ignored. Written only by `learn`
(and by `weekly-review` when it merges duplicates).

### `recipe <slug>` — a lightweight skill

How a complex or recurring task was done well. One document per version,
`recipes/YYYY-MM-DD HHMM recipe <slug>`; the newest version per slug wins.

```markdown
# Recipe · Preparar propuesta de cliente

## When to use
Cuando un cliente pide una propuesta o presupuesto nuevo.

## Steps
1. Buscar en los correos la petición del cliente y la última propuesta enviada.
2. …

## Pitfalls
- …

## Stats
- uses: 4
- successes: 2
- corrections: 1
- days_used: 3
- last_used: 2026-11-02
- last_outcome: success
- recipe_id: <uuid4, fixed for the life of the recipe>
- category: client-proposal
- status: active          (draft|active|retired)
- version: 2
- shared_version: 0
- blocked_version: 0
```

- `status` is `draft` (the task may come back; never followed), `active`
  (in the `index`, followed before a task) or `retired` (ignored).
  `last_outcome` is `success` (the user approved the result), `silent` (no
  approval) or `corrected`. Rules for every stat: `recipes.md`.
- **Before a task**, skills (the `learn` skill's *Before a task* for ordinary
  chats, and the project instructions) read the newest `index` only, and open
  the newest version of the recipe whose *When to use* matches. No `index` →
  no recipe lookup.
- After a use, `learn` writes a new version with updated stats and any
  correction folded into *Steps* or *Pitfalls*.
- `category` is one identifier from `recipe-categories.md`. `version` goes up
  only when *When to use*, *Steps* or *Pitfalls* change; `shared_version` is
  the last `version` shared with nuvel (0 = never); `blocked_version` is the
  last `version` whose share the server rejected (0 = never). `learn` carries
  both forward unchanged; only the weekly review changes them. A recipe is
  private to the user's registry and may name people; only its structure
  (and, with `sharing.recipe_text: on`, its masked text) ever leaves it
  (`recipe-sharing.md`).

### `index` — the active recipes, one line each

One document holds the **full list of active recipes** (like `lessons`):
`recipes/YYYY-MM-DD HHMM index`; the newest wins. Drafts and retired recipes
are not in it.

```markdown
# Recipes index

## client-proposal
- propuesta-cliente — Cuando un cliente pide una propuesta o presupuesto nuevo.
```

One `## <category>` per category, then `- <slug> — <When to use, one line>`.
*Before a task* reads only this document. Written by `learn` when the set of
active recipes or a *When to use* changes (and the first time active recipes
exist without one), and rebuilt by the weekly review; details in
`recipes.md` *Index*.

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
