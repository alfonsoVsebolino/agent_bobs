> **Superseded.** This plan's root-level logger, `release_hook.py` and the `Stop`
> hook were removed after a live test showed Stop fires on every pause. Kept for
> the record of how the hooks were designed with Bob.

# Plan: log_hook.py + .bob/settings.json (Option B1)

## Overview

Build a passive audit hook at `.bob/hooks/log_hook.py` that fires on every Bob
lifecycle event, appends a timestamped JSON record to `hooklog.jsonl`, and for
`PreToolUse` events calls the server's read-only `/api/check` to record whether
the tool call *would* conflict with another agent — before the blocking hook
ever runs. For `SessionStart` it prints the session identity to stdout. It
never exits 2.

Three deliverables, in dependency order:

1. Add `POST /api/check` to `server/api.py` (the hook needs an HTTP target).
2. Write `.bob/hooks/log_hook.py` (calls `/api/check`, logs everything).
3. Write `.bob/settings.json` (wires the hook into all three events).

---

## Sub-Task 1 — Add `POST /api/check` to `server/api.py`

**Intent**
Expose the already-implemented `state.check()` function over plain HTTP so that
stdlib-only hook scripts can call it without an MCP client. STATE is never
mutated; no WebSocket broadcast is sent.

**Expected Outcomes**
- `POST /api/check` accepts `{"session": str, "files": list, "symbols"?: list,
  "calls"?: list}`.
- Returns `{"clear": true, "conflict": null}` or
  `{"clear": false, "conflict": {"with": str, "reason": str, "type": str}}`.
- No side effects on STATE, no broadcast.
- Reuses the existing `ClaimRequest` Pydantic model (same shape) — no new model
  needed.

**Todo List**
- [ ] In `server/api.py`, add `check as _check` to the existing import from
  `.state` (currently imports only `claim as _claim`, `release as _release`,
  `get_snapshot`).
- [ ] Add a `POST /api/check` route function that calls
  `_check(req.session, req.files, req.symbols, req.calls)` and returns the
  result directly.
- [ ] Reuse `ClaimRequest` as the request body type (it already has `session`,
  `files`, `symbols`, `calls` with the right defaults).

**Relevant Context**
- `server/api.py`: `ClaimRequest` model and `/api/claim`
  are the direct pattern. The new route is structurally identical minus the
  broadcast call.
- `server/state.py`: `check()` is already fully
  implemented; returns `{"clear": bool, "conflict": dict | None}`.
- `server/mcp_tools.py`: the MCP `check` tool
  calls `_check(session_id, files, symbols, calls)` — exact same call this
  route will make.

**Status** `[ ] pending`

---

## Sub-Task 2 — Create `.bob/hooks/log_hook.py`

**Intent**
A single stdlib-only script handles all three hook events. For every event it
appends one timestamped JSON line to `hooklog.jsonl`. For `PreToolUse` events
that carry a file path it also calls `/api/check` and records the conflict
prediction in that same line, giving a per-tool-call audit trail of cross-agent
risk. For `SessionStart` it prints the session name to stdout.

**Expected Outcomes**
- `.bob/hooks/log_hook.py` is valid Python 3, stdlib only (`json`, `sys`, `os`,
  `datetime`, `urllib.request`, `urllib.error`).
- Every invocation appends exactly one JSON line to
  `.bob/hooks/hooklog.jsonl`, resolved relative to `__file__` (never cwd).
- Log record fields:
  - All original fields from the Bob event envelope (forwarded as-is).
  - `"_ts"` — `datetime.datetime.utcnow().isoformat() + "Z"`.
  - `"_session"` — derived from cwd basename (`demo-aig` → `"aig"`;
    fallback to full basename).
  - `"_would_conflict"` — `true` or `false`. Present only on `PreToolUse`
    events where a file path was found **and** the server was reachable.
  - `"_conflict_detail"` — the conflict dict from the server, or `null`.
    Present only when `_would_conflict` is `true`.
- If the server is unreachable, the two `_would_conflict` / `_conflict_detail`
  keys are omitted from that record entirely (fail open).
- `SessionStart` event → `print("Your Agent Bobs session name is test")` to
  stdout.
- Any exception anywhere is caught at the top level; script always exits 0.

**Todo List**
- [ ] Create `.bob/hooks/` directory (implicit when writing the file).
- [ ] Write `.bob/hooks/log_hook.py` with this structure:
  1. `try/except` wrapping the entire `main()` body; `sys.exit(0)` in finally.
  2. `event = json.load(sys.stdin)` — on failure, write a minimal error record
     and exit 0.
  3. Derive `_session` from `os.path.basename(os.getcwd())`; strip `"demo-"`
     prefix if present.
  4. Build record: `{**event, "_ts": ..., "_session": ...}`.
  5. Extract `hook_event_name = event.get("hook_event_name", "")`.
  6. If `PreToolUse`: extract file path from
     `(event.get("input") or event.get("tool_input") or {})` trying keys
     `path`, `file_path`, `file_name` in order. If found, POST
     `{"session": _session, "files": [path]}` to
     `http://127.0.0.1:8765/api/check` via `urllib.request.urlopen` (timeout
     5 s). On success parse response and set `_would_conflict` and (if true)
     `_conflict_detail` on the record. On `URLError` or any exception, skip
     those keys.
  7. If `SessionStart`: `print("Your Agent Bobs session name is test")`.
  8. Resolve log path:
     `os.path.join(os.path.dirname(os.path.abspath(__file__)), "hooklog.jsonl")`.
  9. Append `json.dumps(record) + "\n"` to the log file.
 10. `sys.exit(0)`.

**Relevant Context**
- `demo/.bob/hooks/claim_hook.py`:
  path extraction pattern (`input` / `tool_input`, three inner keys), session
  derivation, urllib POST shape — `/api/check` takes the same request body as
  `/api/claim`.
- `demo/.bob/hooks/session_hook.py`:
  stdout print pattern; reads stdin even when not consumed.
- `demo/.bob/hooks/release_hook.py`:
  fail-open pattern on server error.
- Log file sibling to the script — `__file__`-relative path is essential since
  Bob may invoke the hook from any working directory.

**Status** `[ ] pending`

---

## Sub-Task 3 — Create `.bob/settings.json`

**Intent**
Wire `log_hook.py` into all three Bob lifecycle hook slots with no matcher,
so every tool call and session event is captured.

**Expected Outcomes**
- `.bob/settings.json` exists at the repo-root `.bob/` (not inside `demo/`).
- Valid JSON; matches the schema of `demo/.bob/settings.json`.
- `PreToolUse`, `Stop`, and `SessionStart` each have one hook entry:
  `{"type": "command", "command": "python .bob/hooks/log_hook.py"}`.
- No `"matcher"` key anywhere — fires for every tool.

**Todo List**
- [ ] Write `.bob/settings.json` following the exact schema from
  `demo/.bob/settings.json`: top-level `"hooks"`
  object → each event key → array of one object with a `"hooks"` array →
  each hook has `"type": "command"` and `"command"`.

**Relevant Context**
- `demo/.bob/settings.json`: exact schema to copy.
- No matcher is intentional — confirmed by the comment in
  `claim_hook.py:19`: *"no matcher filter,
  so this hook fires for EVERY tool call"*.

**Status** `[ ] pending`

---

## Execution order

```
Sub-Task 1  →  Sub-Task 2  →  Sub-Task 3
(server route)  (hook script)  (settings wire-up)
```

Sub-Task 3 is independent of Sub-Task 1 but depends on Sub-Task 2 existing.
Sub-Task 2 depends on Sub-Task 1 being deployed so the `/api/check` call
actually resolves at runtime.
