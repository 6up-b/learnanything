# Measurement efficiency — instruments, inference, and fast certification (v1)

**Status:** proposed direction. Successor to `spec_diagnostic_augmentation_v1.md`
for the half of the program that document does not cover: the **instruments** the
diagnostician reads, the **inference** that makes measurement unnecessary, and the
**decision rule** that ends a measurement episode.

**Relationship to the existing specs.** `spec_causal_attribution_v1.md` remains
the authority on epistemics — the authority ladder (§2), causal-state ownership
(§3), the deterministic firewalls, promotion discipline. `spec_diagnostic_
augmentation_v1.md` remains the authority on measuring and improving *diagnostic
quality*. Nothing here weakens either. This document takes over:

| Prior section | Disposition here |
|---|---|
| causal §1 principle 8 (machine-side uncertainty) | **Sharpened, not weakened.** Machine-resident vs learner-resident uncertainty are different things and only the first is forbidden to spend learner effort. Amendment applied in that document; rationale in §3.A8. |
| causal §5.1 (grading schema, candidate causes) + `RubricFatalError.misconception_id` | **Extended** by A5: items author a full per-hypothesis discrimination profile, not a single fatal-error link. Profiles are a prior over causes the diagnostician may reject, never a constraint on it. |
| augmentation §4 Phase C | **Extended.** C1–C4 there are all diagnosis-side (prompt, verifier, k-sampling, history). The authoring rungs are Part I here and ship under the same hypothesis/revert discipline. |
| augmentation §3 B5 (scoreboard) | **Extended** with three certification metrics (§5.7). B5 is frozen before *its* Phase C; these are added before that freeze, not after. |
| augmentation §5 Phase D (vocabulary repair) | **Split.** Its review-and-mint loop is unchanged. The *gate* moves upstream to ingest (D2), because a facet minted at ingest is a measurement obligation from that moment on. |

---

## 0. Thesis

The number of questions a learner must answer before the system can say anything
is, to a first approximation:

```
questions  ≈  (cells to clear)  /  (cells cleared per question)
```

Every current design decision drives the denominator toward 1 and lets the
numerator grow without bound — and one of them makes the numerator grow *as a
direct consequence of authoring*, so the learner becomes less certified when the
system generates an item and they do nothing (§2 F6).

P0–P2 made diagnosis honest. Honest diagnosis of an inefficient instrument is
still an inefficient measurement. This document:

1. **raises cells-per-question** — the instruments (Part I);
2. **removes cells that never needed measuring** — inference and vocabulary
   (Parts II and IV);
3. **replaces coverage with a decision rule** — certification as a bounded search
   for a counterexample rather than a checklist (Part III);
4. **adds evidence channels that cost the learner nothing** (Part V).

The division of labour from the prior specs is unchanged and carries here: **the
LLM proposes; the harness verifies, bounds, and decides.** Applied to instruments
this reads: the model authors the item and reports what it saw in the trace; the
harness decides what that observation is worth, at which capability, and whether
it may certify anything.

## 1. Standing constraints

Inherits all six standing constraints of `spec_diagnostic_augmentation_v1.md` §1
(which inherit the causal spec's two). Adds:

7. **No instrument ships that cannot be shown to discriminate.** Every new
   instrument class in Part I passes the authoring-time planted-persona gate
   (§3.0) before it reaches a learner. An item that a facet-holder and a
   misconception-holder answer identically measures nothing, however good it
   looks.
8. **An instrument's evidence is bounded by the capability it actually
   observes.** A spoken one-line justification is `schema_interpretation`; it is
   never allowed to certify `procedure_execution` because it was convenient. This
   is constraint 4 of the augmentation spec (deterministic outranks
   model-reported) applied to observation contracts.
9. **Inference may fill a cell; only evidence may certify one — with one
   bounded exception.** Dominance and prerequisite entailment (Part II) move
   mass and predictions freely. They reach certification only through the
   discounted substitution rule of §5.3, which names itself on the certificate.
   A certificate that cannot say what was measured and what was inferred is not
   a certificate.
10. **The question budget is a learner-facing cost.** Every question competes
    with learning time. An instrument or channel that raises information per
    question but raises annoyance faster is a regression, and
    `problems_to_cold_success` is the metric that catches it (augmentation §3 B5,
    which orders it first for exactly this reason).
11. **A distinction no instrument separates and no repair distinguishes is a
    synonym.** This is augmentation §2 A2's criterion, applied one level up to
    the facet vocabulary itself (Part IV).

---

## 2. Verified findings

Measured against the working tree, not predicted. These are the facts the rest of
the document acts on.

**F1. The unit of state is the (facet × capability) cell, not the facet.**
`capability_grid.py` builds them; `exam_pool._item_components` (`:343`) records
that an item "observes its facets at the capability it was authored at";
readiness conjoins them.

**F2. A generated practice item can only ever fill one column.**
`RubricCriterionPayload` (`codex/schemas.py:206`) has **no `targets` field**, so
generation cannot author `CriterionTarget{facet, capability, role}`.
`compile_criterion_targets` (`capability_mapping.py:85`) therefore falls back to
every criterion → `primary` at the item's single declared `capability`. The
`supporting` role (`ROLE_WEIGHTS` 1.0 / 0.3) and the `embedded` credit channel
the ledger already honours are structurally unreachable from the
practice-expansion path. The **synthesis** path can author them
(`SynthCriterion.targets`, `codex/schemas.py:1274`). The asymmetry appears
accidental.

**F3. Authoring is instructed to spread, not to conjoin.**
`_BLUEPRINT_SPREAD_RULE` (`practice_generation.py:1320`) pushes one blueprint
component per item. Correct against surface-permutation; it also pins
cells-per-item near 1 by policy.

**F4. `required_facets` is derived from the items themselves.**
`facet_diagnostics.py:43` unions the `evidence_facets` of *active authored items*.
The coverage denominator grows every time the system authors.

**F5. Nothing propagates.** `Demonstrated` is strictly per-cell; only `Ready` is
capability-agnostic and tiles a facet's row from the pooled mean
(`capability_grid.py` docstring, `ready_for`). Unassisted success at
`coordination` credits nothing at `retrieval` for the same facet.

**F6. Authoring an item lowers the learner's certification confidence.** The
chain: `covered_required_fraction` (`facet_diagnostics.py:150`) is the fraction of
F4's required facets whose aggregate mass exceeds
`min_facet_evidence_mass` (0.50, `config.py:1153`) → it floors mastery variance
between 0.5 and 0.0 (`variance_floor`, `:194`; `config.py:1154-1155`) → applied on
**every attempt** (`attempts.py:1774` computes it, `:1827` applies it). Generate an
item, and the LCB lane immediately becomes less confident about a learner who has
done nothing. The floor is right in principle; the denominator is an artifact of
authoring history rather than an obligation.

**F7. Certification has no probabilistic path at all.** `lo_certification`
(`goal_certification.py:135`) is a boolean AND: for some blueprint, every hard
component demonstrated at its exact capability, plus direct evidence on the
integration facet. No partial credit, no inference, no probability. There is no
route from overwhelming evidence to certified — only from *touched every cell* to
certified. Two systems that do not talk: a probabilistic one (mastery
mean/variance, beta facet recall, FSRS projection, `_attempts_to_certify`
`goal_projection.py:334`) with no certification decision rule attached, and a
boolean one that cannot be fast by construction.

**F8. Facet identity is lexical everywhere it is checked.** Ingest mints one
facet per extracted claim, id `facet_<slug>_<ulid8>` when the model supplies none,
landing at `status: "reviewed"` (`source_set_synthesis.py:596`). Existing facet
ids *are* passed as context (`:265`), but nothing structurally prevents a
near-duplicate. The only dedup anywhere is MinHash Jaccard ≥ 0.6
(`facet_candidates.py`, explicitly "review-only, never merges") and token Jaccard
(`facet_doctor.near_duplicate_facet_review`). This is precisely the defect
augmentation §2 A2 identifies for the mechanism taxonomy — keying on the model's
lexical habits — unaddressed one level up, in the vocabulary that generates every
cell. The merge substrate, by contrast, already exists and is cheap:
`facet_aliases` plus transitive `facet_merges`, resolved in
`facet_state_reader.py:62`.

**F9. The resulting arithmetic.** An LO with ~8 facets whose blueprints require
~2.5 capabilities each is ~20 cells. At ~2 cells per item (F2, F3) and ~2
independent items per cell (F6's mass threshold under kinship discounting,
augmentation §8), that is **~20 authored items per LO** before anything reads as
demonstrated. This is arithmetic, not a defect report. Parts I–IV attack each
term.

---

## 3. Part I — Instruments

Cells-per-question is an authoring decision. Every item here is a *class* of
instrument; none of them is a new subsystem.

### 3.0 The shared gate: authoring-time planted-persona discrimination

Ships **before** A3, A4, A5 — they all depend on it.

`services/diagnostic_gate.py` already simulates a planted student answering
misconception-consistently and a clean student, grades both **in memory** so
learner state cannot be polluted, and turns fire-counts into Beta posteriors over
sensitivity/specificity. Reuse it as an authoring gate:

- A persona **holding** the target facet must pass the item.
- A persona holding the target misconception must **fail** it.
- For a contrast pair (A4), the misconception-holder must fail **exactly one**
  member.
- If the personas do not separate, the item does not ship.

Zero learner cost, no state writes, no new machinery. This is
`identifiability.analyze_identifiability`'s question asked at authoring time
instead of discovered after twenty attempts, and it is the enforcement mechanism
for standing constraint 7. The same harness is reused by D2 at ingest.

Persona realism inherits augmentation §3 B2's blinded matcher: if a matcher can
separate persona traces from real vault traces, the gate is measuring a
distribution that does not exist and its verdicts do not count.

### A1. Conjunctive items with authored supporting targets

**The change.**

- Add `targets: list[CriterionTargetPayload]` to `RubricCriterionPayload`
  (`codex/schemas.py:206`), mirroring `SynthCriterionTarget` (`:1261`) —
  `{facet, capability, role}` with the existing closed vocabularies. This closes
  F2's asymmetry; the vault model (`CriterionTarget`) and the compile path
  (`compile_criterion_targets`) already accept authored targets and prefer them
  verbatim.
- Invert `_BLUEPRINT_SPREAD_RULE` (`practice_generation.py:1320`): **cover the
  blueprint in as few honest items as possible.** Prefer one task that genuinely
  requires k components over k tasks requiring one each. The spread rule survives
  as the fallback for components no single task can honestly conjoin, and the
  anti-clone clauses (no shared `surface_family` within a batch, vary
  representation) survive unchanged — they were never the problem.
- A criterion's `primary` target is the step it owns; its `supporting` targets are
  the facets that step *consumes*.

**The semantics, and why they are safe.** A pass credits every cell — primary at
1.0, supporting at 0.3 as embedded. A failure localizes through first-divergence
and only the diverged facet takes the negative. That asymmetry is epistemically
correct: success on a conjunction is strong evidence for every conjunct; failure
is weak evidence about any particular one. **The passed-facet write barrier
(causal §1 principle 5, `services/grading.py:273-444`) is exactly what makes this
safe** — it is the firewall that prevents failure from smearing across conjuncts.
A1 is unlocked by P0–P2, not in tension with it.

**The new exposure is positive smearing.** The firewall protects the negative
direction only. Crediting a facet the learner never actually exercised is a
harmful write in the other sign, and it is *more* dangerous than the negative
kind because nothing contests it — a learner does not object to being told they
know something. Three guards, all required:

1. **Supporting credit requires trace evidence.** A supporting target confers
   credit only where the graded trace shows the facet exercised (the A6 channel
   supplies this observation). Absent that, the target is recorded and confers
   nothing — a typed `unexercised_supporting_target`, not silence.
2. **A cap on embedded share.** No cell may take more than a configured fraction
   of its total mass from embedded evidence. A cell whose entire history is
   supporting credit is not demonstrated; it is inferred, and Part II already has
   an honest label for that.
3. **Certification unaffected.** Embedded credit feeds mass and Ready. Whether it
   may certify is governed by §5.3, never by A1.

- *Hypothesis:* `cells_cleared_per_question` rises materially; questions to first
  certification falls; `harmful_write_rate` holds.
- *Revert if:* `harmful_write_rate` rises at all, or the delayed cold probe
  (§5.7) shows certified cells failing at a higher rate than pre-A1 cohorts.
  Positive smearing shows up there and almost nowhere else.

### A2. Laddered stems — one stimulus, parts climbing the capability ladder

One stimulus; parts that walk the same facet up the capability vocabulary: state
it (`retrieval`) → which theorem applies (`method_selection`) → execute
(`procedure_execution`) → the edge case where coordination is the difficulty
(`coordination`). One context-loading cost, four columns.

The dominant cost in any assessment is loading the problem into the learner's
head. Laddered stems amortize it, and they are the only instrument that fills a
*row* of the capability grid rather than a cell.

**The kinship rule this needs.** `EvidenceFingerprint.shared_stimulus_id` already
exists, and the soft-kinship implementation (augmentation §8,
`progression.py:208-239`) would otherwise correctly collapse the parts into one
independent group. The honest treatment: parts of one stem are **correlated
within a cell** (two `procedure_execution` parts on one stimulus are close to one
observation) and **independent across columns** (retrieval and coordination on
one stimulus are genuinely different measurements). One rule, in the existing
implementation, per augmentation §8's "one code path" requirement — not a
parallel notion of kinship.

- *Hypothesis:* capability-grid rows fill without an increase in items authored;
  `questions_to_certification` falls on LOs whose blueprints span ≥3 capabilities.
- *Revert if:* cross-column outcomes on one stem correlate as tightly as
  within-column ones, i.e. the independence claim is empirically false. Measure
  this before trusting it; it is a claim about learners, not about code.

### A3. Error-hunt items

Present a fully worked solution containing planted errors; the learner finds and
**repairs** them. Every facet the solution touches yields evidence; misses
localize for free, because the planting location is known. Cost is a fraction of a
full derivation.

**Non-triviality is the whole design.** An error-hunt item that any careful reader
catches measures carefulness, which is not a facet anyone wants:

- **The planted error must be invisible to a holder of the misconception.** That
  is the criterion, and §3.0 enforces it: the misconception-persona must *not*
  find the error.
- **Plant from the registry, never freehand** — from the misconception registry
  and the facet payload's `error_signatures` (ingest already emits these; see
  F8/D2). A freehand error is an untyped instrument.
- **Require the repair, not the flag.** Flagging is recognition; repairing is
  construction. This is what keeps the instrument on the right side of the
  no-recognition-items gate rather than smuggling multiple choice back in under a
  new name.
- **Do not declare the error count, and rotate in clean solutions.** A prompt
  saying "find the 2 errors" is a scavenger hunt. A rotation that sometimes
  presents *correct* work is strictly more informative: a learner who "finds" an
  error in a correct solution has just handed you a misconception directly, and
  the rotation kills the "there is always an error" strategy.

- *Hypothesis:* highest `cells_cleared_per_minute` of any instrument class;
  false-positive detections on clean solutions surface misconceptions that
  constructed items miss.
- *Revert if:* the planted-persona gate passes items that real learners solve by
  proofreading — detectable as error-hunt outcomes uncorrelated with the same
  learner's constructed-response outcomes on the same facet.

### A4. Contrast pairs

Two prompts differing in exactly one requirement. The *difference* in outcome
identifies the facet with the learner's general ability held constant, which is
why it buys more per minute than two independent items — it removes the nuisance
parameter instead of averaging over it.

Commissioned, not merely permitted: `identifiability.analyze_identifiability`
already finds facet pairs no instrument separates, and those findings become
contrast-pair authoring requests.

**Non-triviality constraints, all gates rather than guidance:**

- **Both members must independently sit in the target difficulty band.** Not "one
  hard, one easy." Enforce with the existing `_success_band_difficulty` inversion
  in `practice_generation`. A pair where one member is trivial measures nothing on
  that member and wastes the contrast.
- **The manipulation must change the *structure* of the correct answer** — does a
  precondition hold, is the theorem applicable — never merely its values.
  Different numbers is a clone, and kinship will correctly refuse to count it
  twice anyway.
- **Do not serve them adjacent unless the surfaces differ enough that the
  manipulation is not salient.** A visible contrast measures "spots the
  manipulation," a facet nobody has.
- The pair carries `contrast_of: <item_id>` and `differing_component:
  {facet, capability}` so the analysis is structural rather than inferred.

- *Hypothesis:* facet-level identifiability findings close; per-facet posterior
  variance falls faster per question than on matched independent items.
- *Revert if:* within-pair outcome differences are dominated by order effects —
  check by randomizing which member is served first.

### A5. Discrimination profiles on items

**Into the causal pipeline**, extending the single authored link an item can
carry today from a fatal error to the misconception it catches
(`RubricFatalError.misconception_id`, `vault/models.py`).

Today a wrong answer mostly carries the information "this criterion failed." The
*shape* of the wrong answer is where the diagnostic information actually lives,
and it is discarded. An item authors, per plausible candidate hypothesis, what a
holder of that hypothesis visibly produces — the same content the planted personas
consume, written down once and reused:

- by §3.0 as the authoring gate's oracle;
- by the diagnostician at grading time, as candidate structure the trace can be
  matched against (this is a *prior over causes*, never a posterior — causal §1
  principle 4);
- by A4 to commission the pair that separates two profiles;
- by the augmentation spec's Phase B eval harness as planted ground truth (§3 B1
  requires exactly this and currently has no producer for authored items).

**The discipline that keeps this from becoming the disease it treats.** Causal
§0's root cause 8 is precisely an *authoring* failure — the contract demanded a
nonempty facet map per criterion in a vocabulary that had no name for what the
learner actually did, so authoring manufactured false structure at mint time. A
discrimination profile is also authored structure about causes. It is the same
shape of risk, and if a profile is allowed to *constrain* diagnosis rather than
inform it, this document reintroduces the exhibit. So: a profile is a candidate set
the diagnostician may match against and must be free to reject, with
`no_profile_applies` a first-class outcome carrying the same weight as any named
match. Profile match rates are watched on both tails per standing constraint 2 —
a profile that matches ~100% of failures is as suspect as one that never matches.

- *Hypothesis:* first-divergence anchor accuracy rises on items carrying profiles;
  abstention *precision* rises (the model has legitimate candidates to reject
  rather than a blank space to fill).
- *Revert if:* `no_profile_applies` rate collapses toward zero — that is the
  model matching the nearest authored profile rather than reading the trace, and
  it is the original disease with better tooling.

### A6. Opportunistic trace evidence

The grader already reads the whole natural-language trace. Let it report facets it
saw **exercised** beyond the item's declared set.

This is the most bitter-lesson-aligned item in the document: the model observes,
the harness decides what the observation is worth. It also multiplies every other
instrument — under A1, it is what discharges the "supporting credit requires trace
evidence" guard.

**Bounds, all three required:**

- **Positive only.** Opportunistic evidence may credit a facet; it may never
  indict one. Indicting a facet the item did not intend to measure is exactly the
  smearing causal §1 principle 5 forbids, and there is no criterion to appeal to.
- **`supporting` at most**, so it lands as embedded credit under the A1 cap.
- **Never certification-eligible on its own** (§5.3).

**Explanation elicitation — the annoyance boundary.** More explanation is more
evidence, so there is a standing temptation to demand it everywhere. Do not.

- **Elicit where the answer underdetermines the reasoning, nowhere else.** The
  discriminator already exists: `trace_contract`. A worked derivation is
  self-documenting — the steps *are* the explanation, and demanding prose beside
  them is pure friction that produces filler and pollutes the trace. The genuinely
  ambiguous cases are: correct answer with skipped steps, a choice among methods,
  an applicability judgment.
- **One line at a decision point, not a paragraph at every step.** "Why this
  method?" is one line and enormously informative. "Explain each algebra step" is
  annoying and tells you nothing.
- **Rewarded, never required.** Volunteered explanation earns evidence, and the
  feedback surface says so ("this also demonstrated 3 facets"). Voluntary and
  visibly rewarded self-selects for learners with something to say; mandatory
  trains people to write filler.
- **A per-session elicitation budget**, so it cannot creep.

- *Hypothesis:* `cells_cleared_per_question` rises with no change to items;
  volunteered-explanation rate rises after the reward is made visible.
- *Revert if:* `problems_to_cold_success` rises (standing constraint 10 — the
  instrument got more informative and the session got worse), or opportunistic
  credit concentrates on a few facets, which indicates the grader is pattern-
  matching the vocabulary rather than reading the work.

### A7. Adjacent-facet questions in context

*(the first of the two tutor channels raised in review)*

After an attempt, ask about a facet that is **undemonstrated but adjacent to the
task just worked**.

The argument is cost structure: the dominant expense in assessment is loading the
problem into the learner's head, and it has just been paid. "You used
independence there — what breaks if these vectors were dependent?" costs twenty
seconds and buys a cell that would otherwise need an authored item, a scheduling
slot, and a fresh context load.

- **Adjacency is structural, not lexical**: same blueprint recipe, one
  prerequisite hop, or same `correlation_group`. Then ranked by EIG over open
  contract cells (§5.4), so it is subject to causal §1 principle 8's "probe only
  when it changes the action" like everything else.
- **It measures at the capability it actually observes** (standing constraint 8):
  a spoken answer is `schema_interpretation` or `method_selection`, never
  `procedure_execution`. It can move a cell from unknown to measured-at-retrieval
  and feed B1's ladder from below; it cannot certify the task. That ceiling is
  what stops the channel becoming a shortcut around real performance.
- **Budget it hard**: at most one or two per attempt, above an EIG threshold,
  suppressed entirely when the learner is struggling or mid-flow. `dont_know` is
  already an attempt type and a "don't know" here is genuinely informative, so the
  skip path costs nothing and is not a failure.
- **Substrate**: this is system→learner, so it is probe-dialogue/teach-back
  shaped (`ProbeDialogueTurn`, `probe_instance_generation`), not `tutor_qa`, which
  is the learner→system direction.

- *Hypothesis:* cells cleared per *session* rises without a rise in
  `problems_to_cold_success`.
- *Revert if:* session abandonment or skip rate rises, or answers to adjacent
  questions predict nothing about later performance on the same cell — which
  would mean the channel measures compliance, not knowledge.

### A8. Clarification questions that resolve grading uncertainty

*(the second tutor channel raised in review — and the one I would ship first)*

When the grader is genuinely unsure what the learner did — ambiguous notation, a
skipped step that is either fluency or a gap, a correct answer possibly reached
by invalid reasoning — ask **one** targeted question and let the answer resolve
the grade retroactively.

**This is not primarily a coverage win.** Three of the six regression shapes in
augmentation §3 B1's eval set (notation typo over valid reasoning; missing step;
correct answer from invalid reasoning) are exactly this uncertainty, and no amount
of machine effort resolves them because *the information is not in the machine's
possession.*

**The epistemic argument for putting it in the causal pipeline.** Right now
abstaining forfeits the measurement entirely, so there is standing pressure on the
grader to fill in a guess — which is the disease P0–P2 exists to cure. If an
abstention can be repaired by one question, honest uncertainty stops costing
anything, and the over-fill incentive drops at its source. A8 is a *reinforcement*
of the abstention discipline, not an addition to it.

**Reconciling with causal §1 principle 8.** That principle says machine-side
uncertainty is resolved with machine effort, never learner effort — and it is
right. But it collapses two different things:

- **Machine-resident uncertainty** — grader flakiness, a missing item contract,
  symbolic correctness the CAS could settle, an unmapped repair class. The
  machine holds everything needed; spending learner effort is a tax on the learner
  for the system's own debt. **Forbidden, unchanged.**
- **Learner-resident uncertainty** — what the learner meant, whether a skipped
  step was fluency or a gap, which of two methods they believed they were using.
  This information exists **only in the learner's head**. No machine effort
  recovers it. The alternatives are to guess (a harmful write) or to discard the
  measurement (a wasted attempt), and asking is strictly better than both.

The principle is amended in `spec_causal_attribution_v1.md` to draw this line
explicitly. The forbidden case stays forbidden; the newly permitted case is
bounded below.

**Bounds.** One question per attempt, only on a criterion the grader has flagged
hedged or abstained with reason — never on a confident grade, which would make it
an interrogation. Requires a `provisional_pending_clarification` grade state and a
resolution path that stamps the clarifying exchange onto the grading evidence, so
replay reproduces the resolved grade rather than re-asking (causal §1 principle 9).
An unanswered clarification times out to the abstention that triggered it, never
to a guess.

- *Hypothesis:* abstention *recall* rises (abstention becomes cheap, so the model
  stops over-filling) while abstention *precision* holds; anchor accuracy rises on
  the three affected regression shapes.
- *Revert if:* clarification rate exceeds a small fraction of attempts — that is
  a grader problem or an item-contract problem masquerading as learner-resident
  uncertainty, and it must be fixed machine-side per the unamended half of
  principle 8.

---

## 4. Part II — Inference

The cheapest question is the one you do not ask because the answer is entailed.

### B1. Capability dominance

Unassisted success at a higher capability is evidence at lower capabilities for
the same facet, at a discount, never the reverse. Solving an integrative
`coordination` task unassisted is strong evidence you can retrieve the definition;
retrieving the definition says nothing about coordination.

The hard version of this already exists for probes:
`probe_targeting.prerequisite_already_demonstrated` (`:112-120`) suppresses
re-establishing a prerequisite with downstream embedded credit. Generalize the
same reasoning from *suppression* to *credit*.

- The ladder is `retrieval < schema_interpretation < procedure_execution <
  method_selection < coordination` for propagation purposes. It is a partial
  order in reality and treating it as total is a simplification — record the
  discount basis so it can be revisited.
- **Assisted attempts propagate nothing.** Hints, scaffolding, primed sources
  break the entailment: the higher-capability performance was not the learner's
  alone. The hint-policy dampening fields already exist.
- Dominance credit is `embedded`, so it falls under A1's cap and §5.3's
  substitution rule automatically. No new authority path.

- *Hypothesis:* cells demonstrated per attempt rises sharply on LOs with
  multi-capability blueprints; `questions_to_certification` falls.
- *Revert if:* learners with dominance-credited lower cells fail those cells when
  probed directly at a higher rate than directly-credited learners. This is
  measurable and should be measured — schedule a sampled direct probe on
  dominance-credited cells specifically to keep the discount honest.

### B2. Three-state labels — measured / inferred / unknown

Ship first in Part II; it costs nothing and it may resolve a meaningful share of
the complaint on its own.

`predicted_facet_recall` (`selection_rewards.py:438`) already pools the LO mastery
mean with the facet mean by evidence count, and `capability_grid` already renders
`Ready` for untested cells. But `facet_state_label` (`facet_diagnostics.py:305`)
decides `unexamined` on a raw mass threshold alone, so a facet the system can
predict confidently still reads as untouched.

Replace the binary with three states:

- **measured** — direct evidence above the mass threshold;
- **inferred** — pooled/dominance-derived prediction, rendered with its interval,
  explicitly labelled as inference;
- **unknown** — neither.

This is a display and labelling change over state the system already holds. It
writes nothing and certifies nothing. Keep the existing `mean ±√variance` readout
in Practice/Today/Feedback unchanged.

- *Hypothesis:* the count of cells reading as untouched falls substantially with
  zero new questions, and the remaining ones are the ones actually worth asking
  about.
- *Revert if:* inferred states are treated as measured anywhere downstream —
  audit by asserting that no certification path reads the label rather than the
  underlying evidence.

### B3. Prerequisite entailment — with caveats

LOs already carry `prerequisites`. Success downstream is evidence for upstream
competence; failure upstream predicts downstream failure. In the noiseless case
this turns a linear scan into a binary search for the frontier — the classic
knowledge-space result, and the largest structural reduction available in the
document.

**It is also the item in Part II most likely to be quietly wrong, for three
reasons:**

1. **The edges are LLM-authored.** A false prerequisite edge propagates false
   credit to a facet nobody measured, and it does so silently and at scale. The
   edges were authored for *instructional ordering*, which is a weaker claim than
   *logical entailment* — "teach A before B" does not mean "B implies A."
2. **Slips break deterministic implication.** A learner who knows a prerequisite
   can fail an item on it. Any implication rule must be probabilistic (the noisy
   BLIM-style version), never a hard inference.
3. **Entailment strength is not uniform.** Some prerequisites are genuinely
   necessary; some are facilitating. The `RequirementModality` vocabulary
   (`hard | path_specific | facilitating | instructional_order`) already draws
   this distinction for recipe components — **only `hard` and exercised
   `path_specific` edges may carry entailment**, and `instructional_order` must
   carry none by construction. This is the safeguard that stops the pedagogical
   graph from being read as a logical one.

**Mitigations, all required before it goes live:**

- Probabilistic implication at a discount, feeding mass and Ready only. Never
  certification except through §5.3.
- **Self-audit the graph from the evidence.** A learner who passes downstream and
  fails upstream is evidence the *edge* is wrong at least as much as evidence the
  learner is unusual. Track per-edge implication-violation rates; an edge above
  threshold is retired to `instructional_order` and stops conferring anything.
  This is cheap, it runs on data you already log, and without it a bad edge is
  invisible forever.
- Ship in shadow first: compute the entailed credit, do not apply it, and compare
  against directly measured outcomes on the same cells.

- *Hypothesis:* frontier location converges in O(log n) rather than O(n) probes
  on chains ≥4 deep.
- *Revert if:* per-edge violation rates are high across the graph generally —
  that means the prerequisite graph is instructional rather than logical, and the
  right response is to fix the graph, not to weaken the rule.

### B4. The Q-matrix model — selection authority only

`evidence_facets` across the item pool literally is a Q-matrix. With slip/guess
parameters, a cognitive diagnostic model infers a joint attribute profile from few
items instead of estimating each facet independently — the principled version of
B1 and B2 together, and the thing that would let EIG be computed *jointly* rather
than per-facet.

**The model risk is specific, and it is why this does not get belief authority:**

1. **Not identifiable at n = 1 learner.** Slip and guess are per-item parameters.
   With tens of attempts per LO there are fewer observations than parameters, so
   the fitted profile is the prior wearing a posterior's clothes. It will report
   confident attribute states it never measured — which is `harmful_write_rate`,
   the headline failure P0–P2 exists to prevent.
2. **Q-matrix errors stop being local.** Today a wrong `evidence_facets` entry
   damages one facet. In a joint model, one wrong row shifts the entire profile.
   And the Q-matrix is LLM-authored with a *lexical* fallback for items missing
   metadata (`_inferred_criterion_facet_weights`, `recall_coverage.py:819`), so
   misspecification is the expected case, not the tail.
3. **The conjunctive assumption does not match the blueprints.** DINA assumes all
   attributes are required; DINO assumes any. The blueprints are AND/OR recipes
   with real `any_of` structure. Either choice silently biases every inference,
   and the bias is invisible without ground truth.
4. **It produces no receipt.** A fitted latent profile carries no first-divergence
   anchor, no repair class, no provenance. It cannot be contested (causal §5.6),
   cannot be retracted to the learner (augmentation §2 A6), cannot be explained.
   That is a governance mismatch with the authority ladder, not merely a
   statistical concern.
5. **It optimizes prediction, not repair.** A CDM predicts item responses. It does
   not say what to fix, which is the actual product.

**The resolution is a lane split.** B4's payoff is overwhelmingly in *selection* —
which question next, when to stop — while its risk is entirely in *belief*. So:

- **Selection authority only.** It may rank candidate items and inform the
  stopping rule (§5.4, §5.5). It may **never** write facet state, mastery,
  certification, or anything a learner is shown.
- **Shadow before live**, on the same terms augmentation §6 uses for the
  simulation-likelihood arm and the knowledge-model §11.1 shadow item uses for
  capability-direct-vs-prior disagreement (`services/probe_targeting.py`, which
  by its own docstring "earns live authority only on held-out data"): compute it,
  log it, compare against the deterministic selection, and grant it selection
  authority only after it beats the incumbent on held-out data.
- **Keep the parameterization tiny.** One discrimination and one guess per *item
  family* (the existing `surface_family` / fingerprint grouping), not per item.
  At this sample size, fewer parameters that are identifiable beat more that are
  not.
- **The fitted values live in the `fitted_parameters` store**, not in TOML — per
  the mvp-0.4 convention already established.

- *Hypothesis:* the model's item ranking reaches the stopping threshold in fewer
  questions than deterministic EIG on replayed history.
- *Revert if:* it does not beat the deterministic ranking on held-out replay, or
  at any sign of its outputs reaching a belief write. The second is not a
  performance question; it is a firewall.

---

## 5. Part III — Selection and certification

### 5.1 The reframe

Coverage is the wrong objective for certification. Mastery of a subject is a
**conjunction**: the claim is `min over contract cells ≥ θ`. To prove a minimum
clears a bar you do not estimate every component — you **hunt for the one that
does not clear it**.

That inverts the exam objective. `exam_pool._select` (`:371`) greedily maximizes
newly covered components: a breadth objective, correct for a first look, wrong for
certification. The certification objective is adversarial — **spend every question
where P(this cell is below θ) is highest.** Failure to break the claim, after k
well-targeted attempts, *is* the certificate.

This is fast in both directions, which is the property worth having:

- **True master** — no weak links exist, the search finds nothing and terminates
  in a handful of hard integrative items. Each conjunctive pass (A1) clears
  several cells; dominance (B1) clears the rungs beneath; entailment (B3) clears
  upstream.
- **Clear non-master** — one clean failure on a well-chosen weakest link ends it
  immediately.
- **Genuinely borderline** — slow, and correctly so. That is where the information
  is.

### 5.2 Blocker: the coverage denominator (F6)

`covered_required_fraction`'s denominator becomes the **contract frontier** — the
(facet, capability) cells the active goal contract actually requires — instead of
the union of active items' `evidence_facets`.

The variance floor is right in principle: you *should* be less certain about what
you have not measured. But F4's denominator is an artifact of authoring history,
not an obligation, so today the floor punishes the learner for the system's
authoring activity. A cell nobody's goal requires is not a measurement debt.

Additionally: the floor is relieved by **inference as well as direct touch**, at
the Part II discount. An inferred cell is not a measured cell, but it is also not
an unexamined one, and the variance floor should say so.

Legacy vaults with no goal contract fall back to the current behaviour, so this is
strictly additive.

### 5.3 Blocker: a probabilistic path to certification (F7)

`lo_certification` stays the authority and its structure is unchanged: for some
blueprint, every hard component demonstrated, plus direct integration evidence.
What changes is what may satisfy a component.

**The substitution rule.** A component may be satisfied by inference (dominance,
entailment, embedded credit) instead of capability-matched direct evidence when
**all** of:

1. the inferred posterior for that cell clears the certification threshold by a
   configured margin — a wider margin than direct evidence requires, because the
   inference is the weaker channel;
2. the inference chain is recorded — which observation, which rule, what discount;
3. the component is **not** the blueprint's `integration` component. Integration
   is the coordination claim, and coordination is exactly what component-wise
   inference cannot establish. This preserves the existing invariant that strong
   components alone cannot saturate an LO.

**Every certificate carries its receipt**: which cells were measured directly,
which were inferred and by what chain, and the margin the decision was made at.
A certificate that cannot distinguish these is not one (standing constraint 9). It
is also what makes A6 (the system saying it was wrong) possible for certification
as well as for beliefs — a retired dominance edge (B3) can withdraw a certificate
and name why.

### 5.4 C1. Budgeted information design

Replace `exam_pool._select`'s coverage objective with **expected information per
minute over open contract cells**, computed against the current posterior.

The greedy structure survives — the objective stays submodular, so greedy remains
(1 − 1/e)-optimal — but the ranking now accounts for what the current design
ignores: prior uncertainty per cell (a cell already near-certain yields nothing),
expected success probability (an item the learner will certainly pass or certainly
fail is uninformative), and item cost in minutes (which requires a per-item time
estimate; use authored `expected_minutes` where present and a family median
otherwise, and record which).

Under §5.1's reframe the weighting is adversarial: cells are weighted by
P(below θ), so the design naturally concentrates on plausible weak links rather
than spreading uniformly.

- *Hypothesis:* fewer items reach the same certification confidence on replay.
- *Revert if:* the selected sittings concentrate on a narrow slice and
  post-certification delayed probes fail more often — over-concentration is the
  failure mode of an adversarial objective and it is caught in exactly one place.

### 5.5 C2. Adaptive sittings with a decision-equivalence stop

Select the next item mid-sitting from the updated posterior, and **stop when the
decision no longer changes** — the action-equivalence stopping rule that already
exists on the probe path, applied to certification.

Stop when P(all contract cells clear) > 1 − α, or when P(some cell fails) > 1 − β.

**Honesty caveat, which is a design constraint rather than a footnote.** At n = 1
learner you cannot obtain analytically calibrated α. There are no per-item
slip/guess parameters worth trusting (B4 risk 1), so any likelihood ratio is only
as good as the item model behind it. What ships is a **posterior-threshold stop
with conservative defaults whose realized error rate is measured and tuned**
(§5.7) — not a sequential probability ratio test with guaranteed error control.
Do not describe it as one, in the code, in the UI, or to the learner.

**Held-out integrity.** `reserve_exam_pool` reserves a fixed set; adaptive
selection needs to choose mid-sitting. Reserve a **superset** and select within
it, so the leakage guarantee that reservation exists to provide survives
unchanged.

- *Hypothesis:* median questions to a certification decision falls; the
  distribution becomes bimodal (fast clear decisions, slow borderline ones), which
  is the signature of a working sequential rule.
- *Revert if:* `false_certification_rate` rises above its pre-adaptive baseline.

### 5.6 C3. Spend only where a decision depends on it

Most cells should not read as debt at all. The goal contract defines which cells
need certification; everything else needs only enough confidence to schedule well.
Two consequences:

- The EIG objective ranges over **contract cells**, not all cells (this is the
  same set §5.2 fixes the denominator to — one definition, one code path).
- Non-contract cells are surfaced as inferred/unknown (B2) without generating
  work. A cell nobody's goal requires and no scheduling decision turns on is a
  shrug, not a gap.

### 5.7 Two claims at two speeds, and the metrics that license speed

**Separate "competent now" from "will retain."** These are different claims and
conflating them is a third reason certification feels unreachable — the system
implicitly waits for time to pass before saying anything confident, which reads to
the learner as never being noticed.

- **Competent now** is decidable today, from evidence gatherable in one sitting.
  Say it plainly, with the §5.3 receipt.
- **Will still have it at horizon H** is a *prediction*. No amount of questioning
  today resolves it; only time does. `goal_projection` already forms the FSRS
  retention ratio at the goal horizon — the machinery exists. Ship it as a
  separately-labelled claim with an interval that tightens as spaced probes land.

**Scoreboard additions** (extending augmentation §3 B5, before its freeze):

```text
false_certification_rate     # certified, then failed a delayed cold probe.
                             # This is the alpha actually being run at, and it is
                             # the only number that licenses any speed claim.
questions_to_certification   # the thing to minimize. Meaningless alone.
certification_regret         # questions served after the point at which the
                             # evidence already supported certification
cells_cleared_per_question   # Part I's direct measure
measurement_rank             # Part IV's: independent dimensions the item pool
                             # can actually resolve, vs facets declared
```

`false_certification_rate` is listed first deliberately, for the same reason
augmentation §3 B5 orders `problems_to_cold_success` first: **optimizing
time-to-certification without measuring false certification is lowering the bar
with extra steps.** No Part III change ships without it.

**The delayed cold probe is the ground truth**, and it is wanted anyway for
retention: one held-out-surface item per certified LO at +2–3 weeks. If it passes,
the certificate held. In a single-learner vault this is the only external validity
check available — the same argument augmentation §2 A2 makes for cross-model
agreement on the taxonomy.

### 5.8 Step 0 — the replay experiment

**Before building any of Part III.** `rebuild-derived-state` →
`replay_learning_object` re-runs the live computation path with no provider calls
(`services/replay.py:52-58`). So the proposed stopping rule can be run
retrospectively over existing history:

> Against `fixtures/linear_algebra` and `fixtures/arxiv`: at which attempt would
> an adversarial weakest-link rule with a posterior-threshold stop have certified
> each LO, versus when the system actually did?

That yields `certification_regret` on real data today, for the cost of a script
and no learner time. If the answer is "attempt 6 instead of 22," the prize is
quantified before anything is built. If it is "attempt 20 instead of 22," the
bottleneck is instrument quality (Part I) rather than the decision rule, and Part
III should wait. **This experiment is the cheapest decision-relevant artifact in
the document and it should run first.**

#### 5.8.1 Correction to the method (measured, not predicted)

**Replaying a prefix of the attempts does not produce a prefix of the state.**
`project_canonical_facet_state` → `replace_canonical_facet_state`
(`db/repositories.py:4336-4355`) `DELETE`s and rebuilds `facet_recall_state` and
`facet_capability_evidence` **whole**, as a pure order-independent projection over
the immutable observation ledger — deliberately, so that "no per-LO reset can
shear a facet shared across LOs." `reset_learning_object_derived_state` clears
mastery, facet recall, uncertainty, error events and item state, but the raw log
it projects from survives by design (augmentation §9). So a harness that replays
only the first k attempts still reads a ledger reflecting all n, and any
certification timestamp it reports is an artifact.

A correct prefix harness must **filter the observation ledger by cutoff** — remove
the attempts and their error events after k on a scratch copy — before replaying
and projecting. That is O(n²) attempt-replays for a full trajectory (~2.5s each on
`fixtures/linear_algebra`), so sample a coarse grid of cutoffs rather than every k.

#### 5.8.2 Measured result: `fixtures/linear_algebra`

21 LOs, 55 practice items, 39 facets, 43 attempts across 8 LOs. Findings marked
**static** need no replay and are unaffected by 5.8.1.

**Certification never fires (static).** 7 of the 8 practiced LOs are
undemonstrated, and *every one* of them has an unmet integration component. The
8th (`lo_orient_to_the_vector_space_idea`) has exactly one contract cell.

**And it cannot fire, at any k (static).** Reachability — can *any* authored item
observe this contract cell? — over all 21 LOs:

| | cells | share |
|---|---|---|
| contract cells | 64 | |
| reachable by some item | 9 | 14% |
| **unreachable** | **55** | **86%** |
| integration cells | 19 | |
| **integration cells reachable** | **0** | **0%** |

**Zero of 55 items observe `coordination`**, and 18 of 19 integration components
require it. Certification is structurally impossible for 20 of 21 LOs regardless
of learner performance, practice volume, or decision rule. The incumbent baseline
does not fire late — it does not exist, so `certification_regret` has no
denominator here.

**All of the loss is on the capability axis, none on the facet axis (static).**
Of the 43 attempts, scored against their own LO's contract:

- **100%** hit a facet the contract requires (capability ignored);
- **28%** hit a required (facet, capability) cell;
- **72%** hit no contract cell at all — *purely* because the item sits at the
  wrong rung.

Every attempt was on-topic. Nearly three quarters of the learner's practice was
discarded by the capability dimension alone. This is F2/F3 measured in learner
minutes, and it is the single most actionable number in this document.

**Why: the pool sits at the bottom of the ladder.** 44 of 55 items declare
`retrieval`; blueprints require `schema_interpretation` (20), `procedure_execution`
(14), `method_selection` (7), `retrieval` (8), and `coordination` for almost every
integration component. On practiced LOs the 25 contract cells split:

| | cells | remedy |
|---|---|---|
| reachable | 7 (28%) | — |
| `MISMATCH_ABOVE` — observed higher than required | 1 (4%) | **B1 dominance** |
| `MISMATCH_BELOW` — observed only lower than required | 14 (56%) | real instruments at the rung (A1, A2) |
| `NO_INSTRUMENT` — facet never observed at all | 3 (12%) | authoring |

**This revises the plan's own ranking.** B1 dominance was sequenced in Wave 4 as a
major lever; on this vault it converts **one cell out of 25**, because the pool is
almost never *above* the requirement — 9 of the 14 shortfall cells top out at
`retrieval`. Dominance only propagates downward, and there is nothing above to
propagate from. The lever that matters here is **rung placement**: authoring at
the capability the contract names (A1's `targets`, A2's laddered stems, and the
existing depth-rung machinery actually being honoured), plus genuine
coordination-level instruments for integration — which is exactly A1's conjunctive
capstone, since an integrative task *is* a coordination observation.

**D1 has no work to do here; D2 does (static).** Of 39 declared facets, only 14
are observed by any item, and among those 14 **no two share a measurement
signature** — there are zero indistinguishable pairs to collapse. The vocabulary
is not redundant, it is **uninstrumented**: 25 of 39 facets (64%) have no item
measuring them at any capability. `measurement_rank / facets_declared = 14/39 =
0.36`, and the deficit is non-instrumentation rather than synonymy. (The alias
table is already carrying 52 real redirects into 37 canonical targets, so some
merging has happened.) D1's collapse criterion is still correct; it is simply not
where this vault's loss is. D2's *separability* criterion is — a facet admitted at
ingest with no authorable instrument is precisely these 25.

#### 5.8.3 The integration default, and what fixing it buys

18 of 19 integration components sit at `coordination` — and the one that does not
(`method_selection`) proves the model was choosing, not falling through a code
path. The driver was the authoring prompt, which described `integration` as *"the
single component that **coordinates** them"*: it named the capability in the
definition and implied every recipe should have one, against a knowledge model
that says author it *only when* component competence can coexist with a
repeatable, observable, separately repairable assembly failure.

**Shipped** (`codex/prompts.py` constraint 14, `codex/schemas.py`
`SynthIntegrationComponent`, `source_set_synthesis.py` recipe mapping):

- The prompt now states the real criterion, says most recipes should omit
  `integration`, and warns that naming `coordination` makes the objective
  uncertifiable until a whole-task instrument exists.
- `SynthIntegrationComponent.capability` is `| None` with **no default**, so
  "the model did not choose" is representable. `SynthRecipeComponent` keeps its
  `retrieval` default — an `all_of` component always observes something, an
  integration component is optional and its capability decides certifiability.
- An undeclared capability is **dropped with a typed review diagnostic**, never
  defaulted. Minting the one capability the default rung trajectory refuses to
  author, from a missing field, was the defect.
- An explicit `coordination` integration is **kept and flagged** — legitimate,
  but it announces the obligation it creates rather than creating it silently.

**What it buys on this vault** (upper bound: every coordination integration
either dropped or lowered to an observable rung):

| scope | | cells reachable | certifiable LOs |
|---|---|---|---|
| practiced (8) | today | 7/25 (28%) | 1/8 |
| practiced (8) | integration fixed | 7/18 (39%) | **3/8** |
| all (21) | today | 9/64 (14%) | 1/21 |
| all (21) | integration fixed | 9/45 (20%) | **3/21** |

So the fix triples the certifiable population and removes a third of the contract
cells outright — but it does **not** move the reachable-cell count at all (still
7, still 9). Every cell it fixes was an integration cell; not one component cell
changes. The 72% rung mismatch is untouched, because that is a statement about
`all_of` components sitting below their required capability, and no integration
policy addresses it.

**It also does not repair existing vaults.** Blueprints are vault content, not
derived state, so `rebuild-derived-state` will not touch the 18 already persisted.
Those need a re-authoring pass or a doctor-flagged manual review — see Wave 2.

**Verdict for the plan.** §5.8's stated branch applies in its strongest form: the
bottleneck is not the decision rule, and **Part III must wait.** No stopping rule
can improve on a certification path that is structurally unreachable. Wave order
stands, with one correction: B1 drops in priority relative to rung-correct
authoring, and the reachability report itself (`REACHABLE / MISMATCH_ABOVE /
MISMATCH_BELOW / NO_INSTRUMENT` per contract cell) should ship as a standing
`learnloop doctor` check — it is pure static analysis, it costs nothing, and it
would have caught this before 43 attempts were spent.

---

## 6. Part IV — Vocabulary

Every facet is a standing measurement obligation. Facet proliferation is the
numerator of §0's ratio, and it is currently unbounded.

### D1. Collapse facets no instrument can separate

**The criterion is behavioural, not lexical** (standing constraint 11). Two facets
are one facet for measurement purposes when:

1. no item in the pool discriminates them — `identifiability.analyze_identifiability`
   already computes exactly this; **and**
2. they imply the same repair class.

Then one becomes an alias of the other. The substrate is already there and cheap:
`facet_aliases` plus transitive `facet_merges`, resolved centrally in
`facet_state_reader.py:62`, so a collapse is a vocabulary decision rather than a
migration. Existing evidence follows the alias.

**Publish `measurement_rank`** — the number of independent dimensions the item
pool can actually resolve, against the number of facets declared. If 40 facets
resolve to 12 dimensions, the system is charging the learner 40 facets' worth of
questions for 12 facets' worth of information, and that number should be visible
rather than inferred from frustration.

**Review, never auto-merge** — inherited from augmentation §5 Phase D item 3. The
analysis proposes; a human decides. The existing lexical MinHash review
(`facet_candidates.py`) stays as a *hint* for the review surface and is never
promoted to a merge criterion; it is exactly the lexical-habit key augmentation §2
A2 rejects.

### D2. Gate facet minting at ingest

**Ingest is where the proliferation happens** (F8), so this is where the gate
belongs — moved upstream from augmentation §5 Phase D, whose review loop is
otherwise unchanged.

Today `source_set_synthesis` mints one facet per extracted claim at
`status: "reviewed"`, with existing ids offered as context and nothing structural
preventing a near-duplicate.

**The mint criterion.** A new facet is admitted only when:

1. it is **separable** from its nearest existing neighbours — there exists an
   authorable item on which a holder of one and a holder of the other visibly
   diverge; **and**
2. it implies a **distinct repair**.

Otherwise it is registered as an **alias** of the neighbour, not as a facet.
Same criterion as augmentation §2 A2, one level up, and the same test as D1
applied at mint time rather than after the debt accrues.

**The raw material is already in the payload.** Ingest emits `preconditions`,
`applicability`, `positive_examples`, `negative_examples`, `error_signatures` and
`instructional_repairs` per facet (`source_set_synthesis.py:596-620`). Those are
precisely what a planted persona needs — so the separability test is §3.0's
harness, run at ingest. **One mechanism, three uses**: the authoring gate for
A3/A4/A5, the mint gate here, and the discrimination profiles of A5 are the same
artifact viewed from three directions.

**Failure is typed, not silent.** A facet that cannot be shown separable is
recorded with the reason (no authorable discriminating item / same repair class /
insufficient payload to test), because that record is the missing-vocabulary
signal augmentation §2 A5 wants, arriving from the other end of the pipe.

**Sequencing note.** D2 lands **before** the next round of item authoring. Every
facet minted today is a cell owed questions forever, and ingest is currently a
facet firehose behind a lexical filter.

### D3. Gate integration components at ingest (sibling rule to D2)

D2 governs what the *facet* vocabulary admits. The same admission logic belongs
one level up, on the blueprint, because an integration component is a
certification obligation minted at ingest exactly as a facet is a measurement
obligation minted at ingest — and §5.8.3 measured what happens without it: 18 of
19 objectives born uncertifiable.

**The admission criterion.** A recipe earns an `integration` component only when:

1. the **assembly failure is nameable** — a learner could hold every `all_of`
   component and still fail, repeatably, observably, and in a separately
   repairable way (the knowledge model's own words, previously stated nowhere the
   author could see them); **and**
2. its **capability is observable** — an instrument at that rung is authorable.
   `coordination` satisfies this only behind a reviewed depth envelope, because
   the default trajectory deliberately refuses to generate whole-task work.

Absent (1), omit the component — omission is the correct output, not a gap.
Absent (2), the objective is uncertifiable by construction and the reachability
check (§5.8.2, Wave 1) must say so at authoring time rather than after the
learner has spent attempts against it.

**Shipped for the ingest path** (§5.8.3). What remains is the same rule applied to
blueprints already persisted, and the reachability check that enforces it
continuously.

- *Hypothesis:* integration components per ingested LO falls well below 1.0;
  certifiable-LO share rises without any change to the item pool.
- *Revert if:* dropping integration components lets LOs certify on components
  alone where a real assembly failure existed — visible as certified LOs failing
  the §5.7 delayed cold probe on whole-task items specifically. That is the
  invariant integration exists to protect, and it is worth more than the
  certification-rate win.

- *Hypothesis:* facets minted per ingested source falls; `measurement_rank` /
  facets-declared approaches 1.
- *Revert if:* the gate rejects facets that later prove separable once better
  instruments exist — detectable because rejections are typed and reviewable, and
  reversible because an alias can be split back out. Prefer alias-and-revisit over
  mint-and-regret; the asymmetry favours it.

---

## 7. Part V — Cheap channels

Evidence that costs the learner little or nothing. All of these fill *unknown*;
none of them certifies (standing constraint 9).

**E1. Teach-back as a coverage instrument.** Two-tier rubrics exist, with
`transfer`-tier criteria already carrying a reduced symmetric evidence-mass
multiplier and defaulting to `method_selection`. One teach-back artifact touches
many facets at low mass each — which is the right shape for moving cells out of
unknown. It is currently used as a depth instrument; it is also a breadth one.

**E2. Learner claims as priors only.** `covering_learner_claim` already seeds a
rung entry point and the difficulty band. Surface the claim in the diagnostic view
as *claimed, unverified* — a distinct state from unknown, which it genuinely is.
It never certifies and never writes mastery.

**E3. Source-ordered difficulty from ingest.** Imported exercises carry the
original author's ordering, which is a free difficulty prior — usually better than
an LLM estimate, since it reflects observed student performance at scale. Record
it as `difficulty_source='author'` and let it inform the band inversion.

**E4. Success plus silence decays uncertainty.** `question_signal` already raises
displayed uncertainty for recent unresolved tutor questions
(`unresolved_question_facet_counts`); the inverse is available from the same
machinery.

**The caution is load-bearing:** bind the decay to *success*, not to silence.
Silence alone is not evidence — a disengaged learner also asks nothing, and
decaying variance without evidence is precisely how confident wrongness is
manufactured. `success + silence` decays, capped and bounded; `silence` alone
does nothing at all. The decay is on uncertainty only; it never moves a mean.

---

## 8. Sequencing

Ordered by (decision value ÷ cost), with dependencies respected.

**Step 0 — done. See §5.8.2.** It reordered what follows: on
`fixtures/linear_algebra` the decision rule is not the bottleneck by a wide
margin, so Part III waits and Part I moves up.

**Wave 1 — no new questions, no new instruments.**
- **Contract-cell reachability as a `doctor` check** (§5.8.2). Static, free, and
  it is the check whose absence let 43 attempts land on a contract that could
  never close. Ship it first.
- B2 three-state labels (§4).
- §5.2 coverage-denominator fix — removes the perverse incentive of F6.
- D1 `measurement_rank` published (analysis only; merges follow review). Expect it
  to report *non-instrumentation* rather than synonymy, as it does on
  `linear_algebra`.

**Wave 2 — stop the bleeding upstream.**
- **D3 integration gate at ingest — shipped** (§5.8.3). Was the cheapest item in
  the document and it triples the certifiable-LO share on `linear_algebra`.
- **Backfill the blueprints already persisted.** The ingest fix is forward-only;
  blueprints are vault content, so no rebuild touches them. `fixtures/arxiv` and
  `fixtures/linear_algebra` carry integration components authored under the old
  prompt. Re-author against D3's criterion — expect most to be dropped, a
  minority to be lowered to an observable rung, and a few to be genuinely
  `coordination` and therefore owed an A1 capstone.
- §3.0 planted-persona authoring gate.
- D2 ingest mint gate. Before the next authoring round, per §6.

**Wave 3 — the instruments.**
- A1 (`targets` on `RubricCriterionPayload`, spread-rule inversion) — the single
  largest lever on §0's denominator.
- A6 opportunistic trace evidence — required to discharge A1's guard 1.
- A8 clarification channel. Small, and it protects the abstention discipline.
- A2, A3, A4, A5, A7 in whatever order the fixtures make convenient; they are
  independent of one another once §3.0 exists.

**Wave 4 — inference.**
- B1 dominance (with its sampled direct-probe audit). **Demoted by §5.8.2**: it
  converted 1 of 25 contract cells on `linear_algebra`, because the item pool sits
  *below* the contract almost everywhere and dominance only propagates downward.
  Cheap and still correct — but it is not the lever it looked like, and it should
  not be sequenced ahead of rung-correct authoring.
- B3 entailment, shadow first, with per-edge violation tracking from day one.

**Wave 5 — certification.**
- §5.3 substitution rule and certificate receipts.
- §5.7 metrics and the delayed cold probe — **before** C1/C2, not alongside.
- C1, C2, C3.

**Parked.** B4 (§9).

## 9. What stays parked, and what would unpark it

**B4 as a belief model.** Never. The selection-only lane is the permanent
disposition, not a staging area.

**B4 as a selection model.** *Trigger:* the §5.8 replay shows the deterministic
EIG ranking leaving material regret on the table, AND enough attempt volume exists
to fit item-family parameters, AND it beats the deterministic ranking on held-out
replay. Absent the first condition it is solving a problem that has not been shown
to exist.

**Cross-learner pooling.** Every identifiability problem in B3 and B4 dissolves
with multi-learner data. Nothing here assumes it arrives; nothing here is
structured to prevent it.

## 10. Validation

Adds to the regression matrices of causal §12 and augmentation §10:

- A criterion with authored `targets` compiles to those targets verbatim; a
  criterion without them compiles to all-primary at the item capability
  (unchanged legacy behaviour).
- A conjunctive item passed in full credits every primary cell at 1.0 and every
  *trace-exercised* supporting cell at 0.3; a supporting target with no trace
  evidence records `unexercised_supporting_target` and confers nothing.
- A conjunctive item failed at step 3 writes negative evidence against the
  diverged facet only; the passed-facet firewall blocks the rest (regression on
  the existing invariant, under the new instrument).
- A cell whose mass exceeds the embedded-share cap does not read as demonstrated.
- Two parts of one laddered stem at the same capability count as ~one independent
  group; two parts at different capabilities count as two.
- An item whose facet-holder and misconception-holder personas produce the same
  outcome is rejected by the §3.0 gate and never reaches a learner.
- A contrast pair whose members fall in different difficulty bands is rejected.
- An error-hunt item whose planted error is found by the misconception-persona is
  rejected.
- A clean-solution error-hunt on which the learner reports an error writes a
  misconception candidate, not a facet failure.
- `no_profile_applies` is representable, recordable, and appears in the two-tailed
  fill-rate telemetry.
- A confidently-graded criterion never triggers a clarification (A8); a hedged one
  triggers at most one; an unanswered clarification resolves to the abstention,
  never to a guess; replay reproduces the resolved grade without re-asking.
- An adjacent-facet question (A7) writes evidence at its observed capability only;
  it can never satisfy a `procedure_execution` component.
- Dominance credit from an *assisted* attempt is zero.
- A prerequisite edge of modality `instructional_order` confers no entailment; an
  edge whose violation rate exceeds threshold is retired and stops conferring.
- Adding a practice item does not change `covered_required_fraction` for a goal
  whose contract does not include that item's facets (§5.2 regression on F6).
- A component satisfied by inference is certifiable only at the wider margin, is
  never the integration component, and appears as inferred on the certificate.
- A goal certified on inferred components loses certification, with a
  learner-visible correction (augmentation §2 A6), when the underlying edge is
  retired.
- A facet minted at ingest that is not separable from its nearest neighbour is
  registered as an alias with a typed reason.
- Merging two facets by alias preserves the union of their evidence and changes no
  attempt history.
- `success + silence` decays uncertainty within its cap; `silence` alone changes
  nothing; neither moves a mean.

## 11. Non-goals

- **No certification from inference alone.** §5.3 is a bounded substitution with a
  receipt, not a bypass. The integration component always requires direct
  evidence.
- **No belief authority for B4, ever.** Selection only, and the firewall is not
  performance-conditional.
- **No auto-merge of facets and no auto-mint.** D1 and D2 propose; humans decide.
- **No lexical criterion promoted to an identity criterion**, anywhere.
- **No recognition-mode items smuggled in as screens.** A3's repair requirement
  and A7's constructed answers are load-bearing, not stylistic.
- **No mandatory explanation.** A6's elicitation is targeted, rewarded and
  budgeted; a system that makes people narrate their arithmetic has traded a
  measurement problem for a retention problem.
- **No persona output as learner evidence** — inherited unchanged from
  augmentation §11. The §3.0 gate grades in memory; that is the invariant, not a
  convenience.
- **No relaxation of any causal-spec firewall.** A1 in particular *depends* on the
  passed-facet barrier; it does not negotiate with it.
- **No speed claim without `false_certification_rate`.** A faster certificate that
  is not measured for correctness is not a faster certificate.
