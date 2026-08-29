---
title: "learnloop.diagnosis.misconceptions"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/misconceptions.py"
source_paths:
  - "src/learnloop/diagnosis/misconceptions.py"
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
  - "learnloop.diagnosis.misconceptions module"
  - "src/learnloop/diagnosis/misconceptions.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.misconceptions`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.misconceptions` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Misconception registry normalization and evidence-based resolution.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/misconceptions.py](../../../../../../src/learnloop/diagnosis/misconceptions.py) |
| Source lines | 815 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `normalize_text(text: str) -> str` ([source](../../../../../../src/learnloop/diagnosis/misconceptions.py), line 31) — Case/whitespace/punctuation-normalized statement for deterministic match.
- `request_misconception_match(client: OperationClient, context: MisconceptionMatchContext) -> MisconceptionMatch` ([source](../../../../../../src/learnloop/diagnosis/misconceptions.py), line 81) — Run the feature-owned misconception matching operation.
- `normalize_attempt_misconceptions(vault: LoadedVault, repository: Repository, *, attempt_id: str, learning_object_id: str, ai_client: object | None=None, clock: Clock | None=None) -> list[str]` ([source](../../../../../../src/learnloop/diagnosis/misconceptions.py), line 154) — Normalize an attempt's misconception error events into the registry (spec §2.2).
- `promote_candidate_if_independent(vault: LoadedVault, repository: Repository, candidate_id: str, *, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/misconceptions.py), line 381) — Promote ``candidate_id`` if §5.6 arm (b) is now satisfied; else None.
- `promote_candidate(vault: LoadedVault, repository: Repository, candidate: dict, *, learning_object, reason: str, clock: Clock | None) -> str` ([source](../../../../../../src/learnloop/diagnosis/misconceptions.py), line 432) — Mint a durable compositional misconception from a promoted candidate (§10.2).
- `misconception_posterior(vault: LoadedVault, repository: Repository, record: MisconceptionRecord) -> float` ([source](../../../../../../src/learnloop/diagnosis/misconceptions.py), line 667) — P(learner still holds ``record``) from persisted evidence (spec §7).
- `update_misconception_posteriors_and_resolve(vault: LoadedVault, repository: Repository, *, learning_object_id: str, clock: Clock | None=None) -> list[str]` ([source](../../../../../../src/learnloop/diagnosis/misconceptions.py), line 733) — Resolve (or reactivate) registry rows on ``learning_object_id`` by posterior (§7).
- `normalize_and_resolve_attempt(vault: LoadedVault, repository: Repository, *, attempt_id: str, learning_object_id: str, ai_client: object | None=None, clock: Clock | None=None) -> list[str]` ([source](../../../../../../src/learnloop/diagnosis/misconceptions.py), line 778) — Run normalization then posterior resolution for one attempt (spec §2.2 + §7).

### Module constants

- `_PUNCT_RE` ([src/learnloop/diagnosis/misconceptions.py](../../../../../../src/learnloop/diagnosis/misconceptions.py), line 27)
- `_WS_RE` ([src/learnloop/diagnosis/misconceptions.py](../../../../../../src/learnloop/diagnosis/misconceptions.py), line 28)
- `_PRIOR_FLOOR` ([src/learnloop/diagnosis/misconceptions.py](../../../../../../src/learnloop/diagnosis/misconceptions.py), line 658)
- `_PRIOR_CEIL` ([src/learnloop/diagnosis/misconceptions.py](../../../../../../src/learnloop/diagnosis/misconceptions.py), line 659)
- `_PROB_EPS` ([src/learnloop/diagnosis/misconceptions.py](../../../../../../src/learnloop/diagnosis/misconceptions.py), line 660)

## Internal implementation anchors

- `_confusable_neighbor_concepts(vault: LoadedVault, concept_id: str | None) -> list[str]` ([source](../../../../../../src/learnloop/diagnosis/misconceptions.py), line 38) — Concepts reachable from ``concept_id`` over ``confusable_with`` edges (§2.2.1).
- `_candidate_misconceptions(vault: LoadedVault, repository: Repository, learning_object_id: str) -> list[MisconceptionRecord]` ([source](../../../../../../src/learnloop/diagnosis/misconceptions.py), line 54) — Registry rows a new attribution on this LO could merge into (spec §2.2.1).
- `_match_misconception(statement: str, candidates: list[MisconceptionRecord], ai_client: object | None, *, learning_object_id: str) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/misconceptions.py), line 97) — Return the id of the registry row ``statement`` belongs to, or ``None`` (new).
- `_event_facet_ids(vault: LoadedVault, event: dict, attempt: dict | None) -> list[str]` ([source](../../../../../../src/learnloop/diagnosis/misconceptions.py), line 139) — Coarse facets a new registry row targets (spec §1.1 / §2.2.4).
- `_surface_family_for_attempt(vault: LoadedVault, attempt: dict | None) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/misconceptions.py), line 247)
- `_probe_signature_reproduced(candidate: dict, attempt: dict | None) -> bool` ([source](../../../../../../src/learnloop/diagnosis/misconceptions.py), line 258)
- `_postdictive_trace_consistent(vault: LoadedVault, repository: Repository, event: dict, attempt: dict | None) -> bool` ([source](../../../../../../src/learnloop/diagnosis/misconceptions.py), line 266) — Hard-veto only deterministic claims contradicted by elicited full credit.
- `_promotion_reason(vault: LoadedVault, candidate: dict, attempt: dict | None) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/misconceptions.py), line 302) — Which §10.3 condition (if any) promotes ``candidate`` to a durable belief.
- `_independent_group_count(vault: LoadedVault, candidate: dict) -> int` ([source](../../../../../../src/learnloop/diagnosis/misconceptions.py), line 358) — Distinct independent evidence groups behind ``candidate`` (augmentation §8).
- `_authored_correction(vault: LoadedVault, target_facet_id: str | None, confused_with_facet_id: str | None) -> tuple[str | None, list[str]]` ([source](../../../../../../src/learnloop/diagnosis/misconceptions.py), line 486) — Freeze correction copy from reviewed canonical facet contracts.
- `_normalize_compositional(vault: LoadedVault, repository: Repository, *, attempt_id: str, learning_object_id: str, ai_client: object | None, clock: Clock | None) -> list[str]` ([source](../../../../../../src/learnloop/diagnosis/misconceptions.py), line 523) — mvp-0.7 normalization with promotion discipline (§10.3) and compositional records (§10.2).
- `_clamp(value: float, low: float, high: float) -> float` ([source](../../../../../../src/learnloop/diagnosis/misconceptions.py), line 663)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/error_hunt|learnloop.diagnosis.error_hunt]] — imports `promote_candidate_if_independent`; statically calls `promote_candidate_if_independent`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `normalize_and_resolve_attempt`; statically calls `normalize_and_resolve_attempt`
- [[Reference/Modules/learnloop/diagnosis/probe_blocks|learnloop.diagnosis.probe_blocks]] — imports `normalize_and_resolve_attempt`; statically calls `normalize_and_resolve_attempt`
- [[Reference/Modules/learnloop/substrate/replay|learnloop.substrate.replay]] — imports `update_misconception_posteriors_and_resolve`; statically calls `update_misconception_posteriors_and_resolve`
- [[Reference/Modules/learnloop/tutor/durable_promotion|learnloop.tutor.durable_promotion]] — imports `normalize_text`, `promote_candidate`; statically calls `normalize_text`, `promote_candidate`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `OperationClient`, `execute_structured_operation`; calls `execute_structured_operation`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `MisconceptionRecord`, `Repository`
- [[Reference/Modules/learnloop/diagnosis/ai_contracts|learnloop.diagnosis.ai_contracts]] — imports `MisconceptionMatch`, `MisconceptionMatchContext`, `misconception_match_prompt`; calls `MisconceptionMatchContext`, `misconception_match_prompt`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `materialize_causal_episode`; calls `materialize_causal_episode`
- [[Reference/Modules/learnloop/diagnosis/causal_factor_deferral|learnloop.diagnosis.causal_factor_deferral]] — imports `sweep_promotion_blocking_factors`; calls `sweep_promotion_blocking_factors`
- [[Reference/Modules/learnloop/diagnosis/error_taxonomy_map|learnloop.diagnosis.error_taxonomy_map]] — imports `map_legacy_error_type`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `maybe_reprobe_for_misconception`; calls `maybe_reprobe_for_misconception`
- [[Reference/Modules/learnloop/learner/facet_state_reader|learnloop.learner.facet_state_reader]] — imports `is_canonical_state_vault`; calls `is_canonical_state_vault`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `surface_group_id`; calls `surface_group_id`
- [[Reference/Modules/learnloop/tutor/durable_promotion|learnloop.tutor.durable_promotion]] — imports `sweep_late_promotion_evidence`; calls `sweep_late_promotion_evidence`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `re`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/error_hunt|learnloop.diagnosis.error_hunt]], [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]], [[Reference/Modules/learnloop/diagnosis/probe_blocks|learnloop.diagnosis.probe_blocks]], [[Reference/Modules/learnloop/substrate/replay|learnloop.substrate.replay]], [[Reference/Modules/learnloop/tutor/durable_promotion|learnloop.tutor.durable_promotion]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_causal_attribution_p0.py](../../../../../../tests/test_causal_attribution_p0.py) — direct import
  - `test_event_facet_ids_never_fall_back_to_attempt_facets`
- [tests/test_codex_http_client.py](../../../../../../tests/test_codex_http_client.py) — direct import
  - `test_http_codex_client_misconception_match_bare_payload`
  - `test_http_codex_client_misconception_match_round_trip`
- [tests/test_durable_promotion_arms.py](../../../../../../tests/test_durable_promotion_arms.py) — direct import
  - `test_a_promoted_belief_is_not_resolved_away_by_the_next_posterior_pass`
  - `test_correct_verdict_promotes_the_cause_the_system_asserted`
  - `test_proof_plus_confirmation_promotes`
- [tests/test_independent_group_counting.py](../../../../../../tests/test_independent_group_counting.py) — direct import
  - `test_the_stored_surface_families_list_is_not_trusted`
  - `test_two_genuinely_independent_items_still_promote`
  - `test_two_parts_of_one_stem_do_not_promote_a_durable_belief`
  - `test_unverifiable_provenance_fails_closed`
- [tests/test_km4_taxonomy.py](../../../../../../tests/test_km4_taxonomy.py) — direct import
  - `test_legacy_vault_still_mints_immediately`
  - `test_probe_cannot_preregister_its_signature_after_seeing_response`
  - `test_promotion_on_independent_surface`
  - `test_promotion_requires_independent_surface_or_probe_reproduction`
  - `test_unresolved_cause_set_does_not_mint_misconception`
- [tests/test_misconception_registry.py](../../../../../../tests/test_misconception_registry.py) — direct import
  - `test_a_primed_attempt_that_fires_anyway_still_counts_against_the_learner`
  - `test_clean_discriminating_attempts_resolve`
  - `test_clean_non_discriminating_attempts_do_not_resolve`
  - `test_fired_keyed_fatal_raises_posterior`
  - `test_llm_match_new_inserts_over_text_match`
  - `test_llm_match_same_merges`
  - `test_normalization_creates_row_with_provenance`
  - `test_normalization_dedupes_by_normalized_statement`
  - `test_normalization_is_idempotent`
  - `test_normalization_reactivates_resolved_row`
  - `test_primed_attempts_do_not_resolve_a_misconception`
  - `test_resolution_reactivates_when_posterior_climbs`
  - `test_statementless_events_create_nothing`
- [tests/test_sidecar_adjudication.py](../../../../../../tests/test_sidecar_adjudication.py) — direct import
  - `test_record_reports_the_belief_effect_the_backend_confirms`
- [tests/test_structured_transport_parity.py](../../../../../../tests/test_structured_transport_parity.py) — direct import

## Modification guidance

- Change misconceptions policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/misconceptions.py](../../../../../../src/learnloop/diagnosis/misconceptions.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
