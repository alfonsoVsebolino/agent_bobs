# Roles and first tasks

Team **iMAGIC**: four people, roughly 20–24 working hours each across the 48
hours. Every role builds with Bob, and every person saves their **own** Bob task
summaries in `bob_sessions/` — see [`bob_sessions/README.md`](../bob_sessions/README.md).

| Role | Who | Owns |
|---|---|---|
| Person 1 — Server | Marco (MarcoAndreiBelen) | `server/` |
| Person 2 — Dashboard | Gabriel | `dashboard/` |
| Person 3 — Bob integration | Alfonso | `demo/.bob/` and the hooks |
| Person 4 — Demo and submission | Abrahm | `demo/`, the video, README, writeup, submission |

**How we work:** pull before you start. Commit only your own folder plus your
screenshots, so we never edit the same files. Push every 2–3 hours, check in every
4 hours, and say so in the group chat if you're stuck for more than 30 minutes. If
a push is rejected, ask Alfonso to add you as a collaborator on the repo.

---

## Person 1 — Server (Marco)

**Done:** the whole server — the collision rules, the MCP tools Bob calls, the
`/api` routes for the hooks, and the `/ws` websocket for the dashboard — with 13
passing tests. How to run it is in the README.

**Next:** the demo harness in `harness/`. One script builds the three demo copies,
with or without Agent Bobs; another merges their work and runs the tests, for
the control run.

---

## Person 2 — Dashboard (Gabriel)

**Built:** `dashboard/index.html` — live from the server's `/ws`: one column per
session showing files, functions being changed and called, conflict boxes with
the reason, connector lines, a waiting state and automatic reconnect. Tested
against the real server with the three-Bob demo.

**Next — so that every number on screen is true:**

1. **Count collisions as pairs.** The panel counts sessions that have a conflict,
   so the demo's two collisions (aig–jay and aig–kim) show as "3 collisions".
   Count unique pairs, the same way the connector lines are drawn.
2. **No fake data by default.** When the server is off, the page shows invented
   collisions under a small "offline" badge. Show the waiting state instead, and
   keep the sample data behind `index.html?demo`, with a clear "sample data" label.
3. **Take the git number from a real merge.** "0 conflicts" is hard-coded. Read it
   from the URL — `index.html?git=0`, set from the real `git merge` in the
   control run — and show "—" when it isn't given.
4. **Optional:** a Bob that holds a function but isn't blocked gets a red badge
   too, so viewers can't tell who is blocked. Make the holder's badge neutral.
5. **Rename your Bob screenshot.** `bob_sessions/Screenshot 2026-09-26 230001.png`
   is the right panel with the wrong name. Retake it as a tight crop of just the
   Task panel, named `imagic_<your-lablab-username>_task01_dashboard_summary.png`,
   and delete the old file.

### The first task

You build the live screen the judges watch during the demo. You don't need the
server to start: build it with fake data now and connect it later.

**Before you start:** pull the repo, open `agent-bobs` in Bob IDE, and read the
"Data contract" section of `AGENTS.md`. Your page receives exactly that shape.

**What to build:** one file, `dashboard/index.html`, that opens by double-clicking
it — no npm and no build step. It shows one column per Bob session. Each column
shows the session name, its status, the files it's working on, and the functions
it's changing. A column turns **red** when its `conflict` is not null, and shows
the conflict's `reason` in large, readable text. Status is either `working` or
`blocked`.

**Use this fake data** — three sessions, which is exactly what the demo will show:

- `aig` is working on `auth/user.py`, changing `get_user`, with a conflict with
  `jay` (reason: "aig is renaming get_user, which jay calls").
- `jay` is blocked on `auth/reset.py`, with a conflict with `aig` (same reason).
- `kim` is working on `tests/test_user.py` with no conflict, so it stays green.

**One rule that saves a rewrite later:** put all the drawing in a single function,
`render(sessions)`, that takes a list of those session objects. Later it will be
called with the real data from `ws://127.0.0.1:8765/ws`, which sends that same
list every time something changes.

**Make it readable on video:** large text, strong contrast, and a red state nobody
can miss. The judges will see it in a small video frame.

**Done means:** double-clicking `index.html` shows three columns — two red, one
green. Commit `dashboard/` and your screenshots, push, and post a screenshot of
the page in the group chat.

---

## Person 3 — Bob integration (Alfonso)

**Built:** the Bob integration in `demo/.bob/` — the MCP connection, the three
hooks, the Agent Bobs mode and its rules. Running the hooks against the real
server found two problems, so it isn't demo-ready yet.

**Next — prove it in a real Bob, and fix what that shows:**

1. **Claim only for tools that change files.** Today the hook claims every tool
   that carries a path, so a Bob that only *reads* or *lists* a file gets
   blocked, and every dashboard column turns red. The fix needs the exact names
   of Bob's file-editing tools — question 1 of the first task below.
2. **Find out when the Stop hook fires** — question 4 below. If it fires whenever
   Bob pauses, for example right after telling the user about a conflict, remove
   it from `settings.json` and let the mode's `release` call do the job.
   Otherwise a blocked Bob vanishes from the dashboard the moment it's caught.
3. **Let Bob explain a blocked write.** The hook's message goes to Bob's log, not
   to Bob. Add a rule: if a write is blocked, call `check` on that file, then
   tell the user who holds it and why.
4. **Confirm in Bob** that the Agent Bobs mode appears in the mode list, the MCP
   tab shows `agent-bobs` connected with 3 tools, and Bob knows its session name.
5. **Replace the screenshot** `bob_sessions/image_alfonsovsebolino_sessionlog.png`
   with the Task summary panel, named
   `imagic_alfonsovsebolino_task01_bob_integration_summary.png`.

### The first task — the hook experiment

You make Bob check with our server before it edits anything. Your first job is
the biggest unknown in the project: **proving Bob's hooks behave the way its docs
say.** You don't need the server for this.

**Setup:** make a throwaway folder outside the repo, such as
`C:\Users\<you>\hooktest`, and open it in Bob IDE. Nothing from this folder goes
into the repo.

**Step 1 — a logger.** Ask Bob, in Agent mode, to create `.bob\hooks\log_hook.py`:
a standard-library Python script that reads the JSON Bob sends on stdin and
appends it, with a timestamp, as one line to `hooklog.jsonl` in the folder. When
the event is `SessionStart`, it also prints "Your Agent Bobs session name is test".

**Step 2 — turn the hooks on.** Create `.bob\settings.json` in that folder. The
format comes from Bob's lifecycle-hooks docs; with no matcher, it catches every
tool:

```json
{
  "hooks": {
    "PreToolUse":   [{"hooks": [{"type": "command", "command": "python .bob\\hooks\\log_hook.py"}]}],
    "Stop":         [{"hooks": [{"type": "command", "command": "python .bob\\hooks\\log_hook.py"}]}],
    "SessionStart": [{"hooks": [{"type": "command", "command": "python .bob\\hooks\\log_hook.py"}]}]
  }
}
```

Open Bob Settings → **Hooks** and confirm all three appear. If they don't, reload
the Bob window.

**Step 3 — find out five things.** Start a **new** task for each, and read
`hooklog.jsonl` afterwards:

1. **Tool names:** ask Bob to create a file, then edit it, then append a line.
   Write down the exact `tool` name of every file-editing action. Our hook has to
   match all of them.
2. **Payload:** for those tools, write down which key inside `input` holds the
   file path. The docs show `path`; check it.
3. **Blocking:** make the logger exit with code 2 when the path contains
   `blocked.txt`, then ask Bob to create `blocked.txt`. Confirm Bob refuses the
   write and says it was blocked. This is the core of our demo.
4. **When Stop fires — the most important one:** give Bob a two-part task where
   it must ask you something halfway, such as "ask me which name to use, then
   create the file". Check whether `Stop` was logged after the question, or only
   once at the very end. This decides how we release claims.
5. **SessionStart:** in a new task, ask Bob "what is your Agent Bobs session
   name?" If it answers "test", the hook's output reaches Bob's context.

**Done means:** a post in the group chat with the five answers and a copy of
`hooklog.jsonl`. Only your screenshots go into the repo.

---

## Person 4 — Demo and submission (Abrahm)

**Built:** the sample app in `demo/` (12 passing tests) and `demo/TASKS.md`. A dry
run of the control run with this app works exactly as the pitch says: each of
the three edits passes its tests on its own, git merges all three with 0
conflicts, and the merged code fails its tests.

**Next:**

1. **End tasks 2 and 3 in `TASKS.md` with "Don't change any other file."** If a
   Bob puts its work into a file that aig is also editing — `tests/test_auth.py`
   is the likely one — git can report a real conflict, and the "0 conflicts"
   moment is gone.
2. **In task 2, also ask for a test in a new file, `tests/test_reset.py`.** Today
   the merged tests only catch kim's breakage. jay's `reset.py` is broken too,
   but no test imports it.
3. **One screenshot per task.** Keep the final one (1.19 Bobcoins), named
   `imagic_johnabrahmzapico_task01_demo_app_summary.png`, and delete the earlier
   copy and the misspelled name.
4. **Your second job:** everything the lablab submission form asks for, and the
   exact deadline.
5. **Optional:** "The demo" in AGENTS.md also asks for one same-file collision
   where a hook visibly blocks a write. It doesn't fit these three tasks without
   risking a git conflict, so make it a short separate scene — Alfonso's
   two-window test is exactly that.

### The first task

You own the sample app we break on purpose, and later the video and the writeup.
The demo app comes first, and it doesn't need the server.

**Before you start:** pull the repo, open `agent-bobs` in Bob IDE, and read "The
demo" section of `AGENTS.md`.

**What to build:** a small Python app in `demo/` — about 100 lines, **standard
library only**, no web framework. Keep it simple enough that three Bobs can each
change one part:

- `demo/auth/user.py` — a small in-memory dict of users, `get_user(user_id)`, and
  `login(email, password)`, which uses `get_user`.
- `demo/auth/utils.py` — `hash_password(password)` and `validate_email(email)`.
- `demo/auth/profile.py` — `update_profile(user_id, name)`, which calls `get_user`.
- `demo/tests/test_auth.py` — a few `unittest` tests, runnable from inside `demo/`
  with `python -m unittest`.
- Empty `__init__.py` files wherever Python needs them.

**Then write `demo/TASKS.md`** with the three tasks we'll give three Bobs at the
same time, each written like a real request:

1. "Clean up the login code: rename `get_user` to `fetch_user` and update every
   caller."
2. "Add password reset in a new file, `auth/reset.py`, that looks the user up
   with `get_user`."
3. "Add tests for user accounts in a new file, `tests/test_user.py`, that call
   `get_user`."

**Why they're designed this way:** each task touches a different file, so Git
reports **zero conflicts** when they're merged — yet after task 1 renames
`get_user`, tasks 2 and 3 are broken. That's the whole pitch: Git sees nothing,
and Agent Bobs catches it. Tasks 2 and 3 only *call* `get_user`, so they must
**not** conflict with each other — which shows the tool doesn't raise false
alarms.

**Save your Bobcoins.** Your laptop may end up running the demo — three Bob
windows at once, all billed to your account — so keep today's prompts short.

**Done means:** `python -m unittest` passes inside `demo/`, and `TASKS.md` exists.
Commit `demo/` and your screenshots, push, and post in the group chat.

**Your second job:** list everything the lablab submission form asks for — video
length, statement word limits, slides, links — and the exact deadline. Right now
we only know these secondhand.
