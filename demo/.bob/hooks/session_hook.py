"""
session_hook.py — SessionStart hook for Agent Bobs.

Bob calls this at the start of every session.  The hook prints the session
name to stdout so it appears in Bob's context — Bob will then know its own
session_id without being told manually.

Stdlib only.  Works on Linux, macOS, and Windows.

Session identity: derived from the cwd basename.
  demo-aig  →  session name is "aig"
  demo-jay  →  session name is "jay"
"""

from __future__ import annotations

import json
import os
import sys


def _session_name() -> str:
    basename = os.path.basename(os.getcwd())
    if basename.startswith("demo-"):
        return basename[len("demo-"):]
    return basename


def main() -> None:
    # Read stdin so Bob doesn't get a broken pipe, even though we don't need it.
    try:
        json.load(sys.stdin)
    except Exception:
        pass

    session = _session_name()
    # This output goes to Bob's context via the SessionStart hook mechanism.
    print(f"Your Agent Bobs session name is {session}")
    sys.exit(0)


if __name__ == "__main__":
    main()
