---
title: Goals and Certification
aliases:
  - Goal System
  - Exams and Certification
status: active
doc_version: 1.0.0
implementation_version: mvp-0.68
last_reviewed: 2026-11-23
source_commit: 86f29b0d390ed2ecdbb0347d98ccb1175ac52728
source_commit_timestamp: "2026-11-23T23:12:28-05:00"
source_paths:
  - src/learnloop/goals
  - src/learnloop/learner/capability_grid.py
tags:
  - learnloop/concept
  - learnloop/goals
  - learnloop/certification
---

# Goals and Certification

Goals constrain scope, deadlines, required capabilities, and terminal evidence. They influence which work is valuable; they do not manufacture evidence.

## Goal projection

An active goal resolves to scoped facets/learning objects and a terminal contract. The frontier identifies unexamined, at-risk, or insufficiently demonstrated cells and contributes selection value. Forecasts and pace estimates are receipts/projections over evidence and time.

## Certification

Certification reads canonical facet × capability evidence under the confirmed terminal contract. It requires licensed observation mass, coverage, independence, and any cold/held-out conditions. The prediction-only LO EKF, learner claims, familiarity, and source-visible instruction do not grant certification credit.

^certification-boundary

## Exams

Exam pools reserve held-out items and quarantine them from ordinary practice. Exam sessions use the shared attempt application/post-attempt pipeline, then assemble report-level feedback. Calibration evaluates the grader/exam channel rather than silently changing scores.

## Cold probes

Certification may schedule a delayed cold probe on a fresh surface. It detects false certification after spacing and prevents immediate familiarity from being mistaken for durable ability. The shared serving eligibility rule can defer a time-bounded hold. When a scheduled probe can no longer measure cold, the serving path withdraws it and can offer the item as ordinary practice. From `mvp-0.61` (verdict policy `certification_cold_probe_policy_v2`, stamped on the outcome row) an answer whose every criterion is unassessed abstains (`indeterminate`, `grade_unavailable`, no correctness) and stays out of `false_certification_rate`; below the tag it scored its scheduling-only correctness as `held`. The scheduling stamps keep `v1`, and stored outcomes keep their verdicts.

## Goal series

Series and forecasts use copied/scratch state where replay or scenario analysis needs writes. Scratch repositories attach writable without migrating the copied live database unexpectedly.

## Modification guidance

- Change goal scope/contract semantics in versioned definitions and receipts.
- Keep forecast/calibration outputs separate from evidence.
- Preserve exam quarantine and coldness invariants.
- Add new certification rules to capability-grid/evidence tests and shadow evaluation.
- Treat `goals.md` as retained scaffolding pending a separate authority decision.

## Workflows and tests

- [[Goals Exams and Certification Workflow]]
- goal scope/frontier/projection/contract/certification suites
- exam pool/session/readiness/calibration suites
- cold-probe and false-certification metrics

