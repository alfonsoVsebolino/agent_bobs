"""
state.py — the single source of truth for all session data.

All mutation goes through claim() and release().  The MCP tools and /api
routes call only these two functions; no claim logic lives anywhere else.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Path normalisation
# ---------------------------------------------------------------------------

def normalise_path(path: str) -> str:
    """Return a canonical, comparable path string.

    Rules:
    - Backslashes → forward slashes
    - Strip a leading ./
    - Lowercase  (Windows paths are case-insensitive; the server runs on
                  Windows in the demo, so we always lowercase)
    """
    p = path.replace("\\", "/")
    if p.startswith("./"):
        p = p[2:]
    return p.lower()


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class SessionRecord:
    session: str
    files: list[str] = field(default_factory=list)
    symbols: list[str] = field(default_factory=list)
    calls: list[str] = field(default_factory=list)
    status: str = "working"            # "working" | "blocked"
    conflict: Optional[dict] = None    # None or {"with", "reason", "type"}

    def to_dict(self) -> dict:
        return {
            "session": self.session,
            "files": list(self.files),
            "symbols": list(self.symbols),
            "calls": list(self.calls),
            "status": self.status,
            "conflict": self.conflict,
        }


# ---------------------------------------------------------------------------
# Shared state
# ---------------------------------------------------------------------------

STATE: dict[str, SessionRecord] = {}
_LOCK = threading.Lock()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def claim(
    session_id: str,
    files: list[str],
    symbols: list[str],
    calls: list[str],
) -> dict:
    """Check for a conflict and record the claim atomically.

    Claims accumulate: new files/symbols/calls are *added* to the session's
    existing sets, never replaced.

    Returns {"clear": True, "conflict": None} on success.
    Returns {"clear": False, "conflict": {...}} on conflict; the new claimant
    is recorded with status "blocked".  The existing holder stays "working"
    but gets its conflict field set so its dashboard column turns red.
    A clear claim never clears a conflict already on the session — only
    release() does that.
    """
    from .collision import detect  # local import avoids circular at module level

    with _LOCK:
        # Build the candidate's accumulated sets by merging with any existing record.
        existing = STATE.get(session_id)
        acc_files   = list(existing.files)   if existing else []
        acc_symbols = list(existing.symbols) if existing else []
        acc_calls   = list(existing.calls)   if existing else []

        # Accumulate new items (no duplicates needed for correctness, but keep clean).
        seen_f = set(normalise_path(f) for f in acc_files)
        for f in files:
            nf = normalise_path(f)
            if nf not in seen_f:
                acc_files.append(f)
                seen_f.add(nf)

        seen_s = set(s.lower() for s in acc_symbols)
        for s in symbols:
            if s.lower() not in seen_s:
                acc_symbols.append(s)
                seen_s.add(s.lower())

        seen_c = set(c.lower() for c in acc_calls)
        for c in calls:
            if c.lower() not in seen_c:
                acc_calls.append(c)
                seen_c.add(c.lower())

        conflict_info = detect(
            session_id, acc_files, acc_symbols, acc_calls, STATE
        )

        # Determine the conflict and status for the new claimant.
        # On a clear claim, preserve any existing conflict already on the
        # session — conflicts are only cleared by release().
        if conflict_info:
            new_status = "blocked"
            new_conflict = conflict_info
        else:
            new_status = existing.status   if existing else "working"
            new_conflict = existing.conflict if existing else None

        record = SessionRecord(
            session=session_id,
            files=acc_files,
            symbols=acc_symbols,
            calls=acc_calls,
            status=new_status,
            conflict=new_conflict,
        )
        STATE[session_id] = record

        if conflict_info:
            # Set the conflict field on the other (holder) session so its
            # dashboard column turns red, but leave its status as "working" —
            # only the new claimant is blocked.
            other_id = conflict_info["with"]
            if other_id in STATE:
                other = STATE[other_id]
                if other.conflict is None:
                    other.conflict = {
                        "with": session_id,
                        "reason": conflict_info["reason"],
                        "type": conflict_info["type"],
                    }
                # other.status intentionally NOT changed — holder stays "working"

            return {"clear": False, "conflict": conflict_info}

        return {"clear": True, "conflict": None}


def release(session_id: str) -> None:
    """Remove a session and un-block any session that was blocked by it."""
    with _LOCK:
        STATE.pop(session_id, None)

        # Clear conflicts that pointed at the released session.
        for rec in STATE.values():
            if rec.conflict and rec.conflict.get("with") == session_id:
                rec.conflict = None
                rec.status = "working"


def get_snapshot() -> list[dict]:
    """Return a list of all session records as plain dicts (for WebSocket)."""
    with _LOCK:
        return [rec.to_dict() for rec in STATE.values()]
