---
title: "learnloop.diagnosis.probe_blocks"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/probe_blocks.py"
source_paths:
  - "src/learnloop/diagnosis/probe_blocks.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.probe_blocks module"
  - "src/learnloop/diagnosis/probe_blocks.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.probe_blocks`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.probe_blocks` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Diagnostic block boundary semantics (spec_probe_eig_redesign.md §5.7).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/probe_blocks.py](../../../../../../src/learnloop/diagnosis/probe_blocks.py) |
| Source lines | 563 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `block_observation_rows(repository: Repository, episode: ProbeEpisodeRecord) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/probe_blocks.py), line 56) — The active block's observation rows: observations whose committed presentation belongs to the episode's active state segment.
- `block_complete(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, probe_presentation_id: str) -> bool` ([source](../../../../../../src/learnloop/diagnosis/probe_blocks.py), line 70) — Whether recording this presentation's observation closed the block.
- `evaluate_open_set_trigger(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, posterior: EpisodePosterior, *, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_blocks.py), line 161) — §6.3: when ``other_or_unknown`` becomes competitive, trigger the misconception review path — evaluated at block end, never per attempt.
- `build_typed_transition_decision(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, posterior: EpisodePosterior | None, *, first_error_step_or_claim: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/probe_blocks.py), line 251) — The §12.1 typed transition decision, persisted before tutor prose.
- `first_error_from_block(rows: list[dict[str, Any]]) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/probe_blocks.py), line 313) — First divergent step/claim from the block's structured traces (§8.2).
- `settle_block_answers(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, *, ai_client: object | None=None, clock: Clock | None=None) -> tuple[list[dict[str, Any]], list[str]]` ([source](../../../../../../src/learnloop/diagnosis/probe_blocks.py), line 325) — What the attempt pipeline deferred for the active block's committed answers: their withheld feedback (claim-checked), their normalization or blind diagnosis job, and their causal hooks.
- `stop_on_router_decision(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, *, router_decision_id: str, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/diagnosis/probe_blocks.py), line 453) — The probe router's stop on a router-owned episode between blocks (``daily_plan.probe_continuation``): the episode completes with ``router_stop``, and, as a block end that completes it, a diagnosed gap gets its typed transition decision and the tutoring segment.
- `end_diagnostic_block(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord | str, *, ai_client: object | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/probe_blocks.py), line 479) — The §5.7 block-end hook.

### Module constants

- `OPEN_SET_REVIEW_CAPABILITY` ([src/learnloop/diagnosis/probe_blocks.py](../../../../../../src/learnloop/diagnosis/probe_blocks.py), line 53)
- `_TUTOR_MOVE_BY_ACTION` ([src/learnloop/diagnosis/probe_blocks.py](../../../../../../src/learnloop/diagnosis/probe_blocks.py), line 209)
- `_TUTOR_MOVE_BY_LABEL` ([src/learnloop/diagnosis/probe_blocks.py](../../../../../../src/learnloop/diagnosis/probe_blocks.py), line 221)

## Internal implementation anchors

- `_next_observation_does_not_pay(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, rows: list[dict]) -> bool` ([source](../../../../../../src/learnloop/diagnosis/probe_blocks.py), line 126)
- `_derive_tutor_move(top_label: str, top_probability: float, first_error: str | None, instructional_action: str | None) -> str` ([source](../../../../../../src/learnloop/diagnosis/probe_blocks.py), line 231)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/probe_continuation|learnloop.daily_plan.probe_continuation]] — imports `stop_on_router_decision`; statically calls `stop_on_router_decision`
- [[Reference/Modules/learnloop/diagnosis/probe_controls|learnloop.diagnosis.probe_controls]] — imports `block_observation_rows`, `build_typed_transition_decision`, `first_error_from_block`, `settle_block_answers`; statically calls `block_observation_rows`, `build_typed_transition_decision`, `first_error_from_block`, `settle_block_answers`
- [[Reference/Modules/learnloop/diagnosis/probe_dialogue|learnloop.diagnosis.probe_dialogue]] — imports `end_diagnostic_block`; statically calls `end_diagnostic_block`
- [[Reference/Modules/learnloop/diagnosis/probe_evidence|learnloop.diagnosis.probe_evidence]] — imports `block_complete`, `end_diagnostic_block`; statically calls `block_complete`, `end_diagnostic_block`
- [[Reference/Modules/learnloop/tui/screens/feedback|learnloop.tui.screens.feedback]] — imports `end_diagnostic_block`; statically calls `end_diagnostic_block`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/probes|learnloop.db.stores.probes]] — imports `ProbeEpisodeRecord`
- [[Reference/Modules/learnloop/diagnosis/calibration_sessions|learnloop.diagnosis.calibration_sessions]] — imports `calibration_cap_lifted`; calls `calibration_cap_lifted`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `claim_checked_feedback`; calls `claim_checked_feedback`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `common_repair_recommendation`, `run_deferred_block_repair_hooks`; calls `common_repair_recommendation`, `run_deferred_block_repair_hooks`
- [[Reference/Modules/learnloop/diagnosis/guided_redo|learnloop.diagnosis.guided_redo]] — imports `guided_redo_available`; calls `guided_redo_available`
- [[Reference/Modules/learnloop/diagnosis/misconceptions|learnloop.diagnosis.misconceptions]] — imports `normalize_and_resolve_attempt`; calls `normalize_and_resolve_attempt`
- [[Reference/Modules/learnloop/diagnosis/probe_authority|learnloop.diagnosis.probe_authority]] — imports `router_selected_presentation`; calls `router_selected_presentation`
- [[Reference/Modules/learnloop/diagnosis/probe_completion|learnloop.diagnosis.probe_completion]] — imports `complete_on_router_stop`, `episode_maximum_binds`, `evaluate_completion`, `persist_episode_beliefs`, `set_target_decision`; calls `complete_on_router_stop`, `episode_maximum_binds`, `evaluate_completion`, `persist_episode_beliefs`, `set_target_decision`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `EpisodePosterior`, `effective_episode_observations`, `eligible_instruments`, `episode_posterior`, `session_qualifying_total`; calls `effective_episode_observations`, `eligible_instruments`, `episode_posterior`, `session_qualifying_total`
- [[Reference/Modules/learnloop/diagnosis/probe_hypotheses|learnloop.diagnosis.probe_hypotheses]] — imports `H_OTHER`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `enqueue_diagnosis`; calls `enqueue_diagnosis`
- [[Reference/Modules/learnloop/diagnosis/voi_stopping|learnloop.diagnosis.voi_stopping]] — imports `module`; calls `VoiContext`, `probe_episode_decision`, `voi_stopping_active`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/probe_continuation|learnloop.daily_plan.probe_continuation]], [[Reference/Modules/learnloop/diagnosis/probe_controls|learnloop.diagnosis.probe_controls]], [[Reference/Modules/learnloop/diagnosis/probe_dialogue|learnloop.diagnosis.probe_dialogue]], [[Reference/Modules/learnloop/diagnosis/probe_evidence|learnloop.diagnosis.probe_evidence]], [[Reference/Modules/learnloop/tui/screens/feedback|learnloop.tui.screens.feedback]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/probe_router_owned_helpers.py](../../../../../../tests/probe_router_owned_helpers.py) — direct import
- [tests/test_probe_block_end.py](../../../../../../tests/test_probe_block_end.py) — direct import
  - `test_block_end_repair_consultation_is_idempotent`
  - `test_end_diagnostic_block_noop_on_terminal_episode`
  - `test_open_set_trigger_fires_at_threshold_with_dedup`
- [tests/test_probe_router_authority.py](../../../../../../tests/test_probe_router_authority.py) — direct import
  - `test_j_a_generated_followups_block_ends_at_its_one_question_and_value_ends_any_other`

## Modification guidance

- Change probe blocks policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/probe_blocks.py](../../../../../../src/learnloop/diagnosis/probe_blocks.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
