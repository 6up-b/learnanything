"""S2b (G10): intervention needs are fulfilled from the sources before generation (mvp-0.16)."""
from __future__ import annotations

import pytest

from learnloop.algorithm_versions import SOURCE_FIRST_NEEDS_ALGORITHM_VERSION, SOURCE_REFERENCE_GATE_ALGORITHM_VERSION
from learnloop.content.authoring import pf_sandbox
from learnloop.db.stores.source_service import imports_for_item
from learnloop.instructional.needs import fulfil_need_from_sources, need_intent, source_first_active
from tests.helpers import set_algorithm_version
from tests.source_service_fakes import FakeServiceLLM, build_textbook_vault, loaded, service_clients, set_config


def _need(repository, *, facets=("facet_eigen",), focus=None, lo="lo_matrices"):
    need_id = repository.upsert_intervention_need({
        "learning_object_id": lo, "desired_intent": "diagnostic", "trigger_reason": "test",
        "target_facets": list(facets), "blocked_reason": "no_suitable_item", "updated_at": "2026-10-12T00:00:00Z",
        "diagnostic_focus": focus, "candidate_requirements": {"same_learning_object": True}})
    return repository.intervention_need(need_id)


@pytest.fixture
def active(tmp_path):
    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    set_algorithm_version(paths, SOURCE_FIRST_NEEDS_ALGORITHM_VERSION)
    return paths, repository, spans


def _fulfil(paths, repository, need, llm, **kwargs):
    return fulfil_need_from_sources(loaded(paths), repository, need, path=kwargs.pop("path", "primed_retry"),
                                    clients=service_clients(llm), rerank_client=llm, **kwargs)


def test_a_primed_retry_need_is_fulfilled_by_a_verified_textbook_exercise(active):
    paths, repository, _spans = active
    need = _need(repository)
    outcome = _fulfil(paths, repository, need, FakeServiceLLM())
    assert outcome["outcome"] == "fulfilled" and outcome["intent"] == "remediate"
    item_id = outcome["practice_item_id"]
    assert loaded(paths).practice_items[item_id].canonical_exercise is not None
    assert repository.intervention_need(need["id"])["status"] == "fulfilled"
    with repository.connection() as connection:
        rows = imports_for_item(connection, item_id)
    assert rows[-1]["need_id"] == need["id"] and rows[-1]["key_status"] in ("book_solution", "checked", "panel_agrees")


def test_an_unverifiable_key_never_fulfils_and_generation_proceeds(active, monkeypatch):
    paths, repository, _spans = active
    monkeypatch.setattr(pf_sandbox, "_sandbox_bwrap_path", lambda: None)
    need = _need(repository)
    outcome = _fulfil(paths, repository, need, FakeServiceLLM(drop_cited_quote=True, key_override="9"))
    assert outcome["outcome"] == "generate"
    assert all(entry["status"] == "rejected" for entry in outcome["tries"])
    assert repository.intervention_need(need["id"])["status"] == "pending"
    vault = loaded(paths)
    assert not [item for item in vault.practice_items.values() if item.canonical_exercise is not None]


def test_discriminate_drafts_must_pass_the_choosers_own_gate(active, monkeypatch):
    """The chooser's unchanged gate decides (it reads the draft's profiled
    rubric): a draft it refuses is never written and the need generates."""

    from learnloop.instructional import needs as needs_module

    paths, repository, _spans = active
    misconception = repository.insert_misconception(
        learning_object_id="lo_matrices", statement="Eigenvalues are the diagonal entries of any matrix",
        target_facet="facet_eigen", severity=0.9)
    need = _need(repository, focus={"misconception_ids": [misconception],
                                    "misconception_statements": {misconception: "diagonal entries"}})
    assert need_intent(need, "cli") == "discriminate" and need_intent(need, "primed_retry") == "remediate"
    seen = []

    def refusing_gate(repository_, vault_, item, rubric, hypothesis_set, active_mcs, tau):
        seen.append({error.misconception_id for error in rubric.fatal_errors})
        return False, 0.0, 0.0

    monkeypatch.setattr(needs_module, "misconception_discrimination", refusing_gate)
    outcome = _fulfil(paths, repository, need, FakeServiceLLM(), path="cli")
    assert outcome["outcome"] == "generate"
    assert outcome["tries"] and all(entry["status"] != "written" for entry in outcome["tries"])
    assert seen and all(misconception in linked for linked in seen)  # the gate read the screen's links


def test_a_value_stop_makes_the_need_stale_without_writing_or_generating(active):
    from learnloop.diagnosis.probe_hypotheses import H_OTHER

    paths, repository, _spans = active
    set_id = repository.insert_hypothesis_set(learning_object_id="lo_matrices", probe_phase_id="p",
                                              hypotheses=[{"label": "h1"}, {"label": "h2"}, {"label": H_OTHER}],
                                              prior={"h1": 0.5, "h2": 0.4, H_OTHER: 0.1},
                                              algorithm_version="mvp-0.6", prior_basis="support_weighted")
    need = _need(repository, focus={"misconception_ids": ["mc_x"]})
    decision = {"hypothesis_set_id": set_id, "action_by_slot": {"h1": "repair_same", "h2": "repair_same"},
                "live_repair_class": "repair_other"}
    outcome = _fulfil(paths, repository, need, FakeServiceLLM(), path="cli", pending_decision=decision)
    assert outcome["outcome"] == "stale" and outcome["reason"].startswith("value_stop:common_action:")
    assert outcome["action_disagreement"] == {"valuation": "repair_same", "live": "repair_other"}
    assert repository.intervention_need(need["id"])["status"] == "stale"


def test_an_unpriced_decision_goes_to_generation(active):
    paths, repository, _spans = active
    need = _need(repository, focus={"misconception_ids": ["mc_x"]})
    outcome = _fulfil(paths, repository, need, FakeServiceLLM(), path="cli",
                      pending_decision={"unavailable": "no_locked_hypothesis_set"})
    assert outcome["outcome"] == "generate" and outcome["verdict"] == "abstain"


def test_below_the_tag_and_with_the_switch_off_nothing_runs(tmp_path):
    paths, repository, _spans = build_textbook_vault(tmp_path / "vault")
    set_algorithm_version(paths, SOURCE_REFERENCE_GATE_ALGORITHM_VERSION)
    llm = FakeServiceLLM()
    assert not source_first_active(loaded(paths))
    assert _fulfil(paths, repository, _need(repository), llm)["outcome"] == "generate" and llm.calls == []
    set_algorithm_version(paths, SOURCE_FIRST_NEEDS_ALGORITHM_VERSION)
    set_config(paths, "source_service", source_first_needs=False)
    assert not source_first_active(loaded(paths))


def test_the_primed_retry_adapter_tries_sources_before_generating(active, monkeypatch):
    from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
    from learnloop.instructional import needs as needs_module
    from learnloop_sidecar.handlers import feedback
    from tests.source_service_fakes import call

    paths, repository, _spans = active
    complete_self_graded_attempt(loaded(paths), repository,
                                 AttemptDraft(practice_item_id="pi_determinant_1", learner_answer_md="x",
                                              attempt_type="independent_attempt"),
                                 SelfGradeInput(criterion_points={"correct": 0}, fatal_errors=[], confidence=3))
    with repository.connection() as connection:
        attempt_id = connection.execute("SELECT id FROM practice_attempts ORDER BY created_at DESC").fetchone()[0]
    need_id = repository.upsert_intervention_need({
        "attempt_id": attempt_id, "learning_object_id": "lo_matrices", "desired_intent": "diagnostic",
        "trigger_reason": "test", "target_facets": ["facet_eigen"], "blocked_reason": "no_suitable_item",
        "updated_at": "2026-10-12T00:00:00Z"})
    fulfilled: list[str] = []

    def fake_fulfil(vault, repository, need, *, path, **_kwargs):
        assert path == "primed_retry" and need["id"] == need_id
        fulfilled.append("pi_eigen_1")
        return {"outcome": "fulfilled", "practice_item_id": "pi_eigen_1", "intent": "remediate"}

    def fake_pick(vault, repository, attempt, need):
        return (vault.practice_items[fulfilled[0]], []) if fulfilled else (None, [])

    monkeypatch.setattr(needs_module, "fulfil_need_from_sources", fake_fulfil)
    monkeypatch.setattr(feedback, "_pick_primed_sibling", fake_pick)
    result = call(paths.root, "start_primed_retry", {"attemptId": attempt_id})["result"]
    assert result["available"] and not result["generated"], sorted(result)
    assert result["source_first"]["outcome"] == "fulfilled"
    assert result["practice_item"]["id"] == "pi_eigen_1"


def test_the_cli_dry_run_names_the_source_first_step(active):
    import json

    from typer.testing import CliRunner

    from learnloop.cli import app

    paths, repository, _spans = active
    _need(repository)
    result = CliRunner().invoke(app, ["generate-diagnostics", "--dry-run", "--json", "--vault", str(paths.root)])
    payload = json.loads(result.stdout)
    assert result.exit_code == 0, result.stdout
    assert payload.get("source_first") is None or all(
        entry["outcome"] == "would_try_sources_first" for entry in payload["source_first"])


def _follow_up_slate(paths, repository):
    from learnloop.diagnosis.followups import _choose_intervention_item

    selection = _choose_intervention_item(
        loaded(paths), repository, attempt_id=None, learning_object_id="lo_matrices",
        exclude_practice_item_id="__none__", target_facets=[], failed_facets=[], intent="diagnostic",
        max_error_severity=0.5)
    return selection, {row["practice_item_id"]: row for row in selection.slate}


@pytest.mark.parametrize("exposure", ["source_read", "impression", "worked_example"])
def test_the_follow_up_rechecks_independence_before_serving_a_need_import(active, exposure):
    """F4 (Codex sources-build review): the item passed the exposure rule when
    it was retrieved; before the follow-up serves it, the learner reads its
    source, sees it in another proposal, or studies a worked example nobody
    judged against it. The follow-up re-checks and does not serve it."""

    from learnloop.db.stores.source_service import insert_impression
    from learnloop.ids import new_ulid

    paths, repository, spans = active
    outcome = _fulfil(paths, repository, _need(repository), FakeServiceLLM())
    item_id = outcome["practice_item_id"]
    _selection, rows = _follow_up_slate(paths, repository)
    assert rows[item_id]["source_first"]["need_id"] and rows[item_id]["source_first"]["serve_time"]["eligible"]
    assert rows[item_id]["gate_passed"]
    canonical = loaded(paths).practice_items[item_id].canonical_exercise
    if exposure == "source_read":
        repository.insert_source_exposure_event({"context": "reader", "extraction_id": canonical.extraction_id,
                                                 "span_id": canonical.span_ids[0]})
        reason = "source_exposed"
    elif exposure == "impression":
        with repository.connection() as connection:
            insert_impression(connection, id="imp_" + new_ulid(), created_at="2099-01-01T00:00:00Z",
                              surface="plan", caller_kind="learner", caller_ref=None, proposal_id="pip_other",
                              candidate_kind="item", practice_item_id=item_id, extraction_id=None, span_ids=[],
                              shown_fields={"prompt": True}, session_id=None)
            connection.commit()
        reason = "seen_in_proposal"
    else:
        repository.insert_source_exposure_event({"context": "reader", "extraction_id": "ext_text",
                                                 "span_id": spans["worked"][1]})
        reason = "worked_example_unjudged"
    selection, rows = _follow_up_slate(paths, repository)
    row = rows[item_id]
    assert reason in row["source_first"]["serve_time"]["reasons"]
    assert not row["gate_passed"] and row["filtered_reason"] == "exposed_since_valuation"
    assert selection.candidate is None or selection.candidate.id != item_id
    # An ordinary item on the LO is not touched by the source-first recheck.
    others = [value for key, value in rows.items() if key != item_id]
    assert others and all("source_first" not in value for value in others)


@pytest.mark.parametrize("switch", ["exercise_arm", "discriminating_search"])
def test_a_phase_switch_turns_the_need_step_off(active, switch):
    """F15: the need step used to inject the arm and the valuer itself."""

    paths, repository, _spans = active
    set_config(paths, "source_service", **{switch: False})
    misconception = repository.insert_misconception(
        learning_object_id="lo_matrices", statement="Eigenvalues are the diagonal entries of any matrix",
        target_facet="facet_eigen", severity=0.9)
    need = _need(repository, focus={"misconception_ids": [misconception],
                                    "misconception_statements": {misconception: "diagonal entries"}})
    llm = FakeServiceLLM()
    outcome = _fulfil(paths, repository, need, llm, path="cli")
    assert outcome["outcome"] == "generate" and outcome["reason"] == f"source_service.{switch} is false"
    assert llm.calls == []
    with repository.connection() as connection:
        proposals = connection.execute("SELECT COUNT(*) FROM practice_index_proposals").fetchone()[0]
    assert proposals == 0
    if switch == "exercise_arm":
        # A primed retry (remediate) is off too.
        assert _fulfil(paths, repository, _need(repository), llm)["outcome"] == "generate"


def test_batch_commands_honour_their_switches(active):
    from learnloop.instructional.harvest import harvest, verify

    paths, repository, _spans = active
    set_config(paths, "source_service", exercise_arm=False, exercise_verification=False)
    vault = loaded(paths)
    assert harvest(vault, repository, dry_run=True, max_cost_usd=None)["status"] == "disabled"
    assert harvest(vault, repository, dry_run=False, max_cost_usd=1.0)["status"] == "disabled"
    assert verify(vault, repository, dry_run=False, max_cost_usd=1.0)["status"] == "disabled"


def test_a_worked_example_outside_the_items_teaching_scope_does_not_block_it(active):
    """Rule 4 at serving reads the scope its valuation-time shortlist came
    from: a worked example studied in a book the LO does not use was never
    a candidate for the judge, so it is not ``unjudged`` against this item."""

    from tests.source_service_fakes import seed_textbook

    paths, repository, _spans = active
    outcome = _fulfil(paths, repository, _need(repository), FakeServiceLLM())
    item_id = outcome["practice_item_id"]
    other = seed_textbook(repository, source_id="src_other", revision_id="rev_other", extraction_id="ext_other",
                          title="Another subject")
    repository.insert_source_exposure_event({"context": "reader", "extraction_id": "ext_other",
                                             "span_id": other["worked"][1]})
    _selection, rows = _follow_up_slate(paths, repository)
    assert rows[item_id]["source_first"]["serve_time"]["eligible"] and rows[item_id]["gate_passed"]


def test_a_need_resumes_its_search_before_it_goes_to_generation(active, monkeypatch):
    """Codex re-review F5: when nothing on the first page passed, the need
    step generated at once although the search had candidates left. It now
    resumes the search from its cursor and generation waits for exhaustion
    (or a refused budget)."""

    from learnloop.instructional import needs as needs_module

    paths, repository, _spans = active
    set_config(paths, "practice_index", candidate_pool=1)
    real = needs_module.import_source_exercise
    seen: list[tuple[str, ...]] = []

    def first_fails(*args, **kwargs):
        seen.append(tuple(kwargs["span_ids"]))
        if len(seen) == 1:
            return {"status": "rejected", "reason": "validation: the draft does not fit the request",
                    "import_id": None, "key_status": None}
        return real(*args, **kwargs)

    monkeypatch.setattr(needs_module, "import_source_exercise", first_fails)
    # A request several textbook exercises answer (the need's own words).
    need = _need(repository, focus={"misconception_statements": {"m": "solve for x to find the eigenvalue"}})
    outcome = _fulfil(paths, repository, need, FakeServiceLLM())
    assert len(seen) >= 2 and len(set(seen)) == len(seen), (seen, outcome)
    assert outcome["outcome"] == "fulfilled", outcome
    assert len(outcome.get("proposal_ids") or [outcome["proposal_id"]]) >= 2


def test_a_discriminate_need_is_fulfilled_with_the_screens_profiles_and_rubric_links(active):
    """Codex re-review F3: a screened exercise reached import with only its
    spans, so its draft had no discrimination profile and no fatal error
    linking the belief, and the chooser's unchanged gate always refused it.
    The persisted screen now becomes the item's profiles and the rubric's
    misconception-linked fatal errors, validated before the gate runs."""

    from learnloop.db.stores.source_service import import_row

    paths, repository, _spans = active
    misconception = repository.insert_misconception(
        learning_object_id="lo_matrices", statement="An eigenvalue is found by subtracting instead of dividing",
        correction_statement="Isolate the variable: subtract, then divide", target_facet="facet_eigen",
        severity=0.9)
    need = _need(repository, focus={"misconception_ids": [misconception],
                                    "misconception_statements": {misconception: "solve for x to find the eigenvalue"}})
    outcome = _fulfil(paths, repository, need, FakeServiceLLM(), path="cli")
    assert outcome["outcome"] == "fulfilled", outcome
    assert outcome["intent"] == "discriminate"
    item = loaded(paths).practice_items[outcome["practice_item_id"]]
    profiles = [profile for profile in item.discrimination_profiles if profile.misconception_id == misconception]
    assert profiles and profiles[0].observable_signature.strip()
    assert profiles[0].observable_signature.strip() != str(item.expected_answer).strip()
    linked = [error for error in item.grading_rubric.fatal_errors if error.misconception_id == misconception]
    assert linked, item.grading_rubric
    assert repository.intervention_need(need["id"])["status"] == "fulfilled"
    with repository.connection() as connection:
        row = import_row(connection, outcome["import_id"])
    diagnostic = row["validation"]["diagnostic"]
    assert diagnostic["screen_judgment_id"] and diagnostic["misconception_ids"] == [misconception]
    assert row["validation"]["chooser_gate"]["ok"] is True
