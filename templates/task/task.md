# LLL Worker Task

```text
task_id: <task-id>
carrier: <current|subagent|script|agent_cli|background|scheduler|board|human>
preset: <preset-or-default>
status: pending
```

## Objective
<worker goal>

## Inputs
- [mission.md](../../../mission.md)
- <other inputs>

## Required outputs
- [handoff.md](handoff.md)
- [artifacts/](artifacts/) as needed

## Compact LLL contract
- Read `mission.md`, this task file, and listed inputs before starting.
- Treat the workdir as the source of truth; chat is only a short handoff.
- Write detailed work, logs, evidence, drafts, and outputs under this task directory unless explicitly assigned a shared root deliverable.
- Human-facing deliverables usually live at the workdir root as `01-*`, `02-*`, etc.; merge when one file preserves thematic completeness, split only when content or themes justify it.
- Current next steps belong inside the primary report/relevant deliverable, not in a standalone next-step file.
- Write an artifact skeleton early, then fill it incrementally for long reading/research tasks.
- Do not edit shared state files unless explicitly granted ownership through a lock or runner API.
- Keep claims traceable to artifact paths, sources, commands, or validation notes; append JSONL trace entries only when assigned/authorized.
- If blocked, record what was tried and propose the smallest fallback.

## Logging
Append commands, sources, decisions, failures, and retries to [log.txt](log.txt).

## Handoff contract
status, outputs, 1-3 key results, risks/blockers, recommended next step
