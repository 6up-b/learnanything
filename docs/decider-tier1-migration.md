# Decider Tier 1 (owner decision 2026-10-13)

`mvp-0.20` is the immediate successor of `mvp-0.19`. It changes new
judgments, not the interpretation of recorded learner history. The upgrade
uses `sources_upgrade.upgrade_to_mvp020`, chains through `upgrade_to_mvp019`,
passes advisory notes through, prepares the existing P0 projection before the
atomic version write, and leaves raw ledgers intact. No new tables or replay
owners are introduced. Older defaults fingerprints change only because the
new config fields serialize; the serving changes are gated at mvp-0.20.
The facet span-support content check is independently enabled at every version.

All switches default on. A false switch restores that judgment's prior path:

```toml
[decider_routes]
learner_gap_judge = true
learner_gap_kind = true
misconception_match = true
diagnosis_link_judgment = true
field_question_classification = true
contamination_leak_judgment = true
contamination_reveal_judgment = true
facet_span_support = true
```

`ai.routing.tier1_decider` defaults to `openrouter_decider`; it is a
Decider-only route, with no generic chat fallback. Text gaps retain their
existing `learner_gap_decider` profile, and their Decider requests are admitted
on the text's budget under that route. Each feature owns its LLM fallback.
`router_decider` is untouched. The Decider chooses the probability argmax,
not the response's separate choice field, and applies no confidence cutoff.
Failed, unavailable and spend-refused checks are ledgered without inventing a
verdict. Only those outcomes trigger the LLM fallback. No shadow sampling is
introduced. D6 permits learner text on the Decider route.

## Caller inventory

| Judgment | Callers and behavior |
| --- | --- |
| Gap kind | `diagnosis/text_gaps/pipeline._decide` → `tier1.decide_kind`; tutor questions, stuck answers and diagnosis readings enter through `sources`, `jobs` and `process_learner_text`. Existing context readings are logged; the Decider owns the kind. Generating the name/statement of a gap remains with the context model. A kind the Decider already answered for the same input is reused (never paid for twice). |
| Gap identity | `pipeline._prerequisite` and `_belief` → `_judge_all` → `text_gaps/tier1.judge_all`. Prerequisite and belief pairs use same/different/unsure. Decider failures fall back pair by pair to `LLMPairExecutor`. |
| Prerequisite needed | `pipeline._maybe_edge` → `judges.ask_needed`; yes/no/unsure, with `learner_gap_judge`'s switch. |
| Misconception match | `diagnosis/misconceptions._durable_match` → `_match_misconception`; called from the legacy normalizer and the holding-pen normalizer. Chooses one registry ID or new. Split diagnosis already supplies `registry_match`; `diagnosis/split/jobs` retains that diagnosis-owned decision. |
| Diagnosis link | `offline_review/runner._judge_links` → `decider_links.judge_links`; typed same/different/not_sure per blinded earlier answer. `offline_review/links.import_pattern_links` retains the actual producer when importing real-attempt links. Diagnosis-quality and planted-cause judges remain LLMs. |
| Field question | `cli/field_classification.classify_questions` → `field/classification.classify_missing_questions` → `field/decider.Classifier`. Classifies missing question type, and typed yes/no catalog membership for missing LO/facet mappings in one request (the API limit is 128 questions; larger catalogs use the LLM fallback). Logged metadata is retained. Fallback uses the original structured classifier. |
| Leak/reveal | `cli/contamination.report` → `ops/contamination/report.contamination_report` → `judge.run_judgments`. Exam leakage, tutor answer leakage and reader reserve reveal use the same two-text verdict question. Existing repeats stay repeats of the chosen judge; they do not add shadow pairing. |
| Facet support | `content/facet_identity/authority.check_meaning_write`, through the resolver of a proposal's apply (`ProposalAuthority.for_proposal`), which every model-proposed facet write passes, synthesis output included. Exam-only refusal runs first. One question contains only validated explanatory spans (each once) and new wording. Only supports applies; other outcomes hold the existing confirmation card. `confirm_reword`, `keep_current_wording` and the undo of a reword the check judged (held and confirmed, or let apply) append labels linked to that check. Library owner edits, confirms and undos bypass the check. |

`diagnosis/recurrence/judging`, its live `diagnosis/split` callers and
`cli/embeddings.adjudicate --task same_cause` use the separate
`same_cause_judge` route. They are not aliases of `diagnosis_link_judgment`
and retain their LLM judgment. Recurrence accepts Decider authority only for attempt-level imported links explicitly marked diagnosis_link_judgment at mvp-0.20 or later; unmarked historical Decider second opinions remain non-authoritative. Existing same_cause ledger pairs are included in the
agreement report. Grading, diagnosis, re-derivation, generation, tutor, T6 span
verification and proof-like item reading are unchanged.

## Evidence and spend

`decider_judgments.decide` uses `ReviewSpend`, the existing shared spend envelopes and
model-call receipt sink. Decider estimates contain input tokens only; no LLM
output-budget policy is imposed. Fallback calls retain their existing shared
output policy. Report commands share their call/candidate/pair caps across
Decider and fallback requests; subscription LLM work retains its subscription
billing treatment.

`learnloop decider agreement --vault PATH --json` reads the ledger without
model calls or migrations. It groups by task, entity identities and input hash,
compares the latest actual Decider and LLM/diagnoser verdict for each input,
and reports counts, agreement and a Decider-by-LLM confusion matrix. Failure
rows count as fallbacks, not agreements. Labels bind by exact input or an
explicit label/supersession reference. Calibration reports multiclass Brier
score and confidence-bin accuracy only where the full distribution and an
option-valued label exist; missing evidence is null, not zero. Facet confirm
labels supports; keep and undo label does not support. These are owner action
labels, not independently adjudicated textual entailment.

The tests (`tests/test_tier1_decider.py`, `tests/test_facet_span_support.py`,
`tests/test_decider_agreement.py`, `tests/test_mvp020_upgrade.py`) use
in-process fakes; the upgrade test also uses a backup-API copy of
`fixtures/migration_head_197`. They check raw-history preservation, foreign
keys, doctor, chained notes, defaults, and same-version rebuild equivalence.
As in the predecessor fixture test, two initial rebuilds settle the parameter
manifest before comparing the derived snapshots.
