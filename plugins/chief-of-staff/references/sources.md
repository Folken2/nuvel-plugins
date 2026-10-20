# Sources: what the chief of staff watches

Sources are described by **kind**, not by product. At setup (and at the start of
every radar run) map each kind to whatever tool the host actually has. If a kind
has no tool, it is simply off — say so in the radar journal rather than guessing.

| Kind | What to pull | Typical tools (any one is enough) |
|---|---|---|
| `email` | New messages since the cursor in inbox + sent; flagged/starred; threads the user is waiting on | Gmail connector, Microsoft 365 / Outlook connector, Composio `gmail` / `outlook` |
| `calendar` | Today + next 2 working days; changes since the cursor (new, moved, cancelled, RSVP changes) | Google Calendar connector, Outlook calendar connector, Composio `googlecalendar` / `outlookcalendar` |
| `chat` | DMs and mentions since the cursor; threads the user posted in | Slack connector, Microsoft Teams connector, Composio `slack` / `microsoft_teams` |
| `tasks` | Items assigned to the user that changed or fall due | Linear, Jira, Asana, Notion, Todoist, GitHub issues/PRs |
| `meetings` | Notes/transcripts of meetings that ended since the cursor | Granola, Fireflies, Otter, Teams/Meet recordings, Notion meeting notes |
| `docs` | Files shared with the user or comments that mention them | Google Drive / OneDrive / SharePoint connector |

## Discovering tools

1. Look at the tools available in this session. Connector tools usually carry the
   product in their name (`gmail`, `outlook`, `calendar`, `slack`, `teams`,
   `drive`, `sharepoint`, `linear`, …).
2. If a kind the user wants has no tool, offer the host's way to add one, in this
   order: the host's own connector directory (Claude: Settings → Connectors /
   the connector registry; Codex: Plugins / Apps), then an MCP server the user
   already trusts, then Composio (`composio link <toolkit>`). Never install
   anything without the user saying yes.
3. Make one tiny read call per source (e.g. "1 most recent email") to prove it
   works before saving it in the `config` document. Record `via` as the tool or connector
   name you used.

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
