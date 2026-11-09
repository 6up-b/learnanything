---
title: "learnloop.matching.judge"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/matching/judge.py"
source_paths:
  - "src/learnloop/matching/judge.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.matching"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.matching.judge module"
  - "src/learnloop/matching/judge.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-matching"
---

# `learnloop.matching.judge`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/matching/_package|learnloop.matching]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.matching.judge` exists within [[Reference/Modules/learnloop/matching/_package|learnloop.matching]] to own the behavior summarized by its module contract: The judge decides; every verdict goes to ``judgment_ledger`` (Slice 2 R4, §5.8).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/matching/judge.py](../../../../../../src/learnloop/matching/judge.py) |
| Source lines | 350 |
| Owning package | [[Reference/Modules/learnloop/matching/_package|learnloop.matching]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class SameOrDifferent(WireModel)` ([source](../../../../../../src/learnloop/matching/judge.py), line 73) — A pairwise verdict.
- `class Executor(Protocol)` ([source](../../../../../../src/learnloop/matching/judge.py), line 84) — One admitted, isolated structured call; ``producer`` is known before it.
  - `__call__(self, prompt: str, result_model: type[SameOrDifferent], purpose: str) -> tuple[SameOrDifferent, str]` (line 93; internal)
- `ordered(left: Subject, right: Subject) -> tuple[Subject, Subject]` ([source](../../../../../../src/learnloop/matching/judge.py), line 96) — A presentation order that depends on ids only, never on rank.
- `pair_prompt(kind: MatchKind, left: Subject, right: Subject) -> str` ([source](../../../../../../src/learnloop/matching/judge.py), line 102)
- `pair_input_hash(kind: MatchKind, left: Subject, right: Subject) -> str` ([source](../../../../../../src/learnloop/matching/judge.py), line 114) — The exact input a verdict was given: both subjects' content, unordered.
- `claim_key(kind: MatchKind, producer: str, input_hash: str, *, judge: str=DEFAULT_JUDGE) -> str` ([source](../../../../../../src/learnloop/matching/judge.py), line 130) — The work item: one question to one producer under one prompt and input.
- `already_judged(connection: Any, kind: MatchKind, left: Subject, right: Subject, *, input_hash: str, producer: str | None, judge: str=DEFAULT_JUDGE) -> bool` ([source](../../../../../../src/learnloop/matching/judge.py), line 145) — A verdict exists for this pair, prompt and input FROM THIS PRODUCER (and judge label).
- `class JudgedPair` ([source](../../../../../../src/learnloop/matching/judge.py), line 188)
  - `as_dict(self) -> dict[str, Any]` (line 201; public)
- `judge_pairs(repository: Any, kind: MatchKind, pairs: Sequence[CandidatePair], *, execute: Callable[..., Any], producer: str | None=None, judge: str | None=None, rerun: bool=False, stop_on: tuple[type[BaseException], ...]=(SpendLimitExceeded, AIInterrupted), lease_seconds: int=DEFAULT_LEASE_SECONDS, now: Callable[[], str]=utc_now_iso) -> list[JudgedPair]` ([source](../../../../../../src/learnloop/matching/judge.py), line 215) — Judge each pair once per producer; stop (leaving the rest ``not_run``) on spend or cancel.

### Module constants

- `_COMMON_RULES` ([src/learnloop/matching/judge.py](../../../../../../src/learnloop/matching/judge.py), line 61)
- `DEFAULT_LEASE_SECONDS` ([src/learnloop/matching/judge.py](../../../../../../src/learnloop/matching/judge.py), line 70)
- `DEFAULT_JUDGE` ([src/learnloop/matching/judge.py](../../../../../../src/learnloop/matching/judge.py), line 81)

### Explicit exports

`__all__` declares:

- `DEFAULT_JUDGE`
- `DEFAULT_LEASE_SECONDS`
- `Executor`
- `JudgedPair`
- `SameOrDifferent`
- `already_judged`
- `claim_key`
- `judge_pairs`
- `ordered`
- `pair_input_hash`
- `pair_prompt`

## Internal implementation anchors

- `_pair_clause(left: Subject, right: Subject) -> tuple[str, tuple[Any, ...]]` ([source](../../../../../../src/learnloop/matching/judge.py), line 137)
- `_previous_verdict(connection: Any, kind: MatchKind, left: Subject, right: Subject, *, producer: str, judge: str=DEFAULT_JUDGE) -> tuple[str, Subject, Subject] | None` ([source](../../../../../../src/learnloop/matching/judge.py), line 167) — This producer's latest standing verdict on the pair (id, its orientation).
- `_release(repository: Any, key: str, owner: str, epoch: int, now: Callable[[], str]) -> None` ([source](../../../../../../src/learnloop/matching/judge.py), line 330)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/recurrence/backlog|learnloop.diagnosis.recurrence.backlog]] — imports `already_judged`, `judge_pairs`, `pair_input_hash`, `pair_prompt`; statically calls `already_judged`, `judge_pairs`, `pair_input_hash`, `pair_prompt`
- [[Reference/Modules/learnloop/diagnosis/recurrence/guard|learnloop.diagnosis.recurrence.guard]] — imports `already_judged`, `judge_pairs`, `pair_input_hash`, `pair_prompt`; statically calls `already_judged`, `judge_pairs`, `pair_input_hash`, `pair_prompt`
- [[Reference/Modules/learnloop/diagnosis/recurrence/judging|learnloop.diagnosis.recurrence.judging]] — imports `SameOrDifferent`
- [[Reference/Modules/learnloop/diagnosis/recurrence/live|learnloop.diagnosis.recurrence.live]] — imports `judge_pairs`; statically calls `judge_pairs`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/judges|learnloop.diagnosis.text_gaps.judges]] — imports `SameOrDifferent`; statically calls `SameOrDifferent`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/pipeline|learnloop.diagnosis.text_gaps.pipeline]] — imports `JudgedPair`, `judge_pairs`, `pair_input_hash`; statically calls `JudgedPair`, `judge_pairs`, `pair_input_hash`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/tier1|learnloop.diagnosis.text_gaps.tier1]] — imports `JudgedPair`, `SameOrDifferent`, `judge_pairs`, `pair_input_hash`; statically calls `judge_pairs`, `pair_input_hash`
- [[Reference/Modules/learnloop/matching/__init__|learnloop.matching]] — imports `JudgedPair`, `SameOrDifferent`, `judge_pairs`, `pair_input_hash`, `pair_prompt`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendLimitExceeded`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`
- [[Reference/Modules/learnloop/db/stores/judgment_claims|learnloop.db.stores.judgment_claims]] — imports `CLAIMED`, `HELD`, `claim_work`, `complete_claim`, `holds_claim`, `release_claim`; calls `claim_work`, `complete_claim`, `holds_claim`, `release_claim`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/matching/kinds|learnloop.matching.kinds]] — imports `MatchKind`, `Subject`
- [[Reference/Modules/learnloop/matching/shortlist|learnloop.matching.shortlist]] — imports `CandidatePair`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `typing`, `uuid`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/recurrence/backlog|learnloop.diagnosis.recurrence.backlog]], [[Reference/Modules/learnloop/diagnosis/recurrence/guard|learnloop.diagnosis.recurrence.guard]], [[Reference/Modules/learnloop/diagnosis/recurrence/judging|learnloop.diagnosis.recurrence.judging]], [[Reference/Modules/learnloop/diagnosis/recurrence/live|learnloop.diagnosis.recurrence.live]], [[Reference/Modules/learnloop/diagnosis/text_gaps/judges|learnloop.diagnosis.text_gaps.judges]] and 3 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/recurrence_fakes.py](../../../../../../tests/recurrence_fakes.py) — direct import
- [tests/test_learner_text_gaps_review.py](../../../../../../tests/test_learner_text_gaps_review.py) — direct import
  - `test_f1_a_fenced_pair_is_not_a_verdict`
- [tests/test_matching.py](../../../../../../tests/test_matching.py) — direct import
  - `test_presentation_order_and_input_hash_ignore_rank_and_side`
- [tests/test_recurrence_commands.py](../../../../../../tests/test_recurrence_commands.py) — direct import
  - `test_verdicts_split_across_two_models_do_not_pass_for_the_configured_one`
- [tests/text_gap_fakes.py](../../../../../../tests/text_gap_fakes.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains judge within learnloop.matching; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/matching/judge.py](../../../../../../src/learnloop/matching/judge.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
