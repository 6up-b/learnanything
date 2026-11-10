# Refactor A5: a bug-finding linter in every gate

Step A5 of `docs/specs/refactor_strategy_v3.md` (§2.3). Branch `refactor/a5-ruff`, based on main `9a623e3d9c` (A1, S0, A2, A3 and A4 landed). `ruff check` is clean on the tip and joins every gate beside `lint-imports`. No behaviour change in `src`: no finding turned out to be a live bug, so there is no behaviour-fix commit and no fail-first test. Every edit is either ruff's own safe fix, an explicit `strict=` that cannot fire on the lengths the code builds, a deleted dead assignment, a corrected annotation, or a `noqa` with its reason.

## Order, as the strategy sets it

1. **The `LOG` bug** at `diagnosis/probe_instance_generation.py` was already fixed on main by `cf45777002` (`LOG = logging.getLogger(__name__)`, with its test in `tests/test_followup_reserved_only.py`). Confirmed an ancestor of the base and skipped.
2. **Config, then one mechanical commit.** `bd1d6302cc` adds ruff and `[tool.ruff.lint]`. `70acea4cbd` marks the imports the fix would wrongly remove (below). `856d252438` is `ruff check --fix` (safe fixes only) and nothing else: 307 files, 229 insertions, 538 deletions.
3. **Every remaining finding read** (one commit per rule family): `da0975feaf` B905, `f32e99725a` B023, `2b60eb4fec` F841, `15ce78a634` the rest.
4. **Gates**: `14722beef0`; references regenerated once on the committed source: `f09f257e05`.

## Rules chosen, and why

`pyproject.toml`, `[tool.ruff.lint]`; ruff `==0.17.1` in the `dev` extra (`uv.lock` gains the one `ruff` package entry and nothing else changes; the wheel came from PyPI because the lock needs every platform's hashes, which the offline cache didn't have).

| Selected | Why |
|---|---|
| `F` (pyflakes) | undefined names, unused imports and locals, redefinitions: the class the `LOG` bug belonged to |
| `E9` | syntax and IO errors |
| `B` (bugbear) | loop-variable closures, zip truncation, mutable defaults, misleading loops |
| `PLE` | pylint's error class (here: raw zero-width spaces in string literals) |
| `RUF100` | a `noqa` that suppresses nothing, so suppressions don't rot |
| `SIM115` | a file opened without a context manager is never closed (the one `SIM` rule that finds a defect rather than a style) |

No `UP` rule was taken: none finds a bug, and the ones with findings (UP037 quoted annotations 332, UP035 deprecated imports 293, UP017 `datetime.UTC` 77, ...) would rewrite hundreds of lines in files every branch in flight touches. No other `SIM` rule either: SIM117 (169), SIM300 (106), SIM105 (70) and the rest are style. No formatter, no naming, style or complexity rule.

| Off, or narrowed | Why |
|---|---|
| `B007` (ignore) | an unused loop variable is a naming nit; all 47 were read at A5 and none was a bug |
| `B904` (ignore) | Python chains the handled exception implicitly, so the traceback already keeps the cause; `from exc` would change only the wording between the two tracebacks (72 sites) |
| `F405` in `src/learnloop/cli/*.py` | the CLI modules share one namespace by star import (`cli/__init__.py`, `runtime.py`, `render.py`); 3,518 warnings, all noise; rewriting them is not this step's job |
| `F401` in `cli/runtime.py`, `cli/render.py` | both are star-imported by the other CLI modules, so an import with no local use is still the name those modules call (78 + 1) |
| `F811` in `tests/**` | an imported pytest fixture is redefined by the test's parameter of the same name, which is how pytest finds it (653 at A5). Checked first that none of them is a duplicate test name, the case F811 would really catch |
| `B017` in `tests/**` | 30 `pytest.raises(Exception)`: weak assertions, not bugs; narrowing each needs the test's intended exception, so they are listed below for later |
| `extend-immutable-calls` | `Path`, `pydantic.Field`, and three frozen dataclasses (`ReplaySettings`, `SelectionConstants`, `GenerationOptions`) plus the tests' `always()` are safe shared defaults (13 B008 findings) |
| `external = [ANN, ARG, BLE, D, E402, E731, N8, PLC, S, SLF]` | see the next section |

### Why the 847 "stale" noqa comments stay

The strategy counted about 847 stale `noqa` comments and asked that they go in the mechanical commit if `--fix` removes them safely. It doesn't: RUF100's fix deletes the whole comment, reason included (`# noqa: BLE001 - scheduling never fails a serve` becomes nothing). 804 of them are `BLE001` and 746 of those carry a reason that says why the broad `except` is right, which is exactly the convention's "what breaks without this". So the codes of rules this config doesn't run are declared `external`: ruff keeps those comments and RUF100 still checks every code it does run. Three comments whose code no longer applies but whose reason still informs were turned into plain comments by hand before the fix (`figures/rich.py`'s nested `hold`, `tests/figure_fixtures.py`, three in `tests/test_teacher_te2_review_fixes.py`).

## Counts

Before is the base `9a623e3d9c` under the final config (the same files, `ruff check --statistics`); after is the tip.

| Rule | Before | After | How |
|---|---|---|---|
| F401 unused import | 515 | 0 | 493 removed by the fix; 22 kept with `noqa` (20 lines) as re-exports or imported fixtures |
| B905 zip without strict | 344 | 0 | 295 `strict=True`, 41 `strict=False`, 8 `noqa` (owner list) |
| B023 loop-variable closure | 80 | 0 | all called in their own iteration; `noqa` on 67 lines |
| RUF100 unused noqa | 73 | 0 | removed by the fix (after the reasons above were saved) |
| F841 unused local | 48 | 0 | dead assignments deleted; calls kept; 4 expressions kept for their raise |
| F402 import shadowed by loop variable | 12 | 0 | `noqa`: the functions never call the shadowed `field()` / `entry()` |
| PLE2515 zero-width space | 7 | 0 | the fix writes them as `​` escapes (same strings) |
| F811 redefinition | 6 | 0 | 5 duplicate imports removed by the fix; the fixture generator's fixture parameter `noqa` |
| F821 undefined name | 6 | 0 | 2 annotations corrected; 4 false positives `noqa` |
| F541 f-string without placeholder | 4 | 0 | fix |
| B008 call in default | 4 | 0 | `noqa` (Path is immutable; two lambdas bind on purpose) |
| SIM115 open without with | 4 | 0 | three tests read through a `with` |
| B009 getattr with constant | 3 | 0 | fix |
| B020 loop variable overrides iterable | 1 | 0 | `noqa`: the tuple is built before the rebind |
| B039 mutable ContextVar default | 1 | 0 | `noqa`: never mutated, writers copy |
| **Total** | **1,108** | **0** | |

For comparison, the same base with the selected rules and none of the config's ignores (`--isolated --select F,E9,B,PLE,RUF100`): 6,518 findings, of which F405 3,518, RUF100 1,052, F811 682, F401 594, B905 344, B023 80, B904 72, F841 48, B007 47, B017 30, B008 17, F402 12, and the small rest as above. The strategy's ruff 0.17 run on `a36da14a4a` (src and tests only, with `UP` and `SIM`) counted 238 B905 and 65 B023; this run covers every tracked Python file (src, tests, scripts, the vault's `_scripts`, fixtures, apps, integrations) at a later tip.

## The F401 keep-list (before the mechanical commit)

pyflakes doesn't know about re-exports or pytest fixtures, so the fix would have removed names other code needs. An AST scan over every tracked Python file (`f401_classify.py` in the step's scratch) kept an unused import when its name is imported from this module elsewhere, read as this module's attribute (`LA.QUESTION`), named in a dotted string, or is a pytest fixture in its source module (followed through re-imports). It found 18 lines in `src` (`learner/assessment_contracts.py`'s six version constants, `substrate/canonical_projection.py`'s five, `reader/reader_progression.py`, `reader/reader_guidance.py`, `attempts/reveal_ledger.py`, `content/authoring/{ai_contracts,practice_generation}.py`, `daily_plan/learner_action.py`) and two imported fixtures in tests; each got `# noqa: F401  <reason>`. After the fix: every `src` module still imports (`pkgutil.walk_packages` over the four packages, 0 failures), and every dotted `monkeypatch.setattr`/`patch` target string in `tests/` still resolves (56 targets, 0 missing).

## B905: how each zip was judged

All 344 read one by one.

- **`strict=True` (295)** where the lengths are equal by construction: a SELECT's column list and its row (`zip(COLUMNS, row)`, `cursor.description`), a list and one built from it in the same function (`specs` from `points`, `rows` from `proposal.items`, `verdicts` per candidate), a pair guarded by a length check just above, AST fields that are parallel by definition (`kwonlyargs`/`kw_defaults`), a function's parallel arguments (`roc_auc(scores, labels)`, a posterior's weights and banks), and every test pairing an expectation with a result. There it never fires; a later change that breaks the pairing raises instead of silently dropping the tail.
- **`strict=False` (41)** where truncation is the point: `x` with `x[1:]` windows (25 of them), the first two surfaces of a pool, roles matched to however many hits `find_sources` returned (it is asked for `len(roles)` and may return fewer), left/right pairs within a group of unequal sides. Three of them were first judged `strict=True` and the targeted run showed they pair the first N on purpose (`de8bfb40a5`): an on/off twin compared up to the shorter trace (`test_ih4_preferences_inform_router`), owner verdicts labelling only the first answers (`test_recurrence_benchmarks`), confidence events on the first work lines (`test_teacher_te0_confidence_events`). All three are in tests; no `src` zip raised.
- **Kept open with `noqa: B905` (8)**, because the lengths are not proven equal and what a mismatch should do is a design call (listed for the owner below).

## B023: all 80 read

Every closure runs before the loop rebinds the variable: `record_generated()` in both probe-generation loops (17) is defined and called in the same iteration; `ai_compare`'s `call()` and its lambdas run inside the profile's iteration; the sort keys, `close()` helpers and lambdas are passed to a call that runs at once; the tests' monkeypatched lambdas are used inside their iteration. None is the late-binding bug, so each line carries `# noqa: B023  called within this iteration, before the loop rebinds it`. `cli/ai_compare.py`'s backslash-continued `with` became the parenthesized form so the `noqa` could sit on the reported line.

## F841: all 48 read

None was a forgotten use. `causal_attribution`'s first `burden` is computed again where the sort key reads it; `authoring_gates`' `original` copy predates the candidate copy that already leaves the payload untouched on refusal; `kinship_feature`'s `now` was an unused clock read. Pure assignments were deleted, calls kept without their binding (tests' setup calls, `test_ro4_objective_serving`'s spy runs the real chooser then reports a timeout). Four expressions stay for their effect, each with a comment saying so: the CLI's two `load_vault(vault_root)` (a vault that doesn't load stops the command), `sketch_verify`'s `compiled.probes[observe.probe]` and the help report's `attempts[row["resolved_attempt"]]` (both raise `KeyError` on a bad input, as before).

## F821

The six undefined names include no live bug. `recurrence/upgrade.py`'s `LoadedVault` annotation now has its import (`learnloop.vault.models`; the module already imports `learnloop.vault`), and `facet_evidence_timeline._observation_events` names the type it returns (`ObservationEvent`; no `FacetEvidenceEvent` exists anywhere). Both annotations were postponed, so nothing evaluated them. The other four are false positives with a `noqa` saying which: `causal_orchestrator`'s return annotation names a class the body imports, `tests/codex_cli_fakes.py`'s `render_prompt_input` is defined by `exec(_RENDERER)`, and `test_reading_request_sweep`'s lambda runs before the `del host` below it.

## noqa reasons, by kind

| Kind | Lines |
|---|---|
| called within this iteration (B023) | 67 |
| re-exported: imported from here or read as this module's attribute (F401) | 18 |
| an imported pytest fixture (F401 2, F811 1) | 3 |
| a local loop variable; the function never calls the shadowed import (F402) | 12 |
| lengths not proven equal; mismatch behaviour open (B905) | 8 |
| an immutable or deliberately early-bound default (B008) | 4 |
| false positive: body import, `exec`, lambda before `del` (F821) | 3 |
| the tuple is built before the rebind (B020); never mutated (B039) | 2 |

## Behaviour fixes

None. No finding was a live bug at this tip (the one the strategy found, `LOG`, was fixed before the step). So there is no behaviour-fix commit and no fail-first test.

## For the owner

1. **Eight zips whose mismatch behaviour is a design call** (`# noqa: B905`): `content/authoring/exercise_authoring.py:_item_refs` (span ids de-duplicated, source refs maybe not), `diagnosis/robust_composition.py:evaluate_selection` (best and runner-up ensembles' series), `diagnosis/split/history.py:evidence_units` (attribution facets against scopes), `evsi_calibration/response_fit.py:_fit_subject` (items against designated), `reader/as_printed.py:printed_crops` (two: a failed render may return fewer images than boxes), `sim/ad_synthetic.py:related_topics` (runs' logs of different lengths), `learnloop_sidecar/handlers/library_exercises.py:_fallback_candidates` (ids from `record_shown_spans`). Today each truncates silently, as before.
2. **30 `pytest.raises(Exception)`** (B017, ignored in tests): each could name the exception it means (mostly `sqlite3.IntegrityError`, `pydantic.ValidationError` or the sidecar's error type). A test-by-test job, not a lint one.
3. **164 broad `except Exception` without a `BLE001` reason** exist beside the 804 with one. `BLE001` is not selected; selecting it would make the reason convention enforced, after those 164 are read.

## Proofs

- `ruff check` on the tip: clean ("All checks passed!").
- `lint-imports --no-cache`: 43 kept, 0 broken.
- The mechanical commit changes no test outcome. Selection rule (`select_tests.py` in the step's scratch): every test file the commit touches, plus every `tests/test_*.py` whose imports (AST: `import M`, `from M import ...`, `from P import leaf`) name a `src` module or a `tests/` helper module the commit touches. 986 files, run at `856d252438` under the 5 GB cap at `-n 6`: 25,880 passed, 75 skipped, 11 xfailed, 3 failed (`test_chat_total_transport_deadline::test_rw6b2_f3_a_dribbling_response_is_aborted_at_the_total_deadline`, `test_instruct_handoff_ih1::test_no_new_draw_joins_an_open_item`, `test_ih2_lessons_compete::test_a_requested_item_is_placed_at_the_build_with_no_offer_beside_it`). None of the three files is touched by the commit; they are deadline- and timing-sensitive, the run peaked at the memory cap, and all three passed in the later run below, on a tree that contains the mechanical commit. Read as load flakes, not outcomes the commit changed.
- The later commits (B905 to the gates): the same rule over their files, plus the four named tests (`test_architecture`, `test_cli_help_snapshot`, `test_effective_defaults_golden`, `test_public_tip_guards`) and the three files above: 1,101 files. A first `-n 6` run was OOM-killed at the 5 GB cap; rerun in four chunks at `-n 4`: 27,577 passed, 97 skipped, 44 xfailed, 4 failed, all the three test zips above (`ValueError` from `strict=True`); after `de8bfb40a5` those three files: 98 passed.
- The four validators after one regeneration of the references on the committed source (`f09f257e05`): `module_validate`, `desktop_validate`, `db_validate_reference` and `validate_vault` all pass (2,271 notes).

## Vault

`Maps/Developer Map.md`'s safe change sequence now runs `uv run ruff check` beside `lint-imports` and says how a finding is kept. `Architecture/Testing and Invariants.md`'s verification commands gain `.venv/bin/ruff check`. Gate lists: `CLAUDE.md`'s commands, `docs/specs/implementation_goal.md` (gate row and the fixer's list), `docs/specs/implementation_handoffs.md` ("Done always includes"), and the strategy's per-step gate. No test pins a gate list, so none was added.
