---
title: "learnloop.diagnosis.causal_discrimination"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/causal_discrimination.py"
source_paths:
  - "src/learnloop/diagnosis/causal_discrimination.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.causal_discrimination module"
  - "src/learnloop/diagnosis/causal_discrimination.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.causal_discrimination`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.causal_discrimination` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Classify pinned probes and record discriminating observations.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/causal_discrimination.py](../../../../../../src/learnloop/diagnosis/causal_discrimination.py) |
| Source lines | 678 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `pinned_causal_probe(repository: Repository, presentation_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/causal_discrimination.py), line 58)
- `classify_probe_response(repository: Repository, *, presentation_id: str, observed_features: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_discrimination.py), line 69) — Classify an administered causal probe against its PINNED bundles.
- `class DiscriminatingObservation` ([source](../../../../../../src/learnloop/diagnosis/causal_discrimination.py), line 129) — One classification, judged: what it may close and what it may not.
  - `outcome(self) -> str` (line 141; public)
  - `observation_id(self) -> str | None` (line 145; public)
  - `as_dict(self) -> dict[str, Any]` (line 148; public)
- `record_learner_embedded_prediction(repository: Repository, *, factor_id: str, prediction: str, question_event_id: str, attempt_id: str | None=None, practice_item_id: str | None=None, remediation_episode_id: str | None=None, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/causal_discrimination.py), line 252) — Record a falsifiable expectation the learner's OWN question asserted.
- `record_probe_classification(repository: Repository, *, presentation_id: str, observed_features: Mapping[str, Any], feature_source: str, probe_attempt_id: str | None=None, clock: Clock | None=None) -> DiscriminatingObservation` ([source](../../../../../../src/learnloop/diagnosis/causal_discrimination.py), line 331) — Classify an administered probe AND act on the verdict (§6, §7).
- `deterministic_probe_features(vault: LoadedVault, repository: Repository, attempt_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_discrimination.py), line 525) — The graded probe attempt's own criterion outcomes, as a feature vector.
- `auto_classify_pinned_probe(vault: LoadedVault, repository: Repository, *, attempt_id: str, clock: Clock | None=None) -> DiscriminatingObservation | None` ([source](../../../../../../src/learnloop/diagnosis/causal_discrimination.py), line 590) — Close the loop automatically when a probe answer can be read by machine.

### Module constants

- `BLIND_PROBE_BASIS` ([src/learnloop/diagnosis/causal_discrimination.py](../../../../../../src/learnloop/diagnosis/causal_discrimination.py), line 39)
- `OBSERVATION_FEATURE_SOURCES` ([src/learnloop/diagnosis/causal_discrimination.py](../../../../../../src/learnloop/diagnosis/causal_discrimination.py), line 45)
- `VALIDATOR_OWNED_FEATURE_SOURCES` ([src/learnloop/diagnosis/causal_discrimination.py](../../../../../../src/learnloop/diagnosis/causal_discrimination.py), line 52)
- `DETERMINISTIC_FEATURE_PREFIX` ([src/learnloop/diagnosis/causal_discrimination.py](../../../../../../src/learnloop/diagnosis/causal_discrimination.py), line 55)
- `_EMBEDDED_PREDICTION_OUTCOME` ([src/learnloop/diagnosis/causal_discrimination.py](../../../../../../src/learnloop/diagnosis/causal_discrimination.py), line 249)

## Internal implementation anchors

- `_measured_hypotheses(repository: Repository, classification: Mapping[str, Any], observed_features: Mapping[str, Any]) -> tuple[set[str], set[str]]` ([source](../../../../../../src/learnloop/diagnosis/causal_discrimination.py), line 161) — Which of the locked set's concrete hypotheses the observation MEASURED.
- `_observation_support_scores(classification: Mapping[str, Any], measured: set[str]) -> dict[str, float]` ([source](../../../../../../src/learnloop/diagnosis/causal_discrimination.py), line 217) — Support mass a discriminating observation licenses, and nothing more.
- `_deterministic_probe_features_with_reason(vault: LoadedVault, repository: Repository, attempt_id: str) -> tuple[dict[str, Any], str | None]` ([source](../../../../../../src/learnloop/diagnosis/causal_discrimination.py), line 550)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `auto_classify_pinned_probe`; statically calls `auto_classify_pinned_probe`
- [[Reference/Modules/learnloop/diagnosis/probe_offer|learnloop.diagnosis.probe_offer]] — imports `pinned_causal_probe`; statically calls `pinned_causal_probe`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `record_learner_embedded_prediction`; statically calls `record_learner_embedded_prediction`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/causal_activity_policy|learnloop.causal_activity_policy]] — imports `DISCRIMINATING_OUTCOMES`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `OBSERVATION_CHANNEL_LEARNER_QUESTION`, `Repository`
- [[Reference/Modules/learnloop/db/stores/causal|learnloop.db.stores.causal]] — imports `OBSERVATION_CHANNEL_BLIND_PROBE`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `CAUSAL_DECISION_POLICY_VERSION`, `SUPPORT_BASIS_AUTHORITY`
- [[Reference/Modules/learnloop/diagnosis/causal_probe_coherence|learnloop.diagnosis.causal_probe_coherence]] — imports `bundle_feature_row_report`, `candidate_has_current_blind_input_contract`, `classify_against_blind_bundles`; calls `bundle_feature_row_report`, `candidate_has_current_blind_input_contract`, `classify_against_blind_bundles`
- [[Reference/Modules/learnloop/diagnosis/causal_reads|learnloop.diagnosis.causal_reads]] — imports `CAUSAL_ORCHESTRATOR_FORMULA_VERSION`, `CausalRepairError`; calls `CausalRepairError`
- [[Reference/Modules/learnloop/diagnosis/chain_records|learnloop.diagnosis.chain_records]] — imports `module`; calls `record_probe_classification_declined`
- [[Reference/Modules/learnloop/diagnosis/content_ids|learnloop.diagnosis.content_ids]] — imports `content_id`; calls `content_id`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `probe_answer_admissibility`; calls `probe_answer_admissibility`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `unassessed_evidence_row`; calls `unassessed_evidence_row`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]], [[Reference/Modules/learnloop/diagnosis/probe_offer|learnloop.diagnosis.probe_offer]], [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/diagnosis_identity_helpers.py](../../../../../../tests/diagnosis_identity_helpers.py) — direct import
- [tests/diagnosis_journey_helpers.py](../../../../../../tests/diagnosis_journey_helpers.py) — direct import
- [tests/probe_records_helpers.py](../../../../../../tests/probe_records_helpers.py) — direct import
- [tests/test_causal_orchestrator.py](../../../../../../tests/test_causal_orchestrator.py) — direct import
  - `test_a_router_decided_pin_names_its_router_decision_not_a_causal_receipt`
  - `test_accepting_the_offer_enters_a_factor_aware_episode_with_pinned_bundles`
- [tests/test_causal_p2_acceptance.py](../../../../../../tests/test_causal_p2_acceptance.py) — direct import
  - `test_a_probe_answered_after_a_reveal_is_not_independent_evidence`
  - `test_a_probe_answered_with_no_reveal_is_marked_independent`
  - `test_a_verdict_over_unmeasured_features_is_inadmissible`
  - `test_an_instrument_that_did_not_discriminate_resolves_nothing`
  - `test_auto_classification_declines_a_sensor_it_cannot_read`
  - `test_causal_disambiguation_end_to_end_acceptance`
  - `test_no_bundle_matched_supports_the_open_set_but_closes_nothing`
- [tests/test_causal_repair_sidecar_rpcs.py](../../../../../../tests/test_causal_repair_sidecar_rpcs.py) — direct import
  - `test_serving_the_pinned_probe_reuses_its_presentation`
- [tests/test_dialogue_causal_join.py](../../../../../../tests/test_dialogue_causal_join.py) — direct import
  - `test_an_embedded_prediction_stays_admissible_after_a_reveal`
  - `test_embedded_prediction_is_idempotent_per_question`
  - `test_question_join_never_fails_the_learners_answer`
- [tests/test_followup_fg1c_codex_review.py](../../../../../../tests/test_followup_fg1c_codex_review.py) — direct import
  - `test_f3_the_report_and_the_orchestrator_share_one_contract`
- [tests/test_followup_generate_e2e.py](../../../../../../tests/test_followup_generate_e2e.py) — direct import
  - `test_a_miss_with_two_rivals_generates_one_pinned_probe`
- [tests/test_pfc_unassessed_readers.py](../../../../../../tests/test_pfc_unassessed_readers.py) — direct import
  - `test_a_pinned_probe_declines_to_classify_an_unassessed_criterion`
- [tests/test_probe_records.py](../../../../../../tests/test_probe_records.py) — direct import
  - `test_noncausal_or_already_read_answer_is_silent`
- [tests/test_why_cases.py](../../../../../../tests/test_why_cases.py) — direct import
  - `test_why_wasnt_this_probe_answer_read`

## Modification guidance

- Change causal discrimination policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/causal_discrimination.py](../../../../../../src/learnloop/diagnosis/causal_discrimination.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
