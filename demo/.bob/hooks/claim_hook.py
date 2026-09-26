"""
claim_hook.py — PreToolUse hook for Agent Bobs.

Bob calls this before every tool.  The hook:
  1. Reads the JSON event from stdin and appends it (with timestamp) to
     .bob/hooks/hooklog.jsonl — always, for every tool.
  2. If the tool is in WRITE_TOOLS, extracts the file path and POSTs to
     /api/claim.  If the server returns clear=false, exits with code 2 so
     Bob refuses the write.
  3. For every other tool, exits 0 immediately after logging.

Stdlib only.  Works on Linux, macOS, and Windows.

Session identity
----------------
The session name is derived from the workspace folder name: a folder called
demo-aig gives session name "aig".  The hook reads the cwd at runtime so that
three copies of demo/ each get their own name automatically.
"""

from __future__ import annotations

import datetime
import json
import os
import sys
import urllib.error
import urllib.request


# ---------------------------------------------------------------------------
# Tools that write, edit, create, or delete a file.
# Only these trigger a /api/claim call and a potential exit-2 block.
# Read this list aloud to the user when they ask which tools change files.
# ---------------------------------------------------------------------------
WRITE_TOOLS = {
    "write_file",
    "str_replace_based_edit_tool",
    "create_file",
    "apply_diff",
    "insert_content",
    "search_and_replace",
    # Bob sometimes uses these aliases — keep both spellings:
    "str_replace_editor",
    "edit_file",
}

SERVER_URL = "http://127.0.0.1:8765/api/claim"

LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hooklog.jsonl")


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


def _log(event: dict, extra: dict | None = None) -> None:
    """Append one JSON line to hooklog.jsonl."""
    record = {
        **event,
        "_ts": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
        "_session": _session_name(),
    }
    if extra:
        record.update(extra)
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")
    except Exception:
        pass  # never let a logging failure block Bob


def main() -> None:
    # Read the JSON event Bob sends on stdin.
    try:
        event = json.load(sys.stdin)
    except Exception:
        # Unparseable input — let Bob continue.
        sys.exit(0)

    # Always log the raw event first.
    _log(event)

    # Only proceed to claim if this is a file-writing tool.
    tool_name = event.get("tool_name") or event.get("name") or ""
    if tool_name not in WRITE_TOOLS:
        sys.exit(0)

    # Extract the file path from the tool input.
    tool_input = event.get("input") or event.get("tool_input") or {}
    path = (
        tool_input.get("path")
        or tool_input.get("file_path")
        or tool_input.get("file_name")
    )

    if not path:
        # Write tool but no path declared — nothing to claim.
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
        # The hook message goes to Bob's log; the rules.md tells Bob to surface
        # the conflict to the user by calling `check` and reporting who holds it.
        print(
            f"[Agent Bobs] BLOCKED — {reason} (conflict with session '{other}')",
            file=sys.stderr,
        )
        sys.exit(2)  # exit 2 tells Bob to refuse the write

    sys.exit(0)


if __name__ == "__main__":
    main()
