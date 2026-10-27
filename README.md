# nuvel plugins

Official [nuvel](https://github.com/Folken2/nuvel) plugins for **Claude and
Cowork** (also **Codex**).

## Chief of Staff

An AI chief of staff for busy people. Every couple of hours it reads your email,
calendar and chat and keeps one short, current picture: what needs you now,
decisions waiting for you, today's meetings with context, and promises still
open. Each morning you get a brief; before a meeting you get a prep; on Friday
a weekly review. You can correct it in plain language and it remembers.

- **What you need:** your Microsoft 365 account (Outlook, Teams, OneDrive) or
  your Google account (Gmail, Calendar, Drive) connected in Claude. Setup takes
  about 15 minutes and is a short conversation, no technical knowledge needed.
- **What it never does:** it only reads. It never sends, replies, archives,
  accepts, deletes or shares anything. Its notes live in a folder in your own
  storage.
- **Privacy:** it shares anonymous usage signals and anonymised "recipes" (how
  a kind of task was done, with names, companies, amounts and addresses
  removed) with nuvel to improve the product. This can be switched off per
  customer.

Open [plugins/chief-of-staff](plugins/chief-of-staff/) for the full guide. Once
installed, just say: *"Set up my chief of staff."*

## For installers and builders

This repo is a plugin marketplace for both Claude and Codex: one skills tree per
plugin, with a manifest for each host.

| Plugin | What it does |
|---|---|
| [chief-of-staff](plugins/chief-of-staff/) | Radar, morning brief, meeting prep, weekly review, recall, setup and learn. Microsoft 365 and Google. |

### Install

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

### Layout

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

### Develop

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
