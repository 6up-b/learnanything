---
title: "learnloop.figures.rich"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/figures/rich.py"
source_paths:
  - "src/learnloop/figures/rich.py"
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
  - "learnloop.figures.rich module"
  - "src/learnloop/figures/rich.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-figures"
---

# `learnloop.figures.rich`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.figures.rich` exists within [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] to own the behavior summarized by its module contract: Reader RW5d P2b: the rich tiers, their menu, the rich author route and the rich job.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/figures/rich.py](../../../../../../src/learnloop/figures/rich.py) |
| Source lines | 1063 |
| Owning package | [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `rich_tiers_switch(vault: Any) -> bool` ([source](../../../../../../src/learnloop/figures/rich.py), line 128)
- `manim_runtime_state(vault: Any, *, probe: bool=True) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/rich.py), line 132) — Whether this machine can run the Manim tier, and why not: Linux, the ``bwrap`` binary, Manim installed (probed once per process per command: ``manim --version`` takes seconds).
- `manim_tier_ready(vault: Any) -> bool` ([source](../../../../../../src/learnloop/figures/rich.py), line 169) — The Manim tier is on the menu: the rich tiers on, this machine ready, the standing opt-in given.
- `manim_opt_in_needed(vault: Any) -> bool` ([source](../../../../../../src/learnloop/figures/rich.py), line 177) — The Manim tier would be on the menu but for the opt-in, never asked yet (the press shows the inline *allow · not now* once; spec §9b.3).
- `tiers_allowed(vault: Any, *, sketch: bool) -> tuple[str, ...]` ([source](../../../../../../src/learnloop/figures/rich.py), line 187) — The author's menu (module docstring), in the spec's order.
- `rich_on_menu(tiers: Sequence[str]) -> bool` ([source](../../../../../../src/learnloop/figures/rich.py), line 198)
- `runtime_digest(vault: Any) -> str` ([source](../../../../../../src/learnloop/figures/rich.py), line 202) — What a Manim figure's reuse key and row name: the Manim version and the sandbox profile (§8.5).
- `class RichBrief` ([source](../../../../../../src/learnloop/figures/rich.py), line 214)
  - `as_dict(self) -> dict[str, Any]` (line 222; public)
- `parse_brief(raw: Any, tiers: Sequence[str], status: str, *, grounded: bool=True) -> tuple[RichBrief | None, list[str]]` ([source](../../../../../../src/learnloop/figures/rich.py), line 228) — The author's ``rich_json`` for a rich status: the tier must be the status and on the menu; the brief is capped at :data:`RICH_BRIEF_MAX`.
- `class FigureManimOutputV1(ManimAnimation)` ([source](../../../../../../src/learnloop/figures/rich.py), line 271) — The rich author's answer for the ``manim`` tier: the concept animation contract (scene_code, scene_class, title, narration_md), reused, plus ``declared_json`` (the functions, claims and plotted_from; spec §9b.1).
- `declared_text() -> str` ([source](../../../../../../src/learnloop/figures/rich.py), line 297)
- `rich_instructions() -> str` ([source](../../../../../../src/learnloop/figures/rich.py), line 312)
- `rich_context(vault: Any, author_context: Mapping[str, Any], brief: Mapping[str, Any], problems: Sequence[str], revision: Mapping[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/rich.py), line 316) — What the rich author is sent: what the figure author saw (passages, the request, its grounding), the brief, the animation settings the concept pipeline uses, and the problems of the last attempt (code's words).
- `rich_prompt(context: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/figures/rich.py), line 344)
- `rich_build_key(vault: Any) -> tuple[Any, ...]` ([source](../../../../../../src/learnloop/figures/rich.py), line 354) — What a rich job depends on, compared before every request it makes (:class:`~learnloop.figure_admission.FiguresGate`): the vault, the switches, the rich route as configured, the day's cap and price, and the standing opt-in (withdrawn: the job stops with nothing stored).
- `attempt_hosted_job(repository: Repository, payload: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/figures/rich.py), line 374) — RW5d P3 (orchestrator ruling R1): a rich job for a figure asked on an attempt host (practice, feedback or the workbench).
- `class RichJobStopped(Exception)` ([source](../../../../../../src/learnloop/figures/rich.py), line 396) — The rich job ends without a row (``code``: ``figures_changed``, ``rich_disabled``, ``manim_unavailable``, ``exam_material``, ``waiting_for_plan``, ``capped``, ``unpriced``, ``unrouted``, ``not_isolated``, ``models_off``); ``retryable`` for the plan wait.
  - `__init__(self, code: str, message: str, *, retryable: bool=False) -> None` (line 402; internal)
- `run_rich_job(vault: Any, repository: Repository, payload: Mapping[str, Any], *, client: Any | None=None, report: Report | None=None, renderer: Renderer | None=None, function_runner: M.FunctionRunner | None=None, live_vault: Callable[[], Any] | None=None, cancellation: tuple[type[BaseException], ...]=(), clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/rich.py), line 445) — The rich job's body (module docstring).
- `content_key_for(payload: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/figures/rich.py), line 832) — A rich job's request identity: its input and the quick figure it follows (a rerun recovers a paid answer).
- `canonical_spec(figure: M.ManimFigure, brief: Mapping[str, Any], assumptions: Sequence[Mapping[str, Any]], claims: Sequence[Mapping[str, Any]]) -> str` ([source](../../../../../../src/learnloop/figures/rich.py), line 841)
- `rich_jobs(repository: Repository) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/figures/rich.py), line 924) — The rich jobs the queue still keeps, newest first.
- `job_state(job: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/rich.py), line 933) — A rich job as the figure line reads it: ``pending`` (with its phase), ``waiting_for_plan``, ``failed`` (with code's reason) or ``cancelled``.
- `rich_job_for_quick(repository: Repository, fast_figure_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/figures/rich.py), line 953) — The newest rich job started for this quick figure, in any state, looked up by its payload over the whole queue (not a recent window), so a recovered intent (Codex review F8) never restarts a build that ran, failed or was cancelled long ago.
- `rich_job_for_request(repository: Repository, request_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/figures/rich.py), line 966) — The newest rich job of this figure request, in any state, looked up by its payload over the whole queue (Reader follow-ups Nov 1b, RW5d P2b ruling R1: a stored failure's job, however many rich jobs ran since).
- `rich_job_for_figure(repository: Repository, figure_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/figures/rich.py), line 978) — The newest rich job correcting this figure (payload ``supersedes_id``), in any state, over the whole queue (Reader follow-ups Nov 1b, Codex review F4: a newer correction speaks for the figure even after it left the recent window, a cancelled one that stored no row included).
- `rich_job_id_for_quick(repository: Repository, fast_figure_id: str) -> str | None` ([source](../../../../../../src/learnloop/figures/rich.py), line 991)
- `rich_job_for(jobs: Sequence[Mapping[str, Any]], *, input_hash: str | None=None, fast_figure_id: str | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/figures/rich.py), line 996)
- `due_for_plan_retry(job_id: str, *, now: float | None=None) -> bool` ([source](../../../../../../src/learnloop/figures/rich.py), line 1011) — A plan-waiting job is asked again at most once per :data:`PLAN_WAIT_RETRY_SECONDS` (in this process).
- `plan_retry_order(job_id: str) -> float` ([source](../../../../../../src/learnloop/figures/rich.py), line 1023) — A sort key: the job's last plan retry in this process (``-inf``: never asked), so a scan asks the least recently asked job first (follow-ups batch 6, Codex review F2).

### Module constants

- `RICH_TASK` ([src/learnloop/figures/rich.py](../../../../../../src/learnloop/figures/rich.py), line 89)
- `RICH_PROMPT_VERSION` ([src/learnloop/figures/rich.py](../../../../../../src/learnloop/figures/rich.py), line 90)
- `RICH_TIERS` ([src/learnloop/figures/rich.py](../../../../../../src/learnloop/figures/rich.py), line 92)
- `RICH_BRIEF_MAX` ([src/learnloop/figures/rich.py](../../../../../../src/learnloop/figures/rich.py), line 94)
- `MAX_RICH_ATTEMPTS` ([src/learnloop/figures/rich.py](../../../../../../src/learnloop/figures/rich.py), line 96)
- `SANDBOX_PROFILE_VERSION` ([src/learnloop/figures/rich.py](../../../../../../src/learnloop/figures/rich.py), line 98)
- `RICH_JOB_TYPE` ([src/learnloop/figures/rich.py](../../../../../../src/learnloop/figures/rich.py), line 100)
- `PLAN_WAIT_RETRY_SECONDS` ([src/learnloop/figures/rich.py](../../../../../../src/learnloop/figures/rich.py), line 104)
- `WAITING_FOR_PLAN` ([src/learnloop/figures/rich.py](../../../../../../src/learnloop/figures/rich.py), line 106)
- `RICH_OFF_KIND` ([src/learnloop/figures/rich.py](../../../../../../src/learnloop/figures/rich.py), line 108)
- `RICH_OFF_LABEL` ([src/learnloop/figures/rich.py](../../../../../../src/learnloop/figures/rich.py), line 109)
- `MANIM_LABEL` ([src/learnloop/figures/rich.py](../../../../../../src/learnloop/figures/rich.py), line 111)
- `MANIM_UNCHECKED_LABEL` ([src/learnloop/figures/rich.py](../../../../../../src/learnloop/figures/rich.py), line 112)
- `MANIM_NOT_FROM_BOOKS_LABEL` ([src/learnloop/figures/rich.py](../../../../../../src/learnloop/figures/rich.py), line 113)
- `MANIM_NOT_COVERED` ([src/learnloop/figures/rich.py](../../../../../../src/learnloop/figures/rich.py), line 115)
- `LEDGER_TASK` ([src/learnloop/figures/rich.py](../../../../../../src/learnloop/figures/rich.py), line 116)
- `TIER_LEDGER_TASK` ([src/learnloop/figures/rich.py](../../../../../../src/learnloop/figures/rich.py), line 117)
- `_MANIM_PROBE` ([src/learnloop/figures/rich.py](../../../../../../src/learnloop/figures/rich.py), line 124)
- `_PROBE_GUARD` ([src/learnloop/figures/rich.py](../../../../../../src/learnloop/figures/rich.py), line 125)
- `DECLARED_TEXT` ([src/learnloop/figures/rich.py](../../../../../../src/learnloop/figures/rich.py), line 279)
- `RICH_INSTRUCTIONS` ([src/learnloop/figures/rich.py](../../../../../../src/learnloop/figures/rich.py), line 301)
- `ATTEMPT_HOST_READER_ONLY` ([src/learnloop/figures/rich.py](../../../../../../src/learnloop/figures/rich.py), line 370)
- `PREFETCH_NOT_PLAN` ([src/learnloop/figures/rich.py](../../../../../../src/learnloop/figures/rich.py), line 551)
- `PREFETCH_RENDER_CAP` ([src/learnloop/figures/rich.py](../../../../../../src/learnloop/figures/rich.py), line 553)
- `BACKGROUND_HOLDS` ([src/learnloop/figures/rich.py](../../../../../../src/learnloop/figures/rich.py), line 562)
- `LEARNER_STATE_OFF` ([src/learnloop/figures/rich.py](../../../../../../src/learnloop/figures/rich.py), line 615)
- `PHASES` ([src/learnloop/figures/rich.py](../../../../../../src/learnloop/figures/rich.py), line 920)
- `_LAST_REQUEUE` ([src/learnloop/figures/rich.py](../../../../../../src/learnloop/figures/rich.py), line 1007)
- `_REQUEUE_GUARD` ([src/learnloop/figures/rich.py](../../../../../../src/learnloop/figures/rich.py), line 1008)

### Explicit exports

`__all__` declares:

- `FigureManimOutputV1`
- `MAX_RICH_ATTEMPTS`
- `PLAN_WAIT_RETRY_SECONDS`
- `RICH_BRIEF_MAX`
- `RICH_JOB_TYPE`
- `RICH_PROMPT_VERSION`
- `RICH_TASK`
- `RICH_TIERS`
- `RichBrief`
- `LEARNER_STATE_OFF`
- `RichJobStopped`
- `WAITING_FOR_PLAN`
- `job_state`
- `manim_opt_in_needed`
- `manim_runtime_state`
- `manim_tier_ready`
- `parse_brief`
- `plan_retry_order`
- `rich_build_key`
- `rich_context`
- `rich_job_for`
- `rich_job_for_quick`
- `rich_job_for_figure`
- `rich_job_for_request`
- `rich_job_id_for_quick`
- `rich_jobs`
- `rich_on_menu`
- `rich_prompt`
- `run_rich_job`
- `tiers_allowed`

## Internal implementation anchors

- `_say(report: Report | None, phase: str, message: str) -> None` ([source](../../../../../../src/learnloop/figures/rich.py), line 419)
- `_existing(repository: Repository, input_hash: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/figures/rich.py), line 424)
- `_verified_quotes(brief: Mapping[str, Any], span_texts: Mapping[str, str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/figures/rich.py), line 429)
- `_background_holds() -> tuple[str, ...]` ([source](../../../../../../src/learnloop/figures/rich.py), line 556)
- `_prefetch_hold(repository: Repository, client: Any | None) -> Callable[[Any], str | None]` ([source](../../../../../../src/learnloop/figures/rich.py), line 565) — RW5d P5: a prebuild's rich job's hold before every request (the vault as configured now): the switch, the power and foreground work (the gate waits for it first, before it reads the vault: Codex re-review F16), the rich author's route on the plan (Codex review F2), and today's b…
- `_prefetch_wait() -> bool` ([source](../../../../../../src/learnloop/figures/rich.py), line 590) — A prebuild's rich job's wait for foreground work to end (at most ``FOREGROUND_WAIT_SECONDS``), run by its gate before it reads the vault.
- `_pressed_foreground(pressed: bool) -> Iterator[None]` ([source](../../../../../../src/learnloop/figures/rich.py), line 600) — RW5d P5 (Codex review F7): a pressed rich build is the learner's work in flight, so background prebuilds yield to it while it runs.
- `_recovered(vault: Any, repository: Repository, payload: Mapping[str, Any], found: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/rich.py), line 619) — The figure this job's input already stored (a resumed job whose row committed before it was acknowledged, or a concurrent store), returned only while the learner state its author was sent, as the stored row and the job's payload record it, is not protected now (Codex re-review F…
- `_plan_down(exc: BaseException) -> bool` ([source](../../../../../../src/learnloop/figures/rich.py), line 636)
- `_interrupt(report: Report | None, phase: str) -> Callable[[], None] | None` ([source](../../../../../../src/learnloop/figures/rich.py), line 643) — The claim check's ``interrupt`` hook: the job's heartbeat in its current phase, where a cancel is noticed (Codex review F2, F6).
- `_run(vault: Any, repository: Repository, payload: Mapping[str, Any], *, base: Mapping[str, Any], gate: FiguresGate, client: Any | None, report: Report | None, renderer: Renderer | None, function_runner: M.FunctionRunner | None, clock: Clock | None, cancellation: tuple[type[BaseException], ...]=()) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/rich.py), line 652)
- `_repair_render(vault: Any, repository: Repository, payload: Mapping[str, Any], *, base: Mapping[str, Any], gate: FiguresGate, route: R.FigureRoute, report: Report | None, render: Renderer, function_runner: M.FunctionRunner | None, stderr: str, previous: M.ManimFigure, clock: Clock | None, cancellation: tuple[type[BaseException], ...]=()) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/rich.py), line 770)
- `_store(vault: Any, repository: Repository, payload: Mapping[str, Any], *, base: Mapping[str, Any], route: R.FigureRoute, figure: M.ManimFigure | None, checks: M.CheckReport | None, video: bytes | None, failure: str, span_texts: Mapping[str, str], clock: Clock | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/rich.py), line 852)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `RichJobStopped`, `run_rich_job`; statically calls `run_rich_job`
- [[Reference/Modules/learnloop/figures/author_answer|learnloop.figures.author_answer]] — imports `module`; statically calls `parse_brief`
- [[Reference/Modules/learnloop/figures/build|learnloop.figures.build]] — imports `module`; statically calls `RichBrief`, `job_state`, `rich_job_for`, `rich_job_id_for_quick`, `rich_jobs`, `rich_on_menu`, `runtime_digest`, `tiers_allowed`
- [[Reference/Modules/learnloop/figures/listing|learnloop.figures.listing]] — imports `module`; statically calls `job_state`, `rich_job_for_figure`, `rich_job_for_request`, `rich_jobs`
- [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] — imports `RICH_TASK`, `module`; statically calls `job_state`, `rich_job_for_request`, `rich_jobs`
- [[Reference/Modules/learnloop/figures/request|learnloop.figures.request]] — imports `module`; statically calls `manim_tier_ready`, `rich_tiers_switch`
- [[Reference/Modules/learnloop/figures/view|learnloop.figures.view]] — imports `module`; statically calls `job_state`, `rich_job_for_quick`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `module`; statically calls `attempt_hosted_job`, `due_for_plan_retry`, `manim_opt_in_needed`, `manim_runtime_state`, `rich_on_menu`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`, `gate_model_requests`; calls `content_key`, `gate_model_requests`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendLimitExceeded`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/content/authoring/ai_contracts|learnloop.content.authoring.ai_contracts]] — imports `CONCEPT_ANIMATION_PROMPT`, `CONCEPT_ANIMATION_SCENE_SCAFFOLD`, `ManimAnimation`
- [[Reference/Modules/learnloop/content/authoring/concept_animation|learnloop.content.authoring.concept_animation]] — imports `capped_scope_prefix`, `lint_scene_pacing`, `manim_runtime`, `pacing_band`, `quality_preset`, `render_scene`, `resolve_manim_command`, `sandbox_bwrap_path`, `store_video_bytes`, `validate_scene_code`; calls `capped_scope_prefix`, `lint_scene_pacing`, `manim_runtime`, `pacing_band`, `quality_preset`, `resolve_manim_command`, `sandbox_bwrap_path`, `store_video_bytes`, `validate_scene_code`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/figures|learnloop.db.stores.figures]] — imports `module`; calls `has_tables`, `insert_figure`, `request`, `reusable`, `set_request_figure`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/figure_admission|learnloop.figure_admission]] — imports `FiguresChanged`, `FiguresGate`, `author_learner_state_enabled`, `figures_enabled`, `manim_opt_in`, `rich_tiers_enabled`; calls `FiguresGate`, `author_learner_state_enabled`, `figures_enabled`, `manim_opt_in`, `rich_tiers_enabled`
- [[Reference/Modules/learnloop/figures/foreground|learnloop.figures.foreground]] — imports `foreground`, `module`; calls `foreground`, `wait_idle`
- [[Reference/Modules/learnloop/figures/labels|learnloop.figures.labels]] — imports `module`
- [[Reference/Modules/learnloop/figures/manim_figure|learnloop.figures.manim_figure]] — imports `module`; calls `ManimFigure`, `check_claims`, `parse_figure`
- [[Reference/Modules/learnloop/figures/power|learnloop.figures.power]] — imports `NOT_ON_MAINS`, `SWITCHED_OFF`, `YIELDED`, `background_hold`; calls `background_hold`
- [[Reference/Modules/learnloop/figures/prefetch_ledger|learnloop.figures.prefetch_ledger]] — imports `render_minutes_left`; calls `render_minutes_left`
- [[Reference/Modules/learnloop/figures/protection|learnloop.figures.protection]] — imports `ATTEMPT_HOST_REFS`, `LEARNER_STATE_INPUTS_KEY`, `_carries_learner_state`, `_inherited_withheld`, `_inherits_learner_state`, `_learner_state_withheld`, `_withheld`, `rich_base_item_protected`, `stored_learner_state_withheld`; calls `_carries_learner_state`, `_inherited_withheld`, `_inherits_learner_state`, `_learner_state_withheld`, `_withheld`, `rich_base_item_protected`, `stored_learner_state_withheld`
- [[Reference/Modules/learnloop/figures/routes|learnloop.figures.routes]] — imports `module`; calls `FigureRoute`, `daily_envelope`, `models_off`
- [[Reference/Modules/learnloop/figures/spec|learnloop.figures.spec]] — imports `MANIM_FIG_VERSION`
- [[Reference/Modules/learnloop/figures/verify|learnloop.figures.verify]] — imports `quote_in`; calls `quote_in`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `plan_route`; calls `plan_route`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `json`, `sqlite3`, `sys`, `threading`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/figures/author_answer|learnloop.figures.author_answer]], [[Reference/Modules/learnloop/figures/build|learnloop.figures.build]], [[Reference/Modules/learnloop/figures/listing|learnloop.figures.listing]], [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] and 3 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/followups_batch6_prefetch_plan_wait_helpers.py](../../../../../../tests/followups_batch6_prefetch_plan_wait_helpers.py) — direct import
- [tests/identity_pins_helpers.py](../../../../../../tests/identity_pins_helpers.py) — direct import
- [tests/rich_fixtures.py](../../../../../../tests/rich_fixtures.py) — direct import
- [tests/test_figure_label_wording.py](../../../../../../tests/test_figure_label_wording.py) — direct import
  - `test_the_vocabulary_comes_from_the_code_owned_labels`
- [tests/test_figure_rich_contract.py](../../../../../../tests/test_figure_rich_contract.py) — direct import
  - `test_switched_off_no_rich_tier_and_no_ask`
  - `test_the_prompt_names_the_rich_tiers_the_menu_offers`
  - `test_tiers_allowed_needs_the_switch_linux_bwrap_manim_and_the_standing_opt_in`
  - `test_v3_instructions_replace_the_preference_and_carry_the_rich_brief`
  - `test_without_the_standing_opt_in_manim_is_not_on_the_menu`
- [tests/test_figure_rich_failed_correction_durable.py](../../../../../../tests/test_figure_rich_failed_correction_durable.py) — direct import
  - `test_codex_f4_a_newer_cancelled_correction_still_speaks_for_the_figure_after_500_newer_rich_jobs`
- [tests/test_figure_rich_job.py](../../../../../../tests/test_figure_rich_job.py) — direct import
  - `test_the_quick_figure_shows_first_and_the_fuller_one_lands_under_it`
  - `test_without_a_grant_a_plan_down_job_waits_and_asks_nothing`
- [tests/test_figure_rich_job_golden.py](../../../../../../tests/test_figure_rich_job_golden.py) — direct import
  - `test_every_stop_code_has_a_case`
- [tests/test_figure_rich_review_fixes.py](../../../../../../tests/test_figure_rich_review_fixes.py) — direct import
  - `test_a_cancel_raised_inside_the_render_repair_propagates`
  - `test_a_crash_rerun_keeps_the_generation_and_the_rich_prompt`
- [tests/test_figure_rich_rpc.py](../../../../../../tests/test_figure_rich_rpc.py) — direct import
  - `test_allowing_where_manim_cannot_run_is_refused`
  - `test_without_a_grant_the_job_belongs_to_no_action_waits_and_a_read_asks_again`
- [tests/test_figure_wait_estimate.py](../../../../../../tests/test_figure_wait_estimate.py) — direct import
  - `test_a_rich_figures_calls_are_named_by_the_rich_jobs_own_key_and_a_reuse_never_relabels_a_build`
- [tests/test_figures_help_codex_review.py](../../../../../../tests/test_figures_help_codex_review.py) — direct import
  - `test_s0_a_legacy_queued_attempt_rich_job_stops_before_any_model_request`
  - `test_s0_an_attempt_hosted_payload_is_refused_by_its_flag_too`
- [tests/test_figures_prefetch_review_fixes.py](../../../../../../tests/test_figures_prefetch_review_fixes.py) — direct import
  - `test_f17_a_plan_wait_is_not_retried_off_mains_or_switched_off`
  - `test_f17_a_speculative_prebuilds_plan_wait_is_retried_by_the_reader_read`
  - `test_f2_a_queued_prebuild_rich_job_is_not_sent_once_its_route_is_metered`
  - `test_f6_a_prebuilds_rich_job_checks_the_render_minutes_when_it_starts`
- [tests/test_followups_batch6_prefetch_plan_wait.py](../../../../../../tests/test_followups_batch6_prefetch_plan_wait.py) — direct import
- [tests/test_followups_batch6_review_fixes.py](../../../../../../tests/test_followups_batch6_review_fixes.py) — direct import
  - `test_f1_the_worker_rechecks_before_the_store`
  - `test_f1_the_worker_stops_a_requeued_prebuild_before_any_request`
  - `test_f1_unreadable_protection_requeues_nothing_and_the_worker_fails_closed`
  - `test_f2_a_job_that_keeps_meeting_the_limit_yields_the_slot_to_the_least_recently_asked`
  - `test_f2_a_paced_job_first_in_line_never_starves_a_due_one`
  - `test_f2_the_scan_goes_past_paced_jobs_until_the_bound_of_requeues`
- [tests/test_followups_batch6_verify_fixes.py](../../../../../../tests/test_followups_batch6_verify_fixes.py) — direct import
  - `test_v1_an_unreadable_stored_plan_fails_closed_everywhere`
  - `test_v1_the_worker_rechecks_the_plan_before_the_store`
  - `test_v1_the_worker_stops_a_requeued_prebuild_a_later_plan_holds_before_any_request`
- [tests/test_followups_batch7_prefetch_capped_resume.py](../../../../../../tests/test_followups_batch7_prefetch_capped_resume.py) — direct import
  - `test_a_rich_only_request_whose_job_exists_is_linked_with_no_figure_yet`
- [tests/test_followups_batch7_prefetch_link_served.py](../../../../../../tests/test_followups_batch7_prefetch_link_served.py) — direct import
- [tests/test_learner_data_relax_2.py](../../../../../../tests/test_learner_data_relax_2.py) — direct import
  - `test_a_recovered_rich_job_rechecks_its_stored_figures_learner_state`
  - `test_a_saved_learner_state_with_no_record_of_its_inputs_is_never_sent`

## Modification guidance

- Make changes here when the responsibility remains rich within learnloop.figures; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/figures/rich.py](../../../../../../src/learnloop/figures/rich.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
