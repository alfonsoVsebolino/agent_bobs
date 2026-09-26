"""
claim_hook.py — PreToolUse hook for Agent Bobs.

Bob calls this before every file-editing tool.  The hook reads the JSON event
from stdin, extracts the file path, and POSTs to /api/claim on the Agent Bobs
server.  If the server returns clear=false (conflict), the hook exits with code
2, which tells Bob to refuse the write.

Stdlib only.  Works on Linux, macOS, and Windows.

Session identity
----------------
The session name is derived from the workspace folder name: a folder called
demo-aig gives session name "aig".  The hook reads the cwd at runtime so that
three copies of demo/ each get their own name automatically.

NOTE: tool-name coverage
The PreToolUse matcher in settings.json has no matcher filter, so this hook
fires for EVERY tool call.  For non-file-editing tools the event will either
have no "path" key in input, or the file will not conflict — both are handled
gracefully (the hook exits 0 and Bob continues).

Known file-editing tool names (verify with hooklog.jsonl probe):
  write_file, str_replace_based_edit_tool, create_file, apply_diff,
  insert_content, search_and_replace
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request


SERVER_URL = "http://127.0.0.1:8765/api/claim"


def _session_name() -> str:
    """Derive session name from the current working directory basename.

    demo-aig  →  aig
    demo-jay  →  jay
    If the folder does not match the pattern, fall back to the full basename.
    """
    basename = os.path.basename(os.getcwd())
    if basename.startswith("demo-"):
        return basename[len("demo-"):]
    return basename


def _rel_path(raw: str) -> str:
    """Return a repo-relative forward-slash path."""
    try:
        rel = os.path.relpath(raw, os.getcwd())
    except ValueError:
        # On Windows, relpath fails across drives — use raw path as-is.
        rel = raw
    return rel.replace("\\", "/")


def main() -> None:
    # Read the JSON event Bob sends on stdin.
    try:
        event = json.load(sys.stdin)
    except Exception:
        # Unparseable input — let Bob continue.
        sys.exit(0)

    # Extract the file path from the tool input.
    tool_input = event.get("input") or event.get("tool_input") or {}
    path = (
        tool_input.get("path")
        or tool_input.get("file_path")
        or tool_input.get("file_name")
    )

    if not path:
        # Not a file-editing event (or no path declared) — nothing to claim.
        sys.exit(0)

    session = _session_name()
    rel = _rel_path(path)

    body = json.dumps({"session": session, "files": [rel]}).encode()
    req = urllib.request.Request(
        SERVER_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read())
    except urllib.error.URLError:
        # Server not running — let Bob continue (fail open so dev work isn't blocked).
        sys.exit(0)
    except Exception:
        sys.exit(0)

    if not result.get("clear", True):
        conflict = result.get("conflict") or {}
        reason = conflict.get("reason", "conflict detected")
        other = conflict.get("with", "another session")
        # Print to stderr — Bob shows this message when it blocks the write.
        print(
            f"[Agent Bobs] BLOCKED — {reason} (conflict with session '{other}')",
            file=sys.stderr,
        )
        sys.exit(2)  # exit 2 tells Bob to refuse the write

    sys.exit(0)


if __name__ == "__main__":
    main()
