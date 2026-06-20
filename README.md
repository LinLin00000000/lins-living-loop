# Lin's Living Loop / LLL

[中文](README.md) | [English](README.en.md)

一个给长任务用的、文件系统承载的 living loop。

LLL 原名 DOP（Deep Orchestration Protocol）。改名不是为了把工具包装得更玄，而是把真实用法说清楚：工作不应该只活在聊天窗口里。聊天会中断，模型会换，API 会抽风，上下文会爆。真正可靠的状态，应该落在文件里。

```text
The filesystem is where the work lives.
The chat is only the current interface.
The agent is the caretaker of the next loop.
```

LLL 让主对话退到 supervisor 的位置，把任务、证据、产物、错误、恢复状态放进一个可读、可审计、可继续的工作目录。它不是 LangGraph，不是 Temporal，也不是新的 agent 平台。它更像小工具哲学下的工作纪律：先用普通文件解决 90% 的耐久性问题，只有真的需要时再升级到 runner、board 或更重的编排系统。

## 适合什么场景

适合：

- 深度调研、长文写作、复杂选型、代码改造、审计、验证。
- 会爆上下文、会超时、需要多轮恢复，或当前上下文已经很大、容易漂移的任务。
- 需要多个 worker / 子代理 / 脚本 / 独立 agent CLI 协作的任务。
- 需要把过程、证据、错误和最终结论分开的任务。
- 用户之后可能说“继续上次那个”的任务。

不适合：简单问答、一两次工具调用能完成的小任务、不需要恢复/审计的临时操作。

如果拿不准，用 LLL Lite：建一个很小的 workdir，写 `mission.md`、`notes.md` 或一个根目录产物，不启动复杂 runner。上下文很大时，先把目标、约束、决策、当前状态和验收标准外置到文件里，再继续执行。

## 默认工作目录

新任务默认放在：

```text
~/lll-work/YYYYMMDD-HHMMSS_short-description-in-kebab-case/
```

核心结构：

```text
<lll-workdir>/
  mission.md
  <task-specific-name>.md     # 可选：根据任务内容命名的人类可读产物
  <another-topic>.md          # 可选：内容多/主题独立时再拆分
  notes.md                   # 可选：Lite 工作笔记
  internal/
    tasks.jsonl
    runs.jsonl
    error-report.jsonl       # append-only 工作流/运行时异常与修复
    traceability.jsonl       # append-only 结论/来源/变更追踪
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

新工作区不再创建 `output/`、`00-index.md` 或单独的 `99-next-steps.md`。人类可读产物直接放在根目录；下一步写进主报告或相关产物；追踪性报告和错误报告改为 `internal/*.jsonl`，便于追加和验证。

## 这条 loop 怎么跑

```text
Seed -> Split -> Work -> Trace -> Heal -> Validate -> Hand off -> Grow or Close
```

| 阶段 | 文件动作 |
|---|---|
| Seed | 写或更新 `mission.md` |
| Split | 拆分 `internal/tasks.jsonl` 和 worker `task.md` |
| Work | worker 写日志、证据、草稿和产物 |
| Trace | 追加到 `internal/traceability.jsonl` |
| Heal | 追加到 `internal/error-report.jsonl` |
| Validate | 在 `internal/validation-report.md` 里做独立验收 |
| Hand off | 更新 `internal/handoff.md` 和 `internal/recovery-state.md` |
| Grow or Close | 在主报告/相关产物中写当前下一步 |

## 名称和 slug

展示名使用 **Lin's Living Loop / LLL**。仓库和 skill slug 使用 `lins-living-loop`，是为了保持 URL、shell、安装命令和 registry 搜索的稳定；apostrophe 在命令行里需要转义，不适合作为包名。

长期源码目录建议放在 `~/projects/lins-living-loop`。`~/lll-work/` 只放一次次 LLL 运行的工作记录，不作为项目源码仓库。

## `lll` CLI

`lll` 是 LLL 文件协议的 stdlib reference implementation：负责初始化、任务队列、状态/验证、runner、reaper 与服务 wrapper 生成；它不是 planning brain、Web UI 或平台。

LLL 的默认用户是 Agent，不是人类终端用户：人类通常只提出目标与验收标准，Agent 负责发现 `lll`/`aios lll`、创建工作区、写任务、执行 runner、读取 artifacts、修复失败并收尾。README 里的命令主要是 Agent 操作手册与极端情况下的人类 fallback，不要求人类逐条理解或手输。

Agent 优先的健康检查入口：

```bash
lll --version
lll doctor --json
lll doctor <workdir> --json
aios lll doctor --json
```

仓库内可直接运行：

```bash
./lll init ~/lll-work/20260608-150000_demo --objective "比较三个自部署笔记方案"
./lll task add ~/lll-work/20260608-150000_demo \
  --title "write marker" \
  --goal "创建一个 marker 文件" \
  --preset code-loop \
  --command "printf ok > marker.txt" \
  --verify "test -f marker.txt"
./lll status ~/lll-work/20260608-150000_demo --json
./lll validate ~/lll-work/20260608-150000_demo --json
./lll run once ~/lll-work/20260608-150000_demo --json
./lll event ~/lll-work/20260608-150000_demo --event note --message "agent checkpoint" --json
./lll checkpoint ~/lll-work/20260608-150000_demo --checkpoint "safe point" --json
./lll run reaper ~/lll-work/20260608-150000_demo --json
./lll service install ~/lll-work/20260608-150000_demo --target systemd --user --json
```

也可以安装为 Python console script（仍然只有标准库运行依赖）：

```bash
python3 -m pip install .
lll --help
```

`scripts/lll.py` 现在保留为兼容 shim，会转发到 `src/lll_cli`；旧命令 `add-task` / `set-status` 仍可用，但新文档优先使用 `task add` / `task set-status`。老名字 `scripts/dop.py` 还保留为兼容入口，会转发到 `lll.py`。旧的 `~/dop-work/` 工作区也可以继续读，不强制迁移。

### Code Loop / Runner 边界

- `shell` executor 是 MVP 默认 executor，用于本体 smoke、自举和本地脚本型任务。
- runner 会写 `internal/agents/<task-id>/artifacts/runner-run-<run-id>/`，并由 verify 命令决定是否 `succeeded`。
- `serve` 和 `reaper` 提供连续执行与过期 lease 回收；默认仍保持单机、单并发、文件状态。
- service 子命令默认生成 systemd/launchd/Windows Task Scheduler wrapper 文件；只有显式 `--apply` 才尝试安装 systemd user service。
- AIOS 可以通过 `aios lll ...` 发现/代理 LLL，但不拥有 LLL 状态机。

## 安装

通过 Skills CLI：

```bash
npx skills add LinLin00000000/lins-living-loop -g -y
```

也可以直接 clone：

```bash
git clone https://github.com/LinLin00000000/lins-living-loop.git
```

在 Hermes 里，如果已经安装为 skill，可以在任务里说 “use LLL” / “用 Lin's Living Loop” / “用 DOP”，这三个入口都应该触发同一套工作流。

## 设计边界

LLL 的底层逻辑保持可靠优先：

- plain files before databases
- small scripts before frameworks
- handoffs before long chat summaries
- independent validation before delivery
- root deliverables, internal state

Living 不是装饰，而是一种工作纪律：每个 caretaker 都应该让这份工作比接手时更健康、更可追踪、更容易继续。
