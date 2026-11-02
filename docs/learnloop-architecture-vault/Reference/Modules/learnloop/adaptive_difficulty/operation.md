---
title: "learnloop.adaptive_difficulty.operation"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/operation.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/operation.py"
source_commit: "357909efe74bc22fe557de06724aa48088bc5990"
source_commit_timestamp: "2026-10-27T14:15:10-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.adaptive_difficulty"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.adaptive_difficulty.operation module"
  - "src/learnloop/adaptive_difficulty/operation.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.operation`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.operation` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: Guarded AD operations: A8 by construction at the data sources (the AD23 redesign, Option B).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/operation.py](../../../../../../src/learnloop/adaptive_difficulty/operation.py) |
| Source lines | 796 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `357909efe74bc22fe557de06724aa48088bc5990` |
| Commit timestamp | `2026-10-27T14:15:10-04:00` |

## Public API

- `class GuardDenied(RuntimeError)` ([source](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 82) — A read or write the AD guard refused inside an operation (A8): AD is unavailable for it.
- `class OperationPoisoned(GuardDenied)` ([source](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 86) — An operation in which the guard refused something: its output may not be used, whatever the code inside did with the refusal.
- `class Guard` ([source](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 92) — The operation's SQLite authorizer (see the module docstring).
  - `__post_init__(self) -> None` (line 121; internal)
  - `_statement_started(self, sql: Any) -> None` (line 125; internal) — SQLite's trace: a statement began running, after its preparation (round 6).
  - `authorize(self, action: int, arg1: Any, arg2: Any, database: Any, source: Any) -> int` (line 139; public)
  - `_write_access(self, table: str, column: str | None) -> bool` (line 172; internal)
  - `_read(self, table: str, database: Any, column: str | None=None) -> int` (line 179; internal)
  - `_write(self, table: str, verb: str) -> int` (line 217; internal)
  - `_deny(self, verb: str, table: str, why: str, reader: str) -> int` (line 232; internal)
  - `install(self, connection: Any) -> None` (line 249; public)
  - `refresh(self) -> None` (line 263; public) — Expire every guarded connection's statement cache (by re-installing the authorizer).
  - `remove(self, connection: Any) -> None` (line 275; public)
- `class Scope(str, Enum)` ([source](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 299) — The rules' read scopes, closed (the final round): the material view's readers, the derivation of a visible reading's stored structure, and the held-out predicate's own inputs.
- `class ViewFailure(RuntimeError)` ([source](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 311) — A failure inside a rules scope, as it leaves the scope: its kind (``error`` or ``denied``) and the failing exception's type name, nothing else (no cause, no context, no inner frames; the final round's codec, :func:`scoped`).
- `class ViewDenied(ViewFailure, GuardDenied)` ([source](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 317) — The guard's refusal inside a rules scope, as it leaves the scope (still a denial).
- `scoped(scope: Scope, run: Callable[[], Any]) -> Any` ([source](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 321) — ``run()`` inside the rules scope ``scope``; any exception leaving it becomes a :class:`ViewFailure` (or :class:`ViewDenied`) carrying only its kind and type name, raised OUTSIDE the ``except`` clause so that neither ``__cause__`` nor ``__context__`` points at the original (``rai…
- `class Operation` ([source](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 416) — One AD operation (see the module docstring).
  - `available(self) -> bool` (line 428; public)
- `current() -> Operation | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 432) — The operation open in this context, if any.
- `epoch_of(view: Any) -> str | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 438) — The protection epoch of a material view (:meth:`MaterialView.epoch`): a digest of everything its projection withholds.
- `rules(name: Scope) -> Iterator[None]` ([source](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 450) — The rules' read scope: protected tables may be read (the rules' own SQL carries :data:`RULES_MARKER`).
- `own_write(table: str) -> Iterator[None]` ([source](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 479) — A store writer's own idempotency read of the AD table it writes (its existence check before the insert): allowed for that table only, and only around the writer's call.
- `suspended() -> Iterator[None]` ([source](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 499) — Leave the operation for a deliberate egress (the AD23 redesign): the send guard re-reads the predicate afresh at each request by design, and a model call may run the incumbent's own work (a reload's maintenance), which never runs inside an operation.
- `ad_operation(vault: Any, repository: Any, *, protected: Any=None, connections: tuple[Any, ...]=(), mode: str | None=None, name: str | None=None, savepoint: bool=False, read_only: bool=False) -> Iterator[Operation]` ([source](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 540) — Open (or join) the operation for this database (see the module docstring).
- `optional_operation(vault: Any, repository: Any, *, savepoint: bool=False, read_only: bool=False) -> Iterator[Operation | None]` ([source](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 683) — The operation, or None with adaptive difficulty off (then nothing opens).
- `is_denial(exc: BaseException) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 697) — Whether an exception is the guard's refusal (SQLite's "not authorized" for a statement, "access to <table>.<column> is prohibited" for a column read), or an AD reader's refusal to read a withheld record it would otherwise reuse (:class:`GuardDenied`).
- `entry(func: Callable[..., Any] | None=None, *, poisoned: Callable[[Mapping[str, Any]], Any] | None=None, savepoint: bool=False, read_only: bool=False, durable: str | None=None) -> Any` ([source](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 714) — Run an AD entry point inside an operation: its ``vault`` and ``repository`` arguments are replaced by the operation's, its ``view`` (when it takes one and none was given) by the operation's view, and a ``connection`` it was handed carries the guard.

### Module constants

- `LOG` ([src/learnloop/adaptive_difficulty/operation.py](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 67)
- `EPOCH_VERSION` ([src/learnloop/adaptive_difficulty/operation.py](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 70)
- `RULES_MARKER` ([src/learnloop/adaptive_difficulty/operation.py](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 72)
- `_CURRENT` ([src/learnloop/adaptive_difficulty/operation.py](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 74)
- `_IN_RULES` ([src/learnloop/adaptive_difficulty/operation.py](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 75)
- `_OWN_WRITE` ([src/learnloop/adaptive_difficulty/operation.py](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 76)
- `_READ` ([src/learnloop/adaptive_difficulty/operation.py](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 78)
- `_WRITES` ([src/learnloop/adaptive_difficulty/operation.py](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 79)
- `UPDATE_SELECT` ([src/learnloop/adaptive_difficulty/operation.py](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 286)
- `RETURNING` ([src/learnloop/adaptive_difficulty/operation.py](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 287)
- `_RETURNING_RE` ([src/learnloop/adaptive_difficulty/operation.py](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 288)
- `_SQL_NOISE_RE` ([src/learnloop/adaptive_difficulty/operation.py](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 289)
- `DERIVE` ([src/learnloop/adaptive_difficulty/operation.py](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 308)
- `DERIVED_READ` ([src/learnloop/adaptive_difficulty/operation.py](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 338)
- `CONTENT_READ` ([src/learnloop/adaptive_difficulty/operation.py](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 340)
- `POISONED` ([src/learnloop/adaptive_difficulty/operation.py](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 342)
- `_SCHEMA_FACTS` ([src/learnloop/adaptive_difficulty/operation.py](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 344)
- `_MODE` ([src/learnloop/adaptive_difficulty/operation.py](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 648)
- `DENIALS` ([src/learnloop/adaptive_difficulty/operation.py](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 658)
- `OBSERVERS` ([src/learnloop/adaptive_difficulty/operation.py](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 664)
- `WRITE_FORMS` ([src/learnloop/adaptive_difficulty/operation.py](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 710)
- `_READ_ONLY` ([src/learnloop/adaptive_difficulty/operation.py](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 711)

### Explicit exports

`__all__` declares:

- `EPOCH_VERSION`
- `GuardDenied`
- `OBSERVERS`
- `Operation`
- `OperationPoisoned`
- `RULES_MARKER`
- `ad_operation`
- `current`
- `Scope`
- `ViewDenied`
- `ViewFailure`
- `denial_count`
- `entry`
- `epoch_of`
- `is_denial`
- `scoped`
- `optional_operation`
- `own_write`
- `rules`
- `suspended`

## Internal implementation anchors

- `_bare_sql(sql: str) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 292) — A statement without its literals, quoted identifiers and comments.
- `_schema_facts(raw: Any, database: Path) -> tuple[frozenset[str], dict[str, frozenset[tuple[str, str]]]]` ([source](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 347) — The schema's trigger names, and per AD-writable table the KEY COLUMNS its declared foreign keys read, as ``(table, column)``: its parents' referenced keys, and the children's referencing columns (cached per schema version).
- `_entry_name() -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 381)
- `_stack_modules() -> tuple[str, ...]` ([source](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 392)
- `_reader() -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 403) — The innermost LearnLoop module (outside the database layer and this module) on the stack.
- `_no_hook() -> Iterator[None]` ([source](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 525)
- `_same_database(op: Operation, repository: Any) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 532)
- `_operation(vault: Any, repository: Any, *, protected: Any=None, connections: tuple[Any, ...]=(), mode: str | None=None, name: str | None=None) -> Iterator[Operation]` ([source](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 579)
- `_default_mode() -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 651)
- `_record_denials(op: Operation) -> None` ([source](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 667)
- `_is_protection(value: Any) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/operation.py), line 787)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/arms|learnloop.adaptive_difficulty.arms]] — imports `entry`; statically calls `entry`
- [[Reference/Modules/learnloop/adaptive_difficulty/backfill|learnloop.adaptive_difficulty.backfill]] — imports `entry`; statically calls `entry`
- [[Reference/Modules/learnloop/adaptive_difficulty/background|learnloop.adaptive_difficulty.background]] — imports `ad_operation`, `entry`, `epoch_of`; statically calls `ad_operation`, `entry`, `epoch_of`
- [[Reference/Modules/learnloop/adaptive_difficulty/dose|learnloop.adaptive_difficulty.dose]] — imports `entry`, `is_denial`; statically calls `entry`, `is_denial`
- [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]] — imports `entry`; statically calls `entry`
- [[Reference/Modules/learnloop/adaptive_difficulty/generation|learnloop.adaptive_difficulty.generation]] — imports `entry`, `own_write`; statically calls `entry`, `own_write`
- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `EPOCH_VERSION`, `Scope`, `current`, `scoped`; statically calls `current`, `scoped`
- [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]] — imports `entry`, `epoch_of`; statically calls `entry`, `epoch_of`
- [[Reference/Modules/learnloop/adaptive_difficulty/projection|learnloop.adaptive_difficulty.projection]] — imports `epoch_of`; statically calls `epoch_of`
- [[Reference/Modules/learnloop/adaptive_difficulty/protection|learnloop.adaptive_difficulty.protection]] — imports `Scope`, `scoped`; statically calls `scoped`
- [[Reference/Modules/learnloop/adaptive_difficulty/readiness|learnloop.adaptive_difficulty.readiness]] — imports `entry`; statically calls `entry`
- [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]] — imports `entry`; statically calls `entry`
- [[Reference/Modules/learnloop/adaptive_difficulty/relatedness|learnloop.adaptive_difficulty.relatedness]] — imports `current`, `entry`, `epoch_of`, `own_write`; statically calls `current`, `entry`, `epoch_of`, `own_write`
- [[Reference/Modules/learnloop/adaptive_difficulty/relatedness_jobs|learnloop.adaptive_difficulty.relatedness_jobs]] — imports `entry`; statically calls `entry`
- [[Reference/Modules/learnloop/adaptive_difficulty/replay|learnloop.adaptive_difficulty.replay]] — imports `entry`, `epoch_of`; statically calls `entry`, `epoch_of`
- [[Reference/Modules/learnloop/adaptive_difficulty/report|learnloop.adaptive_difficulty.report]] — imports `entry`; statically calls `entry`
- [[Reference/Modules/learnloop/adaptive_difficulty/scoring|learnloop.adaptive_difficulty.scoring]] — imports `entry`; statically calls `entry`
- [[Reference/Modules/learnloop/adaptive_difficulty/sending|learnloop.adaptive_difficulty.sending]] — imports `suspended`; statically calls `suspended`
- [[Reference/Modules/learnloop/adaptive_difficulty/serve|learnloop.adaptive_difficulty.serve]] — imports `entry`; statically calls `entry`
- [[Reference/Modules/learnloop/adaptive_difficulty/serving|learnloop.adaptive_difficulty.serving]] — imports `GuardDenied`, `entry`, `is_denial`; statically calls `GuardDenied`, `entry`, `is_denial`
- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `is_denial`; statically calls `is_denial`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `ad_operation`, `is_denial`; statically calls `ad_operation`, `is_denial`
- [[Reference/Modules/learnloop/daily_plan/ad_slot|learnloop.daily_plan.ad_slot]] — imports `ad_operation`, `is_denial`; statically calls `ad_operation`, `is_denial`
- [[Reference/Modules/learnloop_sidecar/handlers/adaptive_difficulty|learnloop_sidecar.handlers.adaptive_difficulty]] — imports `is_denial`, `optional_operation`; statically calls `is_denial`, `optional_operation`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/column_classes|learnloop.adaptive_difficulty.column_classes]] — imports `module`; calls `column_class`
- [[Reference/Modules/learnloop/adaptive_difficulty/denial_log|learnloop.adaptive_difficulty.denial_log]] — imports `append_denials`, `denial_count`, `denial_log_path`; calls `append_denials`
- [[Reference/Modules/learnloop/adaptive_difficulty/logs|learnloop.adaptive_difficulty.logs]] — imports `warn_failure`; calls `warn_failure`
- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `MaterialView`, `detached_view`; calls `detached_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/projection|learnloop.adaptive_difficulty.projection]] — imports `project_repository`, `project_vault`; calls `project_repository`, `project_vault`
- [[Reference/Modules/learnloop/adaptive_difficulty/protected_tables|learnloop.adaptive_difficulty.protected_tables]] — imports `module`; calls `read_verdict`, `role`, `write_verdict`
- [[Reference/Modules/learnloop/adaptive_difficulty/protection|learnloop.adaptive_difficulty.protection]] — imports `Protection`
- [[Reference/Modules/learnloop/adaptive_difficulty/switches|learnloop.adaptive_difficulty.switches]] — imports `ad_enabled`; calls `ad_enabled`
- [[Reference/Modules/learnloop/ai/plan_fallback|learnloop.ai.plan_fallback]] — imports `module`; calls `quiet`
- [[Reference/Modules/learnloop/db/scopes|learnloop.db.scopes]] — imports `connection_hook`; calls `connection_hook`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `vault_loads_forbidden`; calls `vault_loads_forbidden`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `contextvars`, `copy`, `dataclasses`, `enum`, `functools`, `hashlib`, `inspect`, `logging`, `pathlib`, `re`, `sqlite3`, `sys`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/arms|learnloop.adaptive_difficulty.arms]], [[Reference/Modules/learnloop/adaptive_difficulty/backfill|learnloop.adaptive_difficulty.backfill]], [[Reference/Modules/learnloop/adaptive_difficulty/background|learnloop.adaptive_difficulty.background]], [[Reference/Modules/learnloop/adaptive_difficulty/dose|learnloop.adaptive_difficulty.dose]], [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]] and 19 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/ad_reachable_reads.py](../../../../../../tests/ad_reachable_reads.py) — direct import
- [tests/test_ad23_contract.py](../../../../../../tests/test_ad23_contract.py) — direct import
- [tests/test_ad23_fix_r8.py](../../../../../../tests/test_ad23_fix_r8.py) — direct import
  - `test_a_withheld_items_facet_never_enters_the_facet_maps_or_the_reading_map`
- [tests/test_ad23_intent_compose.py](../../../../../../tests/test_ad23_intent_compose.py) — direct import
- [tests/test_ad23_inversion.py](../../../../../../tests/test_ad23_inversion.py) — direct import
  - `test_a_failure_inside_a_scope_leaves_with_no_cause_context_or_text`
  - `test_high2_a_rules_scope_by_any_name_but_a_scope_member_is_refused`
  - `test_no_incumbent_privilege_exists_inside_an_ad_operation`
- [tests/test_ad23_pool_membership.py](../../../../../../tests/test_ad23_pool_membership.py) — direct import
- [tests/test_ad23_t1_routes.py](../../../../../../tests/test_ad23_t1_routes.py) — direct import
  - `test_inside_an_ad_operation_no_route_asks_and_no_grant_serves`
- [tests/test_ad_denial_log.py](../../../../../../tests/test_ad_denial_log.py) — direct import
  - `test_a_new_denial_line_names_the_refused_operation`
  - `test_a_refused_upgrade_leaves_the_log_in_place`
  - `test_a_successful_upgrade_archives_the_log_and_the_report_counts_from_zero`
  - `test_f1_a_denial_after_the_upgrade_returned_stays_live`
  - `test_old_format_lines_stay_readable_and_are_grouped_as_unrecorded`
  - `test_v2_f1_an_unmarked_upgrade_leaves_the_log_live`
- [tests/test_ad_epoch.py](../../../../../../tests/test_ad_epoch.py) — direct import
  - `test_the_replay_cache_and_the_alias_memo_are_keyed_by_the_epoch`
- [tests/test_ad_guard.py](../../../../../../tests/test_ad_guard.py) — direct import
  - `test_a_cached_ad_write_is_refused_once_the_operation_is_poisoned`
  - `test_a_planted_read_swallowed_in_the_dose_decision_yields_no_decision_and_no_rows`
  - `test_a_raw_read_of_a_content_column_of_a_neutral_table_is_refused`
  - `test_a_read_only_entry_point_cannot_write`
  - `test_a_statement_prepared_in_own_write_is_not_reused_outside_it`
  - `test_a_swallowed_denial_poisons_the_operation`
  - `test_a_write_context_never_outlives_its_statement`
  - `test_a_write_reads_its_target_and_foreign_keys_freely`
  - `test_a_write_reads_only_its_own_target_and_declared_constraints`
  - `test_a_write_then_a_swallowed_denial_then_an_early_return_keeps_no_ad_rows`
  - `test_a_write_to_a_table_ad_does_not_own_is_refused`
  - `test_a_write_with_returning_poisons_the_operation_and_rolls_back`
  - `test_a_writes_foreign_key_allowance_covers_its_key_columns_only`
  - `test_an_exam_reserved_items_contract_is_read_only_through_the_rules`
  - `test_an_incumbent_model_calls_text_is_unreadable_raw_while_its_accounting_is`
  - `test_an_unclassified_table_is_refused_in_every_scope`
  - `test_an_update_with_a_subquery_set_or_a_from_clause_is_refused`
  - `test_every_ad_entry_point_declares_its_write_form_and_writers_use_the_savepoint_form`
  - `test_in_the_incumbent_scope_only_its_named_readers_read_content`
  - `test_incumbent_maintenance_and_vault_loads_never_run_inside_an_operation`
  - `test_negative_control_with_the_guard_disabled_the_planted_read_check_fails`
  - `test_the_pinned_connection_carries_the_guard_only_inside_the_operation`
  - `test_the_rules_never_read_a_derived_column_outside_its_derivation`
  - `test_the_rules_read_a_content_column_inside_an_operation`
- [tests/test_ad_guard_offer_receipts.py](../../../../../../tests/test_ad_guard_offer_receipts.py) — direct import
  - `test_rebuild_derived_state_over_a_learner_pick_runs_with_zero_denials`
  - `test_the_fix_changes_serving_on_the_affected_shape_and_the_switches_restore_the_refusal_state`
  - `test_the_receipt_stays_refused_outside_the_rules`
  - `test_the_view_labels_the_pick_as_field_does_outside_ad`
- [tests/test_ad_guard_reachable_reads.py](../../../../../../tests/test_ad_guard_reachable_reads.py) — direct import
  - `test_every_serving_branch_runs_with_zero_denials_and_fields_labels`
- [tests/test_ad_projection.py](../../../../../../tests/test_ad_projection.py) — direct import
  - `test_a_mixed_reading_gives_no_reading_signal_as_if_deleted`
  - `test_a_whole_extraction_held_out_reads_as_no_extraction`
  - `test_every_protected_table_reads_as_in_the_absent_copy`
- [tests/test_ad_protected_readings.py](../../../../../../tests/test_ad_protected_readings.py) — direct import
  - `test_a_clean_reading_is_read_as_the_reader_and_the_incumbent_read_it`
  - `test_a_practice_interaction_event_is_not_a_reading_event`
  - `test_a_reader_question_anchored_by_note_on_a_mixed_reading_is_withheld`
  - `test_an_item_from_a_visible_span_of_a_mixed_reading_is_not_over_withheld`
  - `test_attempt_evidence_from_a_visible_span_of_a_mixed_reading_is_unchanged`
  - `test_probe_candidates_are_taken_in_reading_order_not_span_id_order`
  - `test_probe_markdown_level_two_fallback`
- [tests/test_adaptive_difficulty_ad1.py](../../../../../../tests/test_adaptive_difficulty_ad1.py) — direct import
  - `test_feature_audit_ledgered_with_fallback`
- [tests/test_learner_blindness_relax.py](../../../../../../tests/test_learner_blindness_relax.py) — direct import
  - `test_the_frozen_state_version_follows_the_switch`
- [tests/test_pr4_superseded_claims_landing.py](../../../../../../tests/test_pr4_superseded_claims_landing.py) — direct import
  - `test_landing_iii_upgrade_to_mvp037_archives_the_denial_log_exactly_once`

## Modification guidance

- Make changes here when the responsibility remains operation within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/operation.py](../../../../../../src/learnloop/adaptive_difficulty/operation.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
