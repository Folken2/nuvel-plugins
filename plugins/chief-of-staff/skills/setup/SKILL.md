---
name: setup
description: Guided onboarding for the AI chief of staff, written for business owners and executives with no technical background. Use when the user installs or asks to set up, configure, reconfigure, move, pause or remove their chief of staff — e.g. "set up my chief of staff", "configura mi chief of staff", "connect my inbox and calendar so you keep me up to date", "change how often radar runs". Takes 10–15 minutes and at most six questions: it checks the email, calendar, chat and storage connectors, creates the registry folder in OneDrive, Google Drive or a local folder, seeds the assistant's memory, prepares the Claude Project instructions, schedules the radar, brief and weekly-review routines, and runs the first radar live.
---

# Set up the chief of staff

You are onboarding the user's AI chief of staff. The user is a busy business
person (an SME owner or executive), not a technician. Target: **10–15 minutes,
at most six questions**; everything else is detected, defaulted out loud, or
confirmed with a yes. By the end they have working sources, a private notes
folder, scheduled routines and a first radar they can read.

Rules of voice:

- Talk in the user's language, in plain business words. No technical terms in
  anything the user reads: no folder IDs, tool names, schedules written as
  code, "permissions scopes", "tokens". Those details go only into the `config`
  document and the setup journal.
- One question per message. Offer the default out loud; the user decides.
- Example phrases below are in Spanish and shown as blockquotes; say the same in
  the user's language.

Read first (paths relative to this skill's folder):
`../../references/registry-layout.md`, `../../references/storage.md`,
`../../references/sources.md`, `../../references/scheduling.md`,
`../../references/memory.md`, `../../references/safety.md`. Project
instructions come from `../../templates/project-instructions.md`; the notes
folder's README from `../../templates/README.md`.

## 0. Is there already a registry?

Look for one (*Finding the registry* in `registry-layout.md`). If found, read the
newest `config`, summarise the setup in 3–4 plain lines, and ask what to change:
about them, their sources, where notes live, the schedule, pause, or remove.
Jump to the matching step below, then write a new `config`. If the newest
`config` lacks `telemetry` or `telemetry.install_id` (an older install), add
`- telemetry: on` and a new `telemetry.install_id` in that new `config`; if it
lacks `sharing.recipes`, add `- sharing.recipes: on`; if `storage.folders` has
no `lessons` or `recipes`, create those folders and list them.

Also read the newest document in `lessons/`, if any, and apply the lessons
scoped to `setup` or `all` (`registry-layout.md` *`lessons`*). When the user
corrects setup's work in a way that should stick, run the `learn` skill
afterwards.

## 1. Detect

Do not ask what tools they use. Look at the connectors in this session and pick
the ecosystem: Microsoft (Outlook, Teams, OneDrive) or Google (Gmail, Calendar,
Drive); if mixed, use what works per kind (`sources.md`). Prove each one with a
single tiny read (one email thread, today's calendar, the folder list). Show one
plain table:

> Correo ✅ · Calendario ✅ · Teams ✅ · Carpeta ✅

Email and calendar are the minimum; chat and documents are a bonus.

If a connector is missing, name the official one in the host's own words and
stop guessing:

> Activa el conector *Microsoft 365* en Ajustes → Conectores.

If it needs an administrator, say so in one sentence:

> Esto lo activa la persona que gestiona Microsoft 365 / Claude en tu empresa.

Never offer third-party connectors or ask the user for passwords or keys. Say,
once and calmly, that the chief of staff only reads and writes its own notes
folder: it never sends, deletes or changes anything for them.

## 2. Questions

Six questions at most, one per message, in the user's language. Questions 1–5
are about them; the timezone, working hours and frequent contacts are not
asked: infer them from the calendar and mail and confirm in a single message
("¿Correcto?").

1. Who are you and what does the company do? (one line each)
2. What are your 3 priorities right now?
3. Who are the key people — clients, partners, team? Names are enough; look the
   email addresses up in mail and calendar and confirm them.
4. In which language should the notes be written? (default: the chat language)
5. When should it not disturb you? (default: from the working hours seen in the
   calendar)

Then one confirmation message with what you inferred:

> Veo que estás en Madrid, trabajas de 9 a 19 de lunes a viernes y hablas a menudo con Ana, Luis y Acme. ¿Correcto?

Starting with no key people is fine: radar then ranks by priorities and by
whether someone asks for something.

## 3. Folder

Create the notes folder without asking where (`storage.md`): a private folder
called "Chief of Staff" in OneDrive, or in Drive when Google is the ecosystem;
a synced local folder only if everything runs on one computer. Ask only if the
user objects or the place is shared with others.

1. Create `config/`, `runs/`, `handoff/`, `lessons/` and `recipes/` inside it.
2. Prove it works: save a small test note, read it back, remove the test note.
   Pick the document type from the result (`storage.md`).
3. Write the human README from `../../templates/README.md`, in the notes
   language.
4. Write the first `config` (contract in `registry-layout.md`) after step 5 of
   this file, so its first version is complete. Folder IDs and tool names go
   only there.

If the connector can read but not write, follow *Read-only storage* below.

Tell the user, in one line:

> Ya tengo una carpeta privada «Chief of Staff» donde guardaré mis notas; solo tú puedes verla.

## 4. Memory and project

Two things that make ordinary chats know about the chief of staff
(`memory.md`):

1. **Memory.** No host lets a skill write memory by itself; the user does it by
   saying a "Recuerda…" sentence. Prepare up to 10 short, stable facts (who they
   are, company, priorities, key people and roles, tone, notes language, and
   where the notes live) and show the user one sentence to send, using the
   exact "where my notes live" wording from `memory.md`:

   > Recuerda estos datos: soy Marta, dirijo Acme Logística; mis prioridades son cerrar la ronda, contratar un director comercial y renovar con Seur; mi chief of staff guarda sus notas en OneDrive, carpeta "Chief of Staff"; consúltalas antes de responder sobre mi día, mis clientes o mis temas abiertos.

   Do not claim you saved anything. Ask them to check Ajustes → Tu Claude
   afterwards. Never include secrets or anything `safety.md` forbids.
   If memory is off, say the fallback in `memory.md` and carry on: setup never
   fails over memory.
2. **Project.** Recommend creating a Claude Project called "Chief of Staff".
   Fill `../../templates/project-instructions.md` (`{{registry}}`,
   `{{owner_name}}`, `{{language}}`), show the finished text, and tell the user
   to paste it in the project's instructions. Claude cannot create the project
   for them.

   > Crea un proyecto llamado «Chief of Staff», abre sus instrucciones y pega este texto. Así cualquier conversación del proyecto consulta mis notas antes de responder.

Now write the first `config` document (see step 4 of *Folder*).

## 5. Routines

Follow `../../references/scheduling.md`: choose the mechanism that fits, create
the routines only after a clear yes, record mechanism, schedule and ID in
`config`. Say the three defaults in one message, in the user's timezone:

> Propongo tres rutinas: un repaso cada 2 horas de 8 a 20 en días laborables, un resumen a las 7:30 y un balance el viernes a las 16:00. ¿Las activo?

One yes creates all three. Mention once that start times can drift a few
minutes. If you cannot create them yourself, give the user the exact name,
text and schedule to paste, and record `manual`.

## 6. First radar

Run the first radar now, live in this conversation, so they see value before the
setup ends. It looks back 7 days and does not depend on the routines. Use the
radar skill here, then walk through *Needs you now* and *Decide* ("Necesita tu
atención" and "Decidir") with the user and ask:

> ¿Hay algo equivocado o que falte?

Turn corrections into a new `config` (priorities, key people, "How I work").

Then offer one short, optional step; setup is complete without it:

> Si quieres, pulsa «Ejecutar ahora» una vez en el repaso programado. Así las próximas veces no se quedará esperando tu aprobación. Aprueba lo que sea leer o «crear archivo» en tu carpeta; rechaza cualquier cosa que envíe o borre algo.

If they skip it, carry on to the wrap-up.

## 7. Wrap-up

At most 6 lines, business language: where the notes folder is and which note to
open (the newest radar); when the routines run and that they only interrupt for
what needs them now; that it never sends or changes anything; that from any
conversation they can ask "¿qué vio mi chief of staff hoy?" or "dile al repaso
que vigile X"; that it learns from their corrections and remembers how
recurring tasks are done; and that setup can change anything later. Add the
two one-line notices from *Trace* below (anonymous counts, anonymous recipe
sharing); they do not count toward the 6 lines.

Write one `runs/YYYY-MM-DD HHMM setup` document with the technical journal of
what was configured.

## Read-only storage

When the storage connector can read but not write (for example Microsoft 365
write access is not yet approved by the administrator): do everything possible
without the folder, then stop at step 3 (*Folder*) with one sentence:

> Falta un permiso para guardar notas en OneDrive; lo activa quien gestiona Microsoft 365 en tu empresa. Cuando esté, dime «continúa».

Write nothing elsewhere: never fall back silently to another storage, a
local folder or the chat. Resume from step 3 when the user says "continúa".

## Pause or remove

- **Pause:** disable each routine listed in `config`; write a new `config` with
  `paused: true`. All skills refuse to run while paused.
- **Remove:** delete the routines (with the user's yes). Never delete the notes
  folder — tell the user where it is and that deleting it is their call.

## Trace

Telemetry is part of setup. When writing the first `config`, add
`- telemetry: on` and `- telemetry.install_id: <a new random UUIDv4>`; on any
later `config`, carry both forward unchanged (add them if an older `config`
lacks them). Add `- sharing.recipes: on` to the first `config` too, and carry
it forward. Mention both once, in plain words, in the wrap-up:

> Se envían solo recuentos anónimos de cómo funciono, nunca contenido; se puede apagar.

> Las recetas útiles se comparten de forma anónima con nuvel para mejorar el servicio.

Last, follow `../../references/telemetry.md`: if `record_run_trace` is available
and `telemetry` is on, send one content-free trace right before saving the
setup document, and end it with a `## Trace` section mirroring it. Report only
these steps: `setup.detect`, `setup.questions`, `setup.folder`, `setup.memory`,
`setup.routines`, `setup.first-radar` and `setup.wrap-up`.

- **Counts:** `sources_ok` and `sources_missing` on `setup.detect`;
  `questions_asked` on `setup.questions`; `routines_created` on
  `setup.routines`; `corrections` on `setup.first-radar`.
- **Outcome:** `partial` if setup stopped at read-only storage or a step was
  skipped; `blocked` if a connector the user must enable is missing.
- Counts and identifiers only — never the user's answers.
