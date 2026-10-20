# nuvel plugins

Official [nuvel](https://github.com/Folken2/nuvel) plugins for **Claude and
Cowork** (also **Codex**). This repo is a plugin marketplace for both Claude and
Codex: one skills tree per plugin, with a manifest for each host.

| Plugin | What it does |
|---|---|
| [chief-of-staff](plugins/chief-of-staff/) | An AI chief of staff for Claude and Cowork: sweeps email and calendar every two hours and keeps an append-only registry in Google Drive, OneDrive, SharePoint or a local folder. Morning briefs, meeting prep, weekly reviews. |

## Install

Claude Code:

```bash
claude plugin marketplace add Folken2/nuvel-plugins
```

Codex:

```bash
codex plugin marketplace add Folken2/nuvel-plugins
```

Then install a plugin by name, e.g. `claude plugin install chief-of-staff@nuvel`
or `codex plugin add chief-of-staff@nuvel`.

## Layout

```
.claude-plugin/marketplace.json     # Claude marketplace
.agents/plugins/marketplace.json    # Codex marketplace
plugins/<name>/
├── .claude-plugin/plugin.json      # Claude manifest
├── .codex-plugin/plugin.json       # Codex manifest (+ interface for the Codex UI)
├── plugin.json                     # agent-plugins.org manifest (loads in `nuvel plugins`)
├── skills/<skill>/SKILL.md         # shared by every host
├── skills/<skill>/agents/openai.yaml   # Codex per-skill UI metadata
├── references/  templates/
└── README.md
```

## Develop

```bash
uvx --with pytest pytest tests -q
```

```bash
claude plugin validate .
```

The tests keep the three manifests in agreement (name, version), check both
marketplaces list every plugin, and fail if a skill cites a file that doesn't
exist. Bump the version in all three manifests together and add a
`CHANGELOG.md` entry.

Try a local checkout without publishing: `claude plugin marketplace add ./` or
`codex plugin marketplace add "$PWD"`.

## License

MIT
