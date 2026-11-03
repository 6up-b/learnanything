---
title: "learnloop.scheduling.device_eligibility"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/device_eligibility.py"
source_paths:
  - "src/learnloop/scheduling/device_eligibility.py"
source_commit: "d80ce2fc8a244552f530bf803ee1b7cc82e44ea9"
source_commit_timestamp: "2026-11-03T01:44:06-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.scheduling"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.scheduling.device_eligibility module"
  - "src/learnloop/scheduling/device_eligibility.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling"
---

# `learnloop.scheduling.device_eligibility`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.device_eligibility` exists within [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] to own the behavior summarized by its module contract: Mobile PR-6: which items a device can answer (``spec_mobile_tailnet_v1`` §6.4).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py) |
| Source lines | 125 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `d80ce2fc8a244552f530bf803ee1b7cc82e44ea9` |
| Commit timestamp | `2026-11-03T01:44:06-05:00` |

## Public API

- `ineligibility_reason(vault: Any, item: Any, device_class: str) -> str | None` ([source](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 101) — Why ``device_class`` cannot answer ``item``, or None when it can.

### Module constants

- `DESKTOP` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 37)
- `PHONE` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 38)
- `DESKTOP_ONLY_MODES` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 42)
- `_TEACH_BACK_MODE` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 44)
- `ERROR_HUNT` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 46)
- `LADDERED_STEM` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 47)
- `MULTI_TURN_TEACH_BACK` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 48)
- `DESKTOP_ONLY_MODE` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 49)
- `LESSON_CHECK` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 50)
- `EMBEDS_IMAGE` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 51)
- `LINKS_LLPDF` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 52)
- `REFERENCES_ITEM_ASSET` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 53)
- `_LITERAL_TEXT` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 57)
- `_MARKDOWN_IMAGE` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 66)
- `_HTML_IMAGE` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 67)
- `_MARKDOWN_LINK` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 68)
- `_URL_SCHEME` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 69)
- `_LOCAL_SCHEMES` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 71)
- `_FILE_SUFFIX` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 72)

## Internal implementation anchors

- `_references_item_asset(text: str) -> bool` ([source](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 75) — A Markdown link to a file: a local scheme, or a relative target that is a path.
- `_prompt_reason(prompt: str) -> str | None` ([source](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 90)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/request_origin|learnloop_sidecar.request_origin]] — imports `DESKTOP`, `PHONE`
- [[Reference/Modules/learnloop_sidecar/serving|learnloop_sidecar.serving]] — imports `ineligibility_reason`; statically calls `ineligibility_reason`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/vault/lifecycle|learnloop.vault.lifecycle]] — imports `minted_for_lesson`; calls `minted_for_lesson`

### Platform and third-party dependencies

- Standard library: `__future__`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/request_origin|learnloop_sidecar.request_origin]], [[Reference/Modules/learnloop_sidecar/serving|learnloop_sidecar.serving]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_device_eligibility.py](../../../../../../tests/test_device_eligibility.py) — direct import
  - `test_a_by_id_door_refuses_what_the_phone_cannot_answer`
  - `test_a_lessons_own_held_check_stays_in_its_lesson`
  - `test_a_prompt_that_needs_more_than_text_is_kept_for_the_desktop`
  - `test_a_teach_back_source_on_any_mode_is_the_multi_turn_reason`
  - `test_each_contract_reason_is_returned_for_the_phone_and_never_for_the_desktop`
  - `test_item_kinds_landed_since_the_spec_keep_the_ordinary_answer`
  - `test_plain_text_mathematics_and_text_cues_stay_eligible`

## Modification guidance

- Change device eligibility policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
