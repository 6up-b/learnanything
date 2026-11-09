-- Instruct hand-off IH3 (docs/specs/spec_instruct_handoff_v1.md §6): "Something else would help".
--
-- Additive: one new append-only RAW_LEDGER table; no existing table changes.
--
-- router_learner_preferences: what the learner said would help, at one moment, with what the router could have done
-- then. One immutable row per use of the link on the feedback screen, the lesson offer page or a plan boundary, on the
-- desktop or the phone.
--
-- * decision_id: the router decision whose drawn block was waiting when the learner chose (NULL when no draw existed
--   yet: the offered set is then what the plan could produce without forcing one, and offered_json says so).
-- * offered_json: the options shown, as refs, with the router's own probabilities where the decision logged them
--   (NULL where it did not: never a made-up number).
-- * chosen_kind / chosen_ref: the learner's choice (a kind in plain words and the candidate it stands for).
-- * note_md: the learner's optional free text, kept as written.
-- * served_decision_id: the learner_pick decision that served the choice (router_decisions.parent_decision_id names
--   decision_id, so router_outcomes reports the parent as overridden), or the parent's own id when the choice was what
--   the plan had already drawn (an agreement serves nothing new), or NULL when router.log_decisions is off.
--
-- A preference is self-selected: it is a statement of what the learner would take, never evidence of mastery, and no
-- score or scheduler reads it. The table is a capture ledger (the row is the only record of what the learner said, and
-- nothing else holds its replay input), so it is a RAW_LEDGER, never derived, never cleared by a rebuild.
CREATE TABLE router_learner_preferences (
  id TEXT PRIMARY KEY,
  decision_id TEXT REFERENCES router_decisions(id),
  attempt_id TEXT,
  session_id TEXT,
  -- Where the link was used: feedback | offer_page | today, with the phone's prefixed (phone_feedback, phone_today).
  surface TEXT NOT NULL,
  offered_json TEXT NOT NULL CHECK (json_valid(offered_json)),
  chosen_kind TEXT NOT NULL,
  chosen_ref TEXT NOT NULL,
  note_md TEXT,
  served_decision_id TEXT REFERENCES router_decisions(id),
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX router_learner_preferences_decision ON router_learner_preferences(decision_id);
CREATE INDEX router_learner_preferences_session ON router_learner_preferences(session_id, created_at, id);
CREATE INDEX router_learner_preferences_served ON router_learner_preferences(served_decision_id);

CREATE TRIGGER router_learner_preferences_no_update
BEFORE UPDATE ON router_learner_preferences
BEGIN
    SELECT RAISE(ABORT, 'router_learner_preferences is append-only');
END;

CREATE TRIGGER router_learner_preferences_no_delete
BEFORE DELETE ON router_learner_preferences
BEGIN
    SELECT RAISE(ABORT, 'router_learner_preferences is append-only');
END;
