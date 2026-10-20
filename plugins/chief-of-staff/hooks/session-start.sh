#!/usr/bin/env bash
# Prints a short registry summary for the main agent. Never fails the session:
# any problem (no python, no registry, unreadable files) means "print nothing".
[ "${CHIEF_OF_STAFF_HOOK:-on}" = "off" ] && exit 0
command -v python3 >/dev/null 2>&1 || exit 0
python3 -I "$(dirname "$0")/session_start.py" 2>/dev/null || true
exit 0
