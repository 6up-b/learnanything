---
title: ADR-010 Production telemetry before retirement
status: needs-owner-input
doc_version: 1.0.0
implementation_version: mvp-0.9
decision_date: 2026-08-17
decision_status: accepted-gate
last_reviewed: 2026-08-17
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - REFACTOR_PROPOSAL.md
  - src/learnloop/ops/doctor.py
tags:
  - learnloop/decision
  - learnloop/status/needs-owner-input
  - learnloop/telemetry
---

# ADR-010 Production telemetry before retirement

## Context

Contested deprecated tables appeared empty in repository fixtures, but fixture absence cannot prove an owner's production vault has no data. An aborting drop migration would also block the sequential chain.

## Decision

Add read-only doctor telemetry and warnings first. Perform no schema drops or archive renames in this refactor. Retain gated CRUD/table references and deliberate SQLite-admin behavior until owner production vaults report clean and approve the visible change.

## Evidence

All ten repository fixture databases were inspected read-only: present `source_exam_profiles`, `source_locator_schemes`, and `learner_theta` tables had zero rows; older schemas report unavailable rather than empty. No owner production vault was present.

## Consequences

- The refactor is data-conservative.
- A future retirement requires `learnloop doctor --vault PATH --json` on owner vaults, escalation of any nonzero count, explicit decision, and a separate migration/change.
- Zero fixture rows are not permission to delete production state.

> [!warning] Current gate
> This note intentionally remains `needs-owner-input`. It describes an operational prerequisite, not missing repository implementation.

