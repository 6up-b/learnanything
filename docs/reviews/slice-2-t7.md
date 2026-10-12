# Slice 2 T7: knowledge-map neighbours from item text (display only)

Branch `slice-2/t7`, worktree `learnanything-t7`, base `aa9320f8`.
Spec: `docs/specs/spec_embedding_consumers_v1.md` §10, with R1–R6 (§1) and §4.
Handoff: `docs/specs/implementation_handoffs.md`, "Slice 2 T4, T5, T7, T8", filled in for T7.
The prerequisite "previous track's report reviewed" is waived (owner, 2026-10-12; `implementation_goal.md` §1a).

## Plan (written before coding)

**What T7 changes.** The four neighbours shipped per item point (`get_knowledge_map`
→ `points[].neighbors`) are ranked by item-text similarity from stored
`item/stem` vectors when those exist. Otherwise they stay today's neighbours (the
0.6 facet-cosine + 0.4 concept-geodesic blend). The spec allows a third distance
term or "the source of the four shown neighbours". I take the second:

- The map's **geometry stays untouched**: the blended distance matrix, the MDS
  coordinates, the stress, `preview_knowledge_map` and the whole `facet_field`
  (well depth, demonstrated beads, decay markers, Ready fog). A third term would
  move every point whenever a backfill ran or an item was added, and would
  mix a partially covered term into one matrix.
- The layout already shows facet/graph proximity, so the spokes add a second,
  different lens: which items read alike.

**Files to add or change**
- `src/learnloop/db/stores/embedding_vectors.py`: add `nearest_among_current()`,
  all-pairs top-k by the store's own mean-centred cosine. Unlike `retrieve()`, it
  tolerates partial coverage: only records whose stored content hash is current
  take part, and the result's keys say which ones did. Appended at the end of the
  module, so nothing existing changes.
- `src/learnloop_sidecar/handlers/item_text_neighbors.py` (new): reads the current
  `item/stem` manifest (`learnloop.vault.embedding_recipes`) and the stored vectors
  for `embedding.model` / `retrieval-document`. It never builds an embedding client.
  numpy and the store are imported lazily, so sidecar start-up is unchanged.
- `src/learnloop_sidecar/handlers/knowledge_map.py`: a small change to the neighbour
  step. It adds a per-point `neighbor_basis` (`item_text` or `facet_graph`) and a
  top-level `item_text_neighbors` coverage summary. Each item-text neighbour keeps
  `distance` (still the blended facet/graph distance) and adds `similarity`.
- `src/learnloop/config/schema.py`: kill switch `embedding.map_neighbors_enabled`
  (default `true`).
- `src/learnloop/config/template.py`: the effective-defaults fingerprint for
  `mvp-0.9`, with a decision comment (display-only; same precedent as Phase 1).
- `docs/learnloop-architecture-vault/_scripts/db_generate_reference.py`: a function
  text for the new config leaf, so the next regeneration describes it properly.
- Frontend: `apps/learnloop-tauri/src/api/dto.ts` and `KnowledgeMapScreen.tsx`.
  The strata item panel gets a "Nearest items" section with an honest caption:
  "similar wording", with the model and coverage, or "shared facets + concept graph".
  Today the shipped neighbours are rendered nowhere, so without this T7 would have
  no visible effect.

**When item text is used.** An item uses item-text neighbours only when two things
hold:
- its current stem has a stored vector;
- enough other items do too to fill the same number of spokes as today
  (`min(4, items − 1)`).

Otherwise the item keeps today's neighbours. This covers stale hashes after an edit,
items added since the last backfill, a model switch, retired items and a vault with
no vectors, which is the default because embeddings are off. Each point says which
basis it used, and the summary gives the model and the embedded/total counts.

**Migrations:** none. No tables, so `table_roles` and the replayers are unchanged.

**Algorithm successors and kill switches:**
- No algorithm successor: nothing persisted changes meaning, and nothing served
  (queue, scheduling, scoring, evidence, certification) reads the neighbours.
  `algorithm_version` stays `mvp-0.9`.
- Kill switch: `embedding.map_neighbors_enabled = false` restores today's
  neighbours exactly. The output then equals the base commit's except for the
  `neighbor_basis` label and the summary.
- It is independent of `embedding.enabled`, which governs remote calls; the map
  makes none.

**Spend caps and model routes:** none. Zero model or embedding calls at map render,
asserted by tests with patched client factories and a model-call observer.
The only paid step is Phase 1's existing `learnloop embeddings backfill`,
which has its own dry-run and caps.

**`judgment_ledger` writes:** none. T7 ranks for display and decides nothing (R1:
embeddings may rank and supply context). No "same / different" task, so §4's
blocking-cutoff rule doesn't apply, and no cosine cutoff is hand-set.

**Tests:**
- new `tests/test_knowledge_map_text_neighbors.py`:
  - ranking matches the store's `retrieve()` ordering;
  - per-item fallback for stale, missing and other-model vectors and too-small
    coverage;
  - the kill switch;
  - geometry and the facet field are byte-identical with and without vectors;
  - no client construction or model calls, even with embeddings enabled;
  - no database writes;
  - determinism;
- store tests for `nearest_among_current()` in `tests/test_embedding_store.py`;
- the sidecar contract test's key set (`tests/test_sidecar_contract.py`);
- the defaults fingerprint (`tests/test_config_refactor.py`).
