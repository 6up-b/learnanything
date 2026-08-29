---
title: "learnloop.content.synthesis.synthesis_eval"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/synthesis/synthesis_eval.py"
source_paths:
  - "src/learnloop/content/synthesis/synthesis_eval.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.content.synthesis"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.synthesis.synthesis_eval module"
  - "src/learnloop/content/synthesis/synthesis_eval.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-synthesis"
---

# `learnloop.content.synthesis.synthesis_eval`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.synthesis.synthesis_eval` exists within [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] to own the behavior summarized by its module contract: Synthesis quality eval harness (ING M6, spec §14 / §15 M6).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/synthesis/synthesis_eval.py](../../../../../../../src/learnloop/content/synthesis/synthesis_eval.py) |
| Source lines | 302 |
| Owning package | [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class EvalReport` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_eval.py), line 53)
  - `as_dict(self) -> dict[str, Any]` (line 70; public)
  - `format_text(self) -> str` (line 89; public)
- `evaluate(gold: dict[str, Any], candidate: dict[str, Any]) -> EvalReport` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_eval.py), line 143)
- `extract_candidate_from_vault(vault: LoadedVault, *, prompt_version: str='') -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_eval.py), line 264) — Build the eval candidate summary from an applied study map.
- `load_gold(path: Path) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_eval.py), line 295)
- `default_gold_path() -> Path` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_eval.py), line 301)

### Module constants

- `_TOKEN_RE` ([src/learnloop/content/synthesis/synthesis_eval.py](../../../../../../../src/learnloop/content/synthesis/synthesis_eval.py), line 36)
- `_SEMANTIC_ROLES` ([src/learnloop/content/synthesis/synthesis_eval.py](../../../../../../../src/learnloop/content/synthesis/synthesis_eval.py), line 37)
- `_FUZZY_THRESHOLD` ([src/learnloop/content/synthesis/synthesis_eval.py](../../../../../../../src/learnloop/content/synthesis/synthesis_eval.py), line 38)

## Internal implementation anchors

- `_tokens(text: str) -> set[str]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_eval.py), line 41)
- `_jaccard(a: set[str], b: set[str]) -> float` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_eval.py), line 45)
- `_fingerprint(facet: dict[str, Any]) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_eval.py), line 105)
- `_match_facets(candidate: list[dict[str, Any]], gold: list[dict[str, Any]]) -> dict[int, int]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_eval.py), line 112) — Greedy candidate-index -> gold-index alignment by fingerprint then fuzzy claim.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `default_gold_path`, `evaluate`, `extract_candidate_from_vault`, `load_gold`; statically calls `default_gold_path`, `evaluate`, `extract_candidate_from_vault`, `load_gold`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/vault/facet_fingerprint|learnloop.vault.facet_fingerprint]] — imports `semantic_fingerprint`; calls `semantic_fingerprint`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/vault/yaml_io|learnloop.vault.yaml_io]] — imports `read_yaml`; calls `read_yaml`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `pathlib`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_synthesis_eval.py](../../../../../../../tests/test_synthesis_eval.py) — direct import
  - `test_canned_synthesis_scores_perfect_against_matching_gold`
  - `test_gold_file_loads_and_is_prompt_versioned`
  - `test_low_provenance_when_only_exam_role_cited`
  - `test_over_fragmentation_and_duplicate_are_reported`
  - `test_repair_distinctness_flags_false_distinction`

## Modification guidance

- Change synthesis eval policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/synthesis/synthesis_eval.py](../../../../../../../src/learnloop/content/synthesis/synthesis_eval.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
