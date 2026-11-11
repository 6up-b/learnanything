---
title: "learnloop_sidecar.serving"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/serving.py"
source_paths:
  - "src/learnloop_sidecar/serving.py"
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
  - "learnloop_sidecar.serving module"
  - "src/learnloop_sidecar/serving.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar"
---

# `learnloop_sidecar.serving`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.serving` exists within [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] to own the behavior summarized by its module contract: Sidecar refusal for serving an item of a put-away Learning Object.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/serving.py](../../../../../src/learnloop_sidecar/serving.py) |
| Source lines | 266 |
| Owning package | [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `device_policy(vault: Any, origin: RequestOrigin | None=None) -> str` ([source](../../../../../src/learnloop_sidecar/serving.py), line 62) — The rules a phone request is served under, for the router's inputs: a new rule set is a new name, so a phone whose host has its Reader on (mobile v2 §2.3, V4) names ``device_eligibility_v2``.
- `origin_ineligibility(origin: RequestOrigin | None, vault: Any, item: Any) -> str | None` ([source](../../../../../src/learnloop_sidecar/serving.py), line 71) — Why the request's device cannot answer ``item``; never asked for the desktop.
- `device_filter(origin: RequestOrigin | None, vault: Any, repository: Any=None, session_id: str | None=None) -> DeviceFilter | None` ([source](../../../../../src/learnloop_sidecar/serving.py), line 91) — What a queue build holds back for the request's device (§6.4, D6).
- `refuse_device_ineligible_item(origin: RequestOrigin | None, vault: Any, item: Any) -> None` ([source](../../../../../src/learnloop_sidecar/serving.py), line 113) — A by-id door (§6.4): a stale list, a deep link or a restored session cannot bring the phone an item it cannot show.
- `refuse_inactive_learning_object(vault: LoadedVault, learning_object_id: str | None) -> None` ([source](../../../../../src/learnloop_sidecar/serving.py), line 126)
- `refuse_generated_probe_door(ctx_origin: RequestOrigin | None, repository: Any, item: PracticeItem, *, serve: bool, phone_probes: bool=False, owned: Callable[[], None] | None=None) -> None` ([source](../../../../../src/learnloop_sidecar/serving.py), line 148) — FG1 §4.2: every serve door for a generated probe, before its text leaves.
- `refuse_unservable_item(vault: LoadedVault, item: PracticeItem) -> None` ([source](../../../../../src/learnloop_sidecar/serving.py), line 242) — The item-level door: its LO's refusal, then the adoption kill switch.
- `refuse_held_out_item(vault: LoadedVault, repository: Any, item: PracticeItem) -> None` ([source](../../../../../src/learnloop_sidecar/serving.py), line 256) — A session serve of an item made from held-out material is refused.

### Module constants

- `DESKTOP_ONLY_ERROR_CODE` ([src/learnloop_sidecar/serving.py](../../../../../src/learnloop_sidecar/serving.py), line 53)
- `INACTIVE_LEARNING_OBJECT_ERROR_CODE` ([src/learnloop_sidecar/serving.py](../../../../../src/learnloop_sidecar/serving.py), line 54)
- `HELD_OUT_MATERIAL_ERROR_CODE` ([src/learnloop_sidecar/serving.py](../../../../../src/learnloop_sidecar/serving.py), line 55)

## Internal implementation anchors

- `_device_rules_on(vault: Any) -> bool` ([source](../../../../../src/learnloop_sidecar/serving.py), line 58)
- `_media_served(origin: RequestOrigin | None, vault: Any, repository: Any=None) -> Any` ([source](../../../../../src/learnloop_sidecar/serving.py), line 80) — Mobile v2 V4 (Codex review F10): the host's own page and asset predicate, which the phone's media lift asks, so an item is admitted only with a stimulus the host then serves.
- `_claim_refusal(repository: Any, practice_item_id: str, row: Any, *, surface: str, owned: Callable[[], None] | None=None) -> str | None` ([source](../../../../../src/learnloop_sidecar/serving.py), line 215) — The atomic claim, against the presentation actually open for this item, not the id a caller or a workflow row remembers (it may have ended, and an absent one is no wildcard).
- `_claim(repository: Any, practice_item_id: str, row: Any, *, surface: str) -> str | None` ([source](../../../../../src/learnloop_sidecar/serving.py), line 230)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]] — imports `DESKTOP_ONLY_ERROR_CODE`, `device_filter`, `device_policy`; statically calls `device_filter`, `device_policy`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `device_filter`, `refuse_device_ineligible_item`, `refuse_generated_probe_door`, `refuse_held_out_item`, `refuse_inactive_learning_object`, `refuse_unservable_item`; statically calls `device_filter`, `refuse_device_ineligible_item`, `refuse_generated_probe_door`, `refuse_held_out_item`, `refuse_inactive_learning_object`, `refuse_unservable_item`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `device_filter`, `device_policy`, `origin_ineligibility`, `refuse_device_ineligible_item`, `refuse_generated_probe_door`, `refuse_held_out_item`, `refuse_unservable_item`; statically calls `device_filter`, `device_policy`, `origin_ineligibility`, `refuse_device_ineligible_item`, `refuse_generated_probe_door`, `refuse_held_out_item`, `refuse_unservable_item`
- [[Reference/Modules/learnloop_sidecar/handlers/sessions|learnloop_sidecar.handlers.sessions]] — imports `origin_ineligibility`; statically calls `origin_ineligibility`
- [[Reference/Modules/learnloop_sidecar/handlers/teach_back|learnloop_sidecar.handlers.teach_back]] — imports `refuse_held_out_item`, `refuse_unservable_item`; statically calls `refuse_held_out_item`, `refuse_unservable_item`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `HELD_OUT_ITEM_REFUSAL`, `held_out_item_ids`, `held_out_material`, `held_out_selection_active`; calls `held_out_item_ids`, `held_out_material`, `held_out_selection_active`
- [[Reference/Modules/learnloop/followup_serve/gates|learnloop.followup_serve.gates]] — imports `PHONE_SURFACE`, `SERVING_SURFACE`
- [[Reference/Modules/learnloop/followup_serve/identity|learnloop.followup_serve.identity]] — imports `module`; calls `claim_serve`, `closed_probe_ids`, `door_refusal`, `is_generated_probe`
- [[Reference/Modules/learnloop/followup_serve/workflow|learnloop.followup_serve.workflow]] — imports `module`; calls `retire_waiting`, `waiting_still_valid`, `workflow_of_item`
- [[Reference/Modules/learnloop/reader/phone_media|learnloop.reader.phone_media]] — imports `media_predicate`; calls `media_predicate`
- [[Reference/Modules/learnloop/scheduling/device_eligibility|learnloop.scheduling.device_eligibility]] — imports `DEVICE_POLICY`, `DEVICE_POLICY_MEDIA`, `DEVICE_POLICY_OFF`, `DeviceFilter`, `ineligibility_reason`; calls `DeviceFilter`, `ineligibility_reason`
- [[Reference/Modules/learnloop/vault/lifecycle|learnloop.vault.lifecycle]] — imports `LEARNER_TEXT_GAP_DISABLED`, `REFERENCE_ADOPTION_DISABLED`, `learning_object_serving_block`, `practice_item_serving_block`; calls `learning_object_serving_block`, `practice_item_serving_block`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/request_origin|learnloop_sidecar.request_origin]] — imports `RequestOrigin`, `device_class`, `phone_probes_on`, `phone_reader_on`; calls `device_class`, `phone_probes_on`, `phone_reader_on`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]], [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]], [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]], [[Reference/Modules/learnloop_sidecar/handlers/sessions|learnloop_sidecar.handlers.sessions]], [[Reference/Modules/learnloop_sidecar/handlers/teach_back|learnloop_sidecar.handlers.teach_back]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_mobile_v3_codex_review.py](../../../../../tests/test_mobile_v3_codex_review.py) — direct import
- [tests/test_mobile_v4_codex_review.py](../../../../../tests/test_mobile_v4_codex_review.py) — direct import
  - `test_f10_a_page_is_phone_eligible_exactly_when_the_page_endpoint_serves_it`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/serving.py](../../../../../src/learnloop_sidecar/serving.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
