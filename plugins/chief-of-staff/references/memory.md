# Memory: host memory versus the registry

Two layers with a clear split. The host's own memory holds a few short, stable
facts that are loaded into every chat. The registry folder (see `storage.md`
and `registry-layout.md`) holds everything that changes.

## What goes where

| Host memory (Claude / ChatGPT) | Registry folder |
|---|---|
| Short, stable facts: who the user is, company, current priorities, key people and roles, preferred tone, notes language, and where the notes live | Radar snapshots, runs, handoffs, lessons, recipes, config history |

Rules:

- At most 10 facts in host memory.
- Never put anything in host memory that `safety.md` section 3 forbids in the
  registry: no passwords, codes, keys, bank or ID numbers, health information
  or full email bodies.
- Always include the "where my notes live" fact, worded exactly like this
  (adjust the storage name and folder to what `config` records):
  > My chief of staff keeps its notes in OneDrive, folder "Chief of Staff"; check it before answering about my day, clients or open topics.
- Only stable facts go to host memory (a changed priority, a new key person, a
  tone preference). Anything that changes weekly belongs in the registry.

## Writing to host memory

No host exposes a tool that a skill can call to write memory. The mechanism is
a "remember ..." sentence in the conversation. Verified 2026-10-27; see
`docs/research/2026-10-27-host-capabilities.md` in the plugin repository.

### Claude chat and Projects

Confirmed: telling Claude "remember this" (or what to remember, change or
forget) saves it, effective from the next conversation. Each project has its own
memory, and also sees the user's non-project memory. On Team and Enterprise the
owner must enable memory and each member must turn it on, so check it is on
before relying on it. The user can review and edit it in Settings > Your Claude.

Procedure: send the facts as one message, "Recuerda estos datos: ...", then ask
the user to open Settings > Your Claude to confirm they were saved.

### Cowork

Confirmed: memory is shared with chat only when Cowork runs in the cloud;
locally run Cowork sessions do not use memory. A Cowork project has its own
instructions and memory. So in a local Cowork session, put the facts in the
project instructions instead.

### ChatGPT

**Unconfirmed (snippet only; help pages not readable).** An explicit "Remember
that ..." request is stored as a saved memory, managed in Settings >
Personalization > Memory. Temporary Chats neither read nor write memory.

## Fallback

When memory is off, unavailable, or the session does not use it: tell the user
the one sentence to say, for example "Recuerda que mi jefe de gabinete guarda
sus notas en OneDrive, carpeta Chief of Staff", or put the facts in the project
instructions. Never fail setup over memory; the registry holds the truth and
host memory is only a convenience.
