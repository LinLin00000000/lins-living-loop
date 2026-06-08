# Lin's Living Loop / LLL

[中文](README.md) | [English](README.en.md)

A tiny file-backed living loop for durable AI-agent work.

LLL was formerly DOP, the Deep Orchestration Protocol. The rename does not change the core machinery. It changes the product surface: less cold protocol language, more emphasis on living work, repair, recovery, and continuation.

```text
The filesystem is where the work lives.
The chat is only the current interface.
The agent is the caretaker of the next loop.
```

LLL turns the main chat into a lightweight supervisor. The durable state lives in files: mission, queue, logs, worker handoffs, validation, traceability, error reports, and final outputs. It is not LangGraph, Temporal, or a new agent platform. It is the small-tools version of durable agent work: solve 90% of the reliability problem with readable files, then escalate only when the simple path is no longer enough.

## When to use it

Use LLL for:

- deep research, long writing, complex comparisons, code changes, audits, and validation-heavy work;
- tasks that may overflow context, time out, or need recovery across turns;
- multi-worker work using subagents, scripts, independent agent CLIs, schedulers, or humans;
- work where evidence, process state, errors, and final conclusions should stay separate;
- anything the user may later want to resume.

Skip full LLL for simple Q&A, tiny edits, or tasks that fit safely in a few tool calls. When in doubt, use LLL-lite: a small workdir, a mission file, numbered outputs, traceability, and validation, without a heavy runner.

## Default workdir

New runs default to:

```text
~/lll-work/YYYYMMDD_HHMMSS_slug/
```

Canonical layout:

```text
<lll-workdir>/
  mission.md
  internal/
    tasks.jsonl
    runs.jsonl
    agent_registry.md
    recovery_state.md
    handoff.md
    validation_report.md
    inputs/
    logs/
    agents/<task-id>/
      task.md
      status.json
      log.txt
      handoff.md
      artifacts/
  output/
    00_index.md
    01_<deliverable>.md
    90_error_report.md
    91_traceability.md
    99_next_steps.md
```

The paths stay boring on purpose. `mission.md`, `internal/`, and `output/` are easier for agents, scripts, and humans to understand than a fully metaphorical taxonomy. The Living layer belongs in the narrative, headings, lifecycle, and discipline, not in fragile machine interfaces.

## The loop

```text
Seed -> Split -> Work -> Trace -> Heal -> Validate -> Hand off -> Grow or Close
```

| Step | File-backed action |
|---|---|
| Seed | Write or update `mission.md` |
| Split | Decompose `internal/tasks.jsonl` and worker `task.md` |
| Work | Workers write logs, evidence, drafts, and artifacts |
| Trace | Track claims and evidence in `output/91_traceability.md` |
| Heal | Record errors, repairs, and self-maintenance in `output/90_error_report.md` |
| Validate | Write `internal/validation_report.md` |
| Hand off | Refresh `internal/handoff.md` and `internal/recovery_state.md` |
| Grow or Close | Update `output/99_next_steps.md` and decide whether to continue or close |

## Helper script

`scripts/lll.py` is a thin stdlib helper. It does not run agents. It only helps maintain the file protocol.

```bash
python scripts/lll.py init ~/lll-work/20260608_150000_demo --objective "Compare three self-hosted note-taking options"
python scripts/lll.py add-task ~/lll-work/20260608_150000_demo --id T001 --title "collect candidates" --goal "Collect candidates and write a handoff"
python scripts/lll.py status ~/lll-work/20260608_150000_demo --all
python scripts/lll.py validate ~/lll-work/20260608_150000_demo
```

The old `scripts/lll.py` / compatibility `scripts/dop.py` name remains as a compatibility shim and forwards to `lll.py`. Old `~/dop-work/` directories remain readable; LLL does not force a bulk migration.

## Install

With the Skills CLI:

```bash
npx skills add LinLin00000000/lins-living-loop -g -y
```

Or clone it directly:

```bash
git clone https://github.com/LinLin00000000/lins-living-loop.git
```

After installation, prompts such as “use LLL”, “use Lin's Living Loop”, and “use DOP” should all reach the same workflow.

## Design boundary

LLL keeps the reliable core intact:

- plain files before databases
- small scripts before frameworks
- handoffs before long chat summaries
- independent validation before delivery
- boring paths, living narrative

Living is not decoration. It is the discipline that each caretaker should leave the work healthier, more traceable, and easier to resume than they found it.

## License

MIT
