# Agent Builder

Build production-ready AI agents from Claude Code or Codex. Say *"build me an
agent that triages my support inbox"* and it:

1. scaffolds a runnable project with [nuvel](https://github.com/Folken2/nuvel):
   a FastAPI server with auth and health checks, a 17-plugin chain (cost
   guard, tracing, caching, resilience, guardrails…), tests, a Dockerfile and
   Railway config. The project is plain Python that doesn't depend on nuvel at
   runtime.
2. writes the agent itself (its tools, system prompt and domain skills),
   following the bundled framework skills so the code uses each framework's
   real APIs.
3. checks it: the tests pass, the agent imports and `nuvel doctor` is clean.

## Install

```bash
claude plugin marketplace add Folken2/nuvel-plugins
claude plugin install agent-builder@nuvel
```

```bash
codex plugin marketplace add Folken2/nuvel-plugins
codex plugin add agent-builder@nuvel
```

Scaffolding uses the `nuvel` CLI from PyPI (`nuvel-cli`). The skill runs it
through `uvx --from nuvel-cli nuvel`, so nothing is installed globally, or
asks before running `pipx install nuvel-cli`. The knowledge skills work
without the CLI.

## Skills

| Skill | For |
|---|---|
| `build-agent` | The workflow: pick a framework, scaffold, fill in, verify |
| `adk-agent-patterns` | Choosing the shape: single LlmAgent, Workflow graph, multi-agent |
| `adk-workflow-graphs` | ADK 2.0 `Workflow`: nodes, routing, fan-out, human gates |
| `adk-task-delegation` | Sub-agents with `mode='task'` and typed contracts |
| `adk-tool-creation` | Function tools: `ToolContext`, signatures, errors |
| `adk-prompt-engineering` | System prompts, `InstructionProvider`, state placeholders |
| `adk-callbacks-hitl` | Callbacks, approval gates, state deltas |
| `adk-skill-creation`, `adk-skill-design-patterns` | Writing the agent's own SKILL.md files |
| `adk-streaming` | Voice and video agents on the Gemini Live API |
| `adk-composio-tool-router` | ~1000 integrations through Composio |
| `adk-long-horizon-guardrails`, `adk-long-horizon-sessions` | Unattended and long-running agents |
| `adk-cron-isolation` | Scheduled runs with scoped secrets |
| `adk-org-memory-retrieval`, `adk-memory-self-improvement` | Team memory; self-improving memory (experimental) |
| `claude-sdk-*` (6) | Claude Agent SDK: tools, hooks, permissions, MCP, system prompt, deployment |
| `hermes` | Hermes agents and the Telegram gateway |

## Where the skills come from

Every skill except `build-agent` is copied byte for byte from the nuvel repo
(`nuvel/backends/<framework>/skills/`). `source.json` records the nuvel commit
the copy was taken from, and CI fails if the copy differs from that commit.
To update:

```bash
python scripts/sync_skills.py agent-builder --from ../nuvel           # copy and pin nuvel's HEAD
python scripts/sync_skills.py agent-builder --from ../nuvel --check   # what CI runs
```

Change skill content in nuvel, not here. Only `agents/openai.yaml` (Codex UI
metadata) and `build-agent` belong to this plugin.
