---
title: "learnloop.algorithm_versions"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/algorithm_versions.py"
source_paths:
  - "src/learnloop/algorithm_versions.py"
source_commit: "017c3ed22ddf583d5cddfe612d4e1ac32dc70950"
source_commit_timestamp: "2026-11-05T12:03:53-05:00"
source_worktree_state: "clean"
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
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.algorithm_versions` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: Dependency-neutral algorithm-version vocabulary.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py) |
| Source lines | 1082 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `017c3ed22ddf583d5cddfe612d4e1ac32dc70950` |
| Commit timestamp | `2026-11-05T12:03:53-05:00` |

## Public API

- `successors_from(version: str) -> frozenset[str]` ([source](../../../../../src/learnloop/algorithm_versions.py), line 851) — ``version`` and every later tag in :data:`SUCCESSOR_CHAIN`.

### Module constants

- `KM_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 12)
- `P0_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 18)
- `REVEAL_LEDGER_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 23)
- `DIAGNOSIS_SPLIT_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 40)
- `PLACEMENT_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 59)
- `RECURRENCE_GROUP_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 73)
- `STUCK_PROMPT_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 91)
- `DAILY_PLAN_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 105)
- `PROBE_TIE_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 119)
- `LEARNER_TEXT_GAP_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 137)
- `PROOF_ROUTE_CHECK_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 171)
- `SOURCE_REFERENCE_GATE_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 189)
- `SOURCE_FIRST_NEEDS_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 198)
- `ROUTE_RULES_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 220)
- `VOI_STOPPING_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 241)
- `DECIDER_TIER1_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 257)
- `ROUTER_STAGED_FRAME_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 277)
- `ROUTER_MIXTURE_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 298)
- `METHOD_EXPLICIT_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 321)
- `REGRADE_CONTRACT_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 345)
- `ELIGIBILITY_DECISION_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 368)
- `INTENT_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 387)
- `ADAPTIVE_DIFFICULTY_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 409)
- `WORKBENCH_FIELD_SIGNALS_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 431)
- `READING_PATH_PLAN_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 451)
- `CLAIM_FIXES_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 473)
- `REPLAY_LEDGER_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 492)
- `ONE_ASK_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 518)
- `SUPERSEDED_CLAIMS_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 542)
- `ATTEMPT_CONTENT_STATE_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 569)
- `COLD_RETRY_RESCHEDULE_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 591)
- `READER_FOLLOWUPS_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 609)
- `DELIVERABLE_PLAN_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 628)
- `TEACHER_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 657)
- `HELP_FOLD_ATTACH_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 677)
- `LESSON_SUGGESTIONS_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 702)
- `DATA_CAPTURE_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 721)
- `FOLLOWUP_SERVE_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 737)
- `INTERVAL_FACTOR_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 758)
- `ROUTER_OBJECTIVE_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 771)
- `ROUTER_CALIBRATION_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 785)
- `ROUTER_LEARNED_TAIL_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 798)
- `SUCCESSOR_CHAIN` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 807)
- `DIAGNOSIS_SPLIT_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 862)
- `RECURRENCE_GROUP_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 867)
- `STUCK_PROMPT_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 873)
- `P0_SUCCESSOR_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 878)
- `P0_PROJECTION_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 879)
- `CANONICAL_STATE_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 886)
- `PLACEMENT_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 893)
- `DAILY_PLAN_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 898)
- `PROBE_TIE_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 903)
- `LEARNER_TEXT_GAP_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 909)
- `SOURCE_REFERENCE_GATE_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 913)
- `SOURCE_FIRST_NEEDS_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 917)
- `ROUTE_RULES_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 924)
- `VOI_STOPPING_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 931)
- `DECIDER_TIER1_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 935)
- `ROUTER_STAGED_FRAME_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 940)
- `ROUTER_MIXTURE_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 946)
- `METHOD_EXPLICIT_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 952)
- `REGRADE_CONTRACT_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 958)
- `ELIGIBILITY_DECISION_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 964)
- `INTENT_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 969)
- `ADAPTIVE_DIFFICULTY_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 975)
- `WORKBENCH_FIELD_SIGNALS_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 981)
- `READING_PATH_PLAN_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 986)
- `CLAIM_FIXES_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 992)
- `REPLAY_LEDGER_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 997)
- `ONE_ASK_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1003)
- `SUPERSEDED_CLAIMS_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1008)
- `ATTEMPT_CONTENT_STATE_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1014)
- `COLD_RETRY_RESCHEDULE_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1019)
- `READER_FOLLOWUPS_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1024)
- `DELIVERABLE_PLAN_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1028)
- `TEACHER_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1031)
- `HELP_FOLD_ATTACH_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1036)
- `LESSON_SUGGESTIONS_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1041)
- `DATA_CAPTURE_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1047)
- `FOLLOWUP_SERVE_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1052)
- `INTERVAL_FACTOR_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1059)
- `ROUTER_OBJECTIVE_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1065)
- `ROUTER_CALIBRATION_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1071)
- `ROUTER_LEARNED_TAIL_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1077)
- `LATEST_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 1082)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ad_successor_upgrade|learnloop.ad_successor_upgrade]] — imports `ADAPTIVE_DIFFICULTY_ALGORITHM_VERSION`, `INTENT_ALGORITHM_VERSION`, `SUCCESSOR_CHAIN`
- [[Reference/Modules/learnloop/adaptive_difficulty/successor|learnloop.adaptive_difficulty.successor]] — imports `ADAPTIVE_DIFFICULTY_ALGORITHM_VERSION`, `ADAPTIVE_DIFFICULTY_VERSIONS`
- [[Reference/Modules/learnloop/attempt_content_state_upgrade|learnloop.attempt_content_state_upgrade]] — imports `ATTEMPT_CONTENT_STATE_ALGORITHM_VERSION`, `SUCCESSOR_CHAIN`, `SUPERSEDED_CLAIMS_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `ATTEMPT_CONTENT_STATE_VERSIONS`, `P0_PROJECTION_VERSIONS`, `REGRADE_CONTRACT_VERSIONS`, `REPLAY_LEDGER_VERSIONS`, `SOURCE_REFERENCE_GATE_VERSIONS`
- [[Reference/Modules/learnloop/attempts/blind_grading|learnloop.attempts.blind_grading]] — imports `DIAGNOSIS_SPLIT_VERSIONS`
- [[Reference/Modules/learnloop/attempts/grade_resolution|learnloop.attempts.grade_resolution]] — imports `REGRADE_CONTRACT_VERSIONS`, `SOURCE_REFERENCE_GATE_VERSIONS`
- [[Reference/Modules/learnloop/attempts/grading_support|learnloop.attempts.grading_support]] — imports `METHOD_EXPLICIT_VERSIONS`, `ROUTE_RULES_VERSIONS`
- [[Reference/Modules/learnloop/attempts/hint_fold|learnloop.attempts.hint_fold]] — imports `HELP_FOLD_ATTACH_VERSIONS`
- [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]] — imports `REGRADE_CONTRACT_VERSIONS`, `SOURCE_REFERENCE_GATE_VERSIONS`
- [[Reference/Modules/learnloop/attempts/stuck|learnloop.attempts.stuck]] — imports `STUCK_PROMPT_VERSIONS`
- [[Reference/Modules/learnloop/claim_fixes_upgrade|learnloop.claim_fixes_upgrade]] — imports `CLAIM_FIXES_ALGORITHM_VERSION`, `READING_PATH_PLAN_ALGORITHM_VERSION`, `SUCCESSOR_CHAIN`
- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `ATTEMPT_CONTENT_STATE_ALGORITHM_VERSION`, `CLAIM_FIXES_ALGORITHM_VERSION`, `COLD_RETRY_RESCHEDULE_ALGORITHM_VERSION`, `DATA_CAPTURE_ALGORITHM_VERSION`, `DELIVERABLE_PLAN_ALGORITHM_VERSION`, `FOLLOWUP_SERVE_ALGORITHM_VERSION`, `HELP_FOLD_ATTACH_ALGORITHM_VERSION`, `INTERVAL_FACTOR_ALGORITHM_VERSION`, `LATEST_ALGORITHM_VERSION`, `LESSON_SUGGESTIONS_ALGORITHM_VERSION`, `ONE_ASK_ALGORITHM_VERSION`, `READER_FOLLOWUPS_ALGORITHM_VERSION`, `READING_PATH_PLAN_ALGORITHM_VERSION`, `REPLAY_LEDGER_ALGORITHM_VERSION`, `ROUTER_CALIBRATION_ALGORITHM_VERSION`, `ROUTER_LEARNED_TAIL_ALGORITHM_VERSION`, `ROUTER_OBJECTIVE_ALGORITHM_VERSION`, `SUPERSEDED_CLAIMS_ALGORITHM_VERSION`, `TEACHER_ALGORITHM_VERSION`, `WORKBENCH_FIELD_SIGNALS_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/cold_retry_reschedule_upgrade|learnloop.cold_retry_reschedule_upgrade]] — imports `ATTEMPT_CONTENT_STATE_ALGORITHM_VERSION`, `COLD_RETRY_RESCHEDULE_ALGORITHM_VERSION`, `SUCCESSOR_CHAIN`
- [[Reference/Modules/learnloop/config/template|learnloop.config.template]] — imports `LATEST_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `DAILY_PLAN_VERSIONS`, `DELIVERABLE_PLAN_VERSIONS`, `READING_PATH_PLAN_VERSIONS`
- [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]] — imports `LESSON_SUGGESTIONS_VERSIONS`, `ROUTER_MIXTURE_VERSIONS`, `TEACHER_VERSIONS`
- [[Reference/Modules/learnloop/daily_plan/policy|learnloop.daily_plan.policy]] — imports `ROUTER_MIXTURE_VERSIONS`, `ROUTER_STAGED_FRAME_VERSIONS`
- [[Reference/Modules/learnloop/daily_plan_upgrade|learnloop.daily_plan_upgrade]] — imports `DAILY_PLAN_ALGORITHM_VERSION`, `DIAGNOSIS_SPLIT_ALGORITHM_VERSION`, `PLACEMENT_ALGORITHM_VERSION`, `RECURRENCE_GROUP_ALGORITHM_VERSION`, `REVEAL_LEDGER_ALGORITHM_VERSION`, `STUCK_PROMPT_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/data_capture/gates|learnloop.data_capture.gates]] — imports `DATA_CAPTURE_VERSIONS`
- [[Reference/Modules/learnloop/data_capture_upgrade|learnloop.data_capture_upgrade]] — imports `DATA_CAPTURE_ALGORITHM_VERSION`, `LESSON_SUGGESTIONS_ALGORITHM_VERSION`, `SUCCESSOR_CHAIN`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `CANONICAL_STATE_VERSIONS`
- [[Reference/Modules/learnloop/decider_judgments|learnloop.decider_judgments]] — imports `DECIDER_TIER1_VERSIONS`
- [[Reference/Modules/learnloop/decider_upgrade|learnloop.decider_upgrade]] — imports `DECIDER_TIER1_ALGORITHM_VERSION`, `SUCCESSOR_CHAIN`, `VOI_STOPPING_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/deliverable_plan_upgrade|learnloop.deliverable_plan_upgrade]] — imports `DELIVERABLE_PLAN_ALGORITHM_VERSION`, `READER_FOLLOWUPS_ALGORITHM_VERSION`, `SUCCESSOR_CHAIN`
- [[Reference/Modules/learnloop/diagnosis/recurrence/live|learnloop.diagnosis.recurrence.live]] — imports `RECURRENCE_GROUP_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/diagnosis/recurrence/report|learnloop.diagnosis.recurrence.report]] — imports `RECURRENCE_GROUP_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/diagnosis/recurrence/upgrade|learnloop.diagnosis.recurrence.upgrade]] — imports `DIAGNOSIS_SPLIT_ALGORITHM_VERSION`, `PLACEMENT_ALGORITHM_VERSION`, `RECURRENCE_GROUP_ALGORITHM_VERSION`, `REVEAL_LEDGER_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `COLD_RETRY_RESCHEDULE_VERSIONS`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/actions|learnloop.diagnosis.text_gaps.actions]] — imports `LEARNER_TEXT_GAP_VERSIONS`
- [[Reference/Modules/learnloop/diagnosis/voi_stopping|learnloop.diagnosis.voi_stopping]] — imports `VOI_STOPPING_VERSIONS`
- [[Reference/Modules/learnloop/eligibility_decision_upgrade|learnloop.eligibility_decision_upgrade]] — imports `ELIGIBILITY_DECISION_ALGORITHM_VERSION`, `REGRADE_CONTRACT_ALGORITHM_VERSION`, `SUCCESSOR_CHAIN`
- [[Reference/Modules/learnloop/field/outcomes|learnloop.field.outcomes]] — imports `P0_ALGORITHM_VERSION`, `P0_SUCCESSOR_VERSIONS`
- [[Reference/Modules/learnloop/field/signals|learnloop.field.signals]] — imports `LEARNER_TEXT_GAP_VERSIONS`
- [[Reference/Modules/learnloop/field/workbench_signals|learnloop.field.workbench_signals]] — imports `WORKBENCH_FIELD_SIGNALS_VERSIONS`
- [[Reference/Modules/learnloop/followup_serve/gates|learnloop.followup_serve.gates]] — imports `FOLLOWUP_SERVE_VERSIONS`
- [[Reference/Modules/learnloop/followup_serve_upgrade|learnloop.followup_serve_upgrade]] — imports `DATA_CAPTURE_ALGORITHM_VERSION`, `FOLLOWUP_SERVE_ALGORITHM_VERSION`, `SUCCESSOR_CHAIN`
- [[Reference/Modules/learnloop/goals/certification_cold_probe|learnloop.goals.certification_cold_probe]] — imports `SOURCE_REFERENCE_GATE_VERSIONS`
- [[Reference/Modules/learnloop/goals/exam_pool|learnloop.goals.exam_pool]] — imports `SOURCE_REFERENCE_GATE_VERSIONS`
- [[Reference/Modules/learnloop/help_fold_attach_upgrade|learnloop.help_fold_attach_upgrade]] — imports `HELP_FOLD_ATTACH_ALGORITHM_VERSION`, `SUCCESSOR_CHAIN`, `TEACHER_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/instructional/needs|learnloop.instructional.needs]] — imports `SOURCE_FIRST_NEEDS_VERSIONS`
- [[Reference/Modules/learnloop/instructional/reader_digest|learnloop.instructional.reader_digest]] — imports `READER_FOLLOWUPS_VERSIONS`
- [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]] — imports `READER_FOLLOWUPS_VERSIONS`
- [[Reference/Modules/learnloop/intent_upgrade|learnloop.intent_upgrade]] — imports `ELIGIBILITY_DECISION_ALGORITHM_VERSION`, `INTENT_ALGORITHM_VERSION`, `SUCCESSOR_CHAIN`
- [[Reference/Modules/learnloop/interval_factor_upgrade|learnloop.interval_factor_upgrade]] — imports `FOLLOWUP_SERVE_ALGORITHM_VERSION`, `INTERVAL_FACTOR_ALGORITHM_VERSION`, `SUCCESSOR_CHAIN`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `CANONICAL_STATE_VERSIONS`, `KM_ALGORITHM_VERSION`, `P0_ALGORITHM_VERSION`, `P0_PROJECTION_VERSIONS`, `P0_SUCCESSOR_VERSIONS`, `REVEAL_LEDGER_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/learner/facet_evidence_timeline|learnloop.learner.facet_evidence_timeline]] — imports `REGRADE_CONTRACT_VERSIONS`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `CLAIM_FIXES_VERSIONS`, `SUPERSEDED_CLAIMS_VERSIONS`
- [[Reference/Modules/learnloop/learner_text_gap_upgrade|learnloop.learner_text_gap_upgrade]] — imports `DAILY_PLAN_ALGORITHM_VERSION`, `DIAGNOSIS_SPLIT_ALGORITHM_VERSION`, `LEARNER_TEXT_GAP_ALGORITHM_VERSION`, `PLACEMENT_ALGORITHM_VERSION`, `PROBE_TIE_ALGORITHM_VERSION`, `RECURRENCE_GROUP_ALGORITHM_VERSION`, `REVEAL_LEDGER_ALGORITHM_VERSION`, `STUCK_PROMPT_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/lesson_suggestions_upgrade|learnloop.lesson_suggestions_upgrade]] — imports `HELP_FOLD_ATTACH_ALGORITHM_VERSION`, `LESSON_SUGGESTIONS_ALGORITHM_VERSION`, `SUCCESSOR_CHAIN`
- [[Reference/Modules/learnloop/method_explicit_upgrade|learnloop.method_explicit_upgrade]] — imports `METHOD_EXPLICIT_ALGORITHM_VERSION`, `ROUTER_MIXTURE_ALGORITHM_VERSION`, `SUCCESSOR_CHAIN`
- [[Reference/Modules/learnloop/one_ask_upgrade|learnloop.one_ask_upgrade]] — imports `ONE_ASK_ALGORITHM_VERSION`, `REPLAY_LEDGER_ALGORITHM_VERSION`, `SUCCESSOR_CHAIN`
- [[Reference/Modules/learnloop/ops/vault_upgrade|learnloop.ops.vault_upgrade]] — imports `DIAGNOSIS_SPLIT_ALGORITHM_VERSION`, `PLACEMENT_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/placement/report|learnloop.placement.report]] — imports `PLACEMENT_VERSIONS`
- [[Reference/Modules/learnloop/placement/state|learnloop.placement.state]] — imports `DIAGNOSIS_SPLIT_VERSIONS`, `LEARNER_TEXT_GAP_VERSIONS`, `PLACEMENT_VERSIONS`
- [[Reference/Modules/learnloop/probe_tie_upgrade|learnloop.probe_tie_upgrade]] — imports `DAILY_PLAN_ALGORITHM_VERSION`, `DIAGNOSIS_SPLIT_ALGORITHM_VERSION`, `PLACEMENT_ALGORITHM_VERSION`, `PROBE_TIE_ALGORITHM_VERSION`, `RECURRENCE_GROUP_ALGORITHM_VERSION`, `REVEAL_LEDGER_ALGORITHM_VERSION`, `STUCK_PROMPT_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/proof_check_upgrade|learnloop.proof_check_upgrade]] — imports `DAILY_PLAN_ALGORITHM_VERSION`, `DIAGNOSIS_SPLIT_ALGORITHM_VERSION`, `LEARNER_TEXT_GAP_ALGORITHM_VERSION`, `PLACEMENT_ALGORITHM_VERSION`, `PROBE_TIE_ALGORITHM_VERSION`, `PROOF_ROUTE_CHECK_ALGORITHM_VERSION`, `RECURRENCE_GROUP_ALGORITHM_VERSION`, `REVEAL_LEDGER_ALGORITHM_VERSION`, `STUCK_PROMPT_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/reader_followups_upgrade|learnloop.reader_followups_upgrade]] — imports `COLD_RETRY_RESCHEDULE_ALGORITHM_VERSION`, `READER_FOLLOWUPS_ALGORITHM_VERSION`, `SUCCESSOR_CHAIN`
- [[Reference/Modules/learnloop/reading_path_plan_upgrade|learnloop.reading_path_plan_upgrade]] — imports `READING_PATH_PLAN_ALGORITHM_VERSION`, `SUCCESSOR_CHAIN`, `WORKBENCH_FIELD_SIGNALS_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/regrade_contract_upgrade|learnloop.regrade_contract_upgrade]] — imports `METHOD_EXPLICIT_ALGORITHM_VERSION`, `REGRADE_CONTRACT_ALGORITHM_VERSION`, `SUCCESSOR_CHAIN`
- [[Reference/Modules/learnloop/replay_ledger_upgrade|learnloop.replay_ledger_upgrade]] — imports `CLAIM_FIXES_ALGORITHM_VERSION`, `REPLAY_LEDGER_ALGORITHM_VERSION`, `SUCCESSOR_CHAIN`
- [[Reference/Modules/learnloop/route_rules_upgrade|learnloop.route_rules_upgrade]] — imports `ROUTE_RULES_ALGORITHM_VERSION`, `SOURCE_FIRST_NEEDS_ALGORITHM_VERSION`, `SUCCESSOR_CHAIN`
- [[Reference/Modules/learnloop/router_calibration_upgrade|learnloop.router_calibration_upgrade]] — imports `ROUTER_CALIBRATION_ALGORITHM_VERSION`, `ROUTER_OBJECTIVE_ALGORITHM_VERSION`, `SUCCESSOR_CHAIN`
- [[Reference/Modules/learnloop/router_learned_tail_upgrade|learnloop.router_learned_tail_upgrade]] — imports `ROUTER_CALIBRATION_ALGORITHM_VERSION`, `ROUTER_LEARNED_TAIL_ALGORITHM_VERSION`, `SUCCESSOR_CHAIN`
- [[Reference/Modules/learnloop/router_mixture_upgrade|learnloop.router_mixture_upgrade]] — imports `ROUTER_MIXTURE_ALGORITHM_VERSION`, `ROUTER_STAGED_FRAME_ALGORITHM_VERSION`, `SUCCESSOR_CHAIN`
- [[Reference/Modules/learnloop/router_objective_switches|learnloop.router_objective_switches]] — imports `INTERVAL_FACTOR_VERSIONS`, `ROUTER_CALIBRATION_VERSIONS`, `ROUTER_LEARNED_TAIL_VERSIONS`, `ROUTER_OBJECTIVE_VERSIONS`
- [[Reference/Modules/learnloop/router_objective_upgrade|learnloop.router_objective_upgrade]] — imports `INTERVAL_FACTOR_ALGORITHM_VERSION`, `ROUTER_OBJECTIVE_ALGORITHM_VERSION`, `SUCCESSOR_CHAIN`
- [[Reference/Modules/learnloop/router_staged_upgrade|learnloop.router_staged_upgrade]] — imports `DECIDER_TIER1_ALGORITHM_VERSION`, `ROUTER_STAGED_FRAME_ALGORITHM_VERSION`, `SUCCESSOR_CHAIN`
- [[Reference/Modules/learnloop/scheduling/intent/serving|learnloop.scheduling.intent.serving]] — imports `INTENT_VERSIONS`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `PROBE_TIE_VERSIONS`
- [[Reference/Modules/learnloop/serve_eligibility|learnloop.serve_eligibility]] — imports `ELIGIBILITY_DECISION_VERSIONS`, `ONE_ASK_VERSIONS`
- [[Reference/Modules/learnloop/sources_upgrade|learnloop.sources_upgrade]] — imports `PROOF_ROUTE_CHECK_ALGORITHM_VERSION`, `SOURCE_FIRST_NEEDS_ALGORITHM_VERSION`, `SOURCE_REFERENCE_GATE_ALGORITHM_VERSION`, `SUCCESSOR_CHAIN`
- [[Reference/Modules/learnloop/stuck_prompt_upgrade|learnloop.stuck_prompt_upgrade]] — imports `DIAGNOSIS_SPLIT_ALGORITHM_VERSION`, `PLACEMENT_ALGORITHM_VERSION`, `RECURRENCE_GROUP_ALGORITHM_VERSION`, `REVEAL_LEDGER_ALGORITHM_VERSION`, `STUCK_PROMPT_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `REGRADE_CONTRACT_VERSIONS`
- [[Reference/Modules/learnloop/substrate/recurrence_groups|learnloop.substrate.recurrence_groups]] — imports `DECIDER_TIER1_VERSIONS`, `RECURRENCE_GROUP_VERSIONS`
- [[Reference/Modules/learnloop/superseded_claims_upgrade|learnloop.superseded_claims_upgrade]] — imports `ONE_ASK_ALGORITHM_VERSION`, `SUCCESSOR_CHAIN`, `SUPERSEDED_CLAIMS_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `TEACHER_VERSIONS`
- [[Reference/Modules/learnloop/teacher_upgrade|learnloop.teacher_upgrade]] — imports `DELIVERABLE_PLAN_ALGORITHM_VERSION`, `SUCCESSOR_CHAIN`, `TEACHER_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/voi_stopping_upgrade|learnloop.voi_stopping_upgrade]] — imports `ROUTE_RULES_ALGORITHM_VERSION`, `SUCCESSOR_CHAIN`, `VOI_STOPPING_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/workbench_field_signals_upgrade|learnloop.workbench_field_signals_upgrade]] — imports `ADAPTIVE_DIFFICULTY_ALGORITHM_VERSION`, `SUCCESSOR_CHAIN`, `WORKBENCH_FIELD_SIGNALS_ALGORITHM_VERSION`

### Repository tooling consumers

- [scripts/voi_cap_report.py](../../../../../scripts/voi_cap_report.py)

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

Static participation evidence comes from [[Reference/Modules/learnloop/ad_successor_upgrade|learnloop.ad_successor_upgrade]], [[Reference/Modules/learnloop/adaptive_difficulty/successor|learnloop.adaptive_difficulty.successor]], [[Reference/Modules/learnloop/attempt_content_state_upgrade|learnloop.attempt_content_state_upgrade]], [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/blind_grading|learnloop.attempts.blind_grading]] and 74 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/followup_serve_helpers.py](../../../../../tests/followup_serve_helpers.py) — direct import
- [tests/intent_fakes.py](../../../../../tests/intent_fakes.py) — direct import
- [tests/router_mixture_helpers.py](../../../../../tests/router_mixture_helpers.py) — direct import
- [tests/teacher_fakes.py](../../../../../tests/teacher_fakes.py) — direct import
- [tests/test_ad23_successor.py](../../../../../tests/test_ad23_successor.py) — direct import
  - `test_the_successor_is_the_next_link_with_its_defaults_snapshot`
- [tests/test_ad_denial_log.py](../../../../../tests/test_ad_denial_log.py) — direct import
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
  - `test_a_bare_upgrade_targets_the_latest_through_mvp037`
  - `test_an_mvp035_journal_is_handed_down_the_chain_then_the_tag_activates`
  - `test_mvp037_is_one_constant_after_mvp036`
- [tests/test_batch3_landing.py](../../../../../tests/test_batch3_landing.py) — direct import
  - `test_a_bare_upgrade_targets_the_latest_through_mvp035`
  - `test_mvp035_is_one_constant_after_mvp034_and_the_latest`
- [tests/test_canonical_projection_fold_skip.py](../../../../../tests/test_canonical_projection_fold_skip.py) — direct import
- [tests/test_cold_retry_reschedule.py](../../../../../tests/test_cold_retry_reschedule.py) — direct import
  - `test_a_bare_upgrade_targets_the_latest_through_mvp038_and_mvp038_refuses_twice`
  - `test_an_interrupted_mvp037_activation_then_upgrade_to_mvp038_completes_it`
  - `test_mvp038_is_one_constant_after_mvp037`
  - `test_without_a_completion_an_attach_refuses_and_the_upgrade_still_completes_the_mvp037_journal`
- [tests/test_config_refactor.py](../../../../../tests/test_config_refactor.py) — direct import
  - `test_a_successor_merge_appends_one_tag_and_every_gate_follows`
  - `test_new_vaults_start_at_the_latest_algorithm_version`
  - `test_the_defaults_snapshot_covers_the_successor_chain`
- [tests/test_curriculum_c0b_landing.py](../../../../../tests/test_curriculum_c0b_landing.py) — direct import
- [tests/test_curriculum_c1_landing.py](../../../../../tests/test_curriculum_c1_landing.py) — direct import
  - `test_the_chain_is_rw6b_then_c1`
- [tests/test_curriculum_c1_plan_follows_path.py](../../../../../tests/test_curriculum_c1_plan_follows_path.py) — direct import
  - `test_the_successor_is_one_constant_after_rw6bs_followups`
- [tests/test_data_capture_a1_prefilter.py](../../../../../tests/test_data_capture_a1_prefilter.py) — direct import
- [tests/test_data_capture_a2_measurement.py](../../../../../tests/test_data_capture_a2_measurement.py) — direct import
- [tests/test_data_capture_a5_not_ready_floor.py](../../../../../tests/test_data_capture_a5_not_ready_floor.py) — direct import
- [tests/test_data_capture_a6_delayed_pick.py](../../../../../tests/test_data_capture_a6_delayed_pick.py) — direct import
- [tests/test_data_capture_successor.py](../../../../../tests/test_data_capture_successor.py) — direct import
  - `test_the_successor_is_one_constant_after_te1b_and_the_latest`
- [tests/test_diagnosis_input_provenance.py](../../../../../tests/test_diagnosis_input_provenance.py) — direct import
  - `test_f5_every_defaults_snapshot_records_the_switch_off`
- [tests/test_evsi_staged_binding.py](../../../../../tests/test_evsi_staged_binding.py) — direct import
- [tests/test_exam_protection_review.py](../../../../../tests/test_exam_protection_review.py) — direct import
  - `test_replay_never_reads_the_switch`
- [tests/test_facet_state_write_on_change.py](../../../../../tests/test_facet_state_write_on_change.py) — direct import
- [tests/test_field_workbench_signals.py](../../../../../tests/test_field_workbench_signals.py) — direct import
  - `test_the_successor_vocabulary_is_one_constant_after_its_predecessor`
- [tests/test_followup_fg1d_probe_shadow.py](../../../../../tests/test_followup_fg1d_probe_shadow.py) — direct import
- [tests/test_followup_successor.py](../../../../../tests/test_followup_successor.py) — direct import
  - `test_the_successor_is_one_constant_after_data_capture`
- [tests/test_followups_batch5_recap_dependencies.py](../../../../../tests/test_followups_batch5_recap_dependencies.py) — direct import
- [tests/test_followups_nov2_help_fold.py](../../../../../tests/test_followups_nov2_help_fold.py) — direct import
- [tests/test_forecast_receipts.py](../../../../../tests/test_forecast_receipts.py) — direct import
  - `test_a_regrade_re_resolves_the_forecast`
- [tests/test_forecast_receipts_landing.py](../../../../../tests/test_forecast_receipts_landing.py) — direct import
  - `test_the_resolver_reads_the_regraded_events_the_lineage_names_never_a_retired_one`
- [tests/test_help_fold_attach_successor.py](../../../../../tests/test_help_fold_attach_successor.py) — direct import
  - `test_mvp042_is_one_constant_after_mvp041_and_the_latest`
- [tests/test_intent_codex_rereview.py](../../../../../tests/test_intent_codex_rereview.py) — direct import
  - `test_f2_the_chain_ends_at_the_intent_successor`
  - `test_f2_the_upgrade_takes_the_predecessor_or_the_chain_and_refuses_the_rest`
- [tests/test_intent_codex_review.py](../../../../../tests/test_intent_codex_review.py) — direct import
- [tests/test_intent_fix_round4.py](../../../../../tests/test_intent_fix_round4.py) — direct import
  - `test_f15_the_probe_contract_carries_the_diagnostic_variant`
- [tests/test_intent_fix_round5.py](../../../../../tests/test_intent_fix_round5.py) — direct import
- [tests/test_intent_fix_round6.py](../../../../../tests/test_intent_fix_round6.py) — direct import
- [tests/test_intent_fix_round7.py](../../../../../tests/test_intent_fix_round7.py) — direct import
- [tests/test_intent_plan.py](../../../../../tests/test_intent_plan.py) — direct import
- [tests/test_km2b_consumer_rekey.py](../../../../../tests/test_km2b_consumer_rekey.py) — direct import
  - `test_every_canonical_version_refuses_legacy_facet_state_write`
- [tests/test_learner_report_superseded.py](../../../../../tests/test_learner_report_superseded.py) — direct import
  - `test_a_bare_upgrade_targets_the_latest_through_mvp036`
  - `test_the_tag_is_one_constant_after_mvp035_and_the_latest`
- [tests/test_lp_claim_fixes.py](../../../../../tests/test_lp_claim_fixes.py) — direct import
  - `test_the_successor_is_one_constant_after_its_predecessor`
- [tests/test_lp_claim_fixes_rereview.py](../../../../../tests/test_lp_claim_fixes_rereview.py) — direct import
- [tests/test_lp_claim_fixes_review.py](../../../../../tests/test_lp_claim_fixes_review.py) — direct import
- [tests/test_method_explicit_upgrade.py](../../../../../tests/test_method_explicit_upgrade.py) — direct import
  - `test_defaults_fingerprint_is_recorded_for_the_successor`
  - `test_new_vaults_start_at_the_successor`
  - `test_the_successor_is_the_latest_and_keeps_every_predecessor`
  - `test_upgrade_command_defaults_to_the_successor`
- [tests/test_model_grade_lane.py](../../../../../tests/test_model_grade_lane.py) — direct import
  - `test_rebuild_moves_only_learning_objects_with_model_graded_attempts`
- [tests/test_mvp010_upgrade.py](../../../../../tests/test_mvp010_upgrade.py) — direct import
  - `test_split_version_is_a_p0_successor`
- [tests/test_mvp011_upgrade.py](../../../../../tests/test_mvp011_upgrade.py) — direct import
  - `test_existing_vaults_keep_their_version_until_the_owner_upgrades`
  - `test_new_vaults_start_at_the_latest_version`
  - `test_placement_successor_keeps_the_split_and_the_p0_projection_namespace`
- [tests/test_mvp013_upgrade.py](../../../../../tests/test_mvp013_upgrade.py) — direct import
  - `test_defaults_fingerprint_is_recorded_for_the_successor`
  - `test_stuck_version_is_a_successor_and_keeps_every_predecessor`
- [tests/test_mvp014_upgrade.py](../../../../../tests/test_mvp014_upgrade.py) — direct import
  - `test_defaults_fingerprint_is_recorded_for_the_plan_successor`
  - `test_new_vaults_serve_the_plan`
  - `test_the_plan_successor_keeps_every_predecessor`
- [tests/test_mvp015_upgrade.py](../../../../../tests/test_mvp015_upgrade.py) — direct import
  - `test_defaults_fingerprint_is_recorded_for_the_probe_tie_successor`
  - `test_new_vaults_start_at_a_successor_that_admits_probe_ties`
  - `test_probe_tie_successor_keeps_every_predecessor`
  - `test_upgrade_command_defaults_to_the_latest`
- [tests/test_mvp016_upgrade.py](../../../../../tests/test_mvp016_upgrade.py) — direct import
  - `test_defaults_fingerprint_is_recorded_for_the_learner_text_gap_successor`
  - `test_learner_text_gap_successor_keeps_every_predecessor`
  - `test_new_vaults_start_at_a_successor_with_sooner_checks`
  - `test_upgrade_command_defaults_to_the_latest`
- [tests/test_mvp017_upgrade.py](../../../../../tests/test_mvp017_upgrade.py) — direct import
  - `test_the_route_check_successor_keeps_every_predecessor`
- [tests/test_mvp018_upgrade.py](../../../../../tests/test_mvp018_upgrade.py) — direct import
  - `test_defaults_fingerprints_are_recorded_for_every_successor`
  - `test_the_sources_successors_follow_the_route_check_and_keep_every_predecessor`
- [tests/test_mvp020_upgrade.py](../../../../../tests/test_mvp020_upgrade.py) — direct import
  - `test_defaults_fingerprint_is_recorded_for_the_route_rules_successor`
  - `test_new_vaults_start_at_a_successor_with_the_route_rules`
  - `test_the_route_rules_successor_keeps_every_predecessor`
  - `test_upgrade_command_defaults_to_the_latest`
- [tests/test_mvp021_upgrade.py](../../../../../tests/test_mvp021_upgrade.py) — direct import
  - `test_defaults_fingerprint_is_recorded_for_every_successor`
  - `test_new_vaults_start_at_a_successor_with_voi_stopping`
  - `test_upgrade_command_defaults_to_the_latest`
  - `test_voi_successor_keeps_every_predecessor`
- [tests/test_mvp022_upgrade.py](../../../../../tests/test_mvp022_upgrade.py) — direct import
  - `test_defaults_fingerprints_are_recorded_for_every_successor`
  - `test_new_vaults_start_at_a_successor_with_the_deciders_judgments`
  - `test_the_decider_successor_follows_voi_stopping_and_keeps_every_predecessor`
  - `test_upgrade_command_defaults_to_the_latest`
- [tests/test_mvp023_upgrade.py](../../../../../tests/test_mvp023_upgrade.py) — direct import
  - `test_defaults_fingerprints_are_recorded_for_every_successor`
  - `test_new_vaults_start_at_the_router_successor`
  - `test_the_router_successor_follows_the_decider_and_keeps_every_predecessor`
  - `test_upgrade_command_defaults_to_the_latest`
- [tests/test_mvp024_upgrade.py](../../../../../tests/test_mvp024_upgrade.py) — direct import
  - `test_defaults_fingerprints_are_recorded_for_every_successor`
  - `test_new_vaults_start_at_the_mixture_successor`
  - `test_the_mixture_successor_follows_the_staged_frame_and_keeps_every_predecessor`
  - `test_upgrade_command_defaults_to_the_latest`
- [tests/test_pfc_unverified_unassessed.py](../../../../../tests/test_pfc_unverified_unassessed.py) — direct import
- [tests/test_plan_determinism.py](../../../../../tests/test_plan_determinism.py) — direct import
  - `test_every_defaults_snapshot_records_the_switch_on`
  - `test_replay_never_reads_the_switch`
  - `test_the_switch_acts_only_where_the_router_composes_today`
- [tests/test_plan_determinism_landing.py](../../../../../tests/test_plan_determinism_landing.py) — direct import
- [tests/test_plan_follows_path.py](../../../../../tests/test_plan_follows_path.py) — direct import
  - `test_the_successor_is_one_constant_after_rw2d`
- [tests/test_pr4_superseded_claims_landing.py](../../../../../tests/test_pr4_superseded_claims_landing.py) — direct import
  - `test_landing_i_a_too_easy_retirement_during_a_session`
  - `test_landing_i_control_below_the_tag_the_same_session_reopens_the_retired_row`
  - `test_landing_iii_a_refused_chained_upgrade_to_mvp037_leaves_the_log_in_place`
  - `test_landing_iii_upgrade_to_mvp037_archives_the_denial_log_exactly_once`
- [tests/test_rbeq_pr2_landing.py](../../../../../tests/test_rbeq_pr2_landing.py) — direct import
- [tests/test_reader_ca2_codex_rereview.py](../../../../../tests/test_reader_ca2_codex_rereview.py) — direct import
- [tests/test_reader_ca2_codex_review.py](../../../../../tests/test_reader_ca2_codex_review.py) — direct import
- [tests/test_reader_ca2_one_ask.py](../../../../../tests/test_reader_ca2_one_ask.py) — direct import
  - `test_the_successor_is_one_constant_after_rebuild_equivalence`
- [tests/test_reader_digest_narrative.py](../../../../../tests/test_reader_digest_narrative.py) — direct import
  - `test_below_the_follow_ups_successor_the_summary_row_says_so`
- [tests/test_reader_followups.py](../../../../../tests/test_reader_followups.py) — direct import
- [tests/test_reader_followups_successor.py](../../../../../tests/test_reader_followups_successor.py) — direct import
  - `test_a_bare_upgrade_targets_the_latest_through_mvp039_and_mvp039_refuses_twice`
  - `test_mvp039_is_one_constant_after_mvp038_and_the_latest`
- [tests/test_reader_guidance.py](../../../../../tests/test_reader_guidance.py) — direct import
  - `test_split_guide_reason_names_the_diagnosers_statement`
- [tests/test_reader_recap_review_r2.py](../../../../../tests/test_reader_recap_review_r2.py) — direct import
  - `test_f1_r2_the_as_of_curve_ignores_gradings_recorded_after_the_cutoff`
- [tests/test_reader_recap_review_r3.py](../../../../../tests/test_reader_recap_review_r3.py) — direct import
  - `test_f2_r3_embedded_credit_banking_beside_standing_direct_credit_answers_the_claim`
  - `test_f2_r3_embedded_credit_whose_direct_credit_was_regraded_away_leaves_the_claim_open`
- [tests/test_reader_rw3a_landing.py](../../../../../tests/test_reader_rw3a_landing.py) — direct import
- [tests/test_reading_step_switch.py](../../../../../tests/test_reading_step_switch.py) — direct import
  - `test_every_defaults_snapshot_records_the_switch_on`
  - `test_new_vaults_read_on_from_the_furthest_section`
  - `test_replay_never_reads_the_switch`
  - `test_the_reading_step_acts_wherever_the_plan_acts_behind_its_switch`
  - `test_the_reading_step_is_not_a_successor_tag`
- [tests/test_rebuild_equivalence.py](../../../../../tests/test_rebuild_equivalence.py) — direct import
  - `test_a_second_learner_report_on_an_lo_after_an_attempt_rebuilds_to_live`
- [tests/test_rebuild_equivalence_review.py](../../../../../tests/test_rebuild_equivalence_review.py) — direct import
  - `test_the_successor_is_one_constant_after_its_predecessor_with_its_defaults_snapshot`
  - `test_upgrade_from_the_predecessor_rebuilds_to_live_and_through_the_chain`
- [tests/test_recurrence_commands.py](../../../../../tests/test_recurrence_commands.py) — direct import
  - `test_successor_vocabulary`
  - `test_the_upgrade_command_defaults_to_the_latest`
  - `test_the_upgrade_command_prints_the_advisory_guard_status`
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
- [tests/test_regrade_contract_upgrade.py](../../../../../tests/test_regrade_contract_upgrade.py) — direct import
  - `test_upgrade_command_reaches_the_successor`
- [tests/test_required_method_authority.py](../../../../../tests/test_required_method_authority.py) — direct import
- [tests/test_required_method_grading.py](../../../../../tests/test_required_method_grading.py) — direct import
  - `test_the_method_explicit_successor_is_the_latest_after_the_route_rules`
- [tests/test_required_method_reopened.py](../../../../../tests/test_required_method_reopened.py) — direct import
- [tests/test_required_method_rereview.py](../../../../../tests/test_required_method_rereview.py) — direct import
- [tests/test_required_method_round3.py](../../../../../tests/test_required_method_round3.py) — direct import
- [tests/test_required_method_round3_review.py](../../../../../tests/test_required_method_round3_review.py) — direct import
- [tests/test_ro0_codex_review.py](../../../../../tests/test_ro0_codex_review.py) — direct import
  - `test_f3_a_list_that_served_no_head_still_decides_nothing_and_reads_no_ad`
  - `test_f3_a_served_offer_keeps_its_candidates_ad_numbers`
  - `test_f3_a_staged_decision_keeps_its_ad_numbers`
  - `test_f3_the_staged_bridge_hands_its_decision_the_ad_reader`
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
- [tests/test_ro5_calibration.py](../../../../../tests/test_ro5_calibration.py) — direct import
  - `test_below_the_tag_the_cli_report_has_no_calibration_section`
- [tests/test_ro5_checks.py](../../../../../tests/test_ro5_checks.py) — direct import
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
- [tests/test_route_rules_in_grader.py](../../../../../tests/test_route_rules_in_grader.py) — direct import
  - `test_the_route_rules_follow_the_route_check_and_value_of_information_stopping_follows_them`
- [tests/test_router_card.py](../../../../../tests/test_router_card.py) — direct import
- [tests/test_router_g1_feasibility.py](../../../../../tests/test_router_g1_feasibility.py) — direct import
  - `test_a_chooser_naming_an_infeasible_or_unknown_id_falls_back`
  - `test_a_reserved_assessment_surface_is_refused_on_today`
  - `test_a_seen_probe_is_served_by_dl1_and_refused_by_the_staged_frame`
  - `test_an_unseen_probe_stays_in_the_plan`
  - `test_the_staged_frame_keeps_refusals_through_the_projection`
- [tests/test_router_g4_restraint.py](../../../../../tests/test_router_g4_restraint.py) — direct import
  - `test_a_follow_up_joins_the_current_block_today_and_waits_with_a_decider_near_zero`
- [tests/test_router_p2_bridge.py](../../../../../tests/test_router_p2_bridge.py) — direct import
  - `test_a_requested_state_other_than_the_canonical_successor_is_the_learners_choice`
  - `test_a_retried_constraint_vetoed_advance_stays_deferred`
  - `test_a_staged_veto_defers_the_run_and_says_why_in_plain_words`
  - `test_golden_path_advance_consults_the_staged_policy_through_the_bridge`
  - `test_switched_off_the_rpc_advances_the_run_directly`
  - `test_the_response_shape_is_unchanged_for_the_desktop`
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
- [tests/test_source_first_needs.py](../../../../../tests/test_source_first_needs.py) — direct import
  - `test_below_the_tag_and_with_the_switch_off_nothing_runs`
- [tests/test_teach_back.py](../../../../../tests/test_teach_back.py) — direct import
- [tests/test_teacher_te1_curriculum_c4.py](../../../../../tests/test_teacher_te1_curriculum_c4.py) — direct import
- [tests/test_teacher_te1_successor.py](../../../../../tests/test_teacher_te1_successor.py) — direct import
  - `test_a_bare_upgrade_goes_through_mvp041_along_the_chain`
  - `test_the_tag_is_the_chains_last_link_after_curriculum_c1`
  - `test_the_upgrade_from_the_predecessor_and_its_refusals`
  - `test_with_the_switch_off_or_below_the_tag_practice_is_byte_identical`
- [tests/test_teacher_te1b_suggestions.py](../../../../../tests/test_teacher_te1b_suggestions.py) — direct import
  - `test_the_successor_is_the_latest_link_after_followups_nov2`
  - `test_the_upgrade_from_teacher_te1_and_its_refusals`
- [tests/test_ux_phase1_round2_rereview.py](../../../../../tests/test_ux_phase1_round2_rereview.py) — direct import
  - `test_f2_every_plan_version_serves_the_reading_step_behind_its_kill_switch`
- [tests/test_ux_phase4_landing.py](../../../../../tests/test_ux_phase4_landing.py) — direct import
  - `test_a_contest_regrade_records_provenance_and_re_resolves_the_forecast`
  - `test_a_contest_the_regrade_does_not_uphold_is_flagged_never_held`

## Modification guidance

- Make changes here when the responsibility remains algorithm versions within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
