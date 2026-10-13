"""Source-first fulfilment of intervention needs (spec_source_practice_and_probes_v1 §8.5; S2b).

When the follow-up chooser finds no suitable item it records an intervention
need, and the generation lane authors one. S2b adds one step before
generating, in the two adapters that fulfil needs today (the primed-retry
handler and ``learnloop generate-diagnostics``): try the learner's own
textbook exercises first ("retrieval first, generation on demand").

1. ``find_practice`` with ``kinds = source_exercises``, the need's LO and
   target facets, and the intent: ``remediate`` for a primed retry (a primed
   answer is never an independent check); in the CLI path ``discriminate`` when
   the need's diagnostic focus names rival misconceptions, else ``remediate``.
2. Candidates are tried in the order the valuation gives (the judge's order for
   ``remediate``). Screened exercises only order and skip, never license: in
   information mode one whose upper bound fails the stop is skipped and the
   rest are tried by bound per minute. Before anything is written, each draft
   is authored, its key checked (only ``book_solution``, ``checked`` or
   ``panel_agrees`` may fulfil a need), validated against the request, and,
   for ``discriminate``, passed through the follow-up chooser's OWN gate
   (``misconception_discrimination``). A draft that fails is not written.
3. Decision mode (an open causal factor with a priced repair choice):
   ``measure`` orders the tries; ``stop`` ends diagnostic fulfilment (the need
   becomes ``stale`` with ``value_stop:<action kind>:<proposal>``; the live
   repair is untouched and any disagreement logged); ``abstain`` and no
   evaluable candidate leave the need to generation, the stronger-instrument
   path.
4. A written item fulfils the need; otherwise generation proceeds exactly as
   today. Nothing ever falls back to an EIG-ordered exercise.

An algorithm successor (``mvp-0.16``): vaults below the tag never run it, and
``source_service.source_first_needs = false`` leaves the lane byte-identical.
"""
from __future__ import annotations

from collections.abc import Mapping
from contextlib import closing
from typing import Any

from learnloop.algorithm_versions import SOURCE_FIRST_NEEDS_VERSIONS
from learnloop.clock import Clock, utc_now_iso
from learnloop.content.authoring.source_exercise_import import import_source_exercise
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.source_service import import_row, update_import
from learnloop.diagnosis.followups import misconception_discrimination
from learnloop.diagnosis.probes import build_hypothesis_set
from learnloop.instructional.validation import draft_validator
from learnloop.instructional.wiring import disabled_reason, find_practice_injections
from learnloop.practice_index.retrieval import PracticeConstraints, find_practice
from learnloop.source_retrieval.corpus import teaching_scope
from learnloop.vault.loader import load_vault
from learnloop.vault.models import LoadedVault, PracticeItem

PATHS = ("primed_retry", "cli")


def source_first_active(vault: LoadedVault) -> bool:
    config = vault.config.source_service
    return (config.enabled and config.source_first_needs
            and vault.config.algorithms.algorithm_version in SOURCE_FIRST_NEEDS_VERSIONS)


def need_intent(need: Mapping[str, Any], path: str) -> str:
    if path == "primed_retry":
        return "remediate"
    focus = need.get("diagnostic_focus") or {}
    return "discriminate" if focus.get("misconception_ids") else "remediate"


def _chooser_gate(vault: LoadedVault, repository: Repository, need: Mapping[str, Any]):
    """The follow-up chooser's own rule, applied to an authored draft."""

    lo_id = str(need["learning_object_id"])
    hypothesis_set = build_hypothesis_set(vault, repository, lo_id)
    active = list(repository.misconceptions_for_learning_object(lo_id, statuses=("active",)))
    tau = vault.config.scheduler.followup.tau_discrimination_power

    def gate(draft: Any) -> dict[str, Any]:
        item = PracticeItem.model_validate({**draft.payload, "status": "active"})
        ok, j_lb, eig = misconception_discrimination(repository, vault, item, vault.rubric_for_item(item),
                                                     hypothesis_set, active, tau)
        return {"ok": ok, "youden_j_lb": round(j_lb, 4), "misconception_eig": round(eig, 6),
                "reason": None if ok else "the follow-up chooser's discrimination gate refused the draft"}

    return gate


def fulfil_need_from_sources(
    vault: LoadedVault,
    repository: Repository,
    need: Mapping[str, Any],
    *,
    path: str,
    clients: Mapping[str, Any] | None = None,
    rerank_client: Any | None = None,
    estimator: Any | None = None,
    pending_decision: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Try the sources for one need; ``{"outcome": fulfilled | stale | generate, ...}``.

    ``generate`` means the adapter proceeds exactly as today.
    """

    if path not in PATHS:
        raise ValueError(f"path must be one of {', '.join(PATHS)}")
    if not source_first_active(vault):
        return {"outcome": "generate", "reason": "source_first_needs inactive"}
    intent = need_intent(need, path)
    focus = need.get("diagnostic_focus") or {}
    requirements = need.get("candidate_requirements") or {}
    targets = [{"kind": "misconception", "id": str(value)} for value in focus.get("misconception_ids") or ()]
    if pending_decision and pending_decision.get("hypothesis_set_id"):
        # Decision mode: the factor's own space, priced by its repair classes.
        targets = [{"kind": "causal_hypothesis", "id": str(pending_decision["hypothesis_set_id"])}]
    constraints = PracticeConstraints(
        kinds="source_exercises", intent=intent, learning_object_ids=(str(need["learning_object_id"]),),
        facet_ids=tuple(str(facet) for facet in need.get("target_facets") or ()), target_hypotheses=tuple(targets),
        facet_match="all" if requirements.get("all_target_facets") else "any",
    )
    query = " ".join(filter(None, [*(focus.get("misconception_statements") or {}).values(),
                                   " ".join(need.get("target_facets") or ()),
                                   vault.learning_objects[str(need["learning_object_id"])].title
                                   if str(need["learning_object_id"]) in vault.learning_objects else ""]))[:1800]
    if decision := (pending_decision or None):
        if decision.get("unavailable"):
            return {"outcome": "generate", "intent": intent, "verdict": "abstain",
                    "reason": f"decision unpriced: {decision['unavailable']}"}
    clients_by_role = dict(clients or {})
    # The same switch-aware wiring every other caller uses (F15): a phase
    # switched off is off here too, and the need goes to generation.
    switched_off = disabled_reason(vault, "exercise_arm",
                                   *(("discriminating_search",) if intent == "discriminate" else ()))
    if switched_off is not None:
        return {"outcome": "generate", "intent": intent, "reason": switched_off}
    injected = find_practice_injections(vault, estimator=estimator,
                                        screen_client=clients_by_role.get("exercise_discrimination"),
                                        judge_client=clients_by_role.get("worked_example_equivalence"))
    result = find_practice(vault, repository, query or "practice", constraints, origin="api",
                           caller={"kind": "need", "ref": str(need["id"])}, exercise_arm=injected["exercise_arm"],
                           valuer=injected.get("valuer") if intent == "discriminate" else None,
                           estimator=estimator, rerank_client=rerank_client, clock=clock,
                           pending_decision=pending_decision)
    proposal_id = result.get("proposal_id")
    exercises = {entry["key"]: entry for entry in result.get("source_exercises") or ()}
    receipt: dict[str, Any] = {"intent": intent, "proposal_id": proposal_id, "candidates": len(exercises)}
    order: list[str]
    if intent == "discriminate":
        valuation = result.get("valuation") or {}
        sections = valuation.get("problems") or []
        decision_sections = [section for section in sections if section.get("mode") == "decision"]
        if decision_sections:
            section = decision_sections[0]
            verdict = section.get("verdict")
            receipt.update(verdict=verdict, named_action=section.get("named_action"),
                           action_kind=section.get("action_kind"))
            if verdict == "stop":
                reason = f"value_stop:{section.get('action_kind')}:{proposal_id}"
                repository.update_intervention_need_status(str(need["id"]), status="stale", blocked_reason=reason,
                                                           clock=clock)
                live = (pending_decision or {}).get("live_repair_class")
                if live and section.get("named_action") and live != section.get("named_action"):
                    receipt["action_disagreement"] = {"valuation": section.get("named_action"), "live": live}
                return {"outcome": "stale", "reason": reason, **receipt}
            if verdict != "measure":
                return {"outcome": "generate", "reason": section.get("reason") or verdict, **receipt}
            order = [check["ref"] for check in section.get("checks") or () if check["ref"] in exercises]
        else:
            bounded = [entry for section in sections for entry in section["groups"].get("bounded", [])]
            usable = [entry for entry in bounded if not entry.get("skip_licensed")]
            skipped = [entry["ref"] for entry in bounded if entry.get("skip_licensed")]
            receipt["skipped_by_bound"] = skipped
            usable.sort(key=lambda entry: -(entry["upper_bound_minutes"] / max(entry["expected_minutes"], 1e-6)))
            order = [entry["ref"] for entry in usable if entry["ref"] in exercises]
            if not order:
                return {"outcome": "generate", "reason": "no_discriminating_instrument", **receipt}
    else:
        order = list(exercises)
    validate = draft_validator(vault, constraints, intent=intent, estimator=estimator, independent=True)
    gate = _chooser_gate(vault, repository, need) if intent == "discriminate" else None

    def check(draft: Any) -> Mapping[str, Any]:
        verdict = dict(validate(draft))
        if verdict.get("ok") and gate is not None:
            gated = gate(draft)
            verdict["chooser_gate"] = gated
            if not gated["ok"]:
                verdict.update(ok=False, reason=gated["reason"])
        return verdict

    tries = []
    for key in order:
        entry = exercises[key]
        outcome = import_source_exercise(
            vault.root, repository, extraction_id=entry["extraction_id"], span_ids=entry["span_ids"], caller="need",
            proposal_id=proposal_id, clients=clients, validate=check, need_id=str(need["id"]),
            label=entry.get("label"), learning_object_hint=str(need["learning_object_id"]), clock=clock,
        )
        tries.append({key_: outcome.get(key_) for key_ in ("import_id", "status", "key_status", "reason")})
        if outcome.get("status") == "written":
            repository.update_intervention_need_status(
                str(need["id"]), status="fulfilled",
                blocked_reason=f"source_exercise:{outcome['practice_item_id']}", clock=clock)
            # The retrieval provenance the follow-up re-checks at serving
            # (§5.4): rule 4's shortlist scope, the intent and the proposal.
            scope = teaching_scope(vault, repository, [str(need["learning_object_id"])], item_bound=False)
            with repository.connection() as connection:
                validation = dict((import_row(connection, outcome["import_id"]) or {}).get("validation") or {})
                validation["retrieval"] = {"intent": intent, "proposal_id": proposal_id,
                                           "scope_extraction_ids": sorted(scope.extractions)}
                update_import(connection, outcome["import_id"], updated_at=utc_now_iso(clock), need_id=str(need["id"]),
                              validation=validation)
            return {"outcome": "fulfilled", "practice_item_id": outcome["practice_item_id"],
                    "import_id": outcome["import_id"], "tries": tries, **receipt}
        vault = load_vault(vault.root)
    return {"outcome": "generate", "reason": "no source exercise passed every check", "tries": tries, **receipt}


def pending_causal_decision(vault: LoadedVault, repository: Repository,
                            need: Mapping[str, Any]) -> dict[str, Any] | None:
    """The need's attempt's open causal factor as a priced decision, or None.

    A factor whose prior or repair classes cannot be read is returned as
    ``{"unavailable": reason}``: missing machine data never buys a question
    (the need then goes to generation, the stronger-instrument path).
    """

    attempt_id = need.get("attempt_id")
    if not attempt_id:
        return None
    factors = repository.unresolved_cause_factors_for_attempt(str(attempt_id), status="open")
    if not factors:
        return None
    ids = [str(c.get("hypothesis_id")) for c in factors[0].get("candidate_causes") or ()
           if isinstance(c, Mapping) and c.get("hypothesis_id") and not c.get("open_set")]
    if not ids:
        return {"unavailable": "no_concrete_hypotheses"}
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        rows = connection.execute(
            f"SELECT id, repair_class_id FROM causal_hypotheses WHERE id IN ({','.join('?' for _ in ids)})",
            ids).fetchall()
    repair = {str(row[0]): row[1] for row in rows}
    for episode in repository.open_probe_episodes().values():
        if episode.hypothesis_set_id is None:
            continue
        record = repository.fetch_hypothesis_set(episode.hypothesis_set_id) or {}
        if set(ids) <= set((record.get("prior") or {}).keys()):
            return {"hypothesis_set_id": episode.hypothesis_set_id,
                    "action_by_slot": {hypothesis: repair.get(hypothesis) for hypothesis in ids}}
    return {"unavailable": "no_locked_hypothesis_set"}


__all__ = ["PATHS", "fulfil_need_from_sources", "need_intent", "pending_causal_decision", "source_first_active"]
