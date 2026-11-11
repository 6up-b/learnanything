"""Curriculum C2b, past papers option A (spec_deliverable_curriculum_v1 §5.3 as built).

When the deliverable's subject is ambiguous (``deliverable_subjects`` names none: two active
subjects and no syllabus or resolution naming one), every active subject's past-paper LO ids are
sent grouped by subject NAME (``past_papers_by_subject``, ``deliverable_scope_resolver.v3``) with an
instruction to use only the group of the deliverable's own subject; a resolver fake picks the
matching group. When the subject is known, only that subject's ids are sent (v2, one flat list, a
code filter). With ``curriculum.exam_units_in_scope`` off, C0b's v1 prompt byte for byte.

Every model is a fake; nothing leaves the machine.
"""
from __future__ import annotations

from typing import Any, Mapping

from learnloop.content.synthesis.source_unit_selection import save_unit_selection
from learnloop.source_retrieval import deliverables as DL
from learnloop.vault.loader import load_vault
from tests.deliverable_fixtures import DeliverableFake, prompt_context
from tests.exam_scope_fixtures import PAST_PAPER_LOS
from tests.curriculum_c2b_past_papers_helpers import PROB_PAPER, _two_subject_vault

OFF = "[curriculum]\nexam_units_in_scope = false\n"


class GroupPickingResolver(DeliverableFake):
    """Reads ``past_papers_by_subject`` and uses only the group whose subject name the learner's
    words name (the instruction the prompt gives); a known-subject prompt's flat list as is."""

    def __init__(self) -> None:
        super().__init__(needs=())
        self.picked: list[str] = []

    def _scope(self, context: Mapping[str, Any]) -> dict[str, Any]:
        words = " ".join(str(entry["text"]) for entry in context["inputs"]).casefold()
        chosen: list[str] = []
        for group in context.get("past_papers_by_subject") or ():
            if group["subject"].casefold() in words:
                chosen = list(group["topics"])
        chosen = chosen or list(context.get("past_papers_test") or ())
        self.picked = chosen
        return {"needs": [{"learning_object_id": lo, "phrase": "everything on the midterm"} for lo in chosen],
                "unmatched": []}


def test_ambiguous_subject_sends_the_ids_grouped_by_subject_name_and_the_resolver_picks_its_group(tmp_path):
    paths, repository = _two_subject_vault(tmp_path)
    vault = load_vault(paths.root)
    goal_id = DL.create_deliverable(vault, repository, "everything on my Probability midterm")["goal_id"]
    vault = load_vault(paths.root)
    with repository.connection() as connection:
        from learnloop.db.stores import deliverables as store

        rows = store.inputs(connection, goal_id)
    assert DL.deliverable_subjects(vault, repository, goal_id, rows) == frozenset()  # ambiguous
    groups = dict(DL.past_paper_groups(vault, repository))
    assert groups == {"linear-algebra": list(PAST_PAPER_LOS), "probability": ["lo_bayes"]}
    resolver = GroupPickingResolver()
    result = DL.resolve(vault, repository, goal_id, client=resolver)
    assert result.status == "ready"
    context = resolver.contexts[0]
    assert "past_papers_test" not in context
    assert context["past_papers_by_subject"] == [{"subject": "Linear Algebra", "topics": list(PAST_PAPER_LOS)},
                                                 {"subject": "Probability", "topics": ["lo_bayes"]}]
    prompt = resolver.prompts[0]
    assert DL.SCOPE_PAST_PAPERS_GROUPED_PROMPT_VERSION in prompt and "Use ONLY the group" in prompt
    assert "Find P(A | B)" not in prompt  # ids only: never a question's text
    assert result.resolution["prompt_version"] == DL.SCOPE_PAST_PAPERS_GROUPED_PROMPT_VERSION
    assert resolver.picked == ["lo_bayes"]
    assert [entry["learning_object_id"] for entry in result.resolution["learning_objects"]] == ["lo_bayes"]


def test_a_known_subject_sends_only_its_own_ids_as_one_flat_list(tmp_path):
    paths, repository = _two_subject_vault(tmp_path)
    vault = load_vault(paths.root)
    goal_id = DL.create_deliverable(vault, repository, "everything on my Probability midterm")["goal_id"]
    DL.resolve(load_vault(paths.root), repository, goal_id, client=GroupPickingResolver())
    # The newest resolution names one subject (lo_bayes): the subject is known now.
    DL.add_input(load_vault(paths.root), repository, goal_id, "text", text="and conditional independence")
    resolver = GroupPickingResolver()
    result = DL.resolve(load_vault(paths.root), repository, goal_id, client=resolver)
    assert result.status == "ready"
    context = resolver.contexts[0]
    assert context["past_papers_test"] == ["lo_bayes"] and "past_papers_by_subject" not in context
    assert result.resolution["prompt_version"] == DL.SCOPE_PAST_PAPERS_PROMPT_VERSION


def test_switched_off_the_prompt_is_c0bs_v1(tmp_path, monkeypatch):
    paths, repository = _two_subject_vault(tmp_path, config=OFF)
    vault = load_vault(paths.root)
    goal_id = DL.create_deliverable(vault, repository, "everything on my Probability midterm")["goal_id"]

    def never(*_args, **_kwargs):
        raise AssertionError("no past-papers input is read with the switch off")

    monkeypatch.setattr(DL, "past_paper_groups", never)
    monkeypatch.setattr(DL, "past_paper_learning_objects", never)
    resolver = DeliverableFake()
    result = DL.resolve(load_vault(paths.root), repository, goal_id, client=resolver)
    context = prompt_context(resolver.prompts[0])
    assert "past_papers_test" not in context and "past_papers_by_subject" not in context
    assert result.resolution["prompt_version"] == DL.SCOPE_PROMPT_VERSION


def test_a_group_held_out_meanwhile_refuses_the_request(tmp_path):
    """The guard re-reads each group for its own subject: a unit held out after the prompt
    was built (lo_bayes's paper) refuses the request; nothing is published."""

    paths, repository = _two_subject_vault(tmp_path)
    vault = load_vault(paths.root)
    goal_id = DL.create_deliverable(vault, repository, "everything on my Probability midterm")["goal_id"]

    class HoldsOut(GroupPickingResolver):
        def complete(self, request):
            save_unit_selection(repository, "ext_prob_paper", list(PROB_PAPER),
                                exam_use_modes={"prob_q1": "held_out_evaluation"})
            return super().complete(request)

    result = DL.resolve(load_vault(paths.root), repository, goal_id, client=HoldsOut())
    assert result.status == "unavailable"
    assert DL.latest_resolution(repository, goal_id) is None
