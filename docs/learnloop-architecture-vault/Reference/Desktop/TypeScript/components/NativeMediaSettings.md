---
title: "Desktop module · src/components/NativeMediaSettings.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.NativeMediaSettings"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/NativeMediaSettings.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/NativeMediaSettings.tsx"
source_commit: "df36567be6701733d162bffc27ac2a72c43d872a"
source_commit_timestamp: "2026-09-03T10:49:58-07:00"
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

# `src/components/NativeMediaSettings.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `NativeMediaSettings` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/NativeMediaSettings.tsx](../../../../../../apps/learnloop-tauri/src/components/NativeMediaSettings.tsx) |
| Source lines | 323 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `df36567be6701733d162bffc27ac2a72c43d872a` |
| Commit timestamp | `2026-09-03T10:49:58-07:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/SettingsScreen|src/screens/SettingsScreen.tsx]] → [[Reference/Desktop/TypeScript/components/NativeMediaSettings|src/components/NativeMediaSettings.tsx]]

## Public API

- `export interface SettingsStyles` — interface, line 33
- `export function NativeMediaSettings(` — function, line 66

## Internal implementation anchors

- `const PDF_ENGINE_OPTIONS: Array<` — const, line 19
- `const AUDIO_MODE_OPTIONS: Array<` — const, line 26
- `const CHAT_PROVIDER_TYPES = new Set(["openai_chat", "openrouter"])` — const, line 31
- `function ReadinessLine(` — function, line 40
- `function ModalityChips(` — function, line 51
- `const on = modalities.includes(modality)` — const, line 55
- `const native = settings.ingest.native` — const, line 83
- `const pdfState = native.modalities.find((entry)` — const, line 84
- `const audioState = native.modalities.find((entry)` — const, line 85
- `const inflightRef = useRef<Set<string>>(new Set())` — const, line 89
- `const saveIngest = (input: Parameters<typeof api.updateIngestSettings>[0], toast: string)` — const, line 91
- `const detect = (provider: string, refresh: boolean,` — const, line 103
- `const applyModalities = (provider: string, inputModalities: string[])` — const, line 119
- `const routed = [pdfState, audioState].filter( (state): state is NativeModalityStateDto` — const, line 137
- `const providers = Array.from(new Set(routed.map((state)` — const, line 145
- `const chatProviders: SettingsProviderDto[] = settings.ai.providers.filter((provider)` — const, line 152
- `const detectButton = (provider: string)` — const, line 156
- `const detection = detections[provider.name]` — const, line 251
- `const detectionCurrent = detection != null && detection.model === provider.model` — const, line 254
- `const detectedDiffers = detectionCurrent && detection.detected != null && (detection.detected.length !== provider.inputModalities.length || detection.detected.some((m)` — const, line 255

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/SettingsScreen|src/screens/SettingsScreen.tsx]] — import-or-re-export: `NativeMediaSettings`; references `NativeMediaSettings`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AudioMode`, `NativeModalityStateDto`, `PdfEngine`, `ProviderCapabilitiesDto`, `SettingsDto`, `SettingsProviderDto`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `TermCheckbox`, `TermSelect`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Configure AI Providers|Configure AI Providers]] — owns provider setup.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [tests/test_maintenance_feed.py](../../../../../../tests/test_maintenance_feed.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_doctor.py](../../../../../../tests/test_doctor.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_desktop_rpc_contract.py](../../../../../../tests/test_desktop_rpc_contract.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/NativeMediaSettings.tsx](../../../../../../apps/learnloop-tauri/src/components/NativeMediaSettings.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
