"""Teacher TE2: a lesson's probe, written by FG1's generation path (spec_teacher_v1 rev 5 §11.3 "What code does").

A ``followup_generation_jobs`` row of kind ``lesson`` (dedupe key ``lesson:<lesson id>:<node>``) runs here, in the
worker's follow-up slot, under FG1's envelope and attempt bound (at most :data:`jobs.MAX_GENERATION_ATTEMPTS`
physical runs, every call recorded as ``followup_generation``):

1. **Exam protection first** (FG1 §8): the reserved questions are read (unreadable: no question,
   ``protection_unavailable``) and a reading that reproduces one stops the probe before anything is sent
   (``reserved_match``). The author's context is FG1's builder's: only admissible, unreserved questions and a summary
   that quotes none; never the learner's answers, never a reserved question or its solution.
2. **Authoring** is FG1's one operation (``followup_probe_author``, the frontier route) with the readings as the
   rival readings: two or more are rivals; one is "held or not", the reading the rival of full credit (FG1 §4.3's
   family-pattern contract binds to FG1's probe episodes, which a lesson has none of: the review file records it).
   FG1's output checks run unchanged (the criterion and prediction contracts, the manipulation contract's axes, no
   repeat of withheld material).
3. **Admission** is FG1's ``persist_item`` unchanged: the reserved-match check over everything the learner would see,
   the structural instance gate, the never-before-seen check; the single-use identity (``source = 'lesson'``) and the
   family link (pending review: state sync never activates it) committed before the file exists. The lesson's
   admission receipt pins the author's per-reading predictions (the blind bundle over the readings) before the probe
   can be served. FG1's manipulation audit compares a new question with the missed one; a lesson probe has none, so
   it is recorded ``not_applicable``.
4. The lesson is told (:func:`learnloop.teacher.probes.record_ready` / ``record_refused``). A probe retired while the
   model wrote is retired again as it lands, so it is never served.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.teacher import probes as P

#: The admission receipt's version (what a lesson probe's ``probe_ready`` entry records).
ADMISSION_VERSION = "lesson_probe_admission_v1"
#: How the author is told where the question goes (data, never instructions; FG1's ``router_decision`` slot).
LESSON_DECISION = {"origin": "lesson", "chosen": "placement_probe", "timing": "now",
                   "note": "no question was missed: a teacher places the learner on this topic before teaching it"}


def parse_key(dedupe_key: str) -> tuple[str, str] | None:
    """``(lesson id, node id)`` from a lesson job's key."""

    parts = str(dedupe_key).split(":", 2)
    if len(parts) != 3 or parts[0] != "lesson" or not parts[1] or not parts[2]:
        return None
    return parts[1], parts[2]


def enabled(vault: Any) -> bool:
    from learnloop.teacher.te2 import on

    return on(vault)


def refuse(vault: Any, repository: Repository, job: Mapping[str, Any], reason: str, *, clock: Clock | None) -> None:
    key = parse_key(str(job.get("dedupe_key") or ""))
    if key is not None:
        P.record_refused(vault, repository, lesson_id=key[0], node_id=key[1], reason=reason, clock=clock)


def failure_reason(error: str) -> str:
    """A job's last error as the probe's refusal reason (its runs exhausted)."""

    return "route_unavailable" if "route_not_ready" in str(error) else "generation_failed"


def _context(vault: Any, repository: Repository, *, learning_object_id: str, readings: list[str], card: Any,
             template: Any) -> tuple[Any, dict[str, str]]:
    """FG1's context with the readings as the rival readings (no causal hypothesis row exists for them)."""

    from learnloop.content.authoring.practice_leakage import reserved_findings
    from learnloop.diagnosis.ai_contracts import FollowupProbeContext
    from learnloop.diagnosis.probe_instance_generation import family_measurement_intent
    from learnloop.followup_run.authoring import admissible_item, protection_view, reserved_view

    withheld = protection_view(vault, repository)
    reserved = reserved_view(vault, repository)
    learning_object = vault.learning_objects[learning_object_id]
    existing = sorted(
        item.prompt.strip() for item in vault.practice_items.values()
        if item.learning_object_id == learning_object_id and item.prompt and admissible_item(withheld, item)
        and not reserved_findings(item.prompt, reserved)
    )
    summary = learning_object.summary
    if summary and reserved_findings(str(summary), reserved):
        summary = ""
    refs: dict[str, str] = {}
    rows: list[dict[str, Any]] = []
    for index, reading in enumerate(readings):
        ref = f"H{index + 1}"
        refs[ref] = f"reading_{index + 1}"
        statement = reading if len(readings) > 1 else f"does not hold this yet: {reading}"
        rows.append({"hypothesis_ref": ref, "statement": statement, "cause_scope": "lesson_reading",
                     "target_ref": None})
    context = FollowupProbeContext(
        learning_object_title=learning_object.title, learning_object_concept=learning_object.concept,
        learning_object_summary=summary, target_facets=[str(value) for value in card.target_facets],
        hypotheses=rows, router_decision=dict(LESSON_DECISION),
        measurement_pattern=family_measurement_intent(template.id), source_question_md=None,
        existing_prompts=existing, avoid_phrases=[])
    return context, refs


def run(vault: Any, repository: Repository, job: Mapping[str, Any], *, clients: Any, clock: Clock | None) -> None:
    """One lesson job: a typed refusal recorded in the lesson, or the admitted question. A transport failure or a
    route not ready raises (the worker's bounded retry); everything else ends here."""

    from learnloop.content.authoring.practice_leakage import reserved_findings
    from learnloop.followup_run import admission, authoring
    from learnloop.followup_run.jobs import GenerationDeferred, _author_client

    key = parse_key(str(job.get("dedupe_key") or ""))
    if key is None:
        return
    lesson_id, node_id = key
    lesson, probe = P.pending_request(repository, lesson_id, node_id)
    if lesson is None or probe is None or probe.status != "preparing":
        return
    if not enabled(vault):
        P.record_refused(vault, repository, lesson_id=lesson_id, node_id=node_id, reason="switch_off", clock=clock)
        return
    if lesson.get("closed_at") is not None:
        P.record_refused(vault, repository, lesson_id=lesson_id, node_id=node_id, reason="lesson_closed", clock=clock)
        return
    lo = probe.learning_object_id
    if not lo or lo not in vault.learning_objects:
        P.record_refused(vault, repository, lesson_id=lesson_id, node_id=node_id, reason="not_admitted", clock=clock)
        return

    def refused(reason: str) -> None:
        P.record_refused(vault, repository, lesson_id=lesson_id, node_id=node_id, reason=reason, clock=clock)

    try:
        reserved = authoring.reserved_view(vault, repository)
    except authoring.AuthoringRejected:
        refused("protection_unavailable")
        return
    # FG1 §8: a reading that reproduces a reserved question sends its words nowhere: no probe.
    if any(reserved_findings(reading, reserved) for reading in probe.readings):
        refused("reserved_match")
        return
    try:
        template, card = admission._template_and_card(vault, repository, lo, clock)
        context, refs = _context(vault, repository, learning_object_id=lo, readings=probe.readings, card=card,
                                 template=template)
    except admission.AdmissionFailed:
        refused("not_admitted")
        return
    except authoring.AuthoringRejected:
        refused("protection_unavailable")
        return
    client = _author_client(vault, clients)
    if client is None:
        raise GenerationDeferred("author_route_not_ready")
    authored = authoring.request_authored_probe(client, context)
    try:
        checked = authoring.check_output(vault, repository, authored, refs=refs, learning_object_id=lo)
    except authoring.AuthoringRejected as rejected:
        refused("protection_unavailable" if str(rejected) == "protection_unavailable" else "not_admitted")
        return
    # Late: the learner chose "Teach it anyway", or the lesson closed, while the model wrote: nothing is written.
    lesson, probe = P.pending_request(repository, lesson_id, node_id)
    if lesson is None or probe is None or probe.status != "preparing" or lesson.get("closed_at") is not None:
        return
    try:
        item_id = admission.persist_item(vault, repository, checked, template=template, card=card, workflow_id=None,
                                         episode_id=None, source="lesson", client=client, clock=clock)
    except admission.AdmissionFailed as failed:
        refused("reserved_match" if failed.reason in authoring.RESERVED_MATCHES else
                "protection_unavailable" if failed.reason == "protection_unavailable" else "not_admitted")
        return
    receipt = {
        "version": ADMISSION_VERSION, "instance_gate": "passed", "never_before_seen": "passed",
        "reserved_check": "passed", "manipulation_audit": "not_applicable_no_source_question",
        "adversarial_review": "not_run", "generation_job_id": str(job["id"]),
        "model": getattr(client, "model", None), "readings": len(probe.readings),
        # The blind bundle over the readings, pinned before any serve: a learner with only that reading misses
        # these criteria (the author's observation-free predictions, by reading).
        "predictions": {refs_name: list(criteria) for refs_name, criteria in sorted(checked.failing.items())},
        "criteria": sorted(criterion.id.strip() for criterion in checked.authored.criteria),
    }
    P.record_ready(vault, repository, lesson_id=lesson_id, node_id=node_id, item_id=item_id, receipt=receipt,
                   clock=clock)


__all__ = ["ADMISSION_VERSION", "LESSON_DECISION", "enabled", "failure_reason", "parse_key", "refuse", "run"]
