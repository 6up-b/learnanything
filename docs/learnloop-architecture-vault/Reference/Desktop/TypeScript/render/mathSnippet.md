---
title: "Desktop module · src/render/mathSnippet.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.render.mathSnippet"
language: "TypeScript"
area: "TypeScript/render"
source_path: "apps/learnloop-tauri/src/render/mathSnippet.ts"
source_paths:
  - "apps/learnloop-tauri/src/render/mathSnippet.ts"
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

# `src/render/mathSnippet.ts`

Area: [[Reference/Desktop/TypeScript/render/_area|TypeScript/render]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Adapts `mathSnippet` content editing or rendering into React presentation behavior.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/render/mathSnippet.ts](../../../../../../apps/learnloop-tauri/src/render/mathSnippet.ts) |
| Source lines | 156 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/render/_area|TypeScript/render]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/app/todayPlan|src/app/todayPlan.ts]] → [[Reference/Desktop/TypeScript/render/mathSnippet|src/render/mathSnippet.ts]]

## Public API

- `export function clipMath(text: string, max: number): string` — function, line 14
- `export function plainMathLine(markdown: string): string` — function, line 89
- `export function selectionQuote(range: Range, asSelected: string): string` — function, line 124

## Internal implementation anchors

- `const MATH = /\\\(([\s\S]*?)\\\)|\\\[([\s\S]*?)\\\]|\$\$([\s\S]*?)\$\$|\$([^$\n]+?)\$/g` — const, line 7
- `let cut = max` — let, line 16
- `const start = match.index ?? 0` — const, line 18
- `const end = start + match[0].length` — const, line 19
- `function dropUnclosedOpener(head: string): string` — function, line 31
- `const closed = head.replace(MATH, (whole)` — const, line 32
- `const opener = Math.max(closed.lastIndexOf("\\("), closed.lastIndexOf("\\["), closed.lastIndexOf("$"))` — const, line 33
- `const GREEK: Record<string, string> =` — const, line 37
- `const SYMBOLS: Record<string, string> =` — const, line 44
- `const STYLE = new Set([ "text", "textbf", "textit", "emph", "mathrm", "mathbf", "mathbb", "mathcal", "mathfrak", "mathit", "mathsf", "mathtt", "boldsymbol", "bm", "operatorname", "hat", "widehat", "bar", "overline", "underline", "vec", "tilde", "widetilde", "…` — const, line 54
- `function plainTex(tex: string): string` — function, line 62
- `let text = tex` — let, line 63
- `function plainMarkdown(text: string): string` — function, line 80
- `let out = ""` — let, line 90
- `let at = 0` — let, line 91
- `const start = match.index ?? 0` — const, line 93
- `const rest = markdown.slice(at)` — const, line 98
- `const opener = rest.search(/\\\(|\\\[|\$/)` — const, line 99
- `const FORMULA = ".katex, .katex-error"` — const, line 107
- `const TEX_SOURCE = 'annotation[encoding="application/x-tex"]'` — const, line 108
- `const BLOCK = "p, div, li, h1, h2, h3, h4, h5, h6, blockquote, pre, td, th, tr"` — const, line 109
- `function formulaTex(formula: Element): string` — function, line 111
- `const source = formula.querySelector(TEX_SOURCE) ?? formula.querySelector(".katex-html") ?? formula` — const, line 114
- `const common = range.commonAncestorContainer` — const, line 125
- `const root = common.nodeType === Node.TEXT_NODE ? common.parentNode : common` — const, line 126
- `const formulaOf = (node: Node)` — const, line 128
- `const walker = (root.ownerDocument ?? document).createTreeWalker(root, NodeFilter.SHOW_TEXT)` — const, line 129
- `const texts: Text[] = []` — const, line 130
- `let out = ""` — let, line 136
- `let block: Element | null = null` — let, line 137
- `const taken = new Set<Element>()` — const, line 138
- `const here = node.parentElement?.closest(BLOCK) ?? null` — const, line 140
- `const formula = formulaOf(node)` — const, line 143
- `const tex = formulaTex(formula)` — const, line 147
- `const start = node === range.startContainer ? range.startOffset : 0` — const, line 151
- `const end = node === range.endContainer ? range.endOffset : node.data.length` — const, line 152

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/todayPlan|src/app/todayPlan.ts]] — import-or-re-export: `plainMathLine`; references `plainMathLine`
- [[Reference/Desktop/TypeScript/components/AskOverlay|src/components/AskOverlay.tsx]] — import-or-re-export: `plainMathLine`; references `plainMathLine`
- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `selectionQuote`; references `selectionQuote`
- [[Reference/Desktop/TypeScript/screens/reader/AskRail|src/screens/reader/AskRail.tsx]] — import-or-re-export: `clipMath`; references `clipMath`
- [[Reference/Desktop/TypeScript/screens/reader/LibraryAnswer|src/screens/reader/LibraryAnswer.tsx]] — import-or-re-export: `plainMathLine`; references `plainMathLine`
- [[Reference/Desktop/TypeScript/screens/reader/ReaderAskBranches|src/screens/reader/ReaderAskBranches.tsx]] — import-or-re-export: `plainMathLine`; references `plainMathLine`
- [[Reference/Desktop/TypeScript/screens/reader/SideBySidePane|src/screens/reader/SideBySidePane.tsx]] — import-or-re-export: `selectionQuote`; references `selectionQuote`

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/render/sourceMacros.test.tsx](../../../../../../apps/learnloop-tauri/src/render/sourceMacros.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/render/selectionQuote.test.tsx](../../../../../../apps/learnloop-tauri/src/render/selectionQuote.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/render/mathSnippet.ts](../../../../../../apps/learnloop-tauri/src/render/mathSnippet.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
