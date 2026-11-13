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

## What each difference became

| Row | Outcome |
|---|---|
| 1 | Left in the public entries (`create_study_map`, `append_source`): each is its mode's API, and the three lines are the same call. |
| 2, 3, 4, 6, 8, 10 | Once, in `open_synthesis_run`, in the same order: source set, brief, (row 5), inputs, budgets, nominator. |
| 5 | The head's `requested_mode` (`create_study_map`'s `mode`; the append passes none) is refused unless it is `"auto"` or the mode's `name`, at the same place (after the brief, before the inputs) with the same code and message, so an unknown set with a bad mode still says `source_set_not_found`. |
| 7, 11, 12, 13 | The mode's scope step, `decide_scope(brief, inputs, budgets, nominator) -> RunScope`: bootstrap's records `bootstrap_scope`; the append's (in `_append`) selects its new inventories and the neighbourhood, records `append_scope`, names its revisions, and returns its context. |
| 9 | `SynthesisMode.recorded_budgets` and `unlimited_recorded_budgets` (field names, in the order the records had). |
| 14 | `SynthesisMode.prompt_version` (the two version functions). |
| 15, 16, 17, 18 | Once, in the head. |
| 19 | `SynthesisMode.agent_purpose`, `prompt_template`, `output_schema`. |
| 20 | `SynthesisMode.name`, which replaces K2.4a's `epigraph_mode` (same values): the run's recorded mode, the epigraph service's mode, the mode a caller may ask for. `StudyMapResult.mode` reads it. |
| 21 | Not moved (K2.4c): each orchestrator builds its call from the head's record (`run.token_budget`, `run.budgets`, `run.provider`, `run.model`, `run.one_facet_per_skill`, `run.manifest`). |
| 22 | The head builds `SynthesisRun`. K2.4a's `digest_extras` is now `context`: the append's request reads it too (`_run_reconciliation` takes the neighbourhood's context dict, the only part of it it read). |
| 23 | Each orchestrator builds its own result; the append's `neighborhood` is the record its manifest holds (`run.manifest["scope"]["neighborhood"]`, the same value `as_manifest_record()` gave). |

## The shape

- **`open_synthesis_run(vault, repository, root, source_set_id, mode, *, client, brief, decide_scope, clock, budget_overrides, unlimited_token_budget, embedding_client_factory, facet_identity_client, progress, requested_mode)`** in `content/synthesis/source_set_synthesis.py`, beside the tail, for the same reason (the append module imports from this one). It returns `SynthesisRun`.
- **`SynthesisRun`** gains what the head opened and the calls read: `manifest`, `budgets`, `token_budget`, `provider`, `model`, `one_facet_per_skill`; `digest_extras` becomes `context`.
- **`RunScope`** (new, frozen): what the mode's scope step returns: `scope`, `revision_ids` (None: the selected revisions), `context`.
- **`SynthesisMode`** gains seven fields, each a row above: `name` (replacing `epigraph_mode`), `agent_purpose`, `prompt_template`, `output_schema`, `prompt_version`, `recorded_budgets`, `unlimited_recorded_budgets`. No boolean.
- **Not added:** no other record, class or registry. The append's new inventories, unit filter and neighbourhood stay in `source_append` (its scope step); its call and the shard runner are untouched.

## Deletion proofs (strategy §2.1)

- **No function is deleted.** What the head replaces was inline code in `_create_study_map` and `_append` (`d6240b7378`); the goldens show the head writes and refuses the same.
- **Imports `source_append` no longer uses** (`d6240b7378`): `utc_now_iso`, `SynthesisRun`, `manifest_inputs`, `resolve_brief`, `build_manifest`, `persist_manifest`, `agent_run_input_context_hash`. Each is still defined and used where it was (`source_set_synthesis`, `synthesis_manifests`, `clock`); `git grep` finds no other use of them through `source_append`, and the only test that reached one through it (`source_append.build_manifest`) is ported below.
- **`SynthesisRun.digest_extras` and `SynthesisMode.epigraph_mode`** (renamed): `git grep -nw` over `src`, `tests`, `scripts`, `apps` and the vault notes finds no other reader; both records are private to the two modules (no `importlib`, Typer, registry or frontend path names them).

## Goldens (P-golden)

`tests/test_synthesis_tail_golden.py` gains seven cases (files in `tests/goldens/synthesis_tail/`), committed at the base behaviour (`3cd2299724`) before the extraction and unchanged by it:

| Case | Mode | Covers |
|---|---|---|
| `bootstrap_unknown_source_set` | bootstrap | an unknown set with `mode="append"`: `source_set_not_found` (the lookup comes first), nothing written, no request |
| `bootstrap_unsupported_mode` | bootstrap | `mode="append"`: `unsupported_mode`, nothing written |
| `bootstrap_over_input_ceiling` | bootstrap | `synthesis_total_input_ceiling = 10`: the manifest and both run rows written, then `budget_exceeded`, both rows failed, no request |
| `bootstrap_unlimited` | bootstrap | `unlimited_token_budget`: the record keeps only the shard size |
| `append_unknown_source_set` | append | `source_set_not_found`, nothing written |
| `append_over_input_ceiling` | append | `append_input_ceiling = 10`: rows written, then `append_input_over_ceiling`, both failed, no request |
| `append_unit_filter_diff_unlimited` | append | a unit filter, a revision diff, a change kind, a neighbourhood budget override and no limits: the scope's `new_unit_ids` and `revision_diff_hash`, the unlimited record |

The 20 cases passed after every later commit. After K2-16's fix, the golden append vault went back to the house helper with the inventory's alias (`2cf86baa1e`): the nine append files moved (the alias adds a neighbour facet and changes the inventory's content, so checkpoint keys, prompt digests and the neighbourhood record move with it), the bootstrap files did not. Those aliased files also pass with the base's two orchestrator modules checked out over the fix (`git checkout fea17dccae -- source_set_synthesis.py source_append.py`, then back), so the extraction is equal on the aliased vault too. All 20 passed under `PYTHONHASHSEED` 0-7 and under `-n 4`.

**Not covered:** the head with graph nominations on (the nominator's identity in bootstrap's scope, the append's embedding writes before its manifest): `test_graph_nomination_ingest` covers both paths, unchanged and passing.

## K2-16

Read first, every consumer of the neighbourhood's record and the manifest hash: the record is the append scope's `neighborhood` (manifest) and `AppendResult.neighborhood`; the request's context (`as_context`) carries no match reasons, and every name scores the same, so the selection's order and the request never moved. The manifest hash is a record (`synthesis_manifests` is unique on it; `agent_runs.input_context_hash` records it; no run is looked up by it since K2.3, and `completed_agent_run_by_context`'s one caller is the inventory's). `_sent_units` reads the scope's revisions and unit filter, not the neighbourhood. The append checkpoint keys render the request. `proposal_match` compares rows. No identity pin builds a neighbourhood (`_append_scope`'s pin passes a fixed dict). So nothing stored keys on the old order, and the fix went in (`951f60e00f`): names, aliases and prerequisite hints are tried in sorted order. The hints had the same fault.

What a vault sees: an append's manifest scope may name another of two matching names in a reason than an earlier one did, so its manifest hash differs; a rerun of an append written before writes a new manifest row (as a different hash seed already did). Nothing is reused, refused or applied differently.

Fail-first: `tests/test_append_neighborhood_order.py` builds one neighbourhood in fresh interpreters under eight seeds (a facet and a concept that a name, its alias and two hints all match, with a stub vault and repository). Both tests were red on the base: seed 2 named the other name, seed 3 the other hint; the context was equal under every seed.

## Tests changed

- `tests/test_retired_config_identities.py`: the two append tests patched `source_append.build_manifest`, which the append no longer calls (T4). Ported to plain values: `test_append_manifest_hashes_the_facet_identity_config_as_before_arc_c` reads the persisted manifest's scope (`synthesis_manifest_by_hash`) and checks the same digest; `test_an_append_run_completed_before_arc_c_is_reused_for_the_same_request` checks the persisted scope's facet-identity dump equals the dump the code at `88607cb3fe` wrote (byte for byte, the file's recorded `BASE_FACET_IDENTITY_DUMP`), so a run completed then had this manifest, then reruns and asserts the same reuse and hash as before. The bootstrap tests that patch `source_set_synthesis.build_manifest` (here and in `test_graph_nomination_ingest`) keep working: the head calls that name in that module.
- `tests/test_synthesis_tail_golden.py`: the seven cases above; its private unaliased vault removed for the house helper.
- No assertion changed.

## Measures

| | base `fea17dccae` | tip |
|---|---|---|
| `source_set_synthesis.py` lines | 4,113 | 4,183 |
| `source_append.py` lines | 1,210 | 1,146 |
| both | 5,323 | 5,329 |
| `_create_study_map` | 145 | 70 |
| `_append` | 151 | 85 |
| `open_synthesis_run` | none | 99 |
| functions over 200 lines in the two files | 2 (`_normalize` 1,081, `_normalize_append` 221) | the same 2 |

The two files are 6 lines longer together: the head's docstring and comments, `RunScope`, the seven `SynthesisMode` fields with their documentation and two rows, and the six new `SynthesisRun` fields. The head's stages exist once.

## Judgment calls

1. **The scope step is a per-run callable** (`decide_scope`), as K2.4a's `ask` and `apply` are: the append's selection needs the head's inputs, budgets and nominator, and the manifest needs its result, so it runs in the middle of the head. A mode field could not take the append's per-run arguments (change kind, revisions, unit filter, revision diff) without the head growing append-only parameters.
2. **`RunScope` is a new frozen record**, returned by the scope step rather than by the head (the head returns the existing `SynthesisRun`). A tuple of three would read worse at both call sites.
3. **`requested_mode` on the head** keeps bootstrap's `unsupported_mode` at its place in the refusal order. Refusing it in `_create_study_map` before the head would have changed which error a request wrong twice (unknown set and bad mode) gets. The message names `create_study_map`; the append never passes a mode, so it never reaches it.
4. **`name` replaces `epigraph_mode`**: the run's recorded mode, the epigraph mode and the askable mode are the same two strings; three fields with equal values would invite drift.
5. **`SynthesisRun.manifest` is the whole manifest**, not its hash: the append's result reads its neighbourhood record from it, which saves the scope step from returning that record twice.
6. **`digest_extras` became `context`**, read by the append's request as well as the epigraph digest; `_run_reconciliation` takes the neighbourhood's context dict instead of the `Neighborhood`, the one part of it it read. That is the only edit inside an append call (K2.4c's).
7. **Row 9's `append_input_ceiling`** stays out of the append's record as K3.4 decided; listed below as an open item rather than kept as drift.
8. **K2-16 went in after the extraction**, so the extraction was proven on the goldens as committed at the base; the aliased goldens were then checked against the base's orchestrators.
9. **The goldens stay in one file** (`test_synthesis_tail_golden.py`, directory `synthesis_tail/`): the harness is shared and test files may not import each other; the docstring now names the head's cases.

## Ledger

- **K2-16**: fixed here (`951f60e00f`).
- No new row: the step found no class (iii) difference in the heads.

## Open items

- K2-9 to K2-15 stay open (the tail's).
- The append's manifest does not record `append_input_ceiling`, while bootstrap's records its total input ceiling. K3.4 kept it out while the manifest was still a reuse key; since K2.3 it is a record, so adding it would only complete the record (a manifest change: behaviour track if wanted).
- K2.4c: the append through the shard runner; it removes `ask`, `drop_answers`, `_run_reconciliation` and the context's separate path.
- `_NewSignals.all_name_tokens` in `append_neighborhood.py` has no caller (seen while fixing K2-16; not removed here).

## Process

Most source and test edits went in through short Python scripts that replace one exact block each and assert it occurs exactly once (the append's head and its imports, `_run_reconciliation`'s parameter, the quick-add comment, the ported tests, the goldens' vault helper, the vault note and the ledger row); a few through the Edit tool; one import line through `sed`.

## Gates

- **Targeted tests.** `scripts/affected_tests.py --base fea17dccae` chose 323 files; with the rules block's list and the files this step adds or edits, 332, run at `62558179d3` (the source tip) with `-m "not arc_close"` in 4 chunks of up to 85 at `-n 4` under the 5 GB cap behind the full-suite lock: 6,404 passed, 26 skipped, 0 failed.
- **Identity pins:** unmoved. K2-16 moves no pinned identity (no pin builds a neighbourhood).
- **Structure ratchets:** no number moved (functions over 200 lines in the two files stay `_normalize` and `_normalize_append`).
- **Lint:** `lint-imports --no-cache` 42 kept; `ruff check` clean.
- **Vault validators:** all four pass. **Gate partition:** 30,828 collected (landing 30,768 + arc_close 60).
- **Regeneration:** after the source commits (`62558179d3`); a second run changed nothing.
- **Not run:** the full suite and the durability lane (the orchestrator's landing gate).
