# Agent Bobs

**When one Bob isn't alone.** When several developers run IBM Bob on the same
project at the same time, their agents can't see each other, and they break each
other's work in ways Git never reports. Agent Bobs lets every Bob session see the
others, and stops a Bob before it writes over another Bob's work.

Built by team **iMAGIC** for the IBM Bob 2.0 Hackathon, 25–27 September 2026.

> **This repo is the only source of truth.** The two PDFs from before the event
> ("Agent Bobs" and "Workflow") are out of date — several details in them have
> changed. Where this repo and a PDF disagree, the repo wins.

## Start here

1. [`AGENTS.md`](AGENTS.md) — what we're building and the rules we build by. Bob
   reads this file automatically.
2. [`docs/ROLES.md`](docs/ROLES.md) — who does what, and your first task.
3. [`docs/DECISIONS.md`](docs/DECISIONS.md) — what changed from the PDFs, and why.
4. [`docs/PITCH.md`](docs/PITCH.md) — the story for the video and the writeup.

## Repo layout

| Folder | What | Owner |
|---|---|---|
| `server/` | the server: collision rules, MCP tools, hook endpoints, websocket | Person 1 |
| `dashboard/` | the live screen | Person 2 |
| `demo/` | the sample app we break on purpose | Person 4 |
| `demo/.bob/` | the Bob mode, MCP connection and hooks for the demo | Person 3 |
| `bob_sessions/` | every participant's Bob task summaries | everyone |
| `docs/` | roles, decisions, pitch | — |

## Status

- ✅ Server core — claim and release, collision rules, 8 passing tests
- 🔨 Server doors — MCP tools, `/api` for the hooks, `/ws` for the dashboard
- 🔨 Dashboard, Bob integration and demo app — first tasks under way

## Run the core tests

No installs needed — the core uses only Python's standard library:

    py -m server.test_core
