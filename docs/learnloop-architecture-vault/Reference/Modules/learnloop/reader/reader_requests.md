---
title: "learnloop.reader.reader_requests"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reader/reader_requests.py"
source_paths:
  - "src/learnloop/reader/reader_requests.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.reader"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop.reader.reader_requests module"
  - "src/learnloop/reader/reader_requests.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-reader"
---

# `learnloop.reader.reader_requests`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reader.reader_requests` exists within [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] to own the behavior summarized by its module contract: Demand-paged synthesis: reader background requests (spec §6, design B step 6).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reader/reader_requests.py](../../../../../../src/learnloop/reader/reader_requests.py) |
| Source lines | 559 |
| Owning package | [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class ReaderRequestError(ValueError)` ([source](../../../../../../src/learnloop/reader/reader_requests.py), line 63) — Domain error for the demand-paged synthesis service.
- `request_reader_preset_synthesis(client: StructuredTransport, context: ReaderPresetSynthesisContext) -> ReaderPresetSynthesis` ([source](../../../../../../src/learnloop/reader/reader_requests.py), line 67) — Synthesize one reader preset through the shared transport.
- `neighborhood(repository: Repository, *, extraction_id: str, span_id: str, selected_span_ids: Sequence[str]=()) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_requests.py), line 80) — Resolve the bounded union around every selected source block (§6.3).
- `request_key(*, revision_id: str, window: Mapping[str, Any], preset: str, provider: str, model: str, config_hash: str, inventory_profile: str='semantic') -> str` ([source](../../../../../../src/learnloop/reader/reader_requests.py), line 145) — Canonical idempotency key over {revision, window, preset, inventory schema + profile, synthesis/output schema, prompt+provider+model, config/policy} (§6.2).
- `enqueue_request(repository: Repository, *, source_id: str, revision_id: str, extraction_id: str, span_id: str, preset: str, provider: str='stub', model: str='stub-1', config_hash: str='', inventory_profile: str='semantic', annotation_id: str | None=None, commitment_id: str | None=None, client_idempotency_key: str | None=None, selected_text: str='', selection_edited: bool=False, selected_span_ids: Sequence[str]=(), clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_requests.py), line 185) — Enqueue a demand-paged synthesis request (§6).
- `request_status(repository: Repository, *, request_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/reader/reader_requests.py), line 281)
- `cancel_request(repository: Repository, *, request_id: str, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/reader/reader_requests.py), line 296)
- `retry_request(repository: Repository, *, request_id: str, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/reader/reader_requests.py), line 300)
- `model_synthesis(client: Any) -> Callable[[Repository, Mapping[str, Any], Clock | None], dict[str, Any]]` ([source](../../../../../../src/learnloop/reader/reader_requests.py), line 357) — Build the real ``synthesize`` seam for :func:`drain_requests`.
- `drain_requests(repository: Repository, *, worker_id: str='reader-synth', lease_seconds: int=120, limit: int=100, synthesize: Callable[[Repository, Mapping[str, Any], Clock | None], dict[str, Any]] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_requests.py), line 499) — Drain queued requests under a fenced lease.

### Module constants

- `PRIORITY_BAND` ([src/learnloop/reader/reader_requests.py](../../../../../../src/learnloop/reader/reader_requests.py), line 38)
- `MAX_ADJACENT_BLOCKS` ([src/learnloop/reader/reader_requests.py](../../../../../../src/learnloop/reader/reader_requests.py), line 40)
- `TOKEN_CAP` ([src/learnloop/reader/reader_requests.py](../../../../../../src/learnloop/reader/reader_requests.py), line 42)
- `INVENTORY_SCHEMA_VERSION` ([src/learnloop/reader/reader_requests.py](../../../../../../src/learnloop/reader/reader_requests.py), line 45)
- `SYNTHESIS_SCHEMA_VERSION` ([src/learnloop/reader/reader_requests.py](../../../../../../src/learnloop/reader/reader_requests.py), line 46)
- `PROMPT_VERSION` ([src/learnloop/reader/reader_requests.py](../../../../../../src/learnloop/reader/reader_requests.py), line 47)
- `_PRESET_OBJECT_TYPE` ([src/learnloop/reader/reader_requests.py](../../../../../../src/learnloop/reader/reader_requests.py), line 51)

## Internal implementation anchors

- `_land_proposals(repository: Repository, request: Mapping[str, Any], clock: Clock | None, *, object_type: str, exact_text: str, content: Mapping[str, Any], span_ids: list[str], model_provenance: Mapping[str, Any]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/reader/reader_requests.py), line 304) — Land one synthesis result as the reviewable §6.4 artifact pair: a PROPOSED source object + canonical mapping proposal (+ commitment mapping for commit-class presets).
- `_deterministic_synthesis(repository: Repository, request: Mapping[str, Any], clock: Clock | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_requests.py), line 460) — Deterministic, no-LLM synthesis producing a PROPOSED source object + canonical mapping proposal (the reviewable artifact, §6.4).
- `_plus_seconds(now_iso: str, seconds: int) -> str` ([source](../../../../../../src/learnloop/reader/reader_requests.py), line 556)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `module`; statically calls `drain_requests`, `model_synthesis`
- [[Reference/Modules/learnloop/reader/reader_capture|learnloop.reader.reader_capture]] — imports `module`; statically calls `enqueue_request`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `module`; statically calls `cancel_request`, `drain_requests`, `enqueue_request`, `request_status`, `retry_request`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `StructuredTransport`, `execute_structured_operation`; calls `execute_structured_operation`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/reader/ai_contracts|learnloop.reader.ai_contracts]] — imports `ReaderPresetSynthesis`, `ReaderPresetSynthesisContext`, `reader_preset_synthesis_prompt`; calls `ReaderPresetSynthesisContext`, `reader_preset_synthesis_prompt`
- [[Reference/Modules/learnloop/reader/source_objects|learnloop.reader.source_objects]] — imports `module`; calls `author_source_object`, `propose_mapping`

### Platform and third-party dependencies

- Standard library: `__future__`, `datetime`, `hashlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/reader/reader_capture|learnloop.reader.reader_capture]], [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_codex_output_schema.py](../../../../../../tests/test_codex_output_schema.py) — direct import
  - `test_sdk_reader_preset_regenerates_when_app_server_rejects_hex_escape`
  - `test_sdk_reader_preset_repairs_invalid_unicode_json_once`
- [tests/test_ingest_jobs.py](../../../../../../tests/test_ingest_jobs.py) — direct import
  - `test_kick_reader_drain_leaves_requests_queued_without_provider`
  - `test_kick_reader_drain_runs_model_synthesis_foreground`
- [tests/test_reader_requests.py](../../../../../../tests/test_reader_requests.py) — direct import
  - `test_cancel_request_never_cancels_the_local_capture`
  - `test_different_selections_in_one_block_do_not_share_a_request`
  - `test_drain_lease_is_fenced_and_reruns_are_noops`
  - `test_drain_produces_reviewable_proposals_not_evidence`
  - `test_enqueue_is_idempotent_on_contract_and_versions_change_identity`
  - `test_model_synthesis_focuses_edited_latex_selection`
  - `test_model_synthesis_lands_generated_content_as_proposed_object`
  - `test_model_synthesis_receives_every_selected_span_and_its_context`
  - `test_model_synthesis_rejects_invented_spans`
  - `test_model_synthesis_without_provider_support_fails_visibly`
  - `test_neighborhood_is_bounded_to_smallest_window`
  - `test_neighborhood_merges_bounded_context_around_every_selected_span`
  - `test_token_cap_keeps_capture_and_never_expands_scope`
- [tests/test_structured_transport_parity.py](../../../../../../tests/test_structured_transport_parity.py) — direct import

## Modification guidance

- Change reader requests policy here when reader owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/reader/reader_requests.py](../../../../../../src/learnloop/reader/reader_requests.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
