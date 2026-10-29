# Recipe actions and placeholders

Two fixed vocabularies owned by nuvel, used when `learn` shares a recipe
(`nuvel.recipe/2`). Every step's `action` is exactly one identifier from the
first list; every entry of a step's `slots`, and every `{placeholder}` written in
a note or the narrative, is one type from the second. Pick the closest; use
`other` only when nothing fits. Never invent one: the lists grow with plugin
releases, not per user, and the server rejects anything else.

The identifiers are in English and never translated; the descriptions are only
to help choose.

## Actions

- `search` — look for something in mail, files, calendar or the web
- `read` — open and read a message, document or page
- `summarise` — boil something down to the key points
- `extract` — pull specific facts or figures out of something
- `compare` — set two or more things side by side
- `check` — verify something against a rule, a calendar or a list
- `calculate` — work out a total, a difference or a forecast
- `list` — put items together into a list or table
- `draft` — write a first version of a message or document
- `edit` — improve or correct an existing text
- `translate` — turn text into another language
- `create` — make something new (a file, an event, a task)
- `update` — change something that already exists
- `file` — save or move something to its place
- `propose_slot` — suggest times for a meeting
- `schedule` — put an event in the calendar
- `send` — send a new message to someone
- `reply` — answer a message
- `forward` — pass a message on to someone else
- `share` — give someone access to a file or folder
- `remind` — set up a reminder
- `follow_up` — chase something that has not been answered
- `ask` — ask the user or a colleague for input or approval
- `decide` — choose between options
- `wait` — pause until something happens
- `other` — none of the above

## Placeholders

Written in curly braces, in lowercase English, for example `{person}`.

- `{person}` — a named person
- `{company}` — a company or organisation
- `{team}` — a team or department
- `{product}` — a product, service or brand
- `{project}` — a named project or deal
- `{document}` — a named document (proposal, contract, report)
- `{file}` — a file name
- `{folder}` — a folder name
- `{amount}` — a sum of money
- `{number}` — any other figure or count
- `{date}` — a day or calendar date
- `{time}` — a time of day
- `{period}` — a span such as a week, a month or a quarter
- `{place}` — a city, address or venue
- `{email}` — an email address
- `{phone}` — a phone number
- `{url}` — a web address
- `{id}` — a reference, invoice or account code
- `{topic}` — the subject something is about
- `{other}` — any other identifying detail

The server also writes a `{?}` where it masks a word it cannot place. Never
write `{?}` yourself.
