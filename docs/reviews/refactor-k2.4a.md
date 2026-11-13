# Refactor K2.4a: one synthesis tail, two modes

Branch `refactor/k2.4a-shared-synthesis-tail`, based on main `655e7a2d07` (K2.1-K2.3 and the phase 1 review's
ingestion fixes I1-I8 landed). Step K2.4a of arc K (`docs/specs/refactor_strategy_v3.md` §2.17), specified in
`docs/reviews/k2-ingestion-strategy-2026-11-11.md` §3.2 (K2.4, first of three sub-steps) from the K2 map's KP5 and KH1.
Structure track: no persisted row, proposal, gate verdict, auto-apply set or model request changes for either mode.

## Step 0: the two tails side by side

Both orchestrators, after their heads have opened the run (inputs, brief, scope, manifest, agent run and synthesis
run rows: K2.4b's), do the same thing in the same order: ask the model, plan facet identity, normalize, run the
synthesis gates and the instrument gates, compare with earlier proposals (K2.3), persist, finalize the run rows, apply,
and write epigraphs. Bootstrap is `_create_study_map` with `_gate_and_persist` in
`content/synthesis/source_set_synthesis.py` (S below); append is `_append` with `_normalize_append` in
`content/synthesis/source_append.py` (A below). Line numbers are at the base `655e7a2d07`.

Classes: **(i)** intended by the mode: it becomes an explicit input of the shared function, named for what it means.
**(ii)** drift with the same behaviour on every input: unified. **(iii)** drift whose behaviour differs and that no spec
settles: both kept exactly (the mode decides) and a ledger row filed for the behaviour track.

| # | Stage | Bootstrap (S) | Append (A) | Difference | Class |
|---|---|---|---|---|---|
| 1 | Retry after a wholly rejected match | `for fresh_answers in (False, True)` S:2300; the gate stage raises `RejectedProposalMatch` S:2523-2525, caught S:2331-2334 | same loop A:576; inline `continue` A:655-659 | control flow only | (ii) |
| 2 | The model call | `_run_synthesis` under `declared_budgets` S:2301-2308 (shards, passes, structuring) | `_run_reconciliation` through `_AppendCall` A:577-581 | the mode's call (K2.4c merges them) | (i) |
| 3 | Answers dropped after a rejected match | `answers.discard` then a new `_SavedAnswers` S:2332-2333 | `call.discard_answers()`, the list kept A:657 | append's later drop names the first attempt's answers again; it deletes something only if the store holds that exact text again (another run saved the identical answer between the two attempts) | (iii) K2-15 |
| 4 | Usage drained from the client | right after each model call S:2309, and again in the failure arms S:2351, S:2363; the agent run gets that sum (`usage=token_usage`) | never drained early: `finish_agent_run(..., client)` drains at the end A:668, A:704, A:715, A:721 | bootstrap's agent run excludes calls on the same client after the model call (the instrument gates' persona fires); append's includes them | (iii) K2-13 |
| 5 | Narrow-adjunct preset | none | drops model restructures with a `narrow_adjunct` review diagnostic A:582-604 | restructures exist only in the append vocabulary | (i) |
| 6 | Facet identity plan | `_facet_identity_plan(merged, ..., progress=progress)` S:2310-2313 | `_facet_identity_plan(SourceSetSynthesis(concepts, facets), ...)`, no progress A:607-613 | `build_plan` reads only `concepts`, `concept_relations` and `facets` (`facet_identity/plan.py:138-166`); the reconciliation has no `concept_relations`, the subset has them empty; append has no progress, so `None` | (ii) |
| 7 | Facet identity usage | joins `usage` at once S:2314-2315, so every later completion records it | `actual_usage = {"facet_identity": ...}` only when a proposal is written A:688-699; a matched or failed run records none | `synthesis_runs.actual_usage` of an append that matched or failed after the plan | (iii) K2-11 |
| 8 | Candidate kept for repair | `save_synthesis_candidate` S:2316-2320; a typed failure then carries `candidate_preserved` and the run id S:2337-2339, S:2470, S:2499 | none | only bootstrap has the zero-model repair (`revalidate_synthesis_candidate`) | (i) |
| 9 | Normalize | `_normalize(merged)` S:2458-2461 | `_normalize_append` A:614-626, A:823-1046: `_normalize` over the new-coverage part, then provenance links (with §10.3's auto-apply ids), notation mappings, conflicts and restructures | the append's additions; its `neighborhood` parameter (A:823) is never read | (i); the unused parameter (ii) |
| 10 | Duplicate client ids | typed `duplicate_client_item_ids` hard fail with diagnostics, candidate preserved S:2462-2471 | no check: `persist_proposal_batch` raises a bare `ValueError` (`db/repositories.py:11175`), the generic arm fails the run with no diagnostics | a model answer repeating a client id | (iii) K2-10 |
| 11 | Identifiability | `analyze_identifiability` over the proposal view S:2476-2481: review diagnostics through the gate hook, and generation needs persisted S:2539-2540 | findings `[]` A:628: no identifiability diagnostics, no generation needs | an append's new facets are never checked for identifiability | (iii) K2-9 |
| 12 | Gate context | `_gate_context(..., findings)` S:2482 | the same with `[]`, then `append_mode = True` A:628-629 | the append vocabulary gate | (i) (findings: row 11) |
| 13 | Gate proposal | from `_Normalized` S:2483-2487 | from the normalizer's tuple A:630-634 | same fields | (ii) |
| 14 | Gate diagnostics | report, then `normalized.edge_diagnostics` S:2489-2490 | report, normalizer diagnostics, preset diagnostics A:636-638 | same order with the answer's own diagnostics last | (ii) |
| 15 | Gate hard fail | `_fail` (both run rows failed), then `StudyMapError("synthesis_gate_failed", "Synthesis proposal failed hard quality gates.", run id, candidate_preserved)` S:2492-2500 | `StudyMapError("append_gate_failed", "Append proposal failed hard quality gates.")` A:639-641; the outer arm fails the rows | code and message (i); run id and preserved flag follow row 8 (i); the inner `_fail` writes what the outer arm rewrites, so the final rows are equal (ii); `_fail` stays because revalidation has no outer arm | (i), (ii) |
| 16 | Instrument gates | `build_instrument_gates(vault, repository, grading_client=client)` over the rows S:2512-2518 | identical A:646-650 | none | (ii) |
| 17 | Proposal match | `match_proposal(purpose=sourceset_bootstrap)` S:2520-2526 | `purpose=sourceset_append` A:652-660 | each mode matches its own proposals | (i) |
| 18 | Matched completion | `complete_synthesis_run(completed, proposal_id, resolved_span_hashes, {gate_diagnostics, matched_proposal}, actual_usage=usage)`; `finish_agent_run(usage=token_usage)` S:2527-2536 | `{gate_diagnostics, auto_apply_item_ids, matched_proposal}`, no hashes, no usage; `finish_agent_run(client)` A:661-668 | `auto_apply_item_ids` (i, the append's auto-apply lane); hashes (iii K2-12); usage (iii K2-11); drain (iii K2-13) | (i), (iii) |
| 19 | Generation needs | persisted first S:2539-2540 | none | follows row 11 | (iii) K2-9 |
| 20 | Persist | `persist_proposal_batch(purpose, summary or "bootstrap study map for {subject}")` S:2543-2556 | the same with `"append reconciliation for {subject}"` A:670-682 | values | (i) |
| 21 | Coverage record | `gate_diagnostics`; `graph_nomination` while nominations are on; facet identity with `origin="ingest"` S:2557-2571 | the same plus `auto_apply_item_ids`; `origin="append"` A:683-698 | values | (i) |
| 22 | Completion | with `resolved_span_hashes` and `usage` S:2572-2578 | no hashes; usage as row 7 A:700-704 | append drops its span round's hashes (`_resolved, _hashes`, A:805) | (iii) K2-12, K2-11 |
| 23 | `StudyMapError` arm | stamps candidate and run id; drops answers on `synthesis_gate_failed`; rows failed with `gate_diagnostics` and `actual_usage=usage`; drains S:2336-2360 | drops answers on `append_gate_failed`; rows failed with `gate_diagnostics`, no usage; `finish_agent_run(client)` A:705-717 | code (i); stamps (i, row 8); usage (iii K2-11); drain (iii K2-13) | (i), (iii) |
| 24 | Other exceptions | run failed, no coverage; drain; finish S:2361-2368 | the same with `finish_agent_run(client)` A:718-724 | drain only (row 4) | (iii) K2-13 |
| 25 | Item counts | `_count_items` S:3801 | `_count` A:1282 | identical functions | (ii) |
| 26 | Apply | `apply and not nothing_new and apply_gate`: the whole proposal, then the exam goal (`_apply_and_wire_goal`) S:2381-2385 | auto/review split (waiting items on a match) A:726-735; `auto_apply and auto_ids and apply_gate`: §10.3's routine items, the study-map diff, the facet doctor A:750-766 | what each mode applies and what follows | (i) |
| 27 | Matched run | returns before facet identity and epigraphs S:2386-2389 | identical A:768-771 | none | (ii) |
| 28 | Facet identity result | `facet_identity_result` S:2390 | identical A:772 | none | (ii) |
| 29 | Epigraphs | `mode="bootstrap"`, `digest_from_proposal_rows(rows, summary)` S:2396-2404 | `mode="append"`, `digest_for_append(rows, new inventories, neighbourhood, summary)` A:777-786 | an append may emit only links, so its digest is topped up | (i) |
| 30 | The rows' subject | `resolve_subject_id(source_set, vault)` S:2324 (an empty `subject_id` becomes the vault's first subject); the result and epigraphs use `source_set.subject_id` | `source_set.subject_id` everywhere A:481 | a source set whose `subject_id` is empty | (iii) K2-14 |
| 31 | Progress | `_notify` at facet identity, validation, gates and persistence | no `progress` parameter, so `None` | none | (ii) |
| 32 | Items off | `resolve_brief` then `practice_items == "as_you_read"` S:2214-2215; `_normalize` drops items | identical A:484-485, through `_normalize_append` | none (K2.3 unified it) | (ii) |
| 33 | Switches and config the tail reads | `facet_identity.enabled` (plan), graph nomination (the nominator), the instrument gates' config, the epigraph service's switches, `apply_gate`; `create_goal` and the exam brief | the same; and `brief.authoring_preset` (row 5) | as rows 5 and 26 | (i) |

**Totals** (33 rows; a row counts once for each class it contains):
- **(i)** 14 rows: 2, 5, 8, 9, 12, 15, 17, 18, 20, 21, 23, 26, 29, 33.
- **(ii)** 12 rows: 1, 6, 9, 13, 14, 15, 16, 25, 27, 28, 31, 32.
- **(iii)** 11 rows, which come to 7 distinct behaviours, ledger K2-9 to K2-15: rows 3 (K2-15), 4 and 24 (K2-13),
  7 (K2-11), 10 (K2-10), 11 and 19 (K2-9), 22 (K2-12), 30 (K2-14); rows 18 and 23 repeat K2-11, K2-12 and K2-13 at
  other completions.

What append adds beyond bootstrap, all kept as the append's: the provenance-link, notation-mapping, conflict and
restructure items with §10.3's auto-apply predicate (row 9), the narrow-adjunct preset (row 5), the neighbourhood (its
head's; it reaches the tail only through the epigraph digest, row 29), the study-map diff and the facet doctor
(row 26).

## What each difference became

| Row | Outcome |
|---|---|
| 1 | One loop, in `finish_synthesis_run`; the gate stage raises `RejectedProposalMatch` for both modes. |
| 2 | The mode's `ask`: bootstrap's `_run_synthesis` under `declared_budgets`; append's `_run_reconciliation` and its preset. Both return a `SynthesisAnswer`. |
| 3 | Kept: the mode's `drop_answers`. Bootstrap's is `_SavedAnswers.discard`, which now forgets what it dropped (the reset after a rejected match did that); append's is `_AppendCall.discard_answers`, unchanged. K2-15. |
| 4, 24 | Kept: `SynthesisMode.meters_the_model_call`. A metered run drains after each answer and passes its sum; an unmetered one passes `usage=None` and its client, so `finish_agent_run` drains at completion. K2-13. |
| 5 | `_within_preset`, inside the append's `ask`; its record is `SynthesisAnswer.diagnostics`. |
| 6 | Unified: facet identity reads the answer itself; progress comes from the run (append has none). |
| 7 | Kept: `SynthesisMode.usage_only_with_a_proposal` (the matched completion, the gate stage's `_fail` and the failure arm record no usage for append). The usage itself is computed one way for both: the answer's own record (append: none) plus the facet-identity plan. K2-11. |
| 8 | `SynthesisMode.keeps_candidate_for_repair`; the gate failure's run id and preserved flag follow it. |
| 9 | `SynthesisMode.normalize`. `_normalize_append` returns `_Normalized` (with the new `auto_apply_ids` field) and drops its unread parameter. |
| 10 | Kept: `SynthesisMode.checks_client_id_collisions`. K2-10. |
| 11, 19 | Kept: `SynthesisMode.analyzes_identifiability`; with no findings, `_persist_generation_needs` writes nothing, as before. K2-9. |
| 12 | `SynthesisMode.append_vocabulary`, passed to `_gate_context(append_mode=...)`. |
| 13, 14, 16 | Unified in `_gate_and_persist`: the gate proposal from `_Normalized`; diagnostics are the report, the normalizer's records, the answer's records, then the instrument gates'. |
| 15 | `SynthesisMode.gate_failure`. The gate stage's own `_fail` now also runs for append; the failure arm completes both rows again, so the final rows are those the append wrote before. `_fail` passes no client, so it never drains an unmetered client before the arm does. |
| 17, 20, 21 | `SynthesisMode.proposal_purpose`, `summary_fallback`, `facet_action_origin`; the coverage records `auto_apply_item_ids` exactly when the normalizer returns them (append), on a match too. |
| 18, 22 | As rows 4, 7 and 17; the hashes are `SynthesisAnswer.resolved_span_hashes`, `None` for append (K2-12). |
| 23 | One arm reading the mode (gate-failure code, the kept candidate, the usage rule, metering). |
| 25 | `_count` deleted (proof below). |
| 26 | The mode's `apply`: `_apply_map` for bootstrap (the apply and goal wiring `_apply_and_wire_goal` did; that function stays for revalidation and delegates), `_apply_routine_items` for append (the auto/review split, §10.3's lane, the diff and the facet doctor). Each returns the fields it adds to its result. |
| 27, 28 | In the tail. |
| 29 | `SynthesisMode.epigraph_mode` and `SynthesisRun.digest_extras` (append: its new inventories and neighbourhood context; bootstrap: none, so the rows' digest). |
| 30 | Kept: `SynthesisMode.resolves_an_empty_subject`, evaluated where bootstrap evaluated it (inside the failure arms, after the candidate is kept), so even its `missing_subject` failure finalizes the same rows. K2-14. |
| 31, 32 | Unified: progress on the run; items off read from the resolved brief in the tail. |

## The shape

- **`finish_synthesis_run(run, mode, *, ask, drop_answers, apply)`** in `content/synthesis/source_set_synthesis.py`, beside `_gate_and_persist`, which it calls and which candidate revalidation also calls. That module is where it reads best: it already holds the normalizer, the gate stage, the answers store and `StudyMapError`, and `source_append` imports from it (the reverse import would be a cycle).
- **`SynthesisMode`**, a frozen record with two rows (`BOOTSTRAP` here, `APPEND` in `source_append`): side by side they are the table of what the modes decide differently. Five fields are kept differences and say so.
- **`SynthesisRun`**, the frozen input record: what the head opened (vault, repository, source set, inputs, resolved brief, run ids, clients, nominator, progress, the epigraph digest's extras).
- **`SynthesisAnswer`** (what `ask` returns) and **`SynthesisOutcome`** (what the tail returns): return values.
- **Three callables, each the mode's own behaviour:** `ask` and `drop_answers` are the mode's model call and the answers it saved (bootstrap's shards and passes; the append's call and span round). K2.4c puts the append through the shard runner, and both become one. `apply` is what each mode applies after persisting and what follows it (bootstrap: the whole proposal and the exam goal, when asked; append: §10.3's routine items, then the diff and the facet doctor). The owner's open auto-apply call (KX4) changes only the append's. The normalizer is a field of the mode row, not a per-run callable.
- **Not added:** no strategy class, registry or protocol. `_create_study_map` and `_append` keep their heads (K2.4b) and their calls (K2.4c), and build their own result from the outcome.

## Deletion proofs (strategy §2.1)

- **`source_append._count`** (deleted in `36bafabe90`): its one caller was `_append`'s result. `git grep -nw _count` over `src`, `tests`, `scripts` and `apps` finds no other reference to it (one unrelated test helper of the same name in `tests/test_notes_linked.py`, its own). It is private, so no `importlib`, Typer, `METHOD_REGISTRY`, `MODULE_INVENTORY` or `_reg_const` entry names it; no frontend, replay, rebuild or upgrade path reads proposal construction. `_count_items` is the same function.
- **`_append`'s gates, instrument gates, proposal match, persist block, failure arms, apply block and epigraph call** (`5d8d117dfd`, `67827d0ecd`): inline code, not functions; `_gate_and_persist` and `finish_synthesis_run` run it, as the goldens show.
- **Nothing else is deleted.** `_apply_and_wire_goal` stays (revalidation and `test_decider_landing` call it) and delegates to `_apply_map`. The append module no longer imports `run_synthesis_gates`, `GateProposal`, `match_proposal`, `_gate_context`, `_facet_identity_plan`, `facet_identity_result`, `finish_agent_run` or the epigraph functions; each is still defined where it was.

## Goldens (P-golden)

`tests/test_synthesis_tail_golden.py`, 13 cases, files under `tests/goldens/synthesis_tail/`, committed at the base (`91afb45416`) and run after every later commit, which left them unchanged. One later commit (`22107d0c95`) changed only the harness: the vault's algorithm tag and the manifest hash that folds it in became placeholders, so a successor tag landing elsewhere does not fail them. The files were regenerated with the base's sources checked out (`git checkout 655e7a2d07 -- src`, then back), the only differences were those placeholders, and they pass unchanged at the tip. They passed under `PYTHONHASHSEED` 0-7 and under `-n 4`.

| Case | Mode | Covers |
|---|---|---|
| `bootstrap_clean_applied` | bootstrap | a clean run with an exam source, applied, with the exam goal |
| `bootstrap_gate_fails` | bootstrap | a vacuous recipe the synthesis gates hard-fail (`synthesis_gate_failed`, candidate kept) |
| `bootstrap_instrument_gate_holds` | bootstrap | a selected-response item the instrument gates mark invalid |
| `bootstrap_items_off` | bootstrap | `practice_items = as_you_read`, applied |
| `bootstrap_rerun_waiting` | bootstrap | a rerun equal to the waiting proposal, applied (K2.3's match) |
| `bootstrap_rerun_rejected` | bootstrap | a rerun after the whole proposal was rejected: answers dropped, paid again, persisted |
| `append_clean_applied` | append | a link (auto-applied), a notation mapping and a conflict (reviewed); diff and facet doctor |
| `append_gate_fails` | append | an exam-only facet reword the gates hard-fail (`append_gate_failed`) |
| `append_instrument_gate_holds` | append | a selected-response practice item, upfront |
| `append_items_off` | append | a practice item dropped by items off |
| `append_rerun_waiting` | append | a rerun equal to a waiting append, with auto-apply: its waiting link applies |
| `append_rerun_rejected` | append | a rerun after the whole append was rejected |
| `append_narrow_adjunct` | append | the preset drops a model restructure, with its review record |

Each record holds every row the build added, changed or removed, table by table (proposal batch, items with their validation and instrument-gate audit, dependencies, manifest, agent and synthesis runs with recorded tokens, checkpoints, shard results, generation needs, links, change batches, epigraphs, and the rows an apply writes), the vault files it changed, the model requests in order (purpose and prompt digest), and the result or typed error. Ids are reproducible (the process's ULID stream seeded, its clock held); wall-clock stamps read `<wall>`. The fake client reports 100 input and 10 output tokens per request, so the agent runs' recorded tokens show where each mode drains.

**Not covered by the goldens:** K2-13 (no item carries persona material, so no instrument-gate call is made on the client); K2-10 and K2-14 (a duplicate client id, an empty subject); the facet-identity judge answering (it is unavailable in every case, so the plan is `judge_unavailable` and no action rows are written). Those paths are kept by reading the code: each is one mode field.

## Tests changed

- `tests/test_synthesis_answer_reuse.py::test_an_append_rejection_keeps_a_fresh_answer_another_run_saved` patched `source_append.run_synthesis_gates`, which the append no longer calls (T4). Ported to plain values: the fake's first answer asks for a span round; its second (the span round) simulates the other run (drop the first answer's checkpoint and save a fresh one under the key) and answers an exam-only reword the gates reject. Its assertion is unchanged: one stored answer, the fresh one. It still fails when a discard drops by key alone (checked with a throwaway plugin that ignores the stored form).
- No assertion changed. The bootstrap tests that patch `source_set_synthesis._gate_and_persist` and `_facet_identity_plan` keep working: both names stay in that module, called from the tail by the same names.

## Measures

| | base `655e7a2d07` | tip |
|---|---|---|
| `source_set_synthesis.py` lines | 3,897 | 4,108 |
| `source_append.py` lines | 1,310 | 1,205 |
| both | 5,207 | 5,313 |
| `_create_study_map` | 216 | 140 |
| `_append` | 330 | 146 |
| `_gate_and_persist` | 172 | 187 |
| `finish_synthesis_run` | none | 123 |
| functions over 200 lines in the two files | 4 (`_normalize` 1,081, `_append` 330, `_normalize_append` 224, `_create_study_map` 216) | 2 (`_normalize` 1,081, `_normalize_append` 221) |

The two files grow by 106 lines together: the tail's records carry a line of documentation per field (`SynthesisMode` alone is about 50 lines with its two rows), and `_apply_map` and `_apply_routine_items` are named functions now. The copy is gone: the tail's stages exist once.

## Judgment calls

1. **The loop is in the tail.** Apply and epigraphs belong to the tail and must run outside the failure arms (a failed apply leaves the run completed), so the arms, and with them the loop and the model call they cover, are the tail's. The mode supplies the call as `ask`.
2. **Three callables** (`ask`, `drop_answers`, `apply`), each justified above; the normalizer is a mode field. A value could not replace any of them: each is behaviour that differs by mode and runs at a point the tail decides.
3. **`apply` returns the fields it adds to the mode's result,** so each orchestrator builds its result once from the outcome, and the tail knows neither result type.
4. **Four records, not one.** `SynthesisMode` (static, two rows) and `SynthesisRun` (per run) are the input; `SynthesisAnswer` and `SynthesisOutcome` are return values. Folding the mode into the run would make every run restate the table; tuples for the returns would be harder to read than the two small records.
5. **Kept differences are mode fields named for what they mean,** not branches on a mode name: five booleans (`checks_client_id_collisions`, `analyzes_identifiability`, `meters_the_model_call`, `usage_only_with_a_proposal`, `resolves_an_empty_subject`), each read in one or two places. The shared function stays shorter than the two copies were, so no stop was needed.
6. **Row 15:** the append now passes through the gate stage's own `_fail` before its failure arm. The final rows are equal (the arm rewrites status, error, coverage and usage), and `_fail` passes no client so an unmetered client is drained once, by the arm.
7. **Row 3:** `_SavedAnswers.discard` forgets what it dropped, in place of the orchestrator's reset; equal on every input.
8. **Row 6:** the append's facet identity reads its answer, not a two-field copy; `build_plan` reads only `concepts`, `concept_relations` and `facets`.
9. **The goldens' append vault** is the house `_bootstrap_and_add` without the inventory's alias, because the neighbourhood's record otherwise follows the process's hash seed (K2-16, filed). The golden harness seeds the ULID stream through `learnloop.ids`' private clock and randomness, as `tests/hint_telemetry_helpers.py` and `tests/ad23_contract_helpers.py` already do.
10. **The vault note** describes the shared tail and the kept differences; its other K2.4 lines (`:55`'s example, `:60`'s routing rule) are K2.4b's.

## Ledger

- **K2-9 to K2-15** (new): the seven kept differences, open for the behaviour track, due at arc K's close.
- **K2-16** (new): the append neighbourhood's set order, found writing the goldens; a small fix, open.

## Gates

- **Targeted tests.** `scripts/affected_tests.py --base 655e7a2d07` chose 318 files; with the rules block's list and the files this step adds or edits, 327, run at `164796fc5d` with `-m "not arc_close"` in 4 chunks of up to 100 at `-n 4` under the 5 GB cap behind the full-suite lock: 6,359 passed, 26 skipped, 0 failed. After the later test-only and docs commits: the goldens, `test_structure_ratchets`, `test_identity_pins`, `test_test_layout`, `test_architecture`, `test_module_catalog_inventory` and the synthesis files again, all passed.
- **Identity pins:** unmoved.
- **Structure ratchets:** lowered (`bb440f7c1e`): functions over 200 lines 82 to 79 (`_append`, `_create_study_map`, and `remediation.reschedule_assisted_cold_retry`, already under 200 at the base); stage-artifact comment lines 2,398 to 2,395 (two in the moved synthesis code, one in `jobs.py` already gone at the base).
- **Lint:** `lint-imports --no-cache` 42 kept; `ruff check` clean.
- **Vault validators:** all four pass. **Gate partition:** 30,848 collected (landing 30,788 + arc_close 60).
- **Regeneration:** after the source commits (`e74bd3639f`), again after the goldens' harness change touched the test references (`e81be18d6a`); a third run changed nothing.
- **Not run:** the full suite and the durability lane (the orchestrator's landing gate).

## Open items

- K2-9 to K2-16 (above).
- The goldens do not exercise K2-10, K2-13, K2-14 or a facet-identity judge that answers (see "Not covered").
- K2.4b (one head) and K2.4c (the append through the shard runner) follow; K2.4c removes `ask`, `drop_answers` and K2-12, K2-15 with them.
- The Build a Study Map note's `:55` example and `:60` routing rule are K2.4b's.
