---
title: "learnloop_sidecar.handlers.reader_cue_discovery"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/reader_cue_discovery.py"
source_paths:
  - "src/learnloop_sidecar/handlers/reader_cue_discovery.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar.handlers"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop_sidecar.handlers.reader_cue_discovery module"
  - "src/learnloop_sidecar/handlers/reader_cue_discovery.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.reader_cue_discovery`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.reader_cue_discovery` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Reader workbench RW3b RPCs: discovered cues (spec_reader_workbench_v1 §6.2-6.4).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/reader_cue_discovery.py](../../../../../../src/learnloop_sidecar/handlers/reader_cue_discovery.py) |
| Source lines | 621 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `remember(ctx: SidecarContext, extraction_id: str, cues: dict[str, Any], *, vault: Any, repository: Any) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_cue_discovery.py), line 142) — The guide plan's merged cues, kept per source so a tap or an impression is resolved by id without rebuilding the plan (RW3a friction note 5).
- `class CueDiscoveryJobs` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_cue_discovery.py), line 247) — Discovery jobs in flight and just finished (in memory), one per source, and the call budget of each source open.
  - `__init__(self) -> None` (line 251; internal)
  - `_source_lock(self, sqlite_path: Any, extraction_id: str) -> threading.Lock` (line 259; internal)
  - `_open(self, source_open_id: str, extraction_id: str, vault: Any) -> _OpenBudget` (line 263; internal)
  - `running(self, extraction_id: str) -> _Job | None` (line 276; public)
  - `start(self, ctx: SidecarContext, extraction_id: str, source_open_id: str) -> _Job` (line 281; public)
  - `get(self, job_id: str) -> _Job | None` (line 360; public)
- `class CueDiscoveryInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_cue_discovery.py), line 391)
- `reader_cue_discovery(ctx: SidecarContext, params: CueDiscoveryInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_cue_discovery.py), line 399) — Look for the open source's missing cue links in the background, within the open's one call budget.
- `class CueDiscoveryJobInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_cue_discovery.py), line 409)
- `reader_cue_discovery_job(ctx: SidecarContext, params: CueDiscoveryJobInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_cue_discovery.py), line 414) — A discovery job's state, at once (never a wait on the request path).
- `class CueImpressionEntry(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_cue_discovery.py), line 452)
- `class CueImpressionsInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_cue_discovery.py), line 463)
- `reader_cue_impressions(ctx: SidecarContext, params: CueImpressionsInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_cue_discovery.py), line 472) — Record impressions (once per visit and cue; the first one stands), each resolved against the plan it was seen on: its arm, density, suppression, seed and propensity as that plan was served (F17).
- `class CueTapInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_cue_discovery.py), line 528)
- `reader_cue_tap(ctx: SidecarContext, params: CueTapInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_cue_discovery.py), line 540) — A tap on a Guide or discovered cue while discovery is on.

### Module constants

- `LOG` ([src/learnloop_sidecar/handlers/reader_cue_discovery.py](../../../../../../src/learnloop_sidecar/handlers/reader_cue_discovery.py), line 69)
- `CUE_DISCOVERY_RPCS` ([src/learnloop_sidecar/handlers/reader_cue_discovery.py](../../../../../../src/learnloop_sidecar/handlers/reader_cue_discovery.py), line 72)
- `MAX_KEPT_JOBS` ([src/learnloop_sidecar/handlers/reader_cue_discovery.py](../../../../../../src/learnloop_sidecar/handlers/reader_cue_discovery.py), line 78)
- `MAX_KEPT_PLANS` ([src/learnloop_sidecar/handlers/reader_cue_discovery.py](../../../../../../src/learnloop_sidecar/handlers/reader_cue_discovery.py), line 80)
- `PLAN_TTL_SECS` ([src/learnloop_sidecar/handlers/reader_cue_discovery.py](../../../../../../src/learnloop_sidecar/handlers/reader_cue_discovery.py), line 82)
- `MAX_KEPT_OPENS` ([src/learnloop_sidecar/handlers/reader_cue_discovery.py](../../../../../../src/learnloop_sidecar/handlers/reader_cue_discovery.py), line 84)
- `CLIENT_REASONS` ([src/learnloop_sidecar/handlers/reader_cue_discovery.py](../../../../../../src/learnloop_sidecar/handlers/reader_cue_discovery.py), line 86)
- `MAX_NOT_RELEVANT_CHARS` ([src/learnloop_sidecar/handlers/reader_cue_discovery.py](../../../../../../src/learnloop_sidecar/handlers/reader_cue_discovery.py), line 87)

### Explicit exports

`__all__` declares:

- `CUE_DISCOVERY_RPCS`
- `remember`

## Internal implementation anchors

- `_require(ctx: SidecarContext)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_cue_discovery.py), line 90)
- `_resolve(repository: Any, extraction_id: str) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_cue_discovery.py), line 98)
- `_cache(ctx: SidecarContext) -> dict[str, tuple[Any, dict[str, Any]]]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_cue_discovery.py), line 109)
- `class _KeptPlan` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_cue_discovery.py), line 118) — One cue plan as it was served: what its impressions are resolved by.
- `_plans(ctx: SidecarContext) -> 'OrderedDict[str, _KeptPlan]'` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_cue_discovery.py), line 130)
- `_clock() -> float` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_cue_discovery.py), line 138)
- `_kept_plan(ctx: SidecarContext, plan_id: str, *, extraction_id: str, repository: Any) -> _KeptPlan` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_cue_discovery.py), line 170) — The plan an impression was seen on, or a refusal: unknown (never served, dropped as one of the oldest, or another vault's), expired, or another source's.
- `_cues_now(ctx: SidecarContext, vault: Any, repository: Any, extraction_id: str, *, fresh: bool=False) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_cue_discovery.py), line 185)
- `_index(cues: dict[str, Any]) -> dict[str, tuple[str, dict[str, Any]]]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_cue_discovery.py), line 198) — Every cue of a payload by id: shown, held out or cut by the density budget.
- `class _Job` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_cue_discovery.py), line 217)
- `class _OpenBudget` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_cue_discovery.py), line 233) — The one judge call budget of one source open (Codex verify F16).
- `_jobs(ctx: SidecarContext) -> CueDiscoveryJobs` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_cue_discovery.py), line 365)
- `_job_payload(job: _Job) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_cue_discovery.py), line 373)
- `_text_hash(text: str | None) -> str | None` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_cue_discovery.py), line 430)
- `_impression_row(cue: dict[str, Any], *, extraction_id: str, visit_id: str, density: str, shown: bool, reason: str | None, now: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_cue_discovery.py), line 435)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `remember`; statically calls `remember`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `record_model_calls`; calls `record_model_calls`
- [[Reference/Modules/learnloop/ai/plan_fallback|learnloop.ai.plan_fallback]] — imports `module`; calls `note_unit`, `relay_job_offer`, `unit`, `unit_origin`, `unit_stamp`, `unit_token`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] — imports `resolve_extraction_id`; calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/reader_cue_links|learnloop.db.stores.reader_cue_links]] — imports `module`; calls `impression_for`, `insert_impression`, `record_response`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/reader/reader_cues|learnloop.reader.reader_cues]] — imports `module`; calls `cue_density`, `find_cue`, `record_cue_tap`
- [[Reference/Modules/learnloop/reader/reader_guidance|learnloop.reader.reader_guidance]] — imports `module`; calls `build_guide_plan`
- [[Reference/Modules/learnloop/source_retrieval/passage_cues|learnloop.source_retrieval.passage_cues]] — imports `module`; calls `discover`, `discovery_budget`, `discovery_enabled`, `find_discovered`, `merged_cues`, `protection`, `try_first_enabled`
- [[Reference/Modules/learnloop_sidecar/background_jobs|learnloop_sidecar.background_jobs]] — imports `background_jobs`; calls `background_jobs`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `check_me_proposal`; calls `check_me_proposal`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `copy`, `dataclasses`, `hashlib`, `logging`, `threading`, `time`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]], [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_mobile_allowlist.py](../../../../../../tests/test_mobile_allowlist.py) — direct import
  - `test_reader_rw3b_rpcs_are_the_modules_own`
- [tests/test_reader_rw3b_fix_round4.py](../../../../../../tests/test_reader_rw3b_fix_round4.py) — direct import
  - `test_a_source_open_id_names_one_source`
  - `test_an_expired_or_dropped_plan_is_refused_and_nothing_is_stored`
- [tests/test_reader_rw3b_review_fixes.py](../../../../../../tests/test_reader_rw3b_review_fixes.py) — direct import
  - `test_the_kept_cues_are_dropped_on_a_reload_and_kept_within_one`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/reader_cue_discovery.py](../../../../../../src/learnloop_sidecar/handlers/reader_cue_discovery.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
