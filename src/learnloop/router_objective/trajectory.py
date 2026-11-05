"""RO0 row 12 (spec_router_objective_v1 §4): decision-to-next-state links, with censoring.

The audit (docs/reviews/router-ro0-logging.md): every link already has its id, so nothing is added.

* decision to action: ``attention_blocks.decision_ref``, ``plan_presentations.router_decision_id``,
  ``router_decisions.scheduler_slate_id`` (an offer), ``router_decision_bindings`` (FG1's itemless decision: its item,
  its probe presentation, its plan presentation, its outcome);
* uptake: ``practice_attempts.plan_presentation_id``, ``probe_presentation_id`` and, for a bound item, an attempt on it
  after the decision; for an offer, ``scheduler_slate_id``. One attempt reached by several links counts once;
* rejection: the block's ``item_skipped`` and ``item_displaced`` events, a pick's ``parent_decision_id``, a binding's
  ``skipped`` or ``abandoned`` outcome. One item rejected twice counts once;
* next decision: the ledger's own order;
* return: the first session to start once the session the action happened in has ended. That session is the decision's
  own, else its block's, presentation's or attempt's: Start builds a plan before it opens a session, so a first decision
  has none of its own, and the session it then opens is its action's and no return. Nothing to say which session it was,
  and the return is censored ``session_unresolved``, never guessed from the clock.

This is a read and not a ``CREATE VIEW``, where the spec said a plain view: SQLite re-resolves every view when a table is
renamed, so a view over ``router_decisions`` makes the rebuild its migrations use (202, 236: create, copy, drop, rename)
fail with "error in view". Nothing serving reads it.
"""

from __future__ import annotations

from typing import Any

VERSION = "decision_trajectory_v1"

#: One row per decision, oldest first. ``*_censored`` names why a link is not known yet: no later decision, no later
#: session to return in, or no session the action can be placed in.
TRAJECTORY_SQL = """
WITH decisions AS (
  SELECT d.id AS decision_id, d.decision_kind, d.session_id, d.created_at AS decided_at, d.chosen_ref,
         d.chosen_practice_item_id, d.learner_pick, d.propensity_kind, d.parent_decision_id, d.scheduler_slate_id,
         LEAD(d.id) OVER (ORDER BY d.created_at, d.id) AS next_decision_id,
         LEAD(d.created_at) OVER (ORDER BY d.created_at, d.id) AS next_decision_at
    FROM router_decisions d
), bound AS (
  SELECT d.*, item.practice_item_id AS bound_item_id, item.probe_presentation_id AS bound_probe_presentation_id,
         served.plan_presentation_id AS bound_plan_presentation_id, outcome.outcome AS binding_outcome
    FROM decisions d
    LEFT JOIN router_decision_bindings item ON item.decision_id = d.decision_id AND item.binding_kind = 'item'
    LEFT JOIN router_decision_bindings served ON served.decision_id = d.decision_id AND served.binding_kind = 'plan_presentation'
    LEFT JOIN router_decision_bindings outcome ON outcome.decision_id = d.decision_id AND outcome.binding_kind = 'outcome'
), acting AS (
  SELECT d.*, COALESCE(
           d.session_id,
           (SELECT b.session_id FROM attention_blocks b WHERE b.decision_ref = d.decision_id AND b.session_id IS NOT NULL
             ORDER BY b.created_at, b.id LIMIT 1),
           (SELECT p.session_id FROM plan_presentations p
             WHERE p.session_id IS NOT NULL
               AND (p.router_decision_id = d.decision_id OR p.id = d.bound_plan_presentation_id
                    OR p.block_id IN (SELECT b.id FROM attention_blocks b WHERE b.decision_ref = d.decision_id))
             ORDER BY p.served_at, p.id LIMIT 1),
           (SELECT a.session_id FROM practice_attempts a
             WHERE a.session_id IS NOT NULL
               AND ((d.scheduler_slate_id IS NOT NULL AND a.scheduler_slate_id = d.scheduler_slate_id)
                    OR (a.practice_item_id = d.bound_item_id AND a.created_at >= d.decided_at))
             ORDER BY a.created_at, a.id LIMIT 1)
         ) AS acting_session_id
    FROM bound d
), with_return AS (
  SELECT d.*, (SELECT MIN(s.started_at) FROM sessions o JOIN sessions s ON s.id != o.id
                WHERE o.id = d.acting_session_id AND s.started_at >= COALESCE(o.ended_at, o.started_at)
              ) AS next_session_started_at
    FROM acting d
)
SELECT t.*,
       (SELECT b.id FROM attention_blocks b WHERE b.decision_ref = t.decision_id ORDER BY b.created_at, b.id LIMIT 1) AS block_id,
       (SELECT COUNT(*) FROM plan_presentations p
         WHERE p.router_decision_id = t.decision_id OR p.id = t.bound_plan_presentation_id) AS presentations,
       (SELECT MIN(p.served_at) FROM plan_presentations p
         WHERE p.router_decision_id = t.decision_id OR p.id = t.bound_plan_presentation_id) AS first_served_at,
       (SELECT COUNT(*) FROM (
          SELECT a.id FROM plan_presentations p JOIN practice_attempts a ON a.plan_presentation_id = p.id
           WHERE p.router_decision_id = t.decision_id
          UNION SELECT a.id FROM practice_attempts a WHERE a.plan_presentation_id = t.bound_plan_presentation_id
          UNION SELECT a.id FROM practice_attempts a WHERE a.probe_presentation_id = t.bound_probe_presentation_id
          UNION SELECT a.id FROM practice_attempts a WHERE a.practice_item_id = t.bound_item_id AND a.created_at >= t.decided_at
        )) AS attempts_on_presentations,
       (SELECT COUNT(*) FROM practice_attempts a WHERE t.scheduler_slate_id IS NOT NULL
           AND a.scheduler_slate_id = t.scheduler_slate_id) AS attempts_on_offer,
       (SELECT COUNT(*) FROM (
          SELECT COALESCE(json_extract(e.detail_json, '$.practice_item_id'), e.id)
            FROM attention_block_events e JOIN attention_blocks b ON b.id = e.block_id
           WHERE b.decision_ref = t.decision_id AND e.kind IN ('item_skipped', 'item_displaced')
          UNION SELECT COALESCE(t.bound_item_id, t.decision_id) WHERE t.binding_outcome IN ('skipped', 'abandoned')
        )) AS items_rejected,
       (SELECT o.arm FROM decision_objectives o WHERE o.decision_id = t.decision_id) AS objective_arm,
       CASE WHEN t.next_decision_id IS NULL THEN 'no_later_decision' END AS next_decision_censored,
       CASE WHEN NOT EXISTS (SELECT 1 FROM sessions o WHERE o.id = t.acting_session_id) THEN 'session_unresolved'
            WHEN t.next_session_started_at IS NULL THEN 'no_later_session' END AS return_censored
  FROM with_return t
 ORDER BY t.decided_at, t.decision_id
"""


def rows(connection: Any) -> list[dict[str, Any]]:
    """Every decision's links, read-only."""

    return [dict(row) for row in connection.execute(TRAJECTORY_SQL)]


__all__ = ["TRAJECTORY_SQL", "VERSION", "rows"]
