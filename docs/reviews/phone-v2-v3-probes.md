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
    - the desktop's **serving** Next, when the plan would resume a probe the phone served (the learner took the session to the desktop), **abandons** it (`daily_plan._abandon_phone_served`: closed, what it held released, the decision's outcome `abandoned`), and the plan's existing reconcile displaces it. Nothing is read or written there for a vault with no phone burn. Not while the phone's answer to it is accepted and still being graded, nor once it has one (Codex review F2, `phone-v3-codex-review.md`): the plan then resumes it until the answer commits, and the learner's own Skip still abandons it;
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
- **What it is:** `PHONE_PROBES_ALGORITHM_VERSION = "mvp-0.54"` after TE3b's mvp-0.53 in `SUCCESSOR_CHAIN`; `PHONE_PROBES_VERSIONS`; `learnloop.phone_probes_upgrade` (the chain's next journalled link: a projection activation, nothing recorded changes; installed by the CLI and sidecar openers; `learnloop upgrade --to mvp-0.54` and the default target); its defaults snapshot (`DEFAULTS_SNAPSHOT_BY_ALGORITHM["mvp-0.54"]`). Below the tag, or with `phone_probes` off, the phone is V2's exactly; the desktop is the same at every version except where a phone burn exists (its serving Next abandons a phone-served probe with no answer on its way, §1.2), which only a phone at the tag can make.
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

The cached V2 app offers *LearnLoop was updated. Reload* (the allowlist moved): tap it. Until then it gets V2's serving (it doesn't say it answers probes).

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
- **Ownership:** every submit keeps PR-4's checks; a phone door that burns a generated probe or commits a probe presentation checks the session's owner in that transaction (Codex review F1: before it, a phone the session had moved away from could burn the desktop's probe); the desktop's abandonment runs only under its owned serving Next.
- **Cached apps:** the host serves probes only to an app that says it answers them (`LearnLoop-Capabilities: phone_probes`, Codex review F3); a cached V2 app keeps V2's doors and plan step until it reloads.
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

## Landing onto main

**Branch tip before this record:** `315f250c7d` (the regenerated references), on `12698bf8b8` (the Codex re-review record). Main was `e9ceaf8d44` (TE3b's landing record) throughout and is an ancestor of the tip. It was already merged in at `00d25c2f8d`, and it did not move during the landing, so no further merge was needed. Router speed stage 2 had not landed. The numbers stand: **mvp-0.54** (after TE3b's mvp-0.53) and **migration 250**. The kill switch is `phone_probes` in `mobile.toml`.

### Rulings (verbatim)

- R1: "The final verify is clean; no further Codex round."
- R2: "Open questions, decided: (a) a probe the phone served is abandoned by the desktop's serving Next when the learner moves to the desktop, and a desktop-served probe is held on the phone: kept as built, since holding a phone-served probe on the desktop needs a desktop step filter that changes desktop serving; (b) 'Teach me instead' (stop_probe_diagnosing) on the phone goes to V6 with lessons (Skip stays meanwhile); (c) lesson probes on the phone wait for V6, as built: acceptable under D3; (d) the numbers are mvp-0.54 and migration 250 unless main moved (recheck after any merge)."
- R3: "Owner, Nov 5: the old item difficulty scalar is to be retired in the refactor. V3 adds no new reader or writer of it; the landing checks this with a grep of the diff against main and records the result."

**R3's grep.** `git diff main...HEAD` was run over `src`, `apps`, `migrations` and `scripts`, keeping only added and removed lines, and searched for `difficulty` (any case): **no line**. Over `tests` the search finds 2 lines. They are the `ADAPTIVE_DIFFICULTY_VERSIONS` version-pin set (the adaptive-difficulty successor set, gaining `mvp-0.54`), not the item's difficulty scalar. V3 adds no reader or writer of the scalar.

### Gate

Every pytest, vitest and npm run went through `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`. The full suite used 10G behind `flock /tmp/learnloop-fullsuite.lock`. Every Python or CLI run went through an `env -i` wrapper: `PATH`, plus empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`, with `TMPDIR` outside the worktree.

| Lane | On | Result |
|---|---|---|
| Setup | `uv sync --extra dev --extra mobile`, then `uv pip install --offline pypdfium2==5.14.0` | ok |
| Import contracts | `lint-imports --no-cache` | **43 kept, 0 broken** |
| Targeted set (step 2) | `12698bf8b8`, 291 files, `-n 6` (behind the lock). It covers: <br>• every `test_mobile_*`, `test_followup_*` and `test_te3b_*`, every `test_probe_*` and `test_diagnostic_probe_*`, `test_sidecar_probe` and `test_certification_cold_probe`; <br>• every file naming the FG1 claim or door (`claim_serve`, `followup_serve`, `generated_probe_closed`, `single_use`, `refuse_generated_probe_door`, `served_elsewhere`); <br>• every test file the branch changed (the version and head pins); <br>• every file naming `migration_head_250` or `discover_migrations`; <br>• `test_migrations`, `test_coordinated_migrations`, `test_tracked_fixture_databases`; <br>• the display-label audit (`test_sidecar_measurement`, `test_router_why_copy`, `test_key_ladder_labels`, `test_measurement_state_labels`, `test_rw5c_labels`); <br>• `test_cli_help_snapshot`, `test_architecture`, `test_desktop_rpc_contract`, `test_sidecar_serializer_snapshot`, `test_config_refactor`, `test_table_roles`, `test_public_tip_guards`, `test_sqlite_file_copies`, `test_mobile_allowlist`, `test_session_ownership`, `test_codex_lockdown_round3`, `test_codex_lockdown_frozen`, `test_registry_audit`, `test_module_catalog_inventory`, `test_hypothesis_marks`; <br>• the review's own 260-file set (`merged.txt`). | **5070 passed, 28 skipped, 6 xfailed, 0 failed** (30 min) |
| `--durable-sqlite` | the five `test_mobile_v3_*` files | **44 passed** |
| References (step 3) | `db_generate_reference.py` / `db_validate_reference.py`; `module_generate` / `module_validate`; `desktop_generate` / `desktop_validate`; `validate_vault.py` | All pass: `errors: []`; module catalog 1251 notes, links 41730/41730; desktop 323/323 plus 6/6 Rust, reproducible; vault 2244 notes. Committed in `315f250c7d`: the module notes for the Codex re-review's tests and changed docstrings, the `practice_attempts` / `probe_presentations` table notes, and the `practice` configuration note (30 files). Provenance-only churn was left out (521 notes). The validators were rerun on the committed tree and pass. |
| Config fingerprints | every `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entry against `defaults_fingerprint_for_version` | **45 of 45** equal; mvp-0.54 present |
| Full suite | `315f250c7d` (this record's commit adds only its text), `-n 8 --dist worksteal`, behind `flock /tmp/learnloop-fullsuite.lock`, 10G scope | **30152 passed, 90 skipped, 47 xfailed, 0 failed** (57 min 2 s) |
| Durability lane | `-m durability`, `-n 6` | **408 passed, 1 skipped** |
| Owner lane | fresh backup-API copies of `learnanything-ad1/fixtures-local/owner-copies-mvp035` in gitignored `fixtures-local/landing-phone-v3/`, `LEARNLOOP_OWNER_VAULTS`, `-m owner_vaults` | **83 passed, 4 skipped, 2 failed**: the two known (`test_activity_backfill.py::test_backfill_logs_attempt_duration_interaction_events`, `test_placement_fixture_copies.py::...[arxiv_v2]`); `owner-copies-mvp035` untouched |
| Phone app (`apps/learnloop-mobile`) | `npm run typecheck`; the whole `npx vitest run --maxWorkers=4`; `npm run build` | clean; **24 files, 289 passed**; built (run at step 2 and again on `315f250c7d`) |
| Desktop app (`apps/learnloop-tauri`) | `npm run typecheck`; the whole `npx vitest run --maxWorkers=4` (5G scope); `npm run frontend:build` | clean; **275 files, 2778 passed**; built. `src-tauri` is unchanged (as is everything under the desktop app), so no `cargo check`. |

No unexpected failure in any lane, so no rerun was needed. The known flakes did not occur.

### Smoke

**The copies.** Fresh backup-API copies of `~/learnloop-backups/mvp043-20261103-copy` went under gitignored `fixtures-local/landing-phone-v3-smoke/`. These are the owner's three vaults at mvp-0.43: `linear_algebra`, `probability` and `arxiv_v2`. Every `*base_url` in each copy's `learnloop.toml` was set to `http://127.0.0.1:9`. The copies were then upgraded in two steps:
- on main's code (`git archive` of `e9ceaf8d44` with its `migrations/`) to **mvp-0.53**, migration 249;
- a further copy of each on the branch's code to **mvp-0.54**, with migration 250 applied on open (`Upgraded vault: mvp-0.53 -> mvp-0.54`, `schema_migrations` max 250).

Every journey ran on its own further fresh copy.

**The harness** is in-process and adapted from phone V2's landing scripts:
- The phone used the real ASGI app (`learnloop_mobile.host.create_app`) through Starlette's `TestClient`, which binds no socket. It was paired by the real pairing exchange and sent the Serve identity header and `LearnLoop-Capabilities: phone_probes`.
- The desktop was a `SidecarContext` on the same database (a None origin). It reloads after the generated question is published, as the desktop app's watcher does.
- The fakes:
  - the router LLM and the Decider: `tests/router_model_fakes.py`, inline, with the seeds pinned by order;
  - the grader: the FG1 tests' `BlindRivalClient`, also used as the split diagnoser (as FG1's tests pair them);
  - FG1's probe author: `AuthorFake`, through `resolve_author_client`.
- Every other AI route stayed at 127.0.0.1:9, and no key was in the environment.
- The clock was frozen at `2026-11-07T09:00Z`, with deterministic ULIDs.
- An audit hook refused every inet `connect`, `bind` and `getaddrinfo`, and any Codex process. Its self-test refused both.

**The desktop at a None origin, main against the branch.** V2's journey ran on each mvp-0.53 copy, on main's code and on the branch's, with AD's background threads not scheduled on either tree. The journey: `get_daily_plan`, `start_session`, then `next_plan_item{serve}` with *I don't know* through the plan; *Keep going* once on the finished plan, then *Done for today*, then `end_session`. Every reply was compared, and every new row of nine tables, with ids renamed by first appearance and stamps normalized. The masks were V2's: `router_decisions.snapshot_hash`, `latency_ms` and `waited_ms`.

| | `linear_algebra` | `probability` | `arxiv_v2` |
|---|---|---|---|
| main against main | identical | identical | identical |
| main against the branch, as built | differs from the extension's first decision on: hash fields, the numeric arm's argmax, the logged propensities (the chosen block and the items served the same) | differs (14 fields) | differs (73 fields) |
| main against the branch, with the finished plan's stop-override receipt drawn where main draws it (before the build) | **identical** | **identical** | **identical** |

Why the as-built run differs, and why this is not a serving change:
- **The one code path behind the difference** is V3's commit 1 (`e64f19daf3`, the F9 class on a finished plan). *Keep going* on a `complete` plan now writes its stop-override receipt inside the transaction that inserts the extension, after `_prepare_plan`, where main wrote it before. The receipt is the same row. What moves is when its ULID is drawn: after the plan's id instead of before it.
- **Main's router is sensitive to that sequence.** Main's own code, with one extra id drawn before the journey, diverges from main on the same copy as much as the branch does (it serves different items).
- **The decision reads the receipt either way.** The decision's inputs that read stop receipts are the stop-accept prior (`objective_inputs._stop_accept`) and the stop coin. They are read at the first block's boundary (`_boundary`), after the insert commits, on both trees. `_prepare_plan` (classify, admit, split) reads no `session_receipts`.
- **Lining up the sequence closes the gap.** With the id sequence lined up and the branch's ordering kept, `linear_algebra` is identical except one block's `content_hash`. The two other copies keep differing only through the receipt's own id value, which orders the `stop_response` rows under the frozen clock (`ORDER BY created_at, id`).

So the desktop serves as main at a None origin, up to id-sequence noise. Real ULIDs are random, so two runs of main differ in the same way.

**At the tag, on each mvp-0.54 copy (branch).** Six journeys, each on a fresh copy: probe, held, abandon, cap, off, and below the tag. On all three copies:

| Check | Result (each copy) |
|---|---|
| The miss | A wrong answer on the phone, through the host's submit job. The diagnosis and FG1 generation ran on the host's shared post-attempt worker: one author call. The workflow was `ready`, lane `probe`, `surface = phone`. The question is a new `pi_gen_minimal_recall_*` item. |
| Before the serve | `followup_status`: the desktop's line, not V2's hand-off, and `held: true`. `get_feedback` held on both devices (no `feedbackMd`, no repairs). `record_answer_display` refused `followup_feedback_held`. |
| F1's race | The phone owns the session at the door's start, and the desktop adopts it before the claim (between `phone_claim_owner`'s pin and `_claim_refusal`). The door was refused **`session_moved`, nothing burned**. |
| Ownership, both directions | **The phone, not owning:** `get_practice_item`, `get_probe_contract`, `open_queue_item` and `next_plan_item` all `session_moved`, no burn. **The desktop, not owning:** `next_plan_item`, `submit_attempt` and `submit_dont_know` all `session_moved`, 0 attempts written, no burn. |
| Next opens it | The phone's `followup_next` answered `open` with the question. No burn before the serve. The serve burned it **as the phone's** (`generated_probe_burns`: `served`, `phone`, its presentation). |
| Cold on the phone | The contract: `active`, `phoneAnswers: true`, `forcedAttemptType: diagnostic_probe`, `followupWhy`, and every restriction on (hints, Ask/tutor, worked example, answer reveal, feedback deferred). A hint reveal was refused (the generated item has no authored hints: 422 `authoredIndex`; the in-suite test covers `diagnostic_block`), with 0 `help_assists` rows on the probe. The allowlist answered **403 for all 460 methods outside it**, including all 20 help methods: Ask, tutor, hint jobs, teach-back, `stop_probe_diagnosing`. |
| A second open | The phone's own re-open passes (the same administration). The desktop's `open_queue_item` was refused `generated_probe_closed`. Still held after the serve. |
| The answer | `submit_attempt` `diagnostic_probe` with its presentation: the workflow `settled`, `probe_answered`. The attempt is on `phone_practice`, naming the presentation. Feedback was released on both devices, the display is now allowed, and the answer's feedback points back at the miss (`heldFeedbackAttemptId`). |
| Never again | Refused `generated_probe_closed` on: the phone's `get_practice_item`, `open_queue_item` and `get_probe_contract`, and the desktop's `open_queue_item`. The phone's `followup_next` answered `continue`. Not listed on the phone. One `served` burn. |
| Cap boundary (copy with `session_qualifying_observation_cap = 1` and VOI stopping off) | The shared gate (`probe_serving_block_reason`) for the phone's session: open (`None`) before the phone's answer. After it: 1 qualifying observation and `session_cap_reached`. The owner's copies have no executable instrument, so a routine episode could not be entered and the phone's routine admission was not driven there. G10's in-transaction admission is pinned in the suite (`test_g10_*`, durable lane included). |
| Hint surface | A phone hint reveal on an ordinary item: `recorded`, `help_assists.surface = phone_practice`. |
| Held on the phone | A desktop miss, generated, and served on the desktop (`served`, `desktop`). The phone, after adopting: every door refused `generated_probe_closed`, `followup_next` answered `continue`, not listed, `deviceDeferredCount` ≥ 1. The phone's plan steps never served it. The desktop took the session back and answered it: `settled`. |
| Abandoned by the desktop | The phone's plan Next placed the question (R12), and the phone served it (`phone` burn) and left. The desktop adopted, and its serving Next went to the next item, not the probe. The probe: `retired`, the workflow `skipped`, reason `abandoned`, released (`continue_without_it`), feedback no longer held. The desktop's day then ran on to `done`. These workflows carried no router decision id, so no decision-outcome binding applied; the binding path is pinned in the suite. |
| `phone_probes` off (at the tag) | `meta` `phone_probes: false`. The status line is V2's hand-off. `followup_next` answered **409 `phone_probes_off`**, with `next_requested_at` unset and 0 workflow events. Every door refused `generated_probe_reserved`. A submit naming the presentation got 422. Nothing closed, not listed. The desktop still opened and burned it as its own. |
| Below the tag (mvp-0.53 copy, switch on, branch code) | `followup_next` answered `continue` and wrote nothing (0 events). Every door refused `generated_probe_reserved`. A submit naming the presentation was refused `validation_error`. Nothing closed. The desktop still served it. |
| Spend and processes | **0 receipts from a real model** (every new receipt is `fake` / `fake-frontier` / `fake_decider` / `fake_llm`). **No socket call. No Codex process.** The only processes were `git rev-parse HEAD` (data capture's stamp) and `powerprofilesctl get`. |

**Rebuild and sync** (each copy, after the probe journey):
- **`rebuild --shadow`, before the journey (a fresh mvp-0.54 copy):** mastery 21 / 18 / 34, facet 0, schedule 0. Every change is the `algorithm_version` stamp (mvp-0.46 to mvp-0.54): the known stamp-only rows.
- **After the journey:** 20 / 17 / 33, every one the same stamp only. The journey's LO was restamped live. Facet 0, schedule 0, 0 unaccounted attempts, live database unchanged.
- **Then `rebuild-derived-state` and a state sync (`sync_vault_state`):** the new rows are all identical before and after:
  - the `phone` burn;
  - the `phone_practice` `diagnostic_probe` attempt naming its presentation;
  - the `help_assists` row on `phone_practice`;
  - the settled workflow on `phone`;
  - the probe observation.
- **`rebuild --shadow` after that:** **0 / 0 / 0**.

### What the owner does

On carson, after the fast-forward. Vaults below mvp-0.53 climb the chain through `learnloop upgrade`.

```bash
cd ~/Documents/thinking/learnanything
.venv/bin/learnloop upgrade --vault ~/learnloop-vaults/<vault>        # each vault; default target mvp-0.54
# migration 250 (help_assists.surface gains phone_practice) applies when the vault opens
(cd apps/learnloop-mobile && npm install && npm run build)            # rebuild the PWA
systemctl --user restart learnloop-mobile                             # restart the phone host
.venv/bin/learnloop-mobile doctor
```

Rebuild the desktop app as for every landing. On the iPhone, tap *LearnLoop was updated. Reload*, then run **P6** (§6 above). **To turn it off:** add `phone_probes = false` to `~/.config/learnloop/mobile.toml` and restart `learnloop-mobile`. The phone then leaves every probe for the desktop, as in V2.

### Open items

1. **A desktop request naming a phone-owned session can claim the phone's ready question.** The desktop's doors check no session ownership on a read, unchanged from main. So a stale desktop practice screen that opens the item with the phone's session id burns it as the desktop's. It then behaves as a desktop-served probe: held on the phone, never served twice. The real desktop app shows the session as the phone's and offers to take it, so it doesn't send this. Smallest finish, if wanted: an ownership check on the desktop's generated-probe claim. That changes the desktop at a None origin, so it is the owner's call.
2. **A submit is not re-checked against the door.** The smoke's own harness sent a phone submit for a generated question whose door had refused it (no presentation; the PWA never sends this). It was accepted as a `diagnostic_probe` attempt and settled its workflow `probe_answered`. The submit path is unchanged by V3, but this was not reproduced on main's code. Smallest finish: refuse a submit on a generated probe served on another surface, or one with no open presentation.
3. **The finished plan's receipt now draws its id after the plan's.** The decision sees the same receipt (§ Smoke), so nothing changes in meaning. A byte-identity comparison against main needs the receipt's id lined up, or a mask.
4. **The routine probe's cap was not driven on the owner's copies,** which have no executable instrument. The shared gate and the in-suite G10 tests cover it.
5. **Carried from the stage:** §2 items 1, 3 and 6 (lesson probes and *Teach me instead* go to V6, per R2), and V2's `test_every_reply_carries_what_the_phone_reads` dependence on the queue's first row.

### Process notes

- **Patches.** No source or test file was patched at the landing. The only tracked change is the regenerated references (`315f250c7d`) and this record.
- **Copies.** The fixtures-local copies were made with `learnloop.db.copies` (backup API). The copies and the archived main code were deleted at the end.
- **The scratch scripts** (the smoke harness, comparisons and outputs) are in `/tmp/claude-1000/-home-saturn-Documents-thinking-learnanything/a22010cc-5149-4947-a2b8-247f18b8f1a0/scratchpad/phone-v3-landing/`, outside the worktree.
