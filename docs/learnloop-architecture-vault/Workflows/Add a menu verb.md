---
title: Add a menu verb
status: active
doc_version: 1.0.0
implementation_version: mvp-0.68
last_reviewed: 2026-11-23
source_commit: 9038b096e7446d5f433f95d881de7e7c1bd0da15
source_commit_timestamp: "2026-11-23T19:57:34-05:00"
source_paths:
  - apps/learnloop-tauri/src/screens/desks/menu
  - apps/learnloop-tauri/src/screens/desks/DeskShell.tsx
  - apps/learnloop-tauri/src/screens/desks/pads/PadStackWindow.tsx
  - src/learnloop_sidecar/handlers/passage_union.py
  - src/learnloop/passage_union/promoted.py
  - tests/test_menu_protected_material.py
  - tests/test_menu_promoted_rows.py
  - scripts/desk_harness/visual_reference.py
tags:
  - learnloop/workflow
  - learnloop/reader
---

# Add a menu verb

1. Start in `apps/learnloop-tauri/src/screens/desks/menu/model.ts`. Add a fixed verb's id, key and applicable object kinds to the verb table. Keep the existing keys and ordering. A promoted row comes from `src/learnloop/passage_union/promoted.py` and the `passage.promoted` handler, where its identity, order and cap are decided. `menu/model.test.ts` checks the fixed lists and `tests/test_menu_promoted_rows.py` checks ranking, labels and the cheap-to-judged reply.
2. Wire the action in `menu/verbs.ts` and its host in `DeskShell.tsx` or `pads/PadStackWindow.tsx`. Reuse `menu/ContextMenu.tsx` and its object and window ownership. A verb that copies, quotes or sends words belongs in the quoting gate as well as in the verb list. Check the whole selection and any linked origins or targets at the action's destination. Give a submenu or shortcut the same protection as the main row. Use [[Workbench protection#Adding a text-bearing reply]] for server delivery. `menu/verbs.test.ts`, `menu/ContextMenu.test.tsx`, `DeskShell.menu.test.tsx`, `pads/PadStackWindow.test.tsx` and `tests/test_menu_protected_material.py` cover applicability, dispatch, old menu replies and protected input. Add the new verb to those cases so a skipped gate or missing handler fails.
3. Reuse the owning handler if its contract covers the action. For a new RPC, follow the sidecar, Rust and TypeScript bridge order in [[Add a window kind to the workbench]]. Update the desktop-only method pin and exercise the desktop RPC contract. If the action adds a persisted desk op, mirror it on both sides and extend `opParity.json`. The parity fixture covers desk ops, so an action with no layout write needs a dispatch or domain test instead. A long action uses [[ADR-022 Scope polled jobs to vault and epoch]] and registers its poll with the asking window.
4. Teach `src/fixtures/desks/fakeCore.ts` the new reply if necessary. Update the menus runner in `scripts/desk_harness/run.py` and the `rd5` states and regions in `visual_reference.py` where the row appears. Compare both viewports, including an applicable object and one that should omit the row. The visual stage measures what is rendered. The dispatch test proves the action runs. If the verb adds desktop files, apply the inventory and activation-count checks in [[Add a window kind to the workbench]].

See [[Reader workbench]] for where verbs, promoted rows and pad proposals meet.
