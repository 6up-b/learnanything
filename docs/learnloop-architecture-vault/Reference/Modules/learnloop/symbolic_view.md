---
title: "learnloop.symbolic_view"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/symbolic_view.py"
source_paths:
  - "src/learnloop/symbolic_view.py"
source_commit: "5825048f775dc44bf0dc7d1a4b5bcaa1b0bf7b9f"
source_commit_timestamp: "2026-10-22T16:23:31-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.symbolic_view module"
  - "src/learnloop/symbolic_view.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop"
---

# `learnloop.symbolic_view`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.symbolic_view` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: Reader workbench RW2b: the ONE accessor for stored symbolic results (fix round 11, the orchestrator's ruling).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/symbolic_view.py](../../../../../src/learnloop/symbolic_view.py) |
| Source lines | 198 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `5825048f775dc44bf0dc7d1a4b5bcaa1b0bf7b9f` |
| Commit timestamp | `2026-10-22T16:23:31-04:00` |

## Public API

- `switch(config: Any) -> bool` ([source](../../../../../src/learnloop/symbolic_view.py), line 33) — ``workbench.symbolic_checks_enabled`` from a config, a vault, or None (off).
- `switch_now(vault: Any) -> bool` ([source](../../../../../src/learnloop/symbolic_view.py), line 40) — ``workbench.symbolic_checks_enabled`` as the vault's config file says NOW (fix round 14, item 3): a job that holds a vault captured earlier (a post-attempt drain) reads the live file, never the captured snapshot.
- `trace_view(trace: Mapping[str, Any] | None, *, enabled: bool) -> dict[str, Any] | None` ([source](../../../../../src/learnloop/symbolic_view.py), line 59) — A diagnoser's workbench trace with each check's verdicts as read now.
- `symbolic_view(raw: Any, *, enabled: bool) -> str` ([source](../../../../../src/learnloop/symbolic_view.py), line 75) — A stored method or claim status as it may be read now.
- `verdict_records(row: Mapping[str, Any] | None, *, enabled: bool) -> list[dict[str, Any]]` ([source](../../../../../src/learnloop/symbolic_view.py), line 91) — A check row's stored verdict records, each ``method`` as read now.
- `has_verdict_record(row: Mapping[str, Any] | None) -> bool` ([source](../../../../../src/learnloop/symbolic_view.py), line 102) — Whether a row recorded step verdicts at all (an empty record included): a help's unaided progress needs the verdicts standing at its delivery, and none on record is not "none valid" (Reader RW2c fix round 3, M1).
- `symbolic_outcomes(placement: Any, *, enabled: bool) -> list[dict[str, Any]]` ([source](../../../../../src/learnloop/symbolic_view.py), line 111) — A check row's stored symbolic outcomes (``placement_json``), each ``method`` as read now (with the switch off a decided ``holds`` is not shown).
- `claim_view(claim: Mapping[str, Any], *, enabled: bool) -> dict[str, Any]` ([source](../../../../../src/learnloop/symbolic_view.py), line 124) — One stored claim as read now (its status and its label).
- `claims_view(claims: Iterable[Any] | None, *, enabled: bool) -> list[dict[str, Any]]` ([source](../../../../../src/learnloop/symbolic_view.py), line 135)
- `stored_claims(row: Mapping[str, Any] | None, *, enabled: bool) -> list[dict[str, Any]]` ([source](../../../../../src/learnloop/symbolic_view.py), line 139) — A hint row's stored claims (``contract_failures_json``) as read now.
- `rounds_view(rounds: Iterable[Any] | None, *, enabled: bool) -> list[Any]` ([source](../../../../../src/learnloop/symbolic_view.py), line 146) — A hint's writer rounds with each round's claims as they may be stored NOW (fix round 13: the switch read right before the row is serialized).
- `live_switch(reader: Any) -> bool | None` ([source](../../../../../src/learnloop/symbolic_view.py), line 159) — A live switch reader's value now (None: no reader; an error: off).
- `hint_result_view(result: Mapping[str, Any], *, enabled: bool) -> dict[str, Any]` ([source](../../../../../src/learnloop/symbolic_view.py), line 170) — A hint job's payload as read now: its claims remapped and the CURRENT switch (the payload is cached with the job; the switch is read each time).

### Module constants

- `SYMBOLIC_METHODS` ([src/learnloop/symbolic_view.py](../../../../../src/learnloop/symbolic_view.py), line 28)
- `MODEL` ([src/learnloop/symbolic_view.py](../../../../../src/learnloop/symbolic_view.py), line 29)
- `MODEL_LABEL` ([src/learnloop/symbolic_view.py](../../../../../src/learnloop/symbolic_view.py), line 30)

### Explicit exports

`__all__` declares:

- `has_verdict_record`
- `MODEL`
- `MODEL_LABEL`
- `SYMBOLIC_METHODS`
- `claim_view`
- `claims_view`
- `hint_result_view`
- `live_switch`
- `rounds_view`
- `stored_claims`
- `switch`
- `switch_now`
- `trace_view`
- `symbolic_outcomes`
- `symbolic_view`
- `verdict_records`

## Internal implementation anchors

- `_loads(value: Any, default: Any) -> Any` ([source](../../../../../src/learnloop/symbolic_view.py), line 82)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/split/context|learnloop.diagnosis.split.context]] — imports `switch_now`, `trace_view`; statically calls `switch_now`, `trace_view`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `switch_now`, `trace_view`; statically calls `switch_now`, `trace_view`
- [[Reference/Modules/learnloop/diagnosis/split/live|learnloop.diagnosis.split.live]] — imports `switch_now`; statically calls `switch_now`
- [[Reference/Modules/learnloop/diagnosis/split/prior_analysis|learnloop.diagnosis.split.prior_analysis]] — imports `switch_now`; statically calls `switch_now`
- [[Reference/Modules/learnloop/diagnosis/split/workbench_trace|learnloop.diagnosis.split.workbench_trace]] — imports `verdict_records`; statically calls `verdict_records`
- [[Reference/Modules/learnloop/hints/report_workbench|learnloop.hints.report_workbench]] — imports `has_verdict_record`, `symbolic_outcomes`, `verdict_records`; statically calls `has_verdict_record`, `symbolic_outcomes`, `verdict_records`
- [[Reference/Modules/learnloop/hints/service|learnloop.hints.service]] — imports `claims_view`, `live_switch`, `rounds_view`; statically calls `claims_view`, `live_switch`, `rounds_view`
- [[Reference/Modules/learnloop/hints/workbench|learnloop.hints.workbench]] — imports `switch`, `symbolic_view`; statically calls `switch`, `symbolic_view`
- [[Reference/Modules/learnloop/workbench/check|learnloop.workbench.check]] — imports `verdict_records`; statically calls `verdict_records`
- [[Reference/Modules/learnloop/workbench/ladder|learnloop.workbench.ladder]] — imports `stored_claims`, `verdict_records`; statically calls `stored_claims`, `verdict_records`
- [[Reference/Modules/learnloop/workbench/route_example|learnloop.workbench.route_example]] — imports `has_verdict_record`, `verdict_records`; statically calls `has_verdict_record`, `verdict_records`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench_help|learnloop_sidecar.handlers.workbench_help]] — imports `hint_result_view`, `switch`; statically calls `hint_result_view`, `switch`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/config/loader|learnloop.config.loader]] — imports `load_config`; calls `load_config`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/split/context|learnloop.diagnosis.split.context]], [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]], [[Reference/Modules/learnloop/diagnosis/split/live|learnloop.diagnosis.split.live]], [[Reference/Modules/learnloop/diagnosis/split/prior_analysis|learnloop.diagnosis.split.prior_analysis]], [[Reference/Modules/learnloop/diagnosis/split/workbench_trace|learnloop.diagnosis.split.workbench_trace]] and 7 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reader_rw2b_fix14.py](../../../../../tests/test_reader_rw2b_fix14.py) — direct import
  - `test_item3_the_trace_is_regated_by_the_accessor`

## Modification guidance

- Make changes here when the responsibility remains symbolic view within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/symbolic_view.py](../../../../../src/learnloop/symbolic_view.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
