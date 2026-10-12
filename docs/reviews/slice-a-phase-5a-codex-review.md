# Slice A Phase 5a: Codex review fixes

**Branch:** `slice-a/phase-5a` (worktree `learnanything-phase-5a`), on top of `7de892b2`.
Not rebased, not merged, not pushed.

**Review:** Codex job `20261012-130618-jLufcp` over the Phase 5a branch: fourteen findings
(5 High, 9 Medium) and seven claims in `slice-a-phase-5a.md` that did not hold.

**Result:** all fourteen are fixed; none rejected. Each was reproduced first: at least one
new or changed test per finding fails on the code before its fix (F2, F5 and F12 were
also reproduced with throwaway scripts before the new APIs existed; noted below). A few
extra tests are guards that also pass before. The seven claims now hold (table below).
The gate passes; the numbers are under Gate results.

## Findings

| ID | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | Codex solver and closed-book calls can read the vault | Fixed | `4fbac362` | `test_pf_generation.py`: `test_every_pf_request_reaches_its_transport_as_an_isolated_turn`, `test_a_route_that_cannot_isolate_is_refused_before_any_request`, `test_a_codex_pf_turn_starts_outside_the_vault_with_tools_off_and_never_reuses_unisolated_work` |
| F2 | High | An unrelated quote makes a false reference "verified" | Fixed | `3274ce7a` | `test_pf_generation.py::test_an_unrelated_or_contradicted_quote_never_verifies_a_reference`; two real calls (below) |
| F3 | High | Freshness overrides the mandatory structure check | Fixed | `565077c9` | `test_pf_generation.py`: `test_freshness_never_restores_isomorph_over_a_failed_structure_check[isomorph,near]`, `test_an_isomorph_verdict_without_preserved_checkpoints_is_never_a_final_isomorph` |
| F4 | High | Multiple skeleton versions break rebuilds | Fixed | `07bf0342` | `test_item_fingerprints.py`: `test_skeletons_from_one_model_at_two_prompt_versions_rebuild_without_a_key_collision`, `test_a_published_item_later_used_as_the_parent_rebuilds` |
| F5 | High | Publication uses an unverified, potentially changed parent contract | Fixed | `72a15819` | `test_pf_generation.py::test_a_selection_whose_parent_contract_changed_is_never_published[rubric,facets,family_undo]` |
| F6 | Medium | Publication recovery can erase existing practice state | Fixed | `c9cfc276` | `test_pf_generation.py::test_publication_recovery_never_erases_scheduling_state` |
| F7 | Medium | New rounds reuse the previous proposal batch forever | Fixed | `ec8f75c2` | `test_pf_generation.py::test_a_new_round_asks_the_proposers_again_with_its_own_generation_seed` |
| F8 | Medium | Embedding cache silently mislabels larger dimension sweeps | Fixed | `0945ac38` | `test_embedding_compare.py::test_a_larger_dimension_sweep_never_reuses_narrower_cached_vectors` |
| F9 | Medium | Paid harness dry runs omit cost and budget admission | Fixed | `f47c31aa` | `test_embedding_compare.py::test_compare_dry_runs_estimate_cost_and_admit_the_whole_plan`, `test_pf_reports.py::test_report_dry_runs_price_and_admit_the_blind_judge` |
| F10 | Medium | Valid-alternative evaluation ignores failed negative controls | Fixed | `eb89474b` | `test_embedding_compare.py::test_valid_alternative_suite_rejects_a_degenerate_equivalence_check` (guard: `test_pf_generation.py::test_a_degenerate_equivalence_check_verifies_no_ensemble_candidate`) |
| F11 | Medium | Frontier generator trials reuse the cheap model's program | Fixed | `47e10f66` | `test_pf_reports.py::test_each_scaling_tier_runs_its_own_program_writer_on_identical_inputs` |
| F12 | Medium | Scaling rewards false-positive freshness judgments | Fixed | `983ab3f1` | `test_pf_reports.py`: `test_suspect_acceptance_is_descriptive_and_never_ranks_a_tier`, `test_judge_accuracy_comes_from_labelled_pairs_judged_at_both_tiers` |
| F13 | Medium | The pilot recommends a winner with zero judged pairs | Fixed | `07156010` | `test_pf_reports.py`: `test_pilot_never_recommends_a_path_without_usable_comparisons`, `test_pairs_never_cross_families_or_frozen_inputs`, `test_pilot_recommends_only_from_agreed_comparisons_on_the_same_families` |
| F14 | Medium | Filter verdicts remain authoritative only in workflow JSON | Fixed | `8d2dffc2` | `test_pf_generation.py`: `test_every_filter_and_selection_decision_is_ledgered[ensemble,generator]`, `test_pilot_report_verdicts_come_from_the_ledger_not_workflow_json`, `test_publication_reads_the_ledger_so_forged_workflow_state_cannot_publish` |

`fa383eac` regenerates the DB and config references (validator: 0 errors on the final
tree). `15634fb3` is a readability follow-up to F9 (an explicit `refused` flag in the
reports), with no behaviour change.

## What changed, per finding

### F1: every PF role is an isolated, tool-free turn (High)

- **Reproduced.** Every PF request reached its transport with `isolated=False`; a route
  that cannot isolate was used; a checkpoint written under the old key was reused.
- **Fix** (`ops/pf_calls.py`).
  - `PFCaller.call` always sends `isolated=True` (the `isolated` parameter is gone). A chat
    completion (OpenRouter, OpenAI) is isolated by construction; a Codex route starts the
    turn in an empty directory outside the vault under LearnLoop's permission profile, with
    the shell, unified exec and every MCP server off.
  - A route that cannot declare `ISOLATED_TURN` is refused before admission (no request,
    retry or charge), at resolution and again at call time.
  - `ISOLATION_BOUNDARY` is part of every checkpoint key, so results produced without the
    boundary are never reused.
- **Transport test.** A real `SdkCodexClient` with a stand-in SDK: the turn's cwd is an
  empty directory outside the vault and the launch carries the isolation overrides.

### F2: the cited span must support the key (High)

- **Reproduced** with the reviewer's case: source "We chose A for accuracy", answer "For
  speed" was `verified`.
- **Fix** (`ops/pf_generation.py`, `content/authoring/pf_contracts.py`).
  - New role `span_support` on route `pf_reference_verifier` (a verifier, not tiered),
    prompt `pf-span-support-v1`, contract `SpanSupportVerdict`. The verifier reads only the
    cited span, writes what the span answers first, then judges whether the span states or
    entails the answer and supports the explanation.
  - Verified only when the quote is verbatim (and complete) **and** the span supports the
    answer and the explanation. `verification_check` is `quote_verified_span+support`.
  - What-if items: an executable consequence (the verifier's call) needs the execution
    check, which is not built, so that reference stays unverified (§5.3).
  - A why-item the span does not support is relabelled `inferred` (provenance) and never
    published.
  - Ledger: `reference_verified` keeps the exact-key quote row and adds the `llm` support row.

### F3: a final isomorph needs a passing checkpoint-preservation check (High)

- **Reproduced** with a freshness judge that calls the parent isomorphic while the
  structure check finds changed checkpoints. (The original fake freshness judge could not.)
- **Fix.**
  - In `_structure`, an `isomorph`/`same_target` verdict without preserved checkpoints counts
    as `near`. This also closes a second path: a declared `near` judged `isomorph` with
    changed checkpoints used to become `isomorph`.
  - In `_freshness`, the relabel to `isomorph` applies only when the structure check
    confirmed it. Otherwise the detail records `isomorph_relabel_refused`.
  - Any final `isomorph`/`same_target` without that confirmation is an assertion error.
  - Publication checks the same rule from the ledger (F14).

### F4: one skeleton key per persisted skeleton (High)

- **Reproduced.** The real migration and the replayer raised `IntegrityError`, for two
  skeletons from one model at two prompt versions, and end to end when a published item
  became the parent and the proposer and skeleton writer were the same model.
- **Fix.** The component is `skeleton:<model>@<prompt version>`, which is unique per
  `item_skeletons` row. Cross-model and cross-version matching is unchanged
  (`shared_keys`). Fingerprint version `pf-fingerprint-v2`.

### F5: publication revalidates the judged inputs under the vault lock (High)

- **Reproduced** with a throwaway test: after a rubric edit, `pf publish` the next day
  published the selection with the new rubric.
- **Fix.**
  - Each candidate stores its run's judged inputs, `pf_candidates.judged_inputs_json`
    (migration 169, fixed at insert):
    - the parent contract hash (every field publication copies or the judges saw, plus the
      effective rubric and surface group);
    - the effective rubric hash;
    - the parent's family membership;
    - the family revision (LO, idea, retrieval target).
  - `publish_candidate` takes the shared `vault_mutation_lock`, reloads the vault inside it
    and compares.
  - A stale selection is ledgered (`pf_publish`, verdict `refuse_stale`, with what
    changed), marked `rejected`/`stale_judged_inputs` and leaves the backlog; regenerate to
    retry. `publish_selected` reports `stale_candidates` and goes on.
  - A publication whose item file is already written resumes as is.
  - A family undo keeps the family record, but it removes the parent's membership, so it is
    caught.

### F6: scheduling state is initialized only when absent

- **Reproduced.** A crash between the item file and the published mark, then practice
  recorded by the sidecar: the retry nulled stability, due date and last attempt.
- **Fix.**
  - `Repository.initialize_practice_item_state` inserts with `ON CONFLICT DO NOTHING`.
  - Publication uses it, including on the already-published recovery path. A crash
    between the published mark and initialization is completed by the retry.

### F7: a per-job generation seed

- **Reproduced.** Round r2 sent zero proposer requests, served from r1's checkpoint.
- **Fix.**
  - The proposer, single-shot and source-anchored prompts carry `generation_seed`. It is
    derived from the job identity (family, path, relation, round, tier, count).
  - A resumed job sends identical requests and reuses its checkpoints; a new round asks for
    new material.
  - Prompt versions: `pf-ensemble-propose-v2`, `pf-single-shot-v2`, `pf-source-anchored-v2`.

### F8: the vector cache is keyed by width and configuration

- **Reproduced.** A 64-dim run reusing a 16-dim run's output directory never called the
  embedder.
- **Fix.**
  - `VectorCache(root, model, task_prefix, *, dims, config)` is one directory per (model,
    task prefix, requested width, embedding config), validated on load.
  - A provider that returns narrower vectors than requested is refused before caching
    (`provider_failed`).
  - `centered_cosines` raises on vectors narrower than the requested width.

### F9: dry runs price and admit the whole plan

- **Reproduced.** The valid-alternative dry run showed zero LLM tokens, and the pilot
  dry-run judge estimate had `estimated_usd=None` with a price supplied.
- **Fix.**
  - The valid-alternative plan estimates input plus output tokens per role from the real
    prompts.
  - `run_compare` resolves each planned role's billing class from its profile, without
    building a client. It prices metered LLM and embedding work and calls
    `PFCaller.check_plan` on the whole plan, in dry runs and before a run:
    - unknown metered prices fail closed;
    - Codex roles are `subscription`, `estimated_only`, with tokens and dollars recorded,
      not capped.
  - The report shows `estimate.metered`, `estimate.subscription`, the billing per role and
    the cost basis.
  - The pilot/scaling blind judge gets the same treatment: `judge_estimate` with dollars,
    billing and cost basis. A refused real run sends and writes nothing.

### F10: the suite applies the production degenerate-check rule

- **Reproduced.** With a sycophantic verifier and an always-true check, the wrong "999"
  alternative entered the "CAS-verified" suite.
- **Fix.**
  - One helper, `pf_sandbox.equivalence_confirmations`, decides confirmations for both
    callers: a check that accepts a negative control confirms nothing.
  - The suite ledgers `degenerate_check` and reports `degenerate_checks`.

### F11: each tier runs its own program writer on frozen inputs

- **Reproduced.** The frontier writer received no request.
- **Fix.**
  - A `--tier` run is a measurement. It neither reads nor stores the family's authored
    program.
  - Each tier's writer writes its own program from the same inputs: parent, family and a
    parent skeleton that is no longer a tiered role, so both tiers share it. The
    verifiers stay fixed as before.
  - The program persists through the writer call's checkpoint (keyed by tier route,
    model/settings, prompt version and inputs).
  - It is recorded as `tier_program` (tier, model, hash, prompt version,
    `inputs_revision`) in the run report and the `generator_tests` ledger rationale.

### F12: judges are scored only against independent labels on identical pairs

- **Reproduced** with a throwaway test: an always-isomorph frontier freshness judge gave
  `freshness_judge: rises_with_tier` (cheap 0/10, frontier 10/10).
- **Fix.**
  - Suspect acceptance and the structure judge's isomorph rate on program draws (positive
    labels only) move to `judge_agreement.descriptive`, marked "not judge accuracy or
    quality". They never rank a tier.
  - Judge accuracy now comes from B2. `learnloop embeddings compare --suite b2 --view judge
    --tier cheap|frontier` runs the freshness judge at a tier and ledgers the tier.
  - The scaling report's `judge_accuracy_on_labelled_pairs.freshness` scores each tier on
    the B2 cases both tiers judged: accuracy, recall on positives, false-positive rate.
  - `components.freshness_judge` uses that accuracy. `components.structure_judge` is
    `insufficient_data` until labelled structure pairs exist.

### F13: a recommendation needs usable agreed comparisons on shared families

- **Reproduced.** Zero pairs recommended ensemble; a position-biased judge (two passes never
  agree) recommended ensemble; pairing crossed families.
- **Fix.**
  - Pairs are formed only within the same family and frozen judged inputs (F5's column),
    spread across families. Scaling pairs also match the path.
  - The recommendation counts two-pass-agreed comparisons on families both arms share and
    needs `MIN_AGREED_PAIRS` = 5 per arm; otherwise it returns `default_path: null` with
    "insufficient evidence".
  - Programs become the default only when their Wilson interval over single-shot is
    clearly above ensemble's. Otherwise ensemble "matches or beats" and is the default, as
    §5.6 says.

### F14: every filter and deterministic selection verdict is ledgered and read back

- **Reproduced.** There were no ledger rows for filter outcomes, and forged `filters_json`
  changed the pilot report.
- **Fix.**
  - Every filter pass, fail or not-applicable appends `judgment_ledger` task `pf_filter`:
    left the candidate, right `pf_filter`/<name>, judge `verifier`, policy
    `pf_gate_v2`, input hash of the candidate, filter and evidence. It is idempotent, and a
    new answer to the same question names the previous one in `supersedes_id`.
  - MMR selection on generator and source-anchored families is ledgered as a `verifier`
    `selection` verdict (`pf-mmr-select-v1`).
  - `db/stores/pf.candidate_verdicts` derives the latest verdicts. The pilot and scaling
    reports use it for verification, survival, panel counts and pairing, and so does
    publication: a verified reference, no failing filter, passing freshness and
    structure, and for `isomorph`/`same_target` a structure check that confirmed the
    checkpoints.
  - `filters_json` remains pipeline state only.

## Claims that did not hold, now

| Claim | Now |
|---|---|
| Declared isomorph without a passing structure check never published as isomorph | Holds: F3 tests make the judges disagree; publication rechecks from the ledger |
| Publication is idempotent after a crash | Holds: F6 (state preserved) and F5 (written item resumes) |
| Every verdict is ledgered; every report reads verdicts from the ledger | Holds for filters, selection, verification and pairing (F14); `by_status` and cost stay workflow/receipts data, which are not verdicts |
| Every paid command estimates calls, tokens and cost | Holds: F9 |
| Scaling runs generators at two tiers | Holds: F11 |
| Recommends a default path only when the data separate the arms | Holds as §5.6 words it: insufficient evidence without usable agreed pairs; programs only when separated, else ensemble (F13) |
| CAS-verified valid-alternative traces | Holds: F10 |

## The shared `learnloop embeddings compare` harness (for Slice 2 T6)

The interface in `slice-a-phase-5a.md` stands, with these review changes:

```text
CompareRequest(suite, output_dir, benchmark_dir=None, models=(), dims=(), views=(),
               family_ids=(), target_recall=0.95, max_cases=None, alternatives=2,
               max_items=20, tier=None, dry_run=False)          # tier: "cheap" | "frontier"
run_compare(vault, *, request, caps, price_per_million=None,
            embedding_price_per_million=None, cancelled=None,
            clients=None, embedding_clients=None) -> report dict
CompareSuite.plan(vault, data, request) -> {"roles": {role: {"calls", "tokens", "pairs"?}},
                                            "embedding": {model: {"calls", "tokens", "texts"}}}
```

- **Plans must carry tokens.** Every role in `plan["roles"]` needs `calls` and `tokens`
  (input plus bounded output, e.g. `pf_calls.estimate_tokens`), and every role name must
  be in `pf_calls.ROLE_TASKS`. `run_compare` resolves each role's billing class from its
  planned profile (no client built), prices metered work (an unknown metered LLM or
  embedding price fails closed; Codex roles are subscription, `estimated_only`) and admits
  the whole plan before any request, dry run or not. The report carries
  `estimate.{llm_calls, llm_tokens, embedding_calls, embedding_tokens, metered,
  subscription, billing, cost_basis}`.
- **`CompareContext.vectors(model, texts, dims=, task_prefix=)`** is unchanged. The cache is
  one directory per (model, task prefix, width, embedding config) under
  `<output>/cache`. Vectors narrower than requested are refused, never sliced.
  `VectorCache` now takes `dims=` and `config=`.
- **`CompareContext.role(name)`** resolves through `[pf.scaling]` routes when
  `request.tier` is set, and `ctx.tier` is available to suites. The B2 judge view ledgers
  its tier, so the scaling report can score each tier's judge on identical labelled pairs.
- **Every PF call is isolated** (F1): suites never pass `isolated`.
- **Equivalence checks:** a suite that runs LLM-written checks decides confirmations with
  `pf_sandbox.equivalence_confirmations` (degenerate checks confirm nothing).

## Migration, fixtures, versions

- **Migration 169** (this branch's own, unmerged) gains `pf_candidates.judged_inputs_json`.
  It still expects a renumber at merge: Phase 5b takes 169, so this becomes 170.
  - `fixtures/migration_head_169/state.sqlite` was rebuilt from the tracked
    `migration_head_168` database (from `974c5647`) through the backup API: 169 applied,
    DELETE journal mode, `integrity_check` ok, no FK violations, no `sqlite_sequence`. Its
    README is updated.
  - Copies made by the earlier real runs under `fixtures-local/` (`pf5a-e2e`, `pf5a-real`,
    `pf5a-baseline`) carry the old 169 schema; make a fresh copy for new runs.
- **Version bumps.**
  - Prompts: `pf-ensemble-propose-v2`, `pf-single-shot-v2`, `pf-source-anchored-v2`, new
    `pf-span-support-v1`.
  - Policies: `pf_gate_v2` (also part of the mint-job key, so a round started under v1
    runs as a new job), `pf-publish-v2`, `pf-mmr-select-v1`.
  - Fingerprints `pf-fingerprint-v2`; judged inputs `pf-judged-inputs-v1`; reports
    `pf-reports-v2`.
- **CLI.** `learnloop embeddings compare --tier` (help snapshot regenerated). No frontend
  change.

## Real paid calls

One external-interface check for the new contract, on a fresh backup-API copy
(`fixtures/conic-sections` → `fixtures-local/pf5a-fix-real`, routes as in the earlier real
runs). No working vault was opened.

- **Dry run:** 2 calls, at most 7,675 tokens, at most $0.023 at the $3/M owner bound.
  Caps: 4 calls, 20,000 tokens, $0.05.
- **Run:** route `pf_reference_verifier` → `openai/gpt-4o-mini` (OpenRouter), prompt
  `pf-span-support-v1`.

| Case | Answer | `answer_supported` | Tokens (in/out) | Cost |
|---|---|---|---|---|
| Contradicted (the reviewer's) | "For speed" vs "We chose A for accuracy…" | false | 452 / 64 | $0.0001062 |
| Supported | "Accuracy" | true | 451 / 56 | $0.00010125 |

**Total:** 2 calls, 1,023 tokens, $0.000207 (provider-reported). The structured contract
validated on the first attempt, with no retries.

## Gate results

Final code tree `15634fb3` (this file is docs only), with `LEARNLOOP_CONFIG_DIR`
isolated by `conftest.py`.

| Check | Result |
|---|---|
| `uv sync --extra dev`, then `uv pip install pypdfium2` | OK (`--extra mobile` not needed: `learnloop_mobile` untouched) |
| `uv run lint-imports --no-cache` | **10 contracts kept, 0 broken** |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **7,160 passed**, 0 failed, 14 existing warnings (fork and SQLite datetime-adapter deprecations); 165.8 s |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **66 passed**, 7,094 deselected; 35.3 s |
| The six PF test modules with `--durable-sqlite` | **84 passed** (55 before this review); 612.6 s on a shared, loaded machine |
| DB reference generator and validator | Generated at `f47c31aa` (`fa383eac`); the validator reports **0 errors** on the final tree. Regenerating after `15634fb3` changes only the commit stamps, so it was not committed. |
| Head fixture `migration_head_169` | DELETE journal mode; `integrity_check` ok; no FK violations; no `sqlite_sequence`; rebuilt from the tracked 168 database through the backup API |
| `git diff --check` | Clean |
| Frontend | Unchanged (no `apps/` edits), so the `npm` checks were not required |

New and changed tests: 24 new test functions (29 new cases with parametrization: 84 PF cases, up from 55) across
`test_pf_generation.py`, `test_item_fingerprints.py`, `test_embedding_compare.py` and
`test_pf_reports.py`. Updated expectations:

- the skeleton component name;
- `verification_check` for source-anchored items;
- the scaling report's descriptive key;
- the pilot recommendation with a position-biased fake judge (now insufficient evidence);
- the B2 dry run, which now passes an LLM price.

`tests/pf_fakes.py` gained:

- a freshness verdict on the parent;
- a structure override;
- a sycophantic verifier;
- fixed source candidates;
- a word-level span-support check;
- per-job proposal variation;
- the `span_support` role.

`tests/cli_help_snapshot.json` is regenerated.

**Environment note.** Midway through, `/tmp` (a 16 GB tmpfs) filled up with other
sessions' files, which broke tool output. Nothing outside this worktree was deleted. Work
continued once space freed. Targeted runs used `TMPDIR=fixtures-local/tmp`; the gate runs
used the default environment.

## Open questions

1. **Structure-judge labels.** The scaling check can score the freshness judge on B2's
   labels at both tiers, but no independently labelled structure-check pairs exist. Should
   B2 carry checkpoint-preservation labels (MATH-Perturb's hard perturbations change the
   required operation), or should the structure judge stay descriptive-only?
2. **Executable what-ifs.** Source-anchored what-if items whose consequence is executable
   stay unverified until the execution check (§5.3) is built. Build it in Phase 5a's
   follow-up, or keep what-ifs to source-stated consequences?
3. **Stale selections.** A selection judged against a since-edited parent is rejected,
   not re-verified, so the owner regenerates. Is that the right default, or should a
   rubric-only change trigger an automatic structure re-check?
4. **Spec-conformance partials not in this fix step** (from the review's table, not
   findings): near/far generator programs; embedding views, calibrated blocking and
   embedding diversity in freshness (they wait for B2); the shadow familiarity writer,
   measured variant distance and exemplar retrieval; enforcing the 2–3-model panel
   default; and the full pilot and B2 results.
