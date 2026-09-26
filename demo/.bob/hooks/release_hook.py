"""
release_hook.py — Stop hook for Agent Bobs.

Bob calls this when the agent stops (task complete or abandoned).  The hook
POSTs to /api/release so the server removes this session and un-blocks any
session that was waiting on a conflict with it.

Stdlib only.  Works on Linux, macOS, and Windows.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request


SERVER_URL = "http://127.0.0.1:8765/api/release"


def _session_name() -> str:
    basename = os.path.basename(os.getcwd())
    if basename.startswith("demo-"):
        return basename[len("demo-"):]
    return basename


def main() -> None:
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
