# UX-37: first questions first

Fixed in the working tree of `fix/ux37-first-questions-first`, not yet
committed or landed. Base: `5a7728283a`.

## Measured problem and ruling

The verification walk on the live route finished an eight-topic section.
Each sequential authoring call took 1.5–2.4 minutes, with about 24,000 input
and 4,300–7,000 output tokens. After four saved topics, a fifth answer was
invalid JSON after one repair. That stopped the job. Its automatic retry
reused the saved answers, but twenty minutes after section completion only
4–6 topics were saved and **no question was offered**: validation, gates and
apply waited for the entire section. These are the supplied measurements;
this implementation did not access the walk, private data or a provider.

The orchestrator superseded UX-33's combined-verdict rule: judge each new
part against **already applied rows of this section plus that part**. Never
retract an applied row. Refuse the new conflicting row, even when a later
whole-proposal judgment would also have refused earlier rows.

## Judgment calls to read first

1. **One small proposal per topic, through the existing apply path.** Initial
   answers and validation-repair answers retain their existing checkpoints.
   Each part is validated, repaired if necessary, gated, persisted and passed
   to `auto_apply_rows` → `accept_items` before the next authoring request.
   Calls remain sequential and in the existing payload/section reading order.
   All request contexts are frozen before the first call, as before.
2. **An applied set, not every saved answer, is gate context.** The joint
   gates receive copies of accepted, applied rows, using their effective
   edited payload when present. Only new rows' verdicts are persisted. A
   refused or review-only row cannot witness its partner's admission: after
   all gates and duplicate checks, the persona and pair gates repeatedly check the auto-apply subset
   until no more new rows are refused. A surviving half of an unapplied pair is refused as unresolved.
3. **Completion means all returned rows applied.** A saved proposal containing
   refused or review-only rows ends failed, naming the topic, and preserves
   row reasons and the review queue. It does not trigger a fresh model retry.
   Try again reuses that proposal; it does not pay to replace an answer that
   already exists. Accepting corrected rows through the existing review path
   can settle it on resume. This differs from a model failure with no saved
   answer, for which Try again requests only the missing topic.
4. **The worker's one automatic retry remains the only outer retry.** Every
   topic gets its first attempt before the collection raises. A model-failed
   topic is requested at most twice per job attempt: once in the first pass,
   once in the runner's automatic retry. On the measured invalid-JSON route,
   each structured attempt includes the provider's existing one wire repair:
   at most four physical calls for that failing topic, not an unbounded loop.
   A timeout with no wire repair is two calls. A user Try again begins another
   bounded attempt; the regression's repaired topic succeeds on its third
   structured request overall. Successful answers and successful repair
   answers are never requested again. Interruptions/cancellation and spend
   control still stop the job; they are not swallowed as topic failures.
5. **Visibility needs a backend reload as well as apply.** Each applied part
   bumps the queue revision. The sidecar's existing reload tracking now also
   sees applied rows of running/failed section jobs, and captures the observed
   row ids before reloading so a later arrival is not marked seen accidentally.
   Both the queue-revision poll and Library's existing reload path use it.
   No frontend code, new polling, schema, migration, config key, algorithm tag,
   prompt template or request-byte pin changed.

## Gates and their scope

Tracing `generate_post_probe_practice_proposal.judge` through
`build_instrument_gates` gives this chain: surface → rung → persona → pair →
information-removing remediation; then exact duplicates. Section generation
has no `leading` gate. The added final joint-gate loop protects the actual apply
subset; it terminates because it only removes candidates. Validation and review routing run before this chain.

| Check | Scope and constraint | Incremental treatment |
|---|---|---|
| Structured schema and deterministic proposal validation | Row: resolvable source refs, existing entity-id collision, required create fields, supported attempt types, rubrics, facets/weights and generated audit; entity references are resolved against the vault/proposal | Same validators and one validation repair, now on one topic's answer; the vault is loaded before validating that part so earlier applied ids are visible |
| Review policy | Row: direct grounded creation, valid source refs, audit and explicit auto-apply route; other operations/unsupported grounding remain for review | Unchanged; no row is promoted to bypass review |
| `SelectedResponseGate` | Row: no banned declared modes, option-list/letter-choice/true-false surfaces | Same check over new rows |
| `_RungGate` | Row against its topic: contract capability membership, waypoint/task-feature bounds, whole-task coordination and difficulty-band tolerance | Same plan-specific gate over new rows; no admission rule weakened |
| `PersonaGate`, ordinary instruments | Row: planted persona separation; instrument-specific hard/advisory/untested policy, keyed detectors, error-hunt checks and realism license | Same check and policy over new rows; existing semantic-fire checkpoints remain |
| `PersonaGate`, contrast pairs | Whole set, grouped by explicit contrast-pair tag or derived pair key: the belief-holder must fail exactly one member; insufficient material/unjudged pairs retain their block/review behavior | Applied copies plus new rows go through the same joint judge. Only new verdicts can change stored rows; rechecked on the apply subset until stable |
| `ContrastPairGate` | Whole set, grouped by derived pair key: no oversubscribed pair, resolvable counterpart, matching differing component, both members in the target band, bounded within-pair difficulty gap, structurally different expected answers | Applied copies plus new rows, with unchanged reasons/audit. Rechecked over the auto-apply subset until stable after other refusals |
| Instrument remediation | Row: remove only recognized option surfaces or an unkeyed speculative misconception, then rejudge; corrected content always needs review | Same remediation on new rows only; cannot edit applied context |
| Exact stripped-prompt duplicate check | Whole proposal/section set: no two creation rows with the same nonempty stripped prompt | Applied prompts are reserved. Duplicate new rows receive `duplicate_prompt`; within a new part all duplicate members still receive it |
| `_mode_mix_compliance` | Per topic: requested teach-back count and other requested mode counts, reported after persistence | Section jobs do not request a mode mix. When the API is used with one, reporting aggregates all part proposals; this was and remains a report, not an apply gate |
| Existing acceptance/dependency checks | Row/dependency closure: invalid rows cannot be accepted, required dependencies must be accepted, apply intents/locks/target conflicts remain authoritative | Existing `accept_items` path, unchanged; no direct vault-writing shortcut |

The diagnostic-generation target/simulation gates and synthesis coverage
gates are not on this finished-section route. They were not removed or
weakened. Pair adjacency/randomization is a serving rule, not an authoring
admission gate, and is unchanged.

**Verdicts that can differ from one whole proposal:** the pair cardinality
check previously refused all three members of an oversubscribed pair; now
an admitted pair stays and the third is refused. The joint persona test can
likewise refuse a later member while the earlier separating pair remains.
Exact duplicates previously refused both topics; now the applied prompt
wins and the later duplicate is refused. A pair split across topics may
also lose the whole-proposal benefit of seeing its future counterpart: a
currently unresolved first member is refused, and an unapplied/refused row
cannot make a later member admissible. The final subset loop can refuse a
partner whose other member was held by a row check or the duplicate check,
or a persona group whose only separating member was refused elsewhere.
These differences are deliberate; they leave the applied set satisfying the
same constraints without retracting earlier questions. Per-row and per-topic
rules do not change.

## Apply once, paid once

The existing section-intent key and frozen `:requests` checkpoint are
unchanged. Each successfully returned authoring/repair answer uses the
existing authoring request checkpoint. Before persisting/applying a part,
`:part:<ordinal>` under that same section scope stores its prepared proposal,
row ids and auto-apply selection using the existing `ModelCheckpoint` store.
No new database shape is required.

Recovery uses this **same proposal id and same row ids**. It persists the
batch only if absent, and selects only still-pending rows for auto-apply.
Already-accepted rows carry their existing `applied_change_batch_id`; a fully
applied receipt is skipped before both authoring and apply. The existing
write-ahead apply protocol remains responsible for interruptions *inside*
an apply. The regression crashes immediately after `auto_apply_rows` returns
and before progress/completion is recorded: recovery does not invoke apply
for that first proposal, produces exactly eight proposals, and asks each
topic only once.

The completed section's existing saved result now also names `patch_ids`
(the legacy `patch_id` remains). A later identical rebuild returns that
result before generation or application; the test installs an apply trap
and proves zero calls, zero applications and no new proposals. Old completed
single-patch results remain readable. The completion key is still scoped to
topic order, source refs, reason and model settings; changing that intent is
new work, as before.

## Failures, facts and Today

A model failure is attached to its topic in the existing job payload's
`question_parts` list. Remaining topics are tried. Successful parts' questions
stay applied during the automatic retry and during a later failed-section
state. Model failures use the existing curable error family after the pass;
refused/review-only saved proposals use a noncurable validation failure.

`questions.count`, `item_ids` and `sections` now aggregate the accepted rows
of all named part proposals during running, failed and completed states.
Pending rows still contribute to `to_look_at`. `questions.writing` retains
its existing list of section labels; `questions.progress` and the outer
status-line `progress` give fully applied parts done/total. A failed topic
uses the existing `{label, resume_id}` shape: its label includes the section
and topic titles (ids only if the title is unavailable). At topic 6 in the
failure case, the fact can therefore carry applied questions, writing and a
failed topic simultaneously. At the final failure it says 7/8; after a
successful Try again it says 8/8.

| Facts / available queue | Existing Today state |
|---|---|
| No applied questions, section writing | `section_writing`; existing Continue reading |
| Applied questions in today's queue, still writing | `questions_ready`; Begin wins over the writing cause |
| Applied questions in queue, one topic failed, still writing | `questions_ready` wins; facts preserve both other conditions |
| Applied questions in queue, writing stopped with a failed topic | `questions_ready` wins; failure is still present in the facts |
| Failed topic and no questions currently offered | `section_failed`; existing Try again resumes the same batch |
| All parts applied and questions offered | `questions_ready` |
| Applied questions, none due, no other cause | `none_up` (phone without a known list can use `questions_ready`) |
| Only rows waiting for review | Facts include `to_look_at`; with a failed part, current precedence selects `section_failed` before `needs_look` |
| No section finished / waiting for book's build | Existing `finish_section` / `section_waiting`, unchanged |

**Frontend follow-up:** there is no combined state for “questions offered AND
more being written AND a topic failed.” Name the missing state
`questions_ready_with_section_work` for that step: keep Begin visible while
showing progress and the failed topic's retry. Likewise the current
`section_writing` renderer does not render the nested part progress. No UI
rendering or combined-state implementation is claimed here.

## Tests first

Only synthetic vaults and the house `StructuredClientFake` were used. Final
regressions were rerun with all changed production sources temporarily
restored to HEAD, then restored in `finally`, without touching the index.
That base run was **15 failed, 49 passed**; a subsequent joint-subset
regression also failed alone on unchanged production (below). Preservation guards (the request
pin, successful repair reuse, topic order and the completed fact) pass on
base rather than being deliberately broken.

| Regression | Failure on unchanged production |
|---|---|
| First of eight topics serves a queue question during topic 2's call | First topic absent from the actual scheduler queue |
| Fifth topic invalid after wire repair; 6–8 apply; automatic retry then Try again only asks 5 | Calls stop at topic 5 instead of continuing; no applied prefix |
| One timeout / two timeouts | Calls restart before later topics are tried; missing partial applied progress |
| Crash after first apply before recording progress | All eight questions applied together rather than only the first |
| Completed section rebuilt, no calls or applications | First run has one proposal rather than eight; old no-repeat behavior itself already held |
| Independent rows equal the previous whole-call result | No `patch_ids` |
| Duplicate topic prompts, later row refused | Job completes, with both rows refused and no applied question |
| Pair and persona incremental gates, originals unchanged, later reason persisted | No `applied_rows` parameter |
| Exact duplicate incremental gate | No `applied_rows` parameter |
| Applied counts during writing, mixed writing/failure, terminal failure | Empty `item_ids` while jobs are active/failed |
| Queue-revision poll reloads each part before completion | No `reloaded` indication while job runs |
| Another check removes the only separating member of a shared persona group | Two remaining rows still auto-apply despite the final group failing persona separation |

The invalid-output fake raises the transport's `AIInvalidOutput` after its
wire repair, rather than trying to implement a second JSON parser in the
fake. The regression also adds an unrelated note before Try again and checks
that all three topic-5 requests have identical bytes. Joint-gate tests first
prove the earlier pair passes, then assert both applied rows are unchanged
and the later row alone carries the ordinary refusal reason.

## Verification commands and results

`t.sh` and `py.sh` below are the supplied isolated wrappers. All pytest
commands name explicit files, use at most two workers, and never run the
whole suite. Temporary logs and wrapper locations are intentionally omitted.

The short development command `S` below expands to:

```sh
t.sh tests/test_section_question_parts.py tests/test_contrast_pairs.py tests/test_first_questions_today.py -q -n 2
```

| Command | Result |
|---|---|
| `S`, initial unchanged production | **13 failed, 50 passed in 23.54s**; expected defects |
| `S` with `tests/test_identity_pins.py tests/test_retired_config_identities.py` added before the flags | **1 failed, 427 passed in 49.28s**; stale provenance-only allowlist entry, not a changed identity |
| `t.sh tests/test_section_question_parts.py -q -n 2 -k queue_revision_reload`, before reload fix | **1 failed in 3.70s**; no mid-job reload |
| `S`, after reload fix | **64 passed in 31.95s** |
| `t.sh tests/test_section_question_parts.py -q -n 2 -k duplicate`, before enforcing failed state for unapplied rows | **1 failed in 2.36s**; incorrectly completed |
| `S`, after failed-state fix | **64 passed in 32.23s** |
| `S`, definitive fail-first run with production restored to HEAD | **15 failed, 49 passed in 24.03s** |

The stale `PROVENANCE_ONLY` entry for `generate_authoring_proposal` was removed
from `identity_pins_helpers.py` because extracting preparation changed the
scanner's local dataflow. No identity-site registration, pinned value, type
shape or golden was changed or regenerated.

All 32 matching test filenames, plus the contrast-pair file (33 total, one
chunk under the 40-file cap):

```sh
t.sh tests/test_authoring_context.py tests/test_authoring_contract.py tests/test_exercise_authoring.py tests/test_family_proposals.py tests/test_first_questions_arrive.py tests/test_first_questions_today.py tests/test_followups_batch6_prefetch_next_section.py tests/test_graph_edit_proposals.py tests/test_ingest_runner.py tests/test_ingestion_checkpoints.py tests/test_item_authoring.py tests/test_learner_pick_proposal.py tests/test_model_work_checkpoints.py tests/test_practice_proposal_caller_columns.py tests/test_probe_proposal_reads.py tests/test_proposal_dependencies.py tests/test_proposal_impressions.py tests/test_proposal_persistence.py tests/test_proposal_review_policy.py tests/test_reader_authoring.py tests/test_reader_ca5a_find_section.py tests/test_rerun_proposals.py tests/test_rospeed2_section_map.py tests/test_section_coverage.py tests/test_section_coverage_migration.py tests/test_section_coverage_review.py tests/test_section_coverage_rpcs.py tests/test_section_done_before_build.py tests/test_section_question_parts.py tests/test_sidecar_item_authoring.py tests/test_ux_phase1_add_source.py tests/test_ux_phase2_error_type_proposals.py tests/test_contrast_pairs.py -q -n 2 -m 'not arc_close'
```

**1 failed, 494 passed in 68.59s.** The failure is exclusively the forbidden
socket in `test_first_questions_arrive.py::test_the_plan_route_request_is_byte_identical_under_a_ceiling`.
It is **not counted as verified**.

Required safeguards plus every added/edited behavioral test:

```sh
t.sh tests/test_identity_pins.py tests/test_retired_config_identities.py tests/test_structure_ratchets.py tests/test_effective_defaults_golden.py tests/test_kill_switches.py tests/test_sqlite_file_copies.py tests/test_mobile_allowlist.py tests/test_section_question_parts.py tests/test_contrast_pairs.py tests/test_first_questions_today.py -q -n 2 -m 'not arc_close'
```

**776 passed in 49.35s.** Existing identity digests and the one-topic request
byte pin hold. No stop condition was reached.

Adjacent joint-gate, mode-mix, apply-protocol and sidecar reload checks:

```sh
t.sh tests/test_persona_gate.py tests/test_discrimination_profiles.py tests/test_error_hunt_items.py tests/test_teach_back_generation.py tests/test_apply_write_ahead.py tests/test_apply_recovery.py tests/test_host_queue_revision.py tests/test_ingest_instrument_gates.py -q -n 2 -m 'not arc_close'
```

**3 failed, 151 passed, 19 warnings in 26.20s.** All three failures are
`PermissionError: Operation not permitted` while opening fake HTTP sockets:

- `tests/test_teach_back_generation.py::test_generate_practice_mode_mix_adds_hard_constraint_and_teach_back_guidance`
- `tests/test_teach_back_generation.py::test_generate_practice_mode_mix_teach_back_count_violation_is_hard`
- `tests/test_teach_back_generation.py::test_generate_practice_mode_mix_other_mode_mismatch_soft_warns`

None of those three is counted as verified. The warnings are multiprocessing
fork deprecations from the existing crash-recovery tests.

Final rerun after restricting joint-gate diagnostics to new rows and
strengthening the mixed-state, unchanged-request and apply-once assertions:
the 33-file command above with these six files appended before its same
`-q -n 2 -m 'not arc_close'` flags (39 files total):

```text
tests/test_persona_gate.py tests/test_discrimination_profiles.py tests/test_error_hunt_items.py tests/test_ingest_instrument_gates.py tests/test_identity_pins.py tests/test_retired_config_identities.py
```

**1 failed, 936 passed in 86.18s.** The only failure remains
`test_first_questions_arrive.py::test_the_plan_route_request_is_byte_identical_under_a_ceiling`
opening its socket; again not counted. Every added/edited behavioral test,
the pins, and all runnable members of this group pass on the final code.

```sh
t.sh tests/test_test_layout.py -q -n 1
```

**3 passed in 19.10s.** Run alone.

```sh
t.sh tests/test_architecture.py -q -n 1
```

**18 passed in 30.66s.** Run alone.

```sh
py.sh ruff check
py.sh lint-imports --no-cache
git diff --check
```

Ruff: **All checks passed!** (development and final runs). Import lint:
**Contracts: 43 kept, 0 broken.** Diff whitespace check: **exit 0**, no output.

### Final joint-subset regression

Two structurally valid contrast pairs share a persona grouping tag. The only
firing member has a forbidden selected-response surface. The initial joint
persona verdict passes the group; removing that row and its dangling partner
leaves a nonseparating pair. Repeating **both** joint gates on the candidates
until stable refuses the remaining new rows with their persona reason. This
is necessary even though each gate's original full-part verdict was correct.

```sh
t.sh tests/test_contrast_pairs.py -q -n 2 -k actual_apply_subset
```

Fixture construction first **1 passed in 1.75s**, because its fake used the
wrong handler method and fell back to deterministic firing; this was not
claimed as defect evidence. Corrected to the house fake's
`grade_diagnostic_fire`: **1 failed in 1.77s** on the implementation before
the joint-subset loop, and **1 failed in 1.71s** on unchanged HEAD production.

```sh
t.sh tests/test_section_question_parts.py tests/test_contrast_pairs.py tests/test_first_questions_today.py tests/test_persona_gate.py tests/test_discrimination_profiles.py tests/test_error_hunt_items.py tests/test_ingest_instrument_gates.py tests/test_identity_pins.py tests/test_retired_config_identities.py tests/test_structure_ratchets.py tests/test_effective_defaults_golden.py tests/test_kill_switches.py tests/test_sqlite_file_copies.py tests/test_mobile_allowlist.py -q -n 2 -m 'not arc_close'
```

**854 passed in 68.70s.** All final incremental behavior, joint-gate subset
checks, identity pins, ratchets, defaults and mobile allowlist checks pass.
Final `py.sh ruff check`: **All checks passed!** Final
`py.sh lint-imports --no-cache`: **Contracts: 43 kept, 0 broken.**

## Size, scope and unverified work

Production: **+225 / -86, net +139 lines, eight files**. Whole change,
including this new record: **+837 / -131, net +706 lines, 15 files**. No stop condition was met.

No staging, commit or landing gate was performed. The orchestrator owns
those steps. `CLAUDE.md`, `refactor-status.md`, configuration, identity goldens,
schema/migrations and vault references are unchanged. No new model or network
calls, private configuration reads, private vault reads, broad filesystem
searches or reference regeneration were performed.

Not verified: the four socket-opening tests named above; real-provider
latency/token spend, a live desktop/phone walk, frontend rendering and the
combined Today state, and a real asynchronous worker/UI race. The first-part
queue test runs the actual scheduler inside the fake's pending second call;
the reload test runs the actual queue-revision handler with a controlled
vault reload. Existing durable apply-recovery and host-revision tests also
ran; this task's crash injection is after apply returns, not a new simulation
of each write-ahead protocol boundary. The backend work is complete; the
combined Today state remains the explicitly identified frontend step.
