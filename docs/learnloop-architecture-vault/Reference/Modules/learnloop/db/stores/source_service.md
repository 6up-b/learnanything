---
title: "learnloop.db.stores.source_service"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/source_service.py"
source_paths:
  - "src/learnloop/db/stores/source_service.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db.stores"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.db.stores.source_service module"
  - "src/learnloop/db/stores/source_service.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.source_service`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.source_service` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: SQL for the canonical-sources service (spec_source_practice_and_probes_v1).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/source_service.py](../../../../../../../src/learnloop/db/stores/source_service.py) |
| Source lines | 1916 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `table_exists(connection: sqlite3.Connection, name: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 21)
- `column_exists(connection: sqlite3.Connection, table: str, column: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 27)
- `required_method_key(method: Any) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 44) — The required method as the answer key names it: ``{"name", "criterion_ids"}`` (the item's field, or the mapping an assessment contract froze), or None without one.
- `reference_content_hash(item: Any) -> str` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 61) — What an answer-key check verified: the prompt, the expected answer and the grading rubric (canonical sources S1, §7.3a).
- `insert_impression(connection: sqlite3.Connection, *, id: str, created_at: str, surface: str, caller_kind: str | None, caller_ref: str | None, proposal_id: str, candidate_kind: str, practice_item_id: str | None, extraction_id: str | None, span_ids: Sequence[str], shown_fields: Mapping[str, Any], session_id: str | None) -> None` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 126)
- `impressions_for_proposal(connection: sqlite3.Connection, proposal_id: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 148)
- `impressions_of_item(connection: sqlite3.Connection, practice_item_id: str, *, since: str | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 157)
- `impressions_of_spans(connection: sqlite3.Connection, extraction_id: str, span_ids: Iterable[str], *, since: str | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 169) — Impressions of a source exercise whose shown spans overlap ``span_ids``.
- `shown_items(connection: sqlite3.Connection, items: Iterable[Any]) -> dict[str, list[str]]` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 196) — Items whose own material the learner has already been shown, ever, and how.
- `insert_import(connection: sqlite3.Connection, *, id: str, created_at: str, caller: str, extraction_id: str, span_ids: Sequence[str], status: str, proposal_id: str | None=None, source_id: str | None=None, revision_id: str | None=None, label: str | None=None, practice_item_id: str | None=None, content_hash: str | None=None, key_status: str | None=None, verification: Mapping[str, Any] | None=None, validation: Mapping[str, Any] | None=None, facet_basis: str | None=None, family_proposal_id: str | None=None, reason: str | None=None, need_id: str | None=None) -> None` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 291)
- `update_import(connection: sqlite3.Connection, import_id: str, *, updated_at: str, **fields: Any) -> None` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 322)
- `import_row(connection: sqlite3.Connection, import_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 346)
- `imports_for_item(connection: sqlite3.Connection, practice_item_id: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 353)
- `imports(connection: sqlite3.Connection, *, status: str | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 361)
- `imported_regions(connection: sqlite3.Connection) -> list[tuple[str, list[str]]]` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 371) — Every written import's (extraction, spans).
- `insert_key_check(connection: sqlite3.Connection, *, id: str, practice_item_id: str, content_hash: str, key_status: str, rung: str, trigger: str, started_at: str, created_at: str, import_id: str | None=None, verification: Mapping[str, Any] | None=None, ledger_ids: Sequence[str]=(), legacy_identity: bool=False) -> None` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 394) — One append-only check row, recording the key identity its hash was computed under.
- `identity_recorded(check: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 422) — Whether a check row records the key identity of its hash (re-review F1).
- `legacy_method_identity(connection: sqlite3.Connection, practice_item_id: str, content_hash: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 428) — Whether ``content_hash``, the hash of a question WITHOUT a method, may be a method contract's legacy identity (method-explicit-3 final verify).
- `applicable_checks(connection: sqlite3.Connection, practice_item_id: str, content_hash: str, *, method_revision: bool | None=None, legacy_hash: str | None=None, checks: Sequence[Mapping[str, Any]] | None=None) -> list[Mapping[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 450) — The checks of ONE revision, oldest first (method-explicit-3 re-review F1).
- `key_checks_for_item(connection: sqlite3.Connection, practice_item_id: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 488)
- `is_reader_import(connection: sqlite3.Connection, practice_item_id: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 496) — A historical Reader import, from its append-only ``learner_item_authored`` event.
- `is_exercise_import(connection: sqlite3.Connection, item: Any) -> bool` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 515)
- `effective_key_status(connection: sqlite3.Connection, item: Any) -> str` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 523) — The item's key status now: the latest check of its CURRENT content.
- `has_required_method(item: Any) -> bool` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 538)
- `key_status_for_content(connection: sqlite3.Connection, item: Any, content_hash: str, *, method_revision: bool | None=None, legacy_hash: str | None=None) -> str` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 542) — The key status of ONE revision of an exercise import (its :func:`reference_content_hash`): the latest of its checks (:func:`applicable_checks`, which reads ``method_revision`` and ``legacy_hash``), else ``changed_since_check``, ``checking`` or ``model_answer`` as :func:`effectiv…
- `checked_content_hashes(connection: sqlite3.Connection, practice_item_id: str, *, legacy_identity: bool=False) -> list[str]` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 566) — Every revision of an item that an answer-key check has recorded, oldest first; with ``legacy_identity``, only those of checks recorded without their identity (:func:`identity_recorded`).
- `exercise_import_ids(connection: sqlite3.Connection, items: Iterable[Any]) -> set[str]` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 576) — Every exercise import among ``items``, read in three bulk queries.
- `unverified_import_ids(connection: sqlite3.Connection, items: Iterable[Any], *, gated: bool) -> set[str]` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 593) — Exercise imports whose CURRENT key is not verified (C3, §7.3a).
- `reference_status_for_item(connection: sqlite3.Connection, item: Any) -> str` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 608) — The attempt-time gate's value: ``not_applicable``, ``verified`` or ``unverified``.
- `bind_replacement_grade(connection: sqlite3.Connection, *, attempt_id: str, item: Any, grading: str, created_at: str, graded_contents: Sequence[str] | None=None, graded_revision: str='current', method_revision: bool | None=None, legacy_contents: Mapping[str, str] | None=None) -> str | None` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 637) — C3 for a grade that replaces an attempt's grade (§7.3a, "Replacement grades").
- `need_source_import(connection: sqlite3.Connection, practice_item_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 719) — The source-first import that fulfilled an intervention need with this item (its retrieval provenance: need, proposal, book solution), or None.
- `book_solution_span_ids(connection: sqlite3.Connection, practice_item_id: str) -> list[str]` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 732) — The imported exercise's own book solution spans (its latest import's verification), or [] when it has none: source text the exposure rule counts as shown from the exercise (rule 3).
- `exercise_key(extraction_id: str, span_ids: Iterable[str]) -> str` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 751) — A stable identity for an unimported exercise (ledger ids, receipts, impressions).
- `serve_time_exposure(connection: sqlite3.Connection, *, practice_item_id: str, family_item_ids: Iterable[str], extraction_id: str | None, span_ids: Iterable[str], solution_span_ids: Iterable[str]=(), candidate_keys: Iterable[str]=(), studied_extraction_ids: Iterable[str] | None=None, since: str) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 757) — The exposure rule's facts at serving time, with no model call (§5.4).
- `insert_comparison(connection: sqlite3.Connection, *, id: str, created_at: str, query_hash: str, query_md: str, requested_perspectives: Sequence[str], counterpart_keys: Sequence[Any], comparison: Mapping[str, Any], dropped_lines: Sequence[Any], dropped_pins: Sequence[Any], unverified_sources: Sequence[Any], policy: str, caller_context: Mapping[str, Any], model: str | None, prompt_version: str, ledger_ids: Sequence[str], caller: str, caller_ref: str | None) -> None` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 860)
- `comparison_row(connection: sqlite3.Connection, comparison_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 887)
- `add_comparison_reuse_provenance(connection: sqlite3.Connection, comparison_id: str, *, dropped_pins: Sequence[Mapping[str, Any]], unverified_sources: Sequence[Mapping[str, Any]], question_event_ids: Sequence[str]=()) -> bool` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 900) — A reuse's contributors joined to the stored comparison's (Reader follow-ups Nov 1, Codex review F1): the passages a reusing call dropped or could not check, each once (by its passage), and the tutor question it was reused for (Codex re-review F1: a direct RPC writes no tool run…
- `find_comparison(connection: sqlite3.Connection, *, query_hash: str, policy: str, counterpart_keys: Sequence[Any]) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 945) — A stored comparison of the same question over the same counterparts under the same policy.
- `insert_tool_call(connection: sqlite3.Connection, *, id: str, created_at: str, row_kind: str, caller_kind: str, caller_ref: str | None, context: Mapping[str, Any], policy: str, tool: str, arguments: Mapping[str, Any], status: str, parent_id: str | None=None, dropped: Sequence[Any]=(), ledger_id: str | None=None, result_ref: str | None=None, result_keys: Sequence[Any]=(), source_versions: Mapping[str, Any] | None=None, model: str | None=None, prompt_version: str | None=None, latency_ms: int | None=None, cost: Mapping[str, Any] | None=None) -> str` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 973)
- `tool_call(connection: sqlite3.Connection, call_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 1000)
- `tool_requests_for_result(connection: sqlite3.Connection, result_ref: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 1005) — RW4d fix round 5: every tool request one of whose runs produced ``result_ref`` (a tutor comparison's questions), oldest first; a run whose request is missing is returned as itself (its ``caller_ref`` still names the question).
- `tool_call_runs(connection: sqlite3.Connection, request_id: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 1021)
- `tool_calls(connection: sqlite3.Connection, *, caller_kind: str | None=None, caller_ref: str | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 1027)
- `insert_intervention(connection: sqlite3.Connection, *, id: str, created_at: str, kind: str, caller_kind: str | None=None, caller_ref: str | None=None, intent: str | None=None, policy: str | None=None, tool_call_id: str | None=None, proposal_id: str | None=None, question_event_id: str | None=None, remediation_episode_id: str | None=None, router_decision_id: str | None=None, assets: Mapping[str, Any] | None=None, targets: Mapping[str, Any] | None=None, state_ref: Mapping[str, Any] | None=None, valuation: Mapping[str, Any] | None=None, exposure_event_ids: Sequence[Any]=(), impression_ids: Sequence[Any]=(), reading_exposure_label: str | None=None, eligibility: Mapping[str, Any] | None=None, seconds_since_related_exposure: float | None=None, session_id: str | None=None, attempt_id: str | None=None, algorithm_version: str | None=None) -> str` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 1050)
- `interventions(connection: sqlite3.Connection, *, proposal_id: str | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 1086)
- `insert_outcomes(connection: sqlite3.Connection, rows: Iterable[Mapping[str, Any]]) -> int` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 1103)
- `replace_outcomes(connection: sqlite3.Connection, rows: Iterable[Mapping[str, Any]]) -> tuple[int, int]` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 1119) — The replayer's write: clear and refill inside the caller's transaction.
- `outcomes(connection: sqlite3.Connection) -> dict[str, dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 1126)
- `receipt_time_floor(since: str) -> str` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 1175) — ``since`` as the earliest string a receipt stamp of that UTC second sorts at or after.
- `ledger_stamp(moment: datetime | str) -> str` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 1268) — The ledger's stamp: UTC to the second with ``Z`` (``utc_now_iso``'s form), so stored leases compare with it as strings.
- `service_spend_accounting(connection: sqlite3.Connection, *, envelope: str, day: str, since: str, now: datetime | str, price_per_million: float | None=None, subscription_providers: Collection[str]=(), owner_kinds: Sequence[str] | None=SERVICE_OWNER_KINDS) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 1382) — The daily cap's total for ``envelope`` on ``day`` (receipts since ``since``), as of ``now``: the one function admission, recovery and every report read.
- `recover_service_spend(connection: sqlite3.Connection, accounting: Mapping[str, Any], *, now: datetime | str) -> dict[str, int]` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 1547) — Write what ``service_spend_accounting`` found for each orphan, inside the caller's BEGIN IMMEDIATE transaction (the one that computed it, so no receipt was written between): reconcile it with its receipts, or release one with none.
- `reserve_service_spend(connection: sqlite3.Connection, *, id: str, envelope: str, day: str, since: str, usd: float, cap: float, process: str, now: datetime | str, lease_seconds: float, price_per_million: float | None=None, subscription_providers: Collection[str]=(), owner_kinds: Sequence[str] | None=SERVICE_OWNER_KINDS) -> tuple[bool, float]` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 1574) — Admit one request under the shared cap, inside the caller's BEGIN IMMEDIATE transaction.
- `renew_service_spend_leases(connection: sqlite3.Connection, ids: Collection[str], *, process: str, until: datetime | str) -> int` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 1602) — The owner's heartbeat: extend its in-flight reservations' leases.
- `charge_service_spend(connection: sqlite3.Connection, id: str, usd: float, now: datetime | str, *, process: str | None=None) -> None` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 1623) — Reconcile an in-flight reservation upward (usage above the estimate); never a refund.
- `settle_service_spend(connection: sqlite3.Connection, id: str, now: datetime | str, actual_usd: float | None=None, *, process: str | None=None) -> None` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 1634) — The owner's reconciliation: the request finished and counts its reported cost from now on, else its charge (at least its estimate).
- `class ReservationReleased(RuntimeError)` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 1659) — A request's shared reservation was released by recovery (its owner was presumed terminal): its receipt cannot start, so the request is never sent.
- `released_reservations(connection: sqlite3.Connection, budget_json: Any) -> list[str]` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 1673) — The reservations a root receipt's declared budget names that recovery released.
- `release_service_spend(connection: sqlite3.Connection, id: str, *, process: str | None=None) -> None` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 1689) — Remove a reservation whose request was never sent (another cap refused it).
- `service_spend_report(connection: sqlite3.Connection, *, envelope: str, days: Sequence[str], price_per_million: float | None=None, subscription_providers: Collection[str]=(), owner_kinds: Sequence[str] | None=SERVICE_OWNER_KINDS, top: int=5) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 1696) — What the service actually spent, per UTC day in ``days`` (``YYYY-MM-DD``, oldest first), read back from what was recorded (owner, 2026-10-13: caps are set later from real use).
- `spend_since(connection: sqlite3.Connection, since: str, *, owner_kinds: Sequence[str] | None=SERVICE_OWNER_KINDS, price_per_million: float | None=None, subscription_providers: Collection[str]=()) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 1791) — Spend of physical requests (leaf receipts) since ``since``, by their receipts alone.

### Module constants

- `IMPRESSION_SURFACES` ([src/learnloop/db/stores/source_service.py](../../../../../../../src/learnloop/db/stores/source_service.py), line 123)
- `_OWN_ATTEMPT_REVEALS` ([src/learnloop/db/stores/source_service.py](../../../../../../../src/learnloop/db/stores/source_service.py), line 193)
- `CHECK_STATUSES` ([src/learnloop/db/stores/source_service.py](../../../../../../../src/learnloop/db/stores/source_service.py), line 271)
- `VERIFIED_STATUSES` ([src/learnloop/db/stores/source_service.py](../../../../../../../src/learnloop/db/stores/source_service.py), line 275)
- `KEY_STATUS_LABELS` ([src/learnloop/db/stores/source_service.py](../../../../../../../src/learnloop/db/stores/source_service.py), line 277)
- `READER_IMPORT_MECHANISM` ([src/learnloop/db/stores/source_service.py](../../../../../../../src/learnloop/db/stores/source_service.py), line 288)
- `_IMPORT_FIELDS` ([src/learnloop/db/stores/source_service.py](../../../../../../../src/learnloop/db/stores/source_service.py), line 316)
- `KEY_IDENTITY_FIELD` ([src/learnloop/db/stores/source_service.py](../../../../../../../src/learnloop/db/stores/source_service.py), line 383)
- `KEY_IDENTITY` ([src/learnloop/db/stores/source_service.py](../../../../../../../src/learnloop/db/stores/source_service.py), line 387)
- `REFERENCE_BINDING_TASK` ([src/learnloop/db/stores/source_service.py](../../../../../../../src/learnloop/db/stores/source_service.py), line 619)
- `AMBIGUOUS_DEFAULT_REVISION` ([src/learnloop/db/stores/source_service.py](../../../../../../../src/learnloop/db/stores/source_service.py), line 624)
- `AMBIGUOUS_METHOD_REVISION` ([src/learnloop/db/stores/source_service.py](../../../../../../../src/learnloop/db/stores/source_service.py), line 632)
- `UNESTABLISHED_REVISIONS` ([src/learnloop/db/stores/source_service.py](../../../../../../../src/learnloop/db/stores/source_service.py), line 634)
- `WORKED_EXAMPLE_LEDGER_TASK` ([src/learnloop/db/stores/source_service.py](../../../../../../../src/learnloop/db/stores/source_service.py), line 748)
- `REUSE_QUESTIONS_KEY` ([src/learnloop/db/stores/source_service.py](../../../../../../../src/learnloop/db/stores/source_service.py), line 897)
- `SERVICE_OWNER_KINDS` ([src/learnloop/db/stores/source_service.py](../../../../../../../src/learnloop/db/stores/source_service.py), line 962)
- `_TOOL_CALL_JSON` ([src/learnloop/db/stores/source_service.py](../../../../../../../src/learnloop/db/stores/source_service.py), line 968)
- `INTERVENTION_KINDS` ([src/learnloop/db/stores/source_service.py](../../../../../../../src/learnloop/db/stores/source_service.py), line 1043)
- `_INTERVENTION_JSON` ([src/learnloop/db/stores/source_service.py](../../../../../../../src/learnloop/db/stores/source_service.py), line 1044)
- `OUTCOME_COLUMNS` ([src/learnloop/db/stores/source_service.py](../../../../../../../src/learnloop/db/stores/source_service.py), line 1097)
- `SERVICE_SPEND_TABLE` ([src/learnloop/db/stores/source_service.py](../../../../../../../src/learnloop/db/stores/source_service.py), line 1234)
- `RESERVATIONS_KEY` ([src/learnloop/db/stores/source_service.py](../../../../../../../src/learnloop/db/stores/source_service.py), line 1239)
- `PRICING_BASES` ([src/learnloop/db/stores/source_service.py](../../../../../../../src/learnloop/db/stores/source_service.py), line 1242)
- `_EPSILON` ([src/learnloop/db/stores/source_service.py](../../../../../../../src/learnloop/db/stores/source_service.py), line 1245)
- `_LEDGER_COLUMNS` ([src/learnloop/db/stores/source_service.py](../../../../../../../src/learnloop/db/stores/source_service.py), line 1247)

### Explicit exports

`__all__` declares:

- `tool_requests_for_result`
- `comparison_row`
- `find_comparison`
- `insert_comparison`
- `SERVICE_OWNER_KINDS`
- `SERVICE_SPEND_TABLE`
- `PRICING_BASES`
- `RESERVATIONS_KEY`
- `ReservationReleased`
- `charge_service_spend`
- `ledger_stamp`
- `recover_service_spend`
- `release_service_spend`
- `released_reservations`
- `renew_service_spend_leases`
- `reserve_service_spend`
- `service_spend_accounting`
- `service_spend_report`
- `settle_service_spend`
- `spend_since`
- `receipt_time_floor`
- `CHECK_STATUSES`
- `KEY_STATUS_LABELS`
- `VERIFIED_STATUSES`
- `checked_content_hashes`
- `applicable_checks`
- `has_required_method`
- `identity_recorded`
- `KEY_IDENTITY`
- `KEY_IDENTITY_FIELD`
- `legacy_method_identity`
- `effective_key_status`
- `reference_content_hash`
- `exercise_import_ids`
- `unverified_import_ids`
- `import_row`
- `imported_regions`
- `imports`
- `imports_for_item`
- `insert_import`
- `insert_key_check`
- `is_exercise_import`
- `is_reader_import`
- `exercise_key`
- `need_source_import`
- `serve_time_exposure`
- `book_solution_span_ids`
- `key_checks_for_item`
- `key_status_for_content`
- `reference_status_for_item`
- `REFERENCE_BINDING_TASK`
- `AMBIGUOUS_DEFAULT_REVISION`
- `AMBIGUOUS_METHOD_REVISION`
- `bind_replacement_grade`
- `update_import`
- `IMPRESSION_SURFACES`
- `column_exists`
- `impressions_for_proposal`
- `impressions_of_item`
- `impressions_of_spans`
- `insert_impression`
- `table_exists`

## Internal implementation anchors

- `_plain(value: Any) -> Any` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 33)
- `_dumps(value: Any) -> str` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 107)
- `_loads(raw: Any, default: Any=None) -> Any` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 111)
- `_impression(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 141)
- `_import(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 338)
- `_identity_fields(legacy_identity: bool=False) -> dict[str, str]` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 390)
- `_check(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 415)
- `_comparison(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 877)
- `_tool_call(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 993)
- `_intervention(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 1079)
- `_root_budget(connection: sqlite3.Connection, parent_id: str | None, budget_json: str | None, cache: dict[str, str | None]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 1138) — The budget the receipt's root call declared (``budget_json``), or {}.
- `_receipt_billing(declared: Mapping[str, Any], provider: str | None, subscription_providers: Collection[str]) -> str` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 1161) — ``subscription`` or ``metered``: the root receipt's declared budget says which (``billing``, ``practice_index.billing``, ``pf.cost_basis``); a root with no declared budget falls back to the provider's profile type.
- `_moment(value: Any) -> datetime | None` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 1251) — An ISO stamp (``Z``, an offset, or naive UTC) as an aware UTC datetime; None if unreadable.
- `_recorded_rate(declared: Mapping[str, Any]) -> float | None` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 1278) — The per-token rate a request recorded on its root receipt when it was admitted (``practice_index.price_per_million``: ``PaidCalls`` and query embeddings; ``pf.price_per_million``: ``PFCaller``), or None.
- `_metered_cost(cost: Any, tokens: int, recorded_rate: float | None, owner_rate: float | None) -> tuple[float | None, str]` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 1296) — A metered leaf receipt's dollars, and their basis (``PRICING_BASES``).
- `_estimated_tokens(tokens: int, usage_json: Any) -> int` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 1316) — A subscription receipt's tokens: reported, else its own estimate.
- `_ledger_rows(connection: sqlite3.Connection, envelope: str, day: str) -> tuple[list[dict[str, Any]], bool]` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 1328) — The envelope's reservations on ``day``, and whether the table has migration 195's columns (a database read without migrating has not).
- `_named_reservations(connection: sqlite3.Connection, envelope: str, refs: Collection[str]) -> set[str]` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 1340) — Which of ``refs`` are reservations of ``envelope`` (on any day).
- `_lifetime(created_at: Any, updated_at: Any) -> tuple[datetime, datetime] | None` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 1353) — A legacy row's lifetime, as far as its stamps (to the second) tell: from the second it was reserved in to the end of the second it last changed in.
- `_legacy_rows(connection: sqlite3.Connection, envelope: str, since: datetime) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 1363) — The envelope's legacy rows (on any day) whose lifetime reaches ``since``.
- `_second_floor(moment: datetime) -> str` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 1376) — ``moment``'s second as the receipt scan's lower bound (``receipt_time_floor``'s form).
- `_owned(process: str | None) -> tuple[str, tuple[str, ...]]` ([source](../../../../../../../src/learnloop/db/stores/source_service.py), line 1619)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `AMBIGUOUS_DEFAULT_REVISION`, `AMBIGUOUS_METHOD_REVISION`, `KEY_IDENTITY`, `KEY_IDENTITY_FIELD`, `checked_content_hashes`, `reference_content_hash`, `reference_status_for_item`; statically calls `checked_content_hashes`, `reference_content_hash`, `reference_status_for_item`
- [[Reference/Modules/learnloop/attempts/grade_resolution|learnloop.attempts.grade_resolution]] — imports `bind_replacement_grade`; statically calls `bind_replacement_grade`
- [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]] — imports `bind_replacement_grade`; statically calls `bind_replacement_grade`
- [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]] — imports `KEY_IDENTITY`, `KEY_IDENTITY_FIELD`, `VERIFIED_STATUSES`, `import_row`, `insert_import`, `insert_key_check`, `update_import`; statically calls `import_row`, `insert_import`, `insert_key_check`, `update_import`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `shown_items`; statically calls `shown_items`
- [[Reference/Modules/learnloop/db/stores/model_calls|learnloop.db.stores.model_calls]] — imports `ReservationReleased`, `released_reservations`; statically calls `ReservationReleased`, `released_reservations`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `exercise_key`, `need_source_import`, `serve_time_exposure`; statically calls `exercise_key`, `need_source_import`, `serve_time_exposure`
- [[Reference/Modules/learnloop/goals/certification_cold_probe|learnloop.goals.certification_cold_probe]] — imports `unverified_import_ids`; statically calls `unverified_import_ids`
- [[Reference/Modules/learnloop/goals/exam_pool|learnloop.goals.exam_pool]] — imports `unverified_import_ids`; statically calls `unverified_import_ids`
- [[Reference/Modules/learnloop/instructional/discriminating|learnloop.instructional.discriminating]] — imports `VERIFIED_STATUSES`, `effective_key_status`, `exercise_import_ids`; statically calls `effective_key_status`, `exercise_import_ids`
- [[Reference/Modules/learnloop/instructional/exercises|learnloop.instructional.exercises]] — imports `exercise_key`, `imported_regions`; statically calls `exercise_key`, `imported_regions`
- [[Reference/Modules/learnloop/instructional/exposure|learnloop.instructional.exposure]] — imports `impressions_of_item`, `impressions_of_spans`; statically calls `impressions_of_item`, `impressions_of_spans`
- [[Reference/Modules/learnloop/instructional/harvest|learnloop.instructional.harvest]] — imports `VERIFIED_STATUSES`, `effective_key_status`, `imports_for_item`, `is_exercise_import`, `reference_content_hash`, `spend_since`; statically calls `effective_key_status`, `imports_for_item`, `is_exercise_import`, `reference_content_hash`, `spend_since`
- [[Reference/Modules/learnloop/instructional/interventions|learnloop.instructional.interventions]] — imports `KEY_STATUS_LABELS`, `effective_key_status`, `exercise_import_ids`, `impressions_for_proposal`, `insert_intervention`, `interventions`, `outcomes`, `tool_call`, `tool_call_runs`; statically calls `effective_key_status`, `exercise_import_ids`, `impressions_for_proposal`, `insert_intervention`, `interventions`, `outcomes`, `tool_call`, `tool_call_runs`
- [[Reference/Modules/learnloop/instructional/needs|learnloop.instructional.needs]] — imports `import_row`, `update_import`; statically calls `import_row`, `update_import`
- [[Reference/Modules/learnloop/instructional/practice|learnloop.instructional.practice]] — imports `IMPRESSION_SURFACES`, `import_row`, `insert_impression`; statically calls `import_row`, `insert_impression`
- [[Reference/Modules/learnloop/instructional/tools|learnloop.instructional.tools]] — imports `insert_tool_call`, `tool_call`, `tool_calls`; statically calls `insert_tool_call`, `tool_call`, `tool_calls`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `KEY_IDENTITY`, `KEY_IDENTITY_FIELD`
- [[Reference/Modules/learnloop/ops/pf_publish|learnloop.ops.pf_publish]] — imports `insert_key_check`, `reference_content_hash`; statically calls `insert_key_check`, `reference_content_hash`
- [[Reference/Modules/learnloop/reader/as_printed|learnloop.reader.as_printed]] — imports `imports_for_item`, `is_reader_import`; statically calls `imports_for_item`, `is_reader_import`
- [[Reference/Modules/learnloop/reader/source_objects|learnloop.reader.source_objects]] — imports `REUSE_QUESTIONS_KEY`, `comparison_row`, `tool_requests_for_result`; statically calls `comparison_row`, `tool_requests_for_result`
- [[Reference/Modules/learnloop/scheduling/intent/followup_gate|learnloop.scheduling.intent.followup_gate]] — imports `book_solution_span_ids`, `exercise_key`, `serve_time_exposure`; statically calls `book_solution_span_ids`, `exercise_key`, `serve_time_exposure`
- [[Reference/Modules/learnloop/source_retrieval/compare|learnloop.source_retrieval.compare]] — imports `add_comparison_reuse_provenance`, `find_comparison`, `insert_comparison`; statically calls `add_comparison_reuse_provenance`, `find_comparison`, `insert_comparison`
- [[Reference/Modules/learnloop/source_retrieval/kept_comparisons|learnloop.source_retrieval.kept_comparisons]] — imports `comparison_row`, `tool_call`, `tool_call_runs`; statically calls `comparison_row`, `tool_call`, `tool_call_runs`
- [[Reference/Modules/learnloop/source_retrieval/library_ask|learnloop.source_retrieval.library_ask]] — imports `comparison_row`; statically calls `comparison_row`
- [[Reference/Modules/learnloop/source_retrieval/service_spend|learnloop.source_retrieval.service_spend]] — imports `SERVICE_OWNER_KINDS`, `charge_service_spend`, `release_service_spend`, `renew_service_spend_leases`, `reserve_service_spend`, `service_spend_accounting`, `service_spend_report`, `settle_service_spend`; statically calls `charge_service_spend`, `release_service_spend`, `renew_service_spend_leases`, `reserve_service_spend`, `service_spend_accounting`, `service_spend_report`, `settle_service_spend`
- [[Reference/Modules/learnloop/substrate/intervention_outcomes|learnloop.substrate.intervention_outcomes]] — imports `interventions`, `replace_outcomes`; statically calls `interventions`, `replace_outcomes`
- [[Reference/Modules/learnloop/vault/hashes|learnloop.vault.hashes]] — imports `reference_content_hash`; statically calls `reference_content_hash`
- [[Reference/Modules/learnloop/workbench/compare_methods|learnloop.workbench.compare_methods]] — imports `applicable_checks`, `effective_key_status`, `has_required_method`, `reference_content_hash`; statically calls `applicable_checks`, `effective_key_status`, `has_required_method`, `reference_content_hash`
- [[Reference/Modules/learnloop_sidecar/handlers/item_authoring|learnloop_sidecar.handlers.item_authoring]] — imports `effective_key_status`; statically calls `effective_key_status`
- [[Reference/Modules/learnloop_sidecar/handlers/library_exercises|learnloop_sidecar.handlers.library_exercises]] — imports `exercise_key`; statically calls `exercise_key`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `KEY_STATUS_LABELS`, `effective_key_status`; statically calls `effective_key_status`
- [[Reference/Modules/learnloop_sidecar/handlers/source_service|learnloop_sidecar.handlers.source_service]] — imports `KEY_STATUS_LABELS`, `effective_key_status`, `import_row`, `insert_import`; statically calls `effective_key_status`, `import_row`, `insert_import`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]] — imports `KEY_STATUS_LABELS`, `effective_key_status`, `import_row`; statically calls `effective_key_status`, `import_row`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/reveal_coverage|learnloop.reveal_coverage]] — imports `routine_coverage_sql`, `routine_window_start`; calls `routine_coverage_sql`, `routine_window_start`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `datetime`, `hashlib`, `json`, `math`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/grade_resolution|learnloop.attempts.grade_resolution]], [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]], [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]], [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] and 29 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/learner_pick_proposal_helpers.py](../../../../../../../tests/learner_pick_proposal_helpers.py) — direct import
- [tests/reader_followups_round4_helpers.py](../../../../../../../tests/reader_followups_round4_helpers.py) — direct import
- [tests/reference_gate_imports_helpers.py](../../../../../../../tests/reference_gate_imports_helpers.py) — direct import
- [tests/required_method_authority_helpers.py](../../../../../../../tests/required_method_authority_helpers.py) — direct import
- [tests/required_method_rereview_helpers.py](../../../../../../../tests/required_method_rereview_helpers.py) — direct import
- [tests/required_method_round3_rereview_helpers.py](../../../../../../../tests/required_method_round3_rereview_helpers.py) — direct import
- [tests/required_method_round3_review_helpers.py](../../../../../../../tests/required_method_round3_review_helpers.py) — direct import
- [tests/source_exercise_import_helpers.py](../../../../../../../tests/source_exercise_import_helpers.py) — direct import
- [tests/test_ad1_fix_round4.py](../../../../../../../tests/test_ad1_fix_round4.py) — direct import
  - `test_an_answer_after_a_vault_switch_writes_no_checkpoint_and_settles_its_spend`
- [tests/test_compare_methods.py](../../../../../../../tests/test_compare_methods.py) — direct import
  - `test_book_solution_reads_the_checked_span_ids_and_never_exam_material`
- [tests/test_compare_sources_keep.py](../../../../../../../tests/test_compare_sources_keep.py) — direct import
  - `test_a_tutor_keep_checks_its_question_passage_before_any_write`
  - `test_a_tutor_keep_keeps_only_the_sources_its_run_showed`
  - `test_a_tutor_take_on_a_learner_keep_is_hidden_once_its_question_is_held_out`
  - `test_the_tutor_shown_a_comparison_the_learner_keeps_modifies_that_keep`
- [tests/test_discriminating_search.py](../../../../../../../tests/test_discriminating_search.py) — direct import
  - `test_a_carried_exercise_imported_since_is_not_restored`
  - `test_an_unverified_import_is_excluded_from_value_intents_but_not_practice`
- [tests/test_help_outcomes.py](../../../../../../../tests/test_help_outcomes.py) — direct import
  - `test_f10_an_s5_record_naming_a_passage_is_its_outcome_and_is_not_counted_again`
- [tests/test_import_split_parity.py](../../../../../../../tests/test_import_split_parity.py) — direct import
  - `test_the_reader_job_records_an_import_row_and_leaves_the_item_unchanged`
- [tests/test_intervention_outcomes_replayer.py](../../../../../../../tests/test_intervention_outcomes_replayer.py) — direct import
  - `test_the_replayer_is_registered_deterministic_and_calls_nothing`
  - `test_the_replayer_reads_persisted_exposure`
- [tests/test_learner_pick_proposal.py](../../../../../../../tests/test_learner_pick_proposal.py) — direct import
- [tests/test_method_explicit_landing.py](../../../../../../../tests/test_method_explicit_landing.py) — direct import
  - `test_a_check_recorded_on_main_still_verifies_and_the_fresh_check_label_needs_a_change`
- [tests/test_pf_generation.py](../../../../../../../tests/test_pf_generation.py) — direct import
  - `test_a_published_variant_of_a_textbook_exercise_keeps_its_own_verification`
- [tests/test_plan_first_transport_grant_scope.py](../../../../../../../tests/test_plan_first_transport_grant_scope.py) — direct import
  - `test_the_edit_recheck_never_uses_the_grant`
- [tests/test_reader_ca1_astra_codex_review.py](../../../../../../../tests/test_reader_ca1_astra_codex_review.py) — direct import
  - `test_a_named_solution_block_holding_part_of_the_statement_withholds_the_whole_crop`
- [tests/test_reader_ca1_astra_fixes.py](../../../../../../../tests/test_reader_ca1_astra_fixes.py) — direct import
  - `test_a_block_on_the_imports_book_solution_spans_is_never_cropped`
- [tests/test_reader_ca1_astra_redesign.py](../../../../../../../tests/test_reader_ca1_astra_redesign.py) — direct import
- [tests/test_reader_ca1_astra_rereview.py](../../../../../../../tests/test_reader_ca1_astra_rereview.py) — direct import
- [tests/test_reader_followups_rereview.py](../../../../../../../tests/test_reader_followups_rereview.py) — direct import
- [tests/test_reader_followups_review.py](../../../../../../../tests/test_reader_followups_review.py) — direct import
- [tests/test_reader_rw3a_landing.py](../../../../../../../tests/test_reader_rw3a_landing.py) — direct import
  - `test_check_me_goes_through_the_plan_path_and_is_logged_once`
- [tests/test_reader_rw6b_landing.py](../../../../../../../tests/test_reader_rw6b_landing.py) — direct import
- [tests/test_reference_check_binding.py](../../../../../../../tests/test_reference_check_binding.py) — direct import
  - `test_a_late_background_check_never_verifies_an_edit`
- [tests/test_reference_gate_imports.py](../../../../../../../tests/test_reference_gate_imports.py) — direct import
  - `test_a_historical_reader_import_resolves_to_model_answer`
  - `test_a_reader_import_row_counts_as_an_import`
  - `test_a_regrade_against_an_edited_unverified_key_never_certifies`
  - `test_a_regrade_never_raises_an_attempts_status`
- [tests/test_required_method_authority.py](../../../../../../../tests/test_required_method_authority.py) — direct import
  - `test_f13_a_frozen_regrade_of_the_current_content_still_binds_it`
- [tests/test_required_method_reopened.py](../../../../../../../tests/test_required_method_reopened.py) — direct import
- [tests/test_required_method_rereview.py](../../../../../../../tests/test_required_method_rereview.py) — direct import
  - `test_f19_a_dispute_of_the_graded_revision_lowers_despite_a_verified_inline_twin`
  - `test_f19_a_method_contract_records_the_reference_content_hash`
- [tests/test_required_method_round3.py](../../../../../../../tests/test_required_method_round3.py) — direct import
  - `test_f19_a_changed_inherited_default_leaves_a_historical_regrade_unverified`
- [tests/test_required_method_round3_final_verify.py](../../../../../../../tests/test_required_method_round3_final_verify.py) — direct import
  - `test_a_branch_contract_recorded_since_review_f1_binds_exactly_only_when_it_is_rebuilt`
  - `test_a_contract_frozen_now_records_its_key_identity_and_binds_exactly_without_its_rubric`
  - `test_a_contract_without_a_recorded_hash_leaves_the_cleared_question_needing_a_fresh_check`
  - `test_an_unrebuildable_method_binding_needs_a_fresh_check_whatever_another_revision_says`
- [tests/test_required_method_round3_rereview.py](../../../../../../../tests/test_required_method_round3_rereview.py) — direct import
  - `test_f1_a_cleared_method_is_never_verified_by_a_check_of_the_method_question`
  - `test_f1_checks_record_their_identity_and_an_item_without_a_method_keeps_its_checks`
  - `test_f1_the_legacy_contract_keeps_its_checks_and_meets_its_own_question_under_the_new_identity`
- [tests/test_required_method_round3_review.py](../../../../../../../tests/test_required_method_round3_review.py) — direct import
  - `test_f1_a_dispute_of_the_new_method_never_reaches_the_contract_frozen_under_the_old`
  - `test_f1_changing_only_the_required_method_needs_a_fresh_check`
  - `test_f1_the_reference_key_identity_carries_the_required_method`
- [tests/test_retrieval_interventions_write_points.py](../../../../../../../tests/test_retrieval_interventions_write_points.py) — direct import
- [tests/test_router_r2a_serving.py](../../../../../../../tests/test_router_r2a_serving.py) — direct import
  - `test_an_unplanned_proposal_pick_delivers_with_its_blocks_decision`
- [tests/test_router_r2bc_landing.py](../../../../../../../tests/test_router_r2bc_landing.py) — direct import
  - `test_check_me_under_the_mixture_is_logged_once_and_binds_to_its_presentation`
- [tests/test_rw2c_fix_round2.py](../../../../../../../tests/test_rw2c_fix_round2.py) — direct import
  - `test_fr2_5_a_later_regrade_never_changes_s5s_outcome_at_as_of_linked_or_standalone`
  - `test_fr2_5_an_s5_record_read_before_its_censoring_horizon_is_pending_not_expired`
  - `test_fr2_5_the_s5_historical_read_leaves_current_behaviour_alone`
- [tests/test_source_exercise_import.py](../../../../../../../tests/test_source_exercise_import.py) — direct import
  - `test_a_model_failure_while_authoring_fails_the_import_and_is_receipted`
  - `test_a_resumed_check_never_verifies_content_edited_since`
  - `test_recovery_never_binds_a_verdict_to_content_edited_before_the_commit`
  - `test_the_books_solution_writes_and_verifies_the_key`
  - `test_the_time_box_writes_checking_and_the_check_lands_later`
  - `test_verification_off_imports_as_today_labelled_model_answer`
- [tests/test_source_exercise_rpcs.py](../../../../../../../tests/test_source_exercise_rpcs.py) — direct import
  - `test_an_interactive_import_bounds_the_authored_drafts_own_duration`
  - `test_an_interactive_import_is_validated_against_its_proposal_and_corrected`
- [tests/test_source_first_needs.py](../../../../../../../tests/test_source_first_needs.py) — direct import
  - `test_a_discriminate_need_is_fulfilled_with_the_screens_profiles_and_rubric_links`
  - `test_a_primed_retry_need_is_fulfilled_by_a_verified_textbook_exercise`
  - `test_the_follow_up_rechecks_independence_before_serving_a_need_import`
- [tests/test_source_service_spend_accounting.py](../../../../../../../tests/test_source_service_spend_accounting.py) — direct import
  - `test_an_upgrade_counts_every_request_and_reports_the_unprovable_overlap`
  - `test_spend_since_counts_a_reported_cost_alongside_tokens`
- [tests/test_source_service_spend_envelopes.py](../../../../../../../tests/test_source_service_spend_envelopes.py) — direct import
  - `test_a_settled_request_is_counted_once_not_by_its_receipt_and_its_reservation`
  - `test_spend_since_counts_a_request_in_the_first_second_of_a_run`
  - `test_spend_since_estimates_subscription_tokens_and_prices_unreported_metered_cost`
- [tests/test_tool_dispatch_policy.py](../../../../../../../tests/test_tool_dispatch_policy.py) — direct import
  - `test_a_cold_administration_opened_after_the_request_narrows_the_run`
  - `test_a_cold_administration_refuses_every_tool`
  - `test_each_caller_gets_its_policy_and_both_rows`
- [tests/test_tools_cli.py](../../../../../../../tests/test_tools_cli.py) — direct import
  - `test_tool_runs_as_an_agent_with_receipts`
- [tests/test_tutor_tool_requests.py](../../../../../../../tests/test_tutor_tool_requests.py) — direct import
  - `test_eager_and_lazy_runs_write_run_rows`
  - `test_requests_are_validated_recorded_and_offered`
  - `test_the_sidecar_offers_requests_and_drops_the_s0_request`
- [tests/test_ux_phase4_feedback.py](../../../../../../../tests/test_ux_phase4_feedback.py) — direct import
  - `test_f1_an_unattempted_disclosed_item_counts_as_shown_for_exam_protection`
- [tests/test_valuation_calibration_fields.py](../../../../../../../tests/test_valuation_calibration_fields.py) — direct import
  - `test_a_studied_worked_example_records_the_seconds_since_exposure`
  - `test_a_valued_pick_followed_by_an_attempt_records_hypothesis_movement`
  - `test_a_valued_pick_keeps_predicted_outcomes_regime_and_minutes`
  - `test_exposure_age_is_measured_at_delivery_not_at_valuation`
- [tests/test_whole_comparison_reuse_provenance.py](../../../../../../../tests/test_whole_comparison_reuse_provenance.py) — direct import

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/source_service.py](../../../../../../../src/learnloop/db/stores/source_service.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
