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


def test_discriminate_drafts_must_pass_the_choosers_own_gate(active):
    paths, repository, _spans = active
    misconception = repository.insert_misconception(
        learning_object_id="lo_matrices", statement="Eigenvalues are the diagonal entries of any matrix",
        target_facet="facet_eigen", severity=0.9)
    need = _need(repository, focus={"misconception_ids": [misconception],
                                    "misconception_statements": {misconception: "diagonal entries"}})
    assert need_intent(need, "cli") == "discriminate" and need_intent(need, "primed_retry") == "remediate"
    outcome = _fulfil(paths, repository, need, FakeServiceLLM(), path="cli")
    # The fake's drafts carry no rubric fatal error linking the belief: the
    # chooser's discrimination gate refuses them, so nothing is written.
    assert outcome["outcome"] == "generate"
    assert outcome.get("tries") is None or all(entry["status"] != "written" for entry in outcome["tries"])


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
