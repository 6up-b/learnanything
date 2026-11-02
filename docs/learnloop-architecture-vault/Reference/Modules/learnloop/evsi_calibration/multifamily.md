---
title: "learnloop.evsi_calibration.multifamily"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/evsi_calibration/multifamily.py"
source_paths:
  - "src/learnloop/evsi_calibration/multifamily.py"
source_commit: "8df6e15b8abe8644a701f01fb74196cd884a748e"
source_commit_timestamp: "2026-10-13T13:06:39-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.evsi_calibration"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.evsi_calibration.multifamily module"
  - "src/learnloop/evsi_calibration/multifamily.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-evsi-calibration"
---

# `learnloop.evsi_calibration.multifamily`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.evsi_calibration.multifamily` exists within [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] to own the behavior summarized by its module contract: The multi-family study behind ``learnloop evsi multisim`` (stage ``evsi-multisim``).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/evsi_calibration/multifamily.py](../../../../../../src/learnloop/evsi_calibration/multifamily.py) |
| Source lines | 1300 |
| Owning package | [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `8df6e15b8abe8644a701f01fb74196cd884a748e` |
| Commit timestamp | `2026-10-13T13:06:39-04:00` |

## Public API

- `class MultiFamilySettings` ([source](../../../../../../src/learnloop/evsi_calibration/multifamily.py), line 133)
  - `as_dict(self) -> dict[str, Any]` (line 154; public)
- `counted_row(hypothesis: str, question: EediQuestion, counts: Mapping[str, Mapping[str, float]], pseudo_count: float) -> dict[str, float]` ([source](../../../../../../src/learnloop/evsi_calibration/multifamily.py), line 282) — The card's compiled row ``(pseudo * vocabulary + counts) / (pseudo + n)`` (``validate_and_compile_card``), mapped onto the four options.
- `run_count_stream(world: World, learners: Sequence[FamilyLearner], *, mode: str, pseudo_count: float, repair_minutes: float, seed: int, max_checks: int=4) -> list[dict[str, float]]` ([source](../../../../../../src/learnloop/evsi_calibration/multifamily.py), line 304) — One stream of episodes in learner order with a capped EIG chooser.
- `study_base(settings: MultiFamilySettings) -> MultiSimSettings` ([source](../../../../../../src/learnloop/evsi_calibration/multifamily.py), line 425) — Every cell's starting settings.
- `run_multifamily(bank: EediBank, fits: FamilyFits, settings: MultiFamilySettings, *, progress: Callable[[str], None] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/multifamily.py), line 435)
- `analyze(report: Mapping[str, Any], *, seed: int | None=None, draws: int | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/multifamily.py), line 975)

### Module constants

- `MULTIFAMILY_VERSION` ([src/learnloop/evsi_calibration/multifamily.py](../../../../../../src/learnloop/evsi_calibration/multifamily.py), line 100)
- `PAIRS` ([src/learnloop/evsi_calibration/multifamily.py](../../../../../../src/learnloop/evsi_calibration/multifamily.py), line 103)
- `_SLOT_OF` ([src/learnloop/evsi_calibration/multifamily.py](../../../../../../src/learnloop/evsi_calibration/multifamily.py), line 247)
- `ROLES` ([src/learnloop/evsi_calibration/multifamily.py](../../../../../../src/learnloop/evsi_calibration/multifamily.py), line 248)
- `MIN_VOTING_FAMILIES` ([src/learnloop/evsi_calibration/multifamily.py](../../../../../../src/learnloop/evsi_calibration/multifamily.py), line 664)
- `INSUFFICIENT` ([src/learnloop/evsi_calibration/multifamily.py](../../../../../../src/learnloop/evsi_calibration/multifamily.py), line 665)
- `NEAR_BEST_MINUTES` ([src/learnloop/evsi_calibration/multifamily.py](../../../../../../src/learnloop/evsi_calibration/multifamily.py), line 911)

### Explicit exports

`__all__` declares:

- `MultiFamilySettings`
- `analyze`
- `counted_row`
- `run_count_stream`
- `run_multifamily`

## Internal implementation anchors

- `_label(strength: float | None) -> str` ([source](../../../../../../src/learnloop/evsi_calibration/multifamily.py), line 158)
- `_compact_episodes(run: MultiSimRun) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/multifamily.py), line 162) — Per policy, per learner (in learner order): total minutes, checks, right action.
- `_paired(compact: Mapping[str, Any], left: str, right: str, *, seed: int, draws: int) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/evsi_calibration/multifamily.py), line 184)
- `_policy_table(run: MultiSimRun, *, seed: int, draws: int) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/multifamily.py), line 203)
- `_cell(run: MultiSimRun, *, seed: int, draws: int) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/multifamily.py), line 234)
- `_vocabulary_role_row(slot: str) -> dict[str, float]` ([source](../../../../../../src/learnloop/evsi_calibration/multifamily.py), line 251)
- `_slot_and_signature(hypothesis: str, question: EediQuestion) -> tuple[str, tuple[str, ...]]` ([source](../../../../../../src/learnloop/evsi_calibration/multifamily.py), line 263) — The contrast card's slot for a hypothesis on a question, and its signature options (exactly :func:`.world.hand_set_row`'s mapping).
- `_role_of(option: str, question: EediQuestion, signature: Sequence[str]) -> str` ([source](../../../../../../src/learnloop/evsi_calibration/multifamily.py), line 276)
- `_stream_summary(records: Sequence[Mapping[str, float]], block: int) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/multifamily.py), line 391)
- `_stream_job(payload: tuple[World, Sequence[FamilyLearner], str, float, float, int, int]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/multifamily.py), line 416)
- `_starting_belief(world: World, learners: Sequence[FamilyLearner]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/multifamily.py), line 575)
- `_sensitivity(name: str, settings: MultiFamilySettings, base: MultiSimSettings, simulate, learners_at) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/multifamily.py), line 591)
- `_part_c(name: str, fits: FamilyFits, settings: MultiFamilySettings, base: MultiSimSettings, simulate, learners_at) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/multifamily.py), line 626)
- `_has_ci(value: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/evsi_calibration/multifamily.py), line 668)
- `_ci_only(values: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/evsi_calibration/multifamily.py), line 673) — A value certifies only through its 95% CI: one without a CI can hold (its point estimate agrees) but is never certified.
- `_voting_families(report: Mapping[str, Any], fitted: Sequence[str]) -> tuple[list[str], list[str], list[dict[str, str]]]` ([source](../../../../../../src/learnloop/evsi_calibration/multifamily.py), line 680) — The families that vote, the families every claim must cover, and the exclusions with their reason.
- `_verdict(values: Sequence[Mapping[str, Any]]) -> str` ([source](../../../../../../src/learnloop/evsi_calibration/multifamily.py), line 724) — ``supported`` when every family's CI agrees with the claim, ``directional`` when every family's point estimate agrees, ``family-dependent`` otherwise; ``no difference`` when the two arms took identical episodes everywhere (a zero effect with a zero-width CI in every family).
- `_regime(block: Mapping[str, Any], consistency: str, repair: float) -> Mapping[str, Any] | None` ([source](../../../../../../src/learnloop/evsi_calibration/multifamily.py), line 745)
- `_signed(pair: Mapping[str, Any], sign: int, **extra: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/multifamily.py), line 752)
- `_pair_claim(report: Mapping[str, Any], families: Sequence[str], consistency: str, repair: float, key: str, sign: int, *, seed: int=0, draws: int=400) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/evsi_calibration/multifamily.py), line 763) — ``key`` = ``right-left``: the paired difference right - left should have sign ``sign`` (+1: right costs more minutes), computed from the stored per-learner episodes of each family's own-system cell.
- `_rotation_claim(report: Mapping[str, Any], families: Sequence[str], key: str, sign: int, *, seed: int, draws: int, systems: Sequence[str] | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/evsi_calibration/multifamily.py), line 781) — The same paired difference when the system is calibrated to another family (every truth x system pair, every rotation regime, and the main comparison).
- `_kendall_tau(left: Mapping[str, float], right: Mapping[str, float]) -> float | None` ([source](../../../../../../src/learnloop/evsi_calibration/multifamily.py), line 806) — Kendall's tau-b between two families' mean minutes over their common policies.
- `_winners(report: Mapping[str, Any], families: Sequence[str], *, seed: int, draws: int, coverage: Sequence[str] | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/evsi_calibration/multifamily.py), line 829) — Per regime: each family's winner, co-winners (not distinguishable from the best), top-1 agreement and the regret of acting on another family's winner.
- `_policy_regret(report: Mapping[str, Any], families: Sequence[str], stress: Sequence[str], expected_regimes: Sequence[str] | None=None, coverage: Sequence[str] | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/evsi_calibration/multifamily.py), line 914) — RankCert's robust choice: each policy's regret (its mean minutes minus the best policy's) in every family x regime cell, worst case first.
- `_per_check_log_loss(arm: Mapping[str, Any], picks: np.ndarray) -> np.ndarray` ([source](../../../../../../src/learnloop/evsi_calibration/multifamily.py), line 964) — A stream arm's log loss per check under each bootstrap resample of its episodes: a ratio of sums over the arm's OWN checks (two arms stop after different numbers of checks, so one arm's count never divides the other's loss).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/evsi|learnloop.cli.evsi]] — imports `MultiFamilySettings`, `analyze`, `run_multifamily`; statically calls `MultiFamilySettings`, `analyze`, `run_multifamily`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `ProbeEpisodeConfig`; calls `ProbeEpisodeConfig`
- [[Reference/Modules/learnloop/diagnosis/probe_families|learnloop.diagnosis.probe_families]] — imports `CONTRAST_CONFUSABLE_DEFAULT_ROWS`, `DEFAULT_CONDITIONAL_PSEUDO_COUNT`, `ORDINAL_VOCABULARY`
- [[Reference/Modules/learnloop/diagnosis/robust_composition|learnloop.diagnosis.robust_composition]] — imports `module`; calls `expected_information_gain`, `observed_update`
- [[Reference/Modules/learnloop/evsi_calibration/eedi|learnloop.evsi_calibration.eedi]] — imports `EediBank`, `EediQuestion`, `OPTIONS`
- [[Reference/Modules/learnloop/evsi_calibration/experiments|learnloop.evsi_calibration.experiments]] — imports `DEFAULT_SWEEP_POLICIES`, `SWEEPS`, `SWEEP_POLICIES`, `hand_set_implied`; calls `hand_set_implied`
- [[Reference/Modules/learnloop/evsi_calibration/families|learnloop.evsi_calibration.families]] — imports `FAMILY_NAMES`, `FamilyModel`, `STRESS_FAMILIES`, `build_families`, `implied_quantities`; calls `build_families`, `implied_quantities`
- [[Reference/Modules/learnloop/evsi_calibration/family_fit|learnloop.evsi_calibration.family_fit]] — imports `FamilyFits`
- [[Reference/Modules/learnloop/evsi_calibration/metrics|learnloop.evsi_calibration.metrics]] — imports `module`; calls `episode_summary`, `paired_difference`, `summarize`
- [[Reference/Modules/learnloop/evsi_calibration/multisim|learnloop.evsi_calibration.multisim]] — imports `FamilyLearner`, `MULTISIM_VERSION`, `MultiSimRun`, `MultiSimSettings`, `SYSTEM_FAMILY`, `SYSTEM_HAND_SET`, `World`, `_Models`, `_seed`, `draw_family_learners`, `run_family_simulation`, `true_loss`, `with_policy`; calls `MultiSimSettings`, `World`, `_Models`, `_seed`, `draw_family_learners`, `run_family_simulation`, `true_loss`, `with_policy`
- [[Reference/Modules/learnloop/evsi_calibration/policies|learnloop.evsi_calibration.policies]] — imports `module`; calls `PolicySettings`, `mixture`
- [[Reference/Modules/learnloop/evsi_calibration/simulate|learnloop.evsi_calibration.simulate]] — imports `loss_table_for`; calls `loss_table_for`
- [[Reference/Modules/learnloop/evsi_calibration/world|learnloop.evsi_calibration.world]] — imports `HYP_KNOWS`, `HYP_OTHER`, `MIS_PREFIX`, `build_scenarios`, `route_for`; calls `build_scenarios`, `route_for`

### Platform and third-party dependencies

- Standard library: `__future__`, `concurrent`, `dataclasses`, `math`, `time`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/evsi|learnloop.cli.evsi]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_evsi_multisim.py](../../../../../../tests/test_evsi_multisim.py) — direct import
  - `test_a_required_adequate_family_absent_from_the_report_blocks_certification`
  - `test_a_zero_effect_everywhere_is_no_difference_not_a_contradiction`
  - `test_c1a_certifies_through_the_consistency_ci_not_a_fixed_margin`
  - `test_certification_needs_adequate_families_and_every_cell`
  - `test_the_counted_card_row_starts_at_the_vocabulary_and_follows_the_counts`
  - `test_the_multi_family_study_runs_every_episode_without_a_count_bound`
  - `test_the_pseudo_count_log_loss_is_per_check_of_each_arm`
  - `test_winners_list_tied_modes_in_name_order_and_score_rank_agreement`

## Modification guidance

- Make changes here when the responsibility remains multifamily within learnloop.evsi_calibration; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/evsi_calibration/multifamily.py](../../../../../../src/learnloop/evsi_calibration/multifamily.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
