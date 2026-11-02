---
title: "learnloop.projects.redaction"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/projects/redaction.py"
source_paths:
  - "src/learnloop/projects/redaction.py"
source_commit: "0fa326ee408bd137041237a2c9f822c2bf2918f3"
source_commit_timestamp: "2026-10-12T01:44:23-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.projects"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.projects.redaction module"
  - "src/learnloop/projects/redaction.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-projects"
---

# `learnloop.projects.redaction`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/projects/_package|learnloop.projects]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.projects.redaction` exists within [[Reference/Modules/learnloop/projects/_package|learnloop.projects]] to own the behavior summarized by its module contract: Secret filtering before anything is stored or sent (spec §4, gate G2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/projects/redaction.py](../../../../../../src/learnloop/projects/redaction.py) |
| Source lines | 360 |
| Owning package | [[Reference/Modules/learnloop/projects/_package|learnloop.projects]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `0fa326ee408bd137041237a2c9f822c2bf2918f3` |
| Commit timestamp | `2026-10-12T01:44:23-04:00` |

## Public API

- `class RedactionCounter` ([source](../../../../../../src/learnloop/projects/redaction.py), line 80) — Per-kind counts of replaced lines for one capture.
  - `add(self, kind: str) -> None` (line 85; public)
  - `total(self) -> int` (line 89; public)
  - `as_dict(self) -> dict[str, int]` (line 92; public)
- `scan_line(text: str) -> str | None` ([source](../../../../../../src/learnloop/projects/redaction.py), line 119) — The redaction kind for one line of text, or ``None`` when it is clean.
- `redact_text(text: str, counter: RedactionCounter) -> str` ([source](../../../../../../src/learnloop/projects/redaction.py), line 158) — Redact free text (a commit message, a file excerpt) line by line.
- `redact_lines(lines: list[str], counter: RedactionCounter) -> list[str]` ([source](../../../../../../src/learnloop/projects/redaction.py), line 169)
- `redact_diff(diff_text: str, counter: RedactionCounter) -> str` ([source](../../../../../../src/learnloop/projects/redaction.py), line 203) — Redact the content lines of a unified diff, keeping its +/-/space markers.
- `class PathRules` ([source](../../../../../../src/learnloop/projects/redaction.py), line 306) — The secret, ignore and noise rules for one repo.
  - `exclusion(self, path: str) -> str | None` (line 312; public) — Why ``path`` is never sent: a reason string, or ``None`` to allow it.
- `load_path_rules(repo: Path) -> PathRules` ([source](../../../../../../src/learnloop/projects/redaction.py), line 330) — Read the repo's current ``.learnloopignore`` (the owner's latest intent).

### Module constants

- `SECRET_PATTERN_VERSION` ([src/learnloop/projects/redaction.py](../../../../../../src/learnloop/projects/redaction.py), line 30)
- `SECRET_PATH_PATTERNS` ([src/learnloop/projects/redaction.py](../../../../../../src/learnloop/projects/redaction.py), line 32)
- `NOISE_PATH_PATTERNS` ([src/learnloop/projects/redaction.py](../../../../../../src/learnloop/projects/redaction.py), line 42)
- `IGNORE_FILE_NAME` ([src/learnloop/projects/redaction.py](../../../../../../src/learnloop/projects/redaction.py), line 51)
- `REDACTED` ([src/learnloop/projects/redaction.py](../../../../../../src/learnloop/projects/redaction.py), line 53)
- `_PREFIX_RULES` ([src/learnloop/projects/redaction.py](../../../../../../src/learnloop/projects/redaction.py), line 55)
- `_CREDENTIAL_NAME` ([src/learnloop/projects/redaction.py](../../../../../../src/learnloop/projects/redaction.py), line 63)
- `_ASSIGNMENT_RULES` ([src/learnloop/projects/redaction.py](../../../../../../src/learnloop/projects/redaction.py), line 64)
- `_TOKEN_RE` ([src/learnloop/projects/redaction.py](../../../../../../src/learnloop/projects/redaction.py), line 74)
- `_HEX_RE` ([src/learnloop/projects/redaction.py](../../../../../../src/learnloop/projects/redaction.py), line 75)
- `_PEM_END` ([src/learnloop/projects/redaction.py](../../../../../../src/learnloop/projects/redaction.py), line 76)
- `_HUNK_COORDINATES` ([src/learnloop/projects/redaction.py](../../../../../../src/learnloop/projects/redaction.py), line 177)

### Explicit exports

`__all__` declares:

- `IGNORE_FILE_NAME`
- `NOISE_PATH_PATTERNS`
- `PathRules`
- `RedactionCounter`
- `SECRET_PATH_PATTERNS`
- `SECRET_PATTERN_VERSION`
- `load_path_rules`
- `redact_diff`
- `redact_lines`
- `redact_text`
- `scan_line`

## Internal implementation anchors

- `_entropy(token: str) -> float` ([source](../../../../../../src/learnloop/projects/redaction.py), line 96)
- `_high_entropy(token: str) -> bool` ([source](../../../../../../src/learnloop/projects/redaction.py), line 102)
- `class _LineRedactor` ([source](../../../../../../src/learnloop/projects/redaction.py), line 134) — Stateful so every line of a PEM block is redacted, not only BEGIN.
- `_redact_hunk_header(line: str, counter: RedactionCounter) -> str` ([source](../../../../../../src/learnloop/projects/redaction.py), line 180) — Keep a hunk header's coordinates; scan the source text git repeats after them.
- `_glob_to_regex(pattern: str) -> re.Pattern[str]` ([source](../../../../../../src/learnloop/projects/redaction.py), line 233) — gitignore-style glob: ``**`` spans directories, ``*``/``?`` do not.
- `class _Rule` ([source](../../../../../../src/learnloop/projects/redaction.py), line 266)
- `_compile(pattern: str) -> _Rule | None` ([source](../../../../../../src/learnloop/projects/redaction.py), line 272)
- `_matches(rule: _Rule, path: str) -> bool` ([source](../../../../../../src/learnloop/projects/redaction.py), line 287)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/projects/capture|learnloop.projects.capture]] — imports `PathRules`, `RedactionCounter`, `SECRET_PATTERN_VERSION`, `load_path_rules`, `redact_diff`, `redact_lines`, `redact_text`; statically calls `RedactionCounter`, `load_path_rules`, `redact_diff`, `redact_lines`, `redact_text`
- [[Reference/Modules/learnloop/projects/report|learnloop.projects.report]] — imports `SECRET_PATTERN_VERSION`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `hashlib`, `math`, `pathlib`, `re`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/projects/capture|learnloop.projects.capture]], [[Reference/Modules/learnloop/projects/report|learnloop.projects.report]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_project_redaction.py](../../../../../../tests/test_project_redaction.py) — direct import
  - `test_diff_redaction_keeps_markers_and_headers`
  - `test_hunk_header_context_is_scanned_and_coordinates_kept`
  - `test_learnloopignore_patterns`
  - `test_pem_bodies_are_redacted_line_by_line`
  - `test_scanner_finds_known_secret_shapes`
  - `test_scanner_leaves_ordinary_code_alone`
  - `test_secret_and_noise_path_patterns`

## Modification guidance

- Make changes here when the responsibility remains redaction within learnloop.projects; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/projects/redaction.py](../../../../../../src/learnloop/projects/redaction.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
