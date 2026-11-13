# Refactor bug ledger

Owner, Nov 12 2026: "As you refactor and find these bugs, they should be fixed at some point either by arc close or by landing."

Every bug a refactor step finds gets a row here: where it was found, the step that fixes it, and the deadline, which is either the landing that found it or the close of the current arc. An arc doesn't close while a row due at its close is open. A strict xfail is allowed only as the fail-first test of a queued fix. A fix that changes persisted meaning (scoring, scheduling, projections) follows `docs/algorithm-change-playbook.md`, and related fixes share one successor. Only a genuine design question goes to the owner, with a recommendation.

Status: **open**, **queued** (a step owns it), **fixed** (commit), **owner** (waiting on a decision).

## Due at arc D's close

| Id | Found in | Bug | Fail-first test | Fix | Status |
|---|---|---|---|---|---|
| D-1 | D2a §4.1 | A success never resets a facet's `consecutive_failures`: in `substrate/canonical_projection.py` the reset sits after the success branch's `continue`. | `test_recall_coverage_interventions::test_success_resets_repeat_failure_gate_and_coverage_is_not_failed` | Successor (facet-belief fixes), with D-3 and D-5 | fixed (`0dda03e99a`, mvp-0.59; docs/reviews/refactor-dfb.md) |
| D-2 | D2a §4.2 | `error_taxonomy.persist_unknown_error_type_proposals` knows only the mvp-0.6 builtin types, so every grade naming a KM4 mechanism type files a "new error type" proposal. | `test_codex_attempt_flow::test_codex_recall_wording_uses_recall_failure_not_new_error_type` | Small fix (no scoring change) | queued |
| D-3 | D2a §4.3 | `teach_back.transfer_evidence_multiplier` doesn't reach the canonical facet belief: a transfer-tier criterion adds full mass. | `test_teach_back::test_transfer_tier_evidence_mass_is_discounted_symmetrically` | Successor (facet-belief fixes) | fixed (`0dda03e99a`, mvp-0.59) |
| D-4 | D2a §4.4 | A targeted error attribution's facet outcome doesn't reach the canonical belief. Possibly KM2's design. | `test_deferred_regrade::test_deferred_regrade_replays_targeted_error_attribution_facets` | KM2's design (KM spec §18 decision 3; refactor-dfb §0): the xfail became a test of the designed behaviour; with D-5 the outcome opens the facet's uncertainty. Recommendation: keep it (refactor-dfb §6) | owner |
| D-5 | D2a §4.5, D2b | `facet_state_reader.facet_uncertainty_states_for_lo` returns `[]` on canonical vaults, so the follow-up facet-EIG ranking and the follow-up overlap gate never run at the head. | `test_predictive_eig` (pinned), `test_subthreshold_noisy…` (pinned) | Successor (facet-belief fixes): per-LO facet uncertainty written and read on canonical vaults, keyed by canonical facet id | fixed (`0dda03e99a`, `a733b7d021`, mvp-0.59) |
| D-6 | D2a §4.7 | Canonical failure observations carry no coverage mass (unverified). | `test_recall_coverage_interventions::test_dont_know_keeps_full_coverage…` (pinned) | Bug, not design (refactor-dfb §0): a total failure books coverage where its failure mass lands | fixed (`0dda03e99a`, mvp-0.59) |
| D-7 | D2a §4.8 | Populate-goal's refusal doesn't name held-out exam material as the cause. | new | Small fix (message) | queued |
| D-8 | D2b | Since mvp-0.12 (recurrence groups) a diagnose drain makes one more embedding request than its dry run estimates (3 against 2). | `test_diagnosis_reports::test_retrieval_embeddings_are_admitted_and_charged_on_the_command_budget` | Small fix (estimate) | queued |
| D-9 | K3.4 | A retry after an append gate failure replays the checkpointed answer and fails again at zero cost; the card still offers Retry. | new | Drop the checkpoint on a gate failure (or offer repair) | queued |
| D-10 | K3.5 | Undo (`reject_applied_items`) isn't refused while an apply intent is outstanding. | new | Small fix | queued |
| D-11 | K3.5 | `facet_identity.authority.write_registry_text` writes `post_hash` without the `sha256:` prefix, so its idempotent skip never matches. | new | Small fix | queued |
| D-12 | K3 | `learnloop synthesize --mode auto` without `--new-revision` still sends every revision's inventories. | new | Small fix (mirror K3.2's filter) | queued |
| D-13 | K0, D2a | `test_model_call_receipt_owners::test_tui_grading_records_receipts_with_usage` waits a fixed ten TUI pauses (timing flake). | — | Wait on the work, not on time | queued |
| D-14 | D2a | RO5's seeded arms (open-pick, stop coin, check rate, mixtures) draw on fresh random ids, so tests that depend on them flake. Two fixed in D2a, one in K3. | — | Sweep the remaining arms' tests | queued |
| D-15 | D2b | `test_instruct_handoff_ih1::test_no_new_draw_joins_an_open_item` failed once in a landing run (20/20 alone on main). | — | Find the race or close as a non-repro with evidence | queued |

## Due before G6 (K1's list, strategy §2.17)

| Id | Found in | Bug | Fix | Status |
|---|---|---|---|---|
| K1-1 | K1 D1 | `exam_material` and its siblings fail open on an unreadable or truncated `source_sets.yaml`; only 4 readers ask `protection_issues`. | Metadata gate inside `exam_material`; atomic write of the file | queued |
| K1-2 | K1 D4 | The Reader import passes non-held-out exam material, and the item is then withheld from model contexts as exam material. | Owner's call (recommended: keep §8 Q3's default and stop withholding the learner's own item) | owner |
| K1-3 | K1 R1 | The session serve door ignores exam reservations (`learnloop_sidecar/serving.py`). | Small fix | queued |
| K1-4 | K1 R2 | MCP `find_sources` returns a diagnostic probe's own passage and assessment-lane passages (`remote/sources.py`). | Small fix | queued |
| K1-5 | K1 R9 | The inspector shows every hint of the item being answered, cold checks included, uncounted. | Small fix | queued |
| K1-6 | K1 D6 | A remediation's cold item isn't reserved until its task exists; the cold-kinds constant is duplicated. | Small fix | queued |
| K1-7 | K1 D3, D8 | Two docstrings contradict the code (rule 4's "no search hit"; figures' set against the Reader's). | Docstrings | queued |

## Due with K2's sub-steps (strategy §2.17)

| Id | Found in | Bug | Fix | Status |
|---|---|---|---|---|
| K2-1 | K2 map KD5 | The persona gate silently falls back to a string comparison when its provider call fails. | K2.12, or earlier as a small fix | queued |
| K2-2 | K2 map KM5 | Conflict resolution isn't atomic. | K2.10 | queued |
| K2-3 | K2 map KM6 | Append hashes before resolving the brief and practice timing, and never inherits the learner's level. | K2.3 | queued |
| K2-4 | K2 map KM1, KM2 | Outer caches bypass the rendered-prompt keys; the manifest omits role overrides and edges. | K2.2, K2.3 | queued |
| K2-5 | K2 map KB4 | The desktop re-implements backend rules and four disagree (assessment roles, retry eligibility, image source kind, page ranges). | K2.11 | queued |
| K2-6 | K3 | Keep-ahead appends no longer see an earlier chapter's pending proposal, so they may mint duplicates. | Owner's auto-apply call (KX4), then a fix | owner |
