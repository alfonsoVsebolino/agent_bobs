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
- **Hooks and MCP behave as documented** — Person 3, first thing once Bob is installed.
- **The exact names of Bob's file-editing tools**, so the `PreToolUse` matcher
  covers all of them. Docs show `write_file`; there are likely others.
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
