# Recipe sharing

nuvel collects good recipes to turn the best into real skills for everyone.
Sharing runs in the weekly review, never in `learn`. Recipe states, stats and
the quality bar are in `recipes.md`; placeholders and step actions in
`recipe-actions.md`; formats in `telemetry.md` *Formats*.

Weekly procedure: see below (weekly review).

## Text (only with `sharing.recipe_text: on`)

By default only the structure of a recipe is shared, never its text. Build the
text below only when `config` says `- sharing.recipe_text: on`. The text is
masked on nuvel's server before anything is stored; your job is to write it
already with placeholders, so that what survives the masking still reads well.

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
