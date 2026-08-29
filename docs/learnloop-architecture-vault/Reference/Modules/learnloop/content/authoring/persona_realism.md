---
title: "learnloop.content.authoring.persona_realism"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/authoring/persona_realism.py"
source_paths:
  - "src/learnloop/content/authoring/persona_realism.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.content.authoring"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.authoring.persona_realism module"
  - "src/learnloop/content/authoring/persona_realism.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-authoring"
---

# `learnloop.content.authoring.persona_realism`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.authoring.persona_realism` exists within [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] to own the behavior summarized by its module contract: B2 blinded persona-vs-real realism matcher.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/authoring/persona_realism.py](../../../../../../../src/learnloop/content/authoring/persona_realism.py) |
| Source lines | 319 |
| Owning package | [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class PersonaRealismReport` ([source](../../../../../../../src/learnloop/content/authoring/persona_realism.py), line 53)
  - `licensed(self) -> bool` (line 66; public)
  - `as_dict(self) -> dict[str, Any]` (line 69; public)
- `text_features(text: str) -> tuple[float, ...]` ([source](../../../../../../../src/learnloop/content/authoring/persona_realism.py), line 86) — Bounded, content-agnostic text-shape features used by the blind matcher.
- `trace_corpus_hash(traces: Iterable[str]) -> str` ([source](../../../../../../../src/learnloop/content/authoring/persona_realism.py), line 185) — Order-independent content identity for one matcher arm.
- `match_persona_realism(repository: Repository, persona_traces: Sequence[str], *, real_traces: Sequence[str] | None=None, persona_source: str='authored_signature', generator_provider: str | None=None, generator_model: str | None=None, generator_family: str | None=None, separation_threshold: float=DEFAULT_SEPARATION_THRESHOLD, persist: bool=True, clock: Clock | None=None) -> PersonaRealismReport` ([source](../../../../../../../src/learnloop/content/authoring/persona_realism.py), line 206) — Run B2 and optionally append its aggregate result.
- `latest_realism_license(repository: Repository, *, generator_family: str | None=None, persona_source: str | None=None, persona_corpus_hash: str | None=None) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/authoring/persona_realism.py), line 306) — Latest matching B2 run; callers must inspect ``verdict``.

### Module constants

- `PERSONA_REALISM_MATCHER_VERSION` ([src/learnloop/content/authoring/persona_realism.py](../../../../../../../src/learnloop/content/authoring/persona_realism.py), line 22)
- `DEFAULT_SEPARATION_THRESHOLD` ([src/learnloop/content/authoring/persona_realism.py](../../../../../../../src/learnloop/content/authoring/persona_realism.py), line 23)
- `MIN_TRACES_PER_ARM` ([src/learnloop/content/authoring/persona_realism.py](../../../../../../../src/learnloop/content/authoring/persona_realism.py), line 24)
- `_WORD_RE` ([src/learnloop/content/authoring/persona_realism.py](../../../../../../../src/learnloop/content/authoring/persona_realism.py), line 26)
- `_SENTENCE_RE` ([src/learnloop/content/authoring/persona_realism.py](../../../../../../../src/learnloop/content/authoring/persona_realism.py), line 27)
- `_MATH_RE` ([src/learnloop/content/authoring/persona_realism.py](../../../../../../../src/learnloop/content/authoring/persona_realism.py), line 28)
- `_HEDGE_RE` ([src/learnloop/content/authoring/persona_realism.py](../../../../../../../src/learnloop/content/authoring/persona_realism.py), line 29)
- `_FIRST_PERSON_RE` ([src/learnloop/content/authoring/persona_realism.py](../../../../../../../src/learnloop/content/authoring/persona_realism.py), line 33)
- `_MARKDOWN_RE` ([src/learnloop/content/authoring/persona_realism.py](../../../../../../../src/learnloop/content/authoring/persona_realism.py), line 34)
- `FEATURE_NAMES` ([src/learnloop/content/authoring/persona_realism.py](../../../../../../../src/learnloop/content/authoring/persona_realism.py), line 36)

## Internal implementation anchors

- `_distance(left: Sequence[float], right: Sequence[float]) -> float` ([source](../../../../../../../src/learnloop/content/authoring/persona_realism.py), line 110)
- `_centroid(rows: Sequence[Sequence[float]]) -> tuple[float, ...]` ([source](../../../../../../../src/learnloop/content/authoring/persona_realism.py), line 114)
- `_standardize(train: Sequence[Sequence[float]], row: Sequence[float]) -> tuple[float, ...]` ([source](../../../../../../../src/learnloop/content/authoring/persona_realism.py), line 118)
- `_blind_leave_pair_out(persona_rows: Sequence[Sequence[float]], real_rows: Sequence[Sequence[float]]) -> tuple[float, int, int]` ([source](../../../../../../../src/learnloop/content/authoring/persona_realism.py), line 130) — Paired folds prevent the held-out arm itself becoming a classifier cue.
- `_corpus_hash(persona: Iterable[str], real: Iterable[str]) -> str` ([source](../../../../../../../src/learnloop/content/authoring/persona_realism.py), line 196)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `match_persona_realism`; statically calls `match_persona_realism`
- [[Reference/Modules/learnloop/content/authoring/persona_gate|learnloop.content.authoring.persona_gate]] — imports `PERSONA_REALISM_MATCHER_VERSION`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_augmentation|learnloop.diagnosis.diagnostic_augmentation]] — imports `latest_realism_license`, `match_persona_realism`, `trace_corpus_hash`; statically calls `latest_realism_license`, `match_persona_realism`, `trace_corpus_hash`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `hashlib`, `json`, `math`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/content/authoring/persona_gate|learnloop.content.authoring.persona_gate]], [[Reference/Modules/learnloop/diagnosis/diagnostic_augmentation|learnloop.diagnosis.diagnostic_augmentation]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_diagnostic_augmentation.py](../../../../../../../tests/test_diagnostic_augmentation.py) — direct import
  - `test_b2_license_cannot_be_reused_for_a_different_b1_corpus`
  - `test_blind_realism_matcher_abstains_on_small_corpus_and_rejects_separable`
  - `test_identical_text_distributions_license_personas`
  - `test_licensed_b1_runs_blind_and_never_writes_a_learner_attempt`
- [tests/test_persona_gate.py](../../../../../../../tests/test_persona_gate.py) — direct import
  - `test_b2_license_from_another_generator_family_stays_advisory`
  - `test_b2_license_promotes_plain_practice_advisory_failure_to_hard`

## Modification guidance

- Change persona realism policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/authoring/persona_realism.py](../../../../../../../src/learnloop/content/authoring/persona_realism.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
