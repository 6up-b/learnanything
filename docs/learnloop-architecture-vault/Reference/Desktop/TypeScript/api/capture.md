---
title: "Desktop module · src/api/capture.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.api.capture"
language: "TypeScript"
area: "TypeScript/api"
source_path: "apps/learnloop-tauri/src/api/capture.ts"
source_paths:
  - "apps/learnloop-tauri/src/api/capture.ts"
source_commit: "51d81ec8ffabc6932dede98eff11a6b691ebcb97"
source_commit_timestamp: "2026-10-12T11:19:28-04:00"
source_worktree_state: "clean"
activation_kind: "entry-reachable build graph"
activation_evidence: "A static TypeScript import path reaches this file from the Vite entry src/main.tsx."
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/reference/module"
  - "learnloop/desktop"
  - "learnloop/desktop/typescript"
  - "refactor/active"
---

# `src/api/capture.ts`

Area: [[Reference/Desktop/TypeScript/api/_area|TypeScript/api]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `CaptureDto`, `InboxSummary`, `CaptureMediaDto` within the desktop's TypeScript/api ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/api/capture.ts](../../../../../../apps/learnloop-tauri/src/api/capture.ts) |
| Source lines | 38 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/api/_area|TypeScript/api]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `51d81ec8ffabc6932dede98eff11a6b691ebcb97` |
| Commit timestamp | `2026-10-12T11:19:28-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] → [[Reference/Desktop/TypeScript/api/capture|src/api/capture.ts]]

## Public API

- `export interface CaptureDto` — interface, line 1
- `export interface InboxSummary` — interface, line 17
- `export interface CaptureMediaDto` — interface, line 30

## Internal implementation anchors

No non-exported declaration anchor was detected by the static extractor.

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — dynamic import: dynamic import; no named call claim
- [[Reference/Desktop/TypeScript/components/CapturePhoto|src/components/CapturePhoto.tsx]] — import-or-re-export: `CaptureMediaDto`; references `CaptureMediaDto`
- [[Reference/Desktop/TypeScript/components/InboxStrip|src/components/InboxStrip.tsx]] — import-or-re-export: `CaptureDto`, `InboxSummary`; references `CaptureDto`, `InboxSummary`

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Architecture/Adapter Architecture#Sidecar structure|sidecar structure]] — owns the four-layer RPC contract.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/components/InboxStrip.test.tsx](../../../../../../apps/learnloop-tauri/src/components/InboxStrip.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Add or change an RPC in all four layers: DTO, client facade, Rust command/registration, and Python sidecar handler/registry.
- Preserve camelCase wire names and typed error behavior; exercise `tests/test_desktop_rpc_contract.py` plus the feature's sidecar tests.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/api/capture.ts](../../../../../../apps/learnloop-tauri/src/api/capture.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
