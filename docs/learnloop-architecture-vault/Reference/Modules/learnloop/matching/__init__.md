---
title: "learnloop.matching"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/matching/__init__.py"
source_paths:
  - "src/learnloop/matching/__init__.py"
source_commit: "7d355b62c11afacbeca52e07210f37c7221c0939"
source_commit_timestamp: "2026-10-12T15:57:32-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.matching"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
aliases:
  - "learnloop.matching module"
  - "src/learnloop/matching/__init__.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-matching"
---

# `learnloop.matching`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/matching/_package|learnloop.matching]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.matching` exists within [[Reference/Modules/learnloop/matching/_package|learnloop.matching]] to own the behavior summarized by its module contract: Embeddings shortlist, judges decide: the one "same or different?" step.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/matching/__init__.py](../../../../../../src/learnloop/matching/__init__.py) |
| Source lines | 33 |
| Owning package | [[Reference/Modules/learnloop/matching/_package|learnloop.matching]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `7d355b62c11afacbeca52e07210f37c7221c0939` |
| Commit timestamp | `2026-10-12T15:57:32-04:00` |

## Public API

No public top-level function or class definition is declared in this file.

### Explicit exports

`__all__` declares:

- `CandidatePair`
- `EmbeddingIdentity`
- `JudgedPair`
- `MatchKind`
- `Refusal`
- `SameOrDifferent`
- `Shortlist`
- `Subject`
- `UnionEdge`
- `UnionResult`
- `VERDICTS`
- `judge_pairs`
- `pair_input_hash`
- `pair_prompt`
- `shortlist_pairs`
- `union_with_refusals`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

No live LearnLoop module directly imports this module in the static graph.

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/matching/judge|learnloop.matching.judge]] — imports `JudgedPair`, `SameOrDifferent`, `judge_pairs`, `pair_input_hash`, `pair_prompt`
- [[Reference/Modules/learnloop/matching/kinds|learnloop.matching.kinds]] — imports `EmbeddingIdentity`, `MatchKind`, `Subject`, `VERDICTS`
- [[Reference/Modules/learnloop/matching/shortlist|learnloop.matching.shortlist]] — imports `CandidatePair`, `Shortlist`, `shortlist_pairs`
- [[Reference/Modules/learnloop/matching/union|learnloop.matching.union]] — imports `Refusal`, `UnionEdge`, `UnionResult`, `union_with_refusals`

### Platform and third-party dependencies

- Standard library: none imported directly
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

No live LearnLoop module imports it directly; its current reach is tests, repository tooling, dynamic registration, or explicit manual invocation where documented above.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_matching.py](../../../../../../tests/test_matching.py) — direct import
  - `test_a_concurrent_worker_skips_a_claimed_pair_and_never_pays_twice`
  - `test_a_cutoff_applies_only_to_the_vectors_it_was_measured_on`
  - `test_a_failed_call_releases_its_claim`
  - `test_a_judge_without_a_producer_is_refused`
  - `test_a_spend_refusal_stops_the_batch_and_a_failure_skips_one_pair`
  - `test_a_stop_that_is_not_an_exception_releases_its_claim_and_propagates`
  - `test_an_asymmetric_kind_shortlists_an_ephemeral_query_against_a_pool_of_another_record_kind`
  - `test_an_expired_lease_is_reclaimed_and_the_late_verdict_is_fenced_out`
  - `test_every_verdict_goes_to_the_ledger_once`
  - `test_presentation_order_and_input_hash_ignore_rank_and_side`
  - `test_reuse_is_per_producer_and_a_rerun_supersedes_the_same_producer`
  - `test_shortlist_takes_top_k_skips_settled_and_applies_only_a_given_cutoff`
  - `test_the_judge_label_is_the_executors_and_reuse_is_per_label`

## Modification guidance

- Change this file when intentionally adding or removing a package-level re-export; keep implementation logic in the owning module.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/matching/__init__.py](../../../../../../src/learnloop/matching/__init__.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
