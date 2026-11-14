# Refactor K2.5: the normalizer in named stages

Branch `refactor/k2.5-normalize-stages`, based on main `2f35db5173`. Step K2.5 of arc K, specified in
`docs/reviews/k2-ingestion-strategy-2026-11-11.md` (K2.5) and the map's KP1. Structure track: a move. For every
input the normalizer returns the same rows, gate items, diagnostics, id lists and auto-apply ids, and mints ids in
the same call order.

## Step 0: the stages at the base

`_normalize` was `source_set_synthesis.py:739-1819` (1,081 lines), one frame. Line numbers below are at the base.
The shared state was fifteen dicts, seven lists and a set; the closures were `d`, `unique`,
`register_concept_reference`, `resolve_concept_reference`, `resolve_concept_references`, `mint_concept`,
`resolve_endpoint`, `edge_review`, `_reaches` and `add_concept_edge`. `_normalize` has no `raise` of its own; the
one handler is the nominator shadow's `except Exception` (:1019), which records the exception's name. Errors from
callees (`judge_facet_mints`, the meaning chokepoint) propagate unchanged.

| # | Stage (now) | Base lines | Reads | Writes | Order dependence |
|---|---|---|---|---|---|
| 1 | `_index_registry_concepts` | 791-792 | `vault.concepts` | `concept_reference_index` | before every reference resolution |
| 2 | `_concepts` | 794-807 | `synth.concepts` | `used_ids` (`unique`), `concept_ids`, `concept_client_for_id`, `concept_reference_index`, `rows`, `gate_items` | ids minted in answer order; ULID for an untitled one |
| 3 | `_facet_candidates` | 901-956 | `synth.facets`, `concept_ids`, `inputs` | `used_ids`, `candidate_facets` | `unique` calls continue after the concepts' |
| 4 | `_facet_retirements` | 958-1001 | `facet_identity_plan`, `candidate_facets`, `vault.evidence_facets` | `retirements`, `retired_candidates`, `pre_union`, `contract_notes`, survivors' payloads, `dropped_diagnostics`; rebinds `candidate_facets` | the join is one retiree after another in sorted client order |
| 5 | `_mint_gate` | 1003-1115 | `candidate_facets`, `vault` | `graph_nomination`, `alias_additions`, `minted_payload_by_id`, `minted_client_by_id`, `row_extras`, `facet_client_to_id`, `facet_dep_client`, `facet_payloads`, `rows`, `gate_items`, `dropped_diagnostics` | a candidate that aliases into an earlier one reads `minted_client_by_id`, so candidate order is the output |
| 6 | `_retired_references` | 1117-1153 | `retired_candidates`, `retirements`, `facet_client_to_id`, `facet_dep_client`, `minted_payload_by_id` | `attach_unions`, `alias_canonical`, `retired_targets`, `facet_dep_client`, `facet_client_to_id`, `alias_additions` | needs 5's maps complete |
| 7 | `_register_aliases` | 1155-1258 | `alias_additions`, `attach_unions`, `minted_payload_by_id`, `vault` | `registered_before`, `contract_notes`, `row_extras`, minted payloads' aliases, `rows`, `gate_items`, `dropped_diagnostics` | alias rows are appended after every facet row; targets in sorted order |
| 8 | `_identity_actions` | 1260-1264 | `retired_targets`, `pre_union`, `minted_payload_by_id`, `registered_before`, `rows`, `contract_notes`, `alias_canonical` | `facet_identity_actions` | reads the rows 5 and 7 wrote, so it runs after both |
| 9 | `_learning_objects` | 1266-1338 | `synth.learning_objects`, the concept maps | `used_ids`, `lo_client_to_id`, `lo_relation_seeds`, `rows`, `gate_items`, `dropped_diagnostics`, and the minted concepts' maps and rows | a minted concept's id comes from `unique` and a ULID mid-stage |
| 10 | `_blueprints` | 1340-1480 | `synth.blueprints`, `lo_client_to_id`, `facet_client_to_id`, `facet_dep_client`, `alias_canonical` | `used_ids`, `recipe_components`, `rows`, `gate_items`, `dropped_diagnostics` | after 5-7 (facet maps) and 9 (LO ids) |
| 11 | `_practice_items` | 1482-1648 | `synth.practice_items`, `items_off`, `rows` (the method target view), the facet maps | `used_ids`, `criterion_targets`, `rows`, `gate_items`, `dropped_diagnostics` | the method view reads the rows written so far, so it follows 2, 3-7 and 9 |
| 12 | `_concept_edges` | 1650-1794 | `synth.concept_relations`, `lo_relation_seeds`, `vault.edges`, the concept maps | `used_ids` (edge ids), `existing_edges`, `edge_signatures`, `prereq_adjacency`, `part_of_parent`, `edge_diagnostics`, `rows`, `gate_items` | explicit relations before the floor from LO seeds; the first edge to claim a part_of parent or close a cycle wins |
| 13 | `_finalize` | 1796-1819 | everything | `rows` payloads of facet rows (`row_extras`) | `edge_diagnostics` precede `dropped_diagnostics` in the result |

The map's twelve stages are these with the registry index counted into the id helpers and the final stage folded
in. No stage needed reordering: every stage already ran to completion before the next began, and no statement
depended on a later stage's output. The one place stages meet in the middle of a loop is none; the closures were
only defined mid-function. `unique` is shared by stages 2, 3, 9, 10, 11 and 12, so its state (`used_ids`) is on
the state object.

Callers and importers at the base: `_normalize` was called by `SynthesisMode.normalize` (`source_set_synthesis.py`,
BOOTSTRAP), by `_normalize_append` (`source_append.py`, which also reached `_Normalized`, `_row`, `_span_refs`,
`_support_citations`), and by three test files (`tests/facet_authority_helpers.py`, `tests/test_facet_authority.py`,
`tests/test_facet_reword_confirm.py`); `_span_refs` by `tests/test_facet_authority.py`; `_method_target_view` by
`tests/test_required_method_items.py`. `tests/identity_pins_helpers.py` named `_normalize` as a site of identity B6
(the target-hash dump). No test patched a name inside either normalizer (checked by searching `monkeypatch` and
`patch` against the modules and the helper names).

## Step 2: coverage before the move

A scratch pytest plugin (`sys.monitoring` LINE and BRANCH events on the code objects of the two functions and their
closures; coverage.py is not installed) ran the 25 goldens, the synthesis, facet identity, mint gate, append, reword,
proposal and sidecar synthesis tests and the other files that reach the normalizers (30 files, 628 tests). Lines of
`_normalize` and `_normalize_append` executed by none of them, at the base: 48 in `_normalize` and 18 in
`_normalize_append`, in these places:

- concept reference resolution by title and by entity id (`resolve_concept_reference`);
- three skip paths of the retirement stage (no such candidate, no such survivor or a retired survivor, an attach to
  an unregistered facet);
- the nominator shadow's `except`;
- the mint gate's refusal of a reword nothing explanatory supports;
- the retired-reference stage's taken-id path;
- an LO with an unresolvable concept reference (the message), recipe components that dedupe facet dependencies,
  an item's `evidence_facets` by name;
- `required_method` dropped from a non-method target, and the advisory statement flag;
- the whole concept-edge validation: unresolvable endpoint, self edge, duplicate, reversed confusable pair, second
  part_of parent, hierarchy cycle, prerequisite cycle, registry edges;
- the append's exam-span link drop and its non-facet restructure.

Added before any source change (commit `be4d17b748`): `tests/test_normalize_cases.py` with its helper
`tests/normalize_helpers.py` and nine goldens under `tests/goldens/synthesis_normalize/`: eight cases that call the
normalizers directly on small built answers over an applied map (concept references, edges, blueprints, practice
items with items on and off, a failing nominator, skipped retirements, a refused reword, an append's links and a
restructure), the ULID stream seeded, the whole `Normalized` compared. After them, still unexecuted: the `def` lines
(an artifact of the monitor), and three branches that look unreachable from any answer: the retired-reference
stage's `if not target: continue` (an in-run survivor with no id in `facet_client_to_id`: the mint gate sets one for
every candidate that is not refused, and a refused one's retirement is also skipped) and the alias stage's two
`continue`s for an alias target with no row or alias (a target neither minted nor registered, or an alias that
shadows a registered id with no new alias and no attach). They are defensive; they move verbatim, and a break would
show as a type error in the stage, not as a silent change.

## Step 3: the move

`content/synthesis/normalize.py` opens with the approach paragraph. It holds `_NormalizeState` (the inputs, the id
maps, the rows and gate items, the diagnostics; `unique` is a method), `normalize()` calling thirteen stage
functions in the table's order, and the helpers the stages need and the orchestrator also uses: `Normalized` (was
`_Normalized`), `_row`, `_span_refs`, `_slug`, `_support_citations`, `_unresolved_citations`, `_joined_contribution`,
`_method_target_view`, `_keep_sibling_criterion_dependencies`, `_facet_identity_actions`. They moved because the
module must not import the orchestrator. The closures are `_register_concept_reference`,
`_resolve_concept_reference(s)`, `_mint_concept`, `_resolve_endpoint`, `_edge_review` and `_add_concept_edge`, each
over the state; `_reaches` is pure. The stage bodies were produced by a token-level rewrite of the old text (state
names read `st.<name>`; nothing else touched) and checked against the old body line by line after stripping the
rewrite; the only lines that differ are the state declarations and the signatures. The empty-initialisation lines
(`x: dict = {}`) were dropped because the state's field defaults hold them.

`_normalize_append` became `_AppendState` and four functions (links, notations, conflicts, restructures) under the
original function, which builds the state from the shared normalizer's result. It reached no locals of the frame:
it called `_normalize` as a whole.

## Step 5: proof

- 25 goldens and the nine added goldens unchanged and green; the 30 coverage files plus the retired-config,
  effective-defaults and CLI snapshot tests: 677 passed after the move (the 628 of step 2, the 8 new cases, and the three
  extra files' tests).
- `lint-imports`: 42 kept. `normalize.py` imports nothing from the orchestrator.
- Structure ratchet: functions over 200 lines 78 to 76 (both normalizers left the list); lowered with `--write`.
- Lines: `source_set_synthesis.py` 4,279 to 2,854; `source_append.py` 1,146 to 1,168; `normalize.py` 1,597 (new).
  Longest function in `normalize.py`: `_practice_items`, 175 lines (the old frame was 1,081); the append's longest
  is 80.

## Judgment calls

- `_span_refs`'s `inputs` annotation is `Any` and the state's `inputs` is `Any` with a note, because the type
  (`_SynthesisInputs`) lives in the orchestrator, which `normalize.py` must not import.
- `_normalize` is `normalize` and `_Normalized` is `Normalized` (cross-module names); tests that imported the old
  names import the new ones (call sites renamed, no assertion changed). The B6 identity site now names
  `normalize.py::_mint_gate`, where the target-hash dump is; the pinned bytes did not move.
- Comments moved with their code, untouched, including six that name a review round (the stage-artifact
  ratchet's count moved from `source_set_synthesis.py` to `normalize.py`, total unchanged).
- The append's `conflict_candidates` is read at the end instead of before the conflicts loop (a pure read of the
  answer).
