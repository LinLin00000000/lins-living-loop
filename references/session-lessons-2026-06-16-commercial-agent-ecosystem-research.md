# Session lesson: commercial agent ecosystem research

When an LLL run compares commercialized/forked/packaged agent products with a self-hosted agent stack, the useful output is usually not a flat feature table or a simple “commercial vs self-host” binary. Treat the products as layers in an ecosystem and preserve evidence discipline.

## Pattern

1. Split workers by evidence type, not just by product name:
   - local-language/community evidence (e.g. Zhihu, V2EX, LinuxDo, developer forums);
   - global/community evidence (Reddit, HN, GitHub, blogs);
   - official/product-architecture evidence (docs, product pages, terms, pricing, lifecycle rules).
2. In synthesis, classify each product by the layer it is trying to own:
   - **entry layer**: IM/mobile/desktop/web surfaces where the user issues commands;
   - **execution layer**: local desktop, cloud VM/sandbox, coding CLI, browser/files/shell, office apps;
   - **state layer**: memory, skills, files, task history, workspace, long-term logs;
   - **governance layer**: permissions, audit, rollback, sandbox, cost limits, data retention, export.
3. Compare the self-hosted tool as a **sovereign state/control layer** when the user cares about digital gardens, long-term memory, migration, auditability, or AI-OS style workflows. Compare commercial products as **entry/execution/productization layers** unless evidence shows they provide durable, exportable state governance.
4. Do not dismiss commercial wrappers as “just wrappers.” Identify the real productized value: reduced setup entropy, familiar channels, bundled model/account/billing, curated skills/experts, safety narrative, managed cloud/runtime, and support.
5. Preserve a mixed-strategy recommendation when warranted: self-hosted system owns long-term state and audit trail; commercial products are replaceable peripherals for low-risk entry points, office deliverables, or temporary cloud execution.

## Evidence discipline

- Use official docs/pages for product capabilities, lifecycle, data retention, pricing, and deployment shape.
- Use community evidence for friction, user concerns, failure modes, adoption patterns, and “what people actually care about.”
- Use hands-on media/blogs as medium-strength evidence when they show concrete tasks, logs, costs, or failure cases.
- Keep search snippets, inaccessible forums, SEO pages, and non-official domains in weak-evidence buckets.
- If workers conflict on whether a named product has official evidence, the supervisor should independently extract official pages before synthesis rather than averaging worker claims.
- Explicitly label products with weak/insufficient public evidence instead of filling gaps with generic category claims.

## Useful final-report frame

A strong report can use this spine:

1. “These are not the same kind of product” — taxonomy by layer.
2. What community users actually worry about: entry, domestic availability, permissions, token/cost runaway, skills, data boundaries.
3. Product-by-product analysis with evidence tiers.
4. Self-host vs commercial decision by risk, time horizon, and sovereignty needs.
5. User-specific architecture recommendation: what stays in the sovereign state layer, what can be outsourced to commercial peripherals.
6. Caveats and weak-evidence products.

## Pitfalls

- Do not make a binary winner/loser table when the right answer is role separation.
- Do not treat “24/7 cloud execution” as equivalent to durable long-term memory; check deletion, retention, export, and lifecycle terms.
- Do not let product marketing claims about safety replace concrete permission/audit/export analysis.
- Do not overfit to the exact product names from one wave; the method generalizes to future commercial agent forks and wrappers.
