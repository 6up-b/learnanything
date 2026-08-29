---
title: "learnloop.diagnosis.causal_attribution"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/causal_attribution.py"
source_paths:
  - "src/learnloop/diagnosis/causal_attribution.py"
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
  - "learnloop.diagnosis.causal_attribution module"
  - "src/learnloop/diagnosis/causal_attribution.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.causal_attribution`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.causal_attribution` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Causal-attribution records, structural repair, and learner reports.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/causal_attribution.py](../../../../../../src/learnloop/diagnosis/causal_attribution.py) |
| Source lines | 3641 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class VerificationResult` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 233) — Typed deterministic-verifier output; no boolean authority laundering.
  - `__post_init__(self) -> None` (line 248; internal)
  - `as_dict(self) -> dict[str, Any]` (line 258; public)
- `class RepairValidationResult` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 269) — Validator-owned structural and deterministic-verification outcome.
  - `as_dict(self) -> dict[str, Any]` (line 277; public)
- `class SympyVerifierAdapter` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 291) — Small P1 CAS adapter for equality checks.
  - `verify(self, observed_expression: str, expected_expression: str, *, assumptions: tuple[str, ...]=(), required_assumptions: tuple[str, ...]=()) -> VerificationResult` (line 298; public)
- `class TestExecutionVerifierAdapter` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 344) — Typed adapter over an already-sandboxed test-execution result.
  - `verify(self, *, returncode: int | None, tests_collected: int, parsed_form: Any=None, assumptions: tuple[str, ...]=()) -> VerificationResult` (line 347; public)
- `validate_repair_candidate(suggestion: dict[str, Any], *, expected_answer: str | dict[str, Any] | None=None, trace_contract: Any=None, execution_result: Mapping[str, Any] | None=None) -> RepairValidationResult` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 471) — Validate a repair without trusting any verdict supplied in its payload.
- `select_minimal_repair(repairs: list[dict[str, Any]], *, protected_refs: list[dict[str, Any]] | None=None, episode_id: str | None=None, repair_policy_version: str=REPAIR_POLICY_VERSION, expected_answer: str | dict[str, Any] | None=None, trace_contract: Any=None, learner_answer_md: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 691) — Select the least-backtracking safe repair by §6.4's lexicographic rule.
- `repair_equivalence_id(repair_class: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 901) — The cross-episode "same help" id for a repair class (Aug A2).
- `repair_class_definition_rows(repair_classes: Sequence[Mapping[str, Any]], *, episode_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 934) — Durable-store rows for the repair classes an episode minted.
- `mint_causal_mechanism_taxonomy(repository: Repository, *, min_cluster_size: int=2, activate: bool=False, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 1024) — Build an immutable mechanism-taxonomy snapshot as an explicit batch.
- `normalized_prior_weights(candidates: Sequence[Mapping[str, Any]]) -> tuple[list[float], str]` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 1515) — Normalize the grader's verbalized candidate weights across one set.
- `hypothesis_mechanism_projection(hypothesis: Mapping[str, Any]) -> tuple[str | None, str]` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 1580) — The post-hoc mechanism projection stored on a hypothesis.
- `receipt_probe_need(receipt: dict[str, Any] | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 2044) — Read `probe_need` from a receipt of any schema version.
- `receipt_trace_consistency(receipt: dict[str, Any] | None, *, hypothesis_ids: list[str] | None=None) -> dict[str, str]` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 2070) — Read the per-hypothesis trace-consistency map from any schema version.
- `materialize_causal_episode(vault: LoadedVault, repository: Repository, *, attempt_id: str, repair_suggestions: list[dict[str, Any]] | None=None, generation_agent_run_id: str | None=None, model: str | None=None, mechanism_taxonomy_version_id: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 2272) — Materialize all P1 causal records and return the immutable receipt.
- `append_dialogue_candidate(vault: LoadedVault, repository: Repository, *, attempt_id: str, candidate: Mapping[str, Any], question_event_id: str, remediation_episode_id: str | None=None, post_reveal: bool=False, generation_agent_run_id: str | None=None, model: str | None=None, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 2621) — Append a hypothesis version for a cause the DIALOGUE surfaced.
- `record_eliciting_response(vault: LoadedVault, repository: Repository, *, attempt_id: str, suggestion_index: int, response_md: str, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 2736) — Record the learner's unaided answer to an eliciting repair's question.
- `causal_episode_for_attempt(repository: Repository, attempt_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 2816)
- `claim_checked_feedback(vault: LoadedVault, repository: Repository, attempt_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 2869) — Build the typed P1 overlay, failing closed on unpermitted claims.
- `record_causal_diagnosis_contest(vault: LoadedVault, repository: Repository, *, attempt_id: str, response: str, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 3117) — Record a typed P1 contest even when P0 opened no ambiguity factor.
- `trace_consistent(vault: LoadedVault, repository: Repository, attempt_id: str, *, hypothesis_id: str | None=None) -> bool` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 3414) — DEPRECATED receipt-level veto; prefer ``_trace_consistency_states``.
- `record_unresolved_cause_self_report(vault: LoadedVault, repository: Repository, *, factor_id: str, response: str, candidate_index: int | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 3437) — Record the one-tap report; confirmation may open a provisional belief.

### Module constants

- `SELF_REPORT_REASONS` ([src/learnloop/diagnosis/causal_attribution.py](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 32)
- `_NORMALIZE_RE` ([src/learnloop/diagnosis/causal_attribution.py](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 43)
- `PERMITTED_USES` ([src/learnloop/diagnosis/causal_attribution.py](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 45)
- `SINGLE_ATTEMPT_USES` ([src/learnloop/diagnosis/causal_attribution.py](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 54)
- `REPAIR_POLICY_VERSION` ([src/learnloop/diagnosis/causal_attribution.py](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 66)
- `REPAIR_SELECTION_BASES` ([src/learnloop/diagnosis/causal_attribution.py](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 75)
- `LATENT_COST_RESOLUTION_FLOOR` ([src/learnloop/diagnosis/causal_attribution.py](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 83)
- `CAUSAL_DECISION_POLICY_VERSION` ([src/learnloop/diagnosis/causal_attribution.py](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 88)
- `OPEN_SET_CAUSE_ID` ([src/learnloop/diagnosis/causal_attribution.py](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 102)
- `REPAIR_MAPPING_BASIS_TARGET_REF` ([src/learnloop/diagnosis/causal_attribution.py](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 113)
- `REPAIR_MAPPING_BASIS_CRITERION_REF` ([src/learnloop/diagnosis/causal_attribution.py](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 114)
- `REPAIR_MAPPING_BASIS_SELECTED_REPAIR` ([src/learnloop/diagnosis/causal_attribution.py](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 119)
- `REPAIR_MAPPING_BASIS_OPEN_SET` ([src/learnloop/diagnosis/causal_attribution.py](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 120)
- `REPAIR_MAPPING_BASIS_UNRESOLVED` ([src/learnloop/diagnosis/causal_attribution.py](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 121)
- `REPAIR_MAPPING_BASES` ([src/learnloop/diagnosis/causal_attribution.py](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 123)
- `REPAIR_MAPPING_UNRESOLVED_REASONS` ([src/learnloop/diagnosis/causal_attribution.py](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 134)
- `DIAGNOSIS_RECEIPT_SCHEMA_VERSION` ([src/learnloop/diagnosis/causal_attribution.py](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 153)
- `SUPPORT_AUTHORITIES` ([src/learnloop/diagnosis/causal_attribution.py](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 159)
- `APPROVED_SUPPORT_AUTHORITIES` ([src/learnloop/diagnosis/causal_attribution.py](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 170)
- `DEFAULT_SUPPORT_AUTHORITY` ([src/learnloop/diagnosis/causal_attribution.py](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 178)
- `SUPPORT_BASIS_AUTHORITY` ([src/learnloop/diagnosis/causal_attribution.py](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 189)
- `DIAGNOSIS_SUPPORT_BASES` ([src/learnloop/diagnosis/causal_attribution.py](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 201)
- `TRACE_CONSISTENCY_STATES` ([src/learnloop/diagnosis/causal_attribution.py](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 207)
- `VERIFICATION_STATUSES` ([src/learnloop/diagnosis/causal_attribution.py](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 214)
- `MECHANISM_TAXONOMY_ALGORITHM` ([src/learnloop/diagnosis/causal_attribution.py](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 971)
- `MECHANISM_ABSTENTION_REASONS` ([src/learnloop/diagnosis/causal_attribution.py](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 977)
- `NONTRIVIAL_REPAIR_ERROR_TYPES` ([src/learnloop/diagnosis/causal_attribution.py](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 2149)
- `TRIVIAL_REPAIR_ERROR_TYPES` ([src/learnloop/diagnosis/causal_attribution.py](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 2161)
- `ELICITING_RESPONSE_REASON` ([src/learnloop/diagnosis/causal_attribution.py](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 2733)

## Internal implementation anchors

- `_content_id(prefix: str, value: Any) -> str` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 225)
- `_declared_checkpoint_ids(trace: dict[str, Any] | None) -> list[str]` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 380)
- `_checkpoint_claims_verifiable(trace_contract: Any, changed_checkpoint_ids: Sequence[str]) -> bool | None` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 392) — Are the claimed checkpoint ids real steps of some authored recipe?
- `_backtracking_depth(trace_contract: Any, changed_steps: Sequence[str]) -> int | None` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 423) — How far back through an authored recipe a repair reaches.
- `_ref_key(ref: Any) -> str` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 618)
- `_trace_edit_cost(before: str, after: str) -> int` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 633)
- `_repair_class(suggestion: dict[str, Any], *, episode_id: str | None=None, repair_policy_version: str=REPAIR_POLICY_VERSION) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 643)
- `_normalized(value: str) -> str` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 897)
- `_discrimination_profile(hypothesis: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 998) — What a probe would have to observe to bear on this hypothesis.
- `_record_abstention_notes(repository: Repository, *, attempt_id: str, repair_classes: Sequence[Mapping[str, Any]], selected_repair_class_id: str | None, clock: Clock | None=None) -> int` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 1196) — Capture A5 missing-vocabulary notes for this episode's abstentions.
- `_operation_labels(members: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 1232) — Operation strings observed in a group, most frequent first.
- `_criterion_receipt(vault: LoadedVault, repository: Repository, attempt_id: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 1250)
- `_repair_definitions(repair_suggestions: list[dict[str, Any]], protected_refs: list[dict[str, Any]], *, episode_id: str, expected_answer: str | dict[str, Any] | None=None, trace_contract: Any=None, learner_answer_md: str | None=None) -> tuple[list[dict[str, Any]], dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 1340)
- `_classes_covering(repair_classes: list[dict[str, Any]], keys: set[str]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 1382)
- `_resolve_repair_mapping(repair_classes: list[dict[str, Any]], *, target_ref: dict[str, Any] | None, criterion_ids: Sequence[Any]=(), open_set: bool=False, selected_repair_class_id: str | None=None) -> tuple[str | None, str, str | None]` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 1394) — Map one hypothesis onto an authored repair class.
- `_candidate_key(candidate: dict[str, Any], *, target_ref: dict[str, Any] | None, status: str) -> str` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 1461) — Stable identity for a candidate independent of presentation order.
- `_event_candidate_causes(event: dict[str, Any]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 1483) — The raw candidate causes an error event proposes, in authored order.
- `_raw_prior_weight(candidate: Mapping[str, Any]) -> float | None` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 1504)
- `_discriminating_predictions(candidate: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 1560) — The candidate's free-text falsifiable expectations, in authored order.
- `_candidate_status(candidate: dict[str, Any]) -> str` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 1607)
- `_selected_repair_class_id(selection: dict[str, Any] | None) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 1616)
- `_repair_mapping_fields(repair_classes: list[dict[str, Any]], *, target_ref: dict[str, Any] | None, criterion_ids: Sequence[Any]=(), status: str, selected_repair_class_id: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 1626) — The three persisted repair-mapping columns for one hypothesis spec.
- `_hypothesis_specs(vault: LoadedVault, repository: Repository, *, attempt_id: str, repair_classes: list[dict[str, Any]], selected_repair_class_id: str | None=None) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 1650)
- `_anchors(hypotheses: list[dict[str, Any]], selection: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 1891)
- `_repair_cover_matrix(hypotheses: list[dict[str, Any]], selection: dict[str, Any]) -> tuple[list[dict[str, Any]], bool, str | None]` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 1960)
- `_probe_need(*, divergent: bool, repair_class_ids: list[str], common_repair_cover: bool, incomplete_repair_mapping: bool) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 2010) — State what a probe would have to resolve — never whether to run one.
- `_attempt_trace_contract(vault: LoadedVault, attempt: dict[str, Any]) -> Any` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 2104) — The authored decomposition of the item an attempt was made on.
- `_attempt_has_nontrivial_error(repository: Repository, *, attempt_id: str, concrete: Sequence[Mapping[str, Any]]) -> bool` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 2166) — True when the attempt's recorded error types include a nontrivial one.
- `_open_repair_factor(repository: Repository, *, attempt: Mapping[str, Any], concrete: Sequence[Mapping[str, Any]], clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 2200) — Open the repair-lane factor a failed attempt owes.
- `_claim_hypothesis_id(claim: dict[str, Any], *, labels: dict[str, str], by_index: list[str | None], known_ids: set[str]) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 3193) — Resolve an explicit hypothesis reference carried by a claim, if any.
- `_postdictive_claim_attribution(repository: Repository, attempt_id: str, hypotheses: list[dict[str, Any]]) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 3220) — Attribute each deterministic claim to at most ONE hypothesis.
- `_trace_consistency_states(vault: LoadedVault, repository: Repository, attempt_id: str, hypotheses: list[dict[str, Any]] | None=None) -> tuple[dict[str, str], dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/causal_attribution.py), line 3313) — Per-hypothesis trace-consistency states plus their audit detail (§5.6).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `materialize_causal_episode`; statically calls `materialize_causal_episode`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `validate_repair_candidate`; statically calls `validate_repair_candidate`
- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `causal_episode_for_attempt`, `mint_causal_mechanism_taxonomy`; statically calls `causal_episode_for_attempt`, `mint_causal_mechanism_taxonomy`
- [[Reference/Modules/learnloop/diagnosis/causal_health|learnloop.diagnosis.causal_health]] — imports `APPROVED_SUPPORT_AUTHORITIES`, `OPEN_SET_CAUSE_ID`
- [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] — imports `CAUSAL_DECISION_POLICY_VERSION`, `SUPPORT_BASIS_AUTHORITY`, `_normalized`; statically calls `_normalized`
- [[Reference/Modules/learnloop/diagnosis/causal_probe_coherence|learnloop.diagnosis.causal_probe_coherence]] — imports `CAUSAL_DECISION_POLICY_VERSION`, `OPEN_SET_CAUSE_ID`, `SUPPORT_BASIS_AUTHORITY`
- [[Reference/Modules/learnloop/diagnosis/diagnosis_adjudication|learnloop.diagnosis.diagnosis_adjudication]] — imports `causal_episode_for_attempt`; statically calls `causal_episode_for_attempt`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_augmentation|learnloop.diagnosis.diagnostic_augmentation]] — imports `SympyVerifierAdapter`, `repair_equivalence_id`; statically calls `SympyVerifierAdapter`, `repair_equivalence_id`
- [[Reference/Modules/learnloop/diagnosis/failure_triage|learnloop.diagnosis.failure_triage]] — imports `APPROVED_SUPPORT_AUTHORITIES`, `OPEN_SET_CAUSE_ID`, `receipt_trace_consistency`; statically calls `receipt_trace_consistency`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `causal_episode_for_attempt`; statically calls `causal_episode_for_attempt`
- [[Reference/Modules/learnloop/diagnosis/misconceptions|learnloop.diagnosis.misconceptions]] — imports `materialize_causal_episode`; statically calls `materialize_causal_episode`
- [[Reference/Modules/learnloop/diagnosis/missing_vocabulary|learnloop.diagnosis.missing_vocabulary]] — imports `CAUSAL_DECISION_POLICY_VERSION`, `REPAIR_POLICY_VERSION`
- [[Reference/Modules/learnloop/diagnosis/probe_blocks|learnloop.diagnosis.probe_blocks]] — imports `claim_checked_feedback`; statically calls `claim_checked_feedback`
- [[Reference/Modules/learnloop/diagnosis/probe_targeting|learnloop.diagnosis.probe_targeting]] — imports `OPEN_SET_CAUSE_ID`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `OPEN_SET_CAUSE_ID`
- [[Reference/Modules/learnloop/tutor/durable_promotion|learnloop.tutor.durable_promotion]] — imports `OPEN_SET_CAUSE_ID`, `causal_episode_for_attempt`, `trace_consistent`; statically calls `causal_episode_for_attempt`, `trace_consistent`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `append_dialogue_candidate`; statically calls `append_dialogue_candidate`
- [[Reference/Modules/learnloop_sidecar/handlers/adjudication|learnloop_sidecar.handlers.adjudication]] — imports `causal_episode_for_attempt`, `claim_checked_feedback`; statically calls `causal_episode_for_attempt`, `claim_checked_feedback`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `record_causal_diagnosis_contest`, `record_eliciting_response`, `record_unresolved_cause_self_report`; statically calls `record_causal_diagnosis_contest`, `record_eliciting_response`, `record_unresolved_cause_self_report`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `causal_episode_for_attempt`, `claim_checked_feedback`; statically calls `causal_episode_for_attempt`, `claim_checked_feedback`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/reveal_ledger|learnloop.attempts.reveal_ledger]] — imports `production_admissibility`; calls `production_admissibility`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/error_taxonomy_map|learnloop.diagnosis.error_taxonomy_map]] — imports `MECHANISM_PROJECTION_OPEN_SET`, `map_legacy_error_type`, `project_mechanism`; calls `map_legacy_error_type`, `project_mechanism`
- [[Reference/Modules/learnloop/diagnosis/missing_vocabulary|learnloop.diagnosis.missing_vocabulary]] — imports `record_diagnostic_abstention_notes`; calls `record_diagnostic_abstention_notes`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/learner/capability_mapping|learnloop.learner.capability_mapping]] — imports `CriterionOutcome`, `localize_criterion_outcomes`; calls `CriterionOutcome`, `localize_criterion_outcomes`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `surface_group_id`; calls `surface_group_id`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `difflib`, `hashlib`, `json`, `re`, `typing`
- Third party: `sympy`

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]], [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/diagnosis/causal_health|learnloop.diagnosis.causal_health]], [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] and 15 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_causal_attribution_p0.py](../../../../../../tests/test_causal_attribution_p0.py) — direct import
  - `test_learner_confirmation_resolves_factor_to_provisional_belief`
  - `test_nonconfirming_self_report_is_recorded_once_without_reprompt`
- [tests/test_causal_attribution_p1.py](../../../../../../tests/test_causal_attribution_p1.py) — direct import
  - `test_a_model_cannot_supply_its_own_execution_result`
  - `test_attempt_materializes_append_only_hypothesis_and_receipt`
  - `test_backend_validator_owns_symbolic_verification_verdict`
  - `test_candidate_reordering_does_not_change_episode_identity`
  - `test_common_repair_cover_requires_explicit_target_match`
  - `test_distinct_measurement_need_splits_a_shared_repair`
  - `test_distinct_repair_splits_one_operation_string_into_two_mechanisms`
  - `test_feedback_overlay_and_cli_are_receipt_checked`
  - `test_feedback_overlay_fails_closed_without_learner_permission`
  - `test_lexical_operation_synonyms_collapse_into_one_mechanism`
  - `test_mechanism_taxonomy_is_earned_from_recurring_operations`
  - `test_repair_class_definitions_are_durable_and_content_addressed`
  - `test_retired_taxonomy_is_never_adopted_by_a_new_receipt`
  - `test_structural_selector_rejects_incomplete_zero_cost_repair`
  - `test_structural_selector_rejects_repairs_that_damage_a_passed_target`
  - `test_test_execution_verifier_is_reachable_from_dispatch`
  - `test_unmapped_repair_class_abstains_with_a_typed_reason`
  - `test_verifier_adapters_preserve_typed_outcomes`
- [tests/test_causal_p2_acceptance.py](../../../../../../tests/test_causal_p2_acceptance.py) — direct import
  - `test_causal_disambiguation_end_to_end_acceptance`
  - `test_self_report_keeps_the_repair_mapping_and_returns_a_live_id`
- [tests/test_causal_repair_mapping_p2.py](../../../../../../tests/test_causal_repair_mapping_p2.py) — direct import
  - `test_authored_divergent_repairs_fill_repair_class_id_end_to_end`
  - `test_open_set_cause_id_and_probe_label_are_distinct_namespaces`
  - `test_repair_declared_by_criterion_maps_to_a_facet_targeted_cause`
  - `test_self_graded_attempt_records_no_repair_authored_not_a_silent_null`
  - `test_two_repairs_on_one_target_are_ambiguous_rather_than_a_guess`
- [tests/test_causal_trace_consistency_p2.py](../../../../../../tests/test_causal_trace_consistency_p2.py) — direct import
  - `test_legacy_schema_two_receipts_are_readable`
  - `test_overlay_carries_per_hypothesis_state`
  - `test_receipt_stamps_schema_three_and_the_decision_policy`
- [tests/test_common_repair_delivery.py](../../../../../../tests/test_common_repair_delivery.py) — direct import
  - `test_diagnostic_factor_is_not_reopened_by_rematerialization`
- [tests/test_diagnosis_adjudication.py](../../../../../../tests/test_diagnosis_adjudication.py) — direct import
  - `test_contest_leads_the_queue_and_is_provenance_never_the_verdict`
  - `test_queue_reason_is_persisted_so_selection_bias_is_auditable`
- [tests/test_diagnostic_augmentation.py](../../../../../../tests/test_diagnostic_augmentation.py) — direct import
  - `test_c3_disagreement_becomes_unresolved_cause_set_and_real_support`
- [tests/test_dialogue_causal_join.py](../../../../../../tests/test_dialogue_causal_join.py) — direct import
  - `test_a_nonsense_candidate_statement_is_never_rejected`
  - `test_an_eliciting_response_after_a_reveal_is_recorded_but_not_independent`
  - `test_an_empty_eliciting_response_is_refused`
  - `test_prior_weights_normalize_and_absent_weights_fall_back_to_uniform`
  - `test_submit_eliciting_response_records_a_factor_response`
- [tests/test_durable_promotion_arms.py](../../../../../../tests/test_durable_promotion_arms.py) — direct import
  - `test_a_contest_is_not_a_confirmation`
  - `test_the_proof_must_be_about_the_confirmed_belief`
- [tests/test_minimal_repair_selection_a1.py](../../../../../../tests/test_minimal_repair_selection_a1.py) — direct import
  - `test_a_one_claim_latent_difference_is_below_the_resolution_floor`
  - `test_checkpoint_outside_every_recipe_is_a_typed_rejection`
  - `test_claiming_checkpoints_on_an_undecomposable_item_is_unverifiable`
  - `test_depth_outranks_a_one_claim_latent_difference`
  - `test_no_reliable_decomposition_still_selects_and_declares_the_regime`
  - `test_no_trace_contract_cannot_verify_and_does_not_pretend_to`
  - `test_repair_policy_version_no_longer_overclaims`
  - `test_the_persisted_repair_class_is_the_structurally_selected_one`
  - `test_trace_edit_cost_breaks_a_depth_and_checkpoint_tie`
- [tests/test_missing_vocabulary_notes.py](../../../../../../tests/test_missing_vocabulary_notes.py) — direct import
  - `test_note_capture_is_idempotent_across_rematerialization`
- [tests/test_sidecar_adjudication.py](../../../../../../tests/test_sidecar_adjudication.py) — direct import
  - `test_queue_is_stratified_contests_first_then_abstentions`

## Modification guidance

- Change causal attribution policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/causal_attribution.py](../../../../../../src/learnloop/diagnosis/causal_attribution.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
