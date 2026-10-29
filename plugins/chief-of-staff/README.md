# Chief of Staff

An AI chief of staff for busy people, in **Claude and Cowork** (also Codex).
Every couple of hours it reads your email, calendar and chat and keeps one
short, current picture in *your own* storage: what needs you now, decisions
waiting for you, today's meetings with context, and promises still open.

## What it does for you

- **Radar** every two hours in working hours: what changed, what needs you.
- **Morning brief** at 07:30: your focus, the day's meetings, loops due.
- **Meeting prep** on request: who is attending, history, what to get out of it.
- **Weekly review** on Friday: the week against your priorities and next week's plan.
- **Learns from you:** correct it once ("a Marta, de usted") and it applies the
  rule from then on. Tasks you repeat become reusable recipes.
- **Remembers on request:** tell it *"Recuerda que los viernes no tengo
  reuniones"* in any chat and it is kept.

## What you need

- Your **Microsoft 365** account (Outlook, Teams, OneDrive) or your **Google**
  account (Gmail, Calendar, Drive) connected in Claude. Microsoft 365 is the
  first-class path in 0.3.0 (not yet verified on a real tenant, see the
  changelog).
- About **15 minutes** for setup: a guided conversation of at most six
  questions. Optionally you then press **Run now** once on the scheduled
  review, so later runs do not wait for your approval.

## What it never does

It only **reads** your sources. It never sends, replies, archives, accepts,
deletes or shares anything; the only thing it does is add new documents to its
own folder. It never stores passwords, codes, financial or ID numbers, or full
email bodies, and it treats email text as data, never as instructions.

## Privacy and what is shared with nuvel

- Your notes stay in your own storage.
- nuvel receives **anonymous usage signals** (content-free counts of how each
  run went, and a weekly snapshot of how each recipe is doing; never any
  content) and, for recipes that have proved themselves, **recipes shared as
  structure only by default**: the steps, the kinds of tool, the kinds of thing
  each step works on and counters, never any of your text.
- The **masked description** of a recipe (in your own words, with names and
  figures replaced on nuvel's server) is sent **only if you said yes** to the
  question in setup. Descriptions in Spanish, English and Catalan are masked;
  in any other language the description is not sent. Masking keeps every word
  in its everyday vocabulary, so a name spelled exactly like one of those words
  (e.g. March, or Sala in Catalan) can pass through, so don't put personal
  names in free text.
- Structure sharing is **on by default**: you are told at setup, not asked.
  Text sharing is **off by default**. nuvel can switch either off per customer.
  With usage signals off, nothing is sent.

## Install

**Claude / Cowork:** *Customize → Plugins → Add marketplace* →
`https://github.com/Folken2/nuvel-plugins`, then install **chief-of-staff**.
Then say: *"Set up my chief of staff."*

---

## For installers and builders

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
          │ lessons/ (your corrections) · recipes/ (how repeated tasks go)   │
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
| learn | Lessons from your corrections and private recipes for repeated tasks; anonymous signals and recipe sharing (structure only by default) run in the weekly review. |

In Claude they appear as `/chief-of-staff:<skill>`; in Codex as `$<skill>`.
Plain language works too: "set up my chief of staff", "what did I miss?",
"prep me for my 3pm".

## Requirements

- An **email** and a **calendar** connector (Microsoft 365 or Google). Chat
  (Teams, Slack), tasks and meeting notes are optional.
- A **storage** connector (OneDrive / SharePoint, Google Drive) or a synced or
  local folder if everything runs on one computer.
- A scheduler: Cowork scheduled tasks, cloud routines (claude.ai/code/routines),
  or desktop scheduled tasks. Setup picks one with you.
- Optional: the nuvel connector, for usage signals and recipe sharing (requires a connector speaking `nuvel.recipe/3` and `nuvel.recipe_signal/2`).

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
