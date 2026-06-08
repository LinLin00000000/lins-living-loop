# Lin's Living Loop / LLL

[中文](README.md) | [English](README.en.md)

一个给长任务用的、文件系统承载的 living loop。

LLL 原名 DOP（Deep Orchestration Protocol）。我改名不是为了把工具包装得更玄，而是想把它真实的用法说清楚：工作不应该只活在聊天窗口里。聊天会中断，模型会换，API 会抽风，上下文会爆。真正可靠的状态，应该落在文件里。

```text
The filesystem is where the work lives.
The chat is only the current interface.
The agent is the caretaker of the next loop.
```

LLL 做的事情很朴素：让主对话退到 supervisor 的位置，把任务、证据、输出、错误、恢复状态放进一个可读、可审计、可继续的工作目录。它不是 LangGraph，不是 Temporal，也不是一个新的 agent 平台。它更像一套小工具哲学下的工作纪律：先用普通文件解决 90% 的耐久性问题，只有真的需要时再升级到 runner、board 或更重的编排系统。

## 适合什么场景

适合：

- 深度调研、长文写作、复杂选型、代码改造、审计、验证。
- 会爆上下文、会超时、需要多轮恢复的任务。
- 需要多个 worker / 子代理 / 脚本 / 独立 agent CLI 协作的任务。
- 需要把过程、证据、错误和最终结论分开的任务。
- 用户之后可能说“继续上次那个”的任务。

不适合：

- 简单问答。
- 一两次工具调用能完成的小任务。
- 不需要恢复、不需要审计、不值得建目录的临时操作。

如果拿不准，用 LLL-lite：建一个很小的 workdir，写 mission、outputs、traceability 和 validation，不启动复杂 runner。

## 默认工作目录

新任务默认放在：

```text
~/lll-work/YYYYMMDD-HHMMSS_short-description-in-kebab-case/
```

核心结构：

```text
<lll-workdir>/
  mission.md
  internal/
    tasks.jsonl
    runs.jsonl
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
  output/
    00-index.md
    01-<deliverable>.md
    90-error-report.md
    91-traceability.md
    99-next-steps.md
```

目录名保持克制。`mission.md`、`internal/`、`output/` 这些名字不够浪漫，但它们对 agent、脚本和人类都清楚。Living 的部分放在叙事、标题、生命周期和工作纪律里，不拿可靠性换可爱。

## 这条 loop 怎么跑

```text
Seed -> Split -> Work -> Trace -> Heal -> Validate -> Hand off -> Grow or Close
```

| 阶段 | 文件动作 |
|---|---|
| Seed | 写或更新 `mission.md` |
| Split | 拆分 `internal/tasks.jsonl` 和 worker `task.md` |
| Work | worker 写日志、证据、草稿和产物 |
| Trace | 在 `output/91-traceability.md` 里追踪结论和证据 |
| Heal | 在 `output/90-error-report.md` 里记录错误、修复和自我维护 |
| Validate | 在 `internal/validation-report.md` 里做独立验收 |
| Hand off | 更新 `internal/handoff.md` 和 `internal/recovery-state.md` |
| Grow or Close | 更新 `output/99-next-steps.md`，决定继续还是收束 |

## 名称和 slug

展示名使用 **Lin's Living Loop / LLL**。仓库和 skill slug 使用 `lins-living-loop`，是为了保持 URL、shell、安装命令和 registry 搜索的稳定；apostrophe 在命令行里需要转义，不适合作为包名。

长期源码目录建议放在 `~/projects/lins-living-loop`。`~/lll-work/` 只放一次次 LLL 运行的工作记录，不作为项目源码仓库。

## helper 脚本

`scripts/lll.py` 是一个很薄的 stdlib helper，不运行 agent，只帮你维护文件协议。

```bash
python scripts/lll.py init ~/lll-work/20260608_150000_demo --objective "比较三个自部署笔记方案"
python scripts/lll.py add-task ~/lll-work/20260608_150000_demo --id T001 --title "collect candidates" --goal "收集候选方案并写 handoff"
python scripts/lll.py status ~/lll-work/20260608_150000_demo --all
python scripts/lll.py validate ~/lll-work/20260608_150000_demo
```

老名字 `scripts/lll.py` / compatibility `scripts/dop.py` 还保留，是兼容入口，会转发到 `lll.py`。旧的 `~/dop-work/` 工作区也可以继续读，不强制迁移。

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
- boring paths, living narrative

Living 不是装饰。它提醒 agent：每一轮离开时，都要让这个工作体更健康一点，更容易被下一个 caretaker 接住。

## License

MIT
