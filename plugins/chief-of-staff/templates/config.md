---
version: 1
paused: false
owner:
  name: ""
  role: ""
  organisation: ""
  timezone: ""          # IANA, e.g. Europe/Madrid
  language: ""          # e.g. es, en
  working_hours: "09:00-19:00"
storage:
  kind: ""              # synced-folder | google-drive | onedrive | sharepoint | local
  root: ""              # absolute path, or folder ID / URL for connector storage
  format: md            # md | gdoc
  ids: {}               # connector storage only: file name -> file ID
sources: []             # - {kind: email, via: "<tool or connector>", scope: "inbox + sent"}
vips: []                # - {name: "", email: "", why: ""}
priorities: []          # 3-5 things that matter this quarter
sensitive_topics: []    # extra topics never copied into the registry
quiet_hours: "20:00-08:00"
notify: needs-you-now   # needs-you-now | never
routines: []            # - {name: radar, mechanism: "", id: "", schedule: ""}
---

# How I work

<!-- Free text the chief of staff reads before every run. Examples: who covers
for you, which clients are sensitive, how you like briefs written, what to
ignore. -->
