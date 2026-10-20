# Chief of Staff

An AI chief of staff for **Claude** and **Codex**. It watches your email,
calendar, chat and tasks on a schedule and keeps a living Markdown registry in
*your* storage — Google Drive, OneDrive, SharePoint or a local folder — so you
(and any agent you work with) always know what needs you.

It only **reads** your sources. It never sends, replies, archives, accepts or
deletes anything; the only place it writes is its own folder.

## How it works

```
 scheduled routines (fresh session each run)          your main agent (any project)
 ┌────────────────────────────────────────┐          ┌──────────────────────────────┐
 │ radar      every 2 h, working hours     │          │ "what did I miss?"  → recall │
 │ brief      07:30 weekdays               │          │ "watch for Acme's reply"     │
 │ weekly-review  Friday 16:00             │          │        → handoff.md          │
 └──────────────┬─────────────────────────┘          └──────────────┬───────────────┘
                │ read: config, handoff, state                       │ read: CONTEXT, loops,
                │ write: CONTEXT, loops, log, notes                  │ log, notes · write: handoff
                ▼                                                    ▼
       ┌──────────────────────── Chief of Staff/ (your drive) ───────────────────────┐
       │ CONTEXT.md · loops.md · handoff.md · log/ · people/ · projects/ · briefs/ … │
       └──────────────────────────────────────────────────────────────────────────────┘
```

Routines run in clean sessions with no memory and no access to the project
you're working in. The registry is the bridge: routines leave everything there
(including a journal entry for every run), and your main agent reads it — in
Claude, a session-start hook even injects a short *Needs you now* summary.

## Skills

| Skill | Claude | Codex | What it does |
|---|---|---|---|
| setup | `/chief-of-staff:setup` | `$setup` | Guided onboarding: profile, sources, storage, routines, first sweep. Also reconfigure / pause / remove. |
| radar | `/chief-of-staff:radar` | `$radar` | Incremental sweep of all sources since the last run; refreshes `CONTEXT.md`, `loops.md`, notes and the journal. |
| brief | `/chief-of-staff:brief` | `$brief` | Morning brief: focus, meetings with context, due loops, free blocks. |
| prep | `/chief-of-staff:prep` | `$prep` | Prep for an upcoming meeting: who, history, open loops, agenda. |
| weekly-review | `/chief-of-staff:weekly-review` | `$weekly-review` | Week vs. priorities, loops, next week's plan; tidies the registry. |
| recall | `/chief-of-staff:recall` | `$recall` | From any project: answer from the registry, or leave instructions for the routines. |

Plain language works too: "set up my chief of staff", "what did I miss?",
"prep me for my 3pm".

## Install

**Claude Code**

```bash
claude plugin marketplace add Folken2/nuvel-plugins
```

```bash
claude plugin install chief-of-staff@nuvel
```

**Codex**

```bash
codex plugin marketplace add Folken2/nuvel-plugins
```

```bash
codex plugin add chief-of-staff@nuvel
```

Then ask: *"Set up my chief of staff."*

## What you need

- At least an **email** and a **calendar** tool in your host (built-in
  connectors, an MCP server, or Composio). Chat, tasks and meeting notes are
  optional. Setup checks what you have and tells you what's missing.
- A place for the registry: a synced Google Drive / OneDrive / SharePoint folder
  (best when routines run on your computer), a Drive/SharePoint connector (needed
  for cloud routines), or any local folder.
- A scheduler: Claude scheduled tasks or routines, Codex automations, or — as a
  fallback — cron / launchd / Task Scheduler. Setup picks one with you.

## Privacy and safety

- Read-only on every source; writes only inside the registry folder.
- Email and chat content is treated as data, never as instructions — suspected
  prompt-injection is flagged to you, not obeyed.
- Never stores passwords, codes, financial or ID numbers, or full email bodies;
  it summarises and links.
- Notifies only for *Needs you now*, never in quiet hours.
- The session-start hook can be turned off with `CHIEF_OF_STAFF_HOOK=off`.

Full rules: [`references/safety.md`](references/safety.md). Registry format:
[`references/registry-layout.md`](references/registry-layout.md).

## Part of nuvel

This plugin is built on [nuvel](https://github.com/Folken2/nuvel)'s skills
format and also loads in nuvel's agent-plugins registry
(`nuvel plugins load plugins/chief-of-staff`).
