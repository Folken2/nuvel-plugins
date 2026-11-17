#!/usr/bin/env python3
"""Check the task IDs of a new radar against the previous one.

    python3 check_task_ids.py [--previous PREVIOUS] NEW

PREVIOUS and NEW are the text of two radar documents (Markdown, or the plain
text a storage connector returns for a Google Doc). Leave out --previous on
the very first radar. Standard library only; Python 3.8+.

Prints one line per problem (`error: ...`, `warning: ...`), then the counts
the radar trace needs (`tasks_new`, `tasks_closed`) and `result: ok` or
`result: failed`. Exit code 0 = no errors (warnings allowed), 1 = errors,
2 = bad usage. The rules are *Task IDs* in references/registry-layout.md.
It checks numbering only; whether two items are the same task is the radar's
judgement.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

OPEN_SECTIONS = ("Needs you now", "Decide", "I owe", "Waiting on", "Watching")
TASK_SECTIONS = OPEN_SECTIONS + ("Closed",)
OTHER_SECTIONS = ("Owner", "Journal", "Today", "Open loops", "Moving", "Handoff", "Cursors", "Trace")

HEADING_RE = re.compile(r"^\s*#{0,6}\s*(?P<name>[A-Za-z][A-Za-z ]*?)\s*(\(.*\))?\s*$")
BULLET_RE = re.compile(r"^\s*[-*•]\s+(?P<body>.*)$")
TASK_RE = re.compile(r"^T-(?P<n>[1-9]\d*)\s+—\s+(?P<rest>.*)$")
LOOSE_ID_RE = re.compile(r"^T\s*-?\s*0*\d+\b")
NEXT_RE = re.compile(r"^\s*[-*•]\s+next_task:\s*T-(?P<n>[1-9]\d*)\s*$", re.MULTILINE)
LINK_RE = re.compile(r"https?://[^\s)>\]]+")


@dataclass
class Radar:
    # id -> list of (section, line)
    tasks: dict[int, list[tuple[str, str]]] = field(default_factory=dict)
    next_task: int | None = None
    problems: list[str] = field(default_factory=list)

    @property
    def open_ids(self) -> set[int]:
        return {i for i, where in self.tasks.items() if any(s != "Closed" for s, _ in where)}

    @property
    def closed_ids(self) -> set[int]:
        return {i for i, where in self.tasks.items() if all(s == "Closed" for s, _ in where)}

    def links(self, n: int) -> set[str]:
        return {link for _, line in self.tasks.get(n, []) for link in LINK_RE.findall(line)}


def _section_of(line: str) -> str | None:
    m = HEADING_RE.match(line)
    if not m or BULLET_RE.match(line):
        return None
    name = m.group("name").strip()
    for known in TASK_SECTIONS + OTHER_SECTIONS:
        if name.lower() == known.lower():
            return known
    return None


def parse(text: str, label: str) -> Radar:
    radar = Radar()
    section = None
    for raw in text.splitlines():
        heading = _section_of(raw)
        if heading:
            section = heading
            continue
        if section not in TASK_SECTIONS:
            continue
        bullet = BULLET_RE.match(raw)
        if not bullet:
            continue
        body = bullet.group("body").strip()
        task = TASK_RE.match(body)
        if task:
            radar.tasks.setdefault(int(task.group("n")), []).append((section, body))
        elif LOOSE_ID_RE.match(body):
            radar.problems.append(f"{label}: malformed task ID in {section}: {body[:60]!r} (expected 'T-<n> — ')")
        elif "—" in body:
            radar.problems.append(f"{label}: item without a task ID in {section}: {body[:60]!r}")
        # A bullet with no "—" is a note such as "none", not an item.
    m = NEXT_RE.search(text)
    radar.next_task = int(m.group("n")) if m else None
    return radar


def check(previous: str | None, new: str) -> tuple[list[str], list[str], dict[str, int]]:
    errors: list[str] = []
    warnings: list[str] = []
    cur = parse(new, "new radar")
    errors += cur.problems

    # The new radar on its own.
    for n, where in sorted(cur.tasks.items()):
        sections = [s for s, _ in where]
        dupes = {s for s in sections if sections.count(s) > 1}
        if dupes:
            errors.append(f"T-{n} is listed twice in {', '.join(sorted(dupes))}")
        distinct = set(sections)
        if "Closed" in distinct and len(distinct) > 1:
            errors.append(f"T-{n} is both closed and open ({', '.join(sorted(distinct - {'Closed'}))})")
        others = distinct - {"Needs you now", "Closed"}  # Needs you now may repeat one loop line
        if len(others) > 1:
            errors.append(f"T-{n} is in more than one section: {', '.join(sorted(others))}")
    if cur.next_task is None:
        errors.append("new radar has no '- next_task: T-<n>' in Cursors")
    elif cur.tasks and cur.next_task <= max(cur.tasks):
        errors.append(f"next_task T-{cur.next_task} is not above the highest ID T-{max(cur.tasks)}")

    # Against the previous radar.
    prev = parse(previous, "previous radar") if previous is not None else Radar()
    if prev.tasks or prev.next_task is not None:
        warnings += prev.problems  # a radar from before task IDs has none, by design
        floor = max(prev.next_task or 1, (max(prev.tasks) + 1) if prev.tasks else 1)
    else:
        floor = 1  # first radar, or a radar from before task IDs: number from T-1
    new_ids = sorted(set(cur.tasks) - set(prev.tasks))

    for n in new_ids:
        if n < floor:
            errors.append(f"T-{n} was given out before (below T-{floor}) and is not in the previous radar: IDs are never reused")
    fresh = [n for n in new_ids if n >= floor]
    expected = list(range(floor, floor + len(fresh)))
    if fresh != expected:
        want = f"T-{expected[0]}…T-{expected[-1]}" if expected else "none"
        errors.append(f"new IDs {', '.join(f'T-{n}' for n in fresh)} skip numbers: expected {want}")
    if cur.next_task is not None and fresh == expected and cur.next_task != floor + len(fresh):
        errors.append(f"next_task is T-{cur.next_task}, expected T-{floor + len(fresh)}")

    for n in sorted(prev.open_ids - set(cur.tasks)):
        errors.append(f"T-{n} was open and is gone: close it (Closed — done | not mine | resolved | expired) instead of dropping it")
    for n in sorted(prev.closed_ids & cur.open_ids):
        warnings.append(f"T-{n} was closed and is open again")

    # Renumbering / missed matches: a new ID pointing at the same source as a carried one.
    for n in fresh:
        for m in sorted(prev.tasks):
            shared = cur.links(n) & prev.links(m)
            if shared:
                warnings.append(f"T-{n} has the same link as T-{m}: same task? ({sorted(shared)[0][:60]})")

    counts = {
        "tasks_new": len(new_ids),
        "tasks_closed": len(cur.closed_ids - prev.closed_ids),
    }
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
