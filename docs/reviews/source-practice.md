# Stage "sources-build": canonical sources as a shared instructional service

**Branch:** `sources/canonical-practice` (worktree `learnanything-sources`, base `0a6f375b`).
**Spec:** `docs/specs/spec_source_practice_and_probes_v1.md`, phases S0–S5, built in the spec's order (S0, S1, S3, S2a, S2b, S4, S5), then the frontend, snapshots and references, and a live sanity run on fixture copies.
**Commits:** `80132615` S0 · `9cbc0eac` S1 · `1124b863` S3 · `f4ea3468` S2a · `efea1e0c` S2b · `d9ea71ce` S4 · `208a17e4` S5 · `98990c3d` frontend · `fa7586b9` snapshots, head fixture, references · `73e5b721` and `b6e71f22` fixes found by the live run · this record.

## 1. Plan

Every behaviour was built with fakes first (`tests/source_service_fakes.py`: `FakeServiceLLM` answers every role the service calls from the prompt's own JSON; `build_textbook_vault` seeds a Marker-shaped textbook with exercises, solutions and worked examples whose role hints come from the real classifier). Each phase landed with its tests, `lint-imports` and the affected suites; the full suite and the durability lane ran at the end. The router's live R2 wiring stays deferred (spec §10.6). The track builds no Reader UI (SC11); the Reader context gets the backend fields only.

Two algorithm successors were needed and take the next free tags on this branch, expecting relabelling at merge: **mvp-0.15** (S1's certification gate, C3) and **mvp-0.16** (S2b's source-first needs). Migrations are **184–190**, expecting renumbering (main already has `181_router_decisions`, which R1 labelled mvp-0.15).

## 2. What was built

### S0: `find_practice` gets real callers
- `learnloop.instructional`, a composition layer: domains, `practice_index` and `source_retrieval` reach it only through injected callables. Two new import-linter contracts plus `tests/test_instructional_layering.py` (the content namespace package is scanned, since grimp cannot traverse it). `lint-imports`: 16 contracts kept.
- Server-derived caller contexts (`instructional/policy.py`, `source_retrieval/policy.py`): tutor, plan, reader, need, router, agent and harvest callers; the policies `reading`, `assisted_practice`, `post_attempt` and `cold_attempt`; a policy argument can only be asserted, never widen.
- The tutor's deterministic `practice_request` on every answer (practice, feedback, library and reader contexts), the proposal's caller columns, learner text on usage taps, `plan_learner_pick` with the proposal id, and `instructional_impressions` (what a surface rendered; migration 184).

### S1: textbook exercises as practice, checked keys, the certification gate (mvp-0.15)
- The exercise arm: exercise regions of the teaching scope by effective role hint, already-imported regions dropped, judged with items in one listwise rerank (`practice_rerank.v2`) whose provisional facets carry quotes verified in code. Unjudged exercises are never proposed.
- The import: authoring around the verbatim statement, the book's solution found by a listwise match (route `source_solution_match`), then the verifier ladder extracted from PF into `ops/pf_verify.py` (PF parity tested): `book_solution` (quote-verified and supported), `checked` (panel plus sympy), `panel_agrees` (prose), `panel_agrees_unconfirmed`, `model_answer`, `disputed`, `checking`. The interactive import is time-boxed and finishes the check in the background. Migration 185: `source_exercise_imports`, the append-only `reference_key_checks` bound to `reference_content_hash` (stem, key and rubric), and `practice_attempts.reference_status`.
- C3: at mvp-0.15 an attempt on an imported exercise whose current content is not verified records `unverified`, updates FSRS and earns no certification credit; exam pools and certification cold probes skip unverified imports. Never retroactive; no switch turns it off. A shadow rebuild of a fixture copy shows zero deltas.
- Family attachment (`substrate/families.py: attach_to_family`, judged, append-only), `learnloop sources exercises harvest|verify`, and the Reader import's job now records an import row and queues the ladder.

### S3: `find_sources` with intents, `compare_sources`, intent-aware grounding
- `find_sources` with the Reader's contract plus intents (`explain`, `remediate`, `alternative`, `worked_example`, `compare`), expansions, correction lists for misconceptions and a receipt-grade manifest. `post_attempt` opens the item's solution only after its attempt window closes, and records a reveal.
- `compare_sources`: every source in scope considered, pins filtered like discovered spans, each contribution's quote verified in its own passage, no consensus field, uncompared and unverified sources listed (migration 186).
- The tutor grounds a question in `remediate` passages when the item's LO has an active misconception; `prescribe_remediation` takes ranked, verified passages (fallback byte-identical).

### S2a: discriminating search ranked by value of information
- Intents on `PracticeConstraints` (`practice`, `discriminate`, `retention`, `remediate`; the Reader's aliases accepted) and the exact filters on both arms (`unattempted_only`, family exclusions, `facet_match`, `allow_generated`, `max_estimated_minutes` through an injected estimator).
- `instructional/valuation.py`: one `ValuationProblem` per hypothesis space (an LO's hypothesis set, a facet marginal, an open probe episode, a causal factor with `H_OTHER` excluded, a retention pair; named gaps feature-detected), normalized credible-set tables per candidate with a likelihood regime, valued with `evaluate_selection` when shapes match and the new `evaluate_selection_credible_sets` otherwise (`evaluate_selection` now raises `EnsembleShapeError` on unequal member counts), greedy conditional valuation with no count cap, decision mode through `rank_feasible`, and no entropy fallback. Only `pinned_channel` licenses a system-initiated check. Each valued candidate carries its robust value interval and P(E); the valued group is listed in value order per minute.
- The exercise discrimination screen (route `exercise_discrimination`: complete screens are upper bounds that can license a skip, never a question), the exposure rule (`reading_exposure_v1`, including the worked-example equivalence judge, route `worked_example_equivalence`, and the dominance rule, now applied in the presentation order), resumable paging (exhausted, budget with a cursor, or the perfect-information bound). Migration 187 stores `valuation_json` and `provisional_json` on the proposal.

### S2b: needs try the learner's textbook first (mvp-0.16)
- `instructional/needs.py` adds one step before generation in the primed-retry handler and `learnloop generate-diagnostics`: source exercises tried in valuation order, each draft authored, key-checked (only `book_solution`, `checked` and `panel_agrees` fulfil), validated and, for `discriminate`, passed through the follow-up chooser's own `misconception_discrimination` gate before anything is written. Decision mode prices an open causal factor by its repair classes; `stop` makes the need stale with `value_stop:<kind>:<proposal>`. Generation proceeds as today otherwise. Migration 188: `source_exercise_imports.need_id`.

### S4: the typed tool interface; the tutor uses it
- `instructional/tools.py`: `find_practice`, `find_sources`, `compare_sources`, `find_facets` (BM25 over labels and dossiers, stored vectors only, no model call) and `practice_availability` (recall and admission, no model call), each with a strict argument model and a published schema; no policy field. The dispatcher derives the policy, refuses everything during a cold administration, drops unknown ids and returns model-reader records that never carry an answer, rubric, hint or solution (and drop anything reproducing the bound item's answer).
- Migration 189: `source_tool_calls` (RECEIPT, append-only request and run rows; a `judgment_ledger` row per model-written request).
- The tutor: `TutorAnswerWithTools` (`ai/tool_requests.py`) under prompt version `mvp-0.9-tutor-qa-source-tool-requests`, injected by the adapters, so `tutor_tools = false` keeps S0's prompt and contract byte for byte. Each query and reason passes `answer_leaks_expected`; a leaking request is recorded refused. `run_source_tool` runs a stored request under its stored caller (it can only narrow). "Explain this with my work" pins chosen spans through `PinnedSpanProvider` and carries the draft. `learnloop sources tools` and `learnloop sources tool` serve external agents.

### S5: retrieval in the evidence loop (reports only)
- Migration 190: `retrieval_interventions` (RAW_LEDGER) written only when an asset is shown or served (a tutor answer citing retrieved or pinned spans, an opened passage offer or a shown comparison via `record_source_offer_shown`, ranked remediation passages delivered, a pick, a need served), with references to the valuation, impressions, both independence verdicts and R1's `learner_pick` row when `router_decisions` exists. `retrieval_intervention_outcomes` (DERIVED, one replayer): `R_next`, `R_cold` as the decision-value outcome states (pending stays right-censored; the reference time is the newest persisted row, so rebuilds are deterministic), the observed bucket beside P(E), actual beside predicted minutes, the learner's taps. `learnloop sources outcomes` reports associations, labelled as such.

### Frontend and the rest
- `AskOverlay` renders the offers under a tutor answer: "Practice this" (eager; impressions recorded; picks through `plan_learner_pick` with the proposal id, textbook exercises through the import), "From your books" (eager, recorded only when opened, labelled source-authored, with "Explain this with my work"), and "How do your books treat this?" (lazy). The practice screen names a textbook exercise's book and its key's label. Nine passthroughs in `commands.rs`/`main.rs`.
- Desktop-only pins (G16): seven new RPCs (`record_proposal_impressions`, `import_source_exercise`, `get_source_exercise_import`, `find_sources`, `compare_sources`, `run_source_tool`, `record_source_offer_shown`) and eight extended ones.
- Config `[source_service]` (master switch, a kill switch per phase, time, prompt-size and money bounds) and four routes (`source_solution_match`, `source_compare`, `exercise_discrimination`, `worked_example_equivalence`). Every defaults snapshot was recomputed; mvp-0.15 and mvp-0.16 record their own. New vaults start at mvp-0.16, and `learnloop upgrade` defaults to it.
- `fixtures/migration_head_190` (backup-API copy of `migration_head_180` with 184–190 applied, rollback journal, integrity and foreign-key checks clean), the CLI help snapshot, and the database and configuration references regenerated at head 190 (both validators clean).

## 3. Deviations from the spec

1. **Episode instruments are valued as `item_point` tables**, not through the compiled probe-card path (`probe_robust.robust_selection`), so the "instrument-only parity" test of §8.3.4 item 2 is not built. The live robust probe path itself is unchanged.
2. **Retention's prior** is the LO's mastery mean; the spec's "recent success, assisted only" condition is not enforced.
3. **Greedy branch truncation** uses its own floor and cap (`BRANCH_MASS_FLOOR = 0.01`, `MAX_BRANCHES = 64`) rather than `plan_precommitted_block`'s. It bounds compute, not the number of checks.
4. **An unjudged studied worked example** (judge unavailable) counts as `related`: conservative for `retention`, a label for `discriminate`.
5. **`post_attempt`'s reveal** is recorded when `find_sources` returns the solution, not when the surface displays it.
6. **Misconception targets** are read from the `misconceptions` table (active ones); there is no separate overlay.
7. **The Reader import's background check** runs in a daemon thread inside the job handler.
8. **The daily money cap** sums the leaf receipts of the service's owner kinds since UTC midnight.
9. **S2b decision mode** needs an open probe episode whose locked hypothesis set covers the factor's hypotheses; otherwise the factor is "unpriced" and the need goes to generation.
10. **S5's hypothesis movement** is not computed: rows keep references (`state_ref`) for the calibration track.
11. **S5's "imported source exercise served"** is recorded at the learner's pick of the exercise (before the import finishes).
12. **The cold-success threshold** in the outcome report is correctness ≥ 0.5, a report threshold.
13. **The tutor may request three tools** (`find_practice`, `find_sources`, `compare_sources`); `find_facets` and `practice_availability` are for agents and the router.
14. **Tests are consolidated**: S2a's named tests (`test_valuation_input`, `test_open_hypotheses_adapters`, `test_practice_constraints_v2`, `test_exact_filters_raw_exercises`, `test_exercise_discrimination_screen`, `test_reading_exposure_adjustment`, `test_valuation_paging`) live in `test_discriminating_search.py` and `test_value_candidates.py`; the Reader consumer contract (G21) in `test_find_sources_intents.py`; comparison policy in `test_compare_sources.py`.
15. **Frontend scope**: the offers live in `AskOverlay`; the plan and DL3 box surfaces get no new strip.
16. **Outside the track**, the live run surfaced a general vault-writer bug (`vault/yaml_io`), fixed in `73e5b721`: written YAML is guaranteed to read back, and any file that was valid stays byte-identical.

## 4. Live sanity run

**Setup.** Backup-API copies under `fixtures-local/sources-run/` of `fixtures/probability` (as the task asked) and, because that copy turned out to hold no usable textbook exercises, of `fixtures/linear_algebra` (Axler, *Linear Algebra Done Right*). The tracked fixtures were not touched. On the copies only, routes were pointed at OpenRouter: Claude Haiku 5.5 (`anthropic/claude-haiku-5.5`, $0.10 / $0.50 per million input / output tokens) for the rerank, the equivalence judge and the panel, GPT-6 Luna (`openai/gpt-6-luna`, same price) as the second panel solver and, after Haiku failed at it, for authoring. Single-rate price set at 0.5 per million (an upper bound) for every metered setting. Keys were loaded by the app; no key or settings file was read.

**Dry runs first.** `learnloop sources exercises harvest --dry-run` planned 30 thin-facet targets on the linear-algebra copy (too many for a sanity run, so a bounded driver was used instead). A no-call plan of the exercise arm returned candidates; `learnloop sources exercises verify --dry-run` lists nine probability items to check (eight historical Reader imports resolving to `model_answer`, one `disputed`).

**What the copies showed before any call.**
- The **probability copy has no exercise regions**: its textbook excerpt (Blitzstein and Hwang ch. 1) ends at the "1.9 Exercises" header, the MIT 6.041 problem set's numbered problems are hinted `ordinary_prose`, and the only `exercise` hints are a misclassified Wikipedia article.
- The **linear-algebra copy had none either**, because its blocks were hinted by an older classifier. Re-applying today's `classify_block_role` to the copy's blocks (a script on the copy, standing in for a re-ingest) gave 76 exercise hints and real regions.
- The first regions showed two bugs, both fixed and tested: page headers and footers led empty "exercises" (`73e5b721`), and each block under an "Exercises" heading started its own region, so "20 Suppose U = …" and "Find a subspace W …" were split and the imported stem lost U's definition (`b6e71f22`).

**Calls and cost.** 44 receipted physical requests (25 Haiku, 19 Luna): 50,475 input and 31,842 output tokens, **$0.0205** as OpenRouter reported it. The first pass's 4–6 authoring requests predate the receipt fix and are unreceipted; at the token sizes seen, they add at most about $0.01. Three strict-schema requests failed with HTTP 400 at no cost. **Total under $0.03**, far inside the $2 cap; no cap was hit.

**Results, with examples.**

| Copy | Exercise | Authored key | Ladder | Label | Verdict on quality |
|---|---|---|---|---|---|
| linear algebra | Axler 1C.20 (pre-fix region: "Find a subspace W of F⁴ such that F⁴ = U ⊕ W", without U's definition) | W = span{(1,0,0,0), (0,0,1,0)} for U = {(x,x,y,y)} (correct, inferred from the surrounding text) | no book solution; panel 0/6 agree | `model_answer` | Stem unusable for a learner (missing setup); the region bug that caused it is fixed |
| linear algebra | Axler 1C.22 (pre-fix region: "Find three subspaces W₁, W₂, W₃ …") | a correct construction | panel 0/6 | `model_answer` | Open constructions have many valid answers, so panel agreement cannot verify them; the honest label is right |
| linear algebra | Axler 1C.21 after the fix: "Suppose U = {(x, y, x+y, x−y, 2x)} … Find a subspace W of F⁵ such that F⁵ = U ⊕ W" | W = span{e₃, e₄, e₅}, with spanning and trivial-intersection proofs (correct) | panel agrees | `panel_agrees` | Good: complete stem, correct key, verified |
| probability | MIT 6.041 PS1 #2 (coin flips: P(HHH), P(HTH), two heads, heads ≥ tails) | 1/8, 1/8, 3/8, 1/2 (correct) | panel 6/6 agree; the judge's sympy program rejected | `disputed` | **False dispute**: a multi-part numeric key defeats the cheap judge's single-value check |
| probability | MIT 6.041 PS1 #5 (darts on a 10-inch board) | P(50) = 1/100, P(30) = 2/25, John's split by halves (correct as far as shown) | panel 6/6, answer kind judged "text" | `panel_agrees` | Correct key, verified; numeric parts labelled as prose by the judge |

- **Exercise arm and rerank** (linear algebra, query "find a subspace W so that the direct sum of U and W is all of Fⁿ"): Haiku judged 11 regions and proposed three: the F⁴ complement exercise ("relevant"), the three-subspace extension ("partial") and a direct-sum counterexample exercise ("partial"). It rejected the axiom, union, intersection and odd-function exercises, each with a one-line reason. Provisional facets were empty because the request named no LO or facet, so the facet vocabulary was empty.
- **Discriminating search** (probability, two facets): two LO problems, each `act` with one check (`stopped_after_1`). The valued group was listed in value order: lower-bound values 6.5, 5.9 and 5.4 minutes against expected costs of 3.5, 3.5 and 7.4 minutes, all on the `item_point` regime and labelled "not yet calibrated". Paging was exhausted, and the step made one rerank call and no screen call (there were no exercises in scope).
- **Provider behaviour.** With `json_object`, Haiku once returned invalid `ExerciseAuthoring` JSON. Strict `json_schema` on Anthropic through OpenRouter is refused for that schema ("compiled grammar is too large"). Luna authored valid JSON every time. Before `73e5b721`, an authoring failure raised out of the import and left the row `authoring`. A Luna-authored trace contract with long checkpoint keys was written as unreadable YAML, so the loader skipped the item. Both are fixed and tested.

**Leftovers on the copies** (disposable, gitignored): one `authoring` and one `checking` import row from the pre-fix crashes, and the two pre-fix linear-algebra items.

**Inadvertent paid calls.** While debugging S2b, a script run outside pytest (so without the test suite's settings isolation) resolved the default Codex route for the exercise-discrimination screen on two synthetic temporary vaults in `fixtures-local/tmp`. That made 2 calls to `gpt-5.6-sol` on the ChatGPT subscription (17,287 + 16,501 input and 164 + 166 output tokens; cost `estimated_only`), with no owner data involved. The tests themselves never resolved a real route. The need step now passes injected clients by role name.

## 5. Gate

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | done |
| `uv run lint-imports --no-cache` | 16 contracts kept, 0 broken |
| Full suite, `flock … uv run pytest -n auto` | 8841 passed, 0 failed (46 warnings), 5 min 42 s once the shared lock was free. An earlier run, before the last fixes, had 2 failures (a capture-recovery response and a successor-chain index), both fixed |
| Durability lane, `flock … uv run pytest -m durability` | 94 passed, 8747 deselected, 0 failed |
| Frontend: `npm run typecheck`, `npm test`, `npm run frontend:build` | typecheck clean; vitest 33 files, 164 tests passed (one earlier run under full CPU load had 3 timing failures that did not reproduce); build ok |
| `cargo check` | ok |
| DB references: `db_generate_reference.py`, `db_validate_reference.py` | regenerated at head 190; validator: 0 errors (306 table notes, 701 config leaves) |

## 6. Owner commands

```bash
# Reach the successors on a vault (never retroactive; the gate has no switch).
uv run learnloop upgrade --vault <vault>                      # default target is now mvp-0.16
uv run learnloop upgrade --to mvp-0.15 --vault <vault>        # C3 gate only
# Check answer keys of imported exercises (historical Reader imports resolve to model_answer).
uv run learnloop sources exercises verify --dry-run --json --vault <vault>
uv run learnloop sources exercises verify --max-cost-usd 0.25 --vault <vault>
# Import judged textbook exercises for thin facets (dry run first; capped).
uv run learnloop sources exercises harvest --dry-run --json --vault <vault>
# Tools for external agents, and the association report.
uv run learnloop sources tools --json
uv run learnloop sources tool find_practice --args '{"query": "...", "intent": "discriminate"}' --vault <vault>
uv run learnloop sources outcomes --vault <vault>
# Source-first needs (mvp-0.16): the dry run names the step.
uv run learnloop generate-diagnostics --dry-run --json --vault <vault>
```

Routes the service uses beyond today's (unset ones fall back to the active provider; metered ones need `source_service.llm_price_per_million` or they are skipped and labelled): `source_solution_match`, `exercise_discrimination`, `worked_example_equivalence`, `source_compare`, `pf_solver_panel` (a list of at least two models), `pf_reference_verifier`, `pf_family_judge`, `practice_rerank`, `source_rerank`. Kill switches: `[source_service] enabled`, `tutor_offers`, `exercise_arm`, `exercise_verification`, `unverified_imports`, `family_attachment`, `discriminating_search`, `source_first_needs`, `tutor_intents`, `remediation_passages`, `compare`, `tutor_tools`, `interventions`.

## 7. Open questions

1. **Stale role hints.** The owner's vaults were hinted by an older classifier, so the exercise arm finds nothing in them until the hints are re-derived (probability: 0 regions; linear algebra: 0 before re-hinting, 18 after re-hinting and the two region fixes). Should there be a `learnloop sources rehint` that re-applies `classify_block_role` to stored blocks, or should the owner re-ingest?
2. **Problem-set headings.** "Problem Set 1 Due …" is not a unit heading, so MIT-style numbered problems never become exercises. Should `unit_heading_role` recognise problem sets and homework?
3. **Bundled and glyph-less exercises.** Marker groups Axler's exercises 1–7 into one `ListGroup` block and drops their math glyphs ("Show that + = + for all , ∈ ."). Split list groups by their numbering, and re-extract math, or skip such regions?
4. **Multi-part numeric keys.** A correct four-part key was marked `disputed` because the judge's single sympy check rejected it, despite 6/6 panel agreement. Should the ladder check per part, or treat multi-part keys as prose (`panel_agrees`)?
5. **Authoring route.** On OpenRouter, Haiku's `json_object` output was once invalid and strict schemas are refused for `ExerciseAuthoring`; Luna worked. Is Codex (today's default) the authoring route for imports, or should the route be set explicitly?
6. **Merge labels.** Main's router R1 already uses migration 181 and mvp-0.15. These migrations (184–190) and successors (mvp-0.15, mvp-0.16) will need renumbering and relabelling, and the defaults snapshots recomputing, at merge.
7. **Decision mode for causal factors** needs an open episode's locked hypothesis set. Is a factor-level hypothesis-set adapter wanted, or is "unpriced → generation" right for v1?
8. **Hypothesis movement in S5** is left to the evsi/calibration track (references only). Confirm.
9. **The YAML writer fix** (`vault/yaml_io`) touches every vault write: output is unchanged unless it would not read back. Confirm it may merge with this track.
