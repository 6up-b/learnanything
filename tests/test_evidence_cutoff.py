"""The evidence cutoff value (``learnloop.db.evidence_cutoff``): its presets reproduce each existing reader's
boundary literally, it round-trips through canonical JSON, and the mutable-field inventory names real columns.

The ``_base_*`` functions are the readers' comparisons copied verbatim from the tree before the cutoff type
existed; each matrix holds the moved kernel, the adapted reader and the preset to them on the same literal inputs,
results and exceptions alike. The reader-level matrices (a vault per reader) are in
``tests/test_evidence_cutoff_readers.py``.
"""

from __future__ import annotations

from contextlib import closing
from datetime import UTC, datetime
import json
import math
import os
import sqlite3
import time
from typing import Any

import pytest

from learnloop.clock import parse_utc
from learnloop.db import evidence_cutoff as EC
from learnloop.db.evidence_cutoff import Cutoff

from tests.helpers import create_basic_vault


# -- the readers' comparisons before the type existed (verbatim) ----------------------------------------------------


def _base_closure_through(local_date: str) -> tuple[datetime, bool]:
    from datetime import date, timedelta

    try:
        following = date.fromisoformat(local_date) + timedelta(days=1)
        limit = datetime(following.year, following.month, following.day).astimezone().astimezone(UTC)
        return limit, False
    except (OverflowError, ValueError):  # the far future (``9999-12-31``): every event
        return datetime.max.replace(tzinfo=UTC), True


def _base_closure_admits(limit: datetime, inclusive: bool, occurred: Any, received: Any = None) -> bool:
    if not occurred:
        return False
    for stamp in (occurred, received):
        if not stamp:
            continue
        moment = parse_utc(str(stamp))
        if moment is None or moment > limit or (moment == limit and not inclusive):
            return False
    return True


def _base_written_before(written: datetime | None, cutoff: datetime | None) -> bool:
    return written is not None and cutoff is not None and written < cutoff


def _base_known_by(known: datetime | None, cutoff: datetime | None) -> bool:
    return known is None or cutoff is None or known <= cutoff


def _base_field_skips(created_at: Any, as_of: Any) -> bool:
    return as_of is not None and created_at > as_of


def _base_ad_skips(created_at: Any, as_of: str | None) -> bool | str:
    """AD's attempt filter: ``continue`` on an unreadable time or ``at > limit``; True means skipped."""

    from learnloop.adaptive_difficulty.replay import days

    limit = days(as_of) if as_of else math.inf
    try:
        at = days(created_at)
    except ValueError:
        return True
    return at > limit


def _outcome(function: Any, *args: Any) -> Any:
    try:
        return ("value", function(*args))
    except Exception as exc:  # noqa: BLE001 - the matrix compares exceptions by type as well as values
        return ("raises", type(exc).__name__)


# -- time zones ----------------------------------------------------------------------------------------------------


@pytest.fixture
def local_zone():
    """Set the process's local time zone for one test (``Closure.through`` reads it), restoring it after."""

    saved = os.environ.get("TZ")

    def use(name: str) -> None:
        os.environ["TZ"] = name
        time.tzset()

    yield use
    if saved is None:
        os.environ.pop("TZ", None)
    else:
        os.environ["TZ"] = saved
    time.tzset()


#: Spring forward (2026-03-08, 02:00 local skipped) and fall back (2026-11-01, 01:00 local twice) in New York.
TRANSITIONS = [("2026-03-07", "2026-03-08T05:00:00Z"), ("2026-03-08", "2026-03-09T04:00:00Z"),
               ("2026-10-31", "2026-11-01T04:00:00Z"), ("2026-11-01", "2026-11-02T05:00:00Z")]


@pytest.mark.parametrize("local_date, midnight", TRANSITIONS)
def test_closure_through_is_the_next_local_midnight_across_a_transition(local_zone, local_date, midnight):
    from learnloop.router_objective.checks import Closure

    local_zone("America/New_York")
    limit, inclusive = EC.closure_through_limit(local_date)
    assert (limit, inclusive) == _base_closure_through(local_date) == (parse_utc(midnight), False)
    closure = Closure.through(local_date)
    assert (closure.limit, closure.inclusive, closure.local_date) == (limit, False, local_date)
    cutoff = closure.cutoff
    assert cutoff == Cutoff.closure_through(local_date)
    assert cutoff.time("limit") == parse_utc(midnight).isoformat()
    assert [b.op for b in cutoff.boundaries] == ["<", "<"]
    # Exclusive at the next local midnight; the instant before is in.
    before = parse_utc(midnight).timestamp() - 1e-6
    just_before = datetime.fromtimestamp(before, UTC).isoformat()
    for occurred, expected in ((midnight, False), (just_before, True)):
        assert closure.admits(occurred) is expected
        assert cutoff.admits(occurred) is expected


@pytest.mark.parametrize("local_date, midnight", TRANSITIONS)
def test_closure_at_the_same_instant_is_inclusive(local_zone, local_date, midnight):
    from learnloop.router_objective.checks import Closure

    local_zone("America/New_York")
    closure = Closure.at(midnight)
    assert closure.inclusive is True and closure.admits(midnight) is True
    assert Closure.through(local_date).admits(midnight) is False
    assert closure.cutoff == Cutoff.closure_at(midnight)
    assert closure.cutoff.admits(midnight) is True and closure.cutoff.boundaries[0].op == "<="
    # A through cutoff stores the instant it computed: read back under another zone it does not move.
    stored = Closure.through(local_date).cutoff.to_json()
    local_zone("Asia/Tokyo")
    assert Cutoff.from_json(stored).time("limit") == parse_utc(midnight).isoformat()
    assert Cutoff.closure_through(local_date).time("limit") != parse_utc(midnight).isoformat()


def test_closure_far_future_admits_everything_inclusively():
    from learnloop.router_objective.checks import Closure

    for local_date in ("9999-12-31",):
        assert EC.closure_through_limit(local_date) == _base_closure_through(local_date)
        closure = Closure.through(local_date)
        assert closure.inclusive is True and closure.admits("9999-12-31T23:59:59Z")
        assert closure.cutoff.admits("9999-12-31T23:59:59Z")
    # A malformed date is the far future in both (the predecessor's except clause catches ValueError).
    assert EC.closure_through_limit("not a date") == _base_closure_through("not a date")
    assert Closure.through("not a date").inclusive is True


STAMPS = [
    "2026-05-05T09:00:00Z", "2026-05-05T09:00:00+00:00", "2026-05-05T05:00:00-04:00", "2026-05-05T09:00:00",
    "2026-05-05T08:59:59.999999Z", "2026-05-05T09:00:00.000001Z", "2026-05-05T09:00:01Z", "2026-05-01T12:00:00Z",
    "2026-05-19T15:30:07Z", "", None, "not-a-time", "2026-05-05",
]


@pytest.mark.parametrize("inclusive", [True, False])
def test_closure_admits_matrix_equals_the_predecessor(inclusive):
    from learnloop.router_objective.checks import Closure

    limit = parse_utc("2026-05-05T09:00:00Z")
    closure = Closure(limit=limit, inclusive=inclusive, local_date="2026-05-05")
    cutoff = Cutoff.closure_at("2026-05-05T09:00:00Z") if inclusive else Cutoff.closure_through("2026-05-04")
    for occurred in STAMPS:
        for received in STAMPS:
            base = _outcome(_base_closure_admits, limit, inclusive, occurred, received)
            assert _outcome(EC.closure_admits, limit, inclusive, occurred, received) == base
            assert _outcome(closure.admits, occurred, received) == base
            if inclusive:  # the preset at the same instant; the through preset's limit depends on the zone
                assert _outcome(cutoff.admits, occurred, received) == base


def test_history_kernels_equal_the_predecessor():
    instants = [None, parse_utc("2026-05-05T09:00:00Z"), parse_utc("2026-05-05T09:00:01Z"),
                parse_utc("2026-05-05T08:59:59Z")]
    for left in instants:
        for right in instants:
            assert EC.history_v1_written_before(left, right) == _base_written_before(left, right)
            assert EC.history_v1_known_by(left, right) == _base_known_by(left, right)


FIELD_TIMES = ["2026-05-05T09:00:00Z", "2026-05-05T09:00:00+00:00", "2026-05-05T09:00:00.5Z", "2026-05-05T08:59:59Z",
               "2026-05-05T10:00:00+02:00", "", None, "garbage", "2026-05-05"]


def test_completed_by_matrix_equals_the_field_predecessor():
    for as_of in [None, "2026-05-05T09:00:00Z", "2026-05-05T09:00:00+00:00", ""]:
        cutoff = Cutoff.completed_by(as_of)
        for created in FIELD_TIMES:
            base = _outcome(_base_field_skips, created, as_of)
            new = _outcome(lambda c, a: a is not None and EC.completed_by_excludes(c, a), created, as_of)
            assert new == base, (created, as_of)
            admitted = _outcome(cutoff.admits, created)
            assert admitted == (("value", not base[1]) if base[0] == "value" else base), (created, as_of)


def test_ad_replay_matrix_equals_the_predecessor():
    for as_of in [None, "2026-05-05T09:00:00Z", "2026-05-05T05:00:00-04:00", "2026-05-05T09:00:00.000001Z"]:
        cutoff = Cutoff.ad_replay(as_of)
        for created in FIELD_TIMES:
            base = _base_ad_skips(created, as_of)
            assert cutoff.admits(created) is (not base), (created, as_of)


def test_ad_replay_with_an_unreadable_as_of_raises_like_the_predecessor():
    from learnloop.adaptive_difficulty.replay import days

    with pytest.raises(ValueError):
        days("garbage")
    with pytest.raises(ValueError):
        Cutoff.ad_replay("garbage").admits("2026-05-05T09:00:00Z")


def test_equal_time_inclusion_ad_and_field():
    """Both admit an attempt stamped exactly at ``as_of``. AD compares parsed days; the field compares text, so a
    later instant whose text sorts first is in and an earlier one whose text sorts last is out (characterized, not
    endorsed: the field's stored times are all ``Z`` stamps of one width)."""

    ad, field = Cutoff.ad_replay("2026-05-05T09:00:00Z"), Cutoff.completed_by("2026-05-05T09:00:00Z")
    assert ad.admits("2026-05-05T09:00:00Z") and field.admits("2026-05-05T09:00:00Z")
    assert ad.admits("2026-05-05T09:00:00+00:00") and field.admits("2026-05-05T09:00:00+00:00")
    assert not ad.admits("2026-05-05T09:00:00.5Z") and field.admits("2026-05-05T09:00:00.5Z")
    assert ad.admits("2026-05-05T10:00:00+02:00") and not field.admits("2026-05-05T10:00:00+02:00")
    assert field.admits("") and not ad.admits("")
    with pytest.raises(TypeError):
        Cutoff.completed_by("2026-05-05T09:00:00Z").admits(None)


def test_history_v1_attempt_rule_and_equal_second_ties():
    target = Cutoff.history_v1("att_b", "2026-05-05T09:00:00Z")
    assert target.admits("2026-05-05T09:00:00Z", attempt_id="att_a")  # same second, smaller id: before
    assert not target.admits("2026-05-05T09:00:00Z", attempt_id="att_b")  # the target itself
    assert not target.admits("2026-05-05T09:00:00Z", attempt_id="att_c")  # same second, larger id: after
    assert not target.admits("2026-05-05T09:00:01Z", attempt_id="att_a")
    # The order is text: an instant spelled otherwise sorts by its text, not its instant.
    assert not target.admits("2026-05-05T10:00:00+02:00", attempt_id="att_a")  # 08:00Z, sorts after
    assert target.admits("2026-05-05T09:00:00.5Z", attempt_id="att_z")  # half a second later, sorts before
    # The known-time gate is read only with the switch on, and only for a non-empty receipt.
    exam = ("2026-05-01T12:00:00Z", "2026-05-19T15:30:07Z")
    assert target.admits(exam[0], exam[1], attempt_id="exam")
    on = Cutoff.history_v1("att_b", "2026-05-05T09:00:00Z", available_at_reads=True)
    assert not on.admits(exam[0], exam[1], attempt_id="exam")
    assert on.admits(exam[0], "", attempt_id="exam") and on.admits(exam[0], "garbage", attempt_id="exam")
    # An imported target is decided at its receipt: an exam received by then is in.
    imported = Cutoff.history_v1("att_b", "2026-05-01T13:00:00Z", known_at="2026-05-19T15:30:07Z",
                                 available_at_reads=True)
    assert imported.admits(*exam, attempt_id="exam")


def test_history_v1_records_are_written_strictly_before_the_completion():
    target = Cutoff.history_v1("att_b", "2026-05-05T09:00:00Z", known_at="2026-05-19T00:00:00Z",
                               available_at_reads=True)
    assert target.written_before("2026-05-05T08:59:59Z")
    assert not target.written_before("2026-05-05T09:00:00Z")  # written at exactly the completion: out
    assert not target.written_before("2026-05-06T00:00:00Z")  # by the known time, but after the completion
    assert not target.written_before(None) and not target.written_before("garbage")
    assert target.mark_before("2026-05-05T08:59:59Z") and not target.mark_before("2026-05-05T09:00:00Z")
    assert target.mark_before(None)  # text: "" sorts first
    with pytest.raises(ValueError):
        Cutoff.current().written_before("2026-05-05T08:59:59Z")


def test_corrected_before_is_the_attempt_order_without_a_known_gate():
    cutoff = Cutoff.corrected_before("att_b", "2026-05-05T09:00:00Z")
    assert cutoff.admits("2026-05-05T09:00:00Z", "2099-01-01T00:00:00Z", attempt_id="att_a")
    assert not cutoff.admits("2026-05-05T09:00:00Z", attempt_id="att_c")
    assert cutoff.corrections == "now" and cutoff.tie_order == "(created_at, id)"


def test_as_known_at_is_known_by_inclusive_and_fails_closed():
    cutoff = Cutoff.as_known_at("2026-05-05T09:00:00Z")
    assert cutoff.admits("2026-05-01T12:00:00Z")
    assert cutoff.admits("2026-05-01T12:00:00Z", "2026-05-05T09:00:00Z")
    assert not cutoff.admits("2026-05-01T12:00:00Z", "2026-05-19T15:30:07Z")  # the imported exam
    assert cutoff.admits("2026-05-01T12:00:00Z", "")  # an empty receipt reads its occurrence (loaded-row form)
    assert not cutoff.admits("2026-05-01T12:00:00Z", "garbage") and not cutoff.admits(None)
    assert cutoff.corrections == "then"


def test_as_known_at_reports_unreconstructable_fields_as_approximate():
    asked = ("misconceptions.status", "misconceptions.statement", "help_assists.shown_at", "help_assists.attempt_id",
             "practice_attempts.created_at")
    cutoff = Cutoff.as_known_at("2026-05-05T09:00:00Z", attempt_id="att_b", fields=asked)
    assert [entry.field for entry in cutoff.approximate] == ["help_assists.attempt_id", "misconceptions.statement"]
    assert cutoff.is_approximate and cutoff.anchor_kind == "attempt"
    assert not Cutoff.as_known_at("2026-05-05T09:00:00Z", fields=("help_assists.shown_at",)).is_approximate


def test_current_admits_everything():
    cutoff = Cutoff.current()
    assert all(cutoff.admits(value) for value in FIELD_TIMES)
    assert cutoff.identity_scalar() is None and cutoff.boundaries == ()


PRESETS = [
    Cutoff.current(),
    Cutoff.corrected_before("att_b", "2026-05-05T09:00:00Z"),
    Cutoff.as_known_at("2026-05-05T09:00:00Z", fields=("misconceptions.statement", "help_assists.attempt_id")),
    Cutoff.as_known_at("2026-05-05T09:00:00Z", attempt_id="att_é"),
    Cutoff.closure_at("2026-05-05T09:00:00Z"),
    Cutoff.closure_through("9999-12-31"),
    Cutoff.history_v1("att_b", "2026-05-05T09:00:00Z", known_at="2026-05-19T00:00:00Z", available_at_reads=True),
    Cutoff.history_v1("att_b", "2026-05-05T09:00:00Z"),
    Cutoff.ad_replay(None),
    Cutoff.ad_replay("2026-05-05T09:00:00Z"),
    Cutoff.completed_by(None),
    Cutoff.completed_by("2026-05-05T09:00:00Z"),
]


@pytest.mark.parametrize("cutoff", PRESETS, ids=lambda c: f"{c.preset}-{c.anchor_kind}")
def test_cutoff_round_trips_through_canonical_json(cutoff):
    text = cutoff.to_json()
    assert Cutoff.from_json(text) == cutoff
    assert Cutoff.from_dict(cutoff.to_dict()) == cutoff
    assert text == json.dumps(json.loads(text), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    assert Cutoff.from_json(text).to_json() == text


def test_the_serialized_form_names_preset_policies_anchor_boundaries_and_approximation():
    raw = json.loads(Cutoff.closure_at("2026-05-05T09:00:00Z").to_json())
    assert raw == {
        "schema": "evidence_cutoff/1", "preset": "closure", "admission": "occurred_and_received_by",
        "corrections": "now", "corrections_then": [], "anchor": {"kind": "moment", "id": "2026-05-05T09:00:00Z"},
        "times": {"limit": "2026-05-05T09:00:00+00:00"},
        "boundaries": [
            {"subject": "events", "time": "occurred_at", "op": "<=", "anchor": "limit", "comparison": "instant",
             "missing": "excluded", "malformed": "raises"},
            {"subject": "answers", "time": "received_at", "op": "<=", "anchor": "limit", "comparison": "instant",
             "missing": "ignored", "malformed": "raises"}],
        "tie_order": None, "availability": "occurred_and_received", "approximate": []}


def test_a_cutoff_refuses_an_unknown_schema_or_policy():
    raw = Cutoff.current().to_dict()
    with pytest.raises(ValueError):
        Cutoff.from_dict({**raw, "schema": "evidence_cutoff/2"})
    with pytest.raises(ValueError):
        Cutoff.from_dict({**raw, "preset": "latest"})
    with pytest.raises(ValueError):
        Cutoff.from_dict({**raw, "corrections": "sometimes"})
    with pytest.raises(ValueError):
        Cutoff.from_dict({**raw, "boundaries": [{"subject": "a", "time": "t", "op": "<<", "anchor": "x",
                                                 "comparison": "instant", "missing": "excluded",
                                                 "malformed": "excluded"}]})


def test_identity_scalars_are_the_readers_old_keys():
    """A cache keyed by a reader's scalar keeps the scalar: the cutoff hands it back unchanged."""

    assert Cutoff.ad_replay(None).identity_scalar() is None
    assert Cutoff.ad_replay("2026-05-05T09:00:00Z").identity_scalar() == "2026-05-05T09:00:00Z"
    assert Cutoff.completed_by("2026-05-05T09:00:00Z").identity_scalar() == "2026-05-05T09:00:00Z"
    assert Cutoff.closure_at("2026-05-05T09:00:00Z").identity_scalar() == "2026-05-05T09:00:00Z"
    assert Cutoff.closure_through("2026-05-05").identity_scalar() == "2026-05-05"
    assert Cutoff.history_v1("att_b", "2026-05-05T09:00:00Z").identity_scalar() == "att_b"


# -- the inventory ---------------------------------------------------------------------------------------------------


def test_the_inventory_names_real_columns(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        tables = {name for (name,) in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        for entry in EC.MUTABLE_FIELDS:
            assert entry.recoverable in EC.RECOVERABILITY, entry
            if entry.table.startswith("("):
                continue  # derived, or applied at read time
            assert entry.table in tables, entry
            columns = {row[1] for row in connection.execute(f"PRAGMA table_info({entry.table})")}
            assert entry.column in columns, entry
    assert len({entry.name for entry in EC.MUTABLE_FIELDS}) == len(EC.MUTABLE_FIELDS)


def test_the_module_imports_nothing_of_learnloop_but_the_clock():
    import ast
    from pathlib import Path

    for module in ("evidence_cutoff", "prediction_target"):
        source = Path(EC.__file__).with_name(f"{module}.py").read_text(encoding="utf-8")
        imported = set()
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
            elif isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
        assert {name for name in imported if name.startswith("learnloop")} <= {"learnloop.clock"}, module
