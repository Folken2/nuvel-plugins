# Scheduling: making the routines run by themselves

The chief of staff is only useful if radar runs without the user remembering to
ask. Each host schedules differently; pick the first mechanism that exists in the
current environment, create the routine **after the user confirms**, and record
it under `routines` in `config.md` (mechanism + ID/name) so it can be edited or
removed later.

## Default routines

| Routine | When (user's timezone) | Prompt |
|---|---|---|
| radar | Every 2 h, 08:00–20:00, Mon–Fri | `Run the chief-of-staff radar skill.` |
| brief | 07:30, Mon–Fri | `Run the chief-of-staff brief skill.` |
| weekly-review | Friday 16:00 | `Run the chief-of-staff weekly-review skill.` |

Every routine prompt ends with the registry location so a clean session can find
it (see `registry-layout.md` → *Finding the registry*), e.g.
`Run the chief-of-staff radar skill. Registry: synced-folder /Users/ana/Library/CloudStorage/OneDrive-Acme/Chief of Staff`.
The short prompts below omit it for readability.

Offer these defaults, then let the user change hours, days or frequency. As an
RRULE (used by Codex automations and most calendar-style schedulers):

```
radar:  FREQ=HOURLY;INTERVAL=2;BYDAY=MO,TU,WE,TH,FR;BYHOUR=8,10,12,14,16,18,20;BYMINUTE=0
brief:  FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR;BYHOUR=7;BYMINUTE=30
review: FREQ=WEEKLY;BYDAY=FR;BYHOUR=16;BYMINUTE=0
```

As cron (UTC offsets are the scheduler's business — check whether it uses local
time or UTC and convert):

```
radar:  0 8-20/2 * * 1-5
brief:  30 7 * * 1-5
review: 0 16 * * 5
```

## Claude

| Where Claude runs | Mechanism | Can it reach a synced folder? |
|---|---|---|
| Claude desktop app (Code or Cowork) | **Scheduled tasks** — use the host's schedule skill or scheduled-tasks tools if present; otherwise tell the user to open *Scheduled* in the sidebar and paste the prompt | Yes, the task runs on this computer |
| Claude Code CLI / web | **Routines** (`/schedule`) — cloud runs on a cron schedule, with the account's claude.ai connectors | No — needs connector storage (`storage.md` option 2) |
| Any long-lived session | `/loop 2h <prompt>` — only while that session stays open; good for trying it out, not for real use | Yes |
| Headless fallback | OS scheduler (cron / launchd / Task Scheduler) running `claude -p "Run the chief-of-staff radar skill."` | Yes |

Notes:
- Routines and scheduled tasks start from a clean session. That is fine: every
  skill begins by reading `config.md` and `.state/radar.json` from the registry.
- A headless run cannot answer permission prompts. Give it only what radar needs
  (read tools for the sources, write access to `storage.root`) through the
  host's allowed-tools / permission settings — never a blanket "skip
  permissions" flag. Show the user the exact command before installing it.

## Codex

| Where Codex runs | Mechanism | Can it reach a synced folder? |
|---|---|---|
| Codex app | **Automations** — a scheduled prompt (RRULE) that runs in a thread. If an automation-creation tool is available, use it; otherwise tell the user to create one from *Automations* and paste the name, prompt and schedule above | Yes, runs on this computer |
| Codex cloud tasks | Not suited to recurring radar unless connectors provide storage | Only with connector storage |
| Headless fallback | OS scheduler running `codex exec "Run the chief-of-staff radar skill."` | Yes |

Codex invokes plugin skills as `$radar`, `$brief`, … — prompts in plain language
("Run the chief-of-staff radar skill.") work in both hosts, so prefer them.

## OS scheduler snippets (fallback)

Only offer these when no host scheduler exists, and show the full snippet first.

macOS (launchd) — `~/Library/LaunchAgents/ai.nuvel.chief-of-staff.radar.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>ai.nuvel.chief-of-staff.radar</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/zsh</string><string>-lc</string>
    <string>claude -p "Run the chief-of-staff radar skill."</string>
  </array>
  <key>StartCalendarInterval</key>
  <array>
    <!-- one dict per run: Weekday 1-5, Hour 8,10,…,20, Minute 0 -->
    <dict><key>Weekday</key><integer>1</integer><key>Hour</key><integer>8</integer><key>Minute</key><integer>0</integer></dict>
  </array>
  <key>StandardErrorPath</key><string>/tmp/chief-of-staff-radar.err</string>
</dict>
</plist>
```

Load with `launchctl load ~/Library/LaunchAgents/ai.nuvel.chief-of-staff.radar.plist`.

Linux / macOS cron — `crontab -e`:

```
0 8-20/2 * * 1-5  claude -p "Run the chief-of-staff radar skill." >> ~/.chief-of-staff-radar.log 2>&1
```

Windows Task Scheduler:

```
schtasks /Create /TN "ChiefOfStaff Radar" /SC HOURLY /MO 2 /ST 08:00 /ET 20:00 /TR "claude -p \"Run the chief-of-staff radar skill.\""
```

Swap `claude -p` for `codex exec` when the user runs Codex.

## Changing or stopping routines

Read `routines` in `config.md`, change or remove it through the same mechanism
that created it, then update `config.md`. If the mechanism is a UI the agent
cannot reach, tell the user exactly where to click and what to change.
