---
title: "learnloop.figures.service"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/figures/service.py"
source_paths:
  - "src/learnloop/figures/service.py"
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
  - "learnloop.figures.service module"
  - "src/learnloop/figures/service.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-figures"
---

# `learnloop.figures.service`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.figures.service` exists within [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] to own the behavior summarized by its module contract: Explorable figures: build, reuse, revise, list, predict, explain (spec_reader_workbench_v1 §8; UX §4.7).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py) |
| Source lines | 3579 |
| Owning package | [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class FigureRefused(Exception)` ([source](../../../../../../src/learnloop/figures/service.py), line 269) — A request the Reader may not make (``code``: ``figures_disabled``, ``exam_material``, ``region_disabled``, ``revisions_disabled``, ``predictions_disabled``, ``offers_disabled`` and ``advanced_disabled`` (RW5b), ``not_found``, ``validation_error``, ``no_image_input``, ``region_un…
  - `__init__(self, code: str, message: str) -> None` (line 277; internal)
- `class FigureRequest` ([source](../../../../../../src/learnloop/figures/service.py), line 284)
- `class SourceContext` ([source](../../../../../../src/learnloop/figures/service.py), line 341)
- `class Grounding` ([source](../../../../../../src/learnloop/figures/service.py), line 353) — Where a request's source text comes from (spec §8.3): ``anchor`` (the learner chose the passage), ``retrieved`` (found in their books for the goal) or ``none`` (nothing found: an illustration that quotes nothing).
- `attempt_hosted(request: 'FigureRequest') -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 365) — RW5d P3: a request made on an attempt host (practice, feedback or the workbench: its verified host references name an item or attempt).
- `lesson_hosted(request: 'FigureRequest') -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 372) — RW5d P4b: a lesson's visual (origin ``teacher``; its host is the lesson, so it has no reading position and no home: it shows in the lesson only).
- `prediction_home(row: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/figures/service.py), line 379) — The extraction a figure's prediction is recorded under: its home, or (RW5d P3, an attempt host's figure with no home) the first book it was grounded in; None for a homeless illustration (its predictions are kept with no extraction: Codex review F9).
- `anchored(request: 'FigureRequest') -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 391) — A request with a passage (a selection or a region).
- `show_me_input(request: 'FigureRequest') -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 397) — RW5d: a request whose goal or grounding the author is sent (a goal, or no passage).
- `build_key(vault: Any) -> tuple[Any, ...]` ([source](../../../../../../src/learnloop/figures/service.py), line 404) — What a build depends on, compared before every request it makes (:class:`~learnloop.figure_admission.FiguresGate`): the vault, the switch, the author route as configured, the day's cap and the price, and (RW5b) whether the advanced panels are on (the author's prompt depends on i…
- `offer_build_key(vault: Any) -> tuple[Any, ...]` ([source](../../../../../../src/learnloop/figures/service.py), line 423) — An offered build's key (origin ``library`` | ``tutor``): :func:`build_key` and ``figures.offers_enabled``, so switching offers off stops it.
- `offered(request: 'FigureRequest') -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 430) — A build an offer started (a "not right?" version of an offered figure is a revision: ``figures.revisions_enabled`` governs it, not the offers).
- `show_me_build_key(vault: Any) -> tuple[Any, ...]` ([source](../../../../../../src/learnloop/figures/service.py), line 437) — A show-me build's key: :func:`build_key` and ``figures.show_me_enabled``.
- `key_for(request: 'FigureRequest')` ([source](../../../../../../src/learnloop/figures/service.py), line 443)
- `rich_row(row: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 473) — RW5d P2b: a stored rich figure (a Manim figure).
- `source_context(vault: Any, repository: Repository, request: FigureRequest) -> SourceContext` ([source](../../../../../../src/learnloop/figures/service.py), line 532)
- `passages_context(vault: Any, repository: Repository, grounding: Grounding) -> SourceContext` ([source](../../../../../../src/learnloop/figures/service.py), line 566) — RW5d: the retrieved passages as the author is sent them (spec §8.2, §8.3): each kept block with the paragraphs around it (held-out ones left out), keyed ``extraction_id:span_id`` so a quote is verified against the right block of the right book.
- `ground(vault: Any, repository: Repository, request: FigureRequest, *, find: FindSources | None=None) -> Grounding` ([source](../../../../../../src/learnloop/figures/service.py), line 674) — A request's grounding (spec §8.3).
- `crop_image(repository: Repository, request: FigureRequest, context: SourceContext) -> tuple[tuple[str, bytes] | None, str | None, list[float] | None]` ([source](../../../../../../src/learnloop/figures/service.py), line 740) — ``(image, asset span, clipped region box)``: a region's crop only, or the figure block's crop; nothing for a selection with no figure.
- `shown_row(row: Mapping[str, Any]) -> Mapping[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 765) — The row as RW5a may show it: nothing in RW5a produces "verified", and a stored one (from a build before the owner's scope decision of 2026-10-21) is shown as the illustration RW5a's rules make it.
- `advanced_off_row(vault: Any, row: Mapping[str, Any]) -> Mapping[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 795) — RW5b: a shown figure that uses a heat map, vector field, trajectory or iterated map, while ``figures.advanced_panels_enabled`` is off, is the unsupported-kind state ("can't draw this yet"); its spec never goes out.
- `sketch_row(row: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 813) — RW5d P2: a stored sketch.
- `sketch_off_row(vault: Any, row: Mapping[str, Any]) -> Mapping[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 819) — RW5d P2: a shown sketch while ``figures.sketch_enabled`` is off (or the engine can't run here) is the unsupported-kind state ("can't draw this yet"); its program never goes out.
- `rich_off_row(vault: Any, row: Mapping[str, Any]) -> Mapping[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 831) — RW5d P2b: a shown rich figure while ``figures.rich_tiers_enabled`` is off is the unsupported-kind state ("can't show this kind here"); its program and video never go out.
- `reverify_hash(spec_json: str, engine_sha256: str, verifier_version: str | None=None) -> str` ([source](../../../../../../src/learnloop/figures/service.py), line 852)
- `sketch_rechecked(row: Mapping[str, Any], repository: Repository | None=None) -> Mapping[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 903) — Spec §8.5, engine upgrades: a shown sketch verified under another engine, or (Codex review F11, round 3) by another verifier version (:data:`.sketch_verify.VERIFIER_REPORT_VERSION`: a report made before a verification fix may carry a check line the fixed verifier would not give)…
- `worded_row(row: Mapping[str, Any]) -> Mapping[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 950) — Spec §9b.4 when a stored figure is presented (Reader follow-ups Nov 1b, Codex review F3): a figure stored before the free-text label rule (or by any path that skipped it) is shown, listed and reused without its label-like text, as :mod:`.labels` rules for an answer that still vi…
- `drawable_now(vault: Any, row: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 985) — A stored figure that can be drawn as configured now (RW5b's panels and RW5d P2's sketch tier both on when it needs them).
- `property_checks(report: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/figures/service.py), line 992) — The closed keys of the checks a shown figure passed (§8.3 steps 1-2).
- `figure_view(vault: Any, repository: Repository, row: Mapping[str, Any], *, versions: int=1, home: Mapping[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 1052) — A figure as the Reader shows it.
- `source_rejected(vault: Any, repository: Repository, row: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 1213) — RW5c (§6.6): the figure's newest check, at the current certification version and with the switch on, proved a stated claim different.
- `rebuild_request(vault: Any, repository: Repository, base: Mapping[str, Any]) -> FigureRequest` ([source](../../../../../../src/learnloop/figures/service.py), line 1283) — *Rebuild* of a figure whose stated claim differs (§6.6, Codex review F3): a new version through the revision path, never a reuse of the rejected row.
- `redelivered_view(vault: Any, repository: Repository, view: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 1312) — A figure view kept since its build (a finished job's result, read again through ``reader.figure_job``) as it may go out now (follow-ups Nov 2): its fuller version is rebuilt from the current rows (:func:`fuller_state`), so a fuller version whose learner inputs became protected s…
- `fuller_state(vault: Any, repository: Repository, row: Mapping[str, Any]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/figures/service.py), line 1346) — RW5d P2b (spec §6.8, §8.6): the fuller version of a quick figure, or None when it has none: ``ready`` (with the rich figure's view), ``failed`` (code's reason; the quick version stays), ``pending`` (the job's phase), ``waiting_for_plan`` or ``cancelled``.
- `request_hash(request: FigureRequest, context: SourceContext, image_digest: str | None, *, advanced: bool=False, grounding: Grounding | None=None, sketch: bool=False, tiers: Sequence[str] | None=None, rich_runtime: str | None=None, learner_state: Mapping[str, Any] | None=None) -> str` ([source](../../../../../../src/learnloop/figures/service.py), line 1433) — The reuse key: the spec and prompt versions (RW5b's panels have their own prompt version, so RW5a's hashes are unchanged while they are off) and everything the author is sent (never the origin: :data:`REUSE_ORIGIN`).
- `check_request(vault: Any, repository: Repository, request: FigureRequest) -> FigureRequest` ([source](../../../../../../src/learnloop/figures/service.py), line 1669) — Validate a request and refuse held-out material, on the request path, before any job or call (the handler's first step; the build repeats it).
- `class BuildOutcome` ([source](../../../../../../src/learnloop/figures/service.py), line 1721)
- `build_figure(vault: Any, repository: Repository, request: FigureRequest, *, author_client: Any | None=None, clock: Clock | None=None, live_vault: Callable[[], Any] | None=None, find: FindSources | None=None, spawn_rich: SpawnRich | None=None, cancelled: Callable[[], bool] | None=None) -> BuildOutcome` ([source](../../../../../../src/learnloop/figures/service.py), line 1789) — Build one figure (module docstring).
- `retry_rich_job(vault: Any, repository: Repository, job_id: str) -> str` ([source](../../../../../../src/learnloop/figures/service.py), line 2043) — Codex review F9: the error code of a rich job that ended with no row and may be requeued (failed, not waiting for the plan, never cancelled), or :class:`FigureRefused`.
- `ensure_rich_job(repository: Repository, spawn: SpawnRich, payload: dict[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/figures/service.py), line 2545) — Start a quick figure's rich job unless it already has one (in any state: a cancelled one stays cancelled) or a stored fuller version (Codex review F8).
- `resume_rich_intents(vault: Any, repository: Repository, extraction_id: str, spawn: SpawnRich | None) -> int` ([source](../../../../../../src/learnloop/figures/service.py), line 2564) — Codex review F8: start the rich job of every shown quick figure of this source whose intent committed but whose job was never enqueued (the sidecar stopped between the two, or the enqueue failed).
- `revision_request(repository: Repository, base: Mapping[str, Any], note: str) -> FigureRequest` ([source](../../../../../../src/learnloop/figures/service.py), line 2897) — "Not right?" on a stored figure: the same input with the note.
- `prefetch_pending(vault: Any, repository: Repository, extraction_id: str, *, pass_running: bool=False) -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 3058) — RW5d P5 (Codex review F11): whether a prebuild for this source is coming now: the Reader then reads its figures again, paced, so a completed prebuild appears without a reopen.
- `prefetch_plan_waits(vault: Any, repository: Repository, extraction_id: str | None, *, request_ids: Collection[str] | None=None, clock: Clock | None=None) -> list[str]` ([source](../../../../../../src/learnloop/figures/service.py), line 3101) — RW5d P5 (Codex re-review F17): this source's speculative prebuild rich jobs waiting for the plan, newest per input, whose retry is admissible now: figures ahead of need on, this machine on mains, and the passage not held out.
- `build_prefetch_figure(vault: Any, repository: Repository, request: FigureRequest, *, author_client: Any | None=None, clock: Clock | None=None, live_vault: Callable[[], Any] | None=None, find: FindSources | None=None, spawn_rich: SpawnRich | None=None) -> BuildOutcome` ([source](../../../../../../src/learnloop/figures/service.py), line 3153) — RW5d P5: one background build for the prefetch service (spec §10b), under ``quiet()``: no offer, no grant (plan down: it waits).
- `list_figures(vault: Any, repository: Repository, extraction_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/figures/service.py), line 3173) — The figures of one source as the Reader shows them: per version chain, the newest shown version (else the newest failed or unsupported one), of the current spec version, and never one whose passage is held out now.
- `section_figures(vault: Any, repository: Repository, extraction_id: str, section_of: Callable[[str], str | None]) -> dict[str, list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/figures/service.py), line 3187) — RW5d P4a (spec §10.2): the kept figures of one reading by the section their anchor is in, for the correspondents read (figures follow the section).
- `rich_pending(vault: Any, repository: Repository, extraction_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/figures/service.py), line 3240) — RW5d P2b (spec §6.8): the rich builds with no quick figure for this source that have not ended (pending, or waiting for the plan), each as the pending line under its passage; empty while the rich tiers are off.
- `rich_revision_retry(vault: Any, repository: Repository, job_id: str) -> FigureRequest | None` ([source](../../../../../../src/learnloop/figures/service.py), line 3360) — Codex re-review F14: "try again" on a correction of an animation whose job stored a failure (the line :func:`rich_pending` lists): the same correction (the figure it corrects, the learner's note), built afresh.
- `shown_figure(vault: Any, repository: Repository, figure_id: str) -> tuple[dict[str, Any], Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 3389) — A figure that may be shown now: shown verification, a current spec version, its passage not held out.
- `record_prediction(vault: Any, repository: Repository, figure_id: str, index: int, answer: str, *, clock: Clock | None=None, on_queued: Callable[[str], None] | None=None, assist_id: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 3429) — The learner's prediction, its observed before/after readout and whether it matched (code decides).
- `record_explanation(vault: Any, repository: Repository, prediction_id: str, text: str, *, clock: Clock | None=None, on_queued: Callable[[str], None] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 3501) — "What changed, and why?" (optional, once).

### Module constants

- `ORIGINS` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 219)
- `RESERVED_ORIGINS` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 220)
- `SERVICE_ORIGINS` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 222)
- `LESSON_TIERS` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 226)
- `OFFER_ORIGINS` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 228)
- `GOAL_AUTHORS` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 231)
- `GOAL_CHARS` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 232)
- `GROUNDING_PASSAGES` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 234)
- `GROUNDINGS` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 235)
- `SHOW_ME_VERSION` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 236)
- `REQUEST_PREFIX` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 237)
- `NOT_FROM_BOOKS_LABEL` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 240)
- `FIGURE_BLOCK_TYPES` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 241)
- `CONTEXT_BLOCKS` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 243)
- `PASSAGE_CHARS` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 244)
- `CONTEXT_CHARS` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 245)
- `NOTE_CHARS` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 246)
- `EXPLANATION_CHARS` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 247)
- `ANSWER_CHARS` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 248)
- `LEDGER_TASK` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 249)
- `RECONSTRUCTION_REASON` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 252)
- `PREDICTION_PREFIX` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 253)
- `FIGURE_PREFIX` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 254)
- `LABELS` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 256)
- `SKETCH_LABEL` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 260)
- `SKETCH_UNCHECKED_LABEL` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 261)
- `SKETCH_NOT_FROM_BOOKS_LABEL` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 262)
- `SKETCH_OFF_KIND` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 264)
- `ENGINE_CHANGED_REASON` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 265)
- `TIER_LEDGER_TASK` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 266)
- `ADVANCED_OFF_KIND` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 480)
- `LEARNER_INPUTS_RECORDED` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 513)
- `PROPERTY_CHECKS` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 780)
- `_RECHECKED` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 844)
- `_RECHECKED_GUARD` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 845)
- `REVERIFY_VERSION` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 849)
- `REUSE_ORIGIN` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 1430)
- `_PREFETCH_BUILD` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 1539)
- `PREFETCH_GOAL_AUTHORS` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 1541)
- `PREFETCH_AUTHOR_NOT_PLAN` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 1837)
- `_BUILD_CANCELLED` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 1855)
- `_BUILDS_GUARD` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 2070)
- `_BUILDS` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 2071)
- `STORAGE_BUSY` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 2124)
- `_LOG` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 2541)
- `_RICH_SPAWN_GUARD` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 2542)

### Explicit exports

`__all__` declares:

- `BuildOutcome`
- `FigureRefused`
- `FigureRequest`
- `GROUNDING_PASSAGES`
- `Grounding`
- `LABELS`
- `LESSON_TIERS`
- `NOT_FROM_BOOKS_LABEL`
- `SERVICE_ORIGINS`
- `anchored`
- `build_figure`
- `rebuild_request`
- `source_rejected`
- `check_request`
- `figure_view`
- `ground`
- `lesson_hosted`
- `revision_request`
- `redelivered_view`
- `show_me_input`
- `fuller_state`
- `ensure_rich_job`
- `resume_rich_intents`
- `retry_rich_job`
- `rich_off_row`
- `rich_pending`
- `rich_row`
- `sketch_off_row`
- `sketch_rechecked`
- `sketch_row`
- `list_figures`
- `record_explanation`
- `record_prediction`
- `section_figures`
- `shown_figure`

## Internal implementation anchors

- `_key_for(request: 'FigureRequest')` ([source](../../../../../../src/learnloop/figures/service.py), line 465)
- `_unrecorded_occupant(vault: Any, connection: Any, input_hash: str) -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 487) — Codex re-review F5: whether this input's reusable figure (its quick figure, or a rich figure built with no quick one) is a marked row that keeps no record of what its author's learner state was read from.
- `_recorded_input_key(input_hash: str) -> str` ([source](../../../../../../src/learnloop/figures/service.py), line 499) — Codex re-review F5: the key a fresh build of an input takes when that input's figure is a marked row with no record.
- `_with_learner_inputs(report: Mapping[str, Any], request: 'FigureRequest') -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 516) — A quick figure's report with what its author's learner state was read from (follow-ups Nov 2: the record rich rows keep since learner data-relax 2, ``protection.LEARNER_STATE_INPUTS_KEY``; never shown or sent to a model), so the figure is rechecked whenever it goes out.
- `_find_sources(vault: Any, repository: Repository, query: str, **kwargs: Any) -> Any` ([source](../../../../../../src/learnloop/figures/service.py), line 622)
- `_reading_learning_objects(vault: Any, repository: Repository, reading_at: Mapping[str, Any] | None) -> list[str]` ([source](../../../../../../src/learnloop/figures/service.py), line 628) — The learning objects of the passage the learner was reading (retrieval context only).
- `_passage_ref(hit: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 642)
- `_with_sources(repository: Repository, passages: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/figures/service.py), line 648) — Each passage with its source's id and title (Codex review F8: the Reader's citation chips peek in this book and open another as a detour, which needs the source).
- `_decode(render: str | None) -> tuple[str, bytes] | None` ([source](../../../../../../src/learnloop/figures/service.py), line 730)
- `_advanced_kinds(row: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/figures/service.py), line 784) — The RW5b panel kinds a stored figure's spec uses (none when it has no spec).
- `_stored_verifier(row: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/figures/service.py), line 859) — The verifier report version a stored row's report was made by (None: before the version existed).
- `_record_reverification(repository: Repository | None, row: Mapping[str, Any], cached: Mapping[str, Any], engine_sha256: str) -> None` ([source](../../../../../../src/learnloop/figures/service.py), line 867) — Codex review F8: an engine re-verification is a verifier verdict, so it is appended to ``judgment_ledger`` (task ``figure_verified``, judge ``verifier``) before the figure is delivered, superseding the figure's last verdict on that question.
- `_label(row: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/figures/service.py), line 1002)
- `_prediction_view(found: Mapping[str, Any] | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/figures/service.py), line 1029)
- `_anchor_span(row: Mapping[str, Any], asked: Mapping[str, Any] | None, home: Mapping[str, Any] | None) -> str | None` ([source](../../../../../../src/learnloop/figures/service.py), line 1040) — Where a figure shows: under the selection's last block; a region's figure (no selected text) under the region's block (Codex review F2); RW5d: a figure with no passage under the passage the learner was reading (``home``, else its own request's reading position).
- `_sketch_view(vault: Any, repository: Repository, row: Mapping[str, Any], view: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 1137) — A shown sketch as the Reader draws it: the program (its code runs in the desktop's sealed engine), the code-owned check lines and the *not covered* line, and its predictions (answers never sent first).
- `_manim_view(row: Mapping[str, Any], view: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 1188) — A shown Manim figure (RW5d P2b, spec §6.8): the content-addressed video (played over ``llmedia://``), its title and transcript, the code-owned check lines and *the video itself is not checked frame by frame*.
- `_source_rejected_row(vault: Any, repository: Repository, row: Mapping[str, Any]) -> Mapping[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 1224)
- `_source_check_view(vault: Any, repository: Repository, row: Mapping[str, Any], compiled: S.CompiledFigure, view: dict[str, Any]) -> None` ([source](../../../../../../src/learnloop/figures/service.py), line 1232) — RW5c (§7.4): a shown grammar figure's ``elements`` and ``source_check``, read from the ledger as the switch is now (absent with it off: the view is RW5a/RW5d's key for key).
- `_coded_answer(answered: Mapping[str, Any], by_label: Mapping[str, str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 1263) — An answered area prediction under code-owned labels: its stored answers (shade labels, kept as they were) go out as the shades' element ids.
- `_code_owned_labels(vault: Any, repository: Repository, row: Mapping[str, Any], compiled: S.CompiledFigure) -> dict[str, str] | None` ([source](../../../../../../src/learnloop/figures/service.py), line 1271) — Model label -> element id while this figure's labels are code-owned, else None.
- `_presented_row(vault: Any, repository: Repository, row: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 1298) — A stored row as :func:`figure_view` presents it under the switches now.
- `_prefetch_intent_refused(vault: Any, repository: Repository, intent: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 1399) — Landing ruling R1: whether background admission refuses a prebuild's unqueued rich intent now: figures ahead of need off, this machine not on mains, or its input held out.
- `_figure_request(repository: Repository, row: Mapping[str, Any]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/figures/service.py), line 1412) — The ``figure_requests`` row a figure was built for (RW5d), or None (RW5a/b rows before 224).
- `_reusable(vault: Any, repository: Repository, connection: Any, input_hash: str, other_hash: str | Sequence[str]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/figures/service.py), line 1505) — The figure a build reuses: this input's under the current prompt version, else (Codex review F2) a SHOWN one of the same input under the other prompt version when it can be drawn now.
- `_validated_request(vault: Any, repository: Repository, request: FigureRequest) -> FigureRequest` ([source](../../../../../../src/learnloop/figures/service.py), line 1544)
- `_validated_prefetch(vault: Any, request: FigureRequest) -> FigureRequest` ([source](../../../../../../src/learnloop/figures/service.py), line 1633) — RW5d P5: a prefetch build's request, as the prefetch service made it: an anchor (a passage of a book), an optional goal by the prefetch judge or a lesson plan's teacher, never an attempt host, a region or a revision.
- `_author_context(request: FigureRequest, context: SourceContext, image_digest: str | None, previous: Mapping[str, Any] | None, problems: Sequence[str], *, request_id: str, grounding: Grounding | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 1736)
- `_prefetch_build_hold(author_client: Any | None) -> Callable[[Any], str | None]` ([source](../../../../../../src/learnloop/figures/service.py), line 1841)
- `_cancel_hold(cancelled: Callable[[], bool], other: Callable[[Any], str | None] | None) -> Callable[[Any], str | None]` ([source](../../../../../../src/learnloop/figures/service.py), line 1858)
- `_build(vault: Any, repository: Repository, request: FigureRequest, *, gate: FiguresGate, author_client: Any | None, clock: Clock | None, find: FindSources | None, spawn_rich: SpawnRich | None=None) -> BuildOutcome` ([source](../../../../../../src/learnloop/figures/service.py), line 1868)
- `_learner_state(vault: Any, repository: Repository, request: FigureRequest, context: SourceContext, grounding: Grounding) -> Any` ([source](../../../../../../src/learnloop/figures/service.py), line 1994) — Learner data-relax 2: what the author is told about the learner on the passage's topics and what it was read from (:func:`.learner_state.read_learner_state`), or None (switched off or no topics; an empty or unreadable state: the predecessor's build).
- `_rich_pending(vault: Any, repository: Repository, request: FigureRequest, input_hash: str) -> BuildOutcome | None` ([source](../../../../../../src/learnloop/figures/service.py), line 2015) — A rich-only build of this input still running or waiting (its job is pending or waiting for the plan): the request takes its pending line.
- `_rich_line(request: FigureRequest, job: Mapping[str, Any], state: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 2031)
- `_withheld_payload(vault: Any, repository: Repository, payload: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 2064)
- `_building(repository: Repository, input_hash: str) -> Iterator[None]` ([source](../../../../../../src/learnloop/figures/service.py), line 2075) — Hold this process's one lock for (vault, input) while a build runs.
- `_request_row(request: FigureRequest, grounding: Grounding, *, figure_id: str | None, clock: Clock | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 2096) — The ``figure_requests`` row of one request (RW5d, spec §13.1): what was asked, as normalized, and what the server derived.
- `_reused(vault: Any, repository: Repository, row: Mapping[str, Any], *, request: FigureRequest | None=None, grounding: Grounding | None=None, clock: Clock | None=None, gate: FiguresGate | None=None) -> BuildOutcome` ([source](../../../../../../src/learnloop/figures/service.py), line 2127)
- `_free_text(output: Any, status: str) -> list[tuple[str, Any]]` ([source](../../../../../../src/learnloop/figures/service.py), line 2153) — The author's model-written free text the label rule reads (spec §9b.4): the tier reason, and what each figure it carries shows and assumes (a rich status's quick figure and brief included).
- `_without_label_text(output: Any) -> Any` ([source](../../../../../../src/learnloop/figures/service.py), line 2171) — The author's answer with its label-like free text left out (spec §9b.4): a tier reason in code's words, a figure's or brief's label-like ``demonstrates`` emptied and label-like assumptions dropped.
- `_step_three(vault: Any, repository: Repository, compiled: S.CompiledFigure, context: SourceContext, request: FigureRequest, grounding: Grounding | None, gate: FiguresGate) -> SC.Check | None` ([source](../../../../../../src/learnloop/figures/service.py), line 2194) — RW5c's check of a spec that passed steps 1-2, or None with the switch off.
- `_author_and_store(vault: Any, repository: Repository, request: FigureRequest, context: SourceContext, author: R.FigureRoute, *, request_id: str, **kwargs: Any) -> BuildOutcome` ([source](../../../../../../src/learnloop/figures/service.py), line 2216) — :func:`_author_attempts_and_store`, then one ``figure_author`` record per attempt (ADR-017), written once the build has ended, refused or failed, so a record never changes the build.
- `_author_attempts_and_store(vault: Any, repository: Repository, request: FigureRequest, context: SourceContext, author: R.FigureRoute, *, previous: Mapping[str, Any] | None, versions: int, image: tuple[str, bytes] | None, asset_id: str | None, digest: str | None, input_hash: str, request_id: str, clock: Clock | None, gate: FiguresGate, attempts: FR.AuthorAttempts, advanced: bool=False, grounding: Grounding | None=None, sketch: bool=False, tiers: Sequence[str] | None=None, spawn_rich: SpawnRich | None=None, generation: int=0) -> BuildOutcome` ([source](../../../../../../src/learnloop/figures/service.py), line 2234) — At most two author calls, the second told the first's problems; then the figure is stored, shown or failed.
- `class _RichSpawn` ([source](../../../../../../src/learnloop/figures/service.py), line 2604) — RW5d P2b (spec §8.6): starting the rich job of a rich status, after the quick figure is stored (:meth:`after_quick`) or with none (:meth:`only`).
- `_rich_revision(vault: Any, repository: Repository, request: FigureRequest, context: SourceContext, grounding: Grounding, *, previous: Mapping[str, Any], input_hash: str, digest: str | None, asset_id: str | None, generation: int, request_id: str, spawn_rich: SpawnRich | None, gate: FiguresGate, clock: Clock | None) -> BuildOutcome` ([source](../../../../../../src/learnloop/figures/service.py), line 2712) — RW5d P2b (spec §8.5, Codex review F11): "not right?" on a Manim figure.
- `_inherited_extra(repository: Repository, previous: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 2756) — Codex review F4: a rich revision's job payload carries what the learner states its earlier versions' authors were sent were read from (:func:`inherited_learner_inputs`); absent when none was sent, so every other revision's payload is exactly as before.
- `_append_tier(connection: Any, figure_id: str, input_hash: str, verdict: tuple[str, str], author: R.FigureRoute, prompt_version: str, created_at: str, *, left_kind: str='interactive_figure') -> None` ([source](../../../../../../src/learnloop/figures/service.py), line 2766) — The tier judgment's receipt (spec §8.4): the author's status, its reason (``why_not_spec`` or the unsupported reason), the model and prompt.
- `_store_sketch(vault: Any, repository: Repository, request: FigureRequest, context: SourceContext, author: R.FigureRoute, *, sketched: K.CompiledSketch | None, report: Any, problems: Sequence[str], versions: int, asset_id: str | None, input_hash: str, prompt_version: str, figure_id: str, asked: dict[str, Any], clock: Clock | None, gate: FiguresGate, grounding: Grounding, verdict: tuple[str, str] | None, rich_spawn: '_RichSpawn | None'=None) -> BuildOutcome` ([source](../../../../../../src/learnloop/figures/service.py), line 2778) — Store a sketch build (RW5d P2): shown (``illustrative``, its check lines) when verification passed, else ``failed`` with the reason (never shown).
- `_sketch_assumptions(compiled: K.CompiledSketch, span_texts: Mapping[str, str]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/figures/service.py), line 2842) — As :func:`.verify.verified_assumptions`: an unverified quote is dropped, the text stays (AI-written).
- `_ungrounded_sketch(raw: Any) -> Any` ([source](../../../../../../src/learnloop/figures/service.py), line 2853) — RW5d P2 + §8.3 step 3: a sketch built with nothing from the learner's books quotes nothing, whatever the author wrote.
- `_ungrounded(raw: Any) -> Any` ([source](../../../../../../src/learnloop/figures/service.py), line 2871) — RW5d (spec §8.3 step 3): with nothing from the learner's books, the figure is an illustration that quotes nothing, whatever the author wrote: code forces ``kind`` illustrative and drops every source claim and quote (there is no passage to verify them against).
- `_chain_length(repository: Repository, figure_id: str) -> int` ([source](../../../../../../src/learnloop/figures/service.py), line 2919)
- `_root(rows_by_id: Mapping[str, Mapping[str, Any]], row: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/figures/service.py), line 2938)
- `_listed(vault: Any, repository: Repository, extraction_id: str) -> list[tuple[Mapping[str, Any], int, list[dict[str, Any] | None]]]` ([source](../../../../../../src/learnloop/figures/service.py), line 2947) — The rows :func:`list_figures` presents, with no presentation (RW5d P4a, Codex review F3): per version chain, the pick, the chain's length and its placements in this source.
- `_prebuilt_within_budget(vault: Any, repository: Repository, extraction_id: str, picks: list[tuple[Mapping[str, Any], int, list[dict[str, Any] | None]]]) -> list[tuple[Mapping[str, Any], int, list[dict[str, Any] | None]]]` ([source](../../../../../../src/learnloop/figures/service.py), line 2995) — RW5d P5 (spec §6.9; Codex review F11): a prebuilt figure nobody pressed for takes its place in the Reader's cue budget (``[cues] density``, per section; cues off: none), the earliest built first; once pressed it is the learner's like any figure (never cut).
- `_prebuilt_listed(vault: Any, repository: Repository, row: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 3036) — RW5d P5: a prebuilt figure lists while figures ahead of need are on, or once a pressed request took it (then it is the learner's like any figure).
- `_prebuilt_pressed(repository: Repository, row: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 3050)
- `_failed_correction(payload: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None` ([source](../../../../../../src/learnloop/figures/service.py), line 3340) — Codex re-review F14: the failure a correction job stored (its request's row, ``failed``) while it is still the newest version of the figure it corrects: nothing supersedes it and no later correction of that figure was stored.
- `_sketch_outcome(compiled: K.CompiledSketch, index: int) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 3487) — A sketch's prediction, decided by code in the sealed engine (spec §9.3).
- `_queue_formative(vault: Any, repository: Repository, prediction_id: str, *, clock: Clock | None) -> str | None` ([source](../../../../../../src/learnloop/figures/service.py), line 3532)
- `_queued(job_id: str | None, on_queued: Callable[[str], None] | None) -> None` ([source](../../../../../../src/learnloop/figures/service.py), line 3538)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/figures/help|learnloop.figures.help]] — imports `module`; statically calls `advanced_off_row`, `drawable_now`, `rich_row`, `sketch_off_row`, `source_rejected`
- [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] — imports `module`; statically calls `FigureRequest`, `build_prefetch_figure`, `prefetch_plan_waits`, `source_context`
- [[Reference/Modules/learnloop/teacher/visuals|learnloop.teacher.visuals]] — imports `FigureRequest`, `module`; statically calls `FigureRequest`, `figure_view`, `rich_row`
- [[Reference/Modules/learnloop_sidecar/handlers/correspondents|learnloop_sidecar.handlers.correspondents]] — imports `module`; statically calls `section_figures`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `module`; statically calls `FigureRequest`, `anchored`, `attempt_hosted`, `build_figure`, `check_request`, `figure_view`, `list_figures`, `prefetch_pending`, `prefetch_plan_waits`, `rebuild_request`, `record_explanation`, `record_prediction`, `redelivered_view`, `resume_rich_intents`, `retry_rich_job`, `revision_request`, `rich_pending`, `rich_revision_retry`, `rich_row`, `shown_figure`
- [[Reference/Modules/learnloop_sidecar/handlers/lesson|learnloop_sidecar.handlers.lesson]] — imports `module`; statically calls `build_figure`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`, `gate_model_requests`; calls `content_key`, `gate_model_requests`
- [[Reference/Modules/learnloop/ai/plan_fallback|learnloop.ai.plan_fallback]] — imports `module`; calls `quiet`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendLimitExceeded`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `exam_material`; calls `exam_material`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/figures|learnloop.db.stores.figures]] — imports `module`; calls `builds_for_input`, `figure`, `figure_verdicts`, `figures_for_extraction`, `fuller_rows`, `has_tables`, `insert_figure`, `insert_prediction`, `insert_request`, `latest_for_input`, `prediction`, `prediction_for`, `predictions_for_figure`, `request`, `reusable`, `set_explanation`, `set_request_figure`, `shown_verification`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/jobs|learnloop.diagnosis.text_gaps.jobs]] — imports `enqueue_figure_explanation`, `enqueue_figure_prediction`; calls `enqueue_figure_explanation`, `enqueue_figure_prediction`
- [[Reference/Modules/learnloop/figure_admission|learnloop.figure_admission]] — imports `FiguresChanged`, `FiguresGate`, `GROUNDING_PASSAGES`, `advanced_panels_enabled`, `author_learner_state_enabled`, `checked_labels_enabled`, `figures_enabled`, `help_kind_enabled`, `offers_enabled`, `predictions_enabled`, `region_enabled`, `revisions_enabled`, `rich_tiers_enabled`, `show_me_enabled`, `sketch_enabled`, `teacher_visuals_enabled`; calls `FiguresGate`, `advanced_panels_enabled`, `author_learner_state_enabled`, `checked_labels_enabled`, `figures_enabled`, `help_kind_enabled`, `offers_enabled`, `predictions_enabled`, `region_enabled`, `revisions_enabled`, `rich_tiers_enabled`, `show_me_enabled`, `sketch_enabled`, `teacher_visuals_enabled`
- [[Reference/Modules/learnloop/figures/elements|learnloop.figures.elements]] — imports `module`; calls `rewrite_spec`
- [[Reference/Modules/learnloop/figures/labels|learnloop.figures.labels]] — imports `module`; calls `json_fields`, `label_like`, `label_problems`, `strip_json`, `strip_lines`
- [[Reference/Modules/learnloop/figures/learner_state|learnloop.figures.learner_state]] — imports `module`, `state_hash`; calls `anchored_learning_objects`, `enabled`, `read_learner_state`, `state_hash`
- [[Reference/Modules/learnloop/figures/power|learnloop.figures.power]] — imports `background_hold`, `power_state`, `prefetch_switch`; calls `background_hold`, `power_state`, `prefetch_switch`
- [[Reference/Modules/learnloop/figures/prefetch_ledger|learnloop.figures.prefetch_ledger]] — imports `module`; calls `capacity_left`
- [[Reference/Modules/learnloop/figures/protection|learnloop.figures.protection]] — imports `ATTEMPT_HOST_REFS`, `INHERITED_LEARNER_INPUTS_KEY`, `LEARNER_STATE_INPUTS_KEY`, `RICH_INTENT_KEY`, `_learner_inputs_unrecorded`, `_withheld`, `figure_homes`, `inherited_learner_inputs`, `item_passages`, `keys_withheld`, `learner_state_withheld`, `rich_base_keys`, `row_withheld`, `show_me_row`, `withheld_message`; calls `_learner_inputs_unrecorded`, `_withheld`, `figure_homes`, `inherited_learner_inputs`, `item_passages`, `keys_withheld`, `learner_state_withheld`, `rich_base_keys`, `row_withheld`, `show_me_row`, `withheld_message`
- [[Reference/Modules/learnloop/figures/records|learnloop.figures.records]] — imports `module`; calls `AuthorAttempts`, `code`, `sketch_problem`, `spec_problem`
- [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]] — imports `module`; calls `RichBrief`, `job_state`, `manim_tier_ready`, `parse_brief`, `rich_job_for`, `rich_job_for_figure`, `rich_job_for_quick`, `rich_job_for_request`, `rich_job_id_for_quick`, `rich_jobs`, `rich_tiers_switch`, `runtime_digest`, `tiers_allowed`
- [[Reference/Modules/learnloop/figures/routes|learnloop.figures.routes]] — imports `module`; calls `FigureRoute`, `author_prompt`, `author_prompt_version`, `daily_envelope`, `output_model`, `rich_menu`
- [[Reference/Modules/learnloop/figures/sketch|learnloop.figures.sketch]] — imports `module`, `sketch_ready`; calls `parse_author_sketch`, `parse_sketch`, `sketch_ready`
- [[Reference/Modules/learnloop/figures/sketch_engine|learnloop.figures.sketch_engine]] — imports `ENGINE_SHA256`, `ENGINE_VERSION`, `SketchEngine`, `SketchRunError`; calls `SketchEngine`
- [[Reference/Modules/learnloop/figures/sketch_verify|learnloop.figures.sketch_verify]] — imports `VERIFIER_REPORT_VERSION`, `module`; calls `prediction_outcome`, `prediction_target_step`, `verify_sketch`
- [[Reference/Modules/learnloop/figures/source_check|learnloop.figures.source_check]] — imports `module`; calls `check_figure`, `current_row`, `enabled`, `failed_check`, `grammar_row`, `recheck_due`, `record`, `stored_problems`
- [[Reference/Modules/learnloop/figures/spec|learnloop.figures.spec]] — imports `ALL_SPEC_VERSIONS`, `RICH_SPEC_VERSIONS`, `SPEC_VERSIONS`, `module`; calls `advanced_kinds`, `parse_author_spec`, `parse_spec`, `prediction_outcome`
- [[Reference/Modules/learnloop/figures/verify|learnloop.figures.verify]] — imports `module`; calls `Report`, `check_claims`, `quote_in`, `verified_assumptions`, `verify_numerics`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `plan_route`; calls `plan_route`
- [[Reference/Modules/learnloop/reader/reader_cues|learnloop.reader.reader_cues]] — imports `cue_density`, `cues_enabled`, `density_budget`; calls `cue_density`, `cues_enabled`, `density_budget`
- [[Reference/Modules/learnloop/reader/reader_guidance|learnloop.reader.reader_guidance]] — imports `extraction_sections`; calls `extraction_sections`
- [[Reference/Modules/learnloop/reader/span_view|learnloop.reader.span_view]] — imports `build_block_region`; calls `build_block_region`
- [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]] — imports `find_sources_for_caller`; calls `find_sources_for_caller`
- [[Reference/Modules/learnloop/source_retrieval/policy|learnloop.source_retrieval.policy]] — imports `CallerContext`, `derive_policy`; calls `CallerContext`, `derive_policy`
- [[Reference/Modules/learnloop/source_retrieval/reader_tutor|learnloop.source_retrieval.reader_tutor]] — imports `passage_learning_objects`; calls `passage_learning_objects`

### Platform and third-party dependencies

- Standard library: `__future__`, `base64`, `collections`, `contextlib`, `contextvars`, `dataclasses`, `hashlib`, `json`, `logging`, `sqlite3`, `threading`, `types`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/figures/help|learnloop.figures.help]], [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]], [[Reference/Modules/learnloop/teacher/visuals|learnloop.teacher.visuals]], [[Reference/Modules/learnloop_sidecar/handlers/correspondents|learnloop_sidecar.handlers.correspondents]], [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/figure_rich_job_helpers.py](../../../../../../tests/figure_rich_job_helpers.py) — direct import
- [tests/figure_rich_rereview_fixes_helpers.py](../../../../../../tests/figure_rich_rereview_fixes_helpers.py) — direct import
- [tests/identity_pins_helpers.py](../../../../../../tests/identity_pins_helpers.py) — direct import
- [tests/reader_rw5d_p4b_teacher_visuals_helpers.py](../../../../../../tests/reader_rw5d_p4b_teacher_visuals_helpers.py) — direct import
- [tests/rw5c_golden_source.py](../../../../../../tests/rw5c_golden_source.py) — direct import
- [tests/test_batch3_landing.py](../../../../../../tests/test_batch3_landing.py) — direct import
  - `test_iv_with_the_student_off_rw5ds_grounding_retrieval_is_p1s`
- [tests/test_figure_decision_records.py](../../../../../../tests/test_figure_decision_records.py) — direct import
  - `test_a_refused_build_leaves_a_refused_record`
  - `test_a_refused_or_failed_prebuild_is_a_stop_record`
  - `test_a_rich_only_build_names_its_job_and_an_interrupted_build_its_error`
- [tests/test_figure_label_wording.py](../../../../../../tests/test_figure_label_wording.py) — direct import
  - `test_f3_a_stored_label_like_sketch_is_presented_without_that_text`
  - `test_f3_a_stored_label_like_spec_is_presented_without_that_text_listed_and_reused`
  - `test_the_vocabulary_comes_from_the_code_owned_labels`
- [tests/test_figure_offers.py](../../../../../../tests/test_figure_offers.py) — direct import
  - `test_a_build_stops_when_the_advanced_panels_are_switched_off_mid_build`
  - `test_a_selection_build_does_not_stop_for_the_offers_switch`
  - `test_an_offered_build_stops_when_offers_are_switched_off_before_its_request`
  - `test_offers_off_the_contract_has_none_and_the_press_is_refused`
  - `test_the_gate_key_of_an_offered_build_includes_the_offers_switch`
- [tests/test_figure_rich_contract.py](../../../../../../tests/test_figure_rich_contract.py) — direct import
  - `test_a_build_with_manim_on_the_menu_sends_v3_and_records_the_menu`
  - `test_the_reuse_key_names_the_menu_and_the_rich_versions`
  - `test_v3_a_status_off_the_menu_or_with_no_reason_gets_the_second_attempt`
  - `test_with_no_rich_tier_on_the_menu_the_contract_is_v2s_byte_for_byte`
  - `test_without_a_way_to_start_the_job_no_rich_tier_is_offered`
- [tests/test_figure_rich_failed_correction_durable.py](../../../../../../tests/test_figure_rich_failed_correction_durable.py) — direct import
  - `test_codex_f4_a_newer_cancelled_correction_still_speaks_for_the_figure_after_500_newer_rich_jobs`
  - `test_r1_a_failed_correction_of_a_fuller_version_outside_the_window_says_so_too`
  - `test_r1_a_failed_correction_outside_the_job_window_still_says_so`
  - `test_r1_a_newer_correction_in_the_window_still_speaks_for_the_figure`
  - `test_r1_a_replaced_failed_correction_lists_nothing_outside_the_window`
- [tests/test_figure_rich_job.py](../../../../../../tests/test_figure_rich_job.py) — direct import
  - `test_rich_only_shows_the_pending_line_and_never_asks_twice`
- [tests/test_figure_rich_job_golden.py](../../../../../../tests/test_figure_rich_job_golden.py) — direct import
- [tests/test_figure_rich_rereview_fixes.py](../../../../../../tests/test_figure_rich_rereview_fixes.py) — direct import
  - `test_a_different_kind_hashes_apart_from_the_ordinary_correction`
  - `test_a_failed_animation_correction_keeps_the_earlier_version_and_says_so`
  - `test_a_failed_correction_of_a_fuller_version_says_so_too`
  - `test_a_later_correction_replaces_the_failed_line`
- [tests/test_figure_rich_review_fixes.py](../../../../../../tests/test_figure_rich_review_fixes.py) — direct import
  - `test_a_cancelled_rich_only_build_leaves_no_line_and_cannot_be_retried`
  - `test_a_failed_enqueue_is_not_swallowed_and_is_recovered`
  - `test_a_normal_build_or_a_cancelled_one_is_never_restarted_by_recovery`
  - `test_a_revision_needs_the_manim_tier_on_this_computer`
  - `test_a_stop_between_the_quick_figure_and_the_enqueue_is_recovered_once`
  - `test_a_stored_rich_only_failure_lists_once`
  - `test_an_interrupted_rich_only_build_stays_as_a_failed_line_and_can_be_tried_again`
  - `test_not_right_on_a_fuller_version_stays_that_quick_figures_fuller_version`
  - `test_not_right_on_an_animation_goes_to_the_rich_author_with_the_note_and_program`
  - `test_try_a_different_kind_of_figure_reruns_the_tier_choice_with_the_note`
- [tests/test_figure_rich_rpc.py](../../../../../../tests/test_figure_rich_rpc.py) — direct import
  - `test_reading_a_source_starts_a_rich_job_whose_enqueue_never_happened`
- [tests/test_figure_verification.py](../../../../../../tests/test_figure_verification.py) — direct import
  - `test_g23_holds_vacuously_a_reconstruction_is_an_illustration`
- [tests/test_figure_wait_estimate.py](../../../../../../tests/test_figure_wait_estimate.py) — direct import
- [tests/test_figures_codex_review.py](../../../../../../tests/test_figures_codex_review.py) — direct import
  - `test_f7_a_paid_answer_survives_a_crash_before_the_row`
  - `test_f7_a_stored_failure_is_a_new_generation_that_asks_afresh`
  - `test_f7_identical_concurrent_builds_join_one_build`
- [tests/test_figures_final_round.py](../../../../../../tests/test_figures_final_round.py) — direct import
  - `test_a_provider_that_cannot_isolate_is_refused_before_any_request`
  - `test_the_view_sends_closed_property_check_keys_only`
- [tests/test_figures_fix_round2.py](../../../../../../tests/test_figures_fix_round2.py) — direct import
  - `test_f7_a_build_committed_between_the_reads_is_reused_inside_the_lock`
- [tests/test_figures_help_codex_review.py](../../../../../../tests/test_figures_help_codex_review.py) — direct import
  - `test_f5_an_attempt_builds_admission_key_carries_the_switch`
  - `test_f7_the_trace_reads_only_what_this_attempt_wrote_as_it_stood_at_submit`
- [tests/test_figures_prefetch.py](../../../../../../tests/test_figures_prefetch.py) — direct import
  - `test_a_background_build_stops_off_mains_before_any_request`
  - `test_a_prebuilt_figure_lists_only_while_on_or_once_pressed`
  - `test_origin_prefetch_is_refused_from_every_rpc_and_outside_the_service`
- [tests/test_figures_prefetch_review_fixes.py](../../../../../../tests/test_figures_prefetch_review_fixes.py) — direct import
  - `test_f10_a_rich_only_prebuild_shows_no_pending_or_failure_line`
  - `test_f11_unpressed_prebuilt_lines_keep_to_the_cue_budget`
  - `test_f16_a_prebuilds_rich_request_rechecks_the_switch_after_waiting_for_foreground_work`
  - `test_f17_a_plan_wait_is_not_retried_off_mains_or_switched_off`
  - `test_f17_a_speculative_prebuilds_plan_wait_is_retried_by_the_reader_read`
  - `test_f18_a_prebuilds_rich_job_is_pending_on_mains_only`
  - `test_f18_an_unstarted_decision_is_pending_only_while_a_pass_runs_and_never_on_battery`
  - `test_f2_a_queued_prebuild_rich_job_is_not_sent_once_its_route_is_metered`
  - `test_f2_a_quick_prebuild_on_a_metered_author_route_sends_nothing`
  - `test_f3_a_recovered_prebuild_intent_keeps_its_guards`
  - `test_f6_a_prebuilds_rich_job_checks_the_render_minutes_when_it_starts`
  - `test_f7_a_prebuilds_rich_job_in_flight_holds_the_next_prebuild_and_the_judge`
  - `test_f7_a_prebuilds_rich_job_yields_to_foreground_work`
  - `test_f7_a_quick_prebuild_stops_before_its_request_while_the_learner_works`
  - `test_r1_a_pressed_fuller_keeps_its_pending_line_and_is_not_speculative`
  - `test_r1_a_queued_speculative_fuller_is_marked_speculative`
  - `test_r1_an_unqueued_speculative_fuller_is_not_pending_on_battery`
  - `test_r1_an_unqueued_speculative_fuller_is_not_pending_switched_off_or_held_out`
- [tests/test_figures_rw5b_review.py](../../../../../../tests/test_figures_rw5b_review.py) — direct import
  - `test_the_reuse_key_never_names_the_origin_and_keeps_rw5as_keys`
- [tests/test_figures_scope_redesign.py](../../../../../../tests/test_figures_scope_redesign.py) — direct import
  - `test_a_build_makes_no_request_after_its_configuration_changes`
  - `test_a_stored_verified_row_is_rendered_as_an_illustration`
  - `test_no_figure_is_labelled_checked`
  - `test_the_build_control_makes_every_request`
- [tests/test_figures_show_me.py](../../../../../../tests/test_figures_show_me.py) — direct import
  - `test_a_goal_alone_is_grounded_in_the_books_and_lands_where_the_learner_was`
  - `test_nothing_found_is_built_anyway_as_an_illustration_not_from_your_books`
- [tests/test_figures_show_me_codex_review.py](../../../../../../tests/test_figures_show_me_codex_review.py) — direct import
  - `test_f1_a_reuse_after_show_me_is_switched_off_is_refused`
  - `test_f1_switching_off_during_grounding_stops_its_calls_and_the_author`
  - `test_f1_the_control_admits_every_grounding_call`
  - `test_f7_a_reuse_whose_request_cannot_be_recorded_fails_retryably_and_the_retry_reuses`
- [tests/test_followups_batch5_lesson.py](../../../../../../tests/test_followups_batch5_lesson.py) — direct import
  - `test_e_the_visual_builder_decides_by_the_lesson_gate_alone`
- [tests/test_followups_batch6_prefetch_plan_wait.py](../../../../../../tests/test_followups_batch6_prefetch_plan_wait.py) — direct import
  - `test_the_runtime_wires_the_paced_requeue`
- [tests/test_followups_batch6_review_fixes.py](../../../../../../tests/test_followups_batch6_review_fixes.py) — direct import
  - `test_f1_the_readers_read_never_requeues_it_either`
  - `test_f1_the_worker_rechecks_before_the_store`
  - `test_f1_the_worker_stops_a_requeued_prebuild_before_any_request`
- [tests/test_followups_batch6_verify_fixes.py](../../../../../../tests/test_followups_batch6_verify_fixes.py) — direct import
  - `test_v1_an_answered_planned_item_lets_the_retry_through`
  - `test_v1_an_unreadable_stored_plan_fails_closed_everywhere`
  - `test_v1_only_todays_plan_holds_an_item`
  - `test_v1_the_reader_and_the_pass_read_the_same_rule`
  - `test_v1_the_readers_read_never_requeues_a_prebuild_a_later_plan_holds`
  - `test_v1_the_worker_rechecks_the_plan_before_the_store`
  - `test_v1_the_worker_stops_a_requeued_prebuild_a_later_plan_holds_before_any_request`
- [tests/test_followups_batch7_prefetch_capped_resume.py](../../../../../../tests/test_followups_batch7_prefetch_capped_resume.py) — direct import
  - `test_a_capped_decision_is_coming_only_while_the_budget_has_room`
  - `test_a_figure_the_learner_pressed_for_meanwhile_is_not_counted_as_the_prebuilds`
- [tests/test_followups_nov2_figure_provenance.py](../../../../../../tests/test_followups_nov2_figure_provenance.py) — direct import
  - `test_a_fresh_figure_for_a_marked_row_is_reused_after_the_panels_are_switched`
  - `test_a_marked_quick_figure_with_no_record_is_withheld`
  - `test_a_press_of_the_same_input_never_backfills_the_marked_row_and_builds_afresh`
  - `test_a_quick_figure_whose_learner_inputs_became_protected_is_not_presented`
  - `test_a_revision_inherits_its_bases_learner_state_protection`
  - `test_a_rich_revision_with_nothing_inherited_carries_no_record`
- [tests/test_learner_data_relax_2.py](../../../../../../tests/test_learner_data_relax_2.py) — direct import
  - `test_a_rich_only_figure_whose_learner_inputs_became_protected_is_never_reused`
  - `test_switched_off_the_payload_prompt_and_key_are_the_predecessors_byte_for_byte`
  - `test_the_learner_state_reaches_the_author_and_protected_work_never_does`
  - `test_the_reuse_key_and_prompt_version_name_the_state_only_when_non_empty`
  - `test_the_rich_author_receives_what_the_figure_author_received`
  - `test_the_switch_is_in_the_build_and_rich_keys`
- [tests/test_reader_rw5d_p4a_figures_follow.py](../../../../../../tests/test_reader_rw5d_p4a_figures_follow.py) — direct import
  - `test_an_unreadable_figure_store_offers_no_figure_and_keeps_the_correspondents`
  - `test_the_quiet_read_never_reverifies_an_outdated_sketch_or_writes`
- [tests/test_reader_rw5d_p4b_teacher_visuals.py](../../../../../../tests/test_reader_rw5d_p4b_teacher_visuals.py) — direct import
  - `test_a_lesson_figure_never_spawns_a_rich_job`
  - `test_a_visual_turn_builds_a_teacher_figure_shown_inline_with_its_predictions_suppressed`
  - `test_switching_visuals_off_hides_a_lessons_figures_and_stops_a_pending_one`
  - `test_the_teacher_origin_is_the_lesson_services_only`
- [tests/test_rw5c_judgments.py](../../../../../../tests/test_rw5c_judgments.py) — direct import
  - `test_at_build_a_failure_leaves_no_figure_row_and_no_verdict`
- [tests/test_rw5c_labels.py](../../../../../../tests/test_rw5c_labels.py) — direct import
  - `test_a_sketch_view_has_no_elements_or_source_check`
- [tests/test_rw5c_recheck.py](../../../../../../tests/test_rw5c_recheck.py) — direct import
  - `test_a_difference_found_at_recheck_gives_the_failed_state_with_rebuild`
  - `test_a_kept_build_result_read_after_the_switch_turns_off_shows_no_label`
  - `test_a_prebuilt_figure_nobody_pressed_for_that_differs_lists_nothing`
  - `test_section_figures_leave_a_rejected_figure_out`
  - `test_the_reuse_key_is_unchanged_without_a_source_check_id`
- [tests/test_rw5c_source_check.py](../../../../../../tests/test_rw5c_source_check.py) — direct import
  - `test_build_key_holds_the_switch_and_the_reuse_key_does_not`
  - `test_the_switch_off_at_the_store_writes_nothing`
  - `test_the_switch_off_between_the_sandbox_and_the_second_attempt_stops_the_build`
- [tests/test_rw5c_switch_off.py](../../../../../../tests/test_rw5c_switch_off.py) — direct import
  - `test_nothing_reads_the_ledger_while_the_switch_is_off`
- [tests/test_sketch_service.py](../../../../../../tests/test_sketch_service.py) — direct import
  - `test_a_report_from_an_older_verifier_is_reverified_before_it_is_shown`
  - `test_a_report_from_this_verifier_and_engine_is_not_reverified`
  - `test_a_sketch_answer_is_verified_stored_and_shown_with_its_check_lines`
  - `test_a_sketch_built_with_nothing_from_the_books_quotes_nothing`
  - `test_a_verifier_version_bump_reverifies_a_current_engines_report`
  - `test_an_engine_reverification_is_a_verifier_judgment_recorded_once`
  - `test_an_engine_upgrade_reverifies_with_no_model_call`
  - `test_off_the_contract_prompt_and_key_are_rw5bs_byte_for_byte`

## Modification guidance

- Make changes here when the responsibility remains service within learnloop.figures; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
