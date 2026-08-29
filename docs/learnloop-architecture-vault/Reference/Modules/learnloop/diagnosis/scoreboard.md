---
title: "learnloop.diagnosis.scoreboard"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/scoreboard.py"
source_paths:
  - "src/learnloop/diagnosis/scoreboard.py"
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
  - "learnloop.diagnosis.scoreboard module"
  - "src/learnloop/diagnosis/scoreboard.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.scoreboard`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.scoreboard` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: The §3 B5 scoreboard, assembled (implementation_plan_v1.md items 4.1/4.3/4.4).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/scoreboard.py](../../../../../../src/learnloop/diagnosis/scoreboard.py) |
| Source lines | 1759 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class Metric` ([source](../../../../../../src/learnloop/diagnosis/scoreboard.py), line 120) — One scoreboard row, with the denominator it is a rate over.
  - `__post_init__(self) -> None` (line 140; internal)
  - `available(self) -> bool` (line 154; public)
  - `as_dict(self) -> dict[str, Any]` (line 157; public)
- `class ColdSuccessTrajectory` ([source](../../../../../../src/learnloop/diagnosis/scoreboard.py), line 281) — One learning object's path to its first cold success (or lack of one).
  - `reached(self) -> bool` (line 291; public)
- `cold_success_trajectories(repository: Repository, *, success_correctness: float | None=None) -> list[ColdSuccessTrajectory]` ([source](../../../../../../src/learnloop/diagnosis/scoreboard.py), line 295) — Per learning object: problems served up to the first cold success.
- `cold_success_metrics(repository: Repository, *, success_correctness: float | None=None) -> tuple[Metric, Metric]` ([source](../../../../../../src/learnloop/diagnosis/scoreboard.py), line 369) — `problems_to_cold_success` (B5's PRIMARY) and its minutes companion.
- `harmful_write_rate(repository: Repository) -> Metric` ([source](../../../../../../src/learnloop/diagnosis/scoreboard.py), line 524) — Wrong-facet damage the learner was actually exposed to (B5, target ~0).
- `cells_cleared_per_question(vault: LoadedVault, repository: Repository) -> Metric` ([source](../../../../../../src/learnloop/diagnosis/scoreboard.py), line 659) — Contract cells measured, per question served (Meas §5.7, §0).
- `class CertificationPrefix` ([source](../../../../../../src/learnloop/diagnosis/scoreboard.py), line 769) — The earliest attempt prefix at which one learning object certifies.
  - `regret(self) -> int | None` (line 783; public)
- `certification_prefixes(vault: LoadedVault, repository: Repository, *, budget: int=DEFAULT_REPLAY_BUDGET) -> tuple[list[CertificationPrefix], dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/scoreboard.py), line 853) — Bisect the earliest certifying prefix for every learning object.
- `certification_efficiency_metrics(vault: LoadedVault, repository: Repository, *, replay: bool=False, budget: int=DEFAULT_REPLAY_BUDGET) -> tuple[Metric, Metric]` ([source](../../../../../../src/learnloop/diagnosis/scoreboard.py), line 965) — `questions_to_certification` and `certification_regret` (Meas §5.7).
- `tokens_per_resolved_diagnostic_episode(repository: Repository) -> Metric` ([source](../../../../../../src/learnloop/diagnosis/scoreboard.py), line 1128) — Grading tokens per resolved diagnostic episode (B5; C3's revert criterion).
- `probe_action_change_rate(repository: Repository) -> Metric` ([source](../../../../../../src/learnloop/diagnosis/scoreboard.py), line 1251) — Probes whose outcome changed the selected repair, over probes administered.
- `planted_ground_truth(repository: Repository) -> dict[str, dict[str, Any]] | None` ([source](../../../../../../src/learnloop/diagnosis/scoreboard.py), line 1328) — Licensed B1 labels keyed by attempt, or ``None`` without a license.
- `planted_vs_adjudicated_agreement(repository: Repository) -> Metric` ([source](../../../../../../src/learnloop/diagnosis/scoreboard.py), line 1358) — B4 agreement on the planted/adjudicated overlap.
- `false_certification_rate(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None) -> Metric` ([source](../../../../../../src/learnloop/diagnosis/scoreboard.py), line 1486) — Composed from item 4.2's producer (Meas §5.7).
- `measurement_rank_metric(vault: LoadedVault) -> Metric` ([source](../../../../../../src/learnloop/diagnosis/scoreboard.py), line 1649) — Independent dimensions the item pool can resolve, vs facets declared.
- `scoreboard(vault: LoadedVault, repository: Repository, *, replay: bool=False, replay_budget: int=DEFAULT_REPLAY_BUDGET, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/scoreboard.py), line 1689) — The whole §3 B5 board, in B5's frozen order.

### Module constants

- `SCOREBOARD_VERSION` ([src/learnloop/diagnosis/scoreboard.py](../../../../../../src/learnloop/diagnosis/scoreboard.py), line 66)
- `AVAILABILITY` ([src/learnloop/diagnosis/scoreboard.py](../../../../../../src/learnloop/diagnosis/scoreboard.py), line 87)
- `UNAVAILABLE` ([src/learnloop/diagnosis/scoreboard.py](../../../../../../src/learnloop/diagnosis/scoreboard.py), line 95)
- `B5_ORDER` ([src/learnloop/diagnosis/scoreboard.py](../../../../../../src/learnloop/diagnosis/scoreboard.py), line 100)
- `_NON_PROBLEM_ATTEMPT_TYPES` ([src/learnloop/diagnosis/scoreboard.py](../../../../../../src/learnloop/diagnosis/scoreboard.py), line 277)
- `HARMFUL_WITHDRAWAL_REASONS` ([src/learnloop/diagnosis/scoreboard.py](../../../../../../src/learnloop/diagnosis/scoreboard.py), line 510)
- `HARMFUL_VERDICTS` ([src/learnloop/diagnosis/scoreboard.py](../../../../../../src/learnloop/diagnosis/scoreboard.py), line 519)
- `DEFAULT_REPLAY_BUDGET` ([src/learnloop/diagnosis/scoreboard.py](../../../../../../src/learnloop/diagnosis/scoreboard.py), line 765)
- `_PROBE_NOW_DECISION` ([src/learnloop/diagnosis/scoreboard.py](../../../../../../src/learnloop/diagnosis/scoreboard.py), line 1244)
- `_PROBE_RECEIPT_LIMIT` ([src/learnloop/diagnosis/scoreboard.py](../../../../../../src/learnloop/diagnosis/scoreboard.py), line 1248)
- `_FALSE_CERTIFICATION_PRODUCER` ([src/learnloop/diagnosis/scoreboard.py](../../../../../../src/learnloop/diagnosis/scoreboard.py), line 1470)

## Internal implementation anchors

- `_rate(name: str, *, numerator: float | None, denominator: float | None, unit: str, denominator_label: str, note: str, empty_note: str | None=None, empty_availability: str='no_data', companion_of: str | None=None, detail: Mapping[str, Any] | None=None) -> Metric` ([source](../../../../../../src/learnloop/diagnosis/scoreboard.py), line 173) — Build a ratio metric, refusing to divide by an empty denominator.
- `_unavailable(name: str, *, availability: str, unit: str, denominator_label: str, note: str, numerator: float | None=None, denominator: float | None=None, companion_of: str | None=None, detail: Mapping[str, Any] | None=None) -> Metric` ([source](../../../../../../src/learnloop/diagnosis/scoreboard.py), line 221)
- `_cell_has_evidence(evidence: Sequence[Any], capability: str) -> bool` ([source](../../../../../../src/learnloop/diagnosis/scoreboard.py), line 637) — Any observation at all in this cell — positive or negative.
- `_attempt_boundaries(repository: Repository) -> list[tuple[str, str]]` ([source](../../../../../../src/learnloop/diagnosis/scoreboard.py), line 789) — Every attempt as (created_at, id), chronological — the cutoff axis.
- `_certified_at_cutoff(vault: LoadedVault, source_path: Path, scratch_dir: Path, boundary_iso: str, index: int) -> frozenset[str]` ([source](../../../../../../src/learnloop/diagnosis/scoreboard.py), line 802) — Learning objects the authority certifies given attempts up to `boundary_iso`.
- `_resolve_false_certification_producer() -> Callable[..., Any] | None` ([source](../../../../../../src/learnloop/diagnosis/scoreboard.py), line 1476)
- `_adjudication_metrics(repository: Repository) -> tuple[list[Metric], dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/scoreboard.py), line 1551) — The four metrics the A4 store already produces, composed not recomputed.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `DEFAULT_REPLAY_BUDGET`, `scoreboard`; statically calls `scoreboard`
- [[Reference/Modules/learnloop/content/authoring/laddered_stems|learnloop.content.authoring.laddered_stems]] — imports `Metric`; statically calls `Metric`
- [[Reference/Modules/learnloop/content/authoring/persona_gate|learnloop.content.authoring.persona_gate]] — imports `Metric`; statically calls `Metric`
- [[Reference/Modules/learnloop/diagnosis/contrast_pairs|learnloop.diagnosis.contrast_pairs]] — imports `Metric`; statically calls `Metric`
- [[Reference/Modules/learnloop/diagnosis/discrimination_profiles|learnloop.diagnosis.discrimination_profiles]] — imports `Metric`; statically calls `Metric`
- [[Reference/Modules/learnloop/diagnosis/error_hunt|learnloop.diagnosis.error_hunt]] — imports `Metric`; statically calls `Metric`
- [[Reference/Modules/learnloop_sidecar/handlers/measurement|learnloop_sidecar.handlers.measurement]] — imports `scoreboard`; statically calls `scoreboard`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `FrozenClock`, `parse_utc`; calls `FrozenClock`, `parse_utc`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/causal_activity_policy|learnloop.diagnosis.causal_activity_policy]] — imports `attempt_counts_as_assisted`; calls `attempt_counts_as_assisted`
- [[Reference/Modules/learnloop/diagnosis/causal_probe_coherence|learnloop.diagnosis.causal_probe_coherence]] — imports `resolve_causal_probe_parameters`; calls `resolve_causal_probe_parameters`
- [[Reference/Modules/learnloop/diagnosis/diagnosis_adjudication|learnloop.diagnosis.diagnosis_adjudication]] — imports `FILLED_VERDICTS`, `adjudicated_ground_truth`, `diagnosis_adjudication_scoreboard`; calls `adjudicated_ground_truth`, `diagnosis_adjudication_scoreboard`
- [[Reference/Modules/learnloop/goals/goal_certification|learnloop.goals.goal_certification]] — imports `lo_certification`; calls `lo_certification`
- [[Reference/Modules/learnloop/goals/goal_series|learnloop.goals.goal_series]] — imports `prune_rows`; calls `prune_rows`
- [[Reference/Modules/learnloop/learner/contract_reachability|learnloop.learner.contract_reachability]] — imports `contract_cells`; calls `contract_cells`
- [[Reference/Modules/learnloop/learner/identifiability|learnloop.learner.identifiability]] — imports `build_registry_view`, `measurement_rank`; calls `build_registry_view`, `measurement_rank`
- [[Reference/Modules/learnloop/learner/surfaced_beliefs|learnloop.learner.surfaced_beliefs]] — imports `typed_withdrawal_reason`; calls `typed_withdrawal_reason`
- [[Reference/Modules/learnloop/substrate/replay|learnloop.substrate.replay]] — imports `rebuild_derived_state`; calls `rebuild_derived_state`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `importlib`, `pathlib`, `shutil`, `tempfile`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/content/authoring/laddered_stems|learnloop.content.authoring.laddered_stems]], [[Reference/Modules/learnloop/content/authoring/persona_gate|learnloop.content.authoring.persona_gate]], [[Reference/Modules/learnloop/diagnosis/contrast_pairs|learnloop.diagnosis.contrast_pairs]], [[Reference/Modules/learnloop/diagnosis/discrimination_profiles|learnloop.diagnosis.discrimination_profiles]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_architecture.py](../../../../../../tests/test_architecture.py) — direct import
  - `test_runtime_constructed_module_references_resolve`
- [tests/test_diagnostic_augmentation.py](../../../../../../tests/test_diagnostic_augmentation.py) — direct import
  - `test_licensed_b1_runs_blind_and_never_writes_a_learner_attempt`
- [tests/test_scoreboard.py](../../../../../../tests/test_scoreboard.py) — direct import
  - `test_a_belief_never_surfaced_is_not_a_harmful_write`
  - `test_a_metric_may_not_carry_a_value_on_an_unavailable_arm`
  - `test_a_run_reporting_zero_tokens_is_unmetered_not_free`
  - `test_adjudication_metrics_are_composed_not_recomputed`
  - `test_adjudication_metrics_track_the_real_store`
  - `test_agreement_is_computed_once_a_planted_side_exists`
  - `test_an_assisted_success_is_not_a_cold_success`
  - `test_an_unrecorded_latency_never_counts_as_zero_minutes`
  - `test_board_is_the_frozen_b5_list_in_b5_order`
  - `test_cells_cleared_per_question_divides_by_questions_served`
  - `test_cells_cleared_per_question_is_unavailable_before_any_question`
  - `test_cells_cleared_per_question_uses_the_contract_cell_vocabulary`
  - `test_censored_learning_objects_are_reported_and_excluded_from_the_mean`
  - `test_certification_metrics_require_an_explicit_replay`
  - `test_certification_replay_budget_bounds_the_answer_and_says_so`
  - `test_cli_json_carries_denominators_and_the_ordering_rationale`
  - `test_cli_prints_the_board_in_b5_order_with_unavailable_arms_visible`
  - `test_every_metric_is_unavailable_on_a_fresh_vault`
  - `test_false_certification_rate_is_composed_from_item_4_2`
  - `test_false_certification_seam_composes_a_producer_when_present`
  - `test_harmful_write_rate_counts_a_surfaced_then_withdrawn_belief`
  - `test_harmful_write_rate_reports_both_arms`
  - `test_measurement_rank_is_composed_from_identifiability`
  - `test_measurement_rank_is_unavailable_with_no_declared_facet`
  - `test_planted_side_absent_reports_no_producer_not_zero_overlap`
  - `test_probe_action_change_rate_counts_resolving_observations`
  - `test_probe_action_change_rate_says_no_probes_administered`
  - `test_problems_to_cold_success_counts_problems_until_the_first_cold_success`
  - `test_self_reports_are_not_problems_served`
  - `test_supersession_is_not_harm_and_is_reported_separately`
  - `test_the_board_composes_rather_than_declaring_its_own_producers`
  - `test_tokens_metric_divides_by_resolved_episodes_only`
  - `test_tokens_metric_is_unavailable_with_no_resolved_episode`
  - `test_tokens_metric_reports_the_ratio_over_metered_episodes`
  - `test_zero_over_empty_and_zero_over_two_are_different_findings`

## Modification guidance

- Change scoreboard policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/scoreboard.py](../../../../../../src/learnloop/diagnosis/scoreboard.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
