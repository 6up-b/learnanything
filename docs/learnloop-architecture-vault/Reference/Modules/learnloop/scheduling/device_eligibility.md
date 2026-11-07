---
title: "learnloop.scheduling.device_eligibility"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/device_eligibility.py"
source_paths:
  - "src/learnloop/scheduling/device_eligibility.py"
source_commit: "cec9749e3a807f0bfb9f46f616e55ee766838077"
source_commit_timestamp: "2026-11-06T23:01:07-05:00"
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
| Source lines | 271 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `cec9749e3a807f0bfb9f46f616e55ee766838077` |
| Commit timestamp | `2026-11-06T23:01:07-05:00` |

## Public API

- `class DeviceFilter` ([source](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 152) — One queue build's device, and what it held back.
  - `refuses(self, item: Any) -> bool` (line 174; public)
  - `holds_back(self, item: Any) -> bool` (line 177; public) — ``refuses``, for an item the build would otherwise serve.
- `class PlanStepFilter` ([source](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 198) — Mobile v2 §2.2: the phone's door into the shared plan, which filters at the step.
  - `holds(self, item: Any) -> str | None` (line 226; public) — Why the device leaves ``item`` for the desktop, or None when it can serve it.
  - `detail(self) -> dict[str, str]` (line 237; public) — What a decision taken at a boundary under this device records (its ``device`` entry).
  - `held_count(self) -> int` (line 243; public)
- `ineligibility_reason(vault: Any, item: Any, device_class: str) -> str | None` ([source](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 247) — Why ``device_class`` cannot answer ``item``, or None when it can.

### Module constants

- `DESKTOP` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 44)
- `PHONE` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 45)
- `DESKTOP_ONLY_MODES` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 49)
- `_TEACH_BACK_MODE` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 51)
- `ERROR_HUNT` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 53)
- `LADDERED_STEM` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 54)
- `MULTI_TURN_TEACH_BACK` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 55)
- `DESKTOP_ONLY_MODE` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 56)
- `LESSON_CHECK` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 57)
- `EMBEDS_IMAGE` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 58)
- `LINKS_LLPDF` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 59)
- `REFERENCES_ITEM_ASSET` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 60)
- `DEVICE_POLICY` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 65)
- `DEVICE_POLICY_OFF` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 66)
- `_LITERAL_TEXT` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 71)
- `_FOOTNOTE_DEFINITION` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 84)
- `_FOOTNOTE_REFERENCE` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 85)
- `_HTML_IMAGE` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 86)
- `_LLPDF` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 87)
- `_URL_SCHEME` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 88)
- `_LOCAL_SCHEMES` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 90)
- `_FILE_SUFFIX` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 91)
- `_MARKDOWN` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 98)
- `READING_BEFORE_PHONE_READER` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 188)
- `GENERATED_PROBE` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 191)
- `PHONE_PLAN` ([src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 194)

## Internal implementation anchors

- `_is_item_asset(target: str) -> bool` ([source](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 102) — A link to a file: a local scheme, or a relative target that is a path.
- `_rendered_tokens(tokens: Iterable[Token]) -> Iterator[Token]` ([source](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 114)
- `_prompt_reason(prompt: str) -> str | None` ([source](../../../../../../src/learnloop/scheduling/device_eligibility.py), line 122) — Read per candidate on every phone build, and a prompt's parse never changes.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `DeviceFilter`
- [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]] — imports `GENERATED_PROBE`, `PlanStepFilter`; statically calls `PlanStepFilter`
- [[Reference/Modules/learnloop_sidecar/request_origin|learnloop_sidecar.request_origin]] — imports `DESKTOP`, `PHONE`, `PHONE_PLAN`
- [[Reference/Modules/learnloop_sidecar/serving|learnloop_sidecar.serving]] — imports `DEVICE_POLICY`, `DEVICE_POLICY_OFF`, `DeviceFilter`, `ineligibility_reason`; statically calls `DeviceFilter`, `ineligibility_reason`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/vault/lifecycle|learnloop.vault.lifecycle]] — imports `minted_for_lesson`; calls `minted_for_lesson`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `functools`, `re`, `typing`
- Third party: `markdown_it`

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]], [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]], [[Reference/Modules/learnloop_sidecar/request_origin|learnloop_sidecar.request_origin]], [[Reference/Modules/learnloop_sidecar/serving|learnloop_sidecar.serving]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_device_eligibility.py](../../../../../../tests/test_device_eligibility.py) — direct import
  - `test_a_by_id_door_refuses_what_the_phone_cannot_answer`
  - `test_a_lessons_own_held_check_stays_in_its_lesson`
  - `test_a_presentation_on_an_item_the_phone_cannot_show_survives_the_phone_queue`
  - `test_a_prompt_that_needs_more_than_text_is_kept_for_the_desktop`
  - `test_a_teach_back_source_on_any_mode_is_the_multi_turn_reason`
  - `test_an_escape_changes_only_the_delimiter_it_escapes`
  - `test_brackets_the_renderer_shows_as_text_stay_eligible`
  - `test_each_contract_reason_is_returned_for_the_phone_and_never_for_the_desktop`
  - `test_item_kinds_landed_since_the_spec_keep_the_ordinary_answer`
  - `test_plain_text_mathematics_and_text_cues_stay_eligible`
  - `test_reference_forms_resolve_as_the_renderer_resolves_them`
  - `test_the_phones_decision_names_the_rules_and_the_desktops_does_not`
  - `test_what_the_renderer_resolves_is_still_kept_for_the_desktop`
  - `test_what_the_renderer_shows_as_text_or_a_web_link_stays_eligible`
- [tests/test_mobile_handoff.py](../../../../../../tests/test_mobile_handoff.py) — direct import
  - `test_suspected_figure_is_a_word_pattern_and_only_a_report`
- [tests/test_mobile_v2_checks.py](../../../../../../tests/test_mobile_v2_checks.py) — direct import
  - `test_j6_a_check_the_phone_can_show_is_served_on_the_phone_as_an_ordinary_item`
- [tests/test_mobile_v2_rereview_fixes.py](../../../../../../tests/test_mobile_v2_rereview_fixes.py) — direct import
  - `test_f5_a_check_restored_from_its_checkpoint_the_next_day_stays_cold`
- [tests/test_mobile_v2_review_fixes.py](../../../../../../tests/test_mobile_v2_review_fixes.py) — direct import
  - `test_f5_the_open_randomized_check_is_named_cold_until_it_is_answered`
- [tests/test_te3b_offers.py](../../../../../../tests/test_te3b_offers.py) — direct import
  - `test_a_phone_step_holds_a_drawn_offer_for_the_desktop`

## Modification guidance

- Change device eligibility policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/device_eligibility.py](../../../../../../src/learnloop/scheduling/device_eligibility.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
