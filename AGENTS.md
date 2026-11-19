# AGENTS.md

Official nuvel plugins for Claude and Codex. Each `plugins/<name>/` ships one
skills tree with three manifests: `.claude-plugin/plugin.json`,
`.codex-plugin/plugin.json`, and an agent-plugins.org `plugin.json`.

- Keep name and version identical in all three manifests; list every plugin in
  both `.claude-plugin/marketplace.json` and `.agents/plugins/marketplace.json`.
- Skills cite shared files with paths relative to the skill folder
  (`../../references/x.md`); tests fail if a cited file is missing.
- Every skill needs `agents/openai.yaml` (Codex UI metadata).
- `agent-builder` skills other than `build-agent` are copies from Folken2/nuvel:
  edit them there, then `python scripts/sync_skills.py agent-builder --from ../nuvel`.
  CI fails if the copy differs from the commit pinned in its `source.json`.
- Run `uvx --with pytest pytest tests -q` and `claude plugin validate --strict .`
  (CI also validates each `plugins/<name>/`) before committing.
- Changes to the radar, references, scripts or evals: also run the radar evals
  (`plugins/chief-of-staff/evals/README.md`); CI runs them on such PRs.
- Release per plugin: bump all three manifests, add `## <plugin> <version> - YYYY-MM-DD`
  to `CHANGELOG.md`, merge, then push tag `<plugin>-v<version>`. `release.yml`
  checks the tag (`scripts/release.py check`) and publishes a GitHub release
  with that CHANGELOG section and a zip of the plugin.
- Commits: conventional prefixes (`feat:`, `fix:`, `docs:`), author Folken2.
