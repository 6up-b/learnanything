---
title: "learnloop.diagnosis.diagnostic_gate"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/diagnostic_gate.py"
source_paths:
  - "src/learnloop/diagnosis/diagnostic_gate.py"
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
  - "learnloop.diagnosis.diagnostic_gate module"
  - "src/learnloop/diagnosis/diagnostic_gate.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.diagnostic_gate`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.diagnostic_gate` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Sim discrimination gate for generated diagnostics.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/diagnostic_gate.py](../../../../../../src/learnloop/diagnosis/diagnostic_gate.py) |
| Source lines | 514 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `request_diagnostic_trials(client: StructuredTransport, context: Any) -> DiagnosticTrials` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_gate.py), line 58) — Generate planted diagnostic trials through the structured transport.
- `request_diagnostic_fire(client: StructuredTransport, **context: Any) -> bool` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_gate.py), line 72) — Semantically judge one simulated diagnostic answer in memory.
- `class GateResult` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_gate.py), line 104) — Beta posteriors + acceptance verdict from a discrimination gate run (§6).
  - `sensitivity_lb(self, q: float=0.25) -> float` (line 122; public)
  - `specificity_lb(self, q: float=0.25) -> float` (line 125; public)
  - `as_dict(self) -> dict[str, Any]` (line 128; public)
- `run_discrimination_gate(vault: LoadedVault, repository: Repository, *, item: PracticeItem | dict[str, Any], misconception: MisconceptionRecord, grading_client: Any=None, trials: int | None=None, clock: Clock | None=None) -> GateResult` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_gate.py), line 260) — Estimate + persist an item's discrimination against ``misconception`` (§6).
- `backfill_discrimination_rows(vault: LoadedVault, repository: Repository, *, force: bool=False, clock: Clock | None=None) -> list[GateResult]` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_gate.py), line 440) — Seed measured discrimination rows for every keyed (item, misconception) pair.

### Module constants

- `_LOGGER` ([src/learnloop/diagnosis/diagnostic_gate.py](../../../../../../src/learnloop/diagnosis/diagnostic_gate.py), line 52)
- `_PUNCT_RE` ([src/learnloop/diagnosis/diagnostic_gate.py](../../../../../../src/learnloop/diagnosis/diagnostic_gate.py), line 54)
- `_WS_RE` ([src/learnloop/diagnosis/diagnostic_gate.py](../../../../../../src/learnloop/diagnosis/diagnostic_gate.py), line 55)
- `BACKFILL_SKIPPED_EXISTING` ([src/learnloop/diagnosis/diagnostic_gate.py](../../../../../../src/learnloop/diagnosis/diagnostic_gate.py), line 411)
- `BACKFILL_SKIPPED_UNREGISTERED` ([src/learnloop/diagnosis/diagnostic_gate.py](../../../../../../src/learnloop/diagnosis/diagnostic_gate.py), line 412)

## Internal implementation anchors

- `_normalize(text: str | None) -> str` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_gate.py), line 87)
- `_payload_field(item: PracticeItem | dict[str, Any], key: str) -> Any` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_gate.py), line 142)
- `_item_id(item: PracticeItem | dict[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_gate.py), line 148)
- `_expected_answer_text(item: PracticeItem | dict[str, Any]) -> str` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_gate.py), line 153)
- `_keyed_fatal_error_ids(item: PracticeItem | dict[str, Any], misconception_id: str) -> list[str]` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_gate.py), line 161) — Fatal-error ids on the item's rubric keyed to ``misconception_id`` (§5.2.3).
- `_keyed_fatal_descriptions(item: PracticeItem | dict[str, Any], misconception_id: str) -> list[dict[str, str]]` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_gate.py), line 185) — ``{id, description}`` for each fatal error keyed to ``misconception_id``.
- `_diagnostic_trials_context(item: PracticeItem | dict[str, Any], misconception: MisconceptionRecord, *, expected: str, misconception_consistent: str | None, n_trials: int) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_gate.py), line 212) — Token-frugal context for the codex answers-under-belief call (spec §6).
- `_keyed_fatal_fires(answer: str, *, expected: str, misconception_consistent: str | None, has_keyed_fatal: bool) -> bool` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_gate.py), line 233) — Whether the keyed fatal error fires on ``answer`` (deterministic grader).
- `_existing_row_gate_result(config: Any, row: ItemMisconceptionDiscrimination) -> GateResult` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_gate.py), line 415) — A read-only GateResult mirroring an existing discrimination row's verdict.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `BACKFILL_SKIPPED_EXISTING`, `BACKFILL_SKIPPED_UNREGISTERED`, `backfill_discrimination_rows`
- [[Reference/Modules/learnloop/content/authoring/persona_gate|learnloop.content.authoring.persona_gate]] — imports `normalize_answer`, `request_diagnostic_fire`; statically calls `normalize_answer`, `request_diagnostic_fire`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `GateResult`, `run_discrimination_gate`; statically calls `run_discrimination_gate`
- [[Reference/Modules/learnloop/content/synthesis/facet_mint_gate|learnloop.content.synthesis.facet_mint_gate]] — imports `normalize_answer`; statically calls `normalize_answer`
- [[Reference/Modules/learnloop/diagnosis/contrast_pairs|learnloop.diagnosis.contrast_pairs]] — imports `normalize_answer`; statically calls `normalize_answer`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_augmentation|learnloop.diagnosis.diagnostic_augmentation]] — imports `request_diagnostic_trials`; statically calls `request_diagnostic_trials`
- [[Reference/Modules/learnloop/diagnosis/error_hunt|learnloop.diagnosis.error_hunt]] — imports `normalize_answer`; statically calls `normalize_answer`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `normalize_answer`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `STRUCTURED_COMPLETION`, `StructuredTransport`, `execute_structured_operation`; calls `execute_structured_operation`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `ItemMisconceptionDiscrimination`, `MisconceptionRecord`, `Repository`; calls `ItemMisconceptionDiscrimination`
- [[Reference/Modules/learnloop/diagnosis/ai_contracts|learnloop.diagnosis.ai_contracts]] — imports `DiagnosticFireJudgment`, `DiagnosticTrials`, `diagnostic_fire_prompt`, `diagnostic_trials_prompt`; calls `diagnostic_fire_prompt`, `diagnostic_trials_prompt`
- [[Reference/Modules/learnloop/numeric|learnloop.numeric]] — imports `beta_quantile`; calls `beta_quantile`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`, `discriminates`; calls `discriminates`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `logging`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]], [[Reference/Modules/learnloop/content/authoring/persona_gate|learnloop.content.authoring.persona_gate]], [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]], [[Reference/Modules/learnloop/content/synthesis/facet_mint_gate|learnloop.content.synthesis.facet_mint_gate]], [[Reference/Modules/learnloop/diagnosis/contrast_pairs|learnloop.diagnosis.contrast_pairs]] and 3 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/structured_ai.py](../../../../../../tests/structured_ai.py) — direct import
- [tests/test_diagnostic_gate.py](../../../../../../tests/test_diagnostic_gate.py) — direct import
  - `test_backfill_creates_row_for_keyed_pair`
  - `test_backfill_force_reruns`
  - `test_backfill_skips_existing_row_without_force`
  - `test_backfill_skips_unregistered_misconception`
  - `test_discriminating_item_accepted_and_row_written`
  - `test_gate_writes_no_attempt_or_error_event_rows`
  - `test_llm_not_called_when_deterministic_rejects`
  - `test_llm_not_called_when_disabled`
  - `test_llm_trials_combine_into_beta_counts`
  - `test_llm_unavailable_falls_back_to_deterministic`
  - `test_paraphrase_rejected_low_sensitivity`
- [tests/test_provider_resolution_parity.py](../../../../../../tests/test_provider_resolution_parity.py) — direct import
  - `test_diagnostic_fire_uses_the_structured_completion_path`
- [tests/test_structured_transport_parity.py](../../../../../../tests/test_structured_transport_parity.py) — direct import

## Modification guidance

- Change diagnostic gate policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/diagnostic_gate.py](../../../../../../src/learnloop/diagnosis/diagnostic_gate.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
