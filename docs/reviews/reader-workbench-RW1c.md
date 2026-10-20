# Reader workbench RW1c: a tutor that looks things up (stage `reader-rw1c`)

Branch `reader/rw1c` (worktree `learnanything-merge4`), base `main` at
`fab576ac1` (RW2b + H3 landed; migration head 213). Spec:
`docs/specs/spec_reader_workbench_v1.md` §1's RW1c line, §4.6 in full, the
RW1c rows of §12 (signals) and §13 (phase table), §11's routes paragraph,
G48, G53, G59, the RW1c test lists (§14) and the §15 checkpoint metrics.
Presentation: `docs/specs/ux_reader_workbench_v1.md` §4.0 (pending as
*looking in your books…* then *writing…*), §4.2 (three answer modes, *another
way*, *that didn't help…*, the offers, abstention), W3, W14. Consumed, never
rebuilt: `spec_source_practice_and_probes_v1.md` §9.1 `find_sources` with its
intents (`explain`, `alternative`, `remediate`), §9.4 `compare_sources`,
§6.2 the deterministic practice request (S0), §10.3 the tutor's
`tool_requests` (S4), §6.5 `record_proposal_impressions`, `practice_availability`.
Friction notes read: RW1b §9 item 2 (reuse `find_sources(intent="alternative")`
with the inquiry's passages excluded; the three modes are the tutor's, not the
router's), RW4a §9 item 1 (the reader branch of `tutor_qa` takes an injected
span provider), RW6a §5 (nothing for RW1c).

## 0. Plan (written before the code)

**Which sources-spec phases are on `main`.** All of S0-S5 merged at
`5db645a33` (mvp-0.18/0.19): `find_sources` with intents and
`compare_sources` (S3), `tool_requests`, `run_source_tool`,
`record_source_offer_shown` and `practice_availability` (S4), the practice
request (S0), impressions with surface `reader`. So RW1c uses the real
interfaces; "absent" (G53) is `source_service.enabled = false`, where RW1c
falls back as §4.6 says (the base `find_sources` for the Reader's own
retrieval, `intent="explain"` with the shown passages excluded for *another
way* and *that didn't help*, "Practice this" as a plain `find_practice` on
the learner's question, no tool requests). RW5b is not on `main`, so "Make
this explorable" is absent; RW1b is, so "Try the next step first" is built.

**Scope (RW1c only).**
1. A Reader-context span provider (`source_retrieval/reader_tutor.py`) with
   its own query: the learner's question, the inquiry's ancestors and, when
   personalized, the open gaps on the passage's LOs; run through the sources
   service's `find_sources(verify=True)` under the server-derived Reader
   caller (`reading`; a bound workbench session's item gives
   `assisted_practice`; a cold administration `cold_attempt` and nothing).
   T6's rule 0 holds: when the verification route cannot run, nothing is
   retrieved or paid for and the tutor is today's. Retrieved spans join the
   tutor's context **after** the selection and its neighbours (the citation
   allowlist keeps them first), held to `tutor_qa.context_token_budget`;
   every passage passes the held-out filter and, item-bound, T6's exclusions
   and `span_leaks_expected`.
2. Three answer modes (`tutor/reader_modes.py`, a prompt and response-schema
   change used only while `reader_tutor.retrieval_enabled`): "From your
   books" (a verbatim excerpt quote-verified in code against its passage;
   dropped, with the answer falling back to mode 2, when its text is not in
   the passage, the passage is not one the tutor was given, it is the
   learner's own selection text, held out, or reproduces a bound item's
   answer), a grounded explanation (today's answer, now with retrieved
   passages), and a bridge to the learner's work (only with open gaps or
   recent workbench steps on the same LOs and the personalized toggle on).
3. Abstention: when verification ran and kept no passage, the answer opens
   with "Your books don't cover this directly — this is LearnLoop's model's
   explanation", the excerpt is dropped and no citation is shown as the
   books'.
4. *Another way* (`find_sources(intent="alternative")`, every passage shown in
   the inquiry excluded, labelled *from a different book* / *a worked example
   instead*) and *that didn't help…* (a branch whose text is a reader
   question; `find_sources(intent="remediate")` with the inquiry's named gaps
   as `target_hypotheses`), both as follow-ups through `reader.ask`.
5. Offers under the answer (`TutorOffers.tsx`, behind
   `reader_tutor.offers_enabled`): the sources spec's practice request and
   tool requests rendered as buttons; `find_practice` and `find_sources`
   lookups start when the answer lands and show nothing until pressed;
   impressions (`record_proposal_impressions`, surface `reader`) and span
   exposures (`record_source_offer_shown`) only on the press;
   `compare_sources` runs only when pressed; an empty lookup turns into the
   line *nothing in your practice or books fits this yet*; a failed one keeps
   its button and runs again on the press. Plus the Reader's own "Try the
   next step first" on a cited derivation or worked example in the open
   source (RW1b's next-step question at that line).
6. Report: a `tutor` row in `learnloop reader report` (answers by mode,
   abstentions, excerpts dropped, another-way and that-didn't-help rates and
   whether the next exchange resolved the inquiry, buttons shown and pressed
   by kind).

**Switches.** `reader_tutor.retrieval_enabled` (retrieval, modes,
abstention, another way, that didn't help) and `reader_tutor.offers_enabled`
(the buttons), both on (frictionless defaults); classified in the parameter
registry. With both off the tutor is byte-identical: pinned against goldens
recorded on the base tree before any RW1c code (pytest
`test_reader_tutor_switch_off.py` with `tests/fixtures/reader_tutor_switch_off.json`;
vitest `tutorSwitchOff.test.tsx` and its snapshot).

**No migration** (the spec says none): exchanges stay `question_events` with
the manifest; presses are `reader_action_invoked` events
(`tutor_offer_pressed`, with the `source_tool_calls` id when the tutor asked).
**No new route**: the tutor's existing route; the sources spec's functions
for theirs. **No new RPC**: `reader.ask` gains optional inputs; the offers use
the existing `find_practice`, `run_source_tool`,
`record_proposal_impressions` and `record_source_offer_shown`. Evidence:
retrieval is context and display; buttons are learner picks; nothing writes
evidence, mastery or grading inputs; a tutor answer's reveal handling is
today's.

## 1. What was built

**Backend.**
- `config/schema.py`: `[reader_tutor]` `retrieval_enabled = true`, `offers_enabled = true` (modelled defaults, left out of the decision-only template); `params/parameter_registry.py` classifies both (structural, operational); every `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entry (mvp-0.9 … mvp-0.27) recomputed with its RW1c comment line.
- `source_retrieval/reader_tutor.py` (the Reader-context span provider): `ReaderLookup` (T6's rule 0 via `verification_route`; `cold_attempt` retrieves nothing; the injected `find` with `verify=True`, `scope="library"`, `limit=source_retrieval.tutor_spans`; a second guard dropping held-out hits and, item-bound, exercise/solution leads and `span_leaks_expected` hits; `books_cover` true/false/None), `reader_query` (the question + the latest two ancestors' questions + up to three open-gap statements when personalized), `passage_learning_objects` (RW4a's anchor, else current `primary`/`support` source links of the passage's blocks), `learner_work` (RW4a's `open_questions` statements, labelled LearnLoop's reading, and the most recent bound workbench session's live steps on those LOs), `inquiry_exchanges` / `shown_span_keys` / `shown_source_ids` / `named_gap_hypotheses` (another way's exclusions and label, remediate's `named_gap` refs), `next_step_buttons` (cited `proof` / `worked_example` blocks of the open source, `block_roles`).
- `tutor/reader_modes.py`: `ReaderTutorRequest`, `deliver` (selection and neighbours first, then retrieved passages not already delivered, held-out never, one budget), `verify_excerpt` (NFKC + whitespace-normalized substring of a passage the tutor was given; never the `selected_text` span; never held out; never a bound item's answer; 8–1,200 characters), `finalize` (modes in order, abstention, the bridge only with the learner's work and personalized; on abstention no citation shown, the count kept as `withheld_citations`).
- `tutor/ai_contracts.py`: `ReaderTutorQAContext(TutorQAContext)` (+`reader_tutor`), `ReaderExcerpt`, `ReaderTutorAnswer` / `ReaderTutorAnswerWithTools` (+`excerpt`, `bridge_md`), prompt versions `mvp-0.11-tutor-qa-reader-modes` (and `…-source-tool-requests`), the modes task appended only for that context. `tutor/tutor_qa.py`: `ask_question(reader_tutor=…)` — retrieval before the row lands (as RW4a's pinned path), `_reader_lookup_context`, the answer model and prompt version chosen from the context, `finalize` before citations persist, `result["reader_tutor"]`. None keeps the base path untouched.
- `reader/reader_dialogue.py`: `ask(reader_tutor=…)` passes through; the manifest records the spans the tutor was given and the retrieval receipt; the exchange payload carries `tutor` (absent on every older exchange), and `ask_history` projects it only with `tutor_views` (the history RPC passes it while either switch is on: fix round 5, R4). `ask(reader_binding=…)` (fix round 5, R1) records the guarded spans and earlier answers in the manifest, and the exchange's and the response's `hint_equivalent` is the bound question row's stored flag. `StubReaderClient` decodes the new context.
- `learnloop_sidecar/handlers/reader_tutor.py` (composition, no RPC) and `handlers/reader.py`: `reader.ask` gains `retrieval_intent` (`explain` | `alternative` | `remediate`), `personalized`, `workbench_session_id`; the caller is RW4a's `reader_caller`; `bound_ask` builds the workbench binding (`tutor/reader_modes.BoundAsk`: the item, the practice session, cold, the item's guard) whenever either switch is on, before and apart from the retrieval request (fix round 5, R1); `propose_sources` bound to it (or `find_sources_for_caller` with `explain` when `source_service.enabled` is off); a bound session writes no tool requests and no practice request; the excerpt's exposure (`source_exposure_events`, `tutor_citation`, entity `question_event`); `tutor_offers.buttons`; the fallback practice request without the service; `reader.prompt_contract` gains `reader_tutor` (retrieval, offers, another_way, personalized_default, try_next_step, manifest_includes) only while a switch is on.
- `reader/reader_inquiry.py`: client events `tutor_offer_shown`, `tutor_offer_pressed` and the fields `offer_kind`, `tool_call_id`, `offer_result` (salience only, no text). `reader/reader_report.py`: the `tutor` row (§15: answers by mode, abstained, excerpts dropped, retrieval statuses, another-way and that-didn't-help rates and whether the inquiry was resolved after, offers shown/pressed by kind and what the press found).

**Frontend** (`apps/learnloop-tauri/src`). `screens/reader/TutorAnswer.tsx` (the abstention line, *§ from your books* excerpt, *◇ LearnLoop's explanation*, *◇ connecting it to your work*, how another way's passages differ, *another way · that didn't help…* with *What's still unclear?*), `screens/reader/TutorOffers.tsx` (G59: eager `findPractice` / `runSourceTool` for practice and passage requests, nothing shown until the press, *◐ looking in your books…* in place, impressions with surface `reader` and `record_source_offer_shown` on the press, the comparison run on its press with *◐ comparing…*, *nothing in your practice or books fits this yet*, failed lookups re-run on the press, *practise ▸* through the Reader's own pick (`onCheckMe`, the working posture), *try the next step first* through RW1b's `activeCtl.start("next_step", …)`); `ReaderAskBranches.tsx` and `AskRail.tsx` render answers through `TutorAnswer` (byte-identical with no RW1c fields); `useReaderInquiry.ts` (`askAnotherWay`, `askDidntHelp`, the exchange's `tutor`/`offers`, history's `tutor`, a bound workbench session's id); `ReaderScreen.tsx` wires the contract's `readerTutor`; the Ask's pending line says *looking in your books, then writing an answer* while retrieval is on; `api/dto.ts`.

## 2. Gates and where they are tested

| Gate | Where |
|---|---|
| G48 (policy: reading / assisted_practice / nothing cold; another way never repeats a shown passage; an excerpt not in its passage dropped; abstention; requests and buttons render as buttons; comparison only when pressed; never serves, schedules or imports) | `test_reader_tutor_retrieval.py` (provider, own query, personalized query and bridge, bound session, cold attempt, verification not ready, excerpt kept / dropped ×4 / selection text, abstention, another way exclusions and its honest abstention, that didn't help, held-out sentinel + control, exam material, G53 absent/faked, no learning state); `test_reader_tutor_offers.py`; `TutorOffers.test.tsx`, `TutorAnswer.test.tsx`, `tutorReader.test.tsx` |
| G53 (the sources spec absent and faked) | `test_with_the_service_absent_the_base_find_sources_serves_explain` (base `find_sources_for_caller`, explain with exclusions, no tool requests, plain "Practice this"); `test_with_the_service_faked_the_readers_calls_are_the_documented_ones`; RW4a's AST test (`test_reader_find_sources_callers.py`) still finds no second service function in a Reader package |
| G59 (fetch early, show on press) | `test_reader_tutor_offers.py` (eager lookups leave only their proposal/run rows; impressions and exposures on the press; the lazy comparison; the empty result and the failed-then-retried run); `TutorOffers.test.tsx` (8) |
| Switch-off byte identity | `test_reader_tutor_switch_off.py` against `tests/fixtures/reader_tutor_switch_off.json`, recorded on `fab576ac1` before any RW1c code (prompts, result models, both `reader.ask` responses, history, contract, interaction events, question rows), plus the retrieval-off/offers-on case; vitest `tutorSwitchOff.test.tsx` with its base-recorded snapshot (the landed answer's clock stamp normalized in both the test and the stored snapshot) |
| Held-out sentinel | `test_a_held_out_sentinel_never_reaches_the_tutor_the_verifier_or_the_excerpt[True]` (never in the tutor's or the verifier's prompts, never on the wire, the excerpt dropped, `exam_withheld ≥ 1`) and its control `[False]` (unmarked, the same passage is retrieved, verified and quoted) |

## 3. Decisions and deviations

1. **Sources-spec phases present.** S0–S5 are all on `main` (`5db645a33`); RW1c consumes the real `find_sources` intents, `compare_sources`, `tool_requests` / `run_source_tool`, `record_source_offer_shown`, `record_proposal_impressions`. "Absent" means `source_service.enabled = false`; `practice_availability` is not called by the Reader (the router's pass; nothing in §4.6 asks the Reader for it).
2. **Where the provider lives.** `learnloop.reader` may not import `learnloop.instructional` (the composition contract), so the provider is `source_retrieval/reader_tutor.py` with `find` injected by the sidecar; the modes are the tutor package's (`tutor/reader_modes.py`, which never imports retrieval).
3. **Abstention is "verification ran and kept nothing"**, or no candidate at all; when verification cannot run (no route, unpriced metered route, cold), nothing is retrieved and no abstention is claimed (the books were not checked). On abstention the validated citations are not shown (their count is kept); the selection passage is still in the tutor's context.
4. **"Another way" that finds nothing new** abstains with its own honest line, *Your books don't explain this another way — this is LearnLoop's model's explanation* (the spec's line would say the books don't cover a question the first answer showed they do).
5. **"That didn't help"'s targets** are the gaps already named on the inquiry's questions (`named_gap` refs); the new "still unclear" text is read by learner-text gaps after the answer, as any reader question is.
6. **Passage LOs.** RW4a's section anchor is often empty; the passage's current `primary`/`support` source links are the fallback.
7. **No session narrative**: nothing on `main` stores one (RW6b's digests have not landed), so the context has none.
8. **Practice offers show items only**, as RW4a's "Practice this question" does; textbook-exercise candidates are RW4b's view.
9. **"Try the next step first"** only on a cited block of the open source (RW1b's fold works on the rendered source); "Make this explorable" is absent (RW5b not on main).
10. **Pending line.** `reader.ask` stays one synchronous RPC, so the two-stage *looking in your books… / writing…* is one honest line, *looking in your books, then writing an answer*.
11. **A bound workbench session** reaches the server only when the Reader names it (the frontend sends the active bound session while either switch is on, fix round 4, F3); there the tutor writes no tool requests and no practice request (its tools would be rebuilt from the reader question under `reading`). The binding is its own value, `BoundAsk` (fix round 5, R1), built whenever either switch is on, retrieval on or off: the question row is stored on the item (its hint counts in the item's window); its hint flag is `BoundAsk.hint_equivalent` (cold: always, whatever the question type and whether or not the cold attempt row exists; otherwise the ordinary classification), stored once and returned as the response's `hintEquivalent`; the item's guard holds for the complete delivered context, cold or not; and every earlier answer in the thread is re-checked under the current binding, alone and combined with the other earlier answers delivered with it, an answer that fails it shown to the tutor as *[An earlier answer is left out while you work this problem.]*, or as nothing when that line itself matches the item's guard (round 5, R2; round 6, R1). Every model-written text a bound request delivers to any model call (the earlier answers, the open-gap and misconception statements of the lookup's query, "that didn't help"'s misconceptions and corrections in the verification's context, the bridge's open questions and problem line) is withheld from one plan that reads each call's union as one (`tutor/reader_modes.plan_bound_delivery` and `withhold_for_call`, round 7, R1); the tutor's thread, the lookup's query and verification inputs, the bridge's work and the manifest are all delivered from it, and the learner's own words are never withheld. The learner field attributes a bound question to the next attempt of its item through the same window rule the count uses (`learnloop/hint_window.py`, round 5, R3), with a zero-mass `bound_question` row it always emits (round 6, R2).
12. **Offers on restored exchanges**: not shown (the lookups would re-run on every source open); the modes are restored while either switch is on, and with both off a saved RW1c answer renders as the base's single model voice (fix round 5, R4).

## 4. Successor

None: retrieval is context, the modes and buttons are display and learner picks (T6's ruling). No evidence, mastery, grading input, scheduling or replay reads anything RW1c writes; a Reader answer's reveal handling is unchanged (none in the reader context). No migration, no new route, no new RPC.

## 5. Tests and counts

New: `tests/test_reader_tutor_retrieval.py` (23), `tests/test_reader_tutor_offers.py` (12), `tests/test_reader_tutor_switch_off.py` (2, golden `tests/fixtures/reader_tutor_switch_off.json`), `tests/reader_tutor_fakes.py`; vitest `TutorOffers.test.tsx` (8), `TutorAnswer.test.tsx` (6), `tutorReader.test.tsx` (2), `tutorSwitchOff.test.tsx` (4, snapshot). Changed: `tests/structured_ai.py` (decodes the Reader lookup context), `tests/test_reader_inquiry_kill_switch.py` (RW1c's keys are not reader_inquiry fields, as `practiceRequest` already was), `tests/test_reader_intent.py` (RW1c off in RW1b's switched-off contract pin, as RW4a's switch already was).

## 6. Files

`src/learnloop/config/{schema,template}.py`, `src/learnloop/params/parameter_registry.py`, `src/learnloop/tutor/{ai_contracts,tutor_qa,reader_modes}.py`, `src/learnloop/source_retrieval/reader_tutor.py`, `src/learnloop/reader/{reader_dialogue,reader_inquiry,reader_report}.py`, `src/learnloop_sidecar/handlers/{reader,reader_tutor}.py`; `apps/learnloop-tauri/src/api/dto.ts`, `screens/ReaderScreen.tsx`, `screens/reader/{AskRail,ReaderAskBranches,TutorAnswer,TutorOffers,useReaderInquiry}.tsx|ts`; `docs/learnloop-architecture-vault/_scripts/db_generate_reference.py` and the regenerated references.

## 7. Open questions (with the default taken)

1. *Default on?* Both switches default on (frictionless defaults). The retrieval costs one `source_rerank` verification per Reader question (plus T6's rewrite when on), under the service's daily cap.
2. *Reader Ask inside a bound workbench session*: retrieval is `assisted_practice`, but the Reader tutor's prompt is still the non-Socratic reader prompt (as today). Default: unchanged (RW2b's help is the workbench's tutor); an owner decision whether the rail's Ask should become the practice-context tutor there.
3. *Abstention line for another way* (§3 item 4). Default: the honest variant.
4. *Offers on restored exchanges* (§3 item 12). Default: not shown.
5. *Personalized toggle in the Reader*: no chip in the Ask composer; the default is `library_ask.personalized_default` (true). Default: no chip until the owner asks.
6. *Abstention hides citations*: default hide (nothing claimed from the books); the alternative is to show the selection's own citation.

## 8. Friction notes for RW4b, RW3b and RW5b

1. **RW4b**: `TutorOffers` shows practice *items* only; a `find_practice` result's `sourceExercises` are ignored there, so RW4b's exercise view should slot into `OfferResult` (practice branch) and its "find an exercise in my sources ▸" belongs beside the plain *nothing in your practice or books fits this yet* line.
2. **RW3b**: the `try_next_step` button and the `▹┆` cue are the same act (`activeCtl.start("next_step", [span], localFold([span]))`); `source_retrieval/reader_tutor.NEXT_STEP_ROLES` (`proof`, `worked_example`) is the role set the cue could share. Named gaps reach "that didn't help" as `named_gap` refs (`named_gap_hypotheses`).
3. **RW5b**: "Make this explorable" goes in `handlers/reader_tutor.offers` beside `next_step_buttons` (a cited `equation`/`figure` block with the feasibility judgment `yes`), and renders as a new `OfferKind` in `TutorOffers` (the press runs RW5a's pipeline with `origin = tutor`); the contract field `reader_tutor` can carry its availability as `try_next_step` does.
4. **All**: `reader.ask` remains one synchronous RPC on the serial sidecar; with retrieval it waits for the verification call too. Moving it to RW4a's job pattern would also allow the true two-stage pending line.

## 9. Owner-run commands

No paid run is needed. To look at it on a copy: `uv run python -c "from pathlib import Path; from learnloop.db.copies import copy_tree_with_databases as c; c(Path('fixtures/linear_algebra'), Path('fixtures-local/rw1c-la'))"`, `uv run learnloop doctor --fix-state --vault fixtures-local/rw1c-la`, then `LEARNLOOP_VAULT=$PWD/fixtures-local/rw1c-la npm run dev` in `apps/learnloop-tauri`. Ask in the Reader: the answer may open with *§ from your books*; under it *another way · that didn't help…* and the buttons. Retrieval needs a ready `source_rerank` route (unset: the active provider); without it the tutor is today's and says nothing about the books. Switches in the copy's `learnloop.toml`: `[reader_tutor] retrieval_enabled = false` (today's tutor), `offers_enabled = false` (no buttons). `uv run learnloop reader report --json --vault <copy>` shows the `tutor` row.

**Model calls made in this stage: none.** Every test uses fakes (`LookupTutor`, `Verifier`/`KeepContaining`/`RejectAll` over `FakeServiceLLM`, `StubReaderClient`); no smoke run on a vault copy was made.

## 10. Gate

Run in the worktree with `TMPDIR` set to `fixtures-local/tmp`, `uv run --no-sync` after the install; `/tmp/learnloop-fullsuite.lock` was free. Targeted only (owner rule 2026-10-17).

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok (pypdfium2 5.14.0) |
| `uv run lint-imports --no-cache` | **28 kept**, 0 broken |
| targeted `pytest -n auto -q -p no:cacheprovider` over the 226 files below | **4,310 passed, 2 xfailed, 2 failed** (11 min 32 s); both failures were `test_reader_intent.py::test_switched_off_the_prompt_contract_is_the_bases` (RW1b's switched-off contract pin did not turn RW1c off); fixed in the test as RW4a's switch was; rerun of `test_reader_intent.py` + the three RW1c files: **64 passed** |
| durability lane | not run: no migration, no DB or connection code changed |
| `npm install`, `npm run typecheck` | ok, clean |
| vitest `src/screens/reader`, `src/screens/ReaderScreen.branches.test.tsx`, `src/screens/ReaderScreen.workbench.test.tsx`, `src/components/SourceOffers.test.tsx` | **52 files, 397 tests passed** (incl. the four RW1c files, `libraryAskSwitchOff`, `intentSwitchOff`, `recapSwitchOff` with their base snapshots unchanged) |
| `npm run frontend:build` | built (the usual chunk-size warning) |
| `cargo check` | not run: nothing under `src-tauri` changed (no new RPC, so no passthrough) |
| `db_generate_reference.py`, `db_validate_reference.py`, `validate_vault.py` | regenerated (head 213, 333 table notes, 919 configuration leaves in 63 sections; `[reader_tutor]` described in the generator); errors []; vault validation passed (1,130 notes, all reachable) |
| contract tests (in the targeted run) | `test_config_refactor.py` (19 snapshots recomputed), `test_cli_help_snapshot.py`, `test_sidecar_serializer_snapshot.py`, `test_desktop_rpc_contract.py`, `test_mobile_allowlist.py` (no new RPC), `test_architecture.py`, `test_instructional_layering.py`, `test_registry_audit.py`, `test_table_roles.py`, `test_coordinated_migrations.py`, `test_tracked_fixture_databases.py`, `test_sqlite_file_copies.py`: pass |

**Not done:** no adversarial (Codex) review in this step; no real-UI look (exercised through the real `ReaderScreen` in jsdom); no vault-copy smoke run.

**The 226 pytest files run** (the new and changed files; every test file naming `tutor_qa`, `reader_dialogue`, `reader_inquiry`, `reader_report`, `tutor.ai_contracts`/`TutorQAContext`, `reader.ask`, `reader.prompt_contract`, the reader handler, `DEFAULTS_SNAPSHOT`/`defaults_fingerprint`, `parameter_registry`, `structured_ai`, `source_retrieval.tutor`, `library_ask`, `config.template` or `LearnLoopConfig`; the contract tests above):

```text
test_ad1_codex_review_fixes test_ad1_fix_round4 test_ad1_migration test_ad1_reading_opportunities 
test_adaptive_difficulty_ad1 test_agent_runs test_ai_config test_ai_runtime test_ai_tool_isolation 
test_architecture test_attempt_ai_flow test_authoring_contract test_blind_grading_contract 
test_blueprint_projection test_capture_desktop test_capture_route_recovery 
test_characterization_mastery_reliability test_chatgpt_plan_provider test_chatgpt_plan_workspace 
test_cli_generate_practice test_cli_help_snapshot test_codex_attempt_flow test_codex_output_schema 
test_cold_start_revision test_concept_animation_service test_config_refactor test_constraint_engine 
test_coordinated_migrations test_daily_loop_reader_authored_practice test_daily_loop_reader_retire 
test_daily_loop_reference_adoption test_decider_landing test_deferred_regrade test_desktop_rpc_contract 
test_diagnosis_input_provenance_landing test_diagnosis_input_provenance test_diagnostic_augmentation 
test_diagnostic_gate test_diagnostic_generation test_dialogue_causal_join test_e2e_codex_mock 
test_embedding_route_isolation test_evidence_config test_exam_protection test_exam_protection_review 
test_exam_seeding test_exercise_authoring test_facet_identity_composition test_facet_locks_landing 
test_facet_reword_confirm_review test_field_config test_field_priors test_field_signal_production_paths 
test_find_sources_intents test_gate_fit test_glm_ocr test_grading_cli test_hint_feedback_texts 
test_hint_outcome test_ingest_m3 test_instructional_layering test_integration_daily_loop_field 
test_item_parameters test_judge_routes test_kinship_feature test_km4_taxonomy 
test_learner_review_system_entries test_learner_text_gaps_composition test_learner_text_gaps_flow 
test_learner_text_gaps test_learner_text_gaps_rereview test_learner_text_gaps_review test_library_ask_expand 
test_library_ask test_library_ask_review test_library_asks_migration test_method_explicit_landing 
test_method_explicit_upgrade test_method_phrasing_report test_misconception_registry test_mobile_allowlist 
test_model_usage_report test_mvp010_upgrade test_mvp011_upgrade test_mvp013_upgrade test_mvp014_upgrade 
test_mvp015_upgrade test_mvp016_upgrade test_mvp017_upgrade test_mvp018_upgrade test_mvp020_upgrade 
test_mvp021_upgrade test_mvp022_upgrade test_mvp023_upgrade test_mvp024_upgrade test_native_media_readiness 
test_openai_chat_client test_openai_embedding_client test_openrouter_video_client test_open_world_gate 
test_output_budget test_p0_cutover_mvp08 test_p2_leakage_suite test_p3_journeys test_persona_gate test_pf_cli 
test_pinned_span_bridge test_placement_opening_probes test_placement_signals test_plan_determinism 
test_practice_leakage test_prescription_passages test_probe_audit test_probe_dialogue 
test_probe_llm_instances test_probe_surface_mint test_project_atomicity test_project_blindness 
test_project_capture test_project_cli test_project_hooks test_project_probes test_project_redaction 
test_project_report test_proposal_persistence test_provider_resolution_parity test_question_context 
test_question_promotion_jobs test_question_promotions test_question_signal test_quick_check 
test_reader_active_reading test_reader_activity test_reader_branches test_reader_compare_table 
test_reader_cues test_reader_dialogue test_reader_find_sources_callers test_reader_formative_texts 
test_reader_guidance test_reader_inquiry_kill_switch test_reader_inquiry_status test_reader_intentions 
test_reader_intent test_reader_observation_records test_reader_passage_check test_reader_progression 
test_reader_quick_check test_reader_recap test_reader_recap_review test_reader_recap_review_r2 
test_reader_reconnect test_reader_reconstruct test_reader_report test_reader_requests test_reader_rw1b_review 
test_reader_rw2b_review test_reader_tutor_offers test_reader_tutor_retrieval test_reader_tutor_switch_off 
test_reader_workbench_rw2a test_reader_wrap_up test_reading_hardening_landing test_reading_step_switch 
test_recall_calibration test_recurrence_commands test_registry_audit test_regrade_contract_successor 
test_regrade_contract_upgrade test_required_method_authority test_required_method_items test_reveal_ledger 
test_router_offer_log test_router_probe_ties test_rw4_kill_switches test_scheduler 
test_self_attributed_misconceptions test_sensitivity_certificates test_serve_eligibility_review 
test_sidecar_animation test_sidecar_reader_p3 test_sidecar_reader test_sidecar_serializer_snapshot 
test_sidecar_source_retrieval test_sidecar_teach_back test_sidecar_trace_and_clarification 
test_sim_teach_back test_simulation test_source_append test_source_ingestion_adapters test_source_ingestion 
test_source_inventory test_source_retrieval_codex_unavailable test_source_retrieval_followup 
test_source_retrieval_guards test_source_retrieval_rereview_cost test_source_retrieval_rereview 
test_source_retrieval_search test_source_retrieval_tutor test_source_set_synthesis 
test_sources_merge_composition test_sqlite_file_copies test_structured_transport_parity test_stuck_prompt 
test_surprise test_t6_followup_review test_table_roles test_teach_back test_tier1_decider 
test_tracked_fixture_databases test_tutor_citations test_tutor_delivery_fixes test_tutor_practice_request 
test_tutor_promotion_service test_tutor_promotion_w2 test_tutor_qa test_tutor_tool_requests 
test_ux_phase1_connect_ai test_ux_phase1_landing test_ux_phase1_usability_round1 test_ux_phase4_feedback 
test_vault_epigraphs test_voi_merge_composition test_voi_stopping test_voi_v2 test_workbench_text_gaps 
```

## Landing onto main

Landed in the `learnanything-merge2` worktree on branch `merge/rw1c-onto-main`, cut from main at `fab576ac1` (the
RW2b + H3 landing, migration head 213). The stage tip is `c8d185b33`, unchanged, and was built on `fab576ac1`, so the
merge had nothing to compose. The orchestrator's last verify (Codex job `20261020-015528-3gpY2e` on `c8d185b33`) is
clean: no High, no Medium. Main was neither fast-forwarded nor pushed here.

**Commits:**
- `7b028edf0`: a `--no-ff` merge of `reader/rw1c` onto `fab576ac1`. No conflicts (the stage's base is main's tip).
- `f18abf518`: the references regenerated on the merged tree (commit labels; 398 files, labels only).
- This record, with the three owner confirmations below.

The landing was interrupted once (after the regeneration, the frontend checks and parity (a)) and resumed. The two
full-suite runs started before the interruption were stopped near the end, with no failure in either log
(`fixtures-local/rw1c-landing-fullsuite.log`, `-fullsuite2.log`); the gate's run is the third, below. Parity (b) was
cut off mid-upgrade; its copies were set aside (`landing-rw1c/stale/`) and (b) was redone from fresh copies.

### Merge and regeneration

- **No conflicts, no migration, no new route, no new RPC.** `reader.ask` gains optional fields; `src-tauri`,
  `migrations/`, `pyproject.toml` and `uv.lock` are unchanged. `migration_head_213` is main's.
- **References.** `db_generate_reference.py`, then `db_validate_reference.py`: **0 errors**, `schema_head` 213, 333
  table notes, **919** configuration leaves (RW1c's two `[reader_tutor]` switches on RW2b's 917; the stage already
  moved the prose counts).
- **Defaults snapshots.** With the config template's `.pyc` cleared, all **19** `DEFAULTS_SNAPSHOT_BY_ALGORITHM`
  entries match (`mvp-0.9` … `mvp-0.27`, recomputed by the stage).
- **CLI help snapshot** (`tests/test_cli_help_snapshot.py --write`): no change. **RPC pins** (serializer snapshot,
  desktop RPC contract, mobile allowlist; the new `reader.ask` fields are desktop-only): pass in the full run, no
  file rewritten.
- **`validate_vault.py`**: passes (1,130 notes, all reachable).
- **Known failures, from before this stage, not fixed:** `desktop_validate.py` stops on
  `components/pdfSelection/testing/syntheticBook.ts` (as at the RW2b landing); `module_validate.py` reports **910**
  issues, up from 900 at RW2b. RW1c adds five modules without module notes (`text_canon.py`, `hint_window.py`,
  `source_retrieval/reader_tutor.py`, `tutor/reader_modes.py`, the sidecar's `reader_tutor.py`); the validator's
  output is truncated, so the ten are not itemised here.

### Gate

Python 3.12.14. `TMPDIR` was merge2's `fixtures-local/tmp`, and every command after the install ran as `uv run
--no-sync`. Both suite lanes ran under `flock /tmp/learnloop-fullsuite.lock`. The AD2+AD3, DL2 and RW4b worktrees
and their processes were not touched. Every test uses fakes. **This is the first full run over the stage's code**:
every stage step and the 12 fix rounds ran targeted tests only (owner rule 2026-10-17).

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok (pypdfium2 5.14.0) |
| `lint-imports --no-cache` | **28 kept**, 0 broken |
| full suite `pytest -n auto` on `f18abf518` | **14,420 passed, 2 xfailed, 0 failed** (26 min 17 s, on a machine shared with three stages' targeted runs; `fixtures-local/rw1c-landing-fullsuite3.log`). The RW2b landing ran 14,032 + its fix |
| `pytest -m durability` on `f18abf518` | **113 passed**, 14,309 deselected (3 min 51 s; `fixtures-local/rw1c-landing-durability.log`) |
| `npm install`, `npm run typecheck` | up to date; clean |
| `npm test` (the whole vitest run) | **144 files, 1,130 tests passed** on the first run. The `FeedbackScreen` flake did not fire |
| `npm run frontend:build` | built (the usual chunk-size warning) |
| `cargo check --manifest-path src-tauri/Cargo.toml` | ok (nothing under `src-tauri` changed) |
| thread, lock and timing tests | all passed on the first run, so none was rerun. The `"8841"` MCP flake did not fire |
| tracked fixtures, worktree | `git status` clean after both lanes and the frontend run, apart from this record and the three confirmation notes; no `-wal` beside a fixture |

No gate fix was needed.

### Parity (backup-API copies; no model call completed)

**Setup** (as at the RW2b landing):
- **Copies.** The owner's `fixtures/linear_algebra` and `fixtures/probability` were copied once with
  `copy_tree_with_databases` from the main checkout into `fixtures-local/landing-rw1c/orig/`; every other copy came
  from `orig/`, or from its upgraded copy `u27/`, through the same helper. `arxiv_v2` was not opened. Both vaults
  start at schema 165, label `mvp-0.8`.
- **Code.** Main's code is `git archive fab576ac1` and the merge's is the merged tree (`src`, `migrations`,
  `pyproject.toml`), each first on `sys.path`; main's archive was re-checked against `main` before use.
- **Environment.** Every run went through `env -i` with only `PATH`, `HOME`, `CODEX_HOME`, `LEARNLOOP_CONFIG_DIR`,
  `TMPDIR` and `LANG`; `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR` were empty directories and still are. No key
  or provider variable was set.
- **Model routes, set before anything ran** (`neutralize3.py`, under each code). Every `AIRoutingConfig` field
  except the opt-in `embedding` / `pf_proposers` / `field_question_classifier` went to `127.0.0.1:9`: chat routes
  (the tutor and Reader routes, `source_rerank`, `hint_writer`, `approach_map`, `hint_outcome`, `workbench_check`,
  `ad_forecast_llm`, `ad_feature_audit`, …) to `blackhole` (`openai_chat`, key variable unset), decider-only routes
  (`hint_chooser`, `ad_forecast_decider`, `tier1_decider`, …) to `blackhole_decider`; the active provider to
  `blackhole`, the fallback cleared; `query_rewrite`, `tutor_query_rewrite`, `tutor_rerank`, `dense` and
  `[embedding]` off; `[learner_text_gaps] enabled = false`; `[hints.maps] build_on_serve = false` and
  `[hints] outcome_placement_enabled = false`. A resolver check over every `AITask` (58 on both codes) found nothing
  outside those two profiles except `embedding` (disabled, keyless).

**(a) Schema and rows, and (b) nothing served changes**

| Check | linear_algebra | probability |
|---|---|---|
| **(a)** open (migrate), main's code / the merge's | 165 → 213 (48) / the same | the same |
| schema, main@213 vs merge@213 | **identical**: 1,414 objects each, none on one side only, no SQL differs | **identical** (1,413) |
| rows of every table (338), all columns | **identical** (16,539 rows); `schema_migrations` differs only in `applied_at` | **identical** (7,637 rows; the same) |
| `foreign_key_check` / `integrity_check`, both sides | 0 / ok | 0 / ok |
| `rebuild --shadow --json` | **0 differences** after normalisation (raw: the marker id and database hashes); facet 0, mastery 2, schedule 8; live database unchanged on both | **0 differences** (facet 0, mastery 1, schedule 1) |
| `doctor --json` | **0 differences** (raw: the copy paths); 57 issues, 1 error | **0 differences**; 101 issues, 48 errors |
| **(b)** at `mvp-0.8`: certification, recipe gaps and curves; the Today queue at a frozen clock (no session, a session, greedy); the daily plan | **byte-identical** (39 facets, 84 points; queue 41; the plan is off below `mvp-0.14`) | **byte-identical** (29 facets; queue 67) |
| upgraded by main's code to `mvp-0.27` (`--to mvp-0.9`, `--to mvp-0.27`, `rebuild-derived-state` twice; all rc 0), then opened by each code | certification and curves **byte-identical** (82 points, 7 corrections; 129,651 bytes); Today queue **byte-identical** (43) | **byte-identical** (cert 17,495 bytes; queue 67) |
| the daily plan at `mvp-0.27` (the sidecar's handlers in process, frozen clock: read, serve, serve again, read; the plan tables, `plan_presentations`, the `plan_block` decisions) | identical except `router_decisions.card_hash`, `snapshot_hash` and the card hash in `detail_json`, which hash a card carrying the plan's ULID. **A second run of main's code differs from the first in exactly these three** | the same |

**(c) The Reader and practice through the real sidecar** (stdio), on copies of probability at `mvp-0.27` (`u27/`).
The sequence:
- `initialize`, `get_config`;
- `reader.prompt_contract`; `reader.ask_history` on `ext_01KYMSJJNJQ0W9QHZ9ZMFD88NY` (3 saved exchanges); one
  `reader.ask` on span `s108`; `reader.ask_history` again;
- `set_grading_provider manual`, `start_session`; one daily-plan serve (`get_daily_plan`, `next_plan_item` with
  `serve` true: `pi_three_independent_birthd`), then a 12 s wait for AD's background jobs;
- on `pi_prob_derive_complement`: `get_practice_item`, `get_probe_contract`, `practice.record_hint_reveal` (authored
  hint 0), `save_practice_draft`, `submit_attempt` with self-grade, the `submissionId` and `difficultyRating:
  "hard"`, then `acknowledge_practice_submission`;
- `submit_dont_know` on `pi_incl_derive_intersections`, acknowledged;
- a hint-free workbench `open`, `get` and `submit` on `pi_story_binomial_translation`;
- `get_session`, `shutdown`.

The runs: (i) main (`ci`, plus `ci2`, main again as the baseline); (ii) the merge with `[reader_tutor]
retrieval_enabled = false`, `offers_enabled = false` (`cii`); (iii) the merge at the defaults (`ciii`).

| Check | Result |
|---|---|
| every response (24 calls + `shutdown`), (i) vs (ii) | **identical**: 11 raw-identical, the rest identical after normalisation (ULIDs, timestamps, the copy path, `initialize`'s schema-head fields), exactly as main against main again |
| (i) vs (iii) | the same, **except one key**: `reader.prompt_contract` gains `readerTutor` = `{retrieval: true, offers: true, anotherWay: true, personalizedDefault: true, tryNextStep: true, manifestIncludes: [the verified book passages after the selection; when personalized, the learner's open questions and recent workbench steps on the passage's learning objects]}`. Every other contract key is equal, and `initialize`'s method list is unchanged (no new RPC) |
| `reader.ask` (route unreachable) | the **same error** in all three runs, raw-identical: `-32001`, `provider_unavailable`, retryable, *"AI provider blackhole is unavailable for reader Ask."*; `reader.ask_history` still returns the 3 saved exchanges, raw-identical |
| the database delta | (ii) and (iii) differ from (i) only in tables where `ci2` (main again) also differs from `ci`: wall-clock floats in `attempt_debug_payloads`, `scheduler_explanations` and `scheduler_slate_candidates`; the router card hash in `attention_block_events`; AD's background rows (`judgment_ledger` uuids, `item_forecast_payloads` request hashes). (iii) also differed in `judgment_work_claims`: AD's feature-audit claim had `lease_epoch` 2. That is timing, not RW1c (below). No question, interaction, exposure or receipt row differs, and no merge-only table or column was written |
| the attempts, all runs | **identical** evidence fields: the `open_text` attempt has `hints_used` 1, `primed` 0, correctness 1.0, `difficulty_rating` hard, assisted, not certifying; the `dont_know` is recorded as stuck (`declared_stuck` 1, scored 0), `hints_used` 0; the workbench attempt (`desktop_practice_workbench`) has `hints_used` 0, `primed` 0. The activity classes are the same, there are 0 `reveal_events` rows, and one `help_assists` row (the client-counted authored reveal, level 3, attached to the first attempt) |

**The `lease_epoch` check.** Ten more runs (`ci3`-`ci7` on main, `ciii2`-`ciii6` at the merge's defaults; six with
a trace of AD's preparation passes) give `lease_epoch` 2 on **3 of 7 main runs** and **1 of 6 merge runs**. It is 2
exactly when AD's background preparation runs a second pass over the served item, which re-claims the unsettled
feature audit. The attempts were identical in every run.

**(d) The learner field and the hint report** (`hint_window.py` and `field/signals.py` changed). Main's and the
merge's code each read the same copy, read-only:

| Copy | field replay rows (attempts, facets, signals with types) | `field data-check --json` | `hints report --json` |
|---|---|---|---|
| linear_algebra at `mvp-0.27` | **byte-identical** (70 attempts, 82 facets, 15 signals) | **byte-identical** | **identical** apart from `generated_at` |
| probability at `mvp-0.27` | **byte-identical** (2, 2, 20) | **byte-identical** | **identical** apart from `generated_at` |
| (c)'s `ci` after its practice | **byte-identical** (5, 7, 21) | **byte-identical** | **identical** apart from `generated_at` |
| (c)'s `ciii` after its practice | **byte-identical** (5, 7, 21) | **byte-identical** | **identical** apart from `generated_at` |

Neither vault has a bound Reader question, so the bound-question window rule (`hint_window.py`) has nothing to move,
and nothing moved.

**`model_call_receipts` across all 34 learner databases** under `landing-rw1c/` (every copy, run and base backup;
the 34 other `state.sqlite` files are probability's empty `.learnloop/state.sqlite`): **0 rows**, so none
`completed`.

### New findings

- **Behaviour to know, not a defect, and not RW1c.** AD's feature-audit work claim ends at `lease_epoch` 1 or 2
  depending on whether a second background preparation pass ran over the same served item (main 3 of 7, merge 1 of
  6). Nothing served or counted depends on it.
- No real failure in the full suite or the durability lane; no gate fix.

### For the owner

- **No migration and no `--to` command.** Nothing served changes (parity (a)-(d)).
- **What you see in the Reader's Ask.** The answer may open with *§ from your books*: a short quote from one of your
  books, checked against the passage. Then *◇ LearnLoop's explanation*, and, when you have work on the passage's
  topics, *◇ connecting it to your work*. When your books don't cover the question, it says so and the explanation
  is labelled as the model's. Under each answer: *another way* (a different passage, never one already shown) and
  *that didn't help…* (asks *What's still unclear?*). Then the buttons: practise, a passage, a comparison, and *try
  the next step first*. Nothing is looked up until you press. While it works, the line reads *looking in your books,
  then writing an answer*.
- **Cost and speed.** Retrieval makes one `source_rerank` verification call per question, on the active provider
  unless routed (Codex in your vaults: slower). For speed, route `ai.routing.source_rerank` to a fast profile, e.g.
  the ChatGPT plan or a priced OpenRouter route. Without a ready route, the tutor is today's and says nothing about
  the books.
- **Turning it off:** `[reader_tutor] retrieval_enabled = false` (today's tutor) and `offers_enabled = false` (no
  buttons). With both off, the Reader is byte-identical to before (parity (c)(ii)).
- **Open questions (§7; defaults taken):**
  1. on by default: yes, both switches;
  2. the Reader Ask inside a bound workbench session keeps the non-Socratic reader prompt;
  3. *another way* that finds nothing new uses the honest abstention line;
  4. offers are not shown on restored exchanges;
  5. no *personalized* chip in the Ask composer (`library_ask.personalized_default`, true);
  6. abstention hides citations.

### Open items

- **F9 (High, inherited, non-blocking):** the same-second boundary between a question and an attempt. It is queued
  as its own follow-up, **durable sub-second event ordering across question/attempt/hint ledgers**.
- **Accepted, Low:** a stem-alone leak through item authoring (item authoring's to fix). **Accepted:** book passages
  outside a call's union are guarded per span.
- **RW4b:** the `TutorOffers` exercise hook (§8 item 1) lands with RW4b.
- `desktop_validate.py` (`syntheticBook.ts`) and `module_validate.py` (910 issues), both from before this stage.

### Owner confirmations recorded with this landing (2026-10-20)

The owner wrote: *"q1: no switch, q44: end it honestly with no replacement, q45: yes it ends the check. for rw6a yes
to defaults"*. Each is noted next to its question:
- `docs/reviews/regrade-contract-replay.md`, Q1 (§2.6, §9, open item 1): no kill switch for the mvp-0.26 regrade;
  rollback means restoring the backup.
- `docs/reviews/serve-eligibility-decision.md`, Q44 and Q45: a withdrawn cold check ends honestly, with no
  replacement surface (no follow-up stage); practice after a check is scheduled ends the check (as built).
- `docs/reviews/reader-workbench-RW6a.md` §6: all six defaults, plus *abandoned problems stay*
  (`reader-rw6a-codex-review.md` F8).
