---
title: "learnloop.capture"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/capture/__init__.py"
source_paths:
  - "src/learnloop/capture/__init__.py"
source_commit: "fd203b85eab9c4a925589c804f6300d11c7dd1ed"
source_commit_timestamp: "2026-10-25T16:07:25-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.capture"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
aliases:
  - "learnloop.capture module"
  - "src/learnloop/capture/__init__.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-capture"
---

# `learnloop.capture`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/capture/_package|learnloop.capture]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.capture` exists within [[Reference/Modules/learnloop/capture/_package|learnloop.capture]] to own the behavior summarized by its module contract: Shared M1 capture domain.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/capture/__init__.py](../../../../../../src/learnloop/capture/__init__.py) |
| Source lines | 35 |
| Owning package | [[Reference/Modules/learnloop/capture/_package|learnloop.capture]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `fd203b85eab9c4a925589c804f6300d11c7dd1ed` |
| Commit timestamp | `2026-10-25T16:07:25-04:00` |

## Public API

No public top-level function or class definition is declared in this file.

### Explicit exports

`__all__` declares:

- `CaptureError`
- `authenticate_device`
- `create_pairing`
- `exchange_pairing`
- `list_devices`
- `revoke_device`
- `touch_device`
- `capture_media_preview`
- `create_capture`
- `dismiss_capture`
- `get_capture`
- `get_inbox_summary`
- `list_captures`
- `photo_for_practice_item`
- `purge_capture`
- `report_orphan_originals`
- `route_capture`
- `sanitize_image`
- `validate_url`
- `log_request`
- `pinned_vault_info`
- `prune_request_log`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/inbox|learnloop.cli.inbox]] — imports `list_captures`; statically calls `list_captures`
- [[Reference/Modules/learnloop_sidecar/handlers/as_printed|learnloop_sidecar.handlers.as_printed]] — imports `photo_for_practice_item`; statically calls `photo_for_practice_item`
- [[Reference/Modules/learnloop_sidecar/handlers/capture|learnloop_sidecar.handlers.capture]] — imports `module`; statically calls `pinned_vault_info`
- [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]] — imports `get_capture`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/capture/devices|learnloop.capture.devices]] — imports `authenticate_device`, `create_pairing`, `exchange_pairing`, `list_devices`, `revoke_device`, `touch_device`
- [[Reference/Modules/learnloop/capture/errors|learnloop.capture.errors]] — imports `CaptureError`
- [[Reference/Modules/learnloop/capture/inbox|learnloop.capture.inbox]] — imports `capture_media_preview`, `create_capture`, `dismiss_capture`, `get_capture`, `get_inbox_summary`, `list_captures`, `photo_for_practice_item`, `purge_capture`, `report_orphan_originals`, `route_capture`, `sanitize_image`, `validate_url`
- [[Reference/Modules/learnloop/capture/maintenance|learnloop.capture.maintenance]] — imports `log_request`, `pinned_vault_info`, `prune_request_log`

### Platform and third-party dependencies

- Standard library: none imported directly
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/inbox|learnloop.cli.inbox]], [[Reference/Modules/learnloop_sidecar/handlers/as_printed|learnloop_sidecar.handlers.as_printed]], [[Reference/Modules/learnloop_sidecar/handlers/capture|learnloop_sidecar.handlers.capture]], [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_capture_desktop.py](../../../../../../tests/test_capture_desktop.py) — direct import
  - `test_card_route_after_success_only`
  - `test_desktop_photo_preview_rpc_reads_only_the_capture_original`
  - `test_image_capture_kind_matches_desktop_dto`
  - `test_quick_add_route_after_durable_enqueue_only`
  - `test_summary_listing_banner_dismiss_purge_and_cli`
  - `test_tutor_route_after_answer_only_and_reference_anchor`
- [tests/test_capture_domain.py](../../../../../../tests/test_capture_domain.py) — direct import
  - `test_capture_concurrent_idempotency`
  - `test_global_idempotency_and_reference_only`
  - `test_image_sanitization_and_raw_fingerprint`
  - `test_inbox_route_atomic_failure_and_orphan_reporting`
  - `test_interrupted_purge_keeps_durable_deletion_intent`
  - `test_old_handled_capture_is_reachable_past_100_newer_and_tombstones`
  - `test_photo_preview_is_resolved_from_the_stored_hash_only`
  - `test_photo_preview_refuses_tampered_hashes_missing_files_and_purge`
  - `test_purge_file_failure_is_visible_and_retryable`
  - `test_purge_retains_canonical_source_original`
  - `test_purge_shared_original_and_retry_never_resurrects`
  - `test_reject_local_or_invalid_urls`
  - `test_routes_dismiss_and_readonly_status`
  - `test_unsupported_and_decoded_image_limit`
  - `test_valid_reference_urls`
- [tests/test_capture_originals_race.py](../../../../../../tests/test_capture_originals_race.py) — direct import
  - `test_source_publication_and_capture_purge_share_writer_reservation`
- [tests/test_capture_route_recovery.py](../../../../../../tests/test_capture_route_recovery.py) — direct import
  - `test_crash_before_destination_accepts_new_inputs_after_restart`
  - `test_crash_before_destination_allows_choosing_another_route`
  - `test_destination_retry_recovers_one_result`
  - `test_incomplete_tutor_event_is_not_duplicated`
  - `test_preflight_failure_allows_corrected_input`
  - `test_purge_during_tutor_answer_does_not_restore_capture`
  - `test_purge_erases_the_persisted_request`
  - `test_reload_failure_is_truthful_and_retry_safe`
  - `test_replacement_tutor_request_moves_the_partial_note_to_its_subject`
  - `test_resume_finishes_an_unfinished_route_without_any_inputs`
- [tests/test_mobile_host_auth.py](../../../../../../tests/test_mobile_host_auth.py) — direct import
  - `test_desktop_only_and_main_rpcs_are_http_denied_for_every_phone_scope`
  - `test_pairing_is_identity_gated_static_and_one_use`
  - `test_rejected_requests_never_touch_devices_or_log`
  - `test_scope_revocation_status_and_no_cors`
  - `test_slow_capture_has_separate_bounded_lane`
  - `test_startup_and_shutdown_never_prune`
- [tests/test_mobile_host_coexistence.py](../../../../../../tests/test_mobile_host_coexistence.py) — direct import
  - `test_capture_host_coexists_without_primary_startup_work`
- [tests/test_mobile_pairing.py](../../../../../../tests/test_mobile_pairing.py) — direct import
  - `test_authentication_and_device_listing_are_read_only`
  - `test_exchange_failure_rolls_back_consumption`
  - `test_expiry_and_unclaimed_device_revocation`
  - `test_failed_attempt_limits_survive_reattach_and_time`
  - `test_log_redaction_and_pruning`
  - `test_pairing_concurrent_exchange_one_winner`
  - `test_pairing_hash_only_scopes_revoke`
- [tests/test_reader_ca1_as_printed.py](../../../../../../tests/test_reader_ca1_as_printed.py) — direct import
  - `test_a_card_written_from_a_photo_shows_the_photo_outside_a_check`
  - `test_a_purged_photo_is_not_offered`

## Modification guidance

- Change this file when intentionally adding or removing a package-level re-export; keep implementation logic in the owning module.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/capture/__init__.py](../../../../../../src/learnloop/capture/__init__.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
