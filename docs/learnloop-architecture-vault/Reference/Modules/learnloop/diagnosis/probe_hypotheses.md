---
title: "learnloop.diagnosis.probe_hypotheses"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/probe_hypotheses.py"
source_paths:
  - "src/learnloop/diagnosis/probe_hypotheses.py"
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
  - "learnloop.diagnosis.probe_hypotheses module"
  - "src/learnloop/diagnosis/probe_hypotheses.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.probe_hypotheses`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.probe_hypotheses` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Cold-start hypothesis templates for diagnostic episodes.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/probe_hypotheses.py](../../../../../../src/learnloop/diagnosis/probe_hypotheses.py) |
| Source lines | 273 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `triage_reason_for_label(label: str) -> str` ([source](../../../../../../src/learnloop/diagnosis/probe_hypotheses.py), line 58)
- `confused_concept(label: str) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/probe_hypotheses.py), line 64)
- `class ItemObservationContext` ([source](../../../../../../src/learnloop/diagnosis/probe_hypotheses.py), line 71) — Item-side flags that decide which latent gaps a generic item elicits.
- `item_observation_context(item: PracticeItem) -> ItemObservationContext` ([source](../../../../../../src/learnloop/diagnosis/probe_hypotheses.py), line 84)
- `generic_bucket_marginals(label: str, context: ItemObservationContext, *, item_a: float=1.0, item_b: float=0.0, irt: ProbeIRTConfig | None=None) -> dict[str, float]` ([source](../../../../../../src/learnloop/diagnosis/probe_hypotheses.py), line 94) — ``P(score_bucket | hypothesis)`` for a generic (card-less) item.
- `build_episode_hypothesis_set(vault: LoadedVault, repository: Repository, learning_object_id: str, *, clock: Clock | None=None) -> HypothesisSet` ([source](../../../../../../src/learnloop/diagnosis/probe_hypotheses.py), line 142) — Instantiate the locked cold-start set for one episode (§6.1/§6.2).
- `strong_prior_claim(vault: LoadedVault, repository: Repository, learning_object_id: str) -> bool` ([source](../../../../../../src/learnloop/diagnosis/probe_hypotheses.py), line 260) — Whether the learner made a strong covering claim (§11 fast-path input).

### Module constants

- `H_UNFAMILIAR` ([src/learnloop/diagnosis/probe_hypotheses.py](../../../../../../src/learnloop/diagnosis/probe_hypotheses.py), line 31)
- `H_SURFACE_ONLY` ([src/learnloop/diagnosis/probe_hypotheses.py](../../../../../../src/learnloop/diagnosis/probe_hypotheses.py), line 32)
- `H_RECALL_WITHOUT_MECHANISM` ([src/learnloop/diagnosis/probe_hypotheses.py](../../../../../../src/learnloop/diagnosis/probe_hypotheses.py), line 33)
- `H_PROCEDURE_WITHOUT_SELECTION` ([src/learnloop/diagnosis/probe_hypotheses.py](../../../../../../src/learnloop/diagnosis/probe_hypotheses.py), line 34)
- `H_SCHEMA_WITHOUT_TRANSFER` ([src/learnloop/diagnosis/probe_hypotheses.py](../../../../../../src/learnloop/diagnosis/probe_hypotheses.py), line 35)
- `H_ROBUST` ([src/learnloop/diagnosis/probe_hypotheses.py](../../../../../../src/learnloop/diagnosis/probe_hypotheses.py), line 36)
- `H_OTHER` ([src/learnloop/diagnosis/probe_hypotheses.py](../../../../../../src/learnloop/diagnosis/probe_hypotheses.py), line 37)
- `CONFUSES_PREFIX` ([src/learnloop/diagnosis/probe_hypotheses.py](../../../../../../src/learnloop/diagnosis/probe_hypotheses.py), line 39)
- `MISCONCEPTION_PREFIX` ([src/learnloop/diagnosis/probe_hypotheses.py](../../../../../../src/learnloop/diagnosis/probe_hypotheses.py), line 40)
- `TRIAGE_REASON_BY_HYPOTHESIS` ([src/learnloop/diagnosis/probe_hypotheses.py](../../../../../../src/learnloop/diagnosis/probe_hypotheses.py), line 47)

## Internal implementation anchors

- `class _Candidate` ([source](../../../../../../src/learnloop/diagnosis/probe_hypotheses.py), line 137)
- `_confusable_neighbors(vault: LoadedVault, learning_object) -> list[str]` ([source](../../../../../../src/learnloop/diagnosis/probe_hypotheses.py), line 246) — Confusable concept ids from the LO's authored list plus concept edges.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/curriculum/confusable_concepts|learnloop.curriculum.confusable_concepts]] — imports `confused_concept`; statically calls `confused_concept`
- [[Reference/Modules/learnloop/diagnosis/causal_diagnostic_selector|learnloop.diagnosis.causal_diagnostic_selector]] — imports `H_OTHER`
- [[Reference/Modules/learnloop/diagnosis/causal_probe_coherence|learnloop.diagnosis.causal_probe_coherence]] — imports `H_OTHER`
- [[Reference/Modules/learnloop/diagnosis/causal_selection_audit|learnloop.diagnosis.causal_selection_audit]] — imports `H_OTHER`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `H_OTHER`, `H_UNFAMILIAR`
- [[Reference/Modules/learnloop/diagnosis/probe_blocks|learnloop.diagnosis.probe_blocks]] — imports `H_OTHER`
- [[Reference/Modules/learnloop/diagnosis/probe_coverage|learnloop.diagnosis.probe_coverage]] — imports `build_episode_hypothesis_set`; statically calls `build_episode_hypothesis_set`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `H_OTHER`, `build_episode_hypothesis_set`, `generic_bucket_marginals`, `item_observation_context`, `strong_prior_claim`, `triage_reason_for_label`; statically calls `build_episode_hypothesis_set`, `generic_bucket_marginals`, `item_observation_context`, `strong_prior_claim`, `triage_reason_for_label`
- [[Reference/Modules/learnloop/diagnosis/probe_families|learnloop.diagnosis.probe_families]] — imports `CONFUSES_PREFIX`, `MISCONCEPTION_PREFIX`
- [[Reference/Modules/learnloop/diagnosis/probe_targeting|learnloop.diagnosis.probe_targeting]] — imports `triage_reason_for_label`; statically calls `triage_reason_for_label`
- [[Reference/Modules/learnloop/sim/diagnostic_validation|learnloop.sim.diagnostic_validation]] — imports `CONFUSES_PREFIX`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `parse_utc`, `utc_now_iso`; calls `SystemClock`, `utc_now_iso`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `ProbeIRTConfig`; calls `ProbeIRTConfig`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/probe_families|learnloop.diagnosis.probe_families]] — imports `knowledge_type_tokens`; calls `knowledge_type_tokens`
- [[Reference/Modules/learnloop/diagnosis/probes|learnloop.diagnosis.probes]] — imports `Hypothesis`, `HypothesisSet`, `_decay`, `_graded_marginals`; calls `Hypothesis`, `HypothesisSet`, `_decay`, `_graded_marginals`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `covering_learner_claim`, `initial_mastery_state_for_learning_object`, `sigmoid`; calls `covering_learner_claim`, `initial_mastery_state_for_learning_object`, `sigmoid`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/curriculum/confusable_concepts|learnloop.curriculum.confusable_concepts]], [[Reference/Modules/learnloop/diagnosis/causal_diagnostic_selector|learnloop.diagnosis.causal_diagnostic_selector]], [[Reference/Modules/learnloop/diagnosis/causal_probe_coherence|learnloop.diagnosis.causal_probe_coherence]], [[Reference/Modules/learnloop/diagnosis/causal_selection_audit|learnloop.diagnosis.causal_selection_audit]], [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] and 6 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_causal_p2_acceptance.py](../../../../../../tests/test_causal_p2_acceptance.py) — direct import
  - `test_causal_disambiguation_end_to_end_acceptance`
  - `test_no_bundle_matched_supports_the_open_set_but_closes_nothing`
  - `test_one_authored_cause_is_unioned_with_the_synthesized_arms`
- [tests/test_causal_repair_mapping_p2.py](../../../../../../tests/test_causal_repair_mapping_p2.py) — direct import
  - `test_open_set_cause_id_and_probe_label_are_distinct_namespaces`
- [tests/test_cold_start_revision.py](../../../../../../tests/test_cold_start_revision.py) — direct import
  - `test_template_labels_route`
- [tests/test_km2_write_path.py](../../../../../../tests/test_km2_write_path.py) — direct import
  - `test_open_set_arm_survives_apply_attempt_into_the_probe_path`
- [tests/test_probe_block_end.py](../../../../../../tests/test_probe_block_end.py) — direct import
  - `test_block_end_payload_carries_open_set_evaluation`
  - `test_open_set_trigger_fires_at_threshold_with_dedup`
- [tests/test_probe_episodes.py](../../../../../../tests/test_probe_episodes.py) — direct import
  - `test_episode_entry_locks_actionable_set_with_open_set_mass`
  - `test_unmatched_systematic_signature_raises_open_set_probability`
- [tests/test_probe_longform_families.py](../../../../../../tests/test_probe_longform_families.py) — direct import
  - `test_derivation_separates_procedure_without_selection`

## Modification guidance

- Change probe hypotheses policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/probe_hypotheses.py](../../../../../../src/learnloop/diagnosis/probe_hypotheses.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
