---
title: Design Decision Index
aliases:
  - ADR Index
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-08-17
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - REFACTOR_PROPOSAL.md
  - ARCHITECTURE.md
tags:
  - learnloop/decision
  - moc
---

# Design Decision Index

These notes capture the accepted decision, its context, consequences, and executable enforcement. They do not repeat the full concept explanation.

| Decision | Main effect |
|---|---|
| [[ADR-001 Domain ownership replaces generic services]] | behavior lives with attempts/learner/scheduling/etc. |
| [[ADR-002 Feature-owned structured AI contracts]] | providers implement transport, features own operation meaning |
| [[ADR-003 Explicit table roles govern rebuild]] | losslessness, not naming, controls replay |
| [[ADR-004 AI is optional and manual is typed]] | storage/manual learning work without a provider |
| [[ADR-005 Independent adapters]] | CLI, TUI, sidecar share public APIs, not each other |
| [[ADR-006 Schema-v2 config with one-way compatibility]] | canonical output, legacy input normalization |
| [[ADR-007 Immutable evidence and append-only correction]] | history stays interpretable |
| [[ADR-008 Coordinated atomic migrations and read-only inspection]] | safe concurrent opens and physically read-only doctor |
| [[ADR-009 Architecture rules are executable ratchets]] | boundaries fail CI instead of relying on memory |
| [[ADR-010 Production telemetry before retirement]] | no gated state deletion without owner-vault evidence |
| [[ADR-011 Retain legacy HTTP as a narrow capability]] | compatibility without weakening the structured protocol |
| [[ADR-012 Freeze the compatibility substrate]] | old vaults stay green without expanding legacy behavior |

## Source of accepted decisions

The implementation decisions are recorded in `REFACTOR_PROPOSAL.md` under **Implementation decisions (2026-08-17)** and its revision changelog. Current behavior and tests override any earlier proposal alternative.

