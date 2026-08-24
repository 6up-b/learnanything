# Open Questions

Questions still unresolved after the spec review pass. Grouped by area, marked **Blocking** (must answer before implementation can proceed in that slice), **Soon** (can scaffold first, must answer before that subsystem ships), or **Defer** (decision can wait for v0.2+).

Each question has my recommended answer in *italics*. Treat these as proposals to react to, not decisions.

---

## A. Scheduler & elicitation

### A1. Heuristic surrogate functional form — **Resolved** (§16 Layer 4)

Dual representation: 5-way score bucket alphabet for EIG / surprise / scheduler explanations / goldens, continuous raw score for EMA and analytics. Surrogate factorizes as `P(o | z, q) = P(score) · P(error | score) · P(confidence | score) · P(latency | score) · P(hints | score)` with parametric heads (cumulative logistic for score, Dirichlet-shrunk per-learner propensity for error, calibration-modulated confidence, log-normal latency, hint-request logistic). Parameters live in `algorithm_priors.yaml`. Latency uses graceful-fallback bucket: `unknown` when no calibrated mean exists, contributes nothing to EIG/surprise for that attempt.

### A2. Cross-LO update propagation — **Resolved** (§16 Layer 2 "Cross-LO propagation")

Bounded transitive propagation, not direct-only, not full closure. Default `max_depth=3`, `hop_decay=0.5`, `total_propagated_weight_cap=0.7`. Success: variance shrink only on prereqs. Failure: mean *and* variance, gated by **error type** — `recall_failure` propagates weakly, `conceptual_error` propagates to all, `procedure_error` to procedural prereqs only, `transfer_failure` to conceptual prereqs lightly, `high_confidence_wrong` propagates strongly and triggers misconception repair. Magnitude scaled by depth decay × score severity × grader_confidence × hint_dampening × mastery_weights[axis]. Per-domain overrides and per-LO override knobs (`receives_propagation_from`, `block_propagation_from`, `max_depth_in`). Audit trail in new `attempt_propagation_events` table.

### A3. Axis correlation — **Resolved** (§16 Layer 2 "Axis correlation")

`mastery_weights` is a partition of evidence with sum-to-one invariant enforced by the storage layer. Single observed score, split across axes via `effective_alpha[axis] = base_alpha · mastery_weights[axis] · grader_confidence · hint_dampening · cold_start_factor`. `error_impacts` apply as additive deltas on top, can affect non-targeted axes. Two-step structure (EMA on targeted axes + additive error corrections) lets correlated axes coexist without inflating evidence.

### A4. Disguised-retest / resolved-misconception queue load cap — **Resolved** (§15.7 "Disguised retest policy")

`per_session_max: 1`, `intervals_days: [14, 30, 60, 120, 365]`, `reopen_on_failures: 1`, `selection: oldest_eligible_first`, `active_goal_scope_required: true`. Disguised retests sit on top of, not inside, the queue budget — they replace one slot in the daily review block. Tunable in `algorithm_priors.yaml`.

### A5. Surprise follow-up UX: interrupt vs enqueue — **Resolved** (§16 "Surprise follow-up insertion")

Negative surprise above threshold inserts a follow-up at position 1 of the remaining queue (never interrupts). Feedback screen shows the inserted mode and reason, with `[Skip follow-up]` for this one-time dismissal. Positive surprise does **not** insert any item — only the existing modest FSRS interval stretch applies. Skip rate above a threshold over a window of attempts flags doctor as evidence the surprise threshold may be miscalibrated.

### A6. Mode→axis mapping for domain-registered modes — **Resolved** (§4 `PracticeModeSpec`)

`PracticeModeSpec` schema added in §4 with `default_target_mastery_axes`, `default_evidence_facets`, `default_mastery_weights` (sum-to-1 invariant), `default_grader_tier`, `fsrs_eligible`, `plausible_error_types`, `short_session_eligible`. Resolution order: PI explicit > domain `PracticeModeSpec` > core mode→axis table > hard fail (doctor flags the PI, scheduler refuses to surface it).

### A7. Replay trigger: automatic or manual — **Resolved** (§16 "Replay trigger and nag cadence")

Prompted-with-default-accept banner on vault open. `[Later]` dismisses for the session; banner returns next open. After 3 cumulative dismissals, an extra nudge line is added (mastery numbers may not reflect the current algorithm). MAJOR bumps add the nudge after the first dismissal; MINOR follows the standard 3-dismissal rule; PATCH never prompts but surfaces in `learnloop doctor` summary. New `replay_banner_state` singleton table tracks dismissal count. `learnloop replay-model --accept-without-replay` available for cases where the user knows no real change occurred.

### A8. Cold-start surrogate parameters — **Resolved** (§16 `algorithm_priors.yaml`)

`algorithm_priors.yaml` lives at the vault root, versioned with `algorithm_version`. Holds `mastery` defaults (`ema_alpha`, `mastery_default`, `variance_default`, `cold_start_alpha_factor`, `cold_start_alpha_attempts`, `prior_pseudo_count`), `surrogate` parameters (logistic weights, bucket thresholds, calibration slopes, latency widths), `cross_lo_propagation` defaults and error gates, `staleness` per-axis days, and `domain_overrides` block. Editing the file bumps `algorithm_version` and prompts replay.

---

## B. Grading

### B1. Tier-3 (embedding-similarity) fallback rules — **Resolved** (§15.6 Tier 3 termination rules)

Asymmetric local grader. Below `tier_3_low_threshold = 0.55` → terminal incorrect. Above `tier_3_high_threshold = 0.85` → escalate to tier 4 with `prior_correct` signal *unless* the PI or domain declares `tier_3_terminal_positive: true`. Middle range → escalate to tier 4 (no prior). Terminal-positive is hard-blocked for `proof_reconstruction`, `derivation_reconstruction`, `transfer/near_transfer/far_transfer`, `contrastive_discrimination`, `misconception_repair`, `error_diagnosis`, `disguised_retest`, items with `fatal_errors`, and `high_stakes_canonical_item`. Override possible with `tier_3_terminal_positive_force: true`, surfaced by doctor.

### B2. Local grader confidence and mastery — **Resolved** (§15.6 "Grader confidence")

Critical reframing: **`grader_confidence` measures reliability of the judgment, not how much credit the answer earned.** Partial credit doesn't imply a low-confidence grader; a confident 1/4 is a clear "mostly wrong." Smoothed functions per tier: tier 1 always 1.00; tier 2 0.95 (clean match) / 0.85 (fuzzy match) / 0.70 (ambiguous, usually escalates); tier 3 grows from 0.70 toward 0.90 as similarity moves further below low_threshold (incorrect direction) and from 0.65 toward 0.80 as similarity moves further above high_threshold (correct direction); tier 4 uses model-reported confidence. Stored separately from score on `practice_attempts` and `grading_evidence`.

### B3. Manual review pile-up UX — **Resolved** (§10 Review grades, §11 CLI `learnloop review-grades`)

Counter on main screen (`Pending Reviews: N`) plus key `R` opens the dedicated triage screen. One item at a time, four keys: `✓` accept, `✗` override (opens numeric prompt; sets grader_confidence to 1.0 — human is the grader), `↺` regrade (re-run the LLM, mark previous evidence superseded), `→` defer. Session-scoped `T` flag auto-accepts subsequent tier-4 grades from the same `(prompt_template, prompt_version)`. End-of-session sweep surfaces pending reviews alongside ephemeral promotions. Daily loop never blocked on pending reviews.

### B1\*. Hint-author guardrails — **Resolved** (§9 "Hint-author validation and retry")

Validation: answer-leakage guard (lexical overlap ≤ 40%, key-term verbatim ≤ 1), rubric-trap guard (no fatal-error description verbatim), ladder shape (2–4 hints, ≤200 chars each, monotonic specificity), final-hint relaxed cap 55%. One retry with constraint-patch prompt. Second failure → static template + doctor warning + agent_runs records both attempts. Configurable in `[grading.hint_author_guardrails]`.

### B4. Per-mode default hint ladders — **Resolved** (§9 "Generation policy (hybrid with cache)", §12 `hint-author` role)

Hybrid: authored hints used as-is; missing hints + Codex available trigger the `hint-author` role on first reveal and cache the generated ladder back into the PI YAML through `change_batches` (rollbackable, provenance-tagged); offline fallback to per-mode static templates in `prompts/hint_ladder_<mode>.md` with substitutions (not cached). Disabled-by-default modes (`recognition`, `multiple_choice`) ship `hints: []`.

---

## C. Content model & concepts

### C1. What is a "subject" exactly — **Resolved** (§4 "Subjects as views", §8, §9, §7)

Subjects are views, not content-ownership. LO/PI YAML carries `subjects: [list]` (≥1 element); first entry is primary subject. PI inherits from its LO by default. Notes get Markdown frontmatter `subjects: [list]`. Folder is advisory: doctor warns if `subjects[0]` doesn't match folder, but moving a file doesn't change membership. Per-subject `concept-graph.yaml` view is derived (union of tagged-LO concepts) with `additional_concepts_in_scope`, `exclude_concepts`, `subject_ordering_hints` for curation. `concept_mastery` table is now concept-keyed (not subject-keyed); per-subject aggregates computed on read.

### C2. Vocabulary scale (language domain) — **Defer**

For language, do we want one Learning Object per vocab word? 5000 LOs adds index/embedding cost.

*Recommendation:* Compact bulk format: `vocab.yaml` with one entry per word, each entry has a synthetic stable LO id (`lo_korean_vocab_<hash>`) that the scheduler treats as a real LO. No full LO YAML file is written for vocab; the bulk file *is* the LO storage. Lazy-promote a vocab entry to a full LO file only when the learner wants to add notes/rubrics specific to that word.

### C3. Worked examples as content vs LO — **Resolved** (§15.8)

Worked-example Markdown carries `teaches_los: [list]` (≥1) in frontmatter and an optional `steps:` array with `fadable: bool` flags enabling deterministic faded variants. LO YAML carries `references_worked_examples: [paths]` for the two-way link. Doctor enforces bidirectional consistency. Reveal tracking via new `worked_example_views(lo_id, example_id, example_path, session_id, shown_at, context, attempt_id)` table; scheduler picks oldest-shown.

### C4. Media references survive file moves — **Resolved** (§15.9)

Hybrid hashing by size: files ≤ `[media].full_hash_threshold_mb` (default 50) get full SHA-256; larger files get a fingerprint `size:first_1mb_sha256:last_1mb_sha256`. On missing path, scanner walks vault root + configurable `[media].search_roots` looking for full-hash matches first, fingerprint matches second. Ambiguous fingerprints reported by doctor. Missing media suspends dependent items rather than deleting them. `[media].fail_on_missing = true` by default so missing media surfaces loudly.

### C5. Observation-to-attempt mapping — **Resolved** (§15.10)

`ObservationTemplate` carries `emits_attempt: bool`, `lo_binding.mode` (`learner_picks` | `template_fixed`), optional `applies_to` predicate with `applies_to_mode` (`suggest_only` default | `restrict` for narrow workflows), and `suggest_from` priority list (applies_to matches, active goals, recent attempts, recent errors, embedding similarity). Filled observations can be left unbound (`binding_mode = pending`) and resolved later. Unified end-of-session review surface combines ephemeral promotions, pending grade reviews, observation promotion/binding, and generated-content cleanup, with `[Run All]` fast-path and section-level skip.

---

## D. Replayability & versioning

### D1. Algorithm semantic versioning rules — **Resolved** (§16 "Behavior by bump type")

Single pipeline-wide `algorithm_version`. MAJOR = mastery numbers would change on identical raw events (formula, surrogate retuning, propagation rule). MINOR = additive (new fields/tables/facets); old outputs preserved. PATCH = bugfix-only; outputs match old on previously-working cases. Banner: MAJOR with 1-strike nudge; MINOR standard 3-strike; PATCH silent + doctor surface. `CHANGELOG.algorithm.md` shipped with releases; "What changed?" link renders entries between vault and code versions. Per-component versioning explicitly rejected because cross-component invariants make independent numbers misleading.

### D2. Replay determinism across machines — **Defer**

If a vault is moved to another machine, replay must produce identical mastery numbers (same algorithm version, same raw events). Embeddings, however, depend on the local model. Does replay re-embed?

*Recommendation:* Replay does **not** re-embed. Embeddings are an index, not derived learner state. If the embedding model changes, run `learnloop reindex-embeddings` separately. Scheduler outputs that depend on embeddings (concept-merge suggestions, near-duplicate detection) are not part of replay's invariants.

### D3. Domain migration policy when a plugin is removed — **Resolved** (§4 "Domain enable / disable / purge")

Soft-disable is default: removing from `[domains].enabled` preserves all data, dormants scheduler hooks/TUI panels, marks namespaced PIs unsurfaceable, doctor warns about orphans. `learnloop domain purge <id>` is the destructive escape valve: dry-run preview → type-domain-id-to-confirm → atomic delete with `change_batches` row → rollbackable for 7 days. Refuses if domain is currently enabled (forces explicit soft-disable first). CLI: `learnloop domain list / enable / disable / purge`.

---

## E. UX

### E1. Answer input widget — **Resolved** (§10 "Answer input widget")

Inline up to `[tui].inline_max_chars = 200`; Ctrl-E opens `$EDITOR` for longer. Feedback view renders Markdown via Rich, syntax-highlights fenced code, and shows LaTeX-style `$...$` / `$$...$$` literal with subtle highlight (no live typesetting in MVP). Autosave hooks into existing `session_checkpoints` even during editor sessions. Configurable. Deferred: KaTeX-style math typeset, file-attachment answers, drag-drop, sandboxed code execution.

### E2. Uncertainty dashboard — **Defer**

MVP exposes `learnloop uncertainty` and "Why now?". Richer chart view of belief variance over time is later.

*Recommendation:* MVP: `learnloop uncertainty` returns a ranked text table of "top 10 highest-variance beliefs scoped to active goals" with `mean`, `variance`, `last_evidence_at`, `staleness_days`. That's enough to be useful. Defer interactive dashboards.

### E3. Domain-specific TUI panel contract — **Defer**

How do domain modules contribute TUI panels without making Textual framework code domain-aware?

*Recommendation:* Each domain exposes `tui_panels() → list[TuiPanelSpec]` where each spec is `{slot, widget_factory, predicate}`. Slots are predefined: `practice_screen_sidebar`, `feedback_screen_extras`, `subject_dashboard_extras`. The TUI shell renders any panel whose `predicate(context)` returns true. Concretely: Overwatch can add a VOD-timestamp panel to the practice screen sidebar when `subject.domain == esports_overwatch`. Defer detailed UI work until after MVP scheduler is solid.

### E4. Git policy default — **Resolved-ish, confirm**

Vaults are git-friendly. `[storage].autocommit = false` is the default. Anything else needed?

*Recommendation:* Add a shipped `.gitignore` template with `state.sqlite`, `.learnloop/`, `exports/` excluded by default (these are derived/mutable; the user can opt them in). Add `learnloop git-init` convenience that runs `git init` and writes the `.gitignore`. No automatic commits; no automatic branch creation.

---

## F. Codex integration

### F1. Codex availability detection — **Resolved** (§12 state machine, §15.6 mid-attempt fallback)

In-process state machine: `unknown / available / auth_required / rate_limited / network_unavailable / server_error / streaming_dropped`. Lazy first check on first AI feature (eager probe optional via `probe_on_vault_open`). Cached for `availability_cache_seconds=300`. Per-error retry policy (auth = no auto-retry; rate-limit respects retry-after with 5min floor; network/server use 30s exponential backoff). Auto-regrade-on-recovery scans deferred attempts (`manual_review_reason = 'codex_unavailable'`) when state returns to available, regrades via tier 4, applies held mastery update on success. Mid-attempt failure during tier-4 grading shows 5s inline prompt defaulting to self-grade; alternatives `silent_self_grade` and `block_and_queue` configurable. TUI corner indicator (green/yellow/red/gray). CLI: `learnloop ai status / login / recheck`. New `practice_attempts.manual_review_reason` column.

### F2. Rate-limit handling during a session — **Resolved** (§12 "Per-purpose rate-limit behavior", "Tutor cache-and-resume")

Per-purpose behavior table specifies what happens for graders (mid-attempt fallback), tutor (cache-and-resume with `tutor_pending_messages` table; TUI shows ETA + accepts appended inputs while waiting; auto-resume on recovery), generators (defer to queue), ingestor (defer to background), diagnoser (mid-attempt fallback), simulator proposer (skip silently). Cached tutor messages survive process restarts.

### F3. Codex-simulator ephemeral proposer output schema — **Resolved** (§16 Layer 4 "Proposer output schema and validation")

Ephemeral-minimal output: 1–3 items each with `prompt`, `expected_answer`, `target_lo_id`, `target_axis`, `discriminates_hypotheses: [hypothesis_ids]`, `practice_mode`. No rubric, hint ladder, provenance, or difficulty (defaulted from LO). Validation: schema + active LO + eligible practice_mode + hypothesis-id resolved + embedding-similarity guard against existing PIs on the LO (`sim ≥ 0.85` rejected). One retry with constraint-patch on failure; second failure means session proceeds without simulator ephemerals. Hypotheses themselves are locally generated from heuristic surrogate posterior modes; Codex is question proposer only.

### F4. Conversation thread management — **Resolved** (§12 "Thread management")

Threads keyed by `(vault_id, subject, purpose)`. Tutor: long-lived, persisted in `tutor_threads`, resumed across sessions. All other purposes: stateless per-call. Hybrid archival trigger: `turn_count > 80` OR `cumulative_tokens > 50000` OR `inactivity > 30 days`. On archive, `tutor-summarizer` produces ~200-token brief stored in `tutor_thread_archives`; next thread on same key starts with that brief as first system message. If summarizer fails, archive still happens with `brief = null` (regenerated opportunistically). `learnloop tutor reset/history` CLI surfaces. Config in `[tutor]`.

---

## G. Privacy

### G1. What leaves the machine — **Resolved, confirm**

Default policy: no product telemetry. Local content leaves the machine only through explicit Codex calls.

*Recommendation:* Document this in `README.md` and `learnloop.toml` as `[privacy] outbound_only_to = ["codex_subscription"]`. `learnloop doctor` includes a privacy section showing every outbound destination it knows about, and refuses to add new ones without a config flip.

### G2. Codex content filtering — **Soon**

A learner's vault may contain medical notes, personal info, draft research. When LearnLoop sends context to Codex, what's the redaction model?

*Recommendation:* Per-vault `[privacy].codex_send_allowlist` and `codex_send_denylist` of glob patterns. By default, `profile/*.md` and `subjects/*/notes/*.md` are allowed (they're the point); `errors/global-error-log.md` and `sessions/*.md` are allowed (needed for tutor continuity). The denylist is empty by default but the toml template ships with commented examples like `# constraints.md  # if you put PII here`. Show the redaction summary in the TUI before any tutor turn that includes new files.

---

## H. Numbers that need tuning

These need a default and a way to revisit, not a blocking decision now:

- **EMA `alpha`** (currently 0.2). Sensitive to attempt frequency. Defer tuning to post-MVP with the sample vault as a calibration target.
- **`surprise_diagnostic_threshold`** (1.5). Tied to the bayesian_surprise scale; needs to be set jointly with the surrogate's parameters in A1.
- **`information_gain_weight`** (0.15) and **`error_uncertainty_weight`** (0.10) in the priority formula. Same as above — joint calibration.
- **Embedding similarity thresholds** (0.85 merge, 0.92 dedup). Validated against a small labeled set during the embedding implementation slice.

---

## Resolved so far

- **Blocking (all):** A1, A2, A3, A6, A8, B1, B2, B3, B4, C1, F1.
- **Soon (most):** A4, A5, A7, B1\*, C3, C4, C5, D1, D3, E1, F2, F3, F4.

Only **G2** (Codex content filtering / outbound redaction policy) remains in Soon. Defer items remain: C2 (vocab scale), D2 (cross-machine determinism), E2 (uncertainty dashboard polish), E3 (domain TUI panel contract), H (parameter tuning post-MVP), G1 (privacy confirmation).

## Implementation order

Everything blocking and most polish is decided. Recommended slice order:

1. Vault scaffold, storage, migrations, config loading.
2. Scheduler core (A cluster + cross-LO propagation + `algorithm_priors.yaml`).
3. Tiered grader pipeline with hint-author + `review-grades` triage.
4. Subject-view loader and doctor checks (C1).
5. Worked-example + media-index + observation templates + end-of-session review (C3/C4/C5).
6. Codex SDK adapter with availability state machine, per-purpose rate-limit, tutor cache-and-resume, thread management.
7. Simulator-EIG ephemeral proposer.
8. Misconception lifecycle (disguised retest policy from A4).
9. Replay with banner + diff view + version-tagged snapshots.
10. Soon items resolved slice-by-slice (G2 when needed); Defer when relevant.

## Implementation order implied by remaining answers

The Blocking decisions unblock the implementation slices. Recommended slice order:

1. Vault scaffold, storage, migrations, config loading (no questions left here).
2. Scheduler core (A cluster + cross-LO propagation + algorithm_priors.yaml).
3. Tiered grader pipeline (B cluster) including hint-author and review-grades triage.
4. Subject-view loader and doctor checks (C1).
5. Codex SDK adapter with availability state machine (F1).
6. Everything else — Soon/Defer questions resolved slice by slice as they become relevant.

---

## How to use this document

Walk through one section at a time. For each question, the user either accepts the recommendation, picks a different answer (which I'll record here), or marks it deferred. Resolved questions get folded into the spec as concrete decisions; this file shrinks over time and ends up archived once empty.
