---
title: "learnloop.diagnosis.contrast_pairs"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/contrast_pairs.py"
source_paths:
  - "src/learnloop/diagnosis/contrast_pairs.py"
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
  - "learnloop.diagnosis.contrast_pairs module"
  - "src/learnloop/diagnosis/contrast_pairs.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.contrast_pairs`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.contrast_pairs` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: A4 — contrast pairs (spec_measurement_efficiency_v1 §3.A4).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/contrast_pairs.py](../../../../../../src/learnloop/diagnosis/contrast_pairs.py) |
| Source lines | 1011 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `pair_key(item_id: str, counterpart_id: str) -> str` ([source](../../../../../../src/learnloop/diagnosis/contrast_pairs.py), line 94) — The shared key of one pair: the two ids, sorted, joined by ``|``.
- `class ContrastPairDisposition(StrEnum)` ([source](../../../../../../src/learnloop/diagnosis/contrast_pairs.py), line 110) — What authoring may do about one identifiability finding.
  - `authorable(self) -> bool` (line 145; public)
- `class ContrastPairRequest` ([source](../../../../../../src/learnloop/diagnosis/contrast_pairs.py), line 180) — One authoring request: separate these two things with one manipulation.
  - `facet_ids(self) -> tuple[str, ...]` (line 203; public)
  - `as_dict(self) -> dict[str, Any]` (line 206; public) — Payload handed to the authoring model — the request, not the report.
- `class ContrastPairCommissionPlan` ([source](../../../../../../src/learnloop/diagnosis/contrast_pairs.py), line 240) — The commissioning queue for A4, in finding order, deferrals included.
  - `commissioned(self) -> tuple[ContrastPairRequest, ...]` (line 246; public)
  - `deferred(self) -> tuple[ContrastPairRequest, ...]` (line 250; public)
  - `for_subject(self, subject_id: str | None) -> tuple[ContrastPairRequest, ...]` (line 255; public)
  - `summary(self) -> dict[str, Any]` (line 260; public)
  - `as_dict(self) -> dict[str, Any]` (line 271; public)
- `commission_contrast_pairs(vault: LoadedVault, repository: Repository | None=None, *, subject_id: str | None=None) -> ContrastPairCommissionPlan` ([source](../../../../../../src/learnloop/diagnosis/contrast_pairs.py), line 279) — Turn identifiability findings into contrast-pair authoring requests.
- `class PairGateReason(StrEnum)` ([source](../../../../../../src/learnloop/diagnosis/contrast_pairs.py), line 353) — Why a pair was refused.
- `answer_skeleton(text: str) -> str` ([source](../../../../../../src/learnloop/diagnosis/contrast_pairs.py), line 380) — The expected answer with every numeral masked (§3.A4 gate 2's test).
- `class PairVerdict` ([source](../../../../../../src/learnloop/diagnosis/contrast_pairs.py), line 410) — One pair's authoring verdict, and the numbers that decided it.
  - `as_dict(self) -> dict[str, Any]` (line 417; public)
- `judge_pair(first: Mapping[str, Any], second: Mapping[str, Any], *, difficulty_band: tuple[float, float] | None) -> PairVerdict` ([source](../../../../../../src/learnloop/diagnosis/contrast_pairs.py), line 426) — §3.A4's three authoring gates over one pair's payloads.
- `class ContrastPairGate` ([source](../../../../../../src/learnloop/diagnosis/contrast_pairs.py), line 492) — §3.A4's authoring gates as a ``row_transform`` (the seam every gate rides).
  - `__init__(self, vault: LoadedVault, *, difficulty_band_by_lo: Mapping[str, tuple[float, float]] | None=None) -> None` (line 507; internal)
  - `__call__(self, rows: list[dict[str, Any]]) -> None` (line 518; internal)
  - `_band_for(self, payload: Mapping[str, Any]) -> tuple[float, float] | None` (line 562; internal)
  - `_resolve_single(self, key: str, row: dict[str, Any]) -> None` (line 565; internal) — A member whose counterpart is not in this batch.
  - `_record(self, row: dict[str, Any], key: str, verdict: PairVerdict) -> None` (line 591; internal)
- `class AdjacencyBasis(StrEnum)` ([source](../../../../../../src/learnloop/diagnosis/contrast_pairs.py), line 629) — Why the two members were or were not served adjacent (§3.A4).
- `randomization_draw(seed: str) -> float` ([source](../../../../../../src/learnloop/diagnosis/contrast_pairs.py), line 642) — A deterministic uniform draw in [0, 1) from a seed string.
- `class PairServingDecision` ([source](../../../../../../src/learnloop/diagnosis/contrast_pairs.py), line 658) — One pair's serving decision, before it is written or applied to a queue.
  - `as_dict(self) -> dict[str, Any]` (line 669; public)
- `plan_contrast_pair_serving(vault: LoadedVault, ordered_item_ids: Sequence[str], *, session_id: str | None) -> list[PairServingDecision]` ([source](../../../../../../src/learnloop/diagnosis/contrast_pairs.py), line 681) — Decide, for every pair in a queue, which member goes first and whether the two are separated.
- `apply_serving_decisions(ordered_item_ids: Sequence[str], decisions: Sequence[PairServingDecision]) -> list[str]` ([source](../../../../../../src/learnloop/diagnosis/contrast_pairs.py), line 756) — Reorder a queue so each pair's randomized first member precedes the other.
- `record_contrast_pair_servings(repository: Repository, decisions: Iterable[PairServingDecision], *, session_id: str | None, clock: Clock | None=None) -> int` ([source](../../../../../../src/learnloop/diagnosis/contrast_pairs.py), line 781) — Persist the serving decisions; returns rows written.
- `contrast_pair_order_effect(vault: LoadedVault, repository: Repository, *, since: str | None=None) -> Metric` ([source](../../../../../../src/learnloop/diagnosis/contrast_pairs.py), line 839) — ``contrast_pair_order_effect``: A4's revert producer.

### Module constants

- `CONTRAST_PAIR_VERSION` ([src/learnloop/diagnosis/contrast_pairs.py](../../../../../../src/learnloop/diagnosis/contrast_pairs.py), line 91)
- `DEFERRAL_REASON` ([src/learnloop/diagnosis/contrast_pairs.py](../../../../../../src/learnloop/diagnosis/contrast_pairs.py), line 151)
- `PAIR_BAND_TOLERANCE` ([src/learnloop/diagnosis/contrast_pairs.py](../../../../../../src/learnloop/diagnosis/contrast_pairs.py), line 345)
- `MAX_WITHIN_PAIR_DIFFICULTY_GAP` ([src/learnloop/diagnosis/contrast_pairs.py](../../../../../../src/learnloop/diagnosis/contrast_pairs.py), line 350)
- `_DIGITS` ([src/learnloop/diagnosis/contrast_pairs.py](../../../../../../src/learnloop/diagnosis/contrast_pairs.py), line 377)
- `ORDER_EFFECT_METRIC` ([src/learnloop/diagnosis/contrast_pairs.py](../../../../../../src/learnloop/diagnosis/contrast_pairs.py), line 822)
- `MIN_COMPLETED_PAIRS` ([src/learnloop/diagnosis/contrast_pairs.py](../../../../../../src/learnloop/diagnosis/contrast_pairs.py), line 825)
- `ORDER_DOMINANCE_CEILING` ([src/learnloop/diagnosis/contrast_pairs.py](../../../../../../src/learnloop/diagnosis/contrast_pairs.py), line 830)
- `ORDER_EFFECT_ALPHA` ([src/learnloop/diagnosis/contrast_pairs.py](../../../../../../src/learnloop/diagnosis/contrast_pairs.py), line 836)

## Internal implementation anchors

- `_disposition_for(finding: IdentifiabilityFinding) -> ContrastPairDisposition` ([source](../../../../../../src/learnloop/diagnosis/contrast_pairs.py), line 165) — Total over the finding vocabulary.
- `_expected_text(payload: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/diagnosis/contrast_pairs.py), line 402)
- `_payload_of(item: PracticeItem) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/contrast_pairs.py), line 606) — A persisted item rendered as the payload shape the gates read.
- `_latest_correctness(attempts: Sequence[Mapping[str, Any]]) -> float | None` ([source](../../../../../../src/learnloop/diagnosis/contrast_pairs.py), line 989) — The most recent scored correctness on one item, or ``None``.
- `_adjacency_tally(servings: Sequence[Mapping[str, Any]]) -> dict[str, int]` ([source](../../../../../../src/learnloop/diagnosis/contrast_pairs.py), line 1006)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `commission_contrast_pairs`, `contrast_pair_order_effect`; statically calls `commission_contrast_pairs`, `contrast_pair_order_effect`
- [[Reference/Modules/learnloop/content/authoring/authoring_gates|learnloop.content.authoring.authoring_gates]] — imports `ContrastPairGate`; statically calls `ContrastPairGate`
- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `commission_contrast_pairs`; statically calls `commission_contrast_pairs`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `apply_serving_decisions`, `plan_contrast_pair_serving`, `record_contrast_pair_servings`; statically calls `apply_serving_decisions`, `plan_contrast_pair_serving`, `record_contrast_pair_servings`
- [[Reference/Modules/learnloop_sidecar/handlers/measurement|learnloop_sidecar.handlers.measurement]] — imports `commission_contrast_pairs`, `contrast_pair_order_effect`; statically calls `commission_contrast_pairs`, `contrast_pair_order_effect`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_gate|learnloop.diagnosis.diagnostic_gate]] — imports `normalize_answer`; calls `normalize_answer`
- [[Reference/Modules/learnloop/diagnosis/discrimination_profiles|learnloop.diagnosis.discrimination_profiles]] — imports `profiles_by_facet`; calls `profiles_by_facet`
- [[Reference/Modules/learnloop/diagnosis/scoreboard|learnloop.diagnosis.scoreboard]] — imports `Metric`; calls `Metric`
- [[Reference/Modules/learnloop/learner/identifiability|learnloop.learner.identifiability]] — imports `IdentifiabilityFinding`, `analyze_identifiability`, `build_registry_view`, `load_misconception_records`; calls `analyze_identifiability`, `build_registry_view`, `load_misconception_records`
- [[Reference/Modules/learnloop/numeric|learnloop.numeric]] — imports `binomial_two_sided_p`; calls `binomial_two_sided_p`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `enum`, `hashlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/content/authoring/authoring_gates|learnloop.content.authoring.authoring_gates]], [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]], [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]], [[Reference/Modules/learnloop_sidecar/handlers/measurement|learnloop_sidecar.handlers.measurement]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_contrast_pairs.py](../../../../../../tests/test_contrast_pairs.py) — direct import
  - `test_a_member_can_pair_with_an_item_already_in_the_vault`
  - `test_a_member_whose_counterpart_does_not_exist_is_refused`
  - `test_a_pair_differing_only_in_its_numbers_is_rejected`
  - `test_a_pair_in_band_with_a_structural_manipulation_passes`
  - `test_a_pair_key_is_derived_not_authored`
  - `test_a_pair_must_declare_one_symmetric_differing_component`
  - `test_a_pair_must_satisfy_both_the_persona_gate_and_the_pair_gate`
  - `test_a_pair_whose_members_fall_in_different_bands_is_rejected`
  - `test_adjacent_members_are_admitted_only_when_the_surfaces_differ`
  - `test_applying_a_decision_swaps_slots_and_moves_nothing_else`
  - `test_commissioning_turns_identifiability_findings_into_requests`
  - `test_members_far_apart_inside_one_wide_band_are_also_rejected`
  - `test_order_effect_abstains_before_enough_completed_pairs`
  - `test_order_effects_dominating_is_named_as_the_revert_verdict`
  - `test_serving_randomizes_which_member_goes_first_and_records_the_seed`
  - `test_the_answer_skeleton_masks_values_and_keeps_structure`
  - `test_the_commissioning_queue_keeps_its_deferrals_with_a_reason`
  - `test_the_draw_is_deterministic_per_session_and_varies_across_them`
  - `test_the_randomization_balance_is_reported_beside_the_effect`
  - `test_three_rows_claiming_one_pair_key_are_refused_together`

## Modification guidance

- Change contrast pairs policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/contrast_pairs.py](../../../../../../src/learnloop/diagnosis/contrast_pairs.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
