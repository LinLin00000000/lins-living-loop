# Session lessons — AIOS unified instance root and distribution-style install

Use when an LLL run changes an installer, skillpack, or AIOS-like distribution layout that deploys state/capabilities/workdirs onto a target machine.

## Durable lessons

- Distinguish **product source** from **deployed instance root**. Product repos may remain modular; the installed user/server instance can still be one coherent tree such as `~/aios`.
- Treat deployed state/capability/work memory as one instance with different lifecycles, not as unrelated folders:
  - instance facts/assets: `~/aios/vault/ops` or equivalent;
  - runtime capabilities: `~/aios/skills` plus agent-specific compatibility links;
  - recoverable work memory: `~/aios/work`;
  - module checkouts: `~/aios/modules`;
  - local state/log/cache: `~/aios/{state,logs,cache}`.
- For friend/new-machine installers, create compatibility symlinks only when safe. Never overwrite existing real paths such as `~/ai-ops`, `~/lll-work`, or `~/.agents/skills`; warn and require an explicit migration task instead.
- If installer options derive default paths from a root option, track whether dependent paths were explicitly supplied. After parsing `--root`, recompute unset defaults (`vault`, `skills`, `modules`, `kit-dir`) from the final root.
- In CLI commands that update multiple files, validate all conflicts before writing anything. Example: `project add --alias X` must check alias conflicts before appending to `registry.jsonl`.
- Public-audit high-entropy filters should avoid path false positives without blanket-exempting slash-containing strings; base64/token-like values can contain `/`.
- Copy-mode installers should not delete arbitrary existing target directories. Mark managed copies (for example `.aios-kit-managed`) and refuse to overwrite unmanaged targets unless an explicit force/override is set.
- When smoke-testing public/friend installs from a local working tree, copy only tracked plus non-ignored files (`git ls-files --cached --others --exclude-standard`). A raw `cp -a` can leak ignored local overlays such as `skillpack.local.yaml` into the simulated friend environment and produce false failures.
- `doctor` commands for friend installs should check the default installed target only unless the user explicitly asks for all targets. Do not fail a universal install merely because Hermes/profile-specific targets are not populated.
- Treat example manifests as examples during friend `doctor`; absence of author-only paths should warn or annotate, not fail.

## Validation pattern

For this class of LLL run, require at least:

1. syntax/compile checks for changed scripts;
2. public audit;
3. installer `--dry-run` including custom-root path derivation;
4. edge-case tests for CLI atomicity/conflicts;
5. fresh temp-HOME smoke install built from tracked/non-ignored files;
6. generated instance `doctor` and domain-specific check (`aiops.py check`, etc.);
7. independent spec + safety review before commit/push;
8. post-push status check and live ops registry/log update if the project is AI-managed.

## Architecture phrasing

Prefer: “distribution/install hub that may evolve toward a core monorepo when shared versioning, atomic changes, and unified release/testing become necessary.”

Avoid over-defensive wording such as “not the whole AIOS” when the user is exploring future product identity. The better distinction is: public product source vs deployed private instance state.