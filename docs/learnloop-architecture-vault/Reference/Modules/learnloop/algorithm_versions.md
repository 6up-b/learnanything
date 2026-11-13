---
title: "learnloop.algorithm_versions"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/algorithm_versions.py"
source_paths:
  - "src/learnloop/algorithm_versions.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.algorithm_versions module"
  - "src/learnloop/algorithm_versions.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop"
---

# `learnloop.algorithm_versions`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.algorithm_versions` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: Dependency-neutral algorithm-version vocabulary.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py) |
| Source lines | 1287 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `successors_from(version: str) -> frozenset[str]` ([source](../../../../../src/learnloop/algorithm_versions.py), line 998) — ``version`` and every later tag in :data:`SUCCESSOR_CHAIN`.

### Module constants

- `LEGACY_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 12)
- `KM_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 16)
- `P0_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 22)
- `REVEAL_LEDGER_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 27)
- `DIAGNOSIS_SPLIT_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 44)
- `PLACEMENT_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 63)
- `RECURRENCE_GROUP_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 77)
- `STUCK_PROMPT_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 95)
- `DAILY_PLAN_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 109)
- `PROBE_TIE_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 123)
- `LEARNER_TEXT_GAP_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 141)
- `PROOF_ROUTE_CHECK_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 175)
- `SOURCE_REFERENCE_GATE_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 193)
- `SOURCE_FIRST_NEEDS_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 202)
- `ROUTE_RULES_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 224)
- `VOI_STOPPING_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 245)
- `DECIDER_TIER1_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 261)
- `ROUTER_STAGED_FRAME_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 281)
- `ROUTER_MIXTURE_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 302)
- `METHOD_EXPLICIT_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 325)
- `REGRADE_CONTRACT_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 349)
- `ELIGIBILITY_DECISION_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 372)
- `INTENT_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 391)
- `ADAPTIVE_DIFFICULTY_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 413)
- `WORKBENCH_FIELD_SIGNALS_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 435)
- `READING_PATH_PLAN_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 455)
- `CLAIM_FIXES_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 477)
- `REPLAY_LEDGER_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 496)
- `ONE_ASK_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 522)
- `SUPERSEDED_CLAIMS_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 546)
- `ATTEMPT_CONTENT_STATE_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 573)
- `COLD_RETRY_RESCHEDULE_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 595)
- `READER_FOLLOWUPS_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 613)
- `DELIVERABLE_PLAN_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 632)
- `TEACHER_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 661)
- `HELP_FOLD_ATTACH_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 681)
- `LESSON_SUGGESTIONS_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 706)
- `DATA_CAPTURE_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 725)
- `FOLLOWUP_SERVE_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 741)
- `INTERVAL_FACTOR_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 762)
- `ROUTER_OBJECTIVE_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 775)
- `ROUTER_CALIBRATION_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 789)
- `ROUTER_LEARNED_TAIL_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 802)
- `ROUTER_FOLLOWUPS_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 810)
- `TEACHER_PROBES_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 828)
- `LESSON_OPPORTUNITY_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 843)
- `LESSON_OFFERS_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 860)
- `PHONE_PROBES_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 875)
- `FAILURE_SHARE_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 888)
- `UNEVIDENCED_RETURN_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 903)
- `SLIP_GAP_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 914)
- `FIGURE_WAIT_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 925)
- `FACET_BELIEF_FIX_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 936)
- `SUCCESSOR_CHAIN` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 944)
- `OLDEST_SUPPORTED` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1006)
- `DIAGNOSIS_SPLIT_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1014)
- `RECURRENCE_GROUP_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1019)
- `STUCK_PROMPT_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1025)
- `P0_SUCCESSOR_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1030)
- `P0_PROJECTION_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1031)
- `CANONICAL_STATE_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1038)
- `PLACEMENT_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1045)
- `DAILY_PLAN_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1050)
- `PROBE_TIE_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1055)
- `LEARNER_TEXT_GAP_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1061)
- `SOURCE_REFERENCE_GATE_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1065)
- `SOURCE_FIRST_NEEDS_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1069)
- `ROUTE_RULES_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1076)
- `VOI_STOPPING_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1083)
- `DECIDER_TIER1_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1087)
- `ROUTER_STAGED_FRAME_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1092)
- `ROUTER_MIXTURE_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1098)
- `METHOD_EXPLICIT_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1104)
- `REGRADE_CONTRACT_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1110)
- `ELIGIBILITY_DECISION_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1116)
- `INTENT_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1121)
- `ADAPTIVE_DIFFICULTY_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1127)
- `WORKBENCH_FIELD_SIGNALS_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1133)
- `READING_PATH_PLAN_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1138)
- `CLAIM_FIXES_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1144)
- `REPLAY_LEDGER_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1149)
- `ONE_ASK_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1155)
- `SUPERSEDED_CLAIMS_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1160)
- `ATTEMPT_CONTENT_STATE_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1166)
- `COLD_RETRY_RESCHEDULE_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1171)
- `READER_FOLLOWUPS_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1176)
- `DELIVERABLE_PLAN_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1180)
- `TEACHER_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1183)
- `HELP_FOLD_ATTACH_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1188)
- `LESSON_SUGGESTIONS_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1193)
- `DATA_CAPTURE_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1199)
- `FOLLOWUP_SERVE_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1204)
- `INTERVAL_FACTOR_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1211)
- `ROUTER_OBJECTIVE_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1217)
- `ROUTER_CALIBRATION_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1223)
- `ROUTER_LEARNED_TAIL_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1229)
- `ROUTER_FOLLOWUPS_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1234)
- `TEACHER_PROBES_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1239)
- `LESSON_OPPORTUNITY_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1246)
- `LESSON_OFFERS_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1252)
- `PHONE_PROBES_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1256)
- `FAILURE_SHARE_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1262)
- `UNEVIDENCED_RETURN_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1267)
- `SLIP_GAP_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1272)
- `FIGURE_WAIT_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1277)
- `FACET_BELIEF_FIX_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1282)
- `LATEST_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1287)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/successor|learnloop.adaptive_difficulty.successor]] — imports `ADAPTIVE_DIFFICULTY_ALGORITHM_VERSION`, `ADAPTIVE_DIFFICULTY_VERSIONS`, `LESSON_OPPORTUNITY_VERSIONS`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `ATTEMPT_CONTENT_STATE_VERSIONS`, `P0_PROJECTION_VERSIONS`, `REGRADE_CONTRACT_VERSIONS`, `REPLAY_LEDGER_VERSIONS`, `SOURCE_REFERENCE_GATE_VERSIONS`
- [[Reference/Modules/learnloop/attempts/blind_grading|learnloop.attempts.blind_grading]] — imports `DIAGNOSIS_SPLIT_VERSIONS`
- [[Reference/Modules/learnloop/attempts/grade_resolution|learnloop.attempts.grade_resolution]] — imports `REGRADE_CONTRACT_VERSIONS`, `SOURCE_REFERENCE_GATE_VERSIONS`
- [[Reference/Modules/learnloop/attempts/grading_support|learnloop.attempts.grading_support]] — imports `METHOD_EXPLICIT_VERSIONS`, `ROUTE_RULES_VERSIONS`
- [[Reference/Modules/learnloop/attempts/hint_fold|learnloop.attempts.hint_fold]] — imports `HELP_FOLD_ATTACH_VERSIONS`
- [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]] — imports `REGRADE_CONTRACT_VERSIONS`, `SOURCE_REFERENCE_GATE_VERSIONS`
- [[Reference/Modules/learnloop/attempts/stuck|learnloop.attempts.stuck]] — imports `STUCK_PROMPT_VERSIONS`
- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `LATEST_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/config/template|learnloop.config.template]] — imports `LATEST_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `DAILY_PLAN_VERSIONS`, `DELIVERABLE_PLAN_VERSIONS`, `READING_PATH_PLAN_VERSIONS`
- [[Reference/Modules/learnloop/daily_plan/lesson_offer|learnloop.daily_plan.lesson_offer]] — imports `FAILURE_SHARE_VERSIONS`
- [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]] — imports `LESSON_SUGGESTIONS_VERSIONS`, `ROUTER_MIXTURE_VERSIONS`, `TEACHER_VERSIONS`
- [[Reference/Modules/learnloop/daily_plan/policy|learnloop.daily_plan.policy]] — imports `ROUTER_MIXTURE_VERSIONS`, `ROUTER_STAGED_FRAME_VERSIONS`
- [[Reference/Modules/learnloop/data_capture/gates|learnloop.data_capture.gates]] — imports `DATA_CAPTURE_VERSIONS`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `CANONICAL_STATE_VERSIONS`, `FACET_BELIEF_FIX_VERSIONS`
- [[Reference/Modules/learnloop/decider_judgments|learnloop.decider_judgments]] — imports `DECIDER_TIER1_VERSIONS`
- [[Reference/Modules/learnloop/diagnosis/recurrence/live|learnloop.diagnosis.recurrence.live]] — imports `RECURRENCE_GROUP_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/diagnosis/recurrence/report|learnloop.diagnosis.recurrence.report]] — imports `RECURRENCE_GROUP_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `COLD_RETRY_RESCHEDULE_VERSIONS`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/actions|learnloop.diagnosis.text_gaps.actions]] — imports `LEARNER_TEXT_GAP_VERSIONS`
- [[Reference/Modules/learnloop/diagnosis/voi_stopping|learnloop.diagnosis.voi_stopping]] — imports `VOI_STOPPING_VERSIONS`
- [[Reference/Modules/learnloop/field/outcomes|learnloop.field.outcomes]] — imports `P0_ALGORITHM_VERSION`, `P0_SUCCESSOR_VERSIONS`
- [[Reference/Modules/learnloop/field/signals|learnloop.field.signals]] — imports `LEARNER_TEXT_GAP_VERSIONS`
- [[Reference/Modules/learnloop/field/workbench_signals|learnloop.field.workbench_signals]] — imports `WORKBENCH_FIELD_SIGNALS_VERSIONS`
- [[Reference/Modules/learnloop/figures/prefetch_ledger|learnloop.figures.prefetch_ledger]] — imports `FIGURE_WAIT_VERSIONS`
- [[Reference/Modules/learnloop/followup_serve/gates|learnloop.followup_serve.gates]] — imports `FOLLOWUP_SERVE_VERSIONS`
- [[Reference/Modules/learnloop/goals/certification_cold_probe|learnloop.goals.certification_cold_probe]] — imports `SOURCE_REFERENCE_GATE_VERSIONS`
- [[Reference/Modules/learnloop/goals/exam_pool|learnloop.goals.exam_pool]] — imports `SOURCE_REFERENCE_GATE_VERSIONS`
- [[Reference/Modules/learnloop/instructional/needs|learnloop.instructional.needs]] — imports `SOURCE_FIRST_NEEDS_VERSIONS`
- [[Reference/Modules/learnloop/instructional/reader_digest|learnloop.instructional.reader_digest]] — imports `READER_FOLLOWUPS_VERSIONS`
- [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]] — imports `READER_FOLLOWUPS_VERSIONS`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `CANONICAL_STATE_VERSIONS`, `KM_ALGORITHM_VERSION`, `P0_ALGORITHM_VERSION`, `P0_PROJECTION_VERSIONS`, `P0_SUCCESSOR_VERSIONS`, `REVEAL_LEDGER_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/learner/facet_evidence_timeline|learnloop.learner.facet_evidence_timeline]] — imports `REGRADE_CONTRACT_VERSIONS`
- [[Reference/Modules/learnloop/learner/facet_state_reader|learnloop.learner.facet_state_reader]] — imports `FACET_BELIEF_FIX_VERSIONS`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `CLAIM_FIXES_VERSIONS`, `SUPERSEDED_CLAIMS_VERSIONS`
- [[Reference/Modules/learnloop/learner/recall_calibration|learnloop.learner.recall_calibration]] — imports `LEGACY_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/ops/upgrades|learnloop.ops.upgrades]] — imports `FACET_BELIEF_FIX_ALGORITHM_VERSION`, `LATEST_ALGORITHM_VERSION`, `SUCCESSOR_CHAIN`
- [[Reference/Modules/learnloop/placement/report|learnloop.placement.report]] — imports `PLACEMENT_VERSIONS`
- [[Reference/Modules/learnloop/placement/state|learnloop.placement.state]] — imports `DIAGNOSIS_SPLIT_VERSIONS`, `LEARNER_TEXT_GAP_VERSIONS`, `PLACEMENT_VERSIONS`, `UNEVIDENCED_RETURN_VERSIONS`
- [[Reference/Modules/learnloop/router_objective_switches|learnloop.router_objective_switches]] — imports `FACET_BELIEF_FIX_VERSIONS`, `FAILURE_SHARE_VERSIONS`, `INTERVAL_FACTOR_VERSIONS`, `LESSON_OFFERS_VERSIONS`, `ROUTER_CALIBRATION_VERSIONS`, `ROUTER_FOLLOWUPS_VERSIONS`, `ROUTER_LEARNED_TAIL_VERSIONS`, `ROUTER_OBJECTIVE_VERSIONS`, `SLIP_GAP_VERSIONS`
- [[Reference/Modules/learnloop/scheduling/intent/serving|learnloop.scheduling.intent.serving]] — imports `INTENT_VERSIONS`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `PROBE_TIE_VERSIONS`
- [[Reference/Modules/learnloop/serve_eligibility|learnloop.serve_eligibility]] — imports `ELIGIBILITY_DECISION_VERSIONS`, `ONE_ASK_VERSIONS`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `REGRADE_CONTRACT_VERSIONS`
- [[Reference/Modules/learnloop/substrate/recurrence_groups|learnloop.substrate.recurrence_groups]] — imports `DECIDER_TIER1_VERSIONS`, `RECURRENCE_GROUP_VERSIONS`
- [[Reference/Modules/learnloop/substrate/shadow_rebuild|learnloop.substrate.shadow_rebuild]] — imports `OLDEST_SUPPORTED`
- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `TEACHER_VERSIONS`
- [[Reference/Modules/learnloop/teacher/te2|learnloop.teacher.te2]] — imports `TEACHER_PROBES_VERSIONS`
- [[Reference/Modules/learnloop/version_floor|learnloop.version_floor]] — imports `OLDEST_SUPPORTED`
- [[Reference/Modules/learnloop_sidecar/request_origin|learnloop_sidecar.request_origin]] — imports `PHONE_PROBES_VERSIONS`

### Repository tooling consumers

- [scripts/refactor_measures.py](../../../../../scripts/refactor_measures.py)

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/successor|learnloop.adaptive_difficulty.successor]], [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/blind_grading|learnloop.attempts.blind_grading]], [[Reference/Modules/learnloop/attempts/grade_resolution|learnloop.attempts.grade_resolution]], [[Reference/Modules/learnloop/attempts/grading_support|learnloop.attempts.grading_support]] and 46 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/ad23_fakes.py](../../../../../tests/ad23_fakes.py) — direct import
- [tests/ad_fakes.py](../../../../../tests/ad_fakes.py) — direct import
- [tests/canonical_facet_helpers.py](../../../../../tests/canonical_facet_helpers.py) — direct import
- [tests/cold_retry_reschedule_helpers.py](../../../../../tests/cold_retry_reschedule_helpers.py) — direct import
- [tests/curriculum_c1_plan_follows_path_helpers.py](../../../../../tests/curriculum_c1_plan_follows_path_helpers.py) — direct import
- [tests/data_capture_a2_measurement_helpers.py](../../../../../tests/data_capture_a2_measurement_helpers.py) — direct import
- [tests/followup_fg1d_probe_shadow_helpers.py](../../../../../tests/followup_fg1d_probe_shadow_helpers.py) — direct import
- [tests/followup_serve_helpers.py](../../../../../tests/followup_serve_helpers.py) — direct import
- [tests/followups_nov2_help_fold_helpers.py](../../../../../tests/followups_nov2_help_fold_helpers.py) — direct import
- [tests/helpers.py](../../../../../tests/helpers.py) — direct import
- [tests/ih2_lessons_compete_helpers.py](../../../../../tests/ih2_lessons_compete_helpers.py) — direct import
- [tests/instruct_handoff_ih0_helpers.py](../../../../../tests/instruct_handoff_ih0_helpers.py) — direct import
- [tests/intent_fakes.py](../../../../../tests/intent_fakes.py) — direct import
- [tests/learner_report_superseded_helpers.py](../../../../../tests/learner_report_superseded_helpers.py) — direct import
- [tests/lp_claim_fixes_review_helpers.py](../../../../../tests/lp_claim_fixes_review_helpers.py) — direct import
- [tests/mobile_v3_probes_helpers.py](../../../../../tests/mobile_v3_probes_helpers.py) — direct import
- [tests/plan_follows_path_helpers.py](../../../../../tests/plan_follows_path_helpers.py) — direct import
- [tests/reader_ca2_codex_rereview_helpers.py](../../../../../tests/reader_ca2_codex_rereview_helpers.py) — direct import
- [tests/reader_ca2_codex_review_helpers.py](../../../../../tests/reader_ca2_codex_review_helpers.py) — direct import
- [tests/reader_followups_helpers.py](../../../../../tests/reader_followups_helpers.py) — direct import
- [tests/reader_rw3a_landing_helpers.py](../../../../../tests/reader_rw3a_landing_helpers.py) — direct import
- [tests/rebuild_equivalence_helpers.py](../../../../../tests/rebuild_equivalence_helpers.py) — direct import
- [tests/recurrence_benchmarks_helpers.py](../../../../../tests/recurrence_benchmarks_helpers.py) — direct import
- [tests/regrade_contract_successor_helpers.py](../../../../../tests/regrade_contract_successor_helpers.py) — direct import
- [tests/regrade_contract_upgrade_helpers.py](../../../../../tests/regrade_contract_upgrade_helpers.py) — direct import
- [tests/required_method_grading_helpers.py](../../../../../tests/required_method_grading_helpers.py) — direct import
- [tests/ro5_calibration_helpers.py](../../../../../tests/ro5_calibration_helpers.py) — direct import
- [tests/ro5_checks_helpers.py](../../../../../tests/ro5_checks_helpers.py) — direct import
- [tests/rospeed_join_helpers.py](../../../../../tests/rospeed_join_helpers.py) — direct import
- [tests/route_rules_in_grader_helpers.py](../../../../../tests/route_rules_in_grader_helpers.py) — direct import
- [tests/router_card_helpers.py](../../../../../tests/router_card_helpers.py) — direct import
- [tests/router_mixture_helpers.py](../../../../../tests/router_mixture_helpers.py) — direct import
- [tests/te3b_offers_helpers.py](../../../../../tests/te3b_offers_helpers.py) — direct import
- [tests/teacher_fakes.py](../../../../../tests/teacher_fakes.py) — direct import
- [tests/teacher_te1b_suggestions_helpers.py](../../../../../tests/teacher_te1b_suggestions_helpers.py) — direct import
- [tests/teacher_te2_probes_helpers.py](../../../../../tests/teacher_te2_probes_helpers.py) — direct import
- [tests/test_ad23_successor.py](../../../../../tests/test_ad23_successor.py) — direct import
  - `test_the_successor_is_the_next_link`
- [tests/test_ad2_serving.py](../../../../../tests/test_ad2_serving.py) — direct import
  - `test_generation_prompt_has_no_band_language_under_successor`
  - `test_selection_switch_off_restores_lane_order`
- [tests/test_ad_denial_log.py](../../../../../tests/test_ad_denial_log.py) — direct import
  - `test_an_upgrade_through_the_table_archives_once_after_the_final_step`
  - `test_old_format_lines_stay_readable_and_are_grouped_as_unrecorded`
  - `test_the_report_renders_a_guard_block_without_entries`
  - `test_v2_f2_a_report_without_the_lock_does_not_count_archives`
- [tests/test_ai_config.py](../../../../../tests/test_ai_config.py) — direct import
  - `test_default_config_contains_ai_codex_profile`
  - `test_in_memory_defaults_match_persisted_algorithm_and_codex_profile`
- [tests/test_architecture.py](../../../../../tests/test_architecture.py) — direct import
  - `test_assessment_service_reexports_neutral_algorithm_versions`
- [tests/test_assumed_known.py](../../../../../tests/test_assumed_known.py) — direct import
  - `test_new_vaults_start_with_placement_on`
- [tests/test_attempt_content_state_race.py](../../../../../tests/test_attempt_content_state_race.py) — direct import
  - `test_below_the_tag_the_retiring_sync_is_still_undone_as_the_predecessor`
- [tests/test_attempt_content_state_successor.py](../../../../../tests/test_attempt_content_state_successor.py) — direct import
  - `test_mvp037_is_one_constant_after_mvp036`
- [tests/test_batch3_landing.py](../../../../../tests/test_batch3_landing.py) — direct import
  - `test_mvp035_is_one_constant_after_mvp034_and_the_latest`
- [tests/test_canonical_projection_fold_skip.py](../../../../../tests/test_canonical_projection_fold_skip.py) — direct import
- [tests/test_cold_retry_reschedule.py](../../../../../tests/test_cold_retry_reschedule.py) — direct import
  - `test_mvp038_is_one_constant_after_mvp037`
- [tests/test_config_refactor.py](../../../../../tests/test_config_refactor.py) — direct import
  - `test_a_successor_merge_appends_one_tag_and_every_gate_follows`
  - `test_new_vaults_start_at_the_latest_algorithm_version`
  - `test_the_template_renders_at_every_tag_by_its_label_alone`
- [tests/test_curriculum_c0b_landing.py](../../../../../tests/test_curriculum_c0b_landing.py) — direct import
- [tests/test_curriculum_c1_landing.py](../../../../../tests/test_curriculum_c1_landing.py) — direct import
  - `test_the_chain_is_rw6b_then_c1`
- [tests/test_curriculum_c1_plan_follows_path.py](../../../../../tests/test_curriculum_c1_plan_follows_path.py) — direct import
  - `test_the_successor_is_one_constant_after_rw6bs_followups`
- [tests/test_daily_plan_composition.py](../../../../../tests/test_daily_plan_composition.py) — direct import
  - `test_a_check_miss_awaiting_its_diagnosis_stays_assumed_and_is_not_rechecked`
- [tests/test_data_capture_a1_prefilter.py](../../../../../tests/test_data_capture_a1_prefilter.py) — direct import
- [tests/test_data_capture_a2_measurement.py](../../../../../tests/test_data_capture_a2_measurement.py) — direct import
- [tests/test_data_capture_a5_not_ready_floor.py](../../../../../tests/test_data_capture_a5_not_ready_floor.py) — direct import
- [tests/test_data_capture_a6_delayed_pick.py](../../../../../tests/test_data_capture_a6_delayed_pick.py) — direct import
- [tests/test_data_capture_successor.py](../../../../../tests/test_data_capture_successor.py) — direct import
  - `test_the_successor_is_one_constant_after_te1b_and_the_latest`
- [tests/test_diagnosis_input_provenance.py](../../../../../tests/test_diagnosis_input_provenance.py) — direct import
  - `test_f5_every_tag_defaults_the_switch_off`
- [tests/test_effective_defaults_golden.py](../../../../../tests/test_effective_defaults_golden.py) — direct import
  - `test_every_tag_has_the_latest_defaults_apart_from_its_label`
  - `test_the_golden_file_reads_back_as_the_effective_config`
- [tests/test_evsi_staged_binding.py](../../../../../tests/test_evsi_staged_binding.py) — direct import
- [tests/test_exam_protection_review.py](../../../../../tests/test_exam_protection_review.py) — direct import
  - `test_replay_never_reads_the_switch`
- [tests/test_facet_belief_successor.py](../../../../../tests/test_facet_belief_successor.py) — direct import
  - `test_the_successor_is_one_constant_after_the_figure_wait_estimate_and_the_latest`
- [tests/test_facet_state_write_on_change.py](../../../../../tests/test_facet_state_write_on_change.py) — direct import
- [tests/test_field_split_outcomes.py](../../../../../tests/test_field_split_outcomes.py) — direct import
  - `test_blind_grades_diagnoses_and_regrades_keep_the_epoch_contract`
- [tests/test_field_workbench_signals.py](../../../../../tests/test_field_workbench_signals.py) — direct import
  - `test_the_successor_vocabulary_is_one_constant_after_its_predecessor`
- [tests/test_figure_wait_estimate.py](../../../../../tests/test_figure_wait_estimate.py) — direct import
  - `test_at_the_tag_the_rows_say_v2_and_the_records_carry_ws_basis`
  - `test_switched_off_or_below_the_tag_the_rows_say_v1_and_the_records_are_as_before`
- [tests/test_figure_wait_successor.py](../../../../../tests/test_figure_wait_successor.py) — direct import
  - `test_the_successor_is_one_constant_after_slip_or_gap_and_the_latest`
- [tests/test_followup_codex_review.py](../../../../../tests/test_followup_codex_review.py) — direct import
  - `test_f6_a_crash_after_the_diagnosis_ended_is_recovered_by_next`
  - `test_f6_startup_recovery_needs_no_click`
- [tests/test_followup_reserved_only.py](../../../../../tests/test_followup_reserved_only.py) — direct import
  - `test_the_mint_and_batch_paths_refuse_a_reserved_question_at_the_tag_only`
- [tests/test_followup_successor.py](../../../../../tests/test_followup_successor.py) — direct import
  - `test_the_successor_is_one_constant_after_data_capture`
- [tests/test_forecast_receipts.py](../../../../../tests/test_forecast_receipts.py) — direct import
  - `test_a_regrade_re_resolves_the_forecast`
- [tests/test_forecast_receipts_landing.py](../../../../../tests/test_forecast_receipts_landing.py) — direct import
  - `test_the_resolver_reads_the_regraded_events_the_lineage_names_never_a_retired_one`
- [tests/test_held_grade_composition.py](../../../../../tests/test_held_grade_composition.py) — direct import
  - `test_a_diagnosis_of_a_held_attempt_is_never_read_as_a_wrong_answer`
  - `test_a_held_attempt_queues_no_gap_reading_as_a_failure`
  - `test_an_empty_stuck_answer_never_reaches_the_grader`
  - `test_placement_and_the_field_read_a_held_attempt_as_unassessed`
- [tests/test_help_fold_attach_successor.py](../../../../../tests/test_help_fold_attach_successor.py) — direct import
  - `test_mvp042_is_one_constant_after_mvp041_and_the_latest`
- [tests/test_hypothesis_marks.py](../../../../../tests/test_hypothesis_marks.py) — direct import
  - `test_with_no_causes_on_the_attempt_the_bundle_has_no_key`
- [tests/test_ih3_learner_preferences.py](../../../../../tests/test_ih3_learner_preferences.py) — direct import
- [tests/test_ih4_preferences_inform_router.py](../../../../../tests/test_ih4_preferences_inform_router.py) — direct import
- [tests/test_ih5_successor.py](../../../../../tests/test_ih5_successor.py) — direct import
  - `test_the_successor_is_one_constant_after_phone_v3`
- [tests/test_ih6_workbench_open_item.py](../../../../../tests/test_ih6_workbench_open_item.py) — direct import
- [tests/test_ih7_lesson_sources_follow_diagnosis.py](../../../../../tests/test_ih7_lesson_sources_follow_diagnosis.py) — direct import
- [tests/test_ih_lesson_candidate_after_cold_miss.py](../../../../../tests/test_ih_lesson_candidate_after_cold_miss.py) — direct import
- [tests/test_instruct_handoff_ih1.py](../../../../../tests/test_instruct_handoff_ih1.py) — direct import
  - `test_no_new_draw_joins_an_open_item`
- [tests/test_intent_codex_rereview.py](../../../../../tests/test_intent_codex_rereview.py) — direct import
  - `test_f2_the_chain_ends_at_the_intent_successor`
- [tests/test_intent_codex_review.py](../../../../../tests/test_intent_codex_review.py) — direct import
- [tests/test_intent_fix_round4.py](../../../../../tests/test_intent_fix_round4.py) — direct import
  - `test_f15_the_probe_contract_carries_the_diagnostic_variant`
- [tests/test_intent_fix_round5.py](../../../../../tests/test_intent_fix_round5.py) — direct import
- [tests/test_intent_fix_round6.py](../../../../../tests/test_intent_fix_round6.py) — direct import
- [tests/test_intent_fix_round7.py](../../../../../tests/test_intent_fix_round7.py) — direct import
- [tests/test_intent_plan.py](../../../../../tests/test_intent_plan.py) — direct import
- [tests/test_km2b_consumer_rekey.py](../../../../../tests/test_km2b_consumer_rekey.py) — direct import
  - `test_every_canonical_version_refuses_legacy_facet_state_write`
- [tests/test_learner_protection_predicates.py](../../../../../tests/test_learner_protection_predicates.py) — direct import
- [tests/test_learner_report_superseded.py](../../../../../tests/test_learner_report_superseded.py) — direct import
  - `test_the_tag_is_one_constant_after_mvp035_and_the_latest`
- [tests/test_lp_claim_fixes.py](../../../../../tests/test_lp_claim_fixes.py) — direct import
  - `test_the_successor_is_one_constant_after_its_predecessor`
- [tests/test_lp_claim_fixes_rereview.py](../../../../../tests/test_lp_claim_fixes_rereview.py) — direct import
  - `test_f9_a_miss_the_diagnosis_timeout_decides_carries_its_line_reopened_after_the_deadline`
- [tests/test_mobile_v3_probes.py](../../../../../tests/test_mobile_v3_probes.py) — direct import
  - `test_without_phone_probes_the_phone_is_v2s`
- [tests/test_mobile_v3_successor.py](../../../../../tests/test_mobile_v3_successor.py) — direct import
  - `test_the_successor_is_one_constant_after_te3b_and_the_latest`
- [tests/test_model_grade_lane.py](../../../../../tests/test_model_grade_lane.py) — direct import
  - `test_rebuild_moves_only_learning_objects_with_model_graded_attempts`
- [tests/test_observation_ledger_bulk.py](../../../../../tests/test_observation_ledger_bulk.py) — direct import
  - `test_p0_replays_bulk_load_calibration_references_once`
- [tests/test_pfc_unverified_unassessed.py](../../../../../tests/test_pfc_unverified_unassessed.py) — direct import
- [tests/test_placement_diagnosis_decides.py](../../../../../tests/test_placement_diagnosis_decides.py) — direct import
- [tests/test_placement_fixture_copies.py](../../../../../tests/test_placement_fixture_copies.py) — direct import
  - `test_no_lo_answered_without_a_due_time_leaves_the_queue_at_the_latest_tag`
  - `test_the_hole_stays_at_the_old_tag_and_with_the_switch_off`
- [tests/test_placement_split_grades.py](../../../../../tests/test_placement_split_grades.py) — direct import
- [tests/test_placement_unevidenced_return.py](../../../../../tests/test_placement_unevidenced_return.py) — direct import
  - `test_the_successor_is_one_constant_after_its_predecessor_and_the_latest`
- [tests/test_plan_determinism.py](../../../../../tests/test_plan_determinism.py) — direct import
  - `test_every_tag_defaults_the_switch_on`
  - `test_replay_never_reads_the_switch`
  - `test_the_switch_acts_only_where_the_router_composes_today`
- [tests/test_plan_determinism_landing.py](../../../../../tests/test_plan_determinism_landing.py) — direct import
- [tests/test_plan_follows_path.py](../../../../../tests/test_plan_follows_path.py) — direct import
  - `test_the_successor_is_one_constant_after_rw2d`
- [tests/test_pr4_superseded_claims_landing.py](../../../../../tests/test_pr4_superseded_claims_landing.py) — direct import
  - `test_landing_i_a_too_easy_retirement_during_a_session`
  - `test_landing_i_control_below_the_tag_the_same_session_reopens_the_retired_row`
- [tests/test_reader_ca2_one_ask.py](../../../../../tests/test_reader_ca2_one_ask.py) — direct import
  - `test_the_successor_is_one_constant_after_rebuild_equivalence`
- [tests/test_reader_cues.py](../../../../../tests/test_reader_cues.py) — direct import
  - `test_a_split_cue_names_the_diagnosers_statement_as_the_rail_does`
- [tests/test_reader_digest_narrative.py](../../../../../tests/test_reader_digest_narrative.py) — direct import
  - `test_below_the_follow_ups_successor_the_summary_row_says_so`
- [tests/test_reader_followups_successor.py](../../../../../tests/test_reader_followups_successor.py) — direct import
  - `test_mvp039_is_one_constant_after_mvp038_and_the_latest`
- [tests/test_reader_guidance.py](../../../../../tests/test_reader_guidance.py) — direct import
  - `test_split_guide_reason_names_the_diagnosers_statement`
- [tests/test_reader_recap_review_r2.py](../../../../../tests/test_reader_recap_review_r2.py) — direct import
  - `test_f1_r2_the_as_of_curve_ignores_gradings_recorded_after_the_cutoff`
- [tests/test_reader_recap_review_r3.py](../../../../../tests/test_reader_recap_review_r3.py) — direct import
  - `test_f2_r3_embedded_credit_banking_beside_standing_direct_credit_answers_the_claim`
  - `test_f2_r3_embedded_credit_whose_direct_credit_was_regraded_away_leaves_the_claim_open`
- [tests/test_reading_step_switch.py](../../../../../tests/test_reading_step_switch.py) — direct import
  - `test_every_tag_defaults_the_switch_on`
  - `test_new_vaults_read_on_from_the_furthest_section`
  - `test_replay_never_reads_the_switch`
  - `test_the_reading_step_acts_wherever_the_plan_acts_behind_its_switch`
  - `test_the_reading_step_is_not_a_successor_tag`
- [tests/test_rebuild_equivalence.py](../../../../../tests/test_rebuild_equivalence.py) — direct import
  - `test_a_second_learner_report_on_an_lo_after_an_attempt_rebuilds_to_live`
- [tests/test_rebuild_equivalence_review.py](../../../../../tests/test_rebuild_equivalence_review.py) — direct import
  - `test_the_successor_is_one_constant_after_its_predecessor`
- [tests/test_recurrence_benchmarks.py](../../../../../tests/test_recurrence_benchmarks.py) — direct import
  - `test_b3_replays_the_vaults_labelled_pairs`
- [tests/test_recurrence_commands.py](../../../../../tests/test_recurrence_commands.py) — direct import
  - `test_successor_vocabulary`
- [tests/test_recurrence_merge_composition.py](../../../../../tests/test_recurrence_merge_composition.py) — direct import
- [tests/test_reference_gate_imports.py](../../../../../tests/test_reference_gate_imports.py) — direct import
  - `test_a_regrade_after_the_tag_binds_an_attempt_recorded_before_it`
  - `test_a_shadow_rebuild_at_the_tag_shows_zero_deltas`
  - `test_below_the_tag_a_regrade_changes_nothing`
  - `test_below_the_tag_the_gate_never_runs`
  - `test_the_gate_is_a_successor_after_the_route_check`
  - `test_the_projection_reads_the_recorded_status_on_replay`
  - `test_the_regraded_grade_is_gated_live_and_on_rebuild`
- [tests/test_regrade_contract_replay.py](../../../../../tests/test_regrade_contract_replay.py) — direct import
- [tests/test_regrade_contract_successor.py](../../../../../tests/test_regrade_contract_successor.py) — direct import
  - `test_the_successor_is_the_latest_and_keeps_every_predecessor`
- [tests/test_required_method_authority.py](../../../../../tests/test_required_method_authority.py) — direct import
  - `test_a_live_answer_its_regrade_and_replay_are_graded_under_the_frozen_field`
- [tests/test_required_method_grading.py](../../../../../tests/test_required_method_grading.py) — direct import
  - `test_the_method_explicit_successor_is_the_latest_after_the_route_rules`
- [tests/test_ro0_codex_review.py](../../../../../tests/test_ro0_codex_review.py) — direct import
  - `test_f3_a_list_that_served_no_head_still_decides_nothing_and_reads_no_ad`
  - `test_f3_a_served_offer_keeps_its_candidates_ad_numbers`
- [tests/test_ro0_codex_verify.py](../../../../../tests/test_ro0_codex_verify.py) — direct import
  - `test_r1_an_arranged_check_keeps_its_objective_whatever_its_delay_meets`
  - `test_r1_an_unserved_check_keeps_its_state_whatever_its_type_meets`
- [tests/test_ro0_gate.py](../../../../../tests/test_ro0_gate.py) — direct import
  - `test_the_plan_blocks_rows_and_serves_are_the_same_on_and_off`
- [tests/test_ro1_availability.py](../../../../../tests/test_ro1_availability.py) — direct import
- [tests/test_ro1_availability_reads.py](../../../../../tests/test_ro1_availability_reads.py) — direct import
- [tests/test_ro1_interval_factor.py](../../../../../tests/test_ro1_interval_factor.py) — direct import
  - `test_the_gate_is_the_tag_and_the_switch`
- [tests/test_ro1_projection.py](../../../../../tests/test_ro1_projection.py) — direct import
- [tests/test_ro1_self_report.py](../../../../../tests/test_ro1_self_report.py) — direct import
- [tests/test_ro1_successor.py](../../../../../tests/test_ro1_successor.py) — direct import
  - `test_the_successor_is_one_constant_after_fg1_and_the_latest`
- [tests/test_ro1_upgrade_report.py](../../../../../tests/test_ro1_upgrade_report.py) — direct import
- [tests/test_ro2_ad_raw_document_reads.py](../../../../../tests/test_ro2_ad_raw_document_reads.py) — direct import
  - `test_ro4s_reading_action_maps_its_section_through_the_chokepoint`
- [tests/test_ro4_codex_review.py](../../../../../tests/test_ro4_codex_review.py) — direct import
- [tests/test_ro4_goals.py](../../../../../tests/test_ro4_goals.py) — direct import
  - `test_create_goal_below_the_tag_writes_no_use_weight_even_when_asked`
  - `test_create_goal_copies_the_asked_use_weight_or_the_default_when_left_alone`
  - `test_the_contract_is_copied_at_confirmation_at_the_tag_and_adjustable`
  - `test_the_goal_form_is_told_the_default_use_weight_at_the_tag_only`
- [tests/test_ro4_objective_serving.py](../../../../../tests/test_ro4_objective_serving.py) — direct import
- [tests/test_ro4_successor.py](../../../../../tests/test_ro4_successor.py) — direct import
  - `test_the_successor_is_one_constant_after_ro1_and_the_latest`
- [tests/test_ro4_trace_report.py](../../../../../tests/test_ro4_trace_report.py) — direct import
  - `test_the_cli_prints_a_decisions_trace_and_the_report`
  - `test_the_first_day_report_against_the_predecessor_on_a_synthetic_vault`
  - `test_the_why_surface_offers_the_trace_in_plain_words`
- [tests/test_ro5_calibration.py](../../../../../tests/test_ro5_calibration.py) — direct import
  - `test_below_the_tag_the_cli_report_has_no_calibration_section`
- [tests/test_ro5_codex_review.py](../../../../../tests/test_ro5_codex_review.py) — direct import
  - `test_f5_the_check_arm_off_restores_ro4s_weight_after_scores_accumulated`
- [tests/test_ro5_landing.py](../../../../../tests/test_ro5_landing.py) — direct import
  - `test_r5_1_below_the_tag_and_with_the_objective_off_fg1s_gate_is_unchanged`
  - `test_r5_2_the_objective_report_prints_w_and_its_posterior`
  - `test_r5_3_how_was_this_chosen_is_plain_words_with_no_stage_names_or_symbols`
- [tests/test_ro5_picks.py](../../../../../tests/test_ro5_picks.py) — direct import
  - `test_below_the_tag_and_at_zero_nothing_is_assigned_and_the_pick_resolves`
- [tests/test_ro5_stop_coin.py](../../../../../tests/test_ro5_stop_coin.py) — direct import
- [tests/test_ro5_successor.py](../../../../../tests/test_ro5_successor.py) — direct import
  - `test_the_successor_is_one_constant_after_ro4_and_the_latest`
- [tests/test_ro6_codex_rereview.py](../../../../../tests/test_ro6_codex_rereview.py) — direct import
  - `test_f1_a_complete_return_leaves_an_unknown_dated_use_out_and_keeps_a_window_with_no_checkable_use`
  - `test_f3_the_chooser_values_the_candidates_again_at_the_carried_cutoff`
- [tests/test_ro6_codex_review.py](../../../../../tests/test_ro6_codex_review.py) — direct import
  - `test_f4_a_diagnosis_queued_after_the_decisions_moment_never_enters_its_features`
  - `test_f5_the_contrasts_return_reader_admits_an_import_only_once_known`
- [tests/test_ro6_landing.py](../../../../../tests/test_ro6_landing.py) — direct import
  - `test_r12_with_the_carried_evaluation_blocked_the_choosers_wait_returns`
  - `test_r2_a_served_decision_logs_its_objective_under_the_generator_it_served`
  - `test_r3_the_no_model_branch_answers_within_the_first_pass_and_censors_the_carried_backup`
  - `test_r7_a_served_decision_freezes_its_support_and_the_measurable_tail`
- [tests/test_ro6_serving.py](../../../../../tests/test_ro6_serving.py) — direct import
- [tests/test_ro6_successor.py](../../../../../tests/test_ro6_successor.py) — direct import
  - `test_the_successor_is_one_constant_after_ro5_and_the_latest`
- [tests/test_ro6_tail_data.py](../../../../../tests/test_ro6_tail_data.py) — direct import
- [tests/test_rofu_ad_latent.py](../../../../../tests/test_rofu_ad_latent.py) — direct import
  - `test_ads_entry_point_hands_the_latent_moments_only_when_asked`
- [tests/test_rofu_ad_link.py](../../../../../tests/test_rofu_ad_link.py) — direct import
  - `test_the_numeric_policy_reads_ads_own_predictive_only_at_the_tag_with_its_switch`
- [tests/test_rofu_carried.py](../../../../../tests/test_rofu_carried.py) — direct import
  - `test_below_the_tag_the_no_model_branch_is_r3s`
- [tests/test_rofu_generator_switches.py](../../../../../tests/test_rofu_generator_switches.py) — direct import
- [tests/test_rofu_learning.py](../../../../../tests/test_rofu_learning.py) — direct import
- [tests/test_rofu_monotone.py](../../../../../tests/test_rofu_monotone.py) — direct import
  - `test_the_numeric_policy_reads_the_monotone_combiner_only_at_the_tag_with_its_switch`
- [tests/test_rofu_review_draw.py](../../../../../tests/test_rofu_review_draw.py) — direct import
  - `test_the_numeric_policy_draws_consistently_only_at_the_tag_with_its_switch`
- [tests/test_rofu_scope.py](../../../../../tests/test_rofu_scope.py) — direct import
  - `test_switched_off_or_below_the_tag_the_growth_is_a_change_point`
- [tests/test_rofu_speed.py](../../../../../tests/test_rofu_speed.py) — direct import
  - `test_the_numeric_policy_merges_only_at_the_tag_with_its_switch`
- [tests/test_rofu_successor.py](../../../../../tests/test_rofu_successor.py) — direct import
  - `test_the_successor_is_one_constant_after_ro6_and_the_latest`
- [tests/test_rofu_switch_key.py](../../../../../tests/test_rofu_switch_key.py) — direct import
  - `test_below_the_tag_the_key_names_no_switch`
- [tests/test_rofu_weeks.py](../../../../../tests/test_rofu_weeks.py) — direct import
  - `test_two_weeks_after_the_batch`
- [tests/test_rospeed2_connections.py](../../../../../tests/test_rospeed2_connections.py) — direct import
  - `test_inside_an_ad_operation_a_pooled_connection_carries_its_guard_and_nothing_after`
  - `test_the_pool_and_the_held_map_follow_their_switches`
- [tests/test_rospeed2_section_map.py](../../../../../tests/test_rospeed2_section_map.py) — direct import
- [tests/test_rospeed_ad_link.py](../../../../../tests/test_rospeed_ad_link.py) — direct import
  - `test_the_switch_reaches_every_rollout_from_the_config`
- [tests/test_route_rules_in_grader.py](../../../../../tests/test_route_rules_in_grader.py) — direct import
  - `test_the_route_rules_follow_the_route_check_and_value_of_information_stopping_follows_them`
- [tests/test_router_failure_records.py](../../../../../tests/test_router_failure_records.py) — direct import
- [tests/test_router_g1_feasibility.py](../../../../../tests/test_router_g1_feasibility.py) — direct import
  - `test_a_chooser_naming_an_infeasible_or_unknown_id_falls_back`
  - `test_a_reserved_assessment_surface_is_refused_on_today`
  - `test_a_seen_probe_is_served_by_dl1_and_refused_by_the_staged_frame`
  - `test_an_unseen_probe_stays_in_the_plan`
  - `test_the_staged_frame_keeps_refusals_through_the_projection`
- [tests/test_router_g4_restraint.py](../../../../../tests/test_router_g4_restraint.py) — direct import
  - `test_a_follow_up_joins_the_current_block_today_and_waits_with_a_decider_near_zero`
- [tests/test_router_offer_log.py](../../../../../tests/test_router_offer_log.py) — direct import
  - `test_placement_components_and_exclusions_are_in_the_candidate_set`
- [tests/test_router_r2a_landing.py](../../../../../tests/test_router_r2a_landing.py) — direct import
- [tests/test_router_r2a_serving.py](../../../../../tests/test_router_r2a_serving.py) — direct import
- [tests/test_router_r2b_serving.py](../../../../../tests/test_router_r2b_serving.py) — direct import
  - `test_staged_mode_at_the_successor_serves_r2a_exactly_and_asks_no_model`
  - `test_the_switches_at_the_successor_serve_their_predecessors_on_fixture_copies`
  - `test_with_no_model_set_up_the_rule_chooses_deterministically`
- [tests/test_router_r2bc_landing.py](../../../../../tests/test_router_r2bc_landing.py) — direct import
- [tests/test_router_r2c_teach_back.py](../../../../../tests/test_router_r2c_teach_back.py) — direct import
  - `test_summaries_run_only_where_the_mixture_serves`
- [tests/test_router_why_copy.py](../../../../../tests/test_router_why_copy.py) — direct import
  - `test_every_why_the_staged_chooser_writes_on_a_plan_is_plain`
- [tests/test_serve_eligibility_review.py](../../../../../tests/test_serve_eligibility_review.py) — direct import
  - `test_f4_the_successor_follows_regrade_contracts_and_keeps_every_predecessor`
- [tests/test_sg_slip_vs_gap.py](../../../../../tests/test_sg_slip_vs_gap.py) — direct import
- [tests/test_sg_successor.py](../../../../../tests/test_sg_successor.py) — direct import
  - `test_the_successor_is_one_constant_after_the_placement_hole_and_the_latest`
- [tests/test_sidecar_close_cancels_jobs.py](../../../../../tests/test_sidecar_close_cancels_jobs.py) — direct import
- [tests/test_source_first_needs.py](../../../../../tests/test_source_first_needs.py) — direct import
  - `test_below_the_tag_and_with_the_switch_off_nothing_runs`
- [tests/test_stuck_prompt_replay.py](../../../../../tests/test_stuck_prompt_replay.py) — direct import
  - `test_a_joint_stuck_reading_survives_rebuild_with_no_model_call`
  - `test_a_stuck_vault_rebuilds_to_a_fixed_point_with_no_model_call`
  - `test_historical_dont_know_rows_replay_unchanged_under_the_successor`
  - `test_the_kill_switch_never_changes_how_stuck_answers_replay`
- [tests/test_te3a_lesson_opportunity.py](../../../../../tests/test_te3a_lesson_opportunity.py) — direct import
- [tests/test_te3a_successor.py](../../../../../tests/test_te3a_successor.py) — direct import
  - `test_the_successor_is_one_constant_after_te2_and_the_latest`
- [tests/test_te3b_binding.py](../../../../../tests/test_te3b_binding.py) — direct import
- [tests/test_te3b_clock.py](../../../../../tests/test_te3b_clock.py) — direct import
- [tests/test_te3b_features.py](../../../../../tests/test_te3b_features.py) — direct import
- [tests/test_te3b_offers.py](../../../../../tests/test_te3b_offers.py) — direct import
- [tests/test_te3b_population.py](../../../../../tests/test_te3b_population.py) — direct import
- [tests/test_te3b_successor.py](../../../../../tests/test_te3b_successor.py) — direct import
  - `test_the_successor_is_one_constant_after_te3a_and_the_latest`
- [tests/test_te3b_value.py](../../../../../tests/test_te3b_value.py) — direct import
- [tests/test_teach_back.py](../../../../../tests/test_teach_back.py) — direct import
- [tests/test_teacher_exam_question_guard.py](../../../../../tests/test_teacher_exam_question_guard.py) — direct import
  - `test_a_logged_field_quoting_a_reserved_stem_is_withheld_by_location`
- [tests/test_teacher_te1_successor.py](../../../../../tests/test_teacher_te1_successor.py) — direct import
  - `test_the_tag_is_the_chains_last_link_after_curriculum_c1`
  - `test_with_the_switch_off_or_below_the_tag_practice_is_byte_identical`
- [tests/test_teacher_te1b_suggestions.py](../../../../../tests/test_teacher_te1b_suggestions.py) — direct import
  - `test_the_successor_is_the_latest_link_after_followups_nov2`
- [tests/test_teacher_te2_landing_r1.py](../../../../../tests/test_teacher_te2_landing_r1.py) — direct import
  - `test_an_ordinary_practice_regrade_already_carries_the_newer_calibration`
  - `test_fg1s_presentation_path_stamps_the_submissions_identity_and_its_regrade_the_replacements`
- [tests/test_teacher_te2_lessons.py](../../../../../tests/test_teacher_te2_lessons.py) — direct import
- [tests/test_teacher_te2_review_fixes.py](../../../../../tests/test_teacher_te2_review_fixes.py) — direct import
  - `test_f5_a_metered_typed_goal_resolver_is_sent_nothing`
- [tests/test_teacher_te2_sidecar.py](../../../../../tests/test_teacher_te2_sidecar.py) — direct import
  - `test_below_the_tag_the_goal_rpc_refuses_and_the_config_carries_no_te2_key`
- [tests/test_teacher_te2_successor.py](../../../../../tests/test_teacher_te2_successor.py) — direct import
  - `test_the_successor_is_one_constant_after_the_router_followups_and_the_latest`
- [tests/test_tier1_decider.py](../../../../../tests/test_tier1_decider.py) — direct import
  - `test_text_gap_kind_authority`
  - `test_text_gap_kind_is_reused_never_paid_for_twice`
  - `test_the_learner_text_gaps_decider_switch_still_keeps_learner_text_from_the_decider`
- [tests/test_upgrades.py](../../../../../tests/test_upgrades.py) — direct import
  - `test_a_jump_is_refused_and_nothing_changes`
  - `test_a_target_the_table_has_no_row_for_is_refused_before_any_step`
  - `test_each_activation_kind_commits_its_own_receipt_once`
  - `test_the_command_reaches_the_tag_by_name_and_the_latest_by_default`
  - `test_the_floor_reaches_each_tag_through_the_table`
  - `test_the_table_is_the_chain_from_the_floor_one_row_per_tag`
- [tests/test_ux_phase1_round2_rereview.py](../../../../../tests/test_ux_phase1_round2_rereview.py) — direct import
  - `test_f2_every_plan_version_serves_the_reading_step_behind_its_kill_switch`
- [tests/test_ux_phase4_landing.py](../../../../../tests/test_ux_phase4_landing.py) — direct import
  - `test_a_contest_regrade_records_provenance_and_re_resolves_the_forecast`
  - `test_a_contest_the_regrade_does_not_uphold_is_flagged_never_held`
- [tests/test_version_floor.py](../../../../../tests/test_version_floor.py) — direct import
  - `test_a_journal_from_the_floor_is_still_completed_by_an_opener`
  - `test_a_journal_naming_a_link_below_the_floor_is_refused`
  - `test_a_shadow_rebuild_cannot_be_forced_below_the_floor`
  - `test_a_vault_at_the_floor_or_the_head_opens`
  - `test_a_vault_whose_config_names_no_tag_is_refused`
  - `test_the_floor_is_a_tag_of_the_chain_and_the_chain_counts_up`
  - `test_the_upgrade_command_refuses_a_journal_from_below_the_floor_with_the_route`
- [tests/why_cases_helpers.py](../../../../../tests/why_cases_helpers.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains algorithm versions within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
