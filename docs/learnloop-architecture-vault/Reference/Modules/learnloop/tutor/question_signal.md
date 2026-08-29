---
title: "learnloop.tutor.question_signal"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/tutor/question_signal.py"
source_paths:
  - "src/learnloop/tutor/question_signal.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.tutor"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Tutor and Teach-Back Workflow"
aliases:
  - "learnloop.tutor.question_signal module"
  - "src/learnloop/tutor/question_signal.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-tutor"
---

# `learnloop.tutor.question_signal`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.tutor.question_signal` exists within [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] to own the behavior summarized by its module contract: Learner questions as observations on facet hypothesis marginals.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/tutor/question_signal.py](../../../../../../src/learnloop/tutor/question_signal.py) |
| Source lines | 597 |
| Owning package | [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class ResolvedQuestionLikelihood` ([source](../../../../../../src/learnloop/tutor/question_signal.py), line 70) — L(ask | facet_solid) / L(ask | not solid), with provenance.
  - `as_dict(self) -> dict[str, Any]` (line 80; public)
- `class QuestionSignal` ([source](../../../../../../src/learnloop/tutor/question_signal.py), line 92) — Unresolved substantive questions for one LO, grouped for consumers.
  - `facets(self) -> list[str]` (line 108; public)
  - `context_entries(self, *, max_entries: int=6, excerpt_chars: int=240) -> list[dict[str, Any]]` (line 111; public) — Compact question context for diagnostic_focus / authoring prompts.
- `resolve_question_likelihood(repository: Repository, config: TutorQAConfig) -> ResolvedQuestionLikelihood` ([source](../../../../../../src/learnloop/tutor/question_signal.py), line 132) — Calibrate the solid-likelihood ratio from the learner's own history.
- `resolve_gap_declaration_likelihood(repository: Repository, config: TutorPromotionConfig) -> ResolvedQuestionLikelihood` ([source](../../../../../../src/learnloop/tutor/question_signal.py), line 160) — Calibrate the gap-declaration solid-likelihood ratio (spec §3 G2).
- `apply_question_observation(hypothesis_marginal: dict[str, float], *, solid_likelihood_ratio: float) -> dict[str, float]` ([source](../../../../../../src/learnloop/tutor/question_signal.py), line 254) — One substantive-question observation on a facet's hypothesis marginal.
- `collect_question_signal(vault: LoadedVault, repository: Repository, learning_object_id: str, *, exclude_attempt_id: str | None=None, clock: Clock | None=None) -> QuestionSignal` ([source](../../../../../../src/learnloop/tutor/question_signal.py), line 276) — Unresolved substantive questions mapped to one LO's facets.
- `question_adjusted_uncertainty_states(vault: LoadedVault, repository: Repository, learning_object_id: str, *, states: list[FacetUncertaintyState] | None=None, signal: QuestionSignal | None=None, exclude_attempt_id: str | None=None, clock: Clock | None=None) -> tuple[list[FacetUncertaintyState], QuestionSignal]` ([source](../../../../../../src/learnloop/tutor/question_signal.py), line 385) — Facet uncertainty states with question observations folded in.

### Module constants

- `SUBSTANTIVE_QUESTION_TYPES` ([src/learnloop/tutor/question_signal.py](../../../../../../src/learnloop/tutor/question_signal.py), line 48)
- `QUESTION_SIGNAL_WINDOW_DAYS` ([src/learnloop/tutor/question_signal.py](../../../../../../src/learnloop/tutor/question_signal.py), line 52)
- `MAX_QUESTION_OBSERVATIONS_PER_FACET` ([src/learnloop/tutor/question_signal.py](../../../../../../src/learnloop/tutor/question_signal.py), line 53)
- `_FRONTIER_NATURES` ([src/learnloop/tutor/question_signal.py](../../../../../../src/learnloop/tutor/question_signal.py), line 58)
- `_RATE_CLAMP` ([src/learnloop/tutor/question_signal.py](../../../../../../src/learnloop/tutor/question_signal.py), line 64)
- `_RATIO_FLOOR` ([src/learnloop/tutor/question_signal.py](../../../../../../src/learnloop/tutor/question_signal.py), line 65)
- `_SMOOTHING_PSEUDO_COUNT` ([src/learnloop/tutor/question_signal.py](../../../../../../src/learnloop/tutor/question_signal.py), line 66)

## Internal implementation anchors

- `_empirical_solid_likelihood(questioned: dict[str, bool], repository: Repository, *, min_samples: int, fallback: float) -> ResolvedQuestionLikelihood` ([source](../../../../../../src/learnloop/tutor/question_signal.py), line 198) — Shared Laplace-smoothed failure-lift → solid-likelihood ratio.
- `_base_failure_rate(repository: Repository) -> float` ([source](../../../../../../src/learnloop/tutor/question_signal.py), line 243)
- `_collect_gap_declarations(vault: LoadedVault, repository: Repository, learning_object_id: str, *, since: str, successes: dict[str, str]) -> dict[str, list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/tutor/question_signal.py), line 328) — Gap-declared promotions mapped to this LO's attributed facets.
- `_apply_question_channels(marginal: dict[str, float], ordinary_events: list[dict[str, Any]], gap_events: list[dict[str, Any]], ordinary_ratio: float, gap_ratio: float, *, preference_damping: float=1.0) -> dict[str, float]` ([source](../../../../../../src/learnloop/tutor/question_signal.py), line 479) — Fold both question channels into one facet marginal under a shared cap.
- `_empty_signal(config: TutorQAConfig) -> QuestionSignal` ([source](../../../../../../src/learnloop/tutor/question_signal.py), line 520)
- `_clamped_rate(successes: float, total: float) -> float` ([source](../../../../../../src/learnloop/tutor/question_signal.py), line 536)
- `_first_attempt_at_or_after(repository: Repository, practice_item_id: str, created_at: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/tutor/question_signal.py), line 543)
- `_attempt_failed(attempt: dict[str, Any]) -> bool` ([source](../../../../../../src/learnloop/tutor/question_signal.py), line 554)
- `_facet_success_times(vault: LoadedVault, repository: Repository, learning_object_id: str, *, exclude_attempt_id: str | None) -> dict[str, str]` ([source](../../../../../../src/learnloop/tutor/question_signal.py), line 563) — Latest *successful* attempt time per canonical facet (the resolution signal).
- `_event_maps_to_lo(vault: LoadedVault, event: dict[str, Any], learning_object_id: str) -> bool` ([source](../../../../../../src/learnloop/tutor/question_signal.py), line 588)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `QuestionSignal`, `question_adjusted_uncertainty_states`; statically calls `question_adjusted_uncertainty_states`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `TutorPromotionConfig`, `TutorQAConfig`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `FacetUncertaintyState`, `Repository`; calls `FacetUncertaintyState`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `entropy`, `facet_state_label`, `normalize_distribution`; calls `entropy`, `facet_state_label`, `normalize_distribution`
- [[Reference/Modules/learnloop/learner/facet_state_reader|learnloop.learner.facet_state_reader]] — imports `facet_recall_states_for_lo`, `facet_uncertainty_states_for_lo`; calls `facet_recall_states_for_lo`, `facet_uncertainty_states_for_lo`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Tutor and Teach-Back Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_question_context.py](../../../../../../tests/test_question_context.py) — direct import
  - `test_preference_channel_gets_damped_mastery_likelihood`
  - `test_unclassified_events_keep_full_likelihood`
- [tests/test_question_signal.py](../../../../../../tests/test_question_signal.py) — direct import
  - `test_adjustment_disabled_by_config`
  - `test_failed_attempt_does_not_resolve_question`
  - `test_likelihood_calibrates_from_question_failure_lift`
  - `test_likelihood_falls_back_below_min_samples`
  - `test_neutral_ratio_is_a_noop`
  - `test_non_substantive_and_unanswered_questions_are_ignored`
  - `test_question_observation_shifts_mass_away_from_solid`
  - `test_successful_attempt_resolves_question`
  - `test_triggering_attempt_cannot_resolve_its_own_questions`
  - `test_virtual_open_state_for_questioned_facet_without_row`
- [tests/test_tutor_promotion_w2.py](../../../../../../tests/test_tutor_promotion_w2.py) — direct import
  - `test_core_recall_gap_on_solid_facet_still_applies`
  - `test_failed_attempt_does_not_resolve_gap_declaration`
  - `test_gap_declaration_bumps_facet_independent_of_question_type`
  - `test_gap_declaration_resolved_by_later_success`
  - `test_gap_likelihood_calibrates_from_declaration_failure_lift`
  - `test_gap_likelihood_uses_own_fallback_below_min_samples`
  - `test_transfer_gap_on_solid_facet_is_skipped`

## Modification guidance

- Change question signal policy here when tutor owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/tutor/question_signal.py](../../../../../../src/learnloop/tutor/question_signal.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
