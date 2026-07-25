-- Diagnosis adjudication store (spec_diagnostic_augmentation_v1.md §2 A4).
--
-- `spec_causal_attribution_v1.md` §12 lists "first-divergence accuracy vs
-- adjudication" and "abstention precision" among its primary metrics, and
-- nothing produces either. Grade-POINTS adjudication exists
-- (`grade_adjudications`, migration 001/§4.4); diagnosis adjudication does not.
-- This table is the missing producer: the eval set, the few-shot pool, and the
-- eventual fine-tune set. Every attempt graded before it exists is a labelled
-- example lost permanently, which is why it lands before the rest of Phase A.
--
-- APPEND-ONLY, like `causal_hypotheses` (118). A re-adjudication appends a
-- successor naming its predecessor in `supersedes_id`; it never rewrites the
-- verdict that was actually recorded at the time. Two partial UNIQUE indexes
-- keep the supersession chain linear and single-headed per attempt.
--
-- WHY THIS IS NOT A PROJECTION OVER `causal_attribution_reports` (the §5.6
-- typed `doesnt_fit` contest): the §2 producer/confirmer matrix lists "learner
-- confirmation" and "adjudication" as SEPARATE confirmation channels, and
-- `SUPPORT_AUTHORITIES` separates `learner_confirmed` from `adjudicated`. A
-- contest is the learner's bounded, typed report; it carries no anchor and no
-- repair, so two of A4's four required fields would be NULL on every laundered
-- record and first-divergence accuracy would be uncomputable. Contests are
-- instead the highest-yield QUEUE for adjudication: `queue_reason` records how
-- each record was surfaced and `learner_report_id` links the contest that
-- prompted it, so the eval set's selection bias is auditable rather than
-- invisible (§3 B4 agreement is meaningless over a silently contest-only set).

CREATE TABLE diagnosis_adjudications (
  id TEXT PRIMARY KEY,

  -- (1/4) The attempt.  No FK: goal-series rewind can remove attempt
  -- projections and the adjudication record must survive as immutable audit,
  -- exactly as `causal_hypotheses.attempt_id` does.
  attempt_id TEXT NOT NULL,

  -- The exact system output being judged.  A verdict that cannot say WHICH
  -- diagnosis it judged is not an eval record once the receipt changes, and
  -- `attempt_debug_payloads` is replay-rebuildable.
  diagnosis_receipt_id TEXT NOT NULL,

  -- (4/4) The verdict on what the system chose.
  --
  -- A4 names five values.  `should_not_have_abstained` is a SIXTH, added
  -- deliberately: the five have no value for a FALSE abstention, so
  -- abstention precision = correctly_abstained / (all abstentions) would be
  -- 1.0 by construction and the metric §12 asks for could never fail.
  -- Standing constraint 2 / §11 ("no new enum without an abstention arm and a
  -- two-tailed fill-rate watch") requires both tails to be representable.
  -- The enum is CHECK-constrained on an append-only table, so it calcifies.
  verdict TEXT NOT NULL CHECK (verdict IN (
    'correct',
    'wrong_anchor',
    'wrong_repair',
    'should_have_abstained',
    'correctly_abstained',
    'should_not_have_abstained'
  )),

  -- What the system DID, snapshotted at adjudication time.  This is what makes
  -- the abstention confusion matrix computable in SQL without re-deriving a
  -- receipt that replay may have rebuilt:
  --   TP = system_abstained=1 AND verdict='correctly_abstained'
  --   FP = system_abstained=1 AND verdict='should_not_have_abstained'
  --   FN = system_abstained=0 AND verdict='should_have_abstained'
  --   TN = system_abstained=0 AND verdict IN (correct, wrong_anchor, wrong_repair)
  system_abstained INTEGER NOT NULL CHECK (system_abstained IN (0, 1)),

  -- (2/4) The adjudicated first-divergence anchor, in the `FirstDivergence`
  -- shape (codex/schemas.py) so it compares directly against the receipt's
  -- `divergence_anchors.first_observable_divergence`.
  adjudicated_anchor_json TEXT,
  adjudicated_anchor_kind TEXT CHECK (
    adjudicated_anchor_kind IS NULL
    OR adjudicated_anchor_kind IN (
      'span', 'between_spans', 'missing_required_step', 'whole_answer', 'none'
    )
  ),

  -- (3/4) The adjudicated minimal repair.  NL first (structure-late, §2): the
  -- prose is always admissible; the repair-class id is recorded only when the
  -- adjudicated repair matches one the episode actually offered, which is what
  -- `repair_class_match_rate` (§3 B5) scores against.
  adjudicated_repair_md TEXT,
  adjudicated_repair_class_id TEXT,

  -- How this attempt reached the adjudicator.  Required for B4: an eval set
  -- drawn only from learner contests is ~100% negative verdicts and its
  -- agreement with the planted set means nothing.
  queue_reason TEXT NOT NULL CHECK (queue_reason IN (
    'learner_contest',
    'system_abstention',
    'anchor_disagreement',
    'incomplete_repair_mapping',
    'sampled',
    'manual'
  )),

  -- Provenance only.  The contest's typed reason is a PRIOR the CLI displays;
  -- it never sets the verdict (that would launder bounded-trust learner
  -- evidence into the `adjudicated` support authority, which §2 forbids).
  learner_report_id TEXT REFERENCES causal_attribution_reports(id),

  -- Full-authority sources only.  `learner_clarification` is deliberately
  -- absent: grade adjudication gives it a bounded trust weight < 1, and a
  -- bounded-trust label is not usable as eval ground truth.
  adjudicator_source TEXT NOT NULL CHECK (adjudicator_source IN (
    'human_owner', 'independent_expert', 'deterministic_verifier'
  )),
  rationale TEXT,

  -- Version pins.  Sliced by §3 B5 ("reported per prompt version and per
  -- model"); all four of these change within a single Phase A/C week, and a
  -- verdict that cannot name the version it judged is not reusable afterwards.
  decision_policy_version TEXT,
  repair_policy_version TEXT,
  grading_prompt_version TEXT,
  grader_model TEXT,
  receipt_schema_version INTEGER,

  -- The rest of the manifest plus the system's own anchor/repair choice, so a
  -- record scores without re-reading a mutable debug payload: grader provider
  -- and revision, grading agent run, mechanism taxonomy version + hash,
  -- support authority, contamination class, selection basis, resolution
  -- counts, plausible hypothesis ids, and the system anchor/repair.
  system_snapshot_json TEXT NOT NULL,

  supersedes_id TEXT REFERENCES diagnosis_adjudications(id),
  created_at TEXT NOT NULL,

  -- The verdict vocabulary partitions on what the system did.  Rejecting the
  -- crossed cells is what stops "the system abstained AND its anchor was
  -- wrong" from being recorded as `wrong_anchor` and vanishing from the
  -- abstention denominator.
  CHECK (
    (system_abstained = 1
     AND verdict IN ('correctly_abstained', 'should_not_have_abstained'))
    OR
    (system_abstained = 0
     AND verdict IN ('correct', 'wrong_anchor', 'wrong_repair',
                     'should_have_abstained'))
  ),

  -- A record that scores anchor accuracy must carry an anchor.
  -- `should_have_abstained` and `correctly_abstained` are exempt: the whole
  -- claim there is that the vocabulary cannot name the cause.
  CHECK (
    verdict NOT IN ('correct', 'wrong_anchor', 'wrong_repair',
                    'should_not_have_abstained')
    OR adjudicated_anchor_json IS NOT NULL
  ),

  -- `wrong_repair` asserts the system's repair was wrong; without the repair
  -- that should have been chosen the record scores nothing.
  CHECK (
    verdict != 'wrong_repair'
    OR adjudicated_repair_md IS NOT NULL
    OR adjudicated_repair_class_id IS NOT NULL
  )
);

CREATE INDEX idx_diagnosis_adjudications_attempt
  ON diagnosis_adjudications(attempt_id, created_at, id);
CREATE INDEX idx_diagnosis_adjudications_receipt
  ON diagnosis_adjudications(diagnosis_receipt_id);
CREATE INDEX idx_diagnosis_adjudications_verdict
  ON diagnosis_adjudications(verdict, created_at);
-- The B5 scoreboard slice: per prompt version and per model.
CREATE INDEX idx_diagnosis_adjudications_versions
  ON diagnosis_adjudications(grading_prompt_version, grader_model, created_at);
-- The B4 selection-bias slice.
CREATE INDEX idx_diagnosis_adjudications_queue_reason
  ON diagnosis_adjudications(queue_reason, created_at);

-- Exactly one root per attempt: a second opinion must name the verdict it
-- revises rather than forking a second head.
CREATE UNIQUE INDEX uq_diagnosis_adjudications_root
  ON diagnosis_adjudications(attempt_id)
  WHERE supersedes_id IS NULL;
-- ...and the chain stays linear.
CREATE UNIQUE INDEX uq_diagnosis_adjudications_supersedes
  ON diagnosis_adjudications(supersedes_id)
  WHERE supersedes_id IS NOT NULL;

CREATE TRIGGER diagnosis_adjudications_no_update
BEFORE UPDATE ON diagnosis_adjudications
BEGIN
  SELECT RAISE(ABORT, 'diagnosis adjudications are append-only');
END;

CREATE TRIGGER diagnosis_adjudications_no_delete
BEFORE DELETE ON diagnosis_adjudications
BEGIN
  SELECT RAISE(ABORT, 'diagnosis adjudications are append-only');
END;
