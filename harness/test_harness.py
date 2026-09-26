"""harness/test_harness.py — end-to-end smoke test for setup_demo + merge_demo.

Exits non-zero on any failure. Uses stdlib only. Works on Windows.

Cases
-----
1. with-agent-bobs     — clean merge, 0 conflicts, merged tests fail, .bob/ present
2. without-agent-bobs  — same edits, same merge outcome, no .bob/
   Both cases also verify --fresh rebuild and a second merge run succeed.
3. conflict-case       — jay also edits tests/test_auth.py; exactly 1 conflicted
   file; demo-kim is reported as not merged.
"""
import os
import pathlib
import shutil
import stat
import subprocess
import sys
import tempfile

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
HARNESS = REPO_ROOT / "harness"
SESSIONS = ["aig", "jay", "kim"]


# ── helpers ────────────────────────────────────────────────────────────────

def _rmtree(path: pathlib.Path) -> None:
    """Remove a directory tree, clearing read-only flags on Windows first."""
    def _handle_readonly(func, fpath, exc_info):
        os.chmod(fpath, stat.S_IWRITE)
        func(fpath)

    shutil.rmtree(path, onerror=_handle_readonly)


def fail(msg: str):
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def run(cmd: list, cwd: pathlib.Path, capture: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, cwd=cwd, capture_output=capture, text=True)
    return result


def assert_tests_pass(session_dir: pathlib.Path, label: str):
    result = run(
        [sys.executable, "-m", "unittest", "discover", "-s", ".", "-q"],
        cwd=session_dir,
    )
    if result.returncode != 0:
        fail(
            f"{label}: expected tests to pass, but they failed.\n"
            + result.stdout + result.stderr
        )
    print(f"  OK: {label} tests pass.")


def assert_tests_fail(session_dir: pathlib.Path, label: str):
    result = run(
        [sys.executable, "-m", "unittest", "discover", "-s", ".", "-q"],
        cwd=session_dir,
    )
    if result.returncode == 0:
        fail(f"{label}: expected tests to fail, but they passed.")
    print(f"  OK: {label} tests fail (as expected).")


def _parse_conflicts(output: str) -> int:
    """Extract the number from 'Total conflicted files: N'.

    Raises ValueError if the line is not found — never silently returns 0.
    """
    for line in output.splitlines():
        if "Total conflicted files:" in line:
            parts = line.split(":")
            return int(parts[-1].strip())
    raise ValueError("merge_demo.py output did not contain 'Total conflicted files:'")


def run_merge(target: pathlib.Path) -> subprocess.CompletedProcess:
    """Run merge_demo and return the result. Fails the test if it crashes."""
    result = run(
        [
            sys.executable,
            str(HARNESS / "merge_demo.py"),
            str(target),
            "--repo-root", str(REPO_ROOT),
        ],
        cwd=REPO_ROOT,
    )
    if result.returncode not in (0, 1):
        fail(
            f"merge_demo.py crashed (exit {result.returncode}).\n"
            + result.stdout + result.stderr
        )
    return result


# ── demo edits ─────────────────────────────────────────────────────────────

def make_aig_edit(base: pathlib.Path):
    """Rename get_user -> fetch_user in three files."""
    files = [
        base / "auth" / "user.py",
        base / "auth" / "profile.py",
        base / "tests" / "test_auth.py",
    ]
    for fp in files:
        text = fp.read_text(encoding="utf-8")
        new_text = text.replace("get_user", "fetch_user")
        fp.write_text(new_text, encoding="utf-8")
    print("  aig: renamed get_user -> fetch_user in 3 files.")


def make_jay_edit(base: pathlib.Path):
    """Add auth/reset.py that calls get_user."""
    reset = base / "auth" / "reset.py"
    reset.write_text(
        "from auth.user import get_user\n"
        "\n"
        "\n"
        "def reset_password(user_id: str, new_password: str) -> bool:\n"
        "    \"\"\"Reset password for user_id. Returns True if the user exists.\"\"\"\n"
        "    user = get_user(user_id)\n"
        "    if user is None:\n"
        "        return False\n"
        "    from auth.utils import hash_password\n"
        "    user['password_hash'] = hash_password(new_password)\n"
        "    return True\n",
        encoding="utf-8",
    )
    print("  jay: added auth/reset.py.")


def make_jay_edit_with_conflict(base: pathlib.Path):
    """Add auth/reset.py AND edit the import line in tests/test_auth.py.

    The edit to tests/test_auth.py will conflict with aig's rename of get_user
    in that same file once the branches are merged.
    """
    make_jay_edit(base)
    test_auth = base / "tests" / "test_auth.py"
    text = test_auth.read_text(encoding="utf-8")
    # Add a comment on the import line so the line content differs from aig's
    # renamed version — guaranteed textual conflict on that line.
    new_text = text.replace(
        "from auth.user import get_user, login",
        "from auth.user import get_user, login  # jay: reset feature added",
    )
    test_auth.write_text(new_text, encoding="utf-8")
    print("  jay: also edited import line in tests/test_auth.py (conflict setup).")


def make_kim_edit(base: pathlib.Path):
    """Add tests/test_user.py that calls get_user."""
    test_user = base / "tests" / "test_user.py"
    test_user.write_text(
        "import unittest\n"
        "\n"
        "from auth.user import get_user\n"
        "\n"
        "\n"
        "class TestUserLookup(unittest.TestCase):\n"
        "    def test_known_user(self):\n"
        "        user = get_user('u1')\n"
        "        self.assertIsNotNone(user)\n"
        "\n"
        "    def test_unknown_user(self):\n"
        "        self.assertIsNone(get_user('nope'))\n"
        "\n"
        "\n"
        "if __name__ == '__main__':\n"
        "    unittest.main()\n",
        encoding="utf-8",
    )
    print("  kim: added tests/test_user.py.")


# ── setup helper ───────────────────────────────────────────────────────────

def run_setup(target: pathlib.Path, extra_args: list[str] = None) -> None:
    """Run setup_demo.py; fail the test if it exits non-zero."""
    args = [
        sys.executable,
        str(HARNESS / "setup_demo.py"),
        str(target),
        "--repo-root", str(REPO_ROOT),
    ]
    if extra_args:
        args.extend(extra_args)
    result = run(args, cwd=REPO_ROOT, capture=False)
    if result.returncode != 0:
        fail("setup_demo.py failed.")


# ── test cases ─────────────────────────────────────────────────────────────

def run_case(tmp: pathlib.Path, without_agent_bobs: bool):
    """Standard case: 0 conflicts, merged tests fail."""
    label = "without-agent-bobs" if without_agent_bobs else "with-agent-bobs"
    print(f"\n{'='*60}")
    print(f"Running case: {label}")
    print(f"{'='*60}")

    target = tmp / label

    # 1. setup
    print("\n1. setup_demo ...")
    extra = ["--without-agent-bobs"] if without_agent_bobs else []
    run_setup(target, extra)

    # 2. make edits
    print("\n2. Making demo edits ...")
    make_aig_edit(target / "demo-aig")
    make_jay_edit(target / "demo-jay")
    make_kim_edit(target / "demo-kim")

    # 3. each copy's tests pass on its own
    print("\n3. Checking per-session tests ...")
    assert_tests_pass(target / "demo-aig", "demo-aig")
    assert_tests_pass(target / "demo-jay", "demo-jay")
    assert_tests_pass(target / "demo-kim", "demo-kim")

    # 4. merge
    print("\n4. Running merge_demo ...")
    merge_result = run_merge(target)
    print(merge_result.stdout)
    if merge_result.stderr:
        print(merge_result.stderr)

    conflicts = _parse_conflicts(merge_result.stdout)
    print(f"  Detected conflict count: {conflicts}")

    if conflicts != 0:
        fail(f"Expected 0 conflicted files, got {conflicts}.")
    print("  OK: 0 conflicted files (git merge was clean).")

    # 5. merged tests fail
    print("\n5. Checking merged tests (should fail) ...")
    assert_tests_fail(target / "merged", "merged")

    # 6. --fresh rebuild succeeds
    print("\n6. Rebuilding with --fresh ...")
    run_setup(target, extra + ["--fresh"])
    print("  OK: --fresh rebuild succeeded.")

    # 7. second merge run (after re-setup means no edits yet, but merged/ will
    #    be recreated from clean base — must not crash)
    print("\n7. Running merge_demo again on the fresh setup ...")
    merge_result2 = run_merge(target)
    if merge_result2.returncode not in (0, 1):
        fail(f"Second merge_demo run crashed (exit {merge_result2.returncode}).")
    print("  OK: second merge_demo run succeeded.")

    # 8. .bob/ presence
    print("\n8. Checking .bob/ presence ...")
    for name in SESSIONS:
        bob_dir = target / f"demo-{name}" / ".bob"
        has_bob = bob_dir.is_dir()
        if without_agent_bobs and has_bob:
            fail(f"demo-{name} has .bob/ but --without-agent-bobs was used.")
        if not without_agent_bobs and not has_bob:
            fail(f"demo-{name} is missing .bob/ but agent bobs mode was requested.")
        state = "absent" if without_agent_bobs else "present"
        print(f"  OK: demo-{name}/.bob/ is {state}.")

    print(f"\n  PASS: {label}")


def run_conflict_case(tmp: pathlib.Path):
    """Conflict case: jay edits tests/test_auth.py; expect 1 conflict, kim skipped."""
    label = "conflict-case"
    print(f"\n{'='*60}")
    print(f"Running case: {label}")
    print(f"{'='*60}")

    target = tmp / label

    # 1. setup
    print("\n1. setup_demo ...")
    run_setup(target)

    # 2. make edits — jay also edits tests/test_auth.py
    print("\n2. Making demo edits (jay also touches tests/test_auth.py) ...")
    make_aig_edit(target / "demo-aig")
    make_jay_edit_with_conflict(target / "demo-jay")
    make_kim_edit(target / "demo-kim")

    # jay's version of tests/test_auth.py still needs to parse — aig renamed
    # get_user in its own copy; jay's copy still has get_user (unexploded), so
    # jay's tests pass on their own.
    print("\n3. Checking per-session tests ...")
    assert_tests_pass(target / "demo-aig", "demo-aig")
    assert_tests_pass(target / "demo-jay", "demo-jay")
    assert_tests_pass(target / "demo-kim", "demo-kim")

    # 4. merge — expect exactly 1 conflict, kim not merged
    print("\n4. Running merge_demo ...")
    merge_result = run_merge(target)
    print(merge_result.stdout)
    if merge_result.stderr:
        print(merge_result.stderr)

    conflicts = _parse_conflicts(merge_result.stdout)
    print(f"  Detected conflict count: {conflicts}")

    if conflicts != 1:
        fail(f"Expected exactly 1 conflicted file, got {conflicts}.")
    print("  OK: exactly 1 conflicted file.")

    # check that "demo-kim" is mentioned as not merged
    combined = merge_result.stdout + merge_result.stderr
    if "demo-kim" not in combined or "Not merged" not in combined:
        fail(
            "Expected merge output to report demo-kim as not merged.\n"
            + combined
        )
    print("  OK: output reports demo-kim was not merged.")

    # 5. second merge run must not crash (merged/ already conflicted; it gets
    #    rebuilt from scratch, same result)
    print("\n5. Running merge_demo again (must not crash) ...")
    merge_result2 = run_merge(target)
    if merge_result2.returncode not in (0, 1):
        fail(f"Second merge_demo run crashed (exit {merge_result2.returncode}).")
    print("  OK: second merge_demo run succeeded.")

    print(f"\n  PASS: {label}")


# ── main ───────────────────────────────────────────────────────────────────

def main():
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="agentbobs-test-"))
    print(f"Temp folder: {tmp}")

    try:
        run_case(tmp, without_agent_bobs=False)
        run_case(tmp, without_agent_bobs=True)
        run_conflict_case(tmp)
    except SystemExit:
        raise
    finally:
        print(f"\nCleaning up {tmp} ...")
        _rmtree(tmp)

    print("\n" + "=" * 60)
    print("ALL CHECKS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
