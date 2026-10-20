# Chief of Staff

This folder is the working memory of your AI chief of staff (the `chief-of-staff`
plugin from nuvel, for Claude and Codex). It is updated automatically by the
routines you set up.

- **Start here:** `CONTEXT.md` — what needs you now, today's meetings, open loops.
- `loops.md` — what you owe people and what you're waiting on.
- `briefs/` — morning briefs. `reviews/` — weekly reviews. `prep/` — meeting prep.
- `log/` — the journal: one entry per routine run, so you (or your agent) can see what happened and why.
- `handoff.md` — notes for the next routine runs ("watch for X", "ignore Y"). Write here, or ask your agent to.
- `people/`, `projects/` — running notes on recurring people and projects.
- `config.md` — your profile, sources and schedule. Edit it freely; the next run picks it up.

The assistant only **reads** your email, calendar and chat. It never sends,
replies, archives or deletes anything; the only place it writes is this folder.
To pause it, ask your assistant to "pause the chief-of-staff routines", or delete
the scheduled routines listed in `config.md`.
