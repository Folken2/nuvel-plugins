# chief-of-staff v0.3 — business-friendly setup, Microsoft 365, traces, self-learning

- Date: 2026-10-27
- Status: draft, builder-checked (awaiting approval)
- Repos: `Folken2/nuvel-plugins` (plugin, phases 1–3) and `Folken2/nuvel`
  (`packages/nuvel-mcp`, phase 3 only)
- Builds on: `docs/test-runs/2026-10-20-cowork-e2e.md` (this repo) and
  `docs/superpowers/specs/2026-10-20-monorepo-mcp-run-traces-design.md` (nuvel)

## Intent

Turn Claude (and, best effort, ChatGPT) into a proactive, Hermes-style chief of
staff for **non-technical business users**: the typical user is the CEO of an
SME on **Outlook + Teams + OneDrive**; Google Workspace is the equal
alternative. Two things are wrong with the default assistant that this fixes:

1. **Memory is poor.** The host's own memory saves little on its own and
   scheduled runs share nothing with the user's chats. The chief of staff keeps
   a folder of its own in the user's storage and also feeds the host's memory
   deliberately.
2. **It never gets better by itself.** When the user corrects it, the lesson is
   lost; when it works through a complex task, the next time starts from zero.
   v0.3 makes it remember corrections and write its own reusable "recipes",
   and tells nuvel (without customer content) which recipes are worth turning
   into skills for everyone.

nuvel (the user of this design) sets up and supports each customer: Microsoft
Entra admin consent, Claude org settings and the nuvel connector are handled by
nuvel, not by the CEO.

## Goals

1. **Setup in 10–15 minutes, business language only.** About 5–6 questions,
   no technical vocabulary (no "MCP", "connector scopes", "cron"), and the CEO
   sees a first useful radar about their real day before setup ends.
2. **Microsoft 365 as a first-class ecosystem**: Outlook mail and calendar,
   Teams, OneDrive/SharePoint storage — at parity with Google.
3. **The host's own connectors are what the agent proposes**: Claude's official
   Microsoft 365 / Gmail / Google Calendar / Google Drive connectors (or
   ChatGPT's apps). Composio and other MCPs are no longer offered to these users.
4. **Use the host's memory** for short, stable facts and the registry folder
   for everything that changes.
5. **Every skill run emits one `nuvel.skill_run/1` trace** to the shared nuvel
   MCP when it is connected, with a published step catalog per skill.
6. **New `learn` skill**: corrections → lessons; complex or repeated tasks →
   recipes (lightweight skills in the registry). Acts on its own and tells the
   user afterwards.
7. **Recipe signals and anonymised recipes reach nuvel automatically** so nuvel
   can promote good recipes into real skills for other customers.

## Non-goals

- Deploying the remote nuvel MCP (nuvel does it; the plugin only needs the
  connector to exist in the session).
- Automatic installation of recipes as official host skills (Claude cannot
  install skills from a chat; promotion is a manual nuvel step).
- Guaranteed ChatGPT parity. The Codex manifest stays and skills stay
  host-neutral, but v0.3 is tested on Claude and Cowork only.
- Claude Code–specific features (hooks, local pointer files as the main path).
- Acting on sources. Still read-only: never send, reply, accept, move or delete.

## Anti-goals (it fails even if it "works")

- Customer content in anything that leaves the customer's tenant, other than
  the anonymised recipe (see the residual risk under Phase 3).
- A setup that feels like an IT form: long question lists, technical terms,
  the user asked to paste IDs or URLs.
- Silent learning that the user can't see or undo.
- A trace or recipe send that blocks or breaks the run when the nuvel MCP is
  missing or down.

## Facts this design relies on (checked 2026-10-27)

Sources: support.claude.com articles 12542951 (Microsoft 365 connector) and
12138966 (release notes), claude.com/docs/connectors/microsoft/365,
help.openai.com 12143177 and 12512241. OpenAI pages were read from search
snippets only.

| | Claude Microsoft 365 connector | ChatGPT Microsoft apps |
|---|---|---|
| Read | Mail (incl. shared mailboxes), calendar, Teams chats/channels/transcripts, OneDrive/SharePoint files (Word, Excel, PowerPoint, PDF, `.md`, `.txt`, `.csv`) | Outlook mail/calendar, Teams, SharePoint/OneDrive, real time |
| Write | Since 2026-07-07: create/update/rename/move/delete files and folders, once a Global/Application Admin re-consents write scopes | Create folders, upload/update files when the workspace admin enables actions |
| Surfaces | Chat, Projects, Cowork; Cowork scheduled tasks use the same connectors | Chat; scheduled tasks in "Work" use plugins/skills (Microsoft apps there unconfirmed) |
| Requirements | Work/school Entra tenant (no outlook.com); tenant admin consent on every plan; Team/Enterprise owner enables the connector | Admin enables actions |

Google Drive connector (from our own test, F5): creates Google Docs, cannot
update content, reads `.md` uploads back empty.

**Consequence:** the registry stays **append-only on every backend** (one code
path, history for free, safe concurrent runs) even though OneDrive could edit
in place. On OneDrive/SharePoint documents are `.md` (verified by the round-trip
test; `.docx` fallback stays).

---

## Phase 1 — setup for business users, Microsoft 365, host memory

### 1.1 Setup flow (rewrite of `skills/setup/SKILL.md`)

Target: ≤ 15 minutes, ≤ 6 questions the user must answer; everything else is
detected, defaulted out loud, or confirmed with a yes.

1. **Detect, don't ask.** Look at the connectors in the session and pick the
   ecosystem: Microsoft (Outlook/Teams/OneDrive) or Google
   (Gmail/Calendar/Drive). Mixed → use what works per kind. Prove each with one
   tiny read. Show one plain table: "Correo ✅ · Calendario ✅ · Teams ✅ ·
   Carpeta ✅".
2. **Missing connector** → name the official one in the host's words ("activa
   el conector *Microsoft 365* en Ajustes → Conectores") and, when it needs an
   administrator, say so in one sentence: "Esto lo activa la persona que
   gestiona Microsoft 365 / Claude en tu empresa." No scopes, no Entra
   vocabulary. Never offer Composio or third-party MCPs in this flow.
3. **Questions (one per message, in the user's language):**
   1. Who you are and what the company does (one line each).
   2. Your 3 priorities right now.
   3. The key people: clients, partners, team (names are enough; emails are
      looked up from mail/calendar and confirmed).
   4. Language for the notes (default: the chat language).
   5. When not to disturb you (default from working hours seen in the
      calendar).
   - Timezone, working hours and frequent contacts are inferred from calendar
     and mail and confirmed in a single "¿Correcto?" message.
4. **Create the folder** "Chief of Staff" in OneDrive (or Drive) without asking
   where, unless the user objects; private; round-trip test; README and first
   `config`.
5. **Seed the host memory** (§1.3) and generate the **project instructions**
   (§1.4).
6. **Schedule** radar / brief / weekly-review with defaults stated in one
   message ("cada 2 horas de 8 a 20, resumen a las 7:30, repaso el viernes a
   las 16"); one yes creates all three.
7. **First radar now**, live in the conversation (7-day window), walk the user
   through *Necesita tu atención* and *Decidir*, take corrections — they go
   through `learn` (Phase 3) once it exists, into `config` until then.
8. **Wrap-up** in ≤ 6 lines, business language, including one line on sharing
   (Phase 3): "Las recetas útiles se comparten de forma anónima con nuvel para
   mejorar el servicio."

Technical details the user never sees (folder IDs, tool names, cron) go only in
the `config` and `setup` documents.

**Connector can read but not write** (e.g. Microsoft 365 write scopes not yet
re-consented): setup does everything it can without the folder, then stops at
step 4 with one sentence ("Falta un permiso para guardar notas en OneDrive; lo
activa quien gestiona Microsoft 365 en tu empresa. Cuando esté, dime
'continúa'."), writes nothing elsewhere and resumes from step 4 later. No
silent fallback to another storage.

### 1.2 Microsoft 365 parity

- `references/sources.md`: Microsoft 365 connector listed first for email,
  calendar, chat (Teams) and docs; Gmail/Google Calendar/Drive second; Composio
  removed from user-facing guidance (kept as a one-line note for builders).
  Outlook triage equivalents of the Gmail rules (focused/other, categories,
  `isRead`, conversation IDs as opaque `seen` IDs).
- `references/storage.md`: OneDrive/SharePoint section with concrete steps:
  create folder at OneDrive root, `.md` documents, round trip; SharePoint only
  if the user asks. Synced/local folders stay as fallbacks but are no longer
  mentioned during the normal flow.
- `registry-layout.md`: "Finding the registry" and "Finding the newest" gain
  Microsoft equivalents (list children of a folder, sort by name, never by
  returned order).
- Read-only rule: list the Microsoft write tools that must never be called on
  sources (send mail, reply, create/update events, post to Teams, and any
  delete/move outside the registry). Writing in the registry = create only.

### 1.3 Host memory

Two layers, with a clear split:

| Host memory (Claude / ChatGPT) | Registry folder |
|---|---|
| Short, stable facts loaded into every chat: who the user is, company, current priorities, key people and roles, preferred tone, notes language, **"my chief of staff keeps its notes in OneDrive → Chief of Staff; check it before answering about my day, clients or open topics."** | Everything that changes: radar snapshots, runs, handoffs, lessons, recipes, config history. |

- Setup writes these facts to the host memory if the host exposes a way to do
  it from the conversation (Claude's memory edits, ChatGPT memory). If not,
  setup tells the user the one sentence to say ("Recuerda que…") or includes
  them in the project instructions. **Builder must verify** which memory write
  mechanism exists in Claude chat, Projects and Cowork today and document the
  fallback in `references/memory.md` (new).
- At most ~10 facts; never secrets, never anything from `safety.md` §3.
- `learn` (Phase 3) updates host memory only for stable facts (a changed
  priority, a new key person, a tone preference).

### 1.4 Claude Project (recommended)

Setup recommends creating a Claude Project called "Chief of Staff" (or a
ChatGPT project) and produces the **project instructions** text for the user
to paste (Claude can't create projects itself). The instructions:
point to the registry, tell Claude to use `recall` before answering about the
user's day/clients/topics, to run `learn` after corrections and complex tasks
(Phase 3), and restate the read-only rule. Ordinary chats still work through
host memory + recall; the project just makes it reliable.

**Builder must verify** whether installed plugin skills load in plain Claude
chat and in Projects (not only Cowork). If they don't, the project
instructions must carry compact versions of the `recall` and `learn`
procedures (lessons format, recipe format, anonymisation rules), generated by
setup from a template in `templates/` and covered by a test that keeps the
template in sync with the skills.

### 1.5 Done when (Phase 1)

- A dry run of the setup script (as a business user, in Spanish) needs ≤ 6
  user answers and no technical term appears in assistant messages.
- Google path passes the new flow end to end (nuvel's own account).
- Microsoft path: written from the documented connector behaviour and
  reviewed, but **verification on a real tenant is deferred** — nuvel has no
  Microsoft 365 tenant yet. Track it as an open item (exact tool names, `.md`
  round trip, Outlook/Teams triage) and verify before the first Microsoft
  customer. Until then the Microsoft sections are marked "unverified" in
  `references/`.
- Structural tests pass (manifests at 0.3.0, every cited path exists).

---

## Phase 2 — traces from every skill

### 2.1 Mechanism

- Each skill ends with a **"Trace"** step: if a tool named `record_run_trace`
  (from the nuvel connector) is available, call it **once** with a
  `nuvel.skill_run/1` object; otherwise skip silently. Telemetry never blocks
  or fails a run; one retry on error, then give up and note
  `trace: not sent (<class>)` in the run journal.
- **`install_id`**: UUIDv4 generated at setup, stored in `config` as
  `- telemetry.install_id: …`. `run_id`: new UUIDv4 per run. `host`, `mode`,
  `started_at`, `duration_s` (approximate is fine), `outcome`.
- `- telemetry: on|off` in `config` (default on; nuvel can switch it off per
  customer).
- Each run document gets a short `## Trace` section mirroring exactly what was
  sent (ids, counts, outcome), so the user can see it — transparency.
- The plugin does **not** ship its own `.mcp.json` server entry; the nuvel
  connector is added to the customer's Claude org by nuvel (one shared MCP for
  all plugins). Builder may add a plugin-level MCP reference only if Cowork
  plugins support remote connectors cleanly; default is no.

### 2.2 Step catalogs

`skills/<skill>/trace-steps.json` for every skill (shape from the nuvel spec):

```json
{"skill": "radar",
 "steps": ["radar.load-state", "radar.sweep.email", "radar.sweep.calendar",
           "radar.sweep.chat", "radar.write", "radar.notify"],
 "counts": ["read", "relevant", "skipped_noise", "needs_you_now", "decide",
            "open_loops", "handoffs_applied"],
 "routing": ["vip", "priority", "ask", "waiting_on", "decide", "watching", "noise"]}
```

The builder writes the catalog for each skill (setup, radar, brief, prep,
weekly-review, recall, learn). Every step id a SKILL.md tells the agent to
report must be in its catalog (new test). Tool names in `tools[]` are the
connector tool names lowercased, never arguments.

### 2.3 Done when (Phase 2)

- Tests: every skill has a catalog; SKILL.md step ids ⊆ catalog; a sample
  trace per skill validates against `skill_run.v1.schema.json` (vendored copy
  or fetched in CI — builder's call).
- One real radar run against a local `nuvel-mcp serve --transport http` shows
  up in `nuvel traces` / `nuvel dashboard` with tenant set by the server.

---

## Phase 3 — `learn`: lessons, recipes, sharing

### 3.1 What it does (Hermes-style)

Triggers (skill description + project instructions):
- The user corrects the assistant ("no, así no", "a Marta de usted", "eso no me
  interesa").
- The end of a complex task or long conversation (several tool calls, multiple
  steps, or the user says it'll recur).
- A routine, when the user's handoffs or `config` changes show a new
  preference.

Behaviour: **acts on its own and tells the user afterwards** in one line at the
end of the reply ("He apuntado 1 corrección y he creado la receta *Preparar
propuesta de cliente*. Dime si alguna sobra."). "Bórrala"/"esa no" → retire it.

### 3.2 Registry additions (append-only, newest wins)

```
Chief of Staff/
├── lessons/
│   └── 2026-10-28 1012 lessons          # full list, newest wins
└── recipes/
    ├── 2026-10-28 1130 recipe propuesta-cliente
    └── 2026-11-02 0915 recipe propuesta-cliente   # newer version wins per slug
```

- **`lessons`** — one document holding the full current list (like `config`):
  each lesson is `- <rule> — scope: <skill or "all"> — since <date>`. Adding a
  correction = new `lessons` document with the previous list + the new rule.
  All skills read the newest `lessons` at start. Stable facts also go to host
  memory (§1.3).
- **`recipe <slug>`** — a lightweight skill:
  `## When to use` · `## Steps` · `## Pitfalls` · `## Stats`
  (`- uses: N`, `- successes: N`, `- corrections: N`, `- last_used: date`,
  `- recipe_id: <uuid>`, `- category: <identifier>`, `- status: active|retired`).
  Before a task, skills (and the project instructions) check `recipes/` for a
  matching "When to use"; after using one, `learn` writes a new version with
  updated stats and any correction folded into the steps.
- `config` gains `- sharing.recipes: on|off` (default on).
- **Successful use** = the task the recipe was used for finished and the user
  did not correct the result in that conversation. A correction increments
  `corrections` and folds into the steps; it is not a success.
- **Categories** come from a fixed vocabulary owned by nuvel,
  `references/recipe-categories.md` (≈ 20 business categories such as
  `client-proposal`, `meeting-followup`, `monthly-close`, `hiring`,
  `travel-planning`, plus `other`), updated with plugin releases. Both recipe
  schemas validate `category` with the identifier regex only (so an old server
  accepts new categories); the plugin test checks recipes reference the list.
- `weekly-review` adds a short "what I learned this week" section (lessons and
  recipes created/changed) and consolidates duplicate lessons.

### 3.3 Signals and anonymised recipes to nuvel (nuvel-mcp changes)

Two new tools in `nuvel-mcp`, both in `HTTP_DEFAULT_TOOLS`, both server-tenanted
(tenant from OAuth `client_id`, rejected if sent), both stored next to traces:

1. **`record_recipe_signal`** — closed schema `nuvel.recipe_signal/1`, content
   free: `recipe_id` (uuid), `install_id`, `plugin`, `category` (identifier),
   `event` (`created | used | succeeded | corrected | retired`), counters
   (`uses`, `successes`, `corrections`), `at`. Sent by `learn` on every recipe
   event.
2. **`share_recipe`** — schema `nuvel.recipe/1`, sent automatically (no
   question to the user, per nuvel's decision; covered by nuvel's contract with
   each customer) when a recipe reaches **≥ 3 successful uses** (builder may
   tune) and on each later version. Shape is **closed and generic**:
   `recipe_id`, `version`, `category`, `title` (≤ 80 chars), `when_to_use`
   (≤ 200), `steps[]` (≤ 15 items: `{action: <verb identifier>, tool_kind:
   enum email|calendar|chat|docs|storage|tasks|web|none, text: ≤ 160 chars}`),
   `pitfalls[]` (≤ 5 × 160 chars). No other fields.

Anonymisation, three layers:
- **Writing rule (skill):** the shared copy is rewritten from scratch in
  generic terms — roles not names ("el cliente", "el socio"), no companies,
  amounts, dates, places, emails, phone numbers, URLs, file names or quotes.
- **Self-check (skill):** a second pass over the shared copy against that list;
  any hit → don't send; note `share: blocked (pii)` in the run journal and try
  again at the next version.
- **Server screen (nuvel-mcp):** reject the whole recipe (field paths only in
  the error) if any text matches emails, phone numbers, URLs, IBAN/card-like
  digit runs, currency amounts, or capitalised multi-word sequences not at the
  start of a sentence (builder tunes; false positives are acceptable).

Residual risk, accepted by nuvel: generic text written by a model can still
carry customer-specific detail. Mitigated by the three layers above and by
`sharing.recipes: off` per customer.

**Where the data lives (decided by nuvel):** in the open-source `nuvel-mcp`,
next to the traces — `{feedback_dir}/_recipes/…` through a small store Protocol
shaped like `TraceStore` (local implementation now; nuvel-cloud can plug in its
own later). The multi-customer view is the OSS `nuvel dashboard` pointed at the
deployed server's data directory; no nuvel-cloud work in v0.3.

nuvel side: `nuvel dashboard` gains a **Recipe candidates** view (by category:
installs, uses, success rate, corrections, latest anonymised version) and
`nuvel traces` can list recipe signals. Turning a candidate into a real skill
is manual.

### 3.4 Done when (Phase 3)

- Correcting the assistant in a chat produces a new `lessons` document and the
  next radar/brief applies it.
- A multi-step task produces a recipe; reusing it 3 times sends signals and one
  anonymised recipe that passes the server screen; a recipe with a planted
  name/amount is blocked by both the skill check and the server.
- nuvel-mcp tests: schemas closed, tenant server-set, remote mode serves the
  two tools, screen rejects the planted cases, readers show candidates.

---

## Cross-cutting

- **Version:** plugin `0.3.0` at the end of Phase 3 (pre-releases per phase are
  the builder's call). Skill versions bump with their content.
- **Languages:** skills stay in English; user-facing phrases are generated in
  the user's language. Examples in this doc are Spanish because the first
  customers are.
- **Branching in nuvel:** the Phase 3 MCP changes depend on the unpushed
  branch `claude/chief-of-staff-plugin-a09233` (trace store, remote mode).
  Build them on top of it or after it merges — builder's call; don't push
  until nuvel says so (PyPI `nuvel-mcp` registration is still pending).
- **Docs:** README and plugin README rewritten for business readers;
  CHANGELOG; nuvel's `docs/reference/skill-run-traces.md` gains the two new
  schemas.

## Decided by nuvel (in conversation, 2026-10-27)

- Typical user: SME CEO on Outlook/Teams/OneDrive; Google is the equal
  alternative. Propose the hosts' own connectors.
- Admin consent and connector provisioning are nuvel's job, not the setup's.
- Setup recommended inside a Claude Project; ordinary chats must still work.
- Use host memory deliberately: seeded by setup, maintained by `learn` (no
  separate memory skill).
- Learning acts alone and tells the user afterwards; recipes are lightweight
  skills in the registry.
- Recipe signals and anonymised recipes go to nuvel **without asking** the
  user; one line of disclosure in setup.
- Phase order: setup/M365/memory → traces → learn.
- Recipe candidates live in the open-source nuvel-mcp + `nuvel dashboard`.
- No Microsoft 365 tenant available yet: Microsoft verification deferred.

## Builder's calls (marked so they can be checked)

- Registry stays append-only on OneDrive too.
- Composio dropped from the user-facing flow.
- Three-layer anonymisation, ≥ 3 successful uses threshold, closed recipe shape.
- "Successful use" definition, fixed category vocabulary.
- Read-only Microsoft connector at setup → stop and resume, no fallback.
- `telemetry` and `sharing.recipes` switches in `config`, default on. nuvel
  switches them per customer during onboarding (it runs setup with the
  customer) or later by asking the customer's assistant to write a new
  `config`; no server-side per-tenant switch in v0.3.
- `## Trace` section mirrored in each run document.
- No `.mcp.json` in the plugin by default.
- Recipes live in `recipes/`, lessons in a single newest-wins `lessons` doc.

## Open for the builder

- The host-memory write mechanism per surface (verify, then document).
- Exact Outlook/Teams tool names in the Microsoft 365 connector and their
  read-only subsets.
- Catalog contents per skill; server-screen regexes; dashboard layout.
