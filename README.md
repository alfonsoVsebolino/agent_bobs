# Agent Bobs

**When one Bob isn't alone.** When several developers run IBM Bob on the same
project at the same time, their agents can't see each other, and they break each
other's work in ways Git never reports. Agent Bobs lets every Bob session see the
others, and stops a Bob before it writes over another Bob's work.

Built by team **iMAGIC** for the IBM Bob 2.0 Hackathon, 25–27 September 2026.

> **This repo is the only source of truth.** The two PDFs from before the event
> ("Agent Bobs" and "Workflow") are out of date — several details in them have
> changed. Where this repo and a PDF disagree, the repo wins.

## Start here

1. [`AGENTS.md`](AGENTS.md) — what we're building and the rules we build by. Bob
   reads this file automatically.
2. [`docs/ROLES.md`](docs/ROLES.md) — who does what, and your first task.
3. [`docs/DECISIONS.md`](docs/DECISIONS.md) — what changed from the PDFs, and why.
4. [`docs/PITCH.md`](docs/PITCH.md) — the story for the video and the writeup.
5. [`docs/SUBMISSION.md`](docs/SUBMISSION.md) — what to submit, the judging criteria, the deadline.

## Repo layout

| Folder | What | Owner |
|---|---|---|
| `server/` | the server: collision rules, MCP tools, hook endpoints, websocket | Person 1 |
| `dashboard/` | the live screen | Person 2 |
| `demo/` | the sample app we break on purpose | Person 4 |
| `demo/.bob/` | the Bob mode, MCP connection and hooks for the demo | Person 3 |
| `harness/` | builds the three demo copies, merges their work, runs the tests | Person 1 |
| `bob_sessions/` | every participant's Bob task summaries | everyone |
| `docs/` | roles, decisions, pitch | — |

## Status

- ✅ Server — collision rules, MCP tools for Bob, `/api` for the hooks, `/ws` for
  the dashboard; 13 passing tests
- ✅ Dashboard — live from the server's `/ws`; small fixes pending
- 🔨 Bob integration — built in `demo/.bob/`; being proven in a real Bob
- ✅ Demo app — 12 passing tests; a dry run of the control run gives 0 git
  conflicts and failing tests, as the pitch says
- ✅ Demo harness — builds the three demo copies, merges their work and runs the
  tests; tested on Windows, including rebuilds and a conflict case

## Run the server

On Windows, from the repo root. The one-time setup downloads the packages, so
start it early on a slow connection:

    py -m venv .venv
    .venv\Scripts\pip install -r server\requirements.txt

Start the server. It keeps running until you press Ctrl+C:

    .venv\Scripts\python -m server.main

It listens on `http://127.0.0.1:8765`, on your own machine only. Bob connects to
`/mcp`, the hooks post to `/api/claim` and `/api/release`, and the dashboard
connects to `ws://127.0.0.1:8765/ws`.

## See it work without Bob

Start the server and open `dashboard/index.html` in a browser. Then, in
PowerShell, play three Bobs:

```powershell
$api = "http://127.0.0.1:8765/api"
Invoke-RestMethod -Method Post "$api/claim" -ContentType application/json -Body '{"session":"aig","files":["auth/user.py"],"symbols":["get_user"]}'
Invoke-RestMethod -Method Post "$api/claim" -ContentType application/json -Body '{"session":"jay","files":["auth/reset.py"],"calls":["get_user"]}'
Invoke-RestMethod -Method Post "$api/claim" -ContentType application/json -Body '{"session":"kim","files":["tests/test_user.py"],"calls":["get_user"]}'
```

aig is renaming `get_user` while jay and kim both call it. The first claim comes
back clear, the other two come back as conflicts, and the dashboard turns red.
When aig finishes, jay and kim go back to green:

```powershell
Invoke-RestMethod -Method Post "$api/release" -ContentType application/json -Body '{"session":"aig"}'
```

Restart the server for a clean slate.

## Run the demo

The harness builds the three-session workspace, applies the demo edits, merges,
and runs the tests — all from the repo root.

**One-time setup** (no extra packages needed — stdlib only):

    py harness\setup_demo.py

This creates `%USERPROFILE%\agent-bobs-demo` with a `base/` git repo and three
clones (`demo-aig`, `demo-jay`, `demo-kim`), each pre-loaded with `.bob/`.

**Control run** (no Agent Bobs — shows the raw git + test failure):

    py harness\setup_demo.py --without-agent-bobs --fresh

**Open each session** in its own Bob window using the *Agent Bobs* mode:

    %USERPROFILE%\agent-bobs-demo\demo-aig
    %USERPROFILE%\agent-bobs-demo\demo-jay
    %USERPROFILE%\agent-bobs-demo\demo-kim

**After all three Bobs finish**, merge and run tests:

    py harness\merge_demo.py

This commits each session's work, merges them, runs `python -m unittest`, and
prints the `file:///…/dashboard/index.html?git=<N>` link.

**Run the harness self-test** (no Bob needed — exercises setup + merge end-to-end):

    py harness\test_harness.py

Exits 0 on success, non-zero on any failure.

## Run the tests

    .venv\Scripts\python -m server.test_core
    .venv\Scripts\python -m server.test_server

`test_core` checks the collision rules and needs no installs. `test_server`
starts a real server on port 8799 and checks that MCP clients, the hook API and
the websocket all share one state.
