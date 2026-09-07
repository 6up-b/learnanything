"""Durable continuation after an attempt has been applied."""

from __future__ import annotations

import json

from learnloop.clock import utc_now_iso


class AttemptCompletionStoreMixin:
    def save_attempt_completion(self, *, attempt_id, submission_id, session_id,
                                practice_item_id, result, clock=None):
        with self.connection() as connection:
            connection.execute(
                """INSERT INTO attempt_completion_work(
                    attempt_id, submission_id, session_id, practice_item_id,
                    result_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(attempt_id) DO UPDATE SET result_json=excluded.result_json
                WHERE attempt_completion_work.status='pending'""",
                (attempt_id, submission_id, session_id, practice_item_id,
                 json.dumps(result, sort_keys=True), utc_now_iso(clock)),
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
        value['route'] = json.loads(value.pop('route_json') or 'null')
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
