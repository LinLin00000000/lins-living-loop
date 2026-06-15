# Session lesson: mid-run research scope correction

Use this when an LLL research run is interrupted and the user changes source scope, excludes a source, or adds a new research axis after workers have already started.

## Pattern

1. Reuse the active workspace; do not start a fresh LLL workdir unless the mission truly changed into a different task.
2. Inspect partial worker outputs before relaunching. Some synchronous subagents may have written artifacts even if the parent received an interrupted status.
3. Update `mission.md` with a timestamped addendum and refresh success criteria / constraints.
4. Update `internal/tasks.jsonl`: mark superseded tasks clearly (`done_with_scope_change`, `deprecated`, `partial`, etc.) and add new task ids for new sources/axes.
5. Preserve but demote invalidated evidence. Example: if a forum/source is removed, keep its artifact as historical background but state it is excluded from final evidence.
6. Append to `internal/error-report.jsonl` for the interrupted worker/scope-repair event and to `internal/traceability.jsonl` for the source-scope change.
7. Update the primary root report/relevant deliverable before continuing so current next steps and resume state reflect the new mission.
8. During synthesis, separate evidence types explicitly: real user feedback, second-hand comments, promotional/AFF/SEO material, weak search snippets, and deprecated/excluded sources.
9. Validation should check for scope leakage: excluded sources must not drive final conclusions, and downgraded promotional sources must not be used as primary ranking evidence.

## Example from VPN/airport research

- Original scope included V2EX, LINUX.DO, Zhihu, and GitHub.
- User interrupted and changed primary sources to IDC Flare / LINUX.DO / V2EX, excluded Zhihu, and downgraded GitHub to overview/promotional evidence only.
- Correct repair: reuse workspace, retain useful LINUX.DO artifact, mark Zhihu as deprecated background, add IDC Flare and self-host-vs-airport tasks, and ensure final report does not cite Zhihu or GitHub promotional lists as primary evidence.
