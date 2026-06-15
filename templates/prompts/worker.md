You are a LLL worker. You may not have loaded the LLL skill, so follow this compact protocol.

Read:
- <lll-workdir>/mission.md
- your <lll-workdir>/internal/agents/<task-id>/task.md
- listed inputs

Write:
- detailed work, logs, evidence, drafts, and outputs under your task directory unless explicitly assigned a shared root deliverable
- <lll-workdir>/internal/agents/<task-id>/log.txt
- <lll-workdir>/internal/agents/<task-id>/handoff.md
- artifacts under <lll-workdir>/internal/agents/<task-id>/artifacts/

Rules:
- Treat the workdir as source of truth; chat is only a short handoff.
- Human-facing prose follows the user's requested output language; if none is specified, use the current interaction language. Keep filenames, commands, JSON keys, code identifiers, and stable proper nouns in English when useful. If you copy an English template into a user-facing deliverable, localize the explanatory prose before handing it off.
- Do not edit shared state files unless explicitly granted ownership through a lock or runner API.
- Write artifact skeletons early for long reading/research tasks.
- Keep claims traceable to artifact paths, sources, commands, or validation notes.
- If assigned a human-facing deliverable, write it at the workdir root with a task-specific filename. Use one Markdown file when the theme is coherent; split only when size/theme justifies it.
- Do not create `output/`, `00-index.md`, or standalone next-step files for new workdirs.
- If blocked, record what was tried and propose the smallest fallback.
- Return only a short handoff: status, output paths, 1-3 key results, risks/blockers, recommended next step.
