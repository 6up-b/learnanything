# Goal: finish the specced build, with a Codex adversarial review and fix on every stage

**Set by the owner, 2026-10-12.** The aim is to finish most of what was specced:
- Slice A;
- the daily loop;
- Slice 1;
- Slice 2 (PF and T1, T4–T8);
- the action router;
- mobile;
- project understanding.

Every stage goes through one loop: implement, then a Codex adversarial review, then a fix (§2).

The prompts for each stage are in `implementation_handoffs.md`. This file says what "done" means, how each stage is reviewed, the order, and what blocks progress.

---

## 1. Definition of done

| Track | Done when | Spec |
|---|---|---|
| **Slice A** | Phases 1, 2, 3, 5a, 5b and 6 are merged. Phase 3b and Phase 4 are built if their evidence triggers fire | `spec_slice_a_practice_and_field_v1.md` |
| **Daily loop** | Its spec is written and accepted, and its phases are merged (capture box, finite plan, re-entry, intent) | `spec_daily_loop_v1.md` (to be written) |
| **Router** | R0, R1 and R2 are merged and R3's first report has run | `spec_action_router_v1.md` |
| **Slice 1** | M1 built and run, M2 merged (including PF-c), and the S1.5 exit review done | `spec_blind_grading_diagnosis_split_v1.md` |
| **Slice 2** | PF (built in Slice A), T6, T1, T4, T5, T7 and T8 are merged, each with its report | `spec_embedding_consumers_v1.md` |
| **Mobile** | M1 merged and accepted on the phone (A1–A3), then the M2 prerequisites, M2a, M2b and M3 | `spec_mobile_tailnet_v1.md` |
| **Project understanding** | M1, M2 and M3 merged. M1b and M4 are optional | `spec_project_understanding_v1.md` |

**Not part of this goal** (each is deferred, with a trigger, in its own spec):
- the learned or LoRA router;
- the facet-level graph field;
- probe targeting;
- `idea_hier_llm_prior`;
- the public benchmark;
- item-level routing by a model;
- affect sensors.

**Two kinds of finishing:**
- **Built.** Code merged and verified. Most of the goal can reach this.
- **Proven.** A live switch decided on evidence: activating a challenger, Phase 3b, router weights, T1's successor. These wait on the owner's real study data (§5, blocker B2), so they finish later and on their own schedule.

---

## 2. The loop every stage goes through

| Step | Who | Output |
|---|---|---|
| **1. Implement** | A Claude agent, in its own worktree, on the branch its handoff prompt names | Commits plus `docs/reviews/<stage>.md`, with all §0 checks passing |
| **2. Adversarial review** | A **Codex** agent (`codex` agent type: ChatGPT-subscription billing, `gpt-6-astra`, `effort: high`, `sandbox: read-only`) in the same worktree | A ranked findings list (prompt below) |
| **3. Fix** | A Claude agent, in the same worktree | For each finding: reproduce it with a failing test, then fix it, or reject it with a reason. Written to `docs/reviews/<stage>-codex-review.md` and committed |
| **4. Re-review** | Codex, only if a High finding was fixed, over the fix commits only | Confirms or reopens the fix |
| **5. Gate** | The fixer | Full suite, durability lane, `lint-imports`, frontend checks, DB reference validate, and a shadow rebuild on a `fixtures-local/` copy for any serving change |
| **6. Integrate** | Claude, in the main checkout | The branch merges into `main` one at a time (renumbering migrations if needed), then `main` is pushed |
| **7. Owner checkpoint** | The owner, where the stage has one | A recorded verdict in `docs/reviews/` |

**Review prompt (step 2).** Fill in the stage, branch, base, spec sections and review file.

```text
model: gpt-6-astra
effort: high
sandbox: read-only

Adversarially review LearnLoop stage <stage> on branch <branch> (the diff
<base>..<branch>) in <worktree path>.

Read first:
- <spec sections>;
- docs/specs/implementation_handoffs.md §0, the standard rules and invariants;
- the implementer's review file <review file>;
- CLAUDE.md.

Find real defects, not style. Check:
1. Spec conformance, item by item. List anything specified but missing, and
   anything built beyond scope.
2. The invariants:
   - replay and rebuild make zero model or embedding calls;
   - nothing predicted or assumed writes evidence or certification;
   - grading stays learner-blind;
   - embeddings never decide identity, novelty or difficulty;
   - every serving change is an algorithm successor with a working kill switch;
   - paid commands have spend caps and a dry-run;
   - verdicts go to judgment_ledger.
3. Data integrity:
   - migrations and table roles;
   - exactly one replayer per DERIVED table;
   - idempotency, crash and resume behaviour;
   - concurrency with the sidecar;
   - WAL and durability.
4. Security and privacy: secrets, what learner text leaves the machine, injection,
   the mobile surface.
5. Tests that test the fakes instead of the behaviour, and missing negative tests.
6. Anything that will make later stages harder.

For each finding give:
- severity (High, Medium or Low);
- file:line;
- a concrete failure scenario (input or state, then the wrong result);
- a suggested fix.
Rank High first. Say plainly if an implementer's claim doesn't hold. Do not edit
files.
```

**Fix prompt (step 3).**

```text
Fix the Codex review findings for LearnLoop stage <stage> on branch <branch> in
<worktree path>. The findings are pasted below.

For each finding:
- reproduce it first, with a failing test where it's testable;
- then fix it, or reject it with a concrete reason if it doesn't reproduce or
  conflicts with the spec.
Don't widen scope.

Follow docs/specs/implementation_handoffs.md §0. Rerun the full gate:
- the full suite;
- the durability lane;
- lint-imports;
- the frontend checks;
- the DB reference validate.

Write docs/reviews/<stage>-codex-review.md with:
- a findings table (finding, verdict, fixed in commit, test);
- the gate results with pass counts.
Commit. Don't merge or push.

<findings>
```

**Orchestration.** Each stage is three or four agent runs: implement, review, fix, and an optional re-review. These can run as a Workflow per stage, once the owner opts in, or by hand, one agent at a time.

---

## 3. Order

Keep at most three or four branches open at once. Waves overlap where their dependencies allow.

| Wave | Stages | Depends on |
|---|---|---|
| **0 (now)** | <ul><li>Integration of the daily-loop follow-ups and Phases 2 and 3 (running), then a Codex review and fix of the integrated branch. Phases 2 and 3 never had a Codex review</li><li>Mobile M1: the owner's revision 2/3 decision, then a Codex review and fix, then integration</li></ul> | — |
| **1** | <ul><li>Phase 5b (practice index)</li><li>Phase 5a (generation)</li><li>Phase 6 (starting new material)</li><li>Router R0 (model clients and the six harness arms)</li><li>The daily-loop **spec** (Codex reviews the spec as well)</li><li>Project understanding M1</li></ul> | <ul><li>Phase 5a, Phase 6 and R0 need Wave 0's integration</li><li>Phase 6 also needs the owner's checkpoint on reports 1–2</li></ul> |
| **2** | <ul><li>Daily-loop implementation phases</li><li>Slice 2 T6</li><li>Router R1</li><li>Slice 2 T8's `emb_ridge` arm (offline; gates the learned router)</li></ul> | <ul><li>The daily-loop spec accepted</li><li>R1 needs Phase 6</li><li>T6 and T8 need Slice A merged and the embedding backfill run</li></ul> |
| **3** | <ul><li>Slice A stop review</li><li>Phase 3b and Phase 4, if triggered</li><li>Router R2</li><li>Mobile M2 prerequisites, then M2a and M2b</li><li>Project understanding M2</li></ul> | <ul><li>R2 needs the daily loop's finite plan</li><li>Mobile M2 needs M1 accepted plus Phase 6 and the daily plan</li><li>Project M2 needs PF-a and PF-b</li></ul> |
| **4** | <ul><li>Slice 1 M1 (it can be built in an earlier wave, since it's offline)</li><li>Slice 1 M2 with PF-c</li><li>The S1.5 exit review</li></ul> | <ul><li>M1 *runs* once `field data-check` shows ≥ ~40 graded wrong answers</li><li>M2 needs the M1 report</li></ul> |
| **5** | <ul><li>Slice 2 T1, then T4, T5 and T7, then the rest of T8</li><li>Router R3 report and switching</li><li>Mobile M3</li><li>Project understanding M3</li></ul> | <ul><li>T1 needs Slice 1's exit review</li><li>Each later Slice 2 track needs the previous report</li><li>R3 needs 200 router decisions</li></ul> |

---

## 4. Open owner decisions

**Needed now:**

| # | Decision | Recommendation |
|---|---|---|
| O-1 | Mobile M1 was built to revision 2 (QR pairing, token scopes) | **Decided (owner, 2026-10-12):** the spec follows the build (mobile spec revision 4) |
| O-2 | Push `main` | **Done (2026-10-12)** |
| O-3 | Defaults for stages whose prompts assume them | **Decided (owner, 2026-10-12): accepted** ("most defaults"). The owner may override any one at its checkpoint |
| O-4 | Route for the paid LLM roles | **Decided (owner, 2026-10-12): Codex on the ChatGPT subscription, without restraint**, with cost estimated from token usage (Slice A plan §5 rule 6). The Decider is `perplexity/pplx-decider-v1.1-27b` on OpenRouter |

**Needed at checkpoints:**
- **Phase 2:** read reports 1–2 once, on a copy of the vault.
- **Phase 3:** run `families propose` on the vault (dry-run first), read the replay report, then decide 3b.
- **Daily loop:** answer Q0 (how often you open LearnLoop and what stops you), Q5, Q7, Q8, Q11 and Q12. The spec agent proposes defaults.
- **Router:**
  - D6, the retention terms at Perplexity (via OpenRouter) and at the LLM provider;
  - the R3 report: which model routes better.
- **Slice 1:** the M1 report (history mode, blind-grader readiness), then the exit review, which gates T1.
- **Mobile:** acceptance A1–A3 on the iPhone, before M2.
- **Slice 2:** each track's report, before the next track.

---

## 5. Blockers

| # | Blocker | Effect | Fix |
|---|---|---|---|
| B1 | **The Phase 2/3 integration** (running) | Blocks Phases 5a and 6 and router R0 | It finishes, then gets a Codex review and fix, then merges |
| B2 | **Study data volume.** Every evidence-gated step needs real use, not code:<ul><li>reports 1–2 (both phases warn that strict revision policies may score few historical rows);</li><li>Slice 1 M1 needs ≥ ~40 graded wrong answers;</li><li>router R3 needs 200 decisions;</li><li>T1 needs Slice 1 M2's ~2 weeks;</li><li>the learned router needs 500 decisions</li></ul> | "Built" can finish; "proven" waits | The owner studies daily. The integration agent's scored-row counts show how thin reports 1–2 will be |
| B3 | **Broken Rust toolchain on carson.** `rustc -vV` fails with a symbol lookup error in `librustc_driver` against LLVM 23.1 (reported by the Phase 2 and mobile agents) | `cargo check` fails, so the Tauri shell can't be rebuilt, and new desktop UI can't be run in the app | Owner: reinstall or upgrade Rust (system `rust` package or rustup) so `rustc -vV` works, then run `cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml` |
| B4 | **The daily-loop spec doesn't exist yet** | Blocks daily-loop implementation, router R2 and mobile M2 | Launch the spec agent now. It is docs only, so it causes no merge conflicts |
| B5 | **Unverified external interfaces:**<ul><li>the Decider on OpenRouter (exact path and body);</li><li>the Eedi dataset (likely needs a Kaggle login, for T1's B1);</li><li>srs-benchmark pretrained weights (optional arm)</li></ul> | R0, T1 and the optional arm can stall | R0 confirms the Decider first, falling back to Perplexity's direct API. The owner downloads Eedi if it needs a login. The memory-model arm is skipped if no weights are published |
| B6 | **Keys and config.** `OPENROUTER_API_KEY` must be in `~/.config/learnloop/settings.env`. The repo-root `.env` isn't read, and Phase 0's checkbox is still open | Paid owner runs (backfill, the Decider) fail | Owner: `! grep '^OPENROUTER_API_KEY=' .env >> ~/.config/learnloop/settings.env` |
| B9 | **Phase 3 refuses Codex for the family judge** (as built) | `families propose` can't run on the subscription | An owner-directed fix in Wave 0, per Slice A plan §5 rule 6 |
| B7 | **Codex capacity.** Every stage adds a review, and High findings add a re-review | ChatGPT subscription rate limits can queue reviews | Review one stage at a time. Don't fan out more than two Codex reviews at once |
| B8 | **Frontend dependency audit.** `npm install` reports 14 findings (2 critical, 6 high) | Not blocking | A small maintenance stage after Wave 1, also run through the loop |

---

*Related: `implementation_handoffs.md` (the step-1 prompts) · `daily_loop_frictionless_defaults.md` · `docs/brainstorming/Daily Loop Open Questions.md`*
