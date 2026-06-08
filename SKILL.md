---
name: lins-living-loop
abbreviation: LLL
description: Use this skill whenever the user asks for Lin's Living Loop, LLL, living loop, DOP, Deep Orchestration Protocol, 深度编排协议, 深度调研, 深入研究, 重型任务, 长时任务, 可恢复执行, 并行 agent, background agent, durable work, or complex multi-step work likely to cause context explosion, API timeouts, upstream instability, long-running execution, workspace reuse, or nontrivial validation. This skill turns chat into a lightweight supervisor, keeps the filesystem as the durable source of truth, chooses the simplest reliable carrier, requires synthesis plus independent validation, keeps human outputs under output/ and process state under internal/, and treats skills/workflows as living procedural memory that can repair itself without sacrificing reliability.
version: 1.0.0
author: Lin
license: MIT
metadata:
  lll:
    formerly: DOP — Deep Orchestration Protocol
    tags: [ai-agents, orchestration, durable-workflows, file-backed, research, validation, recovery]
---

# Lin's Living Loop / LLL

Lin's Living Loop (LLL) is a tiny file-backed living loop for durable AI-agent work. It is formerly DOP — Deep Orchestration Protocol.

LLL is not a fantasy taxonomy and not a heavy orchestration framework. It is a compact way to make serious work survive interruption: deep research, engineering, writing, investigation, large comparisons, long validation, multi-agent execution, and any task where chat history is too fragile to be the only source of truth.

Core sentence:

The filesystem is where the work lives. The chat is only the current interface. The agent is the caretaker of the next loop.

The old DOP name is still valid as a compatibility alias. The technical core remains the same: plain files before databases, small scripts before frameworks, handoffs before long chat summaries, independent validation before delivery, and upgrade paths only when the simple path stops being enough.

Runtime-specific carriers such as synchronous subagents, schedulers, managed background processes, independent agent CLIs, code agents, or durable boards belong in adapters and examples. The canonical worker task area is `internal/agents/<task-id>/`: current agent, subagent, script, CLI agent, human, scheduler job, or board worker. When resuming older DOP workdirs, transitional `collab/agents/<task-id>/` and legacy root-level `agents/<task-id>/` have the same worker meaning, but new workdirs should use the `internal/` + `output/` layout.

LLL optimizes for the smallest durable system that handles most long-task needs. The Living part is the surface and discipline: work has a body, a state, wounds, repairs, validation, and a next loop. The reliability part stays boring on purpose.

## Use / do not use

Use LLL when:
- The user explicitly says LLL, Lin's Living Loop, DOP, 深度调研, 重型任务, 长时任务, 深度编排, 可恢复, 不要爆上下文, 并行执行, background agent, durable worker, or similar.
- The task has multiple tracks such as research, coding, synthesis, review, or validation.
- The task may outlive one turn, one request, or one stable API call.
- The result must be auditable, reproducible, resumable, or suitable for later continuation.
- The main agent would need to carry too much raw material.
- Correctness depends on a separate review or validation pass.

Do not use full LLL for simple Q&A, quick searches, tiny edits, or tasks safely completed in a few tool calls. If unsure, choose LLL-lite: a small workdir, task list, handoffs, and validation, without a runner or extra framework.

## Living loop

The public loop is:

```text
Seed -> Split -> Work -> Trace -> Heal -> Validate -> Hand off -> Grow or Close
```

Mapping:

| LLL step | File-backed action |
|---|---|
| Seed | Write or update `mission.md` |
| Split | Decompose `internal/tasks.jsonl` and worker `task.md` |
| Work | Workers write artifacts and logs |
| Trace | Keep claims/evidence in `output/91-traceability.md` |
| Heal | Record workflow wounds and repairs in `output/90-error-report.md` |
| Validate | Write `internal/validation-report.md` |
| Hand off | Refresh `internal/handoff.md` and `internal/recovery-state.md` |
| Grow or Close | Update `output/99-next-steps.md` and choose continuation/completion |

## Default new workdir; reuse only with a clear signal

Default to a fresh LLL workdir. Do not proactively scan old LLL/DOP/PWF directories just because a similar task may have been done before; finding and judging a reusable workspace costs time, tokens, and attention. The default should be flexible, not archival.

A path to an old LLL/DOP workdir is not by itself a reuse signal. The user may provide old workdir paths as examples, evidence, comparison material, or raw input for a new task. If the request is about learning from or optimizing based on a previous practice, create a fresh workdir and record the old path under `internal/inputs/` unless the user explicitly says to continue/reuse that old workspace.

Reuse only when there is a clear reuse signal:
- the user provides an existing workdir path together with explicit continuation/recovery intent, such as 继续, 接着, 复用, 基于这个目录继续, 恢复, 修复这个工作区, audit this workdir, or add to this run;
- the user explicitly says 上次/上一轮/上一个对话/之前那个任务/刚才那个任务/继续/接着/补充/补充信息/复用/同一件事/基于刚才;
- the user interrupts or follows up on an in-progress LLL task to correct assumptions, add preferences, explain tool policy, ask about an intermediate detail, or supply extra constraints; treat that as an addendum to the active task and resume the prior workflow after absorbing the new information, rather than starting a fresh workdir;
- the user pastes prior progress logs, agent/tool transcript fragments, LLL/DOP status text, or a workdir-like path from another conversation and asks to continue, repair, or add information;
- the current message is a correction or addendum to a task from the previous chat/session, even if the workdir path is not provided;
- this is the same conversation and the topic is highly related, such as a small correction, follow-up validation, or immediate refinement of the work just produced;
- the current task is explicitly about recovering, auditing, repairing, or continuing an existing LLL/DOP/PWF workspace.

When the user gives a cross-conversation reuse signal but no path, do not start a fresh workdir or ask them to repeat the path. Search recent sessions first (for repo names, task keywords, or LLL/DOP/workdir terms) and, if needed, search likely workdir roots such as `~/lll-work/` to locate the latest matching workspace. If one clear match is found, resume it; if multiple plausible matches exist, ask one short disambiguation question.

If the user merely asks a similar question later, says something like “此前已经运行过一次” without asking to continue it, or provides an old workdir path as reference material, do not automatically search for or reuse old workdirs. Create a fresh workdir unless the user gives a clear continuation instruction. If reuse would materially help but the signal is ambiguous, ask one short question or proceed with a fresh workdir and label the assumption.

When reuse is chosen, reuse is not blind appending. First read `mission.md`, the layout-specific recovery file (`internal/recovery-state.md`, transitional root `recovery-state.md`, or legacy root equivalent), the layout-specific queue/registry (`internal/tasks.jsonl` and `internal/agent-registry.md`, transitional `collab/...`, or legacy root files), relevant `output/` deliverables (or transitional `readable/`, legacy `deliverables/`), and relevant worker `handoff.md` files. Then classify the new request as one of:
- extension: same mission, additional scope;
- correction: prior output or assumption needs repair;
- workflow addendum: the user interrupts or follows up to clarify tool policy, install policy, output expectations, style, or execution preferences for the active task; absorb the preference/correction, patch memory/skills if durable, then resume the original task from the existing workdir;
- new evidence: add or re-check sources;
- validation follow-up: fix a FAIL/PASS_WITH_NOTES issue;
- mission change: objective changed enough to risk mixing unrelated evidence.

For reuse, add a mission addendum, append traceable tasks/events, and integrate new deliverables with old context. Dynamically maintain `output/00-index.md` and all `output/9x-*.md` audit files: error reports and traceability are append-only; `output/99-next-steps.md` should be updated to the current state because the previous suggested action may already have been completed. Create a new workdir when the mission changed, old evidence would contaminate the new task, the old workdir is inaccessible/corrupt, the reuse signal is weak, or the user explicitly asks for a new run.

## Minimal workdir

Use a self-contained directory. If no project directory is specified, default to `~/lll-work/YYYYMMDD-HHMMSS_short-description-in-kebab-case/`. Use `-` between date and time, then `_` between the timestamp and short description: `YYYYMMDD-HHMMSS_short-description-in-kebab-case`. The timestamp is one field, the underscore separates it from the semantic slug, and slug words use ASCII hyphens. Avoid `YYYYMMDD_HHMMSS_slug` for new workdirs because the extra underscore makes the name look like three fields instead of timestamp + description. Do not place new LLL runs under legacy PWF storage such as `~/hermes-pwf-record/` unless the user explicitly requests PWF or asks to resume an existing PWF workspace.

Canonical v2 layout for new workdirs:

```text
<lll-workdir>/
  mission.md                    # only root file by default: objective, success criteria, constraints, done definition
  internal/                      # agent/runner collaboration state; humans usually do not start here
    tasks.jsonl                  # current durable queue
    runs.jsonl                   # append-only event log
    agent-registry.md            # worker/status/output map
    recovery-state.md            # compact resume instructions
    handoff.md                   # compact internal handoff for future supervisors
    validation-report.md         # independent validation verdict and evidence
    inputs/                      # raw/reference materials introduced during the run
    logs/supervisor.log
    logs/runner.log
    agents/<task-id>/
      task.md                    # exact assignment and output contract
      status.json                # task-local current state
      log.txt                    # commands, sources, decisions, failures, retries
      handoff.md                 # short worker handoff
      artifacts/                 # detailed evidence, raw data, reports, diffs
  output/                        # human-facing outputs; start here when reading results
    00-index.md                  # required table of contents; indexes every output file
    01-<deliverable>.md          # primary numbered deliverables for stable sorting
    02-<deliverable>.md
    90-error-report.md           # required append-only internal workflow/runtime abnormalities, repairs, and self-maintenance log
    91-traceability.md           # required append-only claim/source/change trace map
    99-next-steps.md             # required mutable current next actions
```

Keep the root shallow. For new workdirs, root should generally contain only `mission.md`, `internal/`, and `output/`. Put raw repositories, source dumps, scraped pages, long logs, validation, recovery state, final/internal handoffs, and other process files under `internal/`. Put only human-facing deliverables under `output/`.

Existing layouts remain valid for resume:
- Transitional v1: `collab/` for process state, `readable/` for human outputs, with root `recovery-state.md`, `handoff.md`, and `validation-report.md`.
- Legacy v0: root-level `tasks.jsonl`, `runs.jsonl`, `agent-registry.md`, `logs/`, `agents/`, and `deliverables/`.

Do not migrate old workdirs unless the user asks or migration itself is the task. New helper/template output should use v2.

Number human-facing outputs in `output/` with two-digit prefixes so file listings preserve reading order:
- `00-index.md`: must index every file in `output/`, including audit and next-step files.
- `01`-`89`: primary reports, summaries, decisions, source notes, designs, or user-facing artifacts.
- `90-error-report.md`: append-only internal workflow/runtime abnormality, repair, and self-iteration report. Create it by default; if no such workflow/runtime errors occurred, say so explicitly.
- `91-traceability.md`: append-only mapping from claims/changes to evidence, commands, files, validation notes, or assumptions.
- `92`-`98`: optional audit/debug/review files.
- `99-next-steps.md`: mutable current recommendations for what the user can do next.

Human-facing `output/` prose should default to the user's explicitly requested output language; if none is specified, use the current interaction language. Treat this as a hidden product default, not a status banner: do not add `language_rule`, `interaction_language`, or `output_language` markers to `mission.md` or `output/` files merely to announce the language. Record language only when it is a real task constraint, such as user-requested non-default language, bilingual deliverables, translation work, or cross-language handoff risk. Keep filenames, JSON keys, commands, API names, code identifiers, external proper nouns, and stable template markers in English when that improves portability; write the explanatory body of reports, indexes, error reports, traceability notes, and next-step files in the chosen human language unless the user asks otherwise.

Append-only files need timestamped entries. Keep `created_at` and, for every appended section/row, include `ts`/`timestamp` or an ISO-8601/RFC3339 timestamp in the heading/table row. Prefer the user's known timezone; otherwise use the runtime/system local timezone with an explicit offset (for example `+08:00`). Do not default to UTC `+00:00` merely because Python or a backend makes UTC easy. If local/user timezone cannot be determined, UTC is acceptable but label it explicitly. This is important for reuse: future supervisors can read only the latest entries while preserving audit order.

Link aggressively but only when links will stay useful:
- Use Markdown link syntax: `[label](target)`.
- Link process-generated files inside the LLL workdir with relative paths from the current file, for example `[worker handoff](../internal/agents/T001/handoff.md)` or `[traceability](91-traceability.md)`.
- Link stable external resources with absolute paths or URLs, for example `[source](https://example.com/report)` or `[local dataset](/abs/path/data.csv)`.
- Do not hyperlink external temporary/user-mentioned files if their location may move; mention them as plain text with enough identifying context instead.
- Prefer `output/91-traceability.md` for audit-grade traceability. If sources themselves are a primary user deliverable, create a normal `02-sources.md` as well and still keep claim-level traceability in `91-traceability.md`.


## Project and source-of-truth hygiene

When LLL is used to create, publish, or maintain a reusable skill, GitHub repo, package, or long-lived project, keep work records and project source code separate:

- `~/lll-work/` is for LLL run/work records only: `mission.md`, `internal/`, `output/`, logs, handoffs, temporary inputs, and validation records.
- Do not put a long-lived Git repo directly under `~/lll-work/` unless the user explicitly asks. Default reusable projects/repos to `~/projects/<repo-slug>/` or a user-specified project directory.
- If a local installed skill should track a canonical repo, prefer a symlink from the installed skill path to the canonical repo over copying the repo into multiple skill directories. Multiple copies drift and can make skill loading ambiguous.
- Avoid duplicate installed skills with the same `name` frontmatter across local skill roots. If duplicates are required for different runtimes, document which one is canonical and keep the others as symlinks or generated copies.
- Legacy names such as DOP may remain as thin aliases or compatibility shims, but they should not become a second source of truth for the same living workflow.

## Reuse/correction archival discipline

On a reused workspace, especially after the user points out mistakes or asks for corrections, the conversation is not the archive. The workspace is. The goal is human-recoverable state, not creating a new file for every chat turn.

- Keep the current human-facing state recoverable from `output/`: update the relevant numbered deliverable, audit file, index, or next-step file so the latest conclusion is not trapped in chat.
- Do not mechanically create a new numbered deliverable for every reuse/correction. Use the human deliverable lifecycle below: small corrections update the existing primary deliverable plus traceability as needed; a new `02-*`, `03-*`, etc. is only for an independently readable analysis, decision, evidence packet, task result, or phase conclusion.
- Update `output/00-index.md` whenever the recommended reading entry, current conclusion, or output file list changes.
- Append to `output/90-error-report.md` for workflow mistakes, wrong assumptions, failed commands, missing records, or repairs.
- Append to `output/91-traceability.md` with evidence for claims, file moves, commits, validation commands, and install checks.
- Update `output/99-next-steps.md` to the current next actions; do not leave stale previous recommendations as the latest state.
- The final chat response should summarize and link paths; it should not be the only place where the result exists.

## Worker record completeness

A task marked `done` in `internal/tasks.jsonl` or `internal/agent-registry.md` must have a non-empty `internal/agents/<task-id>/` record. At minimum include:

```text
internal/agents/<task-id>/
  task.md
  log.txt
  handoff.md
  status.json
```

This applies even when the “worker” was the supervisor doing the work inline rather than a spawned subagent. Empty done directories are a workflow error: repair them before final delivery, and record the repair in `output/90-error-report.md`.

## Human deliverable lifecycle on reuse

Use a mixed strategy instead of always appending to one final report or always creating a new file:

- Keep `output/01-final-report.md` (or the mission's `01-*` primary deliverable) as the current main conclusion for the same mission/stage.
- Update that primary deliverable when the reuse request is a correction, clarification, style cleanup, small supplement, or rewrite of the same deliverable.
- Create the next numbered deliverable (`02-*.md`, `03-*.md`, etc.) when the reuse request produces an independently readable analysis, design decision, new task result, new evidence packet, or new phase conclusion.
- Keep `output/00-index.md` responsible for navigation: mark the current recommended reading entry and distinguish "current conclusion" from historical or supplementary deliverables.
- Do not turn `01-final-report.md` into a chronological transcript. Put audit history in `output/91-traceability.md`; put workflow errors in `output/90-error-report.md`; put current actions in `output/99-next-steps.md`.

Use ASCII-safe directory names. Worker-facing prose and intermediate artifacts should default to the user's language / current interaction language. Use English when it materially improves correctness or portability: code identifiers, JSON keys, file names, CLI commands, API names, external proper nouns, quoted source concepts, or user-specified English output.

## Mission maintenance

`mission.md` is the current task contract, not a one-time kickoff note. Keep it compact and current so workspace reuse starts from files rather than chat history.

Maintain these fields near the top, rendered as a visible fenced metadata block so Markdown renderers preserve line breaks:

```text
created_at: <local/user-timezone timestamp with explicit offset>
updated_at: <refresh whenever mission constraints/success criteria/outputs/status/scope change>
status: <initialized|active|blocked|completed|archived>
```

After final validation and delivery, mark `status` as `completed`.

Do not add mandatory language metadata fields to `mission.md`. If language is explicitly part of the task, record it as an ordinary constraint or expected-output note rather than as a repeated product label.

Keep the main sections (`Objective`, `Success criteria`, `Constraints`, `Inputs`, `Expected outputs`, `Execution policy`) as a mutable current snapshot. When the user adds scope, corrects assumptions, changes output expectations, or gives durable workflow preferences during a reused/active DOP run, update the relevant snapshot section and add a short timestamped entry under `## Mission addenda`. Do not turn mission into a full transcript; put detailed evidence in `internal/` and detailed audit chains in `output/90-error-report.md` / `output/91-traceability.md`.

On reuse, read and update `mission.md` before launching new work: refresh `updated_at`, set status back to `active` if work resumes after completion, append a brief addendum for the new request, and update success criteria/expected outputs if the done definition changed.

## Hard invariants

Do not violate these:

1. Write or update `mission.md`, the layout-specific recovery file, the layout-specific queue (`internal/tasks.jsonl` for v2), and the worker task file before launching long work.
2. Workers write detailed work only under `internal/agents/<task-id>/` unless explicitly assigned a shared human deliverable under `output/`.
3. Shared state files (`internal/tasks.jsonl`, `internal/runs.jsonl`, `internal/agent-registry.md`, `internal/recovery-state.md` in v2) have one writer: the supervisor or a real runner. Workers do not edit them directly unless the task explicitly grants ownership and there is a lock or runner API.
4. Raw data, long logs, evidence, drafts, repositories, downloaded references, and debugging material go under `internal/`; keep worker `handoff.md` short. Artifacts should be durable but not reckless: avoid writing secrets, tokens, private account dumps, or unnecessary huge raw blobs; redact, summarize, or store pointers plus checksums/metadata when appropriate.
5. Synchronous subagents are not durable/background workers; if the parent turn is interrupted, they can be cancelled.
6. When assigning work to a child worker, assume it may not have loaded this DOP skill. Include a compact LLL contract inline instead of only saying "use LLL":
   - Read `mission.md`, your `internal/agents/<task-id>/task.md`, and listed inputs.
   - Treat the workdir as the source of truth; chat is only a short handoff.
   - Write detailed work, logs, evidence, drafts, and outputs under `internal/agents/<task-id>/` unless explicitly assigned a shared deliverable under `output/`.
   - Write the assigned artifact skeleton early, then fill it incrementally. For deep-reading/research workers, do not wait until the end to write the artifact or handoff; synchronous subagents can hit iteration/tool limits after doing useful reading, and unwritten work is not durable.
   - Do not edit shared state files unless explicitly granted ownership through a lock or runner API.
   - Keep `handoff.md` short: status, output paths, key findings, risks/blockers, next step.
   - Keep claims traceable to artifact paths, sources, commands, or validation notes.
   - If blocked, record what was tried and propose the smallest fallback.
   - If writing human-facing outputs, update or request an update to `output/00-index.md`.
   - If you create task files with a helper or template, verify the generated `task.md` itself contains this compact contract; do not assume a separate prompt template will always travel with the task.
7. Runtime-specific carriers are examples/adapters, not the protocol. Keep brand/tool details in adapter notes, project rules, presets, or environment context.
8. For long-running, multi-stage, background, or multi-worker LLL work, provide brief progress updates distinct from final reports.
9. `scripts/lll.py` is an optional file helper, not a durable runner, daemon, or dispatcher.
10. Structure validation is not mission validation. A parseable workdir does not mean the task is correct or complete.
11. Nontrivial DOP requires synthesis plus independent validation before final delivery.
12. If validation fails, create follow-up tasks or record an explicit blocker; do not deliver a FAIL as done.
13. Prefer the simplest reliable carrier and upgrade only when the simpler form is insufficient.

## Naming and product-surface evolution

The public name and metaphor may evolve without changing the core protocol. When the user asks about renaming or publicly packaging DOP as Lin's Living Loop / LLL, or about making the workflow feel more "Living" and less like a cold protocol, first load `references/lins-living-loop-renaming.md`. Treat `Lin's Living Loop` as a serious draft direction centered on living work, repair, continuation, and self-iteration. If the user asks for analysis only or says not to modify the skill yet, create a fresh draft workspace (prefer `~/lll-work/<timestamp>_<slug>/`) and do not patch live skill files until explicitly approved. Keep old DOP names and historical `~/dop-work/` directories compatible during any transition; use `~/lll-work/` for new work records.

## Runtime environment and adapters

Do not hardcode the user's agent stack into LLL's core. Before choosing carriers, inspect the available runtime if possible: tools, CLIs, profiles, schedulers, background process support, project rules, and global agent context. If stable agent-environment facts are missing from the user's global context, help the user record them in the appropriate place for each agent/runtime, with user approval when needed.

Keep DOP portable: the skill describes the protocol; environment-specific mappings live in memory, project rules, wrapper scripts, presets, or adapter references. Concrete Hermes/Codex/cron/Kanban mappings are useful examples when configured, not universal requirements.

## Optional local skill memory

LLL's public skill stays portable. User-specific and environment-specific preferences may live in a single optional local overlay file next to `SKILL.md`:

```text
SKILL.local.md
```

This file is local-only and should be gitignored. If it exists, read it near the start of nontrivial LLL work after `SKILL.md`; if it does not exist, continue without asking the user to create it. Treat it as defaults and context, not as the run's source of truth. When a local preference materially affects the current run, copy the relevant decision into `mission.md`, `output/91-traceability.md`, or `internal/handoff.md` so recovery does not depend on hidden local state.

Before writing any durable preference, identify the user's real intent and choose the right layer:

| Preference type | Write to |
|---|---|
| LLL-specific workflow preferences, local environment facts, adapter choices, or recurring skill-use defaults | `SKILL.local.md` |
| General user preferences that apply across many skills or tasks, such as tool-selection philosophy or communication style | the agent's global user memory/profile |
| General LLL defects, weak triggers, missing pitfalls, better verification, or portable workflow improvements | `SKILL.md` or a tracked reference/template |
| Current task facts, decisions, evidence, and validation state | the current LLL workdir |

If the layer is unclear, ask the user a short clarification question instead of guessing. Keep entries compact, declarative, and durable; do not store secrets, transient task progress, commit hashes, PR numbers, or stale-in-a-week artifacts.

Recommended `SKILL.local.md` shape:

```markdown
# Local memory for Lin's Living Loop

<!-- Local-only. Gitignored. Separate entries with a line containing only: ⟲ -->

LLL-specific preference or environment fact, written as one concise declarative note.

⟲

Another concise note.
```

Use `⟲` as the entry separator: it evokes the living loop, is uncommon in normal prose, and avoids overloading the section sign used by some agent memory stores.

## Execution flow

1. Clarify only if missing information would make the work unsafe or obviously wrong.
2. State important side effects briefly: file writes, network/API calls, background processes, code execution, Git changes, external services.
3. If `SKILL.local.md` exists next to this `SKILL.md`, read it for local/user-specific defaults; otherwise skip it silently.
4. Create a fresh workdir by default, or resume only with a clear reuse signal.
5. Decompose into orthogonal tasks with explicit outputs and acceptance checks.
6. Choose the lightest carrier for each task.
7. Launch work; make workers write files and return short handoffs.
8. Keep supervisor context small: read `mission.md`, `internal/` queue/registry/handoffs, `output/` synthesis/audit files, validation, and selected artifacts only when needed.
9. Synthesize from files.
10. Validate independently.
11. Record errors/lessons and self-maintenance actions in `output/90-error-report.md` even when issues were fixed inline.
12. Before final packaging, check that `output/` body text follows the user-specified output language or current interaction language, without surfacing language metadata unless language itself is part of the task.
13. Ensure `mission.md`, `output/00-index.md`, `output/91-traceability.md`, and `output/99-next-steps.md` are current before final delivery.
14. Final reply points to deliverables and a short conclusion.

## Progress updates

For long-running, multi-stage, background, or multi-worker LLL tasks, provide brief progress updates that are clearly distinct from final reports.

Default to a visible rough percentage when there is any meaningful multi-step work, because it reduces user uncertainty while the supervisor is busy. Prefer this shape:

```text
进行中｜约 45%
当前阶段/新发现。下一步：<next action or blocker>。
```

Use `进度更新｜约 N%` when reporting a phase transition after work is already underway, and `进行中｜约 N%` for quick waiting-state pings. The exact label may vary, but include the approximate percent unless the work is too open-ended to estimate honestly.

Estimate coarsely from phase completion, not from token use or elapsed time. Good anchors: 10% skill/context loaded; 20-30% workdir and decomposition ready; 40-60% workers/data collection underway; 70-85% synthesis/patching/fixes underway; 90-95% validation/final packaging; 100% only after final delivery. Use rounded values such as 15/30/45/60/75/90, not fake precision like 47%.

Use progress updates when starting a long phase, switching phases, a background worker finishes or fails, a key discovery/blocker/validation result changes the plan, or the user has been waiting for a while. Keep updates short: 1-3 lines with the current phase or rough progress, what changed or was learned, and the next action/blocker/relevant artifact path.

Avoid noisy updates for every command or log line. Do not paste raw logs into chat. If the percent is uncertain, say `约` and explain the uncertainty briefly rather than hiding the percent. Final reports remain separate and should include deliverables, validation verdict, conclusion, and caveats.

Example:

```text
进度更新｜约 65%
实现 worker 已写入 handoff，结构检查通过；验证发现 1 个测试失败。下一步先定位失败原因，再决定修复或记录 blocker。
```

## Carrier escalation ladder

Use the lightest reliable carrier:

| level | carrier | use when |
|---|---|---|
| 0 | current supervisor/runtime | planning, small edits, synthesis, quick validation |
| 1 | synchronous subagent / short parallel worker | bounded parallel reasoning inside the current turn |
| 2 | foreground script/command | deterministic commands under a few minutes |
| 3 | managed background process/script | long bounded tests, crawls, builds, batch jobs |
| 4 | independent agent CLI / specialist agent | long research, writing, coding, or analysis that can write durable files |
| 5 | thin file-backed runner | many tasks need retries, leases, checkpoints, or reclaim |
| 6 | durable board / DB / orchestration framework | long project, worker fleet, human interjection, strong durability |

Do not default to LangGraph, Temporal, Celery, Kanban, a database, or a daemon. They are upgrade paths or adapters, not LLL's default core. If the user fixes a carrier, such as a specific code agent for coding, treat it as given and design coordination rather than re-comparing every tool.

For concrete commands and fallbacks, load `references/adapters.md`.

## Synthesis and validation

Use a synthesis worker when there are multiple substantive outputs, conflicts, or a final report/decision. Synthesis reads mission, registry, worker handoffs, and only selected artifacts; it writes final human deliverables, audit files, and next-step files under `output/`.

Every nontrivial LLL task needs an independent validation pass by someone other than the producer of the final artifact.

Validate two layers:

1. Structure validation: required files exist, JSONL parses, task ids/statuses/dependencies are valid, task output paths stay under the layout-specific worker directory (`internal/agents/<task-id>/` for v2), per-task files exist, output files are numbered and indexed, required audit files exist, and tasks/registry/status do not drift. When `scripts/lll.py` is available, run it against the final/resumed workdir before delivery; treat helper validation as baseline structure validation unless it explicitly implements the stricter checklist in `references/minimal-runner.md`. If old structural debt appears, repair it honestly with evidence-labeled recovery notes rather than fabricating missing history, then re-run validation.
2. Mission validation: outputs satisfy mission success criteria, numbered `output/` deliverables exist, claims trace to linked evidence, assumptions are labeled, failed/blocked tasks were handled, code/tests/builds ran or failures are documented, the error/traceability/next-step files are current, and the result is useful without raw intermediate context.

Verdicts:
- `PASS`: deliverables satisfy the mission criteria, required validation ran, remaining caveats are absent or truly trivial.
- `PASS_WITH_NOTES`: deliverables are useful and satisfy the mission well enough to deliver, but there are explicit non-blocking notes such as baseline-only structure checks, same-runtime rather than stronger independent validation, minor queue/registry drift, thin intermediate evidence, skipped optional checks, or caveats the user should know. This is a pass, not a failure; the notes must be visible and non-blocking.
- `FAIL`: mission criteria are not met, required deliverables are missing, important claims are unverified or contradicted, tests/builds/checks fail in a blocking way, or security/safety issues prevent delivery.

If `FAIL`, write concrete follow-up tasks and continue if possible. If `PASS_WITH_NOTES`, final delivery is allowed, but include the notes and any recommended follow-up.

## Self-iteration and error reports

Treat every editable skill as living procedural memory, not a static document.

Create `output/90-error-report.md` by default for meaningful DOP runs, especially any run that changes workflows, skills, tools, or user-facing procedures. If no internal workflow/runtime abnormalities or repairs occurred, the file should explicitly say no meaningful workflow/runtime errors were recorded. Do not omit the file just because everything went well.

During LLL, `output/90-error-report.md` records internal workflow/runtime abnormalities and their repairs, not the user's goals. Record failed assumptions, worker failures, adapter/quoting/tool issues, path-safety issues, validation failures, queue/registry drift, stale or missing skill guidance, weak triggers, and better verification methods. A user correction belongs here only when it reveals that the workflow violated an existing contract or made a wrong internal assumption. New user goals, scope additions, design decisions, and normal requirements belong in `mission.md` addenda, `internal/tasks.jsonl`, `output/91-traceability.md`, or a numbered deliverable instead. Small issues may be fixed directly, but meaningful workflow-relevant corrections should still be logged. Complex unresolved workflow issues or optional follow-up work should also appear in `output/99-next-steps.md`.

Use `output/90-error-report.md` entries with:
- what happened;
- evidence/path;
- impact;
- fix or fallback used;
- what should be patched in a skill, memory, script, template, or adapter.

After validation, decide explicitly:
- patch an existing skill now;
- create a new skill after user confirmation;
- update durable memory for stable user/environment facts;
- or record why no self-maintenance action is needed.

For LLL itself, this loop is mandatory: LLL should improve from its own failures.

## Recovery quickstart

When resuming:
1. Read `mission.md`, the layout-specific recovery file (`internal/recovery-state.md` for v2), queue, registry, and recent event log tail.
2. Identify done, active, blocked, failed, pending, and stale tasks.
3. Check background processes/jobs if possible.
4. Reclaim stale in-progress tasks only after checking lease/heartbeat/process/log evidence.
5. Read relevant worker `handoff.md` files before raw artifacts.
6. Read `output/00-index.md`, then only the relevant human-facing/audit files.
7. Continue from the last safe checkpoint.
8. Update recovery state before launching new work.
9. If reusing the workspace, update `output/00-index.md`, append local-timezone timestamped entries to `output/90-error-report.md`/`output/91-traceability.md` as needed, and rewrite `output/99-next-steps.md` to the current next action.

Recover from files, not chat history, unless files are missing.

Internal append-only files are a context-engineering surface, not just logs. Treat these as append-only by design: `internal/runs.jsonl`, `internal/logs/*.log`, `internal/agents/<task-id>/log.txt`, and any explicitly named `internal/**/events.jsonl`, `journal.md`, or `history.md`. Do not routinely read them in full on resume. Prefer status snapshots and compact handoffs first (`mission.md`, `internal/recovery-state.md`, `internal/tasks.jsonl`, `internal/agent-registry.md`, `internal/agents/*/status.json`, `internal/agents/*/handoff.md`), then read only the tail, entries since the last checkpoint, or entries for a specific task/time window. If a log grows large, add or refresh a compact snapshot/handoff rather than forcing every future agent to ingest the full append-only history.

Queue authority rule: `internal/tasks.jsonl` owns scheduling state in v2; `internal/agents/<task-id>/status.json` is worker-local progress/evidence. If they drift, read `handoff.md`, `log.txt`, and artifacts, then have the supervisor or runner reconcile the queue rather than letting workers edit shared queue state directly. For transitional or legacy workdirs, use the equivalent `collab/` or root paths.

## Final response

Match the user's language. Keep the chat response short unless the user asked for the full report inline.

```text
完成。DOP 工作已通过/部分通过验收。

工作目录：<path>
主要产出：
- <output/01-final-report.md or primary output path>
- <output/90-error-report.md>
- <output/91-traceability.md>
- <output/99-next-steps.md>
- <internal/validation-report.md>

一句话结论：<short conclusion>
注意事项：<0-3 caveats>
可继续：<optional next actions>
```

Do not paste huge reports into chat; put them in numbered files under `output/`.

## Resources

Load only when needed:
- `references/adapters.md`: concrete carriers, Hermes/Codex/terminal/cron/Kanban examples, and fallbacks.
- `references/minimal-runner.md`: helper vs runner, task/event schemas, `internal/` state placement, single-writer rules, strict structure validation, helper quickstart, and legacy compatibility.
- `references/observability-recovery.md`: detailed logging, recovery, validation failure loop, and error/lessons reports.
- `references/validator-pass-patterns.md`: validator-only boundaries, PASS_WITH_NOTES patterns, safe environment/secret checks, and concise validation handoff shape.
- `references/hermes-permissions-config.md`: Hermes Agent config/credential/control-plane permission model and safe config-change adapter.
- `references/dop-lite-vs-pwf-defaults.md`: user-specific defaulting guidance.
- `references/session-lessons-2026-06-07.md`: historical design lessons.
- `references/workdir-ux-migration.md`: checklist for changing LLL workdir layout, human-readable outputs, link policy, templates, helper scripts, and legacy compatibility together.
- `references/output-language-and-append-only.md`: session lesson for output prose language, timestamped append-only files, internal append-only classification, and token-cost-aware resume reads.
- `references/session-lessons-2026-06-08-metadata-naming.md`: session lesson for timestamp separator consistency, fenced metadata blocks, helper/template smoke tests, and output index self-entry checks.
- `references/product-surface-noise-and-reuse-output.md`: product-surface guardrails for hidden defaults, Error Report scope, reused-workspace numbered deliverables, and analyze-only handling.
- `references/lins-living-loop-renaming.md`: user-approved draft direction for rebranding DOP as Lin's Living Loop / LLL, including the Living theme, naming stack, workdir root, concept mapping, and migration stance.
- `templates/workdir/`, `templates/task/`, `templates/prompts/`: starter files and worker prompt patterns.
- `scripts/lll.py`: optional stdlib file helper for init/add-task/status/set-status/event/checkpoint/structure validation. `scripts/dop.py` is kept as a compatibility shim for old docs and habits.
