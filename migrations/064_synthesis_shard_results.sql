-- Durable per-shard synthesis checkpoints. A completed shard's model output is
-- persisted keyed by its full input identity (prompt version, provider/model,
-- brief, registry, exam profile, shard inventories, shard position), so a
-- retried synthesis reuses finished shards at zero model cost instead of
-- re-paying every call. Keyed by content, not manifest hash: retries with
-- revised token ceilings mint a new manifest but keep identical shard inputs.
CREATE TABLE synthesis_shard_results (
  shard_key TEXT PRIMARY KEY,
  manifest_hash TEXT,
  shard_ordinal INTEGER NOT NULL,
  shard_count INTEGER NOT NULL,
  output_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX idx_synthesis_shard_results_manifest
  ON synthesis_shard_results(manifest_hash);
