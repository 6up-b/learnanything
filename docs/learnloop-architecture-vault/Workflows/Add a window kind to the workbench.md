---
title: Add a window kind to the workbench
status: active
doc_version: 1.0.0
implementation_version: mvp-0.68
last_reviewed: 2026-11-23
source_commit: 9038b096e7446d5f433f95d881de7e7c1bd0da15
source_commit_timestamp: "2026-11-23T19:57:34-05:00"
source_paths:
  - src/learnloop/desks/content_ref.py
  - src/learnloop/desks/workspace.py
  - apps/learnloop-tauri/src/screens/desks
  - apps/learnloop-tauri/src/fixtures/desks/opParity.json
  - tests/test_reader_rd1_model_parity.py
  - tests/test_desktop_rpc_contract.py
  - tests/test_mobile_allowlist.py
  - docs/learnloop-architecture-vault/_scripts/desktop_validate.py
  - scripts/desk_harness/visual_reference.py
tags:
  - learnloop/workflow
  - learnloop/reader
---

# Add a window kind to the workbench

1. Define the persisted reference in `src/learnloop/desks/content_ref.py` and mirror it in `apps/learnloop-tauri/src/api/dto.ts`. Decide which fields identify the content and which are a target or a view. Check the open, reopen and state paths in `src/learnloop/desks/workspace.py`. Handle the reference in `screens/desks/model/workspace.ts`, including `contentKey`, so opening beside can find the same content again. The shared `src/fixtures/desks/opParity.json` script is run by `tests/test_reader_rd1_model_parity.py` and `src/fixtures/desks/opParity.test.ts`. Add a case for the new kind, including any op change. Once represented in the fixture, an unsupported op, different result or different slot, focus or version fails parity. The script compares layout and statuses. Add a round-trip check of the ref itself in the model or RPC tests.
2. If a new read or write needs an RPC, register it in `src/learnloop_sidecar/handlers/` and load the module from `handlers/__init__.py`. Add the Rust command in `apps/learnloop-tauri/src-tauri/src/commands.rs`, register it in `main.rs`, then add the client call and DTO in `src/api/client.ts` and `dto.ts`. `tests/test_desktop_rpc_contract.py` detects a missing command, invoke registration, sidecar method or handler load. Include desktop-only methods in the applicable RPC inventory and desktop-only matrix in `tests/test_mobile_allowlist.py`. Its pin checks the listed methods against the handler module and asserts they are denied to the phone. A verb or kind built entirely on existing methods needs no new entry at those layers.
3. Wire the opening path, title and body in `screens/desks/DeskShell.tsx` and the window component under `screens/desks/`. Check the shelf and overview miniature if they show kind-specific content. Register listeners through the window hub and gate work on its lifecycle. Use a stable window id across focus, pairing and reorder. A preview must never start work or log a visit. Use `DeskShell.test.tsx`, `windows/SourceWindow.lifecycle.test.tsx` and the new window's component test to exercise mounting, activation, pause and restoration. A new read with titles, snippets or explanations follows [[Workbench protection#Adding a text-bearing reply]].
4. Put a public-safe case under `apps/learnloop-tauri/src/fixtures/desks/`, give `fakeCore.ts` the real reply shape, and add or extend the runner in `scripts/desk_harness/run.py` and the stage and regions in `scripts/desk_harness/visual_reference.py`. For a lesson or video window, see the `rd9` and `rd10` stages. Run the relevant stage at both viewports with the reference supplied to the runner. It reports missing regions, unreachable states and measured differences, so check the states and findings as well as the exit. See the [visual reference record](../../reviews/reader-visual-reference.md).
5. Classify new desktop modules in the vault's `_scripts/desktop_generate.py` and review the inventory, entry-reachable, test-support and ACTIVE counts in `_scripts/desktop_validate.py`. A new inventoried file or different activation classification trips the count gates. The validator also checks catalog coverage and reproducibility. Those checks belong with the source change and its reference refresh.

See [[Reader workbench]], [[Add a menu verb]] for an opening action, and [[Debug a workbench write]] for a window that failed to persist.
