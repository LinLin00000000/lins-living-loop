# Session lesson: honest mode selection and context control

Date: 2026-06-13

## What happened

A multi-object deep research task compared Hermes Browser, Playwright MCP, and Chrome DevTools MCP. The run created full-looking `internal/agents/T001...` worker records, but most research, synthesis, validation, and repair happened inline in the supervisor context. The main conversation grew to ~122k tokens.

The user pointed out that this violated the spirit of LLL/LLM scaling: the main thread should be a lightweight supervisor, not the place where all raw research context accumulates.

## Durable lesson

Do not confuse file-backed records with real context isolation. A workdir with `internal/agents/T001...` is not a multi-agent run unless real worker contexts, background carriers, independent CLIs, humans, or a clearly labeled `supervisor-inline` audit need existed.

For multi-object deep research, prefer:

```text
subject workers in parallel -> synthesis worker -> independent validator
```

The supervisor should hold only:
- mission and constraints;
- task map / registry;
- compact worker handoffs;
- final synthesis;
- validation notes;
- selected evidence needed to resolve contradictions.

It should not personally ingest every long README, source file, web extract, and raw benchmark output unless there is no workable worker carrier and that limitation is explicitly recorded.

## Full LLL trigger

Default to full LLL when:
- the user asks for deep research / 深度调研 / complex comparison;
- there are three or more independent research objects;
- the work likely requires reading multiple docs, source files, specs, repos, or runtime evidence across those objects;
- correctness benefits from distinct researcher, synthesizer, and validator roles.

If runtime concurrency is limited, batch subject workers or use independent agent CLIs/background jobs. Do not silently fall back to supervisor-heavy inline work for convenience.

## LLL Lite rule

For light or medium single-track tasks, LLL Lite is acceptable and often better. But Lite should look light, following the current compact layout:

```text
<lll-workdir>/
  mission.md
  notes.md                 # optional compact working notes
  <task-specific-name>.md  # optional human-facing deliverable at the root
  internal/
    validation.json   # optional for nontrivial checks
    traceability.jsonl     # optional when claims need traceability
    error-report.jsonl     # optional unless a workflow/runtime issue occurs
```

Add audit/trace/validation files only when useful. Do not create `output/`, index files, standalone next-step files, ornate `internal/agents/` trees, or fake Agent 1/2/3 records when the supervisor did the work inline.

## Helper/tooling caveat

At the time of the lesson, `scripts/lll.py validate` expected full v2 worker directories whenever `internal/tasks.jsonl` existed and was not Lite-aware. Do not satisfy that helper by creating fake worker directories. Instead, record the mismatch as a helper limitation and improve the helper later.
