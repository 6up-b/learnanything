---
title: "learnloop.content.sources.math_text"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/sources/math_text.py"
source_paths:
  - "src/learnloop/content/sources/math_text.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.content.sources"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.sources.math_text module"
  - "src/learnloop/content/sources/math_text.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-sources"
---

# `learnloop.content.sources.math_text`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.sources.math_text` exists within [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] to own the behavior summarized by its module contract: Deterministic Unicode-math <-> LaTeX bridging for quote anchoring.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/sources/math_text.py](../../../../../../../src/learnloop/content/sources/math_text.py) |
| Source lines | 357 |
| Owning package | [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `contains_unicode_math(text: str) -> bool` ([source](../../../../../../../src/learnloop/content/sources/math_text.py), line 111) — True when the text carries Unicode math the extraction stores as LaTeX.
- `canonical_tokens(text: str) -> list[Token]` ([source](../../../../../../../src/learnloop/content/sources/math_text.py), line 158) — Canonical token stream for rendered-surface text (Unicode math + prose).
- `latex_tokens(text: str) -> list[Token]` ([source](../../../../../../../src/learnloop/content/sources/math_text.py), line 170) — Canonical token stream for extraction text (LaTeX-bearing markdown).
- `locate_by_canonical(text: str, quote: str) -> tuple[int, int] | None` ([source](../../../../../../../src/learnloop/content/sources/math_text.py), line 230) — Locate a rendered-surface quote inside LaTeX-bearing block text by aligning both in canonical symbol space; returns codepoint offsets into the ORIGINAL block text (so the caller's slice keeps its LaTeX), or None.
- `unicode_math_to_latex(text: str) -> tuple[str, bool]` ([source](../../../../../../../src/learnloop/content/sources/math_text.py), line 308) — Upgrade Unicode math runs to ``$``-wrapped LaTeX, leaving existing ``$...$`` regions and plain prose untouched.

### Module constants

- `CANONICAL_COVERAGE_MIN` ([src/learnloop/content/sources/math_text.py](../../../../../../../src/learnloop/content/sources/math_text.py), line 30)
- `CANONICAL_WINDOW_SLACK` ([src/learnloop/content/sources/math_text.py](../../../../../../../src/learnloop/content/sources/math_text.py), line 31)
- `GREEK` ([src/learnloop/content/sources/math_text.py](../../../../../../../src/learnloop/content/sources/math_text.py), line 36)
- `SYMBOLS` ([src/learnloop/content/sources/math_text.py](../../../../../../../src/learnloop/content/sources/math_text.py), line 51)
- `LATEX_ALIASES` ([src/learnloop/content/sources/math_text.py](../../../../../../../src/learnloop/content/sources/math_text.py), line 71)
- `STYLE_SKIP` ([src/learnloop/content/sources/math_text.py](../../../../../../../src/learnloop/content/sources/math_text.py), line 86)
- `KEEP_PUNCT` ([src/learnloop/content/sources/math_text.py](../../../../../../../src/learnloop/content/sources/math_text.py), line 96)
- `_SUPERSCRIPTS` ([src/learnloop/content/sources/math_text.py](../../../../../../../src/learnloop/content/sources/math_text.py), line 98)
- `_SUBSCRIPTS` ([src/learnloop/content/sources/math_text.py](../../../../../../../src/learnloop/content/sources/math_text.py), line 100)
- `_LETTERLIKE` ([src/learnloop/content/sources/math_text.py](../../../../../../../src/learnloop/content/sources/math_text.py), line 104)
- `_LATEX_COMMAND` ([src/learnloop/content/sources/math_text.py](../../../../../../../src/learnloop/content/sources/math_text.py), line 167)
- `_CONNECTOR` ([src/learnloop/content/sources/math_text.py](../../../../../../../src/learnloop/content/sources/math_text.py), line 275)
- `_MATH_SEGMENT` ([src/learnloop/content/sources/math_text.py](../../../../../../../src/learnloop/content/sources/math_text.py), line 276)

## Internal implementation anchors

- `_is_math_alphanumeric(ch: str) -> bool` ([source](../../../../../../../src/learnloop/content/sources/math_text.py), line 107)
- `_char_tokens(ch: str, start: int, end: int) -> list[Token]` ([source](../../../../../../../src/learnloop/content/sources/math_text.py), line 127) — Canonical tokens for one source character (shared by both surfaces).
- `_find_contiguous(haystack: list[str], needle: list[str]) -> list[int]` ([source](../../../../../../../src/learnloop/content/sources/math_text.py), line 198) — Start indexes of every contiguous occurrence of needle in haystack.
- `_snap_and_balance(text: str, start: int, end: int) -> tuple[int, int]` ([source](../../../../../../../src/learnloop/content/sources/math_text.py), line 211) — Snap outward to whitespace, then keep ``$`` delimiters paired so the anchored slice renders as the math it points at.
- `_word_is_mathy(word: str) -> bool` ([source](../../../../../../../src/learnloop/content/sources/math_text.py), line 279)
- `_transliterate_run(run: str) -> str` ([source](../../../../../../../src/learnloop/content/sources/math_text.py), line 283)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/authoring/exercise_authoring|learnloop.content.authoring.exercise_authoring]] — imports `contains_unicode_math`, `unicode_math_to_latex`; statically calls `contains_unicode_math`, `unicode_math_to_latex`
- [[Reference/Modules/learnloop/reader/annotations|learnloop.reader.annotations]] — imports `locate_by_canonical`; statically calls `locate_by_canonical`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `difflib`, `re`, `unicodedata`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/authoring/exercise_authoring|learnloop.content.authoring.exercise_authoring]], [[Reference/Modules/learnloop/reader/annotations|learnloop.reader.annotations]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_math_text.py](../../../../../../../tests/test_math_text.py) — direct import
  - `test_ambiguous_canonical_match_refuses`
  - `test_canonical_streams_agree_across_surfaces`
  - `test_contains_unicode_math`
  - `test_locate_by_canonical_returns_latex_slice`
  - `test_transliteration_leaves_prose_and_existing_latex_alone`
  - `test_transliteration_mixed_prose`
  - `test_transliteration_upgrades_runs_and_reports_change`

## Modification guidance

- Change math text policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/sources/math_text.py](../../../../../../../src/learnloop/content/sources/math_text.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
