---
title: "learnloop.diagnosis.discrimination_profiles"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/discrimination_profiles.py"
source_paths:
  - "src/learnloop/diagnosis/discrimination_profiles.py"
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
  - "learnloop.diagnosis.discrimination_profiles module"
  - "src/learnloop/diagnosis/discrimination_profiles.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.discrimination_profiles`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.discrimination_profiles` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: A5 — discrimination profiles on items (spec_measurement_efficiency_v1 §3.A5).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/discrimination_profiles.py](../../../../../../src/learnloop/diagnosis/discrimination_profiles.py) |
| Source lines | 571 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class ProfileMatchOutcome(StrEnum)` ([source](../../../../../../src/learnloop/diagnosis/discrimination_profiles.py), line 81) — The four arms one graded attempt can land on.
- `payload_profiles(payload: Mapping[str, Any]) -> tuple[dict[str, Any], ...]` ([source](../../../../../../src/learnloop/diagnosis/discrimination_profiles.py), line 118) — Authored profiles off a raw proposal-row payload, normalized and filtered.
- `item_profiles(item: PracticeItem) -> tuple[DiscriminationProfile, ...]` ([source](../../../../../../src/learnloop/diagnosis/discrimination_profiles.py), line 154) — Authored profiles off a loaded item, filtered by the same two rules.
- `profile_prior_payload(profiles: Sequence[DiscriminationProfile]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/discrimination_profiles.py), line 165) — What the grader is shown: candidate causes, explicitly labelled as a prior.
- `class ValidatedProfileMatch` ([source](../../../../../../src/learnloop/diagnosis/discrimination_profiles.py), line 196) — One attempt's profile judgement, as the grading validator resolved it.
  - `as_dict(self) -> dict[str, Any]` (line 207; public)
- `validate_profile_match(item: PracticeItem, proposal: Any) -> ValidatedProfileMatch` ([source](../../../../../../src/learnloop/diagnosis/discrimination_profiles.py), line 218) — Resolve the grader's profile report against the item's authored profiles.
- `profile_match_telemetry(match: 'ValidatedProfileMatch | Mapping[str, Any] | None') -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/discrimination_profiles.py), line 278) — The per-attempt counts ``causal_attribution_audit_report`` aggregates.
- `class ProfileTailVerdict(StrEnum)` ([source](../../../../../../src/learnloop/diagnosis/discrimination_profiles.py), line 357) — Which tail, if either, the population is sitting in.
- `profile_match_fill_rate(repository: Repository, *, since: str | None=None) -> Metric` ([source](../../../../../../src/learnloop/diagnosis/discrimination_profiles.py), line 369) — ``discrimination_profile_rejection_rate``: A5's two-tailed revert producer.
- `profile_coverage(vault: LoadedVault) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/discrimination_profiles.py), line 508) — How much of the item pool carries profiles at all, by source.
- `profiles_by_facet(vault: LoadedVault, items: Iterable[PracticeItem] | None=None) -> dict[str, list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/diagnosis/discrimination_profiles.py), line 543) — Canonical facet id -> the profiles authored against it, across the pool.

### Module constants

- `DISCRIMINATION_PROFILE_VERSION` ([src/learnloop/diagnosis/discrimination_profiles.py](../../../../../../src/learnloop/diagnosis/discrimination_profiles.py), line 78)
- `JUDGED_OUTCOMES` ([src/learnloop/diagnosis/discrimination_profiles.py](../../../../../../src/learnloop/diagnosis/discrimination_profiles.py), line 108)
- `NO_PROFILE_APPLIES_FLOOR` ([src/learnloop/diagnosis/discrimination_profiles.py](../../../../../../src/learnloop/diagnosis/discrimination_profiles.py), line 324)
- `PROFILE_SATURATION_CEILING` ([src/learnloop/diagnosis/discrimination_profiles.py](../../../../../../src/learnloop/diagnosis/discrimination_profiles.py), line 340)
- `MIN_MATCHES_FOR_SATURATION` ([src/learnloop/diagnosis/discrimination_profiles.py](../../../../../../src/learnloop/diagnosis/discrimination_profiles.py), line 345)
- `MIN_JUDGED_FOR_VERDICT` ([src/learnloop/diagnosis/discrimination_profiles.py](../../../../../../src/learnloop/diagnosis/discrimination_profiles.py), line 350)
- `PROFILE_REJECTION_METRIC` ([src/learnloop/diagnosis/discrimination_profiles.py](../../../../../../src/learnloop/diagnosis/discrimination_profiles.py), line 354)

## Internal implementation anchors

- `_tail_verdict(rate: float, judged: int, matched: int, concentration: Mapping[str, float]) -> ProfileTailVerdict` ([source](../../../../../../src/learnloop/diagnosis/discrimination_profiles.py), line 485) — Which tail the population sits in.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `profile_match_telemetry`; statically calls `profile_match_telemetry`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `ProfileMatchOutcome`, `item_profiles`, `profile_prior_payload`, `validate_profile_match`; statically calls `item_profiles`, `profile_prior_payload`, `validate_profile_match`
- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `profile_coverage`, `profile_match_fill_rate`; statically calls `profile_coverage`, `profile_match_fill_rate`
- [[Reference/Modules/learnloop/content/authoring/persona_gate|learnloop.content.authoring.persona_gate]] — imports `payload_profiles`; statically calls `payload_profiles`
- [[Reference/Modules/learnloop/diagnosis/contrast_pairs|learnloop.diagnosis.contrast_pairs]] — imports `profiles_by_facet`; statically calls `profiles_by_facet`
- [[Reference/Modules/learnloop_sidecar/handlers/measurement|learnloop_sidecar.handlers.measurement]] — imports `profile_coverage`, `profile_match_fill_rate`; statically calls `profile_coverage`, `profile_match_fill_rate`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/scoreboard|learnloop.diagnosis.scoreboard]] — imports `Metric`; calls `Metric`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `DiscriminationProfile`, `LoadedVault`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `enum`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]], [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/content/authoring/persona_gate|learnloop.content.authoring.persona_gate]], [[Reference/Modules/learnloop/diagnosis/contrast_pairs|learnloop.diagnosis.contrast_pairs]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_discrimination_profiles.py](../../../../../../tests/test_discrimination_profiles.py) — direct import
  - `test_a_match_naming_an_unknown_profile_is_not_coerced_onto_the_nearest`
  - `test_a_match_without_a_trace_citation_is_refused`
  - `test_a_spread_of_matches_across_profiles_is_within_band`
  - `test_coverage_reports_how_much_of_the_pool_is_profiled_at_all`
  - `test_incomplete_profiles_are_dropped_before_they_reach_the_gate`
  - `test_no_profile_applies_is_recorded_and_reaches_the_audit_report`
  - `test_one_profile_taking_every_match_is_the_other_tail`
  - `test_profiles_group_by_facet_for_a4_commissioning`
  - `test_rejection_rate_abstains_before_any_judged_failure`
  - `test_rejection_rate_collapsing_toward_zero_is_named_as_the_revert_tail`
  - `test_successes_and_unoffered_items_stay_out_of_the_denominator`
  - `test_the_four_outcome_arms_are_total_over_one_attempt`
  - `test_the_grading_prior_withholds_the_criteria_the_author_expects_to_fail`
  - `test_the_telemetry_survives_a_derived_state_rebuild`

## Modification guidance

- Change discrimination profiles policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/discrimination_profiles.py](../../../../../../src/learnloop/diagnosis/discrimination_profiles.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
