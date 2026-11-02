---
title: "learnloop.instructional.valuation"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/instructional/valuation.py"
source_paths:
  - "src/learnloop/instructional/valuation.py"
source_commit: "60a1a7e9f1aa558dc1ab96646586079235c8a902"
source_commit_timestamp: "2026-10-31T17:49:17-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.instructional"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.instructional.valuation module"
  - "src/learnloop/instructional/valuation.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-instructional"
---

# `learnloop.instructional.valuation`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.instructional.valuation` exists within [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] to own the behavior summarized by its module contract: Valuing candidates by value of information (spec_source_practice_and_probes_v1 §8.2-§8.3).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/instructional/valuation.py](../../../../../../src/learnloop/instructional/valuation.py) |
| Source lines | 1203 |
| Owning package | [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `60a1a7e9f1aa558dc1ab96646586079235c8a902` |
| Commit timestamp | `2026-10-31T17:49:17-04:00` |

## Public API

- `class HypothesisRef` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 77)
  - `parse(cls, value: Mapping[str, Any] | 'HypothesisRef') -> 'HypothesisRef'` (line 82; public)
- `class PendingDecision` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 93)
- `class ValuationProblem` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 101) — One hypothesis space: mutually exclusive slots under one prior.
  - `describe(self) -> dict[str, Any]` (line 115; public)
- `class CandidateInput` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 126)
  - `evaluable(self) -> bool` (line 150; public)
- `lo_problem(vault: LoadedVault, repository: Repository, lo_id: str, refs: Sequence[HypothesisRef]=()) -> tuple[ValuationProblem | None, list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 169) — The LO's hypothesis set: mastered, unfamiliar and one slot per active belief on the LO and its confusable neighbours (``build_hypothesis_set``).
- `facet_problem(vault: LoadedVault, repository: Repository, lo_id: str, facet_id: str, refs: Sequence[HypothesisRef]=()) -> tuple[ValuationProblem | None, list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 194)
- `episode_problem(vault: LoadedVault, repository: Repository, episode_id: str, refs: Sequence[HypothesisRef]=()) -> tuple[ValuationProblem | None, list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 207)
- `causal_problem(vault: LoadedVault, repository: Repository, hypothesis_set_id: str, refs: Sequence[HypothesisRef]=(), *, repair_class_by_hypothesis: Mapping[str, str | None] | None=None) -> tuple[ValuationProblem | None, list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 232) — A causal factor's concrete hypotheses (``H_OTHER`` excluded explicitly, its mass recorded).
- `recent_assisted_success(vault: LoadedVault, repository: Repository, lo_id: str, facet_id: str | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 262) — The LO's (or the facet's) most recent successful attempt, when it was assisted and no unaided success has followed it; None otherwise.
- `formative_anchor(vault: LoadedVault, repository: Repository, lo_id: str, facet_id: str | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 308) — The item a formative-only retention question's prior is read on (spec_reader_workbench_v1 §9.3 item 1, restored RS3; Codex review F9): the LO's (facet's) most recently attempted item, else its first active item carrying the facet, by id.
- `retention_problem(vault: LoadedVault, repository: Repository, lo_id: str, facet_id: str | None=None, *, predictor: Any | None=None, formative: bool=False) -> tuple[ValuationProblem | None, list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 335) — Does a recently assisted success hold unaided?
- `named_gaps_available(repository: Repository) -> bool` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 402) — The learner-text gaps branch, feature-detected: its card reader and its table (§8.2).
- `named_gap_target(repository: Repository, gap_id: str) -> tuple[HypothesisRef | None, str | None]` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 412) — A named gap's target as the hypothesis it names, through ``named_gaps_for_card()`` (the router card's typed events), or why not.
- `resolve_hypothesis_refs(vault: LoadedVault, repository: Repository, refs: Sequence[Mapping[str, Any] | HypothesisRef]) -> tuple[list[HypothesisRef], list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 445) — Parse refs under the one contract and map each named gap to its target.
- `open_hypotheses(vault: LoadedVault, repository: Repository, *, facet_ids: Sequence[str]=(), learning_object_ids: Sequence[str]=(), refs: Sequence[Mapping[str, Any] | HypothesisRef]=(), intent: str='discriminate', repair_class_by_hypothesis: Mapping[str, str | None] | None=None) -> tuple[list[ValuationProblem], list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 480) — The rival-hypothesis spaces a request bears on, one problem each.
- `check_tables(problem: ValuationProblem, members: Sequence[Mapping[str, Mapping[str, float]]]) -> None` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 572) — Each row sums to 1 over the alphabet and every prior slot has a row (§8.3.1).
- `episode_instruments(vault: LoadedVault, repository: Repository, problem: ValuationProblem) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 600) — The open episode's compiled instruments on its pinned channel, read once per problem: ``{"channel", "by_item", "reason"}``.
- `item_input(vault: LoadedVault, repository: Repository, problem: ValuationProblem, item: PracticeItem, *, estimator: Callable[..., Any] | None=None, channel: Any | None=None) -> CandidateInput` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 667)
- `retention_members(channel: Any, ref: str) -> tuple[tuple[dict[str, dict[str, float]], ...], str]` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 758) — Declared retention rows composed with the pinned grader channel, as the robust probe path composes card rows: ``holds_unaided`` -> the correct class, ``not_unaided`` -> its incorrect classes.
- `discount_members(members: Sequence[Mapping[str, Mapping[str, float]]], prior: Mapping[str, float], discount: float) -> tuple[dict[str, dict[str, float]], ...]` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 786) — Each member's ``P(E|H)`` with an observation worth ``discount`` of an independent one: ``d * P(E|H) + (1 - d) * P(E)``, where ``P(E)`` is the member's prior predictive (the same for every hypothesis, so that share carries no information).
- `exercise_input(problem: ValuationProblem, exercise: Mapping[str, Any], screen: Mapping[str, Any] | None, *, estimator: Callable[..., Any] | None=None) -> CandidateInput` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 809) — An unimported exercise: a complete screen is a noiseless partition (a bound); anything else is structural (§8.4).
- `entropy_nats(prior: Mapping[str, float]) -> float` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 847)
- `value_problem(problem: ValuationProblem, inputs: Sequence[CandidateInput], *, caller_kind: str='learner', system_initiated: bool=False, already_chosen: Sequence[str]=()) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 876) — Groups, verdicts and stops for one hypothesis space.
- `rank_listener(listener: Callable[..., Any]) -> Iterator[None]` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 1050) — Call ``listener(problem=, result=, candidates=, loss_table=)`` for each ``rank_feasible`` decision a valuation in this context makes.
- `value_candidates(problems: Sequence[ValuationProblem], inputs_by_problem: Mapping[str, Sequence[CandidateInput]], *, caller_kind: str='learner', system_initiated: bool=False, unavailable: Sequence[Mapping[str, Any]]=(), already_chosen: Sequence[str]=()) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 1138) — The valuation receipt: one section per problem, nothing summed across them.
- `refuse_mixed_decision(problems: Sequence[ValuationProblem], action_by_slot: Mapping[str, Any]) -> None` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 1163) — A pending decision belongs to one space; one naming slots of several is refused.

### Module constants

- `VALUATION_VERSION` ([src/learnloop/instructional/valuation.py](../../../../../../src/learnloop/instructional/valuation.py), line 57)
- `HYPOTHESIS_KINDS` ([src/learnloop/instructional/valuation.py](../../../../../../src/learnloop/instructional/valuation.py), line 60)
- `HYPOTHESIS_ALIASES` ([src/learnloop/instructional/valuation.py](../../../../../../src/learnloop/instructional/valuation.py), line 63)
- `REFERENCE_KINDS` ([src/learnloop/instructional/valuation.py](../../../../../../src/learnloop/instructional/valuation.py), line 65)
- `LICENSES_SYSTEM_CHECK` ([src/learnloop/instructional/valuation.py](../../../../../../src/learnloop/instructional/valuation.py), line 67)
- `VALUED_REGIMES` ([src/learnloop/instructional/valuation.py](../../../../../../src/learnloop/instructional/valuation.py), line 68)
- `SCALE_LABEL` ([src/learnloop/instructional/valuation.py](../../../../../../src/learnloop/instructional/valuation.py), line 69)
- `BRANCH_MASS_FLOOR` ([src/learnloop/instructional/valuation.py](../../../../../../src/learnloop/instructional/valuation.py), line 72)
- `MAX_BRANCHES` ([src/learnloop/instructional/valuation.py](../../../../../../src/learnloop/instructional/valuation.py), line 73)
- `NAMED_GAPS_MODULE` ([src/learnloop/instructional/valuation.py](../../../../../../src/learnloop/instructional/valuation.py), line 387)
- `_RANK_LISTENER` ([src/learnloop/instructional/valuation.py](../../../../../../src/learnloop/instructional/valuation.py), line 1046)

### Explicit exports

`__all__` declares:

- `CandidateInput`
- `HYPOTHESIS_ALIASES`
- `HYPOTHESIS_KINDS`
- `HypothesisRef`
- `NAMED_GAPS_MODULE`
- `REFERENCE_KINDS`
- `LICENSES_SYSTEM_CHECK`
- `PendingDecision`
- `SCALE_LABEL`
- `VALUATION_VERSION`
- `ValuationProblem`
- `causal_problem`
- `check_tables`
- `discount_members`
- `entropy_nats`
- `episode_instruments`
- `episode_problem`
- `exercise_input`
- `facet_problem`
- `formative_anchor`
- `item_input`
- `lo_problem`
- `named_gap_target`
- `named_gaps_available`
- `open_hypotheses`
- `refuse_mixed_decision`
- `resolve_hypothesis_refs`
- `retention_members`
- `retention_problem`
- `value_candidates`
- `value_problem`

## Internal implementation anchors

- `_hash(value: Any) -> str` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 157)
- `_normalized(prior: Mapping[str, float], slots: Sequence[str]) -> dict[str, float]` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 161)
- `_named_gaps_reader() -> Callable[..., Any] | None` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 390) — ``named_gaps_for_card`` from the learner-text gaps branch, once merged.
- `_facet_los(vault: LoadedVault, facet_id: str) -> list[str]` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 472)
- `_outcome_key(outcome: Any) -> str` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 555)
- `_normalize_rows(table: Mapping[str, Mapping[Any, float]]) -> dict[str, dict[str, float]]` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 561)
- `_item_point_members(point: dict[str, dict[str, float]]) -> tuple[dict[str, dict[str, float]], ...]` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 584) — Member 0 plus ``evsi.stress_matrices``' ±0.15 perturbations: a robustness check, not a calibration.
- `_minutes(estimator: Callable[..., Any] | None, ref: str, mode: str | None, expected: float | None) -> tuple[float, dict[str, Any]]` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 590)
- `_instrument_input(problem: ValuationProblem, item: PracticeItem, channel: Any, entry: Any) -> CandidateInput` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 640) — A compiled probe instrument valued as ``probe_robust.robust_selection`` values it: ``instrument_ensemble`` on the episode's pinned channel, seeded from the decision context of the posterior this selection values under (the problem's prior: concrete slots, ``H_OTHER`` excluded an…
- `_ensemble(candidate: CandidateInput, problem: ValuationProblem) -> RC.Ensemble` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 840)
- `_branches(picks: Sequence[CandidateInput], prior: Mapping[str, float]) -> list[tuple[float, dict[str, float]]]` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 851) — The predicted-outcome branches of the picks so far, on each pick's member 0.
- `_conditional_series(candidate: CandidateInput, branches: Sequence[tuple[float, Mapping[str, float]]]) -> list[float]` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 871)
- `_member0(candidate: CandidateInput) -> dict[str, dict[str, float]] | None` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 1021) — The point-estimate ``P(E|H)`` table, persisted so S5 can replay the posterior movement an observation implies (§11.4 item 2; re-review F11).
- `_predicted(candidate: CandidateInput, prior: Mapping[str, float] | None) -> dict[str, float] | None` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 1031) — P(E) = sum_H P(H) P(E|H) on member 0 (S5 logs it beside the observed bucket).
- `_decision_mode(problem: ValuationProblem, inputs: Sequence[CandidateInput], report: dict[str, Any], by_ref: Mapping[str, CandidateInput], *, system_initiated: bool, already_chosen: Sequence[str]=()) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 1061)
- `_decision_actions(candidate: CandidateInput, problem: ValuationProblem, loss_table: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 1124)
- `_evpi(problem: ValuationProblem, loss_table: Any) -> float` ([source](../../../../../../src/learnloop/instructional/valuation.py), line 1132)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/instructional/discriminating|learnloop.instructional.discriminating]] — imports `discount_members`, `exercise_input`, `item_input`, `open_hypotheses`, `value_candidates`; statically calls `discount_members`, `exercise_input`, `item_input`, `open_hypotheses`, `value_candidates`
- [[Reference/Modules/learnloop/instructional/needs|learnloop.instructional.needs]] — imports `rank_listener`; statically calls `rank_listener`
- [[Reference/Modules/learnloop/instructional/practice|learnloop.instructional.practice]] — imports `resolve_hypothesis_refs`; statically calls `resolve_hypothesis_refs`
- [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]] — imports `SCALE_LABEL`, `VALUATION_VERSION`, `recent_assisted_success`; statically calls `recent_assisted_success`
- [[Reference/Modules/learnloop/instructional/sources|learnloop.instructional.sources]] — imports `named_gap_target`; statically calls `named_gap_target`
- [[Reference/Modules/learnloop/instructional/tools|learnloop.instructional.tools]] — imports `HYPOTHESIS_ALIASES`, `REFERENCE_KINDS`, `named_gap_target`; statically calls `named_gap_target`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/causal_diagnostic_selector|learnloop.diagnosis.causal_diagnostic_selector]] — imports `build_causal_loss_table`, `likelihood_regime_for_candidate`; calls `build_causal_loss_table`, `likelihood_regime_for_candidate`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `eligible_instruments`, `episode_hypothesis_set`, `episode_posterior`; calls `eligible_instruments`, `episode_hypothesis_set`, `episode_posterior`
- [[Reference/Modules/learnloop/diagnosis/probe_hypotheses|learnloop.diagnosis.probe_hypotheses]] — imports `H_OTHER`
- [[Reference/Modules/learnloop/diagnosis/probe_robust|learnloop.diagnosis.probe_robust]] — imports `instrument_ensemble`, `load_pinned_channel`, `use_robust_probe`; calls `instrument_ensemble`, `load_pinned_channel`, `use_robust_probe`
- [[Reference/Modules/learnloop/diagnosis/probes|learnloop.diagnosis.probes]] — imports `Hypothesis`, `HypothesisSet`, `build_hypothesis_set`, `conditional_distribution`, `facet_conditional_distribution`, `item_registry_discrimination`, `resolve_item_irt`; calls `build_hypothesis_set`, `conditional_distribution`, `facet_conditional_distribution`, `item_registry_discrimination`, `resolve_item_irt`
- [[Reference/Modules/learnloop/diagnosis/robust_composition|learnloop.diagnosis.robust_composition]] — imports `module`; calls `Ensemble`, `build_ensemble`, `evaluate_selection`, `evaluate_selection_credible_sets`, `evaluate_series_selection`, `expected_information_gain`, `observed_update`, `robust_quantile`
- [[Reference/Modules/learnloop/held_grades|learnloop.held_grades]] — imports `held_for_review_attempts`; calls `held_for_review_attempts`
- [[Reference/Modules/learnloop/placement/predictor|learnloop.placement.predictor]] — imports `PredictorNotActivatable`, `active_predictor`; calls `active_predictor`
- [[Reference/Modules/learnloop/practice_index/catalog|learnloop.practice_index.catalog]] — imports `item_facets`; calls `item_facets`
- [[Reference/Modules/learnloop/scheduling/evsi|learnloop.scheduling.evsi]] — imports `module`; calls `DiagnosticCandidate`, `EVSIInputError`, `evsi_for_conditionals`, `rank_feasible`, `shared_optimal_action`, `stress_matrices`
- [[Reference/Modules/learnloop/substrate/intervention_outcomes|learnloop.substrate.intervention_outcomes]] — imports `SUCCESS_CORRECTNESS`, `is_assisted`; calls `is_assisted`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `contextvars`, `dataclasses`, `importlib`, `json`, `logging`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/instructional/discriminating|learnloop.instructional.discriminating]], [[Reference/Modules/learnloop/instructional/needs|learnloop.instructional.needs]], [[Reference/Modules/learnloop/instructional/practice|learnloop.instructional.practice]], [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]], [[Reference/Modules/learnloop/instructional/sources|learnloop.instructional.sources]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_discriminating_search.py](../../../../../../tests/test_discriminating_search.py) — direct import
  - `test_causal_space_excludes_h_other_explicitly`
  - `test_item_tables_are_normalized_and_labelled`
  - `test_open_hypotheses_one_problem_per_space_with_typed_misses`
  - `test_retention_is_posed_only_after_an_assisted_only_success_with_the_active_predictor`
  - `test_retention_needs_a_recent_assisted_success`
- [tests/test_hypothesis_reference_contract.py](../../../../../../tests/test_hypothesis_reference_contract.py) — direct import
  - `test_every_published_kind_parses_under_the_adapters_contract`
  - `test_named_gaps_map_to_their_targets_and_reversals_name_nothing`
- [tests/test_reader_followups.py](../../../../../../tests/test_reader_followups.py) — direct import
- [tests/test_reader_followups_review.py](../../../../../../tests/test_reader_followups_review.py) — direct import
  - `test_f12_a_familiar_sibling_counts_for_less_than_its_undiscounted_value`
- [tests/test_reader_followups_round3.py](../../../../../../tests/test_reader_followups_round3.py) — direct import
  - `test_a_live_check_seeds_the_greedy_selection_and_is_never_a_new_check`
- [tests/test_sources_merge_composition.py](../../../../../../tests/test_sources_merge_composition.py) — direct import
  - `test_a_decision_mode_valuation_records_its_forecast_when_logging_is_on`
  - `test_a_held_success_neither_poses_nor_suppresses_retention`
- [tests/test_value_candidates.py](../../../../../../tests/test_value_candidates.py) — direct import
  - `test_a_decision_spanning_spaces_is_refused`
  - `test_a_system_initiated_check_needs_a_licensing_regime`
  - `test_an_instrument_only_request_matches_robust_selection`
  - `test_below_the_robust_cutover_instruments_are_ordinary_items`
  - `test_decision_mode_ranks_by_evsi_and_names_the_action`
  - `test_greedy_conditional_valuation_drops_a_redundant_second_check`
  - `test_identical_inputs_give_identical_receipts`
  - `test_learner_initiated_results_have_three_groups`
  - `test_mixed_regimes_in_one_learner_problem_use_credible_sets_without_index_errors`
  - `test_no_count_cap_three_informative_checks_all_return`
  - `test_stop_when_nothing_clears_the_minutes_cost`
  - `test_two_spaces_are_two_problems_with_their_own_verdicts`

## Modification guidance

- Make changes here when the responsibility remains valuation within learnloop.instructional; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/instructional/valuation.py](../../../../../../src/learnloop/instructional/valuation.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
