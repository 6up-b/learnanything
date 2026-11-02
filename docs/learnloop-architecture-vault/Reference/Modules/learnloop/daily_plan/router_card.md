---
title: "learnloop.daily_plan.router_card"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/router_card.py"
source_paths:
  - "src/learnloop/daily_plan/router_card.py"
source_commit: "781534a7a0b9efe28f58a33873e4859f5f86817a"
source_commit_timestamp: "2026-11-01T19:08:46-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.daily_plan"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.daily_plan.router_card module"
  - "src/learnloop/daily_plan/router_card.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.router_card`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.router_card` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: Router R2a: gathering ``LearnerStateCardV1``'s inputs at a plan boundary.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/router_card.py](../../../../../../src/learnloop/daily_plan/router_card.py) |
| Source lines | 697 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `781534a7a0b9efe28f58a33873e4859f5f86817a` |
| Commit timestamp | `2026-11-01T19:08:46-05:00` |

## Public API

- `class CardText` ([source](../../../../../../src/learnloop/daily_plan/router_card.py), line 140) — The card's text rule (plan §3.6, gate G5), a parameter of the shared protection (``learner_protection.TextRule``).
  - `__init__(self, past: PastWork) -> None` (line 147; internal)
  - `question(self, attempt_id: str, lo_id: Any) -> tuple[str | None, str | None]` (line 150; public)
  - `answer(self, attempt_id: str, text: Any, limit: int) -> tuple[str | None, str | None]` (line 155; public)
  - `statement(self, kind: str, record_id: Any, text: Any, limit: int, *, answers: Any=(), items: Any=(), los: Any=()) -> tuple[str | None, str | None]` (line 159; public)
- `class CardGatherer` ([source](../../../../../../src/learnloop/daily_plan/router_card.py), line 164) — Builds the card for one plan decision (``StagedChooser.card_builder``).
  - `__init__(self, vault: Any, repository: Any, *, clock: Any=None, session_id: str | None=None) -> None` (line 167; internal)
  - `__call__(self, state: PlanState, feasible: Sequence[BlockCandidate]) -> LearnerStateCard` (line 173; internal)
  - `inputs(self, state: PlanState, feasible: Sequence[BlockCandidate], *, now_iso: str) -> CardInputs` (line 182; public)
  - `_reader_activity(self, los: Sequence[str], now_iso: str, unknowns: list[str]) -> dict[str, Any] | None` (line 270; internal) — The card's copy of ``ReaderActivityV1`` (RW6b part 2), or None (switched off, or nothing on these LOs).
  - `_confidence(connection: Any, attempts: Sequence[Mapping[str, Any]], candidate_los: Sequence[str], recent: list[dict[str, Any]], held: frozenset[str], now_iso: str, unknowns: list[str]) -> tuple[dict[str, list[dict[str, Any]]], str | None, int]` (line 288; internal) — TE0 (spec_teacher_v1 §15.2): the confidence events.
  - `_evidence_sections(connection: Any, los: Sequence[str], titles: Mapping[str, str], now_iso: str, withheld: Withheld, unknowns: list[str]) -> dict[str, Any]` (line 333; internal) — The typed evidence registry (R2a's hook).
  - `_candidate(candidate: BlockCandidate, titles: Mapping[str, str]) -> dict[str, Any]` (line 353; internal)
  - `_attempts(self, connection: Any, los: Sequence[str], now_iso: str) -> list[dict[str, Any]]` (line 369; internal)
  - `_classes(self, los: Sequence[str], now_iso: str, unknowns: list[str]) -> dict[str, str] | None` (line 383; internal) — The Today headline's class of each LO (review F7), or None when it cannot be read (then no topic is demonstrated or assumed).
  - `_learning_objects(self, los: Sequence[str], candidate_los: Sequence[str], attempts: Sequence[Mapping[str, Any]], held: frozenset[str], feasible: Sequence[BlockCandidate], titles: Mapping[str, str], now_iso: str, unknowns: list[str]) -> dict[str, dict[str, Any]]` (line 398; internal)
  - `_adaptive_difficulty(self, lo: str, unknowns: list[str]) -> dict[str, Any] | None` (line 487; internal)
  - `_interaction(self, connection: Any, now_iso: str, unknowns: list[str]) -> dict[str, Any]` (line 501; internal)
  - `_open_problems(self, connection: Any, los: set[str], titles: Mapping[str, str], unknowns: list[str], past: PastWork, rule: CardText) -> list[dict[str, Any]]` (line 526; internal)
  - `_self_reports(self, connection: Any, los: set[str], titles: Mapping[str, str], now_iso: str, unknowns: list[str]) -> list[dict[str, Any]]` (line 618; internal)
  - `_withheld_items(self, unknowns: list[str]) -> Withheld` (line 650; internal) — The items whose question and answers the card never shows: the shared predicate (``learner_protection.withheld_items``, the chat frontend's too): exam material by the one exam predicate, live assessment reservations, items a cold check or a repair's cold retry holds, diagnostic…
  - `_recent_work(self, attempts: Sequence[Mapping[str, Any]], held: frozenset[str], past: PastWork, rule: CardText, titles: Mapping[str, str]) -> list[dict[str, Any]]` (line 668; internal)

### Module constants

- `_LOG` ([src/learnloop/daily_plan/router_card.py](../../../../../../src/learnloop/daily_plan/router_card.py), line 93)
- `RECENT_WORK_LIMIT` ([src/learnloop/daily_plan/router_card.py](../../../../../../src/learnloop/daily_plan/router_card.py), line 96)
- `LEARNING_OBJECT_LIMIT` ([src/learnloop/daily_plan/router_card.py](../../../../../../src/learnloop/daily_plan/router_card.py), line 98)
- `OPEN_PROBLEM_LIMIT` ([src/learnloop/daily_plan/router_card.py](../../../../../../src/learnloop/daily_plan/router_card.py), line 99)
- `SELF_REPORT_LIMIT` ([src/learnloop/daily_plan/router_card.py](../../../../../../src/learnloop/daily_plan/router_card.py), line 100)
- `NOT_RECORDED` ([src/learnloop/daily_plan/router_card.py](../../../../../../src/learnloop/daily_plan/router_card.py), line 101)

### Explicit exports

`__all__` declares:

- `CardGatherer`
- `CardText`
- `RECENT_WORK_LIMIT`

## Internal implementation anchors

- `_sigmoid(value: float) -> float` ([source](../../../../../../src/learnloop/daily_plan/router_card.py), line 104)
- `_logit(p: float) -> float` ([source](../../../../../../src/learnloop/daily_plan/router_card.py), line 109)
- `_table(connection: Any, name: str) -> bool` ([source](../../../../../../src/learnloop/daily_plan/router_card.py), line 114)
- `_marks(values: Sequence[Any]) -> str` ([source](../../../../../../src/learnloop/daily_plan/router_card.py), line 118)
- `_status(klass: str | None, counts: Mapping[str, int] | None) -> str` ([source](../../../../../../src/learnloop/daily_plan/router_card.py), line 122) — A topic's status on the card (review F7).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/policy|learnloop.daily_plan.policy]] — imports `CardGatherer`; statically calls `CardGatherer`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/readiness|learnloop.adaptive_difficulty.readiness]] — imports `card_fields`; calls `card_fields`
- [[Reference/Modules/learnloop/adaptive_difficulty/successor|learnloop.adaptive_difficulty.successor]] — imports `subject_view_live`; calls `subject_view_live`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/confidence_events|learnloop.confidence_events]] — imports `module`; calls `enabled`, `event_text`, `readings`, `taps_before`, `taps_limit`
- [[Reference/Modules/learnloop/daily_plan/headline|learnloop.daily_plan.headline]] — imports `module`; calls `classify_learning_objects`
- [[Reference/Modules/learnloop/daily_plan/router_reader|learnloop.daily_plan.router_reader]] — imports `module`; calls `for_card`, `reader_activity_enabled`, `reader_activity_for_card`
- [[Reference/Modules/learnloop/daily_plan/router_teach_back|learnloop.daily_plan.router_teach_back]] — imports `module`; calls `summaries_for`
- [[Reference/Modules/learnloop/daily_plan/types|learnloop.daily_plan.types]] — imports `BlockCandidate`, `PlanState`
- [[Reference/Modules/learnloop/db/stores/daily_plans|learnloop.db.stores.daily_plans]] — imports `open_learner_state_hypotheses`; calls `open_learner_state_hypotheses`
- [[Reference/Modules/learnloop/db/stores/write_provenance|learnloop.db.stores.write_provenance]] — imports `read_snapshot`; calls `read_snapshot`
- [[Reference/Modules/learnloop/learner_protection|learnloop.learner_protection]] — imports `PastWork`, `Withheld`, `attempt_result`, `module`, `past_work_text`, `statement_text`; calls `PastWork`, `attempt_result`, `hypothesis_answers`, `past_work_text`, `statement_text`, `withheld_items`
- [[Reference/Modules/learnloop/placement/predictor|learnloop.placement.predictor]] — imports `active_predictor`; calls `active_predictor`
- [[Reference/Modules/learnloop/router/card|learnloop.router.card]] — imports `CardInputs`, `EXCERPT_LIMIT`, `LearnerStateCard`, `STATEMENT_LIMIT`, `STEM_LIMIT`, `build_card`, `excerpt`; calls `CardInputs`, `build_card`, `excerpt`
- [[Reference/Modules/learnloop/scheduling/fsrs|learnloop.scheduling.fsrs]] — imports `forgetting_curve`; calls `forgetting_curve`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `datetime`, `logging`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/policy|learnloop.daily_plan.policy]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_mcp_c1a_landing.py](../../../../../../tests/test_mcp_c1a_landing.py) — direct import
  - `test_no_reader_keeps_a_protection_of_its_own`
- [tests/test_reread_safety_landing.py](../../../../../../tests/test_reread_safety_landing.py) — direct import
- [tests/test_router_r2a_landing.py](../../../../../../tests/test_router_r2a_landing.py) — direct import
  - `test_the_card_withholds_what_the_one_exam_predicate_names`
  - `test_the_cards_exam_protection_is_not_behind_the_serving_switch`
- [tests/test_router_r2c_teach_back.py](../../../../../../tests/test_router_r2c_teach_back.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains router card within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/router_card.py](../../../../../../src/learnloop/daily_plan/router_card.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
