# Telemetry — content-free run traces

Every skill ends with a **Trace** step. When the nuvel connector is available,
the skill sends **one** `nuvel.skill_run/1` object describing *how the run went*
(which steps ran, how many items, which tools, which errors) so the plugin can
be improved. It never describes *what the run was about*.

## Hard rules

- **Content-free.** Only fixed identifiers and integers. Never a name, subject,
  address, email or message text, file or folder name, meeting title, link,
  project name, tool argument, search query, or free text of any kind. If a value
  is not in the skill's `trace-steps.json` or in the tables below, do not send it.
- **Never fails the run.** Telemetry never blocks, delays, or changes the result
  of a run; a failed trace is only a line in the journal.
- **Read-only and append-only stay true.** Sending a trace is not a source write
  and not a registry write.
- **No connector, no trace.** If no tool named `record_run_trace` is available
  (the nuvel connector is not added), send nothing and say nothing to the user —
  no warning, no mention. The run document's `## Trace` section says only
  `not sent: no connector`. The plugin ships no connector of its own.
- **Off means off.** If the newest `config` has `- telemetry: off`, skip
  silently. If it has no `telemetry.install_id` (a v0.2 install), do not send
  and note `trace: not sent (no install_id)` in the run journal; setup's
  reconfigure path adds the key. A paused chief of staff (`paused: true`) does
  not run, so it sends nothing.

## Building the object

Keep a running tally while the skill works; build the object once, at the end.

| field | value |
|---|---|
| `schema` | `nuvel.skill_run/1` |
| `run_id` | a new UUIDv4 for this run (never reused), in the format below |
| `install_id` | `telemetry.install_id` from the newest `config` (must be in the UUID format below) |
| `plugin` | `{"name": "chief-of-staff", "version": <plugin version, see Formats>}` |
| `skill` | `{"name": <this skill>, "version": <same plugin version>}` (skills have no version of their own) |
| `host` | `claude-chat`, `claude-cowork`, `claude-code`, `claude-routine`, `codex` or `other` — where this run is happening |
| `mode` | `scheduled` (started by a routine) or `interactive` (the user asked) |
| `started_at` | UTC time the run began, in the timestamp format below |
| `duration_s` | whole seconds from start to now; approximate is fine |
| `outcome` | `success`, `partial` (something was skipped or a source failed), `failure`, `blocked` (stopped by a rule, such as no registry) or `skipped` |
| `steps` | one entry per catalog step that ran: `{"id": "<skill>.<step>", "status": "ok"\|"skipped"\|"error", "counts": {…}}` |
| `tools` | optional: `{"name", "calls", "errors"}` per tool used |
| `errors` | optional: `{"step", "class"}` per failure |
| `routing` | optional: how many items landed in each bucket |
| `safety` | optional: `{"injection_suspected": <n>, "forbidden_tool_requested": <n>}` — integer counts (0 to 10000), both keys or neither |
| `user_corrected` | optional boolean: the user corrected the result during an interactive run |

Never add a `tenant` field; the server sets it.

### Formats

The server rejects a whole object on a single malformed value, so these are
exact. A rejected `install_id` would silently drop every trace, signal and
share from that install, forever.

- **UUIDs** (`run_id`, `install_id`, `signal_id`, `recipe_id`) are lowercase
  hex in the form `xxxxxxxx-xxxx-4xxx-Yxxx-xxxxxxxxxxxx`, where `Y` is one of
  `8`, `9`, `a`, `b`. No uppercase, no braces. Generate them with code when a
  code tool exists; never write one by hand if you can avoid it. Example:
  `3f2b8c1e-5d4a-4e9b-9a7c-1b2d3e4f5a6b`.
- **Timestamps** (`started_at`, a signal's `at`) are UTC in the form
  `YYYY-MM-DDTHH:MM:SSZ`, with seconds, a `T` and a final `Z`. Example:
  `2026-10-27T09:30:00Z`. Not `2026-10-27 09:30`, not `2026-10-27T09:30Z`.
- **Plugin version** is the `version` in `../.claude-plugin/plugin.json`,
  currently `0.4.0`: three numbers separated by dots, never `0.3`.
- **Tool names**: any `tools[]` entry whose lowercased name does not match
  `^[a-z0-9][a-z0-9_.:-]{0,79}$` is left out of the object.
- **Error steps**: `errors[].step` is one of the step ids in the skill's
  `trace-steps.json`.

### Identifiers

- Step ids come from the skill's `trace-steps.json` and start with
  `<skill>.`. Only report ids from that file.
- `counts` keys come from the catalog's `counts` list, `routing` keys from its
  `routing` list; values are non-negative integers. At most 20 count keys per
  step, 50 steps, 50 tools, 20 errors. Leave out keys that do not apply.
- `tools[].name` is the lowercase tool name as the host shows it (for example
  `search_threads`). For Microsoft 365, whose tool names are not published, use a
  functional identifier: `m365.mail.search`, `m365.mail.read`,
  `m365.calendar.list`, `m365.chat.read`, `m365.files.search`,
  `m365.files.read`, `m365.files.create`. Never include arguments.
- `errors[].class` is one of `auth`, `rate_limit`, `not_found`, `permission`,
  `timeout`, `tool_error`, `contract_violation`, `registry_missing`, `other`.
  Map the failure to the nearest class; never copy an error message.
- `safety.injection_suspected` is how many times this run noticed
  instruction-like text in source content (`safety.md` §2);
  `forbidden_tool_requested` is how many times content or the registry asked for
  a forbidden action. Integers, never booleans; never quote the content.

## Sending

1. Call `record_run_trace` **once** with the object, right before the run
   document is saved.
2. On error, retry **once**. If it fails again, give up: add
   `trace: not sent (<class>)` to the run document's journal (class as in
   `errors[].class`) and carry on. Never retry further, never report it as a run
   failure, never ask the user about it.
3. Do not try to reconnect the connector during a run, scheduled or not.

## Showing the user what was sent

Because the registry is append-only, the run document is written once, so the
trace is sent **just before** the document is saved (all steps except the final
save are already known; report the save as `ok`). The document then ends with a
short `## Trace` section that mirrors exactly what was sent: outcome, step ids
with status and counts, routing, error classes. Nothing else. If nothing was
sent, one line says why: `not sent: telemetry off`, `not sent: no connector`, or
`trace: not sent (<class>)` after the retry failed. Skills whose last action is
not a document (a recall answer with no handoff) send the trace last and put no
section anywhere.

## Config keys

`config` carries `- telemetry: on` (default; nuvel can set `off` per customer)
and `- telemetry.install_id: <uuid4>`, generated once by setup and carried
forward unchanged in every later `config`. See `registry-layout.md`.

## Recipe signals and recipe sharing

The weekly review sends two more kinds of object through the same nuvel
connector; the full procedure is in `recipe-sharing.md`.

- **`record_recipe_signal`** — argument `{"signal": {...}}`, schema
  `nuvel.recipe_signal/2`: a weekly, content-free snapshot of a changed
  recipe (status and counters).
- **`share_recipe`** — argument `{"recipe": {...}}`, schema `nuvel.recipe/3`:
  the structure of a recipe that passes the quality bar (category, steps,
  counters) and, only with `sharing.recipe_text: on`, its text written with
  placeholders. The server masks that text before anything is stored: Spanish
  (`es`), English (`en`) and Catalan (`ca`) free text is masked word by word.
  Known limit: a name spelled exactly like an everyday word (e.g. March, or
  Sala in Catalan) can pass through, so never put personal names in free
  text.

Switches, all read from the newest `config`:

| key | default | meaning |
|---|---|---|
| `telemetry` | `on` | traces and recipe signals (content-free) |
| `sharing.recipes` | `on` | share the **structure** of recipes that pass the quality bar |
| `sharing.recipe_text` | `off` | also share their text, masked on the server; `on` only when the user said yes at setup |

As with traces: no tool, no send, silently; never a `tenant` field; never
block or change the review; retry an error once, then journal one line in the
`weekly-review` run document (lines in `recipe-sharing.md`).

## Approvals (for installers)

Hosts ask for approval the first time each tool is used, and in a scheduled
task the approval is stored per task. Where the host offers it, set the nuvel
connector's tools (`record_run_trace`, `record_recipe_signal`, `share_recipe`)
to always-allow in the organisation's connector settings, so an unattended run
never waits on them. Setup also tells the user to approve them the first time
they appear (`scheduling.md`).
