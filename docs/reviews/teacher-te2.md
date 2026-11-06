# Teacher TE2: probes, gaps, typed goals and the resume card in lessons (`teacher/te2`, base `5565bede25`)

Built from `docs/specs/spec_teacher_v1.md` revision 5: §24's TE2 row (the scope), §11.3, §11.5, §11.7, §11.8, §20 and
§23.1 (owner-accepted Nov 5). One teacher successor, `mvp-0.50` on this branch (ONE constant,
`TEACHER_PROBES_ALGORITHM_VERSION`; expected `mvp-0.51` at landing, after the router follow-up batch's `mvp-0.50`),
kill switch `teacher.probes` with the existing `teacher.enabled`. One migration, 248 (renumbered at landing if TE3a
claims it first). Every test uses fakes (`TeacherFake`, `StructuredClientFake`, a recording FG1 author,
`DeliverableFake`, `GapLLMFake`); no paid call was made by this stage. No reader or writer of the old item difficulty
scalar is added (see "R4-style check" below).

## Commits

| Part | Commit | What |
|---|---|---|
| 1 | `a21f088b16` | Migration 248 (four CHECK rebuilds; `lesson_episodes.refusal_reason`; the close-once trigger recreated), head fixture `migration_head_248`, the mechanical head pins |
| 2 | `dc5302d98c` | Successor `mvp-0.50`, `teacher.probes`, `teacher.placement.max_probes`, upgrade, CLI and openers, every defaults snapshot recomputed, the version pins; TE2 itself (contracts, doctrine paragraph, brief v2, `serve_probe` end to end, `propose_gap`, typed goals, the resume read, the report), sidecar RPCs |
| 3 | `a46bf6f633` | The desktop: the probe card, the typed-goal start, Today's lesson card, DTOs, client, Rust passthroughs |
| 4 | (this commit) | Spec §20 "As built", this file, the regenerated references |

Parts 2's successor and TE2 code share the config, the turn schema and the test vault, so they land in one commit.

## What exists now

| Spec | Where |
|---|---|
| §18.3 successor | `algorithm_versions.TEACHER_PROBES_ALGORITHM_VERSION` / `TEACHER_PROBES_VERSIONS`; `teacher_probes_upgrade` (the chain's next journalled link, a projection activation; the openers install its completion); `config.schema.TeacherConfig.probes`, `TeacherPlacementConfig.max_probes`; registry rule (structural/operational) |
| The switch | `teacher.te2.on(vault)`: at the tag, `teacher.enabled` and `teacher.probes`; a lesson is TE2's when it was opened under it (`lesson_brief_v2`) and the switch is on now |
| §8.1 brief v2 | `teacher.brief.build_brief(te2=True)`: no `probes` on a node, its `delayed_check` ("an unseen question exists" / "none yet", the delayed checks' own candidate rule, no item named), `where_you_left_off` (`te2.where_you_left_off`) |
| §9 turn | `contracts.TeacherTurnTE2*` (four shapes, over TE1's, TE2-log's and the visuals'); `serve_probe {node, readings, p}`, `propose_gap {ref, gap_kind, gap}`; paragraph `teacher/doctrine/te2/v1.md`, prompt `+te2-v1`, family `+teacher_te2_v1` |
| §11.3 probes | `teacher/probes.py` (request, serve, answer, retire, the worker's report), `followup_run/lesson_probe.py` (FG1's generation path, lesson origin), `followup_serve.queue.enqueue_lesson` / `skip_lesson_job`, `followup_serve.identity` (lesson items reserved at every door), `followup_run/jobs.py` (kind `lesson`) |
| §11.3 forecast | `scheduling.forecast_receipts.LESSON_PROBE_CORRECT` / `LESSON_PROBE_ATTEMPT`, `evsi_calibration.forecast_report.resolve_lesson_probe` |
| §11.7 gaps | `service._propose_gap`, `diagnosis.text_gaps.sources.lesson_gap_text`, `jobs.enqueue_lesson_gap`, source kind `lesson` (readable, serving) |
| §11.5 typed goals | `source_retrieval.deliverables.resolve_typed_goal` / `create_lesson_topic`, `teacher/topics.py`, `service.open_lesson(entry="typed_goal")`, RPC `lesson.goal` |
| §11.8 resume | `service.open_lessons`, RPC `lesson.open_lessons`, `lesson.turn close` (no teacher call); the brief's `where_you_left_off` |
| §11.9 episodes | rows of kind `probe`, `gap`, `goal_lo`, with `refusal_reason` and the item id set with the close |
| §11.10 report | probes refused by reason and served (`teacher/report.py`) |
| §19 UI | `LessonScreen.tsx` (probe card, typed-goal start), `today/ContinueLessonCard.tsx`, `algoConfig.lessonGoals` (`teacher.te2` from the sidecar) |

## How a probe runs (with the files that do it)

1. The teacher's turn asks for `serve_probe`. The contract check (`probes.contract_problem`) names any problem by
   location: the node must be a plan node on a vault LO; one to four readings and `p`; no check open; nothing else
   being prepared or answered; one question per node; at most `teacher.placement.max_probes`. The readings and node
   pass the output guards and the identifier guard before the turn is accepted (`service._logged`).
2. In one transaction with the turn's other effects (`service._serve_probe` → `probes.request`): the `serve_probe`
   entry (readings' words, the probe's ref, an attempt id minted now), the `lesson_probe_correct` receipt bound to that
   attempt id (**written before any serve**), FG1's job (kind `lesson`, key `lesson:<lesson>:<node>`) and the `probe`
   episode (teacher `p`, receipt id, job id). The screen shows *Preparing a question on this…* and *Teach it anyway*.
3. The worker (`lesson_probe.run`, FG1's follow-up slot, under `runtime.spend.metered` as every FG1 job): the
   reserved questions are read first (unreadable: `protection_unavailable`; a reading reproducing one:
   `reserved_match`, nothing sent); FG1's context builder's rules (only admissible, unreserved questions, a summary
   quoting none); FG1's authoring call; FG1's output checks; FG1's `persist_item` (`source = 'lesson'`: the reserved
   echo check, the structural instance gate, the never-before-seen check; identity and parked family link before the
   file). Then `probe_ready` with the admission receipt (the per-reading predictions pinned as the blind bundle) or
   `probe_refused` with its reason, which also closes the episode.
4. `lesson.view` serves it (`probes.serve`): FG1's atomic first-serve claim (surface `lesson`), a `probe_served`
   entry, the question only. While it is open, `reply`, `answer_check` and `answer_prediction` are refused
   (`probe_open`) and no teacher call is made (§9.1 `cold_attempt`).
5. The answer (`answer_probe`): blind-graded on the answer only; one `diagnostic_probe` attempt
   (`entry_surface lesson`, `evidence_origin lesson_probe`, `awaits_completion = False`: no split diagnoser, no FG1
   workflow), its independence the reveal ledger's topic-wide check, then the item retired; `probe_result`; the episode
   closed `answered` with the attempt, grade and item id. The teacher reads the result next.
6. Unused: *Teach it anyway* (before it is open) and the lesson's close retire it (`probes.retire`: the queued job
   skipped, the item retired, `probe_retired`, the episode `retired`); a generator that lands after that retires its
   item at once (`record_ready`).

## Never served again: every door

| Door | What refuses a lesson probe |
|---|---|
| Routine serving, plan pool, probe episodes, AD, exams, Check once, follow-up tasks | `identity.door_sets`: unserved lesson items are reserved (`source = 'lesson'`), served/retired ones closed |
| The sidecar's serve doors | `identity.door_refusal`: reserved before the burn (no workflow can claim it), closed after |
| A second serve in the lesson | after the answer the item is retired: `claim_serve` refuses even surface `lesson` |
| Rebuild, state sync | the item stays parked (pending review) and ledger-closed; tested |
| Remint | `generated_probe_single_use`; tested |
| Delayed checks (TE1's picker) | `delayed_checks.candidates` now leaves every generated probe out (a latent gap for FG1's own probes too) |
| The teacher's brief | v2 has no probe headers; v1 already left generated probes out |

## Calls per probe, rows and the report (on fakes)

**Calls.** Per probe: 1 author call (FG1's operation, route `followup_probe_author`, a plan route), at most 2 with
FG1's one retry after a transport failure (`test_a_generation_that_fails_twice_is_refused_and_the_teacher_is_told`:
2 calls, then `generation_failed`); 0 on a reserved match or unreadable protection; 1 blind-grader call for its answer.
Wait on fakes: 0.395 s from enqueue to `done` (one job). Per typed goal: 1 resolver call (route
`deliverable_scope_resolver`), 0 for the same words over the same LOs (`fresh`). Per gap: the text-gap pipeline's own
judge (one reading request is skipped: the teacher's reading is the context model's) plus its Decider second opinion
where routed. **A lesson a day with two probes:** 2 author calls (up to 4 with retries) + 2 grader calls beyond the
lesson's own turns; with a typed goal, +1 resolver call; with a gap, +1 judge. All plan routes; nothing metered.

**Rows** on a synthetic TE2 lesson (a typed goal with one leftover accepted, a probe answered right, a gap filed, the
stop):

| Table / kind | Rows |
|---|---|
| `lesson_episodes` | `goal_lo` 1 (closed `lesson_closed`), `probe` 1 (`answered`), `gap` 1 (`misconception`, closed `lesson_closed`, result pending: the gap job had not run) |
| `forecast_receipts` | `lesson_probe_correct` 1 |
| `followup_generation_jobs` | `lesson` 1 (`done`) |
| `learner_text_gap_jobs` | `lesson` 1 (`queued`) |
| `generated_probe_items` / `generated_probe_burns` | `lesson` 1 / `served` (surface `lesson`) 1, `retired` 1 |
| `practice_attempts` | `diagnostic_probe` 1 (`lesson`, `lesson_probe`) |
| `deliverable_scope_resolutions` | 1 (`lesson_goal:<hash>`, `resolver`) |
| `lesson_turns` | `goal_lo` 1, `serve_probe` 1, `probe_ready` 1, `probe_served` 1, `probe_answer` 1, `probe_result` 1, `propose_gap` 1, teacher turns 3 |

**What the teacher report prints** (that lesson):

```
lessons: 1 opened, 0 open; closed: goal_reached 1
lesson minutes: active 0.0 (over 0 lesson(s) with intervals; 1 with none, active unknown) · elapsed 4.0 · 0 interval(s) missing
delayed checks: 0 committed, 0 due, 0 answered
episodes: probe 1, detour 0, gap 1, goal_lo 1
probes: 1 generated, 0 refused, 0 retired unused, 1 served, 1 answered
detours by repair: none (0 unlogged)
gaps: misconception:pending 1
probe forecasts (lesson_probe_correct) against their grades: 1 scored, mean forecast 0.40 against 1.00 right, Brier 0.360, log loss 0.916 nats
placement forecasts (lesson_node_held, 0 receipt(s)) against natural outcomes (self-selected): none scored yet
placement forecasts against RO5's randomized checks (randomized): none scored yet
coverage of item 5's fields over 3 episode(s): hypothesis 2/3, repair_class 1/3, teacher_p 1/3, predicted_success 3/3, mastery 3/3, open_misconceptions_and_hypotheses 3/3, elapsed_minutes 3/3, active_minutes 0/3, origin 3/3, objective_trace 0/3, experiment_assignments 0/3, outcome 3/3
```

A refused probe prints `probes: 0 generated, 1 refused (generation_failed 1), 0 retired unused, 0 served, 0 answered`.
With no probe the line is TE2-log's exactly.

## The turn schema

| Turn | Bytes | SHA-256 (first 12) |
|---|---|---|
| `TeacherTurnV1` (TE1; TE2 off) | 3438 | `9668bbc1796b` (unchanged) |
| `TeacherTurnTE2V1` | 3654 | `506ef0e76dc8` |
| `TeacherTurnTE2EpisodesV1` | 3983 | `641d848707d6` |
| `TeacherTurnTE2VisualsV1` | 4771 | `c2823173629e` |
| `TeacherTurnTE2VisualsEpisodesV1` (the defaults with a figure host) | 5160 (+300 over TE2-log's 4860) | `8c6b508788bc` |

The TE2 paragraph adds 2131 characters to the instructions (about 530 tokens per teacher call).

## Off, or below the tag

`tests/test_teacher_te2_lessons.py::test_switch_off_or_below_the_tag_gives_te1s_lesson_byte_for_byte` (with
`teacher.episode_log` on and off): a lesson at mvp-0.49 and one at mvp-0.50 with `teacher.probes = false` send the
same prompts byte for byte (ids aside), with the same schemas, the same `lesson_brief_v1` (probe headers kept), the
same ledger steps and forecast families; the view carries no `te2` or `probe` key; typed goals and `close` are refused;
Today's card is not rendered (`teacher.te2` absent from the sidecar config).

## What could not be built as written, and the smallest alternative

1. **Readings on one node (§11.3 "with one, FG1 §4.3's family-pattern contract").** §4.3's contract
   (`mint_single_use_probe_surface`) is bound to FG1's probe episodes and their instrument cards; a lesson has no probe
   episode. Built: the §4.1 contract with the one reading as the rival of full credit ("does not hold this yet: …"), so
   FG1's output checks (two criteria, a prediction over them) still run. Smallest alternative: give
   `mint_single_use_probe_surface` an episode-free entry point.
2. **FG1's manipulation audit and causal commissioning.** Both compare a new question with the missed one and write
   causal candidates on a factor; a lesson probe has no source question and, by the spec, never resolves a cause
   factor. Built: the admission receipt records `manipulation_audit: not_applicable_no_source_question`, and the blind
   bundle is the author's per-reading predictions pinned in the `probe_ready` entry before any serve. The structural
   gate, never-before-seen, reserved checks and the identity are FG1's, unchanged.
3. **`lessons.entry` has no `typed_goal`.** The migration's scope is the four CHECK rebuilds; rebuilding `lessons`
   (many foreign keys) was not in it. Built: a typed goal's lesson is stored with entry `learning_object` and its goal
   JSON's `typed` block (text, goal key, every leftover with its decision, created LOs). Smallest alternative: add
   `typed_goal` to that CHECK in a later rebuild.
4. **The teacher's own `create_goal_lo` action (§9) mid-lesson.** Not built: new topics come from the typed goal's
   leftovers, on the learner's yes, before the lesson opens (§11.5's journey). Smallest way to finish: a TE2 request
   `create_goal_lo {phrase, title, statement, anchors}` that only offers the topic (a pending card), with the learner's
   yes running `topics.plan_open`'s creation and `_record_goal_los` mid-lesson.
5. **"A library lookup is offered first" (§11.5).** Not built: the card says the new topic is taught from LearnLoop's
   model, not the learner's books. Smallest way to finish: a "Look in my library" link on the leftover opening the
   Library search with the phrase.
6. **Probe answers and the weight tables.** The DERIVED lesson-weight tables describe the ledgers through the latest
   answered lesson *check* (TE1 as built); a probe is no check, so its answer does not refresh them (the next check's
   refresh and every rebuild read it as of then). Without this the live tables diverged from the rebuild.
7. **Rebuild equivalence.** Mastery and facets: 0 deltas. One schedule row differs: the probe's own
   `practice_item_state`, by its `content_hash` stamp only (FG1's `persist_item` parks a generated item with no stamp;
   the rebuild's sync stamps every item); never active, never due, the same last attempt. The test pins exactly this.
   It is FG1's existing behaviour for every generated probe; smallest fix: stamp the hash in `persist_item`.
8. **Independence in practice.** The topic-wide check counts any reveal row on the LO, and a lesson's teaching text
   writes `tutor_answer` rows on every item whose key it overlaps; on the test vault the opening plan's words already
   overlapped one key. So a probe asked after any teaching on its topic is recorded not independent, as the spec says;
   the doctrine tells the teacher to probe before teaching.
9. **The pin moves.** The successor's version pins in 43 test files (sets, negative chain indexes, openers, frozen
   default digests) and the head-fixture pins were moved with `sed`/`perl` over exact patterns (no interpreter on
   source), then read back through `git diff` and the tests; the upgrade module was derived from RO6's by `sed` and
   its docstrings rewritten with the Edit tool. Every other edit used the Edit tool.

## R4-style check

`git diff 5565bede25 -- src migrations` adds no read or write of the difficulty columns,
`mastery.irt.difficulty_from_prior` or surprise's `b` (the probe is aimed by its readings; FG1's instance payload is
unchanged).

## Gate (targeted; the full suite, the durability lane and the whole vitest run are the landing gate's)

Every pytest/vitest/npm/cargo command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p
MemorySwapMax=1G`, pytest at `-n 6`, vitest at `--maxWorkers=4`; every other Python or CLI under `env -i` with empty
`HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`. No model call, no paid call.

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install --offline pypdfium2==5.14.0` | ok |
| `uv run lint-imports --no-cache` | 43 kept, 0 broken |
| pytest: the 65 test files the head rename touched + `test_teacher_te2_migration`, `test_table_roles`, `test_tracked_fixture_databases`, `test_coordinated_migrations`, `test_ad_protected_tables` | 867 passed, 3 skipped, 2 failed (fixed: AD's `column_classes` names `refusal_reason`; 232's altered-tables pin names 248's tables), then 42 passed |
| pytest: the 69 version-pinned test files + `test_teacher_te2_successor`, `test_cli_help_snapshot`, `test_registry_audit`, `test_config_refactor` | 1339 passed, 44 failed (the pins), fixed; the 28 files again: 544 passed, 6 failed (sets ending at `LATEST`), fixed; those 6 again with the sidecar and successor tests: 129 passed (+1 key-case fix, 3 passed) |
| pytest: the TE2 files (`test_teacher_te2_probes`, `test_teacher_te2_lessons`) | 25 passed |
| pytest, the gate: 151 files (every `test_teacher_*`, `test_followup*`, the text-gap, deliverable, forecast-report, delayed-check, remint, serving-exclusion and state-sync files; every file naming a module I changed; the contract set below) | 3072 passed, 6 skipped, 2 xfailed, 2 failed (`test_learner_text_source_widening` pins the migrations that rebuild `learner_text_gaps`; `test_ro2_history_protection` requires AD's `GAP_SOURCES` to judge every readable source: `lesson` added as withheld), fixed: those two with the catalog guards, 59 passed |
| pytest `-m durability` on the migration, probe and lesson files | 4 passed |
| `npm install`; `npm run typecheck` | ok |
| `npx vitest run --maxWorkers=4` LessonScreen.te2, LessonScreen, today/ContinueLessonCard, TodayScreen.suggestion, App.lessonSuggestion, lessonsConfig | 32 passed (6 files) |
| `npm run frontend:build` | ok (the existing chunk-size warning) |
| `cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml` | ok |
| `db_generate_reference.py`, `db_validate_reference.py` (`SCHEMA_HEAD` 248) | errors [] (after the two prose leaf counts 1171 → 1173) |
| `desktop_generate.py`, `desktop_validate.py` (321 TS/TSX, 310 entry-build, ACTIVE 327) | passed, reproducible |
| `module_generate.py`, `module_validate.py` | PASS, 1242 modules |

The contract set inside the gate: `test_architecture` (frozen cycles), `test_table_roles`, `test_registry_audit`,
`test_module_catalog_inventory`, `test_ad_protected_tables`, `test_cli_help_snapshot`, the display-label audit
(`test_router_why_copy`, `test_key_ladder_labels`, `test_measurement_state_labels`, `test_rw5c_labels`), the
process-launch allowlist (`test_ai_tool_isolation`, `test_e0_isolation`, `test_codex_tool_lockdown`,
`test_codex_lockdown_round3`), `test_sqlite_file_copies`, `test_public_tip_guards`, `test_config_refactor`,
`test_desktop_rpc_contract`, `test_sidecar_serializer_snapshot`, `test_sidecar_contract`, `test_sidecar_registry`,
`test_mobile_allowlist`, `test_desktop_activation_audit`, `test_coordinated_migrations`,
`test_tracked_fixture_databases`, `test_migrations` (each run where the file exists).

Reference churn: only stamp lines (`source_commit`, `source_commit_timestamp`) were left out; `schema_head: 248` on
every table note is kept.

New test files: `tests/test_teacher_te2_migration.py` (6), `tests/test_teacher_te2_successor.py` (12),
`tests/test_teacher_te2_probes.py` (12), `tests/test_teacher_te2_lessons.py` (13), `tests/test_teacher_te2_sidecar.py`
(3), `apps/learnloop-tauri/src/screens/LessonScreen.te2.test.tsx` (5),
`apps/learnloop-tauri/src/screens/today/ContinueLessonCard.test.tsx` (1).

## Landing notes

- Renumber: the tag to the next free (expected `mvp-0.51`; one constant, the defaults snapshot key, the pins in the
  43 files and `test_teacher_te2_successor.py`), the migration to the next free (rebuild the head from main's head
  with only it applied; repeat the head pins).
- `lesson.goal` and `lesson.open_lessons` are in their own `LESSON_TE2_RPCS` (the mobile allowlist file holds the
  owner's uncommitted edits); they can join `TEACHER_TE1_RPCS` there once those land.
- Owner steps after the fast-forward: `learnloop upgrade` each vault (migration 248 applies on open; the upgrade
  publishes the tag), rebuild the desktop app. To switch TE2 off: `[teacher] probes = false`.

## Landing onto main

Main was `516db1d862`: the router follow-up batch had landed as mvp-0.50, with no migration. The merge
(`0c2952c5a4`) renumbered TE2's successor to **mvp-0.51 <- mvp-0.50**. Migration 248 stays 248, because main's head
is 247. The router speed stage and TE3a had not landed.

### Orchestrator rulings (verbatim)

- R1: "F7 is fixed at regrade publication: a regrade of a probe grade (a lesson probe's, and FG1's presentation path's, which shares _dual_write_probe_grade) appends and activates a raw grade event and an interpretation carrying the replacement grade's actual identity (prompt, schema, grader identity hash and calibration model), and ordinary replay creates no duplicate. FG1's presentation path also passes the submission's grader_identity on its first write (the re-review's open question). Then check whether an ordinary, non-probe regrade has the same defect (the active interpretation keeping the original grader's calibration): if it does and the fix is in the same publication function, fix it there with a test; if it lives elsewhere, record it with its smallest fix for the follow-up batch. Codex's two regrade reproductions (split toggled on between answer and regrade; an ordinary blind regrade with a newer prompt) are tests, failing on the pre-fix source. No further Codex round; I read the diff before landing."
- R2: "§11.5's library lookup is built: a leftover topic's card offers 'Look in my library' first, opening the Library search with the phrase, before 'Create it'. The teacher's own create_goal_lo mid-lesson (record item 4) and lessons.entry 'typed_goal' (item 3) go to the follow-up batch as recorded."
- R3: "FG1's persist_item stamps the generated item's content_hash, so rebuild equivalence on a lesson fixture with a probe is exact (record item 7); the test's pin moves from 'one stamp differs' to no difference. If this changes any existing FG1 test's expectation, say which."
- R4: "Accepted as recorded: the one-reading probe through FG1's §4.1 contract with the reading as the rival of full credit; FG1's manipulation audit not applicable with no source question; a probe answer does not refresh the lesson-weight tables; a probe after any overlapping teaching on its topic is recorded not independent (the doctrine says probe before teaching)."
- R5: "Paid calls are as recorded (plan route only, nothing metered: per probe 1 author call, at most 2; per typed goal 1 resolver call, none on a repeat; per gap the judge; about 2-4 author and 2 grading calls a day at one lesson a day with two probes). The owner accepted that cost in rev 5's decision 2. The landing smoke makes no real call."
- R6: "Owner, Nov 5: the old item difficulty scalar is to be retired in the refactor. TE2 adds no new reader or writer of it; the landing checks this with a grep of the diff against main for the difficulty columns, mastery.irt.difficulty_from_prior and surprise's b, and records the result."

### Commits

| Step | Commit | What |
|---|---|---|
| Merge, renumber | `0c2952c5a4` | Main merged. `TEACHER_PROBES_ALGORITHM_VERSION = mvp-0.51` follows `ROUTER_FOLLOWUPS_ALGORITHM_VERSION` in the chain. The upgrade's `PREDECESSOR` and completion are the follow-up batch's. The openers install TE2's completion. `--to` names both. Every defaults snapshot was recomputed. The TE2 successor test freezes main's mvp-0.50 snapshot. The follow-up batch's test drops TE2's keys. Pins were moved by exact-pattern scripts. The CLI help snapshot was regenerated |
| R1 | `5564387090`, `af3a975871` | A regrade publishes the probe grade under the replacement's identity. FG1's presentation path stamps the submission's identity. The second commit routes the call through `attempts.attempts`, so the frozen-cycles contract is unchanged (details in `docs/reviews/teacher-te2-codex-review.md`, "Final verify") |
| R2 | `73b4784e41` | "Look in my library", then "Create it" (was "Yes"), then "No". The lookup closes the lesson setup and opens the Reader's library search on the leftover's words |
| R3 | `1a7e274d14` | `persist_item` stamps `content_hash` |
| Review record | `8443ae6be6` | The Codex review file's final-verify section |
| References | `554e01cefb` | Regenerated on the merged tree |

**R1.** The two Codex reproductions and FG1's presentation path failed on the pre-fix source (3 failed). The ordinary
check passes on both sources, as it should. The **ordinary, non-probe regrade** does not have the defect, because its
replay re-mints the grade event under the new blind record's identity. Two follow-ups go to the batch:

- That re-mint happens on **every** replay of an ordinary AI-graded attempt, so each rebuild appends one raw grade
  event and interpretation per attempt. This predates TE2. Smallest fix: `_dual_write_grade_channel` skips a replay
  whose active interpretation already comes from an event with the same identity, class and score.
- A regrade of a **lesson probe** in a split vault appends a blind record. Through the regrade's generic path, that
  record **queues the attempt's diagnosis**, so a regraded lesson probe gets the post-attempt diagnosis its first
  answer skipped. At the smoke it produced causal hypotheses on the probe's attempt. This is not a serve and not a
  door. Smallest fix: `insert_blind_grade_record(queue_diagnosis=False)` when the regraded attempt's
  `evidence_origin` is `lesson_probe`.

**R2** (desktop only). The phrase reaches the Reader's existing across-source search (`reader.search_sources`). At
the smoke, the RPC returned hits for the leftover on each copy: arxiv_v2 16, linear_algebra 5, probability 9.

**R3** changed no existing FG1 test's expectation. The FG1, rebuild and TE2 test files: 708 passed, 4 xfailed.

**R6.** `git diff 516db1d862 -- src migrations` adds no line naming `difficulty`, `difficulty_from_prior`,
`surprise` or the IRT `b`. The grep of added lines is empty. R3's state write passes only `content_hash` in addition.
The same call's existing `difficulty=None` is unchanged: `persist_item` already wrote it, for a parked item.

### Gate

The gate ran at `554e01cefb`: the merged tree with R1-R3 and the references. The record commits after it are docs
only. Every pytest, vitest, npm and cargo command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p
MemorySwapMax=1G`. The full suite ran in 10G/2G under `flock /tmp/learnloop-fullsuite.lock`. Every other Python or CLI
ran under `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`. No model call or paid call was made.

| Command | Result |
|---|---|
| Step 1: targeted pytest, 199 files, `-n 6` (listed below) | 3254 passed, 18 skipped, 6 xfailed, 1 failed (see below) |
| Step 1: `--durable-sqlite` on the touched TE2 and successor files | 68 passed |
| Step 2: `test_measurement_state_labels`, `test_codex_lockdown_round3`, `test_desktop_rpc_contract`, `test_sidecar_serializer_snapshot` | 40 passed |
| Step 1: vitest on the touched files (LessonScreen.te2, LessonScreen, ReaderScreen.followsLearner, App.lessonSuggestion) | 63 passed |
| Step 3: `db_generate_reference` + `db_validate_reference` | errors [] (after the two prose leaf counts 1178 -> 1180) |
| Step 3: `desktop_generate` / `desktop_validate` | passed (321 TS/TSX, ACTIVE 327) |
| Step 3: `module_generate` / `module_validate` | PASS (1244 modules) |
| Step 3: `validate_vault.py` | passed (2235 notes) |
| Step 3: config fingerprints | none moved |
| `uv sync --extra dev --extra mobile`, `uv pip install --offline pypdfium2==5.14.0` | ok |
| `lint-imports --no-cache` | 43 kept, 0 broken |
| Full pytest (`-n 8 --dist worksteal`) | **26916 passed, 90 skipped, 47 xfailed** (1:00:11). No failure, so neither known flake was seen (`test_ro5_landing`'s r8, `test_rofu_carried`'s early publication) |
| Durability lane (`-m durability`) | 404 passed, 1 skipped |
| Owner lane on fresh backup-API copies of `owner-copies-mvp035` | 83 passed, 4 skipped, and the 2 known failures (`test_activity_backfill`, `test_placement_fixture_copies[arxiv_v2]`), as at the follow-up batch's landing |
| Desktop: typecheck, whole vitest (`--maxWorkers=4`), `frontend:build`, `cargo check` | ok, 2772 passed, ok, ok |
| Mobile: typecheck, build | ok, ok |

**Step 1's files:** every `test_teacher_*` and `test_followup*` file; the probe-episode, characterization-probe,
grade-resolution, blind-grading, placement-split, regrade-contract, rebuild-equivalence and rebuild-orchestrator files;
the text-gap, deliverable, forecast, delayed-check, remint, serving-exclusion and state-sync files; the successor and
pin files; and the contract set.

**Step 1's one failure:** `test_regrade_contract_upgrade::test_an_upgrade_interrupted_after_publication_is_resumed`,
a subprocess crash-and-resume test. It failed 33 minutes into the run, while the smoke was loading the machine.

- Rerun alone 3 times: passed each time.
- Its whole file: 17 passed.
- It did not recur in the full suite.

### Smoke

**Setup.**
- **Copies.** Fresh backup-API copies of `~/learnloop-backups/mvp043-20261103-copy` (arxiv_v2, linear_algebra,
  probability), neutralized (every AI route at 127.0.0.1:9), under `fixtures-local/landing-te2-smoke/` (since
  deleted).
- **Upgrades.** On main code (`516db1d862`): mvp-0.45, rebuild, mvp-0.46, mvp-0.47, rebuild, then the default to
  mvp-0.50 (head 247). On branch code, the copy opened once (migration 248 applied on open; head 248), then the
  default upgrade to mvp-0.51. Main and branch were each `git archive`d with `migrations/`. Smoke scripts ran under
  bash, Python under `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`.
- **Fakes.** All in-process: the teacher and its inline blind grader (`TeacherFake`), FG1's probe author
  (`ProbeAuthor`, a plan client), the text-gap judge, reader and drafter (`GapLLMFake`), the C0b resolver
  (`DeliverableFake`), R1's fake blind grader (`ReviewFakeClient`), the router's Decider and LLM.

**Below the tag, and at the tag with probes off.** One scripted lesson per copy: open, a check, a miss, a revised
plan, the close. Main at mvp-0.50 against the branch at mvp-0.50 (below the tag), and against the branch at mvp-0.51
with `teacher.probes = false`. On every copy the following were identical:

- the teacher prompts (6), the schemas (`TeacherTurnVisualsEpisodesV1`, 4860 bytes, `5cd36e9026ff`), the transcript
  and every view;
- the written rows (arxiv_v2 109 rows in 39 tables, linear_algebra 101 in 38, probability 111 in 45), once two
  known differences are set aside:
  - migration 248's new `lesson_episodes.refusal_reason` column (NULL);
  - at the tag, the version string `mvp-0.51` where main writes `mvp-0.50`.

**At the tag, probes on** (each copy, one run of the driver):

| | arxiv_v2 | linear_algebra | probability |
|---|---|---|---|
| Probes | p1 answered right, p2 answered wrong, p3 retired (`teach_anyway`) | the same | the same |
| Author calls | 2 | 2 | 2 |
| Forecast before serve | yes, both (receipt 15:01 < served 15:04; 15:06 < 15:09) | yes | yes |
| Served | once each, surface `lesson` | once | once |
| Other doors after the answer | `door_refusal` closed; desktop claim and second lesson claim refused; in the routine-serving exclusions; not a delayed-check candidate; remint `generated_probe_single_use` | the same | the same |
| Grade | blind (`grading_prompt_v2_blind` / `blind_grading_proposal_v1`), one raw grade event, positive canonical mass for p1 (0.70) and 0 for p2 | the same | the same |
| Activity class | `instructional_diagnostic` (`lesson_probe_exposed`: the plan's text overlapped the item, R4) | `pure_diagnostic` | `instructional_diagnostic` |
| R1 regrade of p1 | 1 -> 2 grade events. The active interpretation is `grading_prompt_v2_1_blind_reference_policy+own-route-v2` (= the new blind record's), with the regrade's model | the same | the same |
| Resume | the teacher was down on p2's result; `resume` made 1 teacher call | the same | the same |
| Gap | a `propose_gap` on the learner's words; the gap job `done` (source `lesson`); one `prerequisite` gap | the same | the same |
| Typed goal | ready, 6 topics, 1 leftover; the repeat `fresh` (1 resolver call in all); the leftover created (`teacher_goal_v1`), 1 `goal_lo` episode | 1 topic, 1 leftover, created | 3 topics, 1 leftover, created |
| Today's open lessons, Close it | listed; closed `learner_stop`, 0 teacher calls; then none listed | the same | the same |
| Protection | 2 withheld items: none of their text and no reserved finding in the author's requests | 20 withheld: none, no finding. A reading quoting the exam-reserved question `pi_axiom_commutative_recall_02` was refused `reserved_match` with nothing sent (0 author calls), from the teacher's turn and from a request written directly | 3 withheld: none, no finding |

arxiv_v2 and probability have no exam-reserved items, so the reserved-match case ran on linear_algebra only.

**Rows per kind** (arxiv_v2; probability is the same; linear_algebra adds its protection lesson's refused probe):

| Table / kind | Rows |
|---|---|
| `lesson_episodes` | `probe` answered 2, `probe` retired 1, `gap` resolved 1, `goal_lo` lesson_closed 1 (linear_algebra: plus `probe` refused, `refusal_reason` `reserved_match`) |
| `forecast_receipts` | `lesson_probe_correct` 3 (linear_algebra 4) |
| `followup_generation_jobs` | `lesson`: done 2, skipped 1 (linear_algebra done 4) |
| `generated_probe_items` / burns | `lesson` 2 / served (`lesson`) 2, retired 2 |
| `practice_attempts` | `diagnostic_probe` (`lesson`, `lesson_probe`) 2 |
| `learner_text_gap_jobs` / `learner_text_gaps` | `lesson` done 1 / `lesson` prerequisite 1 |
| `deliverable_scope_resolutions` | 1 |

**`learnloop teacher report`** (exit 0 on each copy; linear_algebra):

```
lessons: 3 opened, 0 open; closed: goal_reached 1, learner_stop 2
episodes: probe 4, detour 0, gap 1, goal_lo 1
probes: 2 generated, 1 refused (reserved_match 1), 1 retired unused, 2 served, 2 answered
gaps: prerequisite:created_prerequisite 1
probe forecasts (lesson_probe_correct) against their grades: 2 scored, mean forecast 0.40 against 0.00 right, Brier 0.160, log loss 0.511 nats
```

The report reads "0.00 right" because the smoke's R1 regrade, with a fake blind grader that only credits the
expected answer's words, regraded p1 to wrong.

**Today, Next and the follow-up gate.** This used the follow-up batch's driver, with one day, the seed pinned, the
second item missed (FG1's follow-up written by `AuthorFake`) and the first stop declined. Main at mvp-0.50 was
compared with:

- **the branch at mvp-0.50** (below the tag): identical on each copy (Today, plan, every step, every router LLM and
  Decider request, the gate), with one exception. FG1's follow-up probe's raw grade event now names the blind
  grader's identity (`grading_prompt_v2_1_blind_reference_policy+own-route-v2`) where main named the joint one
  (`grading_prompt_v1`). That is R1's ruled fix to FG1's presentation path, at every version. Nothing derived from
  it differed.
- **the branch at mvp-0.51:** identical in the same way. As in RO5's, RO6's and the batch's own landings, the
  boundary key's version string, which seeds the rollouts' noise, was set aside on both sides (`SMOKE_PIN_KEY`).
  So was the trace's generator key, which names the version. Without the key aside, the noise differed and the
  sessions diverged (arxiv_v2 8 served against 7; linear_algebra 7 against 10). With it aside, the steps, Today, the
  plan, the 5-6 LLM and Decider requests and the gate were identical on all three copies.
- **Next on the copies holding the lessons' probes**, after the rebuild and the sync: no lesson probe was served.
  Each probe still has exactly its one lesson attempt.

**Rebuild and sync.** `rebuild --shadow` on each probes-on copy: schedule 0 and facet 0 changes. The probe items'
rows included, so R3 holds on the copies too. Mastery changed by the `algorithm_version` stamp alone (mvp-0.47 ->
mvp-0.51): arxiv_v2 33 rows, linear_algebra 20, probability 17. That is the known upgrade-restamping item. TE2's rows
were identical after `rebuild-derived-state` and a state sync on each copy:

- lesson episodes, turns and intervals;
- the probes' items, burns, receipts, jobs, attempts and grade events (no duplicate);
- the gap's job and gap;
- the probe items' `practice_item_state` (inactive, never due).

**Calls and safety.**
- Every new `model_call_receipts` row on every copy came from a fake: `fake_author` (2), `fake_deliverable` (1),
  `fake_gap_llm` (3-4).
- The net watch logged no connect at all (so no non-loopback socket), and no Codex process. The only subprocesses
  were `git -C` (the data-root resolver) and `powerprofilesctl get`.

### What the owner must run

1. After the fast-forward, upgrade each vault from mvp-0.50 (the follow-up batch's steps first, if a vault is not
   there yet). Opening the vault applies migration 248; the upgrade publishes the tag:

   ```
   learnloop upgrade --vault ~/learnloop-vaults/linear_algebra
   learnloop upgrade --vault ~/learnloop-vaults/probability
   learnloop upgrade --vault ~/learnloop-vaults/arxiv_v2
   ```

   For a vault still at mvp-0.43, run the steps the follow-up batch's record gives first: `--to mvp-0.45`,
   `rebuild-derived-state`, `--to mvp-0.46`, `--to mvp-0.47`, `rebuild-derived-state`. Then the default upgrade
   reaches mvp-0.51 through the chain.
2. Rebuild the desktop app (R2's button, TE2's lesson screen and Today's card), then restart the phone host if it
   serves a vault being upgraded.
3. To switch TE2 off in a vault: `[teacher] probes = false`. Its lessons are then mvp-0.50's (TE1's and TE2-log's)
   byte for byte; `[teacher] enabled = false` turns lessons off altogether.

**Calls per lesson** (R5, plan route only, nothing metered):
- per probe: 1 author call, at most 2 with FG1's one retry, and 1 blind-grading call;
- per typed goal: 1 resolver call, none on a repeat;
- per gap: the text-gap judge;
- at one lesson a day with two probes: about 2-4 author calls and 2 grading calls, plus the lesson's own teacher turns.

### Open items (for the follow-up batch)

- R2's record items 3 and 4: `lessons.entry 'typed_goal'` (a CHECK rebuild), and the teacher's own
  `create_goal_lo` mid-lesson.
- R1's two follow-ups above: the ordinary replay's re-minted grade event per rebuild, and a regraded lesson probe's
  queued diagnosis.
- An FG1 presentation regrade's probe observation keeps the submission's posterior. Only its grade event and
  interpretation move.
- The text-gap judge keeps its existing route. Its Decider second opinion is on OpenRouter (metered, by owner
  decision).
- `lesson.goal` and `lesson.open_lessons` sit in `LESSON_TE2_RPCS` until the owner's mobile allowlist edits land.
- From the earlier records: the upgrade's mastery restamping, and the follow-up batch's R3 list.
