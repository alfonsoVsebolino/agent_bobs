"""
log_hook.py — passive audit hook for Agent Bobs.

Fires on every Bob lifecycle event (PreToolUse, Stop, SessionStart).

For every event:
  - Reads the JSON envelope Bob sends on stdin.
  - Appends one timestamped JSON line to hooklog.jsonl (sibling of this file).

For PreToolUse events that carry a file path:
  - Calls POST /api/check (read-only) on the Agent Bobs server.
  - Records _would_conflict (true/false) and _conflict_detail in the log line,
    giving a per-tool-call audit trail of cross-agent risk.
  - If the server is unreachable, those two keys are omitted (fail open).

For SessionStart events:
  - Prints "Your Agent Bobs session name is test" to stdout so Bob injects
    it into the session context.

Never exits with code 2 — never blocks a write.
Stdlib only. Works on Linux, macOS, and Windows.
"""

from __future__ import annotations

import datetime
import json
import os
import sys
import urllib.error
import urllib.request


SERVER_CHECK_URL = "http://127.0.0.1:8765/api/check"

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


def _extract_path(event: dict) -> str | None:
    """Extract the file path from a PreToolUse event envelope, if present."""
    tool_input = event.get("input") or event.get("tool_input") or {}
    return (
        tool_input.get("path")
        or tool_input.get("file_path")
        or tool_input.get("file_name")
    )


def _check_conflict(session: str, path: str) -> dict | None:
    """Call /api/check and return the parsed response, or None if unreachable."""
    body = json.dumps({"session": session, "files": [path]}).encode()
    req = urllib.request.Request(
        SERVER_CHECK_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read())
    except Exception:
        return None


def main() -> None:
    try:
        raw = sys.stdin.read()
        try:
            event = json.loads(raw)
        except Exception:
            event = {"_parse_error": True, "_raw": raw[:200]}

        session = _session_name()
        ts = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")

        # Build the log record from the original event, injecting metadata.
        record: dict = {**event, "_ts": ts, "_session": session}

        hook_event = event.get("hook_event_name", "")

        # --- PreToolUse: probe for conflicts ---
        if hook_event == "PreToolUse":
            path = _extract_path(event)
            if path:
                result = _check_conflict(session, path)
                if result is not None:
                    record["_would_conflict"] = not result.get("clear", True)
                    if record["_would_conflict"]:
                        record["_conflict_detail"] = result.get("conflict")

        # --- SessionStart: announce session name to Bob's context ---
        if hook_event == "SessionStart":
            print("Your Agent Bobs session name is test")

        # --- Append to log ---
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")

    except Exception:
        # Any unhandled error must not interfere with Bob.
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
