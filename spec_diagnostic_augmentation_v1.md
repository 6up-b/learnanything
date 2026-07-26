# Diagnostic augmentation & measured minimal repair — plan of changes (v1)

**Status:** proposed direction for the phase after P2 of
`spec_causal_attribution_v1.md` lands.

**Relationship to the causal-attribution spec.** That document is the authority
on epistemics: the authority model (§2), causal-state ownership (§3), the
deterministic firewalls, promotion discipline, and the P0a/P0b/P1/P2 sequence.
Nothing here weakens any of it. This document supersedes only its *forward*
sequencing:

| v1 section | Disposition here |
|---|---|
| §8 (P3 simulations) | **Split.** Eval-harness and pre-screening uses move to Phase B. The likelihood/posterior arm stays parked (§6). |
| §8.5 (P3.5 learning patterns) | **Relocated** to its own document (§7). Not in this plan. |
| §9 (P4 learned repair policy) | Unchanged in intent. Its missing-vocabulary *capture* is pulled forward to **Phase A (A5)** because it cannot be backfilled; its clustering and review stay in Phase D. |

**Successor: `spec_measurement_efficiency_v1.md`.** This document measures and
improves the *diagnostician*. It does not touch the **instruments** the
diagnostician reads, and that is a real gap: §4's Phase C ladder is four
diagnosis-side rungs (prompt order, verifier exposure, k-sampling, history) while
the primary metric §3 B5 declares — `problems_to_cold_success` — is largely
determined by how much a single question can measure. The successor takes over
three things and nothing else: authoring rungs alongside Phase C (its Part I, same
hypothesis/revert discipline), the certification metrics added to B5 below, and
the *gate* half of Phase D, which moves upstream to ingest because a facet minted
at ingest is a measurement obligation from that moment. Phase D's clustering and
review loop stay here, unchanged.

---

## 0. Thesis

P0–P2 removed the machinery that corrupted a correct natural-language
diagnosis into false structure. That restores the diagnostician to its
unassisted baseline. It does not exceed it.

Nothing shipped so far makes the model *better* at identifying learner
mistakes than an unconstrained model reading the trace, and nothing measures
whether it is. Meanwhile the half of the architecture that should be
harness-owned — computing the minimal repair counterfactual — currently ranks
candidate repairs by three numbers the model reports about itself
(`services/causal_attribution.py:504-512`).

This phase does two things in strict order:

1. **Make minimal repair actually computable**, so the deterministic layer owns
   the part it is good at.
2. **Make diagnostic quality measurable, then improve it against that
   measurement.** Every augmentation is a hypothesis; none ships without an
   evaluation that could have rejected it.

The division of labour is unchanged and correct: **the LLM is the
counterfactual generator; the harness is the feasibility and minimality
checker.** This phase finishes the harness half and starts genuinely investing
in the LLM half.

## 1. Standing constraints

Inherits both standing constraints of `spec_causal_attribution_v1.md`
(bitter-lesson alignment; schema minimalism without the lazy-model loophole),
plus:

3. **No augmentation without a rejection criterion.** Every change in Phase C
   states its hypothesis, its metric, and the result that would cause it to be
   reverted. A prompt change that cannot be shown to help is a prompt change
   that ships on taste.
4. **Deterministic quantities outrank model-reported ones wherever both
   exist.** This is v1 §2's authority ladder applied to selection keys, not
   only to belief writes. A model-reported count may break ties among
   deterministically indistinguishable candidates; it may never overrule a
   computed one.
5. **Facets stay.** Scheduling, retention, and EIG need a stable *addressable*
   state vocabulary; an NL diagnosis is not addressable. v1's framing — facets
   as knowledge claims never error labels, evidence flowing only through
   criteria that genuinely measure them, the error space unbounded and in prose
   — is the role facets are good at. This phase grows that vocabulary
   (Phase D); it does not shrink or replace it.
6. **Capture-now data is Phase A by default.** If an artifact cannot be
   reconstructed from the log after the fact, its *capture* belongs in the
   earliest phase regardless of where its *consumers* live. This document
   originally applied that reasoning to A4 and missed it for two others: the
   missing-vocabulary note (now A5) and §7's frozen pre-decision baseline
   prediction snapshot, which §8.5.1 explicitly forbids recomputing later
   ("never recompute a historical baseline with the improved pattern model —
   that erases the residual being explained"). Relocating the learning-pattern
   *machinery* is right; relocating the capture of frozen baselines with it
   would silently delete the future ability to run any of it. Split capture
   from consumption whenever the two can be split.

## 2. Phase A — close the P2 debt

These six calcify. A1 and A2 get harder once receipts and taxonomy assignments
accumulate; **A4, A5 and A6 cannot be backfilled at all** (standing
constraint 6) — every attempt graded before A4 exists is a labelled example
lost permanently, every abstention recorded before A5 exists is a
vocabulary-inadequacy signal lost permanently, and you cannot reconstruct after
the fact which claims a learner was actually shown.

A7 is not listed as a numbered item because it is one column set, but it is
Phase A for the same reason: **`agent_runs` has no token columns today**
(verified — `001_initial.sql` defines the table; only the unrelated reader
request table in `093` tracks tokens). v1 §11 schedules them under P3. Add
them here, following the reader table's existing
`est_/actual_ input_/output_tokens` naming rather than growing a second
convention, or `tokens_per_resolved_diagnostic_episode` stays unproducible and
C3's revert criterion stays unmeasurable.

### A1. Minimal-repair selection becomes structural

`select_minimal_repair` (`services/causal_attribution.py:444-560`) ranks by
`(contradiction, invalid_rule, protected_violation, latent_cost,
checkpoint_cost, burden, repair_class_id)`. After the three deterministic
firewall booleans, every sort key is a length of a model-supplied list or the
model's own `expected_minutes`. `_trace_backtracking_depth`
(`:1240`) is genuinely structural and is not in the rank; `_trace_edit_cost`
is computed at `:526` and used for nothing.

Changes:

- **New rank order:** `(contradiction, invalid_rule, protected_violation,
  backtracking_depth, validated_checkpoint_cost, trace_edit_cost, latent_cost,
  burden, repair_class_id)`.
- **Validate checkpoint claims at validation time.** `changed_checkpoint_ids`
  must be a subset of some recipe's checkpoints. Today a hallucinated id causes
  every recipe to be skipped (`:1256`) and depth to become `None` — the one
  deterministic term degrades invisibly. Emit a typed
  `unverifiable_checkpoint_claim` rejection reason instead.
- **Resolution floor on `latent_cost`:** differences within ±1 are ties and
  fall through to the deterministic keys. v1 rejects per-criterion outcome
  distributions as "fabricated precision at real token cost"; a raw list
  length is the same fabrication.
- **Declare the regime.** Record `selection_basis: structural |
  model_reported` on the minimality receipt. When the item's `trace_contract`
  is `no_reliable_decomposition`, the deterministic keys are unavailable and
  selection legitimately falls back — but P4 consumes these receipts as
  training records and must be able to tell the two regimes apart.
- **Bump `REPAIR_POLICY_VERSION`** (`:55`). `structural_lexicographic_v1`
  currently overclaims; the ordering changes regardless.

**Why the reorder.** BRACE's latent-space minimality (d_U) is the right
*objective*, but ordering by a noisy estimator of it ahead of a reliable proxy
maximizes the wrong thing. Latent-claim counts are model self-reports;
backtracking depth and checkpoint diffs are computed against the trace
contract. Order by what you can verify, break ties by what you cannot.

### A2. Mechanism taxonomy keys on repair, not on strings

`mint_causal_mechanism_taxonomy` (`:576`) groups on the exact normalized
`operation` string with min support 2 and explicit singleton abstention. As a
first implementation that is honest — it is a frequency table with an
abstention arm, not a clustering claim. But the key recovers the grader's
lexical habits: `dropped_sign`, `sign_dropped`, and `lost_negative_branch` are
three singletons that all abstain, then mint as three mechanisms once counts
grow.

Change the grouping key to **shared episode repair class + probe
discrimination profile**; keep the operation string as the human-readable
label. This applies v1 §9's own criterion — a cluster earns an id only when it
"predicts a distinct repair or measurement need" — to §6.1, where it is
currently absent. A mechanism distinction that changes no repair and no probe
is a synonym.

Do this before real volume accrues: taxonomy versions and assignments are
append-only (migration 119), so a wrong key means migrating assignments later.

If semantic embedding is ever added, require the taxonomy to survive
re-derivation from a second model's operations over the same attempts.
Cross-model agreement is the only external validity check available in a
single-learner vault.

### A3. The divergent-repair hold gets its own type

`start_remediation_episode` raises `RemediationError` when
`remediation_block_reason` reports divergent causal repair classes
(`services/remediation.py:39-50`); the sidecar converts it to
`SidecarError("invalid_request", …)`
(`learnloop_sidecar/handlers/remediation.py:47-50`) — the same code as
"episode does not exist" and "no practice item is available."

v1 §7's designed behaviour is *hold the branch-specific repair and raise a
high-priority diagnostic need*. That state is legitimate and expected; it must
not reach the UI indistinguishable from a client bug. Give it a typed reason
now (`needs_disambiguation`, carrying the diverging repair-class ids) rather
than waiting for the `causal_orchestrator` refactor the comment at
`remediation.py:41-46` forward-references — that module does not exist.

### A4. Start the diagnosis-adjudication store

Grade-*points* adjudication exists (`cli.py:1068` → `append_adjudication`).
Diagnosis adjudication does not. v1 §12 lists "first-divergence accuracy vs
adjudication" as a metric with nothing producing it.

Append-only store, one CLI command, four fields per record: the attempt, the
adjudicated first-divergence anchor, the adjudicated minimal repair, and a
verdict on what the system chose (`correct | wrong_anchor | wrong_repair |
should_have_abstained | correctly_abstained`).

This is the eval set, the few-shot pool, and the eventual fine-tune set. Every
attempt graded before it exists is a labelled example lost permanently. It
costs one table and it gates Phase C.

**As shipped** (`services/diagnosis_adjudication.py`, migration 126,
`learnloop diagnosis {queue,adjudicate,scoreboard}`), with three deltas from
the paragraph above:

1. **A sixth verdict, `should_not_have_abstained`.** The five have no value for
   a *false* abstention, so abstention precision
   (`correctly_abstained / all abstentions`) would be 1.0 by construction and
   §3 B5's metric could never fail. Standing constraint 2 and §11's "no new
   enum without an abstention arm and a two-tailed fill-rate watch" require
   both tails to be representable, and the enum calcifies on an append-only
   table. The verdict vocabulary partitions on what the system did: the
   abstention verdicts are recordable only against an abstention and the other
   four only against a filled diagnosis, which is what makes the confusion
   matrix (and therefore precision *and* recall) computable.
2. **Every record pins the versions it judged**: diagnosis receipt id,
   `decision_policy_version`, `REPAIR_POLICY_VERSION`, `GRADING_PROMPT_VERSION`,
   grader model/provider/revision, receipt schema version, plus the system's
   own anchor and repair-class choice. The receipt lives in a replay-rebuildable
   debug payload; a verdict that had to re-read it would silently change
   meaning after a rebuild.
3. **`queue_reason` on every record.** Adjudication is queued from learner
   contests first, then abstentions, then the cases the system itself flagged,
   then an unflagged stratum. Persisting which stratum a record came from is
   what makes B4's planted-vs-adjudicated agreement interpretable rather than
   an artifact of an adversarially selected set.

**The learner contest is a queue, not a substitute.** §5.6's typed `doesnt_fit`
vocabulary is already wired to the feedback screen and is the cheapest signal
available, so the queue ranks contested diagnoses first and each adjudication
links the contest that prompted it. They stay separate records: the v1 §2
producer/confirmer matrix lists learner confirmation and adjudication as
distinct confirmation channels, a contest carries no anchor and no repair (two
of the four required fields), and a contest-only eval set is ~100% negative
verdicts, so `correct` and `correctly_abstained` would never be observed.

In a single-learner vault the adjudicator IS the learner, so a CLI annotation
task competes directly with learning time — which is why this store accrues at
"a handful of cases per session". Prefer capturing it as a **by-product of an
affordance the learner already has reason to use**: v1 §5.6's typed
`doesnt_fit` / contest vocabulary, asked on the feedback screen "before the
learner context-switches" and already wired through `contest_causal_diagnosis`
to the Tauri contest UI. A learner who has just been told something wrong about
themselves is motivated to say so; nobody is motivated to do annotation
homework. Keep the CLI path for deliberate, considered verdicts — but if the
primary producer is the CLI, the volume problem is self-inflicted. Where §2's
producer/confirmer matrix requires the learner's report and a considered
adjudication to stay distinct records, keep them distinct but share the
substrate.

### A5. Materialize missing-vocabulary notes (moved here from Phase D)

**Moved from Phase D by A4's own argument, which applies identically and which
the original draft did not apply here.** Abstention rate is the system's
measurement of its own vocabulary inadequacy; every abstention that happens
before the note store exists is that signal lost permanently. Phase D needs
only abstentions and repair classes, and both exist by P1 — so there is no
dependency holding capture back, only sequencing inertia.

**The substrate does not exist yet.** v1 §13 and §5.8 refer to
missing-vocabulary notes accumulating for clustered review; nothing in the
codebase produces or stores them. Today an abstention writes
`resolution_status='abstained'` plus `abstention_reason` on the attribution and
stops there.

Capture only — no clustering, no proposals, no review surface, all of which
stay in Phase D:

- On abstention, and on a §5.8 facet-abstaining variant, write an append-only
  note: the trace, the criterion, the abstention reason, the selected repair
  class, and the item context.
- Stamp the same version set A4 records (`GRADING_PROMPT_VERSION`, model
  revision, `decision_policy_version`), so a later cluster can tell whether a
  vocabulary gap is real or an artifact of one prompt version.
- Surface the abstention rate alongside the existing two-tailed fill-rate
  telemetry (`cli.py` attribution audit report). A rate nobody reads is not a
  signal; standing constraint 2 requires watching both tails, and this is the
  tail that says "the vocabulary cannot name what the learner did."

The motivating exhibit is exactly such a case — no facet for branch retention,
none for sign-case analysis or solution enumeration. That is the shape of the
data this captures.

### A6. The system must be able to say it was wrong

v1 gives the learner a contest action (§5.6 `doesnt_fit`) and gives the system
a demotion lifecycle (`retired_misdiagnosed`, `contradicted_by_trace`,
`superseded`, with history preserved). **The two are not connected in the
learner's direction.** A belief can be asserted to the learner, later retired
as a misdiagnosis, and the learner never hears the correction — they are left
holding the original claim about themselves.

That is a trust defect, not a data defect, and it is the exact counterpart of
the contest affordance: the learner can object, but the system cannot
apologise. In a system whose headline user outcome is "stop telling people
false things about their own minds" (see `harmful_write_rate`, §3 B5), silent
retraction is the failure mode that undoes the win.

The machinery already exists — `learner_review_feed` carries recalibration
entries ("estimates recomputed, your evidence unchanged") on projection-version
change. This is one more entry kind, emitted when a belief that was **surfaced
to the learner** reaches a demoted/retired/contradicted status:

- name what was previously claimed, in the words the learner was shown;
- say it has been withdrawn and why (contradicted by trace / superseded /
  adjudicated / retired as misdiagnosed);
- never quietly re-state it as a weaker belief instead.

Scope guard: only beliefs the learner actually saw. Retiring an internal
provisional hypothesis nobody was shown is housekeeping, not a correction, and
narrating it would be noise. Track "was surfaced" explicitly rather than
inferring it.

Cost is one feed entry kind and a `surfaced_to_learner` flag. It belongs in
Phase A because the flag is capture-now data (standing constraint 6) — you
cannot reconstruct after the fact which claims a learner was actually shown.

## 3. Phase B — the measurement substrate

Phase C cannot start without this. You cannot A/B a prompt change against a
metric that does not exist, and human adjudication alone accrues at a handful
of cases per session in a single-learner vault.

### B1. Planted-misconception eval harness

`services/diagnostic_gate.py` already simulates a planted student (answering
misconception-consistently) and a clean student, grades both **in memory** so
it cannot pollute learner state, and turns fire-counts into Beta posteriors
over sensitivity/specificity that gate acceptance of generated diagnostics.
The safety property, the machinery, and the discipline all exist.

Extend that pattern from *gating generated diagnostics* to *scoring the
diagnostician*:

- Generate traces from known implanted causes across the v1 §12 regression
  shapes (genuine facet failure; notation typo over valid reasoning; missing
  step; alternate valid path; correct answer from invalid reasoning;
  unparseable notation).
- Run the full live diagnostic path **blind** to the implanted cause.
- Score recovery of: first-divergence anchor, cause statement equivalence
  (adjudicated or repair-class-matched), and selected repair class.

**The eval set must include abstention cases** — planted errors that no facet
in the vocabulary can express, of which the motivating exhibit is one. Without
them, every scored improvement selects toward over-filling, which is the
disease v1 exists to cure. Abstention precision and recall are first-class
scores here, not footnotes.

### B2. Persona realism gate (new — v1 does not have this)

v1 §8 has role-adherence checks (the persona must not copy the misconception
statement into its answer, must not exceed the specified epistemic state).
Those stop the persona from cheating. They do not establish that the persona
resembles a learner.

Add a blinded matcher over persona traces and real vault traces. **If the
matcher can separate them, the personas are not valid test cases** and the
harness is measuring performance on a distribution that does not exist. This
is cheap — you already have a corpus of real attempts — and it is what makes
every number in B1 mean anything.

### B3. Cross-model separation

Generate persona traces with one model, diagnose with another. If the same
family does both, cycle-consistency can succeed for the wrong reason: the
generator leaves hypothesis-flavoured tells that a real learner would never
produce, and measured diagnostic accuracy inflates. `diagnostic_gate`'s
deterministic path sidesteps this (equality against a keyed answer); free-
response personas used for diagnostic eval do not.

### B4. Two ground truths, and their agreement rate

- **Planted (B1):** synthetic ground truth, arbitrary volume, available today.
- **Adjudicated (A4):** real ground truth, low volume, accrues slowly.

Report **agreement between the two on the overlap** as a first-class metric.
It is the only thing that licenses using the synthetic set to make decisions.
A drop in agreement means the personas have drifted from real learner
behaviour and the synthetic numbers stop counting until B2 is re-run.

### B5. The scoreboard

Frozen before Phase C begins:

```text
problems_to_cold_success              # PRIMARY. learner minutes to cold success
                                      # as its companion. v1 §12 lists these
                                      # first; they are the only metrics
                                      # denominated in the learner's actual
                                      # experience rather than in the model's
                                      # accuracy against labels.
harmful_write_rate                    # wrong-facet damage; target ~0. Not
                                      # hygiene — this is the headline user
                                      # outcome of P0-P2. Being told something
                                      # false about your own mind, with
                                      # confidence, is worse than silence.
first_divergence_anchor_accuracy      # vs adjudication and vs planted cause
repair_class_match_rate
abstention_precision / abstention_recall
probe_action_change_rate
tokens_per_resolved_diagnostic_episode
planted_vs_adjudicated_agreement

# Certification and instrument efficiency (spec_measurement_efficiency_v1 §5.7,
# added before this freeze, not after). The first is ordered ahead of the rest
# for the same reason problems_to_cold_success leads the block above:
# optimizing time-to-certification without measuring false certification is
# lowering the bar with extra steps.
false_certification_rate              # certified, then failed a delayed cold
                                      # probe. The alpha actually being run at,
                                      # and the only number that licenses any
                                      # speed claim. Ground truth is one
                                      # held-out-surface item per certified LO
                                      # at +2-3 weeks -- wanted anyway for
                                      # retention, and in a single-learner vault
                                      # the only external validity check there is
questions_to_certification            # the thing to minimize. Meaningless alone
certification_regret                  # questions served after the point at which
                                      # the evidence already supported certifying
cells_cleared_per_question            # instrument efficiency, per §0 of that doc
measurement_rank                      # independent dimensions the item pool can
                                      # actually resolve, vs facets declared
```

The first two are ordered deliberately. Diagnostic accuracy and learner outcome
correlate but do not track: a system can raise anchor accuracy while becoming
slower and more interrogative, and every remaining metric on this list would
report success. `problems_to_cold_success` is the only one that fails when the
system gets more accurate *and* more annoying.

**`tokens_per_resolved_diagnostic_episode` has no producer today.** v1 §11
schedules the `agent_runs` token/latency/cache columns under P3. C3 multiplies
diagnosis cost by k and its revert criterion is stated in exactly this metric —
so that column set must land in Phase A or B, or C3 ships with an unmeasurable
revert criterion. That is the same defect shape as "first-divergence accuracy
vs adjudication" being listed in v1 §12 with nothing producing it.

## 4. Phase C — the augmentation ladder

Each rung states a hypothesis and a revert criterion. Ship in order; C1 and C3
are prompt-and-sampling changes with no new plumbing, C2 and C4 add
integration surface.

**All four rungs below are diagnosis-side.** They improve how well the system
reads a trace; none of them changes what the trace contains. The authoring rungs
that do — conjunctive items with authored supporting targets, laddered stems,
error-hunts, contrast pairs, per-item discrimination profiles, opportunistic trace
evidence — are Part I of `spec_measurement_efficiency_v1.md` and ship under this
same discipline: a stated hypothesis, a stated revert criterion, and no rung kept
on judgement. Two of them interlock with this ladder specifically: its A5
(discrimination profiles) supplies the authored planted ground truth §3 B1
currently has no producer for, and its A8 (clarification on hedged or abstained
criteria) makes abstention cheap, which is the direct lever on the abstention
recall C1 is watched for collapsing.

### C1. Repair-first prompt ordering

v1 §5.1 established that field order is causal under autoregressive decoding
and put `diagnosis_md` first (`codex/client.py:1381`). Extend the same logic:
emit the **repaired trace before the causal story**, then generate candidate
causes as explanations of the edit.

The repair is checkable — CAS-verify the repaired answer, string-match the
preserved prefix against the learner's work. The cause is not. Ordering
generation so the verifiable artifact comes first puts the thing you actually
want under the most verification pressure, and makes the causal narrative
answer to it rather than the reverse.

- *Hypothesis:* repair-class match rate rises; anchor accuracy rises or holds.
- *Revert if:* abstention recall collapses (the model rationalizes a cause to
  fit an edit it has already committed to).
- Cost: prompt reorder + `GRADING_PROMPT_VERSION` bump.

### C2. Verifier as instrument, not only adjudicator

v1 §6.5's adapter has typed outcomes (`verified | contradicted | unsupported |
parse_failed | assumption_missing`) and adjudicates *after* diagnosis. Expose
it to the diagnostician during diagnosis. On the motivating exhibit, squaring
`±√(1/2)+√(1/2)i` localizes the dropped branch deterministically — the
harness knows the answer the prose is reaching for.

- *Hypothesis:* anchor accuracy rises materially on CAS-verifiable domains.
- *Revert if:* the model anchors on whichever subproblem happens to be
  parseable and abstention precision falls.
- Adapter outcomes remain typed; `parse_failed`/`unsupported` confer nothing,
  exactly as in v1 §2.

### C3. k-sample agreement as the support score and the cause set

Run diagnosis k times independently; score agreement on (first-divergence
anchor, repair class).

- Agreement becomes `support_score` — a support score sourced from something
  real, in a spec that already reserves the vocabulary.
- **Disagreement becomes the unresolved-cause factor.** This is the better
  fix for v1 §5.3's own caution: cause-set discrimination probes are gated
  today because P0-era candidate causes are the criterion's authored targets,
  "the vocabulary under indictment." A sample-disagreement cause set contains
  hypotheses a model actually held, which is what makes spending learner
  effort on discrimination defensible.

- *Hypothesis:* agreement correlates with adjudicated correctness; probe
  action-change rate rises against authored-target cause sets.
- *Revert if:* tokens per resolved episode rise without a corresponding rise
  in action-change rate.
- Cost: k× on the diagnosis path. Measure it; the metric already exists.

### C4. Learner history in the diagnosis context

Supply the last N traces on the same facet and surface family. Turns a
single-attempt provisional belief into a founded one and gives the §5.6
trace-consistency veto more than one attempt to check against.

- *Hypothesis:* recurrence detection improves; promotion condition (b)
  (fingerprint-distinct recurrence) fires on genuine recurrence sooner.
- *Revert if:* the planted control shows anchoring — **the eval must include a
  learner whose cause changed mid-history.** A model that re-diagnoses the
  prior belief regardless of the current trace is worse than one with no
  history at all.
- Independent-group counting for "fingerprint-distinct" uses the existing
  soft-kinship implementation (§8), not a parallel notion.

## 5. Phase D — the vocabulary repair loop

Pulled forward from v1 §9. It needs only abstentions and repair classes, both
of which exist by P1, and it is the system's only mechanism for learning its
own ontology from data.

**Capture moved to A5.** The note store is a Phase A item — it cannot be
backfilled, and it has no dependency that justified holding it here. What
remains in Phase D is everything that needs accumulated volume to be meaningful:

1. **Cluster by repair equivalence**, not by text similarity. Two abstentions
   belong together when the same minimal repair fixes both.
2. **Mint criterion:** a cluster earns a facet *proposal* only when it
   predicts a distinct repair or a distinct measurement need — the same test
   as A2, applied to vocabulary rather than mechanism.
3. **Review, never auto-mint.** v1's non-goal stands: no on-the-fly minting of
   canonical facets. This is a batch review surface, off the hot path, and the
   human decision is what creates the facet.

Abstention rate is the system's own measurement of vocabulary inadequacy.
Reading it continuously — rather than at P4, behind a learned repair policy —
is the highest-leverage learning signal available, and the motivating exhibit
is exactly a case the vocabulary could not name (no facet for branch
retention; none for sign-case analysis or solution enumeration).

## 6. Phase E — what stays parked, and what would unpark it

**Simulation as a likelihood channel.** P(simulated response | prompted
hypothesis, simulator) is not P(real response | learner hypothesis); v1's
three-noise-channel separation is right and this arm stays shadow-only.
*Trigger:* planted-recovery rate stable across B1 refreshes, B4 agreement
holding, and enough real probe outcomes for prospective comparison. Ordinal
uses (ranking which hypothesis to probe first) remain permitted throughout, as
v1 §8 already allows.

**Learning-pattern discovery.** Relocated (§7). *Trigger:* independent-group
count past ~10³ — realistically meaning pooled multi-learner data — **and**
interpretable slice discovery exhausted with residual structure unexplained.

**Learned repair policy (v1 §9).** Unchanged: needs cold outcomes. Phase A's
`selection_basis` field and Phase B's scoreboard are what make its training
records honest when it arrives.

## 7. Relocation: learning-pattern discovery

v1 §8.5 plus the pattern threads through §9–§13 is roughly a third of that
document, specifying HDBSCAN grids, PLSCAN and Bayesian-mixture comparators,
BOCPD, and a ten-template descriptive vocabulary — for a single-learner vault
whose own gates (independent groups, chronological validation, blocked
bootstrap) cannot fire for a long time.

Move it to `spec_learning_patterns_v1.md` unchanged, with two edits:

1. **Add availability/missingness pattern to the artifact-audit list** (v1
   §12 audits algorithm, policy, grader, generator prompt, source, template,
   session position, and interface versions — not which outcomes happened to
   be scheduled). With cold retention and transfer selectively observed,
   profiles sharing a missingness pattern will be nearest neighbours *because*
   of the missingness. It is the artifact most likely to fire and it is not on
   the list.
2. **Write the §6 trigger condition into its status header**, so it reads as a
   deferred option rather than a standing program.

Keep interpretable slice discovery (its Stage A) as the live path when the
time comes: a supervised, enumerable search over conjunctions with computable
multiple-testing control is honest at small n, because its evidence units are
attempts rather than derived profile rows and its hypothesis space has a null.
When it runs, prefer **LLM proposes the conjunctions, harness tests them with
FDR control and chronological validation** — the v1 §2 producer/confirmer
split applied to pattern discovery, and it skips density estimation entirely.

## 8. One implementation of independent-group counting

`services/progression.py:208-239` already treats a tight soft-kinship cluster
as exactly one independent group, capping effective mass. v1 §5.6's promotion
condition (b) needs precisely this, C4's recurrence check needs it, and any
future pattern work needs it. Call that implementation; do not grow "item
fingerprint family" as a parallel notion. Six errors on six near-clones of one
item are one observation, everywhere, from one code path.

## 9. Migration & legacy vaults

An mvp0.8 vault **migrates; it is never reingested.**

- **Vault content:** untouched. No migration in 115–123 touches note parsing.
- **Schema:** additive. `CREATE TABLE` / `CREATE INDEX` / `ALTER TABLE ADD
  COLUMN`, with two deliberate exceptions — 115 demotes `first_error_trace`
  promotions in place (rows kept for audit; 116 records the authoritative
  `demoted` disposition, distinguished from learner resolution), and 122 drops
  `causal_activity_classifications` after `INSERT`ing into its replacement.
- **Derived state:** `learnloop rebuild-derived-state` (`cli.py:4178`) →
  `replay_learning_object` treats `practice_attempts` plus non-superseded
  `grading_evidence` as the raw log and re-runs the live computation path with
  no provider calls (`services/replay.py:52-58`). **The passed-facet write
  barrier fires on replay** — it lives in `services/grading.py:273-444` and is
  invoked from the attempt path (`services/attempts.py:1589-1600`) — so
  wrong-facet damage clears at rebuild even where the stored attribution still
  names the facet.
- **What does not self-heal:** replay never re-normalizes
  (`services/replay.py:85`). The old validator's criterion→facet expansion was
  applied at grading time and persisted, so stored attributions still claim
  facets the grader never asserted; the firewall suppresses the damage only
  where those facets' criteria all passed. The P0b fields (`diagnosis_md`,
  `resolution_status`, `first_divergence`, `candidate_causes`,
  `postdictive_claims`) do not exist on legacy attempts and cannot be derived
  deterministically. Historical attempts therefore open no unresolved-cause
  factors.

  **Correction (measured, not predicted):** the claim that they "produce no
  causal hypotheses" is **false**. A replay of `fixtures/linear_algebra`
  (3 LOs / 22 attempts, mvp-0.8) mints exactly one — on the motivating exhibit
  attempt `01KY64FZE7ZVJ79YJFWAYZH53Q` — via the `misconception_statement`
  fallback in `_event_candidate_causes`, which derives a cause from a legacy
  error event without needing any P0b field. It lands as
  `cause_scope=learner_state`, `status=candidate`, with
  `repair_class_basis=unresolved` / `no_matching_repair_target`.

  That is the designed behaviour working, not a leak: the statement it
  recovers is the *correct* diagnosis of the exhibit, it lands as a candidate
  rather than a durable belief, its repair mapping is typed-unresolved rather
  than fabricated, and facet state is byte-identical across the rebuild. But
  the sequencing claim above must not be relied on as "legacy data is inert" —
  legacy misconception statements are a live input to the P1 lane.
- **The repair path exists and costs tokens:** `services/regrade.py:264-280`
  re-grades and calls `replay_learning_object` with
  `error_attribution_overrides` from the new validated output.

Recommended sequence on a live vault:

1. Back up `state.sqlite`. `reset_learning_object_derived_state` is
   destructive to derived state by design.
2. Migrate, then `rebuild-derived-state` across all learning objects. Read the
   P0 attribution telemetry (`cli.py:5313`) before and after; the firewall
   trigger count measures how much wrong-facet damage was present.
3. **Selective regrade, not bulk.** Target attempts that still steer
   behaviour: those carrying a misconception, an open unresolved factor, or a
   scheduled repair. Bulk-regrading full history will not pay for itself.
4. **Lazy contract re-authoring.** `measurement_status` and `trace_contract`
   are null on legacy items; a null trace contract is the designed fallback
   (whole-answer anchors, backtracking-depth terms skipped), not breakage. But
   A1's deterministic rank keys are unavailable on those items, so re-author
   unattempted items on demand and give attempted items a new version when
   they are next served.

## 10. Validation

Phase A adds to v1 §12's regression matrix:

- A repair candidate naming a checkpoint outside every recipe is rejected with
  `unverifiable_checkpoint_claim`, not silently depth-`None`.
- Two candidates whose latent-claim counts differ by 1 and whose backtracking
  depths differ are ordered by depth.
- An item with `no_reliable_decomposition` selects successfully and records
  `selection_basis: model_reported`.
- Two mechanisms with distinct operation strings and one shared repair class
  merge; two with one operation string and divergent repair classes split.
- A divergent-repair hold surfaces as `needs_disambiguation`, not
  `invalid_request`.
- An abstention writes a missing-vocabulary note carrying the trace, criterion,
  abstention reason, selected repair class, item context, and the prompt/model
  version set (A5) — and a §5.8 facet-abstaining variant writes one too.
- A retired/demoted belief about the learner produces a learner-visible
  correction entry, not a silent state change (A6).

Phase B/C validation is the scoreboard (§3 B5), reported per prompt version
and per model, with abstention and fill rates on both tails as v1 standing
constraint 2 requires. A Phase C rung that does not move its stated metric on
the planted set **and** hold agreement with adjudication is reverted, not
kept on judgement.

## 11. Non-goals

- No auto-minting of canonical facets. Phase D proposes; humans mint.
- No persona output as learner evidence — ever. Personas score the system;
  they never write mastery, error events, or attempts. `diagnostic_gate`'s
  in-memory grading is the invariant, not a convenience.
- No synthetic likelihood or posterior authority before the §6 trigger.
- No bulk regrade of history.
- No density clustering, no learner types, no learning styles. Relocated with
  §7 and gated behind its own trigger.
- No new enum without an abstention arm and a two-tailed fill-rate watch.
- No relaxation of any v1 firewall. They are safety invariants and they
  survive the bitter-lesson handoff; a learned repair policy inherits them
  unchanged.
