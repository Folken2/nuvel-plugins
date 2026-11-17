# Radar evals

Regression evals for the skills that run unattended. Each case runs the real
skill with the plugin loaded, on the model the routines use (Haiku), against
fixture files instead of connectors, and grades what it writes.

| case | what it pins down |
|---|---|
| `radar-sweep` | sorting (a VIP's "by Friday" → `due 2026-11-20` in Needs you now / I owe; a cold proposal → Decide; a newsletter → left out), closes from a handoff and from evidence (a reply saying it's done), carried task IDs unchanged, new IDs from `next_task`, an invoice in Watching with amount and date, secrets never copied (IBAN, sign-in code), a prompt-injection email flagged and not obeyed, and `check_radar.py` run and passing |

Run locally (needs `bubblewrap` and `socat` for the shell tool's sandbox):

```bash
claude plugin eval plugins/chief-of-staff --trust-plugin --no-publish --scaffold \
  --allow-tools Bash Write --model claude-haiku-5-5 --ablation none -j 2 --max-cost-usd 5
```

CI runs the same command (`.github/workflows/evals.yml`) on pull requests that
touch the radar, references, scripts or evals, with an `ANTHROPIC_API_KEY`
repository secret.

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
