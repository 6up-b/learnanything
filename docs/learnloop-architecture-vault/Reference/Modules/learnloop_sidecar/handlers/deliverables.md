---
title: "learnloop_sidecar.handlers.deliverables"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/deliverables.py"
source_paths:
  - "src/learnloop_sidecar/handlers/deliverables.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar.handlers"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop_sidecar.handlers.deliverables module"
  - "src/learnloop_sidecar/handlers/deliverables.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.deliverables`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.deliverables` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Deliverable curriculum C0b RPCs: the deliverable's scope, its path across books, the Guide's slice, the learner's overrides and "Am I ready?" (spec_deliverable_curriculum_v1 §5, §7.1-§7.5, §8.5, §12).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/deliverables.py](../../../../../../src/learnloop_sidecar/handlers/deliverables.py) |
| Source lines | 788 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `refresh_for_plan(ctx: SidecarContext, vault: Any, repository: Any) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 344) — Curriculum C1 (spec §7.6): start the daily quiet re-judgment of the nearest deliverable's stale path before the plan is built (every plan RPC calls this first; it starts at most once a local day per vault in this sidecar).
- `curriculum_deliverables(ctx: SidecarContext, _params: ParamsModel) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 539) — The learner's deliverables and their scope lines (no model call).
- `class CreateDeliverableInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 547)
- `curriculum_create_deliverable(ctx: SidecarContext, params: CreateDeliverableInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 562) — A new deliverable from the learner's sentence, resolved at once (pressed).
- `class SetScopeInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 576)
- `curriculum_set_scope(ctx: SidecarContext, params: SetScopeInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 588) — One more scope input in the learner's words, then the resolution and the goal's scope.
- `class GoalInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 609)
- `curriculum_scope(ctx: SidecarContext, params: GoalInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 614) — The deliverable's scope lines (no model call).
- `class ScopeDecideInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 624)
- `curriculum_scope_decide(ctx: SidecarContext, params: ScopeDecideInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 633) — *add it* / *no* on a phrase not in the library: an LO is created only on the learner's yes.
- `class SetDepthInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 648)
- `curriculum_set_depth(ctx: SidecarContext, params: SetDepthInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 654) — "How deep for this?" (asked once; the newest stands).
- `class PathInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 673)
- `curriculum_path(ctx: SidecarContext, params: PathInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 681) — The deliverable's path across books (at once; any judgment runs in the background).
- `class GuideSliceInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 688)
- `curriculum_guide_slice(ctx: SidecarContext, params: GuideSliceInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 695) — The Guide's slice of a deliverable's path for this reading (``status: none``: RW7a's card).
- `class PathOverrideInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 718)
- `curriculum_path_override(ctx: SidecarContext, params: PathOverrideInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 728) — A path line's choice: kept across re-judgments; marks nothing as known.
- `curriculum_ready(ctx: SidecarContext, params: GoalInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 743) — The answer to "am I ready?": per topic demonstrated, likely (a prediction) or untested.
- `curriculum_ready_check(ctx: SidecarContext, params: GoalInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 754) — The pressed "Am I ready?": one Check once per topic not shown and not already waiting.
- `class AlsoAboutInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 764)
- `curriculum_also_about(ctx: SidecarContext, params: AlsoAboutInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 771) — *also about…* in the learner's words: resolved to a topic and kept as their correction.

### Module constants

- `LOG` ([src/learnloop_sidecar/handlers/deliverables.py](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 60)
- `DELIVERABLE_RPCS` ([src/learnloop_sidecar/handlers/deliverables.py](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 63)
- `_REGISTRY_LOCK` ([src/learnloop_sidecar/handlers/deliverables.py](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 129)

### Explicit exports

`__all__` declares:

- `DELIVERABLE_RPCS`

## Internal implementation anchors

- `_require(ctx: SidecarContext) -> tuple[Any, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 79)
- `_error(exc: Exception) -> SidecarError` ([source](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 91)
- `_reload(ctx: SidecarContext) -> tuple[Any, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 96)
- `class _Work` ([source](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 104) — One vault's background curriculum work, in memory: coverage per goal, path judgments per (goal, depth, state key), and the OpenRouter offer each failure made (T1).
- `_work(ctx: SidecarContext) -> _Work` ([source](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 132)
- `_spawn(ctx: SidecarContext, name: str, run: Any) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 143)
- `_unit(vault: Any, label: str) -> tuple[Any, Any, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 151)
- `_cover(ctx: SidecarContext, vault: Any, repository: Any, goal_id: str) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 160) — Judge the coverage the deliverable's LOs owe (never judged yet), in the background.
- `_claim_path(work: _Work, goal_id: str, depth: str, state_key: str) -> Iterator[bool]` ([source](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 224) — C1's daily refresh entering the coalescing set (``_Work.judging``) for one deliverable's path state: yields False while a judgment for it is running (the Guide's: nothing is sent), else marks it running for the Guide to see (its open then starts no second judgment) and clears th…
- `_judge_path(ctx: SidecarContext, vault: Any, repository: Any, goal_id: str, depth: str, state_key: str) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 246)
- `_token(kind: str) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 311) — A claim's owner: unique per job (fix round 4), so a job transfers and releases only its own claims, never another job's of the same kind.
- `_release(work: _Work, key: tuple[str, str, str], token: str) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 318) — Drop ``key``'s claim if ``token`` still holds it.
- `_move_claim(work: _Work, held: tuple[str, str, str], wanted: tuple[str, str, str], token: str) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 326) — The Guide's job moving its claim from the key it was started for (``held``) to the key of the inputs it prepared (``wanted``), immediately before its call: False when another job (the daily refresh, or another Guide job) is running ``wanted``, so this one sends nothing.
- `_relay(work: _Work, key: Any) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 422)
- `_readmit_coverage(ctx: SidecarContext, vault: Any, repository: Any, goal_id: str, current: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 431) — A coverage admission refusal (capped, unpriced, unrouted, models off) holds only while its condition does (RW7a's rule; Codex review F6): asked again on each read, before any call.
- `_path_state(ctx: SidecarContext, vault: Any, repository: Any, goal_id: str, *, judge: bool, retry: bool) -> tuple[dict[str, Any] | None, bool, dict[str, Any] | None]` ([source](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 456) — ``(judging, covering, coverage failure)`` for the deliverable now, starting what it owes: the coverage of its LOs first, then (once no coverage is running) the path judgment.
- `_likely(vault: Any, repository: Any) -> Any` ([source](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 519) — AD's labelled prediction per LO for "Am I ready?" (None while AD does not predict).
- `_after_scope(ctx: SidecarContext, goal_id: str, result: DL.ScopeResult) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 553)
- `_path(ctx: SidecarContext, vault: Any, repository: Any, goal_id: str, *, judge: bool, retry: bool) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/deliverables.py), line 665)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]] — imports `refresh_for_plan`; statically calls `refresh_for_plan`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/readiness|learnloop.adaptive_difficulty.readiness]] — imports `LIKELY`, `lo_readiness`; calls `lo_readiness`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `record_model_calls`; calls `record_model_calls`
- [[Reference/Modules/learnloop/ai/plan_fallback|learnloop.ai.plan_fallback]] — imports `module`; calls `note_unit`, `relay_hint`, `unit`, `unit_origin`, `unit_stamp`, `unit_token`
- [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] — imports `resolve_extraction_id`; calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `deliverable_plan_active`, `local_date`; calls `deliverable_plan_active`, `local_date`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/deliverables|learnloop.db.stores.deliverables]] — imports `module`; calls `judged`
- [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]] — imports `module`; calls `reader_enabled`
- [[Reference/Modules/learnloop/source_retrieval/deliverable_path|learnloop.source_retrieval.deliverable_path]] — imports `module`; calls `coverage_key`, `coverage_owed`, `guide_goal`, `guide_slice`, `judge`, `override`, `path_inputs`, `path_view`, `plan_refresh_reason`, `readiness`, `ready_checks`, `refresh_for_plan`
- [[Reference/Modules/learnloop/source_retrieval/deliverables|learnloop.source_retrieval.deliverables]] — imports `module`; calls `add_input`, `admission_problem`, `also_about`, `create_deliverable`, `decide_unmatched`, `deliverable_goals`, `depth_of`, `enabled`, `recover_publications`, `resolve`, `scope_view`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `module`; calls `Library`, `admission_problem`, `judge`
- [[Reference/Modules/learnloop_sidecar/background_jobs|learnloop_sidecar.background_jobs]] — imports `background_jobs`; calls `background_jobs`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `_require_source_reader`, `_source_id_for_extraction`; calls `_require_source_reader`, `_source_id_for_extraction`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `logging`, `pathlib`, `threading`, `typing`, `uuid`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]], [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_curriculum_c1_codex_review_fixes.py](../../../../../../tests/test_curriculum_c1_codex_review_fixes.py) — direct import
  - `test_f3_without_a_new_judgment_the_stale_plan_stays_and_reads_no_path`
- [tests/test_curriculum_c1_fix_round2.py](../../../../../../tests/test_curriculum_c1_fix_round2.py) — direct import
  - `test_m5_a_plan_read_while_the_guides_judgment_runs_sends_no_second_call`
- [tests/test_curriculum_c1_fix_round3.py](../../../../../../tests/test_curriculum_c1_fix_round3.py) — direct import
  - `test_m3_k0_observed_k1_prepared_and_a_concurrent_guide_open_for_k1_send_one_call`
  - `test_m3_the_guides_worker_moves_its_claim_to_the_inputs_it_prepared`
- [tests/test_curriculum_c1_fix_round4.py](../../../../../../tests/test_curriculum_c1_fix_round4.py) — direct import
  - `test_m4_a_finishing_guide_job_keeps_another_jobs_claim_and_the_refresh_sends_nothing`
  - `test_m4_claims_carry_a_token_per_job`
- [tests/test_curriculum_c1_fix_round5.py](../../../../../../tests/test_curriculum_c1_fix_round5.py) — direct import
  - `test_m1_a_metered_route_is_never_asked_by_the_automatic_refresh`
  - `test_m2_a_refresh_queued_before_a_switch_went_off_sends_and_writes_nothing`
- [tests/test_curriculum_c1_plan_follows_path.py](../../../../../../tests/test_curriculum_c1_plan_follows_path.py) — direct import
  - `test_the_daily_refresh_rejudges_quietly_before_the_plan_is_built_once_a_day`
  - `test_with_the_plan_down_the_plan_falls_back_to_rw7b_says_stale_and_nothing_asks`
- [tests/test_deliverable_codex_review.py](../../../../../../tests/test_deliverable_codex_review.py) — direct import
  - `test_f1_the_path_worker_reads_the_live_vault_and_checks_against_it`
  - `test_f6_a_lifted_coverage_admission_refusal_starts_the_coverage_again`
- [tests/test_deliverable_rpcs.py](../../../../../../tests/test_deliverable_rpcs.py) — direct import
  - `test_the_rpcs_are_registered_and_desktop_only`
- [tests/test_mobile_allowlist.py](../../../../../../tests/test_mobile_allowlist.py) — direct import
  - `test_the_pinned_c0b_rpcs_are_all_of_them`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/deliverables.py](../../../../../../src/learnloop_sidecar/handlers/deliverables.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
