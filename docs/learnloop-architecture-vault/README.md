---
title: LearnLoop Architecture Vault
aliases:
  - Documentation Vault
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-08-18
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - ARCHITECTURE.md
  - REFACTOR_PROPOSAL.md
tags:
  - learnloop/home
  - learnloop/docs
---

# LearnLoop Architecture Vault

This folder is a standalone [Obsidian](https://obsidian.md/) vault for the current LearnLoop architecture. Open `docs/learnloop-architecture-vault` as a vault, then begin at [[Home]].

> [!important] Current implementation, not the historical specification
> Notes describe the refactored working tree at the source commit recorded in frontmatter, including uncommitted workspace changes made by the refactor. `spec.md` is historical; this vault treats executable code, migrations, tests, and `learnloop.toml` validation as authority.

## What is here

- [[Architecture Map]] — system boundaries and runtime composition.
- [[Learning System]] — the authoritative explanation of the learning algorithm and its intent.
- [[User Journey Map]] — step-by-step workflows, separate from module references.
- [[Data and State Map]] — Markdown/YAML authority, SQLite roles, replay, and rebuild.
- [[Module Catalog]] — every Python source module with its active/compat/dormant/evaluation status, plus [[Desktop Module Catalog]] for every TypeScript, TSX, and Rust module.
- [[Database Catalog]] — every `state.sqlite` user table and lifecycle role.
- [[Design Decision Index]] — why the refactor chose its current boundaries.
- [[Search Guide]] — useful Obsidian queries, properties, tags, backlinks, and graph filters.

## Reading rule

Each idea has one primary note. Other notes link to a heading or block instead of restating it. For example, modules that update learner state link to [[Learning System#Belief layers]]; provider-using workflows link to [[AI Architecture#Resolution path]]. Backlinks then show every consumer of that idea.

^single-source-rule

## Metadata confidence

Every Markdown note has `status`, a documentation `version`/`doc_version`, source paths, and source-revision metadata. Concept and workflow notes also pin `implementation_version`; generated module/table notes record their architecture/schema version and identify themselves as generated. Regenerate those catalogs when their sources move. See [[Documentation Conventions#Freshness model]].
