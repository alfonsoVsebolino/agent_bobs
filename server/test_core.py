"""
test_core.py — plain-script tests for state.py + collision.py.

Run with:
    .venv\\Scripts\\python -m server.test_core

Exits 0 on all pass, non-zero on any failure.
No third-party dependencies.
"""

from __future__ import annotations

import sys
import traceback

# Reset STATE between tests by clearing it directly.
from server import state as _state_module


def _reset():
    _state_module.STATE.clear()


# ---------------------------------------------------------------------------
# Tiny test harness
# ---------------------------------------------------------------------------

_FAILURES: list[str] = []


def _run(name: str, fn):
    _reset()
    try:
        fn()
        print(f"  PASS  {name}")
    except Exception:
        _FAILURES.append(name)
        print(f"  FAIL  {name}")
        traceback.print_exc()


def _assert(cond: bool, msg: str = ""):
    if not cond:
        raise AssertionError(msg or "assertion failed")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_same_file_conflict():
    """Two sessions claiming the same file → same_file conflict."""
    from server.state import claim

    r1 = claim("aig", ["auth/user.py"], [], [])
    _assert(r1["clear"] is True, "first claim should be clear")

    r2 = claim("jay", ["auth/user.py"], [], [])
    _assert(r2["clear"] is False, "second claim should conflict")
    _assert(r2["conflict"]["type"] == "same_file")
    _assert(r2["conflict"]["with"] == "aig")


def test_same_function_change_vs_call():
    """One session changes get_user, another calls it → same_function."""
    from server.state import claim

    r1 = claim("aig", [], ["get_user"], [])
    _assert(r1["clear"] is True)

    r2 = claim("jay", [], [], ["get_user"])
    _assert(r2["clear"] is False)
    _assert(r2["conflict"]["type"] == "same_function")


def test_both_only_call_same_function_is_clear():
    """Two sessions that only call get_user → no conflict."""
    from server.state import claim

    r1 = claim("aig", [], [], ["get_user"])
    _assert(r1["clear"] is True)

    r2 = claim("jay", [], [], ["get_user"])
    _assert(r2["clear"] is True, "two callers should not conflict")


def test_file_only_claim_does_not_erase_earlier_symbols():
    """A file-only claim must not erase a session's previously declared symbols."""
    from server.state import claim, STATE

    claim("aig", ["auth/user.py"], ["get_user"], [])
    # Second claim for same session: only a file, no symbols.
    claim("aig", ["models.py"], [], [])

    rec = STATE["aig"]
    _assert("get_user" in rec.symbols, "earlier symbol should still be present")
    _assert(len(rec.files) == 2, f"expected 2 files, got {rec.files}")


def test_release_clears_conflict_on_both_sessions_releaser_is_blocker():
    """release(blocking_session) clears conflict on the blocked session."""
    from server.state import claim, release, STATE

    claim("aig", [], ["get_user"], [])     # aig changes, stays "working"
    claim("jay", [], [], ["get_user"])     # jay calls → blocked

    _assert(STATE["jay"].status == "blocked")
    _assert(STATE["aig"].status == "working",   # holder stays working
            f"aig should be working, got {STATE['aig'].status}")
    _assert(STATE["aig"].conflict is not None,  # but conflict field is set
            "aig should have conflict field set")

    release("aig")

    _assert("aig" not in STATE)
    _assert(STATE["jay"].status == "working")
    _assert(STATE["jay"].conflict is None)


def test_release_clears_conflict_on_both_sessions_releaser_is_blocked():
    """release(blocked_session) — the OTHER session should go back to working."""
    from server.state import claim, release, STATE

    claim("aig", [], ["get_user"], [])
    claim("jay", [], [], ["get_user"])

    _assert(STATE["jay"].status == "blocked")

    release("jay")

    _assert("jay" not in STATE)
    # aig had its conflict set when jay was blocked; now jay is gone.
    # aig's conflict pointed at jay → must be cleared.
    _assert(STATE["aig"].conflict is None or STATE["aig"].conflict.get("with") != "jay")
    _assert(STATE["aig"].status == "working")


def test_three_session_aig_jay_kim():
    """aig changes get_user; jay calls it (blocked); kim calls it → conflicts with aig.

    Also verifies:
    - aig stays "working" with its conflict field set throughout
    - aig making another file claim doesn't clear its conflict
    """
    from server.state import claim, STATE

    # aig claims the symbol change
    r_aig = claim("aig", [], ["get_user"], [])
    _assert(r_aig["clear"] is True)
    _assert(STATE["aig"].status == "working")
    _assert(STATE["aig"].conflict is None)

    # jay calls it → blocked
    r_jay = claim("jay", [], [], ["get_user"])
    _assert(r_jay["clear"] is False)
    _assert(r_jay["conflict"]["type"] == "same_function")
    _assert(r_jay["conflict"]["with"] == "aig")
    _assert(STATE["jay"].status == "blocked")

    # aig's status must still be "working", with conflict field set
    _assert(STATE["aig"].status == "working",
            f"aig should be working after jay's claim, got {STATE['aig'].status}")
    _assert(STATE["aig"].conflict is not None,
            "aig should have conflict field set after jay's claim")

    # kim calls get_user → must conflict with aig (aig is "working" so it can block)
    r_kim = claim("kim", [], [], ["get_user"])
    _assert(r_kim["clear"] is False,
            "kim should conflict with aig")
    _assert(r_kim["conflict"]["type"] == "same_function")
    _assert(r_kim["conflict"]["with"] == "aig",
            f"kim's conflict should be with aig, got {r_kim['conflict']['with']}")

    # aig adds another file — clear claim must NOT wipe aig's existing conflict
    r_aig2 = claim("aig", ["models.py"], [], [])
    _assert(r_aig2["clear"] is True,
            "aig's file-only claim should be clear (no new conflict)")
    _assert(STATE["aig"].conflict is not None,
            "aig's conflict must survive its own clear claim")
    _assert(STATE["aig"].status == "working",
            f"aig should still be working, got {STATE['aig'].status}")


def test_symbol_name_normalisation():
    """aig changes 'get_user', jay calls 'auth.user.get_user()' → same_function."""
    from server.state import claim

    r1 = claim("aig", [], ["get_user"], [])
    _assert(r1["clear"] is True)

    r2 = claim("jay", [], [], ["auth.user.get_user()"])
    _assert(r2["clear"] is False,
            "qualified call 'auth.user.get_user()' should conflict with symbol 'get_user'")
    _assert(r2["conflict"]["type"] == "same_function")
    _assert(r2["conflict"]["with"] == "aig")


def test_path_normalisation_variants():
    """./auth/user.py, auth\\user.py and Auth/User.py all match auth/user.py."""
    from server.state import claim, STATE

    # Session 1 claims with the canonical form.
    claim("aig", ["auth/user.py"], [], [])

    for variant in ["./auth/user.py", "auth\\user.py", "Auth/User.py"]:
        _reset()
        claim("aig", ["auth/user.py"], [], [])
        r = claim("jay", [variant], [], [])
        _assert(
            r["clear"] is False,
            f"variant '{variant}' should conflict with 'auth/user.py'",
        )
        _assert(r["conflict"]["type"] == "same_file")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

TESTS = [
    ("same file: same_file conflict", test_same_file_conflict),
    ("change vs call: same_function conflict", test_same_function_change_vs_call),
    ("both only call: clear", test_both_only_call_same_function_is_clear),
    ("file-only claim preserves earlier symbols", test_file_only_claim_does_not_erase_earlier_symbols),
    ("release(blocker) clears blocked session", test_release_clears_conflict_on_both_sessions_releaser_is_blocker),
    ("release(blocked) clears blocker session", test_release_clears_conflict_on_both_sessions_releaser_is_blocked),
    ("three-session aig/jay/kim scenario", test_three_session_aig_jay_kim),
    ("symbol name normalisation (qualified vs bare)", test_symbol_name_normalisation),
    ("path variant normalisation", test_path_normalisation_variants),
]


def main():
    print("Running server core tests...\n")
    for name, fn in TESTS:
        _run(name, fn)

    print()
    if _FAILURES:
        print(f"{len(_FAILURES)} test(s) FAILED: {', '.join(_FAILURES)}")
        sys.exit(1)
    else:
        print(f"All {len(TESTS)} tests passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
