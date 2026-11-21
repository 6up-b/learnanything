"""How often a lesson's planned delayed check is actually answered cold: the receipts classified as of a decision, and
the one-trial seed's Beta posterior over that completion probability (spec_teacher_v2 §7.4). Unserved: nothing under
``src`` reads it yet; the successor that prices checks by it (``mvp-0.62``) is a later step. It sits beside
``delayed_checks``, not in ``router_objective``: it reads the intent resolver (``scheduling``), and the objective's
package importing that would close a package cycle the frozen-cycles import contract refuses.

**The trials.** One per planned entry of a closed lesson's receipt (``lesson_receipts.delayed_checks``), keyed by
lesson, purpose and node (the entry's place in the receipt when two share them), including the entries the picker
could not fill (``missing``): those never became commitments, and they are exactly what the old pricing ignored. At a
decision time ``as_of`` only what was recorded by then is read:

=========================================================  =================================================
The entry or its commitment, as of ``as_of``               Counts as
=========================================================  =================================================
the receipt records ``missing``                            a failure
its item has a graded answer on your own, cold at the      a success (right, partly right or wrong alike)
attempt, at or after the check's effective date
(or a satisfaction event says so; counted once)
stopped or replaced, with no such answer                   a failure
pending, not yet due, paused, answered but not yet         censored (neither), with its reason
graded, or otherwise not answered yet
a lesson still open, an offer declined, no entry           not a trial (never read: no receipt row exists)
=========================================================  =================================================

A success binds the entry's own item and commitment: the effective date is the commitment's (its ``due_hint``, moved
on by every attempt that was not on your own or not cold, as the intent resolver moves it,
``scheduling.intent.serving.build_checks``); "on your own" is ``serving.on_your_own``; "cold at the attempt" is
``serve_eligibility.check_once_at_attempt``; a grade is usable when the attempt has a correctness and its grade was
not held for review as of ``as_of`` (``held_grades``). Another attempt on the same topic never stands in. Settlement
(``intent.checks.settle_answered_checks``) is never called: its satisfaction events are read as evidence, and an
answer it has not yet settled is derived the same way it would derive it.

Retention and transfer are pooled apart; every entry so far is the vault-item picker's (:data:`LEGACY_REGIME`), so a
future generated regime is never pooled with it silently.

**The seed** (:func:`posterior`): ``e`` is 1 when the delayed checks' candidate rule finds an eligible question for the
topic at the decision, else 0; ``alpha = e + S`` and ``beta = (1 − e) + F``. One hypothetical promised check is one
seed observation (:data:`SEED_TRIALS`, basis ``legacy``, the only prior strength here): an empty vault predicts exactly
the availability, and each resolved check moves it. Pending checks are right-censored, not failures, so a learner who
has not come back is not counted against delivery a second time (the rollout's return model already prices that);
the censored counts are reported beside ``S`` and ``F`` so a reader can see how much is still unresolved.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

#: This reader's classification rule (a changed rule is a new version).
DELIVERY_POLICY_VERSION = "committed_check_delivery_v1"
#: The seed's identity: one trial at the decision's availability.
PRIORS_VERSION = "check_delivery_one_trial_seed_v1"
SEED_BASIS = "legacy"
#: One hypothetical promised check supplies one seed observation (design prior; basis ``legacy``: the all-or-nothing
#: availability rule the offer builder has always implied). The only prior strength in this estimate.
SEED_TRIALS = 1.0
#: The delivery regime of every receipt so far: the vault-item picker (``teacher.delayed``).
LEGACY_REGIME = "legacy_vault_item"
PURPOSES = ("retention", "transfer")

SUCCESS = "success"
FAILURE = "failure"
CENSORED = "censored"
NOT_A_TRIAL = "not_a_trial"

#: Why an entry counts as it does.
MISSING = "missing"
ANSWERED_COLD = "answered_cold"
SETTLED = "settled"
STOPPED = "stopped"
REPLACED = "replaced"
NOT_YET_DUE = "not_yet_due"
PAUSED = "paused"
NOT_PENDING = "not_pending"
UNGRADED = "ungraded"
PENDING = "pending"
NO_COMMITMENT = "no_commitment_recorded"
UNKNOWN_COMMITMENT = "commitment_unknown_as_of"

_SERVE = "serve"


@dataclass(frozen=True)
class Trial:
    """One planned delayed-check entry, classified as of the read."""

    key: str
    lesson_id: str
    purpose: str
    learning_object_id: str | None
    item_id: str | None
    commitment_id: str | None
    regime: str
    outcome: str
    reason: str
    #: the attempt that answered it (a success or an ungraded answer), or None
    attempt_id: str | None = None


@dataclass(frozen=True)
class DeliveryCounts:
    """The sufficient statistics for one purpose and regime as of ``as_of``."""

    purpose: str
    regime: str
    as_of: str
    successes: int
    failures: int
    censored_by_reason: Mapping[str, int]
    evidence_digest: str
    policy_version: str = DELIVERY_POLICY_VERSION

    @property
    def censored(self) -> int:
        return int(sum(self.censored_by_reason.values()))


@dataclass(frozen=True)
class DeliveryPosterior:
    """``Beta(alpha, beta)`` over the cold-completion probability of one committed check, or its limiting point mass
    at an endpoint (``alpha = 0``: exactly 0; ``beta = 0``: exactly 1)."""

    alpha: float
    beta: float
    eligible_now: bool
    counts: DeliveryCounts
    priors_version: str = PRIORS_VERSION
    basis: str = SEED_BASIS
    seed_trials: float = SEED_TRIALS
    extra: Mapping[str, Any] = field(default_factory=dict)

    @property
    def predictive_mean(self) -> float:
        return self.alpha / (self.alpha + self.beta)

    @property
    def endpoint(self) -> float | None:
        """The point mass at an endpoint, or None when both shapes are positive."""

        if self.alpha == 0.0:
            return 0.0
        if self.beta == 0.0:
            return 1.0
        return None

    def as_dict(self) -> dict[str, Any]:
        counts = self.counts
        return {"policy_version": counts.policy_version, "priors_version": self.priors_version, "basis": self.basis,
                "as_of": counts.as_of, "purpose": counts.purpose, "delivery_regime": counts.regime,
                "eligible_now": self.eligible_now, "successes": counts.successes, "failures": counts.failures,
                "censored_by_reason": dict(sorted(counts.censored_by_reason.items())), "alpha": self.alpha,
                "beta": self.beta, "predictive_mean": self.predictive_mean,
                "evidence_digest": counts.evidence_digest}


def posterior(counts: DeliveryCounts, *, eligible_now: bool) -> DeliveryPosterior:
    """The one-trial seed updated by the resolved trials: ``alpha = e + S``, ``beta = (1 − e) + F``."""

    e = SEED_TRIALS if eligible_now else 0.0
    return DeliveryPosterior(alpha=e + counts.successes, beta=(SEED_TRIALS - e) + counts.failures,
                             eligible_now=bool(eligible_now), counts=counts)


def counts(trials: Iterable[Trial], *, purpose: str, as_of: str, regime: str = LEGACY_REGIME) -> DeliveryCounts:
    """One purpose's and regime's statistics over classified trials (another purpose's never pooled in)."""

    chosen = sorted((trial for trial in trials if trial.purpose == purpose and trial.regime == regime
                     and trial.outcome != NOT_A_TRIAL), key=lambda trial: trial.key)
    censored: dict[str, int] = {}
    for trial in chosen:
        if trial.outcome == CENSORED:
            censored[trial.reason] = censored.get(trial.reason, 0) + 1
    digest = hashlib.sha256(json.dumps(
        [[trial.key, trial.outcome, trial.reason, trial.attempt_id] for trial in chosen],
        separators=(",", ":")).encode("utf-8")).hexdigest()
    return DeliveryCounts(purpose=purpose, regime=regime, as_of=as_of,
                          successes=sum(1 for trial in chosen if trial.outcome == SUCCESS),
                          failures=sum(1 for trial in chosen if trial.outcome == FAILURE),
                          censored_by_reason=censored, evidence_digest=digest)


# -- reading the receipts -----------------------------------------------------------------------------------------


def _table(connection: Any, name: str) -> bool:
    return connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)
                              ).fetchone() is not None


def _snapshots_as_of(connection: Any, as_of: str) -> dict[str, Any]:
    """Every commitment as it stood at ``as_of``: created by then, its head the latest version by then, its events
    those recorded by then, folded by the intent resolver's own fold."""

    from learnloop.db.stores import intent_reads as reads
    from learnloop.scheduling.intent.resolution import snapshot_from_rows

    if not reads.commitment_tables_present(connection):
        return {}
    commitments = [dict(row) for row in connection.execute(
        "SELECT id, created_action, created_at FROM commitments WHERE created_at <= ? ORDER BY created_at, id",
        (as_of,))]
    ids = [str(row["id"]) for row in commitments]
    versions: dict[str, list[dict[str, Any]]] = {}
    for row in reads.versions_for(connection, ids):
        if str(row["created_at"]) <= as_of:
            versions.setdefault(str(row["commitment_id"]), []).append(row)
    heads = {cid: max(rows, key=lambda r: int(r["version"])) for cid, rows in versions.items()}
    targets: dict[str, list[dict[str, Any]]] = {}
    for row in reads.head_targets_for(connection, [str(head["id"]) for head in heads.values()]):
        targets.setdefault(str(row["commitment_version_id"]), []).append(row)
    events: dict[str, list[dict[str, Any]]] = {}
    for row in reads.events_for(connection, ids):
        if str(row["created_at"]) <= as_of:
            events.setdefault(str(row["commitment_id"]), []).append(row)
    return {str(row["id"]): snapshot_from_rows(row, versions[str(row["id"])], targets.get(str(heads[str(row["id"])]
                                                                                           ["id"]), []),
                                               events.get(str(row["id"]), []))
            for row in commitments if str(row["id"]) in heads}


def _satisfied_by(connection: Any, commitment_id: str, as_of: str) -> list[str]:
    """The administrations settlement recorded as satisfying the commitment by ``as_of`` (attempt ids; may be empty
    strings for a satisfaction recorded without one)."""

    out = []
    for (detail,) in connection.execute(
            "SELECT detail_json FROM commitment_events WHERE commitment_id = ? AND kind = 'disposition_changed' "
            "AND created_at <= ? ORDER BY created_at, id", (commitment_id, as_of)):
        try:
            payload = json.loads(detail or "{}")
        except ValueError:
            continue
        if isinstance(payload, dict) and payload.get("disposition") == "satisfied":
            out.append(str(payload.get("administration_id") or ""))
    return out


def _settled_answer(connection: Any, commitment_id: str, as_of: str, *,
                    derived: Mapping[str, Any] | None) -> str | None:
    """A satisfaction recorded by ``as_of`` whose answer counts: the administration's attempt id when its grade is
    usable then, ``""`` for a satisfaction that names no attempt this store holds (the event is the evidence), or None
    (no satisfaction, or only ones whose answer was not graded yet, the derived answer's included)."""

    for administration in _satisfied_by(connection, commitment_id, as_of):
        if derived is not None and administration == str(derived["id"]):
            continue  # the derived answer, already judged ungraded at this read
        row = connection.execute("SELECT id, correctness FROM practice_attempts WHERE id = ?",
                                 (administration,)).fetchone() if administration else None
        if row is None:
            return ""
        if _grade_usable(connection, {"id": row[0], "correctness": row[1]}, as_of):
            return str(row[0])
    return None


def _grade_usable(connection: Any, attempt: Mapping[str, Any], as_of: str) -> bool:
    """The attempt's grade could be used at ``as_of``: it has a correctness, and it was not held for review then.

    The hold's record half is read as of ``as_of`` (the latest blind grade record recorded by then; an attempt whose
    grade arrived only later had no grade then). Its evidence half and the contract-unrecorded hold have no as-of form
    in the store: they are read as they stand now, and a hold that is released now only by evidence counts as released
    at ``as_of`` too."""

    from learnloop.held_grades import held_for_review_attempts
    from learnloop.outcome_contract import grade_held_for_review

    if attempt.get("correctness") is None:
        return False
    attempt_id = str(attempt["id"])
    held_now = attempt_id in held_for_review_attempts(connection, [attempt_id])
    if not _table(connection, "blind_grade_records"):
        return not held_now
    records = connection.execute(
        "SELECT record_json, created_at FROM blind_grade_records WHERE attempt_id = ? ORDER BY created_at, id",
        (attempt_id,)).fetchall()
    if not records:
        return not held_now
    known = [row for row in records if str(row[1]) <= as_of]
    if not known:
        return False
    try:
        record = json.loads(known[-1][0]) if isinstance(known[-1][0], str) else (known[-1][0] or {})
    except ValueError:
        record = {}
    held_then = isinstance(record, dict) and grade_held_for_review(record.get("grading_support"))
    later = len(known) < len(records)
    if held_then:
        # Held by the record of the time: released since only if no later record exists and nothing holds it now.
        return not later and not held_now
    # Not held by the record of the time: a hold now is a later record's (usable then), or the store's now-only one.
    return later or not held_now


def _answer(repository: Any, connection: Any, snapshot: Any, *, item_id: str, learning_object_id: str | None,
            as_of: str, default_days: int, known: str) -> tuple[Mapping[str, Any] | None, Any]:
    """The attempt that answers the check by ``as_of`` (the intent resolver's rule over the entry's own item), and the
    check's effective date then."""

    from learnloop.clock import parse_utc
    from learnloop.scheduling.intent.serving import check_date, on_your_own
    from learnloop.serve_eligibility import check_once_at_attempt

    when, _source = check_date(snapshot, default_days=default_days)
    cutoff = parse_utc(as_of)
    rows = [dict(row) for row in connection.execute(
        "SELECT id, practice_item_id, created_at, attempt_type, primed, hints_used, correctness "
        f"FROM practice_attempts WHERE practice_item_id = ? AND {known} <= ? ORDER BY created_at, id",
        (item_id, as_of))]
    for row in rows:
        at = parse_utc(str(row["created_at"]))
        if at is None or at < when:
            continue
        if cutoff is not None and at > cutoff:
            break
        verdict = check_once_at_attempt(repository, practice_item_id=item_id, learning_object_id=learning_object_id,
                                        attempt_id=str(row["id"]), attempt_at=str(row["created_at"]),
                                        check_created_at=snapshot.created_at).verdict
        if on_your_own(row) and verdict == _SERVE:
            return row, when
        # Practice, not a check on your own: it answers nothing and the check waits its delay again from it.
        when = at + timedelta(days=int(default_days))
    return None, when


def _replaced(snapshots: Mapping[str, Any], snapshot: Any, item_id: str, learning_object_id: str | None) -> bool:
    """Another commitment decides the check's item as of the read (the intent resolver's F21 rule for an item-level
    check)."""

    from learnloop.scheduling.intent.resolution import Resolution

    resolution = Resolution(snapshots.values(), {})
    return resolution.for_item(item_id, learning_object_id).decided_by != snapshot.id


def _outcome(repository: Any, connection: Any, entry: Mapping[str, Any], snapshots: Mapping[str, Any], *,
             as_of: str, cutoff: Any, default_days: int, known: str) -> tuple[str, str, str | None]:
    """One entry's ``(outcome, reason, answering attempt)`` as of ``as_of`` (the module's table, in its order)."""

    item = str(entry["item_id"]) if entry.get("item_id") else None
    lo = str(entry["learning_object_id"]) if entry.get("learning_object_id") else None
    commitment_id = str(entry["commitment_id"]) if entry.get("commitment_id") else None
    if entry.get("missing"):
        return FAILURE, MISSING, None
    if commitment_id is None or item is None:
        return NOT_A_TRIAL, NO_COMMITMENT, None
    snapshot = snapshots.get(commitment_id)
    if snapshot is None:
        return NOT_A_TRIAL, UNKNOWN_COMMITMENT, None
    answer, when = _answer(repository, connection, snapshot, item_id=item, learning_object_id=lo, as_of=as_of,
                           default_days=default_days, known=known)
    if answer is not None and _grade_usable(connection, answer, as_of):
        return SUCCESS, ANSWERED_COLD, str(answer["id"])
    # Settlement's own record of an answer, read as evidence: the answer derived above is counted once (its grade was
    # not usable yet); one this read did not derive counts when its grade is usable.
    graded = _settled_answer(connection, commitment_id, as_of, derived=answer)
    if graded is not None:
        return SUCCESS, SETTLED, graded or None
    if answer is not None:
        return CENSORED, UNGRADED, str(answer["id"])
    if snapshot.disposition == "stopped":
        return FAILURE, STOPPED, None
    if _replaced(snapshots, snapshot, item, lo):
        return FAILURE, REPLACED, None
    if snapshot.disposition == "paused":
        return CENSORED, PAUSED, None
    if snapshot.disposition != "one_check_pending":
        return CENSORED, NOT_PENDING, None
    if cutoff is not None and when > cutoff:
        return CENSORED, NOT_YET_DUE, None
    return CENSORED, PENDING, None


def classify(repository: Any, *, as_of: str, config: Any = None) -> tuple[Trial, ...]:
    """Every planned delayed-check entry of every lesson receipt recorded by ``as_of``, classified as of then.

    ``repository`` is attached read-only by the caller (``Repository.attach(path, read_only=True)``): nothing here
    writes, and settlement is never called. ``config`` (the vault's, or None for the defaults): the check's default
    delay (``capture.test_me_later_days``) and the attempt ledger's availability rule."""

    from learnloop.clock import parse_utc
    from learnloop.db.attempt_availability import attempt_time_sql

    default_days = int(getattr(getattr(config, "capture", None), "test_me_later_days", 7))
    known = attempt_time_sql(config)
    cutoff = parse_utc(as_of)
    out: list[Trial] = []
    with repository.connection() as connection:
        if not _table(connection, "lesson_receipts"):
            return ()
        snapshots = _snapshots_as_of(connection, as_of)
        receipts = connection.execute(
            "SELECT lesson_id, receipt_json FROM lesson_receipts WHERE created_at <= ? ORDER BY created_at, lesson_id",
            (as_of,)).fetchall()
        for lesson_id, raw in receipts:
            seen: set[str] = set()
            try:
                entries = json.loads(raw or "{}").get("delayed_checks") or ()
            except ValueError:
                entries = ()
            for ordinal, entry in enumerate(entries):
                purpose = str(entry.get("purpose") or "")
                key = f"lesson:{lesson_id}:{purpose}:{entry.get('node_id') or 'lesson'}"
                if key in seen:
                    key = f"{key}#{ordinal}"
                seen.add(key)
                outcome, reason, attempt_id = _outcome(repository, connection, entry, snapshots, as_of=as_of,
                                                       cutoff=cutoff, default_days=default_days, known=known)
                out.append(Trial(
                    key=key, lesson_id=str(lesson_id), purpose=purpose,
                    learning_object_id=str(entry["learning_object_id"]) if entry.get("learning_object_id") else None,
                    item_id=str(entry["item_id"]) if entry.get("item_id") else None,
                    commitment_id=str(entry["commitment_id"]) if entry.get("commitment_id") else None,
                    regime=LEGACY_REGIME, outcome=outcome, reason=reason, attempt_id=attempt_id))
    return tuple(out)


def statistics(repository: Any, *, as_of: str, config: Any = None,
               purposes: Sequence[str] = PURPOSES) -> dict[str, DeliveryCounts]:
    """Each purpose's counts as of ``as_of`` (the legacy regime's)."""

    trials = classify(repository, as_of=as_of, config=config)
    return {purpose: counts(trials, purpose=purpose, as_of=as_of) for purpose in purposes}


__all__ = [
    "ANSWERED_COLD", "CENSORED", "DELIVERY_POLICY_VERSION", "DeliveryCounts", "DeliveryPosterior", "FAILURE",
    "LEGACY_REGIME", "MISSING", "NOT_A_TRIAL", "NOT_PENDING", "NOT_YET_DUE", "PAUSED", "PENDING", "PRIORS_VERSION",
    "PURPOSES", "REPLACED", "SEED_BASIS", "SEED_TRIALS", "SETTLED", "STOPPED", "SUCCESS", "Trial", "UNGRADED",
    "classify", "counts", "posterior", "statistics",
]
