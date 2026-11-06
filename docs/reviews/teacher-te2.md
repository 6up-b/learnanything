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
