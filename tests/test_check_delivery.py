"""The as-of classifier of planned delayed-check receipts and the one-trial seed's posterior
(``learnloop.check_delivery``): synthetic rows for every class, read through a read-only attachment that
never settles anything.

Each case is one planned entry of a closed lesson's receipt with its own item and commitment; the decision times are
before and after the facts that change a class (a grade recorded late, a helped attempt that moves the date, a
settlement written after its answer).
"""

from __future__ import annotations

import ast
import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from learnloop.clock import FrozenClock
from learnloop.curriculum import commitments as C
from learnloop.db.migrate import apply_migrations
from learnloop.db.repositories import Repository
from learnloop import check_delivery as CD

CLOSE = datetime(2026, 11, 1, 9, 0, tzinfo=UTC)
DUE = CLOSE + timedelta(days=3)
EARLY = "2026-11-10T09:00:00Z"
LATE = "2026-11-14T09:00:00Z"
LO = "lo_a"


def _iso(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def _day(day: int, hour: int = 9) -> datetime:
    return datetime(2026, 11, day, hour, 0, tzinfo=UTC)


class _Vault:
    """A migrated database with lessons, their receipts, the commitments behind them and the attempts on their items."""

    def __init__(self, tmp_path):
        self.path = tmp_path / "state.sqlite"
        apply_migrations(self.path)
        self.repository = Repository(self.path)
        self.entries: dict[str, list[dict]] = {}
        self._attempts = 0

    def commit(self, item: str, *, node: str | None, purpose: str = "retention", due: datetime = DUE,
               at: datetime = CLOSE, lesson: str = "les1", lo: str = LO) -> str:
        commitment = C.create_commitment(
            self.repository, action="test_me_later", intent_text=f"one question on your own after a lesson ({purpose})",
            targets=[{"target_kind": "legacy_practice_item", "target_ref": item, "role": "required"}],
            depth_preset="keep_in_touch", client_idempotency_key=f"lesson:{lesson}:{purpose}:{node}",
            due_hint=_iso(due), reason=f"lesson_{purpose}_check",
            provenance={"via": "lesson", "lesson_id": lesson, "node_id": node, "purpose": purpose},
            clock=FrozenClock(at))
        self.entries.setdefault(lesson, []).append(
            {"purpose": purpose, "node_id": node, "learning_object_id": lo, "item_id": item,
             "commitment_id": commitment.id, "due": _iso(due)[:10], "dated_by": "fallback", "days": 3.0})
        return commitment.id

    def missing(self, *, node: str | None, purpose: str = "retention", lesson: str = "les1") -> None:
        self.entries.setdefault(lesson, []).append(
            {"purpose": purpose, "node_id": node, "learning_object_id": LO, "item_id": None, "commitment_id": None,
             "due": None, "missing": True})

    def close(self, lesson: str = "les1", *, at: datetime = CLOSE) -> None:
        with self.repository.connection() as connection:
            connection.execute(
                "INSERT INTO lessons(id, driver, origin, entry, goal_text, goal_json, learning_object_ids_json, "
                "doctrine_version, brief_version, algorithm_version, opened_at, closed_at, close_reason) "
                "VALUES (?, 'desktop', 'learner_pick', 'learning_object', 'teach me', '{}', ?, 'd', 'b', 'v', ?, ?, "
                "'goal_reached')", (lesson, json.dumps([LO]), _iso(at - timedelta(hours=1)), _iso(at)))
            connection.execute(
                "INSERT INTO lesson_receipts(lesson_id, receipt_version, close_reason, receipt_json, created_at) "
                "VALUES (?, 'lesson_receipt_v1', 'goal_reached', ?, ?)",
                (lesson, json.dumps({"delayed_checks": self.entries.get(lesson, [])}), _iso(at)))
            connection.commit()

    def attempt(self, item: str, at: datetime, *, correctness: float | None = 1.0, hints: int = 0,
                attempt_type: str = "independent_attempt", lo: str = LO) -> str:
        self._attempts += 1
        attempt_id = f"att{self._attempts:03d}"
        with self.repository.connection() as connection:
            connection.execute(
                "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
                "hints_used, correctness, latency_seconds, created_at) VALUES (?, ?, ?, 'short_answer', ?, ?, ?, 60, ?)",
                (attempt_id, item, lo, attempt_type, hints, correctness, _iso(at)))
            connection.commit()
        return attempt_id

    def blind(self, attempt_id: str, at: datetime, *, held: bool = False) -> None:
        support = {"proof_route_check": {"held_for_review": True, "version": "route_rule_v1"}} if held else {}
        with self.repository.connection() as connection:
            connection.execute(
                "INSERT INTO blind_grade_records(id, attempt_id, grading_prompt_version, output_schema_version, "
                "context_hash, record_json, created_at) VALUES (?, ?, 'p', 's', 'h', ?, ?)",
                (f"bg_{attempt_id}_{_iso(at)}", attempt_id, json.dumps({"grading_support": support}), _iso(at)))
            connection.commit()

    def reveal(self, item: str, at: datetime, *, lo: str) -> None:
        with self.repository.connection() as connection:
            connection.execute(
                "INSERT INTO reveal_events(id, practice_item_id, learning_object_id, source_kind, amount, basis, "
                "created_at) VALUES (?, ?, ?, 'tutor_answer', 1.0, 'test', ?)", (f"rv_{item}", item, lo, _iso(at)))
            connection.commit()

    def classify(self, as_of: str) -> dict[str, CD.Trial]:
        reader = Repository.attach(self.path, read_only=True)
        return {trial.key: trial for trial in CD.classify(reader, as_of=as_of)}


def _key(node: str | None, purpose: str = "retention", lesson: str = "les1") -> str:
    return f"lesson:{lesson}:{purpose}:{node or 'lesson'}"


@pytest.fixture
def vault(tmp_path, monkeypatch):
    """Every class in one receipt (and a second lesson's transfer entry), with settlement made to fail if called."""

    v = _Vault(tmp_path)
    v.missing(node="n_missing")
    v.commit("pi_right", node="n_right")
    v.commit("pi_wrong", node="n_wrong")
    v.commit("pi_helped", node="n_helped")
    v.commit("pi_early", node="n_early")
    v.commit("pi_late_grade", node="n_late_grade")
    v.commit("pi_pending", node="n_pending")
    v.commit("pi_future", node="n_future", due=_day(20))
    paused = v.commit("pi_paused", node="n_paused")
    resumed = v.commit("pi_resumed", node="n_resumed")
    stopped = v.commit("pi_stopped", node="n_stopped")
    v.commit("pi_replaced", node="n_replaced")
    settled = v.commit("pi_settled", node="n_settled")
    # On a topic of its own: a reveal holds every item of its topic, so it would make the other cases' answers warm.
    v.commit("pi_revealed", node="n_revealed", lo="lo_b")
    settled_only = v.commit("pi_settled_only", node="n_settled_only")
    v.missing(node=None, purpose="transfer")
    # An entry with neither a commitment nor the picker's "missing": nothing planned, so not a trial.
    v.entries["les1"].append({"purpose": "retention", "node_id": "n_unplanned", "learning_object_id": LO})
    v.close()
    # A second lesson: its transfer entry is answered; it is pooled with transfer only.
    v.commit("pi_transfer", node=None, purpose="transfer", lesson="les2")
    v.close("les2")

    v.attempt("pi_right", _day(5), correctness=1.0)
    v.attempt("pi_wrong", _day(5), correctness=0.0)
    v.attempt("pi_helped", _day(5), hints=1)  # not on your own: the check waits its 7 days again, to Nov 12
    v.attempt("pi_helped", _day(11))          # before the moved date: not its answer
    v.attempt("pi_early", _day(2))            # before the check's date: not its answer
    late = v.attempt("pi_late_grade", _day(5))
    v.blind(late, _day(12))                   # its grade is recorded a week after the answer
    C.pause(v.repository, commitment_id=paused, clock=FrozenClock(_day(3)))
    C.pause(v.repository, commitment_id=resumed, clock=FrozenClock(_day(3)))
    C.resume(v.repository, commitment_id=resumed, clock=FrozenClock(_day(3, 12)))
    C.retire(v.repository, commitment_id=stopped, clock=FrozenClock(_day(3)))
    C.create_commitment(v.repository, action="help_me_remember", intent_text="keep this one",
                        targets=[{"target_kind": "legacy_practice_item", "target_ref": "pi_replaced",
                                  "role": "required"}], depth_preset="work_fluently", clock=FrozenClock(_day(3)))
    answer = v.attempt("pi_settled", _day(5))
    C.satisfy_single_check(v.repository, commitment_id=settled, administration_id=answer, clock=FrozenClock(_day(6)))
    v.reveal("pi_revealed", _day(4, 12), lo="lo_b")  # the answer shown before the attempt: not cold
    v.attempt("pi_revealed", _day(5), lo="lo_b")
    v.attempt("pi_transfer", _day(9))
    # Settlement's record is read as evidence even where this read derives no answer (here an attempt before the
    # check's date, which the derivation skips).
    before = v.attempt("pi_settled_only", _day(2))
    C.satisfy_single_check(v.repository, commitment_id=settled_only, administration_id=before,
                           clock=FrozenClock(_day(3)))

    def refuse(*_args, **_kwargs):
        raise AssertionError("the reader called settlement")

    from learnloop.intent import checks as intent_checks

    monkeypatch.setattr(intent_checks, "settle_answered_checks", refuse)
    for name in ("satisfy_single_check", "change_disposition", "pause", "resume", "retire"):
        monkeypatch.setattr(C, name, refuse)
    return v


EXPECTED_EARLY = {
    _key("n_missing"): (CD.FAILURE, CD.MISSING),
    _key("n_right"): (CD.SUCCESS, CD.ANSWERED_COLD),
    _key("n_wrong"): (CD.SUCCESS, CD.ANSWERED_COLD),
    _key("n_helped"): (CD.CENSORED, CD.NOT_YET_DUE),
    _key("n_early"): (CD.CENSORED, CD.PENDING),
    _key("n_late_grade"): (CD.CENSORED, CD.UNGRADED),
    _key("n_pending"): (CD.CENSORED, CD.PENDING),
    _key("n_future"): (CD.CENSORED, CD.NOT_YET_DUE),
    _key("n_paused"): (CD.CENSORED, CD.PAUSED),
    _key("n_resumed"): (CD.CENSORED, CD.NOT_PENDING),
    _key("n_stopped"): (CD.FAILURE, CD.STOPPED),
    _key("n_replaced"): (CD.FAILURE, CD.REPLACED),
    _key("n_settled"): (CD.SUCCESS, CD.ANSWERED_COLD),
    _key("n_revealed"): (CD.CENSORED, CD.NOT_YET_DUE),
    _key("n_settled_only"): (CD.SUCCESS, CD.SETTLED),
    _key("n_unplanned"): (CD.NOT_A_TRIAL, CD.NO_COMMITMENT),
    _key(None, "transfer"): (CD.FAILURE, CD.MISSING),
    _key(None, "transfer", "les2"): (CD.SUCCESS, CD.ANSWERED_COLD),
}


def test_every_class_as_of_a_decision(vault):
    trials = vault.classify(EARLY)
    assert {key: (trial.outcome, trial.reason) for key, trial in trials.items()} == EXPECTED_EARLY
    assert {trial.regime for trial in trials.values()} == {CD.LEGACY_REGIME}
    assert trials[_key("n_right")].attempt_id and trials[_key("n_missing")].commitment_id is None


def test_a_later_decision_sees_the_late_grade_and_the_redated_answer(vault):
    """As of Nov 14 the late grade is recorded (a success); the helped check, moved to Nov 12 by its helped attempt,
    is answered by the cold attempt of Nov 13 (the one of Nov 11 came before the moved date and answered nothing)."""

    answer = vault.attempt("pi_helped", _day(13))
    trials = vault.classify(LATE)
    assert (trials[_key("n_late_grade")].outcome, trials[_key("n_late_grade")].reason) == (CD.SUCCESS,
                                                                                            CD.ANSWERED_COLD)
    assert (trials[_key("n_helped")].outcome, trials[_key("n_helped")].attempt_id) == (CD.SUCCESS, answer)
    # The revealed item's attempt was not cold: its check waits to Nov 12, and nothing has answered it since.
    assert (trials[_key("n_revealed")].outcome, trials[_key("n_revealed")].reason) == (CD.CENSORED, CD.PENDING)


def test_before_its_answer_is_known_nothing_counts(vault):
    """An attempt recorded after the decision is not read: the answered checks are censored at Nov 4, 18:00."""

    trials = vault.classify("2026-11-04T18:00:00Z")
    assert (trials[_key("n_right")].outcome, trials[_key("n_right")].reason) == (CD.CENSORED, CD.PENDING)
    assert (trials[_key("n_settled")].outcome, trials[_key("n_settled")].reason) == (CD.CENSORED, CD.PENDING)
    # A receipt recorded after the decision is not a trial yet.
    assert all(trial.lesson_id in {"les1", "les2"} for trial in trials.values())
    assert vault.classify("2026-10-31T09:00:00Z") == {}


def test_a_settled_answer_counts_once_before_and_after_its_settlement(vault):
    for as_of in ("2026-11-05T12:00:00Z", EARLY):
        trials = vault.classify(as_of)
        counted = CD.counts(trials.values(), purpose="retention", as_of=as_of)
        assert trials[_key("n_settled")].outcome == CD.SUCCESS
        assert trials[_key("n_settled")].attempt_id == "att007"
    assert counted.successes == 4  # right, wrong, settled, settled_only: once each


def test_retention_and_transfer_are_pooled_apart(vault):
    trials = vault.classify(EARLY).values()
    retention = CD.counts(trials, purpose="retention", as_of=EARLY)
    transfer = CD.counts(trials, purpose="transfer", as_of=EARLY)
    assert (retention.successes, retention.failures, retention.censored) == (4, 3, 8)
    assert dict(retention.censored_by_reason) == {CD.NOT_YET_DUE: 3, CD.PENDING: 2, CD.UNGRADED: 1, CD.PAUSED: 1,
                                                  CD.NOT_PENDING: 1}
    assert (transfer.successes, transfer.failures, transfer.censored) == (1, 1, 0)
    assert retention.evidence_digest != transfer.evidence_digest
    assert CD.statistics(Repository.attach(vault.path, read_only=True), as_of=EARLY)["retention"] == retention


def test_the_reader_writes_nothing_and_settles_nothing(vault):
    before = hashlib.sha256(vault.path.read_bytes()).hexdigest()
    vault.classify(EARLY)
    vault.classify(LATE)
    assert hashlib.sha256(vault.path.read_bytes()).hexdigest() == before
    with pytest.raises(Exception, match="readonly|read-only|attempt to write"):
        with Repository.attach(vault.path, read_only=True).connection() as connection:
            connection.execute("INSERT INTO lessons(id) VALUES ('x')")


# --- the seed and its posterior ----------------------------------------------------------------------------------


def _counts(successes: int, failures: int) -> CD.DeliveryCounts:
    return CD.DeliveryCounts(purpose="retention", regime=CD.LEGACY_REGIME, as_of=EARLY, successes=successes,
                             failures=failures, censored_by_reason={}, evidence_digest="d")


def test_an_empty_vault_predicts_exactly_the_availability():
    available = CD.posterior(_counts(0, 0), eligible_now=True)
    absent = CD.posterior(_counts(0, 0), eligible_now=False)
    assert (available.alpha, available.beta, available.predictive_mean, available.endpoint) == (1.0, 0.0, 1.0, 1.0)
    assert (absent.alpha, absent.beta, absent.predictive_mean, absent.endpoint) == (0.0, 1.0, 0.0, 0.0)
    assert available.priors_version == CD.PRIORS_VERSION and available.basis == "legacy"
    assert available.seed_trials == 1.0


def test_resolved_checks_move_the_seed():
    """The documented legacy sample: retention ``S = 0, F = 19`` (the five transfer failures are not pooled in)."""

    unavailable = CD.posterior(_counts(0, 19), eligible_now=False)
    available = CD.posterior(_counts(0, 19), eligible_now=True)
    assert (unavailable.alpha, unavailable.beta, unavailable.predictive_mean) == (0.0, 20.0, 0.0)
    assert (available.alpha, available.beta) == (1.0, 19.0)
    assert available.predictive_mean == pytest.approx(0.05) and available.endpoint is None
    # Evidence can raise a topic with no question today above zero (availability is a seed, never a factor).
    assert CD.posterior(_counts(3, 1), eligible_now=False).predictive_mean == pytest.approx(0.6)
    record = available.as_dict()
    assert record["successes"] == 0 and record["failures"] == 19 and record["delivery_regime"] == CD.LEGACY_REGIME
    assert record["policy_version"] == CD.DELIVERY_POLICY_VERSION and record["eligible_now"] is True


def test_nothing_served_reads_the_statistics_yet():
    """No module under ``src`` imports the reader (by name, from its package, or through importlib) until the
    activation wires it."""

    root = Path(__file__).resolve().parents[1]
    hits = []
    for path in sorted((root / "src").rglob("*.py")):
        if path.name == "check_delivery.py":
            continue
        text = path.read_text(encoding="utf-8")
        if "check_delivery" not in text:
            continue
        for node in ast.walk(ast.parse(text)):
            if isinstance(node, ast.ImportFrom) and ((node.module or "").endswith("check_delivery")
                                                     or any(alias.name == "check_delivery" for alias in node.names)):
                hits.append(str(path.relative_to(root)))
            elif isinstance(node, ast.Import) and any(alias.name.endswith("check_delivery") for alias in node.names):
                hits.append(str(path.relative_to(root)))
            elif isinstance(node, ast.Call) and getattr(node.func, "attr", getattr(node.func, "id", "")) in {
                    "import_module", "__import__"} and any(
                    isinstance(arg, ast.Constant) and "check_delivery" in str(arg.value) for arg in node.args):
                hits.append(str(path.relative_to(root)))
    assert hits == []
