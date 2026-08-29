---
title: Tag Taxonomy
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-08-18
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - docs/learnloop-architecture-vault
tags:
  - learnloop/docs
  - learnloop/meta
  - learnloop/tags
---

# Tag Taxonomy

Tags filter note kinds and operational status; WikiLinks express semantic relationships.

## Canonical tag families

| Family | Examples | Use |
|---|---|---|
| `#learnloop/home` | Home, vault README | entry points |
| `#learnloop/architecture` | persistence, AI, adapters | software boundaries |
| `#learnloop/concept` | learning, evidence, goals | product/algorithm meaning |
| `#learnloop/workflow` | init, ingest, practice | procedures |
| `#learnloop/decision` | ADR notes | rationale |
| `#docs/module` | generated module notes | implementation lookup |
| `#learnloop/desktop/*` | generated TypeScript, TSX, and Rust module notes | desktop implementation lookup |
| `#learnloop/database/table` | generated table notes | database lookup |
| `#learnloop/configuration/*` | configuration references | settings lookup |
| `#learnloop/status/*` | compat, dormant, needs-owner-input | lifecycle filters |

Generated catalogs also use granular `layer/*`, `package/*`, `refactor/*`, and `architecture/reference` tags. Keep those machine-owned rather than normalizing them by hand.

## Rules

- Prefer two to five useful tags over a keyword cloud.
- Use `status` frontmatter for lifecycle; use a status tag only when sidebar/graph filtering is valuable.
- Do not encode source paths in tags; use `source_paths` properties and [[Search Guide]].
- Do not use tags as links between ideas; use WikiLinks and backlinks.
