# FG1d: a probe answer's facet shadow, and the marks panel's cost (`followup/fg1d-facet-shadow`, base `90a2f430c9`)

Two FG1-family follow-ups on main (mvp-0.45, migration 243), each reproduced first and fixed in its own commit. No migration, no
config key, no successor, no RPC or frontend change.

| Commit | What |
|---|---|
| `70ac1b9f38` | Fix 1: a probe answer on its presentation is banked live as replay banks it |
| `6c4406ba4a` | Fix 2: the marks panel reads the bundle's causes, on one connection |
| `ee2530d8fb` | Fix 1's extra test: the capability cell agrees with a real rebuild |

## 1. The facet shadow after a generated probe's answer

### Reproduced

`tests/test_followup_fg1d_probe_shadow.py`, on the synthetic blind vault FG1's tests use (`live_shape_vault`), through the sidecar's
doors as the desktop calls them: a miss with two rivals, the workflow's job generates the probe (faked author), Next opens it,
`get_probe_contract`, then `submit_attempt` with `probePresentationId` (as `PracticeScreen.tsx:1388` sends it). The vault is rebuilt
first and the shadow asserted 0/0/0, so whatever it reads afterwards is the journey's. The clock is frozen at a whole second, which
keeps R14 (a sub-second live write against replay's whole second, a known difference of its own) out of the comparison.

On the base, `rebuild --shadow` read **facet 2**, to FG1c's digits:

| Cell (`facet_recall_state`) | Live | Replay |
|---|---|---|
| `compute`, `method_selection`, the probe item | alpha 1, beta 1, `raw_coverage_mass` 0, `consecutive_failures` 1 | alpha 1.0919, beta 1.3678, raw 0.3678 |
| `compute`, `method_selection`, facet-wide (`practice_item_id` NULL) | the same | the same |

FG1c's description ("the probe item's own `method_selection` scope") was half of it: the second row is the facet-wide cell, which
only the probe feeds on that capability. The same fold also left `facet_capability_evidence`'s `(compute, method_selection)` cell at
zero mass (live 0/0, replay +0.092/+0.368); `rebuild --shadow` doesn't compare that table, so the new test checks it against a real
rebuild.

### Cause

The canonical projection gives an attempt reliable mass only through its active calibrated grade interpretation (P0.3 §4.3: "An
attempt with no active interpretation ... contributes zero reliable mass"). An ordinary attempt's interpretation is written by
`_dual_write_grade_channel` before the attempt's projection. A `diagnostic_probe` attempt is skipped there: the probe-episode path
writes it (`record_episode_evidence` -> `_record_presentation_observation` -> `_dual_write_probe_grade`), and that runs *after*
`_project_canonical_belief` in `_apply_attempt_in_transaction`. So the live fold saw the answer with mass 0: the negative branch made
the cells (prior 1/1, a failure stamp) and the positive branch added nothing. Replay re-applies the attempt with the interpretation
already on the ledger (`grade_interpretations` is never cleared), so its fold at that attempt banks it.

A later projection hid it: on a blind vault the diagnosis job's re-projection (`split/jobs.py:1106`) when it runs for the answer,
else the next attempt, a load that re-projects, or a rebuild. That is why FG1c saw 0/0/0 wherever a later miss followed the probe,
and why the drained case of the repro was already 0/0/0 on the base. Without `probePresentationId` there is no probe observation and
no interpretation on either side, so live and replay agreed (at zero mass), which is why FG1's smoke never saw it.

It isn't FG1's: any diagnostic probe answered on a presentation in a canonical-state vault had it. FG1 made it common.

### Which side is wrong

Live; replay is the reference. `spec_followup_generate_serve_v1.md` §4.1: "**Evidence.** Answers count as evidence from the first
serve, as for any diagnostic probe. The admissibility rule stays exactly as it is (§6.0)." The live write was a stale cache of the
canonical fold, not a different rule, so the fix makes live follow replay. (This line read "Replay." until the Codex review caught the
reversal; see `followup-fg1d-codex-review.md`.)

**Should the answer touch the item-scope cell at all?** Yes, unchanged. The single-use rule (§4.2) governs serving: the item is never
administered again and "stays in the vault so attempts and replays resolve". It says nothing about the projection, and the canonical
fold writes a per-item cell for every attempt it banks (`for scope in (None, practice_item_id)`). For a generated probe that cell is
inert, since nothing will serve the item again to read it; the facet-wide cell is the one that matters, and it was wrong too.
Excluding generated probes from the item scope would change replay of every probe answer already on record, which is a successor for
no learner-visible gain. So the fix makes live equal replay and leaves the fold alone.

### The fix

`_apply_attempt_in_transaction` re-projects (`_project_canonical_belief`, unbounded) after `record_episode_evidence`, for a live
answer (`not replace_existing`) that kept its presentation after `_validate_probe_presentation`. Same transaction, so nothing reads
the stale cells in between. Replay is untouched. The projection writes only on change, and its factor reconciliation reads the same
ledger the first fold read, so it inserts or retires nothing the first didn't (the whole-database comparison below shows it).

### Siblings checked against replay

Each a parametrized case in `test_followup_fg1d_probe_shadow.py`: `rebuild --shadow` 0/0/0 straight after the answer, and the probe's
cells carry mass at once.

| Door | Shadow after the answer (base -> branch) | Notes |
|---|---|---|
| With `probePresentationId`, feedback held (the default lane) | facet 2 -> 0 | observation admitted, independent; workflow settled |
| Show anyway, then the answer | facet 2 -> 0 | `admissible_as_independent` 0, as FG1 §6.0 says |
| Exam origin (nothing held) | facet 2 -> 0 | origin set on the row, as FG1c's smoke did |
| The diagnosis job drained after the answer | 0 -> 0 | the job's projection changes nothing further now |
| Without `probePresentationId` | 0 -> 0 | incidental evidence, zero reliable mass on both sides |
| `facet_capability_evidence` vs a real rebuild | differs -> equal | the table the shadow doesn't compare |

The phone can't send `probe_presentation_id` (`learnloop_mobile/allowlist.py`), and an exam attempt is dual-written by
`exam_session` before its own projection, so neither reaches this path. A held grade (`grade_held_for_review`) takes the same
re-projection, which reads what replay reads.

**Whole database, main against the branch**, after the same journey with module-stream ids and a frozen clock (scratch
`dump_after_submit.py`): of 390 tables only `facet_recall_state` (2 rows), `facet_capability_evidence` (1 row) and
`model_call_receipts` (the faked author's wall-clock times) differ. No factor, observation, workflow or schedule row moved.

**Cost.** One more whole-ledger fold per probe answer on a presentation, the fold every attempt already runs once. On the synthetic
vault: 1.5 to 1.7 ms each; `submit_attempt` 203 to 209 ms on main, 207 to 210 ms on the branch (3 runs each, noise-level). It wasn't
measured on the owner's vaults (none opened).

### The playbook: no successor

Item 1 asks whether the change alters persisted meaning. It doesn't. The meaning of mvp-0.45's facet state is the canonical fold over
the ledger, which replay computes. Replay's output is byte-identical (no replay code changed, and the golden rebuild-equivalence and
receipt-exactness tests pass unchanged). The live cache now holds, at the end of the answer's transaction, what the next projection
or a rebuild would have written anyway. Nothing about which items are served changes (the mvp-0.27 rule), and no ledger or receipt
changes. This is the inverse of the 2026-10-25 rebuild-equivalence case, which changed replay and so took `mvp-0.34`; here replay is
the reference and live is brought to it. Items 2 to 8 don't arise: no ledger edit, no upgrade function, no default, no table, no
fixture.

## 2. The marks panel's cost

### Measured first

`get_feedback` and the panel's own read (`followup_run/marks.py::bundle_view`), timed through the real handler on a synthetic
vault: the same blind vault and journey (a miss with a factor, its generated probe answered), beside the vault's seven seeded
attempts. Production pragmas (WAL, `synchronous=FULL`), 25 rounds per attempt, `recordOpen: false`, medians in ms. Both trees run
with module-stream ids and a frozen clock so their outputs compare byte for byte (scratch `measure.py`, run under `env -i`).

| Attempt | Panel shown | `get_feedback` main | after causes passed | after the pin | Panel read main | causes passed | pin |
|---|---|---|---|---|---|---|---|
| Miss with a factor (FG1 workflow) | yes | 286 | 284 | **199** | 88.2 | 87.6 | **1.0** |
| The probe's answer (shows the miss's list) | yes | 287 | 289 | **204** | 88.0 | 88.4 | **1.0** |
| Seeded misses, claim-checked list, no factor (4) | yes | 259 to 261 | 227 to 230 | **177 to 181** | 83.7 to 84.6 | 51.0 to 51.5 | **0.7** |
| Seeded misses with nothing to mark (2) | no | 242 | 208 to 211 | **185** | 61.9 to 62.0 | 28.9 to 29.6 | **0.4** |
| A pass (nothing to mark) | no | 183 | 177 | **149** | 36.3 | 29.2 | **0.4** |

FG1c measured 65 to 73 ms with nothing to mark and 91 to 99 ms with a panel on the owner's copies; this vault gives 62 and 84 to 88.

A profile of the read (scratch `prof_marks.py`) showed two costs. With no factor, `_claim_checked_ids` recomputed
`claim_checked_feedback` (33 ms), which `feedback_bundle` had just computed. And every repository read opened its own connection:
17 to 24 per panel, about 3 ms each with production pragmas, which is most of what is left once the causes are passed (the factor
path, `diagnosis_status`, `causal_hypothesis` lookups).

### The fix

- `get_feedback` takes the cause ids from the bundle it just built (`claim_checked_ids_of(bundle["causalFeedback"])`, the camel-cased
  `claim_checked_feedback`), **before** `_with_followup` can blank them for a hold, and hands them to `_with_hypothesis_marks`.
- `bundle_view`, `view` and `markable_list` gain an optional `claim_checked_ids`. `markable_list` uses them only where it used to call
  `_claim_checked_ids` (no factor lists the causes); `None` keeps the read. A probe answer's panel is the earlier miss's list, whose
  causes this bundle doesn't carry, so `bundle_view` doesn't pass them there. `record_exposure`, `record_mark` and every other caller
  still read their own.
- The panel's read runs under `repository.pinned()`: one connection for its reads ("purely a performance measure", the pin's own
  docstring). It is read-only, and a failure inside it still costs the panel and never the feedback.

A held list shows no panel either way: `view` returns `None` on `is_holding` before the ids are read, the predicate `get_feedback`'s
hold uses.

### Byte-identical

- **Across trees:** every panel (`hypothesisMarks`: seed, order, surface, statements, marks) on all nine attempts, and the six exposure
  rows `record_hypothesis_exposure` wrote after them, are identical between main and the branch, before and after the pin.
- **In the tests** (`tests/test_followup_fg1d_panel_read.py`): every attempt's panel equals the recomputing read's to the byte; the
  exposure row after the panel has the displayed order and the panel's seed; `claim_checked_feedback` runs once per `get_feedback`
  (that test fails on the base); a held miss still has no panel.

## Gate (implementation step; the full suite runs once at the landing)

Every pytest command inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, at most `-n 6`, one at a time.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install --offline pypdfium2==5.14.0` | done |
| `lint-imports --no-cache` (under `env -i`, empty `HOME`, `CODEX_HOME`, `LEARNLOOP_CONFIG_DIR`) | 43 kept, 0 broken |
| Repro on the base: `test_followup_fg1d_probe_shadow.py` with fix 1 reverted | 4 failed, 1 passed (the capability test, added later: 1 of 1 fails) |
| Repro on the base: `test_followup_fg1d_panel_read.py` with fix 2 reverted | 1 failed (read once), 3 passed (identity against the base's own read) |
| Fix 1, 40 files (every test naming `probe_presentation_id`, `probePresentationId` or `record_episode_evidence`, the FG1/FG1c test files, `test_shadow_rebuild.py`) | 880 passed |
| Fix 2, 21 files (every test calling `get_feedback` or importing the marks module or the feedback handler, the marks tests) | 882 passed, 5 skipped |
| Contracts and equivalence, 30 files: label audit `test_measurement_state_labels.py`, `test_cli_help_snapshot.py`, process-launch list `test_codex_lockdown_round3.py`, `test_architecture.py`, `test_desktop_rpc_contract.py`, `test_mobile_allowlist.py`, `test_sidecar_serializer_snapshot.py`, `test_config_refactor.py`, `test_table_roles.py`, `test_coordinated_migrations.py`, `test_tracked_fixture_databases.py`, `test_public_tip_guards.py`, `test_desktop_activation_audit.py`, `test_data_capture_report.py`, `test_rebuild_equivalence{,_review}.py`, `test_receipt_exactness.py`, `test_km2_{write_path,canonical}.py`, `test_p0_projection_cutover.py`, `test_canonical_projection_{fold_skip,rollout}.py`, `test_shadow_components.py`, `test_followup_{journey,live_shape,codex_review,reserved_only,migration}.py`, `test_characterization_probe_replay.py`, `test_sqlite_file_copies.py` | 767 passed, 1 skipped, 4 xfailed |
| **Final tree, all of the above, 81 files** (`docs/reviews/followup-fg1d.targeted-tests.txt`) | **1984 passed, 6 skipped, 4 xfailed** (7:42) |
| `--durable-sqlite` (production pragmas and WAL): both new files and `test_hypothesis_marks.py` | 47 passed |
| `module_validate.py` | PASS (1:1 coverage) |

No migration, schema, frontend or `src-tauri` change, so no `-m durability` migration lane, npm, vitest, cargo or DB-reference step
applies. The frozen-cycles contract is kept (the panel's new import is inside the sidecar handler, as before).

## What the owner runs

Nothing beyond restarting what runs this code once it lands: close and reopen the desktop app (the sidecar it spawns runs from the
checkout) and restart the phone host. No upgrade, no rebuild, no config.

Optional: `learnloop rebuild --shadow --json --vault ~/learnloop-vaults/<name>` on each vault. A vault whose last attempt was a probe
answered on its presentation (and whose diagnosis job hasn't re-projected) may show the 2 `facet_recall_state` rows until the next
attempt or load; `learnloop rebuild-derived-state` clears them, as FG1c found. After this lands, new answers don't leave them.

## Process notes

- No real model call, no vault opened, no paid command, no desktop window, no tailscale. Synthetic vaults only; every model faked
  (`BlindRivalClient`, `AuthorFake`).
- Scratch measurement and profiling scripts (`measure.py`, `measure_submit.py`, `dump_after_submit.py`, `prof_marks.py` in the stage
  scratch directory) and `lint-imports`/`module_validate.py` ran with the worktree's venv Python under `env -i` with empty `HOME`,
  `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`. Main's tree for the comparison was a `git archive` of `90a2f430c9` (and of `70ac1b9f38` for
  fix 2's base) in the scratch directory.
- Three small text-only patch edits (to the new test file, `followup_run/marks.py`, and a scratch script) used the system `python3`
  outside `env -i`; they read and wrote text and imported no LearnLoop module. Later edits used the Edit tool.
- Reverting a fix to show the repro failing used `git diff > patch`, `git checkout <file>`, `git apply`; no stash.
- Not touched: `apps/learnloop-mobile`, `src/learnloop_mobile/allowlist.py`, the mobile tests, `docs/mobile-shortcuts.md`,
  `docs/specs/spec_mobile_tailnet_v1.md`, `integrations/ios`, `.gitignore`, `README.md`, and RO1's interval block in
  `attempts/attempts.py` (fix 1 sits at the end of `_apply_attempt_in_transaction`, far from it).

## Open items

- **The rest of `get_feedback`** (150 to 200 ms on this vault) is probably the same per-read connection opening (about 3 ms each with
  production pragmas), but only the panel's share was profiled. Pinning the whole handler would be a wider change (it writes the
  open and the reveal debits), so it isn't done here.
- Fix 1's extra fold wasn't timed on an owner-sized ledger.
- R14 (the sub-second live write against replay's whole second) is unchanged; the new tests freeze the clock to keep it apart.
- FG1c's report coverage-line wording is untouched.
