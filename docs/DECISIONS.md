# Decisions — project context v2

What changed from the v1 context doc, and why. Read this once.
`AGENTS.md` is the short version that Bob loads automatically in every session.

| # | Decision | In one line |
|---|---|---|
| 1 | Bob connects over **streamable HTTP**, never stdio | Under stdio the product silently detects nothing |
| 2 | Tools take **`calls`** as well as `symbols` | Makes the headline collision work inside scope, with no false alarms |
| 3 | **Demo redesigned**, plus a **control run** | v1's demo depended on the features we agreed to cut first |
| 4 | Bob **lifecycle hooks** enforce the check | A mode instruction asks Bob to stop; a hook actually stops it |
| 5 | **One dashboard column per active session** | No empty column in the video |

---

## 1. Streamable HTTP, never stdio

**What.** Every Bob connects to one running server by URL:
`http://127.0.0.1:8765/mcp`.

**Why.** Bob can reach an MCP server two ways. Under **stdio**, each Bob starts
its *own private copy* of the server. Three Bobs means three servers and three
separate dicts, so no Bob can ever see another — the whole product does nothing.
Worse, it fails silently: one Bob on its own behaves perfectly, so every early
test passes and we would find out during demo rehearsal.

This was tested with our exact stack (FastMCP 4.0.9 + FastAPI + uvicorn +
websockets) before we wrote anything:

| Transport | Server processes | Second Bob claims the same file |
|---|---|---|
| stdio (FastMCP's default) | two — PID 14130 and 14137 | `clear` — **collision missed** |
| streamable HTTP | one — PID 14111 | conflict in our exact data-contract shape, and the dashboard websocket sees it live |

Bob's docs say streamable HTTP "supports multiple client connections" and "can
be hosted on different machines."

**How it helps us win.** A product that doesn't work doesn't place. And it
answers the first question a judge will ask — *"does this only work on one
laptop?"* No: the server is a network service, so the same design works across
machines. Only our demo is single-laptop, because we have no shared network.

**Cost.** None. It is configuration.

## 2. `calls` alongside `symbols`

**What.** `claim` and `check` take an optional `calls` list next to `symbols`:
- `symbols` — functions this session will **change**
- `calls` — functions it will **call without changing**

A collision happens when someone changes a function another session changes or
calls. Two sessions that only *call* the same function never collide. The
dashboard contract is **unchanged** — the explanation lives in the `reason` text.

**Why.** Our best collision is the rename: one Bob renames `get_user`, another
writes new code calling `get_user`. In v1 that needed stretch goal #4, which v1
also names "the first thing we cut." Declaring `calls` makes it a plain
same-function check — inside scope.

Why not just put called functions into `symbols`? Because then two harmless
callers look like a collision. In our demo, password reset and the tests will
both call `get_user` and change neither. With one list, the dashboard would turn
them red for no reason, in front of the judges.

**How it helps us win.** The rename is the collision **Git can never see**, and
it is what separates us from file-locking tools like GitLive. Keeping callers
green shows precision: the tool doesn't cry wolf.

**Cost.** One optional parameter on the MCP tools. The dashboard is unaffected.

**Limit, stated honestly.** This depends on the agent declaring what it calls.
If it forgets, the collision is missed. Stretch goal #4 (an `ast` check of the
file the hook sees) is the backstop.

## 3. Demo: collisions inside scope, plus a control run

**What.**
- The headline collision is **rename vs call, in different files**.
- One **same-file** collision, so a hook visibly blocks a write.
- One pair that only **calls** the same function, which correctly stays green.
- Run it **twice** — without Agent Bobs, then with it.

**Why.** Two of v1's three tasks relied on stretch goals ("writes its own
duplicate helper" is #3; "calls the function task 1 renamed" is #4). That set two
of our own rules against each other: *cut from the detection list when behind*
and *never cut the demo*. Cutting the list would have broken the demo.

Different files matter because Git only reports a conflict when two edits touch
the same lines. Keeping the rename and its caller in separate files guarantees
"Git says 0 conflicts" is literally true on screen.

**How it helps us win.** The brief asks us to "clearly demonstrate impact" with
numbers. A collision count alone is not impact. The control run is: we show the
real `git merge` output reporting zero conflicts, then the real test failure,
then the same three tasks caught with Agent Bobs — measured, not claimed.

**Cost.** One extra rehearsal run. Drop v1's "4 collisions" figure; quote what
we measure.

## 4. Bob lifecycle hooks

**What.** Hooks in each demo workspace's `.bob/settings.json`:
- `PreToolUse` on every file-editing tool → `POST /api/claim`; exit code 2 **blocks the write**
- `SessionStart` → prints the session name into Bob's context

> **Update, Sunday — the `Stop` hook was removed.** v2 also released claims on
> `Stop`. Alfonso's live test showed Stop fires every time Bob pauses — after
> asking the user a question, or after reporting a conflict — not only when a
> task ends. A session holding `hello.py` asked a question, its claims were
> released, and a second Bob then wrote `hello.py` unblocked. Sessions now
> release through the mode's `release` call; restarting the server clears stale
> claims.

The MCP tools and the custom mode stay exactly as planned. Hooks are added on top.

**Why.**
- **A mode instruction is a request. A hook is enforcement.** In Agent mode Bob
  may make dozens of edits. If it skips `check` once, the collision slips through.
  `PreToolUse` fires on every write, and Bob itself refuses the write on exit 2.
- **Stale claims.** An agent that stops without calling `release` would leave its
  column stuck red. v2 used `Stop` for this; see the update above for why that
  was removed.
- **Session identity.** Every Bob needs its own name. The folder name
  (`demo-aig` → `aig`) gives one source of truth for both the hooks and the agent.
- **It unblocks Person 3.** v1's blocking first task was finding out whether Bob
  exposes its plan before editing. Bob's hook docs answer it: `PreToolUse`
  receives the file path and new content **before** the write.

**How it helps us win.** Our pitch says "we prevent the crash instead of
reporting it afterwards." With hooks that is literally true — Bob's own UI shows
the write as blocked. And using custom modes, MCP, lifecycle hooks and AGENTS.md
together is a much deeper integration than most entries will show, which is what
"meaningful use of Bob" rewards.

**Risk.** Taken from Bob's docs; not yet run on a real Bob. It is purely
additive: if hooks misbehave, the mode-instruction path from v1 still works.

### ADR-4a: `Stop` fires on every pause, not only on task completion

**Observed (verified in live test, Sep 2026).** Bob's `Stop` event fires
whenever the agent finishes a turn and waits for user input — not only when the
task is genuinely complete or abandoned. In a two-session blocking test:

1. Session `alf` claimed `hello.py` and asked the user a question.
2. A `Stop` line appeared in `hooklog.jsonl` immediately after the question.
3. `release_hook.py` fired, removed `alf` from STATE, and unblocked `alf2`.
4. `alf2` then wrote `hello.py` without any conflict — the session it should
   have been blocked by had already vanished.

**Trade-off.**

| Option | Effect |
|---|---|
| Keep `Stop` hook | Sessions auto-release on every pause. Stale claims are impossible but mid-task blocking evaporates the moment Bob asks a question. |
| Remove `Stop` hook | Sessions stay alive across pauses, blocking is durable. Stale claims are possible if a Bob window is closed without calling `release`. |

> **Superseded, Sunday 09:30.** The `Stop` hook was removed from
> `demo/.bob/settings.json` altogether, rather than removed by hand from each demo
> copy: the harness copies `demo/.bob` into every run, so a manual step would be
> forgotten. Later live runs also showed that claims must last until the work is
> **merged** — see `docs/RESULTS.md`. The original decision is kept below for the
> record.

**Original decision.** The `Stop` hook is **retained in the repo** (`demo/.bob/settings.json`)
because removing it would silently break stale-claim cleanup and we do not have
a reliable way to distinguish "turn complete, waiting for input" from "task
abandoned." For the live demo, operators must manually remove the `Stop` entry
from the workspace copies (`~/demo-alf/.bob/settings.json` etc.) before running
the blocking test, and call `release` explicitly at the end of each session.

**Implication for the demo script.** Step 4b of the demo walkthrough in
`README.md` already documents this: check `hooklog.jsonl` for a `Stop` line
after the pause; if present, remove the `Stop` hook from the workspace copies
and repeat. Quote the `Stop` behaviour when reporting — it is an honest finding,
not a bug in our code.

**Future fix.** If Bob exposes a `reason` or `exitCode` field on the `Stop`
event distinguishing "user asked to stop" from "turn boundary", the hook can
filter on that field and only release on a genuine stop.

## 5. One dashboard column per active session

**What.** Render a column for each session in the state, rather than four fixed ones.

**Why.** We are four people, but the demo runs three sessions. Four fixed columns
means an empty one in every frame of the video. Rendering what is in the state is
also *less* code than hard-coding names. Person 2's placeholder-data first task
is unchanged.

---

## Smaller decisions

| Decision | Reason |
|---|---|
| Team context lives in `AGENTS.md` at the repo root | Bob loads it automatically — no pasting, and all four Bobs share the same context |
| Keep `AGENTS.md` short; reasoning lives here | It is sent with every Bob request, which costs Bobcoins |
| Server on port 8765 | Server, `mcp.json`, hooks and dashboard must agree on one number |
| Pin FastMCP 4 | `pip install fastmcp` gives 4.x; tutorials and Bob's own suggestions may show removed 2.x APIs |
| Ask Bob for **Python** FastMCP explicitly | Bob's MCP builder scaffolds TypeScript by default |
| Paths are repo-relative, forward slashes | Three demo copies live in three folders, so absolute paths never match |
| `claim` checks and records in one step | Two separate calls let two racing sessions both pass |
| Demo sessions open a copy of `demo/`, not the repo root | Keeps our build context out of the product under test |
| snake_case everywhere, including slides | We picked Python; v1's pitch used `getUser` |
| Name stays **Agent Bobs** | The plural is the product; "Agent Bob" reads as Bob's own Agent mode |

## Still unverified — check before relying on it

- ~~Judging criteria and deadline~~ — **confirmed** on the lablab event page; see
  `docs/SUBMISSION.md`. The real criteria differ from v1: Application of
  Technology, Presentation, Business Value and Originality.
- ~~**Hooks and MCP behave as documented**~~ — **verified in live runs, with one
  difference from the docs.** `PreToolUse` and `SessionStart` work as documented,
  and `Stop` fires on every pause (ADR-4a). But the event Bob actually sends names
  its fields `hook_event_name`, `tool_name` and `tool_input`, where the docs show
  `event`, `tool` and `input`. `claim_hook.py` reads both.
- ~~**The exact names of Bob's file-editing tools**~~ — **seen in the live runs'
  hook logs:** `write_file` and `apply_diff` for writes; `read_file`,
  `list_files`, `grep` and `FindSymbol` for reads; MCP tools arrive as
  `mcp__agent-bobs__claim` and `mcp__agent-bobs__release`. `claim_hook.py` also
  treats any tool whose name contains write, edit, replace, insert, diff, create
  or delete as a write, so an unseen name is still caught.
- **Whether hooks also fire for subagent tool calls.** If they do, Agent Bobs
  protects Bob's own parallel subagents from each other at no extra cost. Worth
  one question, not one line of code.

## Outside the code

- **Repo description** reads "provider-agnostic." Our entire differentiation
  from prior art is being *Bob-native*, and judges read the description. The
  owner should change it — and consider renaming the repo `agent-bobs`
  (GitHub redirects the old URL).
- **`bob_sessions/`** — every participant captures their own. See
  `bob_sessions/README.md`.
- **Bobcoins** — 40 each, 160 for the team. All three demo sessions run on the
  demo laptop's account, rehearsals included. Budget for it.

## Clock (Philippine time, UTC+8)

| Hour | When | What |
|---|---|---|
| 0 | Fri 25 Sep, 23:00 | Kickoff |
| 28 | **Sun** 27 Sep, 03:00 | Stretch goals allowed only if ahead |
| 36 | Sun 27 Sep, 11:00 | **Feature freeze** — video and writeup only after this |
| 48 | Sun 27 Sep, 23:00 | **Deadline** (confirmed) — submit by 21:00 |

## 6. agent-sync parallelisation extensions

**What.** Four additive extensions to the coordination layer, none of which
replace or modify existing hooks or MCP tools:

1. `PostToolUse` hook → `POST /api/progress` — per-file unblocking
2. `sync` MCP tool + `POST /api/sync` — session readiness handshake
3. `barrier` status + `barrier` MCP tool — N-session rendezvous checkpoint
4. `SessionEnd` hook → `POST /api/release` — auto-release on true session end

**Why.** The existing model is pessimistic locking: first session to claim wins;
second session blocks until the first calls `release`. This is correct for
conflict prevention, but it serialises sessions that could work in parallel.
The `calls × calls → no conflict` rule already proves the design supports
parallelism; these extensions surface it to agents and allow coordinated
split-task execution.

**Scope check.** None of the four extensions add a new detection type. They
operate on existing `same_file` and `same_function` logic, or on infrastructure
only (routing, status fields, signalling).

**Cost.** Extensions 1–3 are additive: new files, new routes, one new field on
`SessionRecord`. Extension 4 is blocked pending verification (see ADR-6d below).

---

### ADR-6a: `PostToolUse` hook + `/api/progress`

**Problem.** The server knows a session *claimed* a file but not when it was
*written*. A blocked session must wait for the full `release` call even if the
holder has already written the file it was waiting on and moved to other work.

**Decision.** Add a `PostToolUse` hook (`post_tool_hook.py`) that fires after
every successful file write and POSTs `{"session", "file", "done": true}` to a
new `POST /api/progress` endpoint. The server removes that file from the
session's claimed set, re-runs `detect()` on any blocked sessions, and unblocks
any whose remaining conflict no longer holds.

**Constraint.** The hook exits 0 always — it never blocks. Only `PreToolUse`
blocks. The `PostToolUse` entry in `settings.json` is added alongside the
existing `PreToolUse` entry; the existing entry is not touched.

**Risk.** If `detect()` produces a false-clear after partial file removal (e.g.
a symbol conflict remains), the re-run catches it because symbols are still in
the session's `symbols` list. File removal only affects the `same_file` check.

---

### ADR-6b: `sync` MCP tool + `POST /api/sync`

**Problem.** Two sessions splitting independent work have no way to signal
readiness to each other. One must either poll the dashboard manually or wait for
a human to relay the signal.

**Decision.** Add a `sync(session_id, wait_for, until_status, timeout)` MCP
tool and matching `POST /api/sync` HTTP route. The server polls STATE on a
0.5 s interval inside an `asyncio.wait_for` block. When the named session
reaches the target status (default `"working"`) or releases, the call returns
`{"ready": true}`. On timeout: `{"ready": false, "reason": "timeout"}`.

**Constraint.** `sync` never mutates STATE. It is a read-only wait. `_LOCK` is
acquired only for each status read, never held across a sleep.

**Trade-off.** Polling at 0.5 s is simple and has no concurrency hazard. An
event-driven approach (condition variable per session) would be faster but adds
complexity that is not justified for a local demo with two or three sessions.

---

### ADR-6c: `barrier` status + `barrier` MCP tool

**Problem.** N sessions splitting a task need a shared rendezvous: all must
reach a checkpoint before any proceeds to the next step.

**Decision.** Add a `"barrier"` status value to `SessionRecord` (alongside
`"working"` and `"blocked"`) and a `barrier_group` field. When a session calls
`barrier(session_id, group_id)`, its status is set to `"barrier"`. When every
session in the group has arrived, the server sets all of them back to
`"working"` and broadcasts.

**Constraint.** `collision.detect()` already skips sessions whose status is not
`"working"` (line 49: `if rec.status != "working": continue`). No change to
collision logic is required.

**Dashboard contract change.** `status` gains a third value: `"barrier"`.
Dashboard columns for `"barrier"` sessions render in amber. This is a contract
change — Person 2 must be told before the branch is merged.

**Build order.** Implement after ADR-6a and ADR-6b have passing tests.

---

### ADR-6d: `SessionEnd` auto-release — blocked pending verification

**Problem.** If a Bob window closes without calling `release`, its claims stay
in STATE indefinitely. The only current fix is restarting the server.

**Proposed decision.** Add a `SessionEnd` hook (`end_hook.py`) that calls the
existing `POST /api/release`. No new server code needed.

**Why blocked.** ADR-4a documents that `Stop` fires on every turn boundary, not
only on true session end. If `SessionEnd` behaves the same way, this hook
re-introduces the mid-task release bug that ADR-4a resolved. Before
implementing, `SessionEnd` must be verified as firing exactly once, on genuine
session close, in a live Bob session. That test has not been run.

**If verified distinct from `Stop`:** add `end_hook.py` (three lines, stdlib
only) and a `SessionEnd` entry in `settings.json`. No other files change.

**If not verified or behaves like `Stop`:** do not implement. Stale claims
remain a known limitation; restarting the server is the documented mitigation.
