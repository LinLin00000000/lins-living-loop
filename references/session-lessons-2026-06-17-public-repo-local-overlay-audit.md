# Session lesson: public repo hardening with local overlays

Use this reference when an LLL run creates or publishes a public repository, skillpack, template, installer, or AIOS/agent tooling derived from a private/local machine.

## What happened

A new public `aios-kit` repo initially committed useful but machine-specific files:

- local asset manifest with real local paths and local workflow state;
- base skillpack containing local-only skills and runtime paths;
- docs that blurred example paths, private live vaults, and reusable templates.

No token/private key was found, but the user correctly identified this as avoidable local-structure leakage for a public repo.

## Durable pattern

For public repos that still need local integration:

1. Commit only portable/base files:
   - `skillpack.yaml` as base/default intent;
   - `manifests/*.example.json` for examples;
   - registry examples/schemas;
   - reusable docs, templates, scripts, and skills.
2. Put machine-specific facts in ignored overlays:
   - `skillpack.local.yaml`;
   - `manifests/local-assets.local.json`;
   - `registries/*.local.*`;
   - private profiles / local device manifests.
3. Make `.gitignore` explicitly ignore local overlays, logs, state, live vaults, secrets, generated indexes, and real asset directories.
4. Add a deterministic public-audit script where practical. Minimum checks:
   - absolute home paths such as `/home/<user>`;
   - Windows drive paths;
   - private-key blocks;
   - secret/token/password/API-key assignments;
   - private/tailnet IP patterns;
   - high-entropy strings, while avoiding obvious URL false positives.
5. Audit both local working tree and a fresh remote clone after push.
6. If a brand-new public repo already committed local structure but no real secret, rewrite reachable history early with a clean root commit and force-push. If an actual secret was exposed, rotate/revoke it; history rewrite alone is insufficient.
7. In validation, search reachable history for the old sensitive strings, not just the current worktree:
   - `git log --all -S '<needle>' --oneline`
   - fresh full clone + audit script.

## Architecture lesson

For AIOS/agent tooling, do not turn the public kit into a dump of the user's live system. Keep the layers separate:

- public kit: schemas, examples, reusable scripts, docs, thin skills;
- local overlays: machine-specific paths, local-only skills, private device names;
- live vault: private current facts and maintenance logs;
- independent repos: reusable products/templates with their own lifecycle;
- registry/resolver: pointers, aliases, permissions, and context lookup.

## Pitfall

A path like `~/ai-ops` in docs is often acceptable as a generic convention, but a committed manifest that states this user's exact local asset topology or private skill names is not a good public default. Prefer examples plus ignored local overrides.
