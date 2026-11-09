---
title: "learnloop.db.stores.reader_digests"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/reader_digests.py"
source_paths:
  - "src/learnloop/db/stores/reader_digests.py"
source_commit: "87fcec5a05cde9ac7f1eaf410972a7f0ae27841b"
source_commit_timestamp: "2026-11-01T01:07:22-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db.stores"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop.db.stores.reader_digests module"
  - "src/learnloop/db/stores/reader_digests.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.reader_digests`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.reader_digests` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Reader workbench RW6b: ``reader_session_digests`` (migration 227).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/reader_digests.py](../../../../../../../src/learnloop/db/stores/reader_digests.py) |
| Source lines | 151 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `87fcec5a05cde9ac7f1eaf410972a7f0ae27841b` |
| Commit timestamp | `2026-11-01T01:07:22-05:00` |

## Public API

- `insert_digest(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None` ([source](../../../../../../../src/learnloop/db/stores/reader_digests.py), line 34)
- `update_digest(connection: sqlite3.Connection, digest_id: str, **columns: Any) -> None` ([source](../../../../../../../src/learnloop/db/stores/reader_digests.py), line 48)
- `set_narrative(connection: sqlite3.Connection, digest_id: str, *, narrative_md: str | None, cited_event_ids: Sequence[str] | None, model: str, prompt_version: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/reader_digests.py), line 74) — Write the session's narrative once (RW6b part 2): True when written.
- `without_narrative(row: Mapping[str, Any] | None) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/reader_digests.py), line 92) — A decoded digest row without its narrative (part 1's comparisons).
- `digest(connection: sqlite3.Connection, digest_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/reader_digests.py), line 109)
- `digest_for_session(connection: sqlite3.Connection, extraction_id: str, session_key: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/reader_digests.py), line 114)
- `digests(connection: sqlite3.Connection, *, extraction_id: str | None=None, ended_after: str | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/reader_digests.py), line 121)
- `digest_for_commitment(connection: sqlite3.Connection, commitment_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/reader_digests.py), line 136)
- `session_keys(connection: sqlite3.Connection, extraction_ids: Sequence[str] | None=None) -> set[tuple[str, str]]` ([source](../../../../../../../src/learnloop/db/stores/reader_digests.py), line 143)

### Module constants

- `TABLE` ([src/learnloop/db/stores/reader_digests.py](../../../../../../../src/learnloop/db/stores/reader_digests.py), line 18)
- `STATUSES` ([src/learnloop/db/stores/reader_digests.py](../../../../../../../src/learnloop/db/stores/reader_digests.py), line 19)
- `MUTABLE_COLUMNS` ([src/learnloop/db/stores/reader_digests.py](../../../../../../../src/learnloop/db/stores/reader_digests.py), line 21)
- `_JSON_COLUMNS` ([src/learnloop/db/stores/reader_digests.py](../../../../../../../src/learnloop/db/stores/reader_digests.py), line 24)
- `NARRATIVE_COLUMNS` ([src/learnloop/db/stores/reader_digests.py](../../../../../../../src/learnloop/db/stores/reader_digests.py), line 65)
- `NARRATIVE_LABEL` ([src/learnloop/db/stores/reader_digests.py](../../../../../../../src/learnloop/db/stores/reader_digests.py), line 68)
- `NARRATIVE_AUTHORITY` ([src/learnloop/db/stores/reader_digests.py](../../../../../../../src/learnloop/db/stores/reader_digests.py), line 69)
- `NARRATIVE_KEYS` ([src/learnloop/db/stores/reader_digests.py](../../../../../../../src/learnloop/db/stores/reader_digests.py), line 71)

### Explicit exports

`__all__` declares:

- `MUTABLE_COLUMNS`
- `NARRATIVE_AUTHORITY`
- `NARRATIVE_COLUMNS`
- `NARRATIVE_KEYS`
- `NARRATIVE_LABEL`
- `STATUSES`
- `TABLE`
- `digest`
- `digest_for_commitment`
- `digest_for_session`
- `digests`
- `insert_digest`
- `session_keys`
- `set_narrative`
- `update_digest`
- `without_narrative`

## Internal implementation anchors

- `_dumps(value: Any) -> str` ([source](../../../../../../../src/learnloop/db/stores/reader_digests.py), line 30)
- `_decode(row: sqlite3.Row | Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/reader_digests.py), line 98)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/router_reader|learnloop.daily_plan.router_reader]] — imports `module`; statically calls `digests`
- [[Reference/Modules/learnloop/instructional/reader_digest|learnloop.instructional.reader_digest]] — imports `module`; statically calls `digest`, `digest_for_session`, `digests`, `insert_digest`, `set_narrative`
- [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]] — imports `module`; statically calls `digest`, `digest_for_commitment`, `digest_for_session`, `digests`, `insert_digest`, `update_digest`, `without_narrative`
- [[Reference/Modules/learnloop/scheduling/intent/followup_gate|learnloop.scheduling.intent.followup_gate]] — imports `digest_for_commitment`; statically calls `digest_for_commitment`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/router_reader|learnloop.daily_plan.router_reader]], [[Reference/Modules/learnloop/instructional/reader_digest|learnloop.instructional.reader_digest]], [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]], [[Reference/Modules/learnloop/scheduling/intent/followup_gate|learnloop.scheduling.intent.followup_gate]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_intent_checks.py](../../../../../../../tests/test_intent_checks.py) — direct import
  - `test_the_way_back_is_rendered_only_when_the_provenance_carries_it`
- [tests/test_narrative_rollback_overlap.py](../../../../../../../tests/test_narrative_rollback_overlap.py) — direct import
- [tests/test_reader_digest_narrative.py](../../../../../../../tests/test_reader_digest_narrative.py) — direct import
  - `test_the_narrative_is_written_once_even_when_two_writers_race`
  - `test_the_narrative_is_written_once_from_the_typed_summary_with_valid_citations`
  - `test_the_queue_build_narrates_a_session_with_follow_ups_off`
- [tests/test_reader_followups.py](../../../../../../../tests/test_reader_followups.py) — direct import
  - `test_the_kill_switch_creates_nothing_and_runs_no_revaluation`
- [tests/test_reader_followups_rereview.py](../../../../../../../tests/test_reader_followups_rereview.py) — direct import
  - `test_f13_a_failure_after_the_exposure_retirement_loses_neither_the_check_nor_the_re_ask`
  - `test_f3_two_resumptions_publishing_in_the_same_second_never_orphan_a_commitment`
- [tests/test_reader_followups_review.py](../../../../../../../tests/test_reader_followups_review.py) — direct import
  - `test_f1_an_impression_since_valuation_holds_the_check_and_revaluation_retires_and_re_asks`
  - `test_f3_a_failure_before_the_digest_is_written_leaves_no_orphan_commitment`
- [tests/test_reader_followups_round3.py](../../../../../../../tests/test_reader_followups_round3.py) — direct import
  - `test_round_2s_reconciliation_reason_is_gone`
- [tests/test_reader_followups_round4.py](../../../../../../../tests/test_reader_followups_round4.py) — direct import
  - `test_f16_a_shared_check_is_held_and_retired_by_retentions_rule`
- [tests/test_reader_followups_round5.py](../../../../../../../tests/test_reader_followups_round5.py) — direct import
  - `test_f17_revaluation_retires_an_unreadable_check_and_re_asks_what_it_can_name`
- [tests/test_reader_followups_round6.py](../../../../../../../tests/test_reader_followups_round6.py) — direct import
  - `test_a_malformed_licensing_list_is_held_as_unreadable`
  - `test_f18_re_planning_that_drops_a_question_keeps_the_shared_check_live_and_served`
- [tests/test_reader_followups_round7.py](../../../../../../../tests/test_reader_followups_round7.py) — direct import
  - `test_f19_a_publication_between_the_read_and_the_write_keeps_the_restored_license`
  - `test_f19_a_question_still_absent_from_the_fresh_receipt_is_pruned`
  - `test_f20_a_line_without_a_licensing_list_is_held_and_retired_as_unreadable`
- [tests/test_reader_followups_round8.py](../../../../../../../tests/test_reader_followups_round8.py) — direct import
  - `test_round8_a_changed_row_is_recomputed_and_the_second_pass_commits`
  - `test_round8_a_row_that_keeps_changing_is_left_for_the_next_pass`
  - `test_round8_a_scalar_licensing_is_unreadable_not_a_crash`
  - `test_round8_sols_interleaving_keeps_the_shared_check_live`
- [tests/test_reader_rw6b_p2_landing.py](../../../../../../../tests/test_reader_rw6b_p2_landing.py) — direct import
- [tests/test_reader_session_digests_migration.py](../../../../../../../tests/test_reader_session_digests_migration.py) — direct import
  - `test_the_digest_row_round_trips_and_one_session_has_one_row`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/reader_digests.py](../../../../../../../src/learnloop/db/stores/reader_digests.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
