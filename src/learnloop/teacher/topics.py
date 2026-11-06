"""Teacher TE2: a lesson on a typed goal (spec_teacher_v1 rev 5 §11.5; §7 step 1).

On the lesson screen's start the learner types what they want to learn. :func:`resolve` runs curriculum C0b's
resolver on the typed text alone (``source_retrieval.deliverables.resolve_typed_goal``: one call, the needed LOs
with the phrase each answers and the phrases nothing matched with a proposed topic; the same text over the same
LOs is answered from the stored resolution with no call). The screen shows *Not in your books yet: "…". Add it as a
topic?* for each leftover; the learner's yes is the decision (no judge). :func:`plan_open` then creates each
accepted topic through C0b's ``create_goal_lo`` (``mechanism = teacher_goal_v1``, the lesson's id as its goal id,
labelled *from LearnLoop's model*, unsourced) and returns the lesson's LOs, how each was resolved and the goal's
record; the lesson's service writes one ``goal_lo`` ledger entry and episode row per created LO.

A typed lesson goal is not a learner goal: nothing is written to ``goals.yaml``. Words that reproduce a question
kept for an exam are refused in one plain line, before any call.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

#: The one plain line for a goal that names protected material (§7 step 1).
PROTECTED_LINE = "That's kept for your exam, so I won't teach it. Try another way of putting what you want to learn."
FROM_MODEL = "from LearnLoop's model"


class TopicsRefused(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def protected(vault: Any, repository: Any, text: str) -> bool:
    """The typed words reproduce a question still reserved or withheld (fail closed: unreadable protection is
    protected)."""

    from learnloop.content.authoring.practice_leakage import reserved_findings, reserved_questions
    from learnloop.learner_protection import withheld_items

    withheld = withheld_items(vault, repository)
    if not withheld.available:
        return True
    try:
        return bool(reserved_findings(str(text), reserved_questions(vault, repository, withheld)))
    except Exception:  # noqa: BLE001 - an unreadable predicate fails closed
        return True


def resolve(vault: Any, repository: Any, text: str, *, client: Any | None = None, clock: Any = None) -> dict[str, Any]:
    """The typed goal resolved (``lesson.goal``): ``{"status", "goal_key", "topics": [{learning_object_id, title,
    phrase}], "unmatched": [{phrase, proposed_title, proposed_statement}], "subject_id", "subjects", "message"}``."""

    from learnloop.source_retrieval import deliverables as DL

    words = " ".join(str(text or "").split())
    if not words:
        raise TopicsRefused("validation_error", "Say what you want to learn first.")
    if protected(vault, repository, words):
        raise TopicsRefused("protected", PROTECTED_LINE)
    result = DL.resolve_typed_goal(vault, repository, words, client=client, clock=clock)
    out: dict[str, Any] = {"status": result.status, "goal_key": DL.typed_goal_key(words), "message": result.message,
                           "topics": [], "unmatched": [], "subject_id": None, "subjects": []}
    if result.resolution is None:
        return out
    needs = [entry for entry in result.resolution.get("learning_objects") or ()
             if isinstance(entry, Mapping) and str(entry.get("learning_object_id")) in vault.learning_objects
             and vault.learning_objects[str(entry["learning_object_id"])].status == "active"]
    out["topics"] = [{"learning_object_id": str(entry["learning_object_id"]),
                      "title": vault.learning_objects[str(entry["learning_object_id"])].title,
                      "phrase": str(entry.get("phrase") or "")} for entry in needs]
    out["unmatched"] = [{k: entry.get(k) for k in ("phrase", "proposed_title", "proposed_statement")}
                        for entry in result.resolution.get("unmatched") or () if isinstance(entry, Mapping)]
    out["subject_id"] = DL.typed_goal_subject(vault, needs)
    out["subjects"] = [{"subject_id": subject_id, "title": subject.metadata.title}
                       for subject_id, subject in sorted(vault.subjects.items()) if subject.metadata.status == "active"]
    return out


@dataclass
class OpenPlan:
    learning_object_ids: list[str]
    how: dict[str, str]
    goal: dict[str, Any]
    created: list[dict[str, Any]] = field(default_factory=list)


def plan_open(vault: Any, repository: Any, *, text: str, lesson_id: str, add_topics: Sequence[str],
              subject_id: str | None, client: Any | None = None, clock: Any = None) -> OpenPlan:
    """Resolve the typed goal again (the stored resolution: no call when nothing changed), create each accepted
    leftover through ``create_goal_lo`` (``teacher_goal_v1``) and return the lesson's LOs."""

    from learnloop.source_retrieval import deliverables as DL
    from learnloop.vault.loader import load_vault

    resolved = resolve(vault, repository, text, client=client, clock=clock)
    if resolved["status"] in ("unavailable", "no_inputs"):
        raise TopicsRefused("plan_unavailable", str(resolved.get("message") or "LearnLoop couldn't read your goal "
                                                                            "just now. Try again."))
    wanted = {" ".join(str(phrase).split()).casefold() for phrase in add_topics if str(phrase).strip()}
    how = {topic["learning_object_id"]: f"your words: {topic['phrase']}" for topic in resolved["topics"]}
    created: list[dict[str, Any]] = []
    unmatched = []
    for entry in resolved["unmatched"]:
        phrase = str(entry.get("phrase") or "")
        decision = "create" if phrase.casefold() in wanted else "declined"
        record = {**entry, "status": decision}
        if decision == "create":
            subject = subject_id or resolved["subject_id"]
            if not subject:
                raise TopicsRefused("no_subject", "Choose the subject this new topic belongs to.")
            try:
                made = DL.create_lesson_topic(vault, repository, lesson_id=lesson_id, phrase=phrase,
                                              title=str(entry.get("proposed_title") or phrase),
                                              statement=str(entry.get("proposed_statement") or phrase),
                                              subject_id=subject, clock=clock)
            except DL.DeliverableError as exc:
                raise TopicsRefused(exc.code, str(exc)) from exc
            lo = str(made["learning_object_id"])
            record.update(status="created", created_learning_object_id=lo)
            created.append({"learning_object_id": lo, "phrase": phrase, "title": entry.get("proposed_title"),
                            "label": FROM_MODEL, "created": bool(made.get("created"))})
            how[lo] = f"a new topic {FROM_MODEL} for your words: {phrase}"
        unmatched.append(record)
    if created:
        vault = load_vault(vault.root)
    los = [lo for lo in how if lo in vault.learning_objects]
    if not los:
        raise TopicsRefused("unknown_topic", "None of your topics matches that yet. Add it as a topic, or put it "
                                             "another way.")
    goal = {"text": " ".join(str(text).split()), "goal_key": resolved["goal_key"], "unmatched": unmatched,
            "created_learning_object_ids": [entry["learning_object_id"] for entry in created],
            "resolution": "fresh" if resolved["status"] == "fresh" else "resolved"}
    return OpenPlan(learning_object_ids=los, how=how, goal=goal, created=created)


__all__ = ["FROM_MODEL", "OpenPlan", "PROTECTED_LINE", "TopicsRefused", "plan_open", "protected", "resolve"]
