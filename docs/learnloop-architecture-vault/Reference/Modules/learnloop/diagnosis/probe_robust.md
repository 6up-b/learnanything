---
title: "learnloop.diagnosis.probe_robust"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/probe_robust.py"
source_paths:
  - "src/learnloop/diagnosis/probe_robust.py"
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
  - "learnloop.diagnosis.probe_robust module"
  - "src/learnloop/diagnosis/probe_robust.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.probe_robust`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.probe_robust` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: mvp-0.8 probe-episode robust cutover glue (spec_p0_measurement_correctness §4.2, change-log entry b').

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/probe_robust.py](../../../../../../src/learnloop/diagnosis/probe_robust.py) |
| Source lines | 309 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `use_robust_probe(vault: LoadedVault) -> bool` ([source](../../../../../../src/learnloop/diagnosis/probe_robust.py), line 51) — True iff this vault runs the mvp-0.8 authority-propagation probe path.
- `class EpisodeChannel` ([source](../../../../../../src/learnloop/diagnosis/probe_robust.py), line 64) — The calibration channel pinned on an episode at open (§4.2, invariant 3).
- `resolve_episode_channel(repository: Repository, *, learning_object_id: str, clock: Clock | None=None) -> EpisodeChannel` ([source](../../../../../../src/learnloop/diagnosis/probe_robust.py), line 75) — Resolve + freeze the coarse calibration channel for an episode (§4.2).
- `load_pinned_channel(repository: Repository, model_hash: str) -> EpisodeChannel | None` ([source](../../../../../../src/learnloop/diagnosis/probe_robust.py), line 162) — Rehydrate the pinned channel from its stored hash for replay (§2.2).
- `instrument_ensemble(channel: EpisodeChannel, instrument: CompiledInstrument, slot_map: Mapping[str, str], posterior: Mapping[str, float], *, episode_id: str | None) -> tuple[rc.Ensemble, str]` ([source](../../../../../../src/learnloop/diagnosis/probe_robust.py), line 199) — Build the deterministic composition ensemble for one candidate on the pinned channel.
- `coarse_emission(channel: EpisodeChannel, instrument: CompiledInstrument, *, observed_outcome: str, grader_confidence: float | None) -> str` ([source](../../../../../../src/learnloop/diagnosis/probe_robust.py), line 229) — The observed joint emission ``E = (coarse_G, confidence_bucket)`` (§3.2).
- `pinned_decision_posterior(channel: EpisodeChannel, instrument: CompiledInstrument, slot_map: Mapping[str, str], posterior_before: Mapping[str, float], *, observed_outcome: str, grader_confidence: float | None, episode_id: str | None) -> dict[str, object]` ([source](../../../../../../src/learnloop/diagnosis/probe_robust.py), line 244) — The immutable decision-time posterior snapshot (§4.2 product 1).
- `class RobustCandidate` ([source](../../../../../../src/learnloop/diagnosis/probe_robust.py), line 281)
- `robust_selection(channel: EpisodeChannel, candidates: Sequence[RobustCandidate], posterior: Mapping[str, float], *, episode_id: str | None) -> rc.RobustDecision` ([source](../../../../../../src/learnloop/diagnosis/probe_robust.py), line 288) — Robust candidate ranking + stop rule + agreement gate + abstention (§4.2).

### Module constants

- `EPISODE_COARSE_SCHEMA_SLUG` ([src/learnloop/diagnosis/probe_robust.py](../../../../../../src/learnloop/diagnosis/probe_robust.py), line 48)

## Internal implementation anchors

- `_persist_pinned_channel(repository: Repository, resolved: gc.ResolvedModel, schema_id: str, schema_version: int, *, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/diagnosis/probe_robust.py), line 117) — Content-address the pooled channel by its composite hash so :func:`load_pinned_channel` can rehydrate it for replay.
- `_decision_context_hash(*, episode_id: str | None, candidate_card_version: str | None, slot_map: Mapping[str, str], posterior: Mapping[str, float]) -> str` ([source](../../../../../../src/learnloop/diagnosis/probe_robust.py), line 183)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `RobustCandidate`, `instrument_ensemble`, `load_pinned_channel`, `pinned_decision_posterior`, `resolve_episode_channel`, `robust_selection`, `use_robust_probe`; statically calls `RobustCandidate`, `instrument_ensemble`, `load_pinned_channel`, `pinned_decision_posterior`, `resolve_episode_channel`, `robust_selection`, `use_robust_probe`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/grade_classifier|learnloop.attempts.grade_classifier]] — imports `bucket_confidence`; calls `bucket_confidence`
- [[Reference/Modules/learnloop/attempts/grader_calibration|learnloop.attempts.grader_calibration]] — imports `module`; calls `resolve_calibration_model`
- [[Reference/Modules/learnloop/attempts/outcome_schemas|learnloop.attempts.outcome_schemas]] — imports `SIGNATURE_ERROR_SLUG`, `resolve_schema_id`; calls `resolve_schema_id`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/probe_families|learnloop.diagnosis.probe_families]] — imports `CompiledInstrument`
- [[Reference/Modules/learnloop/diagnosis/probe_outcome_mapping|learnloop.diagnosis.probe_outcome_mapping]] — imports `PROBE_COARSE_MAPPING_VERSION`, `coarse_class_for_outcome`, `coarse_instrument_rows`; calls `coarse_class_for_outcome`, `coarse_instrument_rows`
- [[Reference/Modules/learnloop/diagnosis/robust_composition|learnloop.diagnosis.robust_composition]] — imports `module`; calls `build_ensemble`, `decision_context_hash`, `evaluate_selection`, `observed_update`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `P0_ALGORITHM_VERSION`, `P0_PROJECTION_VERSIONS`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_probe_robust_cutover.py](../../../../../../tests/test_probe_robust_cutover.py) — direct import
  - `test_robust_selection_abstains_on_indistinguishable_candidates`

## Modification guidance

- Change probe robust policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/probe_robust.py](../../../../../../src/learnloop/diagnosis/probe_robust.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
