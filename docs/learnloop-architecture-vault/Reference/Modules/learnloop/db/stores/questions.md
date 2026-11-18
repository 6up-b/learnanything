---
title: "learnloop.db.stores.questions"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/questions.py"
source_paths:
  - "src/learnloop/db/stores/questions.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db.stores"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Inspect Persistent State"
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.db.stores.questions module"
  - "src/learnloop/db/stores/questions.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.questions`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.questions` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Learner questions, reveals, promotions and claims.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/questions.py](../../../../../../../src/learnloop/db/stores/questions.py) |
| Source lines | 977 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class QuestionStoreMixin` ([source](../../../../../../../src/learnloop/db/stores/questions.py), line 52)
  - `insert_question_event(self, event: Mapping[str, Any], *, clock: Clock | None=None) -> str` (line 56; public) — Append a learner question.
  - `update_question_event_answer(self, event_id: str, *, answer_md: str | None, question_type: str | None, facets: list[str] | None, hint_equivalent: bool, leak_suspected: bool, answer_status: str, signal_channel: str | None=None, source_context: Mapping[str, Any] | None=None, leak_overlap: float | None=None, remediation_episode_id: str | None=None, answered_at: str | None=None) -> bool` (line 140; public) — Complete (or fail) a pending question event after the provider call.
  - `question_events(self, *, context: str | None=None, note_id: str | None=None, practice_item_id: str | None=None, attempt_id: str | None=None, session_id: str | None=None, since: str | None=None, until: str | None=None, answer_status: str | None=None, resolution: str | None=None) -> list[dict[str, Any]]` (line 199; public)
  - `count_question_events(self, *, context: str | None=None, note_id: str | None=None, practice_item_id: str | None=None, attempt_id: str | None=None, session_id: str | None=None, since: str | None=None, answer_status: str | None=None, resolution: str | None=None) -> int` (line 240; public)
  - `question_event(self, event_id: str) -> dict[str, Any] | None` (line 265; public)
  - `set_question_event_rating(self, event_id: str, *, useful: bool) -> bool` (line 272; public)
  - `set_question_event_resolution(self, event_id: str, *, resolution: str) -> bool` (line 281; public) — Learner-facing queue state (migration 102): open | resolved | dismissed.
  - `count_hint_equivalent_question_events(self, practice_item_id: str, session_id: str | None, *, since: str | None=None, until: str | None=None, item_window_only: bool=False) -> int` (line 292; public) — Substantive questions on this item in the hint-equivalence window.
  - `insert_reveal_event(self, event: Mapping[str, Any], *, clock: Clock | None=None) -> str` (line 349; public) — Append one answer-exposure entry to the cross-channel reveal ledger.
  - `reveal_events(self, *, practice_item_id: str | None=None, remediation_episode_id: str | None=None, source_kind: str | None=None, attempt_id: str | None=None, since: str | None=None, until: str | None=None) -> list[dict[str, Any]]` (line 387; public)
  - `reveal_events_for_target(self, *, practice_item_id: str | None=None, learning_object_id: str | None=None, since: str | None=None, until: str | None=None) -> list[dict[str, Any]]` (line 422; public) — Reveals on this item OR anywhere in this learning object (OR, not AND).
  - `total_reveal_amount(self, practice_item_id: str, *, since: str | None=None, until: str | None=None, linked_attempt_id: str | None=None, linked_kinds: Sequence[str]=(), routine_basis_prefixes: Sequence[str]=(), routine_covered_from: str | None=None) -> float` (line 467; public) — Summed reveal amount for one item in a window.
  - `question_counts_by_facet(self) -> dict[str, int]` (line 536; public) — Total question_events touching each classified facet.
  - `set_question_event_saved_note(self, event_id: str, note_id: str | None) -> bool` (line 549; public) — Persist the tutor-turn -> saved-note link (migration 027, spec §5).
  - `insert_question_promotion(self, *, question_event_id: str, intent: str, route: str, attributed_facets: list[str] | None=None, question_nature: str | None=None, attempted_in_thread: bool | None=None, learner_claim_id: str | None=None, intervention_need_id: str | None=None, proposed_patch_id: str | None=None, saved_note_id: str | None=None, existing_practice_item_id: str | None=None, created_practice_item_id: str | None=None, created_learning_object_id: str | None=None, clock: Clock | None=None) -> str` (line 565; public) — Insert the promotion ledger row for a tutor turn (§4 step 4).
  - `update_question_promotion(self, question_event_id: str, *, route: Any=_UNSET, attributed_facets: Any=_UNSET, question_nature: Any=_UNSET, attempted_in_thread: Any=_UNSET, learner_claim_id: Any=_UNSET, intervention_need_id: Any=_UNSET, proposed_patch_id: Any=_UNSET, saved_note_id: Any=_UNSET, existing_practice_item_id: Any=_UNSET, created_practice_item_id: Any=_UNSET, created_learning_object_id: Any=_UNSET, clock: Clock | None=None) -> bool` (line 623; public) — Fill created ids / transition the route on an existing promotion row.
  - `question_promotion(self, event_id: str) -> dict[str, Any] | None` (line 692; public)
  - `question_promotions(self) -> list[dict[str, Any]]` (line 700; public) — All promotion rows, oldest first (requested-floor + signal joins).
  - `question_promotions_for_events(self, event_ids: Iterable[str]) -> dict[str, dict[str, Any]]` (line 709; public) — Promotion rows keyed by question_event_id, for the tutor transcript.
  - `question_promotions_for_patch(self, patch_id: str) -> list[dict[str, Any]]` (line 726; public) — Promotion rows awaiting or completed through one proposal patch.
  - `insert_question_promotion_request(self, *, question_event_id: str, intent: str, subject_id: str | None=None, learning_object_id: str | None=None, status: str='queued', stage: str='queued', batch_id: str | None=None, clock: Clock | None=None) -> str` (line 742; public)
  - `update_question_promotion_request(self, question_event_id: str, *, status: Any=_UNSET, stage: Any=_UNSET, batch_id: Any=_UNSET, promotion_route: Any=_UNSET, error_code: Any=_UNSET, error_message: Any=_UNSET, retryable: Any=_UNSET, subject_id: Any=_UNSET, learning_object_id: Any=_UNSET, clock: Clock | None=None) -> bool` (line 779; public)
  - `question_promotion_request(self, event_id: str) -> dict[str, Any] | None` (line 829; public)
  - `question_promotion_requests_for_events(self, event_ids: Iterable[str]) -> dict[str, dict[str, Any]]` (line 840; public)
  - `retry_question_promotion_request(self, event_id: str, *, clock: Clock | None=None) -> bool` (line 860; public) — Re-open a failed durable request without losing its selected target.
  - `insert_learner_claim(self, claim: Mapping[str, Any], *, clock: Clock | None=None) -> str` (line 883; public)
  - `learner_claims(self, *, include_superseded: bool=False) -> list[dict[str, Any]]` (line 910; public) — The claims in force (newest first); ``include_superseded`` adds the replaced ones.
  - `replace_learner_claim(self, claim: Mapping[str, Any], *, clock: Clock | None=None) -> str` (line 927; public) — The replace seam: ``claim`` replaces the in-force claims of its source on its scope; its id.
  - `delete_learner_claims(self, *, source: str, scope_type: str, scope_id: str | None=None) -> int` (line 956; public) — Delete claims by (source, scope_type[, scope_id]) — the replace seam for init-wizard (global) and rung-variant (per-LO) re-claims.

## Internal implementation anchors

- `_decode_question_event(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/questions.py), line 17)
- `_decode_question_promotion(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/questions.py), line 38)
- `_decode_question_promotion_request(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/questions.py), line 46)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `QuestionStoreMixin`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/records|learnloop.db.records]] — imports `_UNSET`
- [[Reference/Modules/learnloop/db/row_serialization|learnloop.db.row_serialization]] — imports `_json`, `_loads`; calls `_json`, `_loads`
- [[Reference/Modules/learnloop/db/stores/router_objective|learnloop.db.stores.router_objective]] — imports `module`; calls `fill_receipt`, `split_receipt`
- [[Reference/Modules/learnloop/db/stores/write_provenance|learnloop.db.stores.write_provenance]] — imports `pinned_contract_ids`; calls `pinned_contract_ids`
- [[Reference/Modules/learnloop/hint_window|learnloop.hint_window]] — imports `module`; calls `session_clause`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/ad1_codex_rereview_fixes_helpers.py](../../../../../../../tests/ad1_codex_rereview_fixes_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/ad1_reading_opportunities_helpers.py](../../../../../../../tests/ad1_reading_opportunities_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/ad23_contract_helpers.py](../../../../../../../tests/ad23_contract_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/ad23_fakes.py](../../../../../../../tests/ad23_fakes.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/ad23_fix_r8_helpers.py](../../../../../../../tests/ad23_fix_r8_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/ad2_serving_helpers.py](../../../../../../../tests/ad2_serving_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/ad_ingest_fakes.py](../../../../../../../tests/ad_ingest_fakes.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/ad_projection_helpers.py](../../../../../../../tests/ad_projection_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/apply_write_ahead_helpers.py](../../../../../../../tests/apply_write_ahead_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/approach_map_fakes.py](../../../../../../../tests/approach_map_fakes.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/assumed_known_helpers.py](../../../../../../../tests/assumed_known_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/canonical_facet_helpers.py](../../../../../../../tests/canonical_facet_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/questions.py](../../../../../../../src/learnloop/db/stores/questions.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
