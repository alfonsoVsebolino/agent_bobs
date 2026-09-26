# Submission

Official — from the lablab event page, checked Sun 27 Sep, 00:20 PHT.

**Deadline: Sunday 27 September, 11:00 PM Philippine time** (11:00 AM ET,
15:00 UTC). Aim to submit by **9:00 PM**: the video has to upload, and our
connections are slow.

## What to submit

| Deliverable | The rules | Owner |
|---|---|---|
| **Demo video** | MP4 or MOV, up to 300 MB. **3 minutes maximum** — judges stop watching at 3:00. At least **90 seconds** must show the solution working on screen. Show clearly how IBM Bob was used, **with narration**. | Abrahm |
| **Long Description** | Problem & solution statement, **500 words or less**: the problem; what the solution is; who it's for and how they use it; why it's creative and unique; how it addresses the problem in a new way. | Abrahm |
| **IBM Bob Usage Statement** | **500 words or less**: how and where the team used IBM Bob, specifically, throughout development. | Abrahm, from everyone's notes |
| **Public repo + Bob screenshots** | A public link to the repo. **Each team member's** Bob task session summary screenshots in the repo — our `bob_sessions/`. No IBM Cloud credentials anywhere in the repo. | everyone |

For the Bob Usage Statement, each person sends Abrahm two or three sentences on
how they used Bob. Describe each piece by what actually built it: the statement
can be checked against the task summaries in `bob_sessions/`.

## Judging criteria

No weights are published.

| Criterion | Official wording | Where we answer it |
|---|---|---|
| **Application of Technology** | How complete and well thought-out the project is, with a clear application of IBM Bob 2.0. | Bob-native design: MCP server, custom mode, lifecycle hooks, AGENTS.md — and built with Bob, as `bob_sessions/` shows |
| **Presentation** | The clarity and effectiveness of the project presentation. | the video: "git: 0 conflicts" next to the live dashboard catching the collision |
| **Business Value** | The impact and practical value, considering how effectively the solution addresses a high-priority issue. | the measured control run vs. the Agent Bobs run |
| **Originality** | The uniqueness and creativity of the solution and the approach in applying IBM Bob 2.0 to address the stated issue. | the approach: Bob-native, and it prevents the collision instead of reporting it. We don't claim the idea itself is new — see the prior art in `PITCH.md` |

## Video plan (3:00 maximum)

| Time | What |
|---|---|
| 0:00–0:30 | The problem: three Bobs, one repo — git sees nothing |
| 0:30–2:15 | **The demo, on screen** (the rule asks for at least 90 s): the control run's clean merge and failing tests, then the same three tasks with Agent Bobs catching the collision live |
| 2:15–2:45 | How Bob built it and how it runs inside Bob: modes, MCP, hooks |
| 2:45–3:00 | Close |
