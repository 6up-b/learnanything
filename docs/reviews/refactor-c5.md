# Refactor C5: Golden Path

Arc C ("delete what's proven dead"), step C5 of `docs/specs/refactor_strategy_v3.md` §2.5. Branch
`refactor/c5-golden-path`, based on `6629597573` (main `9841893fe0` + the arc C batch C1 + C3 + C4, merged and
regenerated). C2 runs in parallel from the same base; this step touches only the golden-path / `pattern_ladder` entries
of the files C2 also edits (`params/parameter_registry.py`, `scheduling/open_world_gate.py`, `tests/test_architecture.py`).

## Step 0: each candidate proved again at this tip

Written before any deletion.

**Method.** An AST import graph over `src`, `tests`, `scripts` and the vault's `_scripts` (every `import` and
`from … import`, function-local included, `TYPE_CHECKING` blocks excluded) gives each candidate's importers. A closure
over that graph from the replay, rebuild and upgrade roots (`substrate/rebuild_orchestrator`, `shadow_rebuild`,
`canonical_projection`, `attempts/attempts`, `daily_plan/engine`, `ops/doctor`, `activation_journal`,
`vault/repository` and all 45 `*_upgrade` modules) reaches 736 modules and none of the candidates below. String
dispatch: `git grep` for each module name as a string (`importlib` users in `src`: `MODULE_INVENTORY` in
`params/parameter_registry.py`, `open_world_gate._has_attrs`, `instructional/valuation`'s named gaps,
`diagnosis/scoreboard`'s producer, `ai/__init__`'s lazy exports, the fetchers and the PF sandbox; only the first two name
a candidate), each sidecar RPC by its quoted dotted name and its underscore Tauri spelling, and each Typer command. Every
RPC was word-matched (not substring) in `apps/learnloop-tauri/src` and `src-tauri/src` outside the golden files
themselves, in the phone (`src/learnloop_mobile`, the 60-method allowlist) and in MCP (`src/learnloop_mcp`).

### The 39 RPCs (four handler modules)

| Handler module (lines) | RPCs | Callers outside the golden screen and its client methods | Verdict |
|---|---|---|---|
| `handlers/golden_path.py` (326) | `blueprint.register`, `blueprint.review`, `blueprint.get_version`, `blueprint.discover_candidates`, `blueprint.compose_draft`, `golden_path.confirm`, `golden_path.run_status`, `golden_path.list_runs`, `golden_path.advance` | No TS outside `GoldenPathScreen`, `components/goldenpath/GoldenPathSetup`, `ExemplarConfirmDialog` and `client.ts`; none phone-allowed (`golden_path.advance` is pinned desktop-only in `test_mobile_allowlist`); none MCP. Tests: `test_sidecar_golden_path`, `test_sidecar_blueprint_picker`, `test_router_p2_bridge`, `test_ro0_codex_review::test_f3_the_staged_bridge_hands_its_decision_the_ad_reader`, setup calls in `test_sidecar_diagnostic`, `test_sidecar_ladder`. `scripts/gen_goldenpath_fixtures.py` (the screen's fixture generator). | delete |
| `handlers/golden_path_assessment.py` (190) | `golden_path.assess_open`, `.assess_submit`, `.assess_result`, `.restore`, `.boundary_diff`, `.depth_invitation`, `.accept_edge`, `.decline_edge` | As above (the screen only); `boundary_diff` lost its client method and Tauri command in C3. Tests: `test_sidecar_golden_path_assessment`, `test_daily_loop_golden_path_lifecycle`; the fixture generator. | delete |
| `handlers/ladder.py` (332) | `ladder.policy`, `.status`, `.enter`, `.advance`, `practice_pool.assemble`, `.admit_surface`, `.review`, `.status`, `.next_surface`, `.for_run`, `.seed_for_run`, `.admit_anchor` | The screen only. Tests: `test_sidecar_ladder`; the fixture generator. | delete |
| `handlers/diagnostic.py` (210) | `diagnostic.pack_assemble`, `.pack_admit`, `.pack_review`, `.pack_list`, `.baseline_enter`, `.boundary_view`, `.triage`, `.triage_status`, `.triage_decide`, `.triage_override` | The brief's check: does any `diagnostic.*` serve another screen, the phone or MCP? Word-matched each: no TS caller outside the golden screen (C3 already removed the client methods for the pack, baseline, boundary-view and override RPCs), none phone-allowed, none MCP. `handlers/diagnosis_card.py` is a different module (`diagnosis_card.*`), untouched. Tests: `test_sidecar_diagnostic`; the fixture generator. | delete |

No handler module is imported by anything but `learnloop_sidecar/handlers/__init__.py` (the registry fill).

### Frontend

| Candidate | Evidence | Verdict |
|---|---|---|
| `screens/GoldenPathScreen.tsx` (1,276) + its test (23) | Rendered only from `App.tsx` behind `SHOW_GOLDEN_PATH` (`components/ui.tsx:13`, `false`): `goldenRunId && SHOW_GOLDEN_PATH`, the `golden` tab (refused by `gotoTab` while the flag is off) and the Under-the-hood `golden` tool (`hidden: true`, listed only while the flag is on). The test checks one exported helper. | delete |
| `components/goldenpath/GoldenPathSetup.tsx` (380), `TriageDecisionAid.tsx` (116) | Imported only by `App.tsx`'s `renderGolden` and the screen. | delete |
| `components/goldenpath/shared.tsx` (399) | **Live**: `PrimaryButton`, `SecondaryButton`, `DispositionPicker` and `AffectTap` are used by the Reader (`ReaderScreen`, `GuideRail`, `AskRail`, `NotesRail`, `ActiveReadingCard`, `InquiryQuickCheck`, `ScopeFromPassage`, `YouTubeWatchPanel`). | keep the file; delete only the exports nothing else uses once the screen is gone |
| `components/ExemplarConfirmDialog.tsx` (167) | Opened by `App.tsx`'s `confirmOpen`, which only the golden screen's `onOpenConfirm` sets, and by `GoldenPathSetup`. It reads `fixtures/goldenpath` and calls `goldenPathConfirm`/`blueprintGetVersion`. | delete |
| `components/WhyDiagnosisOverlay.tsx` (76) | Shown for `App.tsx`'s `whyTriage`, which only the golden screen's `onWhy` sets. | delete |
| `fixtures/goldenpath/` (23 files, 1,002 lines) + `scripts/gen_goldenpath_fixtures.py` (163) | Imported by the screen and `ExemplarConfirmDialog` only; the script regenerates them from the RPCs above. | delete |
| `SHOW_GOLDEN_PATH`, the `golden` nav tab, the `golden` UTH tool, `old.golden` keymap entry, `goldenRunOpen` in `useQueueRevisionPoll` | The flag is `false`; nothing else reads it. A remembered tool `golden` in `localStorage` already falls back to `ingest` (`rememberedTool` accepts only visible tools); `learnloop.tab` is written, never read. | delete |
| `DoseOffer.tsx`, `readingPathsSwitchOff.test.tsx` (`goldenPathRunId`) | The Reader guidance DTO's `goldenPathRunId`/`targetContractVersionId`, filled by `reader/reader_guidance.py` from `golden_path_runs` (a kept table; a stored run still pins a goal's blueprint to a source). | keep |
| `CardControls.tsx:33` | A comment naming GoldenPath as a user. | fix the comment |
| 27 Tauri commands (`commands.rs:1190-1234`, `main.rs:508-537`) and 27 `client.ts` methods (`:1364-1457`) | Each client method name word-matched in every non-golden `.ts`/`.tsx` file: none. Each command's only caller is its client method. | delete |
| DTO types in `dto.ts` used only by the deleted code | Found by typecheck after deletion; each checked by name in the remaining TS. | delete those with no remaining user |

### Python modules

| Module (lines) | Importers at this tip | Other reach | Verdict |
|---|---|---|---|
| `curriculum/golden_path_compose.py` (216) | `handlers/golden_path.py` only | none | delete |
| `curriculum/pattern_ladder.py` (510) | `handlers/ladder.py` only | `MODULE_INVENTORY` + four `_reg_const` entries; `open_world_gate._c3_p2` imports it by name (`controller open-world` CLI); `test_architecture`'s runtime-module list. Tests: `test_pattern_ladder`, `test_p2_acceptance` (the ten-step walk, the three planted-learner tests, the ladder climb in the replay test). | delete, with its registry entries, the `open_world_gate` name and the `test_architecture` line |
| `substrate/surface_pool.py` (488) | `handlers/ladder.py` only | `MODULE_INVENTORY` + two `_reg_const` entries. Tests: `test_surface_pool`, `test_p2_leakage_suite` (cases 1 and 2 rerun two of its functions), `test_p2_acceptance` (the ten-step walk). | delete, with its registry entries; leakage case 1 (practice exposure blocks the same-fingerprint assessment reserve, a live substrate guard) is kept, rewritten on `activities.open_administration`; case 2 (pool admission) goes with the pool |
| `diagnosis/failure_triage.py` (1,054) | `handlers/diagnostic.py` only | Registry entries. **But** the live causal lane's tests drive it as the triage entry point: `test_causal_p2_acceptance` (the lane's only end-to-end walk, by its own docstring), `test_causal_attribution_p2`, `test_failure_triage_causal_gate`, and `diagnosis/causal_health` reads the events it writes. | **keep** (owner's list): deleting it means re-plumbing the causal lane's acceptance tests, beyond this step |
| `diagnosis/diagnostic_pack.py`, `curriculum/golden_path_assessment.py`, `golden_path_restoration.py`, `golden_path_run.py` | Reached from `reader/reader_restoration.py` → handler `reader.restore` (registered, outside the golden family; no desktop caller, as for the other `reader.*` RPCs C3 listed). `golden_path_run` is also imported by `scheduling/controller_cutover.py`. | — | **keep** (owner's list) |
| `scheduling/controller_cutover.py` (C6's) | Its only `src` caller is `handlers/golden_path.py` (`advance_live`, through `bridge_active`). | `test_controller_cutover`, `test_router_staged_p2` | **keep for C6**: once this step lands it has no `src` caller, which is C6's trigger ("if C5 removed the only caller of `controller_cutover`, it goes with its registry entry") |
| `curriculum/golden_path_confirm.py`, `task_blueprints.py`, `golden_path_fixture.py`, CLI `goldenpath init-fixture` (`cli/goldenpath.py`) | `golden_path_fixture` (and through it `confirm` and `task_blueprints`) is the seeded vault of tests of live code: `test_reader_dialogue`, `test_practice_information`, `test_held_grade_evidence`, `test_p2_leakage_suite`, `test_causal_p2_acceptance`, and `router_staged_p2_helpers`. The CLI command is in `tests/cli_surface.json`. | — | **keep** (owner's list) |
| `scheduling/controller_ownership.py`, `scheduling/serving_exclusions.py` | **Live**: the plan's staged-owned exclusion (`build_due_queue`) reads stored ownership rows. | — | keep |

### `daily_plan/policy.py`: `bridge_active`

`bridge_active(vault)` is `algorithm_version in ROUTER_STAGED_FRAME_VERSIONS and router.enabled`. Readers at this tip:
`router_active` (`policy.py:50`, which every plan path reaches), `handlers/golden_path.py:270` (deleted above),
`tests/test_mvp023_upgrade.py` (three asserts). The check **moves** into `router_active` unchanged; the function goes.

### Tables

Left in place for J1 (`golden_path_runs`, `golden_path_run_events`, `golden_path_artifacts`, `task_blueprints`, the
`diagnostic_pack*`, `failure_triage_*`, ladder and pool tables). Their `Repository` readers stay (`reader_guidance`,
`causal_health`, `probe_episodes`, `voi_*` and the kept modules read them).
