# UX-33: section questions in parts

Implementation investigation on `fix/ux33-section-questions-in-parts`, from
`4566d93ae9`. Found in the verification walk on the live route: one authoring
request for six topics failed at 480 seconds; the learner's retry was still
running seven minutes later. No walk data or real provider was accessed.

## Step 0 (recorded before changing code)

`handle_practice_expansion` passes every payload learning-object id into
`generate_post_probe_practice_proposal`, with the completed-probe requirement
waived, `target_items_per_lo=3`, and `max_new_per_lo=3`. Six empty topics ask for
18 items in one `AuthoringProposal`. The planner can already select one topic
or any named subset; it also has a courtesy-item rule for explicitly named
topics that already meet their target, so rerunning the service is not a
no-op guarantee.

Each target carries its id, title, subjects, concept, current item and probe
counts, mastery, difficulty band, existing facet vocabulary, blueprint
components and surface families. When applicable it also carries its depth
waypoint, capability, task features, float proxy bands, commissioned cells,
contract capabilities and contrast-pair requests. The section handler adds
instructions to ground items in the supplied source bundles and use the
proposal-local source reference ids assigned to that item's topic.

`build_authoring_context` adds subject-scoped learning objects and existing
practice prompts (120-character excerpts), note excerpts (280 characters),
source refs, concepts and active goals. Selecting a topic in the practice plan
does not by itself remove other topics in the same subject from this shared
context. `authoring_prompt` renders that context and the existing instructions;
`request_authoring_proposal` asks for the `AuthoringProposal` structured schema.
There is no section-specific output cap in the handler. The available common output
policy is `ai.route_output_tokens.authoring`, otherwise the serving profile's
`max_tokens`, otherwise `ai.output_tokens` (16,384); the profile maximum caps
an override. A part should use that existing policy, not a new constant.
However this handler gets `default_synthesis_client`, which resolves
`canonical_ingest` with an eight-minute turn deadline, and passes no
`generation_limit`. Its structured request therefore carries no output budget
in the normal section path, and the plan transport adds no budget sentence.
The generic policy's 16,384 is not a measured or enforced reservation on this
existing plan call. Introducing a limit must also respect the requested
one-topic request-byte pin; simply adding `generation_limit` would append a
new sentence on that route.

The authoring request has no `ModelCheckpoint`: its agent-run record is
provenance, not a reusable answer. The one-shot deterministic-validation
repair request is also not checkpointed. Persona fire judgements do use the
existing checkpoint helper. A timeout before the authoring answer therefore
leaves no reusable authoring result. UX-13's automatic retry is for automatic
inventory/bootstrap/append jobs, not ordinary section practice expansion;
the learner's resume retries the same job. The section generation stamp is a
compare-and-set enqueue guard, not a model-response checkpoint.

One proposal contains all topics. Generation performs validation, a possible
repair, and the surface/rung/persona/contrast-pair gates before persisting it.
`auto_apply_rows` then calls `accept_items` for auto-applicable rows through
the existing apply machinery. Direct grounding, resolvable sources, required
metadata and no existing id collision are required; review-only and refused
items are not automatically practisable. The apply API can accept a part's
proposal immediately; it is not restricted to a whole ingest job.

The possible blocker is instead gate composition: `ContrastPairGate` refuses
*every* row when more than two rows claim one pair key. `PersonaGate` also
judges the pair jointly. A later topic's malformed duplicate member can
change the verdict on earlier rows. The next check tests that precise boundary
before introducing early apply, as required by the task's stop rule.

Today currently reads one `result.patch_id` only after the job completes;
active and failed jobs exit before counting applied items. Its writing fact
contains section labels, not per-part counts. Both the multiple-patch fact and
progress need changes for a streaming implementation. Candidate topics are
currently sorted by id, so section reading order also needs explicit handling.

## Ruling and result

**Fixed in the working tree of `fix/ux33-section-questions-in-parts`, not yet
committed or landed: written in parts and saved; applied together; applying a
part early stays open: it needs the contrast-pair gate to judge a part against
what is already applied.**

The continuation ruling supersedes the earlier early-apply stop. Write one
bounded authoring request per topic, keep every answer through the existing
checkpoint helper, collect the answers, then run the original whole-proposal
validation, repair, instrument gates and apply path once. The earlier worker's
`test_a_later_topic_can_revoke_an_earlier_parts_pair_gate_verdict` is retained:
a later member makes `ContrastPairGate` refuse the earlier pair too. Applying
that prefix would expose questions the complete proposal rejects.

Before: one authoring call for all targets (six empty topics request 18
questions); a timeout leaves no answer; retry repeats all work. After: six
calls, each requesting at most three questions for one topic, in section
reading order. Order is first cited source span, with id as the tie breaker;
other callers of the section map retain their existing id order. The job
honors the payload's topic order, including older queued jobs.

No schema, migration, config key, algorithm tag or prompt template changed.
No index update, commit, reference regeneration, `refactor-status.md` or
`CLAUDE.md` edit was made.

## Judgment calls to read first

1. **One proposal, one apply.** Only initial authoring is partitioned. The
   combined deterministic repair remains one call over the invalid rows, just
   as before; its answer is checkpointed too. That repair can still be large
   and can still time out. Splitting it would change the existing repair's
   inputs and merge semantics. All original answers survive that timeout.
2. **Retry scope is the section intent.** Topic ids in order, source refs,
   section reason and model settings key a durable request snapshot and the
   completed result. Requests are frozen before the first paid call, so an
   unrelated note arriving during retry does not cause paid parts to miss.
   Completed work returns its original patch on a later identical enqueue,
   avoiding the planner's courtesy item and the changed post-apply context.
   Changed source refs, topic order, reason or model settings are new work.
3. **Automatic retry is explicit.** The prior automatic retry rule covered
   inventory and synthesis only. Finished-section practice now joins its
   existing one-retry policy for curable failures. Interruption, cancellation,
   budget pauses and gate refusals do not become automatic retries. Two
   timeouts leave the job failed and keep the normal Try again action.
4. **A duplicate test required a small additional gate.** Contrary to the
   earlier assumption, today's gates let two distinct ids on different topics
   with the same prompt auto-apply. The corrected fail-first fixture proves
   both reached the vault. `_reject_duplicate_practice_prompts` now rejects
   every creation row sharing an exact stripped prompt, after the existing
   instrument gates, on both partitioned and whole post-probe generation.
   This is the ruling's explicitly permitted exception to unchanged gates.
   It uses the probe generator's stripped-text comparison, not a model call
   or semantic similarity heuristic. `ContrastPairGate` still owns repeated
   pair membership (`pair_oversubscribed`); existing-id collisions still use
   deterministic proposal validation. No claim is made about paraphrases.
5. **Progress is a fact, not proof of application.** Saved initial answers
   count as done. Six of six may still be awaiting repair, gates or apply.
   Failed jobs keep their saved count. The existing `status_line.progress`
   shape is `{done, total}`, also added as `questions.progress` so a book's
   inventory/synthesis progress can keep precedence on the outer line. Counts
   aggregate its finished sections' question jobs. The queued total comes
   from payload topic ids until actual part counts are reported.
   `apps/learnloop-tauri/src/app/todayCause.ts` reads outer progress for
   `on_the_way`; its `section_writing` branch does not yet render that amount.
   `ReadingQuestionsDto` does not yet declare the additive nested progress.
   No frontend change or rendered “2 of 6” claim is made here.

## Checkpoints and retry

`dispatch_authoring_request` uses `checkpointed` with the rendered authoring
prompt, strict `AuthoringProposal` schema and `model_settings`. Its
`ModelCheckpoint.answer` saves before merging refs, combining parts,
validation, reporting completion, gates or persistence. Repair uses this same
helper before merging its returned items. No checkpoint is written for a
call that raises. Existing non-section authoring callers remain uncheckpointed.

The section request snapshot and completed result use `ModelCheckpoint` too,
under their section-intent key. Each paid answer still has its own request
key, independent of the batch/job id. A retry preloads saved counts before
reporting progress; it does not temporarily claim zero saved parts.

Tests exercise these actual runner and apply boundaries with structured
house fakes: third call times out; first two are kept and nothing is applied;
Try again calls topics 3–6 only, even with a new note added in between. One
curable timeout also retries automatically from topic 3. Two timeouts stop at
2/6 and a learner resume finishes at 6/6. A failure after repair returned but
before apply repeats neither authoring nor repair. A later identical section
build returns the same completed result with zero calls.

The collected proposal is compared with whole-call generation returning the
same six answers. Every persisted row field is compared except generated row,
patch and change-batch ids and timestamps. A second test observes the apply
boundary: one invocation for the collected proposal, equal rows/routing, then
one for the whole-call control. Both real apply runs produce the same six
practice items. The retained contrast-pair test independently pins why an
individual part cannot be applied early.

## Request bytes and spend

The one-topic request was pinned from unchanged production code first. Its
synthetic fixture substitutes only the context's vault root with a fixed,
nonlocal test value before rendering, so the bytes actually sent to the fake
are deterministic across temporary directories. The pin covers prompt, strict
schema, purpose, timeout, output budget/ceiling, workspace/isolation,
reasoning effort and images:

`37a5f8e07262bc797fe344c59601ad0387b65a895e24cb10e92678d4a0208c4b`

It passes on both base and implementation; the base test fails later on the
second build's three total requests versus one. No existing identity moved.
Two **new** checkpoint pins (`section_questions.answer`, `.work`) and the
existing `AuthoringContext` type's shape were registered. Existing digests and
shapes were compared before generating the additive golden entries.

A part calls the existing instruction builder with a one-target plan and
that topic's subjects. Target-specific counts, bands, blueprints and conditional
instructions follow that plan. Shared context remains subject-scoped: other
same-subject topics and existing questions are still present; concepts, notes,
goals, supplied section source bundles and the result schema are repeated.
All supplied source bundles are retained with their original proposal-local
ids; they are not renumbered per topic. There is no prompt template edit.

Measured by `authoring_context_stats` on the test's six-topic synthetic vault
(one subject, seven contextual LOs including the basic fixture's original,
one existing practice item, one note, one goal, no supplied source bundles):

| Request | Prompt chars | Schema chars | Estimated input tokens |
|---|---:|---:|---:|
| Whole section before | 20,613 | 27,191 | 11,951 |
| Each of six parts | 16,723 | 27,191 | 10,979 |
| Six parts together | 100,338 | 163,146 | 65,874 |

The builder uses `ceil((prompt chars + strict schema chars) / 4)` per
request. Total estimated input rises by **53,923 tokens**, about **5.51×**.
The schema alone is repeated five extra times (135,955 extra characters).
These are estimates, not real-provider token usage or billing. A third-call
timeout asks seven requests in total across recovery, with the first two
successful answers paid only once; a completed identical rebuild asks zero.

**Output reservation actually sent: none before; none per part after.**
`StructuredRequest.output_budget_tokens` and its ceiling are `None` on this
section route. The common default authoring policy would reserve 16,384 per
call on a route that enforces it: six × 16,384 = 98,304 versus 16,384, an
81,920 increase in capacity, not generated output. This policy comparison is
not misreported as an enforced cap or spend on the current plan route.

One topic is bounded by three requested questions, not answer length. Its
schema has no maximum length on prompt/answer text: even three answer strings
of 21,846 characters each already exceed 65,536 characters (16,384 at the
builder's four-character approximation), before JSON, rubrics or reasoning.
Thus one topic can exceed that output policy. There is no further split,
new setting or new budget sentence; adding one would change the one-topic
request bytes.

**Learner estimate before and after:** there is no separate finished-section
practice estimate. Add's existing automatic book-build estimate covers
inventory and synthesis, not later section practice, and is unchanged.
The new part counts are progress, not a dollar/token/time estimate. No real
route or UI estimate was measured.

## Tests first

Final fail-first assertions were run on unchanged production sources. During
test construction, the first fixture lacked valid facets and a required
repair target; that was corrected before claiming duplicate or apply evidence.
The first pin capture also exposed the temporary vault root in the prompt;
the fixed-root fixture above was then captured and checked again on base.
Prepared implementation sources were held temporarily while the definitive
base tests ran, then restored without touching the index.

| Test | Failure on base |
|---|---|
| Six-topic timeout/resume and equal applied result | Job completed after one call instead of failing on the third |
| Automatic retry | One six-topic request rather than topics 1,2,3,3,4,5,6 |
| Two timeouts and Try again | Job completed instead of stopping with saved 2/6 |
| Later identical rebuild | Three authoring/repair requests rather than one total |
| One-topic byte pin plus reuse | Byte pin passes; rebuild makes total requests 3 rather than 1 |
| Repair saved before downstream failure | Authoring and repair both repeated (four calls rather than two) |
| Collected proposal at apply | Equal rows/routing already hold; one whole request rather than six topic requests |
| Source topic order | `lo_a, lo_m, lo_z` rather than `lo_z, lo_m, lo_a` |
| Exact cross-topic prompt duplicate | Both duplicate questions auto-applied |
| Progress (six states) | `KeyError: progress` in every state |

The byte equality and whole-proposal equality assertions are preservation
guards and must pass on base. Their containing regressions fail on missing
partition/reuse behavior, not on deliberately wrong golden bytes.

## Verification commands and results

`t.sh` and `py.sh` below mean the supplied isolated-environment wrappers.
All pytest invocations name explicit files; no whole suite or more than two
workers. Temporary pytest roots and log destinations are omitted below.
The prior worker's verification is historical; this continuation's runs follow.

### Fail-first and development runs

- `t.sh tests/test_section_question_parts.py -q -n 2`: initial fixture,
  **5 failed in 3.92s**; next attempt **1 collection error in 0.90s** (corrected
  `add_note` import); corrected valid-question fixture **5 failed in 4.48s**.
- `t.sh tests/test_first_questions_today.py -q -n 2 -k section_writing_progress`:
  **6 failed in 5.91s**, all missing progress.
- `t.sh tests/test_section_question_parts.py -q -n 2 -k one_topic`:
  **1 failed in 2.13s**, temporary-root-dependent pin; fixed as described above.
- `t.sh tests/test_section_question_parts.py -q -n 2` on base with all nine
  scenarios: **9 failed in 5.65s**. Then fixed the comparison's generated
  patch-id exclusion and recorded the deterministic request pin.
- `t.sh tests/test_section_question_parts.py -q -n 2 -k 'one_topic or collected'`
  on base: **2 failed in 2.60s**, only the intended reuse/partition assertions;
  request bytes and row equality pass.
- `t.sh tests/test_section_question_parts.py tests/test_first_questions_today.py
  tests/test_identity_pins.py tests/test_retired_config_identities.py -q -n 2`:
  **1 failed, 388 passed in 40.01s**. All behavior and existing identity values
  passed; coverage required registering the new checkpoint path.
- `py.sh python` fixed-fixture before/after measurement: exit 0; builder
  estimates **11,951 → 6 × 10,979**; after budgets `[None] × 6`.
- `py.sh python` comparison of all prior identity and shape entries: exit 0,
  **All existing identity and shape pins unchanged; adding only section_questions pins.**
- `py.sh python tests/test_identity_pins.py --write`: exit 0; only two new
  identities and one new type-shape block. No previous pin regenerated to a
  different value.

### Required file group and adjacent apply/source-reference tests

```sh
t.sh tests/test_authoring_context.py tests/test_authoring_contract.py tests/test_exercise_authoring.py tests/test_first_questions_arrive.py tests/test_first_questions_today.py tests/test_followups_batch6_prefetch_next_section.py tests/test_ingest_runner.py tests/test_ingestion_checkpoints.py tests/test_item_authoring.py tests/test_model_work_checkpoints.py tests/test_reader_authoring.py tests/test_reader_ca5a_find_section.py tests/test_rospeed2_section_map.py tests/test_section_coverage.py tests/test_section_coverage_migration.py tests/test_section_coverage_review.py tests/test_section_coverage_rpcs.py tests/test_section_done_before_build.py tests/test_section_question_parts.py tests/test_sidecar_item_authoring.py tests/test_ux_phase1_add_source.py tests/test_contrast_pairs.py tests/test_proposal_persistence.py tests/test_reader_progression.py -q -n 2 -m 'not arc_close'
```

**1 failed, 369 passed in 60.30s.** The only failure is
`tests/test_first_questions_arrive.py::test_the_plan_route_request_is_byte_identical_under_a_ceiling`:
its fake HTTP server cannot open a socket (`PermissionError: [Errno 1]
Operation not permitted`). **Not counted as verified.** Every added/edited
behavior test, including the earlier worker's pair boundary, passes.

### Remaining checks

```sh
t.sh tests/test_identity_pins.py tests/test_retired_config_identities.py tests/test_structure_ratchets.py tests/test_effective_defaults_golden.py tests/test_kill_switches.py tests/test_sqlite_file_copies.py -q -n 2 -m 'not arc_close'
```

**380 passed in 17.50s.** Existing identities and retired identities hold;
new checkpoint identities/shape are additive. Structure and defaults hold.

```sh
t.sh tests/test_test_layout.py -q -n 1
```

**3 passed in 19.31s.** Run alone.

```sh
t.sh tests/test_architecture.py -q -n 1
```

**18 passed in 29.92s.** Run alone.

```sh
t.sh tests/test_section_question_parts.py -q -n 2
```

**9 passed in 8.29s.** Final rerun after making the recording fake read the
schema from the actual request model (same bytes/pin) and import cleanup.

```sh
py.sh ruff check
py.sh lint-imports --no-cache
git diff --check
```

Ruff: **All checks passed!** (initial and both final checks). Import lint:
**Contracts: 43 kept, 0 broken.** Diff whitespace check: exit 0, no output.
No requirement is counted as passing from the socket failure.

## Scope and limits

Total diff from HEAD, including the earlier worker’s retained work and the three untracked files: **+892 / -17, net +875, 16 files**. Production: **+157 / -16, net +141, 7 files**.

No real model, network access, private configuration, private vault, UI walk,
full suite or landing gate. The socket test above is unverified, as are live
latency and billing, rendering section progress in Today, and the size of real
single-topic/combined-repair output. The original 480-second provider deadline
is unchanged. Early apply is deliberately still open for the gate reason
above. No stop criterion was reached: the existing helper checkpointed both
call types, proposal equality held, no existing identity moved, and production
changes stayed below about 400 lines.
