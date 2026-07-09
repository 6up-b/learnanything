-- Two-phase tutor Q&A persistence. The question row is now inserted as
-- 'pending' BEFORE the provider call, then updated to 'answered' (with the
-- answer, classification, and facets) or 'failed'. A learner question is
-- elicitation evidence about their knowledge state regardless of whether the
-- tutor managed to answer, so a provider failure must still leave the
-- question on record. Existing rows were all written post-answer, so the
-- column backfills as 'answered'.
ALTER TABLE question_events ADD COLUMN answer_status TEXT NOT NULL DEFAULT 'answered'
  CHECK (answer_status IN ('pending', 'answered', 'failed'));
