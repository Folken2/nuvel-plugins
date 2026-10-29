# Host capabilities: skills, memory, Microsoft 365 tools

Researched 2026-10-27. Official sources only. Each claim is marked
*confirmed* (read on the official page this session) or *unconfirmed*.

> **Implication for Task 3.** Finding (a) is only partly confirmed: plugin
> skills load in chat and Cowork (confirmed), but Projects are not mentioned.
> Because chat and Projects loading is not guaranteed in every plan or
> configuration, the project-instructions template must embed compact `recall`
> (and later `learn`) procedures, so the project works even if the skills do
> not load.

## (a) Do installed plugin skills load?

| Surface | Finding | Status | Source |
|---|---|---|---|
| Claude chat (web, Desktop Chat tab) | Plugins can be added in chat; "The skills and commands bundled in a plugin work in all of these places" (chat, Cowork, Claude Code) | confirmed | https://support.claude.com/en/articles/13837440-use-plugins-in-claude-cowork (2026-10-27) |
| Claude Projects (chat) | Not mentioned on either the plugins or the skills article | unconfirmed | same + https://support.claude.com/en/articles/12512180-use-skills-in-claude |
| Cowork | Plugins install from Customize > Plugins; skills appear via "/" or "+" | confirmed | plugins article above |
| Cowork scheduled tasks | Not mentioned | unconfirmed | plugins article above |
| Skills (not plugins) in chat/Cowork | Managed in Customize > Skills; sharing works in chat and Cowork; needs code execution enabled; Team/Enterprise owners must enable skills | confirmed | skills article above |
| Hooks, sub-agents, local MCP servers in plugins | Run in Cowork and Claude Code, not in chat | confirmed | plugins article |
| Conflict | A search snippet said the developer docs list plugins for Cowork and Code only, not chat; the help center says chat works | unconfirmed (conflicting sources) | claude.com/docs/cowork/guide/plugins.md (snippet) |

## (b) Writing to host memory from a conversation

| Surface | Mechanism | Status | Source |
|---|---|---|---|
| Claude chat | Say "remember this" or tell Claude what to remember, change or forget; applies from the next conversation. No tool is exposed to a skill; it is a user phrase. Claude also saves on its own. | confirmed | https://support.claude.com/en/articles/11817273-use-claude-s-chat-search-and-memory-to-build-on-previous-context (2026-10-27) |
| Claude chat, editing | Settings > Your Claude > Manage next to "Your memory" (user does it) | confirmed | same |
| Claude chat, availability | On by default Free/Pro/Max; on Team/Enterprise the owner enables it and each member must turn it on | confirmed | same |
| Claude Projects | Each project has its own memory; it also sees non-project memory; "Use account memory" can be turned off per project | confirmed | same |
| Cowork | Memory is shared with Chat when Cowork runs in the cloud; "Cowork sessions that run locally on your computer don't use memory" | confirmed | same |
| Cowork project | Has its own instructions, files, context and memory (desktop-only, local) | confirmed (snippet of official support article 14116274) | https://support.claude.com/en/articles/14116274 |
| ChatGPT | Explicit requests ("Remember that ...") become saved memories; managed in Settings > Personalization > Memory; Temporary Chats neither use nor create memory | unconfirmed (snippet; help.openai.com returned 403 to fetch) | https://help.openai.com/en/articles/8590148 , https://help.openai.com/en/articles/8983136-what-is-memory |

No surface exposes a programmatic "write memory" tool to skills. The only
mechanism is the user (or the assistant on the user's request) saying a
"remember ..." sentence in the conversation. Whether Claude honours such a
sentence when it appears in an assistant-authored instruction versus the
user's own message is untested.

## (c) Microsoft 365 connector

Source: https://claude.com/docs/connectors/microsoft/365 (2026-10-27) and
https://support.claude.com/en/articles/12542951 (prior research).

**Exact tool names are not published** on these pages (unconfirmed). Tools are
described by function; Claude "detects which tools it needs". Only Teams tools
are referenced by group ("each Teams messaging tool", per-tool restriction).

| Function | Read/Write | Status |
|---|---|---|
| Search/read mail threads and archived mail | read | confirmed (function), name unconfirmed |
| List/review calendar, meeting info, summaries, attendance (Teams Calendar) | read | confirmed (function), name unconfirmed |
| Read Teams channel and chat discussions | read | confirmed (function), name unconfirmed |
| Search/analyze SharePoint and OneDrive documents | read | confirmed (function), name unconfirmed |
| Create/update files in SharePoint (and OneDrive per prior research; rename/move/delete since 2026-07-07) | write | confirmed (SharePoint create/update); OneDrive and rename/move/delete from release notes, prior research |
| Send mail, manage drafts, labels, filters, auto-replies; create/update/delete calendar events, find meeting times | write | confirmed (function) |
| Send Teams chat and channel messages | write | confirmed (function) |

Write actions need: a Global/Application Admin approving the added scopes once
for the tenant (reconnecting does not add them), and write actions turned on in
the org connector configuration (or via role-based access, beta). Connector
cannot attach files to drafts it creates. Requires a work/school Entra tenant.

Consequence for the plugin: skills stay read-only on sources regardless of what
the connector can do; only the storage folder (`Chief of Staff`) is written, and
that needs the file-write scope. Everything Microsoft-specific stays marked
**Unverified (no tenant yet)** in references.
