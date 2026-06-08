# Hermes permissions and config-change adapter

Use this reference when a LLL task needs to inspect or change Hermes Agent configuration, credentials, profiles, skills, plugins, cron jobs, gateway settings, MCP settings, or other Hermes control-plane files.

## Rule of thumb

Do not patch Hermes control-plane files directly unless the user explicitly asked for raw file surgery and understands the risk. Prefer Hermes-owned commands and tools:

- `hermes config set <key> <value>` for ordinary config values.
- `hermes config edit` for human-reviewed full-file config editing.
- `hermes auth ...` for OAuth/API credential management when supported.
- `hermes tools ...`, `hermes skills ...`, `hermes mcp ...`, `hermes cron ...`, `hermes gateway ...`, and profile-aware CLI commands for their own domains.
- The dedicated Hermes tools (`skill_manage`, `cronjob`, `memory`, etc.) when available.

This keeps schema migrations, profile scoping, atomic writes, permissions, comments, env-template preservation, and secret placement in the code path that owns those semantics.

## Why direct patch/write is blocked

Hermes file tools include defense-in-depth guards. In the current implementation, `write_file` and `patch` refuse protected system/credential/control-plane targets such as:

- `~/.hermes/config.yaml`, `auth.json`, `webhook_subscriptions.json`;
- active profile and root `.env` files;
- OAuth/token stores such as `.anthropic_oauth.json`, `mcp-tokens/`, and `pairing/`;
- common secret-bearing user paths such as `.ssh/`, `.aws/`, `.gnupg/`, `.kube/`, `.docker/`, `.netrc`, `.npmrc`, `.pypirc`, `.git-credentials`;
- selected sensitive system paths such as `/etc/`, `/boot/`, `/etc/sudoers`, `/etc/passwd`, `/etc/shadow`, Docker sockets, and systemd directories.

For reads, Hermes blocks direct reads of credential stores and common `.env` files for the same reason: they may contain provider keys, OAuth tokens, webhook secrets, and account credentials that the agent rarely needs to see raw.

These guards are not a full security sandbox. The terminal runs as the same OS user and can technically bypass many file-tool denials. Treat them as a confusion reducer, audit signal, and prompt-injection brake, not as an unbreakable boundary.

## Config CLI behavior

`hermes config set` is the preferred automated path:

- normal dotted keys go to `config.yaml`, e.g. `hermes config set approvals.mode smart`;
- API keys/tokens and known credential env vars go to `.env`, e.g. `hermes config set OPENROUTER_API_KEY ...`;
- the config writer performs Hermes-specific normalization and atomic YAML writing;
- some changes require a fresh session or gateway restart before taking effect.

Before changing config, usually run:

```bash
hermes config path
hermes config env-path
hermes config show
```

Avoid printing secret values. For `.env`, prefer checking key presence or using `hermes auth list` / provider-specific status commands instead of reading raw contents.

## Approval / automation modes

Hermes has several layers that are easy to confuse:

1. File-tool protected-path denial: blocks `write_file`/`patch` to sensitive files. This is tool-level defense-in-depth and normally should not be bypassed for Hermes control-plane files.
2. Cross-profile soft guard: blocks file-tool writes into another profile's `skills/`, `plugins/`, `cron/`, or `memories/` unless the tool call passes `cross_profile=True` after explicit user direction.
3. Terminal dangerous-command approvals: shell commands may require approval depending on `approvals.mode` (`manual`, `smart`, `off`) or per-invocation YOLO mode.
4. OS permissions: sudo, filesystem ACLs, container/SSH backend permissions, and mounted volume settings still apply.
5. Optional safe write root: `HERMES_WRITE_SAFE_ROOT` can restrict file tool writes to one directory tree.
6. Managed mode: package-manager-managed installs may refuse config/env edits through CLI helpers.

## LLL guidance

For LLL missions that change Hermes itself:

1. Load the `hermes-agent` skill before answering or acting.
2. State side effects clearly: config write, credential write, gateway restart, tool enable/disable, profile mutation, service change.
3. Prefer domain commands over file patches.
4. If a direct file-tool write is blocked, do not fight the guard; switch to the owning CLI/tool path and record the fallback in `internal/agents/<task-id>/log.txt` or `output/90_error_report.md`.
5. For multi-profile tasks, identify the active profile and target profile before writing. Use `cross_profile=True` only after explicit user direction and only for profile-scoped areas where that flag applies.
6. Validate by reading non-secret config/status output, checking command exit codes, and restarting or starting a fresh session when the changed setting is startup-scoped.
7. Keep secrets out of LLL artifacts. Store only key names, presence/absence, command exit codes, redacted values, or paths.

## If the user wants “true full auto”

Offer a deliberate automation profile rather than silently weakening every boundary:

- Use a separate Hermes profile or sandboxed OS user for automation.
- Keep credentials minimal and scoped to that automation profile.
- Set `approvals.mode off` or run `hermes --yolo` only for that profile/session.
- Prefer a workdir or `HERMES_WRITE_SAFE_ROOT` for ordinary file work; explicitly whitelist or script the few control-plane changes that must be automated.
- Use audited wrapper scripts for sensitive changes, e.g. a script that only runs allowed `hermes config set ...` keys.
- Log every side effect to the LLL workdir.
- Keep a rollback path: profile export/backup, config snapshot, or git-tracked dotfiles if appropriate.

The safer default is “high automation inside a bounded sandbox, explicit gates for credentials and global control-plane changes,” not “the agent may edit every file in the user account with no friction.”
