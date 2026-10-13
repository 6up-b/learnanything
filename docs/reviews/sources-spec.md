# Stage "sources-spec": the canonical-sources backend track, specified

**Branch:** `sources/canonical-practice` (base `57d31c63`, `main`: migration head 180, latest algorithm `mvp-0.14`).
**Date:** 2026-10-12.
**Deliverable:** `docs/specs/spec_source_practice_and_probes_v1.md`, "Canonical sources as a shared instructional service: practice, probes and explanations from the learner's sources (v1)". Also a short supersession note in `docs/specs/spec_action_router_v1.md` §15.3.

This is a documentation stage. No code, migration, config or test changed.

## What the spec contains

- **Phases S0–S5**, each with data, routes, spend, kill switch, successor ruling, gates and tests:
  - **S0:** `find_practice` gets real callers: the tutor's "Practice this", plan learner picks with a proposal link, and DL3's and the Reader's boxes on the same RPC. Follow-ups go through S2b; the quick check is ruled out, with the reason.
  - **S1:** textbook exercises as practice candidates. A positive role filter and an injected exercise arm; import through a split `import_exercises`; a verifier ladder built from PF-b (the book's own solution, then panel plus sympy, then honest "model's answer" and "disputed" labels); attachment to an existing family; `PracticeItem.canonical_exercise`; an owner-run harvest.
  - **S2a:** intents (`practice`, `discriminate`, `retention`, `remediate`) and `target_hypotheses`, valued by the existing EIG adapters and by EVSI, with no count cap. A provisional discrimination screen for unimported exercises respects the decision-value spec's likelihood-completeness rule.
  - **S2b:** source-first fulfilment of intervention needs, in the two adapters that fulfil needs today. It is a successor.
  - **S3:** `find_sources` with intents (`explain`, `remediate`, `alternative`, `worked_example`, `compare`); `remediate` reads `correction_source_span_ids` for the first time; `compare_sources` is the syntopic operation, quote-verified, with no consensus field and no source cap.
  - **S4:** the typed tool interface (`find_practice`, `find_sources`, `compare_sources`, `find_facets`, `practice_availability`) as structured-output requests, with receipts and ledger rows. The tutor uses it now. R2 wiring is deferred with a new trigger.
  - **S5:** the intervention → outcome record (RAW_LEDGER plus a DERIVED outcome join with one replayer), a report, and the fields that let the EVSI calibration track check value-of-information predictions (§11.4).
- **Cross-cutting:**
  - the contamination policy (§5): `reading`, `assisted_practice`, `cold_attempt`, internal `authoring`, and a narrowed `post_attempt`;
  - an exposure rule that excludes exercises the learner has effectively seen, including through an equivalent worked example.
- **Coverage (§12):** every round-3 idea (the coverage audit's rows 86–115) and the retrieval ideas of rounds 1–2 are classified as built, narrowed with a reason, or deferred with a trigger.
- **Supporting sections:** owner decisions D1–D14 with recommended defaults (§18), deferrals with triggers (§19), a build order with sizes (§15), gates G1–G18 (§16), cross-spec notes (§20) and the agent prompt template (§21).

## Method

- Read the code on `main` at `57d31c63` in this worktree:
  - `practice_index/`, `source_retrieval/`;
  - `content/authoring/exercise_authoring.py`;
  - PF-b (`ops/pf_generation.py`, `ops/pf_publish.py`, `substrate/families.py`);
  - EIG and EVSI (`diagnosis/probe_families.py`, `probes.py`, `followups.py`, `probe_episodes.py`, `scheduling/evsi.py`, `diagnosis/robust_composition.py`);
  - the tutor (`tutor/tutor_qa.py`, `tutor/ai_contracts.py`, the sidecar handler);
  - remediation, the daily plan's learner pick, admission and serving exclusions, the migrations, `db/table_roles.py`, the import-linter contracts and `tests/test_architecture.py`.
- Read the in-flight branches through `git show` only: `docs/reader-workbench-spec` (the Reader spec and its coverage audit), `merge/r1` (`router_decisions`) and `learner/text-gaps` (`named_gaps_for_card`).
- Read the brainstorm file from the main checkout's untracked copy. It is byte-identical (sha256) to the copy committed on `docs/reader-workbench-spec`.
- No vault database, `settings.env` or `~/.config/learnloop` file was read. The only fixture file read was the committed `fixtures/probability/facets.yaml` (through `git show HEAD:`), to confirm what a facet source ref's `ref_id` holds.

## Gate

| Check | Result |
|---|---|
| Code citations re-checked in the worktree | 198 `file:line` citations extracted by script, and the cited line printed and compared with each claim. 197 resolve in the worktree. One (`diagnosis/text_gaps/pipeline.py:850`) is on `learner/text-gaps`, by design, and was verified there with `git show`. Three citations were wrong in the first draft and are fixed: `practice_generation.py:442` → `:441`; `substrate/families.py:30` → `:32`; and the exercise-import row, whose bare `:n` continuations bound to the wrong file. 0 mismatches remain |
| Brainstorm line references | Every cited brainstorm line and range endpoint printed and compared; 11 corrected (L1101 → L1105, L1098 → L1103, L1104 → L1107, L1366–1372 → L1368–1374, L1398 → L1402, L1400–1402 → L1404, L1404 → L1406, L262 → L261, L1340 → L1342, L875–877 → L877, L854–877 → L869–875) |
| Internal consistency | All 16 `source_service.*` config keys used are declared in §13. Every internal § reference resolves; the unresolved ones all name another spec. Every G1–G18 and D1–D14 reference is defined. Migrations are numbered 184–190 in build order. S2a and S2b are labelled consistently. Contradictions found and fixed while reviewing: see below |
| `git diff --check` | Clean |
| Tests | None run: no code changed |
| Paid calls | None. No paid command belongs to a spec stage |

**Contradictions fixed during the review pass:**
- **The S1 → S3 dependency.** S1's solution search was written against `find_sources`, which S3 builds later. It now uses `search_spans` over `extraction_scope` directly.
- **S1's harvest targets** used S2a's hypothesis adapter. That now applies from S2a on.
- **`kinds`** was used by S0 and S1 but introduced in S2. S1 now introduces it.
- **The layering rules.**
  - `find_practice` cannot import the service, because `source_retrieval` already imports `practice_index` (`source_retrieval/search.py:38`). The exercise arm and the valuation are injected instead.
  - S2b was moved out of the job services and into the two adapters that fulfil needs today, because `content` may not import the service.
  - S5's writes go through a registered `db` store.
  - SC12 and G17 now also name the repository's architecture tests: no private cross-package names, registered SQL owners, and the frozen function-local edge inventory.
- **EVSI's "first live consumer"** was claimed by both this spec and the Reader's RW6b. It is now "whichever merges first".
- **The screened exercises' likelihoods** were first stamped as a prior basis, which `rank_feasible` would have excluded. They are now a separate `likelihood_basis`, with the decision-value spec's completeness rule (arm B, or structural only).
- **Family attachment** first named PF's isomorph judge for the relation. PF's family judge already returns the relation (`same_target` or `isomorph`) under the complete-link rule, and `near` or `far` members come only from generation.
- **The `source_tool_calls` row** first had a mutable `status` while classified as a RECEIPT. Rows are now append-only (request, then run).
- **The `reading` policy** first blocked solution blocks. Reading is never blocked; exposure is recorded, and the exposure rule handles independence.

## Code-truth findings worth the owner's attention

1. **`find_practice` has no caller in the app.** Only the CLI calls it. The sidecar RPC has no frontend caller, and the agent-tool function is called only by a test.
2. **`misconceptions.correction_source_span_ids` holds source ids, not spans.** It stores the facets' `ref.ref_id` (`diagnosis/misconceptions.py:554`–`:560`), and nothing reads it. S3 reads it as a source filter and resolves spans from the facets' locators.
3. **No provider path supports native tool calling.** The ChatGPT-plan route refuses `tools`. Tool use is designed as structured output.
4. **Imported exercises' AI-written keys are never checked today.** S1's ladder adds the check without changing grading semantics; whether unchecked keys should still certify is D2.
5. **Remediation shows the first linked span per facet,** whatever the misconception says. S3 ranks and verifies, behind a kill switch.
6. **EVSI still has no live consumer** (shadow only).

## Open questions for the owner

1. **D2:** should imported exercises with unchecked or disputed keys keep certifying? The recommended default is no change in v1 and a later successor on S1's report.
2. **D3:** S2b is ruled a successor (it changes which item a follow-up serves). Confirm, or rule it a content change like PF publication.
3. **D4:** ranked remediation passages in the repair overlay are treated as context (T6's ruling), with no successor. The S3 reviewer confirms.
4. **The Reader spec is being revised in parallel.** Its §7.2 `find_sources`, its compare tool and RW6b's valuation become consumers of this track (§20). The Reader revision should point its compare UI at this spec's `compare_sources` and record that its §17 router deferral now points here.
5. **The EVSI calibration track** (`evsi/calibration`, nothing committed yet) should adopt §11.4's record as its data source for P(E) calibration, realized decision flips and the value of a nat, rather than designing its own log.
6. **T6 review open question 1** (hybrid versus dense) no longer gates the router's use of the tools. It remains a retrieval-quality question for §17's evaluation.
