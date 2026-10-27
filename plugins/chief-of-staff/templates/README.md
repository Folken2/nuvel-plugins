# Chief of Staff

This folder is the working memory of your AI chief of staff (the nuvel
`chief-of-staff` plugin for Claude and Cowork). Your scheduled routines update
it on their own. Setup writes this page in your registry language.

## How to read it

- **What matters now:** open the newest document in `runs/` whose name ends in
  "radar". It has what needs you now, decisions waiting, today's meetings and
  open loops.
- **runs/** — one document per run (radar, brief, prep, weekly review). It is
  both the journal and the history: nothing is ever deleted.
- **handoff/** — instructions for the next runs ("watch for Acme's reply",
  "ignore that thread"). Ask your assistant from any conversation.
- **lessons/** — what you have corrected ("write to Marta formally"). The
  newest document is the full list; say "forget that rule" to drop one.
- **recipes/** — how recurring tasks were done well, so the next time follows
  the same steps. Say "delete that recipe" to retire one.
- **config/** — your profile, priorities, sources and routines. The newest one
  is in force; to change anything, ask your assistant and it writes a new version.

## What it does and doesn't do

Your assistant only **reads** your email, calendar and files. It never sends,
replies, archives, deletes or shares anything; the only thing it does is add
new documents to this folder. To pause it, ask "pause my chief of staff".
