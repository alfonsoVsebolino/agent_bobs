"""harness/setup_demo.py — build the three-session demo workspace.

Usage
-----
    python harness/setup_demo.py [TARGET] [--fresh] [--without-agent-bobs]
                                 [--sessions aig,jay,kim]
                                 [--repo-root REPO_ROOT]

Run from the repo root, or pass --repo-root explicitly.
"""
import argparse
import os
import pathlib
import shutil
import stat
import subprocess
import sys

MARKER = ".agentbobs-demo"
GIT_NAME = "Agent Bobs Harness"
GIT_EMAIL = "harness@agentbobs.local"
GITIGNORE = """.bob/
hooklog.jsonl
__pycache__/
"""


def _rmtree(path: pathlib.Path) -> None:
    """Remove a directory tree, clearing read-only flags on Windows first."""
    def _handle_readonly(func, fpath, exc_info):
        # Clear the read-only bit and retry (covers .git/objects on Windows).
        os.chmod(fpath, stat.S_IWRITE)
        func(fpath)

    shutil.rmtree(path, onerror=_handle_readonly)


def _git(args: list, cwd: pathlib.Path, capture: bool = False):
    """Run a git command, optionally capturing output."""
    cmd = [
        "git",
        "-c", f"user.name={GIT_NAME}",
        "-c", f"user.email={GIT_EMAIL}",
    ] + args
    if capture:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True
        )
        return result
    subprocess.run(cmd, cwd=cwd, check=True)


def _copy_tree(src: pathlib.Path, dst: pathlib.Path, skip: set[str] | None = None):
    """Recursively copy src → dst, skipping top-level names in *skip*."""
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        if skip and item.name in skip:
            continue
        target = dst / item.name
        if item.is_dir():
            _copy_tree(item, target)
        else:
            shutil.copy2(item, target)


def build(
    target: pathlib.Path,
    repo_root: pathlib.Path,
    sessions: list[str],
    with_agent_bobs: bool,
    fresh: bool,
):
    # ── safety check ────────────────────────────────────────────────────────
    if target.exists():
        marker = target / MARKER
        if not fresh:
            print(
                f"ERROR: {target} already exists.\n"
                f"Pass --fresh to rebuild it (only works if it contains {MARKER})."
            )
            sys.exit(1)
        if not marker.exists():
            print(
                f"ERROR: {target} exists but does not contain {MARKER}.\n"
                f"Refusing to delete a folder that was not created by this script."
            )
            sys.exit(1)
        print(f"--fresh: removing {target}")
        _rmtree(target)

    target.mkdir(parents=True)
    (target / MARKER).write_text("created by harness/setup_demo.py\n")

    demo_src = repo_root / "demo"
    if not demo_src.is_dir():
        print(f"ERROR: demo/ not found under {repo_root}")
        sys.exit(1)

    # ── base/ — bare demo app, no .bob/, no .gitkeep ─────────────────────
    base = target / "base"
    print(f"Creating {base} ...")
    _copy_tree(demo_src, base, skip={".bob", ".gitkeep"})

    # write .gitignore
    (base / ".gitignore").write_text(GITIGNORE)

    # init, add, commit
    _git(["init", "-b", "main"], cwd=base)
    _git(["add", "."], cwd=base)
    _git(["commit", "-m", "Initial demo app"], cwd=base)

    # ── demo-<name>/ — one clone per session ─────────────────────────────
    for name in sessions:
        clone_dir = target / f"demo-{name}"
        print(f"Cloning -> {clone_dir} ...")
        _git(["clone", str(base), str(clone_dir)], cwd=target)

        if with_agent_bobs:
            bob_src = demo_src / ".bob"
            bob_dst = clone_dir / ".bob"
            if bob_src.is_dir():
                _copy_tree(bob_src, bob_dst)
            else:
                print(f"WARNING: {bob_src} not found; skipping .bob copy.")

    # ── instructions ─────────────────────────────────────────────────────
    print()
    print("=" * 60)
    print("Demo workspace ready:", target)
    print("=" * 60)
    print()
    if with_agent_bobs:
        print("1. Start the Agent Bobs server (repo root):")
        print("   .venv\\Scripts\\python -m server.main")
        print()
        print("2. Open the dashboard:")
        print("   dashboard/index.html  (open in a browser)")
        print()
    if with_agent_bobs:
        print("3. Open each folder in its own Bob window")
        print("   (use the 'Agent Bobs' mode in each one):")
    else:
        print("1. Open each folder in its own Bob window:")
    for name in sessions:
        print(f"   {target / f'demo-{name}'}")
    if not with_agent_bobs:
        print()
        print("(Control run -- .bob/ not copied.)")
    print()


def main():
    default_target = pathlib.Path(os.environ.get("USERPROFILE", os.path.expanduser("~"))) / "agent-bobs-demo"

    parser = argparse.ArgumentParser(description="Build the Agent Bobs demo workspace.")
    parser.add_argument(
        "target",
        nargs="?",
        type=pathlib.Path,
        default=default_target,
        help=f"Target folder (default: {default_target})",
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Delete and rebuild target if it already contains the marker file.",
    )
    parser.add_argument(
        "--without-agent-bobs",
        action="store_true",
        help="Control run: do not copy .bob/ into the clones.",
    )
    parser.add_argument(
        "--sessions",
        default="aig,jay,kim",
        help="Comma-separated session names (default: aig,jay,kim).",
    )
    parser.add_argument(
        "--repo-root",
        type=pathlib.Path,
        default=pathlib.Path(__file__).resolve().parent.parent,
        help="Path to the agent-bobs repo root.",
    )
    args = parser.parse_args()

    sessions = [s.strip() for s in args.sessions.split(",") if s.strip()]
    build(
        target=args.target.resolve(),
        repo_root=args.repo_root.resolve(),
        sessions=sessions,
        with_agent_bobs=not args.without_agent_bobs,
        fresh=args.fresh,
    )


if __name__ == "__main__":
    main()
