---
type: regex
target: {source: file, path: "registry/runs/2026-11/2026-11-18 0907 radar.md"}
pattern: 'next_task: T-(9|1[0-9])'
match: contains
weight: 1
---
The radar added at least two new tasks after T-6, so next_task is T-9 or more.
