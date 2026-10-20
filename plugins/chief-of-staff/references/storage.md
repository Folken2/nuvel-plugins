# Storage: where the registry lives

The chief of staff never assumes a vendor. It picks the first option that works,
in this order, and records the choice in `config.md` (`storage.kind`, `storage.root`).

## 1. Synced folder (preferred when routines run on this computer)

Google Drive for desktop, OneDrive and SharePoint (through the OneDrive sync
client) all mount as ordinary folders. Writing there is a normal file write, works
offline, and the provider syncs it to the cloud. Look for:

| Provider | macOS | Windows | Linux |
|---|---|---|---|
| Google Drive | `~/Library/CloudStorage/GoogleDrive-<account>/My Drive/` (older installs: `/Volumes/GoogleDrive/My Drive/`) | `G:\My Drive\` (drive letter may differ) | — (rclone mount, if the user has one) |
| OneDrive (personal) | `~/Library/CloudStorage/OneDrive-Personal/` | `%USERPROFILE%\OneDrive\` | — |
| OneDrive (work) | `~/Library/CloudStorage/OneDrive-<OrgName>/` | `%USERPROFILE%\OneDrive - <OrgName>\` | — |
| SharePoint library | `~/Library/CloudStorage/<OrgName>/<Site> - <Library>/` (after "Sync" or "Add shortcut to My files") | `%USERPROFILE%\<OrgName>\<Site> - <Library>\` | — |

Detection: list the candidate parent folders (e.g. `ls ~/Library/CloudStorage`),
show the user what you found, and let them choose. Never pick one silently when
there are several. `storage.kind: synced-folder`, `storage.root: <absolute path>`.

**Limit:** a routine that runs in the cloud (a Claude cloud routine, a remote
agent) cannot see this folder. If the user wants cloud routines, use option 2.

## 2. Connector (needed for cloud-run routines)

Use the storage connector the host already has: a Google Drive connector, a
Microsoft 365 / SharePoint / OneDrive connector, or a Composio toolkit
(`googledrive`, `one_drive`, `share_point`). Create the root folder through it,
store its ID or URL in `storage.root`, and set `storage.kind` to `google-drive`,
`onedrive` or `sharepoint`.

Connector constraints to plan around:

- Files are written whole: read → change → write back. Keep files small (see
  `registry-layout.md`), so rewriting is cheap.
- Some Drive connectors convert `.md` uploads to Google Docs. Prefer uploading as
  plain text/markdown (`text/markdown` or `text/plain`) so the files stay
  portable; if the connector can only create Docs, accept it and note
  `storage.format: gdoc` in `config.md`.
- Name lookups are not unique on Drive. After creating a file, keep using its ID.
  Record IDs of the fixed files (`CONTEXT.md`, `loops.md`, `config.md`,
  `.state/radar.json`) under `storage.ids` in `config.md`.

## 3. Local folder (fallback)

`~/Chief of Staff/` (or anywhere the user wants: an Obsidian vault, a private git
repo). `storage.kind: local`. Tell the user plainly that nothing syncs off this
machine unless they move it into a synced folder later — moving the folder and
updating `storage.root` is the whole migration.

## Rules for every storage kind

- Only ever write inside `storage.root`. Never touch other files in the user's
  drive, never delete anything outside `.state/`.
- Before the first write of a run, check the root still exists. If it doesn't
  (renamed, unsynced, permissions changed), stop and tell the user — do not
  recreate the registry somewhere else.
- Sharing: the registry contains a summary of the user's inbox. Never change its
  sharing settings. If the folder is inside a shared drive or a SharePoint site
  other people can open, warn the user during setup and suggest a private
  location.
