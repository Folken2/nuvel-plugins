# chief-of-staff 0.5 — dashboard

Date: 2026-11-17. Status: decided in chat. The data is read live from the
registry; drafts and busy blocks are allowed on the user's click; Google ships
first and Microsoft 365 follows.

## Why

The chief of staff writes a good picture of what needs the user, but they
still have to go to a chat (or a Google Doc) to act on it. The dashboard
prototype (designed separately) shows the other way: one page with the
day's focus, what needs you, decisions, delegated work and a calendar, where
each item takes one click. Setup must create it **the same way for every
user**, so it can be supported, improved and trusted. That rules out Claude
writing the page by hand.

## Decisions

1. **Live, not a snapshot.** The page reads the newest radar and brief from
   the registry through the viewer's own connectors (artifact `mcp`
   capability). Setup publishes it once. Routines never republish it, and it
   is as fresh as the last radar. The alternative, rebuilding the page with the
   data inside after every radar, would need every routine to publish
   artifacts and would put task text into page versions.
2. **One template, one script.** `templates/dashboard/` (shell, CSS, strings,
   parser, app) is versioned with the plugin. `scripts/build_dashboard.py`
   fills one settings block from the newest `config` (owner name, language,
   timezone, working hours, registry folder ids, which email/calendar) and
   prints the exact capabilities to publish with. The output is
   deterministic. The `dashboard` skill runs it and publishes; it never edits
   the page. Rebuilding (plugin update, config change) republishes to the
   same link, recorded in `config` as `dashboard` and `dashboard.version`.
3. **Actions on click only.**
   - *Done* / *Not mine* write a `close` handoff (task IDs, `task-ids` spec)
     after a 6-second undo window.
   - *Reply*, *Follow up*, *Accept*, *Decline* and *Ask for more time* save a
     Gmail draft, in the thread when the radar link is a Gmail thread. It is
     never sent.
   - *Block time* adds a busy event to the user's own calendar, with nobody
     invited and no notifications.

   `safety.md` gets one narrow exception for these; skills and routines stay
   read-only.
4. **Google first.** The page must declare exact connector tool names. The
   Google ones are confirmed (`search_files`, `read_file_content`,
   `create_file`, `get_thread`, `create_draft`, `list_events`,
   `create_event`); Microsoft 365's are not yet. The script exits 3 for
   OneDrive/SharePoint storage, and setup says one sentence and carries on.

## What the prototype changed into

- The prototype controls (sample data, state/language/provider/device
  switches) are gone. Language comes from `owner.language` (en, ca, es; other
  languages show the English interface). The states are real: loading, first
  day, stale radar, Drive unreadable (one message per error code), calendar
  unavailable, drafts not allowed, opened outside Claude, Microsoft 365.
- Draft text is a starting template. The hint no longer says Claude wrote it
  from the thread; generating it with the `sample` capability is a possible
  next step.
- *In progress* and *Got it* stay in the viewer's browser: they are personal
  convenience, not registry state.
- Free blocks are computed from today's events and `owner.working_hours`, and
  labelled with the brief's *Free blocks* suggestions when they overlap.

## Parsing

`radar.js` parses the radar contract: task IDs, `due`, `<link>`, `[project]`
tags (also when escaped by Google Docs, `\[x\]`), and `since`/`closed` dates
whatever word precedes them (radars write them in the owner's language). It
merges a task listed in both *Needs you now* and *I owe*. Gmail `thread-f:`
links become thread ids for replying in the thread. The same parser runs in
tests under Node against `tests/fixtures/dashboard/radar.md` and every
task-ID fixture, so the board and `check_task_ids.py` agree on which IDs a
radar holds.

## Verification

- `tests/test_dashboard.py`: build output, determinism, refusals, connector
  choice from sources, only declared tools called (all literal), text never
  rendered as HTML, parser cases, handoff text matching the registry contract.
- Headless Chromium against a mocked connector layer: renders in all states
  with no script errors; a close writes the expected handoff after the undo
  window; Reply finds the thread, prefills sender and subject, and saves a
  draft in the thread; Block time creates a busy event; phone layout.
- Not yet: a real viewer opening the published page with real connectors.
