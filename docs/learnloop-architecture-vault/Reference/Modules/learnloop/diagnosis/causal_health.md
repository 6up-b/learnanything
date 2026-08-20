---
title: "learnloop.diagnosis.causal_health"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/causal_health.py"
source_paths:
  - "src/learnloop/diagnosis/causal_health.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.diagnosis"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.causal_health module"
  - "src/learnloop/diagnosis/causal_health.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.causal_health`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.causal_health` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: P2 causal-lane fill / abstention telemetry (contract §8, v1 §12).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/causal_health.py](../../../../../../src/learnloop/diagnosis/causal_health.py) |
| Source lines | 359 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class ChannelHealth` ([source](../../../../../../src/learnloop/diagnosis/causal_health.py), line 74) — Fill / abstention counts for one causal channel.
  - `missing(self) -> int` (line 83; public)
  - `fill_rate(self) -> float` (line 87; public)
  - `abstention_rate(self) -> float` (line 91; public)
  - `tail(self, min_rows: int) -> str` (line 94; public)
  - `as_dict(self, min_rows: int=DEFAULT_MIN_ROWS) -> dict[str, Any]` (line 103; public)
- `causal_lane_health(repository: Repository, *, min_rows: int=DEFAULT_MIN_ROWS) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_health.py), line 156) — Fill / abstention rates for every causal channel, plus the triage arms.
- `triage_tier_one_health(repository: Repository) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_health.py), line 314) — Which arm of the §2.1 gate committed each tier-one route.

### Module constants

- `CAUSAL_HEALTH_VERSION` ([src/learnloop/diagnosis/causal_health.py](../../../../../../src/learnloop/diagnosis/causal_health.py), line 54)
- `DEFAULT_MIN_ROWS` ([src/learnloop/diagnosis/causal_health.py](../../../../../../src/learnloop/diagnosis/causal_health.py), line 57)
- `CHANNELS` ([src/learnloop/diagnosis/causal_health.py](../../../../../../src/learnloop/diagnosis/causal_health.py), line 59)
- `TAILS` ([src/learnloop/diagnosis/causal_health.py](../../../../../../src/learnloop/diagnosis/causal_health.py), line 70)

### Explicit exports

`__all__` declares:

- `CAUSAL_HEALTH_VERSION`
- `CHANNELS`
- `ChannelHealth`
- `DEFAULT_MIN_ROWS`
- `TAILS`
- `causal_lane_health`
- `triage_tier_one_health`

## Internal implementation anchors

- `class _Counter` ([source](../../../../../../src/learnloop/diagnosis/causal_health.py), line 116)
- `_receipt_for(repository: Repository, attempt_id: str) -> Mapping[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/causal_health.py), line 139)
- `_is_open_set(row: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/diagnosis/causal_health.py), line 148)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `causal_lane_health`; statically calls `causal_lane_health`
- [[Reference/Modules/learnloop_sidecar/handlers/measurement|learnloop_sidecar.handlers.measurement]] — imports `causal_lane_health`; statically calls `causal_lane_health`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `APPROVED_SUPPORT_AUTHORITIES`, `OPEN_SET_CAUSE_ID`
- [[Reference/Modules/learnloop/diagnosis/causal_probe_coherence|learnloop.diagnosis.causal_probe_coherence]] — imports `BLIND_INPUT_CONTRACT_VERSION`, `bundle_feature_row_report`; calls `bundle_feature_row_report`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop_sidecar/handlers/measurement|learnloop_sidecar.handlers.measurement]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_causal_p2_acceptance.py](../../../../../../tests/test_causal_p2_acceptance.py) — direct import
  - `test_a_deterministic_sensor_earns_validator_owned_and_reaches_triage`
  - `test_causal_lane_health_watches_both_tails_and_pins_the_tier_one_basis`

## Modification guidance

- Change causal health policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/causal_health.py](../../../../../../src/learnloop/diagnosis/causal_health.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
