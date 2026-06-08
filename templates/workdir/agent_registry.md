# Agent / Worker Registry

| id | role | carrier | preset | status | task(s) | output | notes |
|---|---|---|---|---|---|---|---|
| supervisor | decomposes, routes, validates, reports | current | default | active | all | [output/00_index.md](../output/00_index.md) | owns queue and final decisions |

## Adapter availability

| adapter | available? | command/tool | fallback |
|---|---:|---|---|
| current | yes | current supervisor/runtime | split task |
| synchronous_subagent | unknown | short parallel worker | current/background_process |
| foreground_command | unknown | shell/script | current/manual |
| background_process | unknown | managed background process | foreground_command/current |
| agent_cli | unknown | independent/specialist agent CLI | current/synchronous_subagent |
| code_agent | unknown | coding agent, e.g. Codex if configured | current/code-capable agent |
| scheduler | unknown | cron/watchdog/scheduled job | manual/background_process |
| durable_board | optional | board/orchestration framework, e.g. Kanban if configured | JSONL queue |
