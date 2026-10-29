# Sources: what the chief of staff watches

Sources are described by **kind**, not by product. At setup (and at the start of
every radar run) map each kind to whatever tool the host actually has. If a kind
has no tool, it is simply off — say so in the radar journal rather than guessing.

| Kind | What to pull | Typical tools (any one is enough) |
|---|---|---|
| `email` | New messages since the cursor in inbox + sent; flagged/starred; threads the user is waiting on | Microsoft 365 connector (Outlook mail), then Gmail connector |
| `calendar` | Today + next 2 working days; changes since the cursor (new, moved, cancelled, RSVP changes) | Microsoft 365 connector (Outlook calendar), then Google Calendar connector |
| `chat` | DMs and mentions since the cursor; threads the user posted in | Microsoft 365 connector (Teams chats and channels), then Slack connector |
| `tasks` | Items assigned to the user that changed or fall due | Linear, Jira, Asana, Notion, Todoist, GitHub issues/PRs |
| `meetings` | Notes/transcripts of meetings that ended since the cursor | Granola, Fireflies, Otter, Teams/Meet recordings, Notion meeting notes |
| `docs` | Files shared with the user or comments that mention them | Microsoft 365 connector (OneDrive / SharePoint files), then Google Drive connector |

## Discovering tools

1. Look at the tools available in this session. Connector tools usually carry the
   product in their name (`gmail`, `outlook`, `calendar`, `slack`, `teams`,
   `drive`, `sharepoint`, `linear`, …).
2. If a kind the user wants has no tool, offer the host's way to add one, in this
   order: the host's own connector directory (Claude: Settings → Connectors /
   the connector registry; Codex: Plugins / Apps), then an MCP server the user
   already trusts. Never install anything without the user saying yes.
3. Make one tiny read call per source (e.g. "1 most recent email") to prove it
   works before saving it in the `config` document. Record `via` as the tool or connector
   name you used.

## Microsoft 365 (first-class)

**Unverified (no tenant yet)**: the connector's exact tool names are not
published and nothing here has been run against a real tenant. Describe and
discover tools by function ("Outlook mail search", "calendar events in a date
range", "Teams chat messages", "OneDrive file search"); never hard-code a tool
name. The first real tenant run must confirm each point below.

- **Email (Outlook).** Triage like the Gmail rules, using Outlook's own signals:
  - *Focused* is the equivalent of Gmail's Primary; *Other* is skimmed like
    Promotions: count it, read only when a VIP or priority matches.
  - Categories (colour labels) replace Gmail labels. Read them as hints; never
    create or change one.
  - `isRead = false` is the unread signal; flagged messages are the starred
    signal. Never mark anything read.
  - Conversation IDs (`conversationId`) are opaque strings: store them as
    `seen` IDs and compare for equality only, never parse them.
  - Shared mailboxes are read only when the user names them in `config`.
- **Calendar.** Same window as always (today + 2 working days). Meeting
  responses are read, never sent.
- **Chat (Teams).** DMs, group chats and mentions since the cursor; channel
  posts only in channels the user named. Never post or react.
- **Docs.** OneDrive and SharePoint files shared with the user or that mention
  them. Read-only: no create, update, rename, move or delete outside the
  registry (`safety.md` §1).

For builders: the tool-selection logic is host-neutral, so any tool provider the host exposes can fill a kind; the user-facing flow never mentions one.

## How much to read

Radar runs every ~2 hours, so it must be cheap and quiet:

- Pull **metadata first** (sender, subject, time, labels, thread ID), open a
  body only when the item looks relevant: VIP, mentions a priority, asks the user
  something, has a date, or is a reply in a thread the user started.
- Skip newsletters, promotions and social notifications unless they match a
  priority. Count them, don't log them.
- **Dated notices are not noise**: renewals, expiries, invoices and bills,
  price changes, account or security notices. Log one line in *Watching* with
  the date and amount (from the snippet when possible) — never card, IBAN or
  account numbers.
- Cap each source per run (e.g. 100 emails, 50 chat messages). If the cap is hit,
  log it and keep the cursor at the last processed item so the next run continues.
- For calendars, always read the full window (today + 2 working days) — it is
  small, and events change without notice.

## What "relevant" means

Rank every candidate against the newest `config`:

1. From or about a VIP.
2. Touches one of the stated priorities.
3. Asks the user for a decision, an answer or an action, or contains a date.
4. Is a reply in a thread where the user is waiting on someone (*Waiting on*).
5. Unsolicited inbound needing a yes/no (cold proposals, offers,
   invitations) → *Decide*. Dated notices (renewals, invoices, expiries) →
   *Watching* with date and amount.
6. Everything else is noise for radar purposes: count it.

Only levels 1–5 are written to the registry.
