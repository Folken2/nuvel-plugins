# chief-of-staff 0.5.2 — setup owns the routines' settings

Date: 2026-11-17. Status: decided in chat ("Connectors is a matter of
discovering and asking the user. Right model: if Haiku does the job, good. If
the user prefers another one, do it. Sonnet is a good model too").

## Why

In the 0.5 test, the routines' model, connectors and instructions were all
fixed by hand after setup. They had been created on a big model, with
Supabase, Tavily, Claude Docs and Claude Code Remote attached, and without the
step that fetches the plugin's scripts. Unattended runs with automatic
approval can use every tool attached to them, so extra connectors are attack
surface for a malicious email.

## Decisions

- **Model:** Haiku by default. It's enough for the routines' work, and the
  radar evals pin it down on Haiku. Setup names the default in the routine
  proposal and takes the user's choice (Sonnet, Opus) by exact ID. It never
  upgrades on its own. Recorded as `routines.model`.
- **Connectors:**
  - **Discover:** the session's connectors, by function, matched to the
    config's sources and storage, plus nuvel.
  - **Propose:** plain product names, in the same message as the schedule and
    the model, so it is a confirmation, not a seventh question.
  - **Confirm:** one yes; a change is applied and confirmed in one line.
  - **Never attached:** search, browsing, code, database, other-project and
    remote-session connectors.

  Recorded as `routines.connectors`.
- **Create, then verify:** pass model and connectors to the creating tool
  where it accepts them. Otherwise set the model right after creating, and
  tell the user which connectors to remove and where. Then read every
  routine back and compare it with `config`; a mismatch is reported, never
  recorded as done.
- **Reconfigure checks existing routines** against `config` and offers fixes.
  Changes in place come first. Recreating a routine loses its run history, so
  it is only offered second, and the new IDs are written to `config`.
- **Template:** the routine prompt includes the scripts step (clone the
  repository, whole scripts folder) and the telemetry line.

## Out of scope

Changing connectors of an existing cloud routine: the scheduling tool
available to skills can set name, schedule, model, prompt and on/off, but
not connectors. Setup tells the user where to change them.

## Addendum: Linear for technical users (same release)

Decided in chat ("add Linear for issue tracking when user is technical").

- **Gate:** Linear is mentioned only for technical users. The signals are a
  connected Linear connector, a technical role in question 1, or Linear or
  GitHub notification emails in the last 7 days. It is never a question;
  without a connector it is one line pointing to Settings → Connectors.
- **What radar reads:** issues assigned to the user that changed since the
  tasks cursor, comments on them or mentioning the user, and issues the user
  created that someone else owns and that became blocked or overdue. Never
  the whole backlog.
- **Mapping:**
  - Urgent, High, or due today or tomorrow → *Needs you now*;
  - due within 7 days or started in the current cycle → *I owe* (at most 10;
    the rest become one count line in *Moving*);
  - a comment asking the user something → *I owe*;
  - the user's issues others are blocked on → *Waiting on*;
  - Done or Canceled → closes the matching task (the evidence);
  - cycle and project progress → *Moving*.
- **Identity:** the issue identifier starts the title and the issue URL is
  the link, so the radar's task matching keeps one task per issue. With
  Linear as a source, its notification emails are noise.
- **Safety:** no Linear write tool, ever. Routines get the Linear connector
  through `routines.connectors` like any other source.
- **Not yet tested on a real workspace:** the tool names come from the claude.ai directory listing,
  not from a real workspace run.
