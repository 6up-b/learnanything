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
