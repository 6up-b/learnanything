---
title: "learnloop.hints.writer"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/hints/writer.py"
source_paths:
  - "src/learnloop/hints/writer.py"
source_commit: "4d995af6881ed260cb561d070a1e429b7ad10deb"
source_commit_timestamp: "2026-10-25T02:02:48-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.hints"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
aliases:
  - "learnloop.hints.writer module"
  - "src/learnloop/hints/writer.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-hints"
---

# `learnloop.hints.writer`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.hints.writer` exists within [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] to own the behavior summarized by its module contract: Adaptive hints H2a: the writer, one structured call per hint (spec §4.4, §4.6, §7.2, D9).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/hints/writer.py](../../../../../../src/learnloop/hints/writer.py) |
| Source lines | 407 |
| Owning package | [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `4d995af6881ed260cb561d070a1e429b7ad10deb` |
| Commit timestamp | `2026-10-25T02:02:48-04:00` |

## Public API

- `models_off() -> bool` ([source](../../../../../../src/learnloop/hints/writer.py), line 68)
- `class HintPlacement(WireModel)` ([source](../../../../../../src/learnloop/hints/writer.py), line 76)
- `class PlanLabel(WireModel)` ([source](../../../../../../src/learnloop/hints/writer.py), line 92)
- `class Prediction(WireModel)` ([source](../../../../../../src/learnloop/hints/writer.py), line 98)
- `class Candidate(WireModel)` ([source](../../../../../../src/learnloop/hints/writer.py), line 103)
- `class WorkedPiece(WireModel)` ([source](../../../../../../src/learnloop/hints/writer.py), line 108)
- `class HintWriterOutputV1(WireModel)` ([source](../../../../../../src/learnloop/hints/writer.py), line 114)
- `build_prompt(vault: Any, item: Any, state: Any, target: Target, *, request_text: str | None=None, selection: str | None=None, feedback: Mapping[str, Any] | None=None, request_id: str | None=None, workbench: Mapping[str, Any] | None=None, confidence: Mapping[str, Any] | None=None) -> str` ([source](../../../../../../src/learnloop/hints/writer.py), line 203)
- `class WriterUnavailable(Exception)` ([source](../../../../../../src/learnloop/hints/writer.py), line 285) — The writer cannot run (``reason``: ``codex_refused`` | ``unrouted`` | ``unpriced`` | ``capped`` | ``unavailable`` | ``models_off``).
  - `__init__(self, reason: str, message: str) -> None` (line 289; internal)
- `class WriterRoute` ([source](../../../../../../src/learnloop/hints/writer.py), line 295) — The hint writer's pinned route for one request: its client, budget and the shared daily envelope.
  - `__init__(self, vault: Any, repository: Any, *, client: Any | None=None, envelope: Any=None, deadline: float | None=None) -> None` (line 299; internal)
  - `subscription(self) -> bool` (line 311; public)
  - `problem(self) -> WriterUnavailable | None` (line 314; public) — Why no hint can be written now (checked before the chooser is asked, so a refused writer spends nothing), or None.
  - `open(self) -> None` (line 335; public)
  - `ask(self, prompt: str, *, owner_id: str, metadata: Mapping[str, Any], result_model: type[HintWriterOutputV1]=HintWriterOutputV1) -> HintWriterOutputV1` (line 351; public)
  - `model(self) -> str | None` (line 364; public)
  - `usage(self) -> dict[str, Any]` (line 369; public)
- `empty_output(**overrides: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/hints/writer.py), line 373) — A writer answer with every field empty (tests and fakes start here).

### Module constants

- `ROUTE_TASK` ([src/learnloop/hints/writer.py](../../../../../../src/learnloop/hints/writer.py), line 48)
- `PURPOSE` ([src/learnloop/hints/writer.py](../../../../../../src/learnloop/hints/writer.py), line 49)
- `OWNER_KIND` ([src/learnloop/hints/writer.py](../../../../../../src/learnloop/hints/writer.py), line 50)
- `PROMPT_VERSION` ([src/learnloop/hints/writer.py](../../../../../../src/learnloop/hints/writer.py), line 51)
- `CODEX_PROFILE_TYPES` ([src/learnloop/hints/writer.py](../../../../../../src/learnloop/hints/writer.py), line 54)
- `MODELS_ENV` ([src/learnloop/hints/writer.py](../../../../../../src/learnloop/hints/writer.py), line 58)
- `_CAPS` ([src/learnloop/hints/writer.py](../../../../../../src/learnloop/hints/writer.py), line 62)
- `WORK_CHARS` ([src/learnloop/hints/writer.py](../../../../../../src/learnloop/hints/writer.py), line 64)
- `TEXT_CHARS` ([src/learnloop/hints/writer.py](../../../../../../src/learnloop/hints/writer.py), line 65)
- `_CONTRACTS` ([src/learnloop/hints/writer.py](../../../../../../src/learnloop/hints/writer.py), line 141)
- `_INSTRUCTIONS` ([src/learnloop/hints/writer.py](../../../../../../src/learnloop/hints/writer.py), line 176)

### Explicit exports

`__all__` declares:

- `CODEX_PROFILE_TYPES`
- `Candidate`
- `HintPlacement`
- `HintWriterOutputV1`
- `MODELS_ENV`
- `OWNER_KIND`
- `PROMPT_VERSION`
- `PURPOSE`
- `ROUTE_TASK`
- `SpendLimitExceeded`
- `WriterRoute`
- `WriterUnavailable`
- `build_prompt`
- `empty_output`
- `models_off`

## Internal implementation anchors

- `_clip(text: Any, limit: int) -> str` ([source](../../../../../../src/learnloop/hints/writer.py), line 194)
- `_expected(expected: Any) -> str` ([source](../../../../../../src/learnloop/hints/writer.py), line 199)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/hints/outcome|learnloop.hints.outcome]] — imports `models_off`; statically calls `models_off`
- [[Reference/Modules/learnloop/hints/report|learnloop.hints.report]] — imports `PROMPT_VERSION`
- [[Reference/Modules/learnloop/hints/service|learnloop.hints.service]] — imports `HintWriterOutputV1`, `PROMPT_VERSION`, `WriterRoute`, `WriterUnavailable`, `build_prompt`, `models_off`; statically calls `WriterRoute`, `build_prompt`, `models_off`
- [[Reference/Modules/learnloop/hints/workbench|learnloop.hints.workbench]] — imports `HintWriterOutputV1`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendBudget`, `SpendCaps`, `SpendLimitExceeded`, `spend_envelopes`; calls `SpendBudget`, `SpendCaps`, `spend_envelopes`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/hints/contracts|learnloop.hints.contracts]] — imports `Target`, `reference_route_id`; calls `reference_route_id`
- [[Reference/Modules/learnloop/hints/kinds|learnloop.hints.kinds]] — imports `HORIZON_LEVELS`, `KINDS`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `PaidCalls`, `PaidRoute`, `SUBSCRIPTION_PROFILE_TYPES`, `plan_route`, `resolve_client`; calls `PaidCalls`, `plan_route`, `resolve_client`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `os`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop/hints/outcome|learnloop.hints.outcome]], [[Reference/Modules/learnloop/hints/report|learnloop.hints.report]], [[Reference/Modules/learnloop/hints/service|learnloop.hints.service]], [[Reference/Modules/learnloop/hints/workbench|learnloop.hints.workbench]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/hint_fakes.py](../../../../../../tests/hint_fakes.py) — direct import
- [tests/test_approach_map_replay.py](../../../../../../tests/test_approach_map_replay.py) — direct import
- [tests/test_hint_contracts.py](../../../../../../tests/test_hint_contracts.py) — direct import
  - `test_a_waypoint_that_misses_the_chosen_horizon_is_caught`
- [tests/test_hint_h2a_review.py](../../../../../../tests/test_hint_h2a_review.py) — direct import
  - `test_f2_a_smaller_step_toward_a_far_waypoint_targets_the_adjacent_node_on_the_way`
  - `test_f8_a_book_origin_on_an_unverified_passage_is_refused`
  - `test_f8_the_writer_is_told_its_passages_are_unverified`
- [tests/test_hint_h2a_review_round4.py](../../../../../../tests/test_hint_h2a_review_round4.py) — direct import
  - `test_r4_the_reference_route_rule_for_every_kind_and_no_map_unchanged`
- [tests/test_hint_replies.py](../../../../../../tests/test_hint_replies.py) — direct import
  - `test_learner_route_keeps_the_learners_route_and_never_targets_the_reference`
- [tests/test_hint_service.py](../../../../../../tests/test_hint_service.py) — direct import
  - `test_a_capped_day_falls_back_to_authored_hints_and_says_so`
  - `test_an_unpriced_metered_writer_is_refused_before_sending`
  - `test_the_unset_writer_route_resolves_to_the_active_provider_and_refuses_codex`
  - `test_the_wording_lint_rejects_judging_words_in_every_learner_facing_string`
  - `test_the_writer_never_runs_on_codex_and_says_why`
  - `test_the_writers_receipts_are_labelled`

## Modification guidance

- Make changes here when the responsibility remains writer within learnloop.hints; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/hints/writer.py](../../../../../../src/learnloop/hints/writer.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
