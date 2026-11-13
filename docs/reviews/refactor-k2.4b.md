# Refactor K2.4b: one synthesis head, two modes

Branch `refactor/k2.4b-shared-synthesis-head`, based on main `fea17dccae` (K2.4a, the shared tail, landed). Step
K2.4b of arc K (`docs/specs/refactor_strategy_v3.md` §2.17), specified in
`docs/reviews/k2-ingestion-strategy-2026-11-11.md` §3.2 (K2.4, second of three sub-steps). Structure track: no
persisted row, proposal, manifest, run row, model request or returned result changes for either mode, with one named
exception (K2-16, below).

## Step 0: the two heads side by side

Before calling the shared tail (`finish_synthesis_run`), each orchestrator opens its run its own way: it finds the
source set, resolves the brief, gathers the inputs, decides the scope, builds and persists the manifest, and opens the
agent run and the synthesis run. Bootstrap is `create_study_map` and `_create_study_map` in
`content/synthesis/source_set_synthesis.py` (S below); append is `append_source` and `_append` in
`content/synthesis/source_append.py` (A below). Line numbers are at the base `fea17dccae`.

Classes, as in K2.4a: **(i)** intended by the mode: an explicit input of the shared function, named for what it
means. **(ii)** drift with the same behaviour on every input: unified. **(iii)** drift whose behaviour differs and that
no spec settles: kept exactly (the mode decides) with a ledger row.

| # | Stage | Bootstrap (S) | Append (A) | Difference | Class |
|---|---|---|---|---|---|
| 1 | Vault and repository | `create_study_map` loads the vault and opens the repository when none is passed S:2069-2072 | `append_source`, identical A:414-417 | none; each public entry keeps its own parameters | (ii) |
| 2 | Source set | looked up by id; `StudyMapError("source_set_not_found", ...)` S:2219-2221 | identical A:482-484 | none | (ii) |
| 3 | Subject | `source_set.subject_id` S:2222, read by the result | identical A:485 | none (the tail's K2-14 is unchanged) | (ii) |
| 4 | Brief | `resolve_brief(vault, brief)` S:2224 (reads the learner profile; `validate_brief(strict=False)` never raises) | identical A:488 | none (K2.3 unified it) | (ii) |
| 5 | Requested mode | `mode` (`"auto"` or `"bootstrap"`; the CLI's `--mode` and a job payload's `mode`) else `StudyMapError("unsupported_mode", ...)`, after the brief and before the inputs S:2226-2228 | no `mode` parameter: never refused | the bootstrap entry takes a mode | (i) |
| 6 | Inputs | `_collect_inputs(repository, vault, source_set)` S:2230 | identical A:490 | none | (ii) |
| 7 | New material | none: every scope unit's inventory | `revs = set(new_revision_ids or selected)`, `select_new_inventories(..., new_unit_ids)`, the new sources A:491-493 | the append's new units | (i) |
| 8 | Budgets | `ingest.budgets` with the run's overrides S:2231 | identical A:497, computed after row 7 (both pure) | order only | (ii) |
| 9 | Token-budget record | `{"unlimited": True, "synthesis_shard_input_tokens"}` or the four synthesis budgets S:2233-2246; also the bootstrap call's `declared_budgets` S:2301 | `{"unlimited": True, "append_neighborhood_input_tokens"}` or the neighbourhood and output budgets, inline in the manifest call A:530-541 | which budgets the record names; `append_input_ceiling` is not among the append's (K3.4 kept the new refusal out of the record) | (i) |
| 10 | Nominator | `GraphNominator.for_ingest(vault, repository, client_factory=...)` S:2250-2252 | identical A:501-503 | none | (ii) |
| 11 | Neighbourhood | none | `select_neighborhood(...)` over the new inventories, capped by `append_neighborhood_input_tokens`, with embedding nominations when on (which may embed and store vectors: the only write before the manifest) A:504-509 | the append's context | (i) |
| 12 | Scope | `bootstrap_scope(vault, brief, nominator, facet_identity_client)`: the brief's scope, the nominator's identity, the facet-identity judge S:2253 | `append_scope(...)`: change kind, new revisions, the neighbourhood's record, the unit filter, the revision diff's hash, the facet-identity judge A:516-519 | the mode's record of what it read | (i) |
| 13 | Manifest's revisions | `manifest_inputs(inputs)["revision_ids"]`: the selected revisions S:2263 | overridden with `sorted(revs)` A:523 | the append names its new revisions | (i) |
| 14 | Prompt version | `source_set_synthesis_prompt_version(one_facet_per_skill)` S:2254-2255 | `append_reconciliation_prompt_version(...)` A:514-515; `one_facet_per_skill` is `facet_identity.enabled` in both | the mode's prompt | (i) |
| 15 | Provider and model | from the client S:2258-2259, after the scope | identical A:511-512, before the scope (both pure reads) | order only | (ii) |
| 16 | Manifest | `build_manifest(..., assessment_schema_version from the exam profile, token_budget, clock)` S:2260-2272 | identical but rows 9, 12, 13 A:520-543 | none beyond rows 9, 12, 13 | (ii) |
| 17 | Persist | `persist_manifest`, then the id by hash, then `agent_run_input_context_hash` S:2273-2276 | identical A:544-547 | none | (ii) |
| 18 | Clock | `now = utc_now_iso(clock)` after the manifest S:2278 | identical A:549 | none | (ii) |
| 19 | Agent run | `purpose=source_set_synthesis`, `prompt_template="source-set-synthesis"`, `output_schema="SourceSetSynthesis"`, the rest shared S:2279-2293 | `append_reconciliation`, `"append-reconciliation"`, `"AppendReconciliation"` A:550-564 | three values | (i) |
| 20 | Synthesis run | `insert_synthesis_run(mode=resolved_mode)`, always `"bootstrap"` S:2294-2296 | `mode="append"` A:565-567 | the run's recorded mode | (i) |
| 21 | The call's setup | `_SavedAnswers`, `ask` under `declared_budgets(token_budget)` with the manifest hash S:2298-2309 | `_AppendCall` with the input ceiling and output budget, `ask` with the preset A:569-584 | the modes' calls (K2.4c) | (i), not moved |
| 22 | The run record | `SynthesisRun(...)` with `progress` S:2322-2327 | the same with the new inventories and neighbourhood context as the digest's extras, no progress A:586-593 | append context (i); progress (append has none) | (i), (ii) |
| 23 | Result | `StudyMapResult` with `mode`, span hashes S:2331-2339 | `AppendResult` with `change_kind`, the neighbourhood's record A:600-607 | each mode's result type | (i) |

**What each reads from config in its head.** Both: `ingest.bootstrap_practice_items` (brief), `ingest.budgets` with
overrides, `facet_identity.enabled` (prompt version, the scope's judge identity) and the judge's route and fields
(`manifest_identity`), graph nomination (`is_active`, the nominator), the inventory route (`_collect_inputs`), the
algorithm tag (the manifest's contract version). Bootstrap's record names `synthesis_shard_input_tokens`,
`synthesis_shard_output_tokens`, `synthesis_total_input_ceiling` and `synthesis_output_tokens`; append's
`append_neighborhood_input_tokens` (also the neighbourhood's cap) and `append_output_tokens`. Their calls read more
(`append_input_ceiling`, the span-round caps): K2.4c.

**Refusals and the first write.** Bootstrap refuses `source_set_not_found`, then `unsupported_mode`, both before
anything is read from the database or written. Append refuses `source_set_not_found` before anything is written. The
first write is the manifest row for bootstrap; for an append with nominations on, the neighbourhood's embedding
vectors (and their spend receipts) come first, since the manifest records what the nominator compared. Then both
write the agent run (`running`) and the synthesis run. Every later refusal (bootstrap `budget_exceeded`, append
`append_input_over_ceiling` or `budget_exceeded`) is raised in the call, after the run is open, and the tail's failure
arm fails both rows. Nothing else is written before the model is asked.

**Append-only inputs.** The new revisions and unit filter (row 7), the change kind and revision diff (scope and
request), the neighbourhood (row 11; its record in the scope, its context in the request and the epigraph digest), and
the preset (the call's, K2.4a row 5). These stay the append's: its scope step is its own function, passed to the head.

**Totals** (23 rows; a row counts once for each class it contains):
- **(i)** 12 rows: 5, 7, 9, 11, 12, 13, 14, 19, 20, 21, 22, 23.
- **(ii)** 12 rows: 1, 2, 3, 4, 6, 8, 10, 15, 16, 17, 18, 22 (progress).
- **(iii)** none. Row 9's omission of `append_input_ceiling` from the append's record was settled by K3.4's record
  ("stays out of the manifest's `token_budget`"); it is listed under open items, not kept as drift.
