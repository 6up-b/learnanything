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
| Source lines | 3905 |
| Owning package | [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class FigureRefused(Exception)` ([source](../../../../../../src/learnloop/figures/service.py), line 257) — A request the Reader may not make (``code``: ``figures_disabled``, ``exam_material``, ``region_disabled``, ``revisions_disabled``, ``predictions_disabled``, ``offers_disabled`` and ``advanced_disabled`` (RW5b), ``not_found``, ``validation_error``, ``no_image_input``, ``region_un…
  - `__init__(self, code: str, message: str) -> None` (line 265; internal)
- `class FigureRequest` ([source](../../../../../../src/learnloop/figures/service.py), line 272)
- `class SourceContext` ([source](../../../../../../src/learnloop/figures/service.py), line 329)
- `class Grounding` ([source](../../../../../../src/learnloop/figures/service.py), line 341) — Where a request's source text comes from (spec §8.3): ``anchor`` (the learner chose the passage), ``retrieved`` (found in their books for the goal) or ``none`` (nothing found: an illustration that quotes nothing).
- `attempt_hosted(request: 'FigureRequest') -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 353) — RW5d P3: a request made on an attempt host (practice, feedback or the workbench: its verified host references name an item or attempt).
- `lesson_hosted(request: 'FigureRequest') -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 360) — RW5d P4b: a lesson's visual (origin ``teacher``; its host is the lesson, so it has no reading position and no home: it shows in the lesson only).
- `teacher_visuals_switch(vault: Any) -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 367) — RW5d P4b: ``teacher.visuals`` (the teacher's manipulatives).
- `prediction_home(row: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/figures/service.py), line 374) — The extraction a figure's prediction is recorded under: its home, or (RW5d P3, an attempt host's figure with no home) the first book it was grounded in; None for a homeless illustration (its predictions are kept with no extraction: Codex review F9).
- `anchored(request: 'FigureRequest') -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 386) — A request with a passage (a selection or a region).
- `show_me_input(request: 'FigureRequest') -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 392) — RW5d: a request whose goal or grounding the author is sent (a goal, or no passage).
- `enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 399) — ``figures.enabled``: the one predicate (:func:`learnloop.figure_admission.figures_enabled`).
- `build_key(vault: Any) -> tuple[Any, ...]` ([source](../../../../../../src/learnloop/figures/service.py), line 405) — What a build depends on, compared before every request it makes (:class:`~learnloop.figure_admission.FiguresGate`): the vault, the switch, the author route as configured, the day's cap and the price, and (RW5b) whether the advanced panels are on (the author's prompt depends on i…
- `offer_build_key(vault: Any) -> tuple[Any, ...]` ([source](../../../../../../src/learnloop/figures/service.py), line 424) — An offered build's key (origin ``library`` | ``tutor``): :func:`build_key` and ``figures.offers_enabled``, so switching offers off stops it.
- `offered(request: 'FigureRequest') -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 431) — A build an offer started (a "not right?" version of an offered figure is a revision: ``figures.revisions_enabled`` governs it, not the offers).
- `show_me_build_key(vault: Any) -> tuple[Any, ...]` ([source](../../../../../../src/learnloop/figures/service.py), line 438) — A show-me build's key: :func:`build_key` and ``figures.show_me_enabled``.
- `key_for(request: 'FigureRequest')` ([source](../../../../../../src/learnloop/figures/service.py), line 444)
- `predictions_enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 478)
- `region_enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 482)
- `revisions_enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 486)
- `advanced_enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 490) — RW5b's panels (``figures.advanced_panels_enabled``).
- `figure_offers_enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 496) — RW5b's offers (``figures.offers_enabled``).
- `show_me_enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 502) — RW5d's "show me" (``figures.show_me_enabled``; :func:`learnloop.figure_admission.show_me_enabled`).
- `help_enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 508) — RW5d P3: ``figures.help_kind_enabled`` (:func:`learnloop.figure_admission.help_kind_enabled`).
- `sketch_switch(vault: Any) -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 516) — RW5d P2's switch (``figures.sketch_enabled`` under ``figures.enabled``).
- `sketch_enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 522) — The sketch tier as offered on this machine: its switch, and the engine present with its pinned digest (spec §7.2: an unavailable tier is left out of the author's menu).
- `rich_enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 534) — RW5d P2b's switch (``figures.rich_tiers_enabled`` under ``figures.enabled``).
- `rich_row(row: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 540) — RW5d P2b: a stored rich figure (a Manim figure).
- `withheld_message(vault: Any, repository: Repository, extraction_id: str, span_ids: Sequence[str]) -> str | None` ([source](../../../../../../src/learnloop/figures/service.py), line 554) — The refusal when any of the spans (or the whole reading) is exam or held-out material (``exam_material(...).withheld``), else None: the shared :func:`~learnloop.content.sources.exam_material.spans_withheld`, which learner-text gaps ask too (fix round 2, F1).
- `keys_withheld(vault: Any, repository: Repository, keys: Sequence[Sequence[str]]) -> str | None` ([source](../../../../../../src/learnloop/figures/service.py), line 581) — RW5d: the refusal when any ``(extraction_id, span_id)`` (a retrieved passage in any source, or its neighbour) is held out now, else None: the one predicate, asked per source.
- `row_withheld(vault: Any, repository: Repository, row: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/figures/service.py), line 597) — A stored figure's held-out refusal now, else None: its home's spans and (RW5d) every retrieved passage it was built from, across sources.
- `learner_state_withheld(vault: Any, repository: Repository, row: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/figures/service.py), line 624) — Why a stored figure may not go out now because of the learner state an author of it was sent, or None (follow-ups Nov 2, ruling R1 of learner data-relax 2: exam-material protection, not privacy).
- `inherited_learner_inputs(repository: Repository, row: Mapping[str, Any]) -> list[Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 709) — What every learner state the authors of ``row`` and of the figures it was made from were sent was read from (Codex review F4): a revision's rich job carries it, so the job checks it at admission, before every request and before it stores, though the revision sends no learner sta…
- `figure_homes(repository: Repository, row: Mapping[str, Any]) -> list[tuple[str, str]] | None` ([source](../../../../../../src/learnloop/figures/service.py), line 771) — Where a figure with no passage lands (:func:`learnloop.figure_admission.figure_home_keys`): every recorded request's reading position; empty for an anchored figure.
- `show_me_row(row: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 781) — A figure built from a goal or with no anchor (RW5d): absent while ``figures.show_me_enabled`` is off.
- `figure_withheld(vault: Any, repository: Repository, figure_id: str) -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 787) — Whether a stored figure may not go out now (its row is gone, or any span it was built from is held out, or (RW5d) it is a show-me figure while show me is off).
- `source_context(vault: Any, repository: Repository, request: FigureRequest) -> SourceContext` ([source](../../../../../../src/learnloop/figures/service.py), line 805)
- `passages_context(vault: Any, repository: Repository, grounding: Grounding) -> SourceContext` ([source](../../../../../../src/learnloop/figures/service.py), line 839) — RW5d: the retrieved passages as the author is sent them (spec §8.2, §8.3): each kept block with the paragraphs around it (held-out ones left out), keyed ``extraction_id:span_id`` so a quote is verified against the right block of the right book.
- `ground(vault: Any, repository: Repository, request: FigureRequest, *, find: FindSources | None=None) -> Grounding` ([source](../../../../../../src/learnloop/figures/service.py), line 947) — A request's grounding (spec §8.3).
- `crop_image(repository: Repository, request: FigureRequest, context: SourceContext) -> tuple[tuple[str, bytes] | None, str | None, list[float] | None]` ([source](../../../../../../src/learnloop/figures/service.py), line 1013) — ``(image, asset span, clipped region box)``: a region's crop only, or the figure block's crop; nothing for a selection with no figure.
- `shown_row(row: Mapping[str, Any]) -> Mapping[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 1038) — The row as RW5a may show it: nothing in RW5a produces "verified", and a stored one (from a build before the owner's scope decision of 2026-10-21) is shown as the illustration RW5a's rules make it.
- `advanced_off_row(vault: Any, row: Mapping[str, Any]) -> Mapping[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 1068) — RW5b: a shown figure that uses a heat map, vector field, trajectory or iterated map, while ``figures.advanced_panels_enabled`` is off, is the unsupported-kind state ("can't draw this yet"); its spec never goes out.
- `sketch_row(row: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 1086) — RW5d P2: a stored sketch.
- `sketch_off_row(vault: Any, row: Mapping[str, Any]) -> Mapping[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 1092) — RW5d P2: a shown sketch while ``figures.sketch_enabled`` is off (or the engine can't run here) is the unsupported-kind state ("can't draw this yet"); its program never goes out.
- `rich_off_row(vault: Any, row: Mapping[str, Any]) -> Mapping[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 1104) — RW5d P2b: a shown rich figure while ``figures.rich_tiers_enabled`` is off is the unsupported-kind state ("can't show this kind here"); its program and video never go out.
- `reverify_hash(spec_json: str, engine_sha256: str, verifier_version: str | None=None) -> str` ([source](../../../../../../src/learnloop/figures/service.py), line 1125)
- `sketch_rechecked(row: Mapping[str, Any], repository: Repository | None=None) -> Mapping[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 1176) — Spec §8.5, engine upgrades: a shown sketch verified under another engine, or (Codex review F11, round 3) by another verifier version (:data:`.sketch_verify.VERIFIER_REPORT_VERSION`: a report made before a verification fix may carry a check line the fixed verifier would not give)…
- `worded_row(row: Mapping[str, Any]) -> Mapping[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 1223) — Spec §9b.4 when a stored figure is presented (Reader follow-ups Nov 1b, Codex review F3): a figure stored before the free-text label rule (or by any path that skipped it) is shown, listed and reused without its label-like text, as :mod:`.labels` rules for an answer that still vi…
- `drawable_now(vault: Any, row: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 1258) — A stored figure that can be drawn as configured now (RW5b's panels and RW5d P2's sketch tier both on when it needs them).
- `property_checks(report: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/figures/service.py), line 1265) — The closed keys of the checks a shown figure passed (§8.3 steps 1-2).
- `figure_view(vault: Any, repository: Repository, row: Mapping[str, Any], *, versions: int=1, home: Mapping[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 1325) — A figure as the Reader shows it.
- `source_rejected(vault: Any, repository: Repository, row: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 1486) — RW5c (§6.6): the figure's newest check, at the current certification version and with the switch on, proved a stated claim different.
- `rebuild_request(vault: Any, repository: Repository, base: Mapping[str, Any]) -> FigureRequest` ([source](../../../../../../src/learnloop/figures/service.py), line 1556) — *Rebuild* of a figure whose stated claim differs (§6.6, Codex review F3): a new version through the revision path, never a reuse of the rejected row.
- `redelivered_view(vault: Any, repository: Repository, view: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 1585) — A figure view kept since its build (a finished job's result, read again through ``reader.figure_job``) as it may go out now (follow-ups Nov 2): its fuller version is rebuilt from the current rows (:func:`fuller_state`), so a fuller version whose learner inputs became protected s…
- `fuller_state(vault: Any, repository: Repository, row: Mapping[str, Any]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/figures/service.py), line 1619) — RW5d P2b (spec §6.8, §8.6): the fuller version of a quick figure, or None when it has none: ``ready`` (with the rich figure's view), ``failed`` (code's reason; the quick version stays), ``pending`` (the job's phase), ``waiting_for_plan`` or ``cancelled``.
- `request_hash(request: FigureRequest, context: SourceContext, image_digest: str | None, *, advanced: bool=False, grounding: Grounding | None=None, sketch: bool=False, tiers: Sequence[str] | None=None, rich_runtime: str | None=None, learner_state: Mapping[str, Any] | None=None) -> str` ([source](../../../../../../src/learnloop/figures/service.py), line 1706) — The reuse key: the spec and prompt versions (RW5b's panels have their own prompt version, so RW5a's hashes are unchanged while they are off) and everything the author is sent (never the origin: :data:`REUSE_ORIGIN`).
- `check_request(vault: Any, repository: Repository, request: FigureRequest) -> FigureRequest` ([source](../../../../../../src/learnloop/figures/service.py), line 1942) — Validate a request and refuse held-out material, on the request path, before any job or call (the handler's first step; the build repeats it).
- `class BuildOutcome` ([source](../../../../../../src/learnloop/figures/service.py), line 1994)
- `build_figure(vault: Any, repository: Repository, request: FigureRequest, *, author_client: Any | None=None, clock: Clock | None=None, live_vault: Callable[[], Any] | None=None, find: FindSources | None=None, spawn_rich: SpawnRich | None=None) -> BuildOutcome` ([source](../../../../../../src/learnloop/figures/service.py), line 2062) — Build one figure (module docstring).
- `retry_rich_job(vault: Any, repository: Repository, job_id: str) -> str` ([source](../../../../../../src/learnloop/figures/service.py), line 2291) — Codex review F9: the error code of a rich job that ended with no row and may be requeued (failed, not waiting for the plan, never cancelled), or :class:`FigureRefused`.
- `ensure_rich_job(repository: Repository, spawn: SpawnRich, payload: dict[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/figures/service.py), line 2744) — Start a quick figure's rich job unless it already has one (in any state: a cancelled one stays cancelled) or a stored fuller version (Codex review F8).
- `resume_rich_intents(vault: Any, repository: Repository, extraction_id: str, spawn: SpawnRich | None) -> int` ([source](../../../../../../src/learnloop/figures/service.py), line 2763) — Codex review F8: start the rich job of every shown quick figure of this source whose intent committed but whose job was never enqueued (the sidecar stopped between the two, or the enqueue failed).
- `revision_request(repository: Repository, base: Mapping[str, Any], note: str) -> FigureRequest` ([source](../../../../../../src/learnloop/figures/service.py), line 3096) — "Not right?" on a stored figure: the same input with the note.
- `prefetch_pending(vault: Any, repository: Repository, extraction_id: str, *, pass_running: bool=False) -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 3257) — RW5d P5 (Codex review F11): whether a prebuild for this source is coming now: the Reader then reads its figures again, paced, so a completed prebuild appears without a reopen.
- `stored_plan_open_items(repository: Repository, *, clock: Clock | None=None) -> list[str]` ([source](../../../../../../src/learnloop/figures/service.py), line 3306) — The ids of the items today's latest stored plan holds open: planned, and not yet done, skipped or displaced.
- `item_passages(vault: Any, repository: Repository, *, clock: Clock | None=None) -> tuple[frozenset[tuple[str, str]], frozenset[str]] | None` ([source](../../../../../../src/learnloop/figures/service.py), line 3326) — RW5d P5 (spec §10b.2, G-SM29): the passages no prebuild may send or show now: every passage (``corpus.item_exclusions``: its exercise, solution or worked answer, whatever the relation) of an item under a live administration (:data:`LIVE_ADMINISTRATION_REASONS`) or that the store…
- `rich_base_keys(base: Mapping[str, Any]) -> list[tuple[str, str]]` ([source](../../../../../../src/learnloop/figures/service.py), line 3374) — Every ``(extraction_id, span_id)`` a rich job's saved context names: its passage, the paragraphs around it the author was sent, its region, its retrieved passages and its home (the spans ``rich._withheld`` checks).
- `rich_base_item_protected(vault: Any, repository: Repository, base: Mapping[str, Any], *, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/figures/service.py), line 3393) — :data:`ITEM_PASSAGE_PROTECTED` when a rich job's saved context touches a passage :func:`item_passages` protects now, or the protection can't be read (fail closed); else None.
- `prefetch_plan_waits(vault: Any, repository: Repository, extraction_id: str | None, *, request_ids: Collection[str] | None=None, clock: Clock | None=None) -> list[str]` ([source](../../../../../../src/learnloop/figures/service.py), line 3407) — RW5d P5 (Codex re-review F17): this source's speculative prebuild rich jobs waiting for the plan, newest per input, whose retry is admissible now: figures ahead of need on, this machine on mains, and the passage not held out.
- `build_prefetch_figure(vault: Any, repository: Repository, request: FigureRequest, *, author_client: Any | None=None, clock: Clock | None=None, live_vault: Callable[[], Any] | None=None, find: FindSources | None=None, spawn_rich: SpawnRich | None=None) -> BuildOutcome` ([source](../../../../../../src/learnloop/figures/service.py), line 3459) — RW5d P5: one background build for the prefetch service (spec §10b), under ``quiet()``: no offer, no grant (plan down: it waits).
- `list_figures(vault: Any, repository: Repository, extraction_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/figures/service.py), line 3479) — The figures of one source as the Reader shows them: per version chain, the newest shown version (else the newest failed or unsupported one), of the current spec version, and never one whose passage is held out now.
- `section_figures(vault: Any, repository: Repository, extraction_id: str, section_of: Callable[[str], str | None]) -> dict[str, list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/figures/service.py), line 3493) — RW5d P4a (spec §10.2): the kept figures of one reading by the section their anchor is in, for the correspondents read (figures follow the section).
- `rich_pending(vault: Any, repository: Repository, extraction_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/figures/service.py), line 3546) — RW5d P2b (spec §6.8): the rich builds with no quick figure for this source that have not ended (pending, or waiting for the plan), each as the pending line under its passage; empty while the rich tiers are off.
- `rich_revision_retry(vault: Any, repository: Repository, job_id: str) -> FigureRequest | None` ([source](../../../../../../src/learnloop/figures/service.py), line 3666) — Codex re-review F14: "try again" on a correction of an animation whose job stored a failure (the line :func:`rich_pending` lists): the same correction (the figure it corrects, the learner's note), built afresh.
- `shown_figure(vault: Any, repository: Repository, figure_id: str) -> tuple[dict[str, Any], Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 3695) — A figure that may be shown now: shown verification, a current spec version, its passage not held out.
- `record_prediction(vault: Any, repository: Repository, figure_id: str, index: int, answer: str, *, clock: Clock | None=None, on_queued: Callable[[str], None] | None=None, assist_id: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 3735) — The learner's prediction, its observed before/after readout and whether it matched (code decides).
- `record_explanation(vault: Any, repository: Repository, prediction_id: str, text: str, *, clock: Clock | None=None, on_queued: Callable[[str], None] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 3807) — "What changed, and why?" (optional, once).

### Module constants

- `ORIGINS` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 198)
- `RESERVED_ORIGINS` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 199)
- `SERVICE_ORIGINS` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 201)
- `LESSON_TIERS` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 205)
- `ATTEMPT_HOST_REFS` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 208)
- `OFFER_ORIGINS` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 210)
- `GOAL_AUTHORS` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 213)
- `GOAL_CHARS` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 214)
- `GROUNDING_PASSAGES` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 216)
- `GROUNDINGS` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 217)
- `SHOW_ME_VERSION` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 218)
- `REQUEST_PREFIX` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 219)
- `NOT_FROM_BOOKS_LABEL` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 222)
- `FIGURE_BLOCK_TYPES` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 223)
- `CONTEXT_BLOCKS` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 225)
- `PASSAGE_CHARS` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 226)
- `CONTEXT_CHARS` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 227)
- `NOTE_CHARS` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 228)
- `EXPLANATION_CHARS` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 229)
- `ANSWER_CHARS` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 230)
- `LEDGER_TASK` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 231)
- `RECONSTRUCTION_REASON` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 234)
- `PREDICTION_PREFIX` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 235)
- `FIGURE_PREFIX` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 236)
- `LABELS` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 238)
- `SPEC_VERSIONS` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 242)
- `RICH_SPEC_VERSIONS` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 245)
- `ALL_SPEC_VERSIONS` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 246)
- `SKETCH_LABEL` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 248)
- `SKETCH_UNCHECKED_LABEL` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 249)
- `SKETCH_NOT_FROM_BOOKS_LABEL` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 250)
- `SKETCH_OFF_KIND` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 252)
- `ENGINE_CHANGED_REASON` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 253)
- `TIER_LEDGER_TASK` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 254)
- `ADVANCED_OFF_KIND` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 547)
- `LEARNER_STATE_UNRECORDED` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 663)
- `LEARNER_INPUTS_RECORDED` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 756)
- `PROPERTY_CHECKS` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 1053)
- `_RECHECKED` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 1117)
- `_RECHECKED_GUARD` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 1118)
- `REVERIFY_VERSION` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 1122)
- `REUSE_ORIGIN` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 1703)
- `_PREFETCH_BUILD` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 1812)
- `PREFETCH_GOAL_AUTHORS` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 1814)
- `PREFETCH_AUTHOR_NOT_PLAN` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 2099)
- `_BUILDS_GUARD` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 2318)
- `_BUILDS` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 2319)
- `STORAGE_BUSY` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 2372)
- `_LOG` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 2737)
- `RICH_INTENT_KEY` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 2740)
- `_RICH_SPAWN_GUARD` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 2741)
- `LIVE_ADMINISTRATION_REASONS` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 3303)
- `ITEM_PASSAGE_PROTECTED` ([src/learnloop/figures/service.py](../../../../../../src/learnloop/figures/service.py), line 3370)

### Explicit exports

`__all__` declares:

- `BuildOutcome`
- `FigureRefused`
- `FigureRequest`
- `GROUNDING_PASSAGES`
- `Grounding`
- `ITEM_PASSAGE_PROTECTED`
- `LABELS`
- `LESSON_TIERS`
- `LIVE_ADMINISTRATION_REASONS`
- `NOT_FROM_BOOKS_LABEL`
- `SERVICE_ORIGINS`
- `anchored`
- `build_figure`
- `rebuild_request`
- `source_rejected`
- `check_request`
- `enabled`
- `figure_view`
- `figure_homes`
- `figure_withheld`
- `ground`
- `item_passages`
- `keys_withheld`
- `lesson_hosted`
- `revision_request`
- `row_withheld`
- `learner_state_withheld`
- `redelivered_view`
- `show_me_enabled`
- `show_me_input`
- `fuller_state`
- `ensure_rich_job`
- `resume_rich_intents`
- `retry_rich_job`
- `rich_enabled`
- `rich_off_row`
- `rich_pending`
- `rich_base_item_protected`
- `rich_base_keys`
- `stored_plan_open_items`
- `rich_row`
- `sketch_enabled`
- `sketch_off_row`
- `sketch_rechecked`
- `sketch_row`
- `list_figures`
- `predictions_enabled`
- `record_explanation`
- `record_prediction`
- `region_enabled`
- `revisions_enabled`
- `section_figures`
- `shown_figure`
- `teacher_visuals_switch`
- `withheld_message`

## Internal implementation anchors

- `_key_for(request: 'FigureRequest')` ([source](../../../../../../src/learnloop/figures/service.py), line 466)
- `_switch(vault: Any, name: str) -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 474)
- `_figure_spans(row: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/figures/service.py), line 565) — Every span a figure was built from: the selection, the region's and the crop's block, and the complete manifest of what the author was sent (the paragraphs around it too: a figure may show a neighbour's quoted assumption; Codex review F1).
- `_rich_intent(row: Mapping[str, Any]) -> Any` ([source](../../../../../../src/learnloop/figures/service.py), line 667)
- `_learner_inputs_unrecorded(row: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 672) — Codex review F3: the row's author was sent a learner state (the prompt version's ``+learner-v1``) and neither its report nor its rich intent keeps what that state was read from.
- `_lineage(repository: Repository, row: Mapping[str, Any]) -> list[Mapping[str, Any]] | None` ([source](../../../../../../src/learnloop/figures/service.py), line 687) — The figure and every figure it was made from (``supersedes_id``, ``fuller_of_id``), read from the current rows; None without the tables.
- `_unrecorded_occupant(vault: Any, connection: Any, input_hash: str) -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 730) — Codex re-review F5: whether this input's reusable figure (its quick figure, or a rich figure built with no quick one) is a marked row that keeps no record of what its author's learner state was read from.
- `_recorded_input_key(input_hash: str) -> str` ([source](../../../../../../src/learnloop/figures/service.py), line 742) — Codex re-review F5: the key a fresh build of an input takes when that input's figure is a marked row with no record.
- `_with_learner_inputs(report: Mapping[str, Any], request: 'FigureRequest') -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 759) — A quick figure's report with what its author's learner state was read from (follow-ups Nov 2: the record rich rows keep since learner data-relax 2, ``RICH.LEARNER_STATE_INPUTS_KEY``; never shown or sent to a model), so the figure is rechecked whenever it goes out.
- `_find_sources(vault: Any, repository: Repository, query: str, **kwargs: Any) -> Any` ([source](../../../../../../src/learnloop/figures/service.py), line 895)
- `_reading_learning_objects(vault: Any, repository: Repository, reading_at: Mapping[str, Any] | None) -> list[str]` ([source](../../../../../../src/learnloop/figures/service.py), line 901) — The learning objects of the passage the learner was reading (retrieval context only).
- `_passage_ref(hit: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 915)
- `_with_sources(repository: Repository, passages: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/figures/service.py), line 921) — Each passage with its source's id and title (Codex review F8: the Reader's citation chips peek in this book and open another as a detour, which needs the source).
- `_decode(render: str | None) -> tuple[str, bytes] | None` ([source](../../../../../../src/learnloop/figures/service.py), line 1003)
- `_advanced_kinds(row: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/figures/service.py), line 1057) — The RW5b panel kinds a stored figure's spec uses (none when it has no spec).
- `_stored_verifier(row: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/figures/service.py), line 1132) — The verifier report version a stored row's report was made by (None: before the version existed).
- `_record_reverification(repository: Repository | None, row: Mapping[str, Any], cached: Mapping[str, Any], engine_sha256: str) -> None` ([source](../../../../../../src/learnloop/figures/service.py), line 1140) — Codex review F8: an engine re-verification is a verifier verdict, so it is appended to ``judgment_ledger`` (task ``figure_verified``, judge ``verifier``) before the figure is delivered, superseding the figure's last verdict on that question.
- `_label(row: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/figures/service.py), line 1275)
- `_prediction_view(found: Mapping[str, Any] | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/figures/service.py), line 1302)
- `_anchor_span(row: Mapping[str, Any], asked: Mapping[str, Any] | None, home: Mapping[str, Any] | None) -> str | None` ([source](../../../../../../src/learnloop/figures/service.py), line 1313) — Where a figure shows: under the selection's last block; a region's figure (no selected text) under the region's block (Codex review F2); RW5d: a figure with no passage under the passage the learner was reading (``home``, else its own request's reading position).
- `_sketch_view(vault: Any, repository: Repository, row: Mapping[str, Any], view: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 1410) — A shown sketch as the Reader draws it: the program (its code runs in the desktop's sealed engine), the code-owned check lines and the *not covered* line, and its predictions (answers never sent first).
- `_manim_view(row: Mapping[str, Any], view: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 1461) — A shown Manim figure (RW5d P2b, spec §6.8): the content-addressed video (played over ``llmedia://``), its title and transcript, the code-owned check lines and *the video itself is not checked frame by frame*.
- `_source_rejected_row(vault: Any, repository: Repository, row: Mapping[str, Any]) -> Mapping[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 1497)
- `_source_check_view(vault: Any, repository: Repository, row: Mapping[str, Any], compiled: S.CompiledFigure, view: dict[str, Any]) -> None` ([source](../../../../../../src/learnloop/figures/service.py), line 1505) — RW5c (§7.4): a shown grammar figure's ``elements`` and ``source_check``, read from the ledger as the switch is now (absent with it off: the view is RW5a/RW5d's key for key).
- `_coded_answer(answered: Mapping[str, Any], by_label: Mapping[str, str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 1536) — An answered area prediction under code-owned labels: its stored answers (shade labels, kept as they were) go out as the shades' element ids.
- `_code_owned_labels(vault: Any, repository: Repository, row: Mapping[str, Any], compiled: S.CompiledFigure) -> dict[str, str] | None` ([source](../../../../../../src/learnloop/figures/service.py), line 1544) — Model label -> element id while this figure's labels are code-owned, else None.
- `_presented_row(vault: Any, repository: Repository, row: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 1571) — A stored row as :func:`figure_view` presents it under the switches now.
- `_prefetch_intent_refused(vault: Any, repository: Repository, intent: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 1672) — Landing ruling R1: whether background admission refuses a prebuild's unqueued rich intent now: figures ahead of need off, this machine not on mains, or its input held out.
- `_figure_request(repository: Repository, row: Mapping[str, Any]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/figures/service.py), line 1685) — The ``figure_requests`` row a figure was built for (RW5d), or None (RW5a/b rows before 224).
- `_reusable(vault: Any, repository: Repository, connection: Any, input_hash: str, other_hash: str | Sequence[str]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/figures/service.py), line 1778) — The figure a build reuses: this input's under the current prompt version, else (Codex review F2) a SHOWN one of the same input under the other prompt version when it can be drawn now.
- `_validated_request(vault: Any, repository: Repository, request: FigureRequest) -> FigureRequest` ([source](../../../../../../src/learnloop/figures/service.py), line 1817)
- `_validated_prefetch(vault: Any, request: FigureRequest) -> FigureRequest` ([source](../../../../../../src/learnloop/figures/service.py), line 1906) — RW5d P5: a prefetch build's request, as the prefetch service made it: an anchor (a passage of a book), an optional goal by the prefetch judge or a lesson plan's teacher, never an attempt host, a region or a revision.
- `_author_context(request: FigureRequest, context: SourceContext, image_digest: str | None, previous: Mapping[str, Any] | None, problems: Sequence[str], *, request_id: str, grounding: Grounding | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 2009)
- `_prefetch_build_hold(author_client: Any | None) -> Callable[[Any], str | None]` ([source](../../../../../../src/learnloop/figures/service.py), line 2103)
- `_build(vault: Any, repository: Repository, request: FigureRequest, *, gate: FiguresGate, author_client: Any | None, clock: Clock | None, find: FindSources | None, spawn_rich: SpawnRich | None=None) -> BuildOutcome` ([source](../../../../../../src/learnloop/figures/service.py), line 2116)
- `_learner_state(vault: Any, repository: Repository, request: FigureRequest, context: SourceContext, grounding: Grounding) -> Any` ([source](../../../../../../src/learnloop/figures/service.py), line 2242) — Learner data-relax 2: what the author is told about the learner on the passage's topics and what it was read from (:func:`.learner_state.read_learner_state`), or None (switched off or no topics; an empty or unreadable state: the predecessor's build).
- `_rich_pending(vault: Any, repository: Repository, request: FigureRequest, input_hash: str) -> BuildOutcome | None` ([source](../../../../../../src/learnloop/figures/service.py), line 2263) — A rich-only build of this input still running or waiting (its job is pending or waiting for the plan): the request takes its pending line.
- `_rich_line(request: FigureRequest, job: Mapping[str, Any], state: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 2279)
- `_withheld_payload(vault: Any, repository: Repository, payload: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 2312)
- `_building(repository: Repository, input_hash: str) -> Iterator[None]` ([source](../../../../../../src/learnloop/figures/service.py), line 2323) — Hold this process's one lock for (vault, input) while a build runs.
- `_request_row(request: FigureRequest, grounding: Grounding, *, figure_id: str | None, clock: Clock | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 2344) — The ``figure_requests`` row of one request (RW5d, spec §13.1): what was asked, as normalized, and what the server derived.
- `_reused(vault: Any, repository: Repository, row: Mapping[str, Any], *, request: FigureRequest | None=None, grounding: Grounding | None=None, clock: Clock | None=None, gate: FiguresGate | None=None) -> BuildOutcome` ([source](../../../../../../src/learnloop/figures/service.py), line 2375)
- `_free_text(output: Any, status: str) -> list[tuple[str, Any]]` ([source](../../../../../../src/learnloop/figures/service.py), line 2401) — The author's model-written free text the label rule reads (spec §9b.4): the tier reason, and what each figure it carries shows and assumes (a rich status's quick figure and brief included).
- `_without_label_text(output: Any) -> Any` ([source](../../../../../../src/learnloop/figures/service.py), line 2419) — The author's answer with its label-like free text left out (spec §9b.4): a tier reason in code's words, a figure's or brief's label-like ``demonstrates`` emptied and label-like assumptions dropped.
- `_step_three(vault: Any, repository: Repository, compiled: S.CompiledFigure, context: SourceContext, request: FigureRequest, grounding: Grounding | None, gate: FiguresGate) -> SC.Check | None` ([source](../../../../../../src/learnloop/figures/service.py), line 2442) — RW5c's check of a spec that passed steps 1-2, or None with the switch off.
- `_author_and_store(vault: Any, repository: Repository, request: FigureRequest, context: SourceContext, author: R.FigureRoute, *, previous: Mapping[str, Any] | None, versions: int, image: tuple[str, bytes] | None, asset_id: str | None, digest: str | None, input_hash: str, request_id: str, clock: Clock | None, gate: FiguresGate, advanced: bool=False, grounding: Grounding | None=None, sketch: bool=False, tiers: Sequence[str] | None=None, spawn_rich: SpawnRich | None=None, generation: int=0) -> BuildOutcome` ([source](../../../../../../src/learnloop/figures/service.py), line 2464)
- `class _RichSpawn` ([source](../../../../../../src/learnloop/figures/service.py), line 2803) — RW5d P2b (spec §8.6): starting the rich job of a rich status, after the quick figure is stored (:meth:`after_quick`) or with none (:meth:`only`).
- `_rich_revision(vault: Any, repository: Repository, request: FigureRequest, context: SourceContext, grounding: Grounding, *, previous: Mapping[str, Any], input_hash: str, digest: str | None, asset_id: str | None, generation: int, request_id: str, spawn_rich: SpawnRich | None, gate: FiguresGate, clock: Clock | None) -> BuildOutcome` ([source](../../../../../../src/learnloop/figures/service.py), line 2911) — RW5d P2b (spec §8.5, Codex review F11): "not right?" on a Manim figure.
- `_inherited_extra(repository: Repository, previous: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 2955) — Codex review F4: a rich revision's job payload carries what the learner states its earlier versions' authors were sent were read from (:func:`inherited_learner_inputs`); absent when none was sent, so every other revision's payload is exactly as before.
- `_append_tier(connection: Any, figure_id: str, input_hash: str, verdict: tuple[str, str], author: R.FigureRoute, prompt_version: str, created_at: str, *, left_kind: str='interactive_figure') -> None` ([source](../../../../../../src/learnloop/figures/service.py), line 2965) — The tier judgment's receipt (spec §8.4): the author's status, its reason (``why_not_spec`` or the unsupported reason), the model and prompt.
- `_store_sketch(vault: Any, repository: Repository, request: FigureRequest, context: SourceContext, author: R.FigureRoute, *, sketched: K.CompiledSketch | None, report: Any, problems: Sequence[str], versions: int, asset_id: str | None, input_hash: str, prompt_version: str, figure_id: str, asked: dict[str, Any], clock: Clock | None, gate: FiguresGate, grounding: Grounding, verdict: tuple[str, str] | None, rich_spawn: '_RichSpawn | None'=None) -> BuildOutcome` ([source](../../../../../../src/learnloop/figures/service.py), line 2977) — Store a sketch build (RW5d P2): shown (``illustrative``, its check lines) when verification passed, else ``failed`` with the reason (never shown).
- `_sketch_assumptions(compiled: K.CompiledSketch, span_texts: Mapping[str, str]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/figures/service.py), line 3041) — As :func:`.verify.verified_assumptions`: an unverified quote is dropped, the text stays (AI-written).
- `_ungrounded_sketch(raw: Any) -> Any` ([source](../../../../../../src/learnloop/figures/service.py), line 3052) — RW5d P2 + §8.3 step 3: a sketch built with nothing from the learner's books quotes nothing, whatever the author wrote.
- `_ungrounded(raw: Any) -> Any` ([source](../../../../../../src/learnloop/figures/service.py), line 3070) — RW5d (spec §8.3 step 3): with nothing from the learner's books, the figure is an illustration that quotes nothing, whatever the author wrote: code forces ``kind`` illustrative and drops every source claim and quote (there is no passage to verify them against).
- `_chain_length(repository: Repository, figure_id: str) -> int` ([source](../../../../../../src/learnloop/figures/service.py), line 3118)
- `_root(rows_by_id: Mapping[str, Mapping[str, Any]], row: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/figures/service.py), line 3137)
- `_listed(vault: Any, repository: Repository, extraction_id: str) -> list[tuple[Mapping[str, Any], int, list[dict[str, Any] | None]]]` ([source](../../../../../../src/learnloop/figures/service.py), line 3146) — The rows :func:`list_figures` presents, with no presentation (RW5d P4a, Codex review F3): per version chain, the pick, the chain's length and its placements in this source.
- `_prebuilt_within_budget(vault: Any, repository: Repository, extraction_id: str, picks: list[tuple[Mapping[str, Any], int, list[dict[str, Any] | None]]]) -> list[tuple[Mapping[str, Any], int, list[dict[str, Any] | None]]]` ([source](../../../../../../src/learnloop/figures/service.py), line 3194) — RW5d P5 (spec §6.9; Codex review F11): a prebuilt figure nobody pressed for takes its place in the Reader's cue budget (``[cues] density``, per section; cues off: none), the earliest built first; once pressed it is the learner's like any figure (never cut).
- `_prebuilt_listed(vault: Any, repository: Repository, row: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 3235) — RW5d P5: a prebuilt figure lists while figures ahead of need are on, or once a pressed request took it (then it is the learner's like any figure).
- `_prebuilt_pressed(repository: Repository, row: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/figures/service.py), line 3249)
- `_failed_correction(payload: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None` ([source](../../../../../../src/learnloop/figures/service.py), line 3646) — Codex re-review F14: the failure a correction job stored (its request's row, ``failed``) while it is still the newest version of the figure it corrects: nothing supersedes it and no later correction of that figure was stored.
- `_sketch_outcome(compiled: K.CompiledSketch, index: int) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/service.py), line 3793) — A sketch's prediction, decided by code in the sealed engine (spec §9.3).
- `_queue_formative(vault: Any, repository: Repository, prediction_id: str, *, clock: Clock | None) -> str | None` ([source](../../../../../../src/learnloop/figures/service.py), line 3838)
- `_queued(job_id: str | None, on_queued: Callable[[str], None] | None) -> None` ([source](../../../../../../src/learnloop/figures/service.py), line 3844)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/reader|learnloop.cli.reader]] — imports `module`; statically calls `row_withheld`
- [[Reference/Modules/learnloop/figures/help|learnloop.figures.help]] — imports `module`; statically calls `advanced_off_row`, `drawable_now`, `rich_row`, `row_withheld`, `show_me_enabled`, `show_me_row`, `sketch_off_row`, `source_rejected`
- [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] — imports `keys_withheld`, `module`, `withheld_message`; statically calls `FigureRequest`, `build_prefetch_figure`, `item_passages`, `keys_withheld`, `prefetch_plan_waits`, `source_context`, `withheld_message`
- [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]] — imports `keys_withheld`, `rich_base_item_protected`, `withheld_message`; statically calls `keys_withheld`, `rich_base_item_protected`, `withheld_message`
- [[Reference/Modules/learnloop/teacher/visuals|learnloop.teacher.visuals]] — imports `FigureRequest`, `module`; statically calls `FigureRequest`, `enabled`, `figure_view`, `figure_withheld`, `rich_row`, `show_me_enabled`, `teacher_visuals_switch`
- [[Reference/Modules/learnloop_sidecar/handlers/correspondents|learnloop_sidecar.handlers.correspondents]] — imports `module`; statically calls `enabled`, `section_figures`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `module`; statically calls `FigureRequest`, `anchored`, `attempt_hosted`, `build_figure`, `check_request`, `enabled`, `figure_offers_enabled`, `figure_view`, `figure_withheld`, `help_enabled`, `list_figures`, `predictions_enabled`, `prefetch_pending`, `prefetch_plan_waits`, `rebuild_request`, `record_explanation`, `record_prediction`, `redelivered_view`, `region_enabled`, `resume_rich_intents`, `retry_rich_job`, `revision_request`, `revisions_enabled`, `rich_enabled`, `rich_pending`, `rich_revision_retry`, `rich_row`, `show_me_enabled`, `shown_figure`, `sketch_enabled`
- [[Reference/Modules/learnloop_sidecar/handlers/hints|learnloop_sidecar.handlers.hints]] — imports `module`; statically calls `figure_withheld`
- [[Reference/Modules/learnloop_sidecar/handlers/lesson|learnloop_sidecar.handlers.lesson]] — imports `module`; statically calls `build_figure`
- [[Reference/Modules/learnloop_sidecar/prefetch_runtime|learnloop_sidecar.prefetch_runtime]] — imports `module`; statically calls `rich_enabled`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`, `gate_model_requests`; calls `content_key`, `gate_model_requests`
- [[Reference/Modules/learnloop/ai/plan_fallback|learnloop.ai.plan_fallback]] — imports `module`; calls `quiet`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendLimitExceeded`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `utc_now_iso`; calls `SystemClock`, `utc_now_iso`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `exam_material`, `spans_withheld`; calls `exam_material`, `spans_withheld`
- [[Reference/Modules/learnloop/daily_plan/records|learnloop.daily_plan.records]] — imports `assemble`; calls `assemble`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/daily_plans|learnloop.db.stores.daily_plans]] — imports `module`; calls `block_events_for`, `daily_plan_tables_present`, `plan_blocks`, `plans_for_date`
- [[Reference/Modules/learnloop/db/stores/figures|learnloop.db.stores.figures]] — imports `module`; calls `builds_for_input`, `figure`, `figure_verdicts`, `figures_for_extraction`, `fuller_rows`, `has_tables`, `insert_figure`, `insert_prediction`, `insert_request`, `latest_for_input`, `prediction`, `prediction_for`, `predictions_for_figure`, `request`, `reusable`, `set_explanation`, `set_request_figure`, `shown_verification`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/jobs|learnloop.diagnosis.text_gaps.jobs]] — imports `enqueue_figure_explanation`, `enqueue_figure_prediction`; calls `enqueue_figure_explanation`, `enqueue_figure_prediction`
- [[Reference/Modules/learnloop/figure_admission|learnloop.figure_admission]] — imports `FiguresChanged`, `FiguresGate`, `GROUNDING_PASSAGES`, `advanced_panels_enabled`, `author_learner_state_enabled`, `checked_labels_enabled`, `figure_home_keys`, `figures_enabled`, `help_kind_enabled`, `offers_enabled`, `show_me_enabled`, `sketch_enabled`; calls `FiguresGate`, `advanced_panels_enabled`, `author_learner_state_enabled`, `checked_labels_enabled`, `figure_home_keys`, `figures_enabled`, `help_kind_enabled`, `offers_enabled`, `show_me_enabled`, `sketch_enabled`
- [[Reference/Modules/learnloop/figures/elements|learnloop.figures.elements]] — imports `module`; calls `rewrite_spec`
- [[Reference/Modules/learnloop/figures/grammar|learnloop.figures.grammar]] — imports `module`
- [[Reference/Modules/learnloop/figures/labels|learnloop.figures.labels]] — imports `module`; calls `json_fields`, `label_like`, `label_problems`, `strip_json`, `strip_lines`
- [[Reference/Modules/learnloop/figures/learner_state|learnloop.figures.learner_state]] — imports `module`, `state_hash`; calls `anchored_learning_objects`, `enabled`, `read_learner_state`, `state_hash`
- [[Reference/Modules/learnloop/figures/manim_figure|learnloop.figures.manim_figure]] — imports `module`
- [[Reference/Modules/learnloop/figures/power|learnloop.figures.power]] — imports `background_hold`, `power_state`, `prefetch_switch`; calls `background_hold`, `power_state`, `prefetch_switch`
- [[Reference/Modules/learnloop/figures/prefetch_ledger|learnloop.figures.prefetch_ledger]] — imports `module`; calls `capacity_left`
- [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]] — imports `_withheld`, `module`; calls `RichBrief`, `_withheld`, `intent_learner_state_withheld`, `job_state`, `manim_tier_ready`, `parse_brief`, `rich_job_for`, `rich_job_for_figure`, `rich_job_for_quick`, `rich_job_for_request`, `rich_job_id_for_quick`, `rich_jobs`, `rich_tiers_switch`, `runtime_digest`, `stored_learner_state_withheld`, `tiers_allowed`
- [[Reference/Modules/learnloop/figures/routes|learnloop.figures.routes]] — imports `module`; calls `FigureRoute`, `author_prompt`, `author_prompt_version`, `daily_envelope`, `output_model`, `rich_menu`
- [[Reference/Modules/learnloop/figures/sketch|learnloop.figures.sketch]] — imports `module`; calls `parse_author_sketch`, `parse_sketch`
- [[Reference/Modules/learnloop/figures/sketch_engine|learnloop.figures.sketch_engine]] — imports `ENGINE_SHA256`, `ENGINE_VERSION`, `SketchEngine`, `SketchRunError`, `engine_ready`; calls `SketchEngine`, `engine_ready`
- [[Reference/Modules/learnloop/figures/sketch_verify|learnloop.figures.sketch_verify]] — imports `VERIFIER_REPORT_VERSION`, `module`; calls `prediction_outcome`, `prediction_target_step`, `verify_sketch`
- [[Reference/Modules/learnloop/figures/source_check|learnloop.figures.source_check]] — imports `module`; calls `check_figure`, `current_row`, `enabled`, `failed_check`, `grammar_row`, `recheck_due`, `record`, `stored_problems`
- [[Reference/Modules/learnloop/figures/spec|learnloop.figures.spec]] — imports `module`; calls `advanced_kinds`, `parse_author_spec`, `parse_spec`, `prediction_outcome`
- [[Reference/Modules/learnloop/figures/verify|learnloop.figures.verify]] — imports `module`; calls `Report`, `check_claims`, `quote_in`, `verified_assumptions`, `verify_numerics`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/learner_protection|learnloop.learner_protection]] — imports `module`; calls `withheld_items`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `plan_route`; calls `plan_route`
- [[Reference/Modules/learnloop/reader/reader_cues|learnloop.reader.reader_cues]] — imports `cue_density`, `cues_enabled`, `density_budget`; calls `cue_density`, `cues_enabled`, `density_budget`
- [[Reference/Modules/learnloop/reader/reader_guidance|learnloop.reader.reader_guidance]] — imports `extraction_sections`; calls `extraction_sections`
- [[Reference/Modules/learnloop/reader/span_view|learnloop.reader.span_view]] — imports `build_block_region`; calls `build_block_region`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `module`; calls `item_exclusions`
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

Static participation evidence comes from [[Reference/Modules/learnloop/cli/reader|learnloop.cli.reader]], [[Reference/Modules/learnloop/figures/help|learnloop.figures.help]], [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]], [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]], [[Reference/Modules/learnloop/teacher/visuals|learnloop.teacher.visuals]] and 5 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/rw5c_golden_source.py](../../../../../../tests/rw5c_golden_source.py) — direct import
- [tests/test_batch3_landing.py](../../../../../../tests/test_batch3_landing.py) — direct import
  - `test_iv_with_the_student_off_rw5ds_grounding_retrieval_is_p1s`
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
- [tests/test_figures_codex_review.py](../../../../../../tests/test_figures_codex_review.py) — direct import
  - `test_f7_a_paid_answer_survives_a_crash_before_the_row`
  - `test_f7_a_stored_failure_is_a_new_generation_that_asks_afresh`
  - `test_f7_identical_concurrent_builds_join_one_build`
- [tests/test_figures_final_round.py](../../../../../../tests/test_figures_final_round.py) — direct import
  - `test_a_provider_that_cannot_isolate_is_refused_before_any_request`
  - `test_the_view_sends_closed_property_check_keys_only`
- [tests/test_figures_fix_round2.py](../../../../../../tests/test_figures_fix_round2.py) — direct import
  - `test_f7_a_build_committed_between_the_reads_is_reused_inside_the_lock`
- [tests/test_figures_fix_round5.py](../../../../../../tests/test_figures_fix_round5.py) — direct import
- [tests/test_figures_help_codex_review.py](../../../../../../tests/test_figures_help_codex_review.py) — direct import
  - `test_f5_an_attempt_builds_admission_key_carries_the_switch`
  - `test_f7_the_trace_reads_only_what_this_attempt_wrote_as_it_stood_at_submit`
- [tests/test_figures_prefetch.py](../../../../../../tests/test_figures_prefetch.py) — direct import
  - `test_a_background_build_stops_off_mains_before_any_request`
  - `test_a_prebuilt_figure_lists_only_while_on_or_once_pressed`
  - `test_origin_prefetch_is_refused_from_every_rpc_and_outside_the_service`
  - `test_unbuilt_candidates_close_asked_or_neither_and_withheld_ones_void`
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
  - `test_r5_a_planned_visual_on_a_held_out_passage_is_not_a_candidate`
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
- [tests/test_followups_batch6_prefetch_decided_once.py](../../../../../../tests/test_followups_batch6_prefetch_decided_once.py) — direct import
  - `test_a_passage_released_after_a_void_decision_may_be_decided`
- [tests/test_followups_batch6_prefetch_next_section.py](../../../../../../tests/test_followups_batch6_prefetch_next_section.py) — direct import
  - `test_the_path_never_opens_a_held_out_section`
- [tests/test_followups_batch6_prefetch_plan_wait.py](../../../../../../tests/test_followups_batch6_prefetch_plan_wait.py) — direct import
  - `test_a_held_out_passage_or_a_closed_decision_is_not_retried`
  - `test_a_pass_retries_at_most_the_daily_build_cap`
  - `test_the_runtime_wires_the_paced_requeue`
- [tests/test_followups_batch6_review_fixes.py](../../../../../../tests/test_followups_batch6_review_fixes.py) — direct import
  - `test_f1_the_readers_read_never_requeues_it_either`
  - `test_f1_the_worker_rechecks_before_the_store`
  - `test_f1_the_worker_stops_a_requeued_prebuild_before_any_request`
  - `test_f2_a_job_that_keeps_meeting_the_limit_yields_the_slot_to_the_least_recently_asked`
  - `test_f2_a_paced_job_first_in_line_never_starves_a_due_one`
  - `test_f2_the_scan_goes_past_paced_jobs_until_the_bound_of_requeues`
- [tests/test_followups_batch6_verify_fixes.py](../../../../../../tests/test_followups_batch6_verify_fixes.py) — direct import
  - `test_v1_an_answered_planned_item_lets_the_retry_through`
  - `test_v1_an_unreadable_stored_plan_fails_closed_everywhere`
  - `test_v1_only_todays_plan_holds_an_item`
  - `test_v1_the_open_items_are_the_plan_records_own`
  - `test_v1_the_reader_and_the_pass_read_the_same_rule`
  - `test_v1_the_readers_read_never_requeues_a_prebuild_a_later_plan_holds`
  - `test_v1_the_worker_rechecks_the_plan_before_the_store`
  - `test_v1_the_worker_stops_a_requeued_prebuild_a_later_plan_holds_before_any_request`
- [tests/test_followups_batch7_prefetch_capped_resume.py](../../../../../../tests/test_followups_batch7_prefetch_capped_resume.py) — direct import
  - `test_a_capped_decision_is_coming_only_while_the_budget_has_room`
  - `test_a_figure_the_learner_pressed_for_meanwhile_is_not_counted_as_the_prebuilds`
- [tests/test_followups_nov2_figure_provenance.py](../../../../../../tests/test_followups_nov2_figure_provenance.py) — direct import
  - `test_a_fresh_figure_for_a_marked_row_is_reused_after_the_panels_are_switched`
  - `test_a_fuller_version_with_no_record_of_its_own_is_checked_by_its_jobs_payload`
  - `test_a_lesson_figure_keeps_its_record_and_is_rechecked_by_its_learner_inputs`
  - `test_a_marked_quick_figure_with_no_record_is_withheld`
  - `test_a_press_of_the_same_input_never_backfills_the_marked_row_and_builds_afresh`
  - `test_a_quick_figure_whose_learner_inputs_became_protected_is_not_presented`
  - `test_a_quick_figure_with_no_learner_state_keeps_its_report_as_before`
  - `test_a_revision_inherits_its_bases_learner_state_protection`
  - `test_a_rich_revision_with_nothing_inherited_carries_no_record`
  - `test_an_unmarked_quick_figure_with_no_record_keeps_the_no_learner_state_reading`
- [tests/test_learner_data_relax_2.py](../../../../../../tests/test_learner_data_relax_2.py) — direct import
  - `test_a_rich_figure_whose_learner_inputs_became_protected_is_not_delivered`
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
  - `test_a_shown_figure_held_out_since_is_no_longer_shown`
  - `test_a_visual_turn_builds_a_teacher_figure_shown_inline_with_its_predictions_suppressed`
  - `test_held_out_inputs_are_refused_before_any_call`
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
