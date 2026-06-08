# Output Index

Human reading order:

1. [00-index.md](00-index.md) — this index; every file in `output/` should be listed here.
2. [01-<deliverable>.md](01-<deliverable>.md) — current primary human-facing deliverable when present; update it for same-scope corrections.
3. [02-<deliverable>.md](02-<deliverable>.md) — optional independent follow-up deliverable; create next numbers for new analyses, decisions, or phase results.
4. [90-error-report.md](90-error-report.md) — append-only internal workflow/runtime abnormalities, repairs, and self-maintenance notes; not for normal user goals or scope additions; each appended entry must include a local-timezone ISO-8601/RFC3339 timestamp.
5. [91-traceability.md](91-traceability.md) — append-only mapping from claims/changes to evidence; each appended entry/row must include a local-timezone ISO-8601/RFC3339 timestamp.
6. [99-next-steps.md](99-next-steps.md) — current recommended next actions.

Internal/process files live under [../internal/](../internal/) and are intentionally not the main reading surface.
