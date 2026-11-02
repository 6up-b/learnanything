---
title: "learnloop.evsi_calibration.policies"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/evsi_calibration/policies.py"
source_paths:
  - "src/learnloop/evsi_calibration/policies.py"
source_commit: "345c8098f98618d8018657a45bad350988cc25ea"
source_commit_timestamp: "2026-10-13T18:01:33-04:00"
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
  - "learnloop.evsi_calibration.policies module"
  - "src/learnloop/evsi_calibration/policies.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-evsi-calibration"
---

# `learnloop.evsi_calibration.policies`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.evsi_calibration.policies` exists within [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] to own the behavior summarized by its module contract: Selection-and-stop policies the simulation compares, all on the real modules.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/evsi_calibration/policies.py](../../../../../../src/learnloop/evsi_calibration/policies.py) |
| Source lines | 565 |
| Owning package | [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `345c8098f98618d8018657a45bad350988cc25ea` |
| Commit timestamp | `2026-10-13T18:01:33-04:00` |

## Public API

- `identity_channel(options: Sequence[str]) -> dict[str, dict[str, float]]` ([source](../../../../../../src/learnloop/evsi_calibration/policies.py), line 100)
- `class PolicySettings` ([source](../../../../../../src/learnloop/evsi_calibration/policies.py), line 105) — Every hand-set number the policies consume, so a sweep can move one.
  - `as_dict(self) -> dict[str, Any]` (line 133; public)
- `class Decision` ([source](../../../../../../src/learnloop/evsi_calibration/policies.py), line 138)
- `class EpisodeState` ([source](../../../../../../src/learnloop/evsi_calibration/policies.py), line 150)
- `mixture(member: Mapping[str, Mapping[str, float]], belief: Mapping[str, float]) -> dict[str, float]` ([source](../../../../../../src/learnloop/evsi_calibration/policies.py), line 163)
- `decide_evsi(state: EpisodeState, settings: PolicySettings, *, obey_abstention: bool=True) -> Decision` ([source](../../../../../../src/learnloop/evsi_calibration/policies.py), line 187)
- `decide_lookahead(state: EpisodeState, settings: PolicySettings) -> Decision` ([source](../../../../../../src/learnloop/evsi_calibration/policies.py), line 259)
- `decide_eig(state: EpisodeState, settings: PolicySettings, *, obey_gate: bool=True) -> Decision` ([source](../../../../../../src/learnloop/evsi_calibration/policies.py), line 270)
- `decide_capped(state: EpisodeState, settings: PolicySettings, *, chooser: str, robust_gate: bool=False) -> Decision` ([source](../../../../../../src/learnloop/evsi_calibration/policies.py), line 358)
- `class ValueGate` ([source](../../../../../../src/learnloop/evsi_calibration/policies.py), line 396) — What a value rule says about the next observation: the paying checks (ref -> robust value in minutes), the method that valued them, and ``rank_feasible``'s ranking when it decided (the lookahead's batch order).
- `decide_successor(state: EpisodeState, settings: PolicySettings) -> Decision` ([source](../../../../../../src/learnloop/evsi_calibration/policies.py), line 473)
- `decide_package(state: EpisodeState, settings: PolicySettings, *, gate: bool=False, fallback: bool=False, lookahead: bool=True, top_value: bool=False) -> Decision` ([source](../../../../../../src/learnloop/evsi_calibration/policies.py), line 484) — The proposed package (``voi_proposed``: every switch at its default), its leave-one-out ablations and its serving variant, each inside the successor's structure (the episode maximum lifted, the stability stops kept, the successor's serving rule): ``gate``: keep today's robust co…
- `decide(policy: str, state: EpisodeState, settings: PolicySettings) -> Decision` ([source](../../../../../../src/learnloop/evsi_calibration/policies.py), line 532)

### Module constants

- `POLICIES` ([src/learnloop/evsi_calibration/policies.py](../../../../../../src/learnloop/evsi_calibration/policies.py), line 40)
- `VARIANTS` ([src/learnloop/evsi_calibration/policies.py](../../../../../../src/learnloop/evsi_calibration/policies.py), line 50)
- `ALL_POLICIES` ([src/learnloop/evsi_calibration/policies.py](../../../../../../src/learnloop/evsi_calibration/policies.py), line 51)
- `SUCCESSOR_ABLATIONS` ([src/learnloop/evsi_calibration/policies.py](../../../../../../src/learnloop/evsi_calibration/policies.py), line 88)
- `SUCCESSOR_VARIANTS` ([src/learnloop/evsi_calibration/policies.py](../../../../../../src/learnloop/evsi_calibration/policies.py), line 89)
- `SUCCESSOR_POLICIES` ([src/learnloop/evsi_calibration/policies.py](../../../../../../src/learnloop/evsi_calibration/policies.py), line 90)
- `LOOKAHEAD_MAX` ([src/learnloop/evsi_calibration/policies.py](../../../../../../src/learnloop/evsi_calibration/policies.py), line 91)
- `_CHANNEL_HIGH` ([src/learnloop/evsi_calibration/policies.py](../../../../../../src/learnloop/evsi_calibration/policies.py), line 96)
- `_CHANNEL_LOW` ([src/learnloop/evsi_calibration/policies.py](../../../../../../src/learnloop/evsi_calibration/policies.py), line 97)

## Internal implementation anchors

- `_entropy(distribution: Mapping[str, float]) -> float` ([source](../../../../../../src/learnloop/evsi_calibration/policies.py), line 171)
- `_prefilter(state: EpisodeState, settings: PolicySettings) -> list[str]` ([source](../../../../../../src/learnloop/evsi_calibration/policies.py), line 175) — Bound the candidate set by mean-member EIG (live slates are small).
- `_joint_member(tables: Sequence[Mapping[str, Mapping[str, float]]], hypotheses: Sequence[str]) -> dict[str, dict[str, float]]` ([source](../../../../../../src/learnloop/evsi_calibration/policies.py), line 218) — ``P(e1, ..., ek | h)`` for conditionally independent checks.
- `_paying_batch(state: EpisodeState, settings: PolicySettings, ranking: Sequence[str]) -> tuple[tuple[str, ...], float, list[float]] | None` ([source](../../../../../../src/learnloop/evsi_calibration/policies.py), line 235) — The knowledge-gradient* step: the smallest batch of the top-k ranked checks (2 <= k <= ``LOOKAHEAD_MAX``) whose joint robust value clears k checks' minutes, as ``(batch, robust value, member values)``; ``None`` when none does.
- `_stable(state: EpisodeState, config: ProbeEpisodeConfig) -> bool` ([source](../../../../../../src/learnloop/evsi_calibration/policies.py), line 288)
- `_action_equivalent(state: EpisodeState, config: ProbeEpisodeConfig) -> bool` ([source](../../../../../../src/learnloop/evsi_calibration/policies.py), line 295)
- `_cap_stop(state: EpisodeState, config: ProbeEpisodeConfig, *, budget: bool=True) -> str | None` ([source](../../../../../../src/learnloop/evsi_calibration/policies.py), line 302) — The cap-only stop rules (``_evaluate_completion`` without the robust gate).
- `_robust_gate_abstains(state: EpisodeState, settings: PolicySettings) -> bool` ([source](../../../../../../src/learnloop/evsi_calibration/policies.py), line 316) — ``probe_episodes._robust_completion_override``: the robust selector over the remaining instruments abstains (the episode-pinned channel here is the simulation's identity channel).
- `_incumbent_stop(state: EpisodeState, settings: PolicySettings, config: ProbeEpisodeConfig, *, budget: bool=True) -> str | None` ([source](../../../../../../src/learnloop/evsi_calibration/policies.py), line 337) — ``probe_episodes._evaluate_completion`` in its own order (review F8).
- `_rank(state: EpisodeState, settings: PolicySettings, refs: Sequence[str]) -> EV.RankResult` ([source](../../../../../../src/learnloop/evsi_calibration/policies.py), line 377)
- `_lcb_paying(result: EV.RankResult) -> dict[str, float]` ([source](../../../../../../src/learnloop/evsi_calibration/policies.py), line 389) — The ranked checks whose robust LCB clears their minutes cost.
- `_successor_value_gate(state: EpisodeState, settings: PolicySettings) -> ValueGate` ([source](../../../../../../src/learnloop/evsi_calibration/policies.py), line 411) — ``voi_stopping.value_candidates`` on this episode.
- `_lcb_value_gate(state: EpisodeState, settings: PolicySettings) -> ValueGate` ([source](../../../../../../src/learnloop/evsi_calibration/policies.py), line 431) — The proposed rule: ``rank_feasible``'s robust LCB decides, a flip abstention included (it never reaches the nat scale).
- `_eig_value_paying(state: EpisodeState, settings: PolicySettings, refs: Sequence[str]) -> dict[str, float]` ([source](../../../../../../src/learnloop/evsi_calibration/policies.py), line 439) — ``value_candidates``' EIG path: each candidate's robust EIG (the members' ``robust_quantile``) times ``VALUE_PER_NAT_MINUTES``, kept where it clears ``lambda_time * minutes + burden``.
- `_highest_eig(state: EpisodeState) -> str` ([source](../../../../../../src/learnloop/evsi_calibration/policies.py), line 454) — The incumbent's instrument: the highest hypothesis-EIG remaining check.
- `_serve_paying(state: EpisodeState, paying: Mapping[str, float], method: str) -> Decision` ([source](../../../../../../src/learnloop/evsi_calibration/policies.py), line 460) — The successor's serving choice: the incumbent's highest-EIG instrument when it pays, else the best paying one; stop when none pays.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/evsi_calibration/compare|learnloop.evsi_calibration.compare]] — imports `module`
- [[Reference/Modules/learnloop/evsi_calibration/experiments|learnloop.evsi_calibration.experiments]] — imports `module`; statically calls `PolicySettings`
- [[Reference/Modules/learnloop/evsi_calibration/multifamily|learnloop.evsi_calibration.multifamily]] — imports `module`; statically calls `PolicySettings`, `mixture`
- [[Reference/Modules/learnloop/evsi_calibration/multisim|learnloop.evsi_calibration.multisim]] — imports `module`; statically calls `EpisodeState`, `PolicySettings`, `decide`, `identity_channel`, `mixture`
- [[Reference/Modules/learnloop/evsi_calibration/simulate|learnloop.evsi_calibration.simulate]] — imports `module`; statically calls `EpisodeState`, `decide`, `identity_channel`, `mixture`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `ProbeEpisodeConfig`; calls `ProbeEpisodeConfig`
- [[Reference/Modules/learnloop/diagnosis/robust_composition|learnloop.diagnosis.robust_composition]] — imports `module`; calls `evaluate_selection`, `expected_information_gain`, `robust_quantile`
- [[Reference/Modules/learnloop/scheduling/action_loss|learnloop.scheduling.action_loss]] — imports `module`
- [[Reference/Modules/learnloop/scheduling/evsi|learnloop.scheduling.evsi]] — imports `module`; calls `DiagnosticCandidate`, `evsi_for_conditionals`, `rank_feasible`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `math`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/evsi_calibration/compare|learnloop.evsi_calibration.compare]], [[Reference/Modules/learnloop/evsi_calibration/experiments|learnloop.evsi_calibration.experiments]], [[Reference/Modules/learnloop/evsi_calibration/multifamily|learnloop.evsi_calibration.multifamily]], [[Reference/Modules/learnloop/evsi_calibration/multisim|learnloop.evsi_calibration.multisim]], [[Reference/Modules/learnloop/evsi_calibration/simulate|learnloop.evsi_calibration.simulate]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_evsi_calibration_sim.py](../../../../../../tests/test_evsi_calibration_sim.py) — direct import
  - `test_simulation_runs_every_policy_on_common_random_numbers`
  - `test_the_incumbent_arm_includes_todays_robust_completion_gate`
  - `test_the_measured_loss_charges_unresolved_minutes_off_the_diagonal`
- [tests/test_evsi_multisim.py](../../../../../../tests/test_evsi_multisim.py) — direct import
  - `test_each_ablation_puts_back_exactly_one_piece_of_the_successor`
  - `test_every_family_and_a_cross_system_run_all_policies`
  - `test_the_family_loop_reproduces_the_single_family_loop_for_the_latent_class_family`
  - `test_the_multi_family_study_runs_every_episode_without_a_count_bound`
  - `test_the_package_with_every_piece_put_back_is_the_successor`
  - `test_the_successor_arm_values_with_the_nat_scale_when_no_decision_is_at_stake`
  - `test_the_successor_arms_lift_the_episode_maximum_onto_value`
  - `test_true_loss_is_the_loss_table_for_one_need_and_charges_each_unaddressed_need`
- [tests/test_evsi_single_family_unbounded.py](../../../../../../tests/test_evsi_single_family_unbounded.py) — direct import
  - `test_the_comparison_tools_ordering_is_stable`
  - `test_the_single_family_path_defaults_to_no_count_bound`

## Modification guidance

- Make changes here when the responsibility remains policies within learnloop.evsi_calibration; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/evsi_calibration/policies.py](../../../../../../src/learnloop/evsi_calibration/policies.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
