---
title: "learnloop.figures.build"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/figures/build.py"
source_paths:
  - "src/learnloop/figures/build.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.figures"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.figures.build module"
  - "src/learnloop/figures/build.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-figures"
---

# `learnloop.figures.build`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.figures.build` exists within [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] to own the behavior summarized by its module contract: Building a figure: reuse it, or ask the author and store what passes (spec_reader_workbench_v1 §8; UX §4.7).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/figures/build.py](../../../../../../src/learnloop/figures/build.py) |
| Source lines | 1416 |
| Owning package | [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `request_hash(request: FigureRequest, context: SourceContext, image_digest: str | None, *, advanced: bool=False, grounding: Grounding | None=None, sketch: bool=False, tiers: Sequence[str] | None=None, rich_runtime: str | None=None, learner_state: Mapping[str, Any] | None=None) -> str` ([source](../../../../../../src/learnloop/figures/build.py), line 155) — The reuse key: the spec and prompt versions (RW5b's panels have their own prompt version, so RW5a's hashes are unchanged while they are off) and everything the author is sent (never the origin: :data:`REUSE_ORIGIN`).
- `class BuildOutcome` ([source](../../../../../../src/learnloop/figures/build.py), line 260)
- `build_figure(vault: Any, repository: Repository, request: FigureRequest, *, author_client: Any | None=None, clock: Clock | None=None, live_vault: Callable[[], Any] | None=None, find: FindSources | None=None, spawn_rich: SpawnRich | None=None, cancelled: Callable[[], bool] | None=None) -> BuildOutcome` ([source](../../../../../../src/learnloop/figures/build.py), line 328) — Build one figure (module docstring).
- `retry_rich_job(vault: Any, repository: Repository, job_id: str) -> str` ([source](../../../../../../src/learnloop/figures/build.py), line 572) — Codex review F9: the error code of a rich job that ended with no row and may be requeued (failed, not waiting for the plan, never cancelled), or :class:`FigureRefused`.
- `ensure_rich_job(repository: Repository, spawn: SpawnRich, payload: dict[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/figures/build.py), line 999) — Start a quick figure's rich job unless it already has one (in any state: a cancelled one stays cancelled) or a stored fuller version (Codex review F8).
- `resume_rich_intents(vault: Any, repository: Repository, extraction_id: str, spawn: SpawnRich | None) -> int` ([source](../../../../../../src/learnloop/figures/build.py), line 1018) — Codex review F8: start the rich job of every shown quick figure of this source whose intent committed but whose job was never enqueued (the sidecar stopped between the two, or the enqueue failed).
- `revision_request(repository: Repository, base: Mapping[str, Any], note: str) -> FigureRequest` ([source](../../../../../../src/learnloop/figures/build.py), line 1307) — "Not right?" on a stored figure: the same input with the note.
- `rebuild_request(vault: Any, repository: Repository, base: Mapping[str, Any]) -> FigureRequest` ([source](../../../../../../src/learnloop/figures/build.py), line 1329) — *Rebuild* of a figure whose stated claim differs (§6.6, Codex review F3): a new version through the revision path, never a reuse of the rejected row.
- `build_prefetch_figure(vault: Any, repository: Repository, request: FigureRequest, *, author_client: Any | None=None, clock: Clock | None=None, live_vault: Callable[[], Any] | None=None, find: FindSources | None=None, spawn_rich: SpawnRich | None=None) -> BuildOutcome` ([source](../../../../../../src/learnloop/figures/build.py), line 1359) — RW5d P5: one background build for the prefetch service (spec §10b), under ``quiet()``: no offer, no grant (plan down: it waits).
- `rich_revision_retry(vault: Any, repository: Repository, job_id: str) -> FigureRequest | None` ([source](../../../../../../src/learnloop/figures/build.py), line 1379) — Codex re-review F14: "try again" on a correction of an animation whose job stored a failure (the line :func:`rich_pending` lists): the same correction (the figure it corrects, the learner's note), built afresh.

### Module constants

- `SHOW_ME_VERSION` ([src/learnloop/figures/build.py](../../../../../../src/learnloop/figures/build.py), line 91)
- `REQUEST_PREFIX` ([src/learnloop/figures/build.py](../../../../../../src/learnloop/figures/build.py), line 92)
- `FIGURE_PREFIX` ([src/learnloop/figures/build.py](../../../../../../src/learnloop/figures/build.py), line 93)
- `TIER_LEDGER_TASK` ([src/learnloop/figures/build.py](../../../../../../src/learnloop/figures/build.py), line 95)
- `LEARNER_INPUTS_RECORDED` ([src/learnloop/figures/build.py](../../../../../../src/learnloop/figures/build.py), line 128)
- `REUSE_ORIGIN` ([src/learnloop/figures/build.py](../../../../../../src/learnloop/figures/build.py), line 152)
- `PREFETCH_AUTHOR_NOT_PLAN` ([src/learnloop/figures/build.py](../../../../../../src/learnloop/figures/build.py), line 376)
- `_BUILD_CANCELLED` ([src/learnloop/figures/build.py](../../../../../../src/learnloop/figures/build.py), line 394)
- `_BUILDS_GUARD` ([src/learnloop/figures/build.py](../../../../../../src/learnloop/figures/build.py), line 599)
- `_BUILDS` ([src/learnloop/figures/build.py](../../../../../../src/learnloop/figures/build.py), line 600)
- `STORAGE_BUSY` ([src/learnloop/figures/build.py](../../../../../../src/learnloop/figures/build.py), line 653)
- `_LOG` ([src/learnloop/figures/build.py](../../../../../../src/learnloop/figures/build.py), line 995)
- `_RICH_SPAWN_GUARD` ([src/learnloop/figures/build.py](../../../../../../src/learnloop/figures/build.py), line 996)

### Explicit exports

`__all__` declares:

- `BuildOutcome`
- `build_figure`
- `rebuild_request`
- `revision_request`
- `ensure_rich_job`
- `resume_rich_intents`
- `retry_rich_job`

## Internal implementation anchors

- `_unrecorded_occupant(vault: Any, connection: Any, input_hash: str) -> bool` ([source](../../../../../../src/learnloop/figures/build.py), line 102) — Codex re-review F5: whether this input's reusable figure (its quick figure, or a rich figure built with no quick one) is a marked row that keeps no record of what its author's learner state was read from.
- `_recorded_input_key(input_hash: str) -> str` ([source](../../../../../../src/learnloop/figures/build.py), line 114) — Codex re-review F5: the key a fresh build of an input takes when that input's figure is a marked row with no record.
- `_with_learner_inputs(report: Mapping[str, Any], request: 'FigureRequest') -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/build.py), line 131) — A quick figure's report with what its author's learner state was read from (follow-ups Nov 2: the record rich rows keep since learner data-relax 2, ``protection.LEARNER_STATE_INPUTS_KEY``; never shown or sent to a model), so the figure is rechecked whenever it goes out.
- `_reusable(vault: Any, repository: Repository, connection: Any, input_hash: str, other_hash: str | Sequence[str]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/figures/build.py), line 227) — The figure a build reuses: this input's under the current prompt version, else (Codex review F2) a SHOWN one of the same input under the other prompt version when it can be drawn now.
- `_author_context(request: FigureRequest, context: SourceContext, image_digest: str | None, previous: Mapping[str, Any] | None, problems: Sequence[str], *, request_id: str, grounding: Grounding | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/build.py), line 275)
- `_prefetch_build_hold(author_client: Any | None) -> Callable[[Any], str | None]` ([source](../../../../../../src/learnloop/figures/build.py), line 380)
- `_cancel_hold(cancelled: Callable[[], bool], other: Callable[[Any], str | None] | None) -> Callable[[Any], str | None]` ([source](../../../../../../src/learnloop/figures/build.py), line 397)
- `_build(vault: Any, repository: Repository, request: FigureRequest, *, gate: FiguresGate, author_client: Any | None, clock: Clock | None, find: FindSources | None, spawn_rich: SpawnRich | None=None) -> BuildOutcome` ([source](../../../../../../src/learnloop/figures/build.py), line 407)
- `_learner_state(vault: Any, repository: Repository, request: FigureRequest, context: SourceContext, grounding: Grounding) -> Any` ([source](../../../../../../src/learnloop/figures/build.py), line 535) — Learner data-relax 2: what the author is told about the learner on the passage's topics and what it was read from (:func:`.learner_state.read_learner_state`), or None (switched off or no topics; an empty or unreadable state: the predecessor's build).
- `_rich_pending(vault: Any, repository: Repository, request: FigureRequest, input_hash: str) -> BuildOutcome | None` ([source](../../../../../../src/learnloop/figures/build.py), line 556) — A rich-only build of this input still running or waiting (its job is pending or waiting for the plan): the request takes its pending line.
- `_withheld_payload(vault: Any, repository: Repository, payload: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/figures/build.py), line 593)
- `_building(repository: Repository, input_hash: str) -> Iterator[None]` ([source](../../../../../../src/learnloop/figures/build.py), line 604) — Hold this process's one lock for (vault, input) while a build runs.
- `_request_row(request: FigureRequest, grounding: Grounding, *, figure_id: str | None, clock: Clock | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/build.py), line 625) — The ``figure_requests`` row of one request (RW5d, spec §13.1): what was asked, as normalized, and what the server derived.
- `_reused(vault: Any, repository: Repository, row: Mapping[str, Any], *, request: FigureRequest | None=None, grounding: Grounding | None=None, clock: Clock | None=None, gate: FiguresGate | None=None) -> BuildOutcome` ([source](../../../../../../src/learnloop/figures/build.py), line 656)
- `_step_three(vault: Any, repository: Repository, compiled: S.CompiledFigure, context: SourceContext, request: FigureRequest, grounding: Grounding | None, gate: FiguresGate) -> SC.Check | None` ([source](../../../../../../src/learnloop/figures/build.py), line 682) — RW5c's check of a spec that passed steps 1-2, or None with the switch off.
- `_author_and_store(vault: Any, repository: Repository, request: FigureRequest, context: SourceContext, author: R.FigureRoute, *, request_id: str, **kwargs: Any) -> BuildOutcome` ([source](../../../../../../src/learnloop/figures/build.py), line 704) — :func:`_author_attempts_and_store`, then one ``figure_author`` record per attempt (ADR-017), written once the build has ended, refused or failed, so a record never changes the build.
- `_author_attempts_and_store(vault: Any, repository: Repository, request: FigureRequest, context: SourceContext, author: R.FigureRoute, *, previous: Mapping[str, Any] | None, versions: int, image: tuple[str, bytes] | None, asset_id: str | None, digest: str | None, input_hash: str, request_id: str, clock: Clock | None, gate: FiguresGate, attempts: FR.AuthorAttempts, advanced: bool=False, grounding: Grounding | None=None, sketch: bool=False, tiers: Sequence[str] | None=None, spawn_rich: SpawnRich | None=None, generation: int=0) -> BuildOutcome` ([source](../../../../../../src/learnloop/figures/build.py), line 722) — At most two author calls, the second told the first's problems; then the figure is stored, shown or failed.
- `_store_quick(vault: Any, repository: Repository, request: FigureRequest, context: SourceContext, author: R.FigureRoute, *, compiled: S.CompiledFigure | None, unsupported: tuple[str, str] | None, problems: list[str], report: V.Report, source_check: SC.Check | None, verdict: tuple[str, str] | None, sketch: bool, v3: bool, versions: int, asset_id: str | None, input_hash: str, prompt_version: str, figure_id: str, asked: dict[str, Any], clock: Clock | None, gate: FiguresGate, grounding: Grounding, rich_spawn: _RichSpawn | None) -> BuildOutcome` ([source](../../../../../../src/learnloop/figures/build.py), line 910) — The grammar figure the attempts came to (shown, failed or unsupported), stored with its request, its verification and tier judgments and its source check in one transaction; a rich answer's quick figure carries the rich job's intent, and the job starts once it is stored.
- `class _RichSpawn` ([source](../../../../../../src/learnloop/figures/build.py), line 1058) — RW5d P2b (spec §8.6): starting the rich job of a rich status, after the quick figure is stored (:meth:`after_quick`) or with none (:meth:`only`).
- `_rich_revision(vault: Any, repository: Repository, request: FigureRequest, context: SourceContext, grounding: Grounding, *, previous: Mapping[str, Any], input_hash: str, digest: str | None, asset_id: str | None, generation: int, request_id: str, spawn_rich: SpawnRich | None, gate: FiguresGate, clock: Clock | None) -> BuildOutcome` ([source](../../../../../../src/learnloop/figures/build.py), line 1166) — RW5d P2b (spec §8.5, Codex review F11): "not right?" on a Manim figure.
- `_inherited_extra(repository: Repository, previous: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/build.py), line 1210) — Codex review F4: a rich revision's job payload carries what the learner states its earlier versions' authors were sent were read from (:func:`inherited_learner_inputs`); absent when none was sent, so every other revision's payload is exactly as before.
- `_append_tier(connection: Any, figure_id: str, input_hash: str, verdict: tuple[str, str], author: R.FigureRoute, prompt_version: str, created_at: str, *, left_kind: str='interactive_figure') -> None` ([source](../../../../../../src/learnloop/figures/build.py), line 1220) — The tier judgment's receipt (spec §8.4): the author's status, its reason (``why_not_spec`` or the unsupported reason), the model and prompt.
- `_store_sketch(vault: Any, repository: Repository, request: FigureRequest, context: SourceContext, author: R.FigureRoute, *, sketched: K.CompiledSketch | None, report: Any, problems: Sequence[str], versions: int, asset_id: str | None, input_hash: str, prompt_version: str, figure_id: str, asked: dict[str, Any], clock: Clock | None, gate: FiguresGate, grounding: Grounding, verdict: tuple[str, str] | None, rich_spawn: '_RichSpawn | None'=None) -> BuildOutcome` ([source](../../../../../../src/learnloop/figures/build.py), line 1232) — Store a sketch build (RW5d P2): shown (``illustrative``, its check lines) when verification passed, else ``failed`` with the reason (never shown).
- `_sketch_assumptions(compiled: K.CompiledSketch, span_texts: Mapping[str, str]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/figures/build.py), line 1296) — As :func:`.verify.verified_assumptions`: an unverified quote is dropped, the text stays (AI-written).
- `_chain_length(repository: Repository, figure_id: str) -> int` ([source](../../../../../../src/learnloop/figures/build.py), line 1344)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] — imports `module`; statically calls `build_prefetch_figure`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `module`; statically calls `build_figure`, `rebuild_request`, `resume_rich_intents`, `retry_rich_job`, `revision_request`, `rich_revision_retry`
- [[Reference/Modules/learnloop_sidecar/handlers/lesson|learnloop_sidecar.handlers.lesson]] — imports `module`; statically calls `build_figure`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`, `gate_model_requests`; calls `content_key`, `gate_model_requests`
- [[Reference/Modules/learnloop/ai/plan_fallback|learnloop.ai.plan_fallback]] — imports `module`; calls `quiet`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendLimitExceeded`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/figures|learnloop.db.stores.figures]] — imports `module`; calls `builds_for_input`, `figure`, `figures_for_extraction`, `fuller_rows`, `has_tables`, `insert_figure`, `insert_request`, `latest_for_input`, `reusable`, `set_request_figure`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/figure_admission|learnloop.figure_admission]] — imports `FiguresChanged`, `FiguresGate`, `figures_enabled`, `rich_tiers_enabled`; calls `FiguresGate`, `figures_enabled`, `rich_tiers_enabled`
- [[Reference/Modules/learnloop/figures/author_answer|learnloop.figures.author_answer]] — imports `module`; calls `read_answer`, `status_of`
- [[Reference/Modules/learnloop/figures/grounding|learnloop.figures.grounding]] — imports `FindSources`, `Grounding`, `SourceContext`, `crop_image`, `ground`, `passages_context`, `source_context`; calls `Grounding`, `crop_image`, `ground`, `passages_context`, `source_context`
- [[Reference/Modules/learnloop/figures/learner_state|learnloop.figures.learner_state]] — imports `module`, `state_hash`; calls `anchored_learning_objects`, `enabled`, `read_learner_state`, `state_hash`
- [[Reference/Modules/learnloop/figures/listing|learnloop.figures.listing]] — imports `_failed_correction`, `_rich_line`; calls `_failed_correction`, `_rich_line`
- [[Reference/Modules/learnloop/figures/power|learnloop.figures.power]] — imports `background_hold`; calls `background_hold`
- [[Reference/Modules/learnloop/figures/protection|learnloop.figures.protection]] — imports `INHERITED_LEARNER_INPUTS_KEY`, `LEARNER_STATE_INPUTS_KEY`, `RICH_INTENT_KEY`, `_learner_inputs_unrecorded`, `_withheld`, `inherited_learner_inputs`, `learner_state_withheld`; calls `_learner_inputs_unrecorded`, `_withheld`, `inherited_learner_inputs`, `learner_state_withheld`
- [[Reference/Modules/learnloop/figures/records|learnloop.figures.records]] — imports `module`; calls `AuthorAttempts`, `code`
- [[Reference/Modules/learnloop/figures/request|learnloop.figures.request]] — imports `FigureRefused`, `FigureRequest`, `LESSON_TIERS`, `_PREFETCH_BUILD`, `anchored`, `attempt_hosted`, `check_request`, `key_for`, `lesson_hosted`, `show_me_input`; calls `FigureRefused`, `FigureRequest`, `anchored`, `attempt_hosted`, `check_request`, `key_for`, `lesson_hosted`, `show_me_input`
- [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]] — imports `module`; calls `RichBrief`, `job_state`, `rich_job_for`, `rich_job_id_for_quick`, `rich_jobs`, `rich_on_menu`, `runtime_digest`, `tiers_allowed`
- [[Reference/Modules/learnloop/figures/routes|learnloop.figures.routes]] — imports `module`; calls `FigureRoute`, `author_prompt`, `author_prompt_version`, `daily_envelope`, `output_model`, `rich_menu`
- [[Reference/Modules/learnloop/figures/sketch|learnloop.figures.sketch]] — imports `module`, `sketch_ready`; calls `sketch_ready`
- [[Reference/Modules/learnloop/figures/sketch_engine|learnloop.figures.sketch_engine]] — imports `ENGINE_SHA256`, `ENGINE_VERSION`
- [[Reference/Modules/learnloop/figures/sketch_verify|learnloop.figures.sketch_verify]] — imports `module`; calls `verify_sketch`
- [[Reference/Modules/learnloop/figures/source_check|learnloop.figures.source_check]] — imports `module`; calls `check_figure`, `current_row`, `enabled`, `failed_check`, `grammar_row`, `record`, `stored_problems`
- [[Reference/Modules/learnloop/figures/spec|learnloop.figures.spec]] — imports `ALL_SPEC_VERSIONS`, `RICH_SPEC_VERSIONS`, `SPEC_VERSIONS`, `module`
- [[Reference/Modules/learnloop/figures/verify|learnloop.figures.verify]] — imports `module`; calls `Report`, `check_claims`, `quote_in`, `verified_assumptions`, `verify_numerics`
- [[Reference/Modules/learnloop/figures/view|learnloop.figures.view]] — imports `LEDGER_TASK`, `RECONSTRUCTION_REASON`, `_figure_request`, `drawable_now`, `figure_view`, `rich_row`, `sketch_row`, `source_rejected`; calls `_figure_request`, `drawable_now`, `figure_view`, `rich_row`, `sketch_row`, `source_rejected`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `plan_route`; calls `plan_route`
- [[Reference/Modules/learnloop/source_retrieval/policy|learnloop.source_retrieval.policy]] — imports `CallerContext`, `derive_policy`; calls `CallerContext`, `derive_policy`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `hashlib`, `json`, `logging`, `sqlite3`, `threading`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]], [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]], [[Reference/Modules/learnloop_sidecar/handlers/lesson|learnloop_sidecar.handlers.lesson]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/figure_rich_job_helpers.py](../../../../../../tests/figure_rich_job_helpers.py) — direct import
- [tests/figure_rich_rereview_fixes_helpers.py](../../../../../../tests/figure_rich_rereview_fixes_helpers.py) — direct import
- [tests/identity_pins_helpers.py](../../../../../../tests/identity_pins_helpers.py) — direct import
- [tests/reader_rw5d_p4b_teacher_visuals_helpers.py](../../../../../../tests/reader_rw5d_p4b_teacher_visuals_helpers.py) — direct import
- [tests/test_figure_decision_records.py](../../../../../../tests/test_figure_decision_records.py) — direct import
  - `test_a_refused_build_leaves_a_refused_record`
  - `test_a_refused_or_failed_prebuild_is_a_stop_record`
  - `test_a_rich_only_build_names_its_job_and_an_interrupted_build_its_error`
- [tests/test_figure_label_wording.py](../../../../../../tests/test_figure_label_wording.py) — direct import
  - `test_f3_a_stored_label_like_sketch_is_presented_without_that_text`
  - `test_f3_a_stored_label_like_spec_is_presented_without_that_text_listed_and_reused`
  - `test_the_vocabulary_comes_from_the_code_owned_labels`
- [tests/test_figure_rich_contract.py](../../../../../../tests/test_figure_rich_contract.py) — direct import
  - `test_a_build_with_manim_on_the_menu_sends_v3_and_records_the_menu`
  - `test_the_reuse_key_names_the_menu_and_the_rich_versions`
  - `test_v3_a_status_off_the_menu_or_with_no_reason_gets_the_second_attempt`
  - `test_with_no_rich_tier_on_the_menu_the_contract_is_v2s_byte_for_byte`
  - `test_without_a_way_to_start_the_job_no_rich_tier_is_offered`
- [tests/test_figure_rich_failed_correction_durable.py](../../../../../../tests/test_figure_rich_failed_correction_durable.py) — direct import
  - `test_r1_a_failed_correction_outside_the_job_window_still_says_so`
- [tests/test_figure_rich_rereview_fixes.py](../../../../../../tests/test_figure_rich_rereview_fixes.py) — direct import
  - `test_a_different_kind_hashes_apart_from_the_ordinary_correction`
  - `test_a_failed_animation_correction_keeps_the_earlier_version_and_says_so`
  - `test_a_later_correction_replaces_the_failed_line`
- [tests/test_figure_rich_review_fixes.py](../../../../../../tests/test_figure_rich_review_fixes.py) — direct import
  - `test_a_cancelled_rich_only_build_leaves_no_line_and_cannot_be_retried`
  - `test_a_failed_enqueue_is_not_swallowed_and_is_recovered`
  - `test_a_normal_build_or_a_cancelled_one_is_never_restarted_by_recovery`
  - `test_a_revision_needs_the_manim_tier_on_this_computer`
  - `test_a_stop_between_the_quick_figure_and_the_enqueue_is_recovered_once`
  - `test_an_interrupted_rich_only_build_stays_as_a_failed_line_and_can_be_tried_again`
  - `test_not_right_on_a_fuller_version_stays_that_quick_figures_fuller_version`
  - `test_not_right_on_an_animation_goes_to_the_rich_author_with_the_note_and_program`
  - `test_try_a_different_kind_of_figure_reruns_the_tier_choice_with_the_note`
- [tests/test_figure_rich_rpc.py](../../../../../../tests/test_figure_rich_rpc.py) — direct import
  - `test_reading_a_source_starts_a_rich_job_whose_enqueue_never_happened`
- [tests/test_figure_wait_estimate.py](../../../../../../tests/test_figure_wait_estimate.py) — direct import
- [tests/test_figures_codex_review.py](../../../../../../tests/test_figures_codex_review.py) — direct import
  - `test_f7_a_paid_answer_survives_a_crash_before_the_row`
  - `test_f7_a_stored_failure_is_a_new_generation_that_asks_afresh`
  - `test_f7_identical_concurrent_builds_join_one_build`
- [tests/test_figures_final_round.py](../../../../../../tests/test_figures_final_round.py) — direct import
  - `test_a_provider_that_cannot_isolate_is_refused_before_any_request`
- [tests/test_figures_fix_round2.py](../../../../../../tests/test_figures_fix_round2.py) — direct import
  - `test_f7_a_build_committed_between_the_reads_is_reused_inside_the_lock`
- [tests/test_figures_prefetch.py](../../../../../../tests/test_figures_prefetch.py) — direct import
  - `test_a_background_build_stops_off_mains_before_any_request`
  - `test_origin_prefetch_is_refused_from_every_rpc_and_outside_the_service`
- [tests/test_figures_prefetch_review_fixes.py](../../../../../../tests/test_figures_prefetch_review_fixes.py) — direct import
  - `test_f10_a_rich_only_prebuild_shows_no_pending_or_failure_line`
  - `test_f16_a_prebuilds_rich_request_rechecks_the_switch_after_waiting_for_foreground_work`
  - `test_f17_a_plan_wait_is_not_retried_off_mains_or_switched_off`
  - `test_f17_a_speculative_prebuilds_plan_wait_is_retried_by_the_reader_read`
  - `test_f18_a_prebuilds_rich_job_is_pending_on_mains_only`
  - `test_f2_a_queued_prebuild_rich_job_is_not_sent_once_its_route_is_metered`
  - `test_f2_a_quick_prebuild_on_a_metered_author_route_sends_nothing`
  - `test_f3_a_recovered_prebuild_intent_keeps_its_guards`
  - `test_f6_a_prebuilds_rich_job_checks_the_render_minutes_when_it_starts`
  - `test_f7_a_prebuilds_rich_job_in_flight_holds_the_next_prebuild_and_the_judge`
  - `test_f7_a_prebuilds_rich_job_yields_to_foreground_work`
  - `test_f7_a_quick_prebuild_stops_before_its_request_while_the_learner_works`
  - `test_r1_a_pressed_fuller_keeps_its_pending_line_and_is_not_speculative`
  - `test_r1_a_queued_speculative_fuller_is_marked_speculative`
- [tests/test_figures_rw5b_review.py](../../../../../../tests/test_figures_rw5b_review.py) — direct import
  - `test_the_reuse_key_never_names_the_origin_and_keeps_rw5as_keys`
- [tests/test_figures_scope_redesign.py](../../../../../../tests/test_figures_scope_redesign.py) — direct import
  - `test_a_build_makes_no_request_after_its_configuration_changes`
  - `test_the_build_control_makes_every_request`
- [tests/test_figures_show_me_codex_review.py](../../../../../../tests/test_figures_show_me_codex_review.py) — direct import
  - `test_f1_a_reuse_after_figures_are_switched_off_is_refused`
  - `test_f1_switching_off_during_grounding_stops_its_calls_and_the_author`
  - `test_f1_the_control_admits_every_grounding_call`
  - `test_f7_a_reuse_whose_request_cannot_be_recorded_fails_retryably_and_the_retry_reuses`
- [tests/test_followups_batch7_prefetch_capped_resume.py](../../../../../../tests/test_followups_batch7_prefetch_capped_resume.py) — direct import
  - `test_a_figure_the_learner_pressed_for_meanwhile_is_not_counted_as_the_prebuilds`
- [tests/test_followups_nov2_figure_provenance.py](../../../../../../tests/test_followups_nov2_figure_provenance.py) — direct import
  - `test_a_revision_inherits_its_bases_learner_state_protection`
  - `test_a_rich_revision_with_nothing_inherited_carries_no_record`
- [tests/test_learner_data_relax_2.py](../../../../../../tests/test_learner_data_relax_2.py) — direct import
  - `test_a_rich_only_figure_whose_learner_inputs_became_protected_is_never_reused`
  - `test_switched_off_the_payload_prompt_and_key_are_the_predecessors_byte_for_byte`
  - `test_the_learner_state_reaches_the_author_and_protected_work_never_does`
  - `test_the_reuse_key_and_prompt_version_name_the_state_only_when_non_empty`
  - `test_the_rich_author_receives_what_the_figure_author_received`
- [tests/test_reader_rw5d_p4b_teacher_visuals.py](../../../../../../tests/test_reader_rw5d_p4b_teacher_visuals.py) — direct import
  - `test_a_lesson_figure_never_spawns_a_rich_job`
  - `test_switching_visuals_off_hides_a_lessons_figures_and_stops_a_pending_one`
- [tests/test_rw5c_judgments.py](../../../../../../tests/test_rw5c_judgments.py) — direct import
  - `test_at_build_a_failure_leaves_no_figure_row_and_no_verdict`
- [tests/test_rw5c_recheck.py](../../../../../../tests/test_rw5c_recheck.py) — direct import
  - `test_a_prebuilt_figure_nobody_pressed_for_that_differs_lists_nothing`
  - `test_the_reuse_key_is_unchanged_without_a_source_check_id`
- [tests/test_rw5c_source_check.py](../../../../../../tests/test_rw5c_source_check.py) — direct import
  - `test_build_key_holds_the_switch_and_the_reuse_key_does_not`
  - `test_the_switch_off_at_the_store_writes_nothing`
  - `test_the_switch_off_between_the_sandbox_and_the_second_attempt_stops_the_build`
- [tests/test_sketch_service.py](../../../../../../tests/test_sketch_service.py) — direct import
  - `test_without_the_engine_the_contract_prompt_and_key_are_rw5bs_byte_for_byte`

## Modification guidance

- Make changes here when the responsibility remains build within learnloop.figures; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/figures/build.py](../../../../../../src/learnloop/figures/build.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
