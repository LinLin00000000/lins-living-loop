# LLL adapter reference

This file maps the portable LLL protocol to concrete runtimes. Treat every command as an example. Check the local runtime/CLI help before relying on flags.

The core protocol stays runtime-independent. An adapter only answers: how do I run this worker here, how do I observe it, how do I recover from failure, and where does it write durable output?

## Adapter capability contract

Before using a carrier, confirm or record:

| capability | question |
|---|---|
| durability | Does work survive the parent chat/request ending? |
| file access | Can it read `mission.md` and write under `internal/agents/<task-id>/` (or the detected legacy worker root)? |
| observability | How do we get status, logs, pid/session/job id, and final output paths? |
| cancellation | How can it be stopped safely? |
| recovery | What files/logs/checkpoints let another supervisor resume? |
| isolation | Which files, repo/worktree, account, model, profile, or sandbox does it own? |
| progress | Can it send concise phase updates, or should it only write log/handoff files? |
| failure mode | How are errors recorded without pretending the task succeeded? |

If a carrier cannot write durable files or provide inspectable status, use it only for short, disposable work.

## Decision rule

Pick the smallest carrier that can finish reliably and write durable files.

1. Can the current supervisor finish without context bloat? Use the current runtime.
2. Is it bounded parallel reasoning that can be rerun if interrupted? Use a synchronous subagent / short parallel worker.
3. Is it deterministic or batch-like? Use a foreground script/command, or a managed background process when it may take longer.
4. Does it need long LLM judgment but can operate from prompt files? Use an independent agent CLI or specialist agent.
5. Is it recurring/watchdog/scheduled? Use a scheduler/cron method.
6. Are there many workers, human block/unblock, strong durability, or a long project board? Upgrade to a durable board or orchestration framework.

For coding tasks, use the user's configured code-agent fast path if one exists. Do not re-compare coding agents unless tool choice is the actual question.

## Current supervisor/runtime

Use for:
- mission writing
- decomposition
- queue/state ownership
- small edits or short deterministic checks
- synthesis of compact handoffs
- final user report

Keep the current supervisor as the single writer of shared LLL state unless you have a real runner/lock API.

Fallback:
- If context grows, stop reading raw details and assign synthesis/validation to another worker.

## Synchronous subagent / short parallel worker

Use for:
- short parallel research lanes
- independent critique
- quick synthesis/validation inside the current turn
- bounded reasoning where cancellation is acceptable

Rules:
- It is usually not durable. If the parent request is interrupted, child work may be cancelled.
- Tell the child to write detailed files and return only a short handoff.
- Do not use as the only carrier for must-not-stop, cross-request, or multi-hour work.
- Include the compact LLL contract inline because the child may not have loaded this skill.

Typical prompt contract:

```text
You may not have loaded the LLL skill, so follow this compact protocol.
Read mission.md and your agents/<task-id>/task.md.
Treat the workdir as the source of truth; chat is only a short handoff.
Write detailed work/logs/evidence under agents/<task-id>/.
Do not edit shared state files unless explicitly granted a lock/runner API.
Write internal/agents/<task-id>/handoff.md (or the detected legacy worker handoff) with status, output paths, key findings, risks/blockers, and next step.
Keep claims traceable to artifacts, sources, commands, or validation notes.
```

Hermes example:
- `delegate_task` is this adapter: good for bounded parallel reasoning, not durable background work.

Fallbacks:
- If the subagent times out or would run too long, convert the task to a background process or independent agent CLI.
- If it returns a long report in chat, save it to a file and summarize only paths.

## Foreground script/command

Use for deterministic commands under a few minutes: parsing, transforms, tests, checks, local searches, conversions, small crawls.

Generic example:

```bash
python scripts/check_sources.py --in agents/T010/artifacts/raw.jsonl --out agents/T010/artifacts/report.json
```

Rules:
- Write outputs under the task area or assigned deliverable path.
- Capture command, exit code, and key output in `agents/<task-id>/log.txt`.
- Do not stream huge stdout into the supervisor context.

Fallbacks:
- Command not found: locate absolute path, activate environment, or write a wrapper script.
- Output too large: write JSONL/CSV/files and return only counts/paths.

## Managed background process / long bounded job

Use for long but bounded commands: crawls, benchmarks, OCR, builds, large tests, batch jobs.

Generic shell example:

```bash
python scripts/deep_research.py --topic digital-twin --out agents/T010/artifacts/raw.jsonl \
  > agents/T010/log.txt 2>&1 &
echo $! > agents/T010/pid.txt
```

Prefer a managed process API when available because it gives status/log/cancel semantics.

Hermes example:

```python
terminal(
  command="python scripts/deep_research.py --topic digital-twin --out agents/T010/artifacts/raw.jsonl",
  workdir="<dop-workdir>",
  background=True,
  notify_on_complete=True,
)
```

For generic environments, use a process manager you can inspect: tmux, systemd user service, nohup plus pid file, a CI job, or the host agent's own background API.

Fallbacks:
- Long command blocks: split into batches or move to a scheduler/runner.
- Network/API failure: retry with backoff, cache partial results, and record failure in status/handoff.
- Process disappears: inspect logs and mark the task failed or stale before retrying.

## Independent agent CLI / specialist agent

Use when the task needs LLM judgment beyond the current request but can operate from a prompt file and write to a directory.

Generic pattern:

```bash
agent_cli --prompt-file internal/agents/T020/task.md \
  --output internal/agents/T020/handoff.md \
  > internal/agents/T020/log.txt 2>&1
```

Rules:
- Write the prompt/task file first.
- Include exact output paths and compact LLL contract in the prompt.
- Use profiles, wrapper scripts, or presets for model/tool choices instead of ad hoc flags in every task.
- Save stdout/stderr to the task log.
- Record pid/job/session id in `runs.jsonl` if available.

Hermes example:

```bash
hermes chat -q "$(cat agents/T020/task.md)" \
  > agents/T020/log.txt 2>&1
```

Fallbacks:
- CLI missing: use current supervisor or synchronous subagent for smaller pieces.
- Flags differ: run `agent_cli --help`, then record the working command in `agent-registry.md` or project adapter notes.
- Output missing: inspect log, mark failed, retry with a narrower prompt.

## Code-agent adapter

Use for repository edits, tests/builds/lints, refactors, debugging, or implementation from plans.

Generic rules:
- Use a branch or worktree per coding worker when tasks may overlap.
- One worker owns one file set or module boundary to avoid edit conflicts.
- The task file states repo path, goal, constraints, touched areas, tests, expected diff, and handoff path.
- Require changed-files summary, test/build results, known issues, and rollback notes.
- Keep final code review/validation separate from implementation.

Preset idea:

```text
carrier: code_agent
preset: code | code-heavy
repo: <path>
worktree: <optional path>
```

This user's example mapping:
- Codex is the user's default coding carrier when available.
- Do not spend LLL effort comparing coding agents unless the user asks for tool selection.
- If Codex is unavailable, use a smaller current-agent edit, another configured code-capable agent, or split into a non-coding plan plus manual/agent implementation.

Fallbacks:
- Tests fail: log command/output, create follow-up task, and do not hide failures.
- Merge conflicts: block, split by file ownership, or use separate worktrees.

## Scheduler / cron method

Use for:
- recurring collection
- watchdogs
- periodic validation
- scheduled reminders/retries
- delayed follow-up checks

Rules:
- Do not recursively schedule new jobs from scheduled-job sessions.
- Keep prompts self-contained; scheduled runs should not depend on chat context.
- Empty output should usually mean no alert for watchdogs.
- For reasoning-heavy scheduled work, prefer a script collector plus a normal LLL synthesis pass.

Hermes example:
- `cronjob` / `hermes cron` is this adapter: durable scheduler with prompt, skills, script, context chaining, and delivery options.

Fallbacks:
- Scheduler unavailable: use manual checkpoint plus a background script.
- Job too complex: make the scheduled job only collect data and trigger/prepare a later LLL pass.

## Durable board / orchestration framework

Use only when the file-backed queue is no longer enough:
- tasks must survive restarts as first-class board items;
- many profiles/workers are configured;
- human interjection/block/unblock is expected;
- dashboard/audit trail matters;
- there are multiple long-running workstreams.

Generic rules:
- Discover actual configured workers/profiles before assigning; do not invent names.
- Put the LLL workdir path and task id in every card/job body.
- Keep dependencies explicit.
- Treat the board as an adapter to LLL, not a replacement for task artifacts and handoffs.

Hermes example:
- Hermes Kanban is this adapter when multi-profile collaboration is configured.

Fallbacks:
- No configured worker profiles: continue with `tasks.jsonl` or a thin file-backed runner.
- Board/dispatcher unavailable: recover from the LLL workdir.
- Task stuck: reclaim/reassign only if the board runtime supports it.

## Model and effort presets

Keep model/effort/tool choices behind named presets:

```json
{"preset":"fast-research","carrier":"agent_cli"}
{"preset":"deep-research","carrier":"agent_cli"}
{"preset":"critic","carrier":"agent_cli"}
{"preset":"code","carrier":"code_agent"}
{"preset":"code-heavy","carrier":"code_agent"}
{"preset":"script","carrier":"foreground_command"}
```

Map presets through profiles, config files, wrapper scripts, or environment variables. This is easier to audit and change than stuffing every task with low-level model flags.

If dynamic model choice is required, update the preset mapping, not every task prompt.
