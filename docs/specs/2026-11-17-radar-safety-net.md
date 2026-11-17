# chief-of-staff 0.5.1 — radar safety net

Date: 2026-11-17. Status: decided in chat ("let's do 1").

## Why

The routines now run unattended on Haiku. The end-to-end test of 0.5 showed
how easily the radar's format breaks: Google Docs' escaping broke two parsers,
and nothing checked the rest of the document (sections, deadlines, secrets).
A skill edit that makes Haiku sort worse would only show up in someone's inbox.

## What

1. **`scripts/check_radar.py`.** One script the radar runs before saving,
   which checks the whole contract:
   - the header line;
   - required sections, in order, with *Trace* last;
   - at most 5 items in *Needs you now*;
   - `due` followed by a real date;
   - cursors as ISO timestamps, and `seen` without addresses;
   - secrets (IBAN, Luhn-valid card numbers, one-time codes, passwords, API keys) and more than one quoted email line;
   - every task-ID rule, by importing `check_task_ids.py`.

   Long lines, a radar over 150 lines and plain-http links are warnings.
   Fixtures: `tests/fixtures/radar/`, one per rule.
2. **Evals.** `plugins/chief-of-staff/evals/radar-sweep` runs the real radar
   skill with the plugin loaded, on Haiku, against fixture files instead of
   connectors (`claude plugin eval` can't reach claude.ai connectors). The
   fixtures are a local registry with the previous radar, a config and an
   open handoff, plus `sources/email.json` and `calendar.json`.
   - **Exact checks:** the file exists, the check script ran and passed, `due 2026-11-20` for "by Friday", no IBAN, no sign-in code, no newsletter, `next_task` advanced, nothing sent.
   - **Judged by a model (Haiku), all at once:** sorting, closes from the handoff and from evidence, carried IDs, the invoice in *Watching*, and the prompt-injection email flagged and not obeyed.

   CI runs the evals on pull requests that touch the radar's behaviour, with a
   pass threshold of 0.8 and a $5 cost ceiling.

## Notes from building it

- Shell commands inside an eval need the sandbox tools (`bubblewrap`,
  `socat`). On GitHub's Ubuntu 24.04 runners, the AppArmor setting that
  blocks unprivileged user namespaces must be lifted.
- Fixtures reach the run through `scaffold.sh`, which finds its own folder
  with `dirname "$0"`, so evals need `--scaffold`.
- The `llm` grader can't point at a file; the case asks the run to end by
  replying with the radar it wrote.
