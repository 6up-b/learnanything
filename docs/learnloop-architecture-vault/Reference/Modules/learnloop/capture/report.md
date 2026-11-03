---
title: "learnloop.capture.report"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/capture/report.py"
source_paths:
  - "src/learnloop/capture/report.py"
source_commit: "ebeb12e2970c51fdd8a276f7295d52327bf89a41"
source_commit_timestamp: "2026-11-03T13:50:57-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.capture"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.capture.report module"
  - "src/learnloop/capture/report.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-capture"
---

# `learnloop.capture.report`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/capture/_package|learnloop.capture]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.capture.report` exists within [[Reference/Modules/learnloop/capture/_package|learnloop.capture]] to own the behavior summarized by its module contract: The M2 usage report (mobile spec §9, §10): read-only, no thresholds.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/capture/report.py](../../../../../../src/learnloop/capture/report.py) |
| Source lines | 134 |
| Owning package | [[Reference/Modules/learnloop/capture/_package|learnloop.capture]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `ebeb12e2970c51fdd8a276f7295d52327bf89a41` |
| Commit timestamp | `2026-11-03T13:50:57-05:00` |

## Public API

- `suspected_figure(prompt: str) -> str | None` ([source](../../../../../../src/learnloop/capture/report.py), line 32) — The phrase that reads like a missing figure, or None.
- `mobile_report(repo: Repository, *, prompts: Mapping[str, str] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/capture/report.py), line 59) — §9's M2a report, §10's device split and §6.4's suspected figures.

### Module constants

- `SUBMIT_ENDPOINTS` ([src/learnloop/capture/report.py](../../../../../../src/learnloop/capture/report.py), line 21)
- `GRADE_CONTEST` ([src/learnloop/capture/report.py](../../../../../../src/learnloop/capture/report.py), line 22)
- `_NOUN` ([src/learnloop/capture/report.py](../../../../../../src/learnloop/capture/report.py), line 23)
- `_LOCATOR` ([src/learnloop/capture/report.py](../../../../../../src/learnloop/capture/report.py), line 24)
- `_SUSPECTED_FIGURE` ([src/learnloop/capture/report.py](../../../../../../src/learnloop/capture/report.py), line 27)

## Internal implementation anchors

- `_percentile(values: list[float], fraction: float) -> float | None` ([source](../../../../../../src/learnloop/capture/report.py), line 39)
- `_week(stamp: str) -> str` ([source](../../../../../../src/learnloop/capture/report.py), line 46)
- `_seconds(start: str, end: str) -> float` ([source](../../../../../../src/learnloop/capture/report.py), line 51)
- `_rate(part: int, whole: int) -> float | None` ([source](../../../../../../src/learnloop/capture/report.py), line 55)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]] — imports `mobile_report`, `suspected_figure`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `datetime`, `json`, `math`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/mobile_host_helpers.py](../../../../../../tests/mobile_host_helpers.py) — imports consumer [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]]
- [tests/test_capture_desktop.py](../../../../../../tests/test_capture_desktop.py) — imports consumer [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]]
- [tests/test_capture_domain.py](../../../../../../tests/test_capture_domain.py) — imports consumer [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]]
- [tests/test_capture_originals_race.py](../../../../../../tests/test_capture_originals_race.py) — imports consumer [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]]
- [tests/test_capture_route_recovery.py](../../../../../../tests/test_capture_route_recovery.py) — imports consumer [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]]
- [tests/test_mobile_handoff.py](../../../../../../tests/test_mobile_handoff.py) — imports consumer [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]]
- [tests/test_mobile_host_auth.py](../../../../../../tests/test_mobile_host_auth.py) — imports consumer [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]]
- [tests/test_mobile_host_coexistence.py](../../../../../../tests/test_mobile_host_coexistence.py) — imports consumer [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]]
- [tests/test_mobile_jobs.py](../../../../../../tests/test_mobile_jobs.py) — imports consumer [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]]
- [tests/test_mobile_pairing.py](../../../../../../tests/test_mobile_pairing.py) — imports consumer [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]]
- [tests/test_reader_ca1_as_printed.py](../../../../../../tests/test_reader_ca1_as_printed.py) — imports consumer [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]]

## Modification guidance

- Make changes here when the responsibility remains report within learnloop.capture; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/capture/report.py](../../../../../../src/learnloop/capture/report.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
