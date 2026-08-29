---
title: "Desktop module · src/render/MarkdownMath.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.render.MarkdownMath"
language: "TypeScript"
area: "TypeScript/render"
source_path: "apps/learnloop-tauri/src/render/MarkdownMath.tsx"
source_paths:
  - "apps/learnloop-tauri/src/render/MarkdownMath.tsx"
source_commit: "f0052f7260eb63224bd103193929a03fd54660d6"
source_commit_timestamp: "2026-07-21T15:03:22-04:00"
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

# `src/render/MarkdownMath.tsx`

Area: [[Reference/Desktop/TypeScript/render/_area|TypeScript/render]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Adapts `MarkdownMath` content editing or rendering into React presentation behavior.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/render/MarkdownMath.tsx](../../../../../../apps/learnloop-tauri/src/render/MarkdownMath.tsx) |
| Source lines | 32 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/render/_area|TypeScript/render]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `f0052f7260eb63224bd103193929a03fd54660d6` |
| Commit timestamp | `2026-07-21T15:03:22-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/AskOverlay|src/components/AskOverlay.tsx]] → [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]]

## Public API

- `export function normalizeMathDelimiters(value: string): string` — function, line 19
- `export function MarkdownMath(` — function, line 26

## Internal implementation anchors

- `const CODE_SEGMENT = /(```[\s\S]*?(?:```|$)|~~~[\s\S]*?(?:~~~|$)|`[^`\n]*`)/g` — const, line 11
- `function rewriteDelimiters(text: string): string` — function, line 13

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/AskOverlay|src/components/AskOverlay.tsx]] — import-or-re-export: `MarkdownMath`; references `MarkdownMath`
- [[Reference/Desktop/TypeScript/components/CausalAttribution|src/components/CausalAttribution.tsx]] — import-or-re-export: `MarkdownMath`; references `MarkdownMath`
- [[Reference/Desktop/TypeScript/components/ConceptAnimationSection|src/components/ConceptAnimationSection.tsx]] — import-or-re-export: `MarkdownMath`; references `MarkdownMath`
- [[Reference/Desktop/TypeScript/components/DialogueProbe|src/components/DialogueProbe.tsx]] — import-or-re-export: `MarkdownMath`; references `MarkdownMath`
- [[Reference/Desktop/TypeScript/components/InspectorOverlay|src/components/InspectorOverlay.tsx]] — import-or-re-export: `MarkdownMath`; references `MarkdownMath`
- [[Reference/Desktop/TypeScript/components/ItemPresentation|src/components/ItemPresentation.tsx]] — import-or-re-export: `MarkdownMath`; references `MarkdownMath`
- [[Reference/Desktop/TypeScript/components/ProbeBlockResult|src/components/ProbeBlockResult.tsx]] — import-or-re-export: `MarkdownMath`; references `MarkdownMath`
- [[Reference/Desktop/TypeScript/components/QuestionQueue|src/components/QuestionQueue.tsx]] — import-or-re-export: `MarkdownMath`; references `MarkdownMath`
- [[Reference/Desktop/TypeScript/components/RepairTrace|src/components/RepairTrace.tsx]] — import-or-re-export: `MarkdownMath`; references `MarkdownMath`
- [[Reference/Desktop/TypeScript/render/LiveMarkdownEditor|src/render/LiveMarkdownEditor.tsx]] — import-or-re-export: `MarkdownMath`; references `MarkdownMath`
- [[Reference/Desktop/TypeScript/screens/ExamScreen|src/screens/ExamScreen.tsx]] — import-or-re-export: `MarkdownMath`; references `MarkdownMath`
- [[Reference/Desktop/TypeScript/screens/FeedbackScreen|src/screens/FeedbackScreen.tsx]] — import-or-re-export: `MarkdownMath`; references `MarkdownMath`
- [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] — import-or-re-export: `MarkdownMath`; references `MarkdownMath`
- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `MarkdownMath`; references `MarkdownMath`
- [[Reference/Desktop/TypeScript/screens/TodayScreen|src/screens/TodayScreen.tsx]] — import-or-re-export: `MarkdownMath`; references `MarkdownMath`

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

- Imported packages/crates: `katex/dist/katex.min.css`, `react-markdown`, `rehype-katex`, `remark-gfm`, `remark-math`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- No repository test directly names this source path or a uniquely owned export. `npm run typecheck` and `npm run frontend:build` are the executable frontend gates; add a focused test when changing behavior.

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/render/MarkdownMath.tsx](../../../../../../apps/learnloop-tauri/src/render/MarkdownMath.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
