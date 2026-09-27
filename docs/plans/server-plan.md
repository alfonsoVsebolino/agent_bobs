> The plan Bob produced in Plan mode for `server/` (Task 01). The review of it
> changed several points — see `AGENTS.md` for what was built.

# Plan: server/ — MCP tools, API routes, WebSocket, collision rules

## Top-Level Overview

Build the entire `server/` package: one FastMCP 4 + FastAPI process, one
in-memory dict, three access doors (MCP, HTTP, WebSocket). The server detects
two collision types — `same_file` and `same_function` — and broadcasts every
state change to the dashboard over WebSocket. Nothing is persisted. No auth.
Python only.

---

## Architecture recap (from AGENTS.md)

```
Bob agent  ── MCP, streamable HTTP ──► /mcp      ┐
Bob hooks  ── HTTP POST ────────────► /api/...   ├─ server  ──  STATE dict
Dashboard  ◄─ websocket ──────────── /ws         ┘
```

Port **8765**.

---

## File layout for server/

```
server/
  __init__.py      (empty, makes server a package)
  state.py         the STATE dict + all mutation helpers
  collision.py     pure collision-detection logic (no I/O)
  api.py           FastAPI app: /api/claim, /api/release, /ws
  mcp_tools.py     FastMCP instance + claim/check/release tools
  main.py          wires FastMCP into FastAPI, calls uvicorn
  requirements.txt fastmcp, fastapi, uvicorn[standard], websockets
```

All five modules share one dict by importing `STATE` from `state.py`.
Nothing else crosses module boundaries.

---

## How the pieces share one dict

```
state.py
  STATE: dict[str, SessionRecord]   # session_id → record
  # helpers: add_session, remove_session, get_all

collision.py
  detect(new_session, STATE) → ConflictInfo | None

api.py
  from .state import STATE, add_session, remove_session
  from .collision import detect

mcp_tools.py
  from .state import STATE, add_session, remove_session
  from .collision import detect

main.py
  from .api import app          # FastAPI app already has /api and /ws
  from .mcp_tools import mcp    # FastMCP instance
  # mount and run
```

Because Python module globals are singletons in one process, every import
of `STATE` from `state.py` refers to the same object in memory. The two
doors (MCP and HTTP) therefore read and write the same dict — no queue,
no lock beyond a simple threading.Lock for the mutation helpers.

---

## Sub-Tasks

---

### Sub-Task 1 — `state.py`: the shared dict and SessionRecord

**Intent**
Define the single source of truth for all session data. Every other module
imports from here. Nothing else in the system holds state.

**Expected Outcomes**
- `STATE` dict exists, keyed by `session_id` (str).
- Each value is a `SessionRecord` dataclass or TypedDict with fields:
  `session`, `files`, `symbols`, `calls`, `status`, `conflict`.
- `conflict` is `None` or a dict matching the AGENTS.md contract:
  `{"with": str, "reason": str, "type": "same_file" | "same_function"}`.
- Thread-safe add/remove helpers exist: `set_session`, `remove_session`.
- A `get_snapshot` helper returns a list of all records (used by WebSocket
  on new connection).
- `normalise_path(path: str) -> str` lives here: strips `./`, lowercases
  on Windows, converts backslashes to forward slashes.

**Todo List**
- [ ] Create `server/state.py`
- [ ] Define `SessionRecord` as a dataclass
- [ ] Define `STATE: dict[str, SessionRecord]` and `_LOCK: threading.Lock`
- [ ] Implement `set_session`, `remove_session`, `get_snapshot`
- [ ] Implement `normalise_path`

**Relevant Context**
- AGENTS.md data contract (line 76–87)
- DECISIONS.md: "claim checks and records in one step" (prevents race)
- Fields: session, files, symbols, calls, status, conflict

**Status** — [ ] pending

---

### Sub-Task 2 — `collision.py`: pure detection logic

**Intent**
Isolate all collision logic in one testable, I/O-free module. Both the MCP
tools and the HTTP API call the same function; no duplication.

**Expected Outcomes**
- `detect(candidate_session_id, candidate_files, candidate_symbols,
  candidate_calls, state_snapshot) -> ConflictInfo | None`
  is a pure function: takes data in, returns data out, touches no globals.
- Detects `same_file`: candidate's files overlap any existing session's files.
- Detects `same_function`: candidate's symbols overlap any existing session's
  symbols **or** calls; OR candidate's calls overlap any existing session's
  symbols.
- Returns the first conflict found; the contract does not require all of them.
- `reason` string matches AGENTS.md example style:
  `"aig is renaming get_user, which jay calls"`
- Path comparison uses normalised paths (call `normalise_path` from state.py).

**Conflict-detection truth table**

| Session A has  | Session B has  | Conflict? |
|----------------|----------------|-----------|
| symbol X       | symbol X       | yes (same_function) |
| symbol X       | calls X        | yes (same_function) |
| calls X        | symbol X       | yes (same_function) |
| calls X        | calls X        | no |
| file F         | file F         | yes (same_file) |

**Todo List**
- [ ] Create `server/collision.py`
- [ ] Implement `detect(...)` — same_file check first, then same_function
- [ ] Ensure the function is side-effect free (unit-testable without mocking)

**Relevant Context**
- AGENTS.md lines 46–49 (symbols vs calls semantics)
- DECISIONS.md section 2 (calls alongside symbols, truth table rationale)

**Status** — [ ] pending

---

### Sub-Task 3 — `api.py`: HTTP routes and WebSocket

**Intent**
Expose `POST /api/claim`, `POST /api/release`, and `GET /ws` on the FastAPI app.
Hooks use the first two; the dashboard uses the third. Both HTTP routes call the
same collision + state functions that the MCP tools use.

**Expected Outcomes**
- `POST /api/claim` body: `{"session": str, "files": list, "symbols"?: list,
  "calls"?: list}` → `{"clear": true}` or `{"clear": false, "conflict": {...}}`
- If clear, the session is added/updated in STATE and all WebSocket clients
  are notified.
- If not clear, STATE is unchanged and the conflict is returned.
- `POST /api/release` body: `{"session": str}` → `{"ok": true}`
  Removes the session from STATE; all WS clients are notified.
- `GET /ws` (WebSocket): on connect, send all current sessions as a JSON array;
  on each state change, broadcast the updated full snapshot.
- A `broadcast(snapshot)` helper sends JSON to every connected client;
  dead connections are silently dropped.
- Module-level `CONNECTIONS: set[WebSocket]` holds live sockets.
- The FastAPI `app` object is created here and exported for `main.py`.

**Todo List**
- [ ] Create `server/api.py`
- [ ] Define `app = FastAPI()`; import STATE, set_session, remove_session,
  detect, normalise_path
- [ ] Implement `broadcast` coroutine
- [ ] Implement `/api/claim` route (check → set → broadcast)
- [ ] Implement `/api/release` route (remove → broadcast)
- [ ] Implement `/ws` WebSocket endpoint

**Relevant Context**
- AGENTS.md lines 56–58 (HTTP route contracts)
- AGENTS.md lines 76–87 (data contract to dashboard)
- AGENTS.md server essentials snippet: define routes BEFORE mounting MCP

**Status** — [ ] pending

---

### Sub-Task 4 — `mcp_tools.py`: FastMCP tools

**Intent**
Expose `claim`, `check`, and `release` as MCP tools. They share collision and
state logic with `api.py` by importing the same helpers — not by copy-pasting.

**Expected Outcomes**
- `mcp = FastMCP("agent-bobs")` instance is created here and exported.
- `claim(session_id, files, symbols=[], calls=[])`:
  - Calls `detect` against current STATE.
  - If conflict: returns conflict description string; STATE unchanged.
  - If clear: calls `set_session`; broadcasts via the same `broadcast` from
    `api.py`; returns "claimed" confirmation string.
- `check(session_id, files, symbols=[], calls=[])`:
  - Calls `detect` only. STATE never mutated. Returns conflict or "clear".
- `release(session_id)`:
  - Calls `remove_session`; broadcasts; returns "released".
- All three use `@mcp.tool` decorator (FastMCP 4 API).

**Note on broadcast**: `mcp_tools.py` imports `broadcast` from `api.py`.
This is the only cross-module call that is not just data; it is acceptable
because both live in the same process and `broadcast` is a pure async helper.

**Todo List**
- [ ] Create `server/mcp_tools.py`
- [ ] Create `mcp = FastMCP("agent-bobs")` instance
- [ ] Implement `claim` tool with `@mcp.tool`
- [ ] Implement `check` tool with `@mcp.tool`
- [ ] Implement `release` tool with `@mcp.tool`

**Relevant Context**
- AGENTS.md lines 40–44 (tool signatures)
- AGENTS.md server essentials: `mcp_app = mcp.http_app(path="/mcp")`
- DECISIONS.md section 1: streamable HTTP only
- FastMCP 4 docs: use `@mcp.tool` (not 2.x `@server.tool`)

**Status** — [ ] pending

---

### Sub-Task 5 — `main.py`: wire FastMCP into FastAPI and launch

**Intent**
Compose the two frameworks into one process following the exact pattern
documented in AGENTS.md. Wrong ordering silently breaks MCP or routing.

**Expected Outcomes**
- `mcp_app = mcp.http_app(path="/mcp")`
- `app = FastAPI(lifespan=mcp_app.lifespan)` — MCP session manager starts.
- `/api` routes and `/ws` are already on `app` (imported from `api.py`);
  they are registered before the mount.
- `app.mount("/", mcp_app)` — last line before `uvicorn.run`.
- `uvicorn.run(app, host="0.0.0.0", port=8765)` in `if __name__ == "__main__"`.
- Running `python -m server.main` starts the server.

**Todo List**
- [ ] Create `server/main.py`
- [ ] Import `app` from `api.py`, `mcp` from `mcp_tools.py`
- [ ] Build `mcp_app` and set `app.lifespan`
- [ ] Mount `mcp_app` at `"/"`
- [ ] Add `uvicorn.run` entry point

**Relevant Context**
- AGENTS.md server essentials snippet (lines 111–115) — exact ordering required
- DECISIONS.md section 1 (why streamable HTTP)

**Status** — [ ] pending

---

### Sub-Task 6 — `requirements.txt` and smoke test

**Intent**
Pin exact dependencies and provide a repeatable way to verify the server
starts and both MCP clients see each other's claims.

**Expected Outcomes**
- `server/requirements.txt` lists: `fastmcp`, `fastapi`, `uvicorn[standard]`,
  `websockets`.
- A manual smoke-test checklist exists (not automated) that proves two separate
  MCP clients share state:
  1. Start server: `python -m server.main`
  2. Client A calls `claim("a", files=["auth/user.py"], symbols=["get_user"])`
     → returns "claimed"
  3. Client B calls `claim("b", files=["auth/user.py"], symbols=["get_user"])`
     → returns conflict `{"type": "same_file", ...}`
  4. Client B calls `check("b", files=["other.py"], symbols=["get_user"])`
     → returns conflict `{"type": "same_function", ...}` (A is changing it, B
     would change it too)
  5. Client B calls `check("b", files=["other.py"], calls=["get_user"])`
     → same conflict (A changes, B calls)
  6. Client C calls `check("c", files=["other.py"], calls=["get_user"])`
     → **clear** (nobody else changes it, C only calls it — wait, A does change
     it, so this is still a conflict). Adjust: run after A releases.
  7. Client A calls `release("a")` → "released"
  8. Now Client C's `check("c", calls=["get_user"])` → clear (correct)

**Todo List**
- [ ] Create `server/requirements.txt`
- [ ] Add smoke-test steps to `docs/DECISIONS.md` or a new `server/README.md`

**Relevant Context**
- AGENTS.md: `.bob/mcp.json` uses `"type": "streamable-http"` — the same
  transport a Python `fastmcp.Client` can use in a test script
- DECISIONS.md table (stdio = two dicts; HTTP = one dict)

**Status** — [ ] pending

---

## How two separate MCP clients see each other's claims

Both clients connect to the same running server at `http://127.0.0.1:8765/mcp`.
FastMCP 4 with streamable-HTTP transport keeps **one process** alive; its MCP
session manager is started via the shared `lifespan` on the FastAPI app. Each
`claim` call from either client writes into the same `STATE` dict in that one
process. When Client B calls `claim` or `check`, `detect` iterates the same
dict that Client A already wrote to — so the collision is visible.

Under stdio this would fail silently: each client spawns its own process, its
own dict, and they never share data. That is why AGENTS.md explicitly forbids
stdio (DECISIONS.md section 1).

---

## Dependency diagram

```
main.py
  └─ api.py      ←── state.py
  └─ mcp_tools.py ←── state.py
                      collision.py ←── state.py (normalise_path)
  api.py ←── collision.py
  mcp_tools.py ←── collision.py
  mcp_tools.py ←── api.py (broadcast)
```
