# AGENTS.md

Official nuvel plugins for Claude and Codex. Each `plugins/<name>/` ships one
skills tree with three manifests: `.claude-plugin/plugin.json`,
`.codex-plugin/plugin.json`, and an agent-plugins.org `plugin.json`.

- Keep name and version identical in all three manifests; list every plugin in
  both `.claude-plugin/marketplace.json` and `.agents/plugins/marketplace.json`.
- Skills cite shared files with paths relative to the skill folder
  (`../../references/x.md`); tests fail if a cited file is missing.
  `scripts/bundle.py` turns each skill into a self-contained folder for MCP
  servers (Skills extension) and fails on a citation that would leave it:
  cite shared files only from the plugin root, and never from a hidden
  folder (`.claude-plugin/` is not in a bundle; use `plugin.json`).
- Every skill needs `agents/openai.yaml` (Codex UI metadata).
- Run `uvx --with pytest pytest tests -q` and `claude plugin validate --strict .`
  (CI also validates each `plugins/<name>/`) before committing.
- Changes to the radar, references, scripts or evals: also run the radar evals
  (`plugins/chief-of-staff/evals/README.md`); CI runs them on such PRs.
- Release per plugin: bump all three manifests, add `## <plugin> <version> - YYYY-MM-DD`
  to `CHANGELOG.md`, merge, then push tag `<plugin>-v<version>`. `release.yml`
  checks the tag (`scripts/release.py check`) and publishes a GitHub release
  with that CHANGELOG section and a zip of the plugin.
- Commits: conventional prefixes (`feat:`, `fix:`, `docs:`), author Folken2.
