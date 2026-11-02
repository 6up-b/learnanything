---
title: "learnloop.field.probability_states"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/field/probability_states.py"
source_paths:
  - "src/learnloop/field/probability_states.py"
source_commit: "69e72f05325649681eefa5c5d2c9dac139e89f1c"
source_commit_timestamp: "2026-10-12T13:59:49-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.field"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.field.probability_states module"
  - "src/learnloop/field/probability_states.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-field"
---

# `learnloop.field.probability_states`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/field/_package|learnloop.field]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.field.probability_states` exists within [[Reference/Modules/learnloop/field/_package|learnloop.field]] to own the behavior summarized by its module contract: The ``state`` each ``llm_probability`` variant sends (field spec §7.2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/field/probability_states.py](../../../../../../src/learnloop/field/probability_states.py) |
| Source lines | 804 |
| Owning package | [[Reference/Modules/learnloop/field/_package|learnloop.field]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `69e72f05325649681eefa5c5d2c9dac139e89f1c` |
| Commit timestamp | `2026-10-12T13:59:49-04:00` |

## Public API

- `estimate_tokens(value: Any) -> int` ([source](../../../../../../src/learnloop/field/probability_states.py), line 110) — UTF-8 bytes / 4, rounded up: the Slice 1 context estimator.
- `canonical_json(value: Any) -> str` ([source](../../../../../../src/learnloop/field/probability_states.py), line 117)
- `state_hash(state: Any) -> str` ([source](../../../../../../src/learnloop/field/probability_states.py), line 121)
- `excerpt(text: str | None, limit: int) -> str` ([source](../../../../../../src/learnloop/field/probability_states.py), line 125)
- `class PredictionPoint` ([source](../../../../../../src/learnloop/field/probability_states.py), line 148) — One harness prediction: the row, and what the harness observed before it.
- `class StateRenderer` ([source](../../../../../../src/learnloop/field/probability_states.py), line 163) — Reads one read-only vault snapshot; renders deterministic states.
  - `__init__(self, vault: LoadedVault, connection: sqlite3.Connection, *, rows: Iterable[AttemptRow]=()) -> None` (line 171; internal)
  - `cutoff(self, attempt_id: str) -> datetime | None` (line 210; public) — The latest instant the attempt provably had not begun, or ``None``.
  - `_item(self, row: AttemptRow) -> PracticeItem | None` (line 236; internal) — The graded revision for an ``exact`` row; today's content only when labelled.
  - `_grading_rows(self) -> tuple[dict[str, dict[str, float]], dict[str, set[Any]]]` (line 262; internal) — Per attempt: the latest surviving points per criterion and the contracts they cite.
  - `_rubric(self, row: AttemptRow) -> Rubric | None` (line 278; internal) — The rubric the revision policy allows: frozen for ``exact``, today's when labelled.
  - `_lo_title(self, lo_id: str) -> str` (line 304; internal)
  - `_facet_titles(self, item: PracticeItem | None) -> list[str]` (line 308; internal)
  - `item_view(self, row: AttemptRow) -> dict[str, Any]` (line 316; public) — V1's content: no reference solution, rubric, hints or answer.
  - `render(self, variant: str, point: PredictionPoint) -> dict[str, Any]` (line 349; public)
  - `_before(self, value: str | None, cutoff: datetime | None) -> bool` (line 361; internal)
  - `_window(self, point: PredictionPoint) -> list[dict[str, Any]]` (line 365; internal)
  - `_store(self) -> VaultHistoryStore` (line 380; internal)
  - `_scope(self, lo_id: str) -> dict[str, str]` (line 385; internal) — The LO, its same-concept LOs and its one-hop prerequisites.
  - `_question_rows(self) -> list[dict[str, Any]]` (line 396; internal)
  - `_mutable_rows(self) -> tuple[dict[tuple[str, str], tuple[datetime | None, datetime | None]], dict[str, list[tuple[datetime, str]]]]` (line 407; internal) — Mutable hypothesis rows' write times and misconception transitions.
  - `_status_as_of(self, record: HypothesisRecord, cutoff: datetime) -> str` (line 429; internal) — A hypothesis's lifecycle as it stood at the cutoff.
  - `_card(self, point: PredictionPoint) -> dict[str, Any]` (line 450; internal)
  - `_facet_title(self, facet_id: str) -> str` (line 581; internal)
  - `_hypotheses(self, store: VaultHistoryStore, scope: Mapping[str, str], titles: Mapping[str, str], cutoff: datetime, verified: Sequence[tuple[HistoryAttempt, AttemptRow]], refs: Mapping[str, str], facets_by_attempt: Mapping[str, frozenset[str]]) -> list[dict[str, Any]]` (line 585; internal) — Typed prior hypotheses as of the cutoff, each with its evidence.
- `history_pairs(history: Sequence[AttemptRow]) -> list[tuple[str, float]]` ([source](../../../../../../src/learnloop/field/probability_states.py), line 781)
- `start_index(times: Sequence[datetime], cutoff: datetime | None) -> int` ([source](../../../../../../src/learnloop/field/probability_states.py), line 785) — How many time-ordered observations precede ``cutoff`` strictly (0 if unknown).

### Module constants

- `STATE_VERSION` ([src/learnloop/field/probability_states.py](../../../../../../src/learnloop/field/probability_states.py), line 76)
- `VARIANTS` ([src/learnloop/field/probability_states.py](../../../../../../src/learnloop/field/probability_states.py), line 77)
- `V2_WINDOW` ([src/learnloop/field/probability_states.py](../../../../../../src/learnloop/field/probability_states.py), line 78)
- `CARD_TOKEN_BUDGET` ([src/learnloop/field/probability_states.py](../../../../../../src/learnloop/field/probability_states.py), line 80)
- `STEM_LIMIT` ([src/learnloop/field/probability_states.py](../../../../../../src/learnloop/field/probability_states.py), line 81)
- `HISTORY_STEM_LIMIT` ([src/learnloop/field/probability_states.py](../../../../../../src/learnloop/field/probability_states.py), line 82)
- `ANSWER_LIMIT` ([src/learnloop/field/probability_states.py](../../../../../../src/learnloop/field/probability_states.py), line 83)
- `QUOTE_LIMIT` ([src/learnloop/field/probability_states.py](../../../../../../src/learnloop/field/probability_states.py), line 84)
- `QUESTION_LIMIT` ([src/learnloop/field/probability_states.py](../../../../../../src/learnloop/field/probability_states.py), line 85)
- `STATEMENT_LIMIT` ([src/learnloop/field/probability_states.py](../../../../../../src/learnloop/field/probability_states.py), line 86)
- `V3_MAX_ATTEMPTS` ([src/learnloop/field/probability_states.py](../../../../../../src/learnloop/field/probability_states.py), line 88)
- `MAX_EVIDENCE_REFS` ([src/learnloop/field/probability_states.py](../../../../../../src/learnloop/field/probability_states.py), line 91)
- `HISTORY_WITHHELD` ([src/learnloop/field/probability_states.py](../../../../../../src/learnloop/field/probability_states.py), line 93)
- `NOT_RECORDED` ([src/learnloop/field/probability_states.py](../../../../../../src/learnloop/field/probability_states.py), line 99)
- `_MISCONCEPTION_LIFECYCLE` ([src/learnloop/field/probability_states.py](../../../../../../src/learnloop/field/probability_states.py), line 102)
- `UNKNOWN_AS_OF` ([src/learnloop/field/probability_states.py](../../../../../../src/learnloop/field/probability_states.py), line 107)

### Explicit exports

`__all__` declares:

- `CARD_TOKEN_BUDGET`
- `HISTORY_WITHHELD`
- `PredictionPoint`
- `STATE_VERSION`
- `StateRenderer`
- `V2_WINDOW`
- `VARIANTS`
- `canonical_json`
- `estimate_tokens`
- `excerpt`
- `start_index`
- `state_hash`

## Internal implementation anchors

- `_instant(value: Any) -> datetime | None` ([source](../../../../../../src/learnloop/field/probability_states.py), line 130)
- `_result(outcome: float) -> str` ([source](../../../../../../src/learnloop/field/probability_states.py), line 139)
- `_iso(instant: datetime) -> str` ([source](../../../../../../src/learnloop/field/probability_states.py), line 678) — The vault's own timestamp form (whole seconds, ``Z``).
- `_days(value: str | None, cutoff: datetime | None) -> float | None` ([source](../../../../../../src/learnloop/field/probability_states.py), line 684)
- `_bounded(entries: list[dict[str, Any]], *, keep_first: bool=False) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/field/probability_states.py), line 691) — The most recent references; the diagnosing attempt always stays.
- `_cited(entry: Mapping[str, Any], kept: set[Any], dropped: set[Any], *, key: str='ref', flag: str='in_recent_work') -> Mapping[str, Any]` ([source](../../../../../../src/learnloop/field/probability_states.py), line 701) — The entry, marked when the work entry its reference names was dropped.
- `_strip_private(card: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/field/probability_states.py), line 712) — The card as sent: private keys gone, every reference reconciled (re-review F8).
- `_fit(card: dict[str, Any], budget: int=CARD_TOKEN_BUDGET) -> dict[str, Any]` ([source](../../../../../../src/learnloop/field/probability_states.py), line 742) — Truncate to the card budget in the router spec's order; typed fields stay.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/probability_arms|learnloop.cli.probability_arms]] — imports `StateRenderer`; statically calls `StateRenderer`
- [[Reference/Modules/learnloop/field/probability_prep|learnloop.field.probability_prep]] — imports `PredictionPoint`, `STATE_VERSION`, `StateRenderer`, `canonical_json`, `history_pairs`, `start_index`, `state_hash`; statically calls `PredictionPoint`, `canonical_json`, `history_pairs`, `start_index`, `state_hash`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]] — imports `AttemptRef`, `HistoryAttempt`, `HypothesisRecord`, `VaultHistoryStore`, `learning_object_neighborhood`; calls `AttemptRef`, `VaultHistoryStore`, `learning_object_neighborhood`
- [[Reference/Modules/learnloop/field/outcomes|learnloop.field.outcomes]] — imports `borrowed_repository`; calls `borrowed_repository`
- [[Reference/Modules/learnloop/field/types|learnloop.field.types]] — imports `AttemptRow`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `rubric_from_contract`; calls `rubric_from_contract`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`, `Rubric`

### Platform and third-party dependencies

- Standard library: `__future__`, `bisect`, `collections`, `dataclasses`, `datetime`, `hashlib`, `json`, `math`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/probability_arms|learnloop.cli.probability_arms]], [[Reference/Modules/learnloop/field/probability_prep|learnloop.field.probability_prep]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_probability_prep.py](../../../../../../tests/test_probability_prep.py) — direct import
  - `test_budget_truncation_never_leaves_an_evidence_reference_dangling`
  - `test_grading_time_never_moves_the_cutoff_and_an_unknown_start_withholds_history`
  - `test_v3_budget_drops_successes_then_excerpts_then_attempts_never_typed_fields`

## Modification guidance

- Make changes here when the responsibility remains probability states within learnloop.field; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/field/probability_states.py](../../../../../../src/learnloop/field/probability_states.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
