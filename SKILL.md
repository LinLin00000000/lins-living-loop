---
name: lins-living-loop
abbreviation: LLL
description: Use this skill whenever the user asks for Lin's Living Loop, LLL, living loop, DOP, Deep Orchestration Protocol, 深度编排协议, 深度调研, 深入研究, 重型任务, 长时任务, 可恢复执行, 并行 agent, background agent, durable work, or complex multi-step work likely to cause context explosion, API timeouts, upstream instability, long-running execution, workspace reuse, or nontrivial validation. This skill turns chat into a lightweight supervisor, keeps the filesystem as the durable source of truth, chooses the simplest reliable carrier, puts human deliverables at the workdir root beside mission.md, keeps process/audit state under internal/, and treats skills/workflows as living procedural memory that can repair itself without becoming ceremonial.
version: 1.1.1
author: Lin
license: MIT
metadata:
  lll:
    formerly: DOP — Deep Orchestration Protocol
    tags: [ai-agents, orchestration, durable-workflows, file-backed, research, validation, recovery]
---

# Lin's Living Loop / LLL

Lin's Living Loop is a tiny file-backed living loop for serious AI-agent work. It is formerly DOP — Deep Orchestration Protocol.

Core sentence:

> The filesystem is where the work lives. The chat is only the current interface. The agent is the caretaker of the next loop.

LLL is intentionally boring at the machine layer: plain files before databases, small scripts before frameworks, handoffs before long chat summaries, independent validation before delivery, and upgrade paths only when the simple path stops being enough.

The current layout is deliberately shallow: `mission.md` and human deliverables live at the workdir root; process state, workers, logs, traceability, and error records live under `internal/`. New workdirs do **not** create `output/`, `00-index.md`, or a standalone Next Steps file.

## Use / do not use

Use LLL when:
- the user explicitly says LLL, Lin's Living Loop, DOP, 深度调研, 重型任务, 长时任务, 深度编排, 可恢复, background agent, durable worker, or similar;
- the task has multiple tracks such as research, coding, synthesis, review, or validation;
- the task may outlive one turn, one request, or one stable API call;
- the conversation/tool context is already large enough that hidden assumptions may drift (long transcript, many tool outputs, context compaction risk, or the user explicitly mentions context drift / 外部文件契约);
- the result must be auditable, reproducible, resumable, or suitable for later continuation;
- correctness depends on separate review or validation.

Do not use full LLL for simple Q&A, quick searches, tiny edits, or tasks safely completed in a few tool calls. If unsure, choose the smallest honest mode that preserves the work without pretending to have more process than actually ran.

Important: loading this skill is not the same as using LLL. For non-trivial skill/repo/workflow edits—especially changes touching several files, scripts, templates, docs, validation, or git commit/push—create at least an LLL Lite workdir (`mission.md` + compact notes/validation) rather than substituting a chat todo list for durable state.

Context-drift rule: when the chat/tool context is large, long-running, or likely to be compacted, externalize the task contract before doing more substantive work. Update `mission.md`, `notes.md` or a root deliverable, `internal/recovery-state.md`, and validation/audit files so the filesystem—not the model's current attention—is the source of truth for objective, constraints, decisions, current status, and acceptance checks.

## Mode selection: structure mode vs carrier

LLL has two orthogonal decisions:

| axis | choices | answers |
|---|---|---|
| Structure mode | no LLL, LLL Lite, full LLL | How much durable workspace, state, validation, and recovery surface is needed? |
| Carrier / adapter | current supervisor, subagent, script, background process, independent agent CLI, scheduler, thin runner, Kanban/board | What actually executes each unit of work? |

Choose the structure mode first, then the lightest reliable carrier.

Use **full LLL** when the work has multiple independent research objects, multiple execution tracks, long-running/background work, large evidence, or separate producer/validator roles.

Use **LLL Lite** for single-track work where one agent can finish without context explosion. Lite is still file-backed, but it should stay visibly simple: `mission.md`, maybe `notes.md`, maybe one root deliverable, and optional `internal/validation-report.md`. If the current conversation is already large, Lite is the minimum drift guard even when the task has only one track. Do not manufacture worker directories when there were no real workers.

## Living loop

```text
Seed -> Split -> Work -> Trace -> Heal -> Validate -> Hand off -> Grow or Close
```

| LLL step | File-backed action |
|---|---|
| Seed | Write/update `mission.md` |
| Split | Decompose `internal/tasks.jsonl` and, for real workers, `internal/agents/<task-id>/task.md` |
| Work | Workers write artifacts and logs under `internal/agents/<task-id>/` |
| Trace | Append claim/source/change records to `internal/traceability.jsonl` |
| Heal | Append workflow/runtime abnormalities and repairs to `internal/error-report.jsonl` |
| Validate | Write `internal/validation-report.md` |
| Hand off | Refresh `internal/handoff.md` and `internal/recovery-state.md` |
| Grow or Close | Put current next steps inside the primary deliverable or relevant deliverable |

## Default new workdir; reuse only with a clear signal

Default to a fresh LLL workdir. Do not proactively scan old LLL/DOP/PWF directories just because a similar task may have been done before.

A path to an old workdir is not by itself a reuse signal. Reuse only when there is explicit continuation/recovery intent, such as 继续, 接着, 复用, 基于这个目录继续, 恢复, repair this workdir, audit this workdir, add to this run, or an immediate same-conversation correction/addendum to the active run.

When reuse is chosen, read the compact current state first:
1. `mission.md`
2. `internal/recovery-state.md`
3. `internal/tasks.jsonl` and `internal/agent-registry.md`
4. relevant `internal/agents/<task-id>/status.json` and `handoff.md`
5. top-level task-specific deliverables
6. tails/slices of `internal/traceability.jsonl`, `internal/error-report.jsonl`, and logs only as needed

Classify the new request as extension, correction, workflow addendum, new evidence, validation follow-up, or mission change. Update `mission.md`, append JSONL audit entries, and update/rewrite the relevant root deliverable. Create a new workdir when the mission changed enough that old evidence would contaminate the new task.

Older layouts remain resumable with loose detection only:
- transitional: `collab/` + `readable/`;
- legacy: root `tasks.jsonl`, `runs.jsonl`, `agent-registry.md`, `agents/`, `deliverables/`.

Do not migrate old workdirs unless the user asks. Do not preserve redundant current-layout logic just to be compatible with old structure detection.

## Minimal workdir

Default new workdir path:

```text
~/lll-work/YYYYMMDD-HHMMSS_short-description-in-kebab-case/
```

Canonical current layout:

```text
<lll-workdir>/
  mission.md                    # current task contract
  <task-specific-name>.md        # optional primary human-facing deliverable
  <another-topic>.md             # optional additional deliverable when justified
  notes.md                      # optional Lite notes / inline supervisor notes
  internal/                     # process, audit, validation, worker state
    tasks.jsonl                 # durable queue, when full LLL or runner state is needed
    runs.jsonl                  # append-only event stream
    error-report.jsonl          # append-only workflow/runtime abnormalities and repairs
    traceability.jsonl          # append-only claim/source/change/evidence map
    agent-registry.md           # worker/status/output map
    recovery-state.md           # compact resume instructions
    handoff.md                  # compact internal handoff for future supervisors
    validation-report.md        # independent validation verdict and evidence
    inputs/                     # raw/reference materials introduced during the run
    logs/
      supervisor.log
      runner.log
    agents/<task-id>/           # only for real workers/background jobs/runner tasks
      task.md
      status.json
      log.txt
      handoff.md
      artifacts/
```

Keep `internal/` shallow. Add deeper folders only when they reduce recovery cost. Raw repositories, source dumps, scraped pages, long logs, validation, recovery state, final/internal handoffs, and process files go under `internal/`. Human-facing deliverables go at the root beside `mission.md`.

Do not create these for new workdirs:
- `output/`
- `00-index.md`
- `99-next-steps.md` / `Next Step.md` / `Next Steps.md`

## Human deliverables

Use root Markdown deliverables named from the task/content, not numeric prefixes or generic report titles. Examples: `architecture-options.md`, `validation-summary.md`, `source-notes.md`, `implementation-plan.md`. Create additional clearly named files for independently readable follow-up analyses, decisions, evidence packets, task results, or phase conclusions.

The agent should decide the number of files from content shape:
- merge into one Markdown file when the theme is coherent and the result remains readable;
- split when there are multiple independent themes, large sections, separate audiences, or files that will be reused independently;
- do not create files merely to satisfy process ceremony.

Next steps belong as a section inside the primary deliverable or the relevant deliverable. If there are no meaningful next steps, say so there or omit the section.

Human-facing prose follows the user's explicitly requested output language; if none is specified, use the current interaction language. Treat this as a hidden default, not metadata. Keep filenames, JSON keys, commands, API names, code identifiers, and stable external proper nouns in English when useful.

## JSONL audit logs

`internal/error-report.jsonl` and `internal/traceability.jsonl` are append-only logs. JSONL is preferred because these files behave like event streams: future agents can append one object to the end without rereading or rewriting the full file, and structure validation is cheap.

Recommended `internal/error-report.jsonl` object:

```json
{"ts":"<local-timezone ISO-8601>","type":"workflow_error","severity":"info|warning|error","what_happened":"...","evidence":["path-or-command"],"impact":"...","fix_or_fallback":"...","self_maintenance":"..."}
```

Recommended `internal/traceability.jsonl` object:

```json
{"ts":"<local-timezone ISO-8601>","type":"claim|source|change|validation","item":"...","evidence":["relative/path","https://example.com"],"status":"supported|assumption|validated|superseded","notes":"..."}
```

Guidelines:
- Every object includes `ts` with explicit timezone offset.
- Append only; do not rewrite history for normal updates.
- Read by tail, time window, task id, or item id on resume.
- If no issue happened, an initial `type:init` object is enough; do not manufacture a Markdown “no errors” report.
- User goals, scope additions, and normal product decisions are not errors; put them in `mission.md` addenda, root deliverables, tasks, or traceability entries.

## Mission maintenance

`mission.md` is the current task contract, not a one-time kickoff note. Keep it compact and current. Its job is to prevent context drift: a future supervisor should be able to recover the real objective, constraints, decisions, and acceptance checks from files without trusting the previous chat window.

Maintain a visible fenced metadata block near the top:

```text
created_at: <local/user-timezone timestamp with explicit offset>
updated_at: <refresh whenever mission constraints/success criteria/outputs/status/scope change>
status: <initialized|active|blocked|completed|archived>
```

Keep the main sections as a mutable current snapshot: `Objective`, `Success criteria`, `Constraints`, `Inputs`, `Expected outputs`, and `Execution policy`. When the user adds scope or corrects assumptions, update the relevant snapshot and add a short timestamped `Mission addenda` entry. Do not turn `mission.md` into a transcript.

After final validation and delivery, mark `status: completed`. If work resumes, set it back to `active` and append an addendum.

## Worker record completeness

Only create `internal/agents/<task-id>/` for real worker contexts, background jobs, independent CLIs, human contributors, runner tasks, or clearly labeled supervisor-inline tasks needed for auditability. Do not create fake Agent 1/2/3 structures when the supervisor did the work inline.

A task marked `done` in `internal/tasks.jsonl` or `internal/agent-registry.md` must have a non-empty worker record:

```text
internal/agents/<task-id>/
  task.md
  log.txt
  handoff.md
  status.json
  artifacts/
```

Empty done directories are a workflow error: repair them before final delivery and append an object to `internal/error-report.jsonl`.

## Hard invariants

1. Write/update `mission.md`, `internal/recovery-state.md`, the queue when used, and worker `task.md` before launching long work. If context is already large or compaction is likely, refresh the file-backed contract before continuing. In Lite, use compact `mission.md` plus `notes.md` or a root deliverable instead of a fake queue.
2. Workers write detailed work only under `internal/agents/<task-id>/` unless explicitly assigned a shared root deliverable.
3. Shared state files (`internal/tasks.jsonl`, `internal/runs.jsonl`, `internal/agent-registry.md`, `internal/recovery-state.md`) have one writer: the supervisor or a real runner.
4. Raw data, long logs, evidence, drafts, repositories, downloads, and debugging material go under `internal/`.
5. Synchronous subagents are not durable/background workers; if the parent turn is interrupted, they can be cancelled.
6. Child worker prompts must include the compact LLL contract: read mission/task/inputs, write under assigned directory, keep handoff short, keep claims traceable, do not edit shared state unless granted, and record blockers with fallback.
7. Runtime-specific carriers are adapters, not the protocol.
8. Nontrivial LLL requires synthesis plus independent validation before final delivery.
9. Structure validation is not mission validation.
10. Prefer the simplest reliable carrier and upgrade only when the simpler form is insufficient.

## Execution flow

1. Clarify only if missing information would make the work unsafe or obviously wrong.
2. State important side effects briefly: file writes, network/API calls, background processes, code execution, Git changes, external services.
3. If `SKILL.local.md` exists next to this file, read it for local/user-specific defaults; otherwise skip it silently.
4. Create a fresh workdir by default, or resume only with a clear reuse signal.
5. If the current context is large, first externalize the contract: objective, constraints, decisions, current status, next action, and validation criteria.
6. Decompose into orthogonal tasks with explicit outputs and acceptance checks.
7. Choose structure mode: no LLL, LLL Lite, or full LLL.
8. Choose the lightest honest carrier for each task: inline supervisor, subagent, script, background process, independent CLI, scheduler, runner, or board.
9. Launch work; make workers write files and return short handoffs.
10. Keep supervisor context small: read compact state and handoffs first; read raw artifacts only when needed.
11. Synthesize into one or more root deliverables.
12. Append traceability and error JSONL entries as needed.
13. Validate independently.
14. Ensure `mission.md`, root deliverables, `internal/traceability.jsonl`, `internal/error-report.jsonl`, and `internal/validation-report.md` are current before final delivery.
15. Final reply points to deliverables and gives a short conclusion.

## Progress updates

For long-running, multi-stage, background, or multi-worker LLL tasks, provide brief progress updates distinct from final responses.

Default shape:

```text
进行中｜约 45%
当前阶段/新发现。下一步：<next action or blocker>。
```

Estimate coarsely from phase completion, not token use or elapsed time. Use rounded values such as 15/30/45/60/75/90. Avoid noisy updates for every command or log line.

## Carrier escalation ladder

| level | carrier | use when |
|---|---|---|
| 0 | current supervisor/runtime | planning, small edits, synthesis, quick validation |
| 1 | synchronous subagent / short parallel worker | bounded parallel reasoning inside the current turn |
| 2 | foreground script/command | deterministic commands under a few minutes |
| 3 | managed background process/script | long bounded tests, crawls, builds, batch jobs |
| 4 | independent agent CLI / specialist agent | long research, writing, coding, or analysis that can write durable files |
| 5 | thin file-backed runner | many tasks need retries, leases, checkpoints, or reclaim |
| 6 | durable board / DB / orchestration framework | long project, worker fleet, human interjection, strong durability |

Do not default to LangGraph, Temporal, Celery, Kanban, a database, or a daemon. They are upgrade paths.

## Synthesis and validation

Use a synthesis worker when there are multiple substantive outputs, conflicts, or a final synthesis/decision. Synthesis reads mission, registry, worker handoffs, and selected artifacts; it writes root deliverables and JSONL audit entries.

Every nontrivial LLL task needs an independent validation pass by someone other than the producer of the final artifact.

Validate two layers:
1. **Structure validation**: required files exist, JSONL parses, task ids/statuses/dependencies are valid, task output paths stay under the worker directory, per-task files exist for real tasks, no obsolete new-layout `output/` surface exists, and validation/handoff files exist before final delivery.
2. **Mission validation**: outputs satisfy success criteria, root deliverables exist when needed, human-facing prose uses the chosen language, important claims trace to evidence, assumptions are labeled, failed/blocked tasks were handled, code/tests/builds ran or failures are documented, and the result is useful without raw intermediate context.

Verdicts:
- `PASS`: deliverables satisfy the mission criteria.
- `PASS_WITH_NOTES`: deliverables are useful and satisfy the mission well enough to deliver, but caveats are visible and non-blocking.
- `FAIL`: mission criteria are not met or blocking checks failed.

If `FAIL`, create follow-up tasks or record an explicit blocker; do not deliver a FAIL as done.

## Self-iteration and error reports

Treat every editable skill as living procedural memory. LLL should improve from its own failures.

During LLL, `internal/error-report.jsonl` records internal workflow/runtime abnormalities and repairs, not user goals. Record failed assumptions, worker failures, adapter/quoting/tool issues, path-safety issues, validation failures, queue/registry drift, stale/missing skill guidance, weak triggers, and better verification methods.

After validation, decide explicitly whether to patch a skill, create a new skill after user confirmation, update durable memory for stable user/environment facts, or record why no self-maintenance action is needed.

## Recovery quickstart

1. Read `mission.md`, `internal/recovery-state.md`, queue/registry, and recent event-log tail.
2. Identify done, active, blocked, failed, pending, and stale tasks.
3. Check background processes/jobs if possible.
4. Reclaim stale in-progress tasks only after checking lease/heartbeat/process/log evidence.
5. Read relevant worker handoffs before raw artifacts.
6. Read root deliverables relevant to the question.
7. Read JSONL audit tails/slices only as needed.
8. Continue from the last safe checkpoint.
9. Update recovery state before launching new work.

Recover from files, not chat history, unless files are missing.

## Project and source-of-truth hygiene

When LLL is used to create, publish, or maintain a reusable skill, GitHub repo, package, or long-lived project, keep work records and project source code separate:
- `~/lll-work/` is for LLL run/work records only.
- Do not put a long-lived Git repo directly under `~/lll-work/` unless the user explicitly asks.
- Default reusable projects/repos to `~/projects/<repo-slug>/` or a user-specified project directory.
- If a local installed skill should track a canonical repo, prefer a symlink from the installed skill path to the canonical repo over copying the repo into multiple skill directories.

## Optional local skill memory

LLL's public skill stays portable. User-specific and environment-specific preferences may live in a local-only `SKILL.local.md` next to `SKILL.md`. If it exists, read it near the start of nontrivial LLL work. Treat it as defaults and context, not as the run's source of truth. When a local preference materially affects the current run, copy the relevant decision into `mission.md`, a root deliverable, `internal/traceability.jsonl`, or `internal/handoff.md`.

## Final response

Match the user's language. Keep the chat response short unless the user asked for the full report inline.

```text
完成。LLL 工作已通过/部分通过验收。

工作目录：<path>
主要产出：
- <primary root deliverable, named from the task>
- <internal/error-report.jsonl>
- <internal/traceability.jsonl>
- <internal/validation-report.md>

一句话结论：<short conclusion>
注意事项：<0-3 caveats>
可继续：<optional next actions already reflected in the report>
```

Do not paste huge reports into chat; put them in root deliverables.

## Resources

Load only when needed:
- `references/adapters.md`: concrete carriers, Hermes/Codex/terminal/cron/Kanban examples, and fallbacks.
- `references/minimal-runner.md`: helper vs runner, task/event schemas, current layout, single-writer rules, validation, and compatibility stance.
- `references/observability-recovery.md`: logging, recovery, validation failure loop, and JSONL error/trace records.
- `references/validator-pass-patterns.md`: validator-only boundaries, PASS_WITH_NOTES patterns, safe environment/secret checks, and concise validation handoff shape.
- `references/workdir-ux-migration.md`: checklist for changing LLL workdir layout, templates, helper scripts, and legacy compatibility together.
- `references/output-language-and-append-only.md`: output prose language and append-only JSONL discipline.
- `references/product-surface-noise-and-reuse-output.md`: product-surface guardrails for hidden defaults, error report scope, and reuse deliverables.
- `references/session-lessons-2026-06-15-compact-layout-jsonl.md`: concrete lesson for compact root deliverables, removing `output/`/index/next-step scaffolding, JSONL audit logs, and generator-surface migration checks.
- `references/session-lessons-2026-06-15-lll-trigger-vs-execution.md`: concrete lesson that loading the LLL skill is not enough; non-trivial/large-context work should use at least LLL Lite and externalize the task contract before context drift.
- `references/lins-living-loop-renaming.md`: naming and product-surface direction.
- `templates/workdir/`, `templates/task/`, `templates/prompts/`: starter files and worker prompt patterns.
- `scripts/lll.py`: optional stdlib file helper for init/add-task/status/set-status/event/checkpoint/structure validation. `scripts/dop.py` is a compatibility shim.
