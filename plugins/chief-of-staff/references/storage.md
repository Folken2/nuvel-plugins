# Storage: where the registry lives

The chief of staff never assumes a vendor. It picks the first option that works,
in this order, and records the choice in the `config` document
(`storage.kind`, `storage.root`, `storage.folders`).

Whatever the backend, the registry is **append-only**: skills only ever create
new documents (see `registry-layout.md`). That is what makes every backend
below work, including connectors that cannot edit files.

## 1. Storage connector (default for Claude, Cowork and cloud routines)

Use the storage connector the user already has: Microsoft 365 (OneDrive /
SharePoint) first, or Google Drive. It works from chat, Cowork, scheduled tasks and cloud routines
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
   - **OneDrive / SharePoint (Microsoft 365 connector):** see the next
     section.
3. Never change sharing. If the chosen place is shared with other people, warn
   and suggest a private one.

### OneDrive / SharePoint (Microsoft 365 connector)

**Unverified (no tenant yet)**: exact tool names are not published and no
tenant has run this. Use tools by function ("OneDrive create file", "list
folder children", "read file content"). The Microsoft 365 connector can write
files since 2026-07-07, but only after a Global or Application Administrator
re-consents the write scopes; if file creation is refused, tell the user that
one sentence ("this is enabled by whoever manages Microsoft 365 / Claude at
your company") and stop.

1. Create the folder `Chief of Staff` at the **OneDrive root** (SharePoint only
   if the user asks for a team library), then `config`, `runs`, `handoff`
   inside it. Record every folder ID (or drive item ID).
2. Create the test document as `.md` plain text. Read it back and compare the
   text. If it reads back as text, every registry document is `.md`; otherwise
   fall back to `.docx`. Record the choice in the `config` document.
3. Round trip done: the setup test document is the only thing ever removed
   (`safety.md` §1). If delete is unavailable, leave it and name it in the
   journal.
4. The registry stays append-only even though OneDrive could edit in place:
   one code path on every backend, history for free, safe concurrent runs.
5. Never change sharing or permissions. A OneDrive folder is private by
   default; if the user picked a shared place, warn and suggest a private one.

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
Documents are `.md` files. `storage.kind: synced-folder`. This is a fallback: do not bring it up during the normal flow unless the connector round trip failed.

## 3. Local folder (fallback)

`~/Chief of Staff/` (or an Obsidian vault, a private git repo).
`storage.kind: local`. Also a fallback, not part of the normal flow. Say plainly that nothing syncs off this machine and cloud
routines can't reach it.

## Rules for every storage kind

- Only ever create documents inside `storage.root`. Never edit, move, trash or
  share anything — except the setup round-trip test document, which setup
  trashes right after the check.
- Before writing, check the root still exists. If it doesn't, stop and tell the
  user — never recreate the registry somewhere else.
