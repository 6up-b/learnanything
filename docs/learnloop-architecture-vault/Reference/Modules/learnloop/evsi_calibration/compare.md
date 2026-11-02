---
title: "learnloop.evsi_calibration.compare"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/evsi_calibration/compare.py"
source_paths:
  - "src/learnloop/evsi_calibration/compare.py"
source_commit: "da5c9ecf8613df293d5f36f7d2c0b3fd93f3eafb"
source_commit_timestamp: "2026-10-13T15:35:46-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.evsi_calibration"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.evsi_calibration.compare module"
  - "src/learnloop/evsi_calibration/compare.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-evsi-calibration"
---

# `learnloop.evsi_calibration.compare`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.evsi_calibration.compare` exists within [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] to own the behavior summarized by its module contract: Compare two ``learnloop evsi simulate`` reports: every recorded value, every headline claim.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/evsi_calibration/compare.py](../../../../../../src/learnloop/evsi_calibration/compare.py) |
| Source lines | 1483 |
| Owning package | [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `da5c9ecf8613df293d5f36f7d2c0b3fd93f3eafb` |
| Commit timestamp | `2026-10-13T15:35:46-04:00` |

## Public API

- `strength_label(value: Any) -> str` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 126) — ``fitted`` (Eedi's own consistency) or the overriding consistency.
- `applied_bound(report: Mapping[str, Any]) -> int | None` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 147) — The count bound a report's episodes ran under.
- `quantity(label: str, old: Any, new: Any, old_ci: Any=None, new_ci: Any=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 169) — One recorded value in both reports, and how it moved.
- `recorded_bound_stops(report: Mapping[str, Any], key: CellKey, policy: str, episodes: int | None) -> tuple[int | None, str]` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 527) — What a stored report itself says its bound stopped in a cell: the ``safety_bound`` stop reason when the report kept it, 0 when it kept every stop reason and that one is absent, else unknown (``truncated``: only the most frequent reasons were kept; ``not_recorded``: none were).
- `bound_stops(old: Mapping[str, Any], new: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 559) — Per cell and arm, the episodes the bounded report's bound stopped, read from the unbounded report's ``count_bound`` cells, and what the bounded report itself recorded.
- `compare_cells(old: Mapping[str, Any], new: Mapping[str, Any], bounds: Mapping[tuple[CellKey, str], tuple[int, int]] | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 668) — Every (cell, arm) of either report, and every report-level section, in the study's order, each recorded value old against new.
- `attribution(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 704) — Every arm where the bound stopped no episode must be identical in both reports; one where it stopped episodes only at a check their own rule would have stopped at anyway (none ran past it unbounded) may differ only in its stop reasons.
- `ranks(old: Mapping[str, Any], new: Mapping[str, Any]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 729) — Each main and regime cell's arms by mean minutes per episode (ties by the study's arm order), old against new.
- `class Assertion` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 891) — One condition of a claim, evaluated on its own.
- `conclusion(id: str, text: str, check: Callable[[Values], bool | None]) -> Assertion` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 906)
- `figure(label: str, stated: float, unit: float, *, part: str='point', low: float | None=None, high: float | None=None, said: str | None=None) -> Assertion` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 910) — A figure the statement gives, within half a unit of its last digit (``unit``), or inside [``low``, ``high``] for a figure stated as a range or to one significant digit.
- `class Claim` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 934)
- `compare_claims(old: Mapping[str, Any], new: Mapping[str, Any]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 1307)
- `compare_reports(old: Mapping[str, Any], new: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 1347) — The whole comparison, in the study's order (see the module docstring).
- `render_markdown(comparison: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 1416) — Tables for a review file: bound stops, claims and their assertions, every moved value, rank changes.

### Module constants

- `COMPARE_VERSION` ([src/learnloop/evsi_calibration/compare.py](../../../../../../src/learnloop/evsi_calibration/compare.py), line 49)
- `SECTIONS` ([src/learnloop/evsi_calibration/compare.py](../../../../../../src/learnloop/evsi_calibration/compare.py), line 50)
- `CELL_SECTIONS` ([src/learnloop/evsi_calibration/compare.py](../../../../../../src/learnloop/evsi_calibration/compare.py), line 51)
- `SYSTEM_MODELS` ([src/learnloop/evsi_calibration/compare.py](../../../../../../src/learnloop/evsi_calibration/compare.py), line 52)
- `PART_C_LOSSES` ([src/learnloop/evsi_calibration/compare.py](../../../../../../src/learnloop/evsi_calibration/compare.py), line 53)
- `METADATA_KEYS` ([src/learnloop/evsi_calibration/compare.py](../../../../../../src/learnloop/evsi_calibration/compare.py), line 58)
- `CELL_ROW` ([src/learnloop/evsi_calibration/compare.py](../../../../../../src/learnloop/evsi_calibration/compare.py), line 61)
- `REPORT_ROW` ([src/learnloop/evsi_calibration/compare.py](../../../../../../src/learnloop/evsi_calibration/compare.py), line 63)
- `SAME` ([src/learnloop/evsi_calibration/compare.py](../../../../../../src/learnloop/evsi_calibration/compare.py), line 65)
- `RECORDED_STOP_REASONS` ([src/learnloop/evsi_calibration/compare.py](../../../../../../src/learnloop/evsi_calibration/compare.py), line 67)
- `STATUS_ORDER` ([src/learnloop/evsi_calibration/compare.py](../../../../../../src/learnloop/evsi_calibration/compare.py), line 69)
- `DIFFERS` ([src/learnloop/evsi_calibration/compare.py](../../../../../../src/learnloop/evsi_calibration/compare.py), line 71)
- `CI_POINTS` ([src/learnloop/evsi_calibration/compare.py](../../../../../../src/learnloop/evsi_calibration/compare.py), line 227)
- `RANGE_KEYS` ([src/learnloop/evsi_calibration/compare.py](../../../../../../src/learnloop/evsi_calibration/compare.py), line 239)
- `RECORD_KEYS` ([src/learnloop/evsi_calibration/compare.py](../../../../../../src/learnloop/evsi_calibration/compare.py), line 241)
- `GROUP_ORDER` ([src/learnloop/evsi_calibration/compare.py](../../../../../../src/learnloop/evsi_calibration/compare.py), line 243)
- `_STOP_REASON` ([src/learnloop/evsi_calibration/compare.py](../../../../../../src/learnloop/evsi_calibration/compare.py), line 244)
- `NONE` ([src/learnloop/evsi_calibration/compare.py](../../../../../../src/learnloop/evsi_calibration/compare.py), line 758)
- `VALUE_RULES` ([src/learnloop/evsi_calibration/compare.py](../../../../../../src/learnloop/evsi_calibration/compare.py), line 943)
- `REPAIRS` ([src/learnloop/evsi_calibration/compare.py](../../../../../../src/learnloop/evsi_calibration/compare.py), line 944)
- `VALUE_PER_NAT` ([src/learnloop/evsi_calibration/compare.py](../../../../../../src/learnloop/evsi_calibration/compare.py), line 946)
- `NAT` ([src/learnloop/evsi_calibration/compare.py](../../../../../../src/learnloop/evsi_calibration/compare.py), line 997)
- `MINUTES_PER_NAT_CELLS` ([src/learnloop/evsi_calibration/compare.py](../../../../../../src/learnloop/evsi_calibration/compare.py), line 1024)
- `SENSITIVITY_ARMS` ([src/learnloop/evsi_calibration/compare.py](../../../../../../src/learnloop/evsi_calibration/compare.py), line 1099)
- `QUANTILE` ([src/learnloop/evsi_calibration/compare.py](../../../../../../src/learnloop/evsi_calibration/compare.py), line 1100)
- `REPAIR_SWEEP` ([src/learnloop/evsi_calibration/compare.py](../../../../../../src/learnloop/evsi_calibration/compare.py), line 1101)
- `CHECK_SWEEP` ([src/learnloop/evsi_calibration/compare.py](../../../../../../src/learnloop/evsi_calibration/compare.py), line 1102)
- `CLAIMS` ([src/learnloop/evsi_calibration/compare.py](../../../../../../src/learnloop/evsi_calibration/compare.py), line 1140)

### Explicit exports

`__all__` declares:

- `CLAIMS`
- `COMPARE_VERSION`
- `METADATA_KEYS`
- `Assertion`
- `applied_bound`
- `bound_stops`
- `compare_reports`
- `quantity`
- `recorded_bound_stops`
- `render_markdown`
- `strength_label`

## Internal implementation anchors

- `_get(mapping: Any, *path: Any) -> Any` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 77)
- `_number(value: Any) -> float | None` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 85)
- `_interval(value: Any) -> list[float] | None` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 95)
- `_absent(value: Any) -> bool` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 102)
- `_g(value: Any) -> str` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 106)
- `_policy_key(policy: str) -> tuple[int, int, str]` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 111)
- `_policies(*mappings: Any) -> list[str]` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 118)
- `_strength_key(label: str) -> tuple[int, float, str]` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 135)
- `_sweep_key(name: str) -> tuple[int, str]` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 142)
- `_shown(raw: Any, number: float | None) -> Any` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 161)
- `_worst(statuses: Sequence[str]) -> str` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 210)
- `class _Ci(tuple)` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 220) — A recorded 95% CI (two endpoints, or empty for ``None``), kept whole so it travels with its point estimate.
- `_canonical(value: Any) -> str` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 247)
- `_records(items: Sequence[Any]) -> list[tuple[str, Any]]` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 251) — A list's items, each under a name that does not depend on the list's order.
- `_flatten(value: Any, prefix: str='', out: dict[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 271) — Every recorded leaf under ``value`` by a dotted path (``a.b[name].c``); a CI stays whole (:class:`_Ci`).
- `_block(value: Any, prefix: str='') -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 292)
- `_metric_key(label: str) -> tuple[int, str]` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 296)
- `_reasons_complete(reasons: Mapping[str, Any], section: str, episodes: Any) -> bool` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 303) — Whether a report kept every stop reason of an arm: a section that keeps all of them, fewer kept than the section keeps, or kept counts that add up to the arm's episodes.
- `_with_absent_reasons(flat: Mapping[str, Any], other: Mapping[str, Any], section: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 318) — A stop reason the other report records and this one does not is 0 here when this report kept every stop reason of the arm.
- `_metrics(left: Mapping[str, Any], right: Mapping[str, Any], section: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 339) — Every value of one arm (or one report-level section) in both reports.
- `class _Cell` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 380)
- `_cells(report: Mapping[str, Any]) -> dict[CellKey, _Cell]` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 388)
- `_cell_label(describe: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 478)
- `_minutes(flat: Mapping[str, Any] | None) -> float | None` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 491)
- `_bound_key(cell: Mapping[str, Any]) -> CellKey` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 500)
- `_recorded_stop_reasons(report: Mapping[str, Any], key: CellKey, policy: str) -> Mapping[str, int] | None` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 511)
- `_bound_result(old_bound: Any, new_bound: Any, relation: str, *, reference: Any=None, reason: str | None=None, rows: Sequence[dict[str, Any]]=()) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 542)
- `_bounds_by_cell(bound: Mapping[str, Any]) -> dict[tuple[CellKey, str], tuple[int, int]]` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 633)
- `_row_bound(bounds: Mapping[tuple[CellKey, str], tuple[int, int]], key: CellKey, policy: str, describe: Mapping[str, Any]) -> tuple[int, int]` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 642) — The episodes behind one row that the bound stopped, and those it changed (ran past it unbounded).
- `_regime_row(report: Mapping[str, Any], strength: Any, repair: float) -> Mapping[str, Any] | None` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 761)
- `_regime_value(report: Mapping[str, Any], strength: Any, repair: float, policy: str, metric: str='mean_total_minutes', ci: str | None='total_minutes_ci95') -> Value` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 769)
- `_regime_stop(report: Mapping[str, Any], strength: Any, repair: float, policy: str, reason: str) -> Value` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 775)
- `_regime_minutes_per_nat(report: Mapping[str, Any], strength: Any, repair: float, policy: str) -> Value` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 785)
- `_sweep_row(report: Mapping[str, Any], parameter: str, value: float) -> Mapping[str, Any] | None` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 790)
- `_sweep_value(report: Mapping[str, Any], parameter: str, value: float, policy: str, metric: str='difference') -> Value` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 797)
- `_sweep_values(report: Mapping[str, Any], parameter: str) -> list[float]` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 807)
- `_sweep_current(report: Mapping[str, Any], parameter: str) -> float | None` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 812)
- `_part_c(report: Mapping[str, Any], strength: Any, encounters: float, policy: str, metric: str='difference') -> Value` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 816)
- `_part_c_encounters(report: Mapping[str, Any]) -> list[float]` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 827)
- `_diff(a: Value, b: Value) -> Value` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 832)
- `_point(values: Values, label: str) -> float | None` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 837)
- `_ci(values: Values, label: str) -> list[float] | None` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 841)
- `_below(values: Values, label: str) -> bool | None` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 845)
- `_above(values: Values, label: str) -> bool | None` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 850)
- `_spans_zero(values: Values, label: str) -> bool | None` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 855)
- `_lt(values: Values, low: str, high: str) -> bool | None` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 860)
- `_all(verdicts: Sequence[bool | None]) -> bool | None` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 865)
- `_any(verdicts: Sequence[bool | None]) -> bool | None` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 871)
- `_extreme(values: Values, policy: str, cell: str, *, highest: bool=False) -> bool | None` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 877) — Strictly the lowest (or highest) of every arm the cell records.
- `_arms(report: Mapping[str, Any], strength: Any, repair: float) -> list[tuple[str, Value]]` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 949)
- `_s2(report: Mapping[str, Any]) -> list[tuple[str, Value]]` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 954)
- `_s3(report: Mapping[str, Any]) -> list[tuple[str, Value]]` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 964)
- `_s3f(report: Mapping[str, Any]) -> list[tuple[str, Value]]` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 979)
- `_s3g(report: Mapping[str, Any]) -> list[tuple[str, Value]]` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 990)
- `_s4a(report: Mapping[str, Any]) -> list[tuple[str, Value]]` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 1000)
- `_s4a_best_at_10(values: Values) -> bool | None` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 1010)
- `_s4a_gate_flat(values: Values) -> bool | None` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 1017)
- `_s4b(report: Mapping[str, Any]) -> list[tuple[str, Value]]` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 1027)
- `_s4b_above_every_ci(values: Values) -> bool | None` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 1049)
- `_sweep_claim(parameter: str, policies: Sequence[str], prefix: str='', tau: bool=False) -> Callable[[Mapping[str, Any]], list[tuple[str, Value]]]` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 1056) — Each swept value's paired difference against the current value, per arm (and, with ``tau``, the first decision's ranking τ against it, read off ``evsi``).
- `_deltas(values: Values, prefix: str='') -> list[str]` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 1076)
- `_no_minutes_effect(values: Values) -> bool | None` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 1080) — Every paired difference is within noise (its CI spans 0) or negligible (under 0.05 minutes per episode: EVSI as built at a concentration of 4 or 10 moves 0.013 with a CI just clear of 0).
- `_rankings_move(prefix: str) -> Callable[[Values], bool | None]` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 1092)
- `_s6(report: Mapping[str, Any]) -> list[tuple[str, Value]]` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 1105)
- `_part_c_cells(values: Values) -> list[tuple[str, str, float]]` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 1116)
- `_s6_check(where: Callable[[str, float], bool], verdict: Callable[[Values, str], bool | None]) -> Callable[[Values], bool | None]` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 1125)
- `_not(predicate: Callable[[Values, str], bool | None]) -> Callable[[Values, str], bool | None]` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 1133)
- `_pair(left: tuple[Any, Any] | None, right: tuple[Any, Any] | None) -> tuple[Any, Any, Any, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 1341)
- `_fmt(value: Any) -> str` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 1393) — A stored number as stored (4 places at most), anything else as text.
- `_fmt_q(point: Any, ci: list[float] | None) -> str` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 1405)
- `_md(text: Any) -> str` ([source](../../../../../../src/learnloop/evsi_calibration/compare.py), line 1410) — Text for a Markdown table cell (a literal ``|`` would split it).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/evsi|learnloop.cli.evsi]] — imports `compare_reports`, `render_markdown`; statically calls `compare_reports`, `render_markdown`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/evsi_calibration/experiments|learnloop.evsi_calibration.experiments]] — imports `SWEEPS`
- [[Reference/Modules/learnloop/evsi_calibration/policies|learnloop.evsi_calibration.policies]] — imports `module`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `math`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/evsi|learnloop.cli.evsi]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_evsi_single_family_unbounded.py](../../../../../../tests/test_evsi_single_family_unbounded.py) — direct import
  - `test_cli_simulate_passes_an_explicit_bound_through`
  - `test_each_conclusion_is_falsified_on_its_own`
  - `test_each_stated_figure_is_checked_at_its_precision`
  - `test_every_assertion_of_every_claim_holds_on_the_stored_run`
  - `test_every_recorded_value_is_compared`
  - `test_the_bound_attribution_needs_the_bound_the_other_report_applied`
  - `test_the_codex_case_no_longer_certifies_s4b`
  - `test_the_comparison_tools_ordering_is_stable`
  - `test_the_stored_reports_own_stop_reasons_are_read_only_where_complete`

## Modification guidance

- Make changes here when the responsibility remains compare within learnloop.evsi_calibration; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/evsi_calibration/compare.py](../../../../../../src/learnloop/evsi_calibration/compare.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
