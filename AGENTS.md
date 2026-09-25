# Agent Bobs

A coordination layer that lets several developers' IBM Bob sessions on one
repository see each other, and stops an agent **before** it breaks another
agent's work.

Bob loads this file automatically in every session. Everything below is decided.
Do not redesign the architecture, add dependencies, or add features beyond the
scope. If a request conflicts with this file, point out the conflict instead of
silently choosing. Why each decision was made: `docs/DECISIONS.md`.

## The problem

Several developers run Bob in Agent mode on one project at once. Each agent
believes it is alone. One renames `get_user` to `fetch_user`; another writes new
code calling `get_user`. Each did its job; together the project is broken. Git
cannot warn anyone: the edits are in different files, so the merge is clean and
the code fails later.

Bob coordinates subagents inside one session. This problem lives *between*
sessions, where no single-session tool can see. We do not claim novelty:
coordination tools exist for other assistants (wit, agent-coord, CoordMCP, grit,
git-paw, agentic-git). Ours is Bob-native — built on Bob's custom modes, MCP and
lifecycle hooks. Never describe it as novel or first-of-its-kind.

## Architecture

One Python process, one in-memory dict, three doors:

```
Bob agent  ── MCP, streamable HTTP ──► /mcp      ┐
Bob hooks  ── HTTP POST ────────────► /api/...   ├─ server  ──  STATE dict
Dashboard  ◄─ websocket ──────────── /ws         ┘
```

Server listens on **port 8765**.

### MCP tools (Bob agent → server)

- `claim(session_id, files, symbols, calls=[])` — declare what this session will touch.
  Checks and records in one step, and returns any conflicts, so two sessions racing
  each other cannot both get through.
- `check(session_id, files, symbols, calls=[])` — read-only: would this claim conflict?
- `release(session_id)` — this session is finished.

`symbols` = functions this session will **change**. `calls` = functions it will
**call without changing**. A conflict exists when one session changes a function
another session also changes or calls. Two sessions that only *call* the same
function never conflict.

### Hook endpoints (Bob lifecycle hooks → server)

Same logic as the MCP tools, exposed over plain HTTP because a hook is a shell
command, not an MCP client. One implementation, two doors.

- `POST /api/claim` — body `{"session": "aig", "files": ["auth/user.py"]}` →
  `{"clear": true}` or `{"clear": false, "conflict": {...}}`
- `POST /api/release` — body `{"session": "aig"}`

### Session identity

Each demo workspace is a folder named `demo-<name>` (e.g. `demo-aig`); the session
name is the part after `demo-`. A `SessionStart` hook prints it into Bob's context
so the agent passes the same name as `session_id`. Hooks derive it from their
working directory.

### Paths

Always repo-relative with forward slashes: `auth/user.py`. Hooks convert with
`os.path.relpath(path, os.getcwd())`. The server also normalises separators,
case and a leading `./` before comparing, because the demo runs three copies of
the app in three folders.

## Data contract (server → dashboard) — do not change without telling the team

```json
{"session": "aig", "files": ["auth/user.py"], "symbols": ["get_user"],
 "status": "working", "conflict": null}
```

When a collision is found, `conflict` becomes:

```json
{"with": "jay", "reason": "aig is renaming get_user, which jay calls", "type": "same_function"}
```

`type` is `same_file` or `same_function`.

## Scope — do not exceed

Detect exactly two things:
1. **same_file** — two sessions claiming the same file
2. **same_function** — one session changing a function another changes or calls

Stretch, only if ahead at hour 28 (Sun 27 Sep, 03:00 PHT):
3. Duplicate work — two sessions writing their own version of the same helper
4. AST check of the hook's file content, catching calls an agent forgot to declare

Not building: other languages, cloud hosting, accounts, auth, permissions,
persistent history, a database. Python only. In-memory only. Runs locally.

## Stack

- Python. MCP server: **FastMCP 4** (`pip install fastmcp` installs 4.x — most
  tutorials show 2.x APIs that no longer exist). Web: FastAPI + uvicorn.
- Dashboard: a single HTML file + websocket, or plain React.
- Parsing: stdlib `ast`. State: a dict. Hooks: Python, **stdlib only**.

### Server essentials — verified against FastMCP 4.0.9

```python
mcp_app = mcp.http_app(path="/mcp")
app = FastAPI(lifespan=mcp_app.lifespan)  # required, or the MCP session manager never starts
# define @app.websocket("/ws") and the /api routes HERE, before the mount
app.mount("/", mcp_app)                    # last, or it swallows every other route
```

**Streamable HTTP, never stdio.** Under stdio each Bob starts its own server
process with its own dict, so no collision is ever detected — and a
single-session test still passes.

### Bob configuration (inside each demo workspace)

- `.bob/mcp.json` — `{"mcpServers": {"agent-bobs": {"type": "streamable-http",
  "url": "http://127.0.0.1:8765/mcp", "alwaysAllow": ["check", "claim", "release"]}}}`
- Also switch on the global **Use MCP servers** auto-approve toggle, or every tool
  call pops a confirmation.
- `.bob/custom_modes.yaml` + `.bob/rules-agent-bobs/` — the Agent Bobs mode: before
  writing, call `claim` with the plan (files, symbols, calls); on conflict, stop and
  tell the user.
- `.bob/settings.json` → `hooks`: `PreToolUse` (matcher covering every
  file-editing tool) → `/api/claim`, exit 2 to block; `Stop` → `/api/release`;
  `SessionStart` → print the session name.
- On Windows hooks run through `cmd /c`.

## Repo layout and owners

```
server/        MCP tools, /api routes, /ws, collision rules    Person 1
dashboard/     the live screen, one column per active session  Person 2
demo/          the sample app we break on purpose              Person 4
demo/.bob/     Agent Bobs mode, MCP connection, hooks          Person 3
bob_sessions/  task-summary screenshots                        everyone, their own
docs/          DECISIONS.md
```

Demo sessions open a **copy of `demo/`** as their workspace, never the repo root,
so this file does not load into the product under test.

## The demo

Three Bob sessions, three copies of `demo/`, one laptop — said openly.
- The headline collision is **rename vs call in different files**: git is
  guaranteed to report nothing, and the code is guaranteed to break.
- Include one **same-file** collision so a hook visibly blocks a write.
- Include one pair that only **calls** the same function, and show it correctly
  stays green.
- Run it twice: once **without** Agent Bobs (show the real git merge output and
  the real test failure), once with. Quote only numbers you measured.

## Team rules

- Push and pull every 2–3 hours. No long-lived branches.
- Stuck over 30 minutes → say so in the group chat.
- Capture your own `bob_sessions/` screenshot when each Bob task finishes.
- Hour 36 (Sun 27 Sep, 11:00 PHT): feature freeze. After that, video and writeup only.
- When behind, cut from the stretch list. Never cut the demo.
- Prefer the smallest thing that works. Python function names in snake_case.
