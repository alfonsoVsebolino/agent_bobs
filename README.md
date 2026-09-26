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

## Repo layout

| Folder | What | Owner |
|---|---|---|
| `server/` | the server: collision rules, MCP tools, hook endpoints, websocket | Person 1 |
| `dashboard/` | the live screen | Person 2 |
| `demo/` | the sample app we break on purpose | Person 4 |
| `demo/.bob/` | the Bob mode, MCP connection and hooks for the demo | Person 3 |
| `bob_sessions/` | every participant's Bob task summaries | everyone |
| `docs/` | roles, decisions, pitch | — |

## Status

- ✅ Server — collision rules, MCP tools for Bob, `/api` for the hooks, `/ws` for
  the dashboard; 13 passing tests
- 🔨 Bob integration — built in `demo/.bob/`; being proven in a real Bob
- 🔨 Dashboard and demo app — under way

## Run the server

### Linux

One-time setup from the repo root:

    python3 -m venv .venv
    .venv/bin/pip install -r server/requirements.txt

Start the server (keeps running until Ctrl+C):

    .venv/bin/python -m server.main

### Windows

One-time setup:

    py -m venv .venv
    .venv\Scripts\pip install -r server\requirements.txt

Start the server:

    .venv\Scripts\python -m server.main

---

The server listens on `http://127.0.0.1:8765`, on your machine only. Bob
connects to `/mcp`, hooks post to `/api/claim`, `/api/check`, and `/api/release`,
and the dashboard connects to `ws://127.0.0.1:8765/ws`.

## Run the tests

**Linux:**

    .venv/bin/python -m pytest server/test_core.py server/test_server.py -v

or without pytest:

    .venv/bin/python server/test_core.py
    .venv/bin/python server/test_server.py

**Windows:**

    .venv\Scripts\python -m server.test_core
    .venv\Scripts\python -m server.test_server

`test_core` checks the collision rules and needs no installs. `test_server`
starts a real server on port 8799 and checks that MCP clients, the hook API and
the websocket all share one state.

## Demo: testing claims (in-repo vs out-of-repo files)

This demo runs two Bob sessions from two separate workspace folders and shows
the server catching a collision — one session claiming a file the other already
holds.

### 1. Start the server

From the repo root (keep this terminal open):

    .venv/bin/python -m server.main

### 2. Create two demo workspaces

Copy the `demo/` folder to two locations **outside** the repo. The folder name
after `demo-` becomes the session name:

    cp -r demo ~/demo-alf
    cp -r demo ~/demo-alf2

Your home directory is fine. The two folders must not be inside the repo root,
because Bob's `PreToolUse` hook derives the session name from the workspace
folder name.

### 3. Open each workspace in its own Bob window

In Bob, open `~/demo-alf` as a workspace. Repeat for `~/demo-alf2`. Select the
**Agent Bobs** mode in both windows.

Verify in each window:

- **MCP tab** → `agent-bobs` connected with 3 tools (`claim`, `check`, `release`).
- **Hooks tab** → 3 hooks registered (PreToolUse, Stop, SessionStart).
- Ask Bob: `"What is your Agent Bobs session name?"` — it should answer `alf`
  (or `alf2` in the second window).

### 4. In-repo file claim (same file, two sessions)

In **demo-alf**, ask Bob:

> "Claim `auth/user.py`, then ask me what to write before you edit it."

Do **not** answer the follow-up question yet. Check `~/demo-alf/.bob/hooks/hooklog.jsonl`
— you should see a `PreToolUse` line with `tool_name: write_file` and no `Stop`
line after it. If a `Stop` line appears, Bob's Stop hook fires on every pause;
remove the `Stop` entry from `~/.../demo-alf/.bob/settings.json` and repeat.

In **demo-alf2**, ask Bob:

> "Add a comment to `auth/user.py`."

Expected result: Bob in demo-alf2 is **blocked**. It calls `check`, then tells
you:

> "`auth/user.py` is held by session 'alf'. Reason: …"

The dashboard at `http://127.0.0.1:8765` should show demo-alf2's column in red.

### 5. Out-of-repo file claim (file outside the workspace folder)

Out-of-repo means a file whose path, when made relative to the workspace root,
starts with `../` — for example, a shared config file that lives next to both
demo folders.

Create a shared file:

    echo "# shared config" > ~/shared_config.py

In **demo-alf**, ask Bob:

> "Claim `../shared_config.py` and ask me what to write before you edit it."

In **demo-alf2**, ask Bob:

> "Edit `../shared_config.py`."

The hook normalises the path to `../shared_config.py` in both cases. The server
sees the same normalised string from both sessions and detects a `same_file`
collision. demo-alf2 is blocked for the same reason as in the in-repo case.

### 6. Verify the log

Each hook call appends one line to `.bob/hooks/hooklog.jsonl` in the workspace.
Open it in either demo folder:

    cat ~/demo-alf/.bob/hooks/hooklog.jsonl | python3 -m json.tool --no-indent

You should see:

- A line per tool call with `tool_name` and `_ts`.
- Write tools (`write_file`, `apply_diff`, etc.) with a `_would_conflict` field
  if the server was running when the log hook fired.
- Read tools (`read_file`, `list_files`, etc.) logged but **not** claimed —
  their lines have no `_would_conflict` field and no blocked status.
- A `Stop` line only if Bob's Stop event fires (use this to decide whether to
  keep the Stop hook in `settings.json`).
