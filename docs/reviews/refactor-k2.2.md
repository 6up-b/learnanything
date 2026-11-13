# Refactor K2.2: the outer caches defer to the rendered request

Branch `refactor/k2.2-outer-caches`, based on main `9eb0194c2c` (K2.1's checkpoint helper and D3 landed). Step K2.2
of arc K (`docs/specs/refactor_strategy_v3.md` §2.17), specified in `docs/reviews/k2-ingestion-strategy-2026-11-11.md`
§3.2 from the K2 map's KM1 (§3.4 of `docs/reviews/k2-ingestion-map-2026-11-11.md`). Structure track, with one stated
consequence: a cache that answered on a label where the rendered request had changed stops answering there.

## Problem

Two of the three outer cache layers answered before the per-call checkpoints that K2.1 keyed on the rendered
request, and they answered on labels:

- **Inventory row** (`source_unit_inventories`, `reusable_unit_inventories`): unit, semantic hash, schema version,
  prompt label, provider and model. A prompt edit without a label bump reused the old inventory; a row recorded under
  another label with the same rendered request was not reused (its windows were read from their checkpoints, so no
  call, but a second row was written and the synthesis manifest moved).
- **Completed shard** (`synthesis_shard_results`, `_shard_checkpoint_key`): a hand-rolled hash of the synthesis prompt
  label, settings, brief, registry index, exam profile, the shard's inventories and its position. Every one of those is
  rendered into the shard's first pass, so the old key never under-reused; but it left out the task text and the
  schema, so a prompt or schema edit under an unchanged label replayed the old shard.

The third layer, the completed run (the manifest), is K2.3's and is untouched.

## What changed

| File | What |
|---|---|
| `content/synthesis/source_unit_inventory.py` | `inventory_row_key(provider, model, schema_version)`: the request key of the inventory prompt rendered over an empty context, under the schema version (as the window key names it) and provider and model, purpose `inventory_row`. A fresh row records it in `usage_json["request_key"]` (`INVENTORY_ROW_KEY_FIELD`); a binding row (a reuse rebound to another reading or revision) copies its origin's key, and a binding of a row without one gets none. `prepare_unit_inventory` passes the key to the reuse query. Module docstring updated |
| `db/repositories.py` | `reusable_unit_inventories(..., request_key)`: a row with a recorded key matches only that key, whatever its label, provider and model columns; a row without one matches those columns as before. `save_synthesis_shard_result`'s docstring names the new key |
| `content/synthesis/source_set_synthesis.py` | `_run_synthesis` files each completed shard under its base pass's request key (the `ModelCheckpoint.key` it already computed for the preflight); `_shard_checkpoint_key` deleted (and the now unused `SOURCE_SET_SYNTHESIS_PROMPT_VERSION` import). The two preflight loops became one; `_SavedAnswers` gets the same keys in both lists, so D-9's discard drops the shard row and the pass checkpoint as before |
| `tests/test_outer_cache_keys.py` | new: the fail-first tests and guards below |
| `tests/identity_pins_helpers.py`, `tests/goldens/` | the new site `K2.2a.row_key`; `SourceUnitInventoryContext`'s shape lists K2.2a beside A15 |

## Judgment calls

1. **The row key is not the first window's key** (the strategy's wording). A window's key carries the window's view,
   whose span ids are per extraction and whose split follows the input budget, and its context carries the request's
   role and profile. Compared against the current request, it would end three reuses the cache makes on purpose and
   tests hold: across revisions and readings (`test_semantic_inventory_cache_rebinds_across_revisions`,
   `test_composite_inventory_cache_rebinds_all_member_spans_across_revisions`), and a `combined` row for a narrower
   request under another role (`test_combined_inventory_reused_for_semantic_request`). So the row key renders the same
   template over an empty context: the instructions, their label, the schema version, provider and model. The unit's
   text stays named by the semantic hash (designed to ignore span ids and layout), its role and profile by the profile
   rule. A change to the view's code (which blocks are omitted) that leaves the semantic hash alone is not caught at
   this layer; the window keys still catch it after a miss.
2. **Settings in the row key are provider and model only.** A cached unit is decided before any client is built, on
   purpose (`test_inventory_merge_parallel::test_full_inventory_cache_hit_never_constructs_provider`: a hit starts no
   provider; building the client is a readiness probe). The full settings (endpoint, reasoning effort, thinking mode,
   response format) exist only once a client does, so a key with them could not be checked on the job's first pass
   without either breaking that property or re-deriving `model_settings` from config. This leaves KM1's settings half
   at this layer open: ledger K2-8.
3. **Rows without a key keep the label match**, as the strategy says, so nothing is orphaned. On the owner's existing
   vaults every row is such a row, so a prompt edit under an unchanged label is still answered by them until the label
   moves. Treating them as misses would re-run each unit, at no cost where its window checkpoints hold and paid where
   they don't. Recorded in K2-8 as the owner's call.
4. **The query filters in SQL** (`json_extract` on `usage_json`, which every writer stores as JSON) rather than in
   Python, so the reuse rule is one statement in the one reuse query the strategy names.
5. **The shard key is the pass key itself**, not a prefixed variant: the two live in different tables, and the shard
   answers exactly when its first pass's checkpoint would. Old rows (`shard:` + hex) are never read again; they stay in
   the table (a `RAW_LEDGER`, nothing deletes them). Their passes' checkpoints answer a rerun at zero calls, the span
   round's too when its first answer is replayed (shown on the base by deleting the rows, below).
6. **The binding row carries its origin's key** (a reuse is the same answer to the same request). Without it, a
   rebinding within a revision (the `ON CONFLICT` update of the same row) would strip the key from the row it rebinds.
7. **No change to what synthesis chooses** (`best_inventory`'s label preference, K3.1) or to the collection build's
   "any row" newness (K3.3): out of the strategy's files for this step; see open items.
8. **D-16 is not in reach.** A wholly rejected run is reused by the completed-run lookup (the manifest), which is
   K2.3's layer; neither layer changed here reuses a run. Left for K2.3.

## Fail-first evidence

`tests/test_outer_cache_keys.py`, run against the base sources before the source change (only the test file in the
tree): 4 failed, 4 passed.

| test | base | tip |
|---|---|---|
| `test_an_inventory_row_answers_a_request_recorded_under_another_label` (under-reuse) | `cache_hit` False (0 calls, windows read from their checkpoints, a second row written) | hit, the same row, no new row |
| `test_an_inventory_prompt_edited_under_the_same_label_is_paid_once` (wrong reuse) | `cache_hit` True, 1 call in all | the edit pays 1 call, the next run hits; one row |
| `test_an_inventory_job_pays_again_for_an_edited_prompt_and_not_for_an_unchanged_one` (wrong reuse, job path) | the edited job hits (`cache_hits` 1) | 0, then 1; 2 calls in all |
| `test_a_shard_prompt_edited_under_the_same_label_is_paid_once` (wrong reuse) | 2 calls (both shards replayed) | 4 (both paid again, `reused_shards` 0) |

Guards, green on both: `test_a_changed_inventory_model_is_paid_and_not_answered_by_the_old_row`,
`test_an_inventory_row_from_before_the_request_key_keeps_its_label_match`,
`test_a_shard_answers_from_its_pass_checkpoint_without_its_completed_row` (the strategy's "a shard reruns from its
pass checkpoint with zero calls": the shard rows deleted, 0 calls, `reused_shards` 0),
`test_an_unchanged_shard_is_read_from_its_completed_row`. The shard layer has no under-reuse test that can fail: every
input of its old key is rendered into the first pass (above), so no request was under-reused there.

The first commit (`d2bf99f1de`) adds the whole test file with the inventory change; its two shard wrong-reuse checks
go green at the next commit.

## Assertions changed

None. No existing test was edited.

## Pins

No existing pin moved (`tests/test_identity_pins.py` passed with the source change before any `--write`). The old
shard key had no pin (the strategy's "the shard key pin is bumped" assumed one); the new shard key is the synthesis
pass key, already pinned as A14. One new site, `K2.2a.row_key` (the inventory row key): `--write` added its line to
`identities.toml` and `"K2.2a"` to `SourceUnitInventoryContext`'s `sites` in `identity_shapes.toml`. Stored rows:
inventory rows without a key keep being read (by label); shard rows under the old key are no longer read.

## P-spend

A synthetic vault (`_setup_two_chapters`: one textbook, two inventoried chapters, two shards), the house fakes
counting calls, each "build" = both units' `run_unit_inventory` then `create_study_map`. A throwaway test, run on the
base (`git checkout 9eb0194c2c -- src`, then back) and on the tip, deleted, never committed. Calls are inventory /
synthesis passes / epigraphs; the first inventory (2 calls) is paid inside the helper on both.

| run | base | tip |
|---|---|---|
| first build | 0 / 2 / 1 | 0 / 2 / 1 |
| rebuild, nothing changed | 0 / 0 / 0, run reused | 0 / 0 / 0, run reused |
| rebuild after a prompt-label change with identical rendered text (the label rows record and synthesis prefers, not the rendered one) | 0 / 0 / 1: not re-paid but wrongly missed: both units miss, their windows are read from checkpoints, two new rows, the manifest moves, a new run (shards reused) pays a new epigraph batch | 0 / 0 / 0: both rows answer, no new row, the run is reused |
| rebuild after the inventory prompt's text is edited under the same label | 0 / 0 / 0: wrongly reused (old inventories) | 2 / 0 / 0: both units paid once; **the run is still reused** (below) |
| rebuild after the synthesis prompt's text is edited under the same label | 0 / 0 / 0, run reused | 0 / 0 / 0, run reused (below) |
| rebuild after one unit's text changed (a new reading of the revision) | 1 / 2 / 1 | 1 / 2 / 1 |

Notes:
- Every label is rendered into its prompt's header (`render_structured_prompt`'s `prompt_version:` line), so a label
  change in code always changes the rendered request; the only labels that are not rendered are the inventory row's
  recorded columns. The label scenario is therefore run as the label rows record and synthesis prefers
  (`SOURCE_UNIT_INVENTORY_PROMPT_VERSION` in `source_unit_inventory`) changing while the rendered prompt does not.
- The text change: only the changed unit's inventory is paid, but both shards are paid again on base and tip, because
  each shard's entries name the reading (`extraction_id`) their citations resolve against, so the unchanged unit's
  shard request changed too. Not this step's.
- **What the manifest (K2.3) leaves:** in both prompt-edit rows the completed run answers before any inventory row or
  shard is consulted, because the manifest records labels, not rendered requests. On the tip the edited inventory
  prompt is paid (2 calls) and the rows are updated in place (same ids), but synthesis does not read them until the
  manifest moves for another reason; the shard fix only takes effect once a run is not reused (a failed or new run, as
  in the tests). K2.3 removes that lookup.
- After the inventory prompt edit is reverted, the rows (now keyed on the edited request) miss and the windows are
  read from their original checkpoints at no cost: the outer layer defers to the checkpoint.

## Vault

`Workflows/Import Canonical Sources.md` (the paragraph after the checkpoint paragraph): the two outer layers and what
each matches; the completed run as the one label-keyed layer left. Generated references regenerated once after the
source commits.

## Ledger

- **K2-4** (KM1, KM2): the inventory row and the completed shard fixed here; the completed run and KM2 remain, queued
  for K2.3.
- **K2-8** (new, open, due at arc K's close): an inventory row's key carries provider and model only, so a change of
  the route's endpoint or reasoning settings under the same provider type and model is still answered by the old row;
  rows without a key keep the label match.

## Gates

See the report for the tip's gate results (targeted tests, `lint-imports`, `ruff`, the four vault validators,
`check_gate_partition.py`, the reference regeneration).

## Open items

- K2-8 (above).
- `best_inventory` (K3.1) still prefers the row whose label column is today's; with cross-label reuse a unit can keep
  only an older-label row, which it then takes as the fallback. Preferring the row whose key matches today's request
  would make the choice follow the same rule (K2.12 records the choice).
- The collection build's newness (`learnloop_sidecar/handlers/ingest.py`, "any row for the unit", K3.3) and K3.2's
  planner do not ask for a unit whose row no longer matches, so after a prompt edit only an inventory job that names
  the unit re-inventories it (by design: re-inventorying existing sources is not done automatically, strategy §4).
- The inventory window key names its schema by version (K2.1's kept shape), and the row key follows it, so a schema
  edit without a version bump is still reused at both layers.
- `handle_inventory`'s prepared work from the first (identity-only) pass is rebuilt with the client for misses, as
  before; unchanged.
- Process: the test file's two small follow-up corrections and the deletion of `_shard_checkpoint_key` (one exact
  block) went in through short exact-pattern Python scripts; every other edit used the Edit tool.
