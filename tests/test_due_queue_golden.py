"""The due queue's whole build pinned on one vault that reaches every stage (``tests/due_queue_helpers.py``).

Three builds of the same state, each on a fresh copy: a serving build with the session that committed a probe
presentation, a read build (``read_due_queue``) with that session, and a read build with no session. Each
record holds the returned queue (ids, order, scores, components, explanations, slate and candidate ids), the
exploration draw (its support, roll, choice and every outcome's composed order, from the offer trace), the trace's
exclusions, cold deferrals and pin, and every row the build added, changed or removed, table by table.

The admission's paths have their own records, each recorded before the admission's reads were gathered up front:
a vault that withholds items for most of the admission's reasons (a serving and a sessionless read build), the
probe episode's reads with value stopping off (context, instruments, familiarity), a phone's build (its device
gate and what it defers), a phone read where no item reaches the in-progress episode, a build with nothing to
serve, and the two admissions built outside a queue (``pool_admission``, ``check_admission``), every item asked.

Ids read ``<ulid:n>`` in order of first appearance in the record (the process's ULID stream is also seeded and its
clock held, setup included, but how many ids the setup mints can vary with the hash seed). Stamps from the wall clock read
``<wall>``, the vault's algorithm tag ``<head tag>``, and floats are rounded to ten places.

A change that means to change what a build returns or writes regenerates the files and shows the diff in review:

    DUE_QUEUE_GOLDEN_WRITE=1 uv run pytest tests/test_due_queue_golden.py

``DUE_QUEUE_GOLDEN_ACTUAL=<dir>`` writes each case's record there as well, to diff against its golden.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import re
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.scheduling.device_eligibility import PHONE, DeviceFilter
from learnloop.scheduling.intent.serving import intent_serving
from learnloop.scheduling.scheduler import (
    OfferTrace,
    SchedulerSession,
    serve_due_queue,
    check_admission,
    pool_admission,
    read_due_queue,
)

from tests.due_queue_helpers import (
    CLOCK,
    LEFT_FOR_DESKTOP,
    SESSION,
    build_figure_vault,
    build_gate_vault,
    build_generated_followup_vault,
    build_intent_targets_vault,
    build_probe_history_vault,
    build_rich_vault,
    build_unconsulted_episode_vault,
    build_waiting_check_episode_vault,
)

GOLDEN_DIR = Path(__file__).parent / "goldens" / "due_queue"
WRITE = os.environ.get("DUE_QUEUE_GOLDEN_WRITE") == "1"

_ULID_MS = 1_790_000_000_000
_ULID = re.compile(r"\b[0-9A-HJKMNP-TV-Z]{26}\b")
_STAMP = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?")
_HEAD_TAG = re.compile(re.escape(LATEST_ALGORITHM_VERSION) + r"(?![0-9.])")
#: FTS shadow tables hold binary segments a queue build never writes.
_SKIPPED_TABLE = re.compile(r"_(data|idx|content|docsize|config)$")


@pytest.fixture
def seeded_ids(monkeypatch):
    from learnloop import ids

    monkeypatch.setattr(ids, "_wall_clock_ms", lambda: _ULID_MS)
    monkeypatch.setattr(ids, "secrets", SimpleNamespace(randbits=random.Random(20261113).getrandbits))
    monkeypatch.setattr(ids, "_last_timestamp_ms", -1)
    monkeypatch.setattr(ids, "_last_randomness", 0)


def _stamp(text: str) -> str:
    try:
        moment = datetime.fromisoformat(text.replace("Z", "+00:00").replace(" ", "T"))
    except ValueError:
        return text
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    return "<wall>" if abs((moment - datetime.now(UTC)).total_seconds()) < 3 * 86400 else text


class _Ids:
    def __init__(self) -> None:
        self.seen: dict[str, str] = {}

    def __call__(self, text: str) -> str:
        def one(match: re.Match[str]) -> str:
            return self.seen.setdefault(match.group(0), f"<ulid:{len(self.seen)}>")

        text = _HEAD_TAG.sub("<head tag>", _STAMP.sub(lambda match: _stamp(match.group(0)), text))
        return _ULID.sub(one, text)


def _clean(value: Any, ids: _Ids) -> Any:
    if isinstance(value, dict):
        return {str(key): _clean(item, ids) for key, item in value.items()}
    if isinstance(value, list | tuple | set | frozenset):
        items = [_clean(item, ids) for item in value]
        return sorted(items, key=json.dumps) if isinstance(value, set | frozenset) else items
    if isinstance(value, bytes):
        return f"<bytes:{hashlib.sha256(value).hexdigest()[:16]}>"
    if isinstance(value, float):
        return round(value, 10)
    if isinstance(value, str):
        stripped = value.strip()
        if stripped[:1] in "[{":
            try:
                return {"<json>": _clean(json.loads(value), ids)}
            except ValueError:
                pass
        return ids(value)
    return value


def _database(path: Path) -> dict[str, list[dict[str, Any]]]:
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        tables = [
            row["name"] for row in connection.execute(
                "SELECT name, sql FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
            if not _SKIPPED_TABLE.search(row["name"]) and "VIRTUAL TABLE" not in str(row["sql"]).upper()
        ]
        out: dict[str, list[dict[str, Any]]] = {}
        for table in tables:
            try:
                rows = connection.execute(f'SELECT rowid AS "<rowid>", * FROM "{table}" ORDER BY rowid').fetchall()
            except sqlite3.OperationalError:  # WITHOUT ROWID
                rows = connection.execute(f'SELECT * FROM "{table}"').fetchall()
            out[table] = [dict(row) for row in rows]
        return out
    finally:
        connection.close()


def _row_key(row: dict[str, Any]) -> str:
    return str(row["<rowid>"]) if "<rowid>" in row else json.dumps(row, sort_keys=True, default=str)


def _database_changes(before: dict[str, list[dict]], after: dict[str, list[dict]]) -> dict[str, Any]:
    changes: dict[str, Any] = {}
    for table in sorted(set(before) | set(after)):
        old = {_row_key(row): row for row in before.get(table, [])}
        new = {_row_key(row): row for row in after.get(table, [])}
        added = [row for key, row in new.items() if key not in old]
        removed = [row for key, row in old.items() if key not in new]
        changed = [{"before": old[key], "after": row} for key, row in new.items() if key in old and old[key] != row]
        entry = {name: rows for name, rows in (("added", added), ("changed", changed), ("removed", removed)) if rows}
        if entry:
            changes[table] = entry
    return changes


def _scheduled(item: Any) -> dict[str, Any]:
    return {
        "practice_item_id": item.practice_item_id,
        "learning_object_id": item.learning_object_id,
        "priority": item.priority,
        "components": dict(sorted(item.components.items())),
        "readiness_factor": item.readiness_factor,
        "selected_mode": item.selected_mode,
        "plain_english": list(item.plain_english),
        "reward_debug": item.reward_debug,
        "followup_kind": item.followup_kind,
        "scheduler_slate_id": item.scheduler_slate_id,
        "scheduler_candidate_id": item.scheduler_candidate_id,
    }


def _trace(trace: OfferTrace) -> dict[str, Any]:
    return {
        "exclusions": {reason: list(ids) for reason, ids in sorted(trace.exclusions.items())},
        "greedy_item_ids": list(trace.greedy_item_ids),
        "considered_item_ids": [item.practice_item_id for item in trace.considered],
        "base_propensity": dict(sorted(trace.base_propensity.items())),
        "exploration": trace.exploration,
        "outcomes": [
            {
                "explored_item_id": outcome.explored_item_id,
                "probability": outcome.probability,
                "composed": [item.practice_item_id for item in outcome.composed],
            }
            for outcome in trace.outcomes
        ],
        "realized": trace.realized,
        "pinned_item_id": trace.pinned_item_id,
        "probe_block_reason": trace.probe_block_reason,
        "cold_deferrals": [dict(row) for row in trace.cold_deferrals],
        "placement_active": trace.placement_active,
        "slate_id": trace.slate_id,
        "voi_decisions": list(trace.voi_decisions),
        "teach_back_exclusion_reason": trace.teach_back_exclusion_reason,
    }


def _record(tmp_path: Path, build: Any, *, vault_builder: Any = build_rich_vault, prepare: Any = None,
            extra: Any = None) -> dict[str, Any]:
    vault, repository = vault_builder(tmp_path / "vault")
    if prepare is not None:
        prepare(vault)
    before = _database(repository.sqlite_path)
    trace = OfferTrace()
    queue = build(vault, repository, trace)
    changes = _database_changes(before, _database(repository.sqlite_path))
    record = {"queue": [_scheduled(item) for item in queue], "trace": _trace(trace), "database": changes}
    if extra is not None:
        record["extra"] = extra()
    return _clean(record, _Ids())


def _check(name: str, record: dict[str, Any]) -> None:
    path = GOLDEN_DIR / f"{name}.json"
    text = json.dumps(record, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    if WRITE:
        GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return
    assert path.exists(), f"no golden for {name}: regenerate with DUE_QUEUE_GOLDEN_WRITE=1"
    if os.environ.get("DUE_QUEUE_GOLDEN_ACTUAL"):
        Path(os.environ["DUE_QUEUE_GOLDEN_ACTUAL"], f"{name}.json").write_text(text, encoding="utf-8")
    assert json.loads(text) == json.loads(path.read_text(encoding="utf-8")), (
        f"{name}: what the build returned or wrote moved (see the module docstring to regenerate)"
    )


def test_a_serving_build_with_a_session(tmp_path, seeded_ids):
    _check("serving_with_session", _record(tmp_path, lambda vault, repository, trace: serve_due_queue(
        vault, repository, clock=CLOCK, session=SchedulerSession(session_id=SESSION), offer_trace=trace)))


def test_a_read_build_with_the_same_session(tmp_path, seeded_ids):
    _check("read_with_session", _record(tmp_path, lambda vault, repository, trace: read_due_queue(
        vault, repository, clock=CLOCK, session=SchedulerSession(session_id=SESSION), offer_trace=trace)))


def test_a_read_build_with_no_session(tmp_path, seeded_ids):
    _check("read_without_session", _record(tmp_path, lambda vault, repository, trace: read_due_queue(
        vault, repository, clock=CLOCK, offer_trace=trace)))


def test_the_vault_reaches_every_stage(tmp_path, seeded_ids):
    """What the goldens are for: if the vault stops reaching a stage, the goldens stop pinning it."""

    record = _record(tmp_path, lambda vault, repository, trace: serve_due_queue(
        vault, repository, clock=CLOCK, session=SchedulerSession(session_id=SESSION), offer_trace=trace))
    queue = record["queue"]
    components = [item["components"] for item in queue]
    assert queue[0]["components"].get("probe_committed") == 1.0, "the committed presentation is pinned first"
    assert any(c.get("exploration_selected") == 1.0 for c in components), "the exploration draw moved an item"
    assert any(c.get("new_material") == 1.0 for c in components), "placement serves new material"
    assert any(item["selected_mode"] == "teach_back" for item in queue), "a teach-back is composed"
    assert any(c.get("voi_stop") == 1.0 for c in components), "the probe episode's value decision is made"
    assert record["trace"]["cold_deferrals"], "the cold lane defers a task"
    assert "contrast_pair_servings" in record["database"], "the contrast pair's order is drawn and recorded"
    assert "pi_a1" in [item["practice_item_id"] for item in queue] and "pi_a2" not in [
        item["practice_item_id"] for item in queue
    ], "the due check serves one of its candidates"


# -- the admission's paths: each gate, the probe episode's reads, a phone's device, the readers outside a build ------


def _phone(vault: Any) -> DeviceFilter:
    return DeviceFilter(vault, PHONE, left_for_desktop=frozenset({LEFT_FOR_DESKTOP}))


def test_a_serving_build_that_withholds_for_each_gate(tmp_path, seeded_ids):
    _check("admission_gates_serving", _record(tmp_path, lambda vault, repository, trace: serve_due_queue(
        vault, repository, clock=CLOCK, session=SchedulerSession(session_id=SESSION), offer_trace=trace),
        vault_builder=build_gate_vault))


def test_a_read_build_with_no_session_that_withholds_for_each_gate(tmp_path, seeded_ids):
    _check("admission_gates_read", _record(tmp_path, lambda vault, repository, trace: read_due_queue(
        vault, repository, clock=CLOCK, offer_trace=trace), vault_builder=build_gate_vault))


def _value_stopping_off(vault: Any) -> None:
    vault.config.voi_stopping.enabled = False


def test_a_serving_build_that_values_the_episodes_probes(tmp_path, seeded_ids):
    """Value stopping off: the probes score their information, each read once for the episode (its context,
    instruments and the items' familiarity, which an answer on the LO discounts); a new session's build records the
    probe selection."""

    _check("admission_probe_reads", _record(tmp_path, lambda vault, repository, trace: serve_due_queue(
        vault, repository, clock=CLOCK, session=SchedulerSession(session_id="sess_probe_reads"), offer_trace=trace),
        vault_builder=build_probe_history_vault, prepare=_value_stopping_off))


def test_a_phone_build(tmp_path, seeded_ids):
    """A phone holds back a picture, a teach-back and the item its session left for the desktop; one answered item
    is never started and one is not due."""

    holder: dict[str, DeviceFilter] = {}

    def build(vault, repository, trace):
        holder["filter"] = _phone(vault)
        return serve_due_queue(vault, repository, clock=CLOCK, session=SchedulerSession(session_id=SESSION),
                               offer_trace=trace, device_filter=holder["filter"])

    _check("admission_phone", _record(tmp_path, build, vault_builder=build_figure_vault,
                                      extra=lambda: {"deferred": sorted(holder["filter"].deferred)}))


#: The probe episode's reads the scheduler makes through these names (the familiarity read aside), spied on so a
#: record can say which episodes a build read.
_EPISODE_READS = (
    "administered_surface_exclusions", "episode_hypothesis_set", "eligible_instruments",
    "qualifying_observation_count", "session_qualifying_total",
)


def _spy_episode_reads(monkeypatch) -> list[str]:
    from learnloop.scheduling import scheduler

    calls: list[str] = []
    for name in _EPISODE_READS:
        real = getattr(scheduler, name)

        def spy(*args, _real=real, _name=name, **kwargs):
            calls.append(_name)
            return _real(*args, **kwargs)

        monkeypatch.setattr(scheduler, name, spy)
    return calls


def test_a_phone_read_where_no_item_reaches_the_episode(tmp_path, seeded_ids, monkeypatch):
    """The probe's LO is paused, so no item of the in-progress episode reaches a gate that reads it, and the phone
    is asked only about what the other gates admit. ``episode_reads``: none, as the lazy build read none."""

    holder: dict[str, DeviceFilter] = {}
    calls = _spy_episode_reads(monkeypatch)

    def build(vault, repository, trace):
        holder["filter"] = _phone(vault)
        calls.clear()
        return read_due_queue(vault, repository, clock=CLOCK, offer_trace=trace, device_filter=holder["filter"])

    _check("admission_unconsulted_episode", _record(
        tmp_path, build, vault_builder=build_unconsulted_episode_vault,
        extra=lambda: {"deferred": sorted(holder["filter"].deferred), "episode_reads": sorted(calls)}))


def test_a_read_where_an_item_of_the_probes_lo_waits_for_its_check(tmp_path, seeded_ids):
    """Every item of the probe's LO is paused but one, whose "Check once" is not due: it passes the routine gate and
    intent's exclusions, then intent holds it, so no item reaches the episode. The admission's reads gathered up
    front read this episode (the lazy build did not); what the build returns and writes is unchanged."""

    _check("admission_waiting_check_episode", _record(tmp_path, lambda vault, repository, trace: read_due_queue(
        vault, repository, clock=CLOCK, offer_trace=trace), vault_builder=build_waiting_check_episode_vault))


def _retire_everything(vault: Any) -> None:
    for item in vault.practice_items.values():
        item.status = "retired"


def test_a_serving_build_with_nothing_to_serve(tmp_path, seeded_ids, monkeypatch):
    calls = _spy_episode_reads(monkeypatch)

    def build(vault, repository, trace):
        calls.clear()
        return serve_due_queue(vault, repository, clock=CLOCK, session=SchedulerSession(session_id=SESSION),
                               offer_trace=trace)

    _check("admission_empty", _record(tmp_path, build, prepare=_retire_everything,
                                      extra=lambda: {"episode_reads": sorted(calls)}))


def _instrument_as_surface(vault: Any) -> None:
    """One of the episode's instruments a diagnostic surface (in memory), so the check split asks the probe gate."""

    vault.practice_items["pi_svd_define_002"].practice_mode = "diagnostic_probe"


def test_a_serving_build_under_recall_targets_and_a_check_on_the_probes_lo(tmp_path, seeded_ids):
    """Master and Light touch move the effective due (the forgetting risk) away from the stored one, and the due
    check on the probe's LO is split over candidates the probe gate decides."""

    _check("intent_targets_serving", _record(tmp_path, lambda vault, repository, trace: serve_due_queue(
        vault, repository, clock=CLOCK, session=SchedulerSession(session_id=SESSION), offer_trace=trace),
        vault_builder=build_intent_targets_vault, prepare=_instrument_as_surface))


def test_a_read_build_under_recall_targets(tmp_path, seeded_ids):
    _check("intent_targets_read", _record(tmp_path, lambda vault, repository, trace: read_due_queue(
        vault, repository, clock=CLOCK, offer_trace=trace), vault_builder=build_intent_targets_vault))


def test_a_serving_build_with_a_limit_and_a_generated_follow_up(tmp_path, seeded_ids):
    """The limit cuts the composed queue the slate and its record are written from; of two due cold retries the
    follow-up door inserts the one whose item is not a generated probe."""

    _check("limit_generated_followup_serving", _record(tmp_path, lambda vault, repository, trace: serve_due_queue(
        vault, repository, clock=CLOCK, session=SchedulerSession(session_id=SESSION), offer_trace=trace, limit=5),
        vault_builder=build_generated_followup_vault))


def test_a_read_build_with_a_limit(tmp_path, seeded_ids):
    _check("limit_read", _record(tmp_path, lambda vault, repository, trace: read_due_queue(
        vault, repository, clock=CLOCK, offer_trace=trace, limit=3)))


def _outside(tmp_path: Path, vault_builder: Any, prepare: Any = None) -> dict[str, Any]:
    """Every item asked of the two admissions built outside a queue, each over its own lazy reads."""

    vault, repository = vault_builder(tmp_path / "vault")
    if prepare is not None:
        prepare(vault)
    before = _database(repository.sqlite_path)
    now = CLOCK.now()
    refusal = pool_admission(vault, repository, now=now)
    pool = {item_id: refusal(item_id) for item_id in sorted(vault.practice_items)}
    check = check_admission(vault, repository, now=now, intent_view=intent_serving(vault, repository, now=now),
                            reasons=True)
    checks = {item_id: check(item_id) for item_id in sorted(vault.practice_items)}
    one_item = check_admission(vault, repository, now=now, intent_view=None, reasons=True)
    changes = _database_changes(before, _database(repository.sqlite_path))
    return _clean({"pool": pool, "check": checks, "one_item_only": one_item("pi_a1"), "database": changes}, _Ids())


def test_the_readers_outside_a_build_on_each_gate(tmp_path, seeded_ids):
    _check("outside_admission_gates", _outside(tmp_path, build_gate_vault))


def _a_valued_probe_surface(vault: Any) -> None:
    """Value stopping off and one of the episode's instruments a diagnostic surface (in memory: state sync would
    not change it, but a reload would), so the probe gate reads the episode for it."""

    _value_stopping_off(vault)
    vault.practice_items["pi_svd_define_002"].practice_mode = "diagnostic_probe"


def test_the_readers_outside_a_build_in_a_probe_episode(tmp_path, seeded_ids):
    _check("outside_admission_probe", _outside(tmp_path, build_rich_vault, _a_valued_probe_surface))


def test_the_admission_goldens_reach_their_paths(tmp_path, seeded_ids):
    """What the admission goldens are for: if a vault stops reaching a gate or a read, they stop pinning it."""

    gates = _record(tmp_path / "gates", lambda vault, repository, trace: serve_due_queue(
        vault, repository, clock=CLOCK, session=SchedulerSession(session_id=SESSION), offer_trace=trace),
        vault_builder=build_gate_vault)["trace"]["exclusions"]
    assert {
        "retired", "inactive_state", "reserved_exam", "cold_check_reserved", "diagnostic_microprobe",
        "diagnostic_probe_administered", "no_learning_object", "lifecycle_put_away", "intent_paused",
        "diagnostic_freshness_reserve", "placement_assumed_withheld", "diagnostic_reserved",
    } <= set(gates)
    probe = _record(tmp_path / "probe", lambda vault, repository, trace: serve_due_queue(
        vault, repository, clock=CLOCK, session=SchedulerSession(session_id="sess_probe_reads"), offer_trace=trace),
        vault_builder=build_probe_history_vault, prepare=_value_stopping_off)
    assert any(item["components"].get("probe_eig", 0.0) > 0 for item in probe["queue"]), "a probe is valued"
    assert any(
        0 < item["components"].get("probe_eig_familiarity_discount", 1.0) < 1 for item in probe["queue"]
    ), "an answer on the probe's LO discounts its probes"
    assert "elicitation_events" in probe["database"], "the probe selection is recorded"
    phone = _record(tmp_path / "phone", lambda vault, repository, trace: serve_due_queue(
        vault, repository, clock=CLOCK, session=SchedulerSession(session_id=SESSION), offer_trace=trace,
        device_filter=_phone(vault)), vault_builder=build_figure_vault)["trace"]["exclusions"]
    assert {"device_ineligible", "cold_start_unattempted"} <= set(phone)
    unconsulted = _record(tmp_path / "unconsulted", lambda vault, repository, trace: read_due_queue(
        vault, repository, clock=CLOCK, offer_trace=trace), vault_builder=build_unconsulted_episode_vault)
    assert unconsulted["trace"]["voi_decisions"] == [], "no item reached the episode's value decision"
    empty = _record(tmp_path / "empty", lambda vault, repository, trace: serve_due_queue(
        vault, repository, clock=CLOCK, session=SchedulerSession(session_id=SESSION), offer_trace=trace),
        prepare=_retire_everything)
    assert empty["queue"] == []


@pytest.mark.parametrize("vault_builder", [build_rich_vault, build_gate_vault], ids=["rich", "gates"])
def test_the_probe_value_decision_reads_nothing_where_it_is_computed(tmp_path, seeded_ids, monkeypatch,
                                                                     vault_builder):
    """The admission computes an episode's value decision where it consults it, from the gathered reads: the value
    context it gets reaches no repository (any read raises), and the decision is the one a context reading the
    repository itself returns, in a build and in the admission asked outside one."""

    from learnloop.diagnosis import voi_stopping as voi

    vault, repository = vault_builder(tmp_path / "vault")
    real = voi.probe_episode_decision
    computed: list[str] = []

    def checked(ctx, episode, eligible, posterior, **kwargs):
        with pytest.raises(RuntimeError, match="read the repository"):
            ctx.repository.connection()
        decision = real(ctx, episode, eligible, posterior, **kwargs)
        kwargs.pop("pinned_channel")
        reference = real(voi.VoiContext(vault, repository), episode, eligible, posterior, **kwargs)
        assert decision.as_dict() == reference.as_dict()
        computed.append(str(episode.id))
        return decision

    monkeypatch.setattr(voi, "probe_episode_decision", checked)
    read_due_queue(vault, repository, clock=CLOCK, session=SchedulerSession(session_id=SESSION))
    assert computed, "the build computed a value decision"
    computed.clear()
    refusal = pool_admission(vault, repository, now=CLOCK.now())
    for item_id in sorted(vault.practice_items):
        refusal(item_id)
    if vault_builder is build_gate_vault:
        assert computed, "the outside admission computed a value decision for its diagnostic surface"
