# Experiment E1 harness: local pplx v2-context-9b (preview), BF16 batch pilot

**Branch:** `experiments/e1-local-v2` (worktree `learnanything-e1`, base: E0's tip `91792831b`). The spec is `docs/specs/spec_contextual_source_embeddings_experiments_v1.md`: §8 (E1), §9 (deferred precision work), §7 and D2.

**Owner decisions:**

- E1 runs regardless of S4 (2026-10-21).
- "Proceed to E1" (2026-10-23).
- E1 reuses E0's bank and labels.

**What this phase did:** it built and tested the harness only.

- No model was downloaded.
- torch never ran on the GPU. The app process never imports torch.
- No paid or live call was made. The only network reads were public Hugging Face and PyPI pages, used for the research below.
- Nothing in the e0 worktree was written. E0's relabel run (`e0_e6a077cd391c5421`) finished while this harness was being built. Both copies are `complete` and S1 is `labels_ok`, with κ 0.657 (linear algebra) and 0.648 (probability).
- E1 then imported that run's outputs into its own `fixtures-local`. The import reads E0 and never writes to it; databases are copied through the backup API.

## 1 The model, researched from public pages only

| Fact | Value | Source |
|---|---|---|
| Repo id | **`perplexity-ai/pplx-embed-v2-context-9b-preview`**. No repo named exactly "v2-context-9b" exists; there is no non-preview v2 context model and no smaller v2 context size | HF API `api/models?author=perplexity-ai` |
| Revision pinned | `e2c06a779d45e8db53066735be1b98ffe3412ca3`, the 2026-10-08 card edit. The modeling code changed on 2026-09-30 (binary/ubinary outputs removed) | HF API, commits |
| Licence and terms | MIT in the card metadata. No LICENSE file, not gated, no use restrictions. The card warns that the preview's weights, embeddings and interface may change and that its embeddings must not be mixed with a future release | model card |
| Size | 8,401,083,632 parameters stored in **FP32**: 7 shards plus a 33.5 MB `contextual_head.safetensors`. **33,624,493,388 bytes** across the files E1 needs (33.6 GB, 31.3 GiB) | `model.safetensors.index.json`, API siblings |
| Architecture | Qwen3.5 (`PplxContextualModel(Qwen3_5Model)`), 32 layers in a repeating pattern of 3 Gated-DeltaNet linear-attention layers then 1 full-attention layer (24 + 8). Hidden size 4096, 16 heads / 4 KV heads, head dim 256, vocabulary 248,320, `is_causal: false`. The unused Qwen3.5 vision tower (~0.4B parameters) ships in the weights | `config.json` |
| Output | One 2048-d vector per chunk, from a bias-free fp32 `Linear(4096→2048)` kept in fp32. Values are `round(tanh(x)·127)`: int8-valued float32, unnormalized. Matryoshka 1024 is the first 1024 values, then normalize; no other widths were trained | remote code, card |
| Software | `transformers>=5.4.0`, torch, numpy, safetensors, tqdm, `trust_remote_code=True`. Not sentence-transformers. `config.json` says `transformers_version: 5.3.0` | card |
| Hosted v2 | None yet; the blog says Perplexity is "working on" API availability | Perplexity blog, 2026-09-30 |

### What the remote code does

I read both files in full: `configuration_pplx_contextual.py` (852 B) and `modeling_pplx_contextual.py` (9,318 B). Their SHA-256 values are pinned, and the worker refuses any other code.

- **The config** only adds fields to `Qwen3_5Config`: `embedding_dim`, the `query_prefix "[Q] "`, the `document_prefix "[D] "`, the `boundary_marker "<|chunk_sep|>"` and the query/document length limits. It also sets `use_cache=False`.
- **Documents: `encode(list[list[str]])`.**
  - Each document is built as one string: `"[D] " + c0 + "<|chunk_sep|>" + c1 + …`, with right padding.
  - Each chunk's character span is mapped to its tokens through the tokenizer's offset mapping.
  - **One forward pass** covers the whole document, so chunks attend to each other.
  - Each chunk is mean-pooled over **its own token span only**, using an fp32 cumulative sum, then projected.
  - Nothing is truncated. An input over the limit raises "split the document into context windows"; a non-empty chunk that yields no tokens also raises.
- **Queries: `encode_queries([[q]])`.**
  - Each row must hold exactly one string.
  - The `[Q] ` token id (248077) is prepended, and the pool is a mean over all tokens.
  - The card warns: "encoding queries with `encode` silently degrades retrieval quality."
- **Security.** There is no eval/exec, subprocess, pickle, extra download or file write (except `save_pretrained`, which E1 never calls).
  - The only network path is the lazy `AutoTokenizer.from_pretrained(config._name_or_path, revision=_commit_hash)`. Loaded from a local directory, it reads that directory.
  - The worker also sets the offline flags and blocks sockets.
- **An asymmetry that is probably harmless.**
  - Both tokenizer calls pass `split_special_tokens=True`, and `"[D] "` is a special token. So the document prefix is likely tokenized as plain text, while the query prefix is inserted by id.
  - This may be how the model was trained. It is recorded here, and E1 uses the model's own methods without reimplementing them.

### Where the spec differs from what the research found

- **Every reported item checks out:**
  - separate query and document methods with the `[Q] `/`[D] ` prefixes;
  - 2048/1024 widths and unnormalized int8-valued output;
  - preview risk and the FP32 contextual projection;
  - MIT, the vision tower, 24/32 linear-attention layers and ~33.6 GB FP32;
  - no sentence-transformers path and transformers ≥5.4.
- **New facts:**
  - The model card's own example passes **no dtype**. At FP32 the weights alone (33.6 GB) exceed the 5090's 32 GB, so E1 passes `dtype=bfloat16` explicitly. BF16 weights come to about 16.8 GB.
  - `max_position_embeddings` is 262,144 in `config.json`. E1 caps its own documents at 8,192 tokens.
  - Binary output is gone; only int8 remains.
- **An unverified risk:** the card names no kernels. My understanding (not verified) is that transformers' Qwen3.5 linear attention runs fast only with flash-linear-attention or causal-conv1d installed and otherwise falls back to slow pure torch. E1 does not install them. The worker records every kernel or fallback message, and the GPU estimate assumes the slow path.

## 2 Design

Code: `src/learnloop/experiments/contextual_embeddings/e1/`. CLI: `learnloop experiments e1 {import, plan, preflight, run --stage local|labels|score, report}`. Production packages never import it; the import-linter contract `experiments-stay-outside-production` holds.

| Module | Role |
|---|---|
| `pins.py` | The model (repo, revision, each file's size and SHA-256, the reviewed code); the separate environment (Python 3.12; `torch==2.14.0`, `transformers==5.18.0`, `accelerate==1.15.0`, `safetensors==0.8.0`, `numpy==2.5.3`, `tqdm==4.70.1`, every release over two weeks old); BF16 with FP8 and LLM.int8 deferred; all bounds; the public smoke text; the $5 cap; the decision rule. All of it is hashed into the plan id |
| `worker.py` | The **standalone batch process**: stdlib plus numpy at import, torch only inside its loader. It runs in the separate environment through `python -I`, inside its own scope. One process loads BF16 with shards straight to the GPU (`device_map={"": 0}`), runs the smoke checks, profiles, encodes everything serially, unloads and exits: **no residency** |
| `gpu_meter.py` | The cumulative **≤4 GPU-hour meter**, file-locked, shared by every E1 plan and process. Each worker is charged its spawn-to-exit wall time, failed loads included. It refuses a second live worker or a start with under 15 minutes left. At the cap it sends SIGTERM and then SIGKILL, to its **own child only** |
| `local.py` | Builds the job, of only what is missing (resumable). Launches the worker as `systemd-run --user --scope -p MemoryMax=12G -p MemorySwapMax=0 -- <env>/bin/python -I worker.py` with an `env -i`-like environment (PATH, an empty private HOME, the user-bus variables; no key). Validates count, width, int8 range, finiteness and nonzero values, then stores the raw rows plus E0's L2-normalized FP32 scoring copy (`adapters.decode`). Ranks by exact cosine. The space id follows E0's formula with `repo@revision:bf16` |
| `replay.py` | **Import and replay of E0.** The import copies the finished run's frozen manifests, results, content-keyed stores and frozen vault copies, plus the label pools from E0's verdict records, each with a tree digest. The replay re-runs E0's bank, R3 contexts, label passes and audits from E0's checkpoints, and every representation arm from E0's vectors. A zero-cap ledger refuses any request before it is sent. Results are then **checked against E0's published slices** (three slices × eight metrics × nine arms) and its κ |
| `supplement.py` | Labels for the v2 arms' **new** candidates, i.e. units in a v2 top 10 that E0 never judged. It uses E0's frozen rubric (its hash is checked), E0's Sonnet 5.5 passes and Opus 5.5 adjudicator, with E1 prompt versions. The protocol has two blinded passes. A new set must contain a new candidate and only supporting members. Opus audits every disagreement and every new set (each is used by the primary endpoint), plus a seeded 20% of the rest. Unresolved candidates stay unknown. κ ≥ 0.60 gates the verdict |
| `ledger.py` | E1's **own ≤$5 hard-cap ledger**: E0's `E0Ledger` class on `contextual-embeddings/e1-ledger/e1_<id>.ledger`, with a Codex allowance of 0. It is cumulative across E1 plans and never opens, carries or seals an E0 ledger (tested) |
| `plan.py`, `run.py`, `decide.py`, `report.py` | The plan (provisional from E0's manifests; frozen from a verified import), the stages, the prespecified decision and the aggregate report (which refuses private fields) |

**The memory guard** applies twice:

1. **The orchestrator's preflight** measures MemAvailable, swap, free VRAM, other GPU compute processes and utilization.
2. **The worker refuses to load** unless all of these hold:
   - it is inside a `.scope` cgroup whose `memory.max` is set and ≤ 12 GiB, with `memory.swap.max` ≤ 0;
   - MemAvailable is ≥ 14 GiB;
   - free VRAM is ≥ 22 GiB;
   - no other compute process uses more than 1 GiB, and utilization is ≤ 15%;
   - the model files have the pinned sizes, and the remote code has the pinned digests.

While the worker runs, a 1-second sampler:

- records host, scope and device peaks and writes a heartbeat;
- aborts below 3 GiB MemAvailable, above the 20 GiB device peak target, or at the GPU-hours deadline;
- writes partial results and exits hard if a forward pass cannot be interrupted.

The 12 GiB scope cap is well below the 33.6 GB FP32 checkpoint. If a load ever tried to materialize FP32 in host RAM, it would die inside its own scope and not take the owner's session with it.

**Smoke checks (§8).** These run on public text before anything is indexed; a failure stops the run:

- separate methods, with query and document vectors of the same text differing;
- widths and order, forward vs reversed;
- context sensitivity of a fixed central chunk across two contexts and alone;
- int8 decoding of unnormalized values;
- finite, nonzero values;
- padding and batch invariance (cos ≥ 0.995);
- determinism;
- no truncation: an over-limit probe is refused before encoding.

The worker also records:

- parameter dtypes and whether the projection is fp32;
- kernel and fallback messages;
- load time;
- device memory after load and at peak, and host and scope peaks;
- unload completion.

It then profiles serialized indexing at 2k/4k/8k tokens with three repeats each. An OOM stops the larger sizes and is counted. Batch-one latency is measured for every query.

**Arms.** `V2_grouped` uses E0's 4,096-token windows; `V2_singleton` is one chunk per document, the same-model context control. Both use common units, exact cosine and @10. Every arm, E0's included, is rescored on the same merged labels. Comparisons are paired family-clustered bootstraps on E0's primary development slice, with logged questions reported apart:

- grouped minus singleton;
- v2 vs each copy's best frozen finalist;
- v2 vs each finalist family.

Hosted v1 is a baseline, never a numerical reference.

**The decision, fixed before any v2 result:**

- **No verdict** unless E0's S1 passed, the replay reproduced E0, the smoke passed, the v2 arms scored ≥95% of the eligible questions, and the supplementary labels are complete with κ ≥ 0.60.
- Otherwise:
  - `retain_candidate` at ≥ +5 points CE@10 with the CI excluding 0. This is always exploratory at under 5 independent families, and confirmation comes before any adoption.
  - `non_inferior_cost_latency_only` when the lower bound is above −0.02.
  - `stop` in every other case.
- Production adoption is `not_authorized_by_e1`.

## 3 The dry runs (this phase's deliverable)

Both dry runs ran under `env -i` (empty HOME, CODEX_HOME and LEARNLOOP_CONFIG_DIR; no key; `OPENROUTER_BASE_URL=http://127.0.0.1:9`) inside the 5 GiB scope. Both had **zero network calls** (socket guard), did not import torch, and read no settings file. The inputs were unchanged before and after, by tree digest.

- **Provisional, from E0's frozen manifests** (`docs/reviews/artifacts/experiments-e1/dry-run-plan.{json,md}`, plan `e1_1da6d5e1246d42d7`): this was made while the relabel run was still finishing. It uses the stated prior, under which 30% of the v2 top-10 slots are new for every question: **$6.71 expected, $10.21 worst case**. That does not fit $5, so the frozen plan replaces the prior with E0's measured novelty.
- **Frozen, from the import** (`docs/reviews/artifacts/experiments-e1/frozen-plan.{json,md}`, plan **`e1_297eff695d89ac0c`**):
  - **The replay reproduced E0:** 216/216 metric values per copy matched with zero mismatches (9 arms × primary/development/logged × 8 metrics), as did both κ values. E0's run id was rebuilt and the import digests are unchanged.
  - **Measured novelty:** this is how often one of E0's hosted contextual arms ranked, in its top 10, a unit no other replayed arm had in its top 20. It is conservative, because E0's system arms are left out. Linear algebra: 23.9% of question-arm pairs, 1.51 units when any. Probability: 29.5%, 1.61.
  - **Cost:** $2.94 expected (labels and audits $2.94 plus about $0.0003 of canaries) and $10.21 worst case (every slot new, every question audited) against the $5.00 cap. **Admission stops at $5.00**, in a frozen priority order: primary development first, then logged, then the rest. Anything left over stays unknown and is reported.
  - **voyage-context-4:** E0's store already holds every vector the replay needs, so the fill costs $0 (the worst case is $0.015).

| Copy | Units | Windows | v2 document tokens (grouped + singleton) | Queries | Labelled questions |
|---|---|---|---|---|---|
| linear_algebra-20261021 | 362 | 10 | 52,274 | 63 | 47 |
| probability-20261021 | 335 | 27 | 66,240 | 55 | 39 |

**GPU estimate.** This uses upper estimates for a pure-torch linear-attention fallback: 600 s to load, 180 s of smoke, 43 s of profiling, 119 s for 118.5k document tokens at 1 s per 1k, and 236 s for 118 queries at 2 s each. That is **0.33 GPU-hours expected and 0.65 worst case** (one failed process repeated) against the 4-hour cap, in one worker process.

**Preflight, run now** (`e1 preflight` with no model and no environment yet):

- **Passing:** plan, import, replay, systemd-run, the GPU meter (4.00 h left, 0 processes) and E0's S1.
- **Failing:** the model files (not downloaded), the environment (not created) and **resources**. Host MemAvailable is 10.5 GiB, below 14 GiB, with 20.7 GiB of swap in use.
- **The GPU itself:** 30.4 GiB free of 32.6 GiB, 10% utilization, 5 other compute processes, all under 1 GiB.

## 4 Findings about E0 (no E0 file changed)

1. **The frozen `run_plan.json` alone does not rebuild E0's bank.**
   - `bank.plan_seeds` takes strata in the dict's iteration order after the distant and deictic strata. E0's live run used its in-memory plan, which is in `pins.DEV_STRATA` order, but the frozen JSON is written with sorted keys.
   - Rebuilt from the JSON, every seed after the 20th per copy changes, and so does E0's run id. (This first showed up as 3 of the 6 writer checkpoints missing per copy.)
   - E1 restores the order (`replay.e0_strata`), and a regression test covers it.
   - E0's own `--reuse-run` is unaffected, because it re-plans in memory. A future E0 resume from a JSON plan would not be.
2. **Failure records from the first paid run name reservations only.** E0's caller inferred a truncation from its ledger's output tokens. E1 replays such a key as that truncation. The inference is checked: a wrong one would miss the split requests' checkpoints and fail the verification. With this in place, R3 replays in linear algebra (one key).

## 5 Deviations (and why)

1. **Supplement depth is 10**, against E0's pool depth of 20: every E1 endpoint is @10. E0 pooled 20 because its pool also fed the answers' evidence.
2. **No blind D1 answers in E1.** The brief's $5 covers labels and the voyage fill only. §8's retention test is evidence value; answer quality would need another plan (open question 4).
3. **The v2 arm is chosen on the same primary development slice** it is reported on, because no separate confirmation slice exists. This is disclosed, and the result is always exploratory.
4. **The hosted fill is limited** to `voyage-context-4` (R5 grouped and singleton), as in the brief. Any other missing E0 vector leaves that arm blocked, never substituted. None is missing today.
5. **GPU time is the worker's wall time,** model load included. This is conservative.
6. **Isolation slips (no effect).** Several `python3 -I` runs outside `env -i` either edited E1 source text or read JSON aggregates. None imported the app, made a network call or touched a credential. Every learnloop, pytest, uv and CLI run used the memory-capped scope, and every CLI run used `env -i`.

## 6 Tests and gate

**New tests: 43, all with fakes.** No torch, no GPU, no download, no network (a socket guard is in every file).

- `tests/test_e1_worker.py` (21): the worker is standalone, and `python -I worker.py --help` runs from `/`. It covers every start refusal: scope, `memory.max`, a cap above the plan, swap, MemAvailable, VRAM, another GPU process, utilization, a remote-code digest, a spent allowance. It also covers the full smoke, int8 rows, an over-limit document refused rather than truncated, a failing context-sensitivity check and a failing method-separation check (each indexes nothing), an OOM at 4k skipping 8k, a host-floor abort keeping partial results, the cgroup, meminfo and nvidia-smi parsers, model-file checks, the network guard, and `main`'s offline environment.
- `tests/test_e1_gpu_meter.py` (5): cumulative charging across plans, failed loads included; the minimum slot; a live worker blocking a second one; a crashed orchestrator charged up to its heartbeat; a cap mismatch; a real child process stopped at a 2-second cap; return codes.
- `tests/test_e1_supplement.py` (5): new means unjudged and in a v2 top 10; blinding; mandatory audits; malformed and background-member sets; unresolved candidates stay unknown; E0's role pins with E1 prompt versions.
- `tests/test_e1_harness.py` (12):
  - A fake E0 run through E0's own `run_live` is imported, and its replay is verified. The plan is frozen and stable, priced on measured novelty.
  - A tampered pool is caught. An unfinished E0 is refused, giving a provisional manifest plan.
  - The whole pilot runs: local in-process, resume with no second worker, labels dry run, refusal without authorization, paid labels under E1's ledger with the E0 ledgers untouched, score and report.
  - Also covered: a provisional plan runs no stage; the cumulative E1 ledger; the scoped launcher's command and environment (no key); the CLI plan; preflight; environment pins; strata order; the replay caller.

**Gate** (memory-capped, `-n 6`):

- **Run 1, after the main build:** `tests/test_e0_*.py`, `tests/test_e1_*.py`, `test_architecture`, `test_cli_help_snapshot`, `test_sqlite_file_copies`, `test_tracked_fixture_databases`, `test_cli_entrypoint` and `test_cli_commands`: **342 passed**.
- **Final run, after the replay fixes (same selection):** **346 passed**.
- **lint-imports:** **30 kept, 0 broken**.
- **Help snapshot:** `tests/cli_help_snapshot.json` gained the six `experiments e1` entries plus the `experiments` group; nothing else changed.

## 7 Commands for the owner-approved steps

All commands run from `/home/saturn/Documents/thinking/learnanything-e1`. `<EMPTY>` is an empty directory. Every step runs in a memory-capped scope.

```bash
# 0. The separate environment (once; the app's environment is never upgraded; ~6 GB of wheels)
systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G -- \
  env UV_CACHE_DIR=/home/saturn/.cache/uv uv venv --python 3.12 fixtures-local/contextual-embeddings/e1/env
systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G -- \
  env UV_CACHE_DIR=/home/saturn/.cache/uv uv pip install --python fixtures-local/contextual-embeddings/e1/env/bin/python \
  torch==2.14.0 transformers==5.18.0 accelerate==1.15.0 safetensors==0.8.0 numpy==2.5.3 tqdm==4.70.1

# 1. The download (owner approval: 33.6 GB, public, ungated, no token; ~45 GB free needed, 823 GB free now)
systemd-run --user --scope --quiet -p MemoryMax=4G -p MemorySwapMax=1G -- \
  env -i PATH=$PATH HOME=<EMPTY> HF_HUB_DISABLE_TELEMETRY=1 \
  HF_HOME=$PWD/fixtures-local/contextual-embeddings/e1/hf-home \
  fixtures-local/contextual-embeddings/e1/env/bin/hf download perplexity-ai/pplx-embed-v2-context-9b-preview \
  --revision e2c06a779d45e8db53066735be1b98ffe3412ca3 \
  --local-dir fixtures-local/contextual-embeddings/e1/models/pplx-embed-v2-context-9b-preview

# 2. Preflight with every shard hashed (no model load; resources measured now)
systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G -- \
  env -i PATH=$PATH HOME=<EMPTY> CODEX_HOME=<EMPTY> LEARNLOOP_CONFIG_DIR=<EMPTY> UV_CACHE_DIR=/home/saturn/.cache/uv \
  uv run learnloop experiments e1 preflight \
  --import fixtures-local/contextual-embeddings/e1/imports/e0_e6a077cd391c5421 \
  --plan docs/reviews/artifacts/experiments-e1/frozen-plan.json \
  --model-dir fixtures-local/contextual-embeddings/e1/models/pplx-embed-v2-context-9b-preview \
  --env-python fixtures-local/contextual-embeddings/e1/env/bin/python --verify-weights

# 3. The GPU run, in an owner-chosen idle slot with no GLM-OCR or other GPU work. The worker starts
#    its own 12G scope; the user-bus variables let systemd-run reach the user manager.
systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G -- \
  env -i PATH=$PATH HOME=<EMPTY> CODEX_HOME=<EMPTY> LEARNLOOP_CONFIG_DIR=<EMPTY> UV_CACHE_DIR=/home/saturn/.cache/uv \
  XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus \
  uv run learnloop experiments e1 run --stage local \
  --import fixtures-local/contextual-embeddings/e1/imports/e0_e6a077cd391c5421 \
  --plan docs/reviews/artifacts/experiments-e1/frozen-plan.json \
  --model-dir fixtures-local/contextual-embeddings/e1/models/pplx-embed-v2-context-9b-preview \
  --env-python fixtures-local/contextual-embeddings/e1/env/bin/python --i-have-an-idle-gpu-slot

# 4. Labels: the exact counts and estimate first (no network), then the paid stage (<= $5, E1's own ledger)
... uv run learnloop experiments e1 run --stage labels --import <same> --plan <same> --dry-run
... uv run learnloop experiments e1 run --stage labels --import <same> --plan <same> \
      --env-file <PATH/TO/KEYS.env> --i-am-authorized-to-spend

# 5. Score and report (aggregates only)
... uv run learnloop experiments e1 run --stage score --import <same> --plan <same>
... uv run learnloop experiments e1 report \
      --results fixtures-local/contextual-embeddings/e1/runs/e1_297eff695d89ac0c/results.json \
      --out docs/reviews/experiments-e1-report.md
```

In steps 4 and 5, `...` stands for the same `systemd-run … env -i …` prefix as step 2.

## 8 Open questions (the defaults in force)

1. **Host RAM.** The worker refuses below 14 GiB MemAvailable, and 10.5 GiB is available now, with 20.7 GiB of swap in use. Default: the owner frees memory for the slot. The alternative is to lower `MIN_HOST_AVAILABLE_GIB` and `SCOPE_MEMORY_MAX` after one measured load; that is a new plan.
2. **Fast kernels.** flash-linear-attention and causal-conv1d are not installed. Default: run the pure-torch path, record the fallback messages, and keep 0.33 h expected. Adding the kernels would be another pinned environment and a new plan.
3. **Costs past $5.** The worst case is $10.21. Default: the ledger stops at $5 in priority order and the rest stays unknown, so completeness is pool-relative. Raising the cap is an owner decision.
4. **Blind answers for v2.** These are not in E1. Default: retention on evidence (§8). A v2 D1 answer comparison needs its own plan and budget.
5. **The preview model.** Its vectors stay in E1's private research store, never mixed with a later release, and never used for production. Any adoption still needs §7's bar and the one-model amendment (D6).
