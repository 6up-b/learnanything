# Slice 2 T7: Codex review and fixes

Branch `slice-2/t7`, worktree `learnanything-t7`. Codex job `20261012-010251-v7PRgl`
reviewed `aa9320f8..f5e2020d` (implementer's file: `docs/reviews/slice-2-t7.md`). It
returned three findings, two Medium and one Low, and ran partial validation only (no
full suites). Fixes are on top of `f5e2020d`.

## Findings

| ID | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | Medium | Live neighbour ranking bypasses the required algorithm successor | **Rejected** | — | Conflicts with the spec, the playbook's scope and the owner's frictionless-defaults decision. The visible change and zero learner-state effect were checked (see F1 below) |
| F2 | Medium | A partially backfilled replacement model becomes active immediately | **Fixed** | `9cf5684a`, docs `030f3be9` | `test_interrupted_replacement_backfill_keeps_the_activated_model`, `test_a_previous_model_ranks_alone_and_is_named`, `test_ranking_model_moves_only_after_a_full_re_embed` (8 cases), `test_current_records_by_model_counts_current_identities_per_model`; caption test in `knowledgeNeighbors.test.ts` |
| F3 | Low | Coverage falsely reports an embedded singleton as unembedded | **Fixed** | `9cf5684a` | `test_coverage_counts_an_embedded_singleton[False]` (one-item vault), `[True]` (other items retired) |

No High findings, so no Codex re-review is needed (`implementation_goal.md` §2 step 4).

### F2: replacement model activates before its full re-embed (fixed)

**Reproduced** with a failing test on `f5e2020d`, then fixed. The defect was wider
than Codex's scenario:
- **Right after `embedding.model` changes,** with no B vectors yet, every item lost its
  item-text spokes. The map fell back to facet/graph neighbours even though A's vectors
  were complete and current.
- **At five of six B stems,** those five items got B-ranked spokes, as Codex reported.
  The narrowed test failed at that step too.

Both break Slice 2 §4: "a full re-embed … before retrieval moves to the new `model_id`".

**Fix.** `embedding.model` stays the model the backfill embeds with. The model that ranks
the spokes is now derived from stored coverage in `ranking_model()`
(`src/learnloop_sidecar/handlers/item_text_neighbors.py`):
- **When `embedding.model` ranks.** Once its current stems include every current stem of
  each other stored model. A completed backfill guarantees this, because it embeds every
  current stem.
- **Until then,** the other model with the most current stems keeps ranking on its own,
  with ties going to the smaller model ID. Vectors from two models never mix.
- **After activation,** an edited or added stem is missing for every model alike. The
  active model stays, and only that item falls back. This keeps the graceful per-item
  degradation Codex asked to preserve.
- **The coverage query** is `current_records_by_model()`, appended to
  `src/learnloop/db/stores/embedding_vectors.py`. It reads identities only, never vectors.
- **Honest label.**
  - The summary gains `pendingModel: {modelId, embedded} | null`.
  - `modelId` now names the model that actually ranks.
  - The caption adds, for example, "· other/embedder: 4/6 re-embedded, used once complete".

**Why derived and not a second config field.** Codex suggested separating the backfill
model from an approved retrieval model. Deriving the approved model from stored coverage
does that without adding an owner step, in line with frictionless defaults. The owner
changes `embedding.model`, runs the backfill, and the map moves when the backfill
completes.

**The benchmark half of §4.** §4 says the benchmark reruns are there to re-derive the
blocking cutoffs. The map's ranking uses no cutoff (R4), so for this consumer the rerun
has nothing to re-derive. Also, the shared `learnloop embeddings compare` harness isn't
on `main` yet (Slice A Phase 5a builds it). Any T7 cutoff in future would be keyed by
model and gated there.

**Changed tests.** `test_other_models_and_prefixes_are_ignored` asserted that vectors of
any other model leave the map untouched. Under §4, a previous model's vectors keep
ranking until the replacement catches up, so that assertion was the defect. The test is
split into:
- `test_other_task_prefixes_are_ignored`, with its original assertion;
- `test_a_previous_model_ranks_alone_and_is_named`: the previous model ranks alone, and
  the configured model's two stored stems don't mix in.

### F3: embedded singleton counted as unembedded (fixed)

**Reproduced:** `{stems: 1, embedded: 0}` both for a one-item vault with a stored vector
and for a vault whose other items are all retired.

**Fix.** The early return for fewer than two stems is gone (only zero stems returns
early). `embedded` is now a field counted from `current_records_by_model()` for the
ranking model, whether or not there are enough stems to rank. The singleton point keeps
`facet_graph`, because it has nobody to rank against.

### F1: algorithm successor for the neighbour ranking (rejected)

The change Codex describes is real and intended: an existing vault with current stem
vectors shows item-text neighbours as soon as T7 is installed. A successor is still the
wrong tool here, for these reasons:

1. **The playbook's scope.**
   - Successors are for changes to "scoring, scheduling, projection, or admissibility
     semantics", and step 1 asks "whether the change alters persisted meaning".
   - The spokes are computed at render time from stored vectors. They are never
     persisted, and no scheduling, scoring, evidence, certification or projection path
     reads them.
   - `algorithm_versions.py` says version names "gate persistence formats as well as
     domain behavior". A T7 version would gate neither.
   - Step 3's upgrade function would have nothing to prepare.
2. **The spec decided this.**
   - Slice 2 §2's track table gives T7's default authority at landing as **"live
     (display only)"**. Where a track needs a successor, that same column says so: PF's
     "retention key live if its replay favours it (successor + kill switch)".
   - The handoff's T7 rule is "display only, with zero effect on learner state".
   - `implementation_goal.md` §1a lists the successors the owner upgrades by command:
     Slice 1's split cutover, T1's recurrence successor, and Phase 3b. T7 is not on that
     list.
   - The T6 handoff covers a larger change to what is shown and says "Retrieval is
     context, so no successor is needed unless something persisted changes meaning".
3. **Precedent on `main`.**
   - The merged daily-loop fixes (`docs/reviews/daily-loop-bugs.md`) changed the served
     queue itself, recorded as "Successor? No: serving only", because nothing replayed
     or persisted changed meaning.
   - Slice A Phases 1, 2 and 3 each updated the `mvp-0.9` defaults fingerprint with a
     decision comment and no successor. T7 did the same (playbook step 4's
     "version/fingerprint decision").
4. **The owner's decision in force.** "Honest labels, generous defaults; live changes
   behind kill switches, no shadow stages by default."
   - Gating the panel behind an owner-run vault upgrade would make it a shadow stage:
     every vault would show facet/graph neighbours until a command with nothing to
     migrate was run.
   - The kill switch `embedding.map_neighbors_enabled = false` restores today's
     neighbours exactly, which is tested.
   - Item-text spokes only appear after the owner's own paid backfill, because
     `embedding.enabled` and `backfill_enabled` default to false.
5. **Later stages.** A display-only successor would claim the next version label
   (`mvp-0.10`), which T1, Slice 1 S1.3 and Phase 6 need. That would force a relabel
   across parallel branches.

**Verification Codex asked for (zero learner-state deltas on a shadow rebuild).** Both
copies are under `fixtures-local/` and made with `learnloop.db.copies`:
- **The two copies:**
  - `t7-linear-algebra`: the implementer's copy, with 59 stored stem vectors;
  - `t7-review-novectors`: the same copy with every vector deleted.
- **Command:** `learnloop rebuild --shadow --json` on each.
- **Result:** identical `learner_state_diff` (`{facet: 2, mastery: 7, schedule: 48}`).
  These deltas are the `mvp-0.8` fixture copy's own replay drift, and they are the same
  with and without vectors. The live database hash was unchanged in both runs.
- **Geometry:** the manual run below shows map geometry and the facet field identical
  across a model switch. The tests assert them byte-identical with and without vectors.

**Claims in the implementer's file that don't hold, corrected here:**
- **Deviation 4, "nothing served changes".** The map's displayed neighbours do change
  live, by design. What doesn't change is anything served to the learner (queue,
  scheduling, scoring, evidence) or anything persisted. The plan section's wording
  ("nothing served … reads the neighbours") is accurate.
- **"Coverage counts items with current stored vectors"** didn't hold for singletons.
  That is F3, now fixed.

If the owner wants T7 behind a successor anyway, that's an override at the T7
checkpoint (open question 1).

## Manual run (fixtures-local copy, fake vectors, no network)

**Setup.** `fixtures-local/t7-review-switch` is a backup-API copy of the implementer's
`t7-linear-algebra`, which has 59 `qwen/qwen3-embedding-8b` stem vectors at 64 dimensions.
The script is `t7_review_switch.py` in the session scratchpad and is not committed.
`embedding.model` was set to `fake/replacement-embedder`, then random 64-d vectors were
stored for it in steps.

| B stems stored | `modelId` ranking | `pendingModel` | Bases (text / facet) | Spokes |
|---|---|---|---|---|
| before switch | qwen | null | 59 / 40 | — |
| 0 / 59 | qwen | B, 0 | 59 / 40 | identical to before |
| 30 / 59 | qwen | B, 30 | 59 / 40 | identical to before |
| 58 / 59 | qwen | B, 58 | 59 / 40 | identical to before |
| 59 / 59 | **B** | null | 59 / 40 | all 59 re-ranked by B |
| switch off | — | null | 0 / 99 | facet/graph |

The 40 facet/graph items are retired, as in the implementer's run. Coordinates, stress
and the facet field were identical across the whole sequence.

## Gate results

Run on `030f3be9` (code is the same as `9cf5684a`).

| Check | Result |
|---|---|
| `uv sync --extra dev`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | **6 kept, 0 broken** |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **6,172 passed**, 14 warnings (164.3 s); was 6,159 |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **62 passed**, 6,110 deselected (35.4 s) |
| `npm install`, `npm run typecheck` | ok, no type errors |
| `npm test` (vitest) | **36 passed** (11 files); was 35 |
| `npm run frontend:build` | ok |
| DB reference | Schema unchanged (no migration). The generator's text for `embedding.map_neighbors_enabled` changed. I regenerated and kept only `Config - embedding.md`, the one note whose content changed; the others differed only in commit stamps. `db_validate_reference.py`: **48 errors**, the same 48 that `main` at `aa9320f8` reports (stale source-line anchors elsewhere). None are T7's |
| Targeted | `tests/test_knowledge_map_text_neighbors.py` 17 passed, was 5; `tests/test_embedding_store.py` 22 passed (1 new); with the contract and config tests, 143 passed |

## Owner notes

**Switching embedding models later:**
1. Change `embedding.model`.
2. Run the existing backfill: dry-run first, then the real run (commands are in
   `slice-2-t7.md`).

The map keeps the previous model's spokes until the new model's backfill completes, and
the item panel shows its progress.

## Open questions

1. **F1 override.** Should T7's neighbour source sit behind an algorithm successor and an
   owner-run upgrade after all? Recommended: no. Keep it live behind
   `embedding.map_neighbors_enabled`, as Slice 2 §2 specifies.
2. **Benchmark vectors (for the integrator of Phase 5a's compare harness).**
   `ranking_model()` counts every stored `item/stem` `retrieval-document` vector.
   - **The risk:** the harness might store candidate-model vectors under that same
     prefix, and a candidate might cover stems that `embedding.model` lacks. That
     candidate would then rank until the next configured backfill. It would be labelled
     honestly, but it isn't intended.
   - **Recommended:** the harness keeps its candidates out of the `retrieval-document`
     scope, for example under its own task prefix.
