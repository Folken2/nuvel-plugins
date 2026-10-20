# Changelog

All notable changes to the plugins in this repo. Versions are per plugin.

## chief-of-staff 0.1.0 - 2026-10-20

### Added

- First release for Claude and Codex.
- Skills: `setup` (guided onboarding), `radar` (incremental sweep every 2 h),
  `brief`, `prep`, `weekly-review`, `recall` (answer from the registry and hand
  instructions to the routines).
- Vendor-agnostic Markdown registry in Google Drive, OneDrive, SharePoint
  (synced folder or connector) or a local folder, with a shared journal
  (`log/`) and a `handoff.md` channel between routines and the main agent.
- Claude `SessionStart` hook that injects a short *Needs you now* summary.
