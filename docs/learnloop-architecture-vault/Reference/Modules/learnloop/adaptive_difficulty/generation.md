---
title: "learnloop.adaptive_difficulty.generation"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/generation.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/generation.py"
source_commit: "38c895e230ef534fc7b4a2eff18a51ca456a06a2"
source_commit_timestamp: "2026-10-24T10:23:24-04:00"
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
  - "learnloop.adaptive_difficulty.generation module"
  - "src/learnloop/adaptive_difficulty/generation.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.generation`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.generation` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: Generation at a feature point, and the re-forecast of a landed commission (spec §7.1, §7.4).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/generation.py](../../../../../../src/learnloop/adaptive_difficulty/generation.py) |
| Source lines | 464 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `38c895e230ef534fc7b4a2eff18a51ca456a06a2` |
| Commit timestamp | `2026-10-24T10:23:24-04:00` |

## Public API

- `class ProtectedRequest(ValueError)` ([source](../../../../../../src/learnloop/adaptive_difficulty/generation.py), line 55) — A commissioned generation request quotes withheld material: it is not sent (A8).
- `class CommissionedRequestGuard` ([source](../../../../../../src/learnloop/adaptive_difficulty/generation.py), line 59) — The authoring call's material view and send-time revalidation (fix round 9, R2).
  - `__init__(self) -> None` (line 69; internal)
  - `ground(self, sources: Sequence[tuple[Any, Any]]) -> None` (line 75; public) — Register grounding spans the request quotes: each is revalidated at every dispatch.
  - `vault_view(self, vault: Any, repository: Any) -> Any` (line 80; public)
  - `__call__(self, request_text: str, sources: Sequence[tuple[Any, Any]]=()) -> None` (line 87; internal) — Revalidate one serialized request with protection read afresh (the vault reloaded from its root), so a source held out between the first request and a repair, or a predicate that became unreadable, refuses the request (fix round 10, R5).
- `contract_on(config: Any) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/generation.py), line 128)
- `lo_cell_facet(view: Any, learning_object_id: str) -> str | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/generation.py), line 132) — The LO's highest-weight facet (summed item weights), ties by facet id.
- `rung_features(point: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/generation.py), line 161) — The commissioned point as a ``RungTarget``'s task features (the five audited dimensions, and ``tools`` only when it differs from the closed-book reference).
- `commission_point(vault: Any, repository: Any, *, learning_object_id: str, incumbent: Any, now: str, selection_id: str | None=None, view: Any=None) -> tuple[dict[str, Any], str, str] | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/generation.py), line 173) — Under ``generation_contract``: ``(features, capability, selection id)`` of the commissioned point for the LO's cell at the incumbent waypoint's capability (the open commission, else a new commission draw).
- `goal_focus_facets(vault: Any, repository: Any, *, scope: Mapping[str, Sequence[str]], target_recall: float, view: Any) -> list[str]` ([source](../../../../../../src/learnloop/adaptive_difficulty/generation.py), line 233) — Under the generation contract, the goal's facets a generation request focuses on (Codex verify F37, fix rounds 11-12): of the goal's scope as AD's material view resolves it (``scope``: LO id -> its scope facets, from the visible items), those whose AD forecast of an unassisted s…
- `serve_commissions(connection: Any, *, view: Any, now: str | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/adaptive_difficulty/generation.py), line 268) — The open commissions a serve draw made (§6.1, "at a serve draw"): those the generation path drew for itself are generated by that path, so only these need a job of their own.
- `schedule_commission_generation(vault: Any, repository: Any, enqueue: Callable[[str, str], Any] | None) -> list[str]` ([source](../../../../../../src/learnloop/adaptive_difficulty/generation.py), line 279) — §6.1 "The chosen point is commissioned for generation and runs in the background" (Codex review F5): after a serve commits, each open serve-time commission's generation is queued on the vault's durable job queue, ``enqueue(commission_id, learning_object_id)``.
- `landing_owner(vault: Any, item: Any, commissions: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/generation.py), line 352) — The commission that owns a landed item: of the commissions of the item's cells drawn at or before it landed, the last in draw order (``commissions`` is in ``(created_at, rowid)`` order, a total order even within one second).
- `record_landed_commissions(vault: Any, repository: Any, connection: Any, *, now: str, view: Any=None) -> list[str]` ([source](../../../../../../src/learnloop/adaptive_difficulty/generation.py), line 373) — §7.4: append an ``ad_commission_results`` receipt for each item that landed in a commissioned cell.

### Module constants

- `LOG` ([src/learnloop/adaptive_difficulty/generation.py](../../../../../../src/learnloop/adaptive_difficulty/generation.py), line 40)
- `CONTRACT_VERSION` ([src/learnloop/adaptive_difficulty/generation.py](../../../../../../src/learnloop/adaptive_difficulty/generation.py), line 42)
- `CONTRACT_TEXT` ([src/learnloop/adaptive_difficulty/generation.py](../../../../../../src/learnloop/adaptive_difficulty/generation.py), line 43)
- `WAYPOINT_CLAUSE` ([src/learnloop/adaptive_difficulty/generation.py](../../../../../../src/learnloop/adaptive_difficulty/generation.py), line 49)
- `SOURCE` ([src/learnloop/adaptive_difficulty/generation.py](../../../../../../src/learnloop/adaptive_difficulty/generation.py), line 51)
- `MODELLED` ([src/learnloop/adaptive_difficulty/generation.py](../../../../../../src/learnloop/adaptive_difficulty/generation.py), line 52)

### Explicit exports

`__all__` declares:

- `CONTRACT_TEXT`
- `CommissionedRequestGuard`
- `ProtectedRequest`
- `goal_focus_facets`
- `CONTRACT_VERSION`
- `SOURCE`
- `WAYPOINT_CLAUSE`
- `commission_point`
- `landing_owner`
- `contract_on`
- `lo_cell_facet`
- `record_landed_commissions`
- `rung_features`
- `schedule_commission_generation`
- `serve_commissions`

## Internal implementation anchors

- `_queueable_commissions(vault: Any, repository: Any, *, view: Any=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/adaptive_difficulty/generation.py), line 312) — The open serve-time commissions to queue, read in one AD operation.
- `_cells(vault: Any, item: Any) -> list[tuple[str, str]]` ([source](../../../../../../src/learnloop/adaptive_difficulty/generation.py), line 325) — The cells a landed (active) item belongs to: each of its facets at its capability.
- `_matches_point(features: Any, row: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/generation.py), line 335) — Whether the landing's realized features are the commission's requested point (recorded, never a condition of ownership: Codex verify F15, round 6).
- `_at_or_after(stamp: str, other: str) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/generation.py), line 347)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/dose|learnloop.adaptive_difficulty.dose]] — imports `lo_cell_facet`; statically calls `lo_cell_facet`
- [[Reference/Modules/learnloop/adaptive_difficulty/serve|learnloop.adaptive_difficulty.serve]] — imports `record_landed_commissions`; statically calls `record_landed_commissions`
- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `CONTRACT_TEXT`, `CommissionedRequestGuard`, `WAYPOINT_CLAUSE`, `goal_focus_facets`, `module`; statically calls `CommissionedRequestGuard`, `commission_point`, `contract_on`, `goal_focus_facets`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `contract_on`; statically calls `contract_on`
- [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]] — imports `schedule_commission_generation`; statically calls `schedule_commission_generation`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]] — imports `item_revision`; calls `item_revision`
- [[Reference/Modules/learnloop/adaptive_difficulty/logs|learnloop.adaptive_difficulty.logs]] — imports `warn_failure`; calls `warn_failure`
- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `detached_view`, `material_view`; calls `detached_view`, `material_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]] — imports `entry`, `own_write`; calls `entry`, `own_write`
- [[Reference/Modules/learnloop/adaptive_difficulty/predict|learnloop.adaptive_difficulty.predict]] — imports `module`; calls `capability`, `current_spec`, `facet_weights`, `point_spec`, `predict`
- [[Reference/Modules/learnloop/adaptive_difficulty/relatedness|learnloop.adaptive_difficulty.relatedness]] — imports `lo_facets`; calls `lo_facets`
- [[Reference/Modules/learnloop/adaptive_difficulty/replay|learnloop.adaptive_difficulty.replay]] — imports `module`; calls `days`, `snapshot`
- [[Reference/Modules/learnloop/adaptive_difficulty/selection|learnloop.adaptive_difficulty.selection]] — imports `module`; calls `constants_from_config`, `entry_point`
- [[Reference/Modules/learnloop/adaptive_difficulty/serving|learnloop.adaptive_difficulty.serving]] — imports `commission_draw`, `view_for`; calls `commission_draw`, `view_for`
- [[Reference/Modules/learnloop/adaptive_difficulty/successor|learnloop.adaptive_difficulty.successor]] — imports `generation_contract_on`, `successor_active`; calls `generation_contract_on`, `successor_active`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/scopes|learnloop.db.scopes]] — imports `current_ingest_job_id`; calls `current_ingest_job_id`
- [[Reference/Modules/learnloop/db/stores/ad_serving|learnloop.db.stores.ad_serving]] — imports `module`; calls `has_table`, `insert_commission_result`, `instant`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/dose|learnloop.adaptive_difficulty.dose]], [[Reference/Modules/learnloop/adaptive_difficulty/serve|learnloop.adaptive_difficulty.serve]], [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]], [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad23_contract.py](../../../../../../tests/test_ad23_contract.py) — direct import
  - `test_a_commissioned_repair_after_protection_changed_mid_call_is_refused`
  - `test_a_held_out_sources_canonical_note_never_reaches_a_commissioned_request`
  - `test_goal_focus_follows_the_live_decision_view_with_promoted_predictor_off`
  - `test_with_the_predicate_unavailable_ad_does_nothing_and_the_incumbent_serves`
- [tests/test_ad23_fix_r5.py](../../../../../../tests/test_ad23_fix_r5.py) — direct import
  - `test_an_item_that_lands_after_expiry_gets_a_marked_receipt_and_a_later_draw_owns_later_items`
- [tests/test_ad23_fix_r6.py](../../../../../../tests/test_ad23_fix_r6.py) — direct import
  - `test_a_late_item_off_the_successors_point_is_the_successors_landing`
- [tests/test_ad23_fix_r7.py](../../../../../../tests/test_ad23_fix_r7.py) — direct import
  - `test_a_protected_item_never_steers_the_commissioned_cell_or_readiness`
  - `test_a_protected_landing_never_closes_forecasts_or_receipts_a_commission`
  - `test_features_match_reads_the_audited_features_the_receipt_records`
  - `test_with_the_predicate_unavailable_nothing_is_reconciled`
- [tests/test_ad23_fix_r9.py](../../../../../../tests/test_ad23_fix_r9.py) — direct import
  - `test_a_commissioned_request_quoting_withheld_material_is_refused_before_it_is_sent`
- [tests/test_ad23_fix_review.py](../../../../../../tests/test_ad23_fix_review.py) — direct import
  - `test_a_commission_queued_before_models_go_off_waits_and_resumes`
  - `test_a_serve_commission_queues_its_generation_once_at_its_point`
- [tests/test_ad23_owner_decisions.py](../../../../../../tests/test_ad23_owner_decisions.py) — direct import
  - `test_a_cancelled_commission_stays_cancelled_when_models_come_back_on`
  - `test_a_commission_waiting_on_models_stays_open_and_a_cancelled_one_expires`
  - `test_an_unlanded_commission_expires_seven_days_after_its_job_and_a_fresh_one_is_drawn`
- [tests/test_ad2_serving.py](../../../../../../tests/test_ad2_serving.py) — direct import
  - `test_commission_result_appended_never_mutates_selection`
  - `test_generation_prompt_has_no_band_language_under_successor`

## Modification guidance

- Make changes here when the responsibility remains generation within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/generation.py](../../../../../../src/learnloop/adaptive_difficulty/generation.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
