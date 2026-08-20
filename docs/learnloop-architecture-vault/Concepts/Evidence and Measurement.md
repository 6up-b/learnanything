---
title: Evidence and Measurement
aliases:
  - Measurement Model
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-08-17
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - src/learnloop/attempts/evidence.py
  - src/learnloop/attempts/effective_observation.py
  - src/learnloop/learner/measurement_state.py
  - src/learnloop/learner/facet_diagnostics.py
  - src/learnloop/learner/recall_coverage.py
tags:
  - learnloop/concept
  - learnloop/evidence
  - learnloop/measurement
---

# Evidence and Measurement

LearnLoop separates **what happened**, **how much of the contract it observed**, **how reliable/independent that observation is**, and **what uses the observation is licensed for**.

## Evidence is not score

A score summarizes rubric performance. Evidence retains criterion/facet targets, coverage, attempt type, assistance, grading confidence, correlation, source visibility, and provenance. Two 3/4 attempts can therefore update state differently without changing either historical score.

## Display labels

Every displayed facet estimate is labeled:

- `measured` — supported by direct eligible observations;
- `inferred` — predictive/propagated estimate without direct measurement authority;
- `claimed` — learner claim used as prior/context;
- `unknown` — insufficient licensed basis.

The label is a display/provenance vocabulary only. It cannot change thresholds, certification, or stored belief; renderers read one authority rather than re-deriving labels.

^measurement-labels

## Coverage

Coverage begins at the frozen criterion targets and contract frontier. It answers how much of the required facet/capability surface the response actually exposed. Dependencies, correlation groups, conjunctive criteria, and criterion tiers prevent naïve point-count double credit.

## Assistance, familiarity, and independence

- Hints dampen evidence and may cap memory ratings.
- A source-visible/instructional response is useful for learning but not cold certification.
- A revealed answer records priming; it may update a prediction while preserving the last cold-evidence clock.
- Recent exposure to the same item/surface/facet discounts independent evidence.
- Probe surfaces are single-use and must be never-before-seen for their diagnostic role.
- Repeated correlated criteria do not count as independent observations.

^assistance-independence

## Grader uncertainty

Grader confidence describes confidence in the judgment. Current mastery calibration keeps the learner score observation mean-preserving and adds interpretation variance to measurement noise rather than shrinking the score toward a prior. This prevents uncertain grading from moving the learner estimate in the wrong direction.

## Certification boundary

Prediction, routing priors, familiarity, learner claims, instructional answers, and source-grounded reader exchanges can influence selection or presentation. They do not become demonstrated certification evidence. Canonical direct evidence and explicit cold/held-out checks govern that boundary.

## Correction

Historical evidence is immutable. Measurement corrections, adjudication, and regrades append superseding/corrective events. Replay interprets the event history rather than rewriting the original row.

## Measurement quality

Audit paths report observation coverage, measurement rank, instrument servability, calibration, harmful writes, false certification, abstention, and no-data explicitly. A metric that cannot be computed must return `no_data` with counts, not a fabricated zero or one.

## Extension guidance

- Add modifiers to the shared evidence/application trace, not only a UI score.
- State what the signal may influence and what it must never influence.
- Add an instrument admission/revert criterion and audit visibility.
- Preserve measurement labels as provenance only.
- Extend anti-double-count, coldness, coverage, and replay tests.

## See also

[[Learning System#Belief layers]], [[Attempt Processing]], [[Goals and Certification]], [[Diagnosis and Remediation]], [[State and Persistence]].

