# UX-40: a finished section's questions apply, and held for review is not failed

Branch `fix/ux40-section-questions-apply`, from main `746335c4a0`.

## The measurement

A rerun of a walk's vault on the real model route (numbers and field values only; this step read no vault and made no model call). After a book's build, a finished section's questions were written topic by topic (UX-37): each topic one authoring call of about 130 s and 6,400 output tokens giving 3 practice items, then six persona-gate judge calls. Every item, 9 of 9 over three topics, came back with `review_route = "review_required"`. Each row was valid (no validation error), its audit status was `passed`, the persona gate's decision was `pass`, and it cited one source reference of `ref_type` `canonical_source` (the Reader's citation of the section's passages, with span ids and a quote). Nothing applied: the three part proposals stayed `pending`; the job recorded for each topic the error "Questions need review before applying" and ended failed; its message stayed "Writing questions: 0 of 7 topics finished"; the learner had no practice. The house doubles answer `auto_apply`, so no test saw it.

## Step 0 (written before any code change)

The rule the brief calls `effective_review_route` is `evaluate_review_policy` in `src/learnloop/content/proposals/proposals.py` (no function of the brief's name exists). The row flag is `proposal_item_row`'s `"_auto_apply": validation_status == "valid" and review_policy == "auto_apply"`; gates can only turn it off.

### a. Who sends this prompt, and what happens to a row the model marks `review_required`

The line is in `_practice_expansion_instructions` (`content/authoring/practice_generation.py`). It is built in two places: `generate_post_probe_practice_proposal` (per topic for a section, once for the whole plan otherwise) and `generate_goal_practice_proposal`. The prompt carrying it is `authoring_prompt` (`content/proposals/ai_contracts.py`): the instructions ride in `context.instructions`. `_cross_source_instructions` (the cross-source route) does not carry the line.

Where a held row goes, for every caller: it is persisted as a `pending` row of a `proposed_patches` batch (`proposed_patch_items`, `decision = 'pending'`); it is never written to the vault, so it is not practisable. It is shown in the desktop's Library (the proposals list in the tree, opened with its payload in the editor) and the Proposals screen (`ProposalsScreen.tsx`, `PayloadPreview`): both show the whole payload, `prompt`, `expected_answer` and `grading_rubric` included, so **a learner who looks at it sees the expected answer before having tried the question**. To get it, the learner must accept it there (or edit, or reject). The phone and Today have no review surface (Today says "“…” needs a look in your Library."). The Proposals screen's route pill reads `auto_apply` for every valid practice-item creation (the sidecar's `_review_route` ignores the model's flag, grounding, the audit and collisions), so a held row shows a green `auto_apply` pill while pending, and "accept all auto_apply" takes it (ledger UX-40b). The model's per-item `rationale` is not stored on the row (`proposed_patch_items` has no such column; `_item_dto` shows the batch summary as every row's rationale), so a reviewer never sees why the model held it.

| Caller | How it reaches the line | Supplied `context.source_refs` | A `review_required` row |
|---|---|---|---|
| A finished section (desktop "Done with this section" or its quick check; the phone's; a section waiting for its build, `jobs.start_waiting_sections`; the sidecar's drain of owed sections, `section_questions.py`) | `practice_expansion` job, reason `reader_section_completed:<section>` → `handle_practice_expansion` → `generate_post_probe_practice_proposal(..., checkpoint_scope=…)` → one part per topic → `_apply_authoring_parts` | the section's passages, `canonical_source` (or a note), merged into the proposal | pending; **before this fix the topic got the error "Questions need review before applying", the job ended failed (`ValueError`, not retried), Today said "Couldn't write the questions…" with a Try again that asks nothing** |
| Starter practice for empty topics (`generate_starter_practice`, goals.py; reason `learner_requested_starter_practice`) | `practice_expansion` job, whole plan in one call | none (payload `source_refs` empty) | pending in the batch; job completes |
| Maintain's commissioning gaps (`generate_commissioning_practice`, measurement.py) | `practice_expansion` job, whole plan | none | pending; job completes. The screen promises review: "authored items land in Proposals for review as the batch completes" (MaintenanceScreen.tsx), and the handler's docstring says "never applied silently" |
| An adaptive-difficulty commission (`daily_plan._commission_enqueue` → `enqueue_practice_expansion(ad_commission_id=…)`) | `_handle_ad_commission` → `generate_post_probe_practice_proposal`, one item | none | pending; the commission stays open until an item lands |
| "More questions" on a missed attempt's primed retry (`start_primed_retry`, feedback.py) | `generate_post_probe_practice_proposal(max_new_per_lo=1)` then `accept_items(root, patch_id)` with no ids | none | **accepted anyway**: `accept_items` with no ids takes every pending valid row, so the route does not matter |
| CLI `learnloop generate-practice` | `generate_post_probe_practice_proposal` | none | pending; printed for `proposals` review |
| Goal population (`goal_population` job from the goal wizard; CLI `populate-goal`) | `generate_goal_practice_proposal` | none | the job and the CLI without `--review` call `accept_items(root, patch_id)` with no ids: **accepted anyway**; with `--review`, pending |

No "more questions" action other than these reaches the line (`generate_starter_practice` is the only learner-facing "write questions for this topic" press; the Reader's per-section questions are this practice route).

**Is applying a grounded, audited, gate-passed question without review wrong anywhere?** For the finished section, no: the learner asked for practice on what they just read, the items cite the passages they read, every gate ran, and the review surface shows the answer first. For primed retry and goal population the route is already moot (they accept every valid row). **Maintain's commissioning is the one caller whose screen promises review.** The new wording therefore applies only where references are supplied in `context.source_refs`, which only the finished-section route supplies; on every other caller `context.source_refs` is empty and the line leaves its items `review_required` (the code also routes an item without a direct, resolvable, supplied-or-declared reference to review). The old line's "a direct note … in the supplied context" could be read to include the context's notes; the measured model did not, so in practice nothing changes there. (Whether Maintain's items should apply is not this task's; its docstring and screen already disagree with the code for any row a model marks `auto_apply` on its own.)

### b. Other authoring prompts that tell the model when to choose a review route

Searched every prompt-building module (`grep review_route|auto_apply|review_required` in `src/`, then each hit that is prompt text). Two lines exist:

1. `content/authoring/practice_generation.py`, `_practice_expansion_instructions` (this task's): "Use review_route='review_required' unless a direct note or canonical source reference in the supplied context supports auto_apply."
2. `content/authoring/practice_generation.py`, `_diagnostic_practice_instructions`: "Use review_route='review_required'; generated diagnostic probes must be reviewed before writing vault content."

Line 2 does not have the wording problem: it is an unconditional rule that matches the code (`evaluate_review_policy` with a diagnostic context never auto-applies; `_diagnostic_proposal_item_row` forces `_auto_apply = False`). Not changed. No other prompt names the route: `authoring_prompt`'s task text, `EXERCISE_AUTHORING_PROMPT`, the probe, teach-back, tutor-promotion and synthesis prompts say nothing about it (their routes are set in code: `graph_edit_proposals.py` writes `"review_route": "review_required"` itself; tutor promotions, rung variants and synthesis decide in code). So only line 1 had the problem.

### c. What `evaluate_review_policy` requires for `auto_apply`, and what the measured rows met

In order (ordinary authoring, `context=None`):

1. The model's route is not `reject` — met.
2. Every cited `source_ref_id` resolves (`_unresolved_source_ref_ids`) — met (valid rows; an unresolved ref is also a validation error).
3. `operation == "create"` and `item_type` in learning_object / practice_item / concept_edge — met (practice_item creates).
4. At least one `source_ref_id` — met (one each).
5. Direct grounding: every cited ref that is in the proposal's refs is `note` or `canonical_source` (`_has_direct_grounding`) — met (`canonical_source`).
6. No id collision with the vault (`_has_id_collision`) — met (valid; a collision is also a validation error).
7. The generated-practice audit: present, not `failed`, and a `not_applicable_with_trace` audit carries its trace (`_generated_practice_audit_error`) — met (`passed`).
8. **Last: the model's own `review_route == "auto_apply"`** — **not met**: the only condition the rows failed.

Then the row flag needs `validation_status == "valid"` (met), and the gates must leave it on (persona decision `pass`; nothing refused). Every condition the code checks held except the model's flag.

## The prompt line

(after code; see below)
