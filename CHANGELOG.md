# Changelog

## 1.0.0

Initial public release as Lin's Living Loop / LLL.

- Renamed public surface from DOP to LLL while keeping DOP as a compatibility alias.
- Changed default new work root to `~/lll-work/YYYYMMDD-HHMMSS_short-description-in-kebab-case/`.
- Kept the reliable file-backed core: `mission.md`, `internal/`, `output/`, JSONL queues, handoffs, traceability, error reports, and validation.
- Added `scripts/lll.py` as the primary helper and kept `scripts/dop.py` as a compatibility shim.
- Added Chinese-first README with English version.
