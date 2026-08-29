---
title: Refactor Status
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-08-18
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - REFACTOR_PROPOSAL.md
  - ARCHITECTURE.md
tags:
  - learnloop/refactor
  - learnloop/status
---

# Refactor Status

## Complete in the working tree

- domain-owned package tree; no `learnloop.services` references;
- provider-neutral AI routing/transport and feature-owned contracts; no `learnloop.codex` namespace;
- real config schema/compat/loader/template split and schema-v2 defaults;
- shared bootstrap, coordinated repository opening, physically read-only doctor;
- CLI package split with exact help snapshots;
- durable content pipeline runner/jobs split and routed transcription;
- table-role registry, true derived owners, exact rebuild and shadow isolation;
- ingest queue/observation stores with write-ownership guards;
- architecture/import/private/SQL/dynamic-reference ratchets;
- updated architecture and algorithm-change documentation.

## Verification

Verification is owned by the executable oracle families and commands in [[Testing and Invariants#Verification commands]], not by a copied historical pass count. The repository snapshot does not contain a dated, committed full-suite report from which a current total can be audited, so this note deliberately makes no full-suite-count claim. The generated documentation catalogs instead carry reproducible coverage validators for their own source inventories.

## Deliberately retained

- `Repository` compatibility facade while further store extraction proceeds;
- frozen cross-domain cycle inventory, allowed only to shrink;
- Textual TUI and `goals.md` scaffolding;
- exact-capability legacy HTTP adapter;
- gen-2 source ingestion behind queue aliases;
- independently selected transcription route and consent semantics;
- compatibility substrate for old vaults.

## Owner-gated follow-up

Run deprecated-table telemetry against owner production vaults before any retirement. No schema drops/archive renames or owner-visible SQLite-admin FK change were made. See [[ADR-010 Production telemetry before retirement]].
