<!-- Draft for the lablab "Long Description" field — 500 words or less.
     Paste everything below the line. Abrahm owns the final wording. -->

---

**Agent Bobs — when one Bob isn't alone**

**The problem.** IBM Bob makes one developer dramatically faster. But teams don't work alone. When several developers run Bob in Agent mode on the same repository at the same time, their agents can't see each other. One Bob renames a function; another writes new code that calls the old name. Each agent does its job correctly and passes its own tests. Git merges the work cleanly, because the changes are in different files, and the code is broken. Nobody finds out until the tests fail at merge time, or later.

We measured it with three real Bobs on a sample app. Every Bob finished in under a minute and passed its own tests. Git reported 0 conflicts. The merged code failed: 84 new lines had been written against a function that no longer existed.

**The solution.** Agent Bobs is a coordination layer built into Bob itself. Every Bob session connects to one small MCP server. In our custom "Agent Bobs" mode, Bob declares its plan before it writes: the files it will edit, the functions it will change, and the functions it will call. The server compares each plan with every other session's. If one Bob is renaming a function that another Bob is about to call, the second Bob is stopped before writing a line, and tells its developer exactly who holds the function and why. A PreToolUse lifecycle hook backs this up: before every file write, Bob checks with the server, and the write is refused if another Bob holds the file. A live dashboard shows every session's plan and every collision.

With Agent Bobs, the same three tasks ended differently. Both collisions were caught at the claim, before either Bob wrote any code, and the merged tests passed.

**Who it's for.** Teams where several developers run Bob on one codebase. They add the Agent Bobs mode, the MCP connection and the hooks to their repository, run the server, and keep working as usual. Nothing changes until two Bobs are about to collide — then the second one stops and explains.

**Why it's different.** Git compares lines, not meaning, and only after the fact. Workspace-awareness tools show people what their teammates are editing, at human speed. Agent Bobs is built for agents, which move too fast to watch: it acts on a collision instead of only displaying it, and it prevents the collision rather than reporting it. It is also Bob-native — a custom mode, lifecycle hooks, an MCP server and AGENTS.md working together — and a claim lasts until the work is merged, which is the moment a rename actually reaches everyone else.

**What's next.** Releasing claims automatically when work is merged, a wait mode that lets a blocked Bob continue once the change it depends on lands, and opening the MCP server to other coding agents.
