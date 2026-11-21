"""Read-only, aggregate check-credit audit. Run against a backup-API copy.

No policy is activated here. Historical values need lossless replay inputs; rounded traces
are evidence of recorded values, never a license to subtract a guessed check bonus.
Directory inputs also permit a present-day lesson-versus-stop scenario. Database-only
inputs deliberately cannot reconstruct authored content or current candidate eligibility.
"""

from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager
from dataclasses import fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
import hashlib
import importlib.util
import json
import logging
import math
from pathlib import Path
import sqlite3
import sys

import numpy as np

from learnloop.db.repositories import Repository
from learnloop.plan_refs import LESSON_OFFER_PREFIX as PREFIX
from learnloop.router_objective import check_value as CV
from learnloop.router_objective import mix, rollouts as ROL, types as OT
from learnloop.router_objective.objective import numeric_choice
from learnloop.daily_plan import check_delivery as CD

REPLAY_VERSION = "check_credit_report_replay_v1"
HISTORICAL_MISSING = [
    "lossless numeric Inputs (all topics, uses, FSRS, AD, combiner, learning and return models)",
    "complete candidate actions including declined branches and forecasts",
    "original numeric seed, completed draws, cutoff and evaluator options",
    "decision-time eligibility, protection/lifecycle view, delivery sensors and duration provenance",
]
AS_OF_MISSING = [
    "historical authored items/goals and protection/lifecycle view",
    "historical fitted models, session state, price and candidate support",
    "unrounded numeric inputs, original numeric seed and refinement settings",
    "grade-hold evidence releases have no complete as-of representation",
]


def _precedent():
    spec = importlib.util.spec_from_file_location(
        "check_credit_copy_reader", Path(__file__).with_name("probe_router_report.py"))
    module = importlib.util.module_from_spec(spec)
    # The precedent's dataclass annotations resolve through its registered module.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class _ReadConnection:
    def __init__(self, connection):
        self.raw = connection

    def __getattr__(self, name):
        return getattr(self.raw, name)

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        # Nested store reads must not end the report's coherent read transaction.
        return False


@contextmanager
def open_repository(path):
    precedent = _precedent()
    database = precedent._database(Path(path))
    connection = precedent.open_read_only(database)
    connection.execute("PRAGMA query_only = ON")
    connection.execute("BEGIN")
    repository = Repository.attach(database, read_only=True)
    repository._pin.connection = _ReadConnection(connection)
    audit = {"write_requested": False}
    repository._report_audit = audit
    writes = {sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_DELETE, sqlite3.SQLITE_CREATE_TABLE,
              sqlite3.SQLITE_DROP_TABLE, sqlite3.SQLITE_ALTER_TABLE, sqlite3.SQLITE_CREATE_INDEX,
              sqlite3.SQLITE_DROP_INDEX, sqlite3.SQLITE_CREATE_TRIGGER, sqlite3.SQLITE_DROP_TRIGGER,
              sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH}

    def authorize(action, *_args):
        if action in writes:
            # A dependency swallowing a read-only error must not make its fallback look like measured evidence.
            audit["write_requested"] = True
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK

    connection.set_authorizer(authorize)
    try:
        yield repository
    finally:
        repository._pin.connection = None
        connection.rollback()
        connection.close()


def _json(raw, default):
    try:
        return json.loads(raw) if raw else default
    except (TypeError, ValueError):
        return default


def _has(db, table):
    return db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None


def _purpose(value):
    return value if value in CD.PURPOSES else "other"


def _statistics(trials, at):
    result = {}
    for purpose in CD.PURPOSES:
        counts = CD.counts(trials, purpose=purpose, as_of=at)
        def shapes(e, counts=counts):
            p = CD.posterior(counts, eligible_now=e)
            return dict(alpha=p.alpha, beta=p.beta, predictive_mean=p.predictive_mean)
        s, f = counts.successes, counts.failures
        result[purpose] = {
            "S": s, "F": f, "censored": counts.censored,
            "censored_by_reason": dict(counts.censored_by_reason),
            "seed_if_unavailable": shapes(False), "seed_if_available": shapes(True),
            "without_seed": {"alpha": s, "beta": f, "predictive_mean": s / (s + f) if s + f else None},
        }
    return result


def _current_eligibility(vault, repository, offers, traces):
    from learnloop.daily_plan.check_inputs import eligible_now

    counts = dict(offers=len(offers), available=0, unavailable=0, unknown=0)
    for offer in offers:
        candidate = traces.get(offer["id"], {}).get("candidates", {}).get(offer["chosen_ref"], {})
        topic = candidate.get("main_lo") or offer.get("chosen_learning_object_id")
        if not topic:
            row = next((c for c in _json(offer["candidates_json"], [])
                        if c.get("ref") == offer["chosen_ref"]), {})
            los = row.get("learning_object_ids") or []
            topic = los[0] if len(los) == 1 else None
        key = "unknown" if vault is None or not topic else (
            "available" if eligible_now(vault, repository, topic) else "unavailable")
        counts[key] += 1
    return counts


def _entries(repository, trials, at, config):
    from learnloop.clock import parse_utc
    from learnloop.db.attempt_availability import attempt_time_sql
    from learnloop.scheduling.intent.serving import check_date, on_your_own

    db = repository.connection()
    snapshots = CD._snapshots_as_of(db, at)
    known = attempt_time_sql(config)
    default_days = int(getattr(getattr(config, "capture", None), "test_me_later_days", 7))
    counts = dict(planned_by_purpose=dict(Counter(_purpose(t.purpose) for t in trials)),
                  missing=0, canonical=0, due=0, presented=0, cold_answered=0, helped_only=0,
                  presented_without_commitment_binding=0,
                  terminally_abandoned=0, censored=0, not_a_trial=0,
                  cold_correctness=dict(correct=0, partial=0, wrong=0, unknown=0))
    ages = []
    for trial in trials:
        counts["missing"] += trial.reason == CD.MISSING
        counts["canonical"] += trial.commitment_id in snapshots
        counts["terminally_abandoned"] += trial.reason in (CD.STOPPED, CD.REPLACED)
        counts["censored"] += trial.outcome == CD.CENSORED
        counts["not_a_trial"] += trial.outcome == CD.NOT_A_TRIAL
        if trial.outcome == CD.SUCCESS:
            counts["cold_answered"] += 1
            row = db.execute("SELECT correctness FROM practice_attempts WHERE id=?", (trial.attempt_id,)).fetchone()
            value = row[0] if row else None
            label = "unknown" if value is None else "correct" if value >= 1 else "wrong" if value <= 0 else "partial"
            counts["cold_correctness"][label] += 1
        snapshot = snapshots.get(trial.commitment_id)
        if snapshot is None or not trial.item_id:
            continue
        initial_due, _ = check_date(snapshot, default_days=default_days)
        _, effective_due = CD._answer(repository, db, snapshot, item_id=trial.item_id,
                                      learning_object_id=trial.learning_object_id, as_of=at,
                                      default_days=default_days, known=known)
        counts["due"] += effective_due <= parse_utc(at)
        if trial.outcome == CD.CENSORED:
            ages.append(max(0.0, (parse_utc(at) - effective_due).total_seconds() / 86400))
        # Presentation is an observed item presentation while this check was due, never a cold-answer label.
        presented = unbound = False
        if _has(db, "plan_presentations"):
            for row in db.execute("SELECT p.served_at,b.commitment_id FROM plan_presentations p "
                                  "LEFT JOIN attention_blocks b ON b.id=p.block_id "
                                  "WHERE p.practice_item_id=? AND p.served_at<=?",
                                  (trial.item_id, at)):
                when = parse_utc(row[0])
                if when and when >= initial_due:
                    # An answer in the presentation's own second cannot retroactively make its display not due.
                    before = (when - timedelta(microseconds=1)).isoformat().replace("+00:00", "Z")
                    _, due_then = CD._answer(repository, db, snapshot, item_id=trial.item_id,
                                            learning_object_id=trial.learning_object_id, as_of=before,
                                            default_days=default_days, known=known)
                    if when >= due_then:
                        presented |= row[1] == trial.commitment_id
                        unbound |= row[1] != trial.commitment_id
        counts["presented"] += presented
        counts["presented_without_commitment_binding"] += unbound and not presented
        attempts = db.execute(
            f"SELECT attempt_type, primed, hints_used, created_at FROM practice_attempts WHERE practice_item_id=? "
            f"AND {known}<=? AND created_at<=?", (trial.item_id, at, at))
        helped = any(not on_your_own(dict(row)) and parse_utc(row["created_at"]) >= initial_due for row in attempts)
        counts["helped_only"] += helped and trial.outcome != CD.SUCCESS
    counts["censored_overdue_days"] = {"mean": sum(ages) / len(ages) if ages else None,
                                       "max": max(ages) if ages else None}
    return counts


def _number(value):
    return float(value) if isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value) else None


def _summary(rows):
    if not rows:
        return None
    keys = sorted(set().union(*(r.keys() for r in rows)))
    out = {}
    for key in keys:
        values = [v for r in rows if (v := _number(r.get(key))) is not None]
        out[key] = {"n": len(values), "mean": sum(values) / len(values) if values else None}
    return out


class _MeteredModel(CV._CheckModel):
    """Observe the evaluator's actual in-window minutes, including an unfinished check."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.check_minutes = np.zeros(self.k)

    def _on_return(self, state, ledger, checks):
        run = super()._on_return(state, ledger, checks)

        def measured(*args, **kwargs):
            used, after = run(*args, **kwargs)
            self.check_minutes += used
            return used, after
        return measured


def paired_scenario(inputs, old_actions, proposed_actions, *, draws, seed, options=None, mixing=None, offer_ref=None):
    """Both numeric policies on exactly the same frozen inputs and named random seed."""
    options = dict(options or {})
    def without_checks(action):
        return replace(action, commitments=(), checks=(),
                       steps=tuple(without_checks(s) for s in action.steps),
                       repair=without_checks(action.repair) if action.repair else None,
                       declined=without_checks(action.declined) if action.declined else None)
    if [without_checks(a) for a in old_actions] != [without_checks(a) for a in proposed_actions]:
        raise ValueError("paired actions differ in non-check inputs")
    old = ROL.evaluate(inputs, old_actions, draws=draws, max_draws=draws, seed=seed, **options)
    new = CV.evaluate(inputs, proposed_actions, draws=draws, max_draws=draws, seed=seed, **options)
    support = [a.ref for a in old_actions if a.choosable]
    if [a.ref for a in proposed_actions if a.choosable] != support:
        raise ValueError("paired support differs")
    old_choice = numeric_choice(old, support)[0]
    new_choice = numeric_choice(new, support)[0]
    old_rows, new_rows = old.by_ref(), new.by_ref()
    changed_mu = None
    if mixing is not None:
        old_mu = mix.recompute({**mixing, "numeric_choice": old_choice})
        new_mu = mix.recompute({**mixing, "numeric_choice": new_choice})
        changed_mu = any(old_mu[ref] != new_mu[ref] for ref in support)
    offers = []
    for action in proposed_actions:
        if action.kind != OT.LESSON or action.accept is None or (offer_ref is not None and action.ref != offer_ref):
            continue
        before, after = old_rows[action.ref], new_rows[action.ref]
        def terms(row):
            b = row.extra["branches"]
            return {"q": row.q, "accepted": b["accepted"], "declined": b["declined"],
                    "p_accept": b["p_accept"], "at_half_acceptance": (b["accepted"] + b["declined"]) / 2,
                    "accepted_terms": row.extra.get("branch_terms", {}).get("accepted"),
                    "declined_terms": row.extra.get("branch_terms", {}).get("declined")}
        # Counting only completed answers would omit the minutes of a check clipped at the horizon.
        model = _MeteredModel(inputs, draws, seed, **options)
        model._do(replace(action, accept=None))
        answer_times = [check.answered_at for check in model.tail_checks]
        p = ROL._beta_draw(model.streams.offer_u, *action.accept)
        completed = sum((np.isfinite(t).astype(float) for t in answer_times), start=np.zeros(draws))
        minutes = model.check_minutes
        a, b = terms(before), terms(after)
        offers.append({"old": a, "proposed": b, "difference": after.q - before.q,
                       "difference_at_half_acceptance": b["at_half_acceptance"] - a["at_half_acceptance"],
                       "expected_completed_checks": float(np.mean(p * completed)),
                       "expected_check_minutes": float(np.mean(p * minutes)),
                       "accepted_expected_completed_checks": float(np.mean(completed)),
                       "accepted_expected_check_minutes": float(np.mean(minutes))})
    rank = lambda rows: sorted(range(len(support)), key=lambda i: -rows[support[i]].q)
    return {"offers": offers, "numeric_ranking_changed": rank(old_rows) != rank(new_rows),
            "numeric_choice_changed": old_choice != new_choice, "mixing_probability_changed": changed_mu}


def _codec(value, *, decode=False):
    from learnloop.router_objective.ad_link import AdLink, LessonCurve
    from learnloop.router_objective.memory import Combiner

    classes = (OT.Inputs, OT.Action, OT.Topic, OT.DatedUse, OT.Price, OT.Learning,
               OT.EffectSlope, OT.CauseSplit, OT.CheckCommitment, AdLink, LessonCurve, Combiner)
    registry = {cls.__name__: cls for cls in classes}
    if not decode and is_dataclass(value):
        if type(value) not in classes:
            raise ValueError("unsupported numeric type")
        return {"type": type(value).__name__, "fields": {f.name: _codec(getattr(value, f.name)) for f in fields(value)}}
    if isinstance(value, dict):
        if decode and set(value) == {"type", "fields"}:
            cls = registry[value["type"]]
            if set(value["fields"]) != {f.name for f in fields(cls)}:
                raise ValueError("incomplete numeric snapshot")
            return cls(**{k: _codec(v, decode=True) for k, v in value["fields"].items()})
        return {k: _codec(v, decode=decode) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        result = [_codec(v, decode=decode) for v in value]
        return tuple(result) if decode else result
    return value


def replay_record(inputs, old_actions, proposed_actions, *, seed, draws, as_of, options, mixing=None):
    """Unserved lossless payload contract for synthetic/future traces; the JSON string survives trace rounding."""
    body = {"inputs": inputs, "old_actions": old_actions, "proposed_actions": proposed_actions,
            "seed": seed, "draws": draws, "as_of": as_of, "options": options, "mixing": mixing,
            "delivery_policy": CD.DELIVERY_POLICY_VERSION, "priors": CD.PRIORS_VERSION,
            "rollout_policy": CV.POLICY_VERSION, "streams": CV.STREAM_LAYOUT_VERSION}
    payload = json.dumps(_codec(body), sort_keys=True, separators=(",", ":"), allow_nan=False)
    return {"version": REPLAY_VERSION, "payload": payload, "sha256": hashlib.sha256(payload.encode()).hexdigest()}


def _replay(record, at, chosen_ref, support):
    if record.get("version") != REPLAY_VERSION:
        raise ValueError("unsupported replay version")
    payload = record["payload"]
    if not isinstance(payload, str) or hashlib.sha256(payload.encode()).hexdigest() != record["sha256"]:
        raise ValueError("invalid replay digest")
    body = _codec(json.loads(payload), decode=True)
    if body["as_of"] != at or not body["seed"] or body["draws"] < 1:
        raise ValueError("missing original clock, seed or draws")
    if chosen_ref not in {a.ref for a in body["old_actions"]}:
        raise ValueError("replay belongs to another offer")
    if {a.ref for a in body["old_actions"] if a.choosable} != set(support):
        raise ValueError("incomplete frozen candidate support")
    if (body["delivery_policy"], body["priors"], body["rollout_policy"], body["streams"]) != (
            CD.DELIVERY_POLICY_VERSION, CD.PRIORS_VERSION, CV.POLICY_VERSION, CV.STREAM_LAYOUT_VERSION):
        raise ValueError("unsupported numeric policy")
    return paired_scenario(body["inputs"], body["old_actions"], body["proposed_actions"],
                           draws=body["draws"], seed=body["seed"], options=body["options"], mixing=body["mixing"],
                           offer_ref=chosen_ref)


def _comparison(label, total, missing, results):
    rows = [row for result in results for row in result["offers"]]
    values = _summary([{**{f"old_{k}": r["old"][k] for k in ("q", "accepted", "declined")},
                        **{f"proposed_{k}": r["proposed"][k] for k in ("q", "accepted", "declined")},
                        **{k: r[k] for k in ("difference", "expected_completed_checks", "expected_check_minutes")}}
                       for r in rows])
    branch_terms = {policy: {branch: _summary([r[policy].get(f"{branch}_terms") or {} for r in rows])
                             for branch in ("accepted", "declined")} for policy in ("old", "proposed")}
    sensors = Counter(json.dumps(s, sort_keys=True) for r in results for s in r.get("delivery_posteriors", []))
    return {"label": label, "status": "computable" if results else "not computable", "computable": len(results),
            "not_computable": total - len(results), "missing_inputs": missing if len(results) < total else [],
            "values": values, "branch_terms": branch_terms,
            "delivery_posteriors": [{**json.loads(s), "checks": n} for s, n in sorted(sensors.items())],
            "numeric_ranking_changed": sum(r["numeric_ranking_changed"] for r in results),
            "numeric_choice_changed": sum(r["numeric_choice_changed"] for r in results),
            "mixing_computable": sum(r["mixing_probability_changed"] is not None for r in results),
            "mixing_probability_changed": sum(r["mixing_probability_changed"] is True for r in results)}


def build_report(path, *, as_of=None, draws=8):
    at = as_of or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    path = Path(path)
    vault = None
    if path.is_dir():
        from learnloop.vault.loader import load_vault

        vault = load_vault(path, load_environment=False)
    config = vault.config if vault else None
    with open_repository(path) as repository:
        db = repository.connection()
        decisions = [dict(r) for r in db.execute("SELECT * FROM router_decisions WHERE created_at<=? ORDER BY created_at,id",
                                                (at,))] if _has(db, "router_decisions") else []
        traces = {r["decision_id"]: _json(r["trace_json"], {}) for r in db.execute(
            "SELECT decision_id,trace_json FROM router_objective_traces WHERE created_at<=? ORDER BY created_at,id",
            (at,))} if _has(db, "router_objective_traces") else {}
        candidate_count = 0
        offers = []
        for decision in decisions:
            candidates = _json(decision["candidates_json"], [])
            refs = {str(c.get("ref") or c.get("candidate_id") or "") for c in candidates
                    if isinstance(c, dict) and c.get("feasible", True)}
            refs.update(traces.get(decision["id"], {}).get("candidates", {}))
            candidate_count += sum(ref.startswith(PREFIX) for ref in refs)
            if str(decision["chosen_ref"] or "").startswith(PREFIX):
                offers.append(decision)
        responses = Counter()
        linked = dict(open=0, closed=0, not_opened=0)
        seen_lessons = set()
        offered_lessons, alternative_lessons = set(), set()
        shown = no_shown = 0
        bindings = Counter()
        has_responses = _has(db, "router_suggestion_responses")
        if not has_responses:
            bindings["router_suggestion_responses_table_missing"] = len(offers)
        for decision in offers:
            did = decision["id"]
            response = db.execute(
                "SELECT * FROM router_suggestion_responses WHERE decision_id=? AND responded_at<=? "
                "AND response IN ('accepted','chose_alternative','declined','ignored')", (did, at)).fetchone() \
                if has_responses else None
            status = response["response"] if response else "unanswered"
            if response is None and has_responses:
                expired = db.execute("SELECT detail_json FROM router_suggestion_responses WHERE decision_id=? "
                                     "AND response='expired' AND responded_at<=?", (did, at)).fetchone()
                detail = _json(expired[0], {}) if expired else {}
                if detail.get("superseded_by_decision"):
                    status = "superseded"
                elif detail.get("withdrawn") == "never_shown":
                    status = "never_shown"
            responses[status] += 1
            displayed = db.execute(
                "SELECT 1 FROM attention_block_events WHERE kind='offer_shown' AND created_at<=? "
                "AND json_extract(detail_json,'$.decision_id')=? LIMIT 1", (at, did)).fetchone()
            shown += displayed is not None
            no_shown += displayed is None
            if response and response["lesson_id"]:
                lesson = db.execute("SELECT opened_at,closed_at FROM lessons WHERE id=? AND opened_at<=?",
                                    (response["lesson_id"], at)).fetchone()
                if lesson is None:
                    linked["not_opened"] += response["lesson_id"] not in seen_lessons
                    seen_lessons.add(response["lesson_id"])
                    bindings["response_lesson_row_missing"] += 1
                    continue
                closed = lesson[1] is not None and lesson[1] <= at
                linked["closed" if closed else "open"] += response["lesson_id"] not in seen_lessons
                seen_lessons.add(response["lesson_id"])
                if status == "chose_alternative":
                    alternative_lessons.add(response["lesson_id"])
                elif response["candidate_ref"] == decision["chosen_ref"]:
                    offered_lessons.add(response["lesson_id"])
                else:
                    bindings["accepted_candidate_mismatch"] += 1
                if closed and db.execute("SELECT 1 FROM lesson_receipts WHERE lesson_id=? AND created_at<=?",
                                         (response["lesson_id"], at)).fetchone() is None:
                    bindings["closed_lesson_receipt_missing"] += 1
            elif status in ("accepted", "chose_alternative"):
                bindings["response_lesson_id_missing"] += 1
        trials = CD.classify(repository, as_of=at, config=config)
        populations = {"lesson_candidates_in_support": candidate_count, "offers_drawn": len(offers),
                       "offers_shown": shown, "offers_without_shown_receipt": no_shown,
                       "responses": dict(responses), "linked_lessons": linked,
                       "binding_gaps": dict(bindings)}
        for name, cohort in (("all_receipt_entries", trials),
                             ("offered_lesson_entries", [t for t in trials if t.lesson_id in offered_lessons]),
                             ("alternative_lesson_entries", [t for t in trials if t.lesson_id in alternative_lessons])):
            populations[name] = _entries(repository, cohort, at, config)
        time_groups = Counter(o["created_at"] for o in offers)
        delivery = {"basis": CD.SEED_BASIS, "priors_version": CD.PRIORS_VERSION,
                    "regime": CD.LEGACY_REGIME, "now": _statistics(trials, at),
                    "current_eligibility": _current_eligibility(vault, repository, offers, traces),
                    "decision_time_groups": [{"offers": n, **_statistics(
                        CD.classify(repository, as_of=t, config=config), t)} for t, n in sorted(time_groups.items())],
                    "eligibility": "historical eligibility unavailable; both one-trial seeds shown",
                    "settings_basis": "copy configuration" if config else "reader defaults; vault configuration unavailable",
                    "limitations": ["resolved-outcome sampling can overestimate completion with persistent censoring",
                                    "grade-hold evidence releases are read in their current state",
                                    "historical capture delay and attempt-availability settings are not frozen"]}
        exact, current, recorded = [], [], []
        exact_reasons, current_reasons = Counter(), Counter()
        for offer in offers:
            trace = traces.get(offer["id"], {})
            candidate = (trace.get("candidates") or {}).get(offer["chosen_ref"], {})
            term = (candidate.get("offer") or {}).get("terms") or {}
            recorded.append({"q": (candidate.get("terms") or {}).get("q"),
                             "accepted": term.get("q_accepted"), "declined": term.get("q_declined")})
            replay = trace.get("check_credit_replay")
            if replay:
                try:
                    support = [c.get("ref") or c.get("candidate_id") for c in _json(offer["candidates_json"], [])
                               if c.get("feasible", True)]
                    exact.append(_replay(replay, offer["created_at"], offer["chosen_ref"], support))
                except (KeyError, TypeError, ValueError):
                    exact_reasons["invalid_or_unsupported_replay_payload"] += 1
            else:
                exact_reasons["rounded_trace_only" if trace else "no_trace"] += 1
            if vault is None:
                current_reasons["authored_vault_and_configuration_unavailable"] += 1
            else:
                try:
                    current.append(_current_pair(vault, repository, offer, candidate, at, draws))
                except (KeyError, TypeError, ValueError, sqlite3.Error):
                    current_reasons["offer_action_or_plan_price_inputs_unavailable"] += 1
        comparisons = {
            "exact_historical": _comparison("EXACT historical counterfactual", len(offers), HISTORICAL_MISSING, exact),
            "as_of_reconstruction": _comparison("AS-OF reconstruction", len(offers), AS_OF_MISSING, []),
            "current_copy": _comparison("CURRENT-COPY paired scenario", len(offers),
                                         ["authored vault, recorded offer action, plan remembered minutes and price"], current),
        }
        comparisons["exact_historical"]["coverage_reasons"] = dict(exact_reasons)
        comparisons["current_copy"]["coverage_reasons"] = dict(current_reasons)
        comparisons["current_copy"]["rollout_options"] = current[0]["options"] if current else None
        comparisons["current_copy"]["scope"] = (
            "present-day inputs; recorded offer contract and plan price; lesson versus stop only; "
            "not a historical correction or historical mixing comparison")
        write_requested = repository._report_audit["write_requested"]
        return {"version": "check_credit_report_v1", "populations": populations, "delivery": delivery,
                "recorded_old_values": _summary(recorded), "comparisons": comparisons,
                "stop_conditions": {"binding_gaps": bool(bindings),
                                    "dependency_requested_write": write_requested,
                                    "no_stored_value_comparison": bool(offers) and not exact and not current}}


def _current_pair(vault, repository, offer, candidate, at, draws):
    from learnloop.daily_plan import check_inputs as CI, objective_inputs as OI
    from learnloop.daily_plan.types import BlockCandidate, PlanState

    action = candidate["offer"]["action"]
    lo = candidate["main_lo"]
    if lo not in vault.learning_objects:
        raise ValueError("authored topic unavailable")
    db = repository.connection()
    plan = db.execute("SELECT p.id,p.remembered_minutes FROM attention_blocks b JOIN daily_plans p "
                      "ON p.id=b.daily_plan_id WHERE b.decision_ref=?", (offer["id"],)).fetchone()
    price = db.execute("SELECT kappa0 FROM router_objective_traces WHERE decision_id=?", (offer["id"],)).fetchone()
    if plan is None or plan[1] is None or price is None or price[0] is None:
        raise ValueError("plan or price unavailable")
    ref = offer["chosen_ref"]
    record = {"learning_object_id": lo, "duration": {"median_minutes": action["minutes"],
              "log_sd": action["minutes_log_sd"]}, "mass": {"mean": action["mass"]},
              "p_accept": {"beta": action["accept"]},
              "checks": [{"lo": c[0], "days": c[1]} for c in action["commitments"]]}
    block = BlockCandidate(ref, "new", "instruct", "lesson_offer", (lo,), (), None,
                           action["minutes"], 0.0, "", annotations={"lesson_offer": record})
    state = PlanState(plan[0], "normal", plan[1], plan[1], {}, 0, 0, None)
    inputs, _, _ = OI.build(vault, repository, state=state, support=[ref, OT.STOP_FOR_TODAY],
                            candidates={ref: block}, now_iso=at, kappa0=float(price[0]), kappa_how="recorded_scenario")
    old = OT.Action(ref=ref, kind=OT.LESSON, item_los=(lo,), minutes=action["minutes"],
                    minutes_log_sd=action["minutes_log_sd"], mass=action["mass"], accept=tuple(action["accept"]),
                    commitments=tuple(tuple(c) for c in action["commitments"]))
    stats = CD.statistics(repository, as_of=at, config=vault.config)
    checks, sensors = [], []
    for i, (topic, days) in enumerate(old.commitments):
        posterior = CD.posterior(stats["retention"], eligible_now=CI.eligible_now(vault, repository, topic))
        duration = CI.dry_check_minutes(vault, repository, topic, as_of=at)
        checks.append(OT.CheckCommitment(topic, days, duration.minutes, (posterior.alpha, posterior.beta),
                                         f"scenario-{i}"))
        sensors.append({"purpose": "retention", "S": posterior.counts.successes, "F": posterior.counts.failures,
                        "censored_by_reason": dict(posterior.counts.censored_by_reason),
                        "eligible_now": posterior.eligible_now, "alpha": posterior.alpha, "beta": posterior.beta,
                        "predictive_mean": posterior.predictive_mean, "minutes": duration.minutes,
                        "duration_basis": duration.basis})
    proposed = replace(old, commitments=(), checks=tuple(checks))
    stop = OT.Action(ref=OT.STOP_FOR_TODAY, kind=OT.STOP)
    from learnloop.daily_plan.objective_chooser import rollout_options

    # The rollouts' options the copy's tag serves (the review draw, merged sessions, the held link): without them the
    # scenario would run the pre-mvp-0.50 review draw, which can flip the sign of a check's effect.
    return {**paired_scenario(inputs, [old, stop], [proposed, stop], draws=draws, seed="check-credit-current-copy-v1",
                              options=rollout_options(vault.config)),
            "delivery_posteriors": sensors, "options": rollout_options(vault.config)}


def render(report):
    p = report["populations"]
    lines = ["Check credit: aggregate read-only audit", "population | count",
             *[f"{k} | {p[k]}" for k in ("lesson_candidates_in_support", "offers_drawn", "offers_shown",
                                        "offers_without_shown_receipt")],
             f"responses | {json.dumps(p['responses'], sort_keys=True)}",
             f"linked lessons | {json.dumps(p['linked_lessons'], sort_keys=True)}"]
    lines.append("entries | retention | transfer | missing | canonical | due | presented | cold | helped | abandoned | censored")
    for cohort in ("offered_lesson_entries", "alternative_lesson_entries", "all_receipt_entries"):
        e = p[cohort]
        counts = [e["planned_by_purpose"].get(purpose, 0) for purpose in CD.PURPOSES]
        counts.extend(e[k] for k in ("missing", "canonical", "due", "presented", "cold_answered", "helped_only",
                                     "terminally_abandoned", "censored"))
        lines.append(cohort + " | " + " | ".join(str(n) for n in counts))
        lines.append("  cold correctness: " + json.dumps(e["cold_correctness"], sort_keys=True)
                     + f"; presentations without commitment binding: {e['presented_without_commitment_binding']}")
        lines.append("  censored overdue days: " + json.dumps(e["censored_overdue_days"], sort_keys=True))
    lines.append("delivery | purpose | S | F | censored | seed e=0 (alpha,beta,mean) | seed e=1 | no seed")
    groups = [(f"decision group {i} ({g['offers']} offers)", g)
              for i, g in enumerate(report["delivery"]["decision_time_groups"], 1)]
    groups.append(("now", report["delivery"]["now"]))
    for name, group in groups:
        for purpose in CD.PURPOSES:
            g = group[purpose]
            def shapes(key, g=g):
                v = g[key]
                return f"({v['alpha']},{v['beta']},{v['predictive_mean']})"
            lines.append(f"{name} | {purpose} | {g['S']} | {g['F']} | {g['censored']} | "
                         f"{shapes('seed_if_unavailable')} | {shapes('seed_if_available')} | {shapes('without_seed')}")
            if g["censored_by_reason"]:
                lines.append("  censored: " + json.dumps(g["censored_by_reason"], sort_keys=True))
    lines.append("Current eligibility: " + json.dumps(report["delivery"]["current_eligibility"], sort_keys=True))
    lines.append("Historical eligibility unavailable unless frozen; the two seed columns are sensitivity scenarios.")
    lines.extend(report["delivery"]["limitations"])
    lines.append("recorded old values | " + json.dumps(report["recorded_old_values"], sort_keys=True))
    for value in report["comparisons"].values():
        lines.append(f"{value['label']} | {value['computable']} computable; {value['not_computable']} not computable")
        if value["values"]:
            lines.append("  means: " + json.dumps({k: v["mean"] for k, v in value["values"].items()}, sort_keys=True))
        if value["delivery_posteriors"]:
            lines.append("  delivery: " + json.dumps(value["delivery_posteriors"], sort_keys=True))
        lines.append(f"  changed ranking: {value['numeric_ranking_changed']}/{value['computable']}; "
                     f"changed numeric choice: {value['numeric_choice_changed']}/{value['computable']}; "
                     f"changed mixing probability: {value['mixing_probability_changed']}/{value['mixing_computable']}")
        if value["missing_inputs"]:
            lines.append("  missing: " + "; ".join(value["missing_inputs"]))
        if value.get("coverage_reasons"):
            lines.append("  coverage: " + json.dumps(value["coverage_reasons"], sort_keys=True))
        if value.get("scope"):
            lines.append("  " + value["scope"])
    lines.append("stop conditions | " + json.dumps(report["stop_conditions"], sort_keys=True))
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", type=Path, required=True, help="backup copy directory or database")
    parser.add_argument("--as-of", help="UTC report cutoff; defaults to now")
    parser.add_argument("--draws", type=int, default=8, help="current-copy scenario draws")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    if args.draws < 1:
        parser.error("draws must be positive")
    # Dependency warnings may contain ids or paths. Only this report's allowlisted aggregates reach the CLI.
    previous = logging.root.manager.disable
    logging.disable(logging.CRITICAL)
    try:
        report = build_report(args.vault, as_of=args.as_of, draws=args.draws)
        output = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) if args.json else render(report)
        if args.out:
            database = _precedent()._database(args.vault).resolve()
            root = args.vault.resolve() if args.vault.is_dir() else database.parent
            if args.out.resolve() == database or args.out.resolve().is_relative_to(root):
                parser.error("--out must be outside the vault copy")
            args.out.write_text(output + "\n", encoding="utf-8")
        else:
            print(output)
    except Exception:  # noqa: BLE001 - exception messages from vault readers can contain learner text
        print("Report unavailable: copy could not be read safely; no vault content printed.", file=sys.stderr)
        return 2
    finally:
        logging.disable(previous)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
