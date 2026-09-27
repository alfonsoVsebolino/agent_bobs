"""
release_hook.py — Stop hook for Agent Bobs.

Bob calls this when the agent stops (task complete or abandoned).  The hook:
  1. Reads the JSON event from stdin and appends it (with timestamp) to
     .bob/hooks/hooklog.jsonl.
  2. POSTs to /api/release so the server removes this session and un-blocks any
     session that was waiting on a conflict with it.

Stdlib only.  Works on Linux, macOS, and Windows.
"""

from __future__ import annotations

import datetime
import json
import os
import sys
import urllib.error
import urllib.request


SERVER_URL = "http://127.0.0.1:8765/api/release"

LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hooklog.jsonl")


def _session_name() -> str:
    basename = os.path.basename(os.getcwd())
    if basename.startswith("demo-"):
        return basename[len("demo-"):]
    return basename


def _log(event: dict) -> None:
    """Append one JSON line to hooklog.jsonl."""
    record = {
        **event,
        "_ts": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
        "_session": _session_name(),
    }
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")
    except Exception:
        pass  # never let a logging failure interfere


def main() -> None:
    # Read and log the event Bob sends on stdin.
    try:
        event = json.load(sys.stdin)
    except Exception:
        event = {}
    _log(event)

    session = _session_name()

    body = json.dumps({"session": session}).encode()
    req = urllib.request.Request(
        SERVER_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=5):
            pass
    except Exception:
        # Server not running or error — nothing to do, exit cleanly.
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
