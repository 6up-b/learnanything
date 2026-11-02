---
title: "learnloop.source_retrieval.deliverable_path"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/deliverable_path.py"
source_paths:
  - "src/learnloop/source_retrieval/deliverable_path.py"
source_commit: "6cb737bb81d4dff88f4e4b411c99c1995b830492"
source_commit_timestamp: "2026-11-01T08:25:13-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.source_retrieval"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.source_retrieval.deliverable_path module"
  - "src/learnloop/source_retrieval/deliverable_path.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.deliverable_path`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.deliverable_path` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: Deliverable curriculum C0b: the curated path across all sources, the Guide's slice, the learner's overrides, "Am I ready?" and the report's rows (spec_deliverable_curriculum_v1 §7.1-§7.5, §8.5, §9, §11, §12).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/deliverable_path.py](../../../../../../src/learnloop/source_retrieval/deliverable_path.py) |
| Source lines | 1962 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `6cb737bb81d4dff88f4e4b411c99c1995b830492` |
| Commit timestamp | `2026-11-01T08:25:13-05:00` |

## Public API

- `class Treatment` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 134) — One standing coverage row as the path reads it.
  - `ref(self) -> str` (line 152; public)
  - `primary_eligible(self) -> bool` (line 156; public)
- `class PathLo` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 161)
  - `treatment(self, ref: str) -> Treatment | None` (line 172; public)
- `class PathInputs` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 177)
  - `lo(self, learning_object_id: str) -> PathLo | None` (line 190; public)
  - `choosable(self) -> bool` (line 194; public) — Some LO has a primary-eligible section: only then is there a path to judge.
  - `statuses(self) -> dict[str, RP.LoStatus]` (line 200; public)
  - `state_key(self) -> str` (line 203; public) — The cache key (§7.2): the depth, the resolved scope, the coverage rows, the LO statuses, the learner-context digest and the prompt version (the prompt itself).
- `reading_pace(vault: Any) -> int` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 217) — DL1's reading pace (``plan.read_words_per_minute``, spec_daily_loop_v1 §6.4): the path's minutes, the minutes available and the report's estimates are all DL1's, so they are comparable (Codex review F11, F14).
- `section_words(reading: Any, section: Any) -> int` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 226)
- `prerequisite_closure(vault: Any, needed: Sequence[str], depth: str) -> dict[str, set[str]]` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 262) — Prerequisite LO -> the needed LOs it is background for, through ``LearningObject.prerequisites`` (concepts) to the depth's reach; needed LOs excluded.
- `daily_minutes(vault: Any, repository: Repository) -> int` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 350) — DL1's daily reading-and-practice budget (spec_daily_loop_v1 §6.6's remembered minutes): the latest plan's, else the last session's, else ``plan.default_minutes``.
- `learner_context(vault: Any, repository: Repository, library: SC.Library, goal_id: str, depth: str, due_at: str | None, *, refs: Iterable[str]=(), lo_ids: Sequence[str]=(), clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 370) — What the judge reads of the learner, as text (§7.2): the books they have been reading, the path's passages they said didn't help (RW1c), their kept comparisons and takes on these LOs (RW4d), their earlier choices on this deliverable, the days left and the minutes available befor…
- `path_inputs(vault: Any, repository: Repository, goal_id: str, *, library: SC.Library | None=None, clock: Clock | None=None) -> PathInputs | None` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 420) — Everything one path is judged and shown from, read now (None: no resolution yet, or no depth).
- `class AlternateChoice(WireModel)` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 472)
- `class PathEntry(WireModel)` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 478)
- `class DeliverablePathOutputV1(WireModel)` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 487)
- `build_prompt(inputs: PathInputs, level: str='full') -> str` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 517)
- `bounded_prompt(vault: Any, inputs: PathInputs) -> str | None` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 550) — The prompt within ``curriculum.max_prompt_tokens`` (Codex review F12), made smaller by :data:`PROMPT_LEVELS` in order; None when even the smallest is over (not sent).
- `honest_label(lo: PathLo, status: RP.LoStatus | None=None) -> tuple[str, bool]` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 567) — ``(label, changed)`` for an LO's primary (§7.1): a prerequisite LO is a prerequisite; a needed LO is already shown only while demonstrated, assumed only with an open assumption row, otherwise core.
- `class Line` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 583)
- `validate(output: DeliverablePathOutputV1, inputs: PathInputs) -> list[Line]` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 598) — The model's choices made honest: one primary per LO that is primary-eligible (else the first eligible row in C0a's order, code's line), alternates only from the LO's own coverage, every LO with an eligible section on the path, prerequisites before what they are background for.
- `exercise_for(vault: Any, repository: Repository, library: SC.Library, extraction_id: str, section_id: str) -> str | None` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 664) — The lead span of the section's first exercise region the one statement reader still reads (exam and held-out material never; fail closed).
- `exercise_view(vault: Any, repository: Repository, extraction_id: str, lead_span_id: str | None, pages: Mapping[str, Any] | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 687) — The stored exercise read again now (None when gone or protected now).
- `class JudgeResult` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 715)
- `judge(vault: Any, repository: Repository, goal_id: str, *, client: Any | None=None, clock: Clock | None=None, inputs: PathInputs | None=None, live_vault: Callable[[], Any] | None=None, still_wanted: Callable[[Any], bool] | None=None, route: DL.ChatRoute | None=None) -> JudgeResult` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 732) — Choose the deliverable's path at its depth: no call when the current state was judged; otherwise one call, the honest-label rules, the exercises, then the ledger verdicts and the rows in one transaction.
- `path_route(vault: Any, repository: Repository, *, client: Any | None=None, clock: Clock | None=None, plan_only: bool=False) -> DL.ChatRoute` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 839) — The path judge's pinned route for one judgment (``plan_only``: C1's automatic refresh, which asks the subscription plan only, on the route and on the client).
- `check_due(vault: Any, repository: Repository, learning_object_id: str, *, due_at: str | None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 853) — The day a check on the LO is due (``YYYY-MM-DD``; §8.5, TE §13): the first day its predicted retrievability falls to DL2's recall target for the check's preset (FSRS on the LO's most recently answered item), else DL2's Check once delay from now; never before tomorrow, never more…
- `ready_parameters(vault: Any) -> tuple[float, int]` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 885) — ``(retrievability target, fallback days)`` for a readiness check: DL2's ``intent.recall_targets[READY_DEPTH_PRESET]`` and ``capture.test_me_later_days``, as the vault's configuration has them now (Codex review F13).
- `pending_checks(repository: Repository) -> dict[str, list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 900) — LO -> its pending Check once commitments (an LO target, or an item of it, is read by the caller), from DL2's own snapshots; read only.
- `commitment_state(repository: Repository, commitment_id: str | None) -> str | None` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 932)
- `check_item(vault: Any, repository: Repository, learning_object_id: str) -> str | None` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 943) — An item for a readiness check by TE §13's candidate rule, chosen by code: active, of the LO, never attempted, no reveal row, and never protected (``learner_protection.withheld_items``: exam, held-out, reservations, open cold checks, probes; fail closed: unreadable protection pic…
- `create_check(vault: Any, repository: Repository, goal: Any, learning_object_id: str, *, via: str, key: str, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 974) — One Check once commitment on the LO (DL2's ``test_me_later``; its serving rule is unchanged).
- `override(vault: Any, repository: Repository, goal_id: str, learning_object_id: str, choice: str, *, section_ref: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 1008) — *use this one instead* (``section_ref`` names the alternate), *read it anyway*, *skip it*, *check me later* or ``none``: one ``learner_card`` verdict and one row.
- `class EffectiveLine` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 1098)
- `effective_lines(vault: Any, repository: Repository, inputs: PathInputs, rows: Sequence[Mapping[str, Any]]) -> list[EffectiveLine]` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 1115) — The path's lines as the learner sees them now: the judge's rows for the LOs still on the path whose sections are still readable, the honest label at today's statuses, the learner's newest choice per LO on top (one rule the Guide shows and C1 will read).
- `path_view(vault: Any, repository: Repository, goal_id: str, *, judging: Mapping[str, Any] | None=None, covering: bool=False, coverage_failure: Mapping[str, Any] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 1271) — What the deliverable's path shows.
- `coverage_owed(vault: Any, repository: Repository, goal_id: str) -> list[str]` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 1323) — The deliverable's LOs (needed, and prerequisites not demonstrated or assumed) with no coverage judgment of their current statement: the background coverage judges them.
- `coverage_key(vault: Any, learning_object_id: str) -> str | None` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 1348) — What C0a's judge read of the LO (its ``lo_hash``): the key an attempt is remembered by, so a statement changed since is tried again (Codex review F5).
- `guide_goal(vault: Any, repository: Repository, extraction_id: str) -> Any | None` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 1360) — The deliverable the Guide shows for this reading: the goal RW7a's ``goal_for_source`` picks over the reading's linked LOs (so RW7a's goal line and the slice never disagree), when it is a deliverable; else, the highest ``(priority, id)`` deliverable whose path names a section of…
- `guide_slice(vault: Any, repository: Repository, extraction_id: str, *, judging: Mapping[str, Any] | None=None, covering: bool=False, coverage_failure: Mapping[str, Any] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 1381) — What the Guide's path card shows for this reading when a deliverable's path names it: its lines here (core, prerequisite, alternate), its other-book lines ("on your path in Strang §6.1"), and this book's sections of no needed LO ("not needed for <deliverable>").
- `readiness(vault: Any, repository: Repository, goal_id: str, *, likely: LikelyReader | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 1448) — The answer to "am I ready?" (§8.5): per needed LO, demonstrated, likely (AD's labelled prediction, through ``likely``) or untested, and the dated checks still to come.
- `ready_checks(vault: Any, repository: Repository, goal_id: str, *, likely: LikelyReader | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 1485) — The pressed "Am I ready?": one Check once per needed LO not demonstrated and without a pending check (``provenance = {via: "deliverable_ready", goal_id}``).
- `report(vault: Any, repository: Repository) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 1504) — ``learnloop curriculum report``: aggregates only.
- `time_row(vault: Any, repository: Repository, goal: Any) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 1544) — §11's time row for one deliverable (Codex review F14): the minutes the learner read (recorded) against DL1's estimate for book order.
- `class PlanStep` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 1632) — One line of a fresh deliverable path as the plan read it, with the rows it came from (RW7b's F3 rule): the judge's row and the learner's newest override row.
  - `planned(self) -> bool` (line 1648; public)
  - `receipt(self) -> dict[str, Any]` (line 1651; public)
- `class DeliverablePlanPath` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 1659) — What C1's plan reads of one deliverable's path (RW7b's :class:`RP.PlanPath`'s sibling).
  - `follows(self) -> bool` (line 1681; public)
  - `in_play(self) -> bool` (line 1685; public)
  - `steps(self) -> tuple[PlanStep, ...]` (line 1689; public) — The lines the reading block may open, in the path's order (none when withheld).
  - `receipt(self) -> dict[str, Any]` (line 1694; public) — The receipt's entry: the inputs' key and the consumed judgment's key apart, and every judge and override row the labels came from, so neither a later judgment nor a later override changes what the receipt says was read.
- `deliverable_plan_path(vault: Any, repository: Repository, goal: Any, *, clock: Clock | None=None) -> DeliverablePlanPath` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 1712) — The deliverable path C1's plan follows for one goal, read now and never judged here (the plan calls no model).
- `nearest_deliverables(vault: Any, repository: Repository) -> list[Any]` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 1777) — The active deliverables (:func:`DL.deliverable_goals`), nearest first (§7.6, Q11).
- `plan_deliverable(vault: Any, repository: Repository, *, clock: Clock | None=None) -> tuple[DeliverablePlanPath | None, list[DeliverablePlanPath]]` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 1783) — Which deliverable the plan follows (§7.6): the nearest active goal among goals with a fresh deliverable path (or a withheld one, which is followed and plans nothing).
- `plan_refresh_reason(vault: Any) -> str | None` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 1818) — Why C1's daily re-judgment does not run (None: it does).
- `plan_refresh_route_problem(vault: Any, client: Any | None=None) -> str | None` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 1830) — Why C1's automatic refresh may not send its judgment on the route the path judge resolves to (None: it may).
- `refresh_for_plan(vault: Any, repository: Repository, *, client: Any | None=None, clock: Clock | None=None, live_vault: Callable[[], Any] | None=None, in_flight: Callable[[str, str, str], AbstractContextManager[bool]] | None=None, still_wanted: Callable[[Any], bool] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 1843) — C1's daily job (§7.6): the deliverable path's key includes learner state (the days left among it), so a path the plan would follow goes stale; once a day, before the plan is built, the nearest deliverable whose path is in play is judged again, **quietly** (``plan_fallback.quiet`…

### Module constants

- `PROMPT_VERSION` ([src/learnloop/source_retrieval/deliverable_path.py](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 84)
- `OVERRIDE_VERSION` ([src/learnloop/source_retrieval/deliverable_path.py](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 85)
- `LEDGER_TASK` ([src/learnloop/source_retrieval/deliverable_path.py](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 86)
- `LEDGER_LEFT` ([src/learnloop/source_retrieval/deliverable_path.py](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 87)
- `LEDGER_RIGHT` ([src/learnloop/source_retrieval/deliverable_path.py](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 88)
- `LABELS` ([src/learnloop/source_retrieval/deliverable_path.py](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 90)
- `CHIPS` ([src/learnloop/source_retrieval/deliverable_path.py](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 91)
- `OVERRIDES` ([src/learnloop/source_retrieval/deliverable_path.py](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 96)
- `PRIMARY_TREATMENTS` ([src/learnloop/source_retrieval/deliverable_path.py](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 98)
- `CLOSURE_DEPTH` ([src/learnloop/source_retrieval/deliverable_path.py](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 103)
- `WORDS_PER_MINUTE` ([src/learnloop/source_retrieval/deliverable_path.py](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 104)
- `REASON_CHARS` ([src/learnloop/source_retrieval/deliverable_path.py](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 105)
- `DEFAULT_REASON` ([src/learnloop/source_retrieval/deliverable_path.py](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 107)
- `PREREQUISITE_REASON` ([src/learnloop/source_retrieval/deliverable_path.py](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 108)
- `NOT_SHOWN_REASON` ([src/learnloop/source_retrieval/deliverable_path.py](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 109)
- `CODE_REASONS` ([src/learnloop/source_retrieval/deliverable_path.py](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 111)
- `READY_DEPTH_PRESET` ([src/learnloop/source_retrieval/deliverable_path.py](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 120)
- `READY_MAX_WAIT_DAYS` ([src/learnloop/source_retrieval/deliverable_path.py](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 123)
- `READY_VIA` ([src/learnloop/source_retrieval/deliverable_path.py](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 125)
- `PATH_VIA` ([src/learnloop/source_retrieval/deliverable_path.py](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 126)
- `_INSTRUCTIONS` ([src/learnloop/source_retrieval/deliverable_path.py](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 491)
- `PROMPT_LEVELS` ([src/learnloop/source_retrieval/deliverable_path.py](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 514)
- `TOO_LARGE_MESSAGE` ([src/learnloop/source_retrieval/deliverable_path.py](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 728)
- `PATH_STATUSES` ([src/learnloop/source_retrieval/deliverable_path.py](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 1267)
- `TIME_LABEL` ([src/learnloop/source_retrieval/deliverable_path.py](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 1538)
- `PLANNED_LABELS` ([src/learnloop/source_retrieval/deliverable_path.py](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 1615)
- `PLAN_PATH_STATUSES` ([src/learnloop/source_retrieval/deliverable_path.py](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 1624)
- `IN_PLAY_STATUSES` ([src/learnloop/source_retrieval/deliverable_path.py](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 1628)
- `REFRESH_STATUSES` ([src/learnloop/source_retrieval/deliverable_path.py](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 1814)

### Explicit exports

`__all__` declares:

- `CHIPS`
- `CLOSURE_DEPTH`
- `DeliverablePathOutputV1`
- `DeliverablePlanPath`
- `IN_PLAY_STATUSES`
- `PLANNED_LABELS`
- `PLAN_PATH_STATUSES`
- `PlanStep`
- `REFRESH_STATUSES`
- `EffectiveLine`
- `LABELS`
- `LEDGER_TASK`
- `Line`
- `OVERRIDES`
- `PATH_STATUSES`
- `PROMPT_VERSION`
- `PathInputs`
- `PathLo`
- `READY_DEPTH_PRESET`
- `READY_MAX_WAIT_DAYS`
- `Treatment`
- `build_prompt`
- `check_due`
- `check_item`
- `coverage_key`
- `coverage_owed`
- `deliverable_plan_path`
- `effective_lines`
- `guide_goal`
- `guide_slice`
- `honest_label`
- `judge`
- `nearest_deliverables`
- `override`
- `path_inputs`
- `path_route`
- `path_view`
- `plan_deliverable`
- `plan_refresh_reason`
- `plan_refresh_route_problem`
- `prerequisite_closure`
- `readiness`
- `ready_checks`
- `refresh_for_plan`
- `ready_parameters`
- `report`
- `time_row`
- `validate`

## Internal implementation anchors

- `_minutes(reading: Any, section: Any, pace: int=WORDS_PER_MINUTE) -> int` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 230)
- `_treatments(library: SC.Library, entries: Mapping[tuple[str, str], SC.Standing]) -> tuple[Treatment, ...]` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 234)
- `_concept_los(vault: Any) -> dict[str, list[str]]` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 253)
- `_didnt_help(repository: Repository, library: SC.Library, refs: set[str]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 291) — RW1c's "that didn't help" (a ``remediate`` follow-on): the path's sections among the passages the answer it followed had shown.
- `_kept(vault: Any, repository: Repository, library: SC.Library, lo_ids: Sequence[str]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 323) — RW4d's kept comparisons on these LOs (protection-filtered by their reader): the books they compared, the relations kept and how many takes the learner wrote.
- `_one_line(text: Any) -> str` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 562)
- `_fallback_primary(lo: PathLo) -> Treatment | None` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 594)
- `_ledger_question(goal_id: str, depth: str) -> str` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 724)
- `_pending_for(vault: Any, checks: Mapping[str, list[dict[str, Any]]], learning_object_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 923)
- `_current_rows(repository: Repository, inputs: PathInputs) -> tuple[list[dict[str, Any]], bool]` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 999)
- `_section_view(treatment: Treatment, *, read: bool) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 1073)
- `_read(repository: Repository) -> Any` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 1082)
- `_unjudged_lines(repository: Repository, inputs: PathInputs, chosen: Mapping[str, Mapping[str, Any]], *, placed: set[str], start: int) -> list[EffectiveLine]` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 1208) — The scope's LOs that have an eligible section but no line in the judgment shown (a topic added since: Codex review F9), each on code's first eligible section with code's line, until the next judgment places it.
- `_line_view(vault: Any, repository: Repository, line: EffectiveLine, inputs: PathInputs, done: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 1250)
- `_nearest_key(goal: Any) -> tuple[Any, ...]` ([source](../../../../../../src/learnloop/source_retrieval/deliverable_path.py), line 1766) — The existing nearest-goal rule (``learnloop_sidecar.handlers.goals._nearest_active_goal``): the nearest due date first (no date last), ties to the higher priority; the id last, so the order is total.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/curriculum|learnloop.cli.curriculum]] — imports `report`; statically calls `report`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `module`; statically calls `plan_deliverable`
- [[Reference/Modules/learnloop/source_retrieval/note_links|learnloop.source_retrieval.note_links]] — imports `module`; statically calls `path_view`
- [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]] — imports `module`; statically calls `nearest_deliverables`, `path_view`
- [[Reference/Modules/learnloop_sidecar/handlers/deliverables|learnloop_sidecar.handlers.deliverables]] — imports `module`; statically calls `coverage_key`, `coverage_owed`, `guide_goal`, `guide_slice`, `judge`, `override`, `path_inputs`, `path_view`, `plan_refresh_reason`, `readiness`, `ready_checks`, `refresh_for_plan`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/ai/plan_fallback|learnloop.ai.plan_fallback]] — imports `module`; calls `quiet`
- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `DEFAULT_RECALL_TARGETS`
- [[Reference/Modules/learnloop/content/sources/exercise_statements|learnloop.content.sources.exercise_statements]] — imports `exercise_region_spans`, `exercise_regions`, `read_exercise_statement`; calls `exercise_region_spans`, `exercise_regions`, `read_exercise_statement`
- [[Reference/Modules/learnloop/curriculum/commitments|learnloop.curriculum.commitments]] — imports `module`; calls `create_commitment`, `resolve_disposition`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/daily_plans|learnloop.db.stores.daily_plans]] — imports `module`; calls `daily_plan_tables_present`, `latest_plan`
- [[Reference/Modules/learnloop/db/stores/deliverables|learnloop.db.stores.deliverables]] — imports `module`; calls `all_path_rows`, `insert_path_row`, `judged`, `latest_judged`, `overrides`, `rows_naming`, `tables_present`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/db/stores/section_coverage|learnloop.db.stores.section_coverage]] — imports `module`; calls `judged_states`, `table_present`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/learner_protection|learnloop.learner_protection]] — imports `withheld_items`; calls `withheld_items`
- [[Reference/Modules/learnloop/params/fitted_params|learnloop.params.fitted_params]] — imports `resolve_fsrs_weights`; calls `resolve_fsrs_weights`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `plan_route`; calls `plan_route`
- [[Reference/Modules/learnloop/reader/reader_progression|learnloop.reader.reader_progression]] — imports `learning_objects_by_section`; calls `learning_objects_by_section`
- [[Reference/Modules/learnloop/scheduling/fsrs|learnloop.scheduling.fsrs]] — imports `interval_for_retention`; calls `interval_for_retention`
- [[Reference/Modules/learnloop/scheduling/intent/resolution|learnloop.scheduling.intent.resolution]] — imports `load_snapshots`; calls `load_snapshots`
- [[Reference/Modules/learnloop/source_retrieval/deliverables|learnloop.source_retrieval.deliverables]] — imports `module`; calls `ChatRoute`, `DeliverableError`, `_is_plan_type`, `daily_envelope`, `deliverable_goals`, `depth_of`, `goal_of`, `kind_of`, `latest_resolution`, `needed_learning_objects`
- [[Reference/Modules/learnloop/source_retrieval/kept_comparisons|learnloop.source_retrieval.kept_comparisons]] — imports `kept_comparisons_for_card`; calls `kept_comparisons_for_card`
- [[Reference/Modules/learnloop/source_retrieval/reader_tutor|learnloop.source_retrieval.reader_tutor]] — imports `shown_span_keys`; calls `shown_span_keys`
- [[Reference/Modules/learnloop/source_retrieval/reading_paths|learnloop.source_retrieval.reading_paths]] — imports `module`; calls `_done`, `exercise_label`, `goal_for_source`, `lo_statuses`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `module`; calls `CoverageGuard`, `Library`, `_active`, `lo_hash`, `standing`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `datetime`, `hashlib`, `json`, `logging`, `math`, `sqlite3`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/curriculum|learnloop.cli.curriculum]], [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/source_retrieval/note_links|learnloop.source_retrieval.note_links]], [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]], [[Reference/Modules/learnloop_sidecar/handlers/deliverables|learnloop_sidecar.handlers.deliverables]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_curriculum_c0b_landing.py](../../../../../../tests/test_curriculum_c0b_landing.py) — direct import
  - `test_i_a_dismissal_and_an_also_about_on_one_section_coexist_through_path_rejudgments`
- [tests/test_curriculum_c1_codex_review_fixes.py](../../../../../../tests/test_curriculum_c1_codex_review_fixes.py) — direct import
  - `test_f3_a_judgment_between_the_stale_read_and_the_plans_stamp_is_adopted`
  - `test_f3_without_a_new_judgment_the_stale_plan_stays_and_reads_no_path`
  - `test_f4_a_nearer_one_still_stale_leaves_the_farther_ones_step`
  - `test_f4_a_nearer_stale_deliverable_refreshed_is_adopted_over_the_farther_fresh_one`
- [tests/test_curriculum_c1_fix_round2.py](../../../../../../tests/test_curriculum_c1_fix_round2.py) — direct import
  - `test_l6_a_choice_made_while_a_read_failed_is_never_kept`
  - `test_m2_farther_refreshed_first_then_nearer_ends_on_the_nearer_step`
  - `test_m3_a_k1_judgment_committed_between_the_builds_inputs_and_its_lookup_is_taken`
- [tests/test_curriculum_c1_fix_round3.py](../../../../../../tests/test_curriculum_c1_fix_round3.py) — direct import
  - `test_m3_k0_observed_k1_prepared_and_a_concurrent_guide_open_for_k1_send_one_call`
  - `test_m3_the_guides_worker_moves_its_claim_to_the_inputs_it_prepared`
- [tests/test_curriculum_c1_fix_round4.py](../../../../../../tests/test_curriculum_c1_fix_round4.py) — direct import
  - `test_m4_a_finishing_guide_job_keeps_another_jobs_claim_and_the_refresh_sends_nothing`
- [tests/test_curriculum_c1_fix_round5.py](../../../../../../tests/test_curriculum_c1_fix_round5.py) — direct import
  - `test_m1_a_metered_route_is_never_asked_by_the_automatic_refresh`
  - `test_m1_the_plan_route_is_asked`
  - `test_m2_the_gate_going_off_at_the_request_or_the_write_keeps_nothing`
- [tests/test_curriculum_c1_plan_follows_path.py](../../../../../../tests/test_curriculum_c1_plan_follows_path.py) — direct import
  - `test_a_path_that_cannot_be_read_leaves_rw7bs_choice_and_says_so`
  - `test_a_shadow_rebuild_is_zero_and_never_reads_a_deliverable_path`
  - `test_a_stale_path_is_not_followed_and_the_receipt_says_stale`
  - `test_a_withheld_path_plans_nothing`
  - `test_the_nearest_deliverable_with_a_fresh_path_is_followed`
  - `test_the_refresh_job_is_quiet_and_only_judges_a_stale_path`
- [tests/test_curriculum_c1_round5_followups.py](../../../../../../tests/test_curriculum_c1_round5_followups.py) — direct import
  - `test_c1_r5_followup_a_a_guide_judgment_keeps_its_route_rules`
  - `test_c1_r5_followup_a_a_metered_client_behind_a_plan_route_sends_nothing`
  - `test_c1_r5_followup_a_the_refresh_resolves_its_route_once_and_judge_sends_on_it`
  - `test_c1_r5_followup_b_a_reload_right_after_the_gates_read_cannot_slip_into_the_admission`
  - `test_c1_r5_followup_b_an_unreadable_gate_admits_nothing`
  - `test_c1_r5_followup_b_the_gate_reads_the_admitted_snapshots_vault`
- [tests/test_curriculum_c3_exam_scoping.py](../../../../../../tests/test_curriculum_c3_exam_scoping.py) — direct import
  - `test_gc1_no_request_correspondent_path_row_or_slice_names_exam_material`
  - `test_gc1_note_link_judge_requests_carry_no_exam_material_from_sources`
  - `test_gc3_readiness_checks_never_pick_exam_reserved_or_held_out_items`
- [tests/test_deliverable_codex_review.py](../../../../../../tests/test_deliverable_codex_review.py) — direct import
  - `test_f10_a_primary_no_longer_eligible_is_replaced_by_codes_choice`
  - `test_f10_a_stored_swap_to_a_section_no_longer_eligible_is_not_shown_as_core`
  - `test_f10_use_instead_refuses_a_section_that_only_mentions_the_topic`
  - `test_f11_didnt_help_kept_comparisons_and_minutes_reach_the_judge`
  - `test_f11_minutes_available_are_dl1s_daily_budget_times_the_days_left`
  - `test_f12_a_prompt_over_the_bound_drops_notation_before_anything_else`
  - `test_f12_an_oversized_prompt_is_never_sent`
  - `test_f13_the_check_dates_follow_the_vaults_dl2_parameters`
  - `test_f14_the_time_row_counts_each_section_once_and_minutes_read_are_recorded`
  - `test_f1_a_path_retry_after_protection_changed_is_never_sent`
  - `test_f1_the_path_keeps_nothing_when_a_section_is_held_out_during_its_call`
  - `test_f1_the_path_worker_reads_the_live_vault_and_checks_against_it`
  - `test_f5_a_changed_statement_owes_coverage_again`
  - `test_f6_a_lifted_coverage_admission_refusal_starts_the_coverage_again`
  - `test_f9_a_topic_added_since_the_judgment_has_a_line_until_the_next`
- [tests/test_deliverable_path.py](../../../../../../tests/test_deliverable_path.py) — direct import
  - `test_a_mentions_only_section_is_never_a_primary`
  - `test_a_section_withheld_since_judging_is_never_shown_and_reasons_are_codes`
  - `test_already_shown_only_while_demonstrated`
  - `test_am_i_ready_creates_one_check_per_untested_lo_never_an_exam_reserved_item`
  - `test_an_unknown_section_falls_back_to_codes_choice_and_an_omitted_lo_is_still_placed`
  - `test_ask_depth_and_no_scope_states`
  - `test_check_due_is_bounded_by_tomorrow_fourteen_days_and_the_deadline`
  - `test_g_c3_held_out_items_are_never_picked`
  - `test_gc1_no_exam_or_held_out_text_reaches_the_path_judge_and_no_row_names_them`
  - `test_no_deliverable_leaves_the_guide_to_rw7a`
  - `test_one_primary_per_lo_from_its_coverage_alternates_from_other_books`
  - `test_overrides_use_instead_skip_and_check_later`
  - `test_prerequisites_come_first_and_only_when_not_demonstrated`
  - `test_reading_more_of_a_book_already_started_does_not_make_a_new_judgment`
  - `test_the_closure_reach_follows_the_depth`
  - `test_the_guide_slice_shows_this_books_lines_other_books_and_not_needed`
  - `test_the_report_rows_are_aggregates_only`
- [tests/test_notes_as_learner_text.py](../../../../../../tests/test_notes_as_learner_text.py) — direct import
  - `test_gc1_exam_sentinels_never_reach_the_gap_model_via_a_notes_context`
- [tests/test_reader_rw6b_landing.py](../../../../../../tests/test_reader_rw6b_landing.py) — direct import
  - `test_i_a_check_once_on_the_follow_ups_own_item_replaces_the_automatic_check`
  - `test_i_check_once_commitments_and_follow_ups_coexist_and_the_gate_touches_only_follow_ups`

## Modification guidance

- Make changes here when the responsibility remains deliverable path within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/deliverable_path.py](../../../../../../src/learnloop/source_retrieval/deliverable_path.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
