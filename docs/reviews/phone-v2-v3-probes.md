# Phone v2, stage V3: probes and cold checks on the phone

**Spec:** `docs/specs/spec_mobile_frontend_v2.md` §8's V3 row (detail in §2.1 J3/J6/J11, §2.3, §7; owner decision **D3**, accepted 2026-11-06: diagnostic probes, FG1's follow-up probes and lesson probes answered on the phone, behind a kill switch). Plus V2's carried items: the `help_assists.surface` widening (V2 landing ruling R5) and the F9 class on a finished plan (V2 landing record, "Open items"). **Branch:** `phone/v3-probes`, from main `14b2ed09ab`. **Successor:** mvp-0.54 (one constant, `PHONE_PROBES_ALGORITHM_VERSION`; built as mvp-0.53 and renumbered when main, with TE3b's mvp-0.53, was merged in at the end of the stage). **Migration:** 250 (renumbered at landing if another lands first). **No model call of its own, no new dependency.**

## Commits

| Commit | What |
|---|---|
| `e64f19daf3` | (1) The F9 class on a finished plan: *Keep going* on a `complete` plan and `plan_more_new{confirm}` commit their stop-override receipt with the extension, reproduce-first |
| `3e98c165d5` | (2) Migration 250: `help_assists.surface` gains `phone_practice`; head fixture rebuilt and renamed `migration_head_250`; every head path and version pin |
| `d7ea71a54a` | (3) The successor (built as mvp-0.53) and its upgrade; the host's `phone_probes` switch on the request origin; the sidecar's V3 serving (doors, filter, Next, the contract, G10's admission transaction); the phone's hint reveal records `phone_practice`; tests |
| `0cc1e5ab54` | (4) The PWA: the probe rendered cold and answered with its presentation; Next on a miss asks its workflow; the generated contract files |
| `bc9eadcc88` | (5) This review, the spec's "As built" note, FG1 §4.2's Phone row and §10 amended, regenerated references |
| `00d25c2f8d` | Merge main (`e9ceaf8d44`, TE3b landed as mvp-0.53): the successor renumbered **mvp-0.54**; references regenerated on the merged tree |
| (this commit) | The review's gate and the landing notes |

## 1. What was built

### 1.1 The gate: switch, tag, origin

- **Kill switch `phone_probes`** in `mobile.toml` (`MobileConfig.phone_probes`, default **true**, as D3's "behind a kill switch" with the owner's frictionless defaults; the same file and shape as V2's `phone_plan`). The host carries it on every `RequestOrigin` it makes (`RequestOrigin.phone_probes`, set by `HostRuntime._origin`, never a parameter). An origin made without it (`False`) is V2's phone, which keeps every V2 test meaning what it meant.
- **The gate** is `request_origin.phone_probes_on(origin, config)`: a phone origin with the switch AND the vault at `PHONE_PROBES_VERSIONS`. Never true for the desktop (a None origin).
- **Host:** off, `followup_next` answers `409 phone_probes_off` and a submit naming `probe_presentation_id` answers `422 validation_error` (`allowlist.check_probe_parameters`), exactly V2's refusal. `GET /api/v1/meta` says `phone_probes`.
- **Sidecar, below the tag** (switch on, vault below mvp-0.54): every phone door refuses as in V2, `followup_next` answers `continue` and writes nothing, and a phone submit naming a presentation is refused `validation_error` (`practice._refuse_phone_probe_answer`).

### 1.2 What the phone does with it (the sidecar)

- **Eligibility, decided structurally.** A probe is phone-eligible exactly when its item passes PR-6's `ineligibility_reason`: no image, page (`llpdf:`) or item-asset link (image-dependent), and not a dialogue microprobe, teach-back, error hunt, laddered stem or lesson check (desktop tools). No new rule and no text cue (`device_eligibility.py`'s docstring says so). With the switch on, the device filter no longer leaves the session's committed presentation for the desktop (`serving.device_filter`): the phone renders it.
- **The contract on the phone.** `get_probe_contract` under a phone origin with the gate on answers the desktop's contract plus `phoneAnswers: true`; the phone renders and answers only such a contract (below the tag an active contract still says *Continue it on the desktop*). The contract's restrictions (hints, Ask, worked examples, the answer: all disabled; feedback deferred) are the desktop's; the server refuses a hint reveal during the probe (`diagnostic_block`, as before); Ask, the tutor, the adaptive hint jobs and *Teach me instead* are not on the phone's allowlist at all.
- **FG1 serving on the phone** (FG1 §4.2's Phone row and §10, amended):
  - the phone's Next on a miss calls `followup_next` (the V3 allowlist row, short, not retried: it can write): it **waits** with the desktop's line, **opens** the question, or **goes on**. On a plan, R12 holds: the plan's next step places it, and the phone's step filter no longer holds a generated probe (`_step_filter`);
  - `followup_status` and the feedback bundle read the desktop's line (V2's hand-off line only with the gate off);
  - **burned at the first serve**: the door (`serving.refuse_generated_probe_door`) takes the desktop's path under the **phone's surface**, so `identity.claim_serve` records a `served` burn with `surface = phone`;
  - **single use across both devices**: the claim keys the surface, so a probe served on one device is refused on the other (`generated_probe_closed`) and each device's re-open of its own administration passes. `identity.served_elsewhere` says which device holds it; with it:
    - the phone's plan step **holds** a desktop-served probe for the desktop (counted, *waiting for the desktop*), the phone's list never heads with one, and `followup_next` answers `continue` to the other device and writes nothing;
    - the desktop's **serving** Next, when the plan would resume a probe the phone served (the learner took the session to the desktop), **abandons** it (`daily_plan._abandon_phone_served`: closed, what it held released, the decision's outcome `abandoned`), and the plan's existing reconcile displaces it. Nothing is read or written there for a vault with no phone burn;
  - **held feedback released only on the answer**: unchanged FG1 machinery; the phone's answer names the presentation and settles the workflow (`probe_answered`); before it, the bundle stays held on both devices and the answer's display is refused.
- **G10's cap boundary.** With the phone answering probes, the host's two workers can act for one device at once (an admission on the RPC worker, a submit on the job worker). The phone's admission (the session cap's count, the session's open presentation, the commit) is one `BEGIN IMMEDIATE` transaction; a submit consumes its presentation and records its observation in one transaction (`apply_attempt`), so no answer can commit between an admission's count and its commit. The desktop's admission is unchanged (serial; no transaction added).
- **Hint surface (migration 250):** `practice.record_hint_reveal` under a phone origin writes `help_assists.surface = 'phone_practice'`; the desktop's stays `practice`.

### 1.3 The PWA

- `practice/QuestionScreen.tsx`: `phoneProbe()` (the desktop's runtime guard on the contract, plus `phoneAnswers`); a probe answered here is cold: the desktop's own line (*Feedback comes when this short check ends · hints are off for now*, with `followupWhy`), no *Hint*, no help sheet; the submit is `diagnostic_probe` with `probePresentationId` and no help counted. A contract the host doesn't say the phone answers waits for the desktop, as in V2; an incomplete one is an error, never a question with help. A `generated_probe_closed`/`reserved` refusal moves on as `desktop_only` does.
- `App.tsx` (`feedbackNext`): Next on Feedback asks `followup_next` first: *open* opens the question, *wait* stays on Feedback with the waiting line (the panel keeps *Continue without it*), *continue* goes to the plan or the list. `phone_probes_off` (or an older host's 403) stops asking.
- `practice/FeedbackScreen.tsx`: the waiting line; a probe answer's feedback points back at the miss whose feedback it released (*See the feedback on your earlier answer*, FG1 §3 step 8).
- `api/phone.ts`: `followupNext`, `SubmitInput.probePresentationId`. The generated `phoneMethods.ts` (the digest moves, so a cached V2 app offers the reload) and the contract files (`contract/followup_next.json`, a probe submit in `contract/submit_attempt.json`).

### 1.4 V2's carried items

- **F9 class on a finished plan** (V2 landing record, open item 1). *Keep going* on a `complete` plan and `plan_more_new{confirm}` wrote their override receipt before `build_plan`, in a transaction of their own. Reproduced first: a phone whose session moved away and back during `_prepare_plan` was refused `session_moved` with the receipt left behind (both failed before the fix). `build_plan` gains `with_insert`: the receipt commits inside the transaction that inserts the extension (the owner-checked one), after the slow build; an empty extension returned instead commits it on its own, as before. The desktop records the same receipt as before.
- **`help_assists.surface`** (R5): migration 250, as above.
- Not carried here: `test_every_reply_carries_what_the_phone_reads`'s dependence on the queue's first row (V2's open item 2); see §5.

## 2. Where the spec was not built as written, and the smallest way to finish

1. **"Lesson probes answered on the phone" (D3).** Lessons are not on the phone until V6 (`lesson.turn` is not allowlisted), so no lesson probe can reach the phone in V3. The serving machinery V3 opens is FG1's and the routine probes'; a lesson's probe is served through its own ledger (`door_refusal` keeps a lesson-source probe reserved for its lesson). Smallest finish (V6): allowlist `lesson.turn` with V6's `expectedTurn`, and let the lesson's probe answer through `phone_probes_on`.
2. **Asymmetry at the handoff.** A probe the desktop served is *held* on the phone (the desktop can resume it); one the phone served is *abandoned* by the desktop's serving Next (the desktop can't open it, and a resumed plan step would strand it). Smallest alternative if the owner prefers symmetry: hold it on the desktop too, which needs a desktop step filter, i.e. a change to the desktop's serving at a None origin.
3. **The desktop reopening a checkpoint that names a phone-served probe** (after an adopt) gets `generated_probe_closed` from its door, as for any closed probe. How the desktop's PracticeScreen words that error was not checked in this stage (no desktop file changed; its serving Next past it is item 2's). No new desktop UI line was added (the desktop must stay as it is at a None origin). Smallest finish: a typed line on the desktop for `generated_probe_closed`.
4. **No in-suite byte-identity test against the base commit.** As V2 did, the desktop journey was compared against `14b2ed09ab`'s code out of the suite (§4); in the suite, the desktop's paths are pinned by FG1's and the plan's own tests, which pass unchanged, plus `test_a_desktop_serving_next_with_no_phone_burn_abandons_nothing` and `test_the_desktops_keep_going_on_a_finished_plan_records_as_before`.
5. **`phone_probes` is a host switch, not a vault key.** As V2's `phone_plan` (its review §2 item 9): the host's door, in `mobile.toml`, not a decision parameter, so `parameter_registry.py` is unchanged and no defaults snapshot moves by a key (mvp-0.54's differs from mvp-0.53's by the tag alone).
6. **Answer confidence (the desktop's optional 1-5 tap on a probe)** is not on the phone: it is logged-only and optional. Smallest finish: five chips under the editor sending `answerConfidence`.

## 3. Persisted meaning and the playbook ruling

- **Ruling: a successor, mvp-0.54** (`docs/algorithm-change-playbook.md`). Step 1: no stored record changes meaning and replay reads nothing new. But the recorded rule of 2026-10-17 applies: *a change to which items are served as measurements … is a successor with a kill switch even when replay is unchanged.* A phone origin now serves and answers, as measurements, the diagnostic and generated probes it used to leave for the desktop. V2's ruling (no successor) rested on the phone never serving a measurement it couldn't show; V3 removes that premise.
- **What it is:** `PHONE_PROBES_ALGORITHM_VERSION = "mvp-0.54"` after TE3b's mvp-0.53 in `SUCCESSOR_CHAIN`; `PHONE_PROBES_VERSIONS`; `learnloop.phone_probes_upgrade` (the chain's next journalled link: a projection activation, nothing recorded changes; installed by the CLI and sidecar openers; `learnloop upgrade --to mvp-0.54` and the default target); its defaults snapshot (`DEFAULTS_SNAPSHOT_BY_ALGORITHM["mvp-0.54"]`). Below the tag, or with `phone_probes` off, the phone is V2's exactly; the desktop is the same at every version.
- **Renumbered at the merge of main:** TE3b landed as mvp-0.53 while this stage was built, so this is mvp-0.54: the one constant, the snapshot key (recomputed), the upgrade's `PREDECESSOR` (TE3b's) and completion hand-off, the openers, the CLI's `--to` list, and the version pins (re-applied to main's own test files after taking them, so TE3b's pins and this stage's agree).
- **New rows:** burns with `surface = phone`; attempts on `phone_practice` naming a presentation (`attempt_type = diagnostic_probe`); `help_assists` rows on `phone_practice`. The probe answer's evidence is FG1's (admissible from the first serve, as any diagnostic probe); its surface is recorded, so reports can split it (D3's trade-off).

## 4. The desktop at a None origin

- **By construction:** every new branch is behind `phone_probes_on` (False for a None origin) or a phone burn (`served_elsewhere`, which no vault had before V3). The desktop's door claims under `desktop` as before; its admission adds no transaction.
- **Against the base commit** (scratch, outside the worktree): FG1's whole desktop journey on the live-shape vault at mvp-0.52 (miss, the held bundle, Next waiting, generation, Next opening, the queue, the serve, the contract, the probe's answer, the released bundle, Next and the door after) was run on `14b2ed09ab`'s `src`/`tests` (`git archive`) and on this branch, the clock frozen, `os.urandom` and `uuid4` seeded, AD's models off, dumping every reply and the rows of eleven tables, ids renamed by first appearance. Base against base differed in 4 fields (a detail's bundle ids order, an ensemble seed, a scheduler exploration roll, an instrument card snapshot's hash order); branch against base differed in those same fields plus the hypothesis display order (its seed is the attempt's random id, which differs between any two runs; base against base drew the same order by chance). No reply or row differed otherwise.
- The plan day was not compared out of the suite: two runs of the base's own plan day already diverge (the router's draws), as V2's landing found. V2's landing smoke compared it with AD's threads off; V3's plan changes for the desktop are the receipt's transaction (§1.4, pinned in the suite) and the abandonment, which needs a phone burn.

## 5. Gate (this step; the full suite runs once in the landing gate)

Run in the worktree. Every pytest, vitest and npm run went through `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`; pytest at `-n 6` at most, vitest at `--maxWorkers=4`; every Python or CLI call under `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`, `TMPDIR` outside the worktree. No paid or live call: every model is a fake.

| Lane | On | Result |
|---|---|---|
| Setup | `uv sync --extra dev --extra mobile`, then `uv pip install --offline pypdfium2==5.14.0`; `npm install --prefer-offline` in both apps | ok |
| Import contracts | `lint-imports --no-cache` (before the first commit, after commit 3, after the merge) | **43 kept, 0 broken** |
| F9 class (commit 1) | `test_mobile_v3_carried.py` (both reproductions failed before the fix), then `test_mobile_v2_landing_fixes.py`, `test_mobile_v2_plan.py`, and every test file naming `keep_going`/`more_new` (16 files) | 25 passed; 291 passed, 3 skipped |
| Migration (commit 2) | every test file naming the head fixture or `discover_migrations`, plus table roles, coordinated migrations, tracked fixture databases, public-tip guards, SQLite copies, hint telemetry, CLI snapshot (89 files) | 1090 passed, 4 skipped, 2 failed (test_ad23's 218-without-214 path, which sees 250's table change, and the CLI snapshot: both fixed, and both in every later run) |
| Successor pins (commit 3) | the 50 files whose version pins moved, plus the successor tests | 919 passed, 12 skipped, 3 xfailed, 6 failed (sets built with `LATEST_ALGORITHM_VERSION` at their end, and TE3a's CLI default target: fixed; the six files then 98 passed, 6 skipped, 1 xfailed) |
| Targeted set (commit 3) | 193 files: every `test_mobile_*`, every `test_followup*`, every test file naming the changed doors, the queue, the probe contract, Next, the claim, the plan's Keep going and More new, `RequestOrigin`, the hint reveal; the successor-pin files; the contract set (`test_desktop_rpc_contract`, `test_sidecar_serializer_snapshot`, `test_architecture`, `test_table_roles`, `test_config_refactor` (defaults snapshot), `test_cli_help_snapshot`, the display-label audit (`test_sidecar_measurement`, `test_router_why_copy`, `test_key_ladder_labels`, `test_measurement_state_labels`, `test_rw5c_labels`), the process-launch allowlist (`test_codex_lockdown_round3`), the frozen cycles (`test_codex_lockdown_frozen`), `test_registry_audit`, `test_module_catalog_inventory`, `test_public_tip_guards`, `test_sqlite_file_copies`, `test_tracked_fixture_databases`, `test_coordinated_migrations`, `test_session_ownership`, `test_probe_orchestration_remainder`, `test_hypothesis_marks`) | **4032 passed, 27 skipped, 3 xfailed, 2 failed** (the allowlist's milestone set and the phone contract's reply journey, which now reach V3's row: fixed; the two files then 82 passed) |
| **After the merge of main** | 260 files: the targeted set above, the version-pin files, every `test_te3b_*`, every V3 file, every head-pinning file (behind `flock /tmp/learnloop-fullsuite.lock`) | **4767 passed, 28 skipped, 3 xfailed, 0 failed** (47 min) |
| Durability (after the merge) | `-m durability` on `test_mobile_v3_migration`, `test_mobile_two_process`, `test_help_assist_figures_migration`, `test_help_assist_work_md_migration`, `test_migrations`, `test_tracked_fixture_databases`; and `--durable-sqlite` on the four V3 files (WAL, FULL: G10's lock test included) | 4 passed; 28 passed |
| Phone app (`apps/learnloop-mobile`), after the merge | `npm run typecheck`; every vitest file (`npx vitest run --maxWorkers=4 src public`); `npm run build` | clean; **24 files, 288 passed**; built |
| Desktop app | no file under `apps/learnloop-tauri` changed (main's `dto.ts` came with the merge; the phone's typecheck reads it) | no desktop vitest, build or `cargo check` needed |
| Phone contract files | `LEARNLOOP_UPDATE_PHONE_CONTRACT=1` (pytest for `phoneMethods.ts`, vitest for `contract/*.json`) | regenerated: `followup_next` added, the digest moved; `contract/followup_next.json`, a probe submit in `contract/submit_attempt.json` |
| References (after the merge) | `db_generate_reference.py` then `db_validate_reference.py` (schema changed: `SCHEMA_HEAD` 250); `module_generate.py` then `module_validate.py`; `desktop_validate.py`; `validate_vault.py` | `errors: []`; PASS (1:1 coverage); passed, 323/323, reproducible; passed (2244 notes). Provenance-only churn left out (81 notes) |
| Desktop byte-identity (§4) | scratch scripts, base `14b2ed09ab` against the branch, twice each | identical up to the fields two runs of one tree differ in |

**Test files run, for reading the landing gate against:** `merged.txt` in the stage's scratch directory (`/tmp/claude-1000/-home-saturn-Documents-thinking-learnanything/a22010cc-5149-4947-a2b8-247f18b8f1a0/scratchpad/phone-v3/`) (260 files; reproducible as: every `tests/test_mobile_*.py`, `tests/test_followup*.py`, `tests/test_te3b_*.py`, the files named in the targeted-set row, every test file this stage changed, and every file naming `migration_head_250` or `discover_migrations`); the durability files above; every vitest file in `apps/learnloop-mobile/src` and `public`.

## 6. What the owner runs on the iPhone (P6)

Nothing below has been run on a device.

On carson, after landing. V3 adds migration 250 (applied when the desktop app opens the vault) and the successor mvp-0.54 (after TE3b's mvp-0.53):

```bash
cd ~/Documents/thinking/learnanything
.venv/bin/learnloop upgrade --vault ~/learnloop-vaults/arxiv_v2     # each vault the phone host serves; default target
(cd apps/learnloop-mobile && npm install && npm run build)
systemctl --user restart learnloop-mobile
.venv/bin/learnloop-mobile doctor
```

The cached V2 app offers *LearnLoop was updated. Reload* (the allowlist moved): tap it.

- **P6. A generated follow-up probe, on the phone.**
  1. Miss a question on purpose on the phone (an answer that is wrong in a way with two plausible causes). Feedback holds the worked answer and says *Preparing a question on this…*.
  2. Tap Next. While the question is being written, Feedback stays and says so (with *Continue without it*). When it is ready, Next opens it.
  3. The question shows *Feedback comes when this short check ends · hints are off for now* and *This question comes from your last answer.* There is no *Hint*, and nothing else offers help.
  4. Answer it. Its feedback appears, with *See the feedback on your earlier answer*: tap it. The earlier miss's worked answer and causes now show.
  5. Reopening it does not serve it again: go back to Today; it is not listed, and on the desktop it is not offered either (the desktop refuses it if opened by link).
  6. Optional, the other device: miss another question on the desktop and open its question there; then take the session on the phone. The phone does not offer that question (*waiting for the desktop*), and the desktop still can.
- **To turn it off:** add `phone_probes = false` to `~/.config/learnloop/mobile.toml` and run `systemctl --user restart learnloop-mobile`. The phone then leaves every probe for the desktop, as in V2 (its Feedback says *Your next question on this is waiting for the desktop.*).

## 7. Security and the review checklist

- **Allowlist:** one method added (`followup_next`, V3 row); every other registered method stays 403 (G3). No method that offers help (hint jobs, Ask, tutor) is reachable.
- **Origin:** the switch comes from the host's config on the origin, never a parameter.
- **Ownership:** every serve door and submit keeps PR-4's checks; the desktop's abandonment runs only under its owned serving Next.
- **Spend:** V3 adds no model request. The question's generation is FG1's, already paid on the desktop path (D2).
- **Exam material:** unchanged (FG1 §8 guards are server-side and run before any phone serve).

## 8. Process notes

- Patches: most source edits used the editor. Some were made with small `python3` text-replacement scripts or `sed`/`perl` that read and wrote only the named files and imported nothing from LearnLoop: `hints/telemetry.py` and `cli/hints.py` (one replacement each), the head-path rename across tests and scripts (`migration_head_249` to `_250`), the version pins (the lists ending at 249 and at mvp-0.52, the negative chain indexes), several test-file edits (`test_mobile_allowlist.py`, `test_mobile_rpc.py`, `test_mobile_v2_feedback.py`, `test_mobile_meta_timing.py`, this stage's own test files), two tests appended with a heredoc, `contract.test.ts`, and the DB reference scripts' `SCHEMA_HEAD`. Migration 250's SQL was generated from the head fixture's own table definition by a script run under `env -i`.
- Every Python or CLI call ran under `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`; every pytest, vitest and npm run in a 5G memory scope; pytest at `-n 6`, vitest at 4 workers.
- The byte-identity scripts and outputs are in the stage's scratch directory, outside the worktree.
- Regenerated DB references: provenance-only churn (73 notes) was left out; the 405 notes whose `schema_head` moved to 250 keep their new provenance lines.

## 9. Open questions

1. Item 2 of §2: abandon on the desktop's Next (built), or hold for the phone (a desktop step filter)?
2. Should the phone offer *Teach me instead* during a probe (`stop_probe_diagnosing` is desktop-only today), or is Skip enough?
3. Main merged in at the stage's end (TE3b, mvp-0.53): the successor is mvp-0.54 and the migration stays 250 (TE3b added none); both are rechecked at landing.
