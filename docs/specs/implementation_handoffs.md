# Implementation handoffs: agent prompts (2026-10-11)

These are the prompts for the agents that build the rest of Slice A and the slices after it. Each prompt is step 1 of the loop in `implementation_goal.md` §2: after it, every stage gets a Codex adversarial review and a fix before it merges. Each prompt is self-contained apart from the standard rules in §0, which every prompt tells the agent to read. Paste a prompt into a fresh agent session in the repo.

**State (updated 2026-10-12):**
- **On `main`:** Slice A Phase 1 (migration head 166) and the daily-loop bug fixes (`be33cdd`).
- **Delivered, not yet merged:**
  - `fix/daily-loop-followups`;
  - `slice-a/phase-2` (learner field F1);
  - `slice-a/phase-3` (PF-a families);
  - `mobile/m1`, built to revision 2's pairing and scopes, so the owner must choose revision 2 or 3.

  All three delivery branches claim migration 167. They integrate one at a time, renumbering as they go (§0 rule 4).
- **Before Phase 5a or 6 starts,** the integration of Phases 2 and 3 must merge, unifying the two `learnloop eval` harnesses (`docs/reviews/pf-a-evaluation-integration.md`).

---

## 0. Standard rules for every agent

1. **Read first:**
   - `CLAUDE.md`;
   - `docs/learnloop-architecture-vault/Home.md`, for orientation;
   - `docs/algorithm-change-playbook.md`, for anything that changes what is served or what persisted data means;
   - the spec sections your prompt names.
2. **Plan first.** Before coding, write a short plan to your review file (`docs/reviews/<name>.md`). It covers:
   - files to add or change;
   - migrations;
   - algorithm successors and kill switches;
   - spend caps and model routes;
   - `judgment_ledger` writes;
   - tests.

   Then proceed without waiting, unless your prompt says to stop.
3. **Branch and worktree.**
   - Work in your own git worktree, on the branch your prompt names, created from the base it names. Run `git fetch` first.
   - Never commit to `main`.
   - Don't merge, push, rebase onto other agents' branches, or delete branches or worktrees.
4. **Parallel agents.** Others work at the same time.
   - Keep changes local. Don't reformat or rename shared code.
   - **Migrations:**
     - take the next free number when you finish (`ls migrations/`);
     - classify every new table in `db/table_roles.py` (a DERIVED table needs exactly one replayer);
     - follow `CLAUDE.md`'s head-fixture procedure.
   - Whichever branch merges second renumbers and regenerates the head fixture.
5. **Invariants:**
   - **Replay and rebuild** make zero LLM and zero embedding calls.
   - **Paid outputs** (vectors, verdicts, skeletons, generated items) are persisted inputs and are never regenerated on rebuild.
   - **A change to what is served** is an algorithm successor with a kill switch, checked by a shadow rebuild on a backup-API copy.
   - **Nothing a model predicts or assumes** writes evidence or certification.
   - **Grading contexts** stay learner-blind.
   - **Embeddings** never decide identity, novelty or difficulty alone.
6. **Paid work.**
   - **Spend controls.** Every command that calls a paid model uses the Phase 1 spend framework (`src/learnloop/ai/spend.py`): caps, plus a `--dry-run` that prints a cost estimate.
   - **Verdicts.** Every LLM, verifier or owner verdict appends to `judgment_ledger`.
   - **Routes.** Each paid component is its own `ai.routing.*` route. An unset route falls back to the active provider, and receipts record the resolved model. `ai.routing.embedding` never falls back.
7. **Owner principles: honest labels, generous defaults** (`docs/specs/daily_loop_frictionless_defaults.md`).
   - Never add a learner step to protect the model.
   - Never let the UI claim something that doesn't happen.
   - Prefer decisive live changes behind kill switches over shadow stages.
8. **Safety.**
   - Never read `~/.config/learnloop/`, any `.env` file, or the owner's vault databases. Never search the filesystem for vaults.
   - No live or paid API calls during development or tests. Use `tests/structured_ai.py` and `tests/openai_fakes.py`.
   - The owner runs paid commands. Give them the exact commands, with the dry-run first.
   - Manual runs use backup-API copies (`learnloop.db.copies`) of your worktree's tracked fixtures, under your worktree's `fixtures-local/`.
   - Never commit changes to `fixtures/linear_algebra`, `fixtures/probability` or `fixtures/arxiv_v2`.
   - Never run `tailscale` commands or enable Funnel.
9. **Setup.**
   - `uv sync --extra dev`;
   - `uv pip install pypdfium2` (one PDF test needs it);
   - `npm install` in `apps/learnloop-tauri` if you touch the frontend.
10. **Done always includes:**
    - `uv run lint-imports --no-cache`;
    - `uv run pytest -n auto`;
    - `uv run pytest -m durability`;
    - `npm run typecheck && npm test` if the frontend changed;
    - the db reference generate and validate scripts if the schema changed.

    The review file lists:
    - what was built;
    - deviations;
    - test results with pass counts;
    - files touched;
    - migrations;
    - owner-run commands;
    - open questions.

    Commit with clear messages.

---

## 1. Order and dependencies

| When | What | Needs |
|---|---|---|
| **Now** | Integrate `fix/daily-loop-followups`, `slice-a/phase-2` and `slice-a/phase-3` into `main`: renumber migrations, unify the two eval harnesses, rerun everything | — |
| **After the owner decides mobile revision 2 vs 3** | Integrate `mobile/m1` (next free migration), then the owner runs acceptance A1–A3 on the iPhone | The integration above |
| **Can start now** | Phase 5b (practice index) | Phase 1 only |
| | Daily-loop spec draft | Nothing; docs only |
| | Project understanding M1 | Nothing; standalone store |
| | Mobile M1, if not already running | Nothing |
| **After the Phase 2/3 integration merges** | Router R0: the Decider (via OpenRouter) and LLM clients, plus the `llm_probability` V1–V3 arms on both models | The integrated harness |
| **After Phase 3 merges** | Phase 5a (generation) | Phase 3 |
| **After Phase 2's checkpoint and the bug fixes merge** | Phase 6 (starting new material) | Phase 2 reviewed; `fix/daily-loop-bugs` |
| **After Phase 6 merges** | Router R1: decision logging with full candidate sets and propensities | R0; Phase 6 (same scheduler files) |
| **Only if a challenger predictor won reports 1–2** | Phase 4 (activation + map fog) | Phase 2 checkpoint; preferably after Phase 6 |
| **After Slice A stops and the owner reviews** | Daily-loop implementation, from its spec | Daily-loop spec accepted |
| | Slice 2 T6 (source retrieval), alongside the daily loop | Slice A merged; it reuses the Phase 5a compare harness |
| **After the daily loop's finite plan** | Router R2: the Decider router live for the daily plan | R1; daily-loop P1–P3 |
| | Slice 1 M1 (offline review) | It can be built any time. The owner runs it once `learnloop field data-check` shows ≥ ~40 graded wrong answers across topics |
| | Slice 1 M2, then PF-c | M1 report reviewed |
| **After Slice 1's exit review (S1.5) supports it** | Slice 2 T1 (M3: recurrence with authority) | Slice 1 M2 merged; trustworthy pattern links |
| **Then, each after the previous report is reviewed** | T4 → T5 → T7 → T8 | The previous track's report |
| **After Phase 6 and the daily plan** | Mobile M2 prerequisites, then M2a | Phase 6; the daily loop's finite plan |
| **Not promptable yet** | Mobile M2b/M3 | — |
| | Project understanding M2+ | PF-a/b and Slice 1 |
| | Learner-field deferred items | Triggers in `spec_learner_field_v1.md` §11 |

**Keeping merges manageable.** Keep at most three or four branches open at once. Merge one at a time, newest last; the later branch renumbers its migration.

---

## 2. Rest of Slice A

### Phase 5a: generation, verification, selection, publishing

```text
Implement Slice A Phase 5a of LearnLoop: practice-family generation, verification,
selection and publishing. Follow the standard rules in
docs/specs/implementation_handoffs.md §0. Review file: docs/reviews/slice-a-phase-5a.md.

Specs:
- docs/specs/spec_slice_a_practice_and_field_v1.md: §3 row 5, §5;
- docs/specs/spec_embedding_consumers_v1.md:
  §5.1 (including "Where families live");
  §5.3 (generator programs, the ensemble path, source-anchored families, verified
  references);
  §5.4 (filters, freshness gate, solver panel, selection);
  §5.6 (B2, the pilot with the generation-path comparison and the scaling check);
  §5.7, §5.8, and §13's PF gates.
The practice index (§5.9) is Phase 5b, a separate agent: don't build it.

Branch slice-a/phase-5a from origin/main after Phase 3 (families) has merged.
Owner decisions: defaults for P10 (the solver panel). The scaling check's two tiers
are the configured cheap and frontier routes.

Must hold:
- Two generation paths:
  - Generator programs, run in the bubblewrap sandbox. Generation fails closed
    without bubblewrap; reuse `_sandboxed_command` from
    content/authoring/concept_animation.py.
  - The ensemble path:
    - at least two distinct proposer models;
    - solve-first panel agreement, with at least two agreeing solves plus a
      sandboxed sympy equivalence check;
    - a mandatory structure check for isomorphs;
    - a selection judge that is only ever offered verified candidates.
- Unverified references are never published.
- Verified survivors publish into their family as ordinary vault items:
  - capped by pf.max_published_per_day (default 10);
  - pf.generation_enabled is off in the template;
  - each published item gets its own card. Shared memory is Phase 3b's decision.
- Reuse the 077 fingerprint namespaces and the 078 mint-job pattern rather than
  adding parallel structures.
- Reuse existing authoring gates and the practice_generation / rung_variants code
  wherever they fit.
- item_skeletons, item_fingerprints and pf_candidates are as specified.
  difficulty_source = "solver_panel". LLM self-labelled difficulty is never used.
- Replay never executes a generator.
- B2 and the valid-alternative regression suite exist as harnesses on
  `learnloop embeddings compare`.

Done also means:
- every applicable PF gate in Slice 2 §13 passes;
- a fake-model end-to-end run on a fixtures-local copy goes generate → verify →
  filter → select → publish for both paths, and respects the daily cap;
- the review file gives the owner's commands for B2, the pilot and the scaling
  check, each with --dry-run first.
```

### Phase 5b: the practice index (can start now)

```text
Implement Slice A Phase 5b of LearnLoop: the practice index (facet dossiers and
find_practice). Follow the standard rules in docs/specs/implementation_handoffs.md §0.
Review file: docs/reviews/slice-a-phase-5b.md.

Specs:
- docs/specs/spec_slice_a_practice_and_field_v1.md: §3 row 5 (the practice-index
  part), §5;
- docs/specs/spec_embedding_consumers_v1.md: §5.9 in full, and §5.8;
- the Phase 1 embedding substrate: src/learnloop/ai/embedding.py,
  db/stores/embedding_vectors.py, vault/embedding_recipes.py,
  ops/embedding_backfill.py.

Branch slice-a/phase-5b from origin/main. It needs only Phase 1. Phase 5a adds the
item/skeleton recipe in parallel, so expect a small merge in
vault/embedding_recipes.py.

Owner decision: the retrieval bar stands as written. Two-level search through
dossiers must beat direct item search (BM25 plus item embeddings) on held-out
queries. Otherwise find_practice uses direct item search.

Must hold:
- facet_dossiers (WORKFLOW), keyed by facet content hash, source hash, model and
  prompt version. Generated under spend caps; regenerated only when the facet or its
  sources change, never on rebuild.
- Per-field dossier embeddings, as recipes named by kind and field
  (facet/dossier_scope, facet/dossier_moves, facet/dossier_errors,
  facet/dossier_contrast).
- find_practice(query, constraints), as a sidecar RPC and an agent tool:
  1. facets ranked by dossier embeddings plus BM25;
  2. items ranked by item/skeleton once it exists, otherwise by item text;
  3. an LLM rerank, written to judgment_ledger as task practice_relevance;
  4. admission through the scheduler's existing eligibility rules. Reuse them; if
     fix/daily-loop-bugs has merged, that includes its LO-lifecycle check.
  It proposes and never serves.
- The coverage report: facets with few eligible items become generation targets
  for 5a.
- The retrieval evaluation:
  - LLM relevance labels in two passes, with their agreement reported;
  - Recall@10 and nDCG@10, against direct item search;
  - usage-signal logging, for later.

Done also means:
- the evaluation runs end to end with fakes on a fixtures-local copy;
- the review file gives the owner's commands (dry-runs for dossier generation and
  the backfill, then the retrieval evaluation) and says which path won on fixtures.
```

### Phase 6: starting new material without ceremony

```text
Implement Slice A Phase 6 of LearnLoop: starting new material without ceremony
(learner field F2). Follow the standard rules in docs/specs/implementation_handoffs.md §0.
Review file: docs/reviews/slice-a-phase-6.md.

Specs:
- docs/specs/spec_slice_a_practice_and_field_v1.md: §3 row 6, §5;
- docs/specs/spec_learner_field_v1.md: §3.1, §4.1, §5.1–5.2, §6 (assumption_decisions),
  §7.1 (G4, G7–G9, G13), §7.3 (report 3), §7.4, §9 (the F2 tests), §10;
- docs/specs/daily_loop_frictionless_defaults.md: S1–S5.

Prerequisites, both merged:
- Phase 2, with the owner's review of reports 1–2 done;
- fix/daily-loop-bugs, so dormant and resolved LOs are no longer served.
Branch slice-a/phase-6 from origin/main after both.

Owner decisions, all defaults:
- D4: the quick check is optional.
- D5: self-reports act immediately.
- D6: fast-track needs at least 2 cold correct first answers with no hints, no help
  before starting and no confusion questions, plus P ≥ 0.8. The first review is at
  14 days.
- D7: don't wait for Slice 1's grader probes.
- D11: opening probes are off by default.

Must hold:
- An algorithm successor, following the playbook, with kill switch
  placement.enabled. Turning it off restores today's initial probes exactly (G9, on
  fixture copies).
- placement.initial_probes = false: no opening probe per new LO. Diagnosis runs only
  when a wrong answer leaves a real choice of repair.
- New material starts as learning, ordered by prerequisites and predicted
  difficulty.
- LOs with confused tutor or reader questions, or help requested before starting,
  are taught first and never fast-tracked (§3.1). Asking never lowers the record
  (G13).
- "Assumed known (not tested)":
  - sources: self-report ("I know this", "too easy"), fast-track, or an activated
    predictor. With the incumbent mastery_ekf the predictor source cannot fire.
  - The LO enters maintenance, and its 14-day first review is the check.
  - A failed first review, or "I don't know this", quietly returns it to learning.
  - Nothing assumed writes evidence or certification (G7).
- The optional "Check what I already know" quick check uses
  start_calibration_session. It is never prompted.
- assumption_decisions receipts hold everything needed to recompute each decision
  (G8). Report 3: first-review miss rate by source.
- The map's "assumed (not tested)" label is distinct from demonstrated (G4).

Done also means:
- a shadow rebuild of a fixtures-local copy shows only the documented serving
  differences;
- frontend tests cover the labels and the buttons;
- the review file gives the owner the report 3 command and what to watch in the
  first weeks.
```

### Phase 4 (conditional): activate the winning predictor, then map fog

Phase 4 was deferred when the learner field was reshaped. Launch it only after the owner's review of reports 1–2 finds a winning challenger. The prompt checks its own trigger first.

```text
Implement Slice A Phase 4 of LearnLoop, but only if its trigger has fired: activate
the winning learner predictor, then add the map uncertainty layer ("fog"). Follow the
standard rules in docs/specs/implementation_handoffs.md §0. Review file:
docs/reviews/slice-a-phase-4.md.

First check the trigger (docs/specs/spec_learner_field_v1.md §7.4 and §11). It has
fired when the owner's recorded review of reports 1–2 (in docs/reviews/) names a
challenger that meets all of these:
- the challenger is lo_general, an extension arm, the composite, or idea_hier;
- it beats mastery_ekf on attempt-level log loss, both overall and on the
  first-attempt split;
- the bootstrap interval excludes 0 at the pre-fixed margin (D9);
- its report-2 miss rate is no worse.
If there is no recorded winner, say so in the review file and stop without coding.

If it fired:
1. Activation. An algorithm successor that sets field.active_predictor to the
   winner, with a kill switch that restores mastery_ekf. Consumers switch as §7.4
   says:
   - fast-track and the "predictor" source of assumed-known use the winner;
   - the quick check orders items by conditional_gain.
2. Map fog. Adapt the map-layer design preserved at commit 936813f
   (spec_learner_field_v1.md §6.1 at that commit) to the current LearnerPredictor
   interface:
   - get_knowledge_map gains an optional field block per point, taken from
     region_estimates: p, an 80% interval, inferred, untested, support, predictor,
     and version.
   - KnowledgeWellView draws inferred regions as fog in a separate palette, with a
     toggle that is on by default. Untested regions keep their label.
   - Well depth, demonstrated beads, ghost rings and decay markers are unchanged.
     Never blend: a vitest asserts identical well depth and beads with the layer on
     and off.
   - The side panel reads "Estimated … Not demonstrated."

Branch slice-a/phase-4 from origin/main, preferably after Phase 6 has merged, since
it touches the same consumers.
```

---

## 3. After Slice A

### Daily-loop spec (docs only; can start now)

```text
Draft LearnLoop's daily-loop specification, docs/specs/spec_daily_loop_v1.md. This is
a spec-writing task with no code changes. Follow rules 1, 3, 7 and 8 of
docs/specs/implementation_handoffs.md §0.

Sources:
- docs/specs/daily_loop_frictionless_defaults.md: the owner's decisions, which win
  over everything else;
- docs/brainstorming/Daily Loop Open Questions.md: Q0–Q18, with their status table;
- docs/brainstorming/LearnLoop_User_Intentions_v2.md and "User intentions.md";
- specs that touch the loop:
  - spec_learner_field_v1.md §5.2;
  - spec_embedding_consumers_v1.md §5.3 (verified solving) and §5.9 (find_practice);
  - spec_mobile_tailnet_v1.md §6.7 (its M3 background capture processor should be
    this spec's processor);
  - spec_project_understanding_v1.md (delayed probes in the daily plan);
- docs/reviews/daily-loop-bugs.md, if it has merged.

Before writing, audit the current code, with file:line citations:
- the Today/Start screen and the queue;
- the shadow planner;
- the welcome-back panel;
- the streak;
- the readiness form;
- every capture path: write a card, Quick Add, reader commitments, tutor-question
  promotion, image drop-in;
- goals, commitments and topic status as intent carriers;
- session time and duration logging.

The spec must:
- Turn C1–C4, S1–S5 and P1–P7 into concrete contracts:
  - the capture box with a shortcut (text, URL, image);
  - silent background filing, correctable with one tap;
  - background verified solving, reusing PF's verified-reference rules;
  - one-tap "Practice this";
  - the finite daily plan with auto-advance, a system-set split and pace, and
    remembered minutes;
  - re-entry after a break;
  - the streak, kept.
- Give each open question a recommended default the owner can accept with
  "defaults":
  - Q5: items before reading;
  - Q7: the intent object (recommend commitments, with goals as optional deadlines);
  - Q8: per-intent recall targets;
  - Q11: the new-material mechanism;
  - Q12: time estimates (the learner's own durations, with an LLM prior).
- Include an optional Today headline: "N demonstrated · N assumed · N learning ·
  N untested — expected recall today N%".
- Leave block selection to the router. The plan's block choice is the action
  router's job (docs/specs/spec_action_router_v1.md, phase R2). This spec defines
  the plan container: minutes, block boundaries, "keep going", re-entry, the
  streak, and what the learner sees. It also defines the interface the router
  fills.
- State which changes alter what is served (with successors and kill switches),
  the migrations, tests, gates and phases. Add an agent prompt template like
  spec_slice_a_practice_and_field_v1.md §6.

Work on branch docs/daily-loop-spec from origin/main, in your own worktree. Commit the
spec; don't merge or push. Return a summary of the decisions the owner must confirm.
```

### Slice 1 M1: offline review of blind grading and history-aware diagnosis

```text
Implement Slice 1 milestone M1 of LearnLoop: the offline review of blind grading and
history-aware diagnosis. Follow the standard rules in
docs/specs/implementation_handoffs.md §0. Review file: docs/reviews/slice-1-m1.md.

Specs:
- docs/specs/spec_blind_grading_diagnosis_split_v1.md, read in full. Build to:
  - the §12 M1 row and §12.1;
  - §4 and §5, including §5.6 snapshot mode;
  - §9.4;
  - §13 E1–E6;
  - the M1 tests in §14.
- docs/specs/spec_slice_a_practice_and_field_v1.md §4 (cross-spec notes):
  - the embedding substrate already exists from Slice A Phase 1; reuse it;
  - pattern-link verdicts import into judgment_ledger;
  - version labels follow Slice A's successors.

M1 changes nothing live and adds no vault migration. `learnloop diagnose --dry-run`
writes to a scratch DB copy.

Build in two stages (owner default; delete this paragraph to build all five arms at
once):
- Stage 1:
  - the S1.0 harness with planted cases;
  - the blind grading prompt;
  - DiagnosisProposal with its context assembler and validators;
  - history modes exact and full;
  - `learnloop diagnose review`, covering arms (a) stored joint grader, (b) exact,
    (d) full, plus the (b′) noise floor.
- Stage 2, only if the stage-1 report leaves the history-mode question open:
  - (c) hybrid kNN, with hypothesis embeddings through the Phase 1 client;
  - (e) snapshot, with the Codex READ_ONLY_WORKSPACE capability.

Judging: planted truth plus a blind pairwise LLM judge in two passes, with verdicts in
judgment_ledger. The optional owner spot-check is capped at about 10 items and
15 minutes.

Done also means:
- M1 runs end to end with fakes on a fixtures-local copy;
- the review file gives the owner the commands:
  1. `learnloop field data-check` first. The run needs ≥ ~40 graded wrong answers
     across topics.
  2. The dry-run cost estimate.
  3. The real run.
  4. The report.
  5. The optional spot-check.
```

### Slice 1 M2: the live split and the diagnosis card

```text
Implement Slice 1 milestone M2 of LearnLoop: the live split between the blind grader
and the history-aware diagnoser, plus the diagnosis card. Follow the standard rules in
docs/specs/implementation_handoffs.md §0. Review file: docs/reviews/slice-1-m2.md.

Prerequisite: the M1 report has been reviewed, and its chosen history mode is
recorded in docs/reviews/slice-1-m1.md (the default is full).

Spec: docs/specs/spec_blind_grading_diagnosis_split_v1.md:
- §4–§8, §10–§11;
- §12 (the M2 row and steps S1.1 → S1.3 → S1.4a → S1.4b only if M1 chose hybrid →
  the diagnosis card, §12.2);
- §13–§14.
Also docs/specs/spec_embedding_consumers_v1.md §5.5 (PF-c). Its grading rules join
the blind prompt at S1.1, and its E1-style before/after report runs after S1.3.

Must hold:
- S1.3 is an algorithm successor with a kill switch, taking the next free version
  label (the spec's "mvp-0.10" and "migration 166" are placeholders).
- Diagnosis is asynchronous. Grading stays synchronous (daily-loop P7).
- Joint vaults rebuild byte-identically under the previous version.
- The diagnosis card asks for at most one optional tap.

Branch slice-1/m2 from origin/main.
```

### Mobile M1: capture (revision 3)

If a mobile agent was launched before revision 3 was committed (`1a0f7a0`), tell it to follow revision 3: one-command tokens with no pairing exchange, no token scopes, and iOS only.

```text
Implement milestone M1 (capture) of LearnLoop's phone client, as specified in
docs/specs/spec_mobile_tailnet_v1.md, revision 3 (the "M1 — Capture" row in §9).
Follow the standard rules in docs/specs/implementation_handoffs.md §0. Review file:
docs/reviews/mobile-m1.md.

Read in full: spec_mobile_tailnet_v1.md, especially
- §3.1 (the capture host, with no SidecarContext);
- §4 (device tokens via `learnloop-mobile token create/list/revoke`, identity check,
  allowlist, limits, doctor);
- §6.1, §6.7, §8 and the M1 gates and tests.
Also docs/specs/daily_loop_frictionless_defaults.md C1–C4. M1 stores captures and
routes them manually; the background processor is M3.

Branch mobile/m1 from origin/main.

Hard rules:
- The host binds only to 127.0.0.1.
- Never run tailscale and never enable Funnel. Write the owner's setup steps
  (tailscale serve, token create, installing the Shortcut) into doctor's output and
  the review file.
- The phone reaches nothing outside the default-deny allowlist.
- Capture never blocks on a model call.
- Use fakes for Tailscale headers in tests.

Done also means:
- everything in the M1 row exists, including the iOS Shortcut file, the desktop
  Inbox strip and `learnloop inbox list`;
- the spec's M1 gates and tests pass;
- the frontend checks pass.
```

### Mobile M2 prerequisites (PR-1 to PR-7)

```text
Implement the M2 prerequisites PR-1 to PR-7 of LearnLoop's phone client, as specified
in docs/specs/spec_mobile_tailnet_v1.md §3.3, with §6.4, §6.5 and §6.8. Follow the
standard rules in docs/specs/implementation_handoffs.md §0. Review file:
docs/reviews/mobile-m2-prereqs.md.

Prerequisites: mobile M1, Slice A Phase 6 and the daily loop's finite plan have all
merged, because these changes touch sessions, queue eligibility and revisions.
Branch mobile/m2-prereqs from origin/main.

The seven changes, each landed as its own commit with its own tests:
- PR-1: secondary attach (SidecarContext.load_secondary), with no writes on attach.
- PR-2: content sync never restores stale scheduling state.
- PR-3: the abandoned-synthesis sweep runs only on primary hosts.
- PR-4: atomic session operations and ownership, including adopt_session.
- PR-5: request origin on the context, mapped to entry_surface.
- PR-6: the device eligibility module, scheduling/device_eligibility.py.
- PR-7: desktop freshness through an app-level revision poll.
Also the probe-presentation check in §6.4.

Done also means: the M2 prerequisites row in §9 is complete. The PWA (M2a) is a
separate agent.
```

### Project understanding M1: delayed questions on agent-written code (can start now)

```text
Implement milestone M1 of LearnLoop's project-understanding track: delayed
comprehension questions on agent-written code. Follow the standard rules in
docs/specs/implementation_handoffs.md §0. Review file:
docs/reviews/project-understanding-m1.md.

Spec: docs/specs/spec_project_understanding_v1.md. Build to:
- §3: automatic capture, by sweeping commits with Co-Authored-By trailers at app
  start and plan build, plus an optional append-only post-commit pending list;
- §4: disclosure, with secret redaction before anything reaches a model;
- §5.2 (delayed probes) and §5.3;
- §6.1: the standalone projects/project_store.sqlite. No vault migration; M2
  imports it later;
- §7 (AI routing), §8.2 gates G1–G3 and G5–G7, the M1 tests in §10, and the §9 M1
  row.
Open decisions: defaults for D1–D10. The opt-in explanation gate (M1b) is NOT part
of this milestone.

Branch projects/m1 from origin/main.

Must hold:
- Tests use temporary git repos created by the tests, never the owner's repos.
- Probe generation and grading use fakes in tests.
- Grading stays learner-blind.
- Probes count as practice only, never cold certification (D6).

Done also means: the review file gives the owner the commands to run:
1. `project enroll <repo>` for each repo they choose;
2. sweep and status;
3. answering probes;
4. the report.
```

### Slice 2 T6: source retrieval (alongside the daily loop)

```text
Implement Slice 2 track T6 of LearnLoop: source retrieval for the reader, the tutor,
Quick Add and PDF pages. Follow the standard rules in
docs/specs/implementation_handoffs.md §0. Review file: docs/reviews/slice-2-t6.md.

Specs:
- docs/specs/spec_embedding_consumers_v1.md: §1 (R1–R6), §4, §9 (T6) in full,
  §12–§13 (T6 entries) and §15 P4;
- the Phase 1 embedding substrate (src/learnloop/ai/embedding.py,
  db/stores/embedding_vectors.py, vault/embedding_recipes.py,
  ops/embedding_backfill.py);
- docs/specs/spec_daily_loop_v1.md, if it exists: capture filing and "Practice this"
  may consume this retrieval, so keep the API usable by them.

Prerequisite: Slice A has merged; T6 reuses Phase 5a's `learnloop embeddings
compare` harness. Branch slice-2/t6 from origin/main.

Must hold:
- Hybrid retrieval:
  - source_block_fts (FTS5 BM25; DERIVED, with exactly one registered replayer);
  - dense retrieval over source blocks (a new recipe named by kind and field);
  - the two fused by RRF.
- LLM query rewriting for conceptual questions. An LLM listwise rerank only on
  consequential paths.
- Consumers:
  - tutor_qa spans become question-dependent, replacing the fixed top-4 LO-linked
    spans;
  - library search goes beyond instr();
  - Quick Add scope goes beyond substring matching;
  - spans without provenance get a nearest-LO suggestion, labelled as a
    suggestion.
- Grounding stays two-stage: retrieve spans, then verify them.
- Retrieval is context, so no successor is needed unless something persisted
  changes meaning. Say which applies in the review file.
- B4 compares page-image embeddings with Marker text chunks:
  - question → page pairs labelled by an LLM in two passes, with agreement
    reported; owner labels are optional;
  - page-image retrieval is the default only if B4 shows a gain (P4).
- The source-block backfill and B4 are paid: spend caps, with --dry-run first.

Done also means:
- the retrieval evaluation runs with fakes on a fixtures-local copy and compares
  against today's substring search;
- the review file gives the owner the commands for the backfill dry-run, the real
  backfill, B4 and the evaluation.
```

### Slice 2 T1 (M3): recurrence with authority

```text
Implement Slice 2 track T1 (milestone M3) of LearnLoop: recurrence with authority.
Mistakes that share a cause across different problems are grouped, and the third
recurrence escalates to a different repair, shown with its evidence. Follow the
standard rules in docs/specs/implementation_handoffs.md §0. Review file:
docs/reviews/slice-2-t1.md.

Specs:
- docs/specs/spec_embedding_consumers_v1.md: §1 (R1–R6; R4 means no calibrators),
  §3 in full, §4, §5.8 (judgment_ledger), §12–§13 (T1 entries), §15 P6 and P13;
- docs/specs/spec_blind_grading_diagnosis_split_v1.md: §5.4 (citation validation),
  §7.6 (the recurrence_key seam), §9.5 (the would-merge log), §12.2–§12.3;
- Slice 1's exit review (docs/reviews/), which must support T1: pattern links were
  judged trustworthy. If it doesn't, stop and say so.

Branch slice-2/t1 from origin/main after Slice 1 M2 has merged.

Must hold:
- No calibrators.
  - Candidate pairs come from hypothesis-embedding kNN, with a top-k and a
    blocking cutoff that B3 sets from recall on confirmed matches.
  - The same-cause judge decides every pair that validated citations don't
    already settle. It is its own route, defaulting to the diagnosis route.
  - Nothing is merged or rejected by score.
- The M1 pattern-link verdicts are imported into judgment_ledger (judge = owner).
  The backlog command runs under spend caps, with --dry-run first.
- B1 (Eedi 2024) and B3 (vault replay) run on the shared compare harness. If the
  Eedi data needs a login, build the loader and leave the download to the owner.
- hypothesis_recurrence_groups (DERIVED) has the no-chaining rule and logs refused
  unions. recurrence_key returns the group id, and singleton groups hash to the old
  key, so vaults with no merges rebuild identically.
- The promotion and escalation change is an algorithm successor with a kill switch.
  It takes the next free version label; the spec's "mvp-0.11" is a placeholder.
  Any false merge in the same-answer/different-cause suite blocks the switch.
- Escalated repairs are shown with their cited earlier answers and a one-tap
  usefulness rating (diagnosis_feedback, response prefixed "escalation:").

Done also means:
- a shadow rebuild of a fixtures-local copy shows only the documented differences;
- the review file gives the owner the commands for the backlog dry-run, B1 and B3,
  the shadow-rebuild review before the switch, and the M3 signals report after
  2–4 weeks.
```

### Slice 2 T4, T5, T7, T8 (one at a time, after T1)

Fill in the track, then give it to an agent once the previous track's report has been reviewed.

```text
Implement Slice 2 track <T4 | T5 | T7 | T8> of LearnLoop, as specified in
docs/specs/spec_embedding_consumers_v1.md <§7 | §8 | §10 | §11>, with the standing
rules in §1 (R1–R6; R4 means embeddings shortlist and judges decide, with no
calibrators) and §4. Follow the standard rules in
docs/specs/implementation_handoffs.md §0. Review file: docs/reviews/slice-2-<track>.md.

Prerequisite: the owner has reviewed the previous track's report (order T1 → T4 →
T5 → T7 → T8; Slice 2 §2). Branch slice-2/<track> from origin/main.

Track rules:
- T4: shadow flags only, and the lexical detectors stay as the floor. Flags may
  propose reserve burns but never execute them until the report is reviewed. Math
  answers also go through the symbolic check.
- T5: nominations only, never identity (spec_knowledge_model.md: no embeddings for
  facet identity). The structuring LLM or the owner decides. Doctor and review
  passes show a cosine column next to Jaccard.
- T7: display only, with zero effect on learner state.
- T8: offline research only, with no live consumer.
  - Pre-register the evaluation in the review file before running anything.
  - Build it as arms in the `learnloop eval` harness from Slice A Phase 2,
    including the zero-data LLM probability arm.
  - Use solver-panel difficulty, never LLM-labelled difficulty.

Done also means: the track's report (Slice 2 §13) generates with fakes on a
fixtures-local copy, and the review file gives the owner the commands to run it for
real, with the dry-run first.
```

### Router R0: the model clients and the `llm_probability` V1–V3 harness arms

```text
Implement phase R0 of LearnLoop's action router: the Decider client (via OpenRouter),
the router LLM route, and the learner field's llm_probability V1–V3 harness arms on
both models. Follow the standard rules in docs/specs/implementation_handoffs.md §0.
Review file: docs/reviews/router-r0.md.

Specs:
- docs/specs/spec_action_router_v1.md: §0, §6 (facts, providers, routes, question
  format) and §11's R0 row;
- docs/specs/spec_learner_field_v1.md: §7.2 (the variant table, the two models and
  the rules), G11, D8 and D9.

First task: confirm how OpenRouter serves perplexity/pplx-decider-v1.1-27b, from
OpenRouter's documentation:
- the endpoint path under https://openrouter.ai/api;
- the request body (state and named questions);
- how typed answers and probabilities come back.
Use Perplexity's Decisions API docs (https://docs.perplexity.ai/docs/decisions/quickstart)
as the reference shape. Record what you found in the review file. If OpenRouter
doesn't expose typed answers, stop and report; that is router D4.

Branch router/r0 from origin/main after the Phase 2/3 integration has merged.

Must hold:
- Provider type decider, with profile openrouter_decider:
  - OPENROUTER_API_KEY;
  - typed question classes (noul, choice, score) and parsing;
  - unknown fields refused.
- Routes:
  - ai.routing.router_decider and ai.routing.llm_probability_decider never fall back
    to a chat provider, and LEARNLOOP_AI_PROVIDER doesn't override them;
  - ai.routing.router_llm and ai.routing.llm_probability_llm use existing chat
    providers with structured output, through a bounded transport only. Codex's
    app-server transport is refused, as Phase 3 did for the family judge.
- Readiness, receipts (purpose plus judge = decider | llm), the Slice A spend
  controls with --dry-run, and privacy disclosures.
- Harness: arms V1, V2 and V3 × {decider, llm}, exactly as the field spec defines
  them:
  - each reported raw and recalibrated (one parameter, fit on past predictions
    only);
  - no outcome or post-attempt material in any prediction;
  - responses cached outside the vault, so replay makes zero calls;
  - never active (G11).
  Register the arms in the unified `learnloop eval` harness.
- Tests use fake endpoints. Make no live calls.

Done also means the review file gives the owner:
- the dry-run cost estimate, then the real `learnloop eval` command with the six
  arms on a copy of their vault;
- what each outcome means: V1 vs V2 vs V3, and Decider vs LLM.
```

### Router R1: decision logging on today's paths

```text
Implement phase R1 of LearnLoop's action router: decision logging with full candidate
sets and exact propensities on today's serving paths. Follow the standard rules in
docs/specs/implementation_handoffs.md §0. Review file: docs/reviews/router-r1.md.

Specs:
- docs/specs/spec_action_router_v1.md: §2 (code truth), §9 (router_decisions) and
  §11's R1 row;
- docs/specs/spec_p4_controller_and_scale.md: §3.3 (the trace contract) and §9.3
  (the randomization layer);
- docs/specs/spec_learner_field_v1.md: §3 (serving origin and serving_propensity).

Prerequisites: R0 and Slice A Phase 6 have merged, since R1 touches the same
scheduler files. Branch router/r1 from origin/main.

Must hold:
- Every Today-queue offer and every staged P2 decision writes a router_decisions
  row with:
  - the full candidate set and planner values;
  - the chosen candidate;
  - the true propensity, or an explicit "deterministic", where it is 1/0;
  - learner picks marked learner_pick.
- "continue" is logged as a candidate wherever a block or item is in progress.
- Probe near-ties are admitted to epsilon_tiebreak with logged propensity, closing
  the probe exclusion at scheduler.py:1544-1551. This is the only serving change:
  an algorithm successor with its own kill switch.
- router_outcomes (DERIVED, one replayer) joins R_next and R_cold under the
  Pipeline plan's S definition, with pending outcomes right-censored.
- No model calls in R1.

Done also means:
- a shadow rebuild of a fixtures-local copy shows only the probe-tie difference;
- the review file shows the logged fields on a sample decision.
```

### Router R2: the Decider router, live for the daily plan

```text
Implement phase R2 of LearnLoop's action router: the Decider and a frontier LLM
choosing the daily plan's blocks inside the P4 staged frame. Follow the standard rules in
docs/specs/implementation_handoffs.md §0. Review file: docs/reviews/router-r2.md.

Specs:
- docs/specs/spec_action_router_v1.md, in full;
- docs/specs/spec_p4_controller_and_scale.md: §3–§5, §7.1 (revised) and §9.3;
- the daily-loop spec's finite-plan sections (P1–P3);
- docs/specs/spec_learner_field_v1.md: §3.1 and §4.1.

Prerequisites: R1 and the daily loop's finite plan have merged, and the owner has
answered router D1–D8 (or said "defaults"). Branch router/r2 from origin/main.

Must hold:
- LearnerStateCardV1 (§4):
  - deterministic from the ledger, with the token budget;
  - no cold-answer or reserved material;
  - never sent to the grader.
- decision/context embeddings and similar-decision retrieval (§5), using matured
  outcomes only.
- One Decider request (router_qs_v1) and one LLM request (router_llm_v1) per decision
  (§6.3), with the LLM's evidence ids validated against the card.
- Selection:
  - the staged and mixture modes (§7.3) and the model_mixture randomization design,
    applied to reversible candidates only;
  - per-component fallback, where a failed model's weight moves to staged;
  - irreversible actions are never sampled (§7.1);
  - the restraint asymmetry (§7.2);
  - fallback to the staged choice;
  - learner picks win.
- Authority and switches:
  - the staged frame composes Today's plan blocks, as an algorithm successor;
  - kill switch router.enabled restores the legacy scheduler exactly;
  - launch mode per D1.
- The learner-facing "why" (§7.4), and `learnloop router report` (§10.3).
- Gates G1–G9 (§12) pass, with a fake Decider and a fake LLM.

Done also means:
- a shadow rebuild of a fixtures-local copy shows only the documented differences;
- the review file gives the owner the commands for the report after 200 decisions.
```

---

*Related: `spec_slice_a_practice_and_field_v1.md` §6 (the template these follow) · `daily_loop_frictionless_defaults.md` · [[Daily Loop Open Questions]]*
