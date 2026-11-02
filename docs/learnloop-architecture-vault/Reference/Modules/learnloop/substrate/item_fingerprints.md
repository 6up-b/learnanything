---
title: "learnloop.substrate.item_fingerprints"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/substrate/item_fingerprints.py"
source_paths:
  - "src/learnloop/substrate/item_fingerprints.py"
source_commit: "e9ced35e32ffb2bb533ea1845f5dc3794720857b"
source_commit_timestamp: "2026-10-12T16:11:05-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.substrate"
layer: "domain"
concepts:
  - "Learning System"
  - "State and Persistence"
workflows:
  - "Inspect Persistent State"
  - "Rebuild and Shadow Compare"
aliases:
  - "learnloop.substrate.item_fingerprints module"
  - "src/learnloop/substrate/item_fingerprints.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-substrate"
---

# `learnloop.substrate.item_fingerprints`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.substrate.item_fingerprints` exists within [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] to own the behavior summarized by its module contract: Deterministic symbolic fingerprints for PF items (Slice 2 §5.4, migration 174).

The authoritative system-level explanation remains in [[Learning System]], [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/substrate/item_fingerprints.py](../../../../../../src/learnloop/substrate/item_fingerprints.py) |
| Source lines | 213 |
| Owning package | [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `e9ced35e32ffb2bb533ea1845f5dc3794720857b` |
| Commit timestamp | `2026-10-12T16:11:05-04:00` |

## Public API

- `normalize_text(text: str) -> str` ([source](../../../../../../src/learnloop/substrate/item_fingerprints.py), line 51) — Case-, width- and whitespace-insensitive text identity.
- `render_expected_answer(final_answer: str, solution: str) -> str` ([source](../../../../../../src/learnloop/substrate/item_fingerprints.py), line 56) — The expected answer a published PF item carries: key first, then the work.
- `final_answer_text(expected_answer: str | Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/substrate/item_fingerprints.py), line 61) — The final answer of an item's reference, or the whole reference.
- `normalize_answer(answer: str) -> str` ([source](../../../../../../src/learnloop/substrate/item_fingerprints.py), line 76)
- `key_quantities(text: str) -> list[str]` ([source](../../../../../../src/learnloop/substrate/item_fingerprints.py), line 91) — The sorted multiset of numeric literals in a stem (its parameters).
- `technique_signature(techniques: Sequence[str]) -> str` ([source](../../../../../../src/learnloop/substrate/item_fingerprints.py), line 96)
- `fingerprint_keys(*, prompt: str, expected_answer: str | Mapping[str, Any], skeletons: Sequence[Mapping[str, Any]]=(), generator_hash: str | None=None, parameters: Mapping[str, Any] | None=None, sympy_normal_form: str | None=None) -> list[tuple[str, str, str]]` ([source](../../../../../../src/learnloop/substrate/item_fingerprints.py), line 100) — ``(namespace, component, value_hash)`` keys; missing inputs yield no key.
- `skeleton_component(skeleton: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/substrate/item_fingerprints.py), line 130) — ``skeleton:<model>@<prompt version>``: unique per persisted skeleton.
- `published_candidate_payloads(connection: Any) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/substrate/item_fingerprints.py), line 141) — Published item id -> its candidate payload (sandbox outputs are persisted).
- `item_fingerprint_keys(item: PracticeItem, *, skeletons: Sequence[Mapping[str, Any]]=(), payload: Mapping[str, Any] | None=None) -> list[tuple[str, str, str]]` ([source](../../../../../../src/learnloop/substrate/item_fingerprints.py), line 149)
- `family_items(vault: LoadedVault) -> list[PracticeItem]` ([source](../../../../../../src/learnloop/substrate/item_fingerprints.py), line 159)
- `compute_item_fingerprints(vault: LoadedVault, connection: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/substrate/item_fingerprints.py), line 163)
- `rebuild_item_fingerprints(vault: LoadedVault, repository: Repository) -> dict[str, int]` ([source](../../../../../../src/learnloop/substrate/item_fingerprints.py), line 184) — The single DERIVED replayer: pure recomputation inside the caller's transaction.
- `shared_keys(left: Iterable[tuple[str, str, str]], right: Iterable[tuple[str, str, str]]) -> list[tuple[str, str]]` ([source](../../../../../../src/learnloop/substrate/item_fingerprints.py), line 193) — ``(namespace, component)`` pairs whose value matches on both sides.

### Module constants

- `FINGERPRINT_VERSION` ([src/learnloop/substrate/item_fingerprints.py](../../../../../../src/learnloop/substrate/item_fingerprints.py), line 35)
- `FINAL_ANSWER_PREFIX` ([src/learnloop/substrate/item_fingerprints.py](../../../../../../src/learnloop/substrate/item_fingerprints.py), line 36)
- `WORKED_SOLUTION_PREFIX` ([src/learnloop/substrate/item_fingerprints.py](../../../../../../src/learnloop/substrate/item_fingerprints.py), line 37)
- `EXACT_COMPONENTS` ([src/learnloop/substrate/item_fingerprints.py](../../../../../../src/learnloop/substrate/item_fingerprints.py), line 40)
- `_NUMBER` ([src/learnloop/substrate/item_fingerprints.py](../../../../../../src/learnloop/substrate/item_fingerprints.py), line 42)
- `_LATEX_DELIMITERS` ([src/learnloop/substrate/item_fingerprints.py](../../../../../../src/learnloop/substrate/item_fingerprints.py), line 43)

### Explicit exports

`__all__` declares:

- `EXACT_COMPONENTS`
- `FINAL_ANSWER_PREFIX`
- `FINGERPRINT_VERSION`
- `WORKED_SOLUTION_PREFIX`
- `compute_item_fingerprints`
- `final_answer_text`
- `fingerprint_keys`
- `item_fingerprint_keys`
- `key_quantities`
- `normalize_answer`
- `normalize_text`
- `rebuild_item_fingerprints`
- `render_expected_answer`
- `shared_keys`
- `skeleton_component`
- `skeleton_content_hash`
- `technique_signature`

## Internal implementation anchors

- `_sha(payload: Any) -> str` ([source](../../../../../../src/learnloop/substrate/item_fingerprints.py), line 46)
- `_canonical_number(token: str) -> str` ([source](../../../../../../src/learnloop/substrate/item_fingerprints.py), line 82)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]] — imports `final_answer_text`; statically calls `final_answer_text`
- [[Reference/Modules/learnloop/ops/embedding_compare|learnloop.ops.embedding_compare]] — imports `final_answer_text`, `fingerprint_keys`, `shared_keys`; statically calls `final_answer_text`, `fingerprint_keys`, `shared_keys`
- [[Reference/Modules/learnloop/ops/pf_generation|learnloop.ops.pf_generation]] — imports `EXACT_COMPONENTS`, `FINGERPRINT_VERSION`, `final_answer_text`, `fingerprint_keys`, `item_fingerprint_keys`, `published_candidate_payloads`, `render_expected_answer`, `shared_keys`, `skeleton_content_hash`; statically calls `final_answer_text`, `fingerprint_keys`, `item_fingerprint_keys`, `published_candidate_payloads`, `render_expected_answer`, `shared_keys`, `skeleton_content_hash`
- [[Reference/Modules/learnloop/ops/pf_publish|learnloop.ops.pf_publish]] — imports `render_expected_answer`; statically calls `render_expected_answer`
- [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] — imports `rebuild_item_fingerprints`; statically calls `rebuild_item_fingerprints`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/pf|learnloop.db.stores.pf]] — imports `candidates`, `replace_item_fingerprints`, `skeletons_for_hashes`; calls `candidates`, `replace_item_fingerprints`, `skeletons_for_hashes`
- [[Reference/Modules/learnloop/vault/hashes|learnloop.vault.hashes]] — imports `practice_item_hash`, `skeleton_content_hash`; calls `practice_item_hash`, `skeleton_content_hash`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `hashlib`, `json`, `re`, `typing`, `unicodedata`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Rebuild and Shadow Compare]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]], [[Reference/Modules/learnloop/ops/embedding_compare|learnloop.ops.embedding_compare]], [[Reference/Modules/learnloop/ops/pf_generation|learnloop.ops.pf_generation]], [[Reference/Modules/learnloop/ops/pf_publish|learnloop.ops.pf_publish]], [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_item_fingerprints.py](../../../../../../tests/test_item_fingerprints.py) — direct import
  - `test_keys_use_the_077_namespaces_and_never_mix_them`
  - `test_normalization_is_surface_insensitive_but_parameter_sensitive`
  - `test_skeletons_from_one_model_at_two_prompt_versions_rebuild_without_a_key_collision`

## Modification guidance

- Change item fingerprints policy here when substrate owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/substrate/item_fingerprints.py](../../../../../../src/learnloop/substrate/item_fingerprints.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
