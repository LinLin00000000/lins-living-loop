# Session lesson: AIOS kit friend install / portable skillpack

When LLL is used to harden a public kit/skillpack for friend or new-machine deployment, validate more than local author mode.

## Durable pattern

1. Separate the portable installer repo from live/private state:
   - public kit repo: install scripts, manifests, docs, examples;
   - template repo: reusable starter vault/files;
   - live vault: private current facts, never copied wholesale.
2. For friend/new-machine installs, prefer `copy` mode over symlink mode so runtime skills do not depend on author worktrees.
3. Independent first-party skills do not need to live inside the assembly repo. Include them in the skillpack by source reference and install them into runtime skills at deployment time.
4. Add a root installer (`install.sh` or equivalent) when users ask for “one-key deploy”; README-only two-command instructions are not enough.
5. Validate with a temporary clean HOME, not only the author machine:
   - install the skillpack into the temp HOME;
   - verify first-party skills exist under the temp runtime skill dir;
   - bootstrap any template vault into the temp HOME;
   - run the vault/kit doctor/check commands.
6. If a doctor command checks author source paths, make it also accept installed runtime skills for remote first-party entries. Otherwise friend installs can succeed but doctor fails because `~/projects/<repo>` is missing.
7. External/remote skill installation may suffer transient GitHub/npm TLS failures. Use bounded retries for install commands. For first-party GitHub skills, consider a direct `git clone --depth 1` fallback that copies a valid `SKILL.md` directory.
8. After pushing a public installer, verify from the remote surface:
   - fetch the raw installer URL;
   - fresh shallow clone;
   - syntax/compile/public-audit checks.

## Verification checklist

- `bash -n install.sh` or equivalent syntax check.
- Compile/lint installer helper scripts.
- Public audit for machine paths/secrets.
- `install.sh --dry-run`.
- Temp-HOME smoke install.
- Fresh remote clone validation after push.
- Update the live operations vault/log if the kit is itself an AI-managed operational resource.
