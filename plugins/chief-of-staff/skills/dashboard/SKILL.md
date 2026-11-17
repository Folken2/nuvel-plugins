---
name: dashboard
description: Create, update or find the user's chief-of-staff dashboard — a private page where they work through their to-dos (needs you, decisions, what they owe, delegated, today's calendar) without a chat. Setup runs it; use it too when the user says "create my dashboard", "update my dashboard", "where is my board?", "torna a crear el tauler", "actualiza mi panel", or after a plugin update or a change of language, timezone, working hours or sources.
---

# Dashboard

Build the dashboard page from the plugin's template and publish it. The page is
**always** made by the build script from the template, never written or edited
by hand, so every user gets the same page. Contract:
`../../references/dashboard.md`. Rules: `../../references/safety.md`.

## Tools you may use

Read the registry (find it, read the newest `config`); create one new `config`
document in `config/`. Run code (the build script). The Artifact tool: publish,
and read an existing dashboard before updating it. Nothing else.

## Lessons and recipes

Right after reading `config`, read the newest document in the registry's
`lessons/` folder and apply every lesson scoped to `dashboard` or `all`; they
override this skill's defaults but never `safety.md`. Then read the newest
`index` in `recipes/` (one read; no `index` → no recipe lookup) and, if one
line's *When to use* matches, open only that recipe's newest version and follow
its *Steps* and *Pitfalls*. No `lessons/` or `recipes/` folder yet → carry on
without them (`../../references/registry-layout.md`).

## Steps

1. **Load.** Find the registry and read the newest `config` (stop if `paused:
   true`). If it has `- dashboard: <link>` and the user only asked where it is,
   give the link and stop.
2. **Can it be built here?** You need to run code and the Artifact tool. If
   either is missing, say in one sentence that the dashboard is created from a
   Claude session that can make artifacts (e.g. "ask me again in Claude Code
   or claude.ai"), and stop. Never write the page yourself instead.
3. **Build.** Save the `config` text exactly as read to a temporary file, then
   run:

   `python3 ../../scripts/build_dashboard.py --config <config file> --out <page file> --manifest <capabilities file>`

   - `result: ok` → go on.
   - exit 3 (`unsupported`, Microsoft 365 storage) → tell the user in one
     sentence that the dashboard works with Google for now and their chief of
     staff keeps working as before; stop (outcome `skipped`).
   - exit 1 → each `error:` line is a missing or wrong `config` key: fix it
     with the setup skill's reconfigure path, then build again. Never edit the
     page or the script output to get past it.
4. **Publish.** Publish the page file with the Artifact tool, passing the
   capabilities file's content **unchanged** as `capabilities` and `icon:
   "checklist"`. If `config` has a `dashboard` link, read that artifact first
   and publish to the same link (update in place); otherwise publish a new
   one. Don't add, drop or rename a connector or tool: the script decides.
5. **Record.** Write a new `config` (copy the newest in full) with
   `- dashboard: <link>` and `- dashboard.version: <the script's version>`.
   Skip it when both are already the same.
6. **Tell the user** (in their language, at most 3 lines): the link; that the
   first time they open it, Claude asks to let the page use Google Drive (and
   Gmail and Google Calendar when they first reply or block time); that it
   never sends anything, drafts wait in Gmail. Offer once to pin it.

Run this skill again whenever the plugin is newer than the recorded dashboard version, or
the `config`'s language, timezone, working hours, folders or sources changed:
it republishes to the same link.

## Trace

Last, follow `../../references/telemetry.md`: if `record_run_trace` is available
and `telemetry` is on, send one content-free trace right before saving the new
`config`, and end that document with a `## Trace` section mirroring it. Report
only these steps: `dashboard.load-config`, `dashboard.build`,
`dashboard.publish` and `dashboard.record` (`skipped` when nothing changed).

- **Counts:** `connectors` (servers in the capabilities) on `dashboard.build`;
  `updated` (1 when an existing dashboard was republished, else 0) on
  `dashboard.publish`.
- **Outcome:** `skipped` for Microsoft 365 storage or no artifact support;
  `failure` if the build failed; `blocked` if the registry could not be found.
- Counts and identifiers only — never the link, a name or a folder id.
