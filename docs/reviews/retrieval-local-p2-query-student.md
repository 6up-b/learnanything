# Local contextual retrieval P2: the 0.6B query student (stage `retrieval-lr-p2-query-student`)

**Branch** `retrieval/lr-p2-query-student` (worktree `learnanything-lr1`), base `eaf9859ad`. **Spec** [spec_local_contextual_retrieval_v1](../specs/spec_local_contextual_retrieval_v1.md) §7.1, §7.2, §9.3, §10 P2, Q8, **Q9 as amended by the owner on 2026-10-26**. **No migration, no algorithm successor** (spec §4.5: a lookup is not an exposure; nothing here changes scoring, scheduling, projection, grading or serving of items). No real generation, no plan call, no teacher run and no real training was made in this stage; the only GPU process was the tiny random-initialised smoke test (below).

## The owner decision recorded (Q9, 2026-10-26)

"For P2, I think the distilled model should be 0.6b since that seems to be the small model for perplexity retrieval with a 9B parent model." Recorded in the spec's status line, §3.1, §7.1 (goal, candidate table, training budget, serving size) and the Q9 row:

* **Primary base** `perplexity-ai/pplx-embed-v1-0.6b` (Perplexity v1 lineage, bidirectional, mean pooling, no instruction prefix, MIT), pinned at revision `2c4d510dd4a732063c31a0f70193e35067b51fd8`.
* **Second (only other) screen arm** `Qwen/Qwen3-Embedding-0.6B` (last-token pooling, its own query instruction, Apache-2.0), pinned at `97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3`.
* **Dropped** `Qwen/Qwen3.5-0.8B-Base` (never downloaded, never screened; `student_pins.DROPPED_BASES`).
* `pplx-embed-v2-late-0.6b` is **not** a drop-in: it shares a space only with `pplx-embed-v2-late-9b`, a ColBERT multi-vector space (128-d per token, MaxSim), not our `context-9b` single-vector space. Successor S-b (a Perplexity small model in the v2 *context* space) stays as written.

**The two bases were downloaded** (allowed by the brief: public, ungated) into the HF cache at their pinned revisions, the ONNX exports and assets excluded: `~/.cache/huggingface/hub/models--perplexity-ai--pplx-embed-v1-0.6b/snapshots/2c4d510d…` (2.38 GB FP32 weights) and `~/.cache/huggingface/hub/models--Qwen--Qwen3-Embedding-0.6B/snapshots/97b0c614…` (1.19 GB BF16). Every file's size and SHA-256 is pinned in `local_embeddings/student_pins.py`. pplx's two remote-code files were **read**: `configuration.py` subclasses `Qwen3Config`; `modeling.py` subclasses `Qwen3Model` and turns causal masking off (bidirectional), nothing else. Its `st_quantize.py` (a sentence-transformers int8/binary quantizer module) is never imported and is pinned as `inert_python`; any other `.py` in a base directory is refused.

**The 9B teacher** is complete in the HF cache at the pinned revision (`…/models--perplexity-ai--pplx-embed-v2-context-9b-preview/snapshots/e2c06a779d45e8db53066735be1b98ffe3412ca3` = `pins.MODEL_REVISION`). It was not opened or modified; it is reached only through P1a's setup (`--adopt-model-dir`, which verifies without moving) and the worker. *Note on the owner's message:* it says the model was downloaded "to the learnanything directory"; the only copy found is the HF cache one above (the main checkout holds no model directory). The commands below adopt the HF cache path; if the owner put another copy elsewhere, adopt that path instead (setup verifies every file either way).

## What landed

| Piece | What | Where |
|---|---|---|
| Pins | The two 0.6B bases (repo, revision, every file's size and SHA-256, reviewed remote code, pooling, query prefix, licence); the student's identity (2048-d FP32 output, BF16 serving, query method); the recipes in spec order; the nested budgets 2k/10k/50k; leakage guards; the P2 GPU budget (6 h) and the memory floors and scopes; optimizer settings labelled numerical with their basis | `local_embeddings/student_pins.py` |
| Decision core | Functional core, numpy only. `U(a) = q + b − λm − μ·p_late − ν·h` over posterior draws; `argmax E[U]`, `P(best)` and the expected loss of acting now (§9.1). Bank posterior: per-arm family rates partially pooled by empirical Bayes, unknown labels imputed (latent), soft labels accepted (the interface a Dawid–Skene label model feeds). `λ` and `ν` learned from owner choices (Bayesian logistic choice model on a log grid), seeded from recorded owner decisions. The cold-start wait `P(in time) > 1/(1+w)` (no constant of its own). The learning-curve continuation rule | `local_embeddings/student_decision.py` |
| Synthetic questions (Q8) | Passages of consecutive **teaching**-class blocks (the window rule's policy classes: no exam, held-out, solution or assessment-lane block), the bank's gold supports left out of every passage; 8–12 questions per passage across `find_sources`' five intents and five shapes (plain, deictic with the selection carried as the Reader sends it, definition and theorem lookups, no-shared-vocabulary paraphrases); 5-gram leakage guard; family = source, one held-out family per vault (unseen-source test), a passage-disjoint tenth of the rest is development; stable ranks make the budgets nested; resumable by passage; protection re-read before every call; receipts in the vault (`retrieval_query_generation`) | `source_retrieval/student_data.py` |
| Generator route | New task `retrieval_query_generator`, code default **`chatgpt_luna`** (GPT-6 Luna on the plan) under T1's tier table (`codex_luna` in the legacy table). Runs under `plan_fallback.quiet()` (no offer, no grant) unless the command itself carries the owner's grant (`LEARNLOOP_AI_FALLBACK=openrouter`); a plan that cannot serve is reported with that instruction. A metered route needs `source_retrieval.llm_price_per_million` (in `METERED_PRICE_SETTINGS`, so no offer is made while it is unset) and is capped at `embedding.local.student_generator_max_cost_usd` ($5, keep) | `ai/routing.py`, `config/schema.py`, `ai/plan_fallback.py` |
| Teacher targets | ONE 9B worker batch in query mode (`encode_queries`, `[Q]`, mean pool) for every question and every bank question, written as **int8 `.npy` shards** by a new worker path (a 50k × 2048 JSON would be ~0.5 GB of Python ints in the app); finished shards survive an abort and only the rest is re-sent. Under the GPU lock and the full-suite lock, in the worker's 12G scope, on the **capped P2 meter** (6 GPU-hours). Canaries checked against the space's stored ones and the software epoch against setup's before anything is kept. The **teacher-cosine leakage guard** (≥ 0.90 to any bank question drops the synthetic one) runs here. Teacher and student are separate processes, one at a time, by the lock | `source_retrieval/query_student.py` (`run_targets`), `local_embeddings/worker.py` (`encode_query_shards`) |
| Trainer | One run, one recipe, one seed, then exit; in the separate env by path, the 9B worker's 12G scope and floors, network blocked, sampler and aborts reused. The student: the base with its own pooling and prefix, plus `Linear(hidden → 2048)` in FP32, L2-normalized FP32 output (never int8). Recipes in spec order: `projection_only` (base frozen), `align` (1 − cos), `align_kd` (+ KL over the teacher's top-50), `align_kd_mp` (+ multi-positive contrastive over every required support; negatives are the teacher's top-50 from training families, gold supports never present). Terms summed unweighted (any weight would be a made-up constant; the recipe itself is chosen by EU). The temperature is structural: the median spread of the teacher's own top-k scores on development. Diagnostics (never gates): median cos to the teacher, teacher top-10 agreement over the whole index, latency on the device and on the CPU, canary vectors per device class. The checkpoint (`student.safetensors` + `student.json`) is pinned by SHA-256 and moved under the space | `local_embeddings/student_trainer.py`, `query_student.install_checkpoint` |
| Schedule | `next_step` (pure): the screen (`projection_only` and `align` on pplx, `align` on Qwen3-Embedding at the screen budget) → base chosen by EU; recipes (`align_kd`, `align_kd_mp`) → recipe chosen by EU; the learning curve (small budget, then the large one only when its expected quality gain beats `ν × GPU-hours` inside the cap); the remaining seeds (≥ 3); then evaluate. A failed run blocks the schedule with its reason (it is charged; nothing retries silently). Every run is resumable and recorded in `p2-ledger.json`; its data files (book text, teacher vectors) are deleted after the run | `query_student.next_step`, `run_next` |
| Evaluation and adoption (§9.3) | The candidate through the **real query process** on the bank, beside the teacher's bank vectors, per stratum (all, deictic, logged, unseen family): `P(student ≥ teacher)` and the difference's 90% interval. **Recommended** when `E[U(student)] ≥ E[U(each alternative)]` and adopted by the owner (`student adopt`; review F5): the alternatives are what serves without a student (per-question outcomes the owner supplies with `--arm`, else E1's committed aggregates for Qwen R1 and Voyage R5, unpaired so wider); `μ` from a supplied keyword arm, else its upper bound; money from the vault's query receipts; lateness from measured latencies and cold starts. The adoption record holds the decision; `revoke` withdraws it | `query_student.evaluate`, `revoke` |
| Query process | `systemd-run --user --scope -p MemoryMax=4G -p MemorySwapMax=0`, started lazily by the first local query; JSON lines over a 0600 Unix socket in `$XDG_RUNTIME_DIR`; inet blocked; refuses outside a ≤ 4 GiB scope or under MemAvailable 6 GiB; GPU when ≥ 4 GiB VRAM is free and the GPU lock is free (it never takes the lock), else CPU; BF16; checkpoint files and digest verified, canary queries at start (cos ≥ 0.999 to the stored vectors of its device class) or it exits `canary_failed`; idle exit after `embedding.local.student_idle_minutes` (20, keep), immediate exit under the host floor. The app never imports torch | `local_embeddings/student_server.py`, `source_retrieval/student_encoder.py` |
| The resolver | `spaces.LOCAL_QUERY_ENCODER` is now the **adopted** student (else None: P1's `encoder_unavailable`). A cold student is started in the background; the query waits only when `P(in time) > 1/(1+w)` on the measured start times (`w` the local lists' seed weight share), else the local space is `encoder_late` for this query and the others serve. The list key carries the student's encoder id, so its fusion weight is learned like any list (§9.2) | `source_retrieval/spaces.py` |
| Nightly teacher replay (§9.3) | Every query the adopted student answers for a logged search is queued in `<vault>/.learnloop/student-replay.sqlite` (learner text stays local, outside `state.sqlite`, like the vector cache). The next index batch, which loads the 9B anyway, re-encodes the waiting queries (≤ 2,000, keep: GPU budget) and stores the teacher's and the student's top 10; a replay-only batch at most once a day. `replay_report` gives the agreement and the signalled spans each list held (biased toward the delivered student list: a lower bound on the teacher's advantage) | `student_encoder` (queue, report), `local_index` (`replay_sample`, `store_replay`) |
| CLI | `learnloop embeddings local student {setup, plan, generate, targets, train, evaluate, adopt, reject, revoke, status}`, every one with a dry run or read-only | `cli/embeddings.py` |

**Config** (`[embedding.local]`, modelled defaults): `student = true` (the kill switch; acts only once a checkpoint is adopted), `teacher_replay = true`, `student_idle_minutes = 20` (keep), `student_generator_max_cost_usd = 5.0` (keep); route `ai.routing.retrieval_query_generator` (unset: `chatgpt_luna`). All 24 defaults snapshots moved only because the effective config gained these keys and the route (recomputed by `defaults_fingerprint_for_version`); the decision-only template is unchanged.

## Kill switches and byte-identity

* `embedding.local.enabled = false` (default): nothing of P2 is reached; retrieval is P1's (and today's).
* `embedding.local.student = false`: no encoder (P1's `encoder_unavailable`), no process, no replay queue.
* No adoption record: the same. `learnloop embeddings local student revoke` removes it.
* `embedding.local.teacher_replay = false`: the student serves but nothing is queued and no replay is added to an index batch.
* With the default left at Qwen the student's seed weight is 0: a cold student is never waited for (it starts in the background for the next query) and Qwen's list serves exactly as before.

## No made-up constants (owner, 2026-10-24)

Every decision is expected utility over posterior draws; nothing is a margin. Priors and their basis are in `student_decision.PRIOR_BASIS`: family pooling (empirical Bayes), Jeffreys priors on lateness and agreement, the KT estimate of in-time starts, `λ` (log-normal at the rates the owner's recorded budget decisions imply: E0 $25 → $40, E1 $5, each for the 5-point stake it tested), `ν` (μ over the 6-hour P2 budget: the owner allotted at most 6 GPU-hours for all the quality a dense query encoder can bring; weak, by analogy), `μ` (bank R1 − R0 when supplied, else its upper bound), `b_local` = 0 (local was already optimal at an even posterior because it is cheaper), the learning curve (log-linear: errs toward training more), the dev quality (the teacher's bank quality times the agreement). Everything fixed is `keep` (identities, budgets, floors, leakage guards, provider-prompt sizes) or `numerical` (optimizer rates with their published basis, computation budgets) and is classified in `params/parameter_registry.py` (39 module constants, 2 config keys).

## Commands for the owner (none was run here)

The commands are the owner's, in a normal shell, on the owner's vaults (outside the checkout since S0) or on backup-API copies. Dry run first, every time.

```bash
# 0. P1a setup, adopting the teacher already in the HF cache (verified, never moved):
uv run learnloop embeddings local setup --dry-run
uv run learnloop embeddings local setup \
  --adopt-model-dir ~/.cache/huggingface/hub/models--perplexity-ai--pplx-embed-v2-context-9b-preview/snapshots/e2c06a779d45e8db53066735be1b98ffe3412ca3
#   (without --adopt-env-python this creates the separate env: Python 3.12, torch 2.14.0, transformers 5.18.0)
# 1. Index each vault (set embedding.local.enabled = true in its learnloop.toml first):
uv run learnloop embeddings local index --vault <vault> --dry-run
uv run learnloop embeddings local index --vault <vault> --now
# 2. The two student bases, adopted from the HF cache (or omit --adopt-base to download them):
uv run learnloop embeddings local student setup --dry-run
uv run learnloop embeddings local student setup \
  --adopt-base pplx-embed-v1-0.6b=$HOME/.cache/huggingface/hub/models--perplexity-ai--pplx-embed-v1-0.6b/snapshots/2c4d510dd4a732063c31a0f70193e35067b51fd8 \
  --adopt-base qwen3-embedding-0.6b=$HOME/.cache/huggingface/hub/models--Qwen--Qwen3-Embedding-0.6B/snapshots/97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3
# 3. The whole plan (no call, no GPU): questions reachable, plan calls, GPU-hours.
uv run learnloop embeddings local student plan --vault <vault> --bank <private E0/E1 bank JSON or JSONL>
# 4. Generation on the plan (GPT-6 Luna, quiet). Plan down: it reports; to use OpenRouter instead
#    (metered, <= $5, needs source_retrieval.llm_price_per_million) rerun with LEARNLOOP_AI_FALLBACK=openrouter.
uv run learnloop embeddings local student generate --vault <vault> --bank <bank> --dry-run
uv run learnloop embeddings local student generate --vault <vault> --bank <bank>
# 5. Teacher targets (one 9B batch per run, on the P2 meter):
uv run learnloop embeddings local student targets --vault <vault> --bank <bank> --dry-run
uv run learnloop embeddings local student targets --vault <vault> --bank <bank>
# 6. Train: rerun until it answers "evaluate" (each call is ONE run; --dry-run shows the next).
uv run learnloop embeddings local student train --vault <vault> --bank <bank> --dry-run
uv run learnloop embeddings local student train --vault <vault> --bank <bank>
# 7. Evaluate (the recommendation by expected utility over the MEASURED actions). --dry-run prints the
#    comparison fingerprint; a supplied alternative is {"comparison": <it>, "outcomes": {id: 1|0|null}} on every
#    in-scope question (E1's aggregates are reported as priors, never decided on). A corrected bank re-evaluates
#    the serving checkpoint (or any completed one: --checkpoint SHA) without retraining. Then answer it (the
#    owner's verdict, in judgment_ledger); no evaluation changes what serves by itself:
uv run learnloop embeddings local student evaluate --vault <vault> --bank <bank> --dry-run
uv run learnloop embeddings local student evaluate --vault <vault> --bank <bank> [--arm qwen=FILE --arm voyage=FILE --arm keyword=FILE] [--checkpoint SHA]
uv run learnloop embeddings local student adopt --vault <vault>     # or: student reject --vault <vault> (withdraws it if it serves)
uv run learnloop embeddings local student status --vault <vault>
```

The bank is the private E0/E1 bank file (its `private()` rows: `query_id`, `question`, `selected_passage`, `family`, `vault`, `origin`, `evidence_sets[].required`, `answer_spans`), read by key; it never enters a prompt or a loss. Without it, `generate`, `targets` and `train` refuse.

### Dry-run plan: time, GPU and plan-call estimates

These are estimates (labelled; the first real run's charged time replaces them). `student plan` prints them for the actual library.

| Step | Per 4,000-block book (≈ 1M recipe tokens) | Basis |
|---|---|---|
| Passages | ≈ 1,600 (≤ 600 estimated tokens of teaching text each) | the window rule's token estimate |
| Questions | ≈ 16,000 (8–12 per passage; ≈ 10% development, one source per vault held out) | spec §7.1 |
| Plan calls | ≈ 400 (4 passages a call), ≈ 7.5k tokens each on the plan's quota ($0 billed; `estimated_only`) | prompt + schema + 4k output budget |
| Plan wall time | ≈ 1.1–3.3 h a book, serial | 10–30 s a call (to be measured) |
| Teacher targets | 50k questions + the bank: ≈ 15 min GPU + the 25 s load, one batch | E1: 18 ms a query, BF16, resident |
| Screen (3 runs at 10k) | ≈ 1.5–2 min GPU each (471 steps) plus load | ≈ 0.15 s a 64-query step for a 0.6B forward+backward (unmeasured) |
| Recipes (2 runs at 10k) | ≈ 2–3 min each | KD adds the 50-document einsum |
| Learning curve (2k, then 50k only if worth it) | ≈ 1 min; ≈ 7–9 min | 2,344 steps at 50k |
| Seeds (2 more at the final budget) | ≈ 15–18 min at 50k | |
| **P2 total** | **≈ 0.9–1.2 GPU-hours** (cap 6, keep) | the P2 meter refuses a run with < 15 min left |

Memory: training uses the 9B worker's 12G scope and floors (MemAvailable ≥ 14 GiB, free VRAM ≥ 22 GiB, the workload rule); a full 0.6B fine-tune with FP32 master weights and AdamW is ≈ 9.5 GB on the device. The query process is 4G, BF16 ≈ 1.2 GB.

**Reachable budgets depend on the library.** The E0/E1 copies held 3 + 4 sources (≈ 700 blocks); at that size the 10k and 50k budgets collapse to what exists (the schedule uses the effective budgets: a budget above the data is the data), so the learning curve may have one point. More books, or the deferred logged Reader queries (spec §7.1 item 3), raise it.

## Calls and cost

* **Downloads:** the two 0.6B bases (public, ungated; ≈ 3.6 GB in total, ONNX and assets excluded) into the HF cache, at their pinned revisions, by `hf download`. The HF model API (public metadata) was read to find the revisions.
* **GPU:** one process: `tests/test_query_student_gpu.py`, a tiny random-initialised Qwen3 (2 layers, 32-d) trained 8 steps under the exclusive GPU lock (taken non-blocking), after checking MemAvailable ≥ 6 GiB and free VRAM ≥ 4 GiB: 94 MiB peak reserved, ≈ 16 s.
* **Paid or model calls:** none. No plan call, no OpenRouter call, no teacher load, no real training. Every Python run outside pytest used `env -i` with an empty HOME, CODEX_HOME and LEARNLOOP_CONFIG_DIR.

## Deviations from the spec, and why

1. **The bank posterior is a simplified P0.** P0's full model (Dawid–Skene label noise from the two blinded passes and the adjudications, MCMC) is still owed (P1 open question 2). Here: per-arm family-pooled Beta posteriors with latent unknowns, unjudged retrieved material latent, and soft labels (the interface a label-noise model feeds); paired structure unused (conservative for differences). **Because of that, the rule recommends and the owner adopts** (Codex review F5, [retrieval-lr-p2-query-student-codex-review](retrieval-lr-p2-query-student-codex-review.md)): `student evaluate` records the §9.3 recommendation with its posterior draws and a `judgment_ledger` verdict, `student adopt` / `student reject` is the owner's verdict (and, when the recommendation was costed against a measured alternative, an observation of λ). No evaluation changes what serves (Codex re-review F4/F5): a checkpoint that loses its re-evaluation gets a verifier `recommend_withdraw` verdict and the command to apply it (`student reject` / `student revoke`); unjudged retrieved blocks stay latent and are listed per question for labelling (`labels_owed`), with the expected loss of acting now, since §9.1's label-buying rule needs a label price P2 does not record. P0's posterior, when a stage supplies it, takes the authority back.
2. **Alternatives without per-question outcomes are labelled priors** (E1's committed aggregates: another corpus, other candidate units, the primary slice's denominator), never measured outcomes; a supplied `--arm` must cover the same in-scope questions (Codex review F4). A teacher-session alternative (P1c) is not an action: P1c is not built.
3. **The cold-start share uses the seed weights**, not a learned draw: with learned fusion on, a cold student whose seed share is 0 is still not waited for (conservative; it starts in the background).
4. **Real logged queries are not added to training** (spec §7.1 item 3, "can be added"): only the replay queue holds them, for evaluation.
5. **Replay sample size.** Every waiting query up to the keep cap is replayed: at 18 ms a query on an already loaded model the marginal cost is below any VOI threshold the rule could weigh; the VOI rule itself is P0's.
6. **No unseen-subject hold-out**: holding out one of two vaults halves the training data (open question 3).
7. **The trainer's tests need torch**, which the app environment has only with the `pdf` extra: under the gate's `uv sync --extra dev --extra mobile` the seven trainer tests skip and say so; they were run with the `pdf` extra (below).

## Open questions for the owner

1. Your message says the model was downloaded "to the learnanything directory"; the teacher found is in the HF cache (complete, pinned revision). Use that path for `setup --adopt-model-dir`, or name the other copy?
2. The bank file: which private E0/E1 bank file (under the E0/E1 `fixtures-local/` plan directories) should `--bank` name? It must carry the evidence sets.
3. Unseen-subject test: hold out a whole vault (halves the data) or keep the per-vault unseen-source hold-out only (built)?
4. P0's label-noise bank posterior: a separate stage before P2's evaluation, or accept this simplified posterior for the first adoption?

## Gate (this step; the full suite runs once in the landing gate)

Every pytest inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, one run at a time, `-n 6` at most.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok (re-synced to exactly this after the `pdf`-extra runs below) |
| `uv run lint-imports --no-cache` | **36 kept, 0 broken** (before and after the final fixes) |
| Targeted pytest, 186 files (below), `-n 6` | **4,347 passed, 6 failed, 36 skipped, 2 xfailed** (49 min 52 s) |
| The 6 failures | `test_codex_lockdown_round2.py` (3) and `test_codex_lockdown_round3.py::test_the_installed_codex_*` (3): they run the Codex CLI installed on this machine, which no longer reports the features `realtime_conversation`, `worktrees` under the isolated turn's overrides (`CodexLockdownUnavailable`). Environmental: `git diff eaf9859ad -- src/learnloop/ai/providers tests/test_codex_lockdown_round2.py` is empty, and this stage's only change to round 3 is the two approved launch sites. Rerun under `env -i` with existing empty HOME / CODEX_HOME / LEARNLOOP_CONFIG_DIR: the same 6 failed, 47 passed |
| After the final fixes: `test_query_student`, `test_source_space_resolver`, `test_local_index` | **58 passed, 7 skipped** (the trainer tests skip without torch) |
| After the final fixes: the 18 files that reach the resolver, the index job or P2 (below) | **301 passed, 3 failed (the same installed-Codex tests), 9 skipped** |
| After the final fixes: `test_registry_audit`, `test_architecture`, `test_config_refactor`, `test_cli_help_snapshot`, `test_diagnosis_input_provenance`, the launch-site audit, `test_e0_isolation`, `test_public_tip_guards` | **180 passed** |
| `test_query_student.py` with torch (`uv sync ... --extra pdf`) | **29 passed** (twice; one earlier run showed a start-status race, fixed: the starter's pid now lives beside the status file) and repeated 25 times without torch (22 passed, 7 skipped each) |
| GPU smoke `LEARNLOOP_GPU_SMOKE=1 tests/test_query_student_gpu.py` (tiny random-initialised model, under the GPU lock and the floors) | **1 passed** (8 steps, 94 MiB peak reserved; GPU p50 2.2 ms, CPU p50 0.14 s for the tiny model) |
| `-m durability` | not run: no migration and no DB/connection code changed (the replay queue is a file outside `state.sqlite` through the existing `connect`) |
| `db_generate_reference.py` / `db_validate_reference.py` (under `env -i`) | config leaves 1,054 → 1,059 (the four new keys and the route); 352 table notes regenerated (source-commit stamps); prose counts updated; **0 validation errors**. `module_validate.py` ok. `desktop_validate.py` fails on `apps/learnloop-tauri/src/components/pdfSelection/testing/syntheticBook.ts` (unclassified desktop source; not touched here, nothing under `apps/` changed) |
| Frontend / Tauri | unchanged: no npm, vitest or cargo step |

Targeted files (186): `test_ad1_codex_rereview_fixes.py`, `test_ad1_codex_review_fixes.py`, `test_ad23_owner_decisions.py`, `test_ad23_successor.py`, `test_ad23_t1_routes.py`, `test_ad2_model.py`, `test_ad3_dose_arm.py`, `test_adaptive_difficulty_ad1.py`, `test_ai_compare.py`, `test_ai_config.py`, `test_approach_map_replay.py`, `test_approach_maps.py`, `test_architecture.py`, `test_chatgpt_plan_cli.py`, `test_chatgpt_plan_landing.py`, `test_chatgpt_plan_provider.py`, `test_chatgpt_plan_sidecar.py`, `test_chatgpt_plan_workspace.py`, `test_cli_help_snapshot.py`, `test_codex_lockdown_round2.py`, `test_codex_lockdown_round3.py`, `test_compare_methods.py`, `test_config_refactor.py`, `test_constraint_engine.py`, `test_coordinated_migrations.py`, `test_daily_loop_start_minutes.py`, `test_daily_plan_replay.py`, `test_decider_client.py`, `test_decider_landing.py`, `test_desktop_rpc_contract.py`, `test_diagnosis_input_provenance_landing.py`, `test_diagnosis_input_provenance.py`, `test_diagnosis_replay.py`, `test_difficulty_band_guards.py`, `test_doctor.py`, `test_e0_isolation.py`, `test_e0_paid_fakes.py`, `test_e0_review_round1.py`, `test_e0_review_round2.py`, `test_e0_review_round3.py`, `test_e1_worker.py`, `test_embedding_route_isolation.py`, `test_evsi_calibration_sim.py`, `test_evsi_multisim.py`, `test_exam_protection_identity.py`, `test_exam_protection.py`, `test_exercise_arm.py`, `test_facet_identity_composition.py`, `test_facet_identity_ingest.py`, `test_facet_locks_landing.py`, `test_facet_reword_confirm_review.py`, `test_family_proposals.py`, `test_field_config.py`, `test_field_workbench_signals.py`, `test_figures_scope_redesign.py`, `test_find_sources_intents.py`, `test_glm_ocr.py`, `test_grading_cli.py`, `test_grading_hardcases.py`, `test_graph_nomination_ingest.py`, `test_hint_telemetry.py`, `test_ingest_m3.py`, `test_ingest_runner.py`, `test_intent_codex_rereview.py`, `test_item_fingerprints.py`, `test_judge_routes.py`, `test_kinship_feature.py`, `test_library_ask_expand.py`, `test_library_ask.py`, `test_library_exercises.py`, `test_local_fusion_core.py`, `test_local_index.py`, `test_lp_claim_fixes.py`, `test_mcp_c1a_narrow.py`, `test_mcp_c1a_review.py`, `test_mcp_cli.py`, `test_mcp_tools.py`, `test_method_explicit_landing.py`, `test_method_explicit_upgrade.py`, `test_method_phrasing_report.py`, `test_mobile_allowlist.py`, `test_mvp010_upgrade.py`, `test_mvp011_upgrade.py`, `test_mvp013_upgrade.py`, `test_mvp014_upgrade.py`, `test_mvp015_upgrade.py`, `test_mvp016_upgrade.py`, `test_mvp017_upgrade.py`, `test_mvp018_upgrade.py`, `test_mvp020_upgrade.py`, `test_mvp021_upgrade.py`, `test_mvp022_upgrade.py`, `test_mvp023_upgrade.py`, `test_mvp024_upgrade.py`, `test_native_media_readiness.py`, `test_openai_embedding_client.py`, `test_openrouter_video_client.py`, `test_open_world_gate.py`, `test_output_budget.py`, `test_p0_cutover_mvp08.py`, `test_pf_cli.py`, `test_plan_determinism.py`, `test_plan_first_transport_grant_scope.py`, `test_plan_first_transport_offer_grants.py`, `test_plan_first_transport_offer_grants_r5.py`, `test_plan_first_transport_paid_roles.py`, `test_plan_first_transport.py`, `test_plan_first_transport_today_quiet.py`, `test_plan_follows_path.py`, `test_practice_index_find.py`, `test_prescription_passages.py`, `test_probability_prep.py`, `test_project_cli.py`, `test_provider_resolution_parity.py`, `test_public_tip_guards.py`, `test_query_student_gpu.py`, `test_query_student.py`, `test_reader_find_sources_callers.py`, `test_reader_intentions.py`, `test_reader_intent.py`, `test_reader_rw1c_review.py`, `test_reader_rw2b_fix9.py`, `test_reader_rw2b_review.py`, `test_reader_rw3b_review_fixes.py`, `test_reader_tutor_offers.py`, `test_reader_tutor_retrieval.py`, `test_reading_paths.py`, `test_reading_step_switch.py`, `test_recurrence_benchmarks.py`, `test_recurrence_commands.py`, `test_recurrence_merge_composition.py`, `test_registry_audit.py`, `test_regrade_contract_successor.py`, `test_regrade_contract_upgrade.py`, `test_required_method_grading.py`, `test_required_method_round3_review.py`, `test_reread_safety_landing.py`, `test_reread_safety.py`, `test_retrieval_interventions_write_points.py`, `test_roles_switch_off_legacy_parity.py`, `test_roles_switch_off.py`, `test_router_offer_log.py`, `test_router_probe_ties.py`, `test_router_r2b_agreement.py`, `test_router_r2b_serving.py`, `test_route_rules_in_grader.py`, `test_rw2c_switch_off.py`, `test_section_coverage_review.py`, `test_section_coverage_rpcs.py`, `test_sensitivity_certificates.py`, `test_serve_eligibility_review.py`, `test_settings_sidecar.py`, `test_settings_store.py`, `test_sidecar_contract.py`, `test_sidecar_serializer_snapshot.py`, `test_source_block_fts.py`, `test_source_retrieval_codex_unavailable.py`, `test_source_retrieval_followup.py`, `test_source_retrieval_guards.py`, `test_source_retrieval_search.py`, `test_source_retrieval_tutor.py`, `test_source_roles.py`, `test_sources_merge_composition.py`, `test_source_space_resolver.py`, `test_sqlite_file_copies.py`, `test_stuck_prompt_replay.py`, `test_success_head_cli.py`, `test_t6_followup_review.py`, `test_table_roles.py`, `test_teacher_te0_review_fixes.py`, `test_tier1_decider.py`, `test_tool_dispatch_policy.py`, `test_tool_registry.py`, `test_tool_results_withhold_answers.py`, `test_tools_cli.py`, `test_tracked_fixture_databases.py`, `test_tutor_tool_requests.py`, `test_ux_phase1_connect_ai.py`, `test_ux_phase1_round2_review.py`, `test_ux_phase2_shell.py`, `test_ux_phase4_feedback.py`, `test_voi_merge_composition.py`, `test_voi_stopping.py`, `test_voi_v2.py`, `test_voyage_fallback.py`, `test_workbench_route_example.py`.

Post-fix subset (18): `test_architecture.py`, `test_codex_lockdown_round3.py`, `test_e0_review_round3.py`, `test_exercise_arm.py`, `test_local_index.py`, `test_numeric.py`, `test_query_student.py`, `test_query_student_gpu.py`, `test_reader_rw3b_review_fixes.py`, `test_roles_switch_off_legacy_parity.py`, `test_section_coverage_review.py`, `test_simulation.py`, `test_source_retrieval_followup.py`, `test_source_retrieval_guards.py`, `test_source_retrieval_search.py`, `test_source_roles.py`, `test_source_space_resolver.py`, `test_t6_followup_review.py`.

## Landing onto main (batch 3: Reader CA2 + Reader RW5d P1 + local retrieval P2, 2026-10-26)

The three stages land together (owner-approved batch landing) on `merge/batch3-onto-main` in `learnanything-merge2`,
cut from `main` at `1335df0c0` (latest `mvp-0.34`, migrations through 222, head fixture `migration_head_222`, Reader
CA1 just landed). Main was neither fast-forwarded nor pushed. The same section is appended to all three stages'
records; the stage-specific owner notes and open items are at the end.

### Commits and conflicts

| Commit | What |
|---|---|
| `043463103` | `--no-ff` merge of `reader/ca2-one-ask` (`ebfbfe7e5`, base `eae00d58a`). Conflicts composed keeping both sides: `algorithm_versions.py` (the chain gains `ONE_ASK_ALGORITHM_VERSION` after `REPLAY_LEDGER_ALGORITHM_VERSION`), `cli/app.py` (help text, `--to` dispatch, refusal text name 0.33, 0.34 and 0.35), `config/schema.py` (`ReplayConfig` and `AskConfig`), `template.py` (23 snapshot hunks: main's notes kept, CA2's note added, renumbered "inert below mvp-0.35"), `parameter_registry.py` (C0a's and CA2's rules), `sidecar/context.py`, `handlers/practice.py`, `handlers/sessions.py` (CA1's `pageSeen` and CA2's `earlierOpened` draft flags side by side: `_with_keyed_flag` and `_with_earlier_opened`, `draft_page_seen` and the earlier-marker helpers), `api/client.ts`, `PracticeScreen.tsx` (CA1's as-printed imports and `OpenInSource` modal beside CA2's `DockedAsk`; the book component stays `bookCarried \|\| pageSeen`, CA2's `earlierCounted` beside it; both draft flags in the checkpoint and its deps), 45 test files (main's absolute chain indices and head paths kept; the version pins moved below), the reference notes (main's side, then regenerated). CA2's `migrations/221_workbench_earlier_opened.sql` renamed **223**; its `fixtures/migration_head_221` dropped (main's 222 kept for the rebuild). CA2's `one_ask_upgrade.py` rewritten to the journalled activation (below). The stale practice-cap wording fixed (below). |
| `bdd511fa6` | `--no-ff` merge of `reader/rw5d-p1-show-me` (`33b9aa5d8`, base `eaf9859ad`). Conflicts: `template.py` (24 hunks, RW5d's `[figures] show_me_enabled` note on every tag), `AskRail.tsx` (CA2's Enter-sends branch and RW5d's `alt+Enter` *show me ▸* branch both kept, CA2's `enterSends` label kept on the ask button, RW5d's show-me row and thread lines after it), `tests/test_mobile_allowlist.py` (the desktop-only list names both `READER_CA1_RPCS` and `READER_RW5D_RPCS`; CA2 adds no RPC). Migration 224 keeps its number. |
| `54aef20c7` | `fixtures/migration_head_224` **rebuilt** from main's tracked, sanitized `migration_head_222/state.sqlite`: a backup-API copy, 223 then 224 applied under `UPGRADE_SCRATCH_COPY`, `wal_checkpoint(TRUNCATE)` (0, 0, 0), `journal_mode=DELETE` (header bytes 1/1), integrity ok, `foreign_key_check` empty, copied into place with the backup API, no companion files. Every table's rows equal main's 222 except `schema_migrations` (+223, +224); against RW5d's own head only `workbench_sessions` differs. Git records it as the rename `migration_head_222 -> migration_head_224`; README updated. |
| `de25dd4fa` | Earlier migrations' schema-diff tests through 223 + 224 (`[..., 222, 223, 224]`, `CA2_ALTERED_TABLES = {"workbench_sessions"}` beside RW5d's sets); CA2's migration test renumbered `test_223_adds_only_the_earlier_opening_column` (from 222, applies [223, 224], head 224); chain pins at mvp-0.35; all 26 defaults fingerprints recomputed (template `.pyc` cleared). |
| `88ac84275` | `--no-ff` merge of `retrieval/lr-p2-query-student` (`3d3755578`, base `eaf9859ad`). Conflicts: `parameter_registry.py` (RW5d's `figure_admission` and LR P2's four module owners), `template.py` (24 hunks, LR P2's `[embedding.local]` student keys and route note on every tag). Fingerprints recomputed again (26, from the composed defaults). |
| `930abc06e` | References and CLI help (below). |
| `867f7934a` | `tests/test_batch3_landing.py`: the chain and journal tests and interactions (i)-(iv); the activation journal's docstring names `one_ask_upgrade`. |
| `9a3dbdeba` | The last tests pinning mvp-0.34 as the latest (LP claim fixes' version set, rebuild equivalence's bare upgrade, mvp-0.18's default target); version comments. |

`main` and all three stage tips (`ebfbfe7e5`, `33b9aa5d8`, `3d3755578`) are ancestors of the tip. Against main the diff
adds **no tracked database or binary apart from the head fixture rename** (`git diff --numstat -M main` lists only
`fixtures/{migration_head_222 => migration_head_224}/state.sqlite` as binary); the root `.gitignore` is unchanged.

### Renumbering and the chain

- `ONE_ASK_ALGORITHM_VERSION = "mvp-0.35"`, after `REPLAY_LEDGER_ALGORITHM_VERSION` (`mvp-0.34`, rebuild equivalence;
  `mvp-0.33` is the LP claim fixes). `LATEST_ALGORITHM_VERSION` is `mvp-0.35`; `ONE_ASK_VERSIONS == {"mvp-0.35"}`; the
  snapshot `mvp-0.35` is recorded; the earlier `*_VERSIONS` sets each gain `mvp-0.35`.
- `one_ask_upgrade.py` now follows `replay_ledger_upgrade.py`: `PREDECESSOR = mvp-0.34`, the chained predecessors
  `mvp-0.9 .. mvp-0.33` go through `upgrade_to_replay_ledger` first; the activation is ONE `BEGIN IMMEDIATE`
  transaction under the vault mutation lock (the predecessor's manifest, `activate_p0_projection`, the registry
  refresh, the journal (`predecessor`, `target`) at the shared `<db>.claim-fixes-activation` path, the durable
  publication last); the completion marker is the `p0_projection_activation` receipt under the tag. Its
  `complete_interrupted_activation` completes a journal naming mvp-0.35 and hands any other to rebuild equivalence's
  (which hands an mvp-0.33 journal on). The CLI (`cli/runtime.py`) and the desktop sidecar (`sidecar/context.py`) now
  install `one_ask_upgrade.complete_interrupted_activation`, the chain's latest.
- `learnloop upgrade --to mvp-0.35` works from mvp-0.9, 0.27, 0.29, 0.30, 0.31, 0.32, 0.33 and 0.34
  (`test_upgrade_to_mvp035_works_from_every_supported_version`, 8 cases); the bare `upgrade` targets mvp-0.35. The
  upgrade's help and refusal text name every tag; `tests/cli_help_snapshot.json` changed only for `upgrade`.
- New keys move no unrelated version hash: `test_eval_harness.py`, `test_success_head*.py` and the field arm tests pass
  as merged (the arm hashes read `[mastery]` only).

### The practice Ask cap (fixed at landing; owner decisions 2026-10-26)

`config/template.py`'s `[tutor_qa]` comment and `TutorQAConfig`'s description said practice was "per item+session".
They now say: **per attempt; enforced on metered routes; unlimited on the subscription (ChatGPT plan) route while
`[ask] panel_enabled`** (off, the cap applies on every route). The cap stays `max_questions_practice = 3` in
`<vault>/learnloop.toml` `[tutor_qa]`, beside `max_questions_feedback` (per attempt), `max_questions_library` (per note
per UTC day) and `max_questions_reader` (per span per UTC day). The code (`tutor_qa.question_usage(metered=...)`) was
already CA2's final rule; no behaviour changed.

### Interactions (`tests/test_batch3_landing.py`; no break found, so no fix)

- **(i) CA2's cap vs RW5d's *show me*.** RW5d's spec §6.2 sends the Ask rail's text "as a figure goal instead of a
  question"; CA2's K5 cap counts question events. A tutor `figure_goal` press and an Ask-rail *show me* each build a
  figure, write no `question_events` row and leave the practice and library budgets as they were, at mvp-0.35 with the
  panel on (`test_i_...`). P3's Ask-panel *show me* (a figure as a hint-equivalent) is not built yet.
- **(ii) CA2's `earlier_opened_at` vs CA1 and rebuild equivalence.** The column is LIFECYCLE state on a WORKFLOW table;
  replay never reads it. A workbench submit with an earlier opening carried into steps rebuilds exactly as the same
  submit without it: mastery 0, facets 0 (`test_ii_...`). **Finding (pre-existing on main, not the batch):** on that
  real-clock sidecar path the shadow rebuild moves the submitted item's `due_at` by 1 s (live 1 s later): reproduced
  3/3 on `git archive main` at mvp-0.34 with a plain workbench submit. The owner parity below (frozen clocks) is 0/0/0.
  CA1's as-printed page reads and writes no learner state (its parity stands).
- **(iii) T1's offer keying vs CA2's routes.** A grant given on `figure.request` (even naming `tutor_qa`) never routes
  CA2's Ask (`ask_tutor_question`) to OpenRouter; a grant given on the Ask itself routes it to OpenRouter, which is
  metered (`is_subscription_transport` false), so the per-attempt cap applies there; the plan route stays unlimited
  with the panel on (`test_iii_...`; fake OpenAI client, nothing sent).
- **(iv) LR P2's resolver vs RW5d's grounding.** RW5d grounds a goal through `find_sources_for_caller`. With an adopted
  (fake) student behind `spaces.LOCAL_QUERY_ENCODER` and `default = "local:grouped"`, the hook is live (it tries to start
  the query process); with `embedding.local.student = false` it starts nothing and the grounding retrieval's status and
  hits equal P1's empty hook exactly (`test_iv_...`).

### Regeneration

- `db_generate_reference.py` then `db_validate_reference.py`: **errors []** after the prose counts were updated by hand
  (Configuration.md and Database.md: **1,064 leaves in 74 sections, 353 table notes**). No new `CONFIG_SECTION_FUNCTIONS`
  entry was needed (CA2 brought `ask`; `figures` and `embedding.local` existed). ~425 other note changes are
  `source_commit` stamps.
- `validate_vault.py`: passed (1,161 notes).
- `tests/cli_help_snapshot.json`: `upgrade` only. RPC contract, serializer snapshot and mobile allowlist pass as merged.

### Gate (at `9a3dbdeba`; `env -i`, empty `HOME`, `CODEX_HOME`, `LEARNLOOP_CONFIG_DIR`; logs in `fixtures-local/landing-batch3/logs/`)

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile` (+ `uv pip install pypdfium2`), 5G scopes; `lint-imports --no-cache` | **36 kept**, 0 broken |
| targeted run (104 files: every stage's tests, the chain/migration/pin files, contracts), `-n 6`, 5G | 2,188 passed, 3 failed (stale latest-version pins, fixed in `9a3dbdeba`, 42 passed on rerun), 25 skipped, 3 xfailed, 26 min |
| `tests/test_batch3_landing.py` | 24 passed |
| full suite (`flock`, 10G/2G scope, `pytest -n 8 --dist worksteal --durations=50`) | **NOT COMPLETED.** Started 20:18:49 after waiting for the thread-leak stage's lock; reached 99% by 21:06:40, then no line was written. One worker held ~737 threads at ~1,100% CPU (the known leaked-thread class); it was SIGKILLed at 21:36 as a worker of this run, but xdist never replaced it and the other 7 workers sat idle in `futex_wait` (load ~0.6): a hang, not slow tests. The progress lines show 16 `F` marks before the hang; with `-q` the names print only at the end, so they are unknown. Killing the rest of the run's process tree was **refused by the permission layer**, so per the brief the gate stopped there: the lock is still held by that hung run, and the requested rerun (`-o faulthandler_timeout=600 --junitxml=full.xml`) and the durability lane were not run. Wall time and the 50 slowest tests are therefore not available. |
| Codex lockdown on main's tree (`git archive main`, alone) | the same 10 fail on codex-cli 0.164.0: `test_codex_isolation_mcp_check` ×3, `test_codex_lockdown_round2` ×3, `test_codex_lockdown_round3` ×3, `test_diagnosis_isolation::test_configured_mcp_servers_are_listed_and_disabled` |
| torch lane (`uv sync ... --extra pdf`; `tests/test_query_student.py` + `_gpu.py`; then the standard extras re-synced, torch gone) | 50 passed, 1 skipped (the GPU smoke) |
| owner lane (`-m owner_vaults`, backup-API copies of the three mvp030 backups in `fixtures-local/owner-lane-batch3/`) | 83 passed, **6 failed: exactly the 6 known** (`test_doctor` pre-044, `test_migrate_fresh` 153, `test_goal_decay_projection`, `test_sidecar_contract` recent ingests, `test_activity_backfill`, `test_placement_fixture_copies[arxiv_v2]`); 0 `model_call_receipts` |
| `npm install` (esbuild's postinstall blocked as before), `npm run typecheck` | clean |
| `npm test -- --maxWorkers=4` (whole vitest) | **221 files, 1,917 tests passed** (61 s) |
| `npm run frontend:build`; `cargo check` | built (the usual chunk-size warning); finished |
| empty dirs | `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR` stayed empty; `HOME` gained `.nv/ComputeCache` and `.local/share` (the torch lane's CUDA cache and a tool cache) |

### Parity (backup-API copies of the mvp030 backups; `fixtures-local/landing-batch3/`, scripts in `scripts/`)

Setup: `orig/` = backup-API copies of `learnanything/fixtures-local/vault-backups-20261025-mvp030/{linear_algebra,probability}`;
`u34/` = `orig` brought to **mvp-0.34 with main's code** (routes to the `127.0.0.1:9` blackhole, 64 tasks on main and 65
on the merge (LR P2's `retrieval_query_generator`), none outside it; `upgrade --to mvp-0.34`, `rebuild-derived-state` ×2).
`code_main` = `git archive 1335df0c0`, `code_merge` = `git archive 867f7934a` (src and migrations unchanged since). Every
run through `env -i` with empty dirs; `run.py`'s audit hook refuses Codex process starts and non-loopback sockets.

- **(a) main vs merge at mvp-0.34** (after the primary sidecar load; a second main copy as the noise control): every
  row of all 357 common tables identical (18,806 rows LA, 8,195 probability); the merge adds only 224's objects
  (`figure_requests` empty, its indexes and triggers) and the new columns (`interactive_figures` ×12,
  `workbench_sessions.earlier_opened_at`), all NULL; `schema_migrations` +223, +224, common rows identical; integrity
  ok, foreign keys 0, `model_call_receipts` 0. Certification, Today and the plan **byte-identical** main vs merge (and
  main vs main). `rebuild --shadow` **0/0/0** both sides; `doctor` identical (57/1 LA, 101/48 probability, pre-existing).
- **(b) `upgrade --to mvp-0.35`** (the merge's code, on copies of u34): "mvp-0.34 -> mvp-0.35", no journal left. **Rows:
  every row kept; mastery and every schedule unchanged (0 LOs, 0 items moved).** What changes, exactly: the
  `algorithm_version` stamp (0.34 -> 0.35) and `updated_at`/`created_at` of `facet_recall_state` (76 / 2 rows) and
  `facet_capability_evidence` (36 / 1) (DERIVED, the projection activation), `parameter_registry.updated_at` (352, the
  refresh), plus one `derived_state_rebuilds` (`p0_projection_activation`), one `parameter_registry_manifests` row.
  Shadow right after the upgrade: facet 0, **mastery 21 / 18 = the `mastery_state` version stamp only** (no value moves),
  schedule 0, as at RW7b's projection-only activation; after `rebuild-derived-state` ×2: **0/0/0**; doctor unchanged.
  After a primary load + 12 live attempts (frozen clock): **0/0/0**. Bare `upgrade` -> mvp-0.35. From the mvp-0.30
  backup straight `--to mvp-0.35` (chains through 0.31-0.34) and the owner's two steps (`--to mvp-0.34`, then
  `--to mvp-0.35`), rebuilt: **0/0/0**, doctor unchanged. **Nothing changes until CA2 is used.**
- **(c) the kill switches** (`[ask] panel_enabled`, `cold_help_converts`, `[figures] show_me_enabled`,
  `[embedding.local] student` all false): set before the upgrade (k35), or after an on upgrade then rebuilt (kr35),
  versus the merge's mvp-0.34 copy: certification, Today, mastery and every schedule identical after the version
  stamp; the plan identical except 7 hashes over the versioned card (`card_hash`, `snapshot_hash`), exactly as the
  rbeq landing recorded for its tag; the switches-on copy (on35) the same. (a) shows the merge at mvp-0.34 equals main.
- **(d) an interrupted mvp-0.35 activation** (the upgrade dies with `os._exit(17)` after the config publication):
  label mvp-0.35, journal present, the predecessor's mastery untouched. `upgrade --to mvp-0.35` completes it ("completed
  the interrupted activation of mvp-0.35"; again: "vault is already mvp-0.35"); the desktop start completes it; both
  equal the clean upgrade (0 LOs moved). Every attach that may not complete it refuses with "The upgrade to mvp-0.35
  did not finish ... run `learnloop upgrade --to mvp-0.35`" (`Repository`, `open_vault_repository` without a
  completer, the secondary attach, and the remote schema check as `SchemaMismatch`), leaving the vault as it was. Plain
  `doctor --json` is a read-only attach and refuses too (the journal stays), as recorded at the LP and rbeq landings.
- **Receipts and calls.** The 42 parity databases with a receipts table and the 3 owner-lane copies hold **0
  `model_call_receipts`** (the other 21 files are the probability backup's empty `.learnloop/state.sqlite` stubs); no
  audit-log line (no process start, no socket). **Spend: $0.** Nothing under `~/learnloop-vaults`, `~/learnloop-retired`
  or `~/learnloop-books` was opened or listed.

### Owner notes

- **Before upgrading:** back up the vaults; close the desktop app, the MCP server and the phone page. Then
  `learnloop upgrade --to mvp-0.35 --vault <vault>` (or the bare `learnloop upgrade`); from mvp-0.30 it chains through
  0.31-0.34 (mvp-0.34's step is the whole-vault rebuild). Migrations 223 and 224 apply on the first open.
- **Kill switches (`<vault>/learnloop.toml`):** `[ask] panel_enabled = false` (the overlay and per-source answer mode
  as before), `[ask] cold_help_converts = false` (the predecessor's cold rules, no downgrade), `[figures]
  show_me_enabled = false` (RW5b's figures exactly), `[embedding.local] student = false` (the query student never
  serves; P1's retrieval).
- **The practice Ask cap:** `[tutor_qa] max_questions_practice` (default 3) per attempt on metered routes; unlimited on
  the ChatGPT plan route while the panel is on.
- **Local retrieval P2 stays off until you run its setup** (`docs/reviews/retrieval-local-p2-query-student.md`,
  "Commands for the owner"): `embeddings local setup` (adopting the cached 9B), `embeddings local index`,
  `embeddings local student setup` (adopting the two 0.6B bases), then `student plan`, `generate`, `targets`, `train`,
  `evaluate`, `adopt` / `reject`, `status`, each with `--dry-run` first.

### Open items

- **The full suite and the durability lane are not done.** The run hung at 99% (leaked-thread workers deadlocked); the
  kill of its process tree was refused by the permission layer, so the lock is still held by it. Owner/coordinator:
  end that run (`fixtures-local/landing-batch3/scripts/fullsuite.sh`'s tree), then rerun once with
  `-o faulthandler_timeout=600 --junitxml=fixtures-local/landing-batch3/logs/full.xml`, then `-m durability`, and
  record the hung tests' stacks, wall time and the 50 slowest here. Do not land before that.
- **Low (pre-existing, main):** a real-clock workbench submit leaves `practice_item_state.due_at` 1 s later than a
  rebuild computes (interaction (ii)); frozen-clock parity is 0/0/0.
- **Low (recorded since LP):** `doctor --json` refuses an interrupted activation rather than completing it.

### Open items for local retrieval P2

- No migration, no successor; off until the owner's setup above (no adopted student = P1's retrieval, interaction (iv)).
- The torch lane ran at landing: `tests/test_query_student.py` + `_gpu.py`, 50 passed, 1 skipped (GPU smoke), under the
  temporary `--extra pdf` sync; the standard extras were re-synced after.
- Still open from the stage: the owner's questions in "Open questions for the owner".
