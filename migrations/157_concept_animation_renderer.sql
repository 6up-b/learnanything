-- Concept animations can be produced by a text-to-video model through
-- OpenRouter instead of a local manim render. `renderer` records which path
-- produced (or failed) the row so the inspector adapts its copy;
-- `storyboard_json` keeps the authored shots (prompt, duration, caption, and
-- per-shot job results) and `video_job_ids` the OpenRouter job ids — what a
-- cost lookup or a bug report needs, since jobs are billed on submission.
ALTER TABLE concept_animations ADD COLUMN renderer TEXT NOT NULL DEFAULT 'manim';
ALTER TABLE concept_animations ADD COLUMN storyboard_json TEXT;
ALTER TABLE concept_animations ADD COLUMN video_job_ids TEXT;
