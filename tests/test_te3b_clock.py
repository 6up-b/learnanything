"""Teacher TE3b (spec_teacher_v1 rev 5 §15.1a): a lesson's active minutes on the objective's clock (``price.activity_spans``),
only at the tag with the switch on.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from learnloop.algorithm_versions import LESSON_OFFERS_ALGORITHM_VERSION, LESSON_OPPORTUNITY_ALGORITHM_VERSION
from learnloop.router_objective import price as P


TAG = LESSON_OFFERS_ALGORITHM_VERSION
OLD = LESSON_OPPORTUNITY_ALGORITHM_VERSION
from tests.te3b_value_helpers import T0, _lesson, _lesson_db, _stamp

# --- the objective's clock -----------------------------------------------------------------------------------


def test_kappa_counts_a_lessons_active_minutes_only_with_lessons_on(tmp_path):
    connection = _lesson_db(tmp_path)
    _lesson(connection, "les_now", T0 - timedelta(minutes=30), [(0, 10), (15, 10)], closed=False)
    now = _stamp(T0)
    without, _start, basis = P.session_active_minutes(connection, now=now, gap_minutes=60.0)
    assert without == 0.0 and basis["basis"] == "attempt_latency_plus_reader_active_seconds"
    with_lessons, start, basis = P.session_active_minutes(connection, now=now, gap_minutes=60.0, lessons=True)
    assert with_lessons == pytest.approx(20.0)  # the foreground minutes only: the 5-minute idle gap is not counted
    assert start == _stamp(T0 - timedelta(minutes=30))
    assert basis["basis"].endswith("lesson_active_seconds")
    # The idle gap inside one lesson never splits its session: one span per lesson.
    spans = P.lesson_spans(connection, since=_stamp(T0 - timedelta(days=1)), until=now)
    assert len(spans) == 1 and spans[0][2] == pytest.approx(20.0 * 60)
    # The integral κ charges starts at those minutes (the session's own clock).
    kappa0, mbar = 0.01, 20.0
    assert kappa0 * ((with_lessons + 10) ** 2 - with_lessons ** 2) / (2 * mbar) > kappa0 * (10 ** 2) / (2 * mbar)


def test_the_serving_clock_reads_only_lesson_intervals_received_by_now(tmp_path):
    """Codex review F4: the serving clock at ``now`` never reads an interval received after ``now``; an outcome
    window read after the fact (RO5's realized cost) counts every interval that happened in it."""

    connection = _lesson_db(tmp_path)
    _lesson(connection, "les_late", T0 - timedelta(minutes=30), [(0, 20)], received=T0 + timedelta(hours=3))
    now = _stamp(T0)
    minutes, _start, _basis = P.session_active_minutes(connection, now=now, gap_minutes=60.0, lessons=True)
    assert minutes == 0.0
    later, _start, _basis = P.session_active_minutes(connection, now=_stamp(T0 + timedelta(hours=3, minutes=1)),
                                                     gap_minutes=600.0, lessons=True)
    assert later == pytest.approx(20.0)
    window = P.activity_spans(connection, since=_stamp(T0 - timedelta(days=1)), until=now, lessons=True)
    assert len(window) == 1 and window[0][2] == pytest.approx(20.0 * 60)


def test_the_gate_reads_lessons_on_the_clock_only_at_the_tag_with_the_switch(tmp_path):
    from learnloop.daily_plan import objective_inputs as OI
    from learnloop.vault.loader import load_vault

    from tests.helpers import append_config_toml, create_basic_vault, set_algorithm_version

    paths = create_basic_vault(tmp_path / "v")
    set_algorithm_version(paths, OLD)
    assert not OI._lessons_on(load_vault(paths.root).config)
    set_algorithm_version(paths, TAG)
    assert OI._lessons_on(load_vault(paths.root).config)
    append_config_toml(paths.root, "[router.lesson_suggestions]\nin_objective = false\n")
    assert not OI._lessons_on(load_vault(paths.root).config)


