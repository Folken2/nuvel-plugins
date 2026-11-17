# Chief of staff configuration

  - version: 1
  - paused: false
  - owner.name: Ana Ferrer
  - owner.role: Managing director
  - owner.timezone: Europe/Madrid
  - owner.language: ca
  - owner.working\_hours: 09:00-19:00 Mon-Fri
  - storage.kind: google-drive
  - storage.root: 1RootFolderExample000000000
  - storage.folders: config=1ConfigFolderExample0000, runs=1Runs\_Folder\_Example0000, handoff=1HandoffFolderExample000, lessons=1LessonsFolderExample000, recipes=1RecipesFolderExample000
  - quiet\_hours: 20:00-08:00
  - notify: needs-you-now
  - telemetry: on

## Priorities
1. Close the Acme renewal </script><script>alert(1)</script>

## Sources
  - email: connector Gmail (<ana@example.com>) — inbox + enviats
  - calendar: Google Calendar connector — primary
  - chat: none

## Routines
  - radar: cowork — every 2 h 08-20 Mon-Fri — manual
