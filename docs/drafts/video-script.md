# Video script — Agent Bobs

**Target length: 2:50.** The rules say 3:00 maximum, and judges stop watching at
3:00. The demo must be on screen for at least 90 seconds (here: 0:45–2:20), the
video must show how IBM Bob was used, and it must be narrated.

Narration is about 300 words: slow and clear is fine. Record the voice
separately in a quiet room (a phone voice memo is enough), then lay it under
the footage.

## What you need

| Clip | Where it comes from |
|---|---|
| **A.** The Agent Bobs run (2:14 raw) | Marco — already sent |
| **B.** The control run, *without* Agent Bobs, ending with the failing merge | Marco — recording it now |
| **C.** Bob tour: the Agent Bobs mode, the MCP tab, the Hooks tab (about 30 s) | Marco — recording it now |
| Cover image | `docs/images/cover.png` in the repo |
| The evidence folder | screen-record yourself scrolling `bob_sessions/` on GitHub |

## The script

### 1 · The problem — 0:00–0:20
**Show:** the cover image for 3 seconds. Then a frozen frame of clip B's three Bob
windows, with a caption over each: *aig: rename get_user* · *jay: password reset,
calls get_user* · *kim: tests, calls get_user*.

**Say:**
> IBM Bob makes one developer much faster. But teams don't work alone. Here, three developers run Bob on the same repository. One Bob renames a function. The other two write new code that calls it.

### 2 · Without Agent Bobs — 0:20–0:45
**Show:** clip B at 3–4× speed while the Bobs work. Each Bob reports its tests
pass. Then cut to the merge summary at normal speed, and put a box around
`Conflicted files : 0`, then around `Merged tests : FAILED (errors=2)`.

**Say:**
> Every Bob does its job and passes its own tests — in under a minute. Then we merge. Git reports zero conflicts, because the changes are in different files. But the tests fail. Two of the three Bobs built on a function that no longer exists, and nobody was warned.

### 3 · With Agent Bobs — 0:45–2:20 (the solution in action, 95 seconds)

**3a · How it plugs into Bob — 0:45–1:00**
**Show:** clip C — the mode dropdown set to *Agent Bobs*, the MCP tab showing
`agent-bobs` connected with `claim`, `check` and `release`, and the Hooks tab.

**Say:**
> Now the same three tasks, with Agent Bobs. It's built into Bob itself: a custom Bob mode, a small MCP server that every Bob connects to, and Bob's lifecycle hooks.

**3b · The rename — 1:00–1:25**
**Show:** clip A. Zoom in on the dashboard as aig's column appears, showing
*changing get_user*. Speed up while aig's Bob edits the files.

**Say:**
> Before writing any code, each Bob declares its plan to the server: the files it will edit, the functions it will change, and the functions it will call. aig's Bob claims the rename, and does it.

**3c · The collision is caught — 1:25–1:55**
**Show:** clip A at normal speed. The dashboard jumps to **2 collisions**, and jay
and kim turn **BLOCKED**. Then zoom in on jay's Bob chat, where it explains that
aig is renaming `get_user`.

**Say:**
> Now jay's and kim's Bobs start. Both plan to call get_user, so the server stops them — before they write a single line. Each Bob tells its developer exactly who holds the function, and why. The dashboard shows both collisions live.

**3d · The hook — 1:55–2:10**
**Show:** stay on the red dashboard, or show the Hooks tab from clip C again.

**Say:**
> And Bob's PreToolUse hook backs this up. It checks every file write with the server, and blocks the write if another Bob holds the file.

**3e · The result — 2:10–2:20**
**Show:** the merge summary from the Agent Bobs run, with a box around
`Merged tests : OK`.

**Say:**
> When we merge this time, the tests pass. Nobody built on the old name.

### 4 · Built with Bob — 2:20–2:42
**Show:** your recording of `bob_sessions/` on GitHub, then `AGENTS.md`. Caption:
*26 Bob tasks · all four team members*.

**Say:**
> We built Agent Bobs with Bob, in Plan and Agent modes, from one shared AGENTS.md that all four of our Bobs loaded automatically. And by running real Bobs, we learned things no document told us — like Bob's Stop event firing on every pause.

### 5 · Close — 2:42–2:50
**Show:** the cover image, with the repo link underneath:
`github.com/alfonsoVsebolino/pulse_mcp.dev`

**Say:**
> Agent Bobs. When one Bob isn't alone, stop the collision — before the code is written.

## Editing tips

- **Clipchamp** comes free with Windows 11. CapCut works too.
- The raw recordings show four windows at once, which is small on screen. **Zoom
  into the one that matters**: the dashboard when it turns red, jay's chat when
  it explains, the terminal for the merge summary.
- Speed up the waiting (Bobs thinking) 3–4×. Keep the key moments at 1×.
- Put the key numbers on screen as captions: *Git: 0 conflicts* · *Tests: FAILED*
  · *2 collisions caught* · *Tests: OK*.
- Background music is optional; keep it quiet under the voice.

## Export and upload

- **MP4, 1080p.** Check the length is under 3:00 and the file under 300 MB. A
  3-minute 1080p export is usually 60–150 MB.
- **Start uploading by 8:00 PM** from the fastest connection anyone has. Our
  connections are slow, and the deadline is 11:00 PM.
