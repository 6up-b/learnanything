# Router R2a: the staged frame on Today, exact receipts, the stored card

**Stage:** router R2, sub-stage A (`docs/specs/plan_router_r2_v1.md` §9 R2a), owner-directed 2026-10-13.
**Branch:** `router/r2a`, base `63309a1e5` (main `f2bfa2928` plus the plan doc).
**Successor:** `mvp-0.23` (placeholder, relabelled at its merge), chained after `mvp-0.22`.
**Migration:** 205 (placeholder, renumbered at its merge).
**Kill switch:** `router.enabled` (off, or below `mvp-0.23`: Today and `golden_path.advance` serve exactly as `mvp-0.22`).
**Model calls:** none (R2b). **Paid calls:** none.

## Summary

R2a makes the router live for Today without a model:

1. **The staged frame** (`staged_frame_v1`). At every plan boundary it runs the P4 constraint engine over the pool VOI v2 already admitted, against one bounded controller snapshot. An item a named hard constraint refuses is dropped before DL1's packing. The refusal is logged on the `plan_block` row under `exclusions_json.named.<constraint>`.
2. **The staged chooser** (`staged_v1`). It is DL1's `lane_quota_v1` over what is left (owner Q1). It is deterministic, so the block order is DL1's wherever nothing is refused. It writes a plain "why".
3. **The exact receipt.** A served plan item writes an append-only `plan_presentations` row, and the plan step names it (`presentation_id`). An answer that sends it back is bound (`practice_attempts.plan_presentation_id`). `router_outcomes` v2 joins through it, and so does the EVSI staged-forecast adapter. R1's session rule stays only as a labelled fallback.
4. **`LearnerStateCardV1`.** The card is built at every routed boundary, hashed onto the decision row (`card_hash`) and stored in `router_decision_payloads`. It is never sent anywhere. `learnloop router card` prints it.
5. **The D13 bridge.** `golden_path.advance` goes through `controller_cutover.advance_live`. A requested state other than the canonical successor is the learner's own choice (owner Q10). A staged veto defers the run and says why in one plain sentence.

The four fail-first tests failed on the base for the reasons the plan names, and pass now (§Fail-first). The gate is green (§Gate). The manual runs show:
- **Shadow rebuild:** 0/0/0 beyond the version labels.
- **R2a against the switch off:** identical wherever nothing is refused. Refusals are counted per constraint.
- **The stored card:** read for leakage, none found.

## Owner decisions built to (2026-10-13)

| # | Decision | Where |
|---|---|---|
| Q1 | The staged component is `lane_quota_v1` over the P4-feasible set. The ladder annotates, marks irreversibles and feeds the card | `daily_plan/staged_frame.py` |
| Q2 | VOI v2 stays the only authority on diagnostic checks. No staged diagnostic blocks: the frame consumes VOI's admitted pool and never re-decides a probe | the frame reads `context.pool` as `_classified_pool` admitted it |
| Q3 | Two successors. R2a has its own placeholder (`mvp-0.23`), chained after `mvp-0.22`, with the chain's notes passed through and T1's guard advisory | `router_staged_upgrade.py` |
| Q10 | A `golden_path.advance` to a non-canonical `to_state` is the learner's own choice. P2-owned items stay out of the plan, through the existing staged-owned exclusion in `build_due_queue`, which is untouched | `controller_cutover.staged_next_action` |
| Q13 | Unverified-key attempts count as router outcomes, with `reference_status` recorded | `router_outcomes.r_next_reference_status` and `r_cold_reference_status` |
| D6 | Recorded (Perplexity terms accepted). R2a sends nothing | n/a |
| R2b | The router LLM's output room will be at least 16,384 tokens | not built here |
| Q10 (receipts) | Exact receipts replace R1's session-rule binding wherever a receipt exists. The session rule stays as a labelled fallback (`action_binding = session_rule`) for old rows, `staged_p2` rows and clients that send no presentation id | `router/outcomes.py` |

## Code truth re-verified at stage start

The plan cites main `e238fa07`. VOI v2, the Decider and UX Phase 1 landed before this base and moved the engine.

**Re-verified at `63309a1e5`:**

| Plan citation | Now | Note |
|---|---|---|
| `engine.py:150-189` `PlanPolicy` | `engine.py:183` | |
| `engine.py:1253`/`:1320-1359` `_boundary`, decide before the transaction | `_boundary` at `:1525`; R1's logger at `:1640` and `:1765` | Still: `decide()` runs before the block's transaction opens |
| `engine.py:1883-1899` `_serve` | `:2221` | |
| `engine.py:1763-1779` `_item_step` | `:2102` | |
| `engine.py:1944` `learner_pick` | `:2284` | |
| `engine.py:1674-1757` `_insert_followups` | `:2013` | R2c |
| VOI admission (`serving/voi-stopping:engine.py:460-663`) | `_select_requests` `:497`, `_classified_pool` `:576`, `_project_probe_admission` `:694` | Admission is still deterministic and before `decide()`. The frame never re-values a probe |
| `types.py:146-168` | `BlockCandidate :113`, `BlockChoice :153`, `BlockChooser :165` | |
| `router/plan_log.py:92-270` | `build_plan_block_decision :92`, `log_plan_block_decision :255`, the own-`decision_ref` rule `:267` | |
| `router/outcomes.py:364-377` session rule | `_action_attempt :364` | |
| `live_report.py:179-205` `_staged_attempt` | `:327` (the plan-probe join at `:285`); `REPORT_VERSION` v5 at `:80` | |
| `golden_path.py:260-276` | `@method("golden_path.advance") :259` | |
| `daily_plan.py:97-116` `_env` | `:105` | |
| `controller_cutover.py:134-319` | `staged_next_action :134`, `_log_staged_decision :207`, `advance_live :266` | Unchanged |
| `staged_policy.py:216-291` | `evaluate_staged_rule :216`, `IRREVERSIBLE_RUNGS :289`, `ladder_eligibility :294` | Unchanged |
| `constraint_engine.py:121-290`, `:301`, `:326` | Constraints `:121-311`, `evaluate :301`, `feasible_set :326` | Unchanged |
| `config/schema.py:2179-2193` `RouterConfig` | `:2358` | |
| `migrations/181_router_decisions.sql:17-19` | `:19` | |

**Composition with VOI v2's commit door** (`learnloop_sidecar/handlers/practice.py:372-382`, `probe_value_block_reason`). The door now lives in the practice handler:
- A refused probe opens as ordinary practice (`active: false`).
- The plan item is still served, and its presentation exists. An answer binds to it as practice, and a skip resolves it. The block is never stuck.

**UX Phase 1's Begin** (`TodayScreen.continuePlan`, `App.beginSession`) passes the served step on. R2a threads its `presentationId` through the same path as `schedulerCandidateId` (§Frontend).

## What was built

### The staged frame (`daily_plan/staged_frame.py`)

**One bounded snapshot per plan env.** `StagedFrame.material(pool)` builds the frame's material once per RPC:
- `controller_snapshot.build_snapshot` over the laned pool. Its query budget does not grow with the pool;
- the item surfaces (`activity_surfaces`, one read) and the live assessment reservations (one read);
- the items an open cold check holds (one read per cold task kind);
- the per-LO ladder signals: pending open-set alarms, in-progress episodes, ignored opening episodes.

The material is rebuilt over the union only when a later pool holds an item it has not evaluated (a follow-up that appeared mid-plan). The view's projections share it, so the projected blocks drop the same items and cost no extra snapshot.

**The role decides the block each item is evaluated in.**
- A **quick check that must be unseen** is evaluated in a `measure_diagnostic` block. These are `diagnostic_probe`, `diagnostic_microprobe` and `probe` items, and due project probes. Here the hard-exposure rule applies:
  - an exact or near-clone exposure in the one ledger refuses the item;
  - so does a surface whose freshness cannot be established (`freshness_unknown`, P4's own fail-closed rule).
  - The surface identity is computed from the item's contract, as `resolve_legacy_item` computes it, so an item never resolved before is checked too.
- **Every other item** is evaluated in its lane's action (`practice` / `maintain` / `instruct`).
  - A teach-back is ordinary practice here: VOI v2 admits teach-backs, and the dialogue is re-served by design (D11).

**So on Today the constraints that can refuse are:**
- `active_status`;
- `stimulus_renderable`;
- `hard_exposure_collision`, on quick checks;
- `assessment_reservation`, on every item: a surface reserved for an assessment is never served as practice;
- `same_facet_dispersion`, a deferral of a back-to-back quick check on the same near-kin surface.

**And these never refuse, by construction:**
- `purpose_compatibility`: an item's purpose is its role in the plan.
- `fatigue_budget`: the container's own minutes rule. The snapshot carries no session minutes, so the engine does not repeat it.
- `stage_interleaving`: it needs a staged block, and Today has none.

**Placed by the container, never by the frame:**
- **requests**, the learner's own (L3);
- **mid-plan follow-ups.** The follow-up rules decide them, with value of information deciding whether each is worth serving. R2c's restraint is where the router meets them.

**Annotations.** Each candidate carries:
- `reason_code` (the "why");
- `topic`;
- `reversible`. It is false when an item holds an open cold check (serving spends it) or a reserved assessment surface (refused anyway); `irreversible_because` names the item;
- `ladder`: the P4 rungs its learning objects are eligible for, and the rung that fires.

**The per-LO ladder signals (annotation only, Q1):**
- **From the lanes:** not acquired (rung 4: no attempted item), fragile (rung 5: in repair) and near the retention limit (rung 9: a due item).
- **From the live adapters' reads:** misspecified (rung 2: a pending open-set alarm) and measurement value (rung 3: an in-progress episode; annotated, never composed, Q2).
- **Never on Today:** rung 7 (a terminal claim needs a run) and rung 8 (no milestone).

### The staged chooser (`staged_v1`)

`StagedChooser.choose` is `LaneQuotaChooser.choose` over the staged-feasible candidates. It returns `chosen_by = "staged"` with propensity 1.

Its `router_record` holds:
- `mode`, `policy` and `why_code`;
- `draw_support`: the reversible candidates, the only ones R2b's mixture may ever draw (G2);
- `irreversible`;
- the card: its version, its hash and the payload.

The chooser writes nothing.
- The container copies `BlockChoice.router_record` to the `plan_block` logger (`PlanBlockDecision.router_record`).
- The logger writes the row and the card in the block's own transaction (`_store_card`, its own savepoint).
- The `block_chosen` receipt carries only a summary (`detail.router`) and the frame's refusals (`detail.staged_frame`).

**The projection chooser stays `lane_quota_v1`** (DL1 F3).

**Policy selection** is in `daily_plan/policy.py`:
- `router_active(vault)` is `plan_active` and `bridge_active`.
- `bridge_active` is the version in `ROUTER_STAGED_FRAME_VERSIONS` and `router.enabled`.
- `policy_for(...)` returns `DEFAULT_POLICY` (DL1's pair exactly) otherwise.

The sidecar's plan `_env` is the only `PlanEnv` builder that makes block decisions. The reader's progress hook and the headline make none.

### The `plan_block` row (`router/plan_log.py`)

With a router record, the row carries:
- `mode = staged` and `policy = staged_v1` (`lane_quota_v1` on a fallback, `learner` for a learner pick);
- `controller_decision_id`, when the chooser named a persisted staged decision. None does in R2a (Q2); the plumbing is proven by the EVSI test;
- `card_hash`;
- the named refusals, one id list per constraint, beside R1's `infeasible` (whole infeasible candidates);
- each block candidate's annotations;
- the frame's snapshot and manifest hashes, with the refusals' reasons, in `detail_json.staged_frame`.

**Payloads.** `router_decision_payloads` keeps the card (kind `card`, unique per decision and kind). Payloads older than `router.payload_retention_days` (365) are pruned on each write; the hash stays on the row.

### The receipt chain

`router_decisions.id` → `attention_blocks.decision_ref` → `plan_presentations.block_id` (and `router_decision_id`) → `practice_attempts.plan_presentation_id`.

**Writing presentations.**
- `_serve` writes the presentation with the `item_served` event, in one transaction. A reopen returns the same row (unique per block and item).
- A learner pick, and an open-list pick after the plan closed, get their own presentations: origin `learner_pick` / `open_list`, with no router decision.
- The router decision id is copied only when the ledger holds it, so a chooser's own reference is never written into the FK.
- A refused presentation row rolls back alone. The item is still served.

**Binding.** `submit_attempt`, `submit_dont_know` (both its paths) and `save_practice_draft` accept `planPresentationId`.
- The repository's attempt insert checks the id in the attempt's own transaction: it must exist, be of the attempt's item, and not be answered by another attempt. A refused id is logged and dropped, and the attempt records unbound. **Binding never fails a submit.**
- The draft RPC only accepts the id (so a client can autosave the parameters it submits with). Binding happens at submit.

**Outcomes v2** (`router_outcomes_v2`). The action is bound by the most exact receipt that exists:
1. `presentation`: the decision's block's presentations in serving order; the first one an attempt answered;
2. `candidate`: R1's offer and pick binding;
3. `session_rule`: R1's rule, labelled.

`action_binding`, `r_next_reference_status` and `r_cold_reference_status` are new DERIVED columns, rebuilt by the one replayer.

**The EVSI adapter** (`voi_calibration_report_v6`).
- **A committed live staged forecast** joins through this path: the `plan_block` decisions naming its controller decision → their blocks' presentation of the chosen item → the bound attempt. It is right-censored as `not_presented` or `presented_unanswered`, and is never joined by a session rule or by the next attempt on the item.
- **An admitted project probe's join** now prefers its presentation's bound attempt over the serving's offer.

### `LearnerStateCardV1`

**The builder is pure** (`router/card.py`):
- typed fields: decision, session, intent, candidates, learning objects, last 7 days, open problems, unknowns, self-reports, recent work, and `evidence_sections` (the registry hook for §15.1 and §15.5);
- text sections;
- the budget order of D8: older successes first, then older excerpts, then older attempts. Typed fields never drop;
- a SHA-256 hash.

**The gatherer reads the ledger** (`daily_plan/router_card.py`) with bounded reads, strictly before the decision time.

**Learning objects.** For the candidates' learning objects and their direct prerequisites, it reads:
- the active predictor's P(success) with a 95% interval, on the first candidate item of each learning object;
- untested / assumed / demonstrated;
- FSRS recall now;
- the evidence counts, including held grades and assisted attempts.

**Recent graded work:** up to 30 attempts, newest first.

**Open problems:** open diagnosed causes, unsettled answers, and learner-named gaps that have not been reversed.

**Self-reports:** returns and claims.

**The leakage rules (G5):**
- no reference solution, key, rubric or source text is read;
- a candidate item contributes its topic, minutes and kind only;
- past work on exam material keeps its result but shows no question and no answer. Exam material is an `exam_attempt`, or an item whose provenance cites what `source_retrieval.corpus.exam_exclusions` names: exam-role members and every `held_out_evaluation` unit. Main's corpus predicate stands in until the one exam predicate (`content/sources/exam_material`) lands;
- past work on a surface reserved for an assessment is treated the same way;
- when the exam predicate cannot be read, no past work shows a question or an answer (fail closed);
- a held grade renders "held for review (no score yet)";
- an unverified key says so.

A section that cannot be read is named in `unknowns`.

### The plain "why" (`router/why.py`)

- **Router blocks** say why in plain words, from the candidate's reason code. Examples:
  - "Eigenvalues again, before it slips."
  - "To check you still know Bases, without hints."
  - "A quick check on Spans, added from your question."
  - "Next: reading 3.2 Bases."
  - "That's today's time."
- **DL1's lane-prefixed reason stays** on the logged candidate.
- **The receipts** sit behind the existing why toggle's `details`: "Picked by the plan's usual rule; no model was asked. Receipt: learnloop router card --decision <id>".
- **A deferred P2 step** shows one sentence, for example "This step waits for a question you haven't seen yet."
- **The deny-list.** `DENY_PATTERNS` is the server-side twin of `copy/denyList.ts`, plus the plan's own terms (lanes, propensity, Decider, staged, queue, due, chooser, candidate, planner). A test runs every sentence through it.

### The D13 bridge

`golden_path.advance` calls `advance_live(requested_to_state, requested_reason)` when `bridge_active`.

- **Staged-owned runs.** The staged policy is consulted and logged as `staged_p2`.
  - A request equal to the canonical successor advances, with the client's reason recorded as the direct call recorded it.
  - A request for another state is the learner's own choice (`explicit_choice`; logged `learner_pick = 1`, no propensity). It advances as requested.
  - A staged veto appends no transition, returns `result: null` with `bridge.deferred` (`vetoReason`, `message`), and writes the existing deferral artifact.
- **Runs the staged policy does not own** advance exactly as requested.
- **Switched off, or below `mvp-0.23`,** the RPC calls `GPR.advance` directly and has no `bridge` key.
- `staged_p2` rows keep R1's session-rule binding: P2 practice opens write no presentations, which is out of scope.

### Versioning, config and CLI

- **Versioning.** `ROUTER_STAGED_FRAME_ALGORITHM_VERSION = "mvp-0.23"` is appended to the chain, with `ROUTER_STAGED_FRAME_VERSIONS`. `upgrade_to_mvp023` accepts `mvp-0.22`, or `mvp-0.9`..`mvp-0.21` through `upgrade_to_mvp022` with its notes passed through. `learnloop upgrade --to mvp-0.23` is also the default. New vaults start at `mvp-0.23`.
- **Config.** `[router]` gains `enabled = true`, `mode = "staged"` (the only value until R2b), `card_token_budget = 16000` and `payload_retention_days = 365`. These are modelled defaults, kept out of the 80-line template.
  - All sixteen defaults snapshots were recomputed (every one moves only because the effective config gains the keys), and `mvp-0.23`'s was added.
  - The two numeric leaves are registered as structural/operational.
- **CLI.**
  - `learnloop router card --vault V --decision ID [--json]` prints a stored card, read-only.
  - `learnloop router log` now shows each decision's `card_hash` and outcome `action_binding`.
  - The help snapshot was regenerated: `<root>`, `upgrade`, `router` and `router card` changed.

### Frontend (`apps/learnloop-tauri`)

- **The presentation id.** The plan step's `presentationId` rides with the practice offer:
  - `PlanStepAction.planPresentationId`;
  - `PracticeOffer.presentationId`;
  - `planPresentationForServe`, which follows the candidate's rules except that a resumed retry key keeps it. (Corrected by review F5: the offer is in memory only, so the draft now stores the presentation beside its retry key and a restart restores it; see `router-r2a-codex-review.md`.)

  It reaches `PracticeScreen`, which sends it on submit and on "I don't know". This works on Begin, on Continue, on feedback's Next under the plan and on a full-list pick.
- **`DailyPlanView`'s why toggle** shows `whyDetails` behind a collapsed `details` (router blocks only).
- **`GoldenPathScreen`** shows a deferred step's sentence.
- **`RunAdvanceResultDto.result`** is nullable, with an optional `bridge`.
- No `src-tauri` change.

## Deviations from the plan, and decisions made here

1. **Where the frame lives.** The plan names `router/staged_frame.py`, but two import contracts rule that out:
   - `router-log-is-a-leaf` forbids the router package from importing `scheduling` (the constraint engine and snapshot);
   - `frozen-cross-package-cycles` forbids a router → `daily_plan` cycle (`daily_plan.engine` imports `router.plan_log`).

   So the frame, the chooser, the card's gatherer and the policy live in `daily_plan/`. The router package keeps the pure, leaf parts: the card builder, the "why" copy and the deny-list, the logger, outcomes and stores. All 17 contracts are kept.
2. **No ε tie-break in R2a's staged mode.**
   - **What the plan says.** §3.1 item 4 says staged-mode ties go through `epsilon_tiebreak`. §0's table, §9's manual run and this stage's task say the order is unchanged, with identical block sequences where no veto fires.
   - **Why not.** The two cannot both hold. Within a lane, `planner_value = 1/(1+rank)` makes adjacent high ranks fall within 5%, which is an artifact of rank, not a value margin. §3.3 item 7 already says these values are not comparable across lanes.
   - **What was built.** R2a's `staged_v1` is deterministic (p = 1).
   - **Where exploration comes in.** R2b's mixture gives every reversible top-k candidate an ε floor, the honest place for it.
   - Open question 1.
3. **The frame's scope on Today.**
   - The item roles, and which constraints can and cannot refuse, are set out in §What was built: a decision made here because the P4 constraints are written for staged blocks.
   - Requests and follow-ups are not vetoed (the container places them).
   - A whole-frame failure (a bug) is logged with `detail.staged_frame.error` and DL1's packing stands. This fails open so Today never blocks. A single item's unknown freshness fails closed, as P4 says.
4. **The card is built by its own gatherer, not the V3 renderer.**
   - The V3 renderer (`field/probability_states.py`) needs `diagnosis.split.history.VaultHistoryStore`, which the router leaf cannot import, and loads the whole history per prediction.
   - The card's gatherer reads scale with the card's topics (at most 40), never with candidate items. (Corrected by the Codex review: the topics' attempt history is read in full for the evidence counts, held grades in 500-attempt chunks, and the headline classification per topic.)
   - It follows the spec's sections and V3's budget rule, but not V3's per-attempt cutoff machinery, which is for a prediction harness.
   - It includes the stem and the learner's own answer for attempted items (spec §4, "Recent work"), except exam or reserved material. (Corrected by review F6: the stem is the attempt's pinned contract prompt, never today's; with no pinned revision no stem shows.)
   - Because the decision time is in the card, the hash moves with the clock.
5. **Presentations are receipts at every plan version.** Like R1's logging, they are written wherever the plan serves, whatever `router.enabled` and the version. They change nothing served, and G8 compares `block_chosen` details. Every plan step therefore carries `presentation_id` (null until served).
6. **Teach-back dialogues and probe-block submissions are not bound.** Their own RPCs do not take the id yet; the outcome falls back to the labelled session rule. Neither does the TUI, which keeps DL0's queue.
7. **Payload pruning runs on write.** It is one indexed `DELETE` in the block's transaction, after the card is stored, isolated so it never blocks the plan. There is no separate command.
8. **`controller_decision_id` on Today** is filled only when a router record names one. R2a's frame persists no staged decision (Q2), so in production it stays NULL. The EVSI test proves the join with a chooser that names a staged decision committed through a fake selector.
9. **Module reference notes were not generated.** `module_validate.py` already reports 474/801 module coverage on main, and no test runs it. The DB and config references were regenerated and validate clean.

## Fail-first (plan §9 R2a)

The tests were written before the code (commit `9633767f1`) and run on the base:

| # | Test | On the base | After R2a |
|---|---|---|---|
| 1 | `test_evsi_staged_binding.py`: a staged forecast committed through a fake `DiagnosticSelector` | main's adapter reports `no_attempt_binding` for every committed live staged forecast (`test_voi_forecasts.py:276`). The new test fails importing the R2a successor; its setup needs the receipt | joins the bound attempt (`taken`). `not_presented` and `presented_unanswered` are right-censored; an unbound attempt is never the outcome |
| 2 | `test_router_presentations.py::test_an_attempt_after_a_skip_binds_by_presentation_not_the_session_rule` | **assertion failure**: R1's session rule bound the block's decision to a later full-list pick of the skipped first item (`att_pi_m1a_…` instead of the answer to the second item) | binds by presentation (`action_binding = presentation`) |
| 3 | `test_router_g1_feasibility.py::test_a_seen_probe_is_served_by_dl1_and_refused_by_the_staged_frame` | DL1 plans the seen diagnostic probe in the maintain block (that half passes on the base), then the R2a import fails | refused, `named.hard_exposure_collision = [pi_probe_seen]`, reason `exact_surface_collision` |
| 4 | `test_router_p2_bridge.py::test_golden_path_advance_consults_the_staged_policy_through_the_bridge` | the RPC advances the run directly with no staged decision logged (that half passes), then the R2a import fails | the bridge logs the `staged_p2` decision and the response carries `bridge.authority = staged` |

## Tests added and changed

**New:**

| File | Covers |
|---|---|
| `tests/test_router_g1_feasibility.py` | G1: the frame's refusals (hard exposure, assessment reservation); an unseen probe stays; a rogue chooser falls back; projections keep the refusals |
| `tests/test_router_r2a_serving.py` | G2 (an irreversible block is only the rule's deterministic pick, π = 0 otherwise, never in `draw_support`); order parity with DL1 where nothing is refused; G9 (picks); the receipt chain through the RPCs, including wrong, foreign and used ids that never fail a submit; G6 (outcomes v2 replayed twice with model clients forbidden); a durability-lane test for both new tables; G8 on backup-API copies of `linear_algebra`, `probability` and `arxiv_v2` (`router.enabled = false` at `mvp-0.23` equals `mvp-0.22`: block sequence and every `block_chosen` detail apart from ids) |
| `tests/test_router_presentations.py` | the presentation row, append-only triggers, picks' presentations, the labelled session-rule fallback |
| `tests/test_evsi_staged_binding.py` | the EVSI adapter (fail-first 1) |
| `tests/test_router_p2_bridge.py` | D13: through the bridge, the learner's choice, a veto in plain words, switched off, response shape |
| `tests/test_router_card.py` | G5 leakage (reference solution, reserved stem, exam stem and answer, held score); the exam predicate failing closed; determinism; budget truncation order; `learnloop router card`; payload pruning |
| `tests/test_router_why_copy.py` | every sentence through the deny-list; reason codes; every why on a real routed plan |
| `tests/test_router_ladder_parity.py` | `ladder_eligibility` against `evaluate_staged_rule` over all 2^11 signal combinations, with and without a reachable rung 8 |
| `tests/test_mvp023_upgrade.py` | the successor: chain, switch, upgrade paths, guard notes, CLI default, new vaults, fingerprints, head fixture, the router Decider route never a Tier-1 judgment |

**Changed:**
- the earlier successors' vocabulary tests (`mvp-0.23` is the latest);
- the head-fixture paths (`migration_head_205`);
- `test_router_outcomes.py` (v2, `action_binding`);
- `test_voi_merge_composition.py` (report v6);
- `test_mobile_allowlist.py` (R2a's extended RPCs, and the new parameter pinned on the three answer RPCs);
- `test_architecture.py` (the presentation store registered as an SQL owner);
- the CLI help snapshot;
- the frontend tests (`dailyPlan.test.tsx`, `practiceOffer.test.ts`, `DailyPlanView.test.tsx`).

## Migrations

**205 (placeholder) `205_router_staged_frame.sql`:**
- rebuilds the append-only `router_decisions`: same columns, rows, indexes and triggers, plus an index on `controller_decision_id`. Its `decision_kind` CHECK now also admits `plan_interrupt` (R2c), so the table is rebuilt once (the 175 precedent; `PRAGMA foreign_keys = OFF`, `foreign_key_check` clean);
- adds three DERIVED columns to `router_outcomes`;
- adds `plan_presentations` (RAW_LEDGER, append-only by trigger);
- adds `practice_attempts.plan_presentation_id` with a partial unique index;
- adds `router_decision_payloads` (WORKFLOW).

**Bookkeeping:**
- Table roles are registered.
- The head fixture is `migration_head_205`: a backup-API copy of `migration_head_201` with only 205 applied, in rollback journal mode, `integrity_check` ok, `foreign_key_check` clean. Its README was updated, and every hard-coded path was moved (19 test files and the two DB reference scripts).
- `db_generate_reference.py` was rerun, and `db_validate_reference.py` reports `errors: []`: 321 table notes, 817 config leaves, schema head 205.

## Manual runs (backup-API copies under `fixtures-local/`)

**Setup.** Backup-API copies (`copy_tree_with_databases`) of this worktree's tracked `fixtures/linear_algebra`, `fixtures/probability` and `fixtures/arxiv_v2` (all at `mvp-0.8`) were made under `fixtures-local/r2a-shadow/` and `fixtures-local/r2a-parity/`, with `LEARNLOOP_CONFIG_DIR` an empty directory.
- Each copy was migrated on open (to 205) and then upgraded: `mvp-0.8` → `mvp-0.9`, then `upgrade_to_mvp023` through the chain.
- The chain's advisory-guard notes were passed through on every copy.
- No tracked fixture was opened except to copy it, and `git status fixtures/` is clean.
- The scripts are in the stage's scratchpad: `r2a_shadow.py`, `r2a_prep_parity.py`, `r2a_parity.py`, `r2a_veto_prep.py` and `card_scan.py`.

### 1. Upgrade, then `rebuild --shadow` (playbook item 7)

On `linear_algebra`: `mvp-0.8` → `mvp-0.9` → `mvp-0.22` (through the chain), rebuilt twice to its fixed point, then shadowed. `learnloop upgrade` (the default target) then took it to `mvp-0.23`, and it was shadowed again.

| | Facet | Mastery | Schedule | Live database |
|---|---:|---:|---:|---|
| `rebuild --shadow` at `mvp-0.22` | 0 | 0 | 0 | unchanged |
| `rebuild --shadow` at `mvp-0.23` | 0 | 21 | 0 | unchanged |

The 21 mastery rows differ only in `algorithm_version` (`mvp-0.22` → `mvp-0.23`), as at every successor. So there is no delta beyond the version labels.

`learnloop doctor --json` at `mvp-0.23` reports 56 issues: no router or plan issue, and one error, the fixture's missing `rubrics` directory (the same as at the Decider landing).

### 2. Sixty seeded sessions: R2a against the switch off

**Setup.** Each fixture has two copies at `mvp-0.23`:
- `on`: the router enabled;
- `off`: a backup-API copy of the upgraded `on` with `router.enabled = false`.

**The sessions.** Twenty seeded sessions per fixture (one a day from 2026-10-14) ran on each copy:
- the real scheduler build and the real plan engine;
- a fixed session id per seed;
- deterministic synthetic answers, written as raw attempt rows bound to their presentations, with no model.

**Measured:**
- (a) the refusals per constraint at every routed boundary;
- (b) at every routed boundary, the counterfactual DL1 decision on the same state (`decide()` with `DEFAULT_POLICY`, which is pure);
- (c) each session's block sequence on `on` against `off`.

| Fixture | Sessions | Routed boundaries | Boundaries with a refusal | Refusals by constraint | Boundaries equal to DL1's | Sessions with identical block sequences |
|---|---:|---:|---:|---|---:|---:|
| linear algebra | 20 | 122 | 0 | none | 122 / 122 | 20 / 20 |
| probability | 20 | 100 | 0 | none | 100 / 100 | 20 / 20 |
| arxiv v2 | 20 | 203 | 0 | none | 203 / 203 | 20 / 20 |
| **total** | **60** | **425** | **0** | | **425 / 425** | **60 / 60** |

**Why nothing was refused.** On these vaults nothing upstream lets a hard-constraint item through:
- the scheduler already withholds administered `diagnostic_probe` items and unrenderable or inactive items;
- no surface holds a live assessment reservation;
- no project-probe provider is registered.

**A seeded-veto run.** To exercise the veto on real data, a third pair of `linear_algebra` copies gave three of the first plan's items a live assessment reservation on both arms (`r2a_veto_prep.py`). The refused items were `pi_orient_incomplete_spec_02`, `pi_what_makes_structure_interpret_01` and `pi_axiom_closure_recall_01`. Ten sessions followed:
- **Refusals:** every one of the 62 routed boundaries refused them, under `assessment_reservation` and only that constraint.
- **Choices:** 22 of those boundaries still chose DL1's block (the refused items were not in it). The rest chose DL1's packing without them.
- **Serving:** the reserved items were served 0 times on the routed copy and 29 times on the switch-off copy.

**Latency** (`advance(serve=True)`: one boundary decision with its frame and card, or a serve):

| | p50 on / off (s) | p90 on / off (s) | max on / off (s) |
|---|---|---|---|
| linear algebra | 0.525 / 0.472 | 0.740 / 0.679 | 1.49 / 1.27 |
| probability | 0.480 / 0.466 | 0.769 / 0.746 | 1.64 / 1.44 |
| arxiv v2 | 0.389 / 0.332 | 0.594 / 0.518 | 0.97 / 0.78 |

`get_daily_plan` on the `linear_algebra` copies (the view rebuilds the frame's snapshot per RPC for its projections):
- first call, building the plan with its card: 1.62 s on, 1.12 s off;
- later calls: p50 0.43 s on, 0.27 s off.

### 3. One boundary's card, read for leakage

`learnloop router card` was run on the `linear_algebra` routed copy for its first decision: card `098d6a6c…`, 15.9 kB of text and about 10k tokens with the JSON, under the 16k budget, so nothing was truncated.

**What it holds:**
- the session;
- seven candidates, each a topic, minutes, item count, kind, reversibility and reason code, with no stem;
- five topics with predicted success, intervals, recall now and evidence counts;
- the last 7 days;
- two open diagnosed causes with their statements;
- self-ratings;
- the recent graded work, with the learner's own answers and the attempted items' stems.

It was read by eye, and no reference solution, answer key, rubric, source text or held-out material appears.

**Programmatic scan (`card_scan.py`).** Every stored card on all four routed copies (122 + 100 + 203 + 62 = 487) was scanned against the vault:
- 0 occurrences of any item's expected answer;
- 0 stems of unattempted candidate items;
- 0 stems of reserved items (3 on the seeded-veto copy).

**Withheld entries.** On `linear_algebra`, 376 recent-work entries, across the cards, show their result but no question and no answer. All are `exam_attempt` answers (the learner's exam sessions). On the seeded-veto copy there are 405, which adds the reserved items' past work.

**The exam predicate.** The cards use main's `corpus.exam_exclusions`, because the one exam predicate has not landed (open question 4).

## Paid calls and spend

None. R2a calls no model.

## Gate

- **Install:** `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2` (pypdfium2 5.14.0). `TMPDIR` was the worktree's `fixtures-local/tmp`.
- **`uv run lint-imports --no-cache`:** 17 contracts kept, 0 broken.
- **`flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto`:**
  - **10665 passed**, 0 failed, 48 warnings (10 min 19 s), on the final code.
  - An earlier run on the first implementation commit failed 22 tests. Twenty were expected moves: the earlier successors' vocabulary pins, the parameter registry's two new config leaves, and the SQL-owner registration of the presentation store. All were fixed in `264b5ed3c`.
  - The other two, `test_mvp021_upgrade.py::test_the_successor_rebuild_equals_mvp020s_projection` and `test_p0_cutover_mvp08.py`, failed only under load and pass alone (11 passed). Both pass in the final run.
- **`flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability`:** **100 passed**, 10565 deselected (2 min 52 s).
- **Frontend** (`apps/learnloop-tauri`):
  - `npm install`: clean, no lockfile change;
  - `npm run typecheck`: clean;
  - `npm test`: **73 files, 485 tests passed**;
  - `npm run frontend:build`: built (the existing chunk-size warning only).
- **`cargo check`:** not required; nothing under `src-tauri` changed.
- **References:** `db_generate_reference.py` was rerun, and `db_validate_reference.py` reports `errors: []` (schema head 205, 321 table notes, 817 config leaves). The CLI help snapshot was regenerated. All sixteen defaults snapshots were recomputed, and the template `.pyc` was cleared first.
- **Targeted runs:** the new R2a test files pass (G1, G2, G5, G6, G8, G9, the receipt chain, EVSI, the bridge, why copy, card, ladder parity, `mvp-0.23`).

## Open questions

1. **Staged-mode ties** (deviation 2). R2a's `staged_v1` is deterministic. Should R2b's `staged` mode keep it so, with exploration only from the mixture's ε floor, or add the §3.1 `epsilon_tiebreak` over in-lane near-ties (which changes DL1's order)? Recommended: keep it deterministic.
2. **The frame's veto on follow-ups.** Mid-plan follow-ups and requests are placed by the container and never vetoed by the frame. A follow-up on a reserved or seen quick-check surface is the follow-up chooser's to refuse. Should R2c's restraint decision also run the constraint engine on them? Recommended: yes, at R2c.
3. **Teach-back and probe-block binding** (deviation 6). Their RPCs could take `planPresentationId` the same way. This was left out of R2a's scope.
4. **The one exam predicate.** The card uses main's `corpus.exam_exclusions` (exam-role members and `held_out_evaluation` units). Switch it to `content/sources/exam_material` when the exam-protection landing merges. It is a one-line change in `daily_plan/router_card.py::_withheld_items`.
5. **Rung signals on Today.** The ladder annotation derives rungs 2, 3, 4, 5 and 9 per LO. Rungs 1 (triage), 6 (integration), 7 (terminal) and 8 (milestone) never hold on Today. R2b's models read the card, not the ladder, so this only matters if the owner wants the ladder to order Today later (Q1 says no).
6. **Successor and migration labels** at the merge: `mvp-0.23` and 205 are placeholders. The exam-protection, reading-hardening and method-explicit stages land in parallel.
