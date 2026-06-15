# Changelog

## Unreleased

- Added a context-drift contract rule: large-context or compaction-prone tasks should externalize objective, constraints, decisions, current state, and validation criteria into LLL files before continuing.
- Simplified new workdir layout: human-facing deliverables now live at the workdir root beside `mission.md`; new workdirs no longer create `output/`, `00-index.md`, or standalone next-step files.
- Moved traceability and error reporting to append-only JSONL under `internal/traceability.jsonl` and `internal/error-report.jsonl`.
- Updated helper script, templates, prompts, README, and key references to the compact current layout.
- Strengthened human-facing output language enforcement: root deliverables such as release summaries must follow the requested/current interaction language, copied English template prose must be localized before closeout, worker prompts now carry the language rule, and validation closeout must check deliverable language before final delivery.
- Added stronger public-release validation guidance: security-sensitive repository/package/skill/template releases should use deterministic scans plus multiple independent validator perspectives by default, and delegated validators should be recorded as real LLL workers even when they run synchronously.

## Previous

- Renamed the public workflow surface to Lin's Living Loop / LLL while preserving DOP compatibility language.
- Changed default new work root to `~/lll-work/YYYYMMDD-HHMMSS_short-description-in-kebab-case/`.
- Added `scripts/lll.py` as the primary helper and kept `scripts/dop.py` as a compatibility shim.
