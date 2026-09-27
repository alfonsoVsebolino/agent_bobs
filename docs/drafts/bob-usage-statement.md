<!-- Draft for the lablab "IBM Bob Usage Statement" field — 500 words or less.
     Paste everything below the line. Each owner should confirm their paragraph
     describes how their part was really built.
     Counts: 26 distinct Bob tasks (bob_sessions/ has 27 files: Alfonso's task02 and
     task03 are two views of one task, Task Id 201e4485…), Bobcoins 12.29 + 14.43
     + 4.27 + 1.98 = 32.97. -->

---

**Bob is both how we built Agent Bobs and what Agent Bobs runs on.**

**Building it.** All four of us built our parts in Bob, from a shared AGENTS.md that every Bob loaded automatically. That kept four agents on the same architecture, data contract and scope rules without anyone pasting context.

- **Server.** Bob's Plan mode produced the server design, which we reviewed and tightened before building. Agent mode then built the collision core with tests, and later the MCP tools, the HTTP routes for the hooks and the dashboard's websocket, with an integration test that connects two MCP clients to one server. When our review found that the first core missed a three-session case, a follow-up in the same Bob task fixed it and added the test.
- **Bob integration.** Bob wrote the "Agent Bobs" custom mode and its rules, the MCP configuration and the lifecycle hooks, and created the pull request that merged them.
- **Dashboard.** Bob built the live dashboard as a single HTML file driven by the server's websocket.
- **Demo app and harness.** Bob built the sample app we break on purpose, and a harness that builds three demo copies, merges their work and runs the tests. A follow-up task fixed rebuilds on Windows, which had failed on git's read-only files.

**Running it.** The product itself runs on Bob's extension points:

- a **custom mode** whose rules make Bob declare its plan through our MCP server before it writes, and stop when there is a conflict;
- **MCP** over streamable HTTP, with our three tools auto-approved;
- **lifecycle hooks**: SessionStart gives each Bob its session name, and PreToolUse checks every file write and blocks it with exit code 2 when another Bob holds the file.

**Learning from Bob.** We tested with real Bob sessions: fifteen Bob tasks ran in our demo copies, nine without Agent Bobs and six with it. Bob's own hook logs taught us three things no document did. Its Stop event fires on every pause, so we stopped releasing claims on it. Its hook events name their fields tool_name and tool_input, unlike its documentation, so our hook reads both. And releasing claims when each Bob finished let a collision slip through, so claims now last until the work is merged. Each finding became a follow-up Bob task.

**Evidence.** bob_sessions/ holds the summaries of 26 Bob tasks from all four team members, covering about 33 Bobcoins.

We did not use watsonx.ai or watsonx Orchestrate.
