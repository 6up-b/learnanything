---
title: "learnloop.hints.discriminating"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/hints/discriminating.py"
source_paths:
  - "src/learnloop/hints/discriminating.py"
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
  - "learnloop.hints.discriminating module"
  - "src/learnloop/hints/discriminating.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-hints"
---

# `learnloop.hints.discriminating`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.hints.discriminating` exists within [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] to own the behavior summarized by its module contract: Adaptive hints H2a: discriminating questions, chosen by expected information gain (spec §4.2, G-H16).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/hints/discriminating.py](../../../../../../src/learnloop/hints/discriminating.py) |
| Source lines | 259 |
| Owning package | [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class Rival` ([source](../../../../../../src/learnloop/hints/discriminating.py), line 60) — One open explanation, as typed records for the writer (statement and status, no prose; §4.6).
  - `as_dict(self) -> dict[str, Any]` (line 70; public)
- `rival_id(statement: str) -> str` ([source](../../../../../../src/learnloop/hints/discriminating.py), line 78)
- `open_rivals(repository: Any, item: Any) -> list[Rival]` ([source](../../../../../../src/learnloop/hints/discriminating.py), line 89) — The item's open rival explanations (local reads only).
- `normalize_answer(text: str) -> str` ([source](../../../../../../src/learnloop/hints/discriminating.py), line 146) — A predicted or given answer as a comparable string (math delimiters, case and spacing ignored): two rivals predicting ``$0$`` and ``0`` agree.
- `class RankedCandidate` ([source](../../../../../../src/learnloop/hints/discriminating.py), line 156)
  - `as_dict(self) -> dict[str, Any]` (line 162; public)
- `compile_candidate(predictions: Mapping[str, str]) -> Any` ([source](../../../../../../src/learnloop/hints/discriminating.py), line 166) — One candidate as an instrument: per rival, all its mass on the answer that rival predicts, over the distinct predicted answers.
- `complete_predictions(candidate: Mapping[str, Any], rivals: Sequence[Rival]) -> dict[str, str] | None` ([source](../../../../../../src/learnloop/hints/discriminating.py), line 180) — The candidate's predicted answer for every rival, or None when it does not predict each of the request's rivals exactly once (a missing, duplicate or unknown rival id): every candidate is ranked against the same rivals and prior, so EIG compares like with like (review F6).
- `rank_candidates(candidates: Sequence[Mapping[str, Any]], rivals: Sequence[Rival]) -> list[RankedCandidate]` ([source](../../../../../../src/learnloop/hints/discriminating.py), line 194) — Every candidate predicting an answer for each of the request's rivals (:func:`complete_predictions`), scored by ``instrument_expected_information_gain`` under uniform weights over all of them, best first (ties keep the writer's order).
- `best_candidate(ranked: Sequence[RankedCandidate]) -> RankedCandidate | None` ([source](../../../../../../src/learnloop/hints/discriminating.py), line 217) — The best candidate with positive EIG, or None (§4.2: no positive EIG, no discriminating question is shown).
- `states_a_rival(question_md: str, rivals: Sequence[Rival]) -> str | None` ([source](../../../../../../src/learnloop/hints/discriminating.py), line 227) — A rival the question states outright (its statement, or most of its content words), which the kind's contract forbids (§4.2: "never states either rival"); the rival's id, or None.

### Module constants

- `MAX_RIVALS` ([src/learnloop/hints/discriminating.py](../../../../../../src/learnloop/hints/discriminating.py), line 47)
- `WEIGHTS_BASIS` ([src/learnloop/hints/discriminating.py](../../../../../../src/learnloop/hints/discriminating.py), line 49)
- `GRADER_POLICY` ([src/learnloop/hints/discriminating.py](../../../../../../src/learnloop/hints/discriminating.py), line 51)
- `PROVENANCE` ([src/learnloop/hints/discriminating.py](../../../../../../src/learnloop/hints/discriminating.py), line 52)
- `EIG_EPSILON` ([src/learnloop/hints/discriminating.py](../../../../../../src/learnloop/hints/discriminating.py), line 54)
- `_LEARNER_SCOPES` ([src/learnloop/hints/discriminating.py](../../../../../../src/learnloop/hints/discriminating.py), line 56)

### Explicit exports

`__all__` declares:

- `EIG_EPSILON`
- `MAX_RIVALS`
- `RankedCandidate`
- `Rival`
- `WEIGHTS_BASIS`
- `best_candidate`
- `compile_candidate`
- `complete_predictions`
- `normalize_answer`
- `open_rivals`
- `rank_candidates`
- `rival_id`
- `states_a_rival`

## Internal implementation anchors

- `_normalize(text: str) -> str` ([source](../../../../../../src/learnloop/hints/discriminating.py), line 74)
- `_since_last_attempt(repository: Any, practice_item_id: str) -> tuple[str | None, str | None]` ([source](../../../../../../src/learnloop/hints/discriminating.py), line 82)
- `_named_gaps(repository: Any, practice_item_id: str, since: str | None) -> list[tuple[str, str]]` ([source](../../../../../../src/learnloop/hints/discriminating.py), line 121)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/hints/service|learnloop.hints.service]] — imports `WEIGHTS_BASIS`, `best_candidate`, `normalize_answer`, `rank_candidates`, `states_a_rival`; statically calls `best_candidate`, `normalize_answer`, `rank_candidates`, `states_a_rival`
- [[Reference/Modules/learnloop/hints/state|learnloop.hints.state]] — imports `Rival`, `open_rivals`; statically calls `open_rivals`
- [[Reference/Modules/learnloop/hints/workbench|learnloop.hints.workbench]] — imports `Rival`, `rival_id`; statically calls `Rival`, `rival_id`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/diagnosis/probe_families|learnloop.diagnosis.probe_families]] — imports `CompiledInstrument`, `instrument_expected_information_gain`; calls `CompiledInstrument`, `instrument_expected_information_gain`
- [[Reference/Modules/learnloop/hints/maps|learnloop.hints.maps]] — imports `norm`; calls `norm`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `hashlib`, `json`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/hints/service|learnloop.hints.service]], [[Reference/Modules/learnloop/hints/state|learnloop.hints.state]], [[Reference/Modules/learnloop/hints/workbench|learnloop.hints.workbench]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_hint_discriminating.py](../../../../../../tests/test_hint_discriminating.py) — direct import
  - `test_the_rank_drops_zero_eig_by_construction`
- [tests/test_hint_feedback_texts.py](../../../../../../tests/test_hint_feedback_texts.py) — direct import
  - `test_reading_it_writes_only_gap_rows_and_the_gap_joins_the_next_hints_rivals`
- [tests/test_hint_h2a_review.py](../../../../../../tests/test_hint_h2a_review.py) — direct import
  - `test_f6_a_candidate_missing_a_rival_is_not_ranked_above_a_complete_one`
  - `test_f6_a_duplicate_or_unknown_prediction_is_refused`

## Modification guidance

- Make changes here when the responsibility remains discriminating within learnloop.hints; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/hints/discriminating.py](../../../../../../src/learnloop/hints/discriminating.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
