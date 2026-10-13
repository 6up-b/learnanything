"""``find_practice`` for real callers (spec_source_practice_and_probes_v1 §6).

The tutor's "Practice this", the daily plan's learner picks, DL3's box and the
Reader's boxes all propose through one function, with one receipt table. This
module adds what a real caller needs around Phase 5b's ``find_practice``:

* the caller context, derived on the server (never from the request), which
  enforces what the context forbids: during a cold administration nothing is
  proposed, and an item-bound tutor context never proposes its own item;
* the injected arms and valuer (``practice_index`` never imports the service);
* impressions: what a surface actually rendered, recorded apart from what was
  merely retrieved (§6.5);
* the pick link: a picked proposal appends the ``practised`` usage signal at the
  pick, not only through the 72-hour attempt join (§6.3).

Nothing here serves. A proposal becomes practice only through an existing
serving path: ``plan_learner_pick``, the open-list pick, the post-attempt
follow-up path, DL2's "Check once" or the quick check's pool (SC1).
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import closing
from typing import Any

from learnloop.ai.execution import content_key
from learnloop.clock import Clock, utc_now_iso
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.judgments import append_judgment
from learnloop.db.stores.practice_index import judgments_by_ids
from learnloop.db.stores.practice_index import proposal as stored_proposal
from learnloop.db.stores.source_service import IMPRESSION_SURFACES, insert_impression
from learnloop.ids import new_ulid
from learnloop.practice_index.retrieval import IntentUnavailable, PracticeConstraints, find_practice
from learnloop.practice_index.usage import USAGE_TASK, record_practice_usage
from learnloop.source_retrieval.policy import CallerContext, PolicyRefused, derive_policy
from learnloop.source_retrieval.service_spend import service_spend
from learnloop.vault.models import LoadedVault

#: Prompt characters an impression keeps of what was shown (a record of the
#: glimpse, not a copy of the item).
SHOWN_PROMPT_CHARS = 400


def service_enabled(vault: LoadedVault) -> bool:
    return bool(vault.config.source_service.enabled)


def constrain_for_caller(constraints: PracticeConstraints, caller: CallerContext | None) -> PracticeConstraints:
    """What the caller's context forbids, applied on top of the request.

    A request can narrow (any filter) but never widen: an item-bound caller's
    own item is always excluded, whatever the request said.
    """

    if caller is None:
        return constraints
    policy, _reason = derive_policy(caller)
    if policy == "cold_attempt":
        raise PolicyRefused("cold_attempt", "nothing is proposed during a cold administration")
    exclude = list(constraints.exclude_item_ids)
    if caller.item_id and caller.item_id not in exclude:
        exclude.append(caller.item_id)
    values = constraints.as_dict()
    values["exclude_item_ids"] = exclude
    return PracticeConstraints.from_mapping(values)


def propose_practice(vault: LoadedVault, repository: Repository, query: str,
                     constraints: PracticeConstraints | Mapping[str, Any] | None, *,
                     caller: CallerContext | None, origin: str = "rpc",
                     embedder: Any | None = None, rerank_client: Any | None = None,
                     clock: Clock | None = None, **injected: Any) -> dict[str, Any]:
    """``find_practice`` under a server-derived caller context."""

    if not isinstance(constraints, PracticeConstraints):
        constraints = PracticeConstraints.from_mapping(constraints)
    notes: list[dict[str, Any]] = []
    if constraints.target_hypotheses:
        # One reference contract (F13): aliases canonical, a named gap passed
        # on as what it names; refs naming nothing usable are reported.
        from dataclasses import asdict, replace

        from learnloop.instructional.valuation import resolve_hypothesis_refs

        refs, notes = resolve_hypothesis_refs(vault, repository, constraints.target_hypotheses)
        constraints = replace(constraints, target_hypotheses=tuple(asdict(ref) for ref in refs))
    if constraints.intent != "practice" and not vault.config.source_service.discriminating_search:
        raise IntentUnavailable("discriminating_search_off",
                                "source_service.discriminating_search is off: only the practice intent is served")
    constraints = constrain_for_caller(constraints, caller)
    caller_block = None if caller is None else {"kind": caller.kind, "ref": caller.ref}
    # The whole operation (the query embedding, every rerank page, the arm's
    # search, the valuation's judges) runs under the service's shared daily
    # cap (Codex re-review F2).
    with service_spend(vault, repository, clock=clock):
        result = find_practice(vault, repository, query, constraints, origin=origin, embedder=embedder,
                               rerank_client=rerank_client, clock=clock, caller=caller_block, **injected)
    if caller is not None:
        policy, reason = derive_policy(caller)
        result["caller"] = {**caller_block, "policy": policy, "policy_reason": reason}
    if notes:
        result["hypothesis_refs"] = notes
    return result


def continuation_cursor(repository: Repository, proposal_id: str, *, caller: CallerContext | None, query: str,
                        intent: str) -> dict[str, Any]:
    """The stored cursor that resumes an earlier search (Codex re-review F5).

    A continuation continues the same request for the same caller: the
    proposal must belong to this caller, for the same query and intent, and
    its paging must have stopped with candidates left (ValueError, or
    PolicyRefused for another caller's search)."""

    from learnloop.practice_index.query_vectors import normalize_query, query_id
    from learnloop.practice_index.retrieval import canonical_intent

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        found = stored_proposal(connection, proposal_id)
    if found is None:
        raise ValueError("Unknown proposal to continue")
    if caller is not None and (found.get("caller"), found.get("caller_ref")) != (caller.kind, caller.ref):
        raise PolicyRefused("continuation_refused", "that search belongs to another caller")
    if found.get("query_id") != query_id(normalize_query(query)) or \
            (found.get("intent") or "practice") != canonical_intent(intent):
        raise ValueError("a continuation continues the same request (its query and intent)")
    cursor = ((found.get("signals") or {}).get("paging") or {}).get("cursor")
    if not cursor:
        raise ValueError("that search has no candidates left to continue")
    return dict(cursor)


def _proposed_key(entry: Mapping[str, Any]) -> tuple[str, ...]:
    if entry.get("kind") == "source_exercise":
        return ("source_exercise", str(entry.get("extraction_id")),
                *sorted(str(span) for span in entry.get("span_ids") or ()))
    return ("item", str(entry.get("practice_item_id")))


def _requested_key(key: Mapping[str, Any]) -> tuple[str, ...] | None:
    kind = str(key.get("kind") or "item")
    if kind == "item" and key.get("practice_item_id"):
        return ("item", str(key["practice_item_id"]))
    if kind == "source_exercise" and key.get("extraction_id") and key.get("span_ids"):
        return ("source_exercise", str(key["extraction_id"]), *sorted(str(span) for span in key["span_ids"]))
    return None


def record_proposal_impressions(vault: LoadedVault, repository: Repository, *, proposal_id: str,
                                keys: Sequence[Mapping[str, Any]], surface: str,
                                session_id: str | None = None,
                                clock: Clock | None = None) -> dict[str, Any]:
    """Record the proposals a surface rendered. Unknown keys are dropped and counted.

    What was shown is read from the stored proposal and the vault, never from
    the request: a frontend reports *which* candidates it rendered, not what
    they said.
    """

    if surface not in IMPRESSION_SURFACES:
        raise ValueError(f"surface must be one of {', '.join(IMPRESSION_SURFACES)}")
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        found = stored_proposal(connection, proposal_id)
    if found is None:
        raise ValueError("Unknown proposal")
    proposed = {_proposed_key(entry): entry for entry in found["proposed"]}
    recorded: list[str] = []
    dropped = 0
    seen: set[tuple[str, ...]] = set()
    now = utc_now_iso(clock)
    with repository.connection() as connection:
        for key in keys:
            wanted = _requested_key(key)
            entry = proposed.get(wanted) if wanted is not None else None
            if entry is None or wanted in seen:
                dropped += 1
                continue
            seen.add(wanted)
            impression_id = "imp_" + new_ulid()
            if wanted[0] == "item":
                item = vault.practice_items.get(wanted[1])
                prompt = " ".join((item.prompt if item is not None else "").split())
                shown = {"prompt": prompt[:SHOWN_PROMPT_CHARS], "rationale": entry.get("rationale")}
                insert_impression(
                    connection, id=impression_id, created_at=now, surface=surface,
                    caller_kind=found.get("caller"), caller_ref=found.get("caller_ref"),
                    proposal_id=proposal_id, candidate_kind="item", practice_item_id=wanted[1],
                    extraction_id=None, span_ids=(), shown_fields=shown, session_id=session_id,
                )
            else:
                statement = " ".join(str(entry.get("statement") or "").split())
                shown = {"statement": statement[:SHOWN_PROMPT_CHARS], "rationale": entry.get("rationale"),
                         "label": entry.get("label"), "page": entry.get("page")}
                insert_impression(
                    connection, id=impression_id, created_at=now, surface=surface,
                    caller_kind=found.get("caller"), caller_ref=found.get("caller_ref"),
                    proposal_id=proposal_id, candidate_kind="source_exercise", practice_item_id=None,
                    extraction_id=wanted[1], span_ids=list(wanted[2:]), shown_fields=shown,
                    session_id=session_id,
                )
            recorded.append(impression_id)
    return {"proposal_id": proposal_id, "recorded": len(recorded), "impression_ids": recorded,
            "dropped": dropped}


def record_proposal_selection(repository: Repository, *, proposal_id: str, practice_item_id: str,
                              clock: Clock | None = None, vault: LoadedVault | None = None) -> dict[str, Any]:
    """The learner's selection of a proposed item: the ``practised`` usage
    signal (idempotent), recorded before serving so a bad proposal is refused
    before anything is served.

    A pick of a ``discriminate`` or ``retention`` proposal re-checks
    independence (§5.4): if the candidate was exposed since it was valued,
    the pick still proceeds, as practice, with the independent label dropped
    and the reason shown. Nothing here says the item was delivered: that is
    :func:`record_proposal_delivery`, after the serving path succeeded."""

    result = dict(record_practice_usage(repository, proposal_id=proposal_id, practice_item_id=practice_item_id,
                                        signal="practised", clock=clock))
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        found = stored_proposal(connection, proposal_id)
    intent = (found or {}).get("intent")
    if vault is not None and intent in ("discriminate", "retention"):
        from learnloop.instructional.exposure import independent_check_eligibility

        verdict = independent_check_eligibility(vault, repository, {"practice_item_id": practice_item_id},
                                                intent=intent, picked_proposal_id=proposal_id, clock=clock)
        result["independence"] = verdict
        result["served_as"] = "independent_check" if verdict["eligible"] else "practice"
        if not verdict["eligible"]:
            result["label"] = verdict.get("practice_label") or "you've seen this question since it was suggested"
    return result


def record_proposal_delivery(vault: LoadedVault, repository: Repository, selection: Mapping[str, Any], *,
                             session_id: str | None = None, router_decision_id: str | None = None,
                             exercise: Mapping[str, Any] | None = None, import_id: str | None = None,
                             clock: Clock | None = None) -> str | None:
    """S5: the picked proposal was delivered (shown and served), after the
    serving path succeeded. ``router_decision_id`` is the exact decision the
    serving path returned (R1's row for the block that served it), never a
    "latest matching row" lookup; ``exercise`` and ``import_id`` name the
    textbook exercise an imported item came from."""

    from learnloop.instructional.interventions import record_pick

    return record_pick(vault, repository, proposal_id=str(selection["proposal_id"]),
                       practice_item_id=str(selection["practice_item_id"]), exercise=exercise, import_id=import_id,
                       serve_verdict=selection.get("independence"), session_id=session_id,
                       router_decision_id=router_decision_id, clock=clock)


def record_proposal_pick(repository: Repository, *, proposal_id: str, practice_item_id: str,
                         clock: Clock | None = None, vault: LoadedVault | None = None,
                         session_id: str | None = None, router_decision_id: str | None = None) -> dict[str, Any]:
    """Selection and delivery together, for a caller that has already served
    the item (the sidecar's pick records them on either side of serving)."""

    result = record_proposal_selection(repository, proposal_id=proposal_id, practice_item_id=practice_item_id,
                                       clock=clock, vault=vault)
    if vault is not None:
        result["intervention_id"] = record_proposal_delivery(vault, repository, result, session_id=session_id,
                                                             router_decision_id=router_decision_id, clock=clock)
    return result


def proposed_exercise(repository: Repository, proposal_id: str, extraction_id: str,
                      span_ids: Sequence[str]) -> dict[str, Any]:
    """The source-exercise entry a proposal proposed, or ValueError."""

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        found = stored_proposal(connection, proposal_id)
    if found is None:
        raise ValueError("Unknown proposal")
    wanted = ("source_exercise", extraction_id, *sorted(str(span) for span in span_ids))
    for entry in found["proposed"]:
        if _proposed_key(entry) == wanted:
            return dict(entry)
    raise ValueError("That exercise was not proposed by this proposal")


def interactive_import_request(vault: LoadedVault, repository: Repository, proposal_id: str,
                               entry: Mapping[str, Any], *, estimator: Any | None = None) -> dict[str, Any]:
    """What a learner's pick of a textbook exercise was proposed for, as plain
    data the import job validates the authored draft against (Codex re-review F7).

    The proposal's own constraints and intent (its receipt), the estimator's
    minutes per practice mode when the request bounded minutes (the job cannot
    import the plan's estimator), and, for a ``discriminate`` proposal, the
    exercise's persisted screen, whose profiles and rubric links the item
    gets (§8.4). A learner's pick is written whatever the validation says
    (learner authority); a failed validation is the correction shown, and the
    item is then served as practice, never as an independent check."""

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        found = stored_proposal(connection, proposal_id) or {}
    constraints = dict(found.get("constraints") or {})
    intent = str(found.get("intent") or constraints.get("intent") or "practice")
    request: dict[str, Any] = {"constraints": constraints, "intent": intent,
                               "provisional": dict(entry.get("provisional") or {})}
    if constraints.get("max_estimated_minutes") is not None and estimator is not None:
        from learnloop.practice_index.retrieval import practice_modes

        minutes = {}
        for mode in practice_modes(vault):
            try:
                estimate = estimator(str(entry.get("key") or ""), mode, None)
            except Exception:  # noqa: BLE001 - a mode with no estimate fails the bound, never passes it
                continue
            minutes[mode] = float(getattr(estimate, "minutes", estimate))
        request["minutes_by_mode"] = minutes
    if intent == "discriminate":
        from learnloop.instructional.screen import persisted_screen

        for section in (found.get("valuation") or {}).get("problems") or ():
            for group in (section.get("groups") or {}).values():
                for candidate in group:
                    if candidate.get("ref") == entry.get("key") and candidate.get("screen_judgment_id"):
                        screen = persisted_screen(repository, str(candidate["screen_judgment_id"]))
                        if screen is not None:
                            request["screen"] = screen
    return request


def record_exercise_pick(repository: Repository, *, proposal_id: str, entry: Mapping[str, Any],
                         clock: Clock | None = None) -> str:
    """The ``practised`` usage verdict for a picked textbook exercise (idempotent).

    The learner's selection only: the exercise is not an item until imported,
    so the verdict names its stable exercise key (``right_kind =
    source_exercise``). Its delivery is recorded once the import has written
    the item and the serving path served it (:func:`record_proposal_delivery`
    with the exercise and the import)."""

    key = str(entry.get("key") or "")
    judgment_id = "pus_" + content_key([proposal_id, key, "practised"])[:40]
    with repository.connection() as connection:
        if not judgments_by_ids(connection, [judgment_id]):
            append_judgment(
                connection, id=judgment_id, task=USAGE_TASK, left_kind="practice_proposal", left_id=proposal_id,
                right_kind="source_exercise", right_id=key, judge="learner_card",
                input_hash=content_key([proposal_id, key]), verdict="practised",
                rationale="learner pick of a textbook exercise proposal", created_at=utc_now_iso(clock),
            )
    return judgment_id


def imported_exercise_selection(repository: Repository, *, proposal_id: str, import_id: str,
                                practice_item_id: str, vault: LoadedVault | None = None,
                                clock: Clock | None = None) -> dict[str, Any]:
    """The selection behind serving an imported textbook exercise: its import
    must have come from this proposal and written this item (ValueError).

    A pick of a ``discriminate`` or ``retention`` proposal is re-checked at
    serving exactly as an existing item's is (§5.4; Codex re-review F7): the
    impression made by the originating proposal does not count against it,
    anything else since does. A draft that failed its validation against the
    proposal (§8.1) is served as practice too, with its correction."""

    from learnloop.db.stores.source_service import import_row

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        row = import_row(connection, import_id)
        found = stored_proposal(connection, proposal_id)
    if row is None or row.get("proposal_id") != proposal_id:
        raise ValueError("That import did not come from this proposal")
    if row.get("status") != "written" or row.get("practice_item_id") != practice_item_id:
        raise ValueError("That import has not written this item")
    entry = proposed_exercise(repository, proposal_id, str(row["extraction_id"]), list(row.get("span_ids") or ()))
    result: dict[str, Any] = {"proposal_id": proposal_id, "practice_item_id": practice_item_id,
                              "signal": "practised", "import_id": import_id, "exercise": entry}
    intent = (found or {}).get("intent")
    validation = dict(row.get("validation") or {})
    if vault is not None and intent in ("discriminate", "retention"):
        from learnloop.instructional.exposure import independent_check_eligibility

        verdict = independent_check_eligibility(vault, repository, {"practice_item_id": practice_item_id},
                                                intent=intent, picked_proposal_id=proposal_id, clock=clock)
        if validation.get("ok") is False:
            verdict = {**verdict, "eligible": False,
                       "reasons": [*verdict.get("reasons", []), "failed_validation"],
                       "practice_label": validation.get("correction") or validation.get("reason")}
        result["independence"] = verdict
        result["served_as"] = "independent_check" if verdict["eligible"] else "practice"
        if not verdict["eligible"]:
            result["label"] = verdict.get("practice_label") or "you've seen this question since it was suggested"
    if validation.get("correction"):
        result["correction"] = validation["correction"]
    return result


__all__ = [
    "SHOWN_PROMPT_CHARS",
    "constrain_for_caller",
    "continuation_cursor",
    "propose_practice",
    "record_proposal_impressions",
    "proposed_exercise",
    "imported_exercise_selection",
    "interactive_import_request",
    "record_exercise_pick",
    "record_proposal_delivery",
    "record_proposal_pick",
    "record_proposal_selection",
    "service_enabled",
]
