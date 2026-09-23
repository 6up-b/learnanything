---
title: "Desktop module · src/screens/reader/useReaderRequests.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.useReaderRequests"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/useReaderRequests.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/useReaderRequests.ts"
source_commit: "33c7456b0f78caa01172f6170de7727f002513c3"
source_commit_timestamp: "2026-09-23T12:06:06-04:00"
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

# `src/screens/reader/useReaderRequests.ts`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `BackgroundRequest`, `SynthesizedObject`, `useReaderRequests`, `parseRequestResult` and related exports within the desktop's TypeScript/screens/reader ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/useReaderRequests.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/useReaderRequests.ts) |
| Source lines | 212 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `33c7456b0f78caa01172f6170de7727f002513c3` |
| Commit timestamp | `2026-09-23T12:06:06-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/useReaderRequests|src/screens/reader/useReaderRequests.ts]]

## Public API

- `export interface BackgroundRequest` — interface, line 5
- `export interface SynthesizedObject` — interface, line 14
- `export function useReaderRequests(sourceId: string | null, enabled: boolean)` — function, line 64
- `export function parseRequestResult( resultJson: string | null | undefined ):` — function, line 183
- `export function parseRequestError(errorJson: string | null | undefined): string | null` — function, line 200

## Internal implementation anchors

- `const ACTIVE_REQUEST_STATUSES = new Set(["queued", "running", "pending"])` — const, line 23
- `function hasActiveRequest(requests: BackgroundRequest[]): boolean` — function, line 25
- `function flattenSourceObjects(heads: Array<Record<string, unknown>>): Map<string, SynthesizedObject>` — function, line 29
- `const flattened = new Map<string, SynthesizedObject>()` — const, line 30
- `const object = (head.object as Record<string, unknown>) ??` — const, line 32
- `const version = (head.version as Record<string, unknown>) ??` — const, line 33
- `const citations = (head.citations as Array<Record<string, unknown>>) ?? []` — const, line 34
- `let contentMd = ""` — let, line 35
- `const content = JSON.parse(String(version.contentJson ?? "")) as` — const, line 37
- `const objectId = String(object.id ?? "")` — const, line 42
- `const activeSourceId = enabled ? sourceId : null` — const, line 65
- `const activeScope = useMemo(()` — const, line 66
- `const activeScopeRef = useRef<typeof activeScope | null>(activeScope)` — const, line 69
- `const observedRequests = useRef(new Map<string, string>())` — const, line 81
- `const loadArtifacts = useCallback(async (targetScope:` — const, line 83
- `const targetSourceId = targetScope.sourceId` — const, line 84
- `const proposals = (inbox.proposals as Array<Record<string, unknown>>) ?? []` — const, line 91
- `const refresh = useCallback(async ()` — const, line 99
- `const targetScope = activeScope` — const, line 101
- `const failures: string[] = []` — const, line 107
- `const polling = useMemo(()` — const, line 129
- `const targetScope = activeScope` — const, line 132
- `const targetSourceId = activeSourceId` — const, line 133
- `let cancelled = false` — let, line 134
- `let timer: number | undefined` — let, line 135
- `const poll = async ()` — const, line 137
- `let pollAgain = true` — let, line 138
- `const snapshot = await api.readerSourceRequests(targetSourceId)` — const, line 140
- `const next = (snapshot.requests as BackgroundRequest[]) ?? []` — const, line 142
- `const signatures = new Map(next.map((request)` — const, line 144
- `const newlyTerminal = next.some((request)` — const, line 147
- `const parsed = JSON.parse(resultJson ?? "") as` — const, line 188
- `const objectRow = (parsed.proposals ?? []).find((proposal)` — const, line 189
- `const mappingRow = (parsed.proposals ?? []).find((proposal)` — const, line 190
- `const parsed = JSON.parse(errorJson ?? "") as` — const, line 202
- `const message = typeof parsed.message === "string" ? parsed.message.trim() : ""` — const, line 203

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `parseRequestError`, `parseRequestResult`, `useReaderRequests`; references `parseRequestError`, `parseRequestResult`, `useReaderRequests`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/useReaderRequests.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/useReaderRequests.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_sidecar_reader.py](../../../../../../../tests/test_sidecar_reader.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_reader_pdf_view.py](../../../../../../../tests/test_sidecar_reader_pdf_view.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_render_views.py](../../../../../../../tests/test_reader_render_views.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_requests.py](../../../../../../../tests/test_reader_requests.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/reader/useReaderRequests.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/useReaderRequests.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
