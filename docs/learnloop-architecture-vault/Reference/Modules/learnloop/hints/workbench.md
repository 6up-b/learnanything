---
title: "learnloop.hints.workbench"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/hints/workbench.py"
source_paths:
  - "src/learnloop/hints/workbench.py"
source_commit: "13ab1168c4357273745ad4b7d1f77e5ede31efe7"
source_commit_timestamp: "2026-10-25T14:30:33-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.hints"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.hints.workbench module"
  - "src/learnloop/hints/workbench.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-hints"
---

# `learnloop.hints.workbench`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.hints.workbench` exists within [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] to own the behavior summarized by its module contract: Adaptive hints H3: the hint service on the Reader workbench (spec_adaptive_hints_v1 §10 H3, §16; spec_reader_workbench_v1 §5.2-5.5, G7, G37, G60, G63, G64).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/hints/workbench.py](../../../../../../src/learnloop/hints/workbench.py) |
| Source lines | 1188 |
| Owning package | [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `13ab1168c4357273745ad4b7d1f77e5ede31efe7` |
| Commit timestamp | `2026-10-25T14:30:33-04:00` |

## Public API

- `reveal_basis(kind: str, level: int) -> str` ([source](../../../../../../src/learnloop/hints/workbench.py), line 101) — The ``reveal_events`` basis of a hint shown in the workbench (§5.4).
- `class WorkbenchStep` ([source](../../../../../../src/learnloop/hints/workbench.py), line 112) — One live step: its stable id (the chain's first row), its newest version's row id, its number on screen and its text.
  - `content_hash(self) -> str` (line 123; public)
- `class StepVerdict` ([source](../../../../../../src/learnloop/hints/workbench.py), line 128) — A check's verdict on one step (spec §5.2), keyed by the step's chain id.
- `class WorkbenchHintContext` ([source](../../../../../../src/learnloop/hints/workbench.py), line 144) — The workbench's part of a hint request (spec §5.2 "the service").
  - `current(self) -> 'WorkbenchHintContext'` (line 185; public) — This context with its verdicts as they may be read NOW (the one accessor, :mod:`learnloop.symbolic_view`, with the current switch).
  - `verdicts(self) -> tuple[StepVerdict, ...]` (line 202; public) — The verdicts as they may be read NOW (fix round 15): every reader (the chooser's state, the writer's prompt, row serialization) goes through :meth:`current`.
  - `step(self, chain_id: str | None) -> WorkbenchStep | None` (line 209; public)
  - `verdict(self, chain_id: str | None) -> StepVerdict | None` (line 212; public)
  - `number(self, chain_id: str | None) -> int | None` (line 215; public)
  - `continue_from_node(self) -> str | None` (line 220; public)
  - `work_md(self) -> str` (line 224; public) — The steps as the writer reads them: one per paragraph, numbered.
  - `placement_hash(self) -> str` (line 230; public) — Where the help is placed: its about-step and that step's text (§5.2 "two hints on the same step", "one at a time" per step).
  - `snapshot(self) -> list[dict[str, Any]]` (line 240; public) — ``step_snapshot_json``: step ids and content hashes at request time, each step's text (bounded) for the diagnoser's trace (§5.4), and a fingerprint of its FULL text (:func:`text_fingerprint`) that the workbench compares with the text on screen (fix round 5, item 3).
  - `verdicts_record(self) -> list[dict[str, Any]]` (line 250; public) — The verdicts as a new row stores them, read NOW (fix round 12).
  - `prompt_block(self) -> dict[str, Any]` (line 255; public) — What the writer is told about the steps (spec §5.8 "context per call"), with the verdicts read NOW before every writer invocation (fix round 12).
- `verdict_record(row: StepVerdict) -> dict[str, Any]` ([source](../../../../../../src/learnloop/hints/workbench.py), line 316)
- `verdict_from_record(record: Mapping[str, Any]) -> StepVerdict` ([source](../../../../../../src/learnloop/hints/workbench.py), line 322)
- `dependents(verdicts: Sequence[StepVerdict], chain_id: str) -> set[str]` ([source](../../../../../../src/learnloop/hints/workbench.py), line 336) — Every step that depends, directly or through others, on ``chain_id``.
- `standing_steps(steps: Sequence[WorkbenchStep], verdicts: Sequence[StepVerdict]) -> list[str]` ([source](../../../../../../src/learnloop/hints/workbench.py), line 351) — Steps that stand (rule 2): marked valid or unchecked (or not checked) and depending on no questionable step.
- `checkpoint_for(steps: Sequence[WorkbenchStep], standing: Sequence[str], about: str | None) -> str | None` ([source](../../../../../../src/learnloop/hints/workbench.py), line 372) — ``continue_from`` (rule 2): the about-step itself when it stands (the picked step of "that's not where I'm stuck"), else the last standing step before it; with no about-step, the last standing step; None at the givens.
- `ladder_options(state: HintState, context: WorkbenchHintContext) -> OptionSet` ([source](../../../../../../src/learnloop/hints/workbench.py), line 426) — Every rung's options (the suggestion's choice set, §5.5).
- `taken_options(state: HintState, context: WorkbenchHintContext, *, request: str, answered: Any, shortcut: str | None, taken_level: int | None) -> OptionSet` ([source](../../../../../../src/learnloop/hints/workbench.py), line 444) — A request's options: H2a's (a reply keeps its level, the learner's picks fix theirs, a taken rung offers its kinds), then the workbench's constraints.
- `check_rivals(context: WorkbenchHintContext) -> list[Rival]` ([source](../../../../../../src/learnloop/hints/workbench.py), line 462) — The check's own error-kind guess and its alternatives on the first questionable step, as rivals (statement and status only), when the hint is about that step.
- `apply_context(state: HintState, context: WorkbenchHintContext) -> HintState` ([source](../../../../../../src/learnloop/hints/workbench.py), line 481) — The state as the workbench places it: the about-step's placement hash, the per-problem help style, and the check's rivals beside the item's own (deduplicated by statement).
- `class Suggestion` ([source](../../../../../../src/learnloop/hints/workbench.py), line 502) — The rung the ladder marks *suggested (why?)*, and how it was chosen.
  - `as_dict(self) -> dict[str, Any]` (line 517; public)
- `fixed_kind(level: int, option_set: OptionSet, state: HintState, item: Any) -> tuple[str, int | None]` ([source](../../../../../../src/learnloop/hints/workbench.py), line 526) — A rung's fixed kind under the fallback (spec §5.5), and the authored hint it serves at rung 3 while one remains.
- `rung_labels(context: WorkbenchHintContext, option_set: OptionSet) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/hints/workbench.py), line 543) — The five rungs as the ladder shows them: every one takeable (W11).
- `suggest(vault: Any, repository: Repository, state: HintState, context: WorkbenchHintContext, item: Any, *, fallback_level: int, assist_id: str, client_factory: Callable[[], Any] | None, seed: str | None, envelope: Any=None, clock: Any=None) -> Suggestion` ([source](../../../../../../src/learnloop/hints/workbench.py), line 596) — The suggested rung (spec §5.5): drawn from the Decider's own probabilities over the five rungs' options, the propensity logged by H2a's chooser (its ``hint_choice`` ledger row); with the chooser off, timed out or unavailable, ``fallback_level`` (the Reader's progression) with it…
- `styled_level(progression: int, help_style: str | None) -> int` ([source](../../../../../../src/learnloop/hints/workbench.py), line 644) — The suggested rung with no judgment (owner capture 2026-10-25, B2): the Reader's progression (rung 1, then one above the last on the step, D8) read through the help style, so the stated preference moves the suggestion without a Decider too.
- `style_of(suggestion: Mapping[str, Any] | None) -> str | None` ([source](../../../../../../src/learnloop/hints/workbench.py), line 661) — The help style a suggestion was judged under (None on rows written before it was recorded).
- `decider_extra(context: WorkbenchHintContext) -> dict[str, Any]` ([source](../../../../../../src/learnloop/hints/workbench.py), line 671) — The workbench's additions to the Decider's typed state (spec §5.5 "the state it gets"): the last check's summary and its map placement.
- `suggestion_record(repository: Repository, judgment_id: str | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/hints/workbench.py), line 704) — A suggestion's ``hint_choice`` row (the Decider's vectors, the seed, the draw and its propensity), or None.
- `taken_choice(state: HintState, option_set: OptionSet, context: WorkbenchHintContext, item: Any, *, taken_level: int, suggestion: Mapping[str, Any] | None) -> Choice | None` ([source](../../../../../../src/learnloop/hints/workbench.py), line 729) — The kind served on a rung the learner took (spec §5.5, G63).
- `step_of(quote: str, context: WorkbenchHintContext) -> WorkbenchStep | None` ([source](../../../../../../src/learnloop/hints/workbench.py), line 799) — The one step a quote lies inside (spacing ignored), or None.
- `check_steps(check: Check, output: Any, *, target: Target, context: WorkbenchHintContext) -> Check` ([source](../../../../../../src/learnloop/hints/workbench.py), line 811) — The workbench's exact rules, added to H2a's check of one answer.
- `symbolic_enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop/hints/workbench.py), line 850) — ``workbench.symbolic_checks_enabled`` now (off by default, fix round 9), read through the one accessor (:mod:`learnloop.symbolic_view`).
- `text_fingerprint(text: str) -> str` ([source](../../../../../../src/learnloop/hints/workbench.py), line 859) — A fingerprint of a step's FULL text: FNV-1a (64-bit) over its UTF-8 bytes, as ``fnv1a64:<16 hex>``.
- `class HintClaim(WireModel)` ([source](../../../../../../src/learnloop/hints/workbench.py), line 877) — One checkable statement a workbench hint makes about a step, with its transformation in sympy syntax (the check's declared kinds).
- `class WorkbenchHintWriterOutputV1(HintWriterOutputV1)` ([source](../../../../../../src/learnloop/hints/workbench.py), line 896) — The writer's answer on the workbench: H2a's, plus the hint's claims (the practice screen's output, prompt and schema are unchanged).
- `verify_claims(check: Check, output: Any, *, target: Target, context: WorkbenchHintContext, verifier: ClaimVerifier | None, item: Any=None, current: Mapping[str, Any] | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/hints/workbench.py), line 920) — Check one answer's claims (level 2 and up): a claim about a step that does not exist, or one the verifier decides does not hold, fails the round (``wb_claim_failed:<step>``: re-asked once with the failure named, then H2a's downgrade "without its unverified claims"); every other…
- `row_columns(context: WorkbenchHintContext, *, level: int | None, taken_level: int | None, request: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/hints/workbench.py), line 996) — The workbench's columns on a hint row (Reader §5.7).
- `step_labels(context: WorkbenchHintContext) -> dict[str, Any]` ([source](../../../../../../src/learnloop/hints/workbench.py), line 1022) — *on your step 3 · continues from step 2* (D45, G60).
- `deliver_workbench(repository: Repository, assist_id: str, *, clock: Any=None, item: Any=None) -> tuple[str, dict[str, Any] | None]` ([source](../../../../../../src/learnloop/hints/workbench.py), line 1039) — Show a prepared workbench row (a check or a hint) through H2a's :func:`~learnloop.hints.service.deliver_hint` (its fence), in one transaction with the check that the row's submission was not admitted yet: the workbench submit stamps ``submitted_at`` on its rows BEFORE it reads t…
- `text_leaks(text: str, item: Any) -> bool` ([source](../../../../../../src/learnloop/hints/workbench.py), line 1060) — Whether a check's line would give the item's answer away (H2a's leak control: the tutor's overlap check and H1's ``gives_away``, which also catches a short numeric answer).
- `current_map_for(vault: Any, repository: Repository, practice_item_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/hints/workbench.py), line 1074) — The item's current approach map record (None with the maps off): the Reader reads maps only through the service.
- `map_for_prompt(record: Mapping[str, Any] | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/hints/workbench.py), line 1086) — The map as the check writer reads it: nodes with their labels and recognizers, the routes; never sent to a grader (W8).
- `place_steps(record: Mapping[str, Any] | None, claims: Sequence[tuple[str, str, str, str]]) -> dict[str, tuple[str | None, str | None]]` ([source](../../../../../../src/learnloop/hints/workbench.py), line 1100) — Validate the check's map claims for its valid steps: ``(chain, verdict, node, route)`` -> ``{chain: (node, route)}``.
- `schedule_map(vault: Any, sqlite_path: Any, practice_item_id: str, *, client: Any=None, builds: Any=None) -> None` ([source](../../../../../../src/learnloop/hints/workbench.py), line 1131) — A map built in the background when the workbench binds an item (§5.2), with H1's own switches, locks and envelope (``build_on_serve``).

### Module constants

- `SURFACE` ([src/learnloop/hints/workbench.py](../../../../../../src/learnloop/hints/workbench.py), line 67)
- `RUNGS` ([src/learnloop/hints/workbench.py](../../../../../../src/learnloop/hints/workbench.py), line 69)
- `REVEAL_PREFIX` ([src/learnloop/hints/workbench.py](../../../../../../src/learnloop/hints/workbench.py), line 71)
- `WORKBENCH_PROMPT_NOTE` ([src/learnloop/hints/workbench.py](../../../../../../src/learnloop/hints/workbench.py), line 72)
- `RUNG_LABELS` ([src/learnloop/hints/workbench.py](../../../../../../src/learnloop/hints/workbench.py), line 75)
- `DISCRIMINATING_RUNG_LABEL` ([src/learnloop/hints/workbench.py](../../../../../../src/learnloop/hints/workbench.py), line 82)
- `RUNG_CONSEQUENCE` ([src/learnloop/hints/workbench.py](../../../../../../src/learnloop/hints/workbench.py), line 83)
- `FALLBACK_WHY` ([src/learnloop/hints/workbench.py](../../../../../../src/learnloop/hints/workbench.py), line 84)
- `FALLBACK_KIND` ([src/learnloop/hints/workbench.py](../../../../../../src/learnloop/hints/workbench.py), line 88)
- `ERROR_KINDS` ([src/learnloop/hints/workbench.py](../../../../../../src/learnloop/hints/workbench.py), line 91)
- `CLAIM_STATEMENT_CHARS` ([src/learnloop/hints/workbench.py](../../../../../../src/learnloop/hints/workbench.py), line 912)
- `CLAIM_LABELS` ([src/learnloop/hints/workbench.py](../../../../../../src/learnloop/hints/workbench.py), line 913)

### Explicit exports

`__all__` declares:

- `symbolic_enabled`
- `text_fingerprint`
- `DISCRIMINATING_RUNG_LABEL`
- `ERROR_KINDS`
- `FALLBACK_KIND`
- `FALLBACK_WHY`
- `REVEAL_PREFIX`
- `RUNGS`
- `RUNG_CONSEQUENCE`
- `RUNG_LABELS`
- `SURFACE`
- `StepVerdict`
- `Suggestion`
- `WorkbenchHintContext`
- `WorkbenchStep`
- `apply_context`
- `check_rivals`
- `check_steps`
- `checkpoint_for`
- `current_map_for`
- `decider_extra`
- `deliver_workbench`
- `dependents`
- `fixed_kind`
- `ladder_options`
- `map_for_prompt`
- `place_steps`
- `reveal_basis`
- `row_columns`
- `rung_labels`
- `schedule_map`
- `standing_steps`
- `step_labels`
- `step_of`
- `suggest`
- `style_of`
- `styled_level`
- `suggestion_record`
- `taken_choice`
- `taken_options`
- `text_leaks`
- `verdict_from_record`
- `verdict_record`

## Internal implementation anchors

- `_waypoint_target(state: HintState) -> str | None` ([source](../../../../../../src/learnloop/hints/workbench.py), line 390) — After a goal to aim for at this placement (the about-step), levels 3+ aim at its target (spec §5.2 "waypoints, with care").
- `_adjust(option_set: OptionSet, state: HintState, context: WorkbenchHintContext) -> OptionSet` ([source](../../../../../../src/learnloop/hints/workbench.py), line 401) — The workbench's constraints on any option set: the discriminating switch, rung 1 is the discriminating question with rivals open (G37).
- `_why(state: HintState, context: WorkbenchHintContext, kind: str, level: int, horizon_index: int | None) -> str` ([source](../../../../../../src/learnloop/hints/workbench.py), line 560) — The chooser's inputs in plain words (spec §5.5 "what the learner sees").
- `_split(probabilities: Mapping[str, float]) -> str | None` ([source](../../../../../../src/learnloop/hints/workbench.py), line 582) — "It leaned between …" when the judgment was split: the second option carries at least half the top option's probability (a display line).
- `_rng(seed: str) -> random.Random` ([source](../../../../../../src/learnloop/hints/workbench.py), line 725)
- `_squash(text: str) -> str` ([source](../../../../../../src/learnloop/hints/workbench.py), line 795)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/hints/service|learnloop.hints.service]] — imports `module`; statically calls `apply_context`, `check_steps`, `decider_extra`, `row_columns`, `style_of`, `suggestion_record`, `taken_choice`, `taken_options`, `verify_claims`
- [[Reference/Modules/learnloop/workbench/check|learnloop.workbench.check]] — imports `module`; statically calls `StepVerdict`, `WorkbenchHintContext`, `current_map_for`, `map_for_prompt`, `place_steps`, `text_leaks`, `verdict_from_record`
- [[Reference/Modules/learnloop/workbench/ladder|learnloop.workbench.ladder]] — imports `module`; statically calls `WorkbenchHintContext`, `WorkbenchStep`, `checkpoint_for`, `standing_steps`, `symbolic_enabled`, `verdict_from_record`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]] — imports `module`; statically calls `schedule_map`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench_help|learnloop_sidecar.handlers.workbench_help]] — imports `module`; statically calls `apply_context`, `current_map_for`, `deliver_workbench`, `reveal_basis`, `step_labels`, `suggest`, `symbolic_enabled`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `spend_envelopes`; calls `spend_envelopes`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/help_assists|learnloop.db.stores.help_assists]] — imports `module`; calls `assist`
- [[Reference/Modules/learnloop/hints/chooser|learnloop.hints.chooser]] — imports `Choice`, `module`; calls `Choice`, `argmax`, `ask`, `draw`, `single_option_choice`
- [[Reference/Modules/learnloop/hints/contracts|learnloop.hints.contracts]] — imports `Check`, `Target`, `in_work`, `leak_flags`, `nodes_by_id`, `routes_by_id`; calls `in_work`, `leak_flags`, `nodes_by_id`, `routes_by_id`
- [[Reference/Modules/learnloop/hints/discriminating|learnloop.hints.discriminating]] — imports `Rival`, `rival_id`; calls `Rival`, `rival_id`
- [[Reference/Modules/learnloop/hints/kinds|learnloop.hints.kinds]] — imports `HORIZON_LABELS`, `KINDS`, `WORKED_HELP_MARK`, `WORKED_LEVELS`, `option_id`, `parse_option`; calls `option_id`, `parse_option`
- [[Reference/Modules/learnloop/hints/map_builder|learnloop.hints.map_builder]] — imports `current_map`, `schedule_build_on_serve`; calls `current_map`, `schedule_build_on_serve`
- [[Reference/Modules/learnloop/hints/options|learnloop.hints.options]] — imports `OFFERABLE`, `Option`, `OptionSet`, `build_options`, `precondition`; calls `Option`, `OptionSet`, `build_options`, `precondition`
- [[Reference/Modules/learnloop/hints/service|learnloop.hints.service]] — imports `module`; calls `deliver_hint`
- [[Reference/Modules/learnloop/hints/state|learnloop.hints.state]] — imports `HintState`
- [[Reference/Modules/learnloop/hints/writer|learnloop.hints.writer]] — imports `HintWriterOutputV1`
- [[Reference/Modules/learnloop/symbolic_view|learnloop.symbolic_view]] — imports `switch`, `symbolic_view`; calls `switch`, `symbolic_view`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `hashlib`, `json`, `random`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/hints/service|learnloop.hints.service]], [[Reference/Modules/learnloop/workbench/check|learnloop.workbench.check]], [[Reference/Modules/learnloop/workbench/ladder|learnloop.workbench.ladder]], [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]], [[Reference/Modules/learnloop_sidecar/handlers/workbench_help|learnloop_sidecar.handlers.workbench_help]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_owner_capture_1025.py](../../../../../../tests/test_owner_capture_1025.py) — direct import
  - `test_b2_the_workbench_fallback_suggestion_reads_the_style`
- [tests/test_reader_rw2b_fix15.py](../../../../../../tests/test_reader_rw2b_fix15.py) — direct import
  - `test_item1_the_choosers_state_reads_the_switch_now`
- [tests/test_reader_rw2b_fix5.py](../../../../../../tests/test_reader_rw2b_fix5.py) — direct import
  - `test_item3_the_snapshot_and_the_check_view_carry_a_full_text_fingerprint`
- [tests/test_reader_rw2b_review.py](../../../../../../tests/test_reader_rw2b_review.py) — direct import
  - `test_f3r_a_hints_claim_about_part_of_a_side_is_the_models_reading`
- [tests/test_workbench_assistance.py](../../../../../../tests/test_workbench_assistance.py) — direct import
  - `test_a_row_is_never_shown_once_its_submission_is_admitted`
- [tests/test_workbench_chooser.py](../../../../../../tests/test_workbench_chooser.py) — direct import
  - `test_another_rung_draws_its_kind_conditional_on_the_level_from_the_same_vector`
  - `test_without_a_judgment_the_ladder_suggests_rung_one_then_one_rung_up_per_press`
- [tests/test_workbench_hint_service.py](../../../../../../tests/test_workbench_hint_service.py) — direct import
  - `test_a_workbench_request_without_its_steps_is_refused_and_a_practice_one_with_them_too`
  - `test_every_workbench_hint_comes_from_request_hint_and_the_suggestion_from_the_service`
- [tests/test_workbench_step_graph.py](../../../../../../tests/test_workbench_step_graph.py) — direct import
  - `test_a_questionable_step_fells_only_its_dependents`
  - `test_the_questionable_step_is_never_the_checkpoint_and_stuck_steps_never_stand`
  - `test_without_a_graph_the_steps_before_the_first_questionable_one_stand`

## Modification guidance

- Make changes here when the responsibility remains workbench within learnloop.hints; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/hints/workbench.py](../../../../../../src/learnloop/hints/workbench.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
