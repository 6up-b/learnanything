---
title: "learnloop.scheduling.intent.followup_gate"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/intent/followup_gate.py"
source_paths:
  - "src/learnloop/scheduling/intent/followup_gate.py"
source_commit: "05ccb8b367cf492371e51689e92f13af089210fd"
source_commit_timestamp: "2026-10-31T21:18:38-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.scheduling.intent"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.scheduling.intent.followup_gate module"
  - "src/learnloop/scheduling/intent/followup_gate.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling-intent"
---

# `learnloop.scheduling.intent.followup_gate`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/intent/_package|learnloop.scheduling.intent]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.intent.followup_gate` exists within [[Reference/Modules/learnloop/scheduling/intent/_package|learnloop.scheduling.intent]] to own the behavior summarized by its module contract: The serve-time gate of Reader RW6b's automatic follow-ups (Codex review F1, F11).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/intent/followup_gate.py](../../../../../../../src/learnloop/scheduling/intent/followup_gate.py) |
| Source lines | 263 |
| Owning package | [[Reference/Modules/learnloop/scheduling/intent/_package|learnloop.scheduling.intent]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `05ccb8b367cf492371e51689e92f13af089210fd` |
| Commit timestamp | `2026-10-31T21:18:38-04:00` |

## Public API

- `independent_reasons(reasons: Iterable[str], *, intent: str, studied: Mapping[str, str | None] | None=None) -> list[str]` ([source](../../../../../../../src/learnloop/scheduling/intent/followup_gate.py), line 57) — The exposure reasons that exclude an independent check of ``intent``.
- `owning_retry(vault: Any, rows: Sequence[Mapping[str, Any]], *, facet_id: str, attempt_ids: Iterable[str], learning_object_ids: Iterable[str]) -> Mapping[str, Any] | None` ([source](../../../../../../../src/learnloop/scheduling/intent/followup_gate.py), line 81) — The repair ``cold_retry`` that owns this claim, or None (F11).
- `open_cold_retries(connection: Any, *, now: datetime) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/scheduling/intent/followup_gate.py), line 107) — Repair cold retries still pending or served (unexpired), oldest first.
- `line_licensing(line: Mapping[str, Any], provenance: Mapping[str, Any]) -> list[dict[str, Any]] | None` ([source](../../../../../../../src/learnloop/scheduling/intent/followup_gate.py), line 140) — The licensing questions a ``chosen`` line carries, or None when the line is inconsistent: its ``licensing`` list missing, empty or malformed (round 7, F20: no fallback to a single question; RW6b never landed, so no vault holds a line without one).
- `licensing_questions(connection: Any, provenance: Mapping[str, Any], commitment_id: str | None, item_id: str | None=None) -> tuple[list[dict[str, Any]], str | None]` ([source](../../../../../../../src/learnloop/scheduling/intent/followup_gate.py), line 154) — ALL the questions that license this check (round 6), read from its own ``chosen`` line, and ``LICENSING_UNREADABLE`` when the digest row or the line is missing or inconsistent (the caller holds the check).
- `followup_gate(vault: Any, repository: Any, *, item_id: str, provenance: Mapping[str, Any], valued_at: str, now: datetime, commitment_id: str | None=None, questions: Sequence[Mapping[str, Any]] | None=None) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/scheduling/intent/followup_gate.py), line 177) — Why a reader follow-up may not be served cold now, or None (it may).

### Module constants

- `VIA` ([src/learnloop/scheduling/intent/followup_gate.py](../../../../../../../src/learnloop/scheduling/intent/followup_gate.py), line 46)
- `_LABEL_ONLY_FOR_DISCRIMINATE` ([src/learnloop/scheduling/intent/followup_gate.py](../../../../../../../src/learnloop/scheduling/intent/followup_gate.py), line 49)
- `REPAIR_RETRY_OWNS` ([src/learnloop/scheduling/intent/followup_gate.py](../../../../../../../src/learnloop/scheduling/intent/followup_gate.py), line 50)
- `LICENSING_UNREADABLE` ([src/learnloop/scheduling/intent/followup_gate.py](../../../../../../../src/learnloop/scheduling/intent/followup_gate.py), line 127)

### Explicit exports

`__all__` declares:

- `LICENSING_UNREADABLE`
- `REPAIR_RETRY_OWNS`
- `VIA`
- `followup_gate`
- `independent_reasons`
- `licensing_questions`
- `line_licensing`
- `open_cold_retries`
- `owning_retry`

## Internal implementation anchors

- `_iso(moment: datetime) -> str` ([source](../../../../../../../src/learnloop/scheduling/intent/followup_gate.py), line 53)
- `_facets(vault: Any, item: Any) -> set[str]` ([source](../../../../../../../src/learnloop/scheduling/intent/followup_gate.py), line 77)
- `_primary(provenance: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/scheduling/intent/followup_gate.py), line 116)
- `_shape(entry: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/scheduling/intent/followup_gate.py), line 130) — A licensing question as the gate reads it (a line's ``licensing`` entry or a caller's).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]] — imports `REPAIR_RETRY_OWNS`, `followup_gate`, `open_cold_retries`, `owning_retry`; statically calls `followup_gate`, `open_cold_retries`, `owning_retry`
- [[Reference/Modules/learnloop/scheduling/intent/serving|learnloop.scheduling.intent.serving]] — imports `followup_gate`; statically calls `followup_gate`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/reader_digests|learnloop.db.stores.reader_digests]] — imports `digest_for_commitment`; calls `digest_for_commitment`
- [[Reference/Modules/learnloop/db/stores/source_service|learnloop.db.stores.source_service]] — imports `book_solution_span_ids`, `exercise_key`, `serve_time_exposure`; calls `book_solution_span_ids`, `exercise_key`, `serve_time_exposure`
- [[Reference/Modules/learnloop/serve_eligibility|learnloop.serve_eligibility]] — imports `COLD_RETRIEVAL_DELAY`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `datetime`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]], [[Reference/Modules/learnloop/scheduling/intent/serving|learnloop.scheduling.intent.serving]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_curriculum_c1_landing.py](../../../../../../../tests/test_curriculum_c1_landing.py) — direct import
  - `test_i_a_served_follow_up_is_a_planned_check_next_to_c1s_reading`
- [tests/test_reader_ca6_side_by_side.py](../../../../../../../tests/test_reader_ca6_side_by_side.py) — direct import
  - `test_a_side_by_side_read_holds_a_follow_up_on_a_shown_span_and_only_there`
- [tests/test_reader_followups_rereview.py](../../../../../../../tests/test_reader_followups_rereview.py) — direct import
  - `test_f1_a_related_example_does_not_mask_another_unjudged_one_for_a_discriminating_check`
  - `test_f1_reading_the_imported_exercises_book_solution_since_valuation_holds_the_check`
- [tests/test_reader_followups_review.py](../../../../../../../tests/test_reader_followups_review.py) — direct import
  - `test_f1_a_related_worked_example_is_only_a_label_for_a_discriminating_check`
- [tests/test_reader_followups_round6.py](../../../../../../../tests/test_reader_followups_round6.py) — direct import
  - `test_the_gate_reads_no_receipt_entry_and_no_answered_state`
- [tests/test_reader_rw6b_landing.py](../../../../../../../tests/test_reader_rw6b_landing.py) — direct import
  - `test_i_check_once_commitments_and_follow_ups_coexist_and_the_gate_touches_only_follow_ups`
  - `test_iii_a_ca5a_peek_of_the_items_source_span_holds_the_follow_up`

## Modification guidance

- Change followup gate policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/intent/followup_gate.py](../../../../../../../src/learnloop/scheduling/intent/followup_gate.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
