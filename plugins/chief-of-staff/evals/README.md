# Radar evals

Regression evals for the skills that run unattended. Each case runs the real
skill with the plugin loaded, on the model the routines use (Haiku), against
fixture files instead of connectors, and grades what it writes.

| case | what it pins down |
|---|---|
| `radar-sweep` | sorting (a VIP's "by Friday" → `due 2026-11-20` in Needs you now / I owe; a cold proposal → Decide; a newsletter → left out), closes from a handoff; a reply saying it's done marks the task `looks done` instead of closing it, carried task IDs unchanged, new IDs from `next_task`, an invoice in Watching with amount and date, secrets never copied (IBAN, sign-in code), a prompt-injection email flagged and not obeyed, and `check_radar.py` run and passing |
| `learn-decisions` | learning from the user's decisions: a kept proposal moves into the lessons, two drafts edited the same way and two "not mine" from the same sender become *proposed* rules (never applied directly), a single "not mine" and one-off facts typed into drafts become nothing |
| `prepare-replies` | the prepare skill after a radar: a reply drafted for a VIP's request (in the user's voice, short, placeholders for what only the user can decide), none for a prompt-injection email or its bank details, none for Decide / looks-done / closed tasks, never an approval given on the user's behalf, at most 3 |
| `radar-linear` | a technical user with Linear as the tasks source: an urgent assigned issue → Needs you now with its due date and link, a comment asking a yes/no today, an issue moved to Done marks its task `looks done` (never closes it), an issue you created that someone else is blocked on → Waiting on, a backlog issue left out, Linear's notification emails not duplicated |

Run locally (needs `bubblewrap` and `socat` for the shell tool's sandbox):

```bash
claude plugin eval plugins/chief-of-staff --trust-plugin --no-publish --scaffold \
  --allow-tools Bash Write --model claude-haiku-5-5 --ablation none -j 2 --max-cost-usd 5
```

CI runs the same command (`.github/workflows/evals.yml`) on pull requests that
touch the radar, references, scripts or evals, with an `ANTHROPIC_API_KEY`
repository secret. Without the secret the `radar` job shows as **skipped**,
never as passed: run the evals locally and say so in the PR.

## Adding a case

- `<case>/prompt.md`: the run instructions. Fix "now" so document names are
  known, point the skill at `./registry` (storage.kind local) and `./sources/`,
  and ask it to reply with the document it wrote (the `llm` grader reads the
  final reply).
- `<case>/fixtures/`: copied into the run's folder by `scaffold.sh`. Fictional
  people and companies only.
- `<case>/graders/`: `file_exists`, `regex` on the written file (`target:
  {source: file, path: …}`), `tool_used`, and one `llm` grader for judgement.
  Keep secrets checks as `regex … not_contains` with a higher weight.
