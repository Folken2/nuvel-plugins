#!/usr/bin/env python3
"""Check a new radar document against the radar contract before it is saved.

    python3 check_radar.py [--previous PREVIOUS] NEW

Covers what an unattended run is most likely to get wrong: the header line,
the sections and their order, deadlines written as real dates, the cursors,
secrets or long email text copied into the registry, and every task-ID rule
(check_task_ids.py, run on the same two documents). PREVIOUS and NEW are the
text of two radars (Markdown, or what a storage connector reads back from a
Google Doc). Leave out --previous on the very first radar.

Prints `error: ...` and `warning: ...` lines, then `tasks_new`, `tasks_closed`,
`id_errors` and `result: ok` or `result: failed`. Exit 0 = no errors, 1 =
errors, 2 = bad usage. Standard library only; Python 3.8+. Contract:
references/registry-layout.md (radar run) and references/safety.md.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_task_ids  # noqa: E402  (same folder)

MD_ESCAPE_RE = check_task_ids.MD_ESCAPE_RE
HEADER_RE = re.compile(
    r"^#\s*Radar · (\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}) · (scheduled|interactive) · [^—]+? — (ok|partial|error)\s*$"
)
# In this order. Owner is optional (no name in config); Trace is always last.
SECTIONS = ["Owner", "Journal", "Needs you now", "Decide", "Today", "Open loops", "I owe", "Waiting on",
            "Closed", "Moving", "Watching", "Handoff", "Cursors", "Trace"]
OPTIONAL = {"Owner"}
HEADING_RE = re.compile(r"^\s*(#{2,3})\s*([A-Za-z][A-Za-z ]*?)\s*(\(.*\))?\s*$")
BULLET_RE = re.compile(r"^\s*[-*•]\s+(.*)$")
DUE_RE = re.compile(r"\bdue\b\s*(\S*)")
CURSOR_RE = re.compile(r"^(\w[\w ]*?):\s*(.+?)\s+—\s+(ok|error\b.*)$")
ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?([+-]\d{2}:\d{2}|Z)$")
SECRET_PATTERNS = [
    ("an IBAN", re.compile(r"\b[A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]{4}){3,7}\b")),
    ("a one-time code", re.compile(r"\b(?:code|codi|código|OTP|PIN|verification)\b[^\n\d]{0,20}\b\d{4,8}\b", re.I)),
    ("a password", re.compile(r"\b(?:password|contrasenya|contraseña)\s*[:=]\s*\S+", re.I)),
    ("an API key or token", re.compile(r"\b(?:sk|pk|rk|ghp|gho|xox[abp])[-_][A-Za-z0-9_-]{16,}\b")),
]
CARD_RE = re.compile(r"\b(?:\d[ -]?){13,19}\b")
LONG_BULLET = 400   # characters: summarise and link instead
MAX_LINES = 150
MAX_NEEDS = 5
CLOSE_REASONS = ("done", "not mine", "expired")  # the user's close handoff, or the radar's own `expired`
LOOKS_DONE_RE = re.compile(r"—\s*looks done:\s*(.+)$")
SNOOZED_RE = re.compile(r"—\s*snoozed until\s*(\S+)\s*$")


def luhn(digits: str) -> bool:
    total, alt = 0, False
    for ch in reversed(digits):
        d = int(ch)
        if alt:
            d *= 2
            if d > 9:
                d -= 9
        total += d
        alt = not alt
    return total % 10 == 0


def sections(text: str) -> tuple[list[str], dict[str, list[str]]]:
    order: list[str] = []
    body: dict[str, list[str]] = {}
    cur = None
    for line in text.splitlines():
        m = HEADING_RE.match(line)
        if m and not BULLET_RE.match(line):
            name = m.group(2).strip()
            known = next((s for s in SECTIONS if s.lower() == name.lower()), None)
            if known:
                cur = known
                order.append(known)
                body.setdefault(known, [])
                continue
            cur = None
            continue
        b = BULLET_RE.match(line)
        if cur and b:
            body[cur].append(b.group(1).strip())
    return order, body


def items(lines: list[str]) -> list[str]:
    """Bullets that are items, not notes such as `none` / `Cap.` (same rule as the board and the ID checker)."""
    return [b for b in lines if "—" in b or check_task_ids.TASK_RE.match(b)]


def check(previous: str | None, new: str) -> tuple[list[str], list[str], dict[str, int]]:
    errors: list[str] = []
    warnings: list[str] = []
    raw = new
    text = MD_ESCAPE_RE.sub(r"\1", new)
    lines = [l for l in text.splitlines() if l.strip()]

    # Header
    first = lines[0] if lines else ""
    m = HEADER_RE.match(first.strip())
    if not m:
        errors.append("first line is not '# Radar · YYYY-MM-DD HH:MM · scheduled|interactive · <host> — ok|partial|error'")
    else:
        try:
            dt.datetime.strptime(m.group(1) + " " + m.group(2), "%Y-%m-%d %H:%M")
        except ValueError:
            errors.append(f"header date/time is not real: {m.group(1)} {m.group(2)}")

    # Sections: present, in order, Trace last
    order, body = sections(text)
    missing = [s for s in SECTIONS if s not in order and s not in OPTIONAL]
    if missing:
        errors.append("missing sections: " + ", ".join(missing))
    seen_order = [s for s in SECTIONS if s in order]
    actual = [s for s in order if s in SECTIONS]
    dedup = list(dict.fromkeys(actual))
    if dedup != seen_order:
        errors.append("sections out of order: " + " > ".join(dedup))
    if len(actual) != len(dedup):
        errors.append("a section heading appears twice")
    if order and order[-1] != "Trace":
        errors.append("## Trace must be the last section")

    # Needs you now: at most 5
    needs = items(body.get("Needs you now", []))
    if len(needs) > MAX_NEEDS:
        errors.append(f"Needs you now has {len(needs)} items (max {MAX_NEEDS})")

    # Deadlines are real dates, written `due YYYY-MM-DD`
    for sec in ("Needs you now", "Decide", "I owe", "Waiting on"):
        for b in items(body.get(sec, [])):
            for d in DUE_RE.findall(b):
                d = d.rstrip(".,;)")
                try:
                    dt.date.fromisoformat(d)
                except ValueError:
                    errors.append(f"{sec}: 'due' must be followed by a date YYYY-MM-DD, got {d!r}: {b[:60]!r}")

    # Cursors
    cursors = body.get("Cursors", [])
    for c in cursors:
        if c.startswith("seen:"):
            ids = [x.strip() for x in c[5:].split(",") if x.strip()]
            bad = [x for x in ids if "@" in x or " " in x]
            if bad:
                errors.append(f"seen holds something that is not an opaque id (names, subjects or addresses): {bad[0][:40]!r}")
            continue
        if c.startswith("next_task:"):
            continue
        cm = CURSOR_RE.match(c)
        if not cm:
            warnings.append(f"cursor line not in '<source>: <timestamp> — ok|error: …' form: {c[:60]!r}")
        elif not ISO_RE.match(cm.group(2)):
            errors.append(f"cursor {cm.group(1)} is not an ISO timestamp with offset: {cm.group(2)!r}")
    if not any(re.match(r"^email:", c) for c in cursors):
        warnings.append("Cursors has no email cursor")

    # Safety: secrets never reach the registry; email bodies are summarised, not copied
    for label, rx in SECRET_PATTERNS:
        hit = rx.search(text)
        if hit:
            errors.append(f"looks like {label} was copied into the radar: {hit.group(0)[:24]!r}… (safety.md §3)")
    for hit in CARD_RE.finditer(text):
        digits = re.sub(r"\D", "", hit.group(0))
        if 13 <= len(digits) <= 19 and luhn(digits) and not re.search(r"thread-f:" + digits, raw):
            errors.append(f"looks like a card number was copied into the radar: {digits[:4]}… (safety.md §3)")
            break
    for sec, bullets in body.items():
        for b in bullets:
            if len(b) > LONG_BULLET and sec not in ("Cursors",):
                warnings.append(f"{sec}: a {len(b)}-character line; summarise and link instead of copying: {b[:50]!r}")
    if sum(1 for l in text.splitlines() if l.lstrip().startswith(">")) > 1:
        errors.append("more than one quoted line ('>'): quote at most one line of any email")
    if len(lines) > MAX_LINES:
        warnings.append(f"the radar is {len(lines)} lines (keep it under ~{MAX_LINES}: summarise, drop stale items)")
    for link in re.findall(r"<?(http://[^\s>]+)", text):
        warnings.append(f"plain http link: {link[:60]}")

    # Trace
    trace = body.get("Trace", [])
    if not any(t.startswith(("outcome:", "not sent")) for t in trace):
        errors.append("## Trace must say 'outcome: …' or 'not sent: <reason>'")

    # Human in the loop: the radar never closes a task on evidence, only the user does
    prev_tasks = check_task_ids.parse(previous, "previous").tasks if previous is not None else {}
    cur_tasks = check_task_ids.parse(raw, "new").tasks
    for n, where in sorted(cur_tasks.items()):
        closed_lines = [line for sec, line in where if sec == "Closed"]
        was_closed = any(sec == "Closed" for sec, _ in prev_tasks.get(n, []))
        if closed_lines and not was_closed:
            reason = MD_ESCAPE_RE.sub(r"\1", closed_lines[0]).rsplit("—", 1)[-1].strip().lower()
            if reason not in CLOSE_REASONS:
                errors.append(f"T-{n} closed as {reason!r}: only the user's close handoff (done / not mine) or "
                              "`expired` closes a task; on evidence, mark it `looks done` instead")
        for sec, line in where:
            m = LOOKS_DONE_RE.search(MD_ESCAPE_RE.sub(r"\1", line))
            if m and not re.search(r"\(\d{4}-\d{2}-\d{2}\)", m.group(1)):
                warnings.append(f"T-{n}: `looks done` should say when, as (YYYY-MM-DD), and link the evidence")
            if m and sec == "Closed":
                errors.append(f"T-{n} is in Closed and marked `looks done`: a closed task needs no mark")
            s = SNOOZED_RE.search(MD_ESCAPE_RE.sub(r"\1", line))
            if s:
                try:
                    dt.date.fromisoformat(s.group(1))
                except ValueError:
                    errors.append(f"T-{n}: `snoozed until` must be followed by a date YYYY-MM-DD, got {s.group(1)!r}")
                if sec == "Needs you now":
                    errors.append(f"T-{n} is snoozed: it stays out of Needs you now until its date")

    # Task IDs
    id_errors, id_warnings, counts = check_task_ids.check(previous, raw)
    errors += id_errors
    warnings += id_warnings
    counts = dict(counts)
    counts["id_errors"] = len(id_errors)
    return errors, warnings, counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--previous", type=Path, help="text of the previous radar (leave out on the first radar)")
    parser.add_argument("new", type=Path, help="text of the new radar, before it is saved")
    args = parser.parse_args(argv)
    try:
        previous = args.previous.read_text(encoding="utf-8") if args.previous else None
        new = args.new.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    errors, warnings, counts = check(previous, new)
    for line in errors:
        print(f"error: {line}")
    for line in warnings:
        print(f"warning: {line}")
    for key, value in counts.items():
        print(f"{key}: {value}")
    print("result: failed" if errors else "result: ok")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
