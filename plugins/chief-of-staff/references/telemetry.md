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
  (the nuvel connector is not added), skip silently — no warning, no mention to
  the user. The plugin ships no connector of its own.
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
| `run_id` | a new UUIDv4 for this run (never reused) |
| `install_id` | `telemetry.install_id` from the newest `config` |
| `plugin` | `{"name": "chief-of-staff", "version": <plugin version from the manifest>}` |
| `skill` | `{"name": <this skill>, "version": <same plugin version>}` (skills have no version of their own) |
| `host` | `claude-chat`, `claude-cowork`, `claude-code`, `claude-routine`, `codex` or `other` — where this run is happening |
| `mode` | `scheduled` (started by a routine) or `interactive` (the user asked) |
| `started_at` | ISO 8601 UTC time the run began |
| `duration_s` | whole seconds from start to now; approximate is fine |
| `outcome` | `success`, `partial` (something was skipped or a source failed), `failure`, `blocked` (stopped by a rule, such as no registry) or `skipped` |
| `steps` | one entry per catalog step that ran: `{"id": "<skill>.<step>", "status": "ok"\|"skipped"\|"error", "counts": {…}}` |
| `tools` | optional: `{"name", "calls", "errors"}` per tool used |
| `errors` | optional: `{"step", "class"}` per failure |
| `routing` | optional: how many items landed in each bucket |
| `safety` | optional: `{"injection_suspected": <n>, "forbidden_tool_requested": <n>}` — integer counts (0 to 10000), both keys or neither |
| `user_corrected` | optional boolean: the user corrected the result during an interactive run |

Never add a `tenant` field; the server sets it.

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

The `learn` skill sends two more kinds of object, through the same nuvel
connector. The full procedure is in `learn`'s skill; these are the rules.

- **`record_recipe_signal`** — argument `{"signal": {...}}`, schema
  `nuvel.recipe_signal/1`. One per recipe event (`created`, `used`,
  `succeeded`, `corrected`, `retired`), content-free like a trace: `signal_id`
  (new UUIDv4), `recipe_id`, `install_id`, `plugin`, `category` (from
  `recipe-categories.md`), `event`, `at` (RFC 3339 UTC) and the cumulative
  `uses`, `successes`, `corrections` after the event.
- **`share_recipe`** — argument `{"recipe": {...}}`, schema `nuvel.recipe/1`.
  An anonymised, generic rewrite of a recipe that has had at least 3
  successful uses, sent again on each later version whose text changed:
  `recipe_id`, `install_id`, `plugin`, `version`, `category`, `language`,
  `title` (≤ 80), `when_to_use` (≤ 200), `steps` (1–15 of `action`,
  `tool_kind`, `text` ≤ 160), optional `pitfalls` (≤ 5 × 160). Nothing else.
  This is the only object that carries text, so it is written to a strict
  rule (roles not names; no companies, products, amounts, currencies, dates,
  places, contacts, URLs, file names, quotes or digits), self-checked, and
  screened again by the server, which rejects the whole recipe on any hit.

Switches, both read from the newest `config`:

| setting | signals | sharing |
|---|---|---|
| `telemetry: off`, or no `telemetry.install_id` | not sent | not sent |
| `telemetry: on` and `sharing.recipes: off` | sent | not sent |
| `telemetry: on` and `sharing.recipes: on` (or missing) | sent | sent |

As with traces: no tool, no send, silently; never a `tenant` field; never
block or change the user's task; retry an error once, then journal one line
in the `learn` run document — `signal: not sent (<class>)`,
`share: not sent (<class>)`, or `share: blocked (pii)` when the self-check or
the server's screen stops a recipe. A blocked share is recorded as the
recipe's `blocked_version` and retried only at the recipe's next `version`
(text change), never on a stats-only update. The user is told once, at setup, that useful recipes are shared
anonymously; they are never asked per recipe.
