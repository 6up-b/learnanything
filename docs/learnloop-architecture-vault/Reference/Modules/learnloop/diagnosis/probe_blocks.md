---
title: "learnloop.diagnosis.probe_blocks"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/probe_blocks.py"
source_paths:
  - "src/learnloop/diagnosis/probe_blocks.py"
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
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.probe_blocks` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Diagnostic block boundary semantics (spec_probe_eig_redesign.md §5.7).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/probe_blocks.py](../../../../../../src/learnloop/diagnosis/probe_blocks.py) |
| Source lines | 439 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `block_observation_rows(repository: Repository, episode: ProbeEpisodeRecord) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/probe_blocks.py), line 44) — The active block's observation rows: observations whose committed presentation belongs to the episode's active state segment.
- `block_complete(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, probe_presentation_id: str) -> bool` ([source](../../../../../../src/learnloop/diagnosis/probe_blocks.py), line 58) — Whether recording this presentation's observation closed the block.
- `evaluate_open_set_trigger(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, posterior: EpisodePosterior, *, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_blocks.py), line 98) — §6.3: when ``other_or_unknown`` becomes competitive, trigger the misconception review path — evaluated at block end, never per attempt.
- `build_typed_transition_decision(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, posterior: EpisodePosterior | None, *, first_error_step_or_claim: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/probe_blocks.py), line 188) — The §12.1 typed transition decision, persisted before tutor prose.
- `end_diagnostic_block(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord | str, *, ai_client: object | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/probe_blocks.py), line 262) — The §5.7 block-end hook.

### Module constants

- `OPEN_SET_REVIEW_CAPABILITY` ([src/learnloop/diagnosis/probe_blocks.py](../../../../../../src/learnloop/diagnosis/probe_blocks.py), line 41)
- `_TUTOR_MOVE_BY_ACTION` ([src/learnloop/diagnosis/probe_blocks.py](../../../../../../src/learnloop/diagnosis/probe_blocks.py), line 146)
- `_TUTOR_MOVE_BY_LABEL` ([src/learnloop/diagnosis/probe_blocks.py](../../../../../../src/learnloop/diagnosis/probe_blocks.py), line 158)

## Internal implementation anchors

- `_derive_tutor_move(top_label: str, top_probability: float, first_error: str | None, instructional_action: str | None) -> str` ([source](../../../../../../src/learnloop/diagnosis/probe_blocks.py), line 168)
- `_first_error_from_block(rows: list[dict[str, Any]]) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/probe_blocks.py), line 250) — First divergent step/claim from the block's structured traces (§8.2).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/probe_dialogue|learnloop.diagnosis.probe_dialogue]] — imports `end_diagnostic_block`; statically calls `end_diagnostic_block`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `_first_error_from_block`, `block_complete`, `block_observation_rows`, `build_typed_transition_decision`, `end_diagnostic_block`; statically calls `_first_error_from_block`, `block_complete`, `block_observation_rows`, `build_typed_transition_decision`, `end_diagnostic_block`
- [[Reference/Modules/learnloop/tui/screens/feedback|learnloop.tui.screens.feedback]] — imports `end_diagnostic_block`; statically calls `end_diagnostic_block`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `ProbeEpisodeRecord`, `Repository`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `claim_checked_feedback`; calls `claim_checked_feedback`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `common_repair_recommendation`, `run_deferred_block_repair_hooks`; calls `common_repair_recommendation`, `run_deferred_block_repair_hooks`
- [[Reference/Modules/learnloop/diagnosis/guided_redo|learnloop.diagnosis.guided_redo]] — imports `guided_redo_available`; calls `guided_redo_available`
- [[Reference/Modules/learnloop/diagnosis/misconceptions|learnloop.diagnosis.misconceptions]] — imports `normalize_and_resolve_attempt`; calls `normalize_and_resolve_attempt`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `EpisodePosterior`, `_evaluate_completion`, `_set_target_decision`, `episode_posterior`, `persist_episode_beliefs`; calls `_evaluate_completion`, `_set_target_decision`, `episode_posterior`, `persist_episode_beliefs`
- [[Reference/Modules/learnloop/diagnosis/probe_hypotheses|learnloop.diagnosis.probe_hypotheses]] — imports `H_OTHER`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/probe_dialogue|learnloop.diagnosis.probe_dialogue]], [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]], [[Reference/Modules/learnloop/tui/screens/feedback|learnloop.tui.screens.feedback]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_probe_block_end.py](../../../../../../tests/test_probe_block_end.py) — direct import
  - `test_block_end_repair_consultation_is_idempotent`
  - `test_end_diagnostic_block_noop_on_terminal_episode`
  - `test_open_set_trigger_fires_at_threshold_with_dedup`

## Modification guidance

- Change probe blocks policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/probe_blocks.py](../../../../../../src/learnloop/diagnosis/probe_blocks.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
