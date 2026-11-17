# Chief of staff configuration

- version: 1
- paused: false
- owner.name: Ana Ferrer
- owner.role: Managing director
- owner.timezone: Europe/Madrid
- owner.language: ca
- owner.working_hours: 09:00-19:00 Mon-Fri
- storage.kind: onedrive
- storage.root: 1RootFolderExample000000000
- storage.folders: config=1ConfigFolderExample0000, runs=1RunsFolderExample000000, handoff=1HandoffFolderExample000, lessons=1LessonsFolderExample000, recipes=1RecipesFolderExample000
- quiet_hours: 20:00-08:00
- notify: needs-you-now
- telemetry: on

## Priorities
1. Close the Acme renewal </script><script>alert(1)</script>

## Sources
- email: Gmail connector — inbox and sent
- calendar: Google Calendar connector — primary
- chat: none

## Routines
- radar: cowork — every 2 h 08-20 Mon-Fri — manual
