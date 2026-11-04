"""RO0 row 12 (spec_router_objective_v1 §4): decision-to-next-state links, with censoring.

The audit (docs/reviews/router-ro0-logging.md): every link already has its id, so nothing is added.

* decision to action: ``attention_blocks.decision_ref``, ``plan_presentations.router_decision_id``,
  ``router_decisions.scheduler_slate_id`` (an offer), ``router_decision_bindings`` (FG1's itemless decision);
* uptake: ``practice_attempts.plan_presentation_id`` and, for an offer, ``scheduler_slate_id``;
* rejection: the block's ``item_skipped`` and ``item_displaced`` events, a pick's ``parent_decision_id``;
* next decision and return: the ledger's own order, and ``sessions``.

This is a read and not a ``CREATE VIEW``, where the spec said a plain view: SQLite re-resolves every view when a table is
renamed, so a view over ``router_decisions`` makes the rebuild its migrations use (202, 236: create, copy, drop, rename)
fail with "error in view". Nothing serving reads it.
"""

from __future__ import annotations

from typing import Any

VERSION = "decision_trajectory_v1"

#: One row per decision, oldest first. ``censored`` names why a link is not known yet: no later decision, or no later
#: session to return in.
TRAJECTORY_SQL = """
WITH decisions AS (
  SELECT d.id AS decision_id, d.decision_kind, d.session_id, d.created_at AS decided_at, d.chosen_ref,
         d.chosen_practice_item_id, d.learner_pick, d.propensity_kind, d.parent_decision_id, d.scheduler_slate_id,
         LEAD(d.id) OVER (ORDER BY d.created_at, d.id) AS next_decision_id,
         LEAD(d.created_at) OVER (ORDER BY d.created_at, d.id) AS next_decision_at
    FROM router_decisions d
)
SELECT t.*,
       (SELECT b.id FROM attention_blocks b WHERE b.decision_ref = t.decision_id ORDER BY b.created_at, b.id LIMIT 1) AS block_id,
       (SELECT COUNT(*) FROM plan_presentations p WHERE p.router_decision_id = t.decision_id) AS presentations,
       (SELECT MIN(p.served_at) FROM plan_presentations p WHERE p.router_decision_id = t.decision_id) AS first_served_at,
       (SELECT COUNT(*) FROM plan_presentations p JOIN practice_attempts a ON a.plan_presentation_id = p.id
         WHERE p.router_decision_id = t.decision_id) AS attempts_on_presentations,
       (SELECT COUNT(*) FROM practice_attempts a WHERE t.scheduler_slate_id IS NOT NULL
           AND a.scheduler_slate_id = t.scheduler_slate_id) AS attempts_on_offer,
       (SELECT COUNT(*) FROM attention_block_events e JOIN attention_blocks b ON b.id = e.block_id
         WHERE b.decision_ref = t.decision_id AND e.kind IN ('item_skipped', 'item_displaced')) AS items_rejected,
       (SELECT o.arm FROM decision_objectives o WHERE o.decision_id = t.decision_id) AS objective_arm,
       (SELECT MIN(s.started_at) FROM sessions s
         WHERE s.started_at > COALESCE((SELECT o.ended_at FROM sessions o WHERE o.id = t.session_id), t.decided_at)
       ) AS next_session_started_at,
       CASE WHEN t.next_decision_id IS NULL THEN 'no_later_decision' END AS next_decision_censored,
       CASE WHEN (SELECT MIN(s.started_at) FROM sessions s
                   WHERE s.started_at > COALESCE((SELECT o.ended_at FROM sessions o WHERE o.id = t.session_id), t.decided_at)
                 ) IS NULL THEN 'no_later_session' END AS return_censored
  FROM decisions t
 ORDER BY t.decided_at, t.decision_id
"""


def rows(connection: Any) -> list[dict[str, Any]]:
    """Every decision's links, read-only."""

    return [dict(row) for row in connection.execute(TRAJECTORY_SQL)]


__all__ = ["TRAJECTORY_SQL", "VERSION", "rows"]
