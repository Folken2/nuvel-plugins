# Storage: where the registry lives

The chief of staff never assumes a vendor. It picks the first option that works,
in this order, and records the choice in the `config` document
(`storage.kind`, `storage.root`, `storage.folders`).

Whatever the backend, the registry is **append-only**: skills only ever create
new documents (see `registry-layout.md`). That is what makes every backend
below work, including connectors that cannot edit files.

## 1. Storage connector (default for Claude, Cowork and cloud routines)

Use the storage connector the user already has: Google Drive, Microsoft 365 /
OneDrive / SharePoint, or a Composio toolkit (`googledrive`, `one_drive`,
`share_point`). It works from chat, Cowork, scheduled tasks and cloud routines
alike, and doesn't depend on any one computer.

At setup:

1. Create the root folder `Chief of Staff` (in *My Drive* / the user's OneDrive
   root, unless they choose a place) and its subfolders `config`, `runs`,
   `handoff`. Record every folder ID.
2. **Prove the round trip** before relying on it: create a small test document,
   read it back, check the text survived, then move the test document to the
   trash. Pick the document type from the result:
   - **Google Drive connector:** create Google Docs by uploading Markdown with
     conversion on (`contentMimeType: text/markdown`, no
     `disableConversionToGoogleType`). Plain `.md` uploads come back empty from
     `read_file_content` and as base64 from `download_file_content`. Docs
     render Markdown headings, lists, links and tables, but mangle YAML
     frontmatter — so documents never use frontmatter.
   - **OneDrive / SharePoint connectors:** use `.md` if it reads back as text;
     otherwise `.docx`.
3. Never change sharing. If the chosen place is shared with other people, warn
   and suggest a private one.

Known connector limits to plan around:

- No in-place edits: never "update" a document; write a new one.
- Search ordering is not guaranteed: always pick "newest" by the name
  (`YYYY-MM-DD HHMM …`), restricted with a `createdTime` window.
- `parentId` filters match direct children only — that's why `runs/` is flat.

## 2. Synced folder (when everything runs on one computer)

Google Drive for desktop, OneDrive and SharePoint (via the OneDrive client)
mount as normal folders. Fine when the routines run on that computer (desktop
scheduled tasks, Claude Code, Codex app); invisible to cloud routines.

| Provider | macOS | Windows |
|---|---|---|
| Google Drive | `~/Library/CloudStorage/GoogleDrive-<account>/My Drive/` | `G:\My Drive\` (letter may differ) |
| OneDrive | `~/Library/CloudStorage/OneDrive-Personal/` or `OneDrive-<Org>/` | `%USERPROFILE%\OneDrive\` or `OneDrive - <Org>\` |
| SharePoint library | `~/Library/CloudStorage/<Org>/<Site> - <Library>/` | `%USERPROFILE%\<Org>\<Site> - <Library>\` |

Show the user what you found and let them choose; never pick silently.
Documents are `.md` files. `storage.kind: synced-folder`.

## 3. Local folder (fallback)

`~/Chief of Staff/` (or an Obsidian vault, a private git repo).
`storage.kind: local`. Say plainly that nothing syncs off this machine and cloud
routines can't reach it.

## Rules for every storage kind

- Only ever create documents inside `storage.root`. Never edit, move, trash or
  share anything — except the setup round-trip test document, which setup
  trashes right after the check.
- Before writing, check the root still exists. If it doesn't, stop and tell the
  user — never recreate the registry somewhere else.
