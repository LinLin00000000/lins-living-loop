# Lin's Living Loop / LLL

[中文](README.md) | [English](README.en.md)

A tiny file-backed living loop for durable AI-agent work.

LLL was formerly DOP, the Deep Orchestration Protocol. The rename does not change the core machinery. It clarifies the product surface: living work, repair, recovery, and continuation without heavyweight orchestration ceremony.

```text
The filesystem is where the work lives.
The chat is only the current interface.
The agent is the caretaker of the next loop.
```

LLL turns the main chat into a lightweight supervisor. Durable state lives in files: mission, queue, logs, worker handoffs, validation, traceability, error records, and final deliverables. It is not LangGraph, Temporal, or a new agent platform. It is the small-tools version of durable agent work: solve 90% of the reliability problem with readable files, then escalate only when the simple path is no longer enough.

## When to use it

Use LLL for:

- deep research, long writing, complex comparisons, code changes, audits, and validation-heavy work;
- tasks that may overflow context, time out, or need recovery across turns;
- multi-worker work using subagents, scripts, independent agent CLIs, schedulers, or humans;
- work where evidence, process state, errors, and final conclusions should stay separate;
- anything the user may later want to resume.

Skip full LLL for simple Q&A, tiny edits, or tasks that fit safely in a few tool calls. When in doubt, use LLL Lite: a small workdir, `mission.md`, maybe `notes.md`, maybe one root report, and no heavy runner.

## Default workdir

New runs default to:

```text
~/lll-work/YYYYMMDD-HHMMSS_short-description-in-kebab-case/
```

Canonical layout:

```text
<lll-workdir>/
  mission.md
  01-<deliverable>.md        # optional human-facing deliverable beside mission.md
  02-<deliverable>.md        # optional split when content/themes justify it
  notes.md                   # optional Lite notes
  internal/
    tasks.jsonl
    runs.jsonl
    error-report.jsonl       # append-only workflow/runtime abnormalities and repairs
    traceability.jsonl       # append-only claim/source/change trace
    agent-registry.md
    recovery-state.md
    handoff.md
    validation-report.md
    inputs/
    logs/
    agents/<task-id>/
      task.md
      status.json
      log.txt
      handoff.md
      artifacts/
```

New workdirs no longer create `output/`, `00-index.md`, or standalone `99-next-steps.md` files. Human-readable deliverables live directly at the workdir root; next steps live inside the primary report or relevant deliverable; traceability and error records are JSONL files under `internal/` for cheap append and validation.

## The loop

```text
Seed -> Split -> Work -> Trace -> Heal -> Validate -> Hand off -> Grow or Close
```

| Step | File-backed action |
|---|---|
| Seed | Write or update `mission.md` |
| Split | Decompose `internal/tasks.jsonl` and worker `task.md` |
| Work | Workers write logs, evidence, drafts, and artifacts |
| Trace | Append to `internal/traceability.jsonl` |
| Heal | Append to `internal/error-report.jsonl` |
| Validate | Write `internal/validation-report.md` |
| Hand off | Refresh `internal/handoff.md` and `internal/recovery-state.md` |
| Grow or Close | Put current next steps inside the primary report/relevant deliverable |

## Name and slug

The display name is **Lin's Living Loop / LLL**. The repository and skill slug use `lins-living-loop` because it is URL-safe, shell-safe, and registry-friendly; an apostrophe in a package/repo name creates quoting and escaping friction.

For local development, keep the canonical source repo under a project directory such as `~/projects/lins-living-loop`. Use `~/lll-work/` for LLL run records, not long-lived source repos.

## Helper script

`scripts/lll.py` is a thin stdlib helper. It does not run agents. It only helps maintain the file protocol.

```bash
python3 scripts/lll.py init ~/lll-work/20260608-150000_demo --objective "Compare three self-hosted note-taking options"
python3 scripts/lll.py add-task ~/lll-work/20260608-150000_demo --id T001 --title "collect candidates" --goal "Collect candidates and write a handoff"
python3 scripts/lll.py status ~/lll-work/20260608-150000_demo --all
python3 scripts/lll.py validate ~/lll-work/20260608-150000_demo
```

The old `scripts/dop.py` name remains as a compatibility shim and forwards to `lll.py`. Old `~/dop-work/` directories remain readable; LLL does not force a bulk migration.

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
- root deliverables, internal state

Living is not decoration. It is the discipline that each caretaker should leave the work healthier, more traceable, and easier to resume than they found it.
