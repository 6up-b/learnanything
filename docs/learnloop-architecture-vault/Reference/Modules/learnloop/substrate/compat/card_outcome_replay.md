---
title: "learnloop.substrate.compat.card_outcome_replay"
type: "module-reference"
status: "current"
refactor_status: "COMPAT"
version: "1.0.0"
source_path: "src/learnloop/substrate/compat/card_outcome_replay.py"
source_paths:
  - "src/learnloop/substrate/compat/card_outcome_replay.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.substrate.compat"
layer: "domain"
concepts:
  - "Learning System"
  - "State and Persistence"
workflows:
  - "Rebuild and Shadow Compare"
aliases:
  - "learnloop.substrate.compat.card_outcome_replay module"
  - "src/learnloop/substrate/compat/card_outcome_replay.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/compat"
  - "layer/domain"
  - "package/learnloop-substrate-compat"
---

# `learnloop.substrate.compat.card_outcome_replay`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/substrate/compat/_package|learnloop.substrate.compat]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.substrate.compat.card_outcome_replay` exists within [[Reference/Modules/learnloop/substrate/compat/_package|learnloop.substrate.compat]] to own the behavior summarized by its module contract: P1 step 10 -- U-015 event-sufficiency replay prototype (spec §1, §9.7, §9.8).

The authoritative system-level explanation remains in [[Learning System]], [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/substrate/compat/card_outcome_replay.py](../../../../../../../src/learnloop/substrate/compat/card_outcome_replay.py) |
| Source lines | 261 |
| Owning package | [[Reference/Modules/learnloop/substrate/compat/_package|learnloop.substrate.compat]] |
| Architecture layer | `domain` |
| Refactor status | `COMPAT` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

> [!warning] Frozen compatibility boundary
> This live module is retained for old vaults. It is green but not a target for new feature growth.

## Public API

- `context_key(admin_context: Mapping[str, Any] | None, reading_phase: str | None=None) -> str` ([source](../../../../../../../src/learnloop/substrate/compat/card_outcome_replay.py), line 54) — A canonical, deterministic stratum key over the §3.10 administration context.
- `outcome_class_for_response_posterior(response_posterior: Mapping[str, Any] | None) -> str | None` ([source](../../../../../../../src/learnloop/substrate/compat/card_outcome_replay.py), line 72) — Argmax outcome class of a grade interpretation's response posterior ``P(Z|E)``.
- `class ReplayResult` ([source](../../../../../../../src/learnloop/substrate/compat/card_outcome_replay.py), line 85) — Per-card outcome counts stratified by administration context, plus the manifest.
  - `as_dict(self) -> dict[str, Any]` (line 98; public)
- `class NormalizedEvent` ([source](../../../../../../../src/learnloop/substrate/compat/card_outcome_replay.py), line 119) — One administration/observation pair reduced to the fields the projection needs.
- `replay_card_outcome_counts(repository: Any) -> ReplayResult` ([source](../../../../../../../src/learnloop/substrate/compat/card_outcome_replay.py), line 152) — The U-015 event-sufficiency prototype (§9.8).
- `replay_event_stream(events: Sequence[Mapping[str, Any]]) -> ReplayResult` ([source](../../../../../../../src/learnloop/substrate/compat/card_outcome_replay.py), line 204) — Deterministic replay of a synthetic activity-event stream (§9.7).
- `u014_resume_shape(result: ReplayResult) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/substrate/compat/card_outcome_replay.py), line 223) — Emit per-card outcome counts in the shape the deferred hierarchical likelihood model consumes (U-014 resume path, §9.8).

### Module constants

- `REPLAY_MANIFEST` ([src/learnloop/substrate/compat/card_outcome_replay.py](../../../../../../../src/learnloop/substrate/compat/card_outcome_replay.py), line 26)
- `_CONTEXT_DIMENSIONS` ([src/learnloop/substrate/compat/card_outcome_replay.py](../../../../../../../src/learnloop/substrate/compat/card_outcome_replay.py), line 43)

## Internal implementation anchors

- `_empty_counts() -> CountsByCardContext` ([source](../../../../../../../src/learnloop/substrate/compat/card_outcome_replay.py), line 114)
- `_accumulate(events: Iterable[NormalizedEvent]) -> ReplayResult` ([source](../../../../../../../src/learnloop/substrate/compat/card_outcome_replay.py), line 128) — Deterministic fold.
- `_outcome_class_from_ledger(repository: Any, observation: Mapping[str, Any]) -> str | None` ([source](../../../../../../../src/learnloop/substrate/compat/card_outcome_replay.py), line 188) — Outcome class from the grade-interpretation head (argmax P(Z|E)), falling back to the raw observed class ``G``.
- `_loads(value: Any) -> Any` ([source](../../../../../../../src/learnloop/substrate/compat/card_outcome_replay.py), line 253)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

No live LearnLoop module directly imports this module in the static graph.

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Rebuild and Shadow Compare]]

No live LearnLoop module imports it directly; its current reach is tests, repository tooling, dynamic registration, or explicit manual invocation where documented above.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_event_sufficiency.py](../../../../../../../tests/test_event_sufficiency.py) — direct import
  - `test_every_admin_obs_pair_carries_card_version_outcome_and_context`
  - `test_outcome_class_argmax_is_deterministic`
  - `test_replay_prefers_active_interpretation_head`
  - `test_replay_reads_ledger_events_only_no_live_tables`
  - `test_ten_thousand_event_replay_is_deterministic_with_manifest`
  - `test_u014_resume_shape_emits_card_level_counts`
- [tests/test_p2_acceptance.py](../../../../../../../tests/test_p2_acceptance.py) — direct import
  - `test_event_replay_equivalence_after_full_walk`

## Modification guidance

- Change card outcome replay policy here when substrate owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- This is frozen old-vault compatibility code: do not extend it without an explicit compatibility decision and fixture-backed tests.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/substrate/compat/card_outcome_replay.py](../../../../../../../src/learnloop/substrate/compat/card_outcome_replay.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
