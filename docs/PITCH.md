# The pitch

Source material for the video, the slides and the written statements. Everything
here is either true of the current design or marked as still to verify. Never put
a number in the video that we have not measured.

## One line

Bob is brilliant when it works alone. But teams don't work alone. When several
developers run Bob on the same project at the same time, the agents crash into
each other and nobody finds out until it's too late. **Agent Bobs lets them see
each other — and stops them before they collide.**

## The problem, as a story

Three of us work on one project, each with Bob in Agent mode, at the same time:

- aig's Bob is cleaning up the login code.
- jay's Bob is adding password reset.
- kim's Bob is writing tests for user accounts.

All three touch the same area, and none of them knows the other two exist. aig's
Bob renames `get_user` to `fetch_user`. At the same moment, jay's and kim's Bobs
write new code that calls `get_user`. Each agent did its job correctly. Together,
the project is broken.

**And Git will not warn us.** Git only reports a conflict when two edits touch the
same lines. The rename is in one file; the new callers are in others. Git merges
everything and reports zero conflicts. The code fails later, when someone runs it.

## Why Bob can't solve this by itself

This is the first question a judge will ask.

Bob does coordinate several agents — inside one developer's session. Its
subagents run in parallel, each in its own context, and report back to one main
conversation. Bob's documentation describes a subagent as an independent agent
that "runs in its own isolated context window, executes its assigned work, and
returns a summary of the results back to the main conversation"
([Bob docs: Subagents](https://bob.ibm.com/docs/ide/features/subagents)).

That is one conductor with one orchestra, and it works well. Our problem is three
orchestras in three rooms who can't hear each other. Bob sees your repo and your
task; it has no way to know another Bob is running on another machine. The
problem lives *between* sessions, so it needs a layer above all of them.

## What we built

- **The brain** — one small server that every Bob session connects to over MCP.
  It records what each session is about to touch: the files, the functions it
  will change, and the functions it will call.
- **The rules** — a custom Bob mode tells Bob to declare its plan before writing
  code, and Bob's lifecycle hooks enforce it: before *every* file write, Bob
  itself checks with the server, and refuses the write if another Bob holds that
  file.
- **The face** — a live dashboard with one column per Bob. When two collide, both
  columns turn red and say why.

We **prevent** the crash instead of reporting it afterwards: with the hook in
place, the conflicting write never happens.

## The 30-second answer

"Every Bob session tells one small server what it's about to touch. Before a Bob
writes any file, Bob itself checks with that server — and if another Bob is
already there, Bob refuses the write and tells the developer. A dashboard shows
all of it live."

## One collision, step by step

1. aig asks their Bob to clean up the login code. In our custom mode, Bob first
   claims its plan: the file `auth/user.py`, changing `get_user`.
2. The server finds nobody else there and records the claim. aig's column
   appears on the dashboard.
3. jay's Bob, adding password reset, claims its plan: a new file `auth/reset.py`
   that calls `get_user`.
4. The server sees that aig is changing a function jay calls, and answers
   "conflict — aig is renaming get_user, which jay calls". jay's Bob stops and
   tells jay. Both columns turn red.
5. kim's Bob, writing tests, also calls `get_user`, and is caught the same way.
6. jay and kim both only *call* `get_user`, so they never conflict with each
   other. The tool doesn't cry wolf.
7. When aig's Bob finishes, its claims are released. jay and kim go back to
   green and continue, now knowing the new name.

Throughout, the hook guards every write: if any Bob tries to write a file that
another Bob holds, Bob refuses it.

## What we detect

| Collision | How it's caught |
|---|---|
| Two Bobs editing the same file | their file claims overlap — and the hook blocks the write |
| One Bob changing a function another Bob changes or calls | their function claims overlap |

Two Bobs that only call the same function are correctly left alone.

Stretch goals, only if time allows: two Bobs each writing their own version of
the same helper; an `ast` check of the written file that catches calls an agent
forgot to declare.

## The demo

Three Bob sessions run three tasks designed to collide, on three copies of the
sample app, on one laptop. Then we show two things side by side:

- **Git says:** 0 conflicts — the real `git merge` output — followed by the real
  test failure.
- **Agent Bobs says:** the collisions, caught before the bad code was written.

We run it twice, without Agent Bobs and then with it, and quote only what we
measured.

## Prior art — we do not claim novelty

Coordination tools already exist for other AI coding assistants: wit,
agent-coord, CoordMCP, grit, git-paw, agentic-git. The research goes back much
further:

- **Palantír** — workspace awareness and early detection of conflicts from
  parallel changes (Sarma, Redmiles & van der Hoek, *IEEE TSE*, 2012)
- **Crystal** — speculative detection of collaboration conflicts (Brun et al.,
  *ESEC/FSE* 2011)
- **FASTDash** — a live awareness dashboard for software teams (Biehl et al.,
  *CHI* 2007)
- **Syde** — sharing change and conflict information across developers'
  workspaces (Hattori & Lanza, *ICSE* 2010)
- **ConE** — concurrent-edit detection, deployed on 234 repositories at
  Microsoft (Maddila et al., *ACM TOSEM*, 2022)

Tools like GitLive already show you what teammates are editing live. Our
difference: those are built for humans watching humans, at human speed. Agent
Bobs is built for agents, which move too fast to watch — and it acts on the
information instead of only displaying it.

**Our position:** coordination tooling exists for other coding assistants, but
none of it is Bob-native. Agent Bobs is built on Bob's own custom modes, MCP,
lifecycle hooks and AGENTS.md. That is our niche, and we say so openly.

## What we say openly

- The demo runs three Bob sessions on one laptop; we don't have three machines on
  a shared network. The server speaks streamable HTTP, which Bob supports across
  machines, but we have not demonstrated that.
- Function-level detection relies on each Bob declaring the functions it changes
  and calls. The hook guarantees file-level protection only.
- Agent Bobs is not a new idea. It is a Bob-native answer to a known problem.

## Never claim

- That it is novel, or the first of its kind.
- Any number we have not measured — collisions caught, seconds, time saved.
- That it works across machines, as though we had shown it.
- That it catches everything.

## Verify before this goes into the video

- [ ] When Bob's Stop hook fires — Person 3 is testing it. It decides whether
      claims are released when a task ends or after every reply.
- [ ] The demo's real numbers: collisions caught, and how quickly.
- [ ] The control run's real `git merge` output and test failure.
- [ ] The exact submission requirements and deadline, from the lablab form.
