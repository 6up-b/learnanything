---
title: "learnloop.diagnosis.causal_orchestrator"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/causal_orchestrator.py"
source_paths:
  - "src/learnloop/diagnosis/causal_orchestrator.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.diagnosis"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.causal_orchestrator module"
  - "src/learnloop/diagnosis/causal_orchestrator.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.causal_orchestrator`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.causal_orchestrator` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: P2 causal repair orchestration (spec_causal_attribution_v1 §6).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py) |
| Source lines | 3301 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class OrchestratorParameters` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 291) — Resolved orchestrator knobs plus their provenance.
  - `__getitem__(self, key: str) -> float` (line 299; internal)
  - `manifest(self) -> dict[str, Any]` (line 302; public)
- `resolve_orchestrator_parameters(repository: Repository | None) -> OrchestratorParameters` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 312)
- `class RepairAction` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 357)
  - `as_dict(self) -> dict[str, str]` (line 361; public)
- `class RepairStatus` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 366) — The typed union returned by :func:`causal_repair_status` (§6).
  - `__post_init__(self) -> None` (line 403; internal)
  - `repair_permitted(self) -> bool` (line 407; public) — True when the causal state allows the targeted repair to run.
  - `as_dict(self) -> dict[str, Any]` (line 417; public)
- `backfill_obligation(targeting: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 489) — The typed backfill obligation for one classified cause set.
- `instrument_commissioning_obligation(targeting: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 524) — The typed obligation for a divergent factor with no instrument.
- `enqueue_backfill_obligation(repository: Repository, obligation: Mapping[str, Any], *, learning_object_id: str | None, source: str='causal_orchestrator', clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 552) — Queue one typed obligation; idempotent on its content hash.
- `sweep_machine_checks(vault: LoadedVault, repository: Repository, learning_object_id: str, *, source: str='causal_orchestrator', clock: Clock | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 578) — Turn backfill obligations into queued machine checks, idempotently.
- `close_satisfied_backfills(repository: Repository, factor_id: str, *, clock: Clock | None=None) -> int` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 716) — Close this factor's repair-mapping checks once it owes nothing.
- `resolve_machine_check(repository: Repository, check_id: str, *, resolution: Mapping[str, Any], status: str='resolved', clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 746) — Explicit discharge for a regrade / verifier / authoring agent.
- `pending_machine_checks_for_factor(repository: Repository, *, factor_id: str, learning_object_id: str | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 761) — Checks that must discharge before this factor may buy learner effort.
- `record_learner_preference(repository: Repository, *, preference: str, factor_id: str | None=None, learning_object_id: str | None=None, session_id: str | None=None, source: str='learner_action', expires_at: str | None=None, detail: Mapping[str, Any] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 798)
- `learner_preference(repository: Repository, *, factor_id: str | None=None, learning_object_id: str | None=None, session_id: str | None=None) -> str` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 835)
- `open_factors_for_hypothesis(repository: Repository, causal_hypothesis_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 855) — Open cause factors on this hypothesis' own learning object (§3.9).
- `diagnosis_receipt(repository: Repository, attempt_id: str | None) -> Mapping[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 960)
- `class DiscriminationInputs` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 1103) — The two EVSI terms plus where each came from (standing constraint 4).
- `class CausalRepairError(ValueError)` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 1185) — The repair case itself is unusable (no such misconception / candidate).
- `causal_repair_status(vault: LoadedVault | None, repository: Repository, *, misconception_id: str, session_id: str | None=None, session_budget_minutes: float | None=None, start_repair: bool=True, clock: Clock | None=None) -> RepairStatus` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 1241) — Resolve — and where safe, START — the repair for one cause.
- `class ProbeOffer` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 1928) — Result of accepting the quick check.
  - `as_dict(self) -> dict[str, Any]` (line 1941; public)
- `episode_conflict_reason(repository: Repository, episode: ProbeEpisodeRecord | None) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 1959) — Why an already-open probe episode cannot host this causal probe.
- `accept_probe_offer(vault: LoadedVault, repository: Repository, *, factor_id: str, decision_receipt_id: str | None=None, session_id: str | None=None, clock: Clock | None=None, ai_client: object | None=None) -> ProbeOffer` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 1998) — "Take the quick check": enter a factor-aware episode and pin the probe.
- `defer_probe_offer(repository: Repository, *, factor_id: str, learning_object_id: str | None=None, session_id: str | None=None, preference: str='decline', clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 2179) — "Not now": persist the decline so the next attempt does not re-offer.
- `request_teaching_now(vault: LoadedVault, repository: Repository, *, misconception_id: str, factor_id: str, session_id: str | None=None, clock: Clock | None=None) -> RepairStatus` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 2202) — "Teach me now": an explicit learner authorisation to skip the check.
- `pinned_causal_probe(repository: Repository, presentation_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 2234)
- `classify_probe_response(repository: Repository, *, presentation_id: str, observed_features: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 2245) — Classify an administered causal probe against its PINNED bundles.
- `class DiscriminatingObservation` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 2305) — One classification, judged: what it may close and what it may not.
  - `outcome(self) -> str` (line 2317; public)
  - `observation_id(self) -> str | None` (line 2321; public)
  - `as_dict(self) -> dict[str, Any]` (line 2324; public)
- `record_learner_embedded_prediction(repository: Repository, *, factor_id: str, prediction: str, question_event_id: str, attempt_id: str | None=None, practice_item_id: str | None=None, remediation_episode_id: str | None=None, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 2454) — Record a falsifiable expectation the learner's OWN question asserted.
- `record_probe_classification(repository: Repository, *, presentation_id: str, observed_features: Mapping[str, Any], feature_source: str, probe_attempt_id: str | None=None, clock: Clock | None=None) -> DiscriminatingObservation` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 2533) — Classify an administered probe AND act on the verdict (§6, §7).
- `deterministic_probe_features(vault: LoadedVault, repository: Repository, attempt_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 2727) — The graded probe attempt's own criterion outcomes, as a feature vector.
- `auto_classify_pinned_probe(vault: LoadedVault, repository: Repository, *, attempt_id: str, clock: Clock | None=None) -> DiscriminatingObservation | None` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 2773) — Close the loop automatically when a probe answer can be read by machine.
- `cold_verification_context(vault: LoadedVault | None, repository: Repository, *, episode: Mapping[str, Any], source_attempt: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 2845) — Everything ``record_delayed_cold_verification`` will need, resolved NOW.
- `record_cold_verification_from_task(vault: LoadedVault, repository: Repository, *, task: Mapping[str, Any], cold_attempt_id: str, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 2955) — Fire the delayed cold verification when a scheduled retry completes.
- `sweep_expired_cold_retries(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 3134) — Turn silent cold-retry expiries into typed §4.3 dispositions.

### Module constants

- `CAUSAL_ORCHESTRATOR_FORMULA_VERSION` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 140)
- `CAUSAL_ORCHESTRATOR_POLICY_SCOPE` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 145)
- `REPAIR_STATUSES` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 147)
- `LEARNER_PREFERENCES` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 155)
- `EVSI_PROVENANCE` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 165)
- `LOSS_TABLE_REGIME_P2_PROXY` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 176)
- `MACHINE_CHECK_REPAIR_MAPPING` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 178)
- `MACHINE_CHECK_INSTRUMENT_COMMISSIONING` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 184)
- `PROBE_BLOCKING_MACHINE_CHECK_KINDS` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 195)
- `SWEPT_MACHINE_CHECK_KINDS` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 200)
- `BLIND_PROBE_BASIS` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 208)
- `OBSERVATION_FEATURE_SOURCES` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 214)
- `VALIDATOR_OWNED_FEATURE_SOURCES` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 221)
- `DISCRIMINATING_OUTCOMES` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 226)
- `DETERMINISTIC_FEATURE_PREFIX` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 229)
- `NEEDS_DISAMBIGUATION_MESSAGE` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 234)
- `DEFERRED_OFFER_MESSAGE` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 238)
- `DEFERRED_MACHINE_CHECKS_MESSAGE` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 242)
- `SAFE_COMMON_REPAIR_MESSAGE` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 246)
- `BLOCKED_PENDING_REVIEW_MESSAGE` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 250)
- `EPISODE_CONFLICT_REASON` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 256)
- `EPISODE_CONFLICT_MESSAGE` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 257)
- `STARTED_MESSAGE` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 262)
- `TAKE_QUICK_CHECK` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 264)
- `TEACH_ME_NOW` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 265)
- `NOT_NOW` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 266)
- `CAUSAL_ORCHESTRATOR_POLICY_DEFAULTS` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 272)
- `_ORCHESTRATOR_POLICY_BOUNDS` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 283)
- `_UNCOMMITTED_REPAIR_STATES` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 1193)
- `_EMBEDDED_PREDICTION_OUTCOME` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 2451)

### Explicit exports

`__all__` declares:

- `BLIND_PROBE_BASIS`
- `CAUSAL_ORCHESTRATOR_FORMULA_VERSION`
- `CAUSAL_ORCHESTRATOR_POLICY_DEFAULTS`
- `CAUSAL_ORCHESTRATOR_POLICY_SCOPE`
- `CausalRepairError`
- `DETERMINISTIC_FEATURE_PREFIX`
- `DISCRIMINATING_OUTCOMES`
- `EVSI_PROVENANCE`
- `OBSERVATION_FEATURE_SOURCES`
- `VALIDATOR_OWNED_FEATURE_SOURCES`
- `DiscriminatingObservation`
- `DiscriminationInputs`
- `EPISODE_CONFLICT_MESSAGE`
- `EPISODE_CONFLICT_REASON`
- `LEARNER_PREFERENCES`
- `MACHINE_CHECK_INSTRUMENT_COMMISSIONING`
- `MACHINE_CHECK_REPAIR_MAPPING`
- `NEEDS_DISAMBIGUATION_MESSAGE`
- `PROBE_BLOCKING_MACHINE_CHECK_KINDS`
- `ProbeOffer`
- `REPAIR_STATUSES`
- `RepairAction`
- `RepairStatus`
- `accept_probe_offer`
- `auto_classify_pinned_probe`
- `backfill_obligation`
- `instrument_commissioning_obligation`
- `causal_repair_status`
- `classify_probe_response`
- `close_satisfied_backfills`
- `deterministic_probe_features`
- `enqueue_backfill_obligation`
- `episode_conflict_reason`
- `cold_verification_context`
- `defer_probe_offer`
- `learner_preference`
- `record_probe_classification`
- `open_factors_for_hypothesis`
- `pending_machine_checks_for_factor`
- `pinned_causal_probe`
- `record_cold_verification_from_task`
- `record_learner_preference`
- `request_teaching_now`
- `resolve_machine_check`
- `resolve_orchestrator_parameters`
- `sweep_expired_cold_retries`
- `sweep_machine_checks`

## Internal implementation anchors

- `_content_id(prefix: str, value: Any) -> str` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 346)
- `_with_reveal_spend(repository: Repository, status: RepairStatus) -> RepairStatus` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 448) — Stamp the episode's reveal spend and the budget it is measured against.
- `_machine_check_id(obligation: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 475)
- `_close_orphan_checks(repository: Repository, learning_object_id: str, live: set[str], *, clock: Clock | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 688)
- `_durable_case_factor(repository: Repository, misconception: Any) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 878) — The open cause factor a durable misconception's case rides on, if any.
- `_case_repair_class_id(repository: Repository, hypothesis: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 911) — The repair class a factor-less diagnosis case would cold-verify (G14).
- `_unmapped_case_obligation(hypothesis: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 932) — The typed mapping obligation for a factor-less unmapped diagnosis case.
- `_receipt_repair_class_id(receipt: Mapping[str, Any] | None) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 973) — The repair class one diagnosis receipt commits to, if any.
- `_repair_class_by_hypothesis(causes: Sequence[Mapping[str, Any]]) -> dict[str, str]` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 999)
- `_avoided_overteaching_minutes(repository: Repository, *, attempt_id: str | None, repair_class_ids: Sequence[str], default_minutes: float) -> tuple[float, str]` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 1013) — Expected teaching minutes a discriminating answer would save, + provenance.
- `_probe_burden_minutes(repository: Repository, practice_item_id: str | None, default_minutes: float) -> tuple[float, str]` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 1066) — Probe burden from the instrument card's own expected seconds, + provenance.
- `_recent_diagnostic_burden(repository: Repository, learning_object_id: str, window: int) -> int` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 1089)
- `_discrimination_inputs(candidate: Mapping[str, Any] | None, repair_class_by_hypothesis: Mapping[str, str]) -> DiscriminationInputs` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 1114) — ``(expected_information_gain, p(information changes the repair))``.
- `_episode_for(repository: Repository, *, case_kind: str, case_ref: str, clock: Clock | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 1196) — The repair episode for this case — reused, not re-minted.
- `_actions(status: str, *, offered: bool) -> tuple[RepairAction, ...]` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 1227)
- `_status_for_factor(repository: Repository, *, misconception_id: str, factor: Mapping[str, Any], session_id: str | None, session_budget_minutes: float | None, start_repair: bool, clock: Clock | None) -> RepairStatus` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 1412)
- `_causal_origin(factor_id: str) -> str` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 1955)
- `_probe_episode_conflict(repository: Repository, *, factor_id: str, learning_object_id: str | None) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 1985) — The conflict that would make ``accept_probe_offer`` refuse, if any.
- `_measured_hypotheses(repository: Repository, classification: Mapping[str, Any], observed_features: Mapping[str, Any]) -> tuple[set[str], set[str]]` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 2337) — Which of the locked set's concrete hypotheses the observation MEASURED.
- `_observation_support_scores(classification: Mapping[str, Any], measured: set[str]) -> dict[str, float]` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 2393) — Support mass a discriminating observation licenses, and nothing more.
- `_probe_production_admissibility(repository: Repository, *, probe_attempt_id: str | None) -> 'ProductionAdmissibility | None'` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 2420) — Was the probe answer produced before anything was revealed to it?

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `MACHINE_CHECK_INSTRUMENT_COMMISSIONING`, `resolve_machine_check`; statically calls `resolve_machine_check`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `CausalRepairError`, `SAFE_COMMON_REPAIR_MESSAGE`, `auto_classify_pinned_probe`, `causal_repair_status`, `record_cold_verification_from_task`, `sweep_machine_checks`; statically calls `auto_classify_pinned_probe`, `causal_repair_status`, `record_cold_verification_from_task`, `sweep_machine_checks`
- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `CausalRepairError`, `causal_repair_status`, `cold_verification_context`; statically calls `causal_repair_status`, `cold_verification_context`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `record_learner_embedded_prediction`; statically calls `record_learner_embedded_prediction`
- [[Reference/Modules/learnloop_sidecar/handlers/remediation|learnloop_sidecar.handlers.remediation]] — imports `CausalRepairError`, `accept_probe_offer`, `causal_repair_status`, `defer_probe_offer`, `request_teaching_now`; statically calls `accept_probe_offer`, `causal_repair_status`, `defer_probe_offer`, `request_teaching_now`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/coldness_receipt|learnloop.attempts.coldness_receipt]] — imports `evaluate_final_coldness`, `record_final_receipt`; calls `evaluate_final_coldness`, `record_final_receipt`
- [[Reference/Modules/learnloop/attempts/reveal_ledger|learnloop.attempts.reveal_ledger]] — imports `production_admissibility`; calls `production_admissibility`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `OBSERVATION_CHANNEL_BLIND_PROBE`, `OBSERVATION_CHANNEL_LEARNER_QUESTION`, `ProbeEpisodeRecord`, `Repository`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `CAUSAL_DECISION_POLICY_VERSION`, `SUPPORT_BASIS_AUTHORITY`, `_normalized`; calls `_normalized`
- [[Reference/Modules/learnloop/diagnosis/causal_diagnostic_selector|learnloop.diagnosis.causal_diagnostic_selector]] — imports `module`; calls `record_shadow_selection`
- [[Reference/Modules/learnloop/diagnosis/causal_factor_deferral|learnloop.diagnosis.causal_factor_deferral]] — imports `sweep_promotion_blocking_factors`; calls `sweep_promotion_blocking_factors`
- [[Reference/Modules/learnloop/diagnosis/causal_probe_coherence|learnloop.diagnosis.causal_probe_coherence]] — imports `ColdVerificationPrecondition`, `ProbeDecision`, `bundle_feature_row_report`, `candidate_has_current_blind_input_contract`, `classify_against_blind_bundles`, `decide_probe`, `order_probe_candidates`, `record_causal_cold_outcome`, `record_delayed_cold_verification`, `repair_class_need_for_factor`, `resolve_causal_probe_parameters`; calls `bundle_feature_row_report`, `candidate_has_current_blind_input_contract`, `classify_against_blind_bundles`, `decide_probe`, `order_probe_candidates`, `record_causal_cold_outcome`, `record_delayed_cold_verification`, `repair_class_need_for_factor`, `resolve_causal_probe_parameters`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `commit_presentation`, `eligible_instruments`, `enter_episode`, `episode_has_observations`, `retarget_episode_to_causal_factor`; calls `commit_presentation`, `eligible_instruments`, `enter_episode`, `episode_has_observations`, `retarget_episode_to_causal_factor`
- [[Reference/Modules/learnloop/diagnosis/probe_targeting|learnloop.diagnosis.probe_targeting]] — imports `CAUSE_SET_INCOMPLETE_MAPPING`, `MAPPING_BASIS_LEGACY_FACET`, `classify_cause_set`; calls `classify_cause_set`
- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `EPISODE_REVEAL_BUDGET`, `episode_reveal_spend`; calls `episode_reveal_spend`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `surface_group_id`; calls `surface_group_id`
- [[Reference/Modules/learnloop/substrate/instrument_serving|learnloop.substrate.instrument_serving]] — imports `unservable_reason`; calls `unservable_reason`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `hashlib`, `json`, `logging`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]], [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]], [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]], [[Reference/Modules/learnloop_sidecar/handlers/remediation|learnloop_sidecar.handlers.remediation]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_causal_cold_outcomes.py](../../../../../../tests/test_causal_cold_outcomes.py) — direct import
  - `test_clean_consume_records_cold_success_row_idempotently`
  - `test_contaminated_consume_records_typed_row`
  - `test_expired_inactive_surface_is_unmeasurable_not_censored`
  - `test_expired_servable_task_right_censors`
  - `test_missing_chain_records_typed_row`
  - `test_same_surface_consume_records_typed_row`
- [tests/test_causal_orchestrator.py](../../../../../../tests/test_causal_orchestrator.py) — direct import
  - `test_a_common_repair_cover_serves_the_repair_and_records_the_skip`
  - `test_a_stale_backfill_check_cannot_wedge_a_now_mapped_factor`
  - `test_a_status_read_records_the_decision_without_minting_an_episode`
  - `test_accepting_the_offer_enters_a_factor_aware_episode_with_pinned_bundles`
  - `test_cold_verification_context_names_the_avoided_affordances`
  - `test_cold_verification_is_carried_through_the_followup_task`
  - `test_divergent_causes_without_a_reviewed_instrument_block_pending_review`
  - `test_evsi_inputs_are_computed_and_carry_their_provenance`
  - `test_inseparable_bundles_yield_a_computed_zero_information_gain`
  - `test_live_attempt_queues_a_repair_mapping_backfill_that_self_closes`
  - `test_not_now_persists_and_the_next_call_does_not_reoffer`
  - `test_relocking_an_open_episode_does_not_inherit_its_evidence`
  - `test_reviewed_active_candidate_produces_the_disambiguation_offer`
  - `test_teach_me_now_starts_the_repair_under_recorded_authorisation`
  - `test_unmapped_hypothesis_defers_the_repair_behind_a_machine_check`
- [tests/test_causal_p2_acceptance.py](../../../../../../tests/test_causal_p2_acceptance.py) — direct import
  - `test_a_probe_answered_after_a_reveal_is_not_independent_evidence`
  - `test_a_probe_answered_with_no_reveal_is_marked_independent`
  - `test_a_verdict_over_unmeasured_features_is_inadmissible`
  - `test_an_instrument_that_did_not_discriminate_resolves_nothing`
  - `test_auto_classification_declines_a_sensor_it_cannot_read`
  - `test_causal_disambiguation_end_to_end_acceptance`
  - `test_no_bundle_matched_supports_the_open_set_but_closes_nothing`
  - `test_self_report_keeps_the_repair_mapping_and_returns_a_live_id`
- [tests/test_causal_probe_commissioning.py](../../../../../../tests/test_causal_probe_commissioning.py) — direct import
  - `test_sweep_machine_checks_queues_the_instrument_debt`
- [tests/test_causal_repair_sidecar_rpcs.py](../../../../../../tests/test_causal_repair_sidecar_rpcs.py) — direct import
  - `test_serving_the_pinned_probe_reuses_its_presentation`
- [tests/test_causal_shadow_selection.py](../../../../../../tests/test_causal_shadow_selection.py) — direct import
  - `test_commissioned_v2_bundles_reach_arm_b_and_the_prior_refusal_passes_through`
  - `test_no_action_mapping_is_a_typed_abstention_not_a_fabricated_route`
  - `test_readiness_report_counts_multiplicity_and_regimes`
  - `test_shadow_failure_and_corruption_cannot_alter_the_live_decision`
  - `test_shadow_receipt_rides_the_live_decision_with_typed_arms`
  - `test_v1_style_bundles_stay_arm_c_and_never_license_measure`
- [tests/test_coldness_receipt.py](../../../../../../tests/test_coldness_receipt.py) — direct import
  - `test_delivered_passage_on_the_cold_items_own_source_span_is_hard`
  - `test_delivered_passages_in_interval_are_typed_exposure_not_indeterminate`
  - `test_delivery_outside_the_interval_is_observed_silence_not_indeterminate`
  - `test_expired_task_gets_a_partial_final_receipt`
  - `test_feedback_reopen_on_the_cold_item_is_a_hard_answer_reveal`
  - `test_feedback_reopen_on_the_source_attempt_is_a_soft_exposure`
  - `test_happy_path_snapshot_verification_and_final_receipt`
  - `test_hard_same_surface_exposure_yields_disposition_not_verification`
  - `test_no_reveal_rows_is_a_scoped_absence_claim_not_a_bare_pass`
  - `test_over_budget_episode_downgrades_the_repair_effect_claim`
  - `test_prescription_without_a_delivery_record_is_unknown_not_pass`
  - `test_recent_retrieval_resets_the_cold_delay_anchor`
  - `test_retrieval_cointervention_demotes_attribution_not_the_verification`
  - `test_reveal_elsewhere_in_the_learning_object_is_soft_not_a_failure`
  - `test_reveal_on_the_cold_item_fails_leakage_and_unassisted`
  - `test_unrelated_remediation_is_counted_but_does_not_change_coldness`
  - `test_within_budget_episode_records_the_spend_without_downgrading`
- [tests/test_common_repair_delivery.py](../../../../../../tests/test_common_repair_delivery.py) — direct import
  - `test_durable_case_records_receipt_readable_by_feedback_attach`
  - `test_failed_diagnostic_attempt_opens_the_repair_lane`
  - `test_learner_derived_hypothesis_defaults_learner_state_and_offer_survives`
  - `test_mapped_factorless_diagnosis_case_still_starts`
  - `test_unmapped_diagnosis_case_defers_machine_checks`
- [tests/test_dialogue_causal_join.py](../../../../../../tests/test_dialogue_causal_join.py) — direct import
  - `test_an_embedded_prediction_stays_admissible_after_a_reveal`
  - `test_embedded_prediction_is_idempotent_per_question`
  - `test_question_join_never_fails_the_learners_answer`
- [tests/test_remediation_cold_retry.py](../../../../../../tests/test_remediation_cold_retry.py) — direct import
  - `test_a_deferred_cold_retry_still_expires_on_its_original_window`
  - `test_repair_status_reports_episode_reveal_spend_against_the_budget`

## Modification guidance

- Change causal orchestrator policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
