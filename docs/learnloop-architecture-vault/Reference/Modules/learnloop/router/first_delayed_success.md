---
title: "learnloop.router.first_delayed_success"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router/first_delayed_success.py"
source_paths:
  - "src/learnloop/router/first_delayed_success.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.router"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.router.first_delayed_success module"
  - "src/learnloop/router/first_delayed_success.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router"
---

# `learnloop.router.first_delayed_success`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router/_package|learnloop.router]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router.first_delayed_success` exists within [[Reference/Modules/learnloop/router/_package|learnloop.router]] to own the behavior summarized by its module contract: A3: the honest time metric: calendar time and recorded minutes to a first delayed success.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router/first_delayed_success.py](../../../../../../src/learnloop/router/first_delayed_success.py) |
| Source lines | 453 |
| Owning package | [[Reference/Modules/learnloop/router/_package|learnloop.router]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class Trajectory` ([source](../../../../../../src/learnloop/router/first_delayed_success.py), line 69)
  - `reached(self) -> bool` (line 91; public)
  - `complete_latency(self) -> bool` (line 95; public)
  - `active_minutes(self) -> float` (line 99; public)
  - `elapsed_minutes(self) -> float` (line 103; public)
  - `as_dict(self) -> dict[str, Any]` (line 106; public)
- `trajectories(connection: sqlite3.Connection, vault: Any, *, success_correctness: float, as_of: str, pfc_states: Mapping[str, str] | None=None, held_attempt_ids: frozenset[str] | set[str]=frozenset(), reader_exposures: Iterable[tuple[str, str]]) -> tuple[list[Trajectory], dict[str, Any]]` ([source](../../../../../../src/learnloop/router/first_delayed_success.py), line 334) — Every enrolled LO's trajectory, reached or not, and the report-level timing facts.
- `summary(rows: Sequence[Trajectory], facts: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router/first_delayed_success.py), line 417) — The report's numbers: counts, means over those reached, and the coverage that bounds them.

### Module constants

- `METRIC_VERSION` ([src/learnloop/router/first_delayed_success.py](../../../../../../src/learnloop/router/first_delayed_success.py), line 41)
- `LABEL` ([src/learnloop/router/first_delayed_success.py](../../../../../../src/learnloop/router/first_delayed_success.py), line 42)
- `SOURCE_GOAL` ([src/learnloop/router/first_delayed_success.py](../../../../../../src/learnloop/router/first_delayed_success.py), line 44)
- `SOURCE_COMMITMENT` ([src/learnloop/router/first_delayed_success.py](../../../../../../src/learnloop/router/first_delayed_success.py), line 45)
- `SOURCE_FIRST_EXPOSURE` ([src/learnloop/router/first_delayed_success.py](../../../../../../src/learnloop/router/first_delayed_success.py), line 46)
- `_SYSTEM_VIA` ([src/learnloop/router/first_delayed_success.py](../../../../../../src/learnloop/router/first_delayed_success.py), line 48)
- `_NON_PROBLEM` ([src/learnloop/router/first_delayed_success.py](../../../../../../src/learnloop/router/first_delayed_success.py), line 50)

### Explicit exports

`__all__` declares:

- `LABEL`
- `METRIC_VERSION`
- `Trajectory`
- `summary`
- `trajectories`

## Internal implementation anchors

- `class _Membership` ([source](../../../../../../src/learnloop/router/first_delayed_success.py), line 54) — One goal's hold on an LO: all its contract versions, oldest first, and which of them cover the LO.
- `_seconds(later: str, earlier: str) -> float | None` ([source](../../../../../../src/learnloop/router/first_delayed_success.py), line 111)
- `_days(later: str, earlier: str) -> float | None` ([source](../../../../../../src/learnloop/router/first_delayed_success.py), line 118)
- `_covers(learning_object: Any, concepts: set[str], facets: set[str]) -> bool` ([source](../../../../../../src/learnloop/router/first_delayed_success.py), line 123)
- `_recorded_scope(version: Mapping[str, Any]) -> tuple[set[str], set[str]] | None` ([source](../../../../../../src/learnloop/router/first_delayed_success.py), line 127) — A contract version's own recorded scope; None when its body names none (the goal's stands in).
- `_goal_scopes(vault: Any, contracts: Mapping[str, list[dict[str, Any]]]) -> dict[str, list[_Membership]]` ([source](../../../../../../src/learnloop/router/first_delayed_success.py), line 139) — Each LO's goals (any status: an enrollment is a historical fact) and which of each goal's contract versions held it, by each version's own scope.
- `_contract_rows(connection: sqlite3.Connection) -> dict[str, list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/router/first_delayed_success.py), line 160)
- `_pinned(memberships: Sequence[_Membership], as_of: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/router/first_delayed_success.py), line 171) — The contract in force at ``as_of`` that applies: of the LO's first goal whose newest confirmed version then covers it.
- `_commitment_times(connection: sqlite3.Connection, vault: Any) -> dict[str, str]` ([source](../../../../../../src/learnloop/router/first_delayed_success.py), line 196) — Each LO's first commitment by the learner (a system-dated check is no enrollment).
- `_enrollment(lo: str, memberships: Sequence[_Membership], commitments: Mapping[str, str], ledger: _Ledger) -> tuple[str, str] | None` ([source](../../../../../../src/learnloop/router/first_delayed_success.py), line 219)
- `_visits(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/router/first_delayed_success.py), line 234) — Reader visits as open, close, active seconds (a visit with no close has no recorded time).
- `_reading_marks(connection: sqlite3.Connection, reader_exposures: Iterable[tuple[str, str]]) -> list[tuple[str, str]]` ([source](../../../../../../src/learnloop/router/first_delayed_success.py), line 259) — ``(time, LO)`` of reading on an LO: the Reader exposures and source exposures.
- `_attribute_visits(visits: Sequence[Mapping[str, Any]], marks: Sequence[tuple[str, str]]) -> tuple[dict[str, list[dict[str, Any]]], float]` ([source](../../../../../../src/learnloop/router/first_delayed_success.py), line 270) — Each LO's visits, an even share of each, and the active seconds no LO could be named for.
- `_plan_reading(connection: sqlite3.Connection, decisions: Sequence[Mapping[str, Any]]) -> dict[str, list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/router/first_delayed_success.py), line 287) — A reading block's start-to-end, on its frozen objective's LO (plan timing, mvp-0.44 on).
- `_merged(spans: Sequence[tuple[str, str]]) -> list[tuple[float, float]]` ([source](../../../../../../src/learnloop/router/first_delayed_success.py), line 306) — The union of ``(start, end)`` time spans as sorted, disjoint instants.
- `_blocks_outside_visits(blocks: Sequence[Mapping[str, Any]], visits: Sequence[Mapping[str, Any]]) -> float` ([source](../../../../../../src/learnloop/router/first_delayed_success.py), line 321) — Seconds of the blocks' union no visit of the same LO holds: a reading block runs inside a Reader visit and both record its interval (Codex review F5), so the visit counts it and the block only the rest.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/scoreboard|learnloop.diagnosis.scoreboard]] — imports `LABEL`, `summary`, `trajectories`; statically calls `summary`, `trajectories`
- [[Reference/Modules/learnloop/ops/capture_report|learnloop.ops.capture_report]] — imports `summary`, `trajectories`; statically calls `summary`, `trajectories`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/delayed_completion|learnloop.delayed_completion]] — imports `module`
- [[Reference/Modules/learnloop/router/outcomes|learnloop.router.outcomes]] — imports `OUTCOME_VERSION_V3`, `_Ledger`, `_completion`, `_decision_block`, `_table_present`; calls `_Ledger`, `_completion`, `_decision_block`, `_table_present`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `learning_object_facet_union`; calls `learning_object_facet_union`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/scoreboard|learnloop.diagnosis.scoreboard]], [[Reference/Modules/learnloop/ops/capture_report|learnloop.ops.capture_report]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_data_capture_a3_time_metric.py](../../../../../../tests/test_data_capture_a3_time_metric.py) — direct import
  - `test_the_summary_keeps_unfinished_trajectories_and_coverage_visible`
- [tests/test_data_capture_codex_rereview.py](../../../../../../tests/test_data_capture_codex_rereview.py) — direct import
  - `test_f1_a_completed_section_is_an_exposure_with_ad_off`
- [tests/test_data_capture_codex_review.py](../../../../../../tests/test_data_capture_codex_review.py) — direct import
- [tests/test_data_capture_landing_review.py](../../../../../../tests/test_data_capture_landing_review.py) — direct import
  - `test_f1_version_3_refuses_to_derive_without_the_read`

## Modification guidance

- Make changes here when the responsibility remains first delayed success within learnloop.router; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router/first_delayed_success.py](../../../../../../src/learnloop/router/first_delayed_success.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
