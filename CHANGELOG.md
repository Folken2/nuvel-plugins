# Changelog

All notable changes to the plugins in this repo. Versions are per plugin.

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
  `{person}` or `{amount}`. Spanish and English descriptions are masked on the
  server; Catalan and other languages are shared as structure only, with their
  free text dropped. A recipe is no longer blocked by a check on the user's
  machine; the server masks it, and rejects it only for a format problem.

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
