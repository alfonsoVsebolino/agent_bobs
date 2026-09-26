# Agent Bobs rules

These rules apply whenever you are in the **Agent Bobs** mode.

## Before every edit

1. Note your session_id — it was printed at the start of this session (e.g. `aig`).
2. Call the `claim` MCP tool with:
   - `session_id` — your session name, exactly as printed.
   - `files` — every file you plan to write, rename, or delete.
   - `symbols` — every function you will change in any way (rename, delete, alter
     parameters or behaviour, change return type). If a changed signature breaks
     callers, it must be listed here.
   - `calls` — every function you will call but not change.
3. If `claim` returns `{"clear": false, ...}`:
   - **STOP. Do not edit anything.**
   - Tell the user exactly what the conflict is and which other session holds it.
   - Wait for the user to decide what to do next.
4. If `claim` returns `{"clear": true, ...}`, proceed with the edit.

## Claims accumulate

You can call `claim` multiple times as you discover what you need to touch.
Each call adds to your session's declared sets — it does not replace them.

## When you are done

Call `release` with your session_id. This frees any session that was waiting on
a conflict with you.

## What not to do

- Never skip `claim` and write directly. The `PreToolUse` hook will also catch
  file writes and post them automatically, but you should still call `claim`
  first with the full plan (files + symbols + calls) so the conflict is detected
  before you start, not file by file.
- Never invent a session_id. Use the one printed at the start of the session.
- Never call `release` mid-task if you intend to keep working.
