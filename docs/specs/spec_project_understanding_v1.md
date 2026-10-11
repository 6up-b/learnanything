# Project understanding — keeping AI-assisted projects explainable (v1)

**Status:** draft for owner review (2026-10-11). This is a new track. It sits alongside Slice 1 (`spec_blind_grading_diagnosis_split_v1.md`) and Slice 2 (`spec_embedding_consumers_v1.md`) and depends on neither for its first milestone.

**Source material:**
- **Intentions.** `docs/brainstorming/User intentions.md` (the GRU gesture-control project, interview preparation, "loss of understanding of your own projects can be easy with AI generated code", Quest) and `docs/brainstorming/LearnLoop_User_Intentions_v2.md` ("Explain and defend the temporal-model choice in my gesture project…", and the project questions it lists).
- **Citations.** `docs/brainstorming/Bitter Lesson Research Sweep.md` §3, §6, §7. Numbers come from the research agents' reading of each paper's page and were not re-checked unless the sweep marks them ✔. Most sources are preprints.

**Relationship to other documents:**

| Document | Relationship |
|---|---|
| Slice 2 §5 (PF) | Project probes are PF `source_anchored` family items from M2 on. This spec reuses PF's rules by reference: answer-first generation, provenance spans, closed-book filter, executed perturbations, verified references (§5.3–5.4). It does not redefine them |
| Slice 1 S1 / §4 | Probe grading is learner-blind. Slice 1 §5.6 `READ_ONLY_WORKSPACE` is reused for the optional repo-scope context |
| `tutor/teach_back.py` | Its deterministic follow-up planner (`plan_followups`, `:244`) and one-question-at-a-time flow are the base for project-defense mode (M4) |
| `attempts/coldness_receipt.py` | Repo-derived probes declare the working tree as an unobserved exposure channel (§6.3) |
| `spec_p2_narrow_golden_path.md:157` | P2 listed "projects … artifact grading" as out of scope. This spec is where they land |

**What exists in the code today (audited 2026-10-11):**
- **Nothing for repos, git, diffs, or code-understanding items.**
  - The only `git` call in `src/learnloop` is Codex's checkout-revision check (`ai/providers/codex.py:763`).
  - `ingest/` handles PDFs, URLs, and transcripts (extractors: `marker`, `datalab`, `pypdf`). `"code"` exists only as a block role in `ingest/ir.py:251`.
- **"Quest" is only a goal-intent sentence.** `goals/goal_intent.py` resolves it, and `TeachBackSourceContract.quest_*` records it (`vault/models.py:617-622`). There is no Quest feature.
- **Reusable pieces:**
  - teach-back (`attempt_type="teach_back"`, evidence mass 0.8, `config/schema.py:1095`);
  - `assistance_discount` (`attempts/effective_observation.py:132`) and the `assisted` channel in `learner/facet_evidence_timeline.py`;
  - the coldness receipt's `unassisted` and `exposure_isolation` dimensions;
  - the originals store (`ingest/originals.py`);
  - the AI task routing table (`ai/routing.py:18-40`);
  - CLI sub-apps registered in `cli/__init__.py:23-41`.

---

## 0. Thesis

The owner builds projects with coding agents. The evidence (sweep §7) says that arrangement, more than model quality, decides whether the owner keeps understanding the code:

| Study | Finding |
|---|---|
| 2602.20206 | With an LLM-judged **explanation gate** before generated code could be integrated, 39% of users later failed a 30-minute maintenance task without AI. Without the gate, 77% failed. Functional output did not differ between the two AI arms (p = .64) |
| 2607.26375 | A coding agent sped up the build but harmed comprehension (d > 0.80). Comprehension was 0.615 when edits were auto-accepted vs 0.777 when accepted one at a time, and participants still preferred the agent |
| 2601.20245 | AI help cut skill formation by 17% (d = 0.74). Conceptual-inquiry patterns preserved learning (65–86%); delegation patterns did not (24–39%) |
| 2607.08849 | An LLM labelled sessions as augmentation vs automation with 82–87% agreement. Augmentation gave +0.34 SD; the automation advantage was gone a week later |
| 2609.12600 | Content that ends up in an accepted draft is often not actually taken in |

So "I accepted the diff" is not evidence of understanding. Understanding is measured later, unassisted, on questions the code itself answers.

**The track has four parts:**
1. **The explain-before-accept gate.** A short written explanation of an agent diff, judged by an LLM that writes its own explanation first.
2. **Delayed probes.** Unassisted questions about accepted diffs, about seven days later, with answers anchored to `file:line`.
3. **Assistance provenance.** How the code was produced (augmentation vs automation; accepting hunk by hunk vs all at once) decides **where probes are spent**, never how much a grade counts.
4. **Project-defense mode (optional).** Interview-style questioning on the owner's own design decisions.

**The bitter-lesson split:**
- Frontier models do the semantic work: judging explanations, generating and checking probes, classifying sessions, examining.
- Hand-built structure appears only where the evidence shows general models misbehave:
  - a gate the learner cannot skip past silently;
  - grading that never sees the arm or the explanation;
  - one question per turn enforced in code, because prompts did not achieve it (2603.18221: 31.2% → 10.9% only with a code-level validator).

**Milestone 1 is a cheap randomized experiment.** Nothing larger is built until its report is in (§9).

---

## 1. Scope

**In scope:**
- **A1.** Repo enrollment and diff capture (§3), with disclosure controls (§4).
- **A2.** The gate: randomization, explanation capture, solve-first judge, overhead timing (§5.1).
- **A3.** Delayed probes: generation, closed-book filtering, sealing, unassisted answering, blind grading (§5.2). From M2 they become PF items.
- **A4.** Assistance provenance: self-report in M1; transcript-linked LLM classification in M3 (§5.3).
- **A5.** Project-defense mode (§5.4; M4, optional).
- **A6.** The M1 experiment report and its pre-registered decision rule (§8).

**Out of scope:**
- Whole-repo ingestion as a source (a Reader for code).
- Mapping repo concepts onto existing textbook LOs. That uses Slice 2 T5-style nomination later.
- Quest planning (competing explanations → discriminating experiment).
- Any learned model of the owner's code comprehension.

---

## 2. Standing constraints

Inherited: Slice 1 S1–S7 where grading is involved; plan invariants 1–15. In addition:

- **P1. Never block the owner's work.**
  - No hook may fail a commit, a push, or an agent turn. Hooks only append to a pending list and always exit 0.
  - The gate is opt-in per repo (`gate_policy`, §6.1).
  - Every prompt has a skip. A skip is recorded and is never negative evidence.
- **P2. The gate explanation is an assisted record, never cold evidence.**
  - The owner writes it with the diff on screen. In M1 it writes nothing to `state.sqlite`.
  - Whether it later counts as discounted assisted evidence is decision **D3**.
- **P3. Measurement is arm-blind.** The probe generator, the closed-book check, and the probe grader never receive the arm, the owner's explanation, the judge's feedback, or provenance labels. This is enforced structurally: their context dataclasses have no field for any of these (the Slice 1 S1 pattern). Probes are generated before the coin flip is revealed.
- **P4. Rationale must be cited.**
  - A "why was this done" answer key must cite a span: commit message, issue, code comment, ADR, diff line, or the agent's own stated reasoning.
  - The agent's reasoning is labelled `agent_stated`. It is the agent's rationale, not the owner's.
  - Anything uncited is labelled `inferred`, shown as "plausible interpretation", and never used as the key. Generated design rationale is mostly plausible but unstated (2504.20781); filtering by verifiability against issues raises coverage (2506.14649). This is PF §5.3, applied to repos.
- **P5. Minimum disclosure** (§4). Diff hunks plus bounded context go to models; whole repos do not by default. Secrets are filtered. Every model call records what was sent.
- **P6. Replay never calls git, a model, or repo code.** Diffs, probes, and grades are stored snapshots. Replay reads them.
- **P7. Pre-registration.** The M1 randomization scheme, outcome definition, and decision rule (§8.1) are written into the experiment store and the report header before the first probe is graded. They are not changed afterward.

---

## 3. Capture

### 3.1 Options compared

| Option | How | For | Against |
|---|---|---|---|
| **Manual CLI** `learnloop project accept` | The owner runs it on the working-tree diff before committing, or on a commit afterward | Zero integration; works for every agent; the gate prompt has a real terminal | Relies on discipline. A forgotten run is missing data, and the owner might skip diffs they found hard (selection bias) |
| **Commit-trailer sweep** `learnloop project sweep` | Lists commits since the last sweep that carry an agent trailer (Claude Code writes `Co-Authored-By: Claude …` by default) and are not yet captured | Makes the sample complete for agent-committed work; closes the selection-bias hole | Only finds agent-*committed* diffs. Codex and owner-committed agent work need `--agent` or self-report |
| **git `post-commit` hook** | Appends `(repo, sha)` to `projects/pending.jsonl`; always `exit 0` | Never blocks; catches owner-committed work | Can't prompt (no TTY for GUI or agent commits); needs per-repo install |
| **git `pre-commit` / `prepare-commit-msg` prompt** | Interactive gate inside the commit | Gate before integration, as in 2602.20206 | **Rejected.** It blocks commits, breaks agent and GUI commits with no TTY, and violates P1 |
| **Agent hooks** (Claude Code `Stop`, Codex notify) | On turn end with a non-empty diff, enqueue a pending capture and print a reminder | Closest to the moment of acceptance; carries the session id for provenance | Agent-specific config; format churn. It can remind but not run the gate prompt inside the agent |
| **Transcript reading** | Link a diff to the agent session that produced it (`~/.claude/projects/…`, `~/.codex/sessions/…`) | The richest provenance: who proposed what, accept style, the agent's stated rationale | Formats are unstable; heavier privacy footprint. Right for M3 provenance, wrong for M1 capture |

### 3.2 Recommendation

- **M1:** manual `accept`, plus `sweep` as the completeness backstop, plus an optional `post-commit` hook that only appends to the pending list. `learnloop project status` shows pending, captured, and missed counts. The report states **capture coverage**: captured / (captured + swept-but-uncaptured).
- **M2:** an agent `Stop` hook (enqueue + reminder) is added for repos that opt in.
- **M3:** transcript linking, for provenance only.

### 3.3 What a capture records

`project_diffs` (§6) records:
- repo id, base and head sha (or a working-tree snapshot hash);
- the diff as `git diff --no-color --find-renames` output, redacted (§4);
- files touched and lines added/removed;
- `agent`: `claude_code` | `codex` | `other` | `unknown`, from the trailer, `--agent`, or a one-tap self-report;
- `capture_timing`: `pre_commit` | `post_commit`;
- the commit message;
- the captured-at time.

The redacted diff is stored in the originals store (`ingest/originals.py`) keyed by content hash, so probes and grades can be reproduced without git (P6).

---

## 4. Disclosure and secrets

The owner accepts learner text leaving the machine (2026-10-11; OpenRouter is fine). Code repos can still contain credentials, so:

- **What is sent by default:**
  - diff hunks of tracked files;
  - ±40 lines of surrounding context per hunk, extended to the enclosing function or class when that fits within `project.context_token_budget`;
  - the commit message.

  Untracked files are included only with `accept --include-untracked`, which uses `git ls-files --others --exclude-standard`, so `.gitignore` is respected by construction.
- **Never sent:**
  - files matching the secret patterns (`.env*`, `*.pem`, `*.key`, `id_rsa*`, `*.p12`, `*credential*`, `*secret*`, plus the repo's own `.learnloopignore`);
  - hunk lines matching a content scanner for known key prefixes (`sk-`, `AKIA`, `ghp_`, `xox`, `-----BEGIN`) or long high-entropy strings. Those lines are replaced with `[REDACTED:<kind>]` before storage **and** before any model call.
- **Repo scope (opt-in per repo, `context_scope = "repo"`).**
  - The probe generator may explore a read-only snapshot of the repo at `head_sha`: a `git worktree` exported without ignored and secret-pattern files. It does so through Slice 1 §5.6's `READ_ONLY_WORKSPACE` capability.
  - This sends more of the repo, so it is off by default and recorded per call.
- **Receipts.** Every model call goes through `model_call(purpose=…)`, and `model_call_receipts` records:
  - files sent;
  - hunk count and bytes;
  - the redaction count;
  - the context scope.

  `learnloop project status --disclosure` summarizes this per repo.

---

## 5. Contracts

### 5.1 The gate

**Randomization (M1).**
- Permuted blocks of 2: within each consecutive pair of captured diffs, one gets `gate` and one gets `plain`, in random order.
- The seed is stored, and the propensity (0.5) is recorded per diff.
- Diffs under `project.min_diff_lines` (default 5 changed lines) are captured but excluded from randomization, so trivial edits don't fill the sample.

**Gate arm.**
1. The owner sees the diff and writes 2–3 sentences: what the change does and why it was needed. Overhead time runs from prompt shown to feedback dismissed.
2. The **judge** (`project_gate_judge`) reads the redacted diff and context. **It writes its own expected explanation first** (solve-first; 2607.05904 cut false accepts from 0.719 to 0.012 this way), then reads the owner's.
3. The judge returns `claims[]`, each `{claim, status: correct | incorrect | missing, diff_ref: file:line}`, plus one short piece of feedback naming what was missed. It scores claims, not prose (2607.28210: fluency and language bias).
4. The owner may revise once. Both versions are kept.

**Plain arm.** Only the overhead clock and the provenance self-report run.

**Both arms.** The owner gets one optional tap each:
- accept style: `per_hunk` | `all_at_once` | `unknown`;
- how the agent was used: `I designed, it typed` | `we iterated` | `it designed` | `skip`.

**The gate never blocks.** Skipping the gate in the gate arm is recorded as `gate_skipped` and analysed as assigned (intention-to-treat).

### 5.2 Delayed probes

**Generation (at capture, before the arm is revealed; P3).**
- `project_probe_authoring` produces about 6 candidates per diff, answer-first:
  - a reference answer citing `file:line` at `head_sha`, or a commit or issue span;
  - then the question.
- Candidate kinds:
  - `what_does` (what this does / trace this computation);
  - `where_change` (where would you change X to achieve Y);
  - `predict` (predict the output or shape for input Z);
  - `why` (only with a cited rationale span, P4).
- The rules are PF §5.3's `source_anchored` rules. `what_if` needs an executed perturbation (PF §5.3), so it waits for M3 (§9).

**Filters.**
- **Closed-book** (PF §5.4; Code-QA-Bench 2605.29277). A model without the diff or repo answers each candidate. A correct answer, graded against the reference by the probe grader, rejects the candidate as generic.
- **Validity.** Each reference's `file:line` citations must resolve in the stored snapshot, and quoted code must match verbatim. Unresolvable candidates are dropped.

**Selection.** Two survivors per diff are chosen **at random** with the stored seed. That prevents choosing easy or hard probes depending on the diff. If fewer than two survive, the diff is reported as `under_probed`; it stays in the analysis with whatever probes it has.

**Sealing and due date.** Probes are sealed (never rendered) until `captured_at + project.probe_delay_days` (default 7).

**Answering.** `learnloop project probes` serves due probes one at a time.
- The owner declares the standard of the existing `unassisted` dimension: no AI, and **no looking at the repo**. They then answer, or tap `don't know`, `question is unfair/ambiguous`, or `skip`.
- Late answers are allowed; `answered_at - due_at` is recorded.

**Grading.**
- The grader reads only item-side material (P3): the probe, its reference, and the stored context. It is the Slice 1 blind grader where built; until then a minimal `ProbeGradingContext` with the same structural blindness.
- One high-effort pass; no voting (sweep §3).
- The owner can contest a grade. A contested grade is adjudicated by the owner and stored as the outcome of record, with the original kept.

### 5.3 Assistance provenance

**Signals:**
- M1 self-report taps (§5.1);
- `agent` from the trailer;
- **M3:** an LLM classification (`project_session_classify`) of the linked agent transcript into `augmentation` | `automation` | `mixed` (2607.08849 reported 82–87% agreement with human labels), with quoted evidence turns;
- accept style inferred from transcript events where the agent records them.

**Use: provenance chooses where probes are spent, and never changes a grade.**
- Diffs labelled `automation` or `all_at_once` get probe priority in the queue (M2+). Those are the arrangements where comprehension loss was largest (2607.26375; 2601.20245).
- Evidence weights are unchanged: a probe answer is graded and weighted the same whatever produced the code.
- Persistence: 2604.04721 found giving up rises after answer-on-demand help. The rate of `don't know` and `skip` on probes is reported per provenance label, as an outcome.

**Validation.** On a sample of 20 sessions, the owner labels augmentation vs automation blind to the classifier. Agreement is reported before M3 lets the classifier set probe priority.

### 5.4 Project-defense mode (M4, optional)

- **Purpose.** Interview-style defense of one's own project ("why a GRU, what changes if the latency budget halves, what would show the design is failing").
- **Machinery.** Built on `tutor/teach_back.py`, with a skeptical-interviewer role instead of the naive student. Two rules are enforced **in code**, not in the prompt (2603.18221):
  - **One question per turn.** A validator rejects and regenerates any examiner turn with more than one question.
  - **Topic selection is deterministic.** The next topic comes from the project's PF families, ranked by `plan_followups`-style uncertainty (`teach_back.py:244`). It is never chosen by the model; when the model was asked to pick at random, 86% of picks landed on one case (2603.18221).
- **Grading.** Solve-first, claims not prose. Recorded as a `teach_back` attempt through `apply_attempt`, with today's teach-back evidence mass.

---

## 6. Persistence

### 6.1 M1: standalone experiment store (no vault migration)

M1 writes only to `<vault>/projects/gate_experiment.sqlite`. Its schema is owned by `learnloop/projects/experiment_store.py`. M1 touches no `state.sqlite` table, algorithm version, or rebuild path. It uses the same connection helper (`learnloop.db.connection.connect`) and is backed up with the vault directory.

| Table | Contents |
|---|---|
| `repos` | id, path, remote URL, enrolled_at, `gate_policy` (`experiment` \| `off` \| `opt_in` \| `default`), `context_scope`, ignore/secret pattern versions |
| `diffs` | §3.3 fields + originals-store hash + `excluded_reason` |
| `assignments` | diff_id, block id, arm, seed, propensity, `gate_skipped` |
| `gate_events` | diff_id, explanation versions, overhead seconds, judge model + prompt version, judge expected explanation, `claims_json`, feedback |
| `provenance_reports` | diff_id, accept style, usage tap, source (`self_report`) |
| `probes` | diff_id, kind, question, reference + citations, closed-book result, selected flag, sealed-until, generator model + prompt version |
| `probe_responses` | probe_id, answer, declaration, served/answered timestamps, grade, grader model, contest + adjudication |
| `preregistration` | the §8.1 rule, the outcome definition, the seed, and a hash of all three, written before the first grade |

### 6.2 M2+: vault tables (next free migration numbers after the Slice 1/2 heads)

Follows the `CLAUDE.md` head-fixture procedure and is classified in `db/table_roles.py`:

| Table | Role |
|---|---|
| `project_repos` | RAW_LEDGER |
| `project_diffs` | RAW_LEDGER |
| `project_gate_events` | RAW_LEDGER |
| `project_provenance` | RAW_LEDGER (self-reports and classifier outputs, with the source tagged) |
| `project_capture_queue` | WORKFLOW (pending captures from hooks and sweeps) |

- **M1 rows are imported once** (`learnloop project import-experiment`).
- **Probes become PF `source_anchored` family items** (Slice 2 §5.1): `PracticeFamily` under one LO per enrolled repo, with items carrying `family_id` and `variant_relation`. They are administered through the normal attempt path, so they need no project-specific tables.

### 6.3 Coldness of repo-derived probes

Between accepting a diff and answering a probe, the owner may read or edit that code. LearnLoop has no telemetry on this. So the coldness receipt (`attempts/coldness_receipt.py`) declares a new unobserved channel, `repo_working_tree`, and `exposure_isolation` for these items is `unknown`, never a silent pass.

As a result, repo probes qualify as practice evidence but not as held-out certification (decision **D6**). The `unassisted` dimension reads the §5.2 declaration.

---

## 7. AI routing

- **New `AITask`:** `"project"` (`ai/routing.py:18-29`), defaulting to the grading provider, with operations:
  - `project_gate_judge`;
  - `project_probe_authoring`;
  - `project_closed_book_check`;
  - `project_session_classify` (M3);
  - `project_defense_question` (M4).
- **Probe grading** uses the `grading` route.
- **Repo-scope probe authoring** requires `READ_ONLY_WORKSPACE` (Slice 1 §5.6). Without it, `context_scope` falls back to `diff`.
- **Code location.** A new package, `src/learnloop/projects/`:
  - `capture.py` (git via `subprocess` with `git -C`, no shell);
  - `redaction.py`;
  - `gate.py`;
  - `probes.py`;
  - `experiment_store.py`;
  - `report.py`;
  - later, `provenance.py` and `defense.py`.

  It gets an import-linter contract entry (`uv run lint-imports`). The CLI is `src/learnloop/cli/project.py`, registered as `project` in `cli/__init__.py`.

---

## 8. Evaluation

### 8.1 M1 pre-registered decision rule (the one numeric threshold in this spec)

**Unit.** A randomized diff, up to the first 20 eligible diffs after enrollment: 10 `gate`, 10 `plain` by the block design.

**Outcome.** A diff's probe accuracy is the mean normalized rubric score (0–1) of its selected probes, using contested-and-adjudicated grades where they exist. An arm's accuracy is the mean over its diffs. The analysis is intention-to-treat.

**Rule.**
- **Gate becomes the default** for enrolled repos if:
  - gate-arm accuracy minus plain-arm accuracy is **≥ 0.15**; and
  - the **median gate overhead is < 120 s per diff**.
- **Otherwise** the gate is offered as **opt-in**.

**Reported alongside, without changing the rule:**
- a permutation-test interval on the difference;
- the noise floor: a regrade of 10 random probe answers by the same grader;
- the per-arm `don't know` / skip / "unfair question" rates;
- capture coverage (§3.2);
- `under_probed` diffs;
- the split by `capture_timing`;
- the split by agent;
- judge-claim examples.

Twenty diffs detect only a large effect. The original study's gap was 38 points of failure rate (77% vs 39%). The report says plainly when the interval spans zero.

### 8.2 Correctness gates (pass/fail)

| Id | Gate |
|---|---|
| G1 | Hooks and sweeps always exit 0, including on git errors, a missing vault, or a locked DB (tested with injected failures) |
| G2 | Secret filtering: fixture repos with planted keys and `.env` files never appear in any model-call payload or stored diff (asserted through a fake transport) |
| G3 | Arm-blindness: the rendered generator, closed-book, and grader prompts contain no arm, explanation, judge output, or provenance label; their context dataclasses have no field for them |
| G4 | Randomization: blocks of 2 balance exactly; the seed reproduces assignments; trivial diffs are excluded before assignment |
| G5 | Sealing: no probe text is rendered before `sealed_until` by any command, including `status` |
| G6 | M1 writes nothing to `state.sqlite` (row counts and schema hash unchanged) |
| G7 | Replay (M2+) makes no git, model, or subprocess calls |
| G8 | Pre-registration is written and hashed before the first grade; the report refuses to run if it is missing or modified |

### 8.3 Quality reports (no thresholds)

| Milestone | Report |
|---|---|
| M1 | §8.1 report. Plus probe validity: "unfair/ambiguous" taps, contest rate, closed-book rejection rate, citation-resolution failures, and generation cost per diff |
| M2 | Probe uptake in the normal queue; per-provenance probe outcomes; repo-family maintenance outcomes over time |
| M3 | Classifier agreement with the owner's blind labels (§5.3); executed-perturbation success rate |
| M4 | Defense sessions: examiner turns rejected by the one-question validator; owner usefulness taps |

---

## 9. Rollout

| Milestone | Build | Owner does | Gate to proceed |
|---|---|---|---|
| **M1 — Gate experiment** | `projects/` capture, redaction, gate, probes, experiment store, report. CLI: `project enroll`, `accept`, `sweep`, `status`, `probes`, `report`. Optional `post-commit` hook installer (append-only) | Runs `accept` on the next ≥20 eligible agent diffs (`sweep` as backstop); answers 2 probes per diff ~7 days later; ~1–2 min per gated diff, ~3 min per probe pair | G1–G8 pass; §8.1 report reviewed. The decision rule sets `gate_policy`. **M2 proceeds only if** the probes were judged valid enough to be worth scheduling (validity rows of the M1 report) |
| **M2 — Projects in the loop** | Migrations (§6.2); import M1 rows; probes become PF `source_anchored` items (needs PF-a/PF-b); `repo_working_tree` coldness channel; agent `Stop` hook for opted-in repos; sidecar handler `learnloop_sidecar/handlers/projects.py` (status, disclosure, gate policy) | Studies normally; repo probes appear in the daily queue | M2 report reviewed |
| **M3 — Provenance + what-if** | Transcript linking and `project_session_classify`; provenance-driven probe priority; `what_if` probes via repo-declared `probe_check_command`s (e.g. a shape check or a 2-minute training run), run in PF's sandbox (Slice 2 §5.3) | Labels 20 sessions blind; declares check commands for repos where it wants what-if items | Classifier agreement reviewed |
| **M4 — Project defense** (optional) | §5.4 | Uses it before interviews | Owner usefulness |

---

## 10. Tests

- `test_project_capture.py`:
  - diffs from fixture git repos built in `tmp_path`: working tree, commit, renames, and untracked with `--exclude-standard`;
  - trailer detection;
  - `capture_timing`.
- `test_project_redaction.py`:
  - secret-pattern files skipped;
  - key-prefix and entropy lines redacted;
  - `.learnloopignore`;
  - redaction counts recorded.
- `test_project_gate.py`:
  - block randomization and seed reproducibility;
  - trivial-diff exclusion;
  - the judge's expected explanation is requested before the learner's text is included (solve-first ordering in the rendered prompt);
  - claim validation (`diff_ref` resolves);
  - skip → `gate_skipped`;
  - overhead timing with an injected clock.
- `test_project_probes.py`:
  - answer-first ordering;
  - citations resolve and quotes match verbatim;
  - closed-book rejection;
  - seeded random selection;
  - sealing (G5);
  - `under_probed`.
- `test_project_blindness.py`: G3, on rendered prompts and on the context dataclasses' fields.
- `test_project_hooks.py`: G1. The installer writes an append-only hook that exits 0 under every injected failure.
- `test_project_experiment_store.py`:
  - G6 (no `state.sqlite` change);
  - G8 (pre-registration hash);
  - `import-experiment` round trip (M2).
- `test_project_report.py`:
  - the §8.1 rule on synthetic outcomes at, above, and below both thresholds;
  - intention-to-treat handling of skipped gates;
  - the permutation interval is deterministic under a seed.
- **Fakes:** `tests/structured_ai.py` gains handlers for the `project_*` purposes. The fake transport records payloads, for G2 and G3.

---

## 11. Open decisions

| # | Decision | Recommendation |
|---|---|---|
| D1 | M1 capture: manual `accept` + `sweep` + optional append-only `post-commit` hook, or agent hooks from the start? | Manual + sweep + optional hook. Agent hooks in M2, once the experiment says the gate is worth the friction |
| D2 | M1 storage: standalone `projects/gate_experiment.sqlite`, or migrate `state.sqlite` now? | Standalone. M1 stays off the migration and algorithm-version path, and M2 imports it |
| D3 | After M1, does the gate explanation count as evidence? | No by default (P2). If wanted, as an assisted record with `assistance_discount`, never toward coldness or certification |
| D4 | Probe delay and count | 2 probes at 7 days, pre-registered. A 30-day re-probe can be added in M2 as ordinary PF scheduling |
| D5 | Agent attribution for Codex and owner-committed agent work | `--agent` flag + one-tap self-report; transcript linking in M3 |
| D6 | Repo probes and coldness: practice evidence only, or eligible for cold certification? | Practice only while `repo_working_tree` is unobserved (§6.3). Revisit only if an editor or agent telemetry channel exists |
| D7 | Default context sent to models | Diff hunks ±40 lines (to the enclosing function when it fits) + commit message. `repo` scope opt-in per repo |
| D8 | What-if execution | Only repo-declared `probe_check_command`s, in PF's sandbox, opt-in, M3 |
| D9 | LO mapping for project families | One LO per enrolled repo in M2. Link to textbook LOs (e.g. the GRU LO) later via T5-style nomination, owner-confirmed |
| D10 | Should the gate arm's judge feedback show the judge's own explanation? | Show only missed or incorrect claims with `file:line`. Showing the full explanation turns the gate into a reading exercise and weakens the manipulation |

---

*Related: `spec_blind_grading_diagnosis_split_v1.md` · `spec_embedding_consumers_v1.md` (§5 PF) · [[Bitter Lesson Research Sweep]] · [[User intentions]] · [[LearnLoop_User_Intentions_v2]] · `spec_p2_narrow_golden_path.md`*
