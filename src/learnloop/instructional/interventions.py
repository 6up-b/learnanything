"""Retrieval in the evidence loop: the intervention records (spec_source_practice_and_probes_v1 §11; S5).

A ``retrieval_interventions`` row is written only when a retrieved asset is
SHOWN or SERVED, never when it is merely retrieved:

* a tutor answer citing retrieved (or pinned) spans; a passage offer opened;
* a comparison shown;
* a remediation passage delivered (ranked by S3's provider);
* a proposal picked (an item, or a textbook exercise to import);
* a need fulfilled from the sources and served.

Each row keeps references, not copies: the assets with their revisions, the
targets, the state the valuation read (problem keys and table hashes), the
valued check's predicted P(E), regime and minutes, the impressions displayed
before the pick, the independence verdict at valuation and at serving time,
and R1's learner_pick row when one exists. ``source_service.interventions``
off writes nothing. Reports only: nothing reads these rows to serve.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from contextlib import closing
from datetime import datetime, timedelta
import json
import math
from typing import Any

from learnloop.clock import Clock, FrozenClock, parse_utc, utc_now_iso
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.practice_index import proposal as stored_proposal
from learnloop.db.stores.source_service import (
    KEY_STATUS_LABELS,
    effective_key_status,
    exercise_import_ids,
    impressions_for_proposal,
    insert_intervention,
    interventions as stored_interventions,
    outcomes as stored_outcomes,
    tool_call,
    tool_call_runs,
)
from learnloop.ids import new_ulid
from learnloop.instructional.policy import caller_for_question_event
from learnloop.source_retrieval.policy import derive_policy
from learnloop.substrate.intervention_outcomes import (
    COLD_STATES,
    MEASURED_COLD_STATES,
    SUCCESS_CORRECTNESS,
    rebuild_intervention_outcomes,
)
from learnloop.vault.models import LoadedVault

ASSOCIATIONS_LABEL = ("Associations, not causes: improvement after an explanation doesn't show the explanation "
                      "caused it.")


def interventions_active(vault: LoadedVault) -> bool:
    config = vault.config.source_service
    return bool(config.enabled and config.interventions)


def record_intervention(vault: LoadedVault, repository: Repository, *, kind: str,
                        clock: Clock | None = None,
                        existing: Callable[[Any], str | None] | None = None, **fields: Any) -> str | None:
    """Append one intervention row; None (nothing written) when the switch is off.

    ``existing`` makes the write idempotent: a row it finds (inside the same
    write transaction) is returned instead of writing another (a delivery is
    recorded once however often its item is served)."""

    if not interventions_active(vault):
        return None
    with repository.atomic():
        connection = repository.connection()
        found = existing(connection) if existing is not None else None
        if found is not None:
            return found
        intervention_id = "rti_" + new_ulid()
        insert_intervention(connection, id=intervention_id, created_at=utc_now_iso(clock), kind=kind,
                            algorithm_version=vault.config.algorithms.algorithm_version, **fields)
    return intervention_id


def _pick_delivery(proposal_id: str, practice_item_id: str | None,
                   import_id: str | None) -> Callable[[Any], str | None]:
    """One delivery per picked proposal candidate (Codex re-review F10)."""

    def find(connection: Any) -> str | None:
        for row in stored_interventions(connection, proposal_id=proposal_id):
            if row["kind"] not in ("practice_pick", "source_exercise"):
                continue
            assets = row.get("assets") or {}
            if (list(assets.get("practice_item_ids") or []) == ([practice_item_id] if practice_item_id else [])
                    and assets.get("import_id") == import_id):
                return str(row["id"])
        return None

    return find


def _revision_ids(repository: Repository, extraction_ids: Sequence[str]) -> dict[str, Any]:
    found = {}
    for extraction_id in sorted(set(extraction_ids)):
        run = repository.get_extraction_run(extraction_id) or {}
        found[extraction_id] = run.get("revision_id")
    return found


def _check_entry(valuation: Mapping[str, Any] | None, ref: str) -> dict[str, Any] | None:
    """The valued check (or valued candidate) for ``ref`` in a proposal's
    valuation receipt: the calibration fields (§11.4)."""

    for section in (valuation or {}).get("problems") or ():
        valued = list((section.get("groups") or {}).get("valued") or ())
        for check in [*(section.get("checks") or ()), *valued]:
            if check.get("ref") == ref:
                problem = section.get("problem") or {}
                listed = next((entry for entry in valued if entry.get("ref") == ref), {})

                def field(name: str) -> Any:
                    return check.get(name) if check.get(name) is not None else listed.get(name)

                return {"problem": problem.get("key"), "regime": check.get("regime"),
                        "robust_eig_nats": field("robust_eig_nats"), "point_eig_nats": field("point_eig_nats"),
                        "value_minutes_lcb": field("value_minutes_lcb"),
                        "value_minutes_ucb": field("value_minutes_ucb"),
                        "expected_minutes": field("expected_minutes"),
                        "predicted_outcomes": field("predicted_outcomes"),
                        "likelihood_basis": listed.get("likelihood_basis"),
                        # What calibration replays the observation against
                        # (§11.4; Codex re-review F11): the problem's prior and
                        # state, the check's member-0 likelihood, EVSI and the
                        # decision's action before and after each outcome.
                        "prior": problem.get("prior"), "state_hash": problem.get("state_hash"),
                        "prior_basis": problem.get("prior_basis"), "likelihood": field("likelihood"),
                        "evsi": check.get("evsi"), "action_before": check.get("action_before"),
                        "action_by_outcome": check.get("action_by_outcome"),
                        "named_action": section.get("named_action"), "action_kind": section.get("action_kind"),
                        "verdict": section.get("verdict"), "mode": section.get("mode"),
                        "check_order": check.get("order", check.get("check_order")),
                        "scale": section.get("scale")}
    return None


def _state_ref(valuation: Mapping[str, Any] | None) -> dict[str, Any]:
    problems = []
    for section in (valuation or {}).get("problems") or ():
        problem = section.get("problem") or {}
        problems.append({"key": problem.get("key"), "space_kind": problem.get("space_kind"),
                         "state_hash": problem.get("state_hash"), "prior_basis": problem.get("prior_basis"),
                         "refs": problem.get("refs") or []})
    return {"problems": problems} if problems else {}


def _exposure_moments(verdict: Mapping[str, Any]) -> list[datetime]:
    """When the verdict's related exposures happened: the persisted stamps,
    else (a verdict recorded before them) its check time less the age it
    measured then."""

    moments: list[datetime] = []
    checked = parse_utc(verdict.get("checked_at")) if verdict.get("checked_at") else None
    worked = verdict.get("worked_example") or {}
    inputs = verdict.get("inputs") or {}
    for stamp, seconds in ((worked.get("related_exposure_at"), worked.get("seconds_since_exposure")),
                           (inputs.get("impression_at"), inputs.get("seconds_since_impression"))):
        moment = parse_utc(str(stamp)) if stamp else None
        if moment is None and seconds is not None and checked is not None:
            moment = checked - timedelta(seconds=float(seconds))
        if moment is not None:
            moments.append(moment)
    return moments


def seconds_since_related_exposure(verdicts: Sequence[Mapping[str, Any] | None], *, now: str) -> float | None:
    """Seconds from the most recent related exposure any verdict records to
    ``now`` (the delivery), or None when none records one (Codex third pass F13)."""

    moments = [moment for verdict in verdicts if verdict for moment in _exposure_moments(verdict)]
    delivered = parse_utc(now)
    if not moments or delivered is None:
        return None
    return round(max(0.0, (delivered - max(moments)).total_seconds()), 1)


def record_pick(vault: LoadedVault, repository: Repository, *, proposal_id: str, practice_item_id: str | None = None,
                exercise: Mapping[str, Any] | None = None, serve_verdict: Mapping[str, Any] | None = None,
                session_id: str | None = None, router_decision_id: str | None = None,
                import_id: str | None = None, clock: Clock | None = None) -> str | None:
    """A picked proposal delivered: an item (``practice_pick``) or an imported
    textbook exercise (``source_exercise``, with the item it became).

    Called after the serving path succeeded. ``router_decision_id`` is the
    decision that path returned (R1's row for the block that served it); the
    current decision is never inferred from a "latest matching row"."""

    if not interventions_active(vault):
        return None
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        found = stored_proposal(connection, proposal_id) or {}
        impressions = [row["id"] for row in impressions_for_proposal(connection, proposal_id)]
    valuation = found.get("valuation")
    ref = str((exercise or {}).get("key") or "") if exercise is not None else (practice_item_id or "")
    check = _check_entry(valuation, ref)
    eligibility = None
    valuation_time = ((valuation or {}).get("eligibility") or {}).get(ref)
    if valuation_time is not None or serve_verdict is not None:
        eligibility = {"valuation_time": valuation_time, "serve_time": serve_verdict}
    label = None
    for verdict in (valuation_time, serve_verdict):
        if verdict and verdict.get("label"):
            label = verdict["label"]
    constraints = found.get("constraints") or {}
    if exercise is None and practice_item_id:
        item = vault.practice_items.get(practice_item_id)
        assets = {"practice_item_ids": [practice_item_id],
                  "family_ids": [item.family_id] if item is not None and item.family_id else []}
        facets = list(constraints.get("facet_ids") or (item.evidence_facets if item is not None else []))
        kind = "practice_pick"
    else:
        entry = dict(exercise or {})
        assets = {"exercise_key": entry.get("key"),
                  "span_keys": [f"{entry.get('extraction_id')}:{span}" for span in entry.get("span_ids") or ()],
                  "source_versions": {str(entry.get("extraction_id")): entry.get("revision_id")}}
        if practice_item_id:
            assets["practice_item_ids"] = [practice_item_id]
        if import_id:
            assets["import_id"] = import_id
        facets = list(constraints.get("facet_ids") or (entry.get("provisional") or {}).get("facets") or [])
        kind = "source_exercise"
    # The time since the most recent related exposure (router §15.2's
    # covariate): a related worked example studied, or an earlier impression
    # of the question, as the eligibility rule recorded them (re-review F11),
    # measured at THIS delivery from when each exposure happened, never as
    # the age a verdict computed at its own check time (third pass F13).
    delivered = utc_now_iso(clock)
    since = seconds_since_related_exposure((serve_verdict, valuation_time), now=delivered)
    return record_intervention(
        vault, repository, kind=kind, clock=FrozenClock(parse_utc(delivered)),
        existing=_pick_delivery(proposal_id, practice_item_id, import_id),
        caller_kind=found.get("caller") or "learner",
        caller_ref=found.get("caller_ref"), intent=found.get("intent") or constraints.get("intent") or "practice",
        policy="reading", proposal_id=proposal_id, router_decision_id=router_decision_id, assets=assets,
        targets={"facets": facets, "learning_object_ids": list(constraints.get("learning_object_ids") or ()),
                 "hypotheses": list(constraints.get("target_hypotheses") or ())},
        state_ref=_state_ref(valuation), valuation=check, impression_ids=impressions,
        reading_exposure_label=label, eligibility=eligibility, seconds_since_related_exposure=since,
        session_id=session_id)


def record_tutor_citations(vault: LoadedVault, repository: Repository, event_id: str, *,
                           clock: Clock | None = None) -> str | None:
    """A tutor answer citing retrieved or pinned spans (``source_passage``)."""

    if not interventions_active(vault):
        return None
    event = repository.question_event(event_id) or {}
    source_context = event.get("source_context") or {}
    citations = source_context.get("citations") or []
    basis = (source_context.get("source_retrieval") or {}).get("basis")
    if not citations or basis not in ("retrieved_verified", "pinned"):
        return None
    caller = caller_for_question_event(vault, repository, event_id)
    policy, _ = derive_policy(caller)
    keys = [f"{c['extraction_id']}:{c['span_id']}" for c in citations]
    return record_intervention(
        vault, repository, kind="source_passage", clock=clock, caller_kind="tutor", caller_ref=event_id,
        intent=(source_context.get("source_retrieval") or {}).get("intent") or "explain", policy=policy,
        question_event_id=event_id,
        assets={"span_keys": keys, "source_versions": _revision_ids(repository, [c["extraction_id"] for c in citations]),
                "basis": basis},
        targets={"facets": list(event.get("facets") or ()), "learning_object_ids": list(caller.learning_object_ids),
                 "practice_item_ids": [caller.item_id] if caller.item_id else []},
        session_id=event.get("session_id"), attempt_id=event.get("attempt_id"))


def record_shown_spans(repository: Repository, keys: Sequence[str], *, context: str, entity_type: str,
                       entity_id: str, source_versions: Mapping[str, Any] | None = None,
                       clock: Clock | None = None) -> list[str]:
    """One ``source_exposure_events`` row per span whose text became visible.

    Written whatever ``source_service.interventions`` says: the exposure rule
    (§5.4 rule 3), the coldness receipts and the Reader's progress read these
    rows, so a passage shown on any surface stops being "unseen" (Codex F3).
    """

    parsed = []
    for key in keys:
        extraction_id, _, span_id = str(key).partition(":")
        if extraction_id and span_id:
            parsed.append((extraction_id, span_id))
    if not parsed:
        return []
    from learnloop.db.stores.source_block_fts import blocks_by_key
    from learnloop.ingest.locators import format_block_span

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        blocks = blocks_by_key(connection, parsed)
    versions = dict(source_versions or {})
    ids = []
    for extraction_id, span_id in dict.fromkeys(parsed):
        block = blocks.get((extraction_id, span_id))
        revision_id = versions.get(extraction_id)
        if revision_id is None:
            revision_id = (repository.get_extraction_run(extraction_id) or {}).get("revision_id")
        revision = repository.get_source_revision(str(revision_id or "")) or {}
        ids.append(repository.insert_source_exposure_event({
            "context": context, "extraction_id": extraction_id, "span_id": span_id,
            "revision_id": revision_id, "source_id": revision.get("source_id"),
            "entity_type": entity_type, "entity_id": entity_id,
            "page": getattr(block, "page", None), "locator": format_block_span(extraction_id, span_id),
            "section_path": list(getattr(block, "section_path", None) or []),
        }, clock=clock))
    return ids


def record_offer_shown(vault: LoadedVault, repository: Repository, tool_call_id: str, *,
                       span_keys: Sequence[str] = (), session_id: str | None = None,
                       clock: Clock | None = None) -> str | None:
    """A tool's passage offer opened (``source_passage``) or comparison shown (``comparison``)."""

    return offer_shown(vault, repository, tool_call_id, span_keys=span_keys, session_id=session_id,
                       clock=clock)["intervention_id"]


def offer_shown(vault: LoadedVault, repository: Repository, tool_call_id: str, *,
                span_keys: Sequence[str] = (), session_id: str | None = None,
                clock: Clock | None = None) -> dict[str, Any]:
    """The passages that became visible are recorded as exposure first, always;
    the intervention (when ``interventions`` is on) links those rows."""

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        request = tool_call(connection, tool_call_id)
        runs = tool_call_runs(connection, tool_call_id) if request is not None else []
    if request is None or request["row_kind"] != "request":
        raise ValueError(f"No tool request {tool_call_id}")
    kinds = {"find_sources": "source_passage", "compare_sources": "comparison"}
    if request["tool"] not in kinds:
        raise ValueError(f"{request['tool']} results are recorded when a proposal is picked")
    ran = [run for run in runs if run["status"] == "ran"]
    if not ran:
        raise ValueError("This tool request has not run")
    run = ran[-1]
    keys = [key for key in run["result_keys"] if not span_keys or key in set(span_keys)]
    arguments = request["arguments"]
    exposure_ids = record_shown_spans(
        repository, keys, context="tutor_citation" if request["caller_kind"] == "tutor" else "library",
        entity_type="source_tool_call", entity_id=tool_call_id, source_versions=run["source_versions"],
        clock=clock)
    intervention_id = record_intervention(
        vault, repository, kind=kinds[request["tool"]], clock=clock, caller_kind=request["caller_kind"],
        caller_ref=request["caller_ref"], intent=arguments.get("intent") or ("compare" if request["tool"]
                                                                              == "compare_sources" else None),
        policy=run["policy"], tool_call_id=tool_call_id,
        question_event_id=request["caller_ref"] if request["caller_kind"] == "tutor" else None,
        assets={"span_keys": keys, "source_versions": run["source_versions"], "result_ref": run["result_ref"],
                "exposure_event_ids": exposure_ids},
        targets={"facets": list(arguments.get("facet_ids") or ()),
                 "hypotheses": list(arguments.get("target_hypotheses") or ()),
                 "practice_item_ids": [request["context"]["item_id"]] if request["context"].get("item_id") else []},
        session_id=session_id)
    return {"intervention_id": intervention_id, "exposure_event_ids": exposure_ids}


def record_remediation_delivery(vault: LoadedVault, repository: Repository, episode: Mapping[str, Any], *,
                                clock: Clock | None = None) -> str | None:
    """Ranked remediation passages delivered (``remediation_passage``); the fallback prescription is not retrieval."""

    passages = [p for p in episode.get("passages_shown") or [] if isinstance(p, Mapping)
                and p.get("basis") == "ranked_verified"]
    if not passages:
        return None
    views = [p.get("span_view") or {} for p in passages]
    keys = [f"{view.get('extraction_id')}:{view.get('span_id')}" for view in views if view.get("extraction_id")]
    return record_intervention(
        vault, repository, kind="remediation_passage", clock=clock, caller_kind="remediation",
        caller_ref=str(episode.get("id")), intent="remediate", policy="reading",
        remediation_episode_id=str(episode.get("id")),
        assets={"span_keys": keys, "source_versions": {str(v.get("extraction_id")): v.get("revision_id") for v in views}},
        targets={"facets": sorted({str(p["facet_id"]) for p in passages if p.get("facet_id")}),
                 "hypotheses": [{"kind": "misconception", "id": str(episode.get("case_ref"))}]
                 if episode.get("case_ref") else []})


def record_need_served(vault: LoadedVault, repository: Repository, need: Mapping[str, Any], *,
                       practice_item_id: str, proposal_id: str | None = None, session_id: str | None = None,
                       clock: Clock | None = None) -> str | None:
    """A need fulfilled from the sources and then served (``source_exercise``)."""

    return record_intervention(
        vault, repository, kind="source_exercise", clock=clock, caller_kind="need", caller_ref=str(need["id"]),
        intent="remediate", policy="reading", proposal_id=proposal_id,
        assets={"practice_item_ids": [practice_item_id]},
        targets={"facets": list(need.get("target_facets") or ()),
                 "learning_object_ids": [str(need.get("learning_object_id"))]},
        session_id=session_id, attempt_id=need.get("attempt_id"))


# -- the report (§11.3) -------------------------------------------------------------------


def _wilson(successes: int, n: int, z: float = 1.96) -> list[float] | None:
    if n == 0:
        return None
    p = successes / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [round(max(0.0, centre - half), 4), round(min(1.0, centre + half), 4)]


def _rates(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    nexts = [row for row in rows if row.get("next_correctness") is not None]
    next_successes = sum(1 for row in nexts if float(row["next_correctness"]) >= SUCCESS_CORRECTNESS)
    measured = [row for row in rows if row.get("cold_outcome_state") in MEASURED_COLD_STATES]
    cold_successes = sum(1 for row in measured if row["cold_outcome_state"] == "cold_success")
    return {
        "n": len(rows),
        "R_next": {"n": len(nexts), "successes": next_successes, "interval_95": _wilson(next_successes, len(nexts)),
                   "assisted": sum(1 for row in nexts if row.get("next_assisted"))},
        "R_cold": {"n": len(measured), "successes": cold_successes,
                   "interval_95": _wilson(cold_successes, len(measured)),
                   "states": dict(Counter(row.get("cold_outcome_state") for row in rows))},
    }


def outcomes_report(vault: LoadedVault, repository: Repository) -> dict[str, Any]:
    """``learnloop sources outcomes``: associations by intent, kind, caller and source."""

    rebuild = rebuild_intervention_outcomes(vault, repository)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        records = stored_interventions(connection)
        joined = stored_outcomes(connection)
        proposals = connection.execute(
            "SELECT valuation_json FROM practice_index_proposals WHERE valuation_json IS NOT NULL").fetchall()
        gated = connection.execute(
            "SELECT COUNT(*) FROM practice_attempts WHERE reference_status='unverified'").fetchone()[0] \
            if any(row[1] == "reference_status" for row in connection.execute("PRAGMA table_info(practice_attempts)")) \
            else 0
        imported = exercise_import_ids(connection, vault.practice_items.values())
        key_labels = Counter(effective_key_status(connection, vault.practice_items[item_id])
                             for item_id in sorted(imported) if item_id in vault.practice_items)
    rows = [{**record, **joined.get(record["id"], {})} for record in records]
    groups: dict[str, dict[str, Any]] = {}
    for name, key in (("intent", lambda row: row.get("intent") or "none"), ("kind", lambda row: row["kind"]),
                      ("caller", lambda row: row.get("caller_kind") or "none"),
                      ("source", lambda row: ",".join(sorted((row.get("assets") or {}).get("source_versions") or {}))
                       or "none")):
        buckets: dict[str, list[Mapping[str, Any]]] = {}
        for row in rows:
            buckets.setdefault(key(row), []).append(row)
        groups[name] = {value: _rates(members) for value, members in sorted(buckets.items())}
    exclusions: Counter[str] = Counter()
    verdicts: Counter[str] = Counter()
    for (raw,) in proposals:
        try:
            valuation = json.loads(raw)
        except (TypeError, ValueError):
            continue
        for verdict in (valuation.get("eligibility") or {}).values():
            for reason in verdict.get("reasons") or ():
                exclusions[reason] += 1
        for section in valuation.get("problems") or ():
            for group, entries in (section.get("groups") or {}).items():
                for entry in entries:
                    verdicts[f"{group}:{entry.get('regime')}"] += 1
            verdicts[f"verdict:{section.get('verdict')}:{section.get('reason')}"] += 1
    serve_time = Counter()
    for row in rows:
        serve = (row.get("eligibility") or {}).get("serve_time")
        if serve is not None:
            serve_time["eligible" if serve.get("eligible") else "exposed_since_valuation"] += 1
    calibration = [{"intervention_id": row["id"], "regime": (row.get("valuation") or {}).get("regime"),
                    "predicted_outcomes": row.get("predicted_outcomes"), "observed_bucket": row.get("observed_bucket"),
                    "predicted_minutes": row.get("predicted_minutes"), "actual_minutes": row.get("actual_minutes"),
                    "reading_exposure_label": row.get("reading_exposure_label")}
                   for row in rows if row.get("valuation")]
    report: dict[str, Any] = {
        "version": 1, "label": ASSOCIATIONS_LABEL, "interventions": len(rows), "rebuild": rebuild,
        "recording": "on" if interventions_active(vault) else
        "off: source_service.interventions is false, so no new rows are written",
        "overall": _rates(rows), "by": groups,
        "key_labels": {status: {"count": count, "label": KEY_STATUS_LABELS.get(status, status)}
                       for status, count in sorted(key_labels.items())},
        "certification_gate": {"unverified_attempts": int(gated),
                               "note": "attempts on imported exercises with unverified keys earn no certification"},
        "exposure_exclusions": dict(sorted(exclusions.items())),
        "serve_time_rechecks": dict(serve_time),
        "valuation": {"by_group_and_regime": dict(sorted(verdicts.items())),
                      "scale": "LearnLoop's estimate; its scale is not yet calibrated"},
        "calibration_records": calibration,
        "cold_states": list(COLD_STATES),
    }
    return report


__all__ = [
    "ASSOCIATIONS_LABEL",
    "interventions_active",
    "offer_shown",
    "outcomes_report",
    "record_intervention",
    "record_need_served",
    "record_offer_shown",
    "record_pick",
    "record_remediation_delivery",
    "record_shown_spans",
    "record_tutor_citations",
    "seconds_since_related_exposure",
]
