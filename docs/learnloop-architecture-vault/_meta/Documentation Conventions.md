---
title: Documentation Conventions
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-08-17
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - docs/learnloop-architecture-vault
tags:
  - learnloop/docs
  - learnloop/meta
---

# Documentation Conventions

## One idea, one authority

Concept notes explain intent. Architecture notes explain boundaries. Workflow notes give procedures. Reference notes enumerate implementation details. A lower-level note links to the authoritative heading rather than copying it. This makes backlinks a dependency map and prevents four stale explanations of the same algorithm.

See [[LearnLoop Architecture Vault#^single-source-rule]].

## Frontmatter contract

Every note carries the first five properties below. Authored concept, architecture, workflow, and decision notes also carry the review/version fields; generated catalogs use the equivalent generated provenance shown in their banners.

| Property | Meaning |
|---|---|
| `status` | documentation lifecycle; see [[Status Legend]] |
| `doc_version` or `version` | semantic version of the note's structure/content |
| `source_commit_timestamp` | commit timestamp, not documentation generation time |
| `source_paths` | executable authorities used by the note |
| `tags` | hierarchical filters for search/sidebar/graph |
| `implementation_version` | algorithm/config era described by an authored note |
| `last_reviewed` | most recent source comparison for an authored note |
| `source_commit` | repository HEAD or workspace state used for the inventory |

Generated references use boolean `generated: true`; when a generation date is stored it uses `generated_at`. They may also carry `architecture_version`, `schema_head`, `source_worktree_state`, `module`, `table_name`, `table_role`, or `refactor_status`.

## Link conventions

- Use `[[Note]]` for conceptual dependency.
- Use `[[Note#Heading]]` when only one section is relevant.
- Use `[[Note#^block-id]]` for a stable invariant or definition.
- Let backlinks answer “who depends on this?” instead of maintaining duplicate consumer lists by hand.
- Source paths use repository-relative code spans in prose; module notes expose exact paths as metadata.

## Callout vocabulary

> [!info] Context
> Background that changes how a section should be read.

> [!important] Invariant
> A rule protected by code or tests.

> [!warning] Gate
> An operation that is unsafe or incomplete without an explicit condition.

> [!example] Observable example
> A command or state transition verified against current behavior.

> [!failure] Compatibility trap
> A tempting modification that would reinterpret history or break an adapter.

## Freshness model

Authored notes are reviewed against their `source_paths`. Generated module and table notes are reproducible inventories: their generator records source metadata and coverage. A note is stale when its source changed after `last_reviewed`, its module/table disappeared, or a link target no longer resolves.

^freshness-model

## Mermaid rule

Use a diagram only for a relationship that is materially harder to understand as prose: multi-stage state changes, dependency direction, or branches with distinct persistence effects. Every diagram must be followed by an interpretation or invariant.
