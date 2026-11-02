---
title: "learnloop.hints.chooser"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/hints/chooser.py"
source_paths:
  - "src/learnloop/hints/chooser.py"
source_commit: "e6d3c96710df3cbdb228f505cada139d72f82cda"
source_commit_timestamp: "2026-11-01T19:56:33-05:00"
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
  - "learnloop.hints.chooser module"
  - "src/learnloop/hints/chooser.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-hints"
---

# `learnloop.hints.chooser`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.hints.chooser` exists within [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] to own the behavior summarized by its module contract: Adaptive hints H2a: the chooser, a judgment over typed state (spec §4.5, D3, D4, G-H7, G-H8).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/hints/chooser.py](../../../../../../src/learnloop/hints/chooser.py) |
| Source lines | 449 |
| Owning package | [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `e6d3c96710df3cbdb228f505cada139d72f82cda` |
| Commit timestamp | `2026-11-01T19:56:33-05:00` |

## Public API

- `class Choice` ([source](../../../../../../src/learnloop/hints/chooser.py), line 118) — One decision: what is served, by whom, with what propensity.
  - `option(self) -> str` (line 142; public)
  - `drawn(self) -> dict[str, Any]` (line 145; public)
  - `as_dict(self) -> dict[str, Any]` (line 149; public)
- `new_seed() -> str` ([source](../../../../../../src/learnloop/hints/chooser.py), line 153) — A fresh seed for one draw (logged; :func:`draw` reproduces from it).
- `draw(probabilities: Mapping[Any, float], rng: random.Random) -> tuple[Any, float]` ([source](../../../../../../src/learnloop/hints/chooser.py), line 163) — One draw from ``probabilities`` (normalized over their sum), in the mapping's order; returns the drawn key and the probability it was drawn with.
- `argmax(probabilities: Mapping[Any, float]) -> Any` ([source](../../../../../../src/learnloop/hints/chooser.py), line 186) — The first option with the top probability (the question's order breaks a tie).
- `kind_question(option_set: OptionSet) -> ChoiceQuestion` ([source](../../../../../../src/learnloop/hints/chooser.py), line 193)
- `horizon_question() -> ScoreQuestion` ([source](../../../../../../src/learnloop/hints/chooser.py), line 201)
- `decider_state(state: HintState, option_set: OptionSet, *, request: str, shortcut: str | None, where: str | None=None, extra_state: Mapping[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/hints/chooser.py), line 210)
- `fallback_choice(option_set: OptionSet, state: HintState, item: Any, *, request: str, shortcut: str | None, reason: str) -> Choice | None` ([source](../../../../../../src/learnloop/hints/chooser.py), line 223) — §4.5's fallback for the practice screen, or None when nothing can be served (no authored hint left and no option).
- `learner_pick_choice(option_set: OptionSet) -> Choice` ([source](../../../../../../src/learnloop/hints/chooser.py), line 276)
- `single_option_choice(option_set: OptionSet) -> Choice` ([source](../../../../../../src/learnloop/hints/chooser.py), line 282) — One option left (a taken level with one kind, a reply that leaves one): the learner's taken level or reply fixed it; propensity 1 (G-H7).
- `ask(*, config: Any, repository: Any, state: HintState, option_set: OptionSet, request: str, shortcut: str | None, assist_id: str, client_factory: Callable[[], Any] | None, seed: str | None=None, clock: Any=None, where: str | None=None, extra_state: Mapping[str, Any] | None=None) -> Choice` ([source](../../../../../../src/learnloop/hints/chooser.py), line 301) — Ask the Decider and draw; a failure falls back (the caller serves the fallback when this answers ``chooser = 'fallback'`` with no kind).
- `policy_version(policy: str | None) -> str` ([source](../../../../../../src/learnloop/hints/chooser.py), line 418) — A served row's ``policy_version`` for a choice made under ``policy`` (``sample``, ``argmax`` or ``fallback``): the fallback's own version for a fallback choice (fix round 2, item 3), else the Decider policy's.

### Module constants

- `ROUTE` ([src/learnloop/hints/chooser.py](../../../../../../src/learnloop/hints/chooser.py), line 57)
- `TASK` ([src/learnloop/hints/chooser.py](../../../../../../src/learnloop/hints/chooser.py), line 59)
- `LEDGER_TASK` ([src/learnloop/hints/chooser.py](../../../../../../src/learnloop/hints/chooser.py), line 60)
- `QUESTION_SET_VERSION` ([src/learnloop/hints/chooser.py](../../../../../../src/learnloop/hints/chooser.py), line 61)
- `POLICY_VERSION` ([src/learnloop/hints/chooser.py](../../../../../../src/learnloop/hints/chooser.py), line 62)
- `FALLBACK_POLICY_VERSION` ([src/learnloop/hints/chooser.py](../../../../../../src/learnloop/hints/chooser.py), line 68)
- `KIND_QUESTION` ([src/learnloop/hints/chooser.py](../../../../../../src/learnloop/hints/chooser.py), line 69)
- `HORIZON_QUESTION` ([src/learnloop/hints/chooser.py](../../../../../../src/learnloop/hints/chooser.py), line 70)
- `_DESCRIBE` ([src/learnloop/hints/chooser.py](../../../../../../src/learnloop/hints/chooser.py), line 72)
- `_INSTRUCTIONS` ([src/learnloop/hints/chooser.py](../../../../../../src/learnloop/hints/chooser.py), line 98)
- `_HORIZON_INSTRUCTIONS` ([src/learnloop/hints/chooser.py](../../../../../../src/learnloop/hints/chooser.py), line 111)
- `PRACTICE_WHERE` ([src/learnloop/hints/chooser.py](../../../../../../src/learnloop/hints/chooser.py), line 207)

### Explicit exports

`__all__` declares:

- `Choice`
- `FALLBACK_POLICY_VERSION`
- `HORIZON_QUESTION`
- `KIND_QUESTION`
- `LEDGER_TASK`
- `POLICY_VERSION`
- `QUESTION_SET_VERSION`
- `ROUTE`
- `TASK`
- `argmax`
- `ask`
- `decider_state`
- `draw`
- `fallback_choice`
- `horizon_question`
- `kind_question`
- `learner_pick_choice`
- `new_seed`
- `policy_version`
- `single_option_choice`

## Internal implementation anchors

- `_rng(seed: str) -> random.Random` ([source](../../../../../../src/learnloop/hints/chooser.py), line 159)
- `_allowed_horizons(option_set: OptionSet) -> list[int]` ([source](../../../../../../src/learnloop/hints/chooser.py), line 291) — Rubric indices a waypoint may take: a waypoint is at least two steps ahead (index 1 and up); ``too_big`` bounds it below the answered one.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/hints/service|learnloop.hints.service]] — imports `Choice`, `module`; statically calls `ask`, `fallback_choice`, `learner_pick_choice`, `policy_version`, `single_option_choice`
- [[Reference/Modules/learnloop/hints/workbench|learnloop.hints.workbench]] — imports `Choice`, `module`; statically calls `Choice`, `argmax`, `ask`, `draw`, `single_option_choice`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/decisions|learnloop.ai.decisions]] — imports `ChoiceQuestion`, `ScoreQuestion`, `choice_probabilities`; calls `ChoiceQuestion`, `ScoreQuestion`, `choice_probabilities`
- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIProviderUnavailable`; calls `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendLimitExceeded`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/decider_judgments|learnloop.decider_judgments]] — imports `ask_decider`; calls `ask_decider`
- [[Reference/Modules/learnloop/hints/kinds|learnloop.hints.kinds]] — imports `FALLBACK_ORDER`, `HORIZON_LEVELS`, `parse_option`; calls `parse_option`
- [[Reference/Modules/learnloop/hints/options|learnloop.hints.options]] — imports `OptionSet`
- [[Reference/Modules/learnloop/hints/state|learnloop.hints.state]] — imports `HintState`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `hashlib`, `json`, `random`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/hints/service|learnloop.hints.service]], [[Reference/Modules/learnloop/hints/workbench|learnloop.hints.workbench]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_approach_map_replay.py](../../../../../../tests/test_approach_map_replay.py) — direct import
- [tests/test_hint_service.py](../../../../../../tests/test_hint_service.py) — direct import
  - `test_a_seed_reproduces_the_draw`
  - `test_every_decider_request_is_one_hint_choice_row_with_labelled_receipts`
- [tests/test_owner_capture_1025.py](../../../../../../tests/test_owner_capture_1025.py) — direct import
  - `test_b2_a_suggestion_judged_under_another_style_is_not_reused`
  - `test_fix2_a_changed_fallback_names_its_new_policy_version`
- [tests/test_workbench_chooser.py](../../../../../../tests/test_workbench_chooser.py) — direct import
  - `test_another_rung_draws_its_kind_conditional_on_the_level_from_the_same_vector`
  - `test_one_decider_request_over_every_rung_with_the_workbenchs_typed_state`

## Modification guidance

- Make changes here when the responsibility remains chooser within learnloop.hints; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/hints/chooser.py](../../../../../../src/learnloop/hints/chooser.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
