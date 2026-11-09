---
title: "learnloop.ops.pf_verify"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ops/pf_verify.py"
source_paths:
  - "src/learnloop/ops/pf_verify.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ops"
layer: "domain"
concepts:
  - "State and Persistence"
  - "Configuration"
workflows:
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.ops.pf_verify module"
  - "src/learnloop/ops/pf_verify.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-ops"
---

# `learnloop.ops.pf_verify`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ops.pf_verify` exists within [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] to own the behavior summarized by its module contract: Reference-key verification, extracted from PF-b (spec_source_practice_and_probes_v1 §7.3).

The authoritative system-level explanation remains in [[State and Persistence]], [[Configuration]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ops/pf_verify.py](../../../../../../src/learnloop/ops/pf_verify.py) |
| Source lines | 292 |
| Owning package | [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class VerifierEnv` ([source](../../../../../../src/learnloop/ops/pf_verify.py), line 67) — What the verification steps need: receipts and ledger, role clients, limits.
  - `call(self, entry: RoleClient, *, on_call: OnCall | None=None, **kwargs: Any) -> CallResult` (line 80; public)
- `panel_solves(env: VerifierEnv, stem: str, *, solves_per_model: int, on_call: OnCall | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/ops/pf_verify.py), line 87) — Each panel model solves ``stem`` ``solves_per_model`` times, never seeing a key.
- `equivalence(env: VerifierEnv, stem: str, reference: str, solves: Sequence[dict[str, Any]], *, on_call: OnCall | None=None) -> tuple[CallResult, Any]` ([source](../../../../../../src/learnloop/ops/pf_verify.py), line 104)
- `agreement(env: VerifierEnv, subject_kind: str, subject_id: str, input_hash: str, stem: str, reference: str, solves: Sequence[dict[str, Any]], *, on_call: OnCall | None=None, on_sandbox_unavailable: str='raise', symbolic_reference: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/pf_verify.py), line 116) — LLM agreement per solve, confirmed by the sandboxed sympy check where numeric/symbolic.
- `symbolic_status(*, symbolic: bool, usable: bool, check_written: bool, sandbox_state: str, degenerate: bool, llm_agrees: Sequence[bool], confirmations: Sequence[bool | None], reference_readable: bool=True) -> str` ([source](../../../../../../src/learnloop/ops/pf_verify.py), line 199) — What the symbolic check said, apart from the model's agreement.
- `span_support(env: VerifierEnv, *, subject_kind: str, subject_id: str, question: str, cited_quote: str, reference_answer: str, explanation: str, item_kind: str, on_call: OnCall | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/pf_verify.py), line 230) — The reference verifier's independent check that a cited span supports the key.
- `verify_reference(env: VerifierEnv, *, stem: str, reference: str, subject_kind: str, subject_id: str, input_hash: str, solves_per_model: int, on_sandbox_unavailable: str='raise', on_call: OnCall | None=None, symbolic_reference: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/pf_verify.py), line 262) — The panel-plus-sympy check of one key: solves, then agreement.

### Module constants

- `SYMBOLIC_KINDS` ([src/learnloop/ops/pf_verify.py](../../../../../../src/learnloop/ops/pf_verify.py), line 54)
- `SYMBOLIC_STATUSES` ([src/learnloop/ops/pf_verify.py](../../../../../../src/learnloop/ops/pf_verify.py), line 55)

### Explicit exports

`__all__` declares:

- `SYMBOLIC_STATUSES`
- `VerifierEnv`
- `agreement`
- `equivalence`
- `panel_solves`
- `span_support`
- `symbolic_status`
- `verify_reference`

## Internal implementation anchors

- `_sha(payload: Any) -> str` ([source](../../../../../../src/learnloop/ops/pf_verify.py), line 59)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]] — imports `module`; statically calls `VerifierEnv`, `span_support`, `verify_reference`
- [[Reference/Modules/learnloop/ops/pf_generation|learnloop.ops.pf_generation]] — imports `module`; statically calls `VerifierEnv`, `agreement`, `panel_solves`, `span_support`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/content/authoring/pf_contracts|learnloop.content.authoring.pf_contracts]] — imports `module`; calls `equivalence_prompt`, `panel_solve_prompt`, `span_support_prompt`
- [[Reference/Modules/learnloop/content/authoring/pf_sandbox|learnloop.content.authoring.pf_sandbox]] — imports `SandboxLimits`, `SandboxUnavailable`, `equivalence_confirmations`, `run_equivalence_checks`, `sandbox_available`; calls `equivalence_confirmations`, `run_equivalence_checks`, `sandbox_available`
- [[Reference/Modules/learnloop/ops/pf_calls|learnloop.ops.pf_calls]] — imports `CallResult`, `PFCaller`, `RoleClient`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `hashlib`, `json`, `subprocess`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]], [[Reference/Modules/learnloop/ops/pf_generation|learnloop.ops.pf_generation]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_pf_verify_extraction_parity.py](../../../../../../tests/test_pf_verify_extraction_parity.py) — direct import
  - `test_a_failed_sympy_run_is_disagreement_for_pf_but_reported_apart`
  - `test_combined_agreement_and_ledger_rows_are_pf_s`
  - `test_pf_still_raises_without_a_sandbox_and_the_ladder_reports`
  - `test_symbolic_status_table`

## Modification guidance

- Make changes here when the responsibility remains pf verify within learnloop.ops; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ops/pf_verify.py](../../../../../../src/learnloop/ops/pf_verify.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
