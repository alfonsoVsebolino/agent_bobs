"""harness/merge_demo.py — commit each Bob's work and merge into one branch.

Usage
-----
    python harness/merge_demo.py [TARGET] [--sessions aig,jay,kim]
                                 [--repo-root REPO_ROOT]

Run after all Bob sessions have finished their edits.
TARGET defaults to %USERPROFILE%\\agent-bobs-demo.
"""
import argparse
import os
import pathlib
import shutil
import stat
import subprocess
import sys

GIT_NAME = "Agent Bobs Harness"
GIT_EMAIL = "harness@agentbobs.local"
MARKER = ".agentbobs-demo"
DASHBOARD_REL = "dashboard/index.html"


def _rmtree(path: pathlib.Path) -> None:
    """Remove a directory tree, clearing read-only flags on Windows first."""
    def _handle_readonly(func, fpath, exc_info):
        os.chmod(fpath, stat.S_IWRITE)
        func(fpath)

    shutil.rmtree(path, onerror=_handle_readonly)


def _git(args: list, cwd: pathlib.Path, capture: bool = False):
    cmd = [
        "git",
        "-c", f"user.name={GIT_NAME}",
        "-c", f"user.email={GIT_EMAIL}",
    ] + args
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if not capture and result.returncode not in (0, 1):
        # returncode 1 from merge means conflicts — we handle that ourselves
        print(result.stdout)
        print(result.stderr)
        result.check_returncode()
    return result


def commit_session_work(session_dir: pathlib.Path, name: str):
    """Stage all changes in session_dir and commit as "<name>'s work"."""
    result = _git(["status", "--porcelain"], cwd=session_dir, capture=True)
    if not result.stdout.strip():
        print(f"  {name}: nothing to commit (no changes detected).")
        return
    _git(["add", "."], cwd=session_dir)
    _git(["commit", "-m", f"{name}'s work"], cwd=session_dir)
    print(f"  {name}: committed.")


def merge_all(
    target: pathlib.Path, sessions: list[str], repo_root: pathlib.Path
) -> tuple[int, list[str]]:
    """Clone base into merged/, pull each session in order.

    Returns (conflict_count, skipped_sessions).  Stops at the first conflict;
    remaining sessions are reported as skipped, not attempted.
    """
    base = target / "base"
    merged = target / "merged"

    if merged.exists():
        _rmtree(merged)

    print(f"Cloning base -> {merged} ...")
    _git(["clone", str(base), str(merged)], cwd=target)

    skipped: list[str] = []

    for i, name in enumerate(sessions):
        session_dir = target / f"demo-{name}"
        if not session_dir.is_dir():
            print(f"WARNING: {session_dir} not found, skipping.")
            skipped.append(name)
            continue

        print(f"\nMerging demo-{name} ...")
        result = _git(
            ["pull", str(session_dir), "main", "--no-rebase"],
            cwd=merged,
            capture=True,
        )
        # print git's real output
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="")

        # count unique conflicted files from git status
        status = _git(["status", "--porcelain"], cwd=merged, capture=True)
        conflicted = {
            line[3:]
            for line in status.stdout.splitlines()
            if len(line) >= 2 and line[:2] in ("UU", "AA", "DD", "AU", "UA", "DU", "UD")
        }
        if conflicted:
            count = len(conflicted)
            print(f"  -> {count} conflicted file(s): {sorted(conflicted)}")
            remaining = sessions[i + 1 :]
            if remaining:
                print(
                    f"  Stopping merge. Not merged due to conflict: "
                    + ", ".join(f"demo-{n}" for n in remaining)
                )
                skipped.extend(remaining)
            return count, skipped

    return 0, skipped


def run_tests(merged: pathlib.Path) -> tuple[str, str]:
    """Run unittest discover inside merged/.

    Returns (full_output, one_line_summary) where summary is e.g. "OK" or
    "FAILED (errors=1)".
    """
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", ".", "-v"],
        cwd=merged,
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr
    print("\n-- Test output ----------------------------------------------")
    print(output)

    # Extract the last non-empty line as the one-line summary ("OK" / "FAILED …")
    lines = [l.rstrip() for l in output.splitlines() if l.strip()]
    summary = lines[-1] if lines else "(no output)"
    return output, summary


def dashboard_link(repo_root: pathlib.Path, conflicts: int) -> str:
    dash = (repo_root / DASHBOARD_REL).resolve()
    # file:/// URLs use forward slashes; on Windows the path starts with a drive letter
    dash_url = dash.as_uri()
    return f"{dash_url}?git={conflicts}"


def main():
    default_target = pathlib.Path(os.environ.get("USERPROFILE", os.path.expanduser("~"))) / "agent-bobs-demo"

    parser = argparse.ArgumentParser(description="Merge Bob sessions and run tests.")
    parser.add_argument(
        "target",
        nargs="?",
        type=pathlib.Path,
        default=default_target,
        help=f"Target folder (default: {default_target})",
    )
    parser.add_argument(
        "--sessions",
        default="aig,jay,kim",
        help="Comma-separated session names in merge order (default: aig,jay,kim).",
    )
    parser.add_argument(
        "--repo-root",
        type=pathlib.Path,
        default=pathlib.Path(__file__).resolve().parent.parent,
        help="Path to the agent-bobs repo root.",
    )
    args = parser.parse_args()

    target = args.target.resolve()
    repo_root = args.repo_root.resolve()
    sessions = [s.strip() for s in args.sessions.split(",") if s.strip()]

    if not target.exists():
        print(f"ERROR: {target} does not exist. Run setup_demo.py first.")
        sys.exit(1)
    if not (target / MARKER).exists():
        print(f"ERROR: {target} is not an Agent Bobs demo folder (no {MARKER}).")
        sys.exit(1)

    # 1. commit each session's work
    print("-- Committing session work ----------------------------------")
    for name in sessions:
        commit_session_work(target / f"demo-{name}", name)

    # 2. merge
    print("\n-- Merging --------------------------------------------------")
    conflicts, skipped = merge_all(target, sessions, repo_root)
    print(f"\nTotal conflicted files: {conflicts}")

    # 3. tests
    _full, test_summary = run_tests(target / "merged")

    # 4. dashboard link
    link = dashboard_link(repo_root, conflicts)

    # 5. three-line summary
    print("-- Summary --------------------------------------------------")
    print(f"Conflicted files : {conflicts}")
    print(f"Merged tests     : {test_summary}")
    print(f"Dashboard        : {link}")
    print()


if __name__ == "__main__":
    main()
