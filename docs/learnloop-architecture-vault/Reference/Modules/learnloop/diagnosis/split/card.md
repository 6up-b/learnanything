---
title: "learnloop.diagnosis.split.card"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/split/card.py"
source_paths:
  - "src/learnloop/diagnosis/split/card.py"
source_commit: "1acf79b2bd5f2014aca94a7b07cee2fa66175b02"
source_commit_timestamp: "2026-10-12T20:11:14-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis.split"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.split.card module"
  - "src/learnloop/diagnosis/split/card.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-split"
---

# `learnloop.diagnosis.split.card`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.split.card` exists within [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] to own the behavior summarized by its module contract: The M2 diagnosis card (Slice 1 §12.2).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/split/card.py](../../../../../../../src/learnloop/diagnosis/split/card.py) |
| Source lines | 482 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `1acf79b2bd5f2014aca94a7b07cee2fa66175b02` |
| Commit timestamp | `2026-10-12T20:11:14-04:00` |

## Public API

- `class CardError(ValueError)` ([source](../../../../../../../src/learnloop/diagnosis/split/card.py), line 80) — A tap that names no diagnosis, an unknown response or an unvalidated citation.
- `plain_summary(repository: Repository, text: str) -> str` ([source](../../../../../../../src/learnloop/diagnosis/split/card.py), line 137) — The diagnoser's ``analysis_md`` with record ids put in learner terms.
- `escalation_block(vault: LoadedVault, repository: Repository, diagnosis_id: str, repair_suggestions: list[Mapping[str, Any]]) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/diagnosis/split/card.py), line 156) — The escalated repair and its evidence, from the escalation receipt.
- `diagnosis_card(vault: LoadedVault, repository: Repository, attempt_id: str) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/split/card.py), line 222) — The card for one attempt (status first; content only when done).
- `record_card_tap(vault: LoadedVault, repository: Repository, *, attempt_id: str, diagnosis_id: str, response: str, cited_attempt_id: str | None=None, shown_at: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/split/card.py), line 312)
- `diagnosis_repairs_debited(repository: Repository, attempt_id: str, diagnosis_id: str) -> bool` ([source](../../../../../../../src/learnloop/diagnosis/split/card.py), line 386) — Were this diagnosis's displayed repairs already charged to the ledger?
- `debit_displayed_repairs(repository: Repository, *, attempt: Mapping[str, Any], diagnosis: Mapping[str, Any], repair_suggestions: list[Mapping[str, Any]], learning_object_id: str | None) -> int` ([source](../../../../../../../src/learnloop/diagnosis/split/card.py), line 396) — Reveal accounting when the diagnosis's repairs are displayed (§8).
- `debit_escalated_repairs(repository: Repository, *, attempt: Mapping[str, Any], repair_suggestions: list[Mapping[str, Any]], learning_object_id: str | None) -> int` ([source](../../../../../../../src/learnloop/diagnosis/split/card.py), line 435) — Charge each shown escalated repair once (basis ``repair_display:escalation:<diagnosis>``).

### Module constants

- `LOG` ([src/learnloop/diagnosis/split/card.py](../../../../../../../src/learnloop/diagnosis/split/card.py), line 48)
- `CARD_RESPONSES` ([src/learnloop/diagnosis/split/card.py](../../../../../../../src/learnloop/diagnosis/split/card.py), line 51)
- `CARD_LABELS` ([src/learnloop/diagnosis/split/card.py](../../../../../../../src/learnloop/diagnosis/split/card.py), line 52)
- `NOT_SAME_MISTAKE` ([src/learnloop/diagnosis/split/card.py](../../../../../../../src/learnloop/diagnosis/split/card.py), line 59)
- `ESCALATION_RESPONSES` ([src/learnloop/diagnosis/split/card.py](../../../../../../../src/learnloop/diagnosis/split/card.py), line 61)
- `ESCALATION_LABELS` ([src/learnloop/diagnosis/split/card.py](../../../../../../../src/learnloop/diagnosis/split/card.py), line 62)
- `_ORDINALS` ([src/learnloop/diagnosis/split/card.py](../../../../../../../src/learnloop/diagnosis/split/card.py), line 67)
- `_FORWARDABLE` ([src/learnloop/diagnosis/split/card.py](../../../../../../../src/learnloop/diagnosis/split/card.py), line 76)
- `PREREQUISITE_LABEL` ([src/learnloop/diagnosis/split/card.py](../../../../../../../src/learnloop/diagnosis/split/card.py), line 77)
- `_ULID` ([src/learnloop/diagnosis/split/card.py](../../../../../../../src/learnloop/diagnosis/split/card.py), line 134)

### Explicit exports

`__all__` declares:

- `CARD_LABELS`
- `CARD_RESPONSES`
- `ESCALATION_LABELS`
- `ESCALATION_RESPONSES`
- `CardError`
- `NOT_SAME_MISTAKE`
- `PREREQUISITE_LABEL`
- `debit_displayed_repairs`
- `debit_escalated_repairs`
- `diagnosis_card`
- `diagnosis_repairs_debited`
- `escalation_block`
- `record_card_tap`

## Internal implementation anchors

- `_ordinal(count: int) -> str` ([source](../../../../../../../src/learnloop/diagnosis/split/card.py), line 70)
- `_normalized(text: str) -> str` ([source](../../../../../../../src/learnloop/diagnosis/split/card.py), line 84)
- `_citations(repository: Repository, diagnosis_id: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/diagnosis/split/card.py), line 90)
- `_prerequisite_gap(vault: LoadedVault, proposal: Mapping[str, Any]) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/diagnosis/split/card.py), line 113)
- `_forward(vault: LoadedVault, repository: Repository, *, attempt_id: str, response: str, proposal: Mapping[str, Any], clock: Clock | None) -> tuple[str | None, str]` ([source](../../../../../../../src/learnloop/diagnosis/split/card.py), line 269) — Forward to an open factor's self-report channel; (factor id, note).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/learner_context|learnloop.learner_context]] — imports `plain_summary`; statically calls `plain_summary`
- [[Reference/Modules/learnloop_sidecar/handlers/diagnosis_card|learnloop_sidecar.handlers.diagnosis_card]] — imports `CardError`, `debit_displayed_repairs`, `diagnosis_card`, `record_card_tap`; statically calls `debit_displayed_repairs`, `diagnosis_card`, `record_card_tap`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `debit_escalated_repairs`, `diagnosis_repairs_debited`; statically calls `debit_escalated_repairs`, `diagnosis_repairs_debited`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/attempts/reveal_ledger|learnloop.attempts.reveal_ledger]] — imports `record_repair_display_reveals`; calls `record_repair_display_reveals`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `record_unresolved_cause_self_report`; calls `record_unresolved_cause_self_report`
- [[Reference/Modules/learnloop/diagnosis/misconceptions|learnloop.diagnosis.misconceptions]] — imports `normalize_text`; calls `normalize_text`
- [[Reference/Modules/learnloop/diagnosis/recurrence/display|learnloop.diagnosis.recurrence.display]] — imports `displayed_repair_suggestions`, `generated_repair`, `is_escalation_suggestion`; calls `displayed_repair_suggestions`, `generated_repair`, `is_escalation_suggestion`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `DONE`, `diagnosis_status`; calls `diagnosis_status`
- [[Reference/Modules/learnloop/diagnosis/split/validation|learnloop.diagnosis.split.validation]] — imports `primary_cause`; calls `primary_cause`
- [[Reference/Modules/learnloop/substrate/recurrence_groups|learnloop.substrate.recurrence_groups]] — imports `refresh_recurrence_groups`; calls `refresh_recurrence_groups`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `logging`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/learner_context|learnloop.learner_context]], [[Reference/Modules/learnloop_sidecar/handlers/diagnosis_card|learnloop_sidecar.handlers.diagnosis_card]], [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_diagnosis_card.py](../../../../../../../tests/test_diagnosis_card.py) — direct import
  - `test_card_summary_names_earlier_answers_by_date_not_id`
- [tests/test_diagnosis_reports.py](../../../../../../../tests/test_diagnosis_reports.py) — direct import
  - `test_m2_report_aggregates_without_learner_text`
- [tests/test_recurrence_live.py](../../../../../../../tests/test_recurrence_live.py) — direct import
  - `test_a_citation_of_an_existing_hypothesis_resolves_through_prior_hypothesis_id`
  - `test_a_generated_escalated_repair_is_validated_shown_like_any_repair_and_debited_once`
  - `test_a_not_the_same_mistake_tap_records_and_refreshes_without_blocking_a_citation`
  - `test_an_invalid_generated_repair_is_never_shown_as_a_different_approach`
  - `test_below_the_successor_there_is_no_judge_and_no_escalation`
  - `test_escalation_ratings_need_an_escalation`
  - `test_identical_repairs_three_times_obtain_a_different_one_at_escalation`
  - `test_the_escalation_card_switch_hides_the_block`
  - `test_the_judge_merges_reworded_recurrences_and_the_third_escalates`
  - `test_the_same_repair_again_is_labelled_honestly`

## Modification guidance

- Change card policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/split/card.py](../../../../../../../src/learnloop/diagnosis/split/card.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
