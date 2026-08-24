# P2 implementation spec: narrow exemplar-driven golden path

**Status:** Draft v0.2, code-audited 2026-07-16; depth contract amended
2026-07-17; orphan/n=1 consensus folded in 2026-07-17 (`suggest_next`-only
first cut, triage mechanism, pool provenance, affect run semantics)
**Parent:** `spec_new_improvements_v2.md` (P2 delivery phase and §8a vertical
slice)
**Depends on:** `spec_p0_measurement_correctness.md` and
`spec_p1_shared_substrate.md`
**Acceptance focus:** one chapter, one exercise family, one end-to-end promise
**Ownership claims** (ledger seed 2026-07-17, `spec_ownership_ledger.md`;
updated 2026-07-18): implements U-010@v2 (affect run semantics), U-027@v1
(triage mechanism), U-028@v1 (pool provenance), U-033@v1 (minimal
bidirectional reader dialogue, §7.6; consumes the U-034 pipeline artifacts
for owner review of its question set); defers automatic depth activation to
the auto-depth package U-018@v1 (which carries U-011 downgrade enforcement
and U-016 edge authoring); U-017@v3 (`ask_now` planner / automatic density)
and U-036 (non-text renderers) are out of scope here

P2 proves the smallest honest version of:

> Choose tasks like this; find my current boundary; teach or repair the nearest
> reason I cannot yet do them; strengthen that ability on changing surfaces;
> then test it on a fresh target-like task and, if I authorized it, grow one
> reviewed step beyond it without making me approve every item.

The implementation deliberately uses reviewed blueprints, reviewed activity
patterns, pre-authored diagnostic cards, and a bounded surface pool. The goal
is to validate the learner loop before increasing authoring or controller
automation. In this cut the promise's final clause ships as an *invitation*:
the run lays out the reviewed next step and one explicit confirmation
activates it. Commit-without-prompt authority (`auto_within_envelope`
enforcement) is deferred to the auto-depth package (U-018) together with its
dead-man switch.

---

## 1. Outcome, entry gate, and boundaries

At P2 exit a learner can select one or more end-of-chapter exercises that
represent one task family, confirm what “tasks like this” means, complete a
short baseline, receive reason-specific instruction/practice, and take one
fresh held-out assessment. Every conclusion is traceable to the P0 measurement
receipt, the P1 commitment/activity tree, and the exact terminal-contract
version. After that assessment, the run records the reached milestone and
renders one reviewed next-depth edge inside the learner-confirmed envelope as
a `suggest_next` invitation; one confirmation activates it (automatic
activation is deferred, U-018).

### 1.1 Entry gate

The P2 feature may activate for a goal only when items 1–6 are true. Items 7–8
are additionally required for `certifying` mode. Items 9–10 are required
before a post-milestone depth edge can activate (confirmed invitation in this
cut; automatic under the deferred auto-depth package, U-018):

1. the selected source revision and chapter/unit are immutable and readable;
2. every exemplar has a resolvable source locator and reviewed solution/rubric
   provenance;
3. one reviewed `TaskBlueprintVersion` describes the target family;
4. the learner confirms the exemplar interpretation, minting P0 goal-contract
   v1;
5. a P1 commitment and purpose-typed families exist;
6. diagnostic cards are pre-authored and pass P0/P1 measurement gates;
7. at least one practice surface and one globally fresh assessment surface are
   admitted;
8. the assessment surface is reserved against the confirmed contract before
   any potentially contaminating practice is shown;
9. the next depth edge is reviewed, wholly inside the confirmed envelope, and
   has admitted successor pattern/family/card paths;
10. when that edge changes terminal support, a fresh successor-assessment
    candidate exists and can be reserved atomically with the P0 successor before
    any deeper activity is exposed.

If items 7–8 cannot be satisfied, the system may still teach and practice only
when at least one admitted practice surface exists; it labels the run
`practice_only` and makes no terminal claim.

### 1.2 Non-negotiable invariants

1. **One chapter and one target family.** P2 rejects mixed-unit or
   multi-family runs rather than pretending it can plan them.
2. **Exemplar confirmation defines v1.** Before confirmation the terminal
   contract is a draft. Every material edit afterward creates a P0 append-only
   successor; no run silently changes its meaning.
3. **Consumer pins hold.** The probe episode pins at open; assessment pins at
   reservation; progression reads/logs the current head at each decision.
4. **The selected exemplar is an anchor, not proof.** It can ground generation
   and explanation but cannot count as unseen assessment.
5. **Cards are pre-authored.** P2 never invents a diagnostic instrument or
   instructional protocol on the hot path. Surface rendering stays inside an
   admitted P1 card/pattern.
6. **Reason precedes repair.** A failure is not sent through a universal wrong-
   answer flow. The run records a bounded triage result and chooses the matching
   intervention.
7. **Instruction changes the state being measured.** Starting instruction
   closes the diagnostic segment. A later cold check opens a new segment; it
   never continues the pre-instruction posterior.
8. **Practice is not assessment.** Practice and assessment use separate
   purpose-typed families and globally shared exposure checks.
9. **Feedback burns assessment freshness.** A failed assessment may seed a
   separate practice-family surface after feedback, but the original never
   returns as pristine assessment.
10. **No automation cliff.** Wide heuristic intervals reduce claims and may
    choose a conservative intervention; they do not block all useful teaching.
11. **Resume exactly.** A crash/retry reopens the same committed administration
    or next state. It never chooses a second item or repeats a side effect.
12. **Depth is bounded authorization — one edge per decision.** P2 commits at
    most one reviewed evidence-gated edge per *decision*, then replans (never
    per run or per session; each subsequent milestone is a fresh decision).
    In this cut every commit requires an explicit learner confirmation
    (`suggest_next` semantics); commit-without-prompt under
    `auto_within_envelope` is deferred to the auto-depth package (U-018). A
    transition never crosses the envelope, recursively climbs, hot-path
    authors a protocol, mutates a card, reuses FSRS/certification across a
    fork, or erases the milestone just achieved.

### 1.3 In scope

- chapter/exercise discovery and explicit learner selection;
- reviewed, versioned task blueprints and exemplar confirmation;
- creation of one P1 commitment/family bundle;
- a 2–4 administration baseline using pre-authored cards;
- transparent failure-reason triage;
- source-grounded instruction, example comparison/completion, setup-only work,
  independent repair, and whole-task integration where the blueprint requires;
- a minimal bidirectional reader dialogue during discovery and instruction
  (U-033, §7.6): span-grounded Ask in a `reader` tutor context, owner-placed
  reading questions, and the four-disposition picker;
- card-level scheduling and rotating practice surfaces;
- one fresh held-out terminal assessment and post-attempt restoration;
- one evidence-gated, learner-confirmed next-depth activation inside a
  confirmed envelope, with a new reserve when terminal support changes;
- narrow boundary/readiness display, activity/commitment retirement, and a
  complete measurement/decision trace;
- deterministic orchestration, migration adapters, and planted-learner tests.

### 1.4 Explicitly out of scope

- more than one source chapter/unit or target exercise family per run;
- automatic blueprint acceptance, automatic new diagnostic-card authoring, or
  whole-library synthesis;
- unbounded, cross-chapter/family, outside-envelope, or unreviewed automatic
  depth escalation;
- the auto-depth package (U-018), deferred as one unit: commit-without-prompt
  `auto_within_envelope` enforcement, its affect-downgrade dead-man switch
  (U-011), and LLM edge-instance authoring (U-016);
- reader annotations, demand-paged reading, and in-reader authoring (P3) —
  the §7.6 dialogue slice runs on block-level span views and existing
  question/tutor persistence, not the P3 annotation layer;
- the LLM `ask_now` intervention planner and any automatic reading-question
  density policy (U-017@v3): every P2 reading question is owner-placed;
- global learned controller, learned familiarity, robust cross-mode scoring,
  general interleaving/dispersion experiments, and open-world expansion (P4);
- mid-episode hypothesis-set mutation;
- a readiness claim spanning task types outside the frozen target support;
- projects, voice/timed-language tasks, artifact grading, syntopic reading,
  population promotion, or learned taste models;
- dynamic-media renderers and authentic notebook/artifact work (U-036) — all
  P2 dialogue and activities render as text/KaTeX.

---

## 2. Verified code-truth ledger

| Area | Verified reality | P2 consequence |
|---|---|---|
| Source inventories | Unit inventories are deterministic, span-cited candidates with `semantic`, `practice`, `assessment`, and `combined` profiles (`source_unit_inventory.py:1-29,50`). | Reuse the inventory/cache and locators; add reviewed exemplar/blueprint semantics rather than another extractor. |
| Blueprint synthesis | Synthesis normalizes task recipes into facet/capability components plus an optional integration component (`source_set_synthesis.py:630-680`). | Version and review this shape; add target-distribution/task-feature/rubric requirements without inventing conjunction state. |
| Generated practice | Synthesis still emits monolithic PracticeItems (`source_set_synthesis.py:692+`). | Materialize through P1 families/cards/surfaces; keep PracticeItem snapshots only for compatibility. |
| Diagnostic generation | Existing probe generation selects admitted families/cards, renders LLM/parametric surfaces, gates them, parks unreviewed instances, and opens episodes only when eligible (`probe_instance_generation.py:929-1083`). | Keep this machinery, but require P2 cards to be pre-authored and reviewed before run start. |
| Diagnostic objective | Probe episodes already have frozen hypothesis sets, committed presentations, predictive/hypothesis EIG, blocks, and bounded observation counts. | Use the episode API; P2 orchestrates entry/exit but does not implement a second posterior. |
| Repair | Current remediation ranks existing PracticeItems by facet overlap, chooses one primed and one cold item, and may choose the same item twice when only one exists (`remediation.py:65-118`). | Replace the P2 path with reason-specific pattern/stage selection and require an independent delayed surface. Preserve legacy remediation outside P2. |
| Delayed check | Current remediation schedules a one-day cold retry after a primed attempt (`remediation.py:121-180`). | Reuse the follow-up/event seam, but bind it to card/surface lineage and P1 freshness rules. |
| Exam pool | Current pool reserves never-attempted PracticeItems, stratifies difficulty, prefers novel `surface_family`, and releases them after use (`exam_pool.py:1-25,105-182`). | P0/P1 assessment reservation supersedes authority; retain this as a compatibility projection and strengthen novelty through the global ledger. |
| Scheduler | Live queue ordering is a weighted selection reward and only limited same-day item rotation exists. | P2 uses a narrow explicit run state machine and feasible-set checks; it does not claim this scheduler is the final controller. |
| Reader/restoration | `span_view` can resolve source text/geometry and record source exposure, but the P3 reader/annotation layer does not exist. | P2 restores cited source neighborhoods through the existing span view; annotation restoration is conditional and lands in P3. |
| Terminal goal | The current YAML Goal is too small, while P0 specifies confirmed versioned terminal contracts and per-consumer pins. | The P2 run requires P0 contract v1 and never infers target support from the legacy goal alone. |

P2 acceptance must re-run this audit. “Existing” means a tested service seam,
not that its current schema or authority survives unchanged.

---

## 3. Reviewed target contract

### 3.1 Exemplar selection

An exemplar candidate is a source object or inventory exercise/problem with:

- source/revision/unit/block locators;
- exact visible statement and asset references;
- solution or answer-key provenance, kept out of learner-visible cold context;
- candidate task-family key;
- extraction-health status;
- practice/assessment eligibility suggestion.

The learner selects exemplars that express one intended family. Selection is a
commit-class action and creates a draft P1 commitment. It does not yet create a
confirmed goal-contract version.

The confirmation screen shows:

- the selected tasks and excluded neighboring task types;
- plain-language “tasks like this” invariants;
- required capabilities, expected complexity/span/transfer range;
- tools/open-book/time conditions;
- acceptable performance and burden;
- the proposed `hold_at_target`, `suggest_next`, or `auto_within_envelope`
  policy, the multidimensional envelope, and its first reviewed next edge;
- which selected tasks are familiar anchors and therefore cannot be held out;
- the proposed fresh-assessment support.

One confirmation atomically activates the reviewed blueprint, appends goal-
contract v1, appends the commitment/depth-policy/envelope versions, and reserves
the assessment surface. If any part fails, none becomes active. Choosing
`auto_within_envelope` is the learner's one-time authorization for eligible
inside-envelope edges; it is not blanket permission to increase difficulty.
In this cut `auto_within_envelope` is recorded as standing authorization but
*served* as `suggest_next` — the run renders each eligible edge for one-tap
confirmation; commit-without-prompt begins when the auto-depth package
(U-018) ships against this stored authorization.

### 3.2 TaskBlueprintVersion

Create stable `task_blueprints`, immutable `task_blueprint_versions`, and
append-only `task_blueprint_review_events`. A version contains:

- source revision/unit and exemplar ids/weights;
- semantic target facets and the closed P1 capability vocabulary;
- alternative solution recipes (`all_of`, `any_of`) and optional integration
  component;
- P1 TaskFeature target ranges and administration conditions;
- task-family invariants and permitted surface-variation axes;
- response contract, outcome schema, full rubric, fatal errors, and criterion
  dependencies;
- common failure signatures mapped to triage candidates;
- source neighborhoods for each component/repair;
- target-distribution support and weights;
- an ordered reviewed depth-milestone graph whose edges specify exact
  TaskFeature/capability/support deltas, exit evidence, successor activity path,
  fresh-proof rule, and burden;
- practice, diagnostic, and assessment leakage boundaries;
- authoring/model/provenance versions and canonical hash.

`reviewed` means a human/owner verified that:

1. every required component is source-grounded or explicitly expert-authored;
2. at least one solution path satisfies the rubric;
3. the exemplar set and variation axes describe one coherent family;
4. the rubric applies verbatim to admitted target-like surfaces;
5. integration is modeled as a blueprint component, not pairwise evidence;
6. assessment support excludes familiar exemplars and leaked solutions;
7. every automatic depth edge is monotone in a declared pedagogical direction,
   lies inside its proposed envelope, and can be served without inventing a
   protocol on the hot path.

Review is append-only. A blueprint material edit mints a successor and requires
a corresponding P0 contract successor before progression or a new reserve may
use it.

### 3.3 Target distribution

The goal contract references an immutable target-distribution snapshot whose
support is the cross-product constrained by the blueprint:

```text
task family × capability requirements × task-feature ranges ×
representation/response form × terminal administration conditions
```

Weights need not enumerate every surface, but support must be testable. Each
diagnostic/assessment card declares which cells it covers. The selected
exercise itself has exposure status `familiar_anchor` and zero held-out weight.

A single P2 assessment surface is a sample from this distribution, not proof of
all conceivable transfer. The resulting claim names covered support and its
interval; it never says “mastered the chapter.”

---

## 4. Golden-path run and state machine

### 4.1 Durable run

Create stable `golden_path_runs` and append-only `golden_path_run_events`.
The run pins:

- commitment and initial version;
- source revision/unit;
- task-blueprint version;
- initial goal-contract version;
- depth-policy/envelope version and initial milestone;
- reserved assessment administration/surface and its contract pin;
- orchestration policy and decision-parameter manifest;
- visible time/probe/burden caps.

Current state is a projection of events. Launch states are:

```text
draft
ready
measuring
triaging
instructing
completing
practicing
integrating
awaiting_delayed_check
ready_to_assess
assessing
restoring
deepening
maintaining
complete
paused
practice_only
needs_review
abandoned
```

The run may skip states when evidence supports it. It may move back from
practice/integration to instruction after a new failure, but it never reopens a
closed diagnostic segment. A later measurement creates a new probe episode.

Every transition event records:

```text
from/to state
reason and feasible alternatives
evidence/observation ids
goal-contract head evaluated
depth-policy/envelope version and predecessor/successor milestone
selected family/card/pattern
policy + calibration status
burden/time consumed and remaining
```

### 4.2 Narrow live policy

P2 uses this transparent staged policy only inside its one run:

```text
if a decision-relevant uncertainty has an admitted probe: measure, within cap
elif target knowledge is absent:                         instruct
elif performance is scaffold-dependent:                 complete / repair
elif components are present but whole task fails:       integrate
elif delayed independent practice is not demonstrated:  practice / wait
elif fresh assessment is valid and reserved:            assess
elif current milestone is reached and one next edge is authorized,
     reviewed, feasible, and positive-value:             deepen one edge
else:                                                    maintain, suggest, pause, or stop
```

This is not the P4 global controller and does not rank unrelated commitments.
Constraints—held-out protection, activity purpose, dispersion, learner burden,
run scope, and the active depth envelope—first produce a feasible set. The state
machine selects only from that set. `deepen one edge` records the achieved
milestone first; in this cut it always renders a proposal requiring one
explicit confirmation (`auto_within_envelope` is stored authorization served
as `suggest_next` until U-018 ships), and under `hold_at_target` it is
infeasible.

### 4.3 Idempotency and resume

Each transition uses an expected current event/head and a client idempotency
key. Opening an administration and appending its `served` exposure are atomic.
On resume:

- a served/unsubmitted administration is restored exactly;
- a submitted administration waits for/reuses the same grade event;
- a completed projection advances at most one transition;
- expired diagnostic presentations end explicitly and burn as required;
- an assessment reservation is revalidated before render, never silently
  replaced after the learner has seen the task.

---

## 5. Baseline and boundary localization

### 5.1 Pre-authored instrument pack

The reviewed target family must have a bounded pack covering the nearest
action-relevant alternatives, normally:

- representative target-like setup/whole-task card;
- schema interpretation or near-confusable comparison;
- procedure execution;
- method selection/setup-only;
- integration where the blueprint has an integration component.

Cards are diagnostic-purpose P1 cards backed by existing probe likelihood and
identifiability machinery. Their coarse outcome spaces follow P0. Pack
provenance mirrors blueprint review (U-028): an LLM drafts candidate cards
within the reviewed blueprint's bounds (or the owner authors them directly),
and the owner reviews each card before admission; nothing enters the pack
unreviewed. The pack is rejected if plausible grader/likelihood perturbations
change the recommended repair without a disclosure/abstention path.

P2 may mint bounded JIT surfaces from these cards and prefetch the next one. It
may not author a new card mid-run.

### 5.2 Episode behavior

- open one P0/P1 diagnostic episode and pin the goal-contract version then
  current;
- begin top-down with a representative target-family instrument when valid;
- use predictive EIG for boundary coverage and hypothesis EIG when a named
  distinction changes the repair;
- cap visible administrations at 2–4 and apply the episode's robust stopping
  rules;
- defer answer feedback until the diagnostic block ends;
- burn every rendered diagnostic surface forever for diagnosis;
- close the episode on stable decision, same-action equivalence, low robust
  value, cap/fatigue, missing instrument, learner stop, or review need.

Under heuristic channels the output is phrased as “best-supported next step”
with alternatives and calibration label, not a declarative diagnosis.

### 5.3 Boundary view for P2

P2 renders only cells relevant to the target blueprint:

```text
facet × capability -> demonstrated | developing | untested | weak | contested
```

This is a view over P0/P1 evidence and active episode hypotheses. “Untested” is
not “cannot”; “weak” describes observed performance under named context; and a
contested cell links to its measurement receipt. No new mastery table is
created.

---

## 6. Failure-reason triage

### 6.1 Triage record

After a qualifying miss, append a `failure_triage_event` with a distribution
or bounded candidate set over:

```text
memory_lapse
unfamiliar_or_missing_knowledge
schema_or_conceptual_hole
false_belief_or_confusion
procedure_execution
method_selection
coordination_or_integration
task_interpretation
surface_or_grading_fault
unknown_or_ambiguous
```

Inputs are the committed response, criterion trace, first divergent step,
prior cold evidence, assistance/familiarity, active misconception history,
surface validity, and P0 grader interpretation. Reading behavior or self-report
may seed alternatives but is not performance evidence.

Triage is produced by a two-tier mechanism (U-027). Tier one is a
deterministic route table over grader outcome class, error signature, grader
confidence bucket, and attempt features (assistance, exposure history,
surface validity), applied whenever evidence is decisive (`dont_know` on
never-exposed content, quarantined grade, expired memory trace). Otherwise
tier two applies: the P0 grading pass emits a provisional distribution over
reasons, presented as a decision aid with named alternatives — never silently
applied to a consequential transition. Learner/owner overrides of either tier
are logged as adjudication anchors feeding the U-020 calibration stream, and
the triage channel is registered `heuristic` in the P0 decision-parameter
registry so misroutes are discoverable rather than ambient. Only
`false_belief_or_confusion` or `unknown_or_ambiguous` opens/continues a
diagnostic episode when the choice of repair would materially differ.

### 6.2 Route table

| Best-supported reason | First intervention | Required cold follow-up |
|---|---|---|
| memory lapse | reveal/reconstruct, then next-day review | fresh or independent retrieval |
| unfamiliar/missing | source-grounded explanation or example study | completion, then retrieval/application |
| schema/conceptual hole | explanation + example comparison/elaboration | altered-context explanation/application |
| false belief/confusion | contrast/counterexample after bounded diagnosis | discriminating fresh surface |
| procedure execution | worked step then faded example completion | independent execution |
| method selection | setup-only + move spotting across contexts | independent selection before execution |
| coordination/integration | component localization, then faded whole task | fresh whole-task integration |
| task interpretation | compare prompt representations and restate contract | fresh representation |
| surface/grading fault | quarantine/adjudicate; no learner repair | replacement administration if needed |
| unknown/ambiguous | clarification or admitted diagnostic card | depends on resolved action |

The route is snapshotted before tutor prose is generated. Prose cannot change
the action, target, scaffold level, reveal budget, or follow-up contract.

---

## 7. Instruction, completion, and practice

### 7.1 Pattern ladder

The run selects the nearest useful rung rather than forcing every learner from
the bottom:

```text
source restore / explanation
  -> example_study or example_comparison
  -> example_completion
  -> setup_only / move_spotting
  -> independent_repair
  -> whole_task_integration (when required)
  -> delayed independent target-like practice
```

All rungs are P1 patterns/families with immutable purpose. An instructional
surface cannot become the independent practice card; a practice sibling is
linked at family level.

### 7.2 Stage transition contracts

Each progression-policy version declares observable entry/exit criteria.
Launch rules:

- `example_study` exits after learner acknowledgement/structured comparison,
  not a correctness claim;
- `example_completion` exits after required steps are completed with scaffold
  use recorded; its success does not certify independence;
- `setup_only` exits when method/subgoals are selected without executing the
  whole answer;
- `independent_repair` requires a cold, unhinted response on a non-hard-colliding
  surface;
- `whole_task_integration` requires blueprint integration criteria on a fresh
  whole-task surface;
- assessment eligibility requires delayed independent evidence, no unresolved
  quarantine, and remaining valid reserve.

Thresholds and delay lengths are P0 decision parameters. The policy may choose
another instructional example after failure, but repeated failures on varied
surfaces trigger `needs_review`/P4 expansion telemetry rather than infinite
near-clone practice.

### 7.3 Surface use and rotation

The selected exemplar is the initial semantic/difficulty anchor. P2 practice
uses an admitted reviewed pool — drafted by an LLM within admitted
cards/blueprint bounds and owner-reviewed before pool admission, mirroring
blueprint review (U-028) — or P1 anchored-isomorph minting with:

- one current surface and one cached spare at most by default;
- exact P1 contract/rubric/task-feature/leakage/novelty gates;
- card-level scheduling, never per-surface FSRS;
- lazy rotation after warmth, not a new surface every attempt;
- an orthogonal/delayed next angle after success;
- no assessment-reserved surface in a generation prompt or candidate set;
- no claim of freshness when the P1 ledger is missing/uncertain.

If minting is unavailable, the learner may continue consolidation on an
eligible familiar surface with visibly reduced evidence. The run waits for a
fresh surface before an independent-transfer gate.

### 7.4 Source restoration during learning

Instructional source views use exact blueprint citations through `span_view`.
Showing source content records source and activity exposure and sets the
administration context `source_visible=true`. That work is primed/scaffolded;
it never earns cold evidence.

The learner can always open the source outside a cold administration. Doing so
ends/invalidates that administration's cold status rather than hiding access.

### 7.5 Post-milestone depth transition (automatic activation deferred)

Cold assessment success (or another explicitly declared milestone exit gate)
first appends `depth_milestone_reached` against the exact target version. It
then evaluates one outgoing reviewed edge — one edge per *decision*, then
replan; a run that reaches successive milestones makes a fresh decision at
each one, never a chained climb from a single success event. In this cut the
eligible edge is rendered as a `suggest_next` invitation and activates only
on explicit confirmation. Conditions 1–6 below are specified now, but their
*unprompted* application is deferred with the auto-depth package (U-018);
conditions 2–6 are checked identically before a confirmed activation.
Automatic activation requires all of:

1. active policy is `auto_within_envelope` and the same envelope version the run
   evaluated is still current;
2. the full capability/TaskFeature/support delta is inside that envelope;
3. the exit evidence is reliability-eligible and no quarantine is unresolved;
4. the successor family/cards are already reviewed and admitted;
5. the expected burden fits and the transparent staged policy has positive
   robust value for continuing;
6. when support changes, P0 can append one `authorized_depth_step` and reserve a
   fresh assessment for it in the same transaction.

The P1 transition service applies lineage classification. Surface-only variation
may retain card state; any material capability/task-regime/rubric change forks
with no inherited FSRS stability or certification. Prior facet evidence may
inform a shrunk family-stage prior, but the new card must earn its own reviews.
The run enters `deepening`, activates only the first successor stage, and
replans. It cannot walk another edge from the same success event.

If any condition fails, the reached milestone stays reached. The run maintains,
stops, or shows an editable envelope/authoring suggestion; it never widens the
envelope or downgrades the learner's completed result.

### 7.6 Minimal bidirectional reader dialogue (U-033)

Reading the chapter is part of the golden path, not a prelude to it. This
slice runs on block-level `span_view` and existing question/tutor
persistence — it does not require the P3 annotation layer.

**Learner → AI (Ask).** While viewing source during discovery or
instruction, the learner can ask a span-grounded question in a new `reader`
tutor context, distinct from the existing library/practice/feedback
profiles: it supports comprehension, inquiry, self-explanation, and goal
connection, and it is not Socratic-by-default because there is no attempt
integrity to protect. The learner chooses the answer mode per ask —
`answer_directly` / `help_me_reason` / `ask_me_first` — with
`answer_directly` as the launch default. Persisted per exchange: question,
exact context manifest, answer with validated citations, provider/model
provenance, and the chosen mode. A learner question is never ability
evidence (P0 invariant 10); asking during a cold administration remains
hint-equivalent under the existing practice rules. Exchanges are hidden
during cold activities.

**AI → learner (owner-placed questions).** During blueprint review the owner
places reading questions at section boundaries of the chapter. Each is an
ordinary **instructional-purpose administration** with
`source_visible=true` and a `reading_phase` — no new activity kind — drawn
from the launch patterns `pretest_prime` (before), `self_explanation` /
`example_comparison` (during/after), and `setup_only` (after). Questions
render at boundaries only, are always skippable, and a skip is an
interaction-policy signal, never low-ability evidence. There is no `ask_now`
planner and no density policy in this cut (U-017@v3): placement is a
reviewed, static part of the blueprint.

**Disposition picker.** Every AI reading question, and any Ask exchange the
learner wants to keep, ends in one explicit disposition:

| Disposition | Mechanism |
|---|---|
| `comprehension_only` | logged exchange; never resurfaces |
| `check_once_later` | one single-use diagnostic-purpose cold check, then retire unless it reveals a problem |
| `keep_developing` | commit-class action: creates/extends the run's commitment (or proposes a new family) |
| `reference_only` | source citation + exchange preserved; no practice |

No reading interaction creates a commitment silently; `keep_developing` is
the only commit-class path.

**Evidence semantics.** Formative reading answers mint a replay-derived
routing prior only: it may reorder triage candidates and scaffold choices
inside the U-027 decision-aid channel (registered `heuristic`) and seed
candidate hypotheses, and it is superseded by the first cold observation on
the same target. It never touches posteriors, FSRS state, or certification.
AI answers append exposure per P1 §4.1 — surfaces whose cues an explanation
revealed are warm, and the assessment reserve's leakage gates see that
exposure.

**Events.** Reader dialogue logs on the P0 `interaction_events` envelope:
`reader_question_presented`, `reader_question_skipped`,
`reader_answer_submitted`, `learner_question_asked`,
`reader_answer_mode_set`, `reader_disposition_chosen`,
`reader_source_restored`. These are the live signals the P3 reader and the
P4 timing shadow will consume.

---

## 8. Fresh held-out assessment

### 8.1 Reservation

Before baseline or instruction, reserve one assessment-purpose surface that:

- maps to the reviewed target distribution and rubric;
- pins the confirmed P0 goal-contract version/support hash;
- is not a selected exemplar, diagnostic/practice surface, shared stimulus,
  solution-recipe clone, or other P1 hard collision;
- has no unresolved leakage or extraction-health issue;
- is never included in authoring/generation context after reservation;
- is atomically rechecked against the global exposure ledger before render.

The old exam pool remains a compatibility view. The P0/P1 surface reservation
is authoritative.

### 8.2 Administration

Assessment is cold relative to the pinned terminal conditions. The
administration snapshot includes all tool/time/open-book conditions, rubric,
grader calibration, surface/card hashes, and target pin. Feedback and source
restore are hidden until response submission and grade commitment.

P0 reliability-aware certification determines the result. The run must expose:

- point/interval and effective evidence mass;
- criterion/capability coverage;
- grader/calibration status and any review state;
- exact target-contract version and covered support;
- why the surface counted as fresh;
- whether the result is provisional, certified for that sample, or
  insufficient.

One success does not certify unsupported target cells. One failure says the
sampled terminal performance was not demonstrated; it does not erase earlier
component evidence.

### 8.3 Burn and follow-up

- render consumes pristine assessment status;
- success permanently consumes the assessment surface;
- failure before feedback still records terminal failure;
- feedback reveal permanently makes it ineligible for pristine assessment;
- after feedback, a separately minted/linking practice-family successor may
  use the task for learning, with shared familiarity intact;
- support-changing goal-contract successor marks the old reserve
  unrepresentative for the new version. An authorized depth transaction may
  reserve a distinct fresh successor surface atomically; it never retargets,
  refreshes, or reuses the old reserve;
- ambiguous/misgraded assessment is quarantined and adjudicated under P0;
  replacement assessment uses a different fresh surface.

### 8.4 Post-attempt restoration

After the grade is committed (or the learner explicitly gives up), show:

- source neighborhoods tied to missed/strong criteria;
- the selected exemplar comparison;
- learner interpretation/annotation when P3 data exists;
- a separate “what changed since baseline” boundary view;
- the achieved milestone, active envelope, and exact next reviewed edge;
- next action: a one-tap confirmation of the reviewed inside-envelope edge
  when authorized and feasible (automatic activation deferred, U-018),
  otherwise maintain, repair, suggest, pause, or stop.

Restoration is an instructional event after measurement. It cannot modify the
assessment observation or continue its measurement segment.

---

## 9. Services and product contract

Required service boundaries:

- discover exercise candidates within exactly one source unit;
- draft/review/version a TaskBlueprint;
- preview and atomically confirm exemplar + goal contract + commitment + depth
  policy/envelope + assessment reserve;
- start/resume/stop a golden-path run;
- open/close baseline episode and render the target boundary view;
- append failure triage and resolve a reason-specific route;
- select/advance a pattern stage under explicit criteria;
- record milestone attainment and commit/suggest one depth edge through the P1
  transition service;
- validate/mint/rotate the bounded practice pool;
- validate/open/submit/burn assessment;
- restore source context and produce the final receipt;
- answer a span-grounded reader Ask in the `reader` tutor context with the
  learner's chosen answer mode, and record its exposure and events (§7.6);
- present an owner-placed reading question as a source-visible instructional
  administration and record its disposition;
- record an affect tap on any activity and apply its commitment-level
  semantics (pause / retire / burden edit) mid-run;
- retire a card/family or change commitment disposition without leaving run
  state inconsistent.

Minimum UI/sidecar surface:

1. chapter exercise picker;
1a. chapter reading view (block-level span view) with the Ask box,
   answer-mode toggle, owner-placed boundary questions, and the
   four-disposition picker (§7.6);
2. “tasks like this” blueprint/depth-envelope review and one-time confirmation;
3. short baseline with visible cap and deferred feedback;
4. one-at-a-time instruction/practice workspace with stage explanation;
5. delayed-check/assessment readiness screen;
6. cold assessment;
7. restoration, boundary-diff, achieved-milestone, and next-depth screen;
8. persistent resume/pause/stop controls.

Every activity screen answers, without exposing cold cues:

```text
Why this now?
Is this teaching, practice, diagnosis, or assessment?
What can this result update?
How much remains in this run?
```

No screen describes a heuristic boundary as a personal deficit. Use
relationship/context phrasing: “not yet demonstrated on an altered-context
setup task,” not “you are weak at method selection.”

The affect tap (P0 capture, U-010) is available on every activity screen,
optional and never interrupting. P2 wires its commitment-level semantics:
`not worth my attention` edits the commitment/burden contract and is never
read as low ability; repeated `felt rote` on a family routes to the
retire/redesign flow (`needs_review`); pause/retire actions apply without
leaving run state inconsistent. The `auto_within_envelope` → `suggest_next`
auto-downgrade *enforcement* is deferred with the auto-depth package
(U-011/U-018); the signals it will consume are captured live from this phase
onward.

---

## 10. Migration, rollout, and failure behavior

### 10.1 Additive rollout

P2 is enabled per goal/run behind an explicit schema/projection capability
check. It does not backfill all existing goals or rewrite all task blueprints.

For a selected legacy chapter:

1. reuse current source revision/unit/inventory rows;
2. import the chosen synthesized blueprint into an immutable reviewed version;
3. map existing reviewed diagnostic items through P1 probe adapters;
4. map selected compatible PracticeItems into fixed P1 cards/surfaces;
5. require a new P0 confirmed goal contract and a fresh assessment reserve;
6. leave existing non-P2 scheduler/remediation flows unchanged.

### 10.2 Coexistence

- the global scheduler excludes administrations/surfaces reserved by an active
  P2 run;
- P2 due follow-ups may appear in Today but retain their run transition id;
- legacy remediation episodes remain readable and are not converted mid-run;
- a learner may pause P2 and do unrelated practice, but P1 exposure can make
  the held-out reserve invalid; revalidation then routes to `needs_review`;
- goal edits never mutate an active diagnostic episode or standing reserve.

### 10.3 Failure behavior

- unresolved source/exemplar locator -> cannot confirm; preserve draft;
- low block extraction health -> require original-region review before
  blueprint approval;
- blueprint/rubric review failure -> preserve proposal, no active run;
- no admitted diagnostic card -> skip/limit measurement and choose only an
  intervention valid across plausible causes, or route `needs_review`;
- grader uncertainty/quarantine -> pause consequential transition; allow
  non-dependent instruction if safe;
- no fresh assessment -> `practice_only`, no terminal claim;
- assessment collision before render -> release unseen reservation and require
  explicit fresh replacement; never substitute silently;
- assessment collision after render -> retain administration and burn; label
  claim invalid if collision predates render;
- generator outage -> serve admitted cache/familiar consolidation or pause;
- source view opened during cold work -> append contamination event and remove
  cold eligibility, never conceal it;
- time/burden cap reached -> persist boundary and offer pause/stop; do not force
  completion;
- contract support successor -> progression follows/logs head, but assessment
  remains about its pinned older version and is labeled accordingly;
- stale/outside envelope, missing reviewed successor, or non-positive robust
  continuation value -> keep milestone success, do not auto-activate, and show
  maintain/stop/suggestion;
- deeper support without an atomically reservable fresh assessment -> preserve
  `practice_only` suggestion; do not claim the old reserve proves the new head.

---

## 11. Implementation order

1. Add immutable TaskBlueprint versions/review events and one-unit validation.
2. Add atomic exemplar-confirmation transaction with P0 contract v1, P1
   commitment/depth envelope/families, and assessment reserve.
3. Add golden-path run/events/projector and exact resume semantics.
4. Build the reviewed diagnostic pack adapter and bounded baseline entry/exit.
5. Add failure-triage events, route table, and typed transition snapshots.
6. Register/validate the P2 pattern ladder and stage-transition contracts.
7. Wire P1 card scheduling, rotation, delayed follow-up, and source restoration.
8. Cut assessment reservation/administration over to P0/P1 burn and
   reliability-aware certification.
9. Add one-edge post-milestone depth transaction plus successor reserve/lineage
   enforcement.
10. Add boundary/restoration/depth UI and full decision/measurement receipt.
11. Run planted-learner, crash/retry, leakage, migration, and end-to-end suites.

The assessment surface must be reserved before any test run that exercises
instruction/practice; otherwise the test is not evidence that held-out
protection works.

---

## 12. Test and acceptance contract

### 12.1 Contract and scope

- mixed chapters or incoherent task families cannot confirm;
- exemplar confirmation atomically mints goal-contract v1 and pins a fresh
  reserve;
- a post-confirmation material edit appends a successor;
- probe episode and reserve keep their own pins while progression logs head;
- confirmation pins the chosen depth policy/envelope and reviewed first edge;
- the selected exemplar can never be labeled held out;
- solution content never enters a cold learner context or reserved-surface
  generation context.

### 12.2 Baseline and triage

- baseline uses only pre-authored admitted cards and stops within 2–4 visible
  administrations;
- ordinary practice cannot update its posterior;
- starting instruction closes the measurement segment;
- planted memory lapse, unfamiliarity, conceptual hole, false belief,
  procedure failure, method-selection failure, integration failure, bad
  surface, and uncertain cause take the intended route;
- a quarantined/misgraded response never becomes a learner deficit;
- when plausible hypotheses imply the same repair, the episode stops and uses
  that repair instead of asking another low-value question.

### 12.3 Learning ladder

- a capable planted learner skips unnecessary instruction;
- instructional success never grants unassisted certification or applies a
  lapse;
- completion records scaffold use and requires later independent work;
- method-selection repair uses setup/move spotting rather than blindly
  repeating procedure execution;
- integration evidence comes only from a whole-task blueprint component;
- repeated failures on varied surfaces terminate into review/expansion
  telemetry rather than infinite practice;
- delayed follow-up is independent/fresh and linked to the original lapse.

### 12.3.1 Depth progression

- `hold_at_target` records milestone success and cannot activate an edge;
- `suggest_next` renders the reviewed edge without activating it, and one
  explicit confirmation activates exactly one edge and replans;
- `auto_within_envelope` is recorded as standing authorization but served as
  `suggest_next` in this cut; unprompted activation is a deferred (U-018)
  acceptance and must not occur;
- stale/outside-envelope, multi-edge, unreviewed, over-budget, quarantined, and
  non-positive-value transitions do not activate;
- a material deeper card forks with no FSRS/certification inheritance, while
  the reached predecessor milestone remains achieved;
- terminal-support growth appends one P0 `authorized_depth_step` and uses a
  distinct fresh reserve; the predecessor reserve remains pinned/burned.

### 12.3.2 Reader dialogue

- a learner question during reading changes no posterior, FSRS state, or
  certification projection under replay;
- an owner-placed reading question records an instructional administration
  with `source_visible=true` and a `reading_phase`, and its outcome mints no
  unassisted-certification evidence;
- an AI answer that reveals a reserved surface's cues (hard-group collision)
  invalidates that reserve exactly as any other exposure;
- each of the four dispositions produces its declared mechanism and nothing
  else: `check_once_later` yields exactly one single-use diagnostic
  administration then retires; only `keep_developing` creates or extends a
  commitment; skipping a question logs `reader_question_skipped` and changes
  no learner-state estimate;
- the routing prior is visible in the triage decision aid's trace as a
  registered `heuristic` input and is superseded in replay by the first cold
  observation on the same target;
- with the reader dialogue disabled or unavailable, the golden path still
  completes end to end.

### 12.4 Rotation and leakage

- card state survives admitted surface rotation;
- current + spare cache remains bounded;
- familiar practice is never reported as fresh evidence;
- global exposure under any purpose can invalidate the reserve;
- hard-colliding assessment is refused before render;
- purpose-specific families cannot transition roles;
- generator outage does not corrupt or block an in-flight response.

### 12.5 Assessment

- assessment revalidates target pin, support, and exposure atomically;
- feedback remains hidden until submission/grade commitment;
- success and feedback-on-failure follow P0 burn rules;
- a failed assessment can seed only a separate practice-family successor;
- reliability/quarantine affects certification exactly as specified in P0;
- result claims only sampled/covered target support;
- restoration happens after measurement and cannot change its observation.

### 12.6 Resume and audit

Inject failure after every write boundary. Retrying must yield exactly one:

- run transition;
- administration/render exposure;
- response/grade/observation;
- schedule update;
- assessment burn;
- source restoration event.

Rebuilding from events after corrupting every run/state cache must reproduce
the same state and next feasible action.

### 12.7 End-to-end golden acceptance

On a reviewed fixture chapter and one exercise family:

1. learner selects two representative exercises and confirms the blueprint;
2. system reserves one unseen sibling assessment;
3. a 2–4 item baseline localizes a planted method-selection boundary;
4. setup-only and move-spotting instruction/practice occur on distinct
   surfaces;
5. a delayed fresh independent practice succeeds;
6. the held-out target-like assessment is administered cold;
7. source neighborhood and boundary diff are restored afterward;
8. the original milestone is recorded as reached, then the reviewed
   transfer/span edge is rendered as a `suggest_next` invitation; one
   explicit confirmation activates it and reserves fresh successor support
   when required (unprompted activation stays deferred with U-018 and must
   not occur);
9. the learner may pause, shrink/disable the envelope, or continue the newly
   active stage;
10. the final receipt traces every version, envelope, milestone, lineage,
   exposure, decision, grade, and
   evidence contribution.

Repeat with planted unfamiliar, conceptual-hole, coordination, misgrade, and
surface-collision profiles. Acceptance fails on any hidden role transition,
false novelty, purpose-blind FSRS update, unpinned terminal claim, or
declarative heuristic diagnosis, outside-envelope or unconfirmed depth
activation, recursive depth climb, lost milestone success, or
FSRS/certification inheritance across a fork.

### 12.8 Operational budgets

- run start performs no whole-library synthesis;
- no LLM call is required to open an already admitted activity;
- candidate generation happens off the answer-submission hot path;
- the visible baseline cap and total burden cap are enforced from persisted
  events;
- a normal restart can resume an in-flight run without reloading unrelated
  source units;
- migration and fixture setup are idempotent.

---

## 13. Launch defaults and explicit assumptions

- P2 starts with owner-reviewed blueprints/cards and a reviewed bounded surface
  pool; automation earns authority later.
- The live run policy is intentionally narrow and transparent. It is not the
  P4 global controller and produces no claim that weighted selector quality has
  improved.
- Two-to-four baseline items, stage thresholds, delay windows, retry cadence,
  and burden caps are decision parameters with visible calibration status.
- Bounded heuristic authority permits a cautious best-supported route; it does
  not permit categorical diagnoses or readiness statements under wide
  intervals.
- The one held-out assessment estimates performance on one frozen target
  distribution sample. Stronger certification may require later independent
  surfaces under P0's contract.
- P3 annotation restoration is additive. P2 always restores cited source
  neighborhoods and includes annotations only when they already exist.
- Reader-dialogue defaults (§7.6): answer mode `answer_directly`; owner-placed
  questions at section boundaries only, reviewed with the blueprint, target
  density ≈1 per major section (owner-tunable, never auto-inserted); default
  disposition when the learner walks past the picker is `comprehension_only` —
  the system never escalates an unanswered picker into an obligation.
- End-of-chapter commitments visibly recommend `suggest_next` in this cut;
  `auto_within_envelope` remains selectable as standing authorization (served
  as `suggest_next` until the auto-depth package, U-018) and `hold_at_target`
  remains first-class. The learner confirms, narrows, or changes the policy
  once on the blueprint screen.
- P2 activates at most one reviewed inside-envelope edge per *decision* and
  then replans — never a chained climb; each later milestone is a fresh
  decision. In this cut every activation requires one explicit confirmation.
  It never expands the envelope itself, crosses a target family/chapter, or
  authors a protocol on the hot path.

---

## 14. Change log

- **2026-07-20 — C3 narrow tier-one signature auto-route, PENDING OWNER
  CONFIRMATION.** The ≥0.85-confidence error-signature route (§6.1) previously
  auto-committed on any high-confidence signature, beyond the spec's three decisive
  triggers (quarantine, `dont_know`-on-never-exposed, expired trace). It now stays
  tier-one ONLY when the P0-supplied provisional reason distribution is concentrated
  on a single dominant signature — one signature carries ≥ `TRIAGE_DOMINANCE_SHARE`
  (new registered `heuristic` param, default 0.75) of the distribution mass; a diffuse
  supplied distribution downgrades it to a tier-two decision aid with named
  alternatives. A bare high-confidence signature with no supplied distribution still
  routes tier-one (cheap to reverse). The three decisive triggers are unchanged.
- **2026-07-20** — **P2 implemented.** The narrow exemplar-driven golden path
  landed in code: migrations **081–087** (`081_task_blueprints`,
  `082_golden_path_runs`, `083_diagnostic_pack_and_triage`, `084_pattern_ladder`,
  `085_surface_pool`, `086_reader_dialogue`, `087_golden_path_artifacts`) plus the
  composed services (`task_blueprints`, `golden_path_confirm`, `golden_path_run`,
  `diagnostic_pack`, `failure_triage`, `pattern_ladder`, `surface_pool`,
  `golden_path_assessment`, `golden_path_restoration`, `reader_dialogue`) and the
  deterministic `golden_path_fixture`. The §12–§13 acceptance contract is covered
  by the track suites plus `tests/test_p2_acceptance.py` (the continuous 10-step
  fixture journey, event-replay equivalence, fault-injection completeness, and
  planted-learner routing divergence) and `tests/test_p2_leakage_suite.py` (the
  consolidated leakage suite). Composition-smell audit result held: **no new
  posterior, FSRS writer, or certification path** — every measurement primitive
  composes a landed P0/P1 service.
- **2026-07-20 — §A memo defaults adopted, PENDING OWNER CONFIRMATION.** Two
  recommended defaults from the §A owner-decision memo are in force and cheap to
  reverse (each registered `heuristic` with a sensitivity certificate):
  - **A.1 routing-prior projection** — derive-on-read from `interaction_events`
    (`routing_prior_projection_v1`), no stored prior table; structural
    supersession by the first cold observation; single knob
    `routing_prior_halflife_days` (7d).
  - **A.2 reader context-manifest bounds** — `reader_context_manifest_v1` carries
    span(s) in view + question + goal invariants + same-span history + answer mode,
    and NEVER the ability/posterior estimate, an assessment-reserved surface's
    statement/rubric, or a cold administration's in-flight response.
- **2026-07-20 — NAMED DEFERRALS (UI rows the UI track skipped).** These P2 UI
  surfaces are deferred with explicit targets; the underlying services + RPCs are
  landed, so each is a UI-only follow-up:
  - **Library-side exemplar picker** — needs a source/library discovery RPC
    (`blueprint.discover_candidates` surfacing candidate exemplars into the library
    view); deferred to a discovery-RPC follow-up. Confirmation itself is shipped.
  - **Owner-review screens** (blueprint / diagnostic-pack / pool / depth-edge
    review) — the review artifacts + admission gates are code; the interactive
    review screens are deferred, driven for now via the **CLI / `waiting_for_input`
    artifact flows**.
  - **Interactive practice workspace** — an **informational** run/stage view
    shipped; the one-at-a-time interactive instruction/practice workspace with
    inline AffectTap is deferred to a practice-workspace follow-up.

### 2026-07-20 — library exemplar picker SHIPPED (deferral closed)

- `blueprint.discover_candidates` + `blueprint.compose_draft` sidecar RPCs landed
  (`services/golden_path_compose.py`): discovery lists each learning object's
  active practice items as the exemplar pool (with per-item freshness); compose
  projects a picker selection (anchors + one held-out sibling) into a §3.2
  template blueprint spec + matching §1.2 contract body, registered as a DRAFT
  and routed through the existing owner review -> atomic confirmation unchanged.
- Desktop `GoldenPathSetup` (Golden tab front door): goal -> learning object ->
  anchors/held-out -> compose -> three-check owner review -> the ONE atomic
  confirmation with a real `confirmInput` — `ExemplarConfirmDialog` now receives
  `blueprintVersionId` + `confirmInput` and treats `reviewed` as confirmable
  (activation happens inside the confirm transaction). The fixture surface
  survives only behind an explicit "open offline demo" toggle.
- Cold-assessment workspace on the live run screen: `golden_path.assess_open`
  now returns the surface's item prompt + rubric ceiling (never the expected
  answer); the screen opens the cold administration, locks the learner's answer
  before revealing, self-grades, and submits through `assess_submit`.
- Proven end-to-end on a plain (non-fixture) vault:
  `tests/test_sidecar_blueprint_picker.py` walks discover -> compose -> review ->
  confirm -> certifying run over serve().
- STILL DEFERRED: the interactive instruction/practice ladder + triage + pool
  workspace on the live screen (informational rendering only).
