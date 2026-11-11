"""Teacher TE2-log, part 5: the receipt's ``episodes`` and ``minutes`` (spec_teacher_v1 §8.3, §11.6, §11.9).

With ``teacher.episode_log`` on, ``LessonReceiptV1`` lists the lesson's episode ids by kind, its active and elapsed
minutes side by side with their source (missing intervals counted, never filled in), and its ``lesson_node_held``
forecast keys; a detour note whose row was refused is a warning. Off, the receipt is TE1's (tests in
test_teacher_te2log_episodes.py).
"""

from __future__ import annotations

from learnloop.teacher import episodes as E
from tests.teacher_te2log_receipt_helpers import _iso, _rows, _run

def test_the_receipt_lists_episodes_by_kind_minutes_and_placement_forecasts(tmp_path):
    intervals = [{"screen_session": "s", "seq": 1, "started_at": _iso(0), "ended_at": _iso(4), "foreground": True},
                 {"screen_session": "s", "seq": 3, "started_at": _iso(6), "ended_at": _iso(8), "foreground": False}]
    repository, lesson_id, receipt = _run(tmp_path, intervals=intervals)
    ids = [row[0] for row in _rows(repository, "SELECT id FROM lesson_episodes ORDER BY opened_at, id")]
    assert receipt["episodes"] == {"probe": [], "detour": ids, "gap": [], "goal_lo": []} and len(ids) == 2
    # Active (the foreground intervals) and elapsed (closed - opened) side by side; never blended.
    assert receipt["minutes"] == {"active_minutes": 4.0, "elapsed_minutes": 10.0, "unreported_minutes": 4.0,
                                  "missing_intervals": 1, "intervals": 2, "source": "lesson_activity"}
    held = [row[0] for row in _rows(repository, "SELECT receipt_key FROM forecast_receipts "
                                                "WHERE kind = 'lesson_node_held' ORDER BY created_at, receipt_key")]
    # Two plan versions, each forecasting n0 and n1 (the nodes with p_held on a topic).
    assert receipt["node_held_forecasts"] == held and len(held) == 4
    # Every episode closed with the lesson or at its re-check, none left open.
    assert _rows(repository, "SELECT COUNT(*) FROM lesson_episodes WHERE closed_at IS NULL") == [(0,)]


def test_with_no_interval_the_minutes_say_so_and_active_is_unknown(tmp_path):
    _repository, _lesson_id, receipt = _run(tmp_path)
    assert receipt["minutes"]["source"] == "no_intervals"
    assert receipt["minutes"]["active_minutes"] is None and receipt["minutes"]["elapsed_minutes"] == 10.0
    assert receipt["minutes"]["unreported_minutes"] == 10.0


def test_a_refused_detour_row_is_a_receipt_warning(tmp_path, monkeypatch):
    repository, _lesson_id, receipt = _run(tmp_path, refuse=True, monkeypatch=monkeypatch)
    # The refused note's row is missing; the later unlogged detour stands.
    assert [row[0] for row in _rows(repository, "SELECT repair_class FROM lesson_episodes")] == [E.UNLOGGED]
    assert any("detour note(s) have no episode row" in warning for warning in receipt["warnings"])
