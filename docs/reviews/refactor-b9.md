# Refactor B9: one entry point, acceptance

Step B9 of `docs/specs/refactor_strategy_v3.md` (§2.4, arc B; the entry point of §3.5 and the acceptance of §3.6). Branch `refactor/b9-entry-point`, based on main `4faa750dd9` (B1-B7 landed). B8 ran in parallel in its own worktree; B9 edits none of its record writers and not ADR-017's inventory section.

**Result.** One reader, `learnloop.why.reader.answer`, now answers "why x and not y" for every surface: `learnloop why`, the sidecar's new read-only `why.get` RPC, and `learnloop router trace` and `trace-evidence` as views over it. For each decision it gives what was chosen, the alternatives with their chances and losing rules, the inputs as of then, who decided with versions and seed, what came next and what was discarded. Decisions older than their records answer through a new reader of the old rows, `learnloop.why.reconstructed`, and every such answer is labelled `reconstructed`, with the fields found only by time-ordering named `inferred`. On a fresh backup-API copy of the owner's Nov 9 backup, all four of §3.6's real cases answer from `why --json` alone (below). B9 writes no record and changes nothing served: it's reads, two read helpers on the leaf, one RPC and a widened late-answer rule.

## What was built

| Piece | Where | What it does |
|---|---|---|
| The reader | `src/learnloop/why/reader.py` | `answer(repository, target, kind=, first_build=, loaded=)`: the records `target` names (B1's `provenance.read`), their traces' calls, `discarded`, `unclaimed`, and per record a `decisions` entry (`chosen`, `rule`, `alternatives`, `inputs`, `decided_by`, `versions`, `seed`, `error`, `next` = the records naming it as parent, `outcome` = its `router_outcomes` row, `objective_trace` = its router objective trace's ids, `discarded`); `attempt:<id>` adds `evidence` (the A6 observations as ids and codes); `--first-build` adds `first_build`. Falls back to `reconstructed` only when no record answers |
| The old-row reader | `src/learnloop/why/reconstructed.py` | A router decision (by id, `block:`, `offer:`, `decision:` or `latest`): its row, each model's status, the mix's alternatives, the inputs it kept, versions and seed, its calls joined by the boundary key (`owner_id`), each with `output` present or `output_absent_reason` (`failed`, `interrupted`, `never_finished`, `pruned`), the calls that finished after it (`discarded`, inferred), its outcome, responses and the plan's next decision (inferred). An offer's `expired` response as `offer_withdrawn`: the forced items from the next decision, each with its workflow (or the generation job and need it came from), the workflows opened and jobs finished while the offer waited (all inferred). An `interactive_figures` row as `figure_author`: its verification reduced to typed codes (`prediction_invalid`, `verification_failed`, `spec_invalid`) and schema paths, prompt version, model, request, and author calls (owner `figure:<content_key(input_hash, generation)>`, the generation a recount, inferred). `--first-build` over `figure_prefetch_decisions`: the skips before the first build and the first non-skip, overall and per trigger kind, the last skip, the first build, what changed, the first measured latency, and whether it falls between |
| `learnloop why` | `cli/app.py` | A thin view: `--first-build` and `--payload` added (compatible additions; `tests/cli_surface.json` unchanged). `--payload` reads each named call's prompt and output from its receipt (`reader.payloads`); the desktop CLI is its only caller. Text output prints the reconstructed answers, the first build, "answered N s late, discarded", and the payloads |
| `why.get` | `learnloop_sidecar/handlers/why.py` | The same answer on a read-only attach, through `reader.codes_only`: every string that isn't an id, a number or a code is dropped and its path listed in `withheld` (an item's plain-English reasons). Never a payload. Returned without `versioned`'s camelCasing, which would rename data keys (rule codes, option refs). Registered through `METHOD_REGISTRY` (`handlers/__init__.py`); not on the phone allowlist |
| `router trace` | `cli/router.py` | Reads through `reader.objective_trace` (same output contract, same errors); `why`'s answer for a router decision names the same trace (`objective_trace`) |
| `trace-evidence` | `cli/app.py` | Reads through `reader.evidence_report` (same output); `why attempt:<id>` shows that attempt's observations |
| Read helpers | `provenance.read_children`, `provenance.read_kind` | What happened next (records by `parent_id`, any trace) and every record of a kind in order (`--first-build`). Reads; outside the replay closure's allowed names, which the replay test already pins |
| Late answers | `db/stores/provenance.LATE_ANSWER_KINDS` | Adds `followup_gate` (B5's open item). Its record is written just after its draw, so `late_ms` is a lower bound and a call finishing between the draw and the write is missed; nothing on time is ever called late |
| `why item:<id>` | `reader.scheduler_explanation`, `item_exclusions` | B3's finding: a malformed stored value (a cold follow-up's `context_json`) raised `JSONDecodeError` and exited 1, on main too. It now answers `source = "unavailable"` with `explanation_error` (the class, `module:function:line`, and the rows holding invalid JSON by table, id and column, found with `json_valid`), plus the item's records and slates |

## Records added

None. B9 is the reader; B2-B8 write the records.

## The failure each answers

| Gap | Before B9 | Now |
|---|---|---|
| An old decision (before migration 253) | `why <router decision id>` answered `not_found`; its calls were reachable only by a hand-written JSON join from `detail_json.mixture.boundary_key` to `owner_id` | `reconstructed` answer with the join, the late calls and the next decision, labelled |
| An offer withdrawn before B3 | Only the `expired` row's `forced_items`; which item, from where, and what came next took time-ordering by hand | `offer_withdrawn` (reconstructed) naming the forced item, its workflow or generation job, and the next decision, with the inferred fields named |
| A figure failed before B4 | The report's free text only | Typed codes and schema paths, prompt version, model, author calls |
| Pre-builds before B4 | Counting skips by hand | `--first-build`: counts per trigger kind, the measurement and whether it falls between |
| `why item:<id>` on malformed stored context | Exit 1, `JSONDecodeError` | Degrades, naming the bad row |
| The follow-up gate's late answers (B5) | Not listed | `discarded` |
| A glass-box view for the UX stage | No RPC | `why.get`, codes only |
| `router trace`, `trace-evidence` | Separate code | Views over the reader |

## Proofs

**§3.6 test 1, staged (`tests/test_why_cases.py`, 5 tests).** Each case through the code path that made the real one, on a synthetic vault, every model a fake, every assertion on `why --json`:
- case 1: a slow LLM past a 0.3 s wait: `plan_block` with `timeout_s`, `prefetch_timeout_s`, `waited_ms`, alternatives with `p` and `lost_by`, versions and seed; the `router_llm` `model_answer` with `timeout`, named in the block's `next`; the late receipts under `discarded` with `late_ms > 0`; the text "s late, discarded"; `--payload` showing the late router call's prompt and answer, plain `--json` none;
- case 2: a probe made ready while an offer waits: `offer_withdrawn`/`forced_items`/`plan`, parent the offer's `plan_block`, the forced probe with its workflow and source attempt, and the next `plan_block` naming it as parent;
- case 3: a figure stored failed (both attempts `verification_failed`, typed codes, prompt version, model, `interactive_figures` detail) and a bad prediction dropping only itself (`prediction_dropped`);
- case 4: two skip passes, a measured press, a build pass: `--first-build` gives the last skip (`no_measured_latency`), the first build (`sampled_eu_positive`), `changed.waits_n = [0, 1]`, `changed.wait_basis = ["none", "author_call"]`, the measurement's receipt and `measurement_between = true`, with EU, wait, cost, p_open, propensity and seed on the records.

**The reader (`tests/test_why_reader.py`, 20 tests).** Each of the four cases staged as above, then aged to what a vault below 253 holds (`decision_records` dropped, every receipt's `trace_id` nulled), answers through `reconstructed` with the fields above; problem-code classification; a native answer has nothing reconstructed beside it; an unknown target is still `not_found`; `why item:` names the malformed row; `why.get` returns codes only, never a planted prompt, withholds an item's reasons and names them, refuses an unknown target; `why.get` is registered and not on the phone allowlist (also pinned in `tests/test_mobile_allowlist.py`'s desktop-only parametrization); the handler names no payload; `codes_only`; `router trace` and `why` name the same objective trace; `trace-evidence` and `why attempt:` read the same observations; a follow-up gate's late call is discarded; `why` with the new options is still a pure read (a digest of every row before and after); `why goal:<id>` and `why lesson:<id>` resolve (B8's records name both subjects; the orchestrator's addition: `goal` and `lesson` joined `provenance.SUBJECT_KINDS`).

**Fail-first.** On main's code (`4faa750dd9`'s `src`, `migrations`, `tests` from `git archive`, under gitignored `fixtures-local/`): `why item:<id>` with a malformed cold follow-up context exits 1 (`JSONDecodeError`), and the follow-up gate's late call is not listed (`discarded == []`); both pass on this branch. On the real copy, main's `why <the Nov 7 decision>` answers `not_found` (exit 1), `why offer:<the Nov 8 offer>` and `why figure:<a Nov 8 figure>` answer empty records, and `--first-build` is an unknown option (exit 2). Before `goal`/`lesson` were subject kinds, `why goal:<id>` was read as a trace id and fell through to `not_found`.

**§3.6 test 2, real rows (`tests/test_why_real_cases.py`, marker `owner_vaults`).** Run on fresh backup-API copies of `~/learnloop-backups/20261109-copy` (`copy_tree_with_databases(database_names=("state.sqlite",))`, the stale `probability/.learnloop/state.sqlite` removed) under `fixtures-local/why-cases/` with `LEARNLOOP_OWNER_VAULTS` pointed there; all three at migration 250, read in place read-only (no migration, journal headers unchanged by conftest's check). **6 passed**, twice (before and after the last edits, the same report). Ids and field names only:

| Case | Found by | What the reconstructed reader gave (field names and counts; the ids are in the step's report, not here) |
|---|---|---|
| 1 | the first Nov 7-8 `router_decisions` row with `models.llm.status = timeout` | `plan_block`, `components.llm.status = timeout`, 2 calls joined through `inputs.boundary_key`, both `output = present`, both `discarded` with `late_ms` about 1.5 s; `inputs.timeout_s_basis = not_stored`; `inferred` = `discarded`, `next.next_decision` |
| 2 | the Nov 8 `expired` response with `withdrawn = forced_items` | `offer_withdrawn`/`withdrawn`/`forced_items`, `parent` = the offer's `router_decisions` row; one forced item (origin `followup`) with no workflow of its own, so `generated_by_job` and `need` name the generation job it came from; one workflow in `opened_between` (settled) with its source attempt; `next.next_decision` present; all labelled inferred |
| 3 | the 11 Nov 8 `interactive_figures` rows with `verification = failed` | every one `figure_author`/`failed`, `rule = prediction_invalid` (11 of 11), one schema path in `problem_paths` (`predictions.0.change.param`), 4 author calls each, prompt version and model present |
| 4 | `why --kind figure_prebuild --first-build` | `skips_before_first_non_skip = 12` (**is 12: yes**), equal to `skips_before_first_build`; per trigger kind 11 `section`, 1 `offer`, 0 `gap`; the first measurement is the first completed `figure_author` call, and **it falls between the last skip and the first build: yes**; `changed` = `cost_minutes`, `p_open_content`, `posterior_digest`, `propensity`, `sampled_eu`, `w_minutes` |

So §3.6's hypothesis for case 4 holds on the rows: no constant of 12 exists; 12 is the number of candidates decided before the first measured build latency, and EU turned positive (cost 0) once one existed. `why latest` on the `linear_algebra` and `probability` copies also answers (2 more tests).

**Verify (no-code reader).** The plain `why --json` outputs the real-case run used, and the questions, are in the step's scratch directory for the orchestrator (`reader-handoff/`: `case1_why.json` to `case4_why.json`, `pastbug4_why.json`, `QUESTIONS.md`). Not tracked.

**P-draw / P-shadow.** Not required: B9 touches no router decision code (the router's code paths, the plan engine and the choosers are unchanged; `cli/router.py`'s `trace` is a read view), writes no record and no table, and adds no migration. `LATE_ANSWER_KINDS` is read at `why` time only.

## Tests

- **Targeted lane** (`-n 4` under the 5 GB scope, six chunks, sharing the full-suite lock): `scripts/affected_tests.py` (run under the env-isolated wrapper) on the source and test diff selected 954 files, plus `test_provenance`, `test_architecture`, `test_cli_help_snapshot`, `test_cli_json`, `test_effective_defaults_golden`, `test_desktop_rpc_contract` and the B2-B7 record tests: 955 files, **16,633 passed, 1 failed, 64 skipped, 5 xfailed**. The failure was `test_e0_isolation::test_the_import_linter_contract_names_every_production_package`: a new top-level package must join the experiments contract's `source_modules` (`pyproject.toml`), fixed. A `pyproject.toml` change makes the selector fall back to the whole suite, so the 955-file lane stands in for it, as the brief allows.
- **Rerun after the fix and the subject kinds** (the why files, `test_e0_isolation`, `test_provenance`, the CLI contract files, `test_mobile_allowlist`, `test_architecture`, `test_effective_defaults_golden`, `test_desktop_rpc_contract`, the B2-B7 record tests, `test_decision_records_migration`): **532 passed, 6 skipped**.
- The owner lane: 6 passed (above).
- `lint-imports --no-cache`: 43 kept, 0 broken. `ruff check src tests scripts`: clean.
- Vault: the four validators pass; the references were regenerated once after the source commits (one generator input changed first: `module_generate.py`'s package description for `learnloop.why`, committed alone) and a second run changed nothing (0 files).

## Open items

- **`why.get` has no frontend.** The UX stage draws it; the Tauri command list, the Rust passthrough and `client.ts` don't name it yet (`tests/test_desktop_rpc_contract.py` checks only names the frontend calls).
- **`timeout_s` on old rows.** The configured router wait was never stored before migration 253; old answers say `timeout_s_basis = "not_stored"` and give the setting now (`timeout_s_now`), which may differ from the day's.
- **Reconstructed forced items from a need.** A probe generated from a recorded need has no workflow; the reconstructed answer names the generation job and need when exactly one finished in the window, else lists the window's jobs and workflows for the reader.
- **The reconstructed figure calls** rely on the generation recount (`builds_for_input` at the time); a figure whose earlier builds were deleted would recount wrong. Labelled inferred.
- **The Nov 8 figures' typed reason.** All 11 failed on a pydantic schema path inside a prediction (`predictions.0.change.param`), which failed the whole spec then. Since `214c206ff1`, `spec.parse_salvaging_predictions` validates each prediction alone and drops a failing one, so today the same answer is `prediction_dropped` (case 3's second staged test). B4's `prediction_invalid` regex reads the compiler's `prediction N:` form; the reconstructed classifier reads both forms, because old reports hold the schema path.
- **B8 merged.** Main with B8 (`f8c26c4da1`) was merged into this branch; only generated notes conflicted, and they were regenerated. After the merge the rerun files plus `test_remaining_decision_records` and `test_ad23_contract`: 572 passed, 6 skipped. `goal` and `lesson` as subject kinds also mean `refusal_records`' Decider judgment record now takes a `goal`/`lesson` left side as its subject (it does so for any subject kind): a record field only, no decision. No B8 record was read through `why` on a real copy.
- **New top-level package.** `learnloop.why` joined the experiments contract's `source_modules` in `pyproject.toml` (`test_e0_isolation` requires every production package there).
- **B1's other items stand:** retention's trigger relaxation.

## Unverified

- The desktop app and the phone host weren't run (no GUI by rule). `why.get` is exercised through `METHOD_REGISTRY` with a real `SidecarContext`; the phone's refusal through its allowlist.
- The durability lane (WAL) wasn't run for the new tests; B9 only reads.
