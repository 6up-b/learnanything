# Refactor K2.3: the manifest records; checkpoints reuse

Branch `refactor/k2.3-manifest-records`, based on main `ff8b42530b` (K2.1's checkpoint helper and K2.2's outer
caches landed). Step K2.3 of arc K (`docs/specs/refactor_strategy_v3.md` §2.17), specified in
`docs/reviews/k2-ingestion-strategy-2026-11-11.md` §3.2 from the K2 map's KX5, KM2, KM6 and KH4. It is a structure
track step, with the consequences stated below. It changes no learner scoring, scheduling or projection.

**Cost of an identical rebuild (measured on real vaults).** An identical rebuild no longer stops at a run-level
lookup. It re-runs the CPU stages that the lookup used to skip: checkpoint replay, normalization, the gates, the
instrument gates, the facet plan and the proposal comparison. It still makes zero model calls. Measured on backup-API
copies of the owner's three vaults (at mvp-0.58), it costs about a second at most, not minutes:
- the lookup hit took 0.16-0.60 s;
- the re-run takes about 0.35-1.2 s;
- no stage reaches a second.

See "Wall time" below for the table and what was timed.

## The stop, and the decision

Removing the run-level lookup alone would have changed which proposal a learner sees. A build re-run after its
proposal was persisted but not applied wrote a second copy, and the first one stayed in review. This happens on a
Retry after an apply failure, on a review build run twice, and on an append run twice. The step stopped and reported.
The orchestrator chose the content dedupe at persist (the option recommended in the report), with the requirements
this record follows.

## What changed

| File | What |
|---|---|
| `content/synthesis/proposal_match.py` (new) | The one rule, stated in its module docstring: `match_proposal(repository, source_set_id, purpose, rows)` compares a run's normalized and gated rows with the earlier proposals of the same source set (completed runs) under the same purpose; `ProposalMatch` (`pending`, `settled`, `rejected`); `RejectedProposalMatch`; `proposed_content` and `stored_content` |
| `content/synthesis/source_set_synthesis.py` | `_reusable_bootstrap_run` and `_nominations_shaped` deleted. `_gate_and_persist` applies the rule after the instrument gates and before anything is written (generation needs, the batch, facet-identity actions): a match completes the run with `proposal_id` = the matched proposal and `coverage_decisions.matched_proposal`; a rejected match raises unless the answers are fresh. `_create_study_map` runs synthesis at most twice (the second time after dropping the answers of a run equal to a rejected proposal), applies a waiting match when asked, and skips the facet-identity summary and epigraphs on a match. `revalidate_synthesis_candidate` refuses a repaired candidate equal to a rejected proposal (`matches_rejected_proposal`). `resolve_brief` (extracted, shared with append). `manifest_inputs`; `_collect_inputs` records role overrides, asset hashes, extractor versions and each inventory row's content hash. `StudyMapResult.nothing_new` |
| `content/synthesis/source_append.py` | The completed-run lookup is deleted. The brief is resolved first (`resolve_brief`), so the manifest records it and the append inherits the learner's level. The manifest is built from `manifest_inputs`. `append_scope` records `revision_diff_hash` when a diff is given. The reconciliation runs at most twice under the same rule. A match returns the earlier proposal, auto-applies its waiting auto-apply items, and skips epigraphs. `AppendResult.nothing_new` |
| `content/synthesis/synthesis_manifests.py` | The module says the manifest is a record. `content_hash`. `curriculum_snapshot_hash` includes the concept edges. `lock_fingerprint` leaves `build_manifest` and the hashed fields (the column stays, NULL) |
| `content/synthesis/vault_epigraphs.py` | Docstring: a matched run writes no epigraphs |
| `content/pipeline/jobs.py` | Both synthesis handlers report "Nothing new" on the `applied` rung when `nothing_new` |
| `db/repositories.py` | `completed_agent_runs_by_context` deleted (its one caller went); a docstring |
| `tests/test_rerun_proposals.py` (new) | The fail-first tests and guards below |
| `tests/test_graph_nomination_ingest.py` | Three assertions ported (below) |
| `tests/identity_pins_helpers.py`, `tests/goldens/identities.toml` | Pin sites describe the manifest as a record; two pins regenerated |

## The rule (requirement 1)

After a run's rows are normalized and gated, and before anything is written, the rows are compared with the proposals
that earlier completed runs of the same source set persisted under the same purpose (`sourceset_bootstrap` or
`sourceset_append`):

- **Pending** (any item still waits): that proposal is the run's result. Nothing is written: no batch, no generation
  needs, no facet-identity actions. An apply the caller asked for applies its waiting items. Epigraphs are skipped.
  The result has `reused=True`.
- **Settled** (nothing waits and not every item was rejected): nothing is written or applied, and `nothing_new=True`.
- **Rejected** (every item was rejected): see D-16 below.

A pending match wins over a settled one, and either over a rejected one. Between two matches of the same kind, the
newer wins.

**Equal**, precisely: the same set of `client_item_id`s, and for each of them the same:
- `item_type`, `operation`, `target_entity_type`, `target_entity_id`;
- `payload` as proposed (not the learner's `edited_payload`);
- `source_ref_ids`, `audit` (the instrument gates' verdicts), `validation_status`, `validation_errors`;
- dependencies, named by the client ids of the items depended on. Unknown and self dependencies are dropped, as the
  batch writer drops them. Stored dependencies (DB ids) are mapped back to client ids within the batch.

Values are compared as the batch stores them (a JSON round trip with sorted keys). These fields are left out, because
each run mints them or the review writes them: the item `id`, the batch id, `created_at`, `updated_at`, `decision`,
`decided_at`, `decided_by`, `edited_payload`, `applied_change_batch_id`, `dependency_status` and
`dependency_block_reason`.

**Shown, not assumed.**
- A probe on two runs of the same answers at different clocks differed only in `id`, `proposed_patch_id`,
  `created_at` and `updated_at` (bootstrap: 7 items each; append: 1).
- `test_two_runs_of_the_same_answers_store_equal_content_whatever_their_ids_and_clocks` builds the same answers in two
  vaults at two clocks. It asserts the ids and stamps differ and the compared content is equal, dependencies included.
- `test_a_changed_payload_is_not_a_match` asserts a changed title, or another purpose, does not match.

## D-16 and the partly rejected case (requirement 2)

**Wholly rejected.** Rows equal to a proposal whose every item was rejected are not that proposal again. The run's
saved answers are dropped (bootstrap: `_SavedAnswers.discard`, the shard results and pass checkpoints including
structuring; append: `_AppendCall.discard_answers`), and the same build runs synthesis again, paying for fresh answers.
What the fresh answers give is persisted, even if it equals the rejected proposal again: a second refusal could only
loop, and a model is not deterministic.

**Partly rejected** (judgment call):
- With anything still waiting, it is a pending match. It is returned as it is: the rejected items stay rejected, and an
  apply takes only the waiting ones (`apply_accepted_items` applies `pending` items).
- With nothing waiting (some applied, some rejected), it is settled, so nothing is new.

Neither reading resurrects an item the learner rejected. Treating it like a wholly rejected proposal would pay for
fresh answers, which could propose the rejected items again.

**The zero-model repair** (`revalidate_synthesis_candidate`) cannot pay for fresh answers. A repaired candidate equal
to a wholly rejected proposal is refused (`matches_rejected_proposal`, candidate not preserved), so the card's Retry
runs a fresh synthesis.

## An applied proposal (requirement 3): what today's code does

These are probes on the base, with the house fakes and no change.

- **Bootstrap applied, then built again.** The manifest moved (curriculum snapshot), so the lookup missed. One
  synthesis call was paid and a second, accepted batch was written: the rebuild proposes `update` operations with
  targets over the applied entities, so its rows differ from the applied `create` rows. On the tip the rows still
  differ, so there is no match and the behaviour is unchanged: a new proposal, as today.
- **Append auto-applied, then run again.** The lookup missed (the applied link changed the request), and one append
  call was paid. The rows equalled the applied proposal's. The base wrote a second batch, re-applied its link (no new
  link: 2 links before and after; `study_map_diff.has_changes` false), and paid a second epigraph batch. On the tip the
  append call is paid as before (its request changed). The rows match the settled proposal, so nothing is written or
  applied, no epigraphs are paid, and the result says `nothing_new`.

What the learner sees in the vault and the review inbox is the same: no new link and nothing waiting. The base
added one more accepted batch to the history, and its job said "Safe source additions applied"; the tip's job says
"Nothing new" on the same rung.

## Fail-first evidence (requirement 4)

`tests/test_rerun_proposals.py`, 19 tests. Each table-row and rule test asserts the proposal batches and their
decisions, not only calls. It was run three ways: on the base sources (`git checkout ff8b42530b -- src`, then back);
with the lookup removed but no dedupe (a throwaway plugin returning `None` from `match_proposal` in both orchestrators);
and at the tip.

| test | base | lookup removed, no rule | tip |
|---|---|---|---|
| retry after an apply failure that follows persist | pass | **fail** (2 batches: 7 pending, 7 accepted) | pass |
| a review build run twice | **fail** (no `nothing_new`; base returned the same proposal) | **fail** (2 pending batches) | pass |
| a review append run twice | pass | **fail** (2 pending batches) | pass |
| an auto-applied append run twice writes nothing new | **fail** (a second accepted batch) | **fail** | pass |
| a waiting append re-run with auto-apply applies its links (D-29) | **fail** (reused, never applied) | **fail** | pass |
| D-16 bootstrap: wholly rejected pays for a fresh one | **fail** (reused the rejected proposal, 0 calls) | **fail** (replayed: 1 call, not 2) | pass |
| D-16 append | **fail** (reused, 0 calls) | **fail** | pass |
| partly rejected returned with its rejections kept | pass | **fail** (a second batch) | pass |
| repaired candidate equal to a rejected proposal is refused | **fail** | **fail** | pass |
| over-invalidation: a budget change re-pays nothing | **fail** (an epigraph batch and a second pending batch) | **fail** | pass |
| under-invalidation: a changed role override is paid | **fail** (0 calls: reused) | pass | pass |
| under-invalidation: a new concept edge reaches a paid structuring request | **fail** (structuring not paid) | **fail** (a second batch) | pass |
| under-invalidation: an inventory re-read in place reaches synthesis | **fail** (0 calls: reused the run) | pass | pass |
| under-invalidation, KM6: an append resolves its brief and inherits the learner's level | **fail** (no `practice_items` in the request) | pass | pass |
| the manifest records rows, assets, extractors | **fail** | pass | pass |
| the curriculum snapshot names concept edges | **fail** | pass | pass |
| an append records its revision diff's hash | **fail** | pass | pass |
| equal content across runs; a changed payload is not a match | pass (they test the new function) | pass | pass |

## Assertions changed

`tests/test_graph_nomination_ingest.py`, following the core (strategy §2.19 T4). Each test's subject was "a change is
a new bootstrap", which was the manifest's job as a key. Each now asserts what the change does now: the record names it,
the request it reaches is paid, and equal rows give the same proposal.

- `test_enabling_nominations_or_completing_the_index_is_a_new_bootstrap` is renamed `..._is_recorded_and_paid_when_it_acts`.
  - "Switch on, index incomplete": `incomplete.reused is False` became `incomplete.manifest_hash != first.manifest_hash`
    plus `incomplete.reused is True and incomplete.proposal_id == first.proposal_id`. Nothing is nominated, the
    structuring answer is read back, and the rows are the first run's.
  - "Index complete": `third.reused is False` became `third.manifest_hash != incomplete.manifest_hash`. The assertion
    that the registry details reach a paid structuring request is kept.
- `test_registry_definition_change_is_a_new_bootstrap_and_repeats_reuse` is renamed
  `..._is_paid_again_and_repeats_reuse`. `changed.reused is False` became
  `changed.manifest_hash != first.manifest_hash`, beside the kept assertion that the new definition reaches the paid
  structuring request. The fake answers the same, so the rows are equal.

No other assertion changed. The existing reuse tests pass unchanged under the new path:
`test_manifest_idempotency_cache_zero_new_calls`, both `test_cached_generation_resume*`,
`test_manifest_cache_hit_writes_no_epigraphs`, `test_identical_append_reuses_its_completed_run` and
`test_retired_config_identities`' reuse checks.

## Pins (identity)

Two pins moved, both regenerated with `python tests/test_identity_pins.py --write` in `7c3dc20ee6`:

- **`A1-A4.manifest_hash.init` and `A1-A4.manifest_hash.legacy`.** Two changes moved them. `lock_fingerprint` (always
  null) left the hashed fields. The curriculum snapshot now hashes the concept edges, which is an empty list at the
  pin's vault. The hash is provenance only now: nothing looks a run up by it.
- **Stored rows.** Every manifest already stored stays in `synthesis_manifests` as the record of its run and is read as
  it is. Old `unit_inventory_versions` values are strings and new ones are objects; the one reader, `_sent_units`,
  reads only the keys. No row is orphaned, because no reuse ever reads one.

Unchanged: `A1-A4.scope.*`, `A1.*`, `A2.*`, `A3.*`, `A4.fixed_vault`, `K3.2.scope.*` (the revision-diff hash enters
an append's scope only when a diff is given), `K3.4` and every checkpoint key. The A1, A2, A3, A1-A4, K3.2 and A4 sites
now describe their consumer as a record whose move pays nothing.

## P-spend: model calls (requirements 5 and 6)

The synthetic two-chapter vault has two shards and a structuring client that merges. Calls are counted as synthesis
passes / structuring / epigraphs, with the batches after each run. The same throwaway probe ran on the base sources
and at the tip; it was never committed.

| run | base | tip |
|---|---|---|
| first build | 2 / 1 / 1; 1 pending batch | 2 / 1 / 1; 1 pending batch |
| rebuild, nothing changed | 0 / 0 / 0 (lookup) | 0 / 0 / 0 (equal pending proposal) |
| rebuild after a budget change | 0 / 0 / **1**; **a second pending batch of 11** | 0 / 0 / 0; still 1 batch |
| rebuild after a role override | 0 / 0 / 0: wrongly reused, the override never reached synthesis | 1 / 0 / 1: the changed shard is paid; its rows differ, so a new pending batch |
| rebuild after an inventory prompt edit (K2.2 pays 2 inventory calls on both) | 0 / 0 / 0: wrongly reused, the new rows never read | 2 / 1 / 0: synthesis reads the new rows; the rows equal a waiting proposal, which is the result |
| append after a wholly rejected append (single-chapter vault) | 0 calls; the rejected proposal returned | 1 append + 1 epigraph; a new pending batch |

**Epigraphs.** The epigraph prompt lists the subject's recent epigraphs, so its checkpoint cannot hit after the first
run. Under the rule, an identical rerun pays none, because a matched run persists nothing and skips the step. A rerun
that persists something new pays one epigraph batch, as today (the role-override row).

**The one-time cost.** Measured on the same vault: the structuring and epigraph checkpoints were deleted after a first
build, as for a run made before K2.1, and then the identical rebuild ran.
- **Tip.** It pays **1 structuring call** (base: 0, the lookup answered) and **0 epigraph calls**: the matched run
  skips them, so the strategy's expected epigraph re-pay does not happen.
- **Persona fires (code-traced; the fixture's items carry none).** Persona fire judgements of a run made before K2.1
  are re-paid once: one per persona trial, for each practice item carrying belief-holder material.
- **Appends (code-traced).** An append made before K2.3 whose brief did not already hold the resolved fields pays its
  append call once (and its span round, if any). Its request now carries the resolved brief, including the learner's
  level when one is on file.

All of these arise only at an identical rebuild, which follows a learner's rebuild, Retry or CLI build. Keep-ahead
builds never repeat a manifest. So the bill is at most: per subject, 1 structuring call plus the persona fires of its
items, and per pending append, 1 append call, each paid once.

## Wall time (requirement 5)

**Identical rebuild, two-chapter vault**, 5 samples each:
- base: 2.6-2.9 ms;
- tip: 7.8-8.2 ms.

Where the tip's time goes:

| stage | time |
|---|---|
| checkpoint replay (`_run_synthesis`) | 1.9 ms |
| `match_proposal` | 1.4 ms |
| `_collect_inputs` | 1.1 ms (on both) |
| `_normalize` | 0.9 ms |
| facet plan | 0.2 ms |
| synthesis gates | 0.1 ms |
| instrument gates | below 0.1 ms |

**Scaling.** One shard per chapter, house fake answers, unlimited budget:

| chapters | rows | base | tip | tip: replay | tip: match | tip: normalize | tip: facet plan | tip: gates |
|---|---|---|---|---|---|---|---|---|
| 4 | 22 | 4.6 ms | 12 ms | 3.1 | 2.4 | 1.2 | 0.4 | 0.1 |
| 16 | 82 | 4.0 ms | 28 ms | 9.1 | 7.6 | 2.9 | 1.1 | 0.2 |
| 64 | 322 | 8.3 ms | 100 ms | 32 | 29 | 11 | 6.8 | 0.6 |
| 128 | 642 | 57 ms | 324 ms | 114 | 118 | 28 | 25 | 1.3 |

The match grows about linearly in rows: one dependency read per item of a candidate proposal, after a cheap check that
the client ids agree.

**On real vaults (measured).** Backup-API copies (`learnloop.db.copies.copy_tree_with_databases`) of the owner's three
vaults, already upgraded to mvp-0.58, were made under the gitignored `fixtures-local/k23/` and deleted afterwards.
Each has one source set with a completed bootstrap run, and the newest such run was timed. No model call was made:
- **Replay.** `_run_synthesis` ran twice. First under a client that answered each pass with the run's own stored shard
  answer, to seed the checkpoints under that client's settings; then, timed, with every pass answered from its
  checkpoint (0 answers needed).
- **Structuring.** The run predates its checkpoint, so the call was refused (1 refused call per run). That is the
  one-time structuring call.
- **Facet plan.** Run with stored vectors only and a judge that refuses. The plan stopped at `judge_unavailable`, so
  judge-checkpoint replay is **not** timed.
- **Downstream stages.** Normalization, the gates and the instrument gates ran over the run's stored candidate against
  the vault as it is now. Instrument gates ran without a grading client, so persona fires are not timed. Then the
  proposal comparison.
- **Base (the lookup hit).** `_collect_inputs`, `build_manifest` and the indexed `agent_runs` query, timed on the same
  copy.
- **Tip total.** Base's inputs and manifest, plus every stage.

| vault | units | items (stored / normalized now) | replay | normalize | gates (incl. identifiability) | instrument gates | facet plan* | match | base (lookup hit) | tip total |
|---|---|---|---|---|---|---|---|---|---|---|
| a | 41 | 176 / 104 | 0.079 s | 0.078 s | 0.003 s | 0.000 s | 0.004 s | 0.016 s | 0.167 s | about 0.35 s |
| b | 19 | 132 / 93 | 0.092 s | 0.050 s | 0.001 s | 0.066 s | 0.002 s | 0.017 s | 0.161 s | about 0.39 s |
| c | 38 | 285 / 194 | 0.214 s | 0.219 s | 0.004 s | 0.121 s | 0.006 s | 0.023 s | 0.595 s | about 1.18 s |

\* Up to the judge, which refused. In every row, the comparison found no equal proposal: the vault holds the applied
map now, so the rows differ.

**What this implies.**
- An identical rebuild of each of the owner's books costs well under the first second over what the lookup cost: about
  0.2-0.6 s more, spread over replay, normalization and the instrument gates. The gate stage itself is milliseconds.
- So the July note's "minutes in the gate stage" does not hold for these runs. Its gate stage was on a larger
  candidate under older code, and was not re-measured here.
- No fast path is proposed: none of these stages is worth a run-level shortcut.

**Not timed:**
- the facet-identity judge's checkpoint replay;
- persona fire checkpoint replay inside the instrument gates;
- the structuring checkpoint's replay (after its one-time call);
- append runs, whose context is a bounded neighbourhood.

The normalized row counts are those of the stored candidate against today's vault (fewer than stored, because the map
is applied), so normalization and gates ran on about 60-70% of the original rows.

## Vault

- `Concepts/Synthesis Identity and Caches.md` (new): the record versus the checkpoints, the proposal rule, what the
  manifest holds, and what a rebuild costs.
- `Workflows/Import Canonical Sources.md`: the paragraph about the completed run as the label-keyed layer now says no
  layer answers for a whole run, and links the note.
- Generated references are regenerated once after the source commits.

## Ledger

- **D-16**: fixed (`7c3dc20ee6`).
- **D-29** (new, map KX5): an append whose completed run was reused never auto-applied its waiting links. Fixed
  (`7c3dc20ee6`).
- **K2-3** (KM6): fixed.
- **K2-4**: the completed run and KM2 are fixed. K2-8 stays open for arc K's close.

## Judgment calls

1. **The rule lives in one module** (`proposal_match`), called where each orchestrator persists. Until K2.4 merges the
   orchestrators, that is two call sites of one rule, not two rules.
2. **Equality includes the instrument gates' audit and the validation status.** They are today's verdicts. A waiting
   proposal whose stored validation was rewritten since (for example by a later revalidation of its items) does not
   match, and the rebuild writes a new proposal.
3. **The partly rejected readings** above. A pending proposal with rejections is returned as it is; with nothing
   waiting, it is settled.
4. **Fresh answers after a rejected match are paid in the same build, once,** and then persisted even if equal. The
   alternative, failing the build so the next Retry pays, would show the learner an error for a correct state.
5. **The zero-model repair refuses** a candidate equal to a wholly rejected proposal, rather than persisting it back.
6. **A matched run is recorded as a completed run** whose `proposal_id` is the matched proposal, with
   `coverage_decisions.matched_proposal`. The result carries the new run's id. Like the old reuse, its result has no
   facet-identity summary; it has the item counts and gate diagnostics of its rows.
7. **A waiting append matched under `auto_apply` applies its waiting auto-apply items.** The old reuse never did
   (KX5): D-29. The requirement says "applied if the caller asked for apply".
8. **`nothing_new`** is a new field on both results and in their `as_dict` (an additive key in the RPC and CLI JSON;
   no `cli_surface.json` change, which pins parameters). The jobs say "Nothing new" on the `applied` rung.
9. **No migration.** The exact inputs go into existing columns:
   - role overrides into each membership entry;
   - each unit's row id, extraction and content hash into `unit_inventory_versions`' values (an object beside the old
     version string);
   - the concept edges into `curriculum_snapshot_hash`. There is no column for a separate edge hash, so the edge hash
     is folded into the curriculum snapshot rather than recorded alone;
   - `asset_hashes` and `extractor_versions` filled;
   - `lock_fingerprint` dropped (its column stays, NULL);
   - an append's `revision_diff_hash` in its scope.
10. **`resolve_brief` sits in `source_set_synthesis.py`,** which both orchestrators already import. `brief.py` would
    import `learner_profile`, which imports `brief`.
11. **Only `completed_agent_runs_by_context` was deleted.** `completed_agent_run_by_context` stays: the legacy canonical
    lane (`source_ingestion.py`) still reuses by context hash. That is outside K2.3's two orchestrators, and the
    strategy keeps the legacy lane until the UX overhaul.
12. **Matching considers completed runs' proposals of the same source set and purpose only.** A proposal written by
    another lane is never a match.

## Gates

- **Targeted tests.** `scripts/affected_tests.py --base ff8b42530b` selects the full suite (`db/repositories.py`;
  `jobs.py` and the synthesis modules do too), so every test file ran on `98ee8560ac`. That was 1,392 files with
  `-m "not arc_close"`, in 14 chunks of up to 100 at `-n 4` under the 5 GB cap behind the full-suite lock:
  - 30,470 passed and 2 failed.
  - `test_module_catalog_inventory`: the new module had no catalog note until the regeneration (`176eb9465a`).
  - `test_ingest_runner::test_append_synthesis_forwards_budget_overrides`: its stand-in `AppendResult` lacked
    `nothing_new`. It gained the field (`nothing_new=False`) in `5ca9274b84`; no assertion changed.
  - Both files, plus `test_rerun_proposals`, `test_identity_pins`, `test_structure_ratchets`, `test_test_layout` and
    `test_architecture`, passed again at the tip: 333 passed.
- **Structure ratchets.** They did not move.
- **Lint.** `lint-imports --no-cache`: 42 kept. `ruff check`: clean.
- **Vault validators.** All four pass: `db_validate_reference.py` (no errors), `module_validate.py`,
  `desktop_validate.py` and `validate_vault.py`.
- **Gate partition.** `scripts/check_gate_partition.py`: 30,708 collected, landing 30,648 + arc_close 60.
- **Regeneration.** References were regenerated once after the source commits (`176eb9465a`, 34 generated notes); a
  second run changed nothing.
- **Not run.** No full suite with `arc_close` (the orchestrator's landing gate).

## Process

- Scripts were used for some edits, each asserting its pattern matched exactly once:
  - the deletion of the completed-run cache block in `source_set_synthesis.py`;
  - the re-indentation of `_append`'s body into its loop;
  - several multi-hunk replacements (docstrings, the bootstrap loop, the pin site descriptions, the ledger rows,
    small test edits).
- Every other edit used the Edit tool.
- The probes swapped the base sources in with `git checkout ff8b42530b -- src` and back.
- The probe tests, the plugin and the scaling probe were never committed.

## Open items

- **The rebuild cost** was measured on the owner's vaults (above): about 0.35-1.2 s. The judge and persona replay
  were not timed.
- **K2-8** (open since K2.2).
- **The legacy canonical lane's context-hash reuse** (`source_ingestion.py:280`), untouched.
- **`tests/conftest.py`, `exam_material.py` and `learner_protection.py` were not touched,** and no change there was
  needed.
