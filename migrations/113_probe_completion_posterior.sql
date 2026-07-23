-- Persist the completion-time hypothesis posterior on the probe episode.
-- The live posterior is replay-derived (never stored), so downstream consumers
-- (depth_rungs entry selection) had no cheap way to read "what did the
-- diagnostic conclude". Snapshot it at completion; replay stays authoritative
-- for any in-flight episode.
ALTER TABLE probe_episodes ADD COLUMN completion_posterior_json TEXT;
