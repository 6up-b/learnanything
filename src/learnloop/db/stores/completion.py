"""Durable continuation after an attempt has been applied.

``route_json`` holds different facts in the two states of a row:

* pending: ``{"applied_probe_episode_id": <id or null>}``, the probe episode the
  attempt was applied under, so a resumed completion routes the learner to
  that episode rather than to whichever episode is open when it resumes;
* completed: the frozen learner route (``episode_id``/``status``/
  ``feedback_deferred``), or null when the attempt belongs to no episode.
"""

from __future__ import annotations

import json

from learnloop.clock import utc_now_iso


class AttemptCompletionStoreMixin:
    def save_attempt_completion(self, *, attempt_id, submission_id, session_id,
                                practice_item_id, result, applied_probe_episode_id=None,
                                awaits_completion=True, clock=None):
        """Save an applied attempt's result and what its completion needs.

        ``awaits_completion=False`` records a door that has no completion phase: the
        row is written completed with no route, so it is never counted as an
        interrupted completion. A repeated save of a pending row refreshes only
        the result.
        """

        now = utc_now_iso(clock)
        if awaits_completion:
            status, route, completed_at = 'pending', {'applied_probe_episode_id': applied_probe_episode_id}, None
        else:
            status, route, completed_at = 'completed', None, now
        with self.connection() as connection:
            connection.execute(
                """INSERT INTO attempt_completion_work(
                    attempt_id, submission_id, session_id, practice_item_id,
                    result_json, route_json, status, created_at, completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(attempt_id) DO UPDATE SET result_json=excluded.result_json
                WHERE attempt_completion_work.status='pending'""",
                (attempt_id, submission_id, session_id, practice_item_id,
                 json.dumps(result, sort_keys=True), json.dumps(route, sort_keys=True),
                 status, now, completed_at),
            )
            connection.commit()

    def attempt_completion(self, attempt_id):
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM attempt_completion_work WHERE attempt_id=?", (attempt_id,)
            ).fetchone()
        if row is None:
            return None
        value = dict(row)
        value['result'] = json.loads(value.pop('result_json'))
        stored_route = json.loads(value.pop('route_json') or 'null')
        if value['status'] == 'completed':
            value['route'] = stored_route
            value['applied_episode_recorded'] = True
            value['applied_probe_episode_id'] = None
        else:
            value['route'] = None
            recorded = isinstance(stored_route, dict) and 'applied_probe_episode_id' in stored_route
            value['applied_episode_recorded'] = recorded
            value['applied_probe_episode_id'] = stored_route['applied_probe_episode_id'] if recorded else None
        return value

    def complete_attempt_work(self, attempt_id, *, result, route, clock=None):
        with self.connection() as connection:
            connection.execute(
                """UPDATE attempt_completion_work
                   SET status='completed', result_json=?, route_json=?, completed_at=?
                   WHERE attempt_id=? AND status='pending'""",
                (json.dumps(result, sort_keys=True), json.dumps(route, sort_keys=True),
                 utc_now_iso(clock), attempt_id),
            )
            connection.commit()
