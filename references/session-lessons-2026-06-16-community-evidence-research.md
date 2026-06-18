# Session lesson: community evidence research in LLL

When an LLL run asks for real-world/community/forum evidence about a tool or workflow, do not treat web results as a flat list of facts. Use an evidence-quality structure so the final synthesis stays useful and honest.

## Pattern

1. Split research tracks by subject when comparison is involved, e.g. `tool-a-community`, `tool-b-community`, and a separate `architecture/absorption-plan` track.
2. Ask workers to prioritize firsthand evidence in this order:
   - GitHub issues/discussions, official community forums, accessible forum posts, and comments with logs/configs.
   - Hacker News / Reddit / LinuxDo / Stack Overflow when directly accessible or clearly quoted.
   - Hands-on blogs with concrete repos/tasks/logs.
   - Official docs for recommended workflow and product intent.
   - SEO/review/tutorial pages only as weak signals or source discovery.
3. Require reliability tiers in handoffs, such as Tier A/B/C/D, and require workers to label search-result snippets or blocked pages as weak evidence.
4. Record absence-of-evidence explicitly. If Stack Overflow, LinuxDo, or another requested forum has little/no high-quality firsthand evidence, say so; do not fill the gap with SEO pages.
5. Separate `community/practical evidence` from `source/architecture evidence`. Community reports can validate product fit and pain points, but they do not prove benchmark-level capability.
6. In synthesis, avoid binary “tool A wins/tool B loses” framing when the evidence actually shows role separation, orchestration, or mixed-tool workflows.
7. For user-facing conclusions, state which claims are source-backed, which are community-backed, and which are product/architecture recommendations.

## Useful final-report sections

- Evidence reliability and retrieval caveats.
- Positive firsthand reports.
- Negative/limitation reports.
- Migration/abandonment/mixed-use patterns.
- Absence-of-evidence and likely causes.
- Decision implications for the user's deployment or product strategy.

## Pitfalls

- Do not over-credit official user stories or SEO review pages as proof of real-world success.
- Do not treat inaccessible Reddit/HN search snippets as equivalent to direct quotes from extracted pages.
- Do not interpret “few public large-project success stories” as proof the tool cannot do large-project work; phrase it as insufficient public evidence.
- When a user is deciding whether to manage one tool or multiple tools, distinguish user-facing complexity from hidden optional carriers/backends.