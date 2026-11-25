---
title: "learnloop.db.stores.activity"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/activity.py"
source_paths:
  - "src/learnloop/db/stores/activity.py"
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
  - "learnloop.db.stores.activity module"
  - "src/learnloop/db/stores/activity.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.activity`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.activity` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Activity catalog, observations, surfaces and their lineage.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/activity.py](../../../../../../../src/learnloop/db/stores/activity.py) |
| Source lines | 2630 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class ActivityStoreMixin` ([source](../../../../../../../src/learnloop/db/stores/activity.py), line 59)
  - `ensure_activity_family(self, *, purpose: str, legacy_kind: str | None, title: str | None, clock: Clock | None=None) -> str` (line 68; public) — Content-addressed activity family, idempotent on ``(purpose, legacy_kind, title)``.
  - `ensure_activity_family_version(self, *, family_id: str, version: int, family_spec_json: str, clock: Clock | None=None) -> str` (line 119; public) — Immutable family-spec snapshot, idempotent on ``(family_id, version)``.
  - `ensure_activity_card(self, *, family_id: str, clock: Clock | None=None) -> str` (line 149; public) — The family's canonical card (one card per family in the P0.1 legacy world).
  - `ensure_activity_card_version(self, *, card_id: str, version: int, card_contract_hash: str, contract_json: str, schema_version: int, predecessor_card_version_id: str | None=None, lineage_kind: str | None=None, legacy_contract_version_id: str | None=None, clock: Clock | None=None) -> str` (line 184; public) — Content-addressed card version, idempotent on ``(card_id, card_contract_hash)``.
  - `ensure_activity_surface(self, *, card_version_id: str, surface_hash: str, fingerprint: str | None, surface_json: str, legacy_practice_item_id: str | None=None, legacy_surface_unverifiable: bool=False, clock: Clock | None=None) -> str` (line 259; public) — Content-addressed surface, idempotent on ``(card_version_id, surface_hash)``.
  - `insert_surface_reservation(self, *, surface_id: str, goal_id: str | None, target_contract_version_id: str | None, target_support_hash: str | None, purpose: str, eligibility_json: str, clock: Clock | None=None) -> str` (line 309; public) — Reserve a surface (§4.5).
  - `close_surface_reservation(self, *, reservation_id: str, status: str, administration_id: str | None=None, expected_status: str | None=None, clock: Clock | None=None) -> bool` (line 357; public) — Transition a reservation to a terminal status (the one permitted mutation on this append-mostly substrate).
  - `open_administration_atomic(self, *, reservation_id: str | None, surface_id: str, card_version_id: str, family_id: str, purpose: str, surface_hash: str, fingerprint: str | None, snapshot_hash: str, snapshot_json: str, consumes_unseen: bool, pins: Mapping[str, Any] | None=None, algorithm_version: str, enforce_eligibility: bool=False, clock: Clock | None=None) -> dict[str, Any]` (line 393; public) — The render burn boundary (§4.5).
  - `write_administration_lineage_atomic(self, *, surface_id: str, card_version_id: str, family_id: str, purpose: str, surface_hash: str, fingerprint: str | None, snapshot_hash: str, snapshot_json: str, consumes_unseen: bool, algorithm_version: str, evidence_eligibility: str | None, eligibility_reason: str | None, reading_phase: str | None=None, admin_context: Mapping[str, Any] | None=None, attempt_id: str | None=None, response_ref: str | None=None, response_ledger_json: str | None=None, fault_after: 'frozenset[str]'=frozenset(), clock: Clock | None=None) -> dict[str, Any]` (line 592; public) — Write the full RAW-EVENT lineage for one administration as ONE transaction (§7.4/§7.5): administration (+ its context, folded in so no NULL-context window exists) + rendered & submitted exposures + expose/consume lifecycle + observation + measurement events (administration_opene…
  - `append_exposure_event(self, *, surface_id: str, administration_id: str | None, surface_hash: str, fingerprint: str | None, kind: str, purpose: str, consumes_unseen: bool=False, detail_json: str | None=None, clock: Clock | None=None) -> str` (line 779; public)
  - `append_surface_lifecycle_event(self, *, surface_id: str, kind: str, reservation_id: str | None=None, administration_id: str | None=None, reason: str | None=None, detail_json: str | None=None, clock: Clock | None=None) -> str` (line 818; public)
  - `insert_activity_observation(self, *, administration_id: str, surface_id: str, attempt_id: str | None=None, response_ref: str | None=None, evidence_eligibility: str | None=None, eligibility_reason: str | None=None, clock: Clock | None=None) -> str` (line 853; public)
  - `insert_retirement_record(self, *, scope: str, family_id: str | None, card_version_id: str | None, surface_id: str | None, reason: str, provenance: str, replacement_proposal_json: str | None=None, lifecycle_event_id: str | None=None, interaction_event_id: str | None=None, clock: Clock | None=None) -> str` (line 889; public)
  - `append_interaction_event(self, *, kind: str, origin: str, subject_type: str | None=None, subject_id: str | None=None, administration_id: str | None=None, surface_id: str | None=None, attempt_id: str | None=None, affect_tap_kind: str | None=None, attempt_duration_ms: int | None=None, payload_json: str | None=None, occurred_at: str | None=None, received_at: str | None=None, actor: str | None=None, client_id: str | None=None, session_id: str | None=None, visit_id: str | None=None, payload_schema_version: str | None=None, source_id: str | None=None, revision_id: str | None=None, render_view_id: str | None=None, locator_json: str | None=None, annotation_id: str | None=None, commitment_id: str | None=None, activity_id: str | None=None, payload_hash: str | None=None, client_idempotency_key: str | None=None, privacy_locality: str | None=None, consent_context: str | None=None, producer_version: str | None=None, app_version: str | None=None, policy_version: str | None=None, supersedes_event_id: str | None=None, clock: Clock | None=None) -> str` (line 931; public)
  - `append_measurement_event(self, *, administration_id: str, kind: str, algorithm_version: str, observation_id: str | None=None, payload_json: str | None=None, clock: Clock | None=None) -> str` (line 1028; public)
  - `measurement_events_for_administration(self, administration_id: str) -> list[dict[str, Any]]` (line 1063; public) — The administration's measurement events in append order (ledger read).
  - `set_active_interpretation(self, *, observation_id: str, interpretation_id: str) -> None` (line 1079; public) — Point the observation's projection head at an interpretation.
  - `administration_by_legacy_presentation(self, presentation_id: str) -> dict[str, Any] | None` (line 1091; public) — Idempotency lookup for the §7.1 step-3 presentation backfill: the synthetic administration stores the presentation id in its snapshot.
  - `exposures_for_surface(self, surface_id: str) -> list[dict[str, Any]]` (line 1106; public)
  - `exposures_by_surface_hash(self, surface_hash: str) -> list[dict[str, Any]]` (line 1117; public)
  - `exposures_by_fingerprint(self, fingerprint: str) -> list[dict[str, Any]]` (line 1128; public)
  - `fetch_surface(self, surface_id: str) -> dict[str, Any] | None` (line 1141; public)
  - `reserved_assessment_surfaces(self) -> list[dict[str, Any]]` (line 1148; public) — Surfaces holding a LIVE assessment reservation (§8.1).
  - `fetch_administration(self, administration_id: str) -> dict[str, Any] | None` (line 1163; public)
  - `observations_for_administration(self, administration_id: str) -> list[dict[str, Any]]` (line 1175; public) — All observation rows recorded under an administration, oldest first.
  - `fetch_reservation(self, reservation_id: str) -> dict[str, Any] | None` (line 1186; public)
  - `surface_lifecycle_history(self, surface_id: str) -> list[dict[str, Any]]` (line 1194; public)
  - `retirement_records_for_surface(self, surface_id: str) -> list[dict[str, Any]]` (line 1205; public)
  - `retirement_records_for_card_version(self, card_version_id: str) -> list[dict[str, Any]]` (line 1213; public)
  - `surfaces_for_card_version(self, card_version_id: str) -> list[dict[str, Any]]` (line 1226; public)
  - `surfaces_for_legacy_practice_item(self, practice_item_id: str) -> list[dict[str, Any]]` (line 1234; public) — Existing substrate surfaces backed by one legacy Practice Item.
  - `surfaces_for_family(self, family_id: str) -> list[dict[str, Any]]` (line 1255; public)
  - `observation_by_attempt(self, attempt_id: str) -> dict[str, Any] | None` (line 1269; public) — The attempt's newest observation (None when it has none): the one the authoritative ledger reads (``observation_ledger``, same order).
  - `first_live_administration_at(self) -> str | None` (line 1284; public) — When the vault first wrote an activity administration itself (not one the §7.1 backfill reconstructed): the stored fact that the activity substrate existed from then on.
  - `answer_grade_records(self) -> list[dict[str, Any]]` (line 1294; public) — Every answer with its newest observation (``observation_id``, None without one) and whether that observation holds a raw grade (``graded``): what an answer's grade record is, read in one query.
  - `observation_attempt_id(self, observation_id: str) -> str | None` (line 1313; public) — Reverse of :meth:`observation_by_attempt` — the practice attempt an activity observation was minted for (ruling A: the grade-points adjudication lane needs the attempt to write its superseding ``grading_evidence`` revision).
  - `mark_surface_unverifiable(self, surface_id: str) -> None` (line 1327; public)
  - `insert_legacy_administration(self, *, surface_id: str, card_version_id: str, family_id: str, purpose: str, snapshot_hash: str, snapshot_json: str, target_contract_version_id: str | None=None, target_support_hash: str | None=None, eligibility_json: str | None=None, created_at: str) -> str` (line 1335; public) — Direct (non-atomic) administration insert for §7.1 backfill, timestamped at the recorded historical time (never now()) so re-runs stay byte-stable.
  - `append_exposure_event_at(self, *, surface_id: str, administration_id: str | None, surface_hash: str, fingerprint: str | None, kind: str, purpose: str, consumes_unseen: bool, created_at: str, detail_json: str | None=None) -> str` (line 1383; public) — Exposure insert timestamped at a recorded historical time (backfill).
  - `interaction_events_for_attempt(self, attempt_id: str) -> list[dict[str, Any]]` (line 1424; public)
  - `upsert_capability_alias(self, *, registry_version: int, legacy_value: str, canonical: str | None, clock: Clock | None=None) -> str` (line 1436; public)
  - `capability_alias(self, *, registry_version: int, legacy_value: str) -> dict[str, Any] | None` (line 1464; public)
  - `ensure_task_feature_schema_version(self, *, schema_slug: str, version: int, dimensions_json: str, content_hash: str, clock: Clock | None=None) -> str` (line 1472; public)
  - `task_feature_schema_version(self, schema_version_id: str) -> dict[str, Any] | None` (line 1501; public)
  - `ensure_activity_pattern(self, *, pattern_slug: str, clock: Clock | None=None) -> str` (line 1508; public)
  - `ensure_activity_pattern_version(self, *, pattern_id: str, version: int, content_hash: str, fields: Mapping[str, Any], status: str, clock: Clock | None=None) -> dict[str, Any]` (line 1523; public) — Content-addressed pattern version, idempotent on ``(pattern_id, content_hash)``.
  - `activity_pattern_version(self, pattern_version_id: str) -> dict[str, Any] | None` (line 1598; public)
  - `activity_pattern_versions(self, *, status: str | None=None) -> list[dict[str, Any]]` (line 1605; public)
  - `activity_pattern_version_by_slug(self, *, pattern_slug: str, status: str | None=None) -> dict[str, Any] | None` (line 1618; public)
  - `upsert_activity_family_authoring(self, *, family_version_id: str, fields: Mapping[str, Any], clock: Clock | None=None) -> None` (line 1646; public) — Insert/replace the authoring side row keyed by the immutable P0 family version id.
  - `set_activity_family_authoring_status(self, *, family_version_id: str, status: str) -> None` (line 1696; public)
  - `activity_family_authoring(self, family_version_id: str) -> dict[str, Any] | None` (line 1706; public)
  - `upsert_activity_card_authoring(self, *, card_version_id: str, fields: Mapping[str, Any], clock: Clock | None=None) -> None` (line 1714; public)
  - `activity_card_authoring(self, card_version_id: str) -> dict[str, Any] | None` (line 1757; public)
  - `activity_family_authoring_purposes(self, family_id: str) -> dict[str, str]` (line 1765; public) — Authoring purposes across every version of one stable family (§1.1 invariant 2 / §9.1 purpose-immutability check), keyed by family_version_id.
  - `activity_family_version_family_id(self, family_version_id: str) -> str | None` (line 1781; public)
  - `create_card_lineage(self, *, card_id: str | None=None, family_id: str | None=None, clock: Clock | None=None) -> str` (line 1793; public)
  - `card_lineage(self, lineage_id: str) -> dict[str, Any] | None` (line 1809; public)
  - `append_card_lineage_edge(self, *, lineage_id: str, to_card_version_id: str, edge_kind: str, classifier_version: str, from_card_version_id: str | None=None, rationale: Mapping[str, Any] | None=None, clock: Clock | None=None) -> str` (line 1816; public)
  - `card_lineage_edges(self, lineage_id: str) -> list[dict[str, Any]]` (line 1851; public)
  - `lineage_for_card_version(self, card_version_id: str) -> str | None` (line 1859; public) — Resolve the lineage a card version belongs to via its lineage edges.
  - `upsert_activity_card_state(self, *, card_lineage_id: str, scheduler_algorithm_version: str, model_label: str, learner_id: str='local', difficulty: float | None=None, stability: float | None=None, retrievability: float | None=None, due_at: str | None=None, last_eligible_review_at: str | None=None, lapse_episode_id: str | None=None, active: bool=True, projection_head: Mapping[str, Any] | None=None, clock: Clock | None=None) -> str` (line 1873; public)
  - `activity_card_state(self, *, card_lineage_id: str, scheduler_algorithm_version: str, learner_id: str='local') -> dict[str, Any] | None` (line 1942; public)
  - `activity_administration(self, administration_id: str) -> dict[str, Any] | None` (line 1962; public)
  - `set_administration_context(self, *, administration_id: str, reading_phase: str | None=None, admin_context: Mapping[str, Any] | None=None) -> None` (line 1969; public)
  - `record_fingerprint_membership(self, *, surface_id: str, namespace: str, value_hash: str, provenance: str | None=None, status: str | None=None, confidence: float | None=None, clock: Clock | None=None) -> str` (line 1995; public)
  - `fingerprint_memberships_for_surface(self, surface_id: str) -> list[dict[str, Any]]` (line 2038; public)
  - `surfaces_sharing_membership(self, *, namespace: str, value_hash: str, exclude_surface_id: str | None=None) -> list[str]` (line 2046; public) — All surfaces in a given (namespace, value_hash) hard group.
  - `upsert_soft_kinship_features(self, *, surface_id: str, feature_schema_version: str, features: Mapping[str, Any], clock: Clock | None=None) -> str` (line 2066; public)
  - `soft_kinship_features_for_surface(self, *, surface_id: str, feature_schema_version: str | None=None) -> dict[str, Any] | None` (line 2103; public)
  - `upsert_activity_surface_authoring(self, *, surface_id: str, fields: Mapping[str, Any], clock: Clock | None=None) -> None` (line 2125; public)
  - `activity_surface_authoring(self, surface_id: str) -> dict[str, Any] | None` (line 2175; public)
  - `activity_exposure_events_for_surface(self, surface_id: str) -> list[dict[str, Any]]` (line 2182; public)
  - `enqueue_surface_mint_request(self, *, card_version_id: str, generator_version: str, gate_policy_version: str, anchor_surface_id: str | None=None, requested_angle_json: str='', token_cost_json: str | None=None, clock: Clock | None=None) -> str` (line 2195; public) — Idempotent on ``(card_version, anchor, requested_angle, generator, gate_policy)`` (§5.6).
  - `surface_mint_request(self, request_id: str) -> dict[str, Any] | None` (line 2264; public)
  - `surface_mint_requests_for_card_version(self, card_version_id: str, *, statuses: Sequence[str] | None=None) -> list[dict[str, Any]]` (line 2271; public)
  - `claim_next_surface_mint_request(self, *, worker_id: str, now_iso: str, lease_expires_at: str, lease_cutoff_iso: str) -> dict[str, Any] | None` (line 2292; public) — Atomically claim the next ``pending`` mint request for ``worker_id``.
  - `claim_surface_mint_request(self, request_id: str, *, worker_id: str, now_iso: str, lease_expires_at: str, reclaim_statuses: Sequence[str]=('pending', 'failed')) -> dict[str, Any] | None` (line 2358; public) — Claim ONE named request under a fenced lease (PF-b, 078 pattern).
  - `release_surface_mint_request(self, request_id: str, *, expected_lease_epoch: int, clock: Clock | None=None) -> bool` (line 2391; public) — Return a cancelled, still-leased request to ``pending`` (resumable).
  - `set_surface_mint_candidate(self, *, request_id: str, candidate_surface_id: str, gate_results_json: str | None=None, token_cost_json: str | None=None, expected_lease_epoch: int | None=None, clock: Clock | None=None) -> bool` (line 2409; public) — Record the gated candidate and move the request to ``candidate_ready``.
  - `resolve_surface_mint_request(self, *, request_id: str, status: str, gate_results_json: str | None=None, failure_reason: str | None=None, candidate_surface_id: str | None=None, expected_lease_epoch: int | None=None, require_active: bool=False, clock: Clock | None=None) -> bool` (line 2447; public) — Terminal transition to ``admitted`` / ``rejected`` / ``failed``.
  - `obsolete_surface_mint_requests_for_card_versions(self, card_version_ids: Sequence[str], *, clock: Clock | None=None) -> int` (line 2492; public) — Mark all not-yet-terminal mint work for the given card versions ``obsolete`` (§5.6: card/family retirement makes pending work obsolete).
  - `reader_interaction_events(self, *, kind: str | None=None, subject_id: str | None=None, subject_type: str | None=None, since: str | None=None) -> list[dict[str, Any]]` (line 2522; public) — Reader interaction events (payload_json decoded), oldest first.
  - `first_cold_observation_for_target(self, target_contract_version_id: str) -> str | None` (line 2556; public) — created_at of the FIRST cold administration pinned to this target contract version (design A.1 supersession).
  - `activity_family_purpose_for_card_version(self, card_version_id: str) -> str | None` (line 2585; public) — The immutable family purpose backing a card version (§12.4 role check).
  - `resolved_activity_for_surface(self, surface_id: str) -> dict[str, Any] | None` (line 2608; public) — Reconstruct the family/card identity of an existing surface (for opening a reserved assessment administration from the run's stored ``reserved_surface_id`` alone).

### Module constants

- `_MEASUREMENT_EVENT_KINDS` ([src/learnloop/db/stores/activity.py](../../../../../../../src/learnloop/db/stores/activity.py), line 20)

## Internal implementation anchors

- `_decode_exposure_event(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/activity.py), line 40)
- `_decode_surface(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/activity.py), line 47)
- `class _InjectedLineageFault(RuntimeError)` ([source](../../../../../../../src/learnloop/db/stores/activity.py), line 54) — Fault injected inside :meth:`Repository.write_administration_lineage_atomic` to prove the raw-event transaction rolls back as one unit (§7.4 fault injection).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `ActivityStoreMixin`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/row_serialization|learnloop.db.row_serialization]] — imports `_loads`; calls `_loads`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `sqlite3`, `typing`
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

1. Modify [src/learnloop/db/stores/activity.py](../../../../../../../src/learnloop/db/stores/activity.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
