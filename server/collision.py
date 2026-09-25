"""
collision.py — pure, side-effect-free collision detection.

detect() takes a candidate and the current STATE snapshot and returns a
ConflictInfo dict or None.  It never mutates anything.

Truth table
-----------
Session A has  | Session B has  | Conflict?
---------------|----------------|----------
symbol X       | symbol X       | yes (same_function)
symbol X       | calls X        | yes (same_function)
calls X        | symbol X       | yes (same_function)
calls X        | calls X        | no
file F         | file F         | yes (same_file)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .state import normalise_path

if TYPE_CHECKING:
    from .state import SessionRecord


def detect(
    candidate_id: str,
    candidate_files: list[str],
    candidate_symbols: list[str],
    candidate_calls: list[str],
    state: dict[str, "SessionRecord"],
) -> dict | None:
    """Return a ConflictInfo dict, or None if there is no conflict.

    Only checks against sessions whose status is "working".
    A session never conflicts with itself.
    same_file is checked first; same_function second.
    """
    norm_files   = {normalise_path(f) for f in candidate_files}
    lower_syms   = {s.lower() for s in candidate_symbols}
    lower_calls  = {c.lower() for c in candidate_calls}

    for sid, rec in state.items():
        if sid == candidate_id:
            continue
        if rec.status != "working":
            continue

        # --- same_file -------------------------------------------------------
        other_files = {normalise_path(f) for f in rec.files}
        shared_files = norm_files & other_files
        if shared_files:
            example = next(iter(shared_files))
            return {
                "with": sid,
                "reason": (
                    f"{candidate_id} and {sid} both claim {example}"
                ),
                "type": "same_file",
            }

        # --- same_function ---------------------------------------------------
        other_syms  = {s.lower() for s in rec.symbols}
        other_calls = {c.lower() for c in rec.calls}

        # candidate changes something the other session also changes
        sym_sym = lower_syms & other_syms
        if sym_sym:
            fn = next(iter(sym_sym))
            return {
                "with": sid,
                "reason": (
                    f"{candidate_id} and {sid} are both renaming {fn}"
                ),
                "type": "same_function",
            }

        # candidate changes something the other session calls
        sym_call = lower_syms & other_calls
        if sym_call:
            fn = next(iter(sym_call))
            return {
                "with": sid,
                "reason": (
                    f"{candidate_id} is renaming {fn}, which {sid} calls"
                ),
                "type": "same_function",
            }

        # candidate calls something the other session changes
        call_sym = lower_calls & other_syms
        if call_sym:
            fn = next(iter(call_sym))
            return {
                "with": sid,
                "reason": (
                    f"{sid} is renaming {fn}, which {candidate_id} calls"
                ),
                "type": "same_function",
            }

        # calls × calls → no conflict (fall through)

    return None
