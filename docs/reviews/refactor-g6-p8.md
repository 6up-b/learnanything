# G6-P8 shared practice lead check

The owner decided on 2026-11-20 to use one lead test on every exit.
`has_item_bound_lead` in `src/learnloop/source_retrieval/corpus.py` (beside the other item-bound rules; `tutor.py` re-exports it, and placing it there keeps the import-cycle count where it was) factors out the
reference filter's existing `lead_role` classification and exercise/solution role set.
`corpus.effective_hint` at `src/learnloop/source_retrieval/corpus.py:313` still only demotes hints.

| Exit | Production call site | Before the fix | After the fix |
|---|---|---|---|
| References and the linked fallback | `src/learnloop/source_retrieval/tutor.py:160` via `with_references` on line 214 and `linked_reference_filter` on line 194. The linked fallback calls the filter on its blocks at `src/learnloop/tutor/tutor_qa.py:2506`. | Withheld | Withheld |
| Reader tutor | `ItemBoundGuard` at `src/learnloop/source_retrieval/reader_tutor.py:302` | Withheld | Withheld |
| Pinned tutor | `PinnedSpanProvider` at `src/learnloop/source_retrieval/tutor.py:530` | Admitted | Withheld |
| Compare under assisted practice | Pin and anchor admission at `src/learnloop/source_retrieval/compare.py:380`, candidate filtering at `src/learnloop/source_retrieval/compare.py:455` | Pins and candidates admitted | Pins and candidates withheld |
| Tutor retrieved pool | `tutor_pool` at `src/learnloop/source_retrieval/tutor.py:303` | Admitted | Withheld |

The Reader passes its existing selection exception to the shared check so an exercise lead may still be
admitted on an explicit selection. A solution lead continues to be withheld there. Pins use the existing
practice availability reason for a lead-only refusal. The retrieved pool keeps its answer-overlap count
specific to the overlap check.

## Regression and controls

`tests/test_protection_surface_matrix.py:1853` exercises the five exits in a copy of the matrix vault.
The fixture gives the item a linked passage and places the `Solution:` block and an ordinary prose block in the
same source. Both blocks have an effective `ordinary_prose` hint and neither reproduces the item's key.
The test checks reference and linked admission separately, and drives compare both with a pin and through
search. Before the production edit, only the pinned tutor, compare and retrieved pool failed. The same solution
was admitted on all five exits without active practice. Ordinary prose was admitted in both contexts.

## Persistence and reuse

The change filters new model contexts and comparison results during practice. Existing rows retain their
meaning. New receipts and comparison provenance reflect the passages the request admitted or dropped.
The withheld set is absent from the cache and reuse keys. The comparison lookup uses the query hash,
policy and admitted counterpart keys (`src/learnloop/db/stores/source_service.py:933`). Listwise verification
uses the rendered prompt with admitted candidates and the route and schema identity
(`src/learnloop/practice_index/listwise.py:119`). Query embeddings use the query text
(`src/learnloop/source_retrieval/queries.py:201`). The tutor's run hash covers its rendered context
(`src/learnloop/tutor/tutor_qa.py:2138`). A filtered passage can change which admitted inputs those
identities see. The identity definitions and pins remain the same.

## Verification

All pytest runs used `t.sh` with explicit files or node IDs, `-q -n 2 -m "not arc_close"`.
The result lines below omit xdist's progress output.

| Targets | Last result line |
|---|---|
| Matrix with `-k g6_p8_practice_leads`, initial fixture assertion | `10 failed in 3.56s` |
| Matrix with `-k g6_p8_practice_leads --tb=short`, before the production edit | `3 failed, 7 passed in 3.02s` |
| Same focused run after the production edit | `10 passed in 2.99s` |
| `tests/test_protection_surface_matrix.py` | `164 passed in 38.60s` |
| `py.sh ruff check` | `All checks passed!` |
| `py.sh lint-imports --no-cache` | `Contracts: 44 kept, 0 broken.` |

The initial fixture assertion looked for a role on the canonical text row. The corrected assertion reads the
fixture's effective hint from `block_roles`. The two focused runs used that corrected fixture.

## Scope of verification

The landing gate, arc-close lane, durability lane, live models, and desktop and phone UI were outside this run.
The direct regression covers the Reader's final admission guard. Code inspection also found that the Reader's
upstream Find Sources verification can receive a mislabeled solution before that guard runs
(`src/learnloop/source_retrieval/reader_tutor.py:213`, `src/learnloop/source_retrieval/find_sources.py:768`).
That separate verification path was outside the five exits in this fix and was assessed by inspection.

The wider run after the move (the orchestrator's, 2026-11-21): the 23 test files whose names contain exam_material, protection, held_out, tutor_qa, compare, pinned or reader_tutor, with the identity pins, the structure ratchets, the public-tip guards and the test layout: `1025 passed in 158.35s`; `ruff check` and `lint-imports --no-cache` (44 kept) clean.
