# Pulse Server rules

These rules apply whenever you are in the **Pulse Server** mode.

## Before every edit

1. Note your session_id — it was printed at the start of this session (e.g. `aig`).
2. Call the `claim` MCP tool with:
   - `session_id` — your session name, exactly as printed.
   - `files` — every file you plan to write, rename, or delete.
   - `symbols` — every function you will change in any way (rename, delete, alter
     parameters or behaviour, change return type). If a changed signature breaks
     callers, it must be listed here.
   - `calls` — every function you will call but not change.
3. If `claim` returns `{"clear": false, ...}`, or if a file write is blocked by
   the `PreToolUse` hook (you will see a hook error rather than a tool result):
   - **STOP. Do not edit anything.**
   - Call the `check` MCP tool with the same file (and any symbols/calls you
     planned) to get the current conflict detail from the server.
   - Tell the user: which file or function is held, which session holds it, and
     the reason string from the conflict. Example:
     > "hello.py is held by session 'alf'. Reason: alf is editing hello.py."
   - The hook's own error message goes to Bob's internal log, not to you — you
     must call `check` yourself to get the information to relay to the user.
   - Wait for the user to decide what to do next.
4. If `claim` returns `{"clear": true, ...}`, proceed with the edit.

## Naming symbols and calls

Always use **bare function names** in `symbols` and `calls` — no module prefix,
no parentheses.

- ✅ `get_user`
- ❌ `auth.user.get_user`
- ❌ `get_user()`

## Claims accumulate

You can call `claim` multiple times as you discover what you need to touch.
Each call adds to your session's declared sets — it does not replace them.

## When you are done

**Do NOT call `release` when your task ends.** Your claims must stay active until
the team merges the work. Other sessions must still be able to see the conflict
after your code lands — removing it early lets them break the repo silently at
merge time.

Only call `release` when:
- The team has confirmed the work has been merged, **or**
- You are explicitly told to release by the user.

## What not to do

- Never skip `claim` and write directly. The `PreToolUse` hook will also catch
  file writes and post them automatically, but you should still call `claim`
  first with the full plan (files + symbols + calls) so the conflict is detected
  before you start, not file by file.
- Never invent a session_id. Use the one printed at the start of the session.
- Never call `release` mid-task if you intend to keep working.
- Never call `release` just because your own task is finished — wait for the merge.
