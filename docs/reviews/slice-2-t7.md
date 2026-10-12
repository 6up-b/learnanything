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

---

## What was built

Commits on `slice-2/t7`, base `aa9320f8`:
- `1d7b92fe`: the backend change and its tests;
- `63b6733d`: the frontend;
- `f76c8b66`: the configuration reference.

**1. Item-text neighbours on the knowledge map** (`get_knowledge_map`).
- **When text decides.** An item's four spokes are ranked by the store's mean-centred cosine over stored `item/stem` vectors when both hold:
  - its current stem has a vector for `embedding.model` (`retrieval-document`, the Phase 1 backfill's prefix);
  - enough other items do too to fill the same number of spokes as today.
- **Otherwise** the item keeps today's blended neighbours, unchanged.
- **New fields:**
  - each point gets `neighborBasis` (`item_text` or `facet_graph`);
  - each item-text neighbour gets `similarity`, and `distance` keeps its old meaning (the blended distance);
  - the snapshot gets `itemTextNeighbors` = `{enabled, modelId, stems, embedded}`.
- **What stays untouched:** coordinates, stress, `preview_knowledge_map`, the facet field (well depth, demonstrated beads, decay markers, Ready fog) and every belief field. Tests assert this byte for byte.

**2. The store function** `nearest_among_current()` (`src/learnloop/db/stores/embedding_vectors.py`, appended at the end).
- It computes all-pairs top-k with `retrieve()`'s own similarity.
- **Partial coverage** is explicit: only records whose stored content hash is current take part, and the result's keys name them.
- **Memory** is bounded by 256-row score blocks.
- **Ties** go to the smaller ID.

**3. The sidecar helper** `src/learnloop_sidecar/handlers/item_text_neighbors.py`.
- It reads the `item/stem` recipe hashes and one read-only connection.
- numpy and the store are imported only when the switch is on and there are at least two stems, so sidecar start-up is unchanged.
- It never builds a client.

**4. The kill switch** `embedding.map_neighbors_enabled` (default `true`).
- **Off:** the payload equals today's except for the `neighborBasis` label and the summary (tested).
- **Independent of `embedding.enabled`:** that switch governs remote calls, and the map makes none.
- **Fingerprint:** the `mvp-0.9` defaults fingerprint is updated with a decision comment.

**5. UI.** The strata item panel gets a "Nearest items" section.
- **Each neighbour** shows its title, links to the inspector, and shows either `sim` (wording) or `d` (blended distance).
- **The caption** names the basis:
  - "by similar wording · stored <model> vectors, K/N items embedded · not a same-skill match", or
  - "by shared facets + concept graph", plus coverage when other items are embedded.
- **Settings → Embeddings** shows the switch read-only.
- **Why the panel was needed:** before T7, the shipped neighbours were rendered nowhere (the chronicle that drew them was removed in `d79bacf5`). Without it, the track would have had no visible effect.

## Gate results

| Check | Result |
|---|---|
| `uv sync --extra dev`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | **6 kept, 0 broken** |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **6,159 passed**, 14 warnings (173.9 s) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **62 passed**, 6,097 deselected |
| `npm install`, `npm run typecheck` | ok, no type errors |
| `npm test` (vitest) | **35 passed** (11 files) |
| `npm run frontend:build` | ok |
| DB reference | Schema unchanged (no migration). The config leaf changed, so the generator ran. I kept only the six notes the leaf touches and hand-updated two leaf counts. `db_validate_reference.py` reports **48 errors, the same 48 that `main` at `aa9320f8` reports**: stale source-line anchors in the scheduler, probe and other sections. T7 adds none. Before the targeted regeneration it added 18 |
| New and changed targeted tests | `tests/test_knowledge_map_text_neighbors.py` 5 passed; 2 new store tests in `tests/test_embedding_store.py` |
| Mutation check | Each injected bug fails at least one test, 6 of 6: short lists allowed, self not excluded, stale hashes accepted, kill switch ignored, centring removed, `distance` replaced by text distance |

The suites ran on `63b6733d`. `f76c8b66` changes generated docs only.

## Manual run on a fixtures-local copy (fakes, no network)

**Setup:**
- `fixtures/linear_algebra` (this worktree's tracked copy) copied with `learnloop.db.copies.copy_tree_with_databases` to `fixtures-local/t7-linear-algebra`;
- `[embedding] enabled = true, backfill_enabled = true, dimensions = 64` added to the copy.

**Commands:**
- the owner's dry-run command (below): 59 pending stems, 2 calls, about 22,199 tokens, an estimated $0.00022;
- then `backfill_embeddings` with a local hashed bag-of-words fake client;
- then `get_knowledge_map` with the switch on and off.

The script is `t7_manual_run.py` in the session scratchpad; it isn't committed.

**Results:**
- **Backfill:** `status: complete`, 59 of 59 stems embedded.
- **Summary:** `itemTextNeighbors = {enabled: true, modelId: qwen/qwen3-embedding-8b, stems: 59, embedded: 59}`.
- **Bases:** of 99 map items, 59 are `item_text` and 40 are `facet_graph`. The 40 are retired items: the recipe skips them, but the map has always shown them.
- **Switch off:** all 99 are `facet_graph`.
- **Geometry:** coordinates, stress and the facet field are identical with the switch on and off.
- **Overlap:** a mean of 0.19 of the wording spokes are also facet/graph spokes, and 0.53 of the wording spokes point into another learning object. The lens is genuinely different, so it adds information rather than repeating the layout.
- **Example:** `pi_axiom_addition_integer_difference` ("On V=Z, define m⊕n=m−n …") gets four other proposed-addition audits, with sims from +0.31 to +0.46.

## Invariants

- **No calls at render.** Asserted with embeddings fully enabled:
  - every client factory patched to raise (`ready_client_for_task`, `client_for_provider`, `make_ai_provider_client`, `make_ai_provider_client_from_profile`, `OpenAIEmbeddingProviderClient.__init__`);
  - a model-call observer that records nothing;
  - an `iterdump()` of the database identical before and after.
- **Replay and rebuild:** untouched, with no tables, replayers or projections.
- **Nothing writes evidence or certification.** The neighbours reach no scheduling, scoring or evidence path. Only the UI reads them.
- **R1/R2 (embeddings rank, never decide):**
  - no identity, novelty, difficulty or isomorphism claim; the caption says "not a same-skill match";
  - no `judgment_ledger` task, because nothing is decided;
  - no hand-set cosine cutoff: the only threshold is "enough embedded items to fill the same number of spokes".
- **R3:** canonical stems only, via the existing recipe.
- **Grading stays learner-blind:** grading isn't touched.

## Deviations

1. **The spec offered two options; I took "source of the four shown neighbours", not a third distance term.** A third term would:
   - move the layout whenever a backfill ran or an item was added;
   - put a partially covered term into the one distance matrix the MDS and stress share;
   - change `preview_knowledge_map`.

   This choice also keeps the `knowledge_map.py` diff to the neighbour step. It doesn't overlap Phase 2's untested-map hunk in `_facet_field` on `integrate/slice-a-2-3`.
2. **No new report command.** Slice 2 §13 lists no T7 report. Coverage is in the map payload and shown in the UI. The backfill dry-run is the owner's coverage check, since it reports `cached` and `pending` stems. The manual run above stands in for "the report generates with fakes".
3. **A UI panel was added.** Without it, nothing would show the neighbours.
4. **No algorithm successor.** No persisted meaning changes and nothing served changes, so `mvp-0.9` stays. The defaults fingerprint is updated with an explicit comment, following Phase 1's precedent (playbook step 4).
5. **The documentation regeneration was targeted,** not repo-wide, to avoid a several-hundred-file conflict with `integrate/slice-a-2-3`'s own regeneration. The module and desktop catalogs aren't regenerated:
   - `module_validate.py` already reports 10 modules without notes on `main`; this branch adds `item_text_neighbors.py` as the 11th;
   - `desktop_validate.py` crashes on `main` with `KeyError: 'TypeScript/screens/today'`.

   Both belong in the integrator's bulk regeneration.

## Files touched

- **Backend:**
  - `src/learnloop/config/schema.py`
  - `src/learnloop/config/template.py`
  - `src/learnloop/db/stores/embedding_vectors.py`
  - `src/learnloop_sidecar/handlers/item_text_neighbors.py` (new)
  - `src/learnloop_sidecar/handlers/knowledge_map.py`
- **Tests:**
  - `tests/test_knowledge_map_text_neighbors.py` (new)
  - `tests/test_embedding_store.py`
  - `tests/test_sidecar_contract.py`
- **Frontend:**
  - `apps/learnloop-tauri/src/api/dto.ts`
  - `apps/learnloop-tauri/src/screens/KnowledgeMapScreen.tsx`
  - `apps/learnloop-tauri/src/screens/knowledgeNeighbors.ts` (new)
  - `apps/learnloop-tauri/src/screens/knowledgeNeighbors.test.ts` (new)
  - `apps/learnloop-tauri/src/screens/SettingsScreen.tsx`
  - `apps/learnloop-tauri/src/screens/SettingsScreen.test.tsx`
- **Docs:**
  - `docs/learnloop-architecture-vault/_scripts/db_generate_reference.py`
  - six reference notes (the `embedding` and `schema_version` configuration sections, the configuration field catalog, `Configuration.md`, `Database.md`, and the `embedding_vectors` table note)
  - this file

## Migrations

None.

## Owner-run commands

The only paid step is Phase 1's existing backfill, run once for item stems. It needs `OPENROUTER_API_KEY` in `~/.config/learnloop/settings.env` (blocker B6).

1. **Dry-run.** No client is built and nothing changes. It prints the pending stems and the cost estimate:

   ```bash
   uv run learnloop embeddings backfill --vault <vault> --record-kind item/stem --dry-run --json
   ```

   The default caps are 100 candidates and 100,000 tokens. Raise `--max-candidates` or `--max-tokens` if the dry-run reports `over_budget`.
2. **Enable the two switches** under `[embedding]` in `learnloop.toml`:

   ```toml
   enabled = true
   backfill_enabled = true
   ```
3. **Run the backfill:**

   ```bash
   uv run learnloop embeddings backfill --vault <vault> --record-kind item/stem --json
   ```

   It is resumable, and a rerun embeds only new or edited stems.
4. **Look.** In the app, open Knowledge map → strata → hover an item → "Nearest items". Items added or edited after the backfill keep facet/graph neighbours until the next backfill run.
5. **Kill switch.** Add `map_neighbors_enabled = false` under `[embedding]`. The map then returns today's neighbours, and Settings → Embeddings shows "facets + concept graph".

## Merge notes

- **Fingerprint conflict.** `DEFAULTS_SNAPSHOT_BY_ALGORITHM["mvp-0.9"]` conflicts with `integrate/slice-a-2-3`, which also changes it. After merging both, recompute it with `uv run python -c "from learnloop.config.template import effective_defaults_fingerprint as f; print(f())"` and merge the two comments.
- **Reference docs.** Rerun `db_generate_reference.py` on the merged tree. The function text for the new leaf is in the generator.
- **`knowledge_map.py`.** My hunks are the neighbour loop, the point dict, the return dict, one import and the docstring. Phase 2's hunk is in `_facet_field`.

## Open questions

1. **Should the switch also follow `embedding.enabled`?** As built, stored vectors still rank the spokes after the owner turns remote embeddings off, because nothing leaves the machine. The alternative treats `enabled = false` as "no embedding features at all". Recommended: keep them independent.
2. **Should the UI show the similarity number?** `sim` is centred on this vault's mean, so its scale is relative. It is shown, with a tooltip saying so. Recommended: keep it, or drop the number and show rank only if it confuses.
3. **Retired items on the map.** The map shows retired items: 40 of 99 in `linear_algebra`. They can't have stem vectors, so they keep facet/graph neighbours. This predates T7 and is outside its scope; flagged only.
4. **Skeleton vectors.** When PF-b's `item/skeleton` vectors exist, should the spokes prefer skeletons over stems? R3 favours LLM-written text, and a skeleton clusters by solution method rather than wording. Recommended: a follow-up once skeletons are backfilled, behind the same switch, with the caption changed to "similar solution steps".
