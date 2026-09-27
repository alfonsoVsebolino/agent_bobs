# Results

Measured results only. Quote these in the video and the writeup; never a number
that isn't here.

## Control run — three Bobs, no Agent Bobs

Sunday 27 September, on one laptop. Built with
`harness/setup_demo.py --without-agent-bobs`; each Bob got its task from
`demo/TASKS.md` in its own copy of the demo app, in Agent mode.

| Bob | Task | What it changed | Its own tests |
|---|---|---|---|
| aig | rename `get_user` to `fetch_user`, update every caller | `auth/user.py`, `auth/profile.py`, `tests/test_auth.py` | ✅ pass |
| jay | password reset in a new file | new `auth/reset.py`, new `tests/test_reset.py` | ✅ pass |
| kim | tests for user accounts in a new file | new `tests/test_user.py` | ✅ pass |

**Every Bob stayed in its lane, finished, and passed its own tests.** Then
`harness/merge_demo.py` merged the three — the real output:

```
conflicted files: 0

ERROR: tests.test_reset
ImportError: cannot import name 'get_user' from 'auth.user'
ERROR: tests.test_user
ImportError: cannot import name 'get_user' from 'auth.user'
Ran 14 tests
FAILED (errors=2)
```

- **Git: 0 conflicts.** The three changes touch different files.
- **Two of the three contributions arrive broken:** 84 new lines — jay's 45 and
  kim's 39 — call a function that no longer exists once aig's rename is merged.
- **Bobs are fast.** Prompts went out at about 00:55; all three Bobs had
  finished writing by 00:55:32 and had run their tests by 00:55:41. The break
  only surfaced at the merge, at 00:58. On a real team, the merge comes much
  later — at review time, or the next day.
- **Cost:** 0.85 Bobcoins for all three Bobs.

Evidence: `bob_sessions/imagic_marcoandreibelen_task08…task10_control_*_summary.png`.

**Reproduced on camera.** The control run was repeated at 12:13 and recorded for
the video, with three new Bob sessions (`task19`–`task21`, 0.75 Bobcoins). Same
result: each Bob stayed in its lane and passed its own tests, git merged all
three with 0 conflicts, and the merged tests failed with 2 errors.
An earlier take (`task05`–`task07`) ran while the demo app wrongly already
contained the password-reset files, so jay had nothing to do. It showed
the same "0 conflicts, tests fail" result, with one broken contribution instead
of two, and led to fixing the demo app.

## Agent Bobs run — the same three tasks, with Agent Bobs

Sunday 27 September, the same laptop. Built with `harness/setup_demo.py` (every
copy gets the Agent Bobs mode, MCP connection and hooks), with the server and
the dashboard running. The same three tasks, sent in the Agent Bobs mode. aig
went first, so its rename was already under way when the others started — the
situation the product is for.

The real timeline, from the hook logs:

```
10:52:43  aig  CLAIM    renaming get_user
10:52:56  aig  done     renamed in 3 files — its claim stays until merge
10:53:38  jay  CLAIM    calls get_user  →  BLOCKED: "aig is renaming get_user, which jay calls"
10:53:41  kim  CLAIM    calls get_user  →  BLOCKED: "aig is renaming get_user, which kim calls"
```

- **Both collisions were caught at the claim, before jay or kim wrote a single
  line.** Each Bob stopped and told its developer who holds `get_user` and why.
- The dashboard showed **2 collisions**, with jay and kim blocked.
- The merge afterwards: **0 conflicted files, and the merged tests pass**
  (12 tests, OK) — nobody built on the old name.
- **Cost:** 0.51 Bobcoins for all three Bobs.

Evidence: `bob_sessions/…task16`–`task18_agentbobs_run2_*_summary.png`, and the
screen recording used in the video.

### The same three tasks, side by side

| | Without Agent Bobs | With Agent Bobs |
|---|---|---|
| What jay and kim did | wrote 84 lines calling a function that no longer existed | wrote nothing — stopped at the claim |
| When the problem surfaced | at merge, when the tests failed | the moment each Bob declared its plan |
| What git reported | 0 conflicts | 0 conflicts |
| Merged tests | **FAILED** (errors=2) | **OK** |

### The first Agent Bobs run caught nothing — and why

An earlier run (10:21, `task12`–`task14`) caught no collision. The hook logs
showed two real problems, both fixed in `d29940c`:

1. **Claims were released too early.** Each Bob released its claims when its own
   task ended. aig released at 10:22:15; jay started at 10:22:17. But aig's
   rename only exists in aig's copy until it is merged, so jay's and kim's code
   would still break at merge. **A claim now lasts until the work is merged.**
2. **Names didn't match.** jay declared its call as `auth.user.get_user`, while
   aig claimed `get_user`. **The server now compares bare names.**

The same logs showed that Bob's real hook events use the fields `tool_name` and
`tool_input`, not the `tool` and `input` shown in Bob's documentation.
