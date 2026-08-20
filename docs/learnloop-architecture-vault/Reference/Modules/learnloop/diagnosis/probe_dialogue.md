---
title: "learnloop.diagnosis.probe_dialogue"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/probe_dialogue.py"
source_paths:
  - "src/learnloop/diagnosis/probe_dialogue.py"
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
  - "learnloop.diagnosis.probe_dialogue module"
  - "src/learnloop/diagnosis/probe_dialogue.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.probe_dialogue`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.probe_dialogue` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Short adaptive dialogue microprobes (spec_probe_eig_redesign.md §8.1).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/probe_dialogue.py](../../../../../../src/learnloop/diagnosis/probe_dialogue.py) |
| Source lines | 450 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `request_probe_dialogue_turn(client: StructuredTransport, context: ProbeDialogueTurnContext) -> ProbeDialogueTurn` ([source](../../../../../../src/learnloop/diagnosis/probe_dialogue.py), line 64) — Generate one adaptive dialogue turn through the shared transport.
- `class DialogueBlockError(ValueError)` ([source](../../../../../../src/learnloop/diagnosis/probe_dialogue.py), line 77)
- `class DialogueTurn` ([source](../../../../../../src/learnloop/diagnosis/probe_dialogue.py), line 82)
  - `as_dict(self) -> dict[str, Any]` (line 89; public)
- `class DialogueBlockState` ([source](../../../../../../src/learnloop/diagnosis/probe_dialogue.py), line 100) — Serializable dialogue-block state (mirrors the teach-back pattern).
  - `to_json(self) -> str` (line 110; public)
  - `from_json(cls, payload: str) -> 'DialogueBlockState'` (line 123; public)
  - `completed_turns(self) -> int` (line 144; public)
- `begin_dialogue_block(vault: LoadedVault, repository: Repository, learning_object_id: str, *, clock: Clock | None=None) -> DialogueBlockState` ([source](../../../../../../src/learnloop/diagnosis/probe_dialogue.py), line 148) — Open a dialogue block against the LO's in-progress episode (§8.1).
- `next_dialogue_turn(vault: LoadedVault, repository: Repository, state: DialogueBlockState, *, ai_client: object | None=None, clock: Clock | None=None) -> tuple[DialogueBlockState, dict[str, Any] | None]` ([source](../../../../../../src/learnloop/diagnosis/probe_dialogue.py), line 180) — Mint and commit the next turn: ephemeral instance + presentation.
- `record_turn_submitted(state: DialogueBlockState, presentation_id: str) -> DialogueBlockState` ([source](../../../../../../src/learnloop/diagnosis/probe_dialogue.py), line 415)
- `end_dialogue_block(vault: LoadedVault, repository: Repository, state: DialogueBlockState, *, ai_client: object | None=None, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_dialogue.py), line 422) — Block boundary (§5.7): invalidate any unsubmitted turn presentation, then run the ordered block-end hook — release withheld feedback, normalize the block's misconceptions, evaluate the open-set trigger and the completion policy, and route (probe_blocks.end_diagnostic_block).

### Module constants

- `DIALOGUE_TURN_KINDS` ([src/learnloop/diagnosis/probe_dialogue.py](../../../../../../src/learnloop/diagnosis/probe_dialogue.py), line 58)
- `DIALOGUE_PRACTICE_MODE` ([src/learnloop/diagnosis/probe_dialogue.py](../../../../../../src/learnloop/diagnosis/probe_dialogue.py), line 59)
- `_KIND_TO_SURFACE_INDEX` ([src/learnloop/diagnosis/probe_dialogue.py](../../../../../../src/learnloop/diagnosis/probe_dialogue.py), line 61)

## Internal implementation anchors

- `_dialogue_prompt_version() -> str` ([source](../../../../../../src/learnloop/diagnosis/probe_dialogue.py), line 339)
- `_prior_turns_with_answers(repository: Repository, state: DialogueBlockState) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/probe_dialogue.py), line 345) — The block so far as {kind, prompt_md, learner_answer_md}, oldest first.
- `_adaptive_turn_surface(vault: LoadedVault, repository: Repository, state: DialogueBlockState, card, kind: str, *, ai_client: object | None) -> tuple[str, str] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_dialogue.py), line 370) — LLM-generated (prompt, expected_answer) for one turn, or None to fall back to the parametric template (§8.1 adaptive dialogue).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/calibration|learnloop_sidecar.handlers.calibration]] — imports `DialogueBlockError`, `DialogueBlockState`, `begin_dialogue_block`, `end_dialogue_block`, `next_dialogue_turn`, `record_turn_submitted`; statically calls `begin_dialogue_block`, `end_dialogue_block`, `next_dialogue_turn`, `record_turn_submitted`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `CodexUnavailable`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `StructuredTransport`, `execute_structured_operation`; calls `execute_structured_operation`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/ai_contracts|learnloop.diagnosis.ai_contracts]] — imports `PROBE_DIALOGUE_TURN_PROMPT_VERSION`, `ProbeDialogueTurn`, `ProbeDialogueTurnContext`, `probe_dialogue_turn_prompt`; calls `ProbeDialogueTurnContext`, `probe_dialogue_turn_prompt`
- [[Reference/Modules/learnloop/diagnosis/probe_blocks|learnloop.diagnosis.probe_blocks]] — imports `end_diagnostic_block`; calls `end_diagnostic_block`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `EligibleInstrument`, `commit_presentation`, `episode_hypothesis_set`, `serve_presentation`; calls `EligibleInstrument`, `commit_presentation`, `episode_hypothesis_set`, `serve_presentation`
- [[Reference/Modules/learnloop/diagnosis/probe_families|learnloop.diagnosis.probe_families]] — imports `DIALOGUE_MICROPROBE_V1`, `map_episode_labels_to_slots`, `real_calibration_counts`, `validate_and_compile_card`; calls `map_episode_labels_to_slots`, `real_calibration_counts`, `validate_and_compile_card`
- [[Reference/Modules/learnloop/diagnosis/probe_instance_generation|learnloop.diagnosis.probe_instance_generation]] — imports `GENERATOR_ID`, `GENERATOR_VERSION`, `LLM_GENERATOR_ID`, `LLM_GENERATOR_VERSION`, `ensure_instrument_card`, `instance_gate_errors`, `parametric_instance_payloads`; calls `ensure_instrument_card`, `instance_gate_errors`, `parametric_instance_payloads`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/vault/writer|learnloop.vault.writer]] — imports `upsert_practice_item`; calls `upsert_practice_item`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/calibration|learnloop_sidecar.handlers.calibration]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_probe_dialogue.py](../../../../../../tests/test_probe_dialogue.py) — direct import
  - `test_adaptive_llm_turn_conditions_on_prior_answers`
  - `test_adaptive_turn_falls_back_to_parametric_on_failure_or_leak`
  - `test_dialogue_observation_replays_to_its_persisted_weighted_posterior`
  - `test_dialogue_state_round_trips_through_json`
  - `test_dialogue_turns_persist_presentation_attempt_observation`
  - `test_end_dialogue_block_invalidates_unsubmitted_turn_and_segments`
  - `test_second_dialogue_block_on_same_lo_can_open`
- [tests/test_structured_transport_parity.py](../../../../../../tests/test_structured_transport_parity.py) — direct import

## Modification guidance

- Change probe dialogue policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/probe_dialogue.py](../../../../../../src/learnloop/diagnosis/probe_dialogue.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
