---
title: "learnloop.diagnosis.split.context"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/split/context.py"
source_paths:
  - "src/learnloop/diagnosis/split/context.py"
source_commit: "e6d3c96710df3cbdb228f505cada139d72f82cda"
source_commit_timestamp: "2026-11-01T19:56:33-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis.split"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.split.context module"
  - "src/learnloop/diagnosis/split/context.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-split"
---

# `learnloop.diagnosis.split.context`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.split.context` exists within [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] to own the behavior summarized by its module contract: Deterministic ``DiagnosisContext`` assembly (Slice 1 §5.2).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/split/context.py](../../../../../../../src/learnloop/diagnosis/split/context.py) |
| Source lines | 1007 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `e6d3c96710df3cbdb228f505cada139d72f82cda` |
| Commit timestamp | `2026-11-01T19:56:33-05:00` |

## Public API

- `estimate_tokens(text: str) -> int` ([source](../../../../../../../src/learnloop/diagnosis/split/context.py), line 81) — Conservative token estimate: UTF-8 bytes / 4, rounded up.
- `canonical_json(value: Any) -> str` ([source](../../../../../../../src/learnloop/diagnosis/split/context.py), line 87)
- `class CurrentAttempt` ([source](../../../../../../../src/learnloop/diagnosis/split/context.py), line 92) — The attempt being diagnosed, with its blind grade (§5.2 "current").
  - `ref(self) -> AttemptRef` (line 121; public)
  - `target_facets(self) -> frozenset[str]` (line 124; public) — The blind grade's facet targets, else the item's own facets.
  - `render(self) -> dict[str, Any]` (line 135; public)
  - `_render(self, grade: Mapping[str, Any]) -> dict[str, Any]` (line 163; internal)
- `current_attempt_from(vault: LoadedVault, item: PracticeItem, *, attempt_id: str, completed_at: str, learner_answer_md: str, blind_grade: Mapping[str, Any], contract: Mapping[str, Any] | None=None, workbench_trace: Mapping[str, Any] | None=None, confidence: Mapping[str, Any] | None=None, figure_trace: Mapping[str, Any] | None=None) -> CurrentAttempt` ([source](../../../../../../../src/learnloop/diagnosis/split/context.py), line 217) — The attempt being diagnosed.
- `class KnownIds` ([source](../../../../../../../src/learnloop/diagnosis/split/context.py), line 271) — The closed world the validators check model-cited ids against (§5.4).
  - `union(self, other: 'KnownIds') -> 'KnownIds'` (line 281; public)
- `class RetrievalMatch` ([source](../../../../../../../src/learnloop/diagnosis/split/context.py), line 293)
- `class RetrievalResult` ([source](../../../../../../../src/learnloop/diagnosis/split/context.py), line 300)
- `class RegistryNeighbor` ([source](../../../../../../../src/learnloop/diagnosis/split/context.py), line 308)
- `class RegistryShortlist` ([source](../../../../../../../src/learnloop/diagnosis/split/context.py), line 315)
- `registry_key(record: RegistryRecord) -> str` ([source](../../../../../../../src/learnloop/diagnosis/split/context.py), line 322) — A registry record's id in the ``misconception/statement`` index.
- `class RegistryRetriever(Protocol)` ([source](../../../../../../../src/learnloop/diagnosis/split/context.py), line 328) — kNN over the whole vault registry (S1.4a shortlist, §5.2).
  - `registry_knn(self, current: 'CurrentAttempt', records: Sequence[RegistryRecord], *, limit: int) -> RegistryShortlist` (line 331; public)
- `class HistoryRetriever(Protocol)` ([source](../../../../../../../src/learnloop/diagnosis/split/context.py), line 341) — kNN over prior failures for the hybrid mode (§9.4).
  - `knn(self, current: CurrentAttempt, candidates: Sequence[HistoryAttempt], *, limit: int) -> RetrievalResult` (line 344; public)
- `class AssembledContext` ([source](../../../../../../../src/learnloop/diagnosis/split/context.py), line 355) — A rendered context plus its audit receipt and closed-world ids.
  - `rendered(self) -> str` (line 371; public)
- `render_context(blocks: Mapping[str, Any], current: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/diagnosis/split/context.py), line 375) — Byte-stable rendering: stable blocks in fixed order, current attempt last.
- `assemble_diagnosis_context(vault: LoadedVault, store: HistoryStore, current: CurrentAttempt, settings: DiagnosisSettings, *, mode: HistoryMode | None=None, retriever: HistoryRetriever | None=None, snapshot_manifest: Mapping[str, Any] | None=None, token_budget: int | None=None, registry_retriever: RegistryRetriever | None=None, prior_analysis: Any=None) -> AssembledContext` ([source](../../../../../../../src/learnloop/diagnosis/split/context.py), line 662) — Assemble one context deterministically.
- `history_attempt_tokens(attempt: HistoryAttempt, neighborhood: Neighborhood, *, with_answer: bool) -> int` ([source](../../../../../../../src/learnloop/diagnosis/split/context.py), line 949) — Estimated tokens one attempt adds to a rendered history block.
- `stable_prefix(rendered: str) -> str` ([source](../../../../../../../src/learnloop/diagnosis/split/context.py), line 955) — Everything before the current attempt.
- `cacheable_prefix(blocks: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/diagnosis/split/context.py), line 963) — The bytes a later diagnosis on the same LO can share with this one.
- `facets_overlap(left: Iterable[str], right: Iterable[str]) -> bool` ([source](../../../../../../../src/learnloop/diagnosis/split/context.py), line 980)

### Module constants

- `CACHEABLE_BLOCKS` ([src/learnloop/diagnosis/split/context.py](../../../../../../../src/learnloop/diagnosis/split/context.py), line 65)
- `STABLE_BLOCKS` ([src/learnloop/diagnosis/split/context.py](../../../../../../../src/learnloop/diagnosis/split/context.py), line 72)
- `CURRENT_BLOCK` ([src/learnloop/diagnosis/split/context.py](../../../../../../../src/learnloop/diagnosis/split/context.py), line 78)

### Explicit exports

`__all__` declares:

- `AssembledContext`
- `CACHEABLE_BLOCKS`
- `CURRENT_BLOCK`
- `CurrentAttempt`
- `HistoryRetriever`
- `KnownIds`
- `RegistryNeighbor`
- `RegistryRetriever`
- `RegistryShortlist`
- `RetrievalMatch`
- `RetrievalResult`
- `STABLE_BLOCKS`
- `assemble_diagnosis_context`
- `cacheable_prefix`
- `canonical_json`
- `current_attempt_from`
- `estimate_tokens`
- `facets_overlap`
- `history_attempt_tokens`
- `registry_key`
- `render_context`
- `stable_prefix`

## Internal implementation anchors

- `_status_for(attempts: Sequence[HistoryAttempt]) -> str` ([source](../../../../../../../src/learnloop/diagnosis/split/context.py), line 387)
- `_neighborhood_block(vault: LoadedVault, neighborhood: Neighborhood, prior: Sequence[HistoryAttempt]) -> tuple[dict[str, Any], set[str], list[dict[str, Any]]]` ([source](../../../../../../../src/learnloop/diagnosis/split/context.py), line 395)
- `_render_attempt(attempt: HistoryAttempt, neighborhood: Neighborhood, *, with_answer: bool, prior: Mapping[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/split/context.py), line 435)
- `_render_hypothesis(record: HypothesisRecord) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/split/context.py), line 486)
- `_render_registry(record: RegistryRecord) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/split/context.py), line 500)
- `_render_repair(record: RepairRecord) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/split/context.py), line 512)
- `_exact_failures(prior: Sequence[HistoryAttempt], targets: frozenset[str], *, current_attempt_id: str) -> list[HistoryAttempt]` ([source](../../../../../../../src/learnloop/diagnosis/split/context.py), line 522) — Non-pass, facet-overlapping, any surface family; most recent first.
- `_exact_successes(prior: Sequence[HistoryAttempt], targets: frozenset[str], *, current_attempt_id: str) -> list[HistoryAttempt]` ([source](../../../../../../../src/learnloop/diagnosis/split/context.py), line 539) — Prior passes on the same facets, cold and unassisted first, recent first.
- `_rrf(exact: Sequence[HistoryAttempt], knn: RetrievalResult, *, k: int, keep: int, by_id: Mapping[str, HistoryAttempt]) -> tuple[list[HistoryAttempt], list[dict[str, Any]]]` ([source](../../../../../../../src/learnloop/diagnosis/split/context.py), line 557)
- `_truncate_oldest(attempts: list[HistoryAttempt], drop: int) -> tuple[list[HistoryAttempt], int]` ([source](../../../../../../../src/learnloop/diagnosis/split/context.py), line 592) — Drop ``drop`` of the OLDEST attempts, keeping the block's display order.
- `_registry_shortlist(retriever: RegistryRetriever, store: HistoryStore, current: 'CurrentAttempt', before: AttemptRef, exact: list[RegistryRecord], *, limit: int) -> tuple[list[RegistryRecord], dict[str, Any]]` ([source](../../../../../../../src/learnloop/diagnosis/split/context.py), line 606) — The exact set plus up to ``limit`` kNN-only registry records.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/ai_compare|learnloop.cli.ai_compare]] — imports `assemble_diagnosis_context`; statically calls `assemble_diagnosis_context`
- [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]] — imports `assemble_diagnosis_context`, `current_attempt_from`, `estimate_tokens`, `history_attempt_tokens`; statically calls `assemble_diagnosis_context`, `current_attempt_from`, `estimate_tokens`, `history_attempt_tokens`
- [[Reference/Modules/learnloop/diagnosis/split/contract|learnloop.diagnosis.split.contract]] — imports `AssembledContext`
- [[Reference/Modules/learnloop/diagnosis/split/diagnoser|learnloop.diagnosis.split.diagnoser]] — imports `AssembledContext`, `CurrentAttempt`, `HistoryRetriever`, `RegistryRetriever`, `assemble_diagnosis_context`; statically calls `assemble_diagnosis_context`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `RegistryShortlist`, `assemble_diagnosis_context`; statically calls `RegistryShortlist`, `assemble_diagnosis_context`
- [[Reference/Modules/learnloop/diagnosis/split/live|learnloop.diagnosis.split.live]] — imports `CurrentAttempt`, `current_attempt_from`; statically calls `current_attempt_from`
- [[Reference/Modules/learnloop/diagnosis/split/retrieval|learnloop.diagnosis.split.retrieval]] — imports `CurrentAttempt`, `RegistryNeighbor`, `RegistryShortlist`, `RetrievalMatch`, `RetrievalResult`, `registry_key`; statically calls `RegistryNeighbor`, `RegistryShortlist`, `RetrievalMatch`, `RetrievalResult`, `registry_key`
- [[Reference/Modules/learnloop/diagnosis/split/snapshot|learnloop.diagnosis.split.snapshot]] — imports `KnownIds`; statically calls `KnownIds`
- [[Reference/Modules/learnloop/diagnosis/split/validation|learnloop.diagnosis.split.validation]] — imports `AssembledContext`, `CurrentAttempt`, `KnownIds`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `resolved_rubric`; calls `resolved_rubric`
- [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]] — imports `AttemptRef`, `HistoryAttempt`, `HistoryStore`, `HypothesisRecord`, `Neighborhood`, `RegistryRecord`, `RepairRecord`, `learning_object_neighborhood`; calls `AttemptRef`, `learning_object_neighborhood`
- [[Reference/Modules/learnloop/diagnosis/split/prior_analysis|learnloop.diagnosis.split.prior_analysis]] — imports `NOTE`, `TRACE_UNRECORDED`
- [[Reference/Modules/learnloop/diagnosis/split/provenance|learnloop.diagnosis.split.provenance]] — imports `DiagnosisReads`, `reads_of_context`, `shown_titles`; calls `DiagnosisReads`, `reads_of_context`, `shown_titles`
- [[Reference/Modules/learnloop/diagnosis/split/settings|learnloop.diagnosis.split.settings]] — imports `DIAGNOSIS_CONTEXT_VERSION`, `DiagnosisSettings`, `HistoryMode`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `surface_group_id`; calls `surface_group_id`
- [[Reference/Modules/learnloop/symbolic_view|learnloop.symbolic_view]] — imports `switch_now`, `trace_view`; calls `switch_now`, `trace_view`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`, `learning_object_facet_union`; calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] — imports `answered_prompt`; calls `answered_prompt`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `hashlib`, `json`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/ai_compare|learnloop.cli.ai_compare]], [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]], [[Reference/Modules/learnloop/diagnosis/split/contract|learnloop.diagnosis.split.contract]], [[Reference/Modules/learnloop/diagnosis/split/diagnoser|learnloop.diagnosis.split.diagnoser]], [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] and 4 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_chatgpt_plan_workspace.py](../../../../../../../tests/test_chatgpt_plan_workspace.py) — direct import
- [tests/test_diagnosis_context.py](../../../../../../../tests/test_diagnosis_context.py) — direct import
  - `test_assembly_and_hash_are_deterministic`
  - `test_current_attempt_renders_last_with_its_blind_grade`
  - `test_exact_mode_selects_neighbourhood_failures_and_successes_as_of`
  - `test_legacy_joint_attempts_are_stripped_of_causal_fields`
  - `test_neighbourhood_and_as_of_prerequisite_status`
  - `test_repair_chain_source_is_visible_to_the_diagnoser`
  - `test_truncation_drops_oldest_first_and_discloses`
- [tests/test_diagnosis_contract.py](../../../../../../../tests/test_diagnosis_contract.py) — direct import
- [tests/test_diagnosis_history_modes.py](../../../../../../../tests/test_diagnosis_history_modes.py) — direct import
  - `test_full_budget_truncates_oldest_attempts_before_any_hypothesis`
  - `test_full_includes_every_neighbour_attempt_chronologically`
  - `test_full_stable_prefix_is_shared_by_consecutive_diagnoses_on_one_lo`
  - `test_hybrid_degrades_to_exact_when_embeddings_fail`
  - `test_hybrid_fuses_exact_and_knn_and_records_provenance`
- [tests/test_figures_help.py](../../../../../../../tests/test_figures_help.py) — direct import
  - `test_the_context_hashes_as_before_without_a_figure_trace`
- [tests/test_learner_blindness_relax.py](../../../../../../../tests/test_learner_blindness_relax.py) — direct import
- [tests/test_pfc_unassessed_readers.py](../../../../../../../tests/test_pfc_unassessed_readers.py) — direct import
  - `test_a_later_diagnosis_cannot_cite_an_unassessed_shortfall_as_a_recurrence`
- [tests/test_reader_rw2b_fix15.py](../../../../../../../tests/test_reader_rw2b_fix15.py) — direct import
  - `test_item2_a_switch_off_during_context_assembly_masks_the_rendered_trace`
- [tests/test_teacher_te0_confidence_events.py](../../../../../../../tests/test_teacher_te0_confidence_events.py) — direct import
  - `test_the_diagnosers_history_and_current_attempt_carry_the_events`
- [tests/test_workbench_trace.py](../../../../../../../tests/test_workbench_trace.py) — direct import

## Modification guidance

- Change context policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/split/context.py](../../../../../../../src/learnloop/diagnosis/split/context.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
