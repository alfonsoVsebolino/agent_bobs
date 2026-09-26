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
An earlier take (`task05`–`task07`) ran while the demo app wrongly already
contained the password-reset files, so jay had nothing to do. It showed
the same "0 conflicts, tests fail" result, with one broken contribution instead
of two, and led to fixing the demo app.

## Agent Bobs run — the same three tasks, with Agent Bobs

To do. Same harness (`setup_demo.py` without `--without-agent-bobs`), the same
three prompts, the server and the dashboard running. Record: when each collision
appeared on the dashboard, whether any Bob wrote code against the renamed
function, and what the merge reports.
