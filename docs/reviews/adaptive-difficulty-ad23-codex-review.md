

## Fix round 11: the whole-pipeline differential contract (2026-10-20)

Codex's verify of round 10 (codex-job `20261020-124929-uzJT57`, verdict REOPENED) confirmed:

- R3, R4, R6 and R7, and the structural dispatch test;
- the owner defaults, A17's `0.25`, migration 214 and the head fixture;
- the 7-day expiry, and that cancelled work is never requeued automatically;
- that no forbidden writer exists;
- that boundaries (a) `ad data-check`, (b) the legacy completed-probe gate and (c) the
  `mastery_ekf` comparator carry no High.

It found four Highs (F20 reopened, F34 reopened, F37, F38) and a Medium (F39). All five are A8
readers outside the material view. After ten rounds of finding such readers one at a time, the
orchestrator's rulings are:

- R1: fix the five;
- R2: make the contract a whole-pipeline differential that catches the next reader.

Commit `ecd7e6652` implements both, with no migration change.

| Id | Severity | Title | Origin | Verdict | Commit | Caught by the differential as |
|---|---|---|---|---|---|---|
| F20 | High | Protected historical reveals still affect AD eligibility | stage (the slot's check 0 and the frozen `pre_exposed`, through the incumbent's reveal reader) | fixed | `ecd7e6652` | `pi_p4` failing `pre_exposed` and `recent_reveal` in the slot's estimates and the selections' `excluded` |
| F34 | High | Guarded repairs still accept newly protected grounding spans | round 10's guard (item tokens only) | fixed | `ecd7e6652` | a request dispatched after the late span was held out quotes it (the cited request's repair); the cross-source and cited repairs not refused |
| F37 | High | Goal generation still uses protected incumbent evidence to choose prompt focus | inherited (`goal_report`), made live by the contract path | fixed | `ecd7e6652` | the goal request refused in A (its focus named the protected-only facet), sent in B |
| F38 | High | Saved relatedness loadings retain protected-only facets | stage | fixed | `ecd7e6652` | with learned coupling on: the frozen loadings, forecasts and scores naming `SENTINEL_FACET_AX9`, and the judgment ids frozen with them |
| F39 | Medium | Protected selections still change report counts and windows | stage | fixed | `ecd7e6652` | the report's and `ad report`'s serve draws, mode shares, time to usable, commission draws and prior-sensitivity cohort |

### What changed (R1)

- **F20, exposure.** `serve_inputs.pre_exposed(..., view=)` gives the incumbent's rule
  (`serve_eligibility.submit_exposure`) the view's reveals of the item or its LO, and the item's
  last visible attempt as the window's opening. Both AD callers use it: the slot's check 0 and the
  frozen `pre_exposed` of the serve inputs.
- **F20, recent reveals.** The slot's exclusions (`ad_slot._exclusions(env, view)`) take the
  recent-reveal set with the view's withheld reveal ids left out
  (`MaterialView.withheld_reveal_ids`). Two new optional parameters carry this,
  `out_of_timing_serving_exclusions(exclude_reveal_ids=)` and
  `items_revealed_between(exclude_ids=)`; omitted, both read exactly as before, so the incumbent
  is unchanged.
- **F34, grounding identities.** A commissioned request's guard now revalidates source identities
  against fresh protection at every dispatch, the repair included. It checks two sets:
  - its context's source refs (`proposals.context_sources`: each ref's extraction and spans);
  - the grounding spans the generator registers (`CommissionedRequestGuard.ground`). The
    cross-source generator registers every `CROSS_SOURCE_CONTEXT` span through
    `_ad_request_options(plan, grounding=)`.

  A span held out since the request was built refuses the request, whether or not any item
  derives from it.

  The guard protocol gains a `sources` keyword, which `_check_request` passes. The repair pass
  replaces the instructions, so a cross-source repair does not re-quote its spans. It is refused
  anyway: the ruling revalidates every grounding span at each dispatch.
- **F37, goal focus.** Under the contract, `build_goal_practice_plan` takes its focus from
  `adaptive_difficulty.generation.goal_focus_facets`. This returns the visible facets of the scope's
  LOs whose AD forecast of an unassisted success at the retrieval entry point is below the goal's
  `target_recall`. The forecast is AD's own state on visible evidence. The predecessor path keeps
  `goal_report`.
- **F38, loadings.**
  - `relatedness.load_structure` revalidates each saved revision unit. A revision that is withheld,
    judged by its own sources (`MaterialView.revision_hash_withheld`), has no unit. A loading onto
    a protected-only facet is dropped (`MaterialView.visible_loadings`).
  - The replay revalidates frozen `loadings_json` the same way.
  - `serving.frozen_loadings` freezes only the judgment ids behind the loadings still in force.
  - The ledger and the frozen rows are never rewritten.
- **F39, the selection cohort.** `MaterialView.selections(kind=)` leaves out three kinds of
  selection:
  - a draw that chose a withheld item;
  - a draw into a presentation withheld with its frozen revision;
  - a commission of a protected-only facet's cell.

  The report's selection statistics, its window boundaries (`readiness_errors`), its prior
  sensitivity and "why this item" all read through it. `MaterialView.open_commissions` drops the
  same commissions. The ledger is unchanged.

### R2, the differential contract

`tests/test_ad23_contract.py::test_protected_material_is_indistinguishable_from_absent_material`
is parametrized `default` (the owner's `learned_coupling` off) and `coupled`. The module docstring
lists the fixture's protected classes: every class the verifies named, including those added
this round. AD's full pipeline runs on each copy:

- the plan serves with the slot draw and an answer;
- the replay, its rebuild and the score rebuild;
- the outside forecasters, as `llm_v3` dispatched from the serves' frozen inputs;
- item preparation (the feature audit, then `llm_v1:item`);
- generation and commissions:
  - the commission draw with commissioned post-probe generation;
  - goal generation and cross-source generation, each with its repair request;
  - a Reader-cited post-probe generation with its repair;
  - the cross-source and cited requests see a grounding span held out while in flight;
- relatedness, readiness and the router card;
- the dose arm with late uptake callbacks;
- the reading sweep;
- the report, `ad report` and `ad eval`.

**What is compared.**
- every prompt captured by the fakes;
- the new rows of every table (`sqlite_master`, not a hand list), apart from nine incumbent
  tables (`OUT_OF_SCOPE`, each named with its reason; no AD module reads any of them):
  - the incumbent's answer pipeline: `attempt_completion_work`, `attempt_debug_payloads`,
    `attempt_surprise`, `hypothesis_recurrence_state`, `learning_object_mastery`,
    `learning_outcome_labels`;
  - its item-state sync: `practice_item_state`, `facet_recall_state`,
    `facet_capability_evidence`;
- the DERIVED replay tables, whole;
- every returned figure.

The test fails on any difference, on any sentinel in a captured request, and on any request
dispatched after a span was held out that quotes it.

**Construction of B.** B is the copy where the protected material was never written: physically
absent, and so is everything derived from it, the incumbent's state included. A copy with the rows
deleted afterwards would keep incumbent state computed from them. That would hide exactly the
F21/F37 class (an AD decision reading incumbent evidence).

**Normalisations** (the complete list):
1. Wall-clock stamps with sub-second digits (`WALL_CLOCK`): the model-call records' own clock.
2. The report's `protection` disclosure block and `generated_at` (`DISCLOSURE`).

Every other id and stamp is made identical at the source:
- ULIDs and uuid4 ids (the judgment ledger, the model-call records) mint per stage from fixed
  counters;
- the clocks are frozen;
- both copies run at one root path, so a hash over `vault_root` matches.

**Carve-outs**, each excluded at its one field by name (`_carve_outs`, `INCUMBENT`): the
incumbent's `mastery_ekf` comparator. Its receipt rows are left out, and the copy of it that
`llm_v3`'s frozen state quotes (`outside._incumbent_inputs`) is pinned to one value in both runs.
This follows round 9's boundary, the round-10 verify's judgment (c) and R2. `ad data-check` is not
in the pipeline.

**Stage coverage** is asserted too, so that nothing is equal by being absent:
- `pi_p4` is a slot candidate;
- the goal request and its repair are both made;
- the public and late grounding texts reach their first requests;
- forecasts and preparation run.

The per-reader tests of rounds 9 and 10 stay.

**Fail-before** (`git archive e005188fe` into `fixtures-local/ad23-r11-base`, `-o pythonpath`,
counted with `AD23_CONTRACT_DIFF`):

| Config | Distinct violations on `e005188fe` | At the tip |
|---|---|---|
| `default` | **31** | 0 |
| `coupled` | **41** | 0 |

By finding:
- **F20:** `pi_p4` fails `pre_exposed` and `recent_reveal` in both serves' estimates and in both
  selections' `excluded`.
- **F34:** the cited repair quotes the late-protected span, and neither the cross-source nor the
  cited repair is refused.
- **F37:** the goal request is refused in A (its focus named the protected-only facet) and sent in
  B. The proposals, agent runs and prompts differ with it.
- **F39:** 9 figures in the report and 9 in `ad report` differ (serve draws 3 against 2, band
  share, time to usable, answers before band, commission draws, prior sensitivity).
- **F38** (`coupled` only): the frozen loadings and the judgment ids frozen with them name
  `SENTINEL_FACET_AX9`, and the serve receipts' `p`, their inputs and the scores differ.

The stage-coverage assertion also fails (the goal request is never made in A).

### Behaviour changes worth knowing

- Under the contract, a goal's generation focus is AD's forecast against `target_recall`, not the
  incumbent's goal projection.
- A cross-source or cited commissioned request is refused when a span it grounds in, or cites, is
  held out before any of its dispatches. This includes a repair that would not re-quote it.
- A commission of a protected-only facet's cell is not open.
- With learned coupling on, a protected-only facet carries no loading, saved or frozen.

### Gate (this round; owner rule 2026-10-17: targeted only)

| Step | Result |
|---|---|
| `uv run lint-imports --no-cache` | 27 kept, 0 broken |
| `test_ad23_contract.py` with `test_ad23_fix_r9.py`, `test_ad23_material_view.py`, `test_ad23_fix_review.py`, `test_ad3_dose_arm.py` | 54 passed (the contract file: 15 tests, the differential in both configurations) |
| targeted pytest, `uv run pytest -n 16` over 158 files: round 10's 157 and every test naming `out_of_timing_serving_exclusions`, `items_revealed_between`, `pre_exposed`, the goal or cross-source generators, `load_structure`, `frozen_loadings`, `why_for_presentation`, `open_commissions`, `serving_exclusions` or `reveal_events` | **8,425 passed, 36 xfailed, 6 failed** (1,649 s) |
| the six failures | all in `test_ad2_serving.py`: test doubles of the private `ad_slot._exclusions(env)`, whose signature gains the slot's view; updated to `(env, view)` |
| rerun: `test_ad2_serving.py` | 34 passed |
| `--durable-sqlite`: `test_ad23_contract.py`, `test_ad23_fix_r9.py`, `test_ad23_fix_r8.py`, `test_ad23_migration.py` | 39 passed |
| references: `db_generate_reference.py`, `db_validate_reference.py` | 0 errors (commit labels; no schema change) |
| migration 214, defaults snapshots, CLI help, vitest, `cargo check` | unchanged or not applicable (no frontend change) |

### For the next verify

The differential test is now the contract. A finding should name an AD reader the pipeline
reaches, together with a class of protected material the fixture lacks. Adding that material to
`_protect` should then make the test fail. The incumbent tables left out of the comparison are
listed in `OUT_OF_SCOPE`, each with its reason.
