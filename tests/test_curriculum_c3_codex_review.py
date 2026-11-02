"""Curriculum C3, Codex review fixes (docs/reviews/curriculum-c3-syllabus-scoping-codex-review.md).

* F1: past papers of another subject never expand a deliverable (§5.3 "of this subject");
* F2: assessment mappings carried by an LO's canonical facets count (held-out ones never do);
* F3: a syllabus (member or unit override) never becomes practice, through either import path;
* F4: the past-papers ids sent are read again before every request and before publication;
* F5 (backend half): the scope view lists the syllabi the panel may attach whole.

Every model is a fake; nothing leaves the machine.
"""
from __future__ import annotations

from datetime import UTC, datetime

import pytest

from learnloop.content.sources import exam_material as EM
from learnloop.content.synthesis.source_unit_selection import save_unit_selection
from learnloop.source_retrieval import deliverables as DL
from learnloop.vault.loader import add_subject, load_vault
from learnloop.vault.writer import upsert_source_set
from learnloop.vault.yaml_io import read_markdown_frontmatter_data, read_yaml, write_markdown_with_frontmatter, write_yaml
from tests.deliverable_fixtures import DeliverableFake, prompt_context
from tests.exam_scope_fixtures import PAPER, PAST_PAPER_LOS, SPANS, build_exam_scope_vault, ref, set_refs
from tests.practice_index_fakes import _learning_object
from tests.source_retrieval_fakes import seed_source

LA = ("linear-algebra",)
PHYS_SENTINEL = "PHYSPAPERSENTINEL physics midterm question one: a block slides down a ramp."


def _rows(repository, sql, params=()):
    with repository.connection() as connection:
        return [tuple(row) for row in connection.execute(sql, params).fetchall()]


def _deliverable(paths, repository, sentence="Only my midterm: eigenvalues, determinants and matrix computations"):
    created = DL.create_deliverable(load_vault(paths.root), repository, sentence)
    return created["goal_id"]


def _scope_rows(repository, goal_id):
    from learnloop.db.stores import deliverables as store

    with repository.connection() as connection:
        return [row for row in store.inputs(connection, goal_id) if row["kind"] in DL.SCOPE_KINDS]


def _prompt(paths, repository, goal_id):
    vault = load_vault(paths.root)
    return DL.build_scope_prompt(vault, repository, DL.goal_of(vault, goal_id), _scope_rows(repository, goal_id))


# --- F1: of this subject -------------------------------------------------------------------------

def _with_physics(root):
    """The exam-scope vault plus a second subject, physics, with its own past paper: its question
    maps to the physics topic ``lo_force`` and to the linear-algebra topic ``lo_eigen`` (which only
    the physics paper tests)."""

    paths, repository = build_exam_scope_vault(root)
    add_subject(paths.root, "physics", "Physics")
    seed_source(repository, source_id="src_phys", revision_id="rev_phys", extraction_id="ext_phys",
                title="Physics midterm 2025", units={"phys_q1": ("Question 1", [(PHYS_SENTINEL, 1)])},
                furniture=False)
    upsert_source_set(paths.root, {"id": "sset_phys", "subject_id": "physics", "title": "Physics sources",
                                   "members": [{"source_id": "src_phys", "revision_id": "rev_phys",
                                                "default_role": "exam"}]})
    save_unit_selection(repository, "ext_phys", ["phys_q1"], exam_use_modes={"phys_q1": "available_for_practice"})
    force = _learning_object("lo_force", "Forces on a ramp")
    force["subjects"] = ["physics"]
    force["summary"] = "Resolve gravity along and across an inclined plane."
    write_yaml(paths.learning_object_path("physics", "lo_force"), force)
    set_refs(paths.learning_object_path("physics", "lo_force"), [ref("src_phys", "ext_phys", "s2")])
    eigen = paths.learning_object_path("linear-algebra", "lo_eigen")
    refs = list((read_yaml(eigen).get("provenance") or {}).get("source_refs") or [])
    set_refs(eigen, [*refs, ref("src_phys", "ext_phys", "s2")])
    return paths, repository


def test_past_papers_are_read_per_subject_never_vault_wide(tmp_path):
    paths, repository = _with_physics(tmp_path / "vault")
    vault = load_vault(paths.root)
    assert {"linear-algebra", "physics"} <= set(vault.subjects)
    # Linear algebra's papers test only linear-algebra topics; lo_eigen is tested by the physics paper only.
    assert DL.past_paper_learning_objects(vault, repository, LA) == list(PAST_PAPER_LOS)
    assert DL.past_paper_learning_objects(vault, repository, ("physics",)) == ["lo_force"]
    assert DL.past_paper_learning_objects(vault, repository, ()) == []


def test_an_ambiguous_deliverable_reads_the_past_papers_grouped_by_subject(tmp_path):
    """Two subjects and nothing saying which (C2b, past papers option A, superseding C3's "no
    paper"): every subject's ids go grouped by subject name, with the instruction to use only the
    deliverable's own subject's group (v3); never a paper's text."""

    paths, repository = _with_physics(tmp_path / "vault")
    goal_id = _deliverable(paths, repository, "everything on my midterm")
    vault = load_vault(paths.root)
    assert DL.deliverable_subjects(vault, repository, goal_id, _scope_rows(repository, goal_id)) == frozenset()
    prompt = _prompt(paths, repository, goal_id)
    context = prompt_context(prompt.text)
    assert prompt.version == DL.SCOPE_PAST_PAPERS_GROUPED_PROMPT_VERSION and "past_papers_test" not in context
    groups = {group["subject"]: group["topics"] for group in context["past_papers_by_subject"]}
    assert list(PAST_PAPER_LOS) in groups.values()
    assert all("lo_force" not in topics for subject, topics in groups.items() if topics == list(PAST_PAPER_LOS))
    assert PHYS_SENTINEL not in prompt.text


def test_a_syllabus_names_the_subject_and_another_subject_s_papers_stay_out(tmp_path):
    paths, repository = _with_physics(tmp_path / "vault")
    goal_id = _deliverable(paths, repository, "everything on my midterm")
    DL.add_input(load_vault(paths.root), repository, goal_id, "passage", extraction_id="ext_syl")
    vault = load_vault(paths.root)
    assert DL.deliverable_subjects(vault, repository, goal_id, _scope_rows(repository, goal_id)) == frozenset(LA)
    fake = DeliverableFake()
    result = DL.resolve(vault, repository, goal_id, client=fake)
    assert result.status == "ready"
    sent = fake.contexts[0]["past_papers_test"]
    assert sent == list(PAST_PAPER_LOS) and "lo_force" not in sent and "lo_eigen" not in sent
    assert PHYS_SENTINEL not in fake.prompts[0]


def test_a_resolution_s_topics_name_the_subject_for_the_next_one(tmp_path):
    paths, repository = _with_physics(tmp_path / "vault")
    goal_id = _deliverable(paths, repository)
    first = DeliverableFake()
    assert DL.resolve(load_vault(paths.root), repository, goal_id, client=first).status == "ready"
    assert "past_papers_test" not in first.contexts[0]  # two subjects, nothing resolved yet
    DL.add_input(load_vault(paths.root), repository, goal_id, "text", text="and inner products")
    second = DeliverableFake()
    assert DL.resolve(load_vault(paths.root), repository, goal_id, client=second).status == "ready"
    assert second.contexts[0]["past_papers_test"] == list(PAST_PAPER_LOS)
    view = DL.scope_view(load_vault(paths.root), repository, goal_id)
    marks = {topic["learning_object_id"]: topic["on_past_papers"] for topic in view["topics"]}
    assert marks.get("lo_eigen") is False  # a physics paper does not make it "on your past papers"


# --- F2: facet-carried mappings ----------------------------------------------------------------

def _facet_cites(paths, lo_id: str, facet_id: str, span: str) -> None:
    """Give the LO a blueprint on ``facet_id`` and put the assessment citation on the facet only."""

    lo_path = paths.learning_object_path("linear-algebra", lo_id)
    lo = read_yaml(lo_path)
    lo["blueprints"] = [{"id": f"bp_{lo_id}", "recipes": [{"id": f"r_{lo_id}", "any_of": [
        {"facet": facet_id, "capability": "procedure_execution"}]}]}]
    write_yaml(lo_path, lo)
    data = read_yaml(paths.facets_path)
    for facet in data["facets"]:
        if facet["id"] == facet_id:
            facet["provenance"] = {"origin": "manual", "source_refs": [ref("src_paper", "ext_paper", span)]}
    write_yaml(paths.facets_path, data)


def test_a_mapping_carried_by_a_canonical_facet_counts(tmp_path):
    paths, repository = build_exam_scope_vault(tmp_path / "vault")
    _facet_cites(paths, "lo_eigen", "facet_eigen", SPANS["paper_q2"])  # blueprint_only
    vault = load_vault(paths.root)
    refs = vault.learning_objects["lo_eigen"].provenance.source_refs
    assert all(getattr(r, "extraction_id", None) != "ext_paper" for r in refs)  # on the facet only
    assert "lo_eigen" in DL.past_paper_learning_objects(vault, repository, LA)
    goal_id = _deliverable(paths, repository)
    fake = DeliverableFake()
    assert DL.resolve(load_vault(paths.root), repository, goal_id, client=fake).status == "ready"
    assert "lo_eigen" in fake.contexts[0]["past_papers_test"]
    view = DL.scope_view(load_vault(paths.root), repository, goal_id)
    assert {t["learning_object_id"]: t["on_past_papers"] for t in view["topics"]}["lo_eigen"] is True


def test_a_held_out_unit_cited_by_a_facet_contributes_nothing(tmp_path):
    paths, repository = build_exam_scope_vault(tmp_path / "vault")
    _facet_cites(paths, "lo_eigen", "facet_eigen", SPANS["paper_q3"])  # held_out_evaluation
    assert "lo_eigen" not in DL.past_paper_learning_objects(load_vault(paths.root), repository, LA)


# --- F4: revalidated before every request and the publication ------------------------------------

def _hold_q1(repository) -> None:
    save_unit_selection(repository, "ext_paper", list(PAPER), exam_use_modes={
        "paper_q1": "held_out_evaluation", "paper_q2": "blueprint_only", "paper_q3": "held_out_evaluation"})


def test_a_mapping_held_out_during_the_call_publishes_nothing(tmp_path):
    """Text-only inputs: lo_matrices is sent because of paper_q1 alone; paper_q1 is held out while
    the resolver answers, so the answer is never published."""

    paths, repository = build_exam_scope_vault(tmp_path / "vault")
    goal_id = _deliverable(paths, repository)
    vault = load_vault(paths.root)
    goal_before = DL.goal_of(vault, goal_id).facet_scope.model_dump()

    class Holding(DeliverableFake):
        def complete(self, request):
            _hold_q1(repository)
            return super().complete(request)

    fake = Holding()
    result = DL.resolve(vault, repository, goal_id, client=fake)
    assert fake.calls == 1 and "lo_matrices" in fake.contexts[0]["past_papers_test"]
    assert result.status == "unavailable" and result.reason == "protection_changed"
    assert _rows(repository, "SELECT COUNT(*) FROM deliverable_scope_resolutions WHERE goal_id = ?",
                 (goal_id,)) == [(0,)]
    assert DL.goal_of(load_vault(paths.root), goal_id).facet_scope.model_dump() == goal_before


def test_a_mapping_held_out_before_the_request_is_never_sent(tmp_path, monkeypatch):
    paths, repository = build_exam_scope_vault(tmp_path / "vault")
    goal_id = _deliverable(paths, repository)
    built = DL.build_scope_prompt

    def build_then_hold(*args, **kwargs):
        prompt = built(*args, **kwargs)
        assert "lo_matrices" in prompt.past_papers
        _hold_q1(repository)
        return prompt

    monkeypatch.setattr(DL, "build_scope_prompt", build_then_hold)
    fake = DeliverableFake()
    result = DL.resolve(load_vault(paths.root), repository, goal_id, client=fake)
    assert fake.calls == 0
    assert result.status == "unavailable" and result.reason == "protection_changed"


def test_a_change_that_leaves_the_sent_ids_practice_available_publishes(tmp_path):
    paths, repository = build_exam_scope_vault(tmp_path / "vault")
    goal_id = _deliverable(paths, repository)

    class Unrelated(DeliverableFake):
        def complete(self, request):
            # paper_q3 was already held out; marking it again changes nothing sent.
            save_unit_selection(repository, "ext_paper", list(PAPER), exam_use_modes={
                "paper_q1": "available_for_practice", "paper_q2": "blueprint_only",
                "paper_q3": "held_out_evaluation"})
            return super().complete(request)

    assert DL.resolve(load_vault(paths.root), repository, goal_id, client=Unrelated()).status == "ready"


# --- F3: a syllabus never becomes practice ---------------------------------------------------------

def _syllabus_textbook(root, *, unit_override: bool):
    from tests.source_service_fakes import build_textbook_vault

    paths, repository, spans = build_textbook_vault(root)
    text = {"source_id": "src_text", "revision_id": "rev_text", "default_role": "primary_textbook"}
    if unit_override:
        text.update(scope=[{"unit_id": "exercises", "role_override": "syllabus"}], scope_extraction_id="ext_text",
                    scope_revision_id="rev_text")
    else:
        text["default_role"] = "syllabus"
    upsert_source_set(paths.root, {"id": "sset_la", "subject_id": "linear-algebra", "title": "Linear algebra sources",
                                   "members": [
                                       {"source_id": "src_book", "revision_id": "rev_book",
                                        "default_role": "primary_textbook"},
                                       {"source_id": "src_exam", "revision_id": "rev_exam", "default_role": "exam"},
                                       text]})
    return paths, repository, spans


@pytest.mark.parametrize("unit_override", [False, True], ids=["syllabus_member", "syllabus_unit_override"])
def test_a_syllabus_exercise_is_refused_before_any_model_call(tmp_path, unit_override):
    from learnloop.content.authoring import source_exercise_import as SEI
    from tests.source_service_fakes import FakeServiceLLM, service_clients

    paths, repository, spans = _syllabus_textbook(tmp_path / "vault", unit_override=unit_override)
    span = spans["exercises"][1]
    vault = load_vault(paths.root)
    assert not EM.exam_material(vault, repository).covers("ext_text", span)  # never protected...
    assert EM.scope_only_among(vault, repository, [("ext_text", span)])  # ...and never practice
    items_before = set(vault.practice_items)
    llm = FakeServiceLLM()
    outcome = SEI.import_source_exercise(paths.root, repository, extraction_id="ext_text", span_ids=[span],
                                         caller="learner", clients=service_clients(llm))
    assert outcome["status"] == "rejected" and outcome["reason"] == EM.SCOPE_ONLY_REFUSAL, outcome
    assert outcome["practice_item_id"] is None and llm.calls == []
    assert set(load_vault(paths.root).practice_items) == items_before


def test_a_unit_override_leaves_the_rest_of_the_book_practice(tmp_path):
    from learnloop.content.authoring import source_exercise_import as SEI
    from tests.source_service_fakes import FakeServiceLLM, service_clients

    paths, repository, spans = _syllabus_textbook(tmp_path / "vault", unit_override=True)
    vault = load_vault(paths.root)
    assert not EM.scope_only_among(vault, repository, [("ext_text", spans["ch5"][1])])
    # Control: the same import with the role taken off writes (the refusal is the role's alone).
    paths2, repository2, spans2 = _syllabus_textbook(tmp_path / "control", unit_override=False)
    upsert_source_set(paths2.root, {"id": "sset_la", "subject_id": "linear-algebra",
                                    "title": "Linear algebra sources", "members": [
                                        {"source_id": "src_text", "revision_id": "rev_text",
                                         "default_role": "primary_textbook"}]})
    outcome = SEI.import_source_exercise(paths2.root, repository2, extraction_id="ext_text",
                                         span_ids=[spans2["exercises"][1]], caller="learner",
                                         clients=service_clients(FakeServiceLLM()), label="Exercise 1")
    assert outcome["status"] == "written", outcome


def test_a_syllabus_made_during_the_import_writes_nothing(tmp_path):
    from learnloop.content.authoring import source_exercise_import as SEI
    from tests.source_service_fakes import FakeServiceLLM, service_clients

    paths, repository, spans = _syllabus_textbook(tmp_path / "vault", unit_override=False)
    # Start as a textbook; it becomes a syllabus while the exercise is being authored.
    upsert_source_set(paths.root, {"id": "sset_la", "subject_id": "linear-algebra", "title": "Linear algebra sources",
                                   "members": [{"source_id": "src_text", "revision_id": "rev_text",
                                                "default_role": "primary_textbook"}]})
    items_before = set(load_vault(paths.root).practice_items)

    class Turning(FakeServiceLLM):
        def complete(self, request):
            if request.result_model.__name__ == "ExerciseAuthoring":
                upsert_source_set(paths.root, {"id": "sset_la", "subject_id": "linear-algebra",
                                               "title": "Linear algebra sources", "members": [
                                                   {"source_id": "src_text", "revision_id": "rev_text",
                                                    "default_role": "syllabus"}]})
            return super().complete(request)

    llm = Turning()
    outcome = SEI.import_source_exercise(paths.root, repository, extraction_id="ext_text",
                                         span_ids=[spans["exercises"][1]], caller="learner",
                                         clients=service_clients(llm), label="Exercise 1")
    assert any(name == "ExerciseAuthoring" for _purpose, name in llm.calls)
    assert outcome["status"] == "rejected" and outcome["reason"] == EM.SCOPE_ONLY_REFUSAL, outcome
    assert set(load_vault(paths.root).practice_items) == items_before


@pytest.mark.parametrize("unit_override", [False, True], ids=["syllabus_member", "syllabus_unit_override"])
def test_the_reader_s_own_import_refuses_a_syllabus_before_any_model_call(tmp_path, monkeypatch, unit_override):
    from learnloop.clock import FrozenClock
    from learnloop.content.authoring.source_exercise_import import selection_for_region
    from learnloop.content.pipeline import jobs
    from learnloop.content.pipeline.runner import IngestRunnerError, JobContext, RunnerServices
    from tests.source_service_fakes import FakeServiceLLM

    paths, repository, spans = _syllabus_textbook(tmp_path / "vault", unit_override=unit_override)
    selection = selection_for_region(repository, "ext_text", [spans["exercises"][1]], vault=load_vault(paths.root))
    llm = FakeServiceLLM()
    ctx = JobContext(repo=repository, vault_root=paths.root,
                     job={"id": "job_1", "attempt_count": 1,
                          "payload": {"extraction_id": "ext_text", "source_id": "src_text",
                                      "raw_selection": selection}},
                     clock=FrozenClock(datetime(2026, 11, 1, tzinfo=UTC)), worker_id="w",
                     services=RunnerServices(exercise_import_client_factory=lambda _ctx: llm,
                                             background_key_checks=False))
    monkeypatch.setattr(JobContext, "report", lambda self, *a, **k: None)
    with pytest.raises(IngestRunnerError) as raised:
        jobs.handle_reader_exercise_import(ctx)
    assert raised.value.code == "scope_only" and llm.calls == []


def test_the_one_write_refuses_a_syllabus_draft(tmp_path):
    """The publication backstop every authoring path shares (``write_draft``)."""

    from learnloop.content.authoring import exercise_authoring as EX
    from learnloop.content.authoring.source_exercise_import import selection_for_region
    from tests.source_service_fakes import FakeServiceLLM

    paths, repository, spans = _syllabus_textbook(tmp_path / "vault", unit_override=False)
    upsert_source_set(paths.root, {"id": "sset_la", "subject_id": "linear-algebra", "title": "Linear algebra sources",
                                   "members": [{"source_id": "src_text", "revision_id": "rev_text",
                                                "default_role": "primary_textbook"}]})
    span = spans["exercises"][1]
    selection = selection_for_region(repository, "ext_text", [span], vault=load_vault(paths.root))
    batch = EX.author_exercises(paths.root, repository, FakeServiceLLM(), extraction_id="ext_text",
                                raw_selection=selection, source_id="src_text", revision_id="rev_text")
    assert batch.drafts
    upsert_source_set(paths.root, {"id": "sset_la", "subject_id": "linear-algebra", "title": "Linear algebra sources",
                                   "members": [{"source_id": "src_text", "revision_id": "rev_text",
                                                "default_role": "syllabus"}]})
    items_before = set(load_vault(paths.root).practice_items)
    with pytest.raises(EX.ExerciseAuthoringError, match="scope_only"):
        EX.write_exercises(paths.root, repository, batch)
    assert set(load_vault(paths.root).practice_items) == items_before


# --- F5 (backend): the syllabi the panel offers -------------------------------------------------

def test_the_scope_view_offers_readable_syllabi_only(tmp_path):
    paths, repository = build_exam_scope_vault(tmp_path / "vault")
    goal_id = _deliverable(paths, repository)
    view = DL.scope_view(load_vault(paths.root), repository, goal_id)
    assert view["syllabi"] == [{"extraction_id": "ext_syl", "title": "Course syllabus"}]  # never ext_syl_exam
    # Attaching it whole is the passage input the panel sends (no selection).
    row = DL.add_input(load_vault(paths.root), repository, goal_id, "passage", extraction_id="ext_syl", span_ids=[])
    assert row["kind"] == "passage"


def test_a_vault_without_a_syllabus_keeps_c0b_s_view(tmp_path):
    paths, repository = build_exam_scope_vault(tmp_path / "vault", syllabus_role="exam")
    goal_id = _deliverable(paths, repository)
    assert "syllabi" not in DL.scope_view(load_vault(paths.root), repository, goal_id)


def test_a_second_active_subject_without_topics_sends_linear_algebras_papers_as_its_own_group(tmp_path):
    """Orchestrator scoped verify remainder of F1: the last fallback is the vault's only *active
    subject*, not the only subject its active topics happen to name. Physics is active but has no
    topics yet, so the deliverable's subject is ambiguous: C2b's option A sends linear algebra's
    papers as linear algebra's group (never as this course's flat list), to be used only if the
    deliverable is linear algebra's; physics has no group."""

    paths, repository = build_exam_scope_vault(tmp_path / "vault")
    add_subject(paths.root, "physics", "Physics")
    goal_id = _deliverable(paths, repository, "everything on my midterm")
    vault = load_vault(paths.root)
    assert {"linear-algebra", "physics"} <= set(vault.subjects)
    assert not any("physics" in (lo.subjects or ()) for lo in vault.learning_objects.values())
    assert DL.deliverable_subjects(vault, repository, goal_id, _scope_rows(repository, goal_id)) == frozenset()
    prompt = _prompt(paths, repository, goal_id)
    context = prompt_context(prompt.text)
    assert prompt.version == DL.SCOPE_PAST_PAPERS_GROUPED_PROMPT_VERSION and "past_papers_test" not in context
    assert [group["topics"] for group in context["past_papers_by_subject"]] == [list(PAST_PAPER_LOS)]
    fake = DeliverableFake()
    assert DL.resolve(vault, repository, goal_id, client=fake).status == "ready"
    assert "past_papers_test" not in fake.contexts[0]


def test_a_paused_second_subject_keeps_the_only_active_subject_s_past_papers(tmp_path):
    """Control: a paused subject is not active, so the vault's only active subject still names the
    deliverable's subject."""

    paths, repository = build_exam_scope_vault(tmp_path / "vault")
    add_subject(paths.root, "physics", "Physics")
    vault = load_vault(paths.root)
    subject_file = vault.subjects["physics"].path
    metadata, body = read_markdown_frontmatter_data(subject_file)
    write_markdown_with_frontmatter(subject_file, {**metadata, "status": "paused"}, body)
    goal_id = _deliverable(paths, repository, "everything on my midterm")
    vault = load_vault(paths.root)
    assert vault.subjects["physics"].metadata.status == "paused"
    assert DL.deliverable_subjects(vault, repository, goal_id, _scope_rows(repository, goal_id)) == frozenset(LA)
    assert prompt_context(_prompt(paths, repository, goal_id).text)["past_papers_test"] == list(PAST_PAPER_LOS)
