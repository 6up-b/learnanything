---
title: "learnloop_sidecar.request_origin"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/request_origin.py"
source_paths:
  - "src/learnloop_sidecar/request_origin.py"
source_commit: "workspace/uncommitted @ HEAD 8d1e02e12e427b95bf7957b96682fa15110bf543"
source_commit_timestamp: "2026-11-07T05:54:41-05:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop_sidecar.request_origin module"
  - "src/learnloop_sidecar/request_origin.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar"
---

# `learnloop_sidecar.request_origin`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.request_origin` exists within [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] to own the behavior summarized by its module contract: Mobile PR-5 (``spec_mobile_tailnet_v1`` §6.8, T8): who a request comes from.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/request_origin.py](../../../../../src/learnloop_sidecar/request_origin.py) |
| Source lines | 157 |
| Owning package | [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 8d1e02e12e427b95bf7957b96682fa15110bf543` |
| Commit timestamp | `2026-11-07T05:54:41-05:00` |

## Public API

- `class RequestOrigin` ([source](../../../../../src/learnloop_sidecar/request_origin.py), line 41) — One authenticated caller: the paired device and the surface it runs.
  - `__post_init__(self) -> None` (line 54; internal)
- `device_class(origin: RequestOrigin | None) -> str` ([source](../../../../../src/learnloop_sidecar/request_origin.py), line 61) — The class the eligibility module asks about (§6.4); None is the desktop.
- `phone_probes_on(origin: RequestOrigin | None, config: Any) -> bool` ([source](../../../../../src/learnloop_sidecar/request_origin.py), line 67) — Mobile v2 V3 (owner decision D3): a phone origin serves and answers phone-eligible probes, diagnostic and FG1's generated ones, under the probe contract.
- `practice_surface(origin: RequestOrigin | None) -> str` ([source](../../../../../src/learnloop_sidecar/request_origin.py), line 81) — ``entry_surface`` of an attempt and of a submission's binding.
- `offer_surface(origin: RequestOrigin | None) -> str` ([source](../../../../../src/learnloop_sidecar/request_origin.py), line 87) — ``entry_surface`` of a published scheduler offer.
- `plan_surface(origin: RequestOrigin) -> str` ([source](../../../../../src/learnloop_sidecar/request_origin.py), line 93) — Mobile v2 §2.2: the surface a phone's plan step and its boundary decisions record.
- `bump_for_host(ctx: Any) -> None` ([source](../../../../../src/learnloop_sidecar/request_origin.py), line 108) — Tell the desktop a host request changed what it shows (PR-7, §3.3).
- `host_mutation(handler: Callable[[Any, Any], Any]) -> Callable[[Any, Any], Any]` ([source](../../../../../src/learnloop_sidecar/request_origin.py), line 135) — A handler whose committed work changes what the desktop shows (PR-7, §3.3).

### Module constants

- `DESKTOP_PRACTICE` ([src/learnloop_sidecar/request_origin.py](../../../../../src/learnloop_sidecar/request_origin.py), line 33)
- `DESKTOP_QUEUE` ([src/learnloop_sidecar/request_origin.py](../../../../../src/learnloop_sidecar/request_origin.py), line 34)
- `PHONE_PRACTICE` ([src/learnloop_sidecar/request_origin.py](../../../../../src/learnloop_sidecar/request_origin.py), line 36)
- `PHONE_QUEUE` ([src/learnloop_sidecar/request_origin.py](../../../../../src/learnloop_sidecar/request_origin.py), line 37)
- `_COMMITTED_REFUSALS` ([src/learnloop_sidecar/request_origin.py](../../../../../src/learnloop_sidecar/request_origin.py), line 105)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `RequestOrigin`, `bump_for_host`; statically calls `bump_for_host`
- [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]] — imports `host_mutation`, `phone_probes_on`, `plan_surface`; statically calls `phone_probes_on`, `plan_surface`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `host_mutation`, `phone_probes_on`; statically calls `phone_probes_on`
- [[Reference/Modules/learnloop_sidecar/handlers/followup|learnloop_sidecar.handlers.followup]] — imports `host_mutation`, `phone_probes_on`; statically calls `phone_probes_on`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `DESKTOP_PRACTICE`, `PHONE_PRACTICE`, `host_mutation`, `phone_probes_on`, `practice_surface`; statically calls `phone_probes_on`, `practice_surface`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `offer_surface`, `phone_probes_on`; statically calls `offer_surface`, `phone_probes_on`
- [[Reference/Modules/learnloop_sidecar/handlers/sessions|learnloop_sidecar.handlers.sessions]] — imports `host_mutation`
- [[Reference/Modules/learnloop_sidecar/serving|learnloop_sidecar.serving]] — imports `RequestOrigin`, `device_class`, `phone_probes_on`; statically calls `device_class`, `phone_probes_on`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `PHONE_PROBES_VERSIONS`
- [[Reference/Modules/learnloop/scheduling/device_eligibility|learnloop.scheduling.device_eligibility]] — imports `DESKTOP`, `PHONE`, `PHONE_PLAN`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `functools`, `logging`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]], [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]], [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]], [[Reference/Modules/learnloop_sidecar/handlers/followup|learnloop_sidecar.handlers.followup]], [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] and 3 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_device_eligibility.py](../../../../../tests/test_device_eligibility.py) — direct import
- [tests/test_followup_journey.py](../../../../../tests/test_followup_journey.py) — direct import
  - `test_a_reserved_probe_refuses_every_door_until_its_workflow_is_ready`
- [tests/test_host_queue_revision.py](../../../../../tests/test_host_queue_revision.py) — direct import
  - `test_a_committed_refusal_bumps_and_any_other_refusal_does_not`
  - `test_bump_for_host_is_the_desktops_no_op`
  - `test_two_vaults_owe_separately_and_a_failed_retry_stays_owed`
- [tests/test_mobile_v2_followup.py](../../../../../tests/test_mobile_v2_followup.py) — direct import
- [tests/test_mobile_v2_review_fixes.py](../../../../../tests/test_mobile_v2_review_fixes.py) — direct import
  - `test_f6_the_check_is_a_phone_origins_too`
- [tests/test_mobile_v3_codex_review.py](../../../../../tests/test_mobile_v3_codex_review.py) — direct import
  - `test_f2_the_desktops_next_keeps_a_phone_probe_whose_answer_is_being_graded`
- [tests/test_mobile_v3_probes.py](../../../../../tests/test_mobile_v3_probes.py) — direct import
- [tests/test_mobile_v3_successor.py](../../../../../tests/test_mobile_v3_successor.py) — direct import
  - `test_the_gate_is_the_switch_and_the_tag_and_never_the_desktop`
  - `test_the_switch_is_the_hosts_and_defaults_on`
- [tests/test_request_origin.py](../../../../../tests/test_request_origin.py) — direct import
  - `test_an_origin_names_a_device_and_a_known_surface`
  - `test_another_paired_device_is_refused_on_the_phones_session`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/request_origin.py](../../../../../src/learnloop_sidecar/request_origin.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
