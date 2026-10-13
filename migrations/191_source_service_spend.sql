-- Canonical sources (spec_source_practice_and_probes_v1.md §7.5; Codex re-review
-- F2): the service's daily money cap (source_service.max_daily_cost_usd) is
-- shared by every process that opens the vault. One row per metered request
-- admitted under it: reserved before the request is sent, inside one
-- BEGIN IMMEDIATE transaction that checks today's total plus the estimate
-- against the cap, so a sidecar and a CLI batch cannot each spend the same
-- allowance; reconciled upward with the request's cost; never refunded
-- while in flight (a crashed process's reservation stays counted). Once the
-- request finished it counts its reported cost (its receipt's), else its
-- reservation. A request that was never sent (another cap refused it) is
-- removed. Subscription requests (Codex, the ChatGPT plan) are never refused
-- by money and reserve nothing here.
CREATE TABLE source_service_spend (
  id TEXT PRIMARY KEY,
  envelope TEXT NOT NULL,
  day TEXT NOT NULL,
  reserved_usd REAL NOT NULL CHECK (reserved_usd >= 0),
  charged_usd REAL NOT NULL CHECK (charged_usd >= 0),
  state TEXT NOT NULL CHECK (state IN ('in_flight', 'settled')),
  process TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX idx_source_service_spend_day ON source_service_spend(envelope, day);
