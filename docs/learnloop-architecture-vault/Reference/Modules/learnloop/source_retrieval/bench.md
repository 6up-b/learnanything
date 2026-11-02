---
title: "learnloop.source_retrieval.bench"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/bench.py"
source_paths:
  - "src/learnloop/source_retrieval/bench.py"
source_commit: "51981532132f73641b17ddcb3f8cb63d6a5d5536"
source_commit_timestamp: "2026-10-13T00:47:49-04:00"
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
  - "learnloop.source_retrieval.bench module"
  - "src/learnloop/source_retrieval/bench.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.bench`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.bench` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: Shared pieces of T6's two compare-harness suites (``source_retrieval``, ``b4``).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/bench.py](../../../../../../src/learnloop/source_retrieval/bench.py) |
| Source lines | 363 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `51981532132f73641b17ddcb3f8cb63d6a5d5536` |
| Commit timestamp | `2026-10-13T00:47:49-04:00` |

## Public API

- `read_only_repository(vault: LoadedVault) -> Repository` ([source](../../../../../../src/learnloop/source_retrieval/bench.py), line 115) — A read-only handle; planning never migrates, so an old schema is refused.
- `stable_key(*parts: Any) -> str` ([source](../../../../../../src/learnloop/source_retrieval/bench.py), line 130)
- `clip(text: str, limit: int) -> str` ([source](../../../../../../src/learnloop/source_retrieval/bench.py), line 134)
- `role_budget(vault: LoadedVault, role: str) -> int` ([source](../../../../../../src/learnloop/source_retrieval/bench.py), line 139) — A T6 role's output budget under the shared policy (for dry-run plans).
- `question_prompt(version: str, seeds: Mapping[str, str | tuple[str, str]], instructions: str=QUESTION_INSTRUCTIONS) -> str` ([source](../../../../../../src/learnloop/source_retrieval/bench.py), line 145) — A writer prompt: single passages, or pairs (``(a, b)``) for compositional questions.
- `label_prompt(version: str, pass_index: int, question: str, candidates: Mapping[str, Mapping[str, Any]]) -> str` ([source](../../../../../../src/learnloop/source_retrieval/bench.py), line 160)
- `plan_question_calls(seed_texts: Sequence[str | tuple[str, str]], version: str, batch: int, output_tokens: int, instructions: str=QUESTION_INSTRUCTIONS) -> dict[str, int]` ([source](../../../../../../src/learnloop/source_retrieval/bench.py), line 170)
- `plan_label_calls(questions: int, pool_bound: int, batch: int, versions: Sequence[str], payload: Mapping[str, Any], output_tokens: int) -> dict[str, int]` ([source](../../../../../../src/learnloop/source_retrieval/bench.py), line 184) — Upper bound: every question's full pool, in both passes.
- `write_questions(ctx: Any, seeds: Sequence[tuple[str, str | tuple[str, str]]], *, version: str, batch: int, instructions: str=QUESTION_INSTRUCTIONS) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/bench.py), line 197) — ``{seed_id: {"question", "model"}}`` for every seed the writer answered.
- `label_pool(ctx: Any, *, question: str, candidates: Mapping[str, Mapping[str, Any]], versions: Sequence[str], batch: int, left_kind: str, right_kind: str, right_id: Callable[[str], str], rationale: Mapping[str, Any] | None=None) -> tuple[dict[str, list[str | None]], dict[str, int]]` ([source](../../../../../../src/learnloop/source_retrieval/bench.py), line 218) — Two-pass labels ``{key: [pass1, pass2]}`` for every candidate, ledgered.
- `mrr(ranked: Sequence[str], relevant: set[str]) -> float | None` ([source](../../../../../../src/learnloop/source_retrieval/bench.py), line 264)
- `score_question(rankings: Mapping[str, Sequence[str]], labels: Mapping[str, Sequence[str | None]]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/source_retrieval/bench.py), line 273) — Per-system metrics for one question, or None when a label is missing.
- `label_agreement(labels: Sequence[Mapping[str, Sequence[str | None]]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/bench.py), line 293)
- `summarize(per_question: Sequence[Mapping[str, Any]], systems: Sequence[str], comparisons: Sequence[tuple[str, str]], *, samples: int=1000, seed: int=0) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/bench.py), line 300) — Means per system and paired bootstrap intervals for each comparison.
- `beats(difference: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/bench.py), line 326) — The bar: nDCG@10 interval above zero, Recall@10 not worse, enough questions.

### Module constants

- `TOP_K` ([src/learnloop/source_retrieval/bench.py](../../../../../../src/learnloop/source_retrieval/bench.py), line 49)
- `QUESTION_ROLE` ([src/learnloop/source_retrieval/bench.py](../../../../../../src/learnloop/source_retrieval/bench.py), line 50)
- `LABEL_ROLE` ([src/learnloop/source_retrieval/bench.py](../../../../../../src/learnloop/source_retrieval/bench.py), line 51)
- `REWRITE_ROLE` ([src/learnloop/source_retrieval/bench.py](../../../../../../src/learnloop/source_retrieval/bench.py), line 52)
- `VERIFY_ROLE` ([src/learnloop/source_retrieval/bench.py](../../../../../../src/learnloop/source_retrieval/bench.py), line 54)
- `T6_ROLE_TASKS` ([src/learnloop/source_retrieval/bench.py](../../../../../../src/learnloop/source_retrieval/bench.py), line 56)
- `LABEL_TASK` ([src/learnloop/source_retrieval/bench.py](../../../../../../src/learnloop/source_retrieval/bench.py), line 62)
- `MIN_SCORED_QUESTIONS` ([src/learnloop/source_retrieval/bench.py](../../../../../../src/learnloop/source_retrieval/bench.py), line 63)
- `_PRACTICE_NAMES` ([src/learnloop/source_retrieval/bench.py](../../../../../../src/learnloop/source_retrieval/bench.py), line 64)
- `QUESTION_INSTRUCTIONS` ([src/learnloop/source_retrieval/bench.py](../../../../../../src/learnloop/source_retrieval/bench.py), line 66)
- `KEYWORD_INSTRUCTIONS` ([src/learnloop/source_retrieval/bench.py](../../../../../../src/learnloop/source_retrieval/bench.py), line 73)
- `COMPOSITIONAL_INSTRUCTIONS` ([src/learnloop/source_retrieval/bench.py](../../../../../../src/learnloop/source_retrieval/bench.py), line 81)
- `PROCEDURAL_INSTRUCTIONS` ([src/learnloop/source_retrieval/bench.py](../../../../../../src/learnloop/source_retrieval/bench.py), line 88)
- `TYPE_INSTRUCTIONS` ([src/learnloop/source_retrieval/bench.py](../../../../../../src/learnloop/source_retrieval/bench.py), line 96)
- `LABEL_INSTRUCTIONS` ([src/learnloop/source_retrieval/bench.py](../../../../../../src/learnloop/source_retrieval/bench.py), line 102)

### Explicit exports

`__all__` declares:

- `COMPOSITIONAL_INSTRUCTIONS`
- `KEYWORD_INSTRUCTIONS`
- `PROCEDURAL_INSTRUCTIONS`
- `TYPE_INSTRUCTIONS`
- `VERIFY_ROLE`
- `role_budget`
- `LABEL_INSTRUCTIONS`
- `LABEL_ROLE`
- `LABEL_TASK`
- `MIN_SCORED_QUESTIONS`
- `QUESTION_ROLE`
- `REWRITE_ROLE`
- `T6_ROLE_TASKS`
- `TOP_K`
- `beats`
- `clip`
- `label_agreement`
- `label_pool`
- `mrr`
- `plan_label_calls`
- `plan_question_calls`
- `read_only_repository`
- `score_question`
- `stable_key`
- `summarize`
- `write_questions`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/source_retrieval/b4|learnloop.source_retrieval.b4]] — imports `module`; statically calls `beats`, `clip`, `label_agreement`, `label_pool`, `plan_label_calls`, `plan_question_calls`, `read_only_repository`, `role_budget`, `score_question`, `stable_key`, `summarize`, `write_questions`
- [[Reference/Modules/learnloop/source_retrieval/evaluation|learnloop.source_retrieval.evaluation]] — imports `module`; statically calls `beats`, `clip`, `label_agreement`, `label_pool`, `plan_label_calls`, `plan_question_calls`, `read_only_repository`, `role_budget`, `score_question`, `stable_key`, `summarize`, `write_questions`
- [[Reference/Modules/learnloop/source_retrieval/suites|learnloop.source_retrieval.suites]] — imports `T6_ROLE_TASKS`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/output_budget|learnloop.ai.output_budget]] — imports `output_budget`; calls `output_budget`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ops/pf_calls|learnloop.ops.pf_calls]] — imports `estimate_tokens`; calls `estimate_tokens`
- [[Reference/Modules/learnloop/practice_index/evaluation|learnloop.practice_index.evaluation]] — imports `agreement`, `paired_bootstrap`, `query_metrics`; calls `agreement`, `paired_bootstrap`, `query_metrics`
- [[Reference/Modules/learnloop/source_retrieval/contracts|learnloop.source_retrieval.contracts]] — imports `SpanLabels`, `VERDICT_SCORE`, `WrittenQuestions`
- [[Reference/Modules/learnloop/source_retrieval/queries|learnloop.source_retrieval.queries]] — imports `query_id`; calls `query_id`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `hashlib`, `json`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/source_retrieval/b4|learnloop.source_retrieval.b4]], [[Reference/Modules/learnloop/source_retrieval/evaluation|learnloop.source_retrieval.evaluation]], [[Reference/Modules/learnloop/source_retrieval/suites|learnloop.source_retrieval.suites]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_source_retrieval_suites.py](../../../../../../tests/test_source_retrieval_suites.py) — direct import
  - `test_the_bar_needs_an_interval_above_zero_recall_not_worse_and_ten_questions`

## Modification guidance

- Make changes here when the responsibility remains bench within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/bench.py](../../../../../../src/learnloop/source_retrieval/bench.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
