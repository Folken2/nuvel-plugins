# Recipe sharing

nuvel collects good recipes to turn the best into real skills for everyone.
Sharing runs in the weekly review (sub-steps *Signals* and *Share* of its
recipe batch), never in `learn`. Recipe states, stats and the quality bar are
in `recipes.md`; placeholders and step actions in `recipe-actions.md`; UUID,
timestamp and plugin-version formats in `telemetry.md` *Formats*.

What leaves the registry, at most:

- a weekly **signal** per changed recipe: counters and status, no content;
- the **structure** of a recipe that passes the quality bar: its category,
  which kinds of step in which order, on which kinds of thing, and its
  counters;
- its **text** (title, when to use, step notes, pitfalls, narrative), masked
  on nuvel's server, only when the user said yes to setup's question 6.

## Switches

All read from the newest `config`.

| setting | signals | structure | text |
|---|---|---|---|
| `telemetry: off`, or no `telemetry.install_id` | not sent | not sent | not sent |
| `telemetry: on`, `sharing.recipes: off` | sent | not sent | not sent |
| `telemetry: on`, `sharing.recipes: on` (or missing), `sharing.recipe_text: off` (or missing) | sent | sent | not sent |
| `telemetry: on`, `sharing.recipes: on` (or missing), `sharing.recipe_text: on` | sent | sent | sent |

A missing `sharing.recipe_text` counts as `off`; a missing `sharing.recipes`
counts as `on`. `sharing.recipes: off` shares nothing, whatever
`sharing.recipe_text` says. Only setup changes these keys, and only setup's
question 6 turns `sharing.recipe_text` on.

No tool, no send, silently: without `record_recipe_signal` there are no
signals, without `share_recipe` no shares, and nobody is told. Never send a
`tenant` or `masking` field: the server sets them and rejects a client that
sends them. Nothing here ever blocks, delays or changes the review.

## Weekly procedure

The weekly review runs its recipe batch in this order (`weekly-review`
*Steps*): expire drafts, merge duplicate recipes, rebuild the index, signals,
share. Work out every recipe's new version **in memory** through all five;
then write **one** new document per recipe that changed this run (expired,
merged, retired by a merge, or given a share outcome). Never two versions of
the same recipe in one run (`recipes.md` *One document per recipe per run*).
The share outcome (`shared_version` or `blocked_version`) goes into that one
document. A share outcome alone is a stats-only change: `version` stays.

## Signals (`nuvel.recipe_signal/2`)

Only when `record_recipe_signal` is available, `telemetry` is `on` and
`config` has `telemetry.install_id`. One signal per recipe whose stats or
status changed since the last weekly review: a recipe with a document newer
than the newest `weekly-review` run, or one this batch changes (an expired
draft, both recipes of a merge). No `weekly-review` run yet → every recipe
that is not a draft. Drafts are never signalled (`recipes.md`); a draft that
*Expire drafts* retires is not signalled either, since nuvel never heard of
it.

Call `record_recipe_signal` with `{"signal": {...}}`, the values as they
stand after this batch:

| field | value |
|---|---|
| `schema` | `nuvel.recipe_signal/2` |
| `signal_id` | a new UUIDv4 for this signal |
| `recipe_id` | the recipe's `recipe_id` |
| `install_id` | `telemetry.install_id` from `config` |
| `plugin` | `{"name": "chief-of-staff", "version": <plugin version, `telemetry.md` *Formats*>}` |
| `category` | the recipe's `category` |
| `status` | `active` or `retired` (the schema also allows `draft`; drafts are not sent) |
| `at` | now, as `YYYY-MM-DDTHH:MM:SSZ`, e.g. `2026-11-06T17:00:00Z` |
| `uses`, `successes`, `corrections`, `days_used` | the recipe's counters |

Nothing else goes in the object: no title, slug, step or name. A
`"duplicate"` reply is fine. On error retry once, then journal
`signal: not sent (<class>)` (classes as in `telemetry.md`) and carry on.

## Share (`nuvel.recipe/3`)

Only when `share_recipe` is available, `telemetry` is `on`,
`telemetry.install_id` exists and `config` does not say
`- sharing.recipes: off`. Share a recipe when **all** hold:

- it passes the quality bar (`recipes.md` *Quality bar*): `status: active`,
  `successes` ≥ 1, `days_used` ≥ 3, `last_outcome` not `corrected`;
- its `version` is greater than both `shared_version` and `blocked_version`
  (first share, or a later version with changed steps or text that was not
  rejected). A stats-only update never re-shares, and never re-attempts a
  rejected version.

There is no self-check that blocks the share: personal details are masked by
the server, not stopped here.

1. **Build `steps`** from the private recipe, one per real step (1–15), each
   exactly `{action, tool_kind, slots}` and nothing else (what a step does in
   words goes only in `text.step_notes`):
   - `action`: one identifier from `recipe-actions.md` (closest fit, else
     `other`);
   - `tool_kind`: what the step works through: `email`, `calendar`, `chat`,
     `docs`, `storage`, `tasks`, `web` or `none`;
   - `slots`: the kinds of thing the step works on, 0–4 different types from
     the placeholder list in `recipe-actions.md` (`[]` when none).
2. **Build `stats`** from the recipe's `## Stats`: `{uses, successes,
   corrections, days_used}`, integers.
3. **Build `text` only with `sharing.recipe_text: on`** (*Text* below).
   Otherwise leave the `text` key out entirely: no empty object, no
   `language` alone.
4. **Call `share_recipe`** with `{"recipe": {...}}`:

| field | value |
|---|---|
| `schema` | `nuvel.recipe/3` |
| `recipe_id` | the recipe's `recipe_id` (UUIDv4) |
| `install_id` | `telemetry.install_id` from `config` (UUIDv4) |
| `plugin` | `{"name": "chief-of-staff", "version": <plugin version, `telemetry.md` *Formats*>}`; the version matches `^\d{1,2}\.\d{1,2}\.\d{1,2}$` |
| `version` | the recipe's `version`, an integer 1–1000 |
| `category` | one identifier from `recipe-categories.md` |
| `steps` | 1–15 items `{"action", "tool_kind", "slots"}` (step 1) |
| `stats` | `{"uses", "successes", "corrections", "days_used"}`, integers 0–100000; `successes`, `corrections` and `days_used` never above `uses` |
| `text` | only with `sharing.recipe_text: on` (*Text*) |

No other fields at any level.

5. **Read the reply**, and put the outcome in the recipe's one new version
   (*Weekly procedure*):
   - `recorded` (with `recipe_id`, `version`, `masked`, `words`, `dropped`) →
     `shared_version` = `version`. Journal `share: recorded`; when `text` was
     sent, `share: recorded (masked N/M)`, N being `masked` and M `words`. If
     `dropped` is not empty, also journal `share: recorded, <fields> dropped`
     with the pointers it lists (they look like `/text/title`). A text field
     is dropped when the server judged too much of it to be names or figures,
     or when its language cannot be masked (*Text*); the structure is kept
     either way.
   - `duplicate` → `shared_version` = `version`.
   - `rejected` (it names field paths only; a key chosen by the client shows
     as `*`; a format problem such as a malformed `install_id` or a value
     outside a list) → journal `share: rejected (<paths>)` and set
     `blocked_version` = `version`; never retry it.
   - Any other error → retry once, then journal `share: not sent (<class>)`
     and leave `shared_version` and `blocked_version` unchanged (the next
     weekly review tries again).

The journal lines go in the weekly review's run document, never the recipe's
name or text. Nothing changes in what the user is told: setup told them once
what is shared; they are never asked per recipe.

## Text (only with `sharing.recipe_text: on`)

By default only the structure of a recipe is shared, never its text. Build
`text` only when `config` says `- sharing.recipe_text: on` (*Switches*). The
text is masked on nuvel's server before anything is stored; your job is to
write it already with placeholders, so that what survives the masking still
reads well.

`text` is `{"language", "title", "when_to_use", "step_notes", "pitfalls",
"narrative"}`: `language` is required and at least one other field must be
there; leave out any field you have nothing for. Limits: `title` ≤ 80
characters, `when_to_use` ≤ 200, `step_notes` ≤ 15 strings of ≤ 160 and never
more than `steps`, `pitfalls` ≤ 5 strings of ≤ 160, `narrative` ≤ 2000.

**Placeholders.** Write `title`, `when_to_use` and `pitfalls`, and the
`step_notes` (one per step, in the order of the steps, ≤ 160 characters
each: what the step does), generic: placeholders instead of any person,
company, product, place, amount or date (`{person}`, `{company}`,
`{amount}`, `{date}`, `{topic}`, …, all in `recipe-actions.md`). The server
masks these fields too, and a title that is mostly names is dropped whole.

Example step notes, in Spanish:

> Buscar el último correo de {person} con la petición de {company}.
>
> Preparar el borrador con el importe de {amount} y la entrega el {date}.
>
> Pedir a {person} que revise el borrador antes de enviarlo.

Example titles, in Spanish:

> Propuesta para {company}
>
> Seguimiento de una reunión con {person}

Example `when_to_use`: "Cuando {person} pide una propuesta con importe y
fecha de entrega." Example pitfall: "No enviar el borrador sin que {person}
confirme el importe."

**Narrative** (optional but wanted, ≤ 2000 characters): in `owner.language`,
the original wording of what the user asked and how it was solved, as a short
story, not a transcript. Replace every person, company, product, place,
amount, date, email, phone, URL, file or folder with its placeholder. The
server masks again regardless; the placeholders you write are what keep the
narrative readable. Example, in Spanish:

> El usuario pidió preparar una propuesta para {company}. Busqué el último
> correo de {person} sobre {topic}, revisé una propuesta parecida y redacté
> un borrador con el importe de {amount} y la entrega el {date}. {person}
> pidió ajustar el plazo y lo corregí antes de enviarlo.

The same in Catalan:

> L'usuari va demanar preparar una proposta per a {company}. Vaig cercar
> l'últim correu de {person} sobre {topic}, vaig revisar una proposta
> semblant i vaig redactar un esborrany amb l'import de {amount} i el
> lliurament el {date}. {person} va demanar ajustar el termini i ho vaig
> corregir abans de l'enviament.

Placeholders matter because masking keeps every word in its everyday
vocabulary, so a name spelled exactly like one of those words (e.g. March, or
Sala in Catalan) can pass through. Never put personal names in free text.

Never write `{?}` yourself: only the server uses it.

**Language.** `title`, `when_to_use`, `step_notes`, `pitfalls` and
`narrative` are written in `owner.language`, and `text.language` is its two
lowercase letters (`es`, `ca`, `en`). The server masks free text in Spanish
(`es`), English (`en`) and Catalan (`ca`). For any other language the recipe
is still sent and recorded, but only its structure is kept: the free text is
dropped on the server and listed in `dropped`. Send it anyway; do not
translate the text to make it pass.
