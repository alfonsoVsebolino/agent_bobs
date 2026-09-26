"""
mcp_tools.py — FastMCP 4 tools for the agent-bobs coordination server.

Three tools are registered:
  claim   — declare files/symbols/calls and detect conflicts (records state)
  check   — same detection but records nothing (read-only probe)
  release — remove a session and unblock anything it was blocking

Bob reads the tool docstrings to decide when to call each one.
All state lives in state.py; broadcast() lives in api.py.
"""

from __future__ import annotations

from fastmcp import FastMCP

from .state import claim as _claim, check as _check, release as _release, get_snapshot

mcp = FastMCP("agent-bobs")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _broadcast_after_change() -> None:
    """Import broadcast lazily to avoid a circular import at module load time."""
    from .api import broadcast  # noqa: PLC0415
    await broadcast(get_snapshot())


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool
async def claim(
    session_id: str,
    files: list[str],
    symbols: list[str] = [],
    calls: list[str] = [],
) -> dict:
    """Declare what this session will touch and check for conflicts atomically.

    Call this BEFORE writing any file or changing any function.  Pass:
      session_id — the Agent Bobs session name you were given at the start of
                   the session (for example "aig").  Always pass that same
                   name; never invent one.
      files      — every file you plan to edit.
      symbols    — every function you will change in any way: rename it,
                   delete it, change its parameters, change its return type,
                   or change its behaviour.  A changed signature breaks callers
                   just as a rename does, so it must be declared here.
      calls      — every function you will call but not change.

    Claims accumulate across calls — later claims ADD to the session's sets,
    they never replace them.  This means you can call claim() once per file
    as you discover what you need to touch.

    Returns {"clear": true, "conflict": null} when no other session conflicts.
    Returns {"clear": false, "conflict": {"with": <session>, "reason": <str>,
             "type": "same_file" | "same_function"}} when a conflict exists.
    On a conflict, STOP and tell the user — do not proceed with the edit.

    Two conflict types:
      same_file     — another session has already claimed the same file.
      same_function — one session is changing a function the other calls or
                      also changes.
    """
    result = _claim(session_id, files, symbols, calls)
    await _broadcast_after_change()
    return result


@mcp.tool
async def check(
    session_id: str,
    files: list[str],
    symbols: list[str] = [],
    calls: list[str] = [],
) -> dict:
    """Read-only conflict probe — same detection as claim(), but records nothing.

    Use this when you want to know whether a planned set of changes would
    conflict with another session WITHOUT committing to those changes yet.

    session_id — the Agent Bobs session name you were given at the start of
                 the session (for example "aig").  Always pass that same
                 name; never invent one.

    The STATE dict is never mutated.  Safe to call at any time.

    Returns {"clear": true, "conflict": null} if no conflict would result.
    Returns {"clear": false, "conflict": {...}} if a conflict would exist.
    """
    return _check(session_id, files, symbols, calls)


@mcp.tool
async def release(session_id: str) -> dict:
    """Remove this session and unblock any session that was waiting on it.

    session_id — the Agent Bobs session name you were given at the start of
                 the session (for example "aig").  Always pass that same
                 name; never invent one.

    Call this when your work is done (or abandoned).  After release, other
    sessions that were blocked because of a conflict with this session will
    automatically return to "working" status.

    Returns {"ok": true}.
    """
    _release(session_id)
    await _broadcast_after_change()
    return {"ok": True}
