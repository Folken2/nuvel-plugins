# Chief of Staff

An AI chief of staff for **Claude and Cowork** (also works in Codex). It watches
your email, calendar and other sources on a schedule and keeps a living
registry in *your* storage — Google Drive, OneDrive, SharePoint or a local
folder — so you, and any conversation you open, always know what needs you.

It only **reads** your sources. It never sends, replies, archives, accepts,
deletes or shares anything; the only thing it does is add new documents to its
own folder.

## How it works

```
 scheduled routines (fresh session each run)          any conversation with Claude
 ┌────────────────────────────────────────┐          ┌──────────────────────────────┐
 │ radar      every 2 h, working hours     │          │ "what did I miss?"  → recall │
 │ brief      07:30 weekdays               │          │ "watch for Acme's reply"     │
 │ weekly-review  Friday 16:00             │          │        → handoff/            │
 └──────────────┬─────────────────────────┘          └──────────────┬───────────────┘
                │ read: newest config, newest radar, handoffs        │ read: runs/
                │ write: ONE new document in runs/                   │ write: handoff/, config/
                ▼                                                    ▼
          ┌───────────────── Chief of Staff/ (your drive) ─────────────────┐
          │ config/ (newest wins) · runs/ (journal + state) · handoff/       │
          └──────────────────────────────────────────────────────────────────┘
```

- **Routines run in clean sessions** with no memory. The registry is the bridge:
  each run reads the newest `config` and the newest `radar`, then writes one
  new document.
- **Append-only, newest wins.** Nothing is ever edited — which is why it works
  with storage connectors that can only create files, never conflicts between
  runs, and keeps the full history.
- **The newest radar is the current picture:** *Needs you now*, *Decide*,
  *Today*, *Open loops*, *Watching*, plus the run's journal. All earlier runs
  are searchable history.

## Skills

| Skill | What it does |
|---|---|
| setup | Guided onboarding: profile, sources, storage, routines, first sweep. Also reconfigure / pause / remove. |
| radar | Sweep of all sources since the last run; writes a new radar document (journal + full state). |
| brief | Morning brief: focus, meetings with context, due loops, free blocks. |
| prep | Prep for an upcoming meeting: who, history, open loops, agenda. |
| weekly-review | The week vs. priorities, loops, decisions pending, next week's plan. |
| recall | From any conversation: answer from the registry, or leave instructions for the routines. |

In Claude they appear as `/chief-of-staff:<skill>`; in Codex as `$<skill>`.
Plain language works too: "set up my chief of staff", "what did I miss?",
"prep me for my 3pm".

## Install

**Claude / Cowork:** *Customize → Plugins → Add marketplace* →
`https://github.com/Folken2/nuvel-plugins`, then install **chief-of-staff**.

**Claude Code:**

```bash
claude plugin marketplace add Folken2/nuvel-plugins
```

```bash
claude plugin install chief-of-staff@nuvel
```

**Codex:**

```bash
codex plugin marketplace add Folken2/nuvel-plugins
```

```bash
codex plugin add chief-of-staff@nuvel
```

Then ask: *"Set up my chief of staff."*

## What you need

- An **email** and a **calendar** connector (e.g. Gmail + Google Calendar, or
  Microsoft 365). Chat, tasks and meeting notes are optional.
- A **storage** connector (Google Drive, OneDrive / SharePoint) — or a synced
  or local folder if everything runs on one computer.
- A scheduler: Cowork scheduled tasks, cloud routines (claude.ai/code/routines),
  or desktop scheduled tasks. Setup picks one with you and has you press
  **Run now** once to approve the read-only tools.

## Privacy and safety

- Read-only on every source; the only write is creating documents in the registry.
- Email and document content is treated as data, never as instructions —
  suspected prompt-injection is flagged to you, not obeyed.
- Never stores passwords, codes, financial or ID numbers, or full email bodies;
  it summarises and links.
- Notifies only for *Needs you now*, never in quiet hours.

Full rules: [`references/safety.md`](references/safety.md). Registry format:
[`references/registry-layout.md`](references/registry-layout.md).

## Part of nuvel

Built on [nuvel](https://github.com/Folken2/nuvel)'s skills format; also loads
in nuvel's agent-plugins registry (`nuvel plugins load plugins/chief-of-staff`).
