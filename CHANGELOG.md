# Changelog

All notable changes to the plugins in this repo. Versions are per plugin.

## chief-of-staff 0.5.1 - 2026-11-17

A safety net for unattended runs, now that the routines run on Haiku.

### Added

- **Whole-radar check:** `scripts/check_radar.py` checks a new radar against
  the contract before it is saved: header, sections and their order, at most 5
  items in *Needs you now*, `due` written as a real date, cursors and `seen`,
  nothing secret or copied from an email (IBAN, card number, one-time code,
  password, API key, quoted email text), plus every task-ID rule. The radar
  runs it instead of the ID-only check and notes `Radar check: ok` in its
  journal.
- **Radar evals:** `plugins/chief-of-staff/evals/` runs the real radar skill on
  Haiku against a fixture inbox and registry, and grades sorting, closes,
  task IDs, deadlines, secrets and a prompt-injection email. A new `evals`
  workflow runs it on pull requests that touch the radar (needs an
  `ANTHROPIC_API_KEY` secret).

### Changed

- The radar's trace step `radar.check-ids` is now `radar.check`, with
  `check_errors` and `check_fixes` (`id_errors` stays, for task-ID rules).

Design: `docs/specs/2026-11-17-radar-safety-net.md`.

## chief-of-staff 0.5.0 - 2026-11-17

Task IDs on every radar item, and a dashboard to work through them without a chat.

### Added

- **Task IDs:** every item in *Needs you now*, *Decide*, *I owe*, *Waiting
  on*, *Watching* and *Closed* starts with an ID like `T-42`. It stays the
  same while the task moves between sections and runs, and is never reused.
  Only the radar gives out IDs (`next_task` in its *Cursors*); the first 0.5
  radar numbers the items it carries over from an older radar.
- **Act on a task by its ID:** say "T-42 is done", "T-42 isn't mine" or "what's
  T-42?" in any chat. Handoffs gain an optional `task` line and a new `close`
  instruction (done or not mine), which the next radar applies by moving the
  task to *Closed*. Brief, prep and weekly review keep the IDs on the items
  they copy.
- **Task IDs are checked by a script:** where code can run, the radar runs
  `scripts/check_task_ids.py` on its draft against the previous radar before
  saving. It catches renumbered, duplicated, reused or dropped tasks, fixes
  them, and notes any failure it couldn't fix in the journal. Sample radars
  in `tests/fixtures/task-ids/` let other readers (the board) run the same
  checks.
- **Dashboard:** a private page to work through your to-dos without a chat:
  *Today* (focus, what needs you, calendar with free blocks), *To-do*,
  *Delegated* and *Nice to know*, in English, Catalan or Spanish. It reads the
  registry live with your own Google connectors. Mark a task done or not
  yours (it writes a close handoff), save a reply as a Gmail draft, or block
  time on your calendar; nothing is ever sent. New `dashboard` skill, run by
  setup: `scripts/build_dashboard.py` fills the template in
  `templates/dashboard/` from your config, so every dashboard is built the
  same way. Microsoft 365 storage isn't supported yet (setup says so and
  carries on).
- Radar traces count `tasks_new` and `tasks_closed`, plus `id_errors` and
  `id_fixes` on the new `radar.check-ids` step; IDs are never sent.

### Changed

- **Microsoft 365 tested on a real tenant:** the "unverified" markers are
  gone. Tools are still discovered by function, since their names are not
  published.
- Anything that parses radar bullets must allow the leading `T-<n> — ` field.
- Safety: one exception to read-only, only on your click on the dashboard:
  Gmail drafts (never sent) and busy blocks on your own calendar.
- `config` gains `dashboard` and `dashboard.version`; handoffs can come
  `from: dashboard (on behalf of the user)`.
- Open tasks never just drop off: *Decide* items after 14 days and *Watching*
  notices past their date move to *Closed* as `expired`.

Design: `docs/specs/2026-11-17-task-ids.md`, `docs/specs/2026-11-17-dashboard.md`.

## chief-of-staff 0.4.1 - 2026-11-02

### Added

- **Your name on the radar:** every radar starts with an `## Owner` section
  holding `owner.name` from your config, so the dashboard and briefs can greet
  you by name.
- **Deadlines as dates:** items in *Needs you now*, *Decide*, *I owe* and
  *Waiting on* carry `due YYYY-MM-DD` when they have a deadline ("by Friday"
  becomes that Friday's date). No deadline, no `due`; the radar never invents
  one.

## chief-of-staff 0.4.0 - 2026-10-29

Honest recipes and structure-only sharing. Requires a nuvel connector speaking
`nuvel.recipe/3` and `nuvel.recipe_signal/2`.

### Changed

- **Recipes start as drafts:** a recipe is promoted to active when a later
  task matches it, or straight away if you say the task will recur; unused
  drafts expire after 60 days (weekly review).
- **Success means explicit approval:** silence, leaving or a scheduled run no
  longer counts as success. Stats gain `days_used` and `last_outcome`.
- **Quality bar before sharing:** active, at least one approval, used on at
  least three different days, last outcome not a correction.
- **Recipe index:** before a task only the newest index is read (one read);
  no index means no recipe lookup.
- **Weekly batch:** the weekly review expires drafts, merges duplicate
  recipes, rebuilds the index, sends one `nuvel.recipe_signal/2` snapshot per
  changed recipe and shares recipes (`references/recipe-sharing.md`).
- **Sharing is structure only by default** (steps, kinds of tool, kinds of
  thing, counters; none of your text) in the new `nuvel.recipe/3` format.
- **Setup question 6:** asks whether to also send the masked description in
  your own words. Default no; `sharing.recipe_text` is `on` only after a yes.
- Every `SKILL.md` stays within 500 lines; long procedures live in
  `references/`. Spanish, English and Catalan descriptions are masked on the
  server when text sharing is on; a name spelled like an everyday word
  (e.g. March, or Sala in Catalan) can pass through, so keep personal names
  out of free text.

### Removed

- `learn` no longer sends signals or shares recipes; it keeps lessons and
  private recipes only.
- Per-event recipe signals (`nuvel.recipe_signal/1`) and `nuvel.recipe/2`.
- Text sharing is no longer on by default.

## chief-of-staff 0.3.0 - 2026-10-27

Business-ready release: guided setup for non-technical owners, Microsoft 365 as
a first-class path, and a chief of staff that learns.

### Added

- **Business setup:** a guided conversation (about 15 minutes, at most six
  questions) with detected defaults, written for owners and executives.
- **Microsoft 365 first-class:** Outlook mail and calendar, Teams, OneDrive and
  SharePoint alongside Gmail, Google Calendar and Drive. **Unverified on a real
  Microsoft 365 tenant so far**; behaviour is marked as such in the references.
- **Host memory:** say a «Recuerda…» sentence in any chat and it is kept.
- **Project instructions:** setup produces instructions for the user's Claude
  project so every conversation starts with the right context.
- **Run traces:** each run records what it read and wrote in its journal and,
  when the nuvel connector is present, sends nuvel the same content-free counts.
- **`learn` skill:** lessons from corrections (read by every skill), recipes for
  complex or repeated tasks, anonymous recipe signals, and recipe sharing with
  nuvel as structure plus a masked description; names and figures are replaced
  on nuvel's server before anything is stored. Sharing is on by default (you are
  told at setup, not asked) and switchable per customer. Recipes are shared in
  the new `nuvel.recipe/2` format: a fixed list of step actions
  (`references/recipe-actions.md`), the kinds of thing each step works on, and a
  description in the user's own words written with placeholders such as
  `{person}` or `{amount}`. Spanish, English and Catalan descriptions are
  masked on the server; other languages are shared as structure only, with
  their free text dropped. Masking keeps every word in its everyday
  vocabulary, so a name spelled exactly like one of those words (e.g. March, or
  Sala in Catalan) can pass through: do not put personal names in free text. A recipe is no
  longer blocked by a check on the user's machine; the server masks it, and
  rejects it only for a format problem.

### Removed

- Composio is no longer part of the user flow; sources connect through the
  Microsoft 365 and Google connectors in Claude.

## chief-of-staff 0.2.0 - 2026-10-20

Refined from a first end-to-end run in the Claude app with Gmail, Google
Calendar and Google Drive connectors (`docs/test-runs/2026-10-20-cowork-e2e.md`).

### Changed

- **Append-only registry:** every run writes one new document; the newest
  `config` and the newest `radar` are the current state. Works with storage
  connectors that can't edit files (the Google Drive connector), never
  conflicts, and keeps full history. Replaces `CONTEXT.md`, `loops.md`,
  `handoff.md`, `log/`, `people/`, `projects/` and `.state/`.
- Google Drive storage uses Google Docs (the connector reads `.md` uploads back
  empty); no YAML frontmatter anywhere — `- key: value` bullets instead.
- Radar: new `## Decide` section for unsolicited inbound (cold proposals,
  offers, invitations) instead of *I owe*; dated notices (renewals, invoices,
  expiries) go to *Watching* with date and amount; `seen` stores opaque source
  IDs instead of hashes; explicit allow-list of read-only tools.
- Scheduling targets Claude and Cowork: Cowork scheduled tasks, cloud routines
  (pointing at this public repo), desktop tasks; first sweep via **Run now** to
  pre-approve read-only tools.
- Setup asks for the registry language separately from the chat language and
  proves a write + read round trip on the storage connector.

### Removed

- The Claude Code `SessionStart` hook (the plugin targets Claude and Cowork;
  `recall` covers reading the registry from any conversation).

## chief-of-staff 0.1.0 - 2026-10-20

### Added

- First release for Claude and Codex.
- Skills: `setup` (guided onboarding), `radar` (incremental sweep every 2 h),
  `brief`, `prep`, `weekly-review`, `recall` (answer from the registry and hand
  instructions to the routines).
- Vendor-agnostic Markdown registry in Google Drive, OneDrive, SharePoint
  (synced folder or connector) or a local folder, with a shared journal
  (`log/`) and a `handoff.md` channel between routines and the main agent.
- Claude `SessionStart` hook that tells each session where the registry is and
  how many items need the user (metadata only, never registry text).
