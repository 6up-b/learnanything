---
title: "learnloop.diagnosis.recurrence.judging"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/recurrence/judging.py"
source_paths:
  - "src/learnloop/diagnosis/recurrence/judging.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis.recurrence"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.recurrence.judging module"
  - "src/learnloop/diagnosis/recurrence/judging.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-recurrence"
---

# `learnloop.diagnosis.recurrence.judging`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/recurrence/_package|learnloop.diagnosis.recurrence]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.recurrence.judging` exists within [[Reference/Modules/learnloop/diagnosis/recurrence/_package|learnloop.diagnosis.recurrence]] to own the behavior summarized by its module contract: Shortlist and judge same-cause pairs (shared by the live step and the backlog).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/recurrence/judging.py](../../../../../../../src/learnloop/diagnosis/recurrence/judging.py) |
| Source lines | 326 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/recurrence/_package|learnloop.diagnosis.recurrence]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class LeaseLost(AIInterrupted)` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/judging.py), line 61) — The enclosing job's lease is held by another worker: no further paid call.
- `beat(heartbeat: Heartbeat | None) -> None` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/judging.py), line 65) — Renew the job lease before a paid request, or stop (``LeaseLost``).
- `estimate_tokens(text: str) -> int` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/judging.py), line 76)
- `settled_class_pairs(repository: Repository) -> set[frozenset[str]]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/judging.py), line 80) — Class pairs a validated citation or a settling verdict already decided.
- `blocking_cutoff(vault: LoadedVault, model_id: str, *, dims: int | None) -> tuple[float | None, str, str | None]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/judging.py), line 92) — (cutoff, basis, refusal): B3's entry for this model when it matches the stored vectors.
- `learner_state(subjects: Sequence[Subject]) -> list[Subject]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/judging.py), line 103)
- `plan_shortlist(vault: LoadedVault, repository: Repository, *, queries: Sequence[Subject], pool: Sequence[Subject], population: Sequence[Subject], model_id: str) -> Shortlist` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/judging.py), line 107) — Shortlist ``queries`` against ``pool``; ``model_id`` is the CONFIGURED model.
- `default_judge_client(vault: LoadedVault) -> Any | None` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/judging.py), line 157) — The ``ai.routing.same_cause_judge`` client (unset: the diagnosis route).
- `model_label(client: Any) -> str` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/judging.py), line 171)
- `producer_label(client: Any) -> str` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/judging.py), line 175) — Who produced a verdict: the model AND its reasoning effort.
- `producer_label_for(*, model: Any, effort: Any=None) -> str` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/judging.py), line 193)
- `sum_estimates(*estimates: SpendEstimate) -> SpendEstimate` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/judging.py), line 199)
- `admit_beside(spend: ReviewSpend, route: str, *, input_tokens: int, reserve: Reserve | None) -> None` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/judging.py), line 210) — Refuse (``SpendLimitExceeded``, nothing sent) unless one request on ``route`` still leaves room for what the enclosing command reserves.
- `class JudgeExecutor` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/judging.py), line 220) — One admitted, isolated structured call per pair on the judge route.
  - `__init__(self, spend: ReviewSpend, client: Any, *, reserve: Reserve | None=None, heartbeat: Heartbeat | None=None) -> None` (line 228; internal)
  - `__call__(self, prompt: str, result_model: type[SameOrDifferent], purpose: str) -> tuple[SameOrDifferent, str]` (line 237; internal)
- `judge_executor(spend: ReviewSpend, client: Any, *, reserve: Reserve | None=None, heartbeat: Heartbeat | None=None) -> JudgeExecutor` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/judging.py), line 251)
- `embed_on_spend(spend: ReviewSpend, client: Any, repository: Repository, records: Sequence[Any], *, reserve: Reserve | None=None, heartbeat: Heartbeat | None=None) -> int` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/judging.py), line 256) — Embed records in admitted batches on ``spend``; returns how many were stored.
- `receipt_sink(repository: Repository, *, owner_kind: str, owner_id: str) -> Callable[[str, dict[str, Any]], None]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/judging.py), line 300)

### Module constants

- `EMBEDDING_ROUTE` ([src/learnloop/diagnosis/recurrence/judging.py](../../../../../../../src/learnloop/diagnosis/recurrence/judging.py), line 52)
- `EMBED_BATCH` ([src/learnloop/diagnosis/recurrence/judging.py](../../../../../../../src/learnloop/diagnosis/recurrence/judging.py), line 53)
- `SETTLING_JUDGES` ([src/learnloop/diagnosis/recurrence/judging.py](../../../../../../../src/learnloop/diagnosis/recurrence/judging.py), line 73)

### Explicit exports

`__all__` declares:

- `EMBEDDING_ROUTE`
- `Heartbeat`
- `JudgeExecutor`
- `LeaseLost`
- `Reserve`
- `SETTLING_JUDGES`
- `admit_beside`
- `beat`
- `blocking_cutoff`
- `default_judge_client`
- `embed_on_spend`
- `estimate_tokens`
- `judge_executor`
- `learner_state`
- `model_label`
- `plan_shortlist`
- `producer_label`
- `producer_label_for`
- `receipt_sink`
- `settled_class_pairs`
- `sum_estimates`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/proposals/method_phrasing|learnloop.content.proposals.method_phrasing]] — imports `receipt_sink`; statically calls `receipt_sink`
- [[Reference/Modules/learnloop/content/proposals/method_statement_judge|learnloop.content.proposals.method_statement_judge]] — imports `receipt_sink`; statically calls `receipt_sink`
- [[Reference/Modules/learnloop/diagnosis/recurrence/backlog|learnloop.diagnosis.recurrence.backlog]] — imports `EMBEDDING_ROUTE`, `EMBED_BATCH`, `default_judge_client`, `embed_on_spend`, `estimate_tokens`, `judge_executor`, `learner_state`, `plan_shortlist`, `producer_label`, `receipt_sink`; statically calls `default_judge_client`, `embed_on_spend`, `estimate_tokens`, `judge_executor`, `learner_state`, `plan_shortlist`, `producer_label`, `receipt_sink`
- [[Reference/Modules/learnloop/diagnosis/recurrence/benchmarks|learnloop.diagnosis.recurrence.benchmarks]] — imports `estimate_tokens`, `sum_estimates`; statically calls `estimate_tokens`, `sum_estimates`
- [[Reference/Modules/learnloop/diagnosis/recurrence/escalation|learnloop.diagnosis.recurrence.escalation]] — imports `Reserve`, `admit_beside`, `estimate_tokens`, `model_label`; statically calls `admit_beside`, `estimate_tokens`, `model_label`
- [[Reference/Modules/learnloop/diagnosis/recurrence/guard|learnloop.diagnosis.recurrence.guard]] — imports `default_judge_client`, `estimate_tokens`, `judge_executor`, `producer_label`, `producer_label_for`, `receipt_sink`; statically calls `default_judge_client`, `estimate_tokens`, `judge_executor`, `producer_label`, `producer_label_for`, `receipt_sink`
- [[Reference/Modules/learnloop/diagnosis/recurrence/live|learnloop.diagnosis.recurrence.live]] — imports `Heartbeat`, `LeaseLost`, `Reserve`, `default_judge_client`, `embed_on_spend`, `judge_executor`, `learner_state`, `plan_shortlist`, `receipt_sink`; statically calls `default_judge_client`, `embed_on_spend`, `judge_executor`, `learner_state`, `plan_shortlist`, `receipt_sink`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/judges|learnloop.diagnosis.text_gaps.judges]] — imports `estimate_tokens`, `producer_label`, `receipt_sink`; statically calls `estimate_tokens`, `producer_label`, `receipt_sink`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/tier1|learnloop.diagnosis.text_gaps.tier1]] — imports `estimate_tokens`; statically calls `estimate_tokens`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `model_settings`; calls `model_settings`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `ready_client_for_task`; calls `ready_client_for_task`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendEstimate`; calls `SpendEstimate`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `execute_structured_operation`; calls `execute_structured_operation`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/embedding_vectors|learnloop.db.stores.embedding_vectors]] — imports `put_vector`; calls `put_vector`
- [[Reference/Modules/learnloop/diagnosis/offline_review/spend|learnloop.diagnosis.offline_review.spend]] — imports `ReviewSpend`
- [[Reference/Modules/learnloop/diagnosis/recurrence/kind|learnloop.diagnosis.recurrence.kind]] — imports `SAME_CAUSE`, `SAME_CAUSE_ROUTE`, `compatible`, `scope_of`; calls `scope_of`
- [[Reference/Modules/learnloop/diagnosis/split/embeddings|learnloop.diagnosis.split.embeddings]] — imports `TASK_PREFIX`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `register_retrieval_route`; calls `register_retrieval_route`
- [[Reference/Modules/learnloop/matching/judge|learnloop.matching.judge]] — imports `SameOrDifferent`
- [[Reference/Modules/learnloop/matching/kinds|learnloop.matching.kinds]] — imports `Subject`
- [[Reference/Modules/learnloop/matching/shortlist|learnloop.matching.shortlist]] — imports `Shortlist`, `active_model`, `compatible_cutoff`, `shortlist_pairs`, `stored_width`; calls `Shortlist`, `active_model`, `compatible_cutoff`, `shortlist_pairs`, `stored_width`
- [[Reference/Modules/learnloop/recurrence|learnloop.recurrence]] — imports `key_for_statement`; calls `key_for_statement`
- [[Reference/Modules/learnloop/substrate/recurrence_groups|learnloop.substrate.recurrence_groups]] — imports `active_group_map`, `compute_groups`; calls `active_group_map`, `compute_groups`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/proposals/method_phrasing|learnloop.content.proposals.method_phrasing]], [[Reference/Modules/learnloop/content/proposals/method_statement_judge|learnloop.content.proposals.method_statement_judge]], [[Reference/Modules/learnloop/diagnosis/recurrence/backlog|learnloop.diagnosis.recurrence.backlog]], [[Reference/Modules/learnloop/diagnosis/recurrence/benchmarks|learnloop.diagnosis.recurrence.benchmarks]], [[Reference/Modules/learnloop/diagnosis/recurrence/escalation|learnloop.diagnosis.recurrence.escalation]] and 4 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_recurrence_benchmarks.py](../../../../../../../tests/test_recurrence_benchmarks.py) — direct import
  - `test_b3_recommends_only_at_the_serving_width_with_its_provenance`
- [tests/test_recurrence_commands.py](../../../../../../../tests/test_recurrence_commands.py) — direct import
  - `test_the_judge_producer_is_model_and_effort_so_codex_tiers_never_share_a_guard_pass`

## Modification guidance

- Change judging policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/recurrence/judging.py](../../../../../../../src/learnloop/diagnosis/recurrence/judging.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
