---
name: lins-living-loop
abbreviation: LLL
description: Use this skill whenever the user asks for Lin's Living Loop, LLL, living loop, DOP, Deep Orchestration Protocol, 深度编排协议, 深度调研, 深入研究, 重型任务, 长时任务, 可恢复执行, 并行 agent, background agent, durable work, or complex multi-step work likely to cause context explosion, API timeouts, upstream instability, long-running execution, workspace reuse, or nontrivial validation. This skill turns chat into a lightweight supervisor, keeps the filesystem as the durable source of truth, chooses the simplest reliable carrier, puts human deliverables at the workdir root beside mission.md, keeps process/audit state under internal/, enforces that human-facing deliverable prose follows the user's requested/current interaction language instead of silently falling back to English templates, and treats skills/workflows as living procedural memory that can repair itself without becoming ceremonial.
version: 1.2.1
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

Context-drift rule: when the chat/tool context is large, long-running, or likely to be compacted, externalize the task contract before doing more substantive work. Update `mission.md`, `notes.md` or a root deliverable, `internal/recovery.json`, and validation/audit files so the filesystem—not the model's current attention—is the source of truth for objective, constraints, decisions, current status, and acceptance checks.

Context-budget rule: do not create a parallel root-level context recovery system inside an LLL workdir. Keep the current restore order and next action in `internal/recovery.json`; put optional budget/risk state in `internal/context-budget.json` only when a CLI/runner consumes it. Root files should remain `mission.md` and human-facing deliverables/product docs, not duplicate process state.

Workflow semantic-layer rule: when a task introduces richer workflow concepts—Matter, Decision, Approval, Artifact, Asset, Presentation View, Execution Projection, typed gates, or promotion policy—treat them as semantic layers on top of the LLL workdir, not as a competing runtime state system. Root Markdown/HTML deliverables are Presentation Views. Kanban, GitHub, runners, Feishu, and similar systems are Execution Projections only when they can link back to the LLL workdir and sync/write state safely. Closeout should classify outputs as accepted deliverables, asset candidates, archived evidence, or pruned noise. Do not add a new workflow root, task root, context root, or event root beside LLL unless a real CLI/runner consumes it and the authority boundary is explicit.

Machine-state format rule:
- current singleton snapshots use JSON (`recovery.json`, `validation.json`, task `status.json`);
- row-oriented collections and append-only history use JSONL (`tasks.jsonl` may be atomically rewritten; `runs.jsonl`, `error-report.jsonl`, and `traceability.jsonl` append);
- Markdown/HTML are for human-facing deliverables or genuinely free-form natural-language contracts/handoffs, not machine state disguised as prose;
- agents decide; `lll` CLI/scripts perform deterministic, atomic structured-state mutation;
- YAML is for human-authored declarative configuration when needed, not runtime state;
- add SQLite only after real cross-Matter query, concurrency, transaction, or latency pressure appears; JSON/JSONL remain the portable protocol boundary.

## Mode selection: structure mode vs carrier

LLL has two orthogonal decisions:

| axis | choices | answers |
|---|---|---|
| Structure mode | no LLL, LLL Lite, full LLL | How much durable workspace, state, validation, and recovery surface is needed? |
| Loop preset | none, Code Loop | Is the task a repeated develop/run/verify/fix loop that needs lease/retry/checkpoint semantics? |
| Carrier / adapter | inline supervisor, delegated worker, command/job, runner/orchestrator | What actually executes each unit of work in this environment? |

Choose the structure mode first, add Code Loop only when the work is truly iterative, then choose the lightest reliable carrier. Code Loop is not a fourth structure mode; it is a runner-oriented preset layered on an LLL workdir.

## Code Loop mode

Use Code Loop mode when the user asks for continuous coding, long-running coding agents, repeated develop/test/fix loops, coding runner/daemon behavior, or Ralph-loop-like workflows.

Default behavior:
1. Assume the human delegates goals, constraints, and acceptance criteria; the Agent operates the CLI. Human-facing commands are fallback documentation, not the primary UX.
2. Discover whether a reference LLL CLI or equivalent runner is available before starting long unattended work.
3. Keep LLL as the protocol: create or reuse a normal LLL workdir with `mission.md` and `internal/` state.
4. Compile the coding objective into one or more `code-loop` tasks with explicit `--command`, `--verify`, safety boundary, repo/cwd, max attempts, and delivery policy.
5. Prefer the independent `lll` CLI reference implementation, or an equivalent file-backed runner, for machine lifecycle. For agent-first parsing, use JSON/status forms where available.
6. Let the runner manage lease/timeout/retry/artifacts/status; let the supervising agent or human remain responsible for judgment, synthesis, validation, and user-facing handoff.
7. Environment-specific wrappers may discover/proxy LLL workdirs and check module health, but they must not duplicate or own the LLL state machine.

Boundary: the skill teaches agents when and how to use LLL/Code Loop; the CLI is the reference implementation; executors such as shell/Hermes/Claude/Codex are replaceable adapters. Do not turn the skill into the runtime or the CLI into a planning brain.

Use **full LLL** when the work has multiple independent research objects, multiple execution tracks, long-running/background work, large evidence, or separate producer/validator roles. For research tasks where the user asks for multiple directions, divergent search, deep research, or parallel agents, treat full LLL as the default and launch independent research directions concurrently where the carrier supports it.

Use **LLL Lite** for single-track work where one agent can finish without context explosion. Lite is still file-backed, but it should stay visibly simple: `mission.md`, maybe `notes.md`, maybe one root deliverable, and optional `internal/validation.json`. If the current conversation is already large, Lite is the minimum drift guard even when the task has only one track. Do not manufacture worker directories when there were no real workers.

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
| Validate | Validator writes evidence; supervisor records the canonical verdict with `lll validation set` |
| Hand off | Refresh `internal/recovery.json`; keep free-form worker handoffs task-local |
| Grow or Close | Put current next steps inside the primary deliverable or relevant deliverable |

## Default new workdir; reuse only with a clear signal

Default to a fresh LLL workdir. Do not proactively scan old LLL/DOP/PWF directories just because a similar task may have been done before.

A path to an old workdir is not by itself a reuse signal. Reuse only when there is explicit continuation/recovery intent, such as 继续, 接着, 复用, 基于这个目录继续, 恢复, repair this workdir, audit this workdir, add to this run, or an immediate same-conversation correction/addendum to the active run.

When reuse is chosen, read the compact current state first:
1. `mission.md`
2. `lll status <workdir> --json --compact` when available; it projects task counts/records plus `recovery.json` and `validation.json` without creating another stored truth
3. otherwise read `internal/recovery.json`, `internal/validation.json`, and `internal/tasks.jsonl`
4. relevant `internal/agents/<task-id>/status.json` and `handoff.md`
5. top-level task-specific deliverables
6. tails/slices of `internal/traceability.jsonl`, `internal/error-report.jsonl`, and logs only as needed

Classify the new request as extension, correction, workflow addendum, new evidence, validation follow-up, or mission change. Update `mission.md`, append JSONL audit entries, and update/rewrite the relevant root deliverable. Create a new workdir when the mission changed enough that old evidence would contaminate the new task.

For a narrow correction or analytical addendum on an existing completed workdir, scale execution to the delta instead of replaying the original run topology. Reuse frozen inputs and deterministic scripts. Default to one canonical producer path (which may be the inline supervisor) plus one independent validator. Multiple producer workers are justified only by genuinely independent evidence searches or materially different methods—not by writing the same files, manufacturing perspectives, or preserving archival symmetry.

Older layouts remain resumable with loose detection only:
- transitional: `collab/` + `readable/`;
- legacy: root `tasks.jsonl`, `runs.jsonl`, `agent-registry.md`, `agents/`, `deliverables/`.

Legacy/transitional layouts remain discoverable, but LLL 0.2 full validation expects the current JSON machine-state format. On an explicit continuation, migrate the active workdir once; never dual-write old Markdown state and new JSON state. Leave unrelated archived workdirs untouched.

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
    recovery.json               # canonical current resume snapshot
    validation.json             # canonical current validation verdict/evidence pointers
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

Use a simple audience model when deciding what to write or link:
- **User deliverables**: root Markdown outputs that satisfy the main request for normal use; link these in final replies.
- **Auxiliary readable files**: optional deep-dive reports, worker/subagent outputs, evidence summaries, or detailed appendices for careful review; link them from the relevant deliverable when they help, not just because they exist.
- **Machine state files**: queues, JSONL event streams, logs, status probes, raw tool output, and other recovery/audit state; keep them under `internal/` and do not present them as user deliverables.

This is an audience model, not a new directory layout. Preserve the shallow root/`internal/` workdir unless a specific task genuinely needs more structure.

Human-facing prose follows the user's explicitly requested output language; if none is specified, use the current interaction language. Treat this as a hidden default, not metadata. Keep filenames, JSON keys, commands, API names, code identifiers, and stable external proper nouns in English when useful.

This applies to root deliverables such as release summaries, synthesis reports, architecture notes, validation summaries intended for the user, README-style handoffs, and any worker output assigned as a human-facing artifact. Internal scaffolding and template headings may start in English, but copied/generated template prose must be localized before final delivery. A human-facing deliverable in the wrong language is a workflow error and must be repaired or explicitly recorded as a blocker before closing the loop.

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
- When the `lll` CLI is available, prefer `lll audit append <workdir> --stream error|trace ...` over rewriting JSONL files by hand; it adds timestamps and appends one valid JSON object.
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

A task marked done in `internal/tasks.jsonl` must have a non-empty worker record:

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

1. Write/update `mission.md`, `internal/recovery.json`, the queue when used, and worker `task.md` before launching long work. If context is already large or compaction is likely, refresh the file-backed contract before continuing. In Lite, use compact `mission.md` plus `notes.md` or a root deliverable instead of a fake queue.
2. Workers write detailed work only under `internal/agents/<task-id>/` unless explicitly assigned a shared root deliverable.
3. Shared state files (`internal/tasks.jsonl`, `internal/runs.jsonl`, `internal/recovery.json`, `internal/validation.json`) have one writer: the supervisor or a real runner; use the CLI where a mutation command exists. Queue mutation must refresh the queue pointer/watermark/nonterminal summary in `recovery.json` under the same queue lock; `tasks.jsonl` remains the task-state owner and recovery stores only the compact discoverability projection.
4. Raw data, long logs, evidence, drafts, repositories, downloads, and debugging material go under `internal/`.
5. Synchronous subagents are not durable/background workers; if the parent turn is interrupted, they can be cancelled.
6. Child worker prompts must include the compact LLL contract: read mission/task/inputs, write under assigned directory, keep handoff short, keep claims traceable, do not edit shared state unless granted, and record blockers with fallback. When the worker will materially contribute to a completed LLL task, explicitly require or have the supervisor finalize the root-level worker record (`task.md`, `status.json`, `log.txt`, `handoff.md`) in addition to files under `artifacts/`; an artifact plus an artifact-local handoff alone is not a complete done record.
   - For read-only reviewers of a shared non-Git Worksite, prompt-only write boundaries are advisory, not isolation. Prefer a read-only snapshot/copy, worktree, sandbox, or tool-level write restriction. If the carrier cannot enforce one, freeze the validation surface with a manifest/hash, keep the supervisor as the only intended writer, and treat any sibling/shared-write warning as possible contamination: stop concurrent edits, read back affected targets, record the incident, and revalidate the final frozen surface.
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
8. Choose the lightest honest carrier for each task: inline supervisor, delegated worker, command/job, or runner/orchestrator.
9. Launch work; make workers write files and return short handoffs. When a runtime supports batching independent synchronous workers, launch independent tasks together instead of serializing them. Sequential child calls are only acceptable when later tasks depend on earlier outputs, or when rate limits/tool constraints require serialization; otherwise record the reason in the handoff or error log.
   - When creating tasks with the reference CLI, `--priority` takes an integer, not labels such as `high`.
   - `lll task add --out` is the worker root and must be exactly `internal/agents/<task-id>/`; put report files below it. Do not pass `artifacts/`, a nested directory, or a filename.
   - Name one canonical producer for each shared/root deliverable. Parallel workers may supply evidence or critique, but should not each rebuild the same analyzer, report, or canonical state unless independent implementation is the stated validation method.
10. Keep supervisor context small: read compact state and handoffs first; read raw artifacts only when needed.
11. Synthesize into one or more root deliverables.
12. Append traceability and error JSONL entries as needed.
13. Validate independently.
14. After a validator-only pass, run a supervisor closeout loop: consume the verdict, repair safe structural gaps, check the language of every human-facing root deliverable against the requested/current interaction language, update the validation task, record the canonical verdict through `lll validation set`, refresh `mission.md` and `internal/recovery.json`, and append trace/error JSONL entries as needed. Then run `lll closeout <workdir> --json --write-report`. Do not deliver while validation is pending, expected worker handoffs are missing, or a primary human-facing deliverable is in the wrong language.
15. Ensure `mission.md`, root deliverables, `internal/traceability.jsonl`, `internal/error-report.jsonl`, `internal/validation.json`, and `internal/recovery.json` are current before final delivery.
16. Final reply points to deliverables and gives a short conclusion.

## Progress updates

For long-running, multi-stage, background, or multi-worker LLL tasks, provide brief progress updates distinct from final responses.

Default shape:

```text
进行中｜约 45%
当前阶段/新发现。下一步：<next action or blocker>。
```

Estimate coarsely from phase completion, not token use or elapsed time. Use rounded values such as 15/30/45/60/75/90. Avoid noisy updates for every command or log line.

## Carrier escalation ladder

Keep the product-level carrier model small. Specific runtimes can map these buckets to their own tools.

| level | carrier bucket | use when |
|---|---|---|
| 0 | inline supervisor | planning, small edits, synthesis, quick validation |
| 1 | delegated worker | bounded parallel research, critique, synthesis, validation, or specialist execution that can write durable files |
| 2 | command/job | deterministic scripts, tests, crawls, builds, scheduled checks, or long bounded jobs |
| 3 | runner/orchestrator | many tasks need leases, retries, checkpoints, recovery, human block/unblock, or long project coordination |

Do not default to databases, daemons, boards, distributed workflow engines, or project-management systems. They are optional adapters inside the runner/orchestrator bucket, not core LLL concepts.

## Subagent load-shedding and fallback

When using synchronous delegated workers on a custom endpoint or any provider that shows stream errors, slow responses, retries, or API instability, treat the model/API as a scarce shared runtime:

1. Keep child prompts and scope small: bounded candidate counts, explicit stop conditions, short handoffs, and selected evidence instead of full raw dumps.
2. Prefer deterministic supervisor scripts for mechanical search/fetch/filter steps; reserve delegated workers for judgment and synthesis.
3. If one worker fails from upstream timeout/stream error, record it in `internal/error-report.jsonl`, reduce scope or concurrency before retrying, and avoid launching an identical large retry.
4. If a retry fails for the same runtime reason, stop retrying that carrier and switch to inline supervisor, scripted collection, background job, or a different model/provider if available.
5. For research runs, cache raw evidence under `internal/` but pass/read only compact excerpts into model calls. Large README/source dumps should be filtered by scripts before entering worker context.
6. Final reports must distinguish workflow failure from evidence absence: a failed worker is not proof that no project/source exists.
7. A missing or late chat completion summary is not proof that the worker failed. Before retrying or switching carriers, inspect the assigned `status.json`, `handoff.md`, expected artifacts, and recent file timestamps. If durable outputs satisfy acceptance, consume them and close the task without relaunching.
8. Keep at most one active carrier for the same logical role. Before fallback, mark the earlier attempt completed, failed, cancelled, or superseded in the single-writer task state; late outputs from a superseded attempt are evidence to review, not permission to overwrite shared state.

## Synthesis and validation

Use a synthesis worker when there are multiple substantive outputs, conflicts, or a final synthesis/decision. Synthesis reads mission, task state, worker handoffs, and selected artifacts; it writes root deliverables and JSONL audit entries.

Every nontrivial LLL task needs an independent validation pass by someone other than the producer of the final artifact.

Start the final validator only after the canonical producer has frozen the validation surface. Record the target deliverable paths and, when practical, content hashes or a generation/version marker in the validator task or producer handoff. If the producer changes a target afterward, that verdict is stale: repair the target, update the frozen marker, and rerun the one validator rather than layering a second validator on a moving artifact.

For security-sensitive public release work—especially publishing a repository, package, skill, installer, or template derived from private/local materials—use multiple independent validation perspectives by default. A good minimum is: one deterministic/scripted scan by the supervisor plus at least two independent validator workers with different prompts or emphases, such as secret/privacy leakage, install/runtime safety, and mission/usefulness. If only one validator is practical, record the reason in `internal/error-report.jsonl` or the validation report.

Delegated validators are real LLL workers even when they are synchronous subagents. Create `internal/agents/<validation-task-id>/` records for them (task, status, handoff/log or summary, and any artifacts) or explicitly record why a lighter inline validation was chosen. Do not let `internal/` imply “single-agent work” when subagents materially contributed to safety or correctness.

Validate two layers:
1. **Structure validation**: required files exist, JSONL parses, task ids/statuses/dependencies are valid, task output paths stay under the worker directory, per-task files exist for real tasks, no obsolete new-layout `output/` surface exists, and validation/handoff files exist before final delivery.
2. **Mission validation**: outputs satisfy success criteria, root deliverables exist when needed, human-facing prose uses the chosen language, important claims trace to evidence, assumptions are labeled, failed/blocked tasks were handled, code/tests/builds ran or failures are documented, and the result is useful without raw intermediate context.

For a continued correction/addendum, validate the changed/active surface plus the current canonical recovery/validation snapshots. Do not normalize or backfill unrelated historical worker records solely to make a newer CLI accept an older run. If a full-workdir structure check reports a legacy-only gap that does not compromise the current delta, record it as a compatibility caveat; repair history only when it is needed for current auditability or recovery.

Verdicts:
- `PASS`: deliverables satisfy the mission criteria.
- `PASS_WITH_NOTES`: deliverables are useful and satisfy the mission well enough to deliver, but caveats are visible and non-blocking.
- `FAIL`: mission criteria are not met or blocking checks failed.

If `FAIL`, create follow-up tasks or record an explicit blocker; do not deliver a FAIL as done.

## Self-iteration and error reports

Treat every editable skill as living procedural memory. LLL should improve from its own failures.

During LLL, `internal/error-report.jsonl` records internal workflow/runtime abnormalities and repairs, not user goals. Record failed assumptions, worker failures, adapter/quoting/tool issues, path-safety issues, validation failures, queue/status drift, stale/missing skill guidance, weak triggers, and better verification methods.

After the basic task is complete and validation has produced a usable verdict, run a lightweight workflow retrospective before final delivery. Inspect the current run's workflow reports — especially `internal/validation.json`, `internal/error-report.jsonl`, `internal/traceability.jsonl`, worker handoffs/logs when relevant, and the root deliverable shape — and ask what the run teaches about the workflow itself. Look for repeatable improvements: clearer triggers, better decomposition, stronger validation, safer fallback paths, smaller context surfaces, better evidence capture, missing templates/scripts, or unnecessary ceremony that should be removed.

Close the loop with one explicit self-maintenance decision: patch an existing skill when the improvement is procedural and reusable; create a new skill only after user confirmation; update durable memory only for stable user/environment preferences; or record in the validation report / handoff why no self-maintenance action is needed. Keep this retrospective small: it should strengthen future LLL runs without turning every task into a meta-project.

## Recovery quickstart

1. Read `mission.md`, `internal/recovery.json`, task/status state, and recent event-log tail.
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

LLL's public skill stays portable. User-specific and environment-specific preferences may live in a local-only `SKILL.local.md` next to `SKILL.md`. If it exists, read it near the start of nontrivial LLL work. Treat it as defaults and context, not as the run's source of truth. When a local preference materially affects the current run, copy the relevant decision into `mission.md`, a root deliverable, `internal/recovery.json`, or `internal/traceability.jsonl`.

## Final response

Match the user's language. Keep the chat response short unless the user asked for the full report inline.

```text
完成。LLL 工作已通过/部分通过验收。

工作目录：<path>
主要产出：
- <primary root deliverable, named from the task>
- <internal/error-report.jsonl>
- <internal/traceability.jsonl>
- <internal/validation.json>

一句话结论：<short conclusion>
注意事项：<0-3 caveats>
可继续：<optional next actions already reflected in the report>
```

Do not paste huge reports into chat; put them in root deliverables. In the final response, link only artifacts that are meant for the user's current reading or next action. Internal process files under `internal/` are recovery/audit state; do not surface them by default, duplicate them into user-facing summaries, or make them previewable just because they exist. Mention internal checks only as brief status when useful, such as validation/closeout passed.

## Resources

Load only when needed:
- `references/adapters.md`: concrete carrier mappings, runtime-specific examples, and fallbacks.
- `references/minimal-runner.md`: helper vs runner, task/event schemas, current layout, single-writer rules, validation, and compatibility stance.
- `references/observability-recovery.md`: logging, recovery, validation failure loop, and JSONL error/trace records.
- `references/validator-pass-patterns.md`: validator-only boundaries, PASS_WITH_NOTES patterns, safe environment/secret checks, and concise validation handoff shape.
- `references/workdir-ux-migration.md`: checklist for changing LLL workdir layout, templates, helper scripts, and legacy compatibility together.
- `references/output-language-and-append-only.md`: output prose language and append-only JSONL discipline.
- `references/product-surface-noise-and-reuse-output.md`: product-surface guardrails for hidden defaults, error report scope, and reuse deliverables.
- `references/session-lessons-2026-06-15-compact-layout-jsonl.md`: concrete lesson for compact root deliverables, removing `output/`/index/next-step scaffolding, JSONL audit logs, and generator-surface migration checks.
- `references/session-lessons-2026-06-15-lll-trigger-vs-execution.md`: concrete lesson that loading the LLL skill is not enough; non-trivial/large-context work should use at least LLL Lite and externalize the task contract before context drift.
- `references/session-lessons-2026-06-15-validation-closeout.md`: historical validator-only closeout lesson; current protocol records canonical verdict/recovery through JSON and CLI.
- `references/session-lessons-2026-06-16-source-research-traceability.md`: source-research runs should append traceability records for fixed inputs and top-level claims before closeout.
- `references/session-lessons-2026-06-16-community-evidence-research.md`: community/forum evidence research should use reliability tiers, label blocked/search-snippet evidence as weak, record absence-of-evidence, and separate practical reports from source/architecture analysis.
- `references/session-lessons-2026-06-16-commercial-agent-ecosystem-research.md`: commercial/forked agent ecosystem comparisons should separate entry, execution, state, and governance layers; treat self-hosted systems as sovereign state/control layers when long-term memory, auditability, migration, or AI-OS goals matter.
- `references/session-lessons-2026-06-17-aios-kit-friend-install.md`: one-key friend/new-machine deployment for AIOS kits should include a root installer, temp-HOME smoke install, runtime-skill fallback validation for independent first-party skills, bounded install retries, and post-push remote-surface checks.
- `references/lins-living-loop-renaming.md`: naming and product-surface direction.
- `templates/workdir/`, `templates/task/`, `templates/prompts/`: starter files and worker prompt patterns.
- `scripts/lll.py`: optional stdlib file helper for init/add-task/status/set-status/event/checkpoint/structure validation. `scripts/dop.py` is a compatibility shim.
