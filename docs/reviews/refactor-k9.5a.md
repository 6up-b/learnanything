# K9.5 part 1: diagnosis identities and test ports

Base: `5f25991018`, branch `refactor/k9.5a-diagnosis-pins`, worktree
`/home/saturn/Documents/thinking/learnanything-k95a`. Tests and this record only; no commit made.

## 1. Scope and method

Read the diagnosis strategy's K9.5 and section 0 row 13, CLAUDE.md's pin contract, the pin runner/helper/goldens,
K10.4's record, and strategy section 2.19 T4. Part 2 (journey golden and coverage) was not started.

52 new value pins across 13 registry sites; 220 existing identity digests are byte-identical to HEAD.
`identities.toml` gains 52 lines, loses none. `identity_shapes.toml` changes only TraceContract's sites metadata,
adding K9.5b; its fields and every existing shape remain unchanged. TraceRecipe was already recursively pinned.
The fixed inputs live in `tests/diagnosis_identity_helpers.py`, registered by `tests/identity_pins_helpers.py`.
No test implements an identity hash. Every value comes from the production path below. Repository fakes return
fixed reads and capture actual write arguments; `CapturedWrite` stops at that boundary without running unrelated
follow-up work. It derives from BaseException so production's best-effort Exception handlers cannot swallow a
capture. The only model response needed is a StructuredClientFake answering the prerequisite judge; no model,
network or real learner data was used. Existing `item()`/`vault()` pin builders keep content fixed in memory.

The AST unregistered-dump guard is unchanged. Sites register the identity builders rather than adding provenance
exemptions. The typed TraceContract enters the blind-input payload whole (including nested TraceRecipe); the
PracticeItem/rubric themselves are projected to explicit fields before they enter this identity. The other inputs
are plain mappings or explicit identity views, not additional whole-dumped model roots.

## 2. Pins

| Site | Pins |
|---|---:|
| K9.5m | 6 |
| K9.5l | 7 |
| K9.5a | 3 |
| K9.5b | 6 |
| K9.5c | 8 |
| K9.5d | 1 |
| K9.5e | 2 |
| K9.5f | 2 |
| K9.5g | 1 |
| K9.5h | 8 |
| K9.5i | 2 |
| K9.5j | 3 |
| K9.5k | 3 |

All module paths below are under `learnloop.diagnosis` unless explicitly named.

| Pin | Production path | Fixed input |
|---|---|---|
| `K9.5a.cdo_probe` | `causal_orchestrator.record_probe_classification → classify_probe_response` | presentation_pin; two pinned version-2 hypotheses with opposite sign predictions; observed sign +; deterministic source |
| `K9.5a.cdo_question` | `causal_orchestrator.record_learner_embedded_prediction` | factor_pin, question_pin, att_pin; whitespace-padded learner prediction, stripped by production |
| `K9.5a.cmc` | `causal_orchestrator.enqueue_backfill_obligation → _machine_check_id` | repair_class_mapping_backfill, factor_pin, att_pin, reversed [hyp_b, hyp_a] |
| `K9.5b.bpb` | `causal_probe_coherence.generate_blind_prediction_bundle` | hyp_a version 2; existing identity-pins item(), result rubric, its typed TraceContract; generator returns predicted sign +; fixed model/schema |
| `K9.5b.bpi` | `causal_probe_coherence.generate_blind_prediction_bundle → BlindGenerationInput.as_payload` | same bundle input; returns the production input_hash, separately from bundle_id |
| `K9.5b.cco` | `causal_probe_coherence.record_causal_cold_outcome` | learner_declined, task_pin, episode_pin, source_pin; no cold attempt or servable opportunity |
| `K9.5b.ccv` | `causal_probe_coherence.record_delayed_cold_verification` | source Jan 1 / cold Jan 3; fresh different-surface item, correctness 1, two hypotheses and two avoided affordances; stops at verification insert |
| `K9.5b.cpc` | `causal_probe_coherence.create_probe_candidate` | passed audit, locked hyp_a/hyp_b/other_or_unknown, opposite pinned predictions, independently compiled item-local contract |
| `K9.5b.pma` | `causal_probe_coherence.audit_manipulation_contract` | Transpose AB / Transpose CD source and candidate; declared prompt change; surface-family incidental change; separate author/reviewer IDs and positive review |
| `K9.5c.ch` | `causal_attribution.mint_causal_mechanism_taxonomy` | same two fixed source heads; pins returned source_head_hash |
| `K9.5c.ck` | `causal_attribution.append_dialogue_candidate → _candidate_key` | fixed hypothesis statement, learner_state scope, result criterion; att_pin/question_pin; pins returned episode_key containing ck |
| `K9.5c.ctv` | `causal_attribution.mint_causal_mechanism_taxonomy` | same taxonomy and assignments; pins taxonomy_version_id |
| `K9.5c.dr` | `causal_attribution.materialize_causal_episode` | fixed identity-pins vault/item; att_pin Jan 1, no evidence/events/hypotheses; frozen tests.helpers.NOW |
| `K9.5c.mechanism` | `causal_attribution.mint_causal_mechanism_taxonomy` | two version-2 concrete hypotheses sharing re_pin, learner_state scope and profile; default minimum 2; draft |
| `K9.5c.rc` | `causal_attribution.select_minimal_repair → _repair_class` | replace_step on result, preserve setup, three minutes, reveal budget .25, episode_pin |
| `K9.5c.re` | `causal_attribution.repair_equivalence_id` | replace_step, result criterion target and facet_pin preservation |
| `K9.5c.rv` | `causal_attribution.RepairValidationResult.as_dict` | valid result; preserves_target structural check; verified x=2 |
| `K9.5d.mvn` | `missing_vocabulary.record_missing_vocabulary_notes → _note_id` | diagnostic abstention; fixed attempt/item/error/criterion and prompt/policy/model revision stamps; production default note version |
| `K9.5e.correct_sample` | `split.live.sampled_correct_answer` | att_pin_0 through att_pin_31 at rate .5; production exposes a Boolean, not the raw draw |
| `K9.5e.prior_draw` | `split.prior_analysis.assign` | randomized assignment for att_pin; full Arm including exact draw |
| `K9.5f.kind` | `text_gaps.judges.kind_input_hash` | tutor question question_pin, fixed words and item context |
| `K9.5f.needed` | `text_gaps.judges.ask_needed` | Transpose AB and matrix-products prerequisite; StructuredClientFake answers yes; capture ledger input_hash |
| `K9.5g.pair` | `recurrence.guard.guard_pairs → _subject; matching.judge.pair_input_hash` | fixed transpose pair; same wrong answer from keeping order versus believing multiplication commutes; GUARD_KIND |
| `K9.5h.workbenchFalse_figuresFalse_priorFalse` | `split.jobs.run_diagnose_job → _diagnose` | shadow att_pin; public input readers give workbench=False, figures=False; prior-analysis config=off; capture agent-run prompt_version before model request |
| `K9.5h.workbenchFalse_figuresFalse_priorTrue` | `split.jobs.run_diagnose_job → _diagnose` | shadow att_pin; public input readers give workbench=False, figures=False; prior-analysis config=on; capture agent-run prompt_version before model request |
| `K9.5h.workbenchFalse_figuresTrue_priorFalse` | `split.jobs.run_diagnose_job → _diagnose` | shadow att_pin; public input readers give workbench=False, figures=True; prior-analysis config=off; capture agent-run prompt_version before model request |
| `K9.5h.workbenchFalse_figuresTrue_priorTrue` | `split.jobs.run_diagnose_job → _diagnose` | shadow att_pin; public input readers give workbench=False, figures=True; prior-analysis config=on; capture agent-run prompt_version before model request |
| `K9.5h.workbenchTrue_figuresFalse_priorFalse` | `split.jobs.run_diagnose_job → _diagnose` | shadow att_pin; public input readers give workbench=True, figures=False; prior-analysis config=off; capture agent-run prompt_version before model request |
| `K9.5h.workbenchTrue_figuresFalse_priorTrue` | `split.jobs.run_diagnose_job → _diagnose` | shadow att_pin; public input readers give workbench=True, figures=False; prior-analysis config=on; capture agent-run prompt_version before model request |
| `K9.5h.workbenchTrue_figuresTrue_priorFalse` | `split.jobs.run_diagnose_job → _diagnose` | shadow att_pin; public input readers give workbench=True, figures=True; prior-analysis config=off; capture agent-run prompt_version before model request |
| `K9.5h.workbenchTrue_figuresTrue_priorTrue` | `split.jobs.run_diagnose_job → _diagnose` | shadow att_pin; public input readers give workbench=True, figures=True; prior-analysis config=on; capture agent-run prompt_version before model request |
| `K9.5i.context` | `robust_composition.decision_context_hash` | episode/card/algorithm IDs, two-slot map, .3/.7 belief; production parameter defaults |
| `K9.5i.seed` | `robust_composition.build_ensemble → _seed_int` | calibration_pin/context_pin, one latent outcome and two emissions; one draw; returns exact seed |
| `K9.5j.embedding` | `split.embeddings.misconception_record → _record` | durable:belief_pin, Matrix multiplication commutes.; production record recipe |
| `K9.5j.gap_query` | `text_gaps.kinds.query_hash` | prerequisite field; Matrix multiplication / The order matters. text |
| `K9.5j.retrieval` | `split.retrieval.content_hash` | fixed transpose divergence text and production recipe version |
| `K9.5k.contrast_draw` | `contrast_pairs.randomization_draw` | session_pin:pair_pin:2026-01-01 |
| `K9.5k.criteria` | `voi_forecasting.facet_contract_criteria_hash` | one result criterion, two points and facet_pin target |
| `K9.5k.pack` | `diagnostic_pack.pack_content_hash` | pack/blueprint IDs and one card with reversed coverage order and instrument ref |
| `K9.5l.compiled` | `probe_families.CompiledInstrument.compiled_likelihood_hash` | two slots (.8/.2 and .3/.7); right/wrong; pseudo-count 12; policy_pin |
| `K9.5l.creation` | `text_gaps.actions.creation_ids → edge_id_for → _hash` | question_pin; Matrix products LO / Product order concept; dependent lo_pin; pins concept, LO and edge IDs |
| `K9.5l.emissions` | `causal_diagnostic_selector.likelihood_regime_for_candidate → _stable_emission_key` | two opposite sign bundles with explicit open-set exclusion; checks arm_b then pins emission keys |
| `K9.5l.family` | `probe_families.ProbeFamilyTemplate.from_dict → schema_hash` | family_pin version 2; contrast; right/wrong alphabet and a/b slots; defaults unset |
| `K9.5l.guard_suite` | `recurrence.guard.guard_suite → _case; suite_hash` | production built-in authored suite; pins ordered case IDs and suite hash |
| `K9.5l.instances` | `probe_instance_generation.parametric_instance_payloads → _instance_payload` | fixed vault, minimal-recall template and card_pin v2; count 2, seed 7, frozen clock; pins ordered item IDs |
| `K9.5l.needed_tier1` | `text_gaps.tier1.ask_needed` | Transpose AB context; capture input_hash at public Decider boundary before any call |
| `K9.5m.belief_reversal` | `text_gaps.actions.not_this_belief` | gap_pin from question_pin targeting durable belief_pin; capture ledger key |
| `K9.5m.card` | `split.card.record_card_tap` | completed diagnosis; not_same_mistake citing att_prior; fixed feedback_pin; capture ledger key |
| `K9.5m.guard_link` | `recurrence.guard.record_diagnoser_links` | run_pin/diagnosis_pin fixed DiagnoserLink; capture lookup query key |
| `K9.5m.pack_card` | `diagnostic_pack.assemble_pack → _canonical_cards` | two candidate cards, fixed blueprint; first card has result/setup coverage and instrument_pin; capture first card hash |
| `K9.5m.pattern` | `split.jobs.record_pattern_verdicts` | diagnosis_pin; validated claim index 2 citing att_prior; capture lookup query key |
| `K9.5m.prerequisite_reversal` | `text_gaps.actions.reversal_verdict` | undo_creation for gap_pin, created lo_pin and pi_pin; learner actor; fixed timestamp |

## 3. Relocated sites and search findings

No requested identity builder was removed. The strategy's line numbers were stale: the two cdo calls are now
causal_orchestrator.py:2621 and :2780; the job version assembly starts at jobs.py:826. Coherence's six calls remain
at :989, :1000, :1478, :1562, :1812 and :1962; attribution's calls are :284, :687, :1104 and :2685.
The recurrence reference :10-20 is descriptive text, not a hash implementation: guard_pairs/_subject build the
subjects, and matching.judge.pair_input_hash builds the reuse key that run_guard and guard_status compare.

The search for hashlib/content_key/_content_id/sha256/seed also added: cmc machine checks; re repair equivalence;
ck dialogue candidate identity; ch source-head and ctv taxonomy-version identities; correct-answer sampling;
robust decision context and ensemble seed; retrieval, embedding and gap-query keys; forecast criterion contracts;
pack and pack-card hashes; contrast draws; family schema and compiled likelihood hashes; generated parametric
item IDs; causal emission labels; prerequisite concept/LO/edge creation IDs; built-in guard case IDs and suite hash;
the tier1 needed checkpoint; validated-pattern and guard-link lookup hashes; card and gap-reversal verdict keys.

Search boundaries: diagnostic_augmentation._sample's fingerprint groups the current batch's model samples (not a
later stored-row lookup); split.context's context_hash and split.snapshot's export hashes are input/run provenance.
The offline_review, grading_hardcases, split.pfc_report and recurrence.benchmarks/report keys remain harness/report
identities under the pin framework's existing HARNESS_REASON policy. No new allowlist entries were introduced.
This is not a new golden for all diagnostic prompts or all report contents.

## 4. Fail-first proof

Each edit below was physically written into src/, its selected pin tests run through the supplied t.sh, and the
original bytes written back in finally. `git diff --exit-code -- src/` succeeded after every restoration. No git
checkout/restore was used. The content-ID functions sort mapping keys, so merely reordering mapping entries would
be inert: these edits rename an identity field, swap distinct seed/list inputs, or change a serialized input.

Command form for each value row: `t.sh tests/test_identity_pins.py -q -k '<pins joined with or>' --junitxml=<scratch>/mutation_*.xml`.
All selected tests failed with the named identity's digest assertion (exit 1); there were no collection/setup errors.
The prompt-base edit covers all eight combinations; an additional prior-suffix order edit covers all four prior-on
combinations. Logs/XML and mutation drivers remain in the caller's scratch directory, outside the worktree.

| Pin | Scratch edit (production function; before → after) | Fails as |
|---|---|---|
| `K9.5a.cdo_question` | `record_learner_embedded_prediction: "question_event_id": question_event_id -> "question_event_key": question_event_id` | 1 identity digest assertion(s) |
| `K9.5a.cdo_probe` | `record_probe_classification: "feature_source": feature_source -> "feature_source_pin": feature_source` | 1 identity digest assertion(s) |
| `K9.5a.cmc` | `_machine_check_id: "kind": obligation.get -> "kind_pin": obligation.get` | 1 identity digest assertion(s) |
| `K9.5b.bpi`, `K9.5b.bpb` | `BlindGenerationInput.as_payload: "trace_contract": self.trace_contract -> "trace_contract_pin": self.trace_contract` | 2 identity digest assertion(s) |
| `K9.5b.bpb` | `generate_blind_prediction_bundle: "model_revision": model_revision -> "model_revision_pin": model_revision` | 1 identity digest assertion(s) |
| `K9.5b.pma` | `audit_manipulation_contract: "status": status -> "status_pin": status` | 1 identity digest assertion(s) |
| `K9.5b.cpc` | `create_probe_candidate: "factor_id": factor_id -> "factor_key": factor_id` | 1 identity digest assertion(s) |
| `K9.5b.cco` | `record_causal_cold_outcome: "outcome": outcome -> "outcome_pin": outcome` | 1 identity digest assertion(s) |
| `K9.5b.ccv` | `record_delayed_cold_verification: "repair_class_id": repair_class_id -> "repair_class_key": repair_class_id` | 1 identity digest assertion(s) |
| `K9.5c.rv` | `RepairValidationResult.as_dict: "verification": self.verification -> "verification_pin": self.verification` | 1 identity digest assertion(s) |
| `K9.5c.rc` | `_repair_class: "equivalence_scope": -> "equivalence_scope_pin":` | 1 identity digest assertion(s) |
| `K9.5c.dr` | `materialize_causal_episode: "schema_version": DIAGNOSIS_RECEIPT_SCHEMA_VERSION -> "schema_version_pin": DIAGNOSIS_RECEIPT_SCHEMA_VERSION` | 1 identity digest assertion(s) |
| `K9.5c.re` | `repair_equivalence_id: "target_refs": sorted -> "target_refs_pin": sorted` | 1 identity digest assertion(s) |
| `K9.5c.ck` | `_candidate_key: "statement_normalized": -> "statement_normalized_pin":` | 1 identity digest assertion(s) |
| `K9.5c.mechanism`, `K9.5c.ctv` | `mint_causal_mechanism_taxonomy: "repair_equivalence_id": equivalence -> "repair_equivalence_key": equivalence` | 2 identity digest assertion(s) |
| `K9.5c.ch`, `K9.5c.ctv` | `mint_causal_mechanism_taxonomy: "statement_normalized": str(value["statement_normalized"]) -> "statement_normalized_pin": str(value["statement_normalized"])` | 2 identity digest assertion(s) |
| `K9.5d.mvn` | `_note_id: "criterion_id", -> "criterion_key",` | 1 identity digest assertion(s) |
| `K9.5e.prior_draw` | `assign: {DESIGN}:{attempt_id} -> {attempt_id}:{DESIGN}` | 1 identity digest assertion(s) |
| `K9.5e.correct_sample` | `sampled_correct_answer: correct-answer-sample:{attempt_id} -> correct-answer-sample-pin:{attempt_id}` | 1 identity digest assertion(s) |
| `K9.5f.kind` | `kind_input_hash: "source": -> "source_pin":` | 1 identity digest assertion(s) |
| `K9.5f.needed` | `ask_needed: "task": NEEDED_TASK -> "task_pin": NEEDED_TASK` | 1 identity digest assertion(s) |
| `K9.5g.pair` | `_subject: statement.encode -> (statement + " pin").encode` | 1 identity digest assertion(s) |
| `K9.5h.workbenchFalse_figuresFalse_priorFalse`, `K9.5h.workbenchFalse_figuresFalse_priorTrue`, `K9.5h.workbenchFalse_figuresTrue_priorFalse`, `K9.5h.workbenchFalse_figuresTrue_priorTrue`, `K9.5h.workbenchTrue_figuresFalse_priorFalse`, `K9.5h.workbenchTrue_figuresFalse_priorTrue`, `K9.5h.workbenchTrue_figuresTrue_priorFalse`, `K9.5h.workbenchTrue_figuresTrue_priorTrue` | `_diagnose: DIAGNOSIS_PROMPT_VERSION -> (DIAGNOSIS_PROMPT_VERSION + "-pin")` | 8 identity digest assertion(s) |
| `K9.5h.workbenchFalse_figuresFalse_priorTrue`, `K9.5h.workbenchFalse_figuresTrue_priorTrue`, `K9.5h.workbenchTrue_figuresFalse_priorTrue`, `K9.5h.workbenchTrue_figuresTrue_priorTrue` | `_diagnose: {prompt_version}{PA.SUFFIX} -> {PA.SUFFIX}{prompt_version}` | 4 identity digest assertion(s) |
| `K9.5i.context` | `decision_context_hash: "episode_id": episode_id -> "episode_key": episode_id` | 1 identity digest assertion(s) |
| `K9.5i.seed` | `_seed_int: {calibration_model_hash}&#124;{decision_context_hash} -> {decision_context_hash}&#124;{calibration_model_hash}` | 1 identity digest assertion(s) |
| `K9.5j.retrieval` | `content_hash: {RECIPE_VERSION}\n{text} -> {text}\n{RECIPE_VERSION}` | 1 identity digest assertion(s) |
| `K9.5j.embedding` | `_record: [kind, field, version, text] -> [field, kind, version, text]` | 1 identity digest assertion(s) |
| `K9.5j.gap_query` | `query_hash: [GAP_RECORD_KIND, field, QUERY_RECIPE_VERSION, text] -> [field, GAP_RECORD_KIND, QUERY_RECIPE_VERSION, text]` | 1 identity digest assertion(s) |
| `K9.5k.criteria` | `facet_contract_criteria_hash: json.dumps(criteria, default=str) -> json.dumps({"criteria": criteria}, default=str)` | 1 identity digest assertion(s) |
| `K9.5k.pack` | `pack_content_hash: "pack_slug": pack_slug -> "pack_key": pack_slug` | 1 identity digest assertion(s) |
| `K9.5k.contrast_draw` | `randomization_draw: seed.encode -> (seed + " pin").encode` | 1 identity digest assertion(s) |
| `K9.5l.family` | `ProbeFamilyTemplate.as_dict: "grader_policy": self.grader_policy -> "grader_policy_pin": self.grader_policy` | 1 identity digest assertion(s) |
| `K9.5l.compiled` | `CompiledInstrument.compiled_likelihood_hash: "alphabet": -> "alphabet_pin":` | 1 identity digest assertion(s) |
| `K9.5l.instances` | `_instance_payload: {card.id}:{surface_family}:{prompt} -> {surface_family}:{card.id}:{prompt}` | 1 identity digest assertion(s) |
| `K9.5l.emissions` | `_stable_emission_key: json.dumps(values, -> json.dumps({"values": values},` | 1 identity digest assertion(s) |
| `K9.5l.creation` | `_hash: content_key(list(parts)) -> content_key(["pin", *parts])` | 1 identity digest assertion(s) |
| `K9.5l.guard_suite` | `_case: [expected, topic, problem, a, b] -> [topic, expected, problem, a, b]` | 1 identity digest assertion(s) |
| `K9.5l.guard_suite` | `suite_hash: [pair.case_id, pair.expected, pair.statement_a, pair.statement_b] -> [pair.expected, pair.case_id, pair.statement_a, pair.statement_b]` | 1 identity digest assertion(s) |
| `K9.5l.needed_tier1` | `ask_needed: "task": NEEDED_TASK -> "task_pin": NEEDED_TASK` | 1 identity digest assertion(s) |
| `K9.5m.pattern` | `record_pattern_verdicts: "claim": index -> "claim_pin": index` | 1 identity digest assertion(s) |
| `K9.5m.guard_link` | `record_diagnoser_links: "run": link.run_id -> "run_pin": link.run_id` | 1 identity digest assertion(s) |
| `K9.5m.card` | `record_card_tap: "diagnosis_feedback_id": feedback_id -> "diagnosis_feedback_key": feedback_id` | 1 identity digest assertion(s) |
| `K9.5m.belief_reversal` | `not_this_belief: "target": [target_kind, target_id] -> "target_pin": [target_kind, target_id]` | 1 identity digest assertion(s) |
| `K9.5m.prerequisite_reversal` | `reversal_verdict: "reversal": reversal -> "reversal_pin": reversal` | 1 identity digest assertion(s) |
| `K9.5m.pack_card` | `_canonical_cards: "instrument_ref": card.get -> "instrument_ref_pin": card.get` | 1 identity digest assertion(s) |
| K9.5b.bpi, K9.5b.bpb; TraceContract shape | Add `identity_pin_scratch: str = "added"` to TraceContract | 2 identity failures and 1 shape failure |
| K9.5b.bpi, K9.5b.bpb; TraceRecipe shape | Add the same field to TraceRecipe | 2 identity failures and 1 shape failure |

The shape commands used `-k 'TraceContract or K9.5b.bpi or K9.5b.bpb'` and the corresponding TraceRecipe selector.
After fixture review, the new cmc/cco inputs were tightened to the real vocabulary (`repair_class_mapping_backfill`
and `learner_declined`); their two mutations were rerun successfully against the final goldens. Thus 50 scratch
invocations total: 46 table rows, 2 shape checks and 2 repeats. All 52 final pins have fail-first evidence.

## 5. Six ports

| Test site | Before | After / behavior preserved |
|---|---|---|
| test_ux_phase4_feedback, simulation covered instrument | Patch probe_episodes.refuse_routine_display_covered to raise | Repository reveal reader writes a real routine disclosure for the first item; the real eligibility core refuses it. The simulation still produces results and at least one observation. |
| test_ux_phase4_feedback, refused offer race | Patch causal_orchestrator._answer_shown to False | Repository reader hides the probe's reveal on its first read and supplies it on subsequent reads. Real offer check passes, real commit refuses; unchanged lock/presentation assertions plus at least two reads. |
| test_voi_v2, _gate_abstains | Patch probe_episodes._robust_completion_override to a string | Supply a plain RobustDecision through probe_robust.robust_selection, with a stored one-observation minimum so real gate preconditions are met. Original episode/counterfactual assertions unchanged. |
| test_voi_v2, continuing receipt | Patch probe_episodes._robust_gate_verdict again | Remove the second patch; the same public selector fake feeds both the completion and counterfactual paths. Receipt still says continue, couldnt_reliably_distinguish and later. |
| test_daily_loop_lo_lifecycle_serving, stale uncertainty | Spy on probe_episodes.enter_episode | Call the producer normally and assert returned episode IDs/LOs plus actual repository state: none for dormant, one for active. |
| test_attempt_chain_records, failed post-diagnosis step | String patch causal_orchestrator.sweep_machine_checks | Repository.open_unresolved_cause_factors raises ValueError; the real sweep and post-diagnosis wrapper produce the same failed decision record. |

None left unported; no production seam was added. No assertion was loosened. The selector fake targets the public
selection dependency, not a relocated private gate. The old simulation patch manufactured an exception; the new
one manufactures the ledger fact that makes production raise it. The seventh strategy site remains outside scope
(already handled by K9.16).

## 6. Verification

Binding wrapper directory:
`/tmp/claude-1000/-home-saturn-Documents-thinking-learnanything/73b37aee-2550-41c4-88a8-8730b0f3c0c0/scratchpad/refactor-k95a/`.
All tests below used its t.sh, all other Python/ruff/lint-imports used its py.sh; explicit test paths only,
at most -n 4, one test command at a time. Golden writes used `py.sh python tests/test_identity_pins.py --write`.

| Command (wrapper names as above) | Result |
|---|---|
| t.sh tests/test_identity_pins.py -q (baseline) | 288 passed, 5.87s |
| same (first 39 new pins) | 327 passed, 5.63s |
| same (52 new pins) | 340 passed, 5.61s |
| same (final, after every mutation was restored and the final fixture vocabulary was checked) | 340 passed, 5.67s |
| t.sh tests/test_daily_loop_lo_lifecycle_serving.py tests/test_attempt_chain_records.py tests/test_ux_phase4_feedback.py -q -n 4 | 184 passed, 1 failed in the new simulation fake (missing datetime import); fixed |
| t.sh tests/test_voi_v2.py tests/test_ux_phase4_feedback.py -q -n 4 | 194 passed, 10.75s |
| t.sh tests/test_test_layout.py tests/test_structure_ratchets.py tests/test_architecture.py -q -n 4 | 24 passed, 24.22s |
| t.sh tests/test_ux_phase4_feedback.py tests/test_voi_v2.py tests/test_daily_loop_lo_lifecycle_serving.py tests/test_attempt_chain_records.py -q -n 4 --junitxml=<scratch>/final_ports.xml | 223 passed, 12.30s |
| py.sh ruff check | All checks passed |
| py.sh lint-imports --no-cache | 42 kept, 0 broken; 1,257 files, 14,096 dependencies |

Final edited-file counts: `tests.test_attempt_chain_records` 18, `tests.test_daily_loop_lo_lifecycle_serving` 11, `tests.test_ux_phase4_feedback` 156, `tests.test_voi_v2` 38.

The requested structure gate passed without a golden rewrite. At this tip `test_structure_ratchets.current()` has
no private-name setattr/getsource counters; the strategy describes their planned M0 ratchet. There was no failure
message naming a lowering command and no measured source structure change, so structure.toml was left untouched.
The six designated patch sites are gone; the three underscore-name patches among them are removed.

## 7. Limits and part 2 handoff

No tests were blocked by the sandbox, none skipped and none killed; no killed-run temporary directory needs removal.
No baseline identity failure or new production bug was found (no bug-ledger row needed). No full suite, coverage,
journey golden, model service, socket or bubblewrap exercise, generated architecture notes, or vault validators
were run. The orchestrator owns the full landing gate and commit.

These pins intentionally stop at hash outputs or write arguments; they do not prove SQL constraints, persistence,
transaction rollback, later routing, or complete prompt content. Part 2 should keep IDs literal at fixed inputs and
normalize minted IDs/times in its row golden; use real repositories there. In particular, the dr pin has an empty
hypothesis set, the cdo pin exercises one matched production, the ccv pin stops before activity/factor updates, and
prompt-suffix pins stop at the agent-run record. Part 2 still owes the five causal statuses, model-dependent branches,
FG1 waiting/asking, resolution/repair/cold pass/fail, holds/regrades, recurrence and prerequisite journeys, and the
function/line coverage of the upcoming moves. The public input-reader fakes in the prompt-version pin must follow
any public reader move; the AST source registry must follow builder moves. No old digest may be regenerated to
make a move pass.

Final cleanliness: `git diff --stat -- src` produced no output; `git diff --check` passed.
The `.pytest_tmp/run-*` glob matched no directories after the final run.
