---
title: "learnloop.figures.prefetch"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/figures/prefetch.py"
source_paths:
  - "src/learnloop/figures/prefetch.py"
source_commit: "d4c02ae06286e5c2866d0e08949bc66df459fc03"
source_commit_timestamp: "2026-11-02T10:02:02-05:00"
source_worktree_state: "clean"
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
  - "learnloop.figures.prefetch module"
  - "src/learnloop/figures/prefetch.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-figures"
---

# `learnloop.figures.prefetch`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.figures.prefetch` exists within [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] to own the behavior summarized by its module contract: Reader RW5d P5: figures ahead of need (spec_reader_show_me_figures_v1 §10b).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/figures/prefetch.py](../../../../../../src/learnloop/figures/prefetch.py) |
| Source lines | 1537 |
| Owning package | [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `d4c02ae06286e5c2866d0e08949bc66df459fc03` |
| Commit timestamp | `2026-11-02T10:02:02-05:00` |

## Public API

- `class Trigger` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 140)
- `class Candidate` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 151)
  - `horizon_kind(self) -> str` (line 165; public)
  - `anchor(self) -> dict[str, Any]` (line 169; public)
  - `request_key(self) -> str` (line 173; public) — The request's identity before any build: its passage and its goal and who wrote it.
- `class PrefetchEnv` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 185) — What one pass reads and calls.
  - `now(self) -> datetime` (line 207; public)
  - `offset(self) -> timedelta` (line 210; public)
  - `today(self) -> str` (line 213; public)
  - `current_vault(self) -> Any` (line 216; public)
  - `is_cancelled(self) -> bool` (line 225; public)
  - `loaded_now(self) -> 'PrefetchEnv | None'` (line 228; public) — This environment over the vault configured now (:meth:`current_vault`), or None when it can't be read (the caller fails closed).
- `class PassResult` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 241)
- `enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 251) — ``figures.enabled`` and ``figures.prefetch_enabled``.
- `class ItemProtection` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 262) — The passages no prebuild may show: every passage of an item that is the subject of a live administration (an open cold check, a repair's cold retry, an assessment reservation or a diagnostic probe: ``learner_protection.withheld_items``) or that the stored plan holds open (its ex…
  - `covers(self, extraction_id: str, span_ids: Iterable[str]) -> bool` (line 273; public)
- `item_protection(env: PrefetchEnv) -> ItemProtection` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 286) — What :class:`ItemProtection` covers now (read fresh on every call: before judging, on the author's whole context, and again before each build).
- `context_spans(env: PrefetchEnv, candidate: 'Candidate') -> list[str]` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 316) — The spans the figure author would be sent for this candidate: its passage and the paragraphs around it (``service.source_context``, the anchored build's own context).
- `protected(env: PrefetchEnv, candidate: 'Candidate', protection: ItemProtection) -> bool` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 330) — The candidate's whole author context touches an item's own passage (landing ruling R5: a planned visual's, over each of its grounding passages and the paragraphs around them).
- `class PrefetchBlockV1(WireModel)` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 350)
- `class PrefetchSectionOutputV1(WireModel)` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 359)
- `class PrefetchGapOutputV1(WireModel)` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 363)
- `class JudgeUnavailable(Exception)` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 388)
  - `__init__(self, reason: str, message: str) -> None` (line 389; internal)
- `section_blocks(env: PrefetchEnv, extraction_id: str, section_id: str, protection: ItemProtection | None=None) -> tuple[str, list[dict[str, Any]]] | None` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 445) — A section's label and its blocks the judge may read: exam and held-out spans removed, and (Codex review F4) every passage of an item under a live administration or held open by the stored plan.
- `judge_section(env: PrefetchEnv, extraction_id: str, section_id: str, *, call: bool=True, result: PassResult | None=None) -> list[dict[str, Any]] | None` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 494) — The section judge's picks ``[{span_id, goal, p_open}]`` (cached by content); None when it could not run (``call`` False and nothing cached: off mains, the plan down, or no section).
- `judge_gap(env: PrefetchEnv, gap: Mapping[str, Any], passage: Mapping[str, Any], result: PassResult | None=None) -> tuple[str, float]` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 568) — The gap judge's goal and ``p_open`` for one gap on one passage.
- `next_section(env: PrefetchEnv, extraction_id: str, section_id: str) -> str | None` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 649) — The section after ``section_id`` in book order whose spans are not withheld.
- `planned_visual(node: Mapping[str, Any]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 668) — A plan node's planned visual (spec §10.4: RW5d P4b's ``write_plan`` node ``visual``, ``PlannedVisualV1``: the goal the teacher wrote and the delivered passages it rests on), as ``{"goal": ..., "anchors": [...]}``, or None.
- `candidates(env: PrefetchEnv, trigger: Trigger, *, call: bool, result: PassResult, open_keys: set[str] | None=None) -> list[Candidate]` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 793) — The trigger's candidates (spec §10b.2), before the filters.
- `open_request_keys(repository: Repository) -> set[str]` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 837) — Requests already decided whose horizon has not closed.
- `already_built(repository: Repository, candidate: Candidate) -> bool` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 855) — A shown figure exists for this passage and goal (any origin): nothing to build.
- `filter_candidates(env: PrefetchEnv, found: Iterable[Candidate], *, open_keys: set[str]) -> list[Candidate]` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 895) — The code filters (spec §10b.2), before any build call; the build repeats the protection.
- `observe_pause(env: PrefetchEnv) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 953) — Append the plan session's latest usage-limit pause, once (by its hit time); return it with ``active`` (whether it still holds now).
- `decide_and_log(env: PrefetchEnv, kept: Sequence[Candidate], *, on_mains: bool, plan_wait: str | None, result: PassResult) -> list[tuple[dict[str, Any], Candidate]]` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 1018) — Decide every kept candidate (spec §10b.3), apply the power, plan and cap conditions in sampled-EU order, and append one decision row each.
- `pending_builds(env: PrefetchEnv) -> list[tuple[dict[str, Any], Candidate]]` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 1078) — Decisions to build that no build has served yet, while their horizon is open: the queue yielded, the cap or the power or the plan went away mid-queue, or (Codex review F5) the decision itself was deferred for the power or the plan.
- `started_today(env: PrefetchEnv) -> set[str]` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 1110) — The decisions whose build started today (local day).
- `reserve_build(env: PrefetchEnv, decision_id: str) -> bool` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 1119) — Spend one of today's builds on this decision, or False when the cap is used up.
- `rich_in_flight(env: PrefetchEnv) -> bool` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 1136) — A prebuild's durable rich job is queued or running (Codex review F7: background work is one pipeline at a time, so nothing else starts until it ends).
- `run_builds(env: PrefetchEnv, queue: Sequence[tuple[dict[str, Any], Candidate]], result: PassResult) -> None` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 1159) — The queue, one build at a time: each waits for no foreground work, and starts only on mains with the switch on (rechecked on the vault as configured now).
- `horizon_at(env: PrefetchEnv, connection: Any, row: Mapping[str, Any], open_gaps: set[str] | None) -> datetime | None` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 1252) — When the decision's structural horizon passed (spec §10b.5), or None while it is open.
- `close_horizons(env: PrefetchEnv, result: PassResult | None=None) -> int` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 1375) — Close every open decision whose horizon has passed, once (spec §10b.5).
- `run_trigger(env: PrefetchEnv, trigger: Trigger) -> PassResult` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 1453) — One pass for one trigger (module docstring).

### Module constants

- `_LOG` ([src/learnloop/figures/prefetch.py](../../../../../../src/learnloop/figures/prefetch.py), line 102)
- `JUDGE_TASK` ([src/learnloop/figures/prefetch.py](../../../../../../src/learnloop/figures/prefetch.py), line 104)
- `JUDGE_PROMPT_VERSION` ([src/learnloop/figures/prefetch.py](../../../../../../src/learnloop/figures/prefetch.py), line 105)
- `LEDGER_TASK` ([src/learnloop/figures/prefetch.py](../../../../../../src/learnloop/figures/prefetch.py), line 107)
- `DECISION_PREFIX` ([src/learnloop/figures/prefetch.py](../../../../../../src/learnloop/figures/prefetch.py), line 108)
- `TRIGGER_KINDS` ([src/learnloop/figures/prefetch.py](../../../../../../src/learnloop/figures/prefetch.py), line 109)
- `HORIZONS` ([src/learnloop/figures/prefetch.py](../../../../../../src/learnloop/figures/prefetch.py), line 110)
- `PREFETCH_SECTION_CANDIDATES` ([src/learnloop/figures/prefetch.py](../../../../../../src/learnloop/figures/prefetch.py), line 115)
- `PREFETCH_CONCURRENT_BUILDS` ([src/learnloop/figures/prefetch.py](../../../../../../src/learnloop/figures/prefetch.py), line 117)
- `MAX_SECTION_BLOCKS` ([src/learnloop/figures/prefetch.py](../../../../../../src/learnloop/figures/prefetch.py), line 119)
- `BLOCK_CHARS` ([src/learnloop/figures/prefetch.py](../../../../../../src/learnloop/figures/prefetch.py), line 120)
- `GAP_STATEMENT_CHARS` ([src/learnloop/figures/prefetch.py](../../../../../../src/learnloop/figures/prefetch.py), line 122)
- `PASSAGE_CHARS` ([src/learnloop/figures/prefetch.py](../../../../../../src/learnloop/figures/prefetch.py), line 123)
- `MAX_JUDGE_ATTEMPTS` ([src/learnloop/figures/prefetch.py](../../../../../../src/learnloop/figures/prefetch.py), line 125)
- `FOREGROUND_WAIT_SECONDS` ([src/learnloop/figures/prefetch.py](../../../../../../src/learnloop/figures/prefetch.py), line 128)
- `MAX_NODE_SPANS` ([src/learnloop/figures/prefetch.py](../../../../../../src/learnloop/figures/prefetch.py), line 130)
- `PLAN_BILLING` ([src/learnloop/figures/prefetch.py](../../../../../../src/learnloop/figures/prefetch.py), line 132)
- `_LIVE_REASONS` ([src/learnloop/figures/prefetch.py](../../../../../../src/learnloop/figures/prefetch.py), line 283)
- `_SECTION_INSTRUCTIONS` ([src/learnloop/figures/prefetch.py](../../../../../../src/learnloop/figures/prefetch.py), line 369)
- `_GAP_INSTRUCTIONS` ([src/learnloop/figures/prefetch.py](../../../../../../src/learnloop/figures/prefetch.py), line 378)
- `_BUILD_SLOTS` ([src/learnloop/figures/prefetch.py](../../../../../../src/learnloop/figures/prefetch.py), line 1101)
- `_CAP_LOCK` ([src/learnloop/figures/prefetch.py](../../../../../../src/learnloop/figures/prefetch.py), line 1106)
- `_STARTED` ([src/learnloop/figures/prefetch.py](../../../../../../src/learnloop/figures/prefetch.py), line 1107)

### Explicit exports

`__all__` declares:

- `DECISION_PREFIX`
- `FOREGROUND_WAIT_SECONDS`
- `HORIZONS`
- `JUDGE_PROMPT_VERSION`
- `JUDGE_TASK`
- `LEDGER_TASK`
- `MAX_JUDGE_ATTEMPTS`
- `PREFETCH_CONCURRENT_BUILDS`
- `PREFETCH_SECTION_CANDIDATES`
- `Candidate`
- `JudgeUnavailable`
- `PassResult`
- `PrefetchEnv`
- `PrefetchGapOutputV1`
- `PrefetchSectionOutputV1`
- `Trigger`
- `ItemProtection`
- `already_built`
- `candidates`
- `context_spans`
- `horizon_at`
- `item_protection`
- `planned_visual`
- `protected`
- `reserve_build`
- `rich_in_flight`
- `started_today`
- `close_horizons`
- `decide_and_log`
- `enabled`
- `filter_candidates`
- `judge_gap`
- `judge_section`
- `next_section`
- `observe_pause`
- `open_request_keys`
- `pending_builds`
- `plan_providers`
- `run_builds`
- `run_trigger`

## Internal implementation anchors

- `_judge_route(env: PrefetchEnv, owner_id: str) -> R.FigureRoute` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 395)
- `_ask(route: R.FigureRoute, prompt: Callable[[list[str]], str], result_model: type[WireModel], validate: Callable[[Any], str | None], revalidate: Callable[[], str | None]) -> Any` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 407) — At most :data:`MAX_JUDGE_ATTEMPTS` calls; the second is told the first's problems (in its context).
- `_section_problem(output: PrefetchSectionOutputV1, ids: Sequence[str]) -> str | None` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 433)
- `_section_hash(extraction_id: str, section_id: str, blocks: Sequence[Mapping[str, Any]]) -> str` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 476)
- `_cached(repository: Repository, input_hash: str) -> list[dict[str, Any]] | None` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 481)
- `_gap_hash(context: Mapping[str, Any], gap: Mapping[str, Any], passage: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 547)
- `_cached_gap(repository: Repository, input_hash: str) -> tuple[str, float] | None` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 553)
- `_section_candidates(env: PrefetchEnv, kind: str, ref: str, extraction_id: str, section_id: str, *, call: bool, result: PassResult) -> list[Candidate]` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 626)
- `_plan_record(env: PrefetchEnv, plan_id: str | None) -> Any` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 636)
- `_lesson_candidates(env: PrefetchEnv, lesson_id: str) -> list[Candidate]` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 686) — Landing ruling R5: each node not yet reached with a planned visual, as the request the lesson's step will make for it (P4b's own builder, ``teacher.visuals.figure_request``, so the goal and the grounding keys are byte for byte the step's and its input hash is the same).
- `_topic_passages(vault: Any, repository: Repository, learning_object_id: str) -> list[tuple[str, str]]` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 721) — A topic's own provenance passages (no retrieval, no model): the explain intent's first list.
- `_span_text(repository: Repository, extraction_id: str, span_id: str) -> str` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 735)
- `_touched_topics(env: PrefetchEnv) -> list[str]` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 745) — The topics the stored plan (today's latest) and the open lessons touch.
- `_gap_candidates(env: PrefetchEnv, *, call: bool, result: PassResult, open_keys: set[str]) -> list[Candidate]` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 762)
- `_decided_refs(repository: Repository, kind: str) -> set[str]` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 829)
- `_span_list(raw: Any) -> list[str]` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 847)
- `_key_list(raw: Any) -> list[list[str]]` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 877)
- `_held_plan_items(env: PrefetchEnv) -> list[Any]` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 885) — The stored plan's (today's latest) items not yet resolved.
- `_pause_minutes(vault: Any) -> int` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 937)
- `_default_pause_reader() -> Mapping[str, Any] | None` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 947)
- `_source_key(repository: Repository, extraction_id: str) -> str` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 983)
- `_author_ready(env: PrefetchEnv) -> str | None` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 992) — Why the figure author can't take a prebuild now (it waits), or None: the route must be the plan (never metered) and resolvable.
- `_rich_spawn(env: PrefetchEnv) -> Callable[[dict[str, Any]], str] | None` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 1007) — A background rich job only when the rich author's route is the plan too (never metered).
- `_link(env: PrefetchEnv, decision_id: str) -> None` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 1146) — Set the decision's request and the figure's input hash, once each (the build stored them).
- `_day_end(env: PrefetchEnv, local_date: str) -> datetime | None` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 1226) — The instant a local day ends (its next midnight, in this machine's offset).
- `_session_end(connection: Any, extraction_id: str | None, created: datetime) -> datetime | None` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 1236) — The end of the reading session the offer was made in (RW6b's session digest of that source spanning the decision), or None while no such session has ended.
- `_figure_ids(connection: Any, request_id: str) -> set[str]` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 1307)
- `_between(value: Any, since: datetime, until: datetime) -> bool` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 1315)
- `_opened(connection: Any, figure_ids: set[str], since: datetime, until: datetime) -> bool` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 1320)
- `_delivered(connection: Any, figure_ids: set[str], since: datetime, until: datetime) -> bool` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 1338) — Landing ruling R5: a lesson's step delivered the prebuilt figure (its own request reused it) before the horizon: the lesson showed it, the lesson's equivalent of opening it.
- `_asked(connection: Any, row: Mapping[str, Any], since: datetime, until: datetime) -> bool` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 1353) — A pressed request for this very input (its passage, and its goal or none) before the horizon.
- `_key(vault: Any) -> tuple[Any, ...]` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 1431)
- `_pass_hold(env: PrefetchEnv) -> Callable[[Any], str | None]` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 1437) — The pass's hold before every physical request (the judge's, a quick build's author): the switch, the power and foreground work in flight (``power.background_hold``).
- `_judge_admitted(env: PrefetchEnv) -> bool` ([source](../../../../../../src/learnloop/figures/prefetch.py), line 1447)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/prefetch_runtime|learnloop_sidecar.prefetch_runtime]] — imports `Trigger`, `module`; statically calls `PrefetchEnv`, `Trigger`, `enabled`, `run_trigger`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/chatgpt_plan/session|learnloop.ai.chatgpt_plan.session]] — imports `DEFAULT_PAUSE_MINUTES`, `PlanSession`; calls `PlanSession`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`, `gate_model_requests`; calls `content_key`, `gate_model_requests`
- [[Reference/Modules/learnloop/ai/plan_fallback|learnloop.ai.plan_fallback]] — imports `module`; calls `quiet`
- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `utc_now_iso`; calls `SystemClock`, `utc_now_iso`
- [[Reference/Modules/learnloop/content/authoring/practice_leakage|learnloop.content.authoring.practice_leakage]] — imports `build_cross_source_spans`; calls `build_cross_source_spans`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `load_records`; calls `load_records`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/figure_prefetch|learnloop.db.stores.figure_prefetch]] — imports `module`; calls `close_decision`, `insert_decisions`, `insert_pause`, `link_request`
- [[Reference/Modules/learnloop/db/stores/figures|learnloop.db.stores.figures]] — imports `SHOWN`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/figure_admission|learnloop.figure_admission]] — imports `FiguresChanged`, `FiguresGate`; calls `FiguresGate`
- [[Reference/Modules/learnloop/figures/foreground|learnloop.figures.foreground]] — imports `module`; calls `wait_idle`
- [[Reference/Modules/learnloop/figures/learner_state|learnloop.figures.learner_state]] — imports `open_gap_statements`; calls `open_gap_statements`
- [[Reference/Modules/learnloop/figures/power|learnloop.figures.power]] — imports `module`; calls `background_hold`, `power_state`, `prefetch_switch`
- [[Reference/Modules/learnloop/figures/prefetch_ledger|learnloop.figures.prefetch_ledger]] — imports `module`; calls `_when`, `anchor_of`, `day_load`, `decisions`, `has_tables`, `load_model`, `render_minutes_today`, `started_today`
- [[Reference/Modules/learnloop/figures/prefetch_model|learnloop.figures.prefetch_model]] — imports `module`; calls `Candidate`
- [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]] — imports `RICH_TASK`, `module`; calls `job_state`, `rich_jobs`
- [[Reference/Modules/learnloop/figures/routes|learnloop.figures.routes]] — imports `module`; calls `FigureRoute`
- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `keys_withheld`, `module`, `withheld_message`; calls `FigureRequest`, `build_prefetch_figure`, `keys_withheld`, `source_context`, `withheld_message`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/learner_protection|learnloop.learner_protection]] — imports `module`; calls `withheld_items`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `plan_route`; calls `plan_route`
- [[Reference/Modules/learnloop/reader/reader_guidance|learnloop.reader.reader_guidance]] — imports `extraction_sections`; calls `extraction_sections`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `item_exclusions`; calls `item_exclusions`
- [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]] — imports `PROVENANCE_SPANS_PER_LO`
- [[Reference/Modules/learnloop/teacher/contracts|learnloop.teacher.contracts]] — imports `PlannedVisualV1`
- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `load_state`; calls `load_state`
- [[Reference/Modules/learnloop/teacher/visuals|learnloop.teacher.visuals]] — imports `module`; calls `figure_request`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `datetime`, `json`, `logging`, `threading`, `typing`
- Third party: `numpy`, `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/prefetch_runtime|learnloop_sidecar.prefetch_runtime]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_figures_prefetch.py](../../../../../../tests/test_figures_prefetch.py) — direct import
  - `test_a_judge_that_never_answers_well_decides_nothing`
  - `test_a_metered_author_route_defers_for_the_plan`
  - `test_a_plan_pause_is_recorded_once_and_defers_the_builds`
  - `test_a_prebuilt_figure_lists_only_while_on_or_once_pressed`
  - `test_a_press_reuses_the_prebuilt_figure_by_its_input_hash`
  - `test_gap_trigger_sends_the_statement_and_a_passage_never_an_attempt`
  - `test_lesson_trigger_builds_the_planned_visuals_of_nodes_not_yet_reached`
  - `test_offer_trigger_is_anchor_only_and_needs_no_judge`
  - `test_on_battery_nothing_starts_and_no_judge_is_asked`
  - `test_outcomes_close_once_at_the_structural_horizon`
  - `test_plan_trigger_judges_the_reading_section_decides_logs_and_builds`
  - `test_prebuilds_yield_to_foreground_work_and_resume_on_the_next_pass`
  - `test_section_trigger_takes_the_next_section_in_book_order`
  - `test_switch_off_nothing_builds_nothing_is_written_and_nothing_is_called`
  - `test_the_daily_cap_cuts_the_queue_in_sampled_eu_order`
  - `test_the_judge_is_never_called_on_a_metered_route_or_with_models_off`
  - `test_the_render_minutes_cap_holds_every_build`
  - `test_the_report_block_appears_only_with_the_switch`
  - `test_the_section_judges_answer_is_checked_and_retried_once`
  - `test_the_switch_going_off_stops_the_queue`
  - `test_the_thompson_decision_is_logged_with_its_propensity_and_is_reproducible`
  - `test_unbuilt_candidates_close_asked_or_neither_and_withheld_ones_void`
- [tests/test_figures_prefetch_review_fixes.py](../../../../../../tests/test_figures_prefetch_review_fixes.py) — direct import
  - `test_f11_reader_figures_says_a_prebuild_is_coming_until_it_lands`
  - `test_f11_unpressed_prebuilt_lines_keep_to_the_cue_budget`
  - `test_f13_the_gap_judges_verdict_is_a_judgment_ledger_row_once`
  - `test_f18_an_unstarted_decision_is_pending_only_while_a_pass_runs_and_never_on_battery`
  - `test_f1_a_gap_judge_retry_is_not_sent_once_its_passage_is_held_out`
  - `test_f1_a_section_judge_retry_is_not_sent_once_a_block_is_held_out`
  - `test_f1_rereview_a_builds_protection_is_read_on_the_vault_loaded_now`
  - `test_f1_rereview_a_gap_judge_retry_revalidates_on_the_vault_loaded_now`
  - `test_f1_rereview_a_section_judge_retry_revalidates_on_the_vault_loaded_now`
  - `test_f1_rereview_an_unreadable_current_vault_sends_no_judge_request`
  - `test_f4_a_build_rechecks_the_protection_before_it_starts`
  - `test_f4_a_cold_items_passage_and_its_neighbours_are_never_prebuilt`
  - `test_f4_unreadable_protection_prebuilds_nothing`
  - `test_f5_a_deferred_decision_is_built_once_the_condition_clears`
  - `test_f6_a_resumed_build_spends_todays_cap`
  - `test_f7_a_prebuilds_rich_job_in_flight_holds_the_next_prebuild_and_the_judge`
  - `test_f7_the_judge_waits_for_foreground_work`
  - `test_f8_a_te1_lesson_plan_has_no_planned_visual_so_nothing_is_prebuilt`
  - `test_f9_an_ask_is_the_same_request_before_the_horizon`
  - `test_f9_an_open_after_the_horizon_is_not_an_outcome`
  - `test_r5_a_planned_visual_is_prebuilt_and_the_lesson_step_reuses_it_with_no_author_call`
  - `test_r5_a_planned_visual_on_a_held_out_passage_is_not_a_candidate`

## Modification guidance

- Make changes here when the responsibility remains prefetch within learnloop.figures; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/figures/prefetch.py](../../../../../../src/learnloop/figures/prefetch.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
