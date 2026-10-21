"""Reader workbench RW7a: reading paths in the Guide, display only (spec_reader_workbench_v1 §10.1; G47).

* **Honest labels in code (G47; orchestrator note 2).** The judge's
  ``already_shown`` stands only when every LO the section teaches is
  demonstrated (``lo_certification(...).demonstrated``) and ``assumed`` only
  with an open ``assumption_decisions`` row; otherwise ``core``, after the
  model and again at display.
* **Display only (note 1).** With paths, depths, overrides and a skip stored,
  ``get_daily_plan``, ``get_today_queue`` and the guide plan answer the bytes
  recorded on ``a76c8358a`` (``tests/fixtures/reading_paths_base_a76c8358a.json``).
  An override writes one ``learner_card`` verdict and one
  ``reader_path_sections`` row, nothing else; *skip it* marks nothing known.
* **One call per source and depth, cached by the state key** (depth, the
  section list sent, every linked LO's status): a fresh path makes no call;
  each trigger re-judges once; nothing is called while switched off; the
  spend cap is checked before the call.
* **Exam protection (note 3):** withheld sections are never sent or shown,
  stored rows withheld later are not shown, an exam or held-out exercise is
  never named, an exam reading has no path.
* **Depth and DL2 (note 7):** the newer of the Guide's choice and DL2's
  source intent (mapped) governs; DL2's rows are never written.
* **Switch-off pins (note 6):** off, the prompt contract and the guide plan
  are ``a76c8358a``'s and every RPC refuses.

Fakes only (``PathJudgeFake``); no network.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import MasteryState
from learnloop.db.stores import placement as placement_store
from learnloop.intent.control import Scope, apply_choice
from learnloop.source_retrieval import reading_paths as RP
from learnloop.vault.loader import load_vault
from learnloop_sidecar.errors import SidecarError
from tests.helpers import append_config_toml
from tests.reading_path_fixtures import (
    DAY1,
    EXT,
    SOURCE,
    FixedClock,
    PathJudgeFake,
    build_path_vault,
    call,
    cite,
    context,
    normalized,
    table_counts,
)

GOLDEN = json.loads((Path(__file__).parent / "fixtures" / "reading_paths_base_a76c8358a.json").read_text())


@pytest.fixture
def path_vault(tmp_path, monkeypatch):
    clock = FixedClock(monkeypatch)
    paths, repository, spans = build_path_vault(tmp_path / "vault")
    return paths, repository, spans, clock


def _ctx(paths, fake=None, **attrs):
    return context(paths.root, reading_path_judge_client=fake if fake is not None else PathJudgeFake(),
                   reading_path_inline=True, **attrs)


def _path(ctx, **params):
    return call(ctx, "reader.reading_path", {"extractionId": EXT, **params})


def _depth(ctx, depth="learn_to_use_it"):
    return call(ctx, "reader.reading_path_set_depth", {"extractionId": EXT, "depth": depth})


def _override(ctx, section, choice, depth="learn_to_use_it"):
    return call(ctx, "reader.reading_path_override",
                {"extractionId": EXT, "depth": depth, "sectionId": section, "choice": choice})


def _labels(view):
    return {section["sectionId"]: section["label"] for section in view["sections"]}


def _demonstrate(monkeypatch, *lo_ids):
    import learnloop.goals.goal_certification as GC

    real = GC.lo_certification

    def fake(vault, repository, learning_object, **kwargs):
        found = real(vault, repository, learning_object, **kwargs)
        if learning_object.id in lo_ids:
            return type(found)(learning_object_id=learning_object.id, demonstrated=True, component_gaps=(),
                               integration_gaps=())
        return found

    monkeypatch.setattr(GC, "lo_certification", fake)


def _assume(repository, lo_id, assumption_id="as_1"):
    with repository.atomic():
        placement_store.insert_assumption_decision(repository.connection(), {
            "id": assumption_id, "learning_object_id": lo_id, "source": "self_report", "trigger_kind": "i_know_this",
            "trigger_ref": None, "p": None, "interval_json": None, "q_used": None, "theta_known": None,
            "predictor": "self_report", "predictor_version": "v1", "first_review_due": "2026-12-01T00:00:00Z",
            "quick_check_session_id": None, "algorithm_version": "mvp-0.29", "config_json": "{}",
            "inputs_json": "{}", "created_at": "2026-10-01T00:00:00Z"})


def _return(repository, lo_id, assumption_id="as_1"):
    with repository.atomic():
        placement_store.insert_assumption_return(repository.connection(), {
            "id": "ar_1", "assumption_id": assumption_id, "learning_object_id": lo_id, "reason": "dont_know_this",
            "trigger_ref": None, "algorithm_version": "mvp-0.29", "created_at": "2026-10-11T00:00:00Z"})


def _practised(repository, lo_id):
    repository.upsert_mastery_state(MasteryState(
        learning_object_id=lo_id, logit_mean=0.0, logit_variance=1.0, evidence_count=1,
        last_evidence_at="2026-10-11T00:00:00Z", algorithm_version="mvp-0.29", updated_at="2026-10-11T00:00:00Z"))


def _rows(repository, sql, params=()):
    with repository.connection() as connection:
        return [tuple(row) for row in connection.execute(sql, params).fetchall()]


# -- configuration, the contract, the palette and the switch-off pins ---------------------------------


def test_on_by_default_classified_and_the_contract_and_palette_gain_only_rw7a_keys(path_vault):
    from learnloop.config.schema import LearnLoopConfig, ReadingPathsConfig
    from learnloop.params.parameter_registry import classify_config_path

    paths, _repository, _spans, _clock = path_vault
    keys = [f"reading_paths.{name}" for name in ReadingPathsConfig.model_fields]
    assert keys == ["reading_paths.enabled", "reading_paths.max_daily_cost_usd"]
    for path in [*keys, "ai.routing.reading_path_judge"]:
        rule = classify_config_path(path)
        assert rule is not None and (rule.kind, rule.param_class) == ("structural", "operational"), path
    defaults = LearnLoopConfig()
    assert (defaults.reading_paths.enabled, defaults.reading_paths.max_daily_cost_usd) == (True, 0.5)
    assert defaults.ai.routing.reading_path_judge is None

    contract = json.loads(normalized(call(context(paths.root), "reader.prompt_contract", {})))
    assert contract.pop("readingPaths") == {"enabled": True, "depths": [
        {"id": "get_the_idea", "label": "get the idea"}, {"id": "learn_to_use_it", "label": "learn to use it"},
        {"id": "fluency", "label": "fluency"}]}
    orient = next(group for group in contract["intent"]["palette"] if group["group"] == "orient")
    added = orient["actions"].pop(0)
    assert added == {"id": "what_matters_here", "group": "orient", "intention": "orient",
                     "label": "what matters here?", "effect": {"kind": "reading_path"}, "model": False}
    # Everything else is the a76c8358a contract exactly.
    assert contract == GOLDEN["contract"]


def test_switched_off_the_guide_contract_and_palette_are_a76c8358a_and_every_rpc_refuses(path_vault):
    paths, repository, _spans, _clock = path_vault
    append_config_toml(paths.root, "[reading_paths]\nenabled = false\n")
    fake = PathJudgeFake()
    ctx = _ctx(paths, fake)
    assert json.loads(normalized(call(ctx, "get_daily_plan", {}))) == GOLDEN["plan"]
    assert json.loads(normalized(call(ctx, "get_today_queue", {}))) == GOLDEN["queue"]
    assert json.loads(normalized(call(ctx, "reader.guide_plan", {"extraction_id": EXT}))) == GOLDEN["guide"]
    assert json.loads(normalized(call(ctx, "reader.prompt_contract", {}))) == GOLDEN["contract"]
    before = table_counts(repository)
    for name, params in (("reader.reading_path", {"extractionId": EXT}),
                         ("reader.reading_path_set_depth", {"extractionId": EXT, "depth": "fluency"}),
                         ("reader.reading_path_override", {"extractionId": EXT, "depth": "fluency",
                                                           "sectionId": "sec_eigen", "choice": "skip"})):
        with pytest.raises(SidecarError) as caught:
            call(ctx, name, params)
        assert caught.value.code == "reading_paths_disabled"
    assert fake.calls == 0 and table_counts(repository) == before


# -- display only (G47): plan builds and Today are a76c8358a's ---------------------------------------


def test_with_paths_depths_overrides_and_a_skip_stored_plan_today_and_guide_are_a76c8358a(path_vault, monkeypatch):
    paths, repository, _spans, _clock = path_vault
    ctx = _ctx(paths, PathJudgeFake({"sec_history": "enrichment", "sec_spectral": "prerequisite"}))
    assert _depth(ctx)["status"] == "ready"
    _override(ctx, "sec_eigen", "skip")
    _override(ctx, "sec_history", "read_anyway")
    _depth(ctx, "fluency")
    _override(ctx, "sec_diag", "skip", depth="fluency")
    with repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM reader_path_sections").fetchone()[0] == 11
    ctx = context(paths.root)
    assert json.loads(normalized(call(ctx, "get_daily_plan", {}))) == GOLDEN["plan"]
    assert json.loads(normalized(call(ctx, "get_today_queue", {}))) == GOLDEN["queue"]
    assert json.loads(normalized(call(ctx, "reader.guide_plan", {"extraction_id": EXT}))) == GOLDEN["guide"]


def test_an_override_writes_one_learner_card_and_one_row_and_skip_marks_nothing_known(path_vault):
    paths, repository, _spans, _clock = path_vault
    ctx = _ctx(paths)
    _depth(ctx)
    vault = load_vault(paths.root)
    statuses = RP.lo_statuses(vault, repository, ["lo_eigen_basics", "lo_spectral", "lo_diag"])
    before = table_counts(repository)
    view = _override(ctx, "sec_eigen", "skip")
    after = table_counts(repository)
    changed = {name: (before[name], after[name]) for name in after if after[name] != before.get(name)}
    assert changed == {"judgment_ledger": (before["judgment_ledger"], before["judgment_ledger"] + 1),
                       "reader_path_sections": (before["reader_path_sections"], before["reader_path_sections"] + 1)}
    card = _rows(repository, "SELECT judge, verdict, task, right_id FROM judgment_ledger ORDER BY created_at DESC, "
                             "rowid DESC LIMIT 1")
    assert card == [("learner_card", "skip", "reading_path_role", "sec_eigen")]
    section = next(s for s in view["sections"] if s["sectionId"] == "sec_eigen")
    assert (section["label"], section["override"], section["effectiveLabel"]) == ("core", "skip", "skipped")
    # Skip marks nothing as known: the statuses, mastery and assumptions are as they were.
    assert RP.lo_statuses(vault, repository, ["lo_eigen_basics", "lo_spectral", "lo_diag"]) == statuses
    assert after["assumption_decisions"] == before["assumption_decisions"] == 0
    assert repository.mastery_states() == {} or all(
        state.evidence_count == 0 for state in repository.mastery_states().values())


def test_an_override_is_kept_across_a_rejudgment_and_can_be_cleared(path_vault):
    paths, repository, _spans, _clock = path_vault
    fake = PathJudgeFake({"sec_history": "enrichment"})
    ctx = _ctx(paths, fake)
    _depth(ctx)
    _override(ctx, "sec_history", "read_anyway")
    _practised(repository, "lo_diag")  # a status change: one new judgment
    view = _path(ctx)
    assert fake.calls == 2 and view["status"] == "ready"
    history = next(s for s in view["sections"] if s["sectionId"] == "sec_history")
    assert (history["label"], history["override"], history["effectiveLabel"]) == ("enrichment", "read_anyway", "core")
    view = _override(ctx, "sec_history", "none")
    history = next(s for s in view["sections"] if s["sectionId"] == "sec_history")
    assert (history["override"], history["effectiveLabel"]) == (None, "enrichment")


# -- honest labels (G47), after the model and at display ---------------------------------------------


def test_already_shown_stands_only_when_every_lo_the_section_teaches_is_demonstrated(path_vault, monkeypatch):
    paths, _repository, _spans, _clock = path_vault
    fake = PathJudgeFake({"sec_eigen": "already_shown", "sec_history": "already_shown"})
    ctx = _ctx(paths, fake)
    view = _depth(ctx)
    labels = _labels(view)
    # Not demonstrated, and a section with no LO: never already shown.
    assert labels["sec_eigen"] == "core" and labels["sec_history"] == "core"
    eigen = next(s for s in view["sections"] if s["sectionId"] == "sec_eigen")
    assert eigen["reason"] == RP.NOT_SHOWN_REASON
    _demonstrate(monkeypatch, "lo_eigen_basics")
    view = _path(ctx)
    assert fake.calls == 2  # the status changed: re-judged once
    eigen = next(s for s in view["sections"] if s["sectionId"] == "sec_eigen")
    assert (eigen["label"], eigen["chip"]) == ("already_shown", "already shown ●")
    assert eigen["reason"] == "You've shown this on your own: Eigenvalues."
    assert _labels(view)["sec_history"] == "core"


def test_a_stored_already_shown_is_shown_as_core_once_the_evidence_no_longer_holds(path_vault, monkeypatch):
    paths, _repository, _spans, _clock = path_vault
    import learnloop.goals.goal_certification as GC

    real = GC.lo_certification
    fake = PathJudgeFake({"sec_eigen": "already_shown"})
    ctx = _ctx(paths, fake)
    _demonstrate(monkeypatch, "lo_eigen_basics")
    assert _labels(_depth(ctx))["sec_eigen"] == "already_shown"
    monkeypatch.setattr(GC, "lo_certification", real)
    view = _path(ctx, judge=False)  # no new judgment: the display re-checks
    assert fake.calls == 1 and view["status"] == "stale" and view["stale"] is True
    eigen = next(s for s in view["sections"] if s["sectionId"] == "sec_eigen")
    assert (eigen["label"], eigen["reason"]) == ("core", RP.NOT_SHOWN_REASON)


def test_assumed_stands_only_with_an_open_assumption_row(path_vault):
    paths, repository, _spans, _clock = path_vault
    fake = PathJudgeFake({"sec_spectral": "assumed", "sec_history": "assumed"})
    ctx = _ctx(paths, fake)
    view = _depth(ctx)
    assert _labels(view)["sec_spectral"] == "core" and _labels(view)["sec_history"] == "core"
    spectral = next(s for s in view["sections"] if s["sectionId"] == "sec_spectral")
    assert spectral["reason"] == RP.NOT_ASSUMED_REASON
    _assume(repository, "lo_spectral")
    view = _path(ctx)
    spectral = next(s for s in view["sections"] if s["sectionId"] == "sec_spectral")
    assert fake.calls == 2 and (spectral["label"], spectral["reason"]) == (
        "assumed", "Assumed known (not tested): Spectral Theorem.")
    _return(repository, "lo_spectral")  # "I don't know this" closes it
    view = _path(ctx)
    # Back to the first state ("new"): its cached path, no call, and core.
    assert fake.calls == 2 and _labels(view)["sec_spectral"] == "core"


def test_unknown_labels_and_sections_the_model_left_out_are_core_and_unknown_ids_are_dropped(path_vault):
    paths, repository, _spans, _clock = path_vault

    class Odd(PathJudgeFake):
        def complete(self, request):
            answer = super().complete(request)
            sections = [entry for entry in answer.sections if entry.section_id != "sec_diag"]
            sections[0] = type(sections[0])(section_id=sections[0].section_id, label="essential", reason="x")
            sections.append(type(sections[0])(section_id="sec_nowhere", label="core", reason="y"))
            return type(answer)(sections=sections)

    view = _depth(_ctx(paths, Odd()))
    assert _labels(view) == {"sec_eigen": "core", "sec_spectral": "core", "sec_diag": "core", "sec_history": "core"}
    assert {row[0] for row in _rows(repository, "SELECT section_id FROM reader_path_sections")} == {
        "sec_eigen", "sec_spectral", "sec_diag", "sec_history"}


def test_honest_label_is_pure_and_total():
    demonstrated = RP.LoStatus("demonstrated", True, False)
    assumed = RP.LoStatus("assumed", False, True)
    new = RP.LoStatus("new", False, False)
    statuses = {"a": demonstrated, "b": assumed, "c": new}
    assert RP.honest_label("already_shown", ["a"], statuses) == ("already_shown", False)
    assert RP.honest_label("already_shown", ["a", "b"], statuses) == ("core", True)
    assert RP.honest_label("already_shown", [], statuses) == ("core", True)
    assert RP.honest_label("assumed", ["a", "b"], statuses) == ("assumed", False)
    assert RP.honest_label("assumed", ["a"], statuses) == ("core", True)
    assert RP.honest_label("assumed", ["b", "c"], statuses) == ("core", True)
    assert RP.honest_label("assumed", ["zzz"], statuses) == ("core", True)
    assert RP.honest_label("enrichment", [], statuses) == ("enrichment", False)
    assert RP.honest_label("prerequisite", ["c"], statuses) == ("prerequisite", False)
    assert RP.honest_label("whatever", ["a"], statuses) == ("core", True)


# -- the call: once per source and depth, cached, re-judged on its triggers ---------------------------


def test_the_depth_is_asked_first_and_nothing_is_called_until_it_is_known(path_vault):
    paths, repository, _spans, _clock = path_vault
    fake = PathJudgeFake()
    ctx = _ctx(paths, fake)
    view = _path(ctx)
    assert view["status"] == "ask_depth"
    assert [d["id"] for d in view["depths"]] == list(RP.DEPTHS) and view["sections"] == []
    assert fake.calls == 0
    assert _rows(repository, "SELECT COUNT(*) FROM model_call_receipts")[0][0] == 0


def test_one_call_per_source_and_depth_and_a_fresh_path_makes_no_call_on_guide_open(path_vault):
    paths, repository, _spans, _clock = path_vault
    fake = PathJudgeFake()
    ctx = _ctx(paths, fake)
    assert _depth(ctx)["status"] == "ready" and fake.calls == 1
    for _ in range(3):
        assert _path(ctx)["status"] == "ready"
    # Another Guide open (a new sidecar): still the cached path.
    assert _path(_ctx(paths, fake))["status"] == "ready" and fake.calls == 1
    receipts = _rows(repository, "SELECT owner_kind FROM model_call_receipts WHERE parent_call_id IS NULL")
    assert ("reading_path_judge",) in receipts


def test_rejudged_once_each_when_the_depth_the_section_list_or_an_lo_status_changes(path_vault, monkeypatch):
    paths, repository, spans, _clock = path_vault
    fake = PathJudgeFake()
    ctx = _ctx(paths, fake)
    first = _depth(ctx)
    keys = [first["stateKey"]]
    # The depth.
    keys.append(_depth(ctx, "fluency")["stateKey"])
    assert fake.calls == 2
    # Back to a depth already judged in this state: the cached path, no call.
    assert _depth(ctx)["stateKey"] == keys[0] and fake.calls == 2
    _depth(ctx, "fluency")
    # An LO's status.
    _practised(repository, "lo_spectral")
    keys.append(_path(ctx)["stateKey"])
    assert fake.calls == 3
    # The section list: the history section now teaches an LO.
    cite(paths, "lo_svd_definition", spans["sec_history"][1])
    ctx = _ctx(paths, fake)
    view = _path(ctx)
    keys.append(view["stateKey"])
    assert fake.calls == 4 and len(set(keys)) == 4
    assert next(s for s in view["sections"] if s["sectionId"] == "sec_history")["learningObjectIds"] == [
        "lo_svd_definition"]
    assert _path(ctx)["stateKey"] == keys[-1] and fake.calls == 4
    # Every judgment's rows are kept (append-only).
    assert _rows(repository, "SELECT COUNT(DISTINCT state_key) FROM reader_path_sections")[0][0] == 4


def test_the_state_key_hashes_depth_section_list_and_statuses_only(path_vault):
    paths, repository, _spans, _clock = path_vault
    vault = load_vault(paths.root)
    inputs = RP.path_inputs(vault, repository, EXT)
    assert inputs.state_key("fluency") != inputs.state_key("get_the_idea")
    assert inputs.state_key("fluency") == RP.path_inputs(vault, repository, EXT).state_key("fluency")
    changed = RP.PathInputs(**{**inputs.__dict__, "statuses": {
        **inputs.statuses, "lo_diag": RP.LoStatus("learning", False, False)}})
    assert changed.state_key("fluency") != inputs.state_key("fluency")


def test_a_failed_judgment_says_so_keeps_the_guide_and_try_again_judges_again(path_vault):
    from learnloop.ai.errors import AIProviderUnavailable

    paths, repository, _spans, _clock = path_vault
    fake = PathJudgeFake(fail=AIProviderUnavailable("down"))
    ctx = _ctx(paths, fake)
    view = _depth(ctx)
    assert view["status"] == "failed" and view["sections"] == [] and "Try again" in view["message"]
    attempts = fake.calls  # one judgment (the paid-call wrapper's own bounded retries)
    assert _path(ctx)["status"] == "failed" and fake.calls == attempts  # no retry loop on its own
    fake.fail = None
    assert _path(ctx, retry=True)["status"] == "ready" and fake.calls == attempts + 1


def test_the_spend_cap_and_the_price_are_checked_before_the_call(path_vault):
    paths, repository, _spans, _clock = path_vault
    fake = PathJudgeFake(provider_type="openai")  # metered
    view = _depth(_ctx(paths, fake))
    assert view["status"] == "failed" and view["reason"] == "unpriced" and fake.calls == 0
    append_config_toml(paths.root, "[source_retrieval]\nllm_price_per_million = 2.0\n"
                                   "[reading_paths]\nmax_daily_cost_usd = 0.0\n")
    view = _path(_ctx(paths, fake))
    assert view["status"] == "failed" and view["reason"] == "capped" and fake.calls == 0
    assert "budget ($0.00) is used" in view["message"]
    assert _rows(repository, "SELECT COUNT(*) FROM model_call_receipts")[0][0] == 0


def test_without_an_injected_client_the_suite_reaches_no_model(path_vault):
    paths, repository, _spans, _clock = path_vault
    ctx = context(paths.root, reading_path_inline=True)
    view = _depth(ctx)
    assert view["status"] == "failed" and view["reason"] == "models_off"
    assert _rows(repository, "SELECT COUNT(*) FROM model_call_receipts")[0][0] == 0


def test_each_verdict_appends_the_ledger_and_a_rejudgment_supersedes_it(path_vault):
    paths, repository, _spans, _clock = path_vault
    fake = PathJudgeFake({"sec_eigen": "already_shown"})
    ctx = _ctx(paths, fake)
    _depth(ctx)
    rows = _rows(repository, "SELECT task, left_kind, left_id, right_kind, right_id, judge, judge_model, verdict, "
                             "rationale, supersedes_id FROM judgment_ledger ORDER BY right_id")
    assert [(r[0], r[1], r[2], r[3], r[5], r[6]) for r in rows] == [
        ("reading_path_role", "reading_path", f"{EXT}:learn_to_use_it", "reader_section", "llm", "fake-path-model")
    ] * 4
    eigen = next(r for r in rows if r[4] == "sec_eigen")
    assert eigen[7] == "core" and json.loads(eigen[8])["model_label"] == "already_shown"
    assert json.loads(eigen[8])["enforced"] is True and eigen[9] is None
    linked = _rows(repository, "SELECT s.section_id, l.verdict FROM reader_path_sections s "
                               "JOIN judgment_ledger l ON l.id = s.ledger_id ORDER BY s.section_id")
    assert dict(linked) == {"sec_diag": "core", "sec_eigen": "core", "sec_history": "core", "sec_spectral": "core"}
    _practised(repository, "lo_eigen_basics")
    _path(ctx)
    superseded = _rows(repository, "SELECT COUNT(*) FROM judgment_ledger WHERE supersedes_id IS NOT NULL")
    assert superseded[0][0] == 4


def test_the_prompt_carries_only_the_section_list_roles_statuses_depth_and_goal(path_vault):
    paths, _repository, _spans, _clock = path_vault
    fake = PathJudgeFake()
    _depth(_ctx(paths, fake))
    context_sent = fake.contexts[0]
    assert set(context_sent) == {"depth", "depth_means", "goal", "sections"}
    assert {key for section in context_sent["sections"] for key in section} == {
        "section_id", "title", "book_roles", "proposed_roles", "topics"}
    assert {key for section in context_sent["sections"] for topic in section["topics"] for key in topic} == {
        "title", "status"}
    # No passage text.
    assert "characteristic polynomial" not in fake.prompts[0] and "Diagonalize the matrix" not in fake.prompts[0]


def test_the_goal_it_serves_is_named_and_otherwise_the_path_says_it_follows_the_depth(path_vault):
    paths, _repository, spans, _clock = path_vault
    fake = PathJudgeFake()
    view = _depth(_ctx(paths, fake))
    assert view["goal"] is None and view["goalLine"] == (
        "No active goal covers this book: the path follows the depth you chose.")
    assert fake.contexts[0]["goal"] == ""
    # The basic vault's active goal covers the SVD concept: once a section
    # teaches lo_svd_definition, the path names it (RW7a creates no goal).
    cite(paths, "lo_svd_definition", spans["sec_history"][1])
    view = _path(_ctx(paths, fake))
    assert view["goal"] == {"id": "goal_linear_algebra_ml", "title": "Linear algebra for ML"}
    assert view["goalLine"] == "toward your goal: Linear algebra for ML"
    assert fake.contexts[-1]["goal"] == "Linear algebra for ML"
    assert len(load_vault(paths.root).goals) == 1


# -- the exercise worth trying, and exam protection ----------------------------------------------------


def test_each_core_section_names_its_exercise_block_and_try_it_carries_the_readers_import(path_vault):
    paths, _repository, spans, _clock = path_vault
    view = _depth(_ctx(paths, PathJudgeFake({"sec_diag": "enrichment"})))
    by = {s["sectionId"]: s for s in view["sections"]}
    eigen = by["sec_eigen"]["exercise"]
    assert eigen["label"] == "Exercise 1.1" and eigen["spanIds"] == [spans["sec_eigen"][2]]
    assert eigen["importRequest"] == {
        "extractionId": EXT, "sourceId": SOURCE, "revisionId": "rev_text",
        "rawSelection": {"nodes": [{"spanId": spans["sec_eigen"][2], "start": 0, "end": len(
            "Exercise 1.1 Compute the eigenvalues of the diagonal matrix [[2,0],[0,3]].")}]}}
    # Only core sections name one (sec_diag is enrichment), and only where one exists.
    assert by["sec_diag"]["exercise"] is None and by["sec_spectral"]["exercise"] is None
    # A "read it anyway" makes it core: its exercise is named now.
    view = _override(_ctx(paths), "sec_diag", "read_anyway")
    diag = next(s for s in view["sections"] if s["sectionId"] == "sec_diag")
    assert diag["effectiveLabel"] == "core" and diag["exercise"]["label"] == "Exercise 3.1"


def test_an_exam_or_held_out_exercise_is_never_named(path_vault, monkeypatch):
    from learnloop.content.sources import exam_material as EM

    paths, repository, spans, _clock = path_vault
    exercise_span = spans["sec_eigen"][2]
    real = EM.exam_withheld

    def withheld(vault, repo, keys):
        keys = list(keys)
        return frozenset({tuple(key) for key in keys if key[1] == exercise_span}) | real(vault, repo, keys)

    monkeypatch.setattr(EM, "exam_withheld", withheld)
    view = _depth(_ctx(paths))
    by = {s["sectionId"]: s for s in view["sections"]}
    assert by["sec_eigen"]["exercise"] is None and by["sec_diag"]["exercise"]["label"] == "Exercise 3.1"
    stored = dict(_rows(repository, "SELECT section_id, exercise_span_id FROM reader_path_sections"))
    assert stored["sec_eigen"] is None
    assert exercise_span not in json.dumps(view)


def test_a_stored_exercise_held_out_later_is_not_named(path_vault, monkeypatch):
    from learnloop.content.sources import exam_material as EM

    paths, _repository, spans, _clock = path_vault
    ctx = _ctx(paths)
    assert _depth(ctx)["sections"][0]["exercise"] is not None
    exercise_span = spans["sec_eigen"][2]
    real = EM.exam_withheld
    monkeypatch.setattr(EM, "exam_withheld", lambda vault, repo, keys: frozenset(
        {tuple(key) for key in keys if key[1] == exercise_span}) | real(vault, repo, list(keys)))
    view = _path(ctx)
    assert view["sections"][0]["exercise"] is None and exercise_span not in json.dumps(view)
    assert "Exercise 1.1" not in json.dumps(view)


def test_a_held_out_section_is_never_sent_and_a_stored_one_withheld_later_is_not_shown(path_vault):
    from learnloop.content.synthesis.source_unit_selection import save_unit_selection

    paths, repository, spans, _clock = path_vault
    fake = PathJudgeFake()
    ctx = _ctx(paths, fake)
    _depth(ctx)
    save_unit_selection(repository, EXT, list(spans), exam_use_modes={"sec_diag": "held_out_evaluation"})
    view = _path(ctx, judge=False)
    assert "sec_diag" not in _labels(view) and "Exercise 3.1" not in json.dumps(view)
    assert "Diagonalization" not in json.dumps(view)
    view = _path(ctx)  # the section list changed: one new judgment, without the section
    assert fake.calls == 2 and "sec_diag" not in _labels(view)
    assert [s["section_id"] for s in fake.contexts[1]["sections"]] == ["sec_eigen", "sec_spectral", "sec_history"]
    assert "Diagonalization" not in fake.prompts[1]


def test_an_exam_reading_has_no_path_and_no_call(path_vault, monkeypatch):
    from learnloop.content.sources import exam_material as EM

    paths, repository, _spans, _clock = path_vault
    real = EM.exam_material

    class Whole:
        def __init__(self, inner):
            self.inner = inner

        def covers(self, extraction_id, span_id=None):
            return extraction_id == EXT or self.inner.covers(extraction_id, span_id)

        def withheld(self, keys):
            return frozenset(tuple(key) for key in keys)

    monkeypatch.setattr(EM, "exam_material", lambda vault, repo: Whole(real(vault, repo)))
    fake = PathJudgeFake()
    ctx = _ctx(paths, fake)
    view = _depth(ctx)
    assert view["status"] == "withheld" and view["sections"] == [] and fake.calls == 0
    assert _rows(repository, "SELECT COUNT(*) FROM reader_path_sections")[0][0] == 0


def test_an_unreadable_exam_predicate_shows_no_path(path_vault, monkeypatch):
    from learnloop.content.sources import exam_material as EM

    paths, _repository, _spans, _clock = path_vault

    def broken(vault, repo):
        raise RuntimeError("no")

    monkeypatch.setattr(EM, "exam_material", broken)
    fake = PathJudgeFake()
    view = _path(_ctx(paths, fake))
    assert view["status"] == "withheld" and fake.calls == 0


# -- the suggested next activity, without a model ------------------------------------------------------


def test_the_next_line_is_composed_without_a_model_and_follows_progress_and_choices(path_vault):
    paths, repository, spans, _clock = path_vault
    fake = PathJudgeFake({"sec_eigen": "prerequisite", "sec_history": "enrichment"})
    ctx = _ctx(paths, fake)
    view = _depth(ctx)
    assert view["next"]["text"] == "Next: read §1 Eigenvalues · about 1 min of reading"  # a prerequisite: no exercise
    assert view["next"]["sectionId"] == "sec_eigen"
    repository.upsert_reader_section_progress(
        extraction_id=EXT, section_id="sec_eigen", spans_seen=len(spans["sec_eigen"]),
        span_count=len(spans["sec_eigen"]), completed=True)
    view = _path(ctx)
    assert view["next"]["text"] == "Next: read §2 The spectral theorem · about 1 min of reading"
    _override(ctx, "sec_spectral", "skip")
    view = _path(ctx)
    assert view["next"]["text"] == ("Next: read §3 Diagonalization, then try Exercise 3.1 · about 1 min of reading")
    _depth(ctx, "get_the_idea")  # overrides are per depth; and no exercise at this depth
    view = _path(ctx)
    assert view["next"]["text"] == "Next: read §2 The spectral theorem · about 1 min of reading"
    _override(ctx, "sec_spectral", "skip", depth="get_the_idea")
    assert _path(ctx)["next"]["text"] == "Next: read §3 Diagonalization · about 1 min of reading"
    assert fake.calls == 2  # one per depth; the line itself never calls


def test_next_activity_counts_read_anyway_as_core_and_is_none_when_nothing_is_left():
    sections = [
        {"section_id": "a", "title": "Intro", "effective_label": "enrichment", "words": 10},
        {"section_id": "b", "title": "5.4 Mixtures", "effective_label": "core", "words": 1000,
         "exercise": {"label": "Exercise 5.14"}},
    ]
    line = RP.next_activity(sections, "fluency", {})
    assert line["text"] == "Next: read §5.4 Mixtures, then try Exercise 5.14 · about 5 min of reading"
    sections[0]["effective_label"] = "core"
    assert RP.next_activity(sections, "fluency", {})["section_id"] == "a"
    assert RP.next_activity(sections, "fluency", {"a": {"completed_at": "x"}, "b": {"completed_at": "y"}}) is None


# -- the depth: remembered per source, DL2's intent one setting (display-level) ---------------------


def test_the_depth_is_remembered_per_source_and_changeable(path_vault):
    paths, repository, _spans, _clock = path_vault
    ctx = _ctx(paths)
    _depth(ctx, "fluency")
    view = _path(_ctx(paths))
    assert (view["depth"], view["depthOrigin"], view["depthLabel"]) == ("fluency", "guide", "fluency")
    assert _rows(repository, "SELECT source_id, depth FROM reader_path_depths") == [(SOURCE, "fluency")]


def test_dl2_intent_preselects_the_depth_and_the_newer_setting_wins_without_writing_dl2(path_vault):
    paths, repository, _spans, clock = path_vault
    vault = load_vault(paths.root)
    apply_choice(vault, repository, Scope("source", SOURCE), "master", clock=FrozenClock(DAY1))
    fake = PathJudgeFake()
    ctx = _ctx(paths, fake)
    view = _path(ctx)
    assert (view["depth"], view["depthOrigin"]) == ("fluency", "intent")
    assert view["intent"] == {"choice": "master", "label": "Master"} and view["status"] == "ready"
    commitments = _rows(repository, "SELECT * FROM commitments ORDER BY id")
    versions = _rows(repository, "SELECT * FROM commitment_versions ORDER BY id")
    clock.advance(minutes=5)
    view = _depth(ctx, "get_the_idea")
    assert (view["depth"], view["depthOrigin"]) == ("get_the_idea", "guide")
    # The Guide's choice wrote nothing of DL2's: its stored intent is unchanged.
    assert _rows(repository, "SELECT * FROM commitments ORDER BY id") == commitments
    assert _rows(repository, "SELECT * FROM commitment_versions ORDER BY id") == versions
    assert view["intent"] == {"choice": "master", "label": "Master"}
    # A later DL2 choice governs again (Learn -> learn to use it).
    clock.advance(minutes=5)
    apply_choice(load_vault(paths.root), repository, Scope("source", SOURCE), "learn",
                 clock=FrozenClock(DAY1.replace(minute=30)))
    view = _path(ctx)
    assert (view["depth"], view["depthOrigin"]) == ("learn_to_use_it", "intent")


@pytest.mark.parametrize("choice, depth", [("master", "fluency"), ("learn", "learn_to_use_it"),
                                           ("keep", "get_the_idea"), ("light_touch", "get_the_idea"),
                                           ("pause", None), ("reference", None)])
def test_each_dl2_choice_maps_onto_a_depth_or_asks(path_vault, choice, depth):
    paths, repository, _spans, _clock = path_vault
    vault = load_vault(paths.root)
    apply_choice(vault, repository, Scope("source", SOURCE), choice, clock=FrozenClock(DAY1))
    view = _path(_ctx(paths))
    assert view["depth"] == depth
    assert RP.INTENT_DEPTH.get(choice) == depth


def test_the_newer_setting_is_compared_as_instants_not_strings():
    assert RP._instant("2026-10-12T09:00:00Z") == RP._instant("2026-10-12T09:00:00+00:00")
    assert RP._instant("2026-10-12T09:00:00.500000+00:00") > RP._instant("2026-10-12T09:00:00Z")
    assert RP._instant("2026-10-12T05:30:00-04:00") > RP._instant("2026-10-12T09:00:00Z")
    assert RP._instant("not a time") < RP._instant("2026-10-12T09:00:00Z")


def test_an_unknown_depth_or_choice_is_refused(path_vault):
    paths, _repository, _spans, _clock = path_vault
    ctx = _ctx(paths)
    with pytest.raises(SidecarError) as caught:
        _depth(ctx, "mastery")
    assert caught.value.code == "validation_error"
    _depth(ctx)
    with pytest.raises(SidecarError) as caught:
        _override(ctx, "sec_eigen", "mark_known")
    assert caught.value.code == "validation_error"
    with pytest.raises(SidecarError):
        _override(ctx, "sec_nowhere", "skip")


# -- roles: ingest's role_hint and RW4e's visible proposals (the existing positive reader) ------------


def test_section_roles_combine_role_hint_and_visible_rw4e_proposals(path_vault):
    from learnloop.reader import source_roles as RS

    paths, repository, spans, _clock = path_vault
    vault = load_vault(paths.root)
    RS.propose_roles(vault, repository, [{"extraction_id": EXT, "span_id": spans["sec_spectral"][1],
                                          "role": "intuition", "confidence": "high", "ledger_id": None}],
                     judge=RS.JUDGE_LABELLER, prompt_version="role_labeller.v1", model="seed")
    fake = PathJudgeFake()
    _depth(_ctx(paths, fake))
    by = {s["section_id"]: s for s in fake.contexts[0]["sections"]}
    assert by["sec_spectral"]["proposed_roles"] == ["intuition"]
    assert "exercise" in by["sec_eigen"]["book_roles"]
    append_config_toml(paths.root, "[roles]\npositive_filter_enabled = false\n")
    assert all(not s.proposed_roles for s in RP.path_inputs(load_vault(paths.root), repository, EXT).sections)


# -- the reader report ---------------------------------------------------------------------------------


def test_the_reader_report_counts_labels_overrides_and_depth_choices(path_vault):
    from learnloop.reader.reader_report import build_reader_report

    paths, repository, _spans, _clock = path_vault
    ctx = _ctx(paths, PathJudgeFake({"sec_history": "enrichment"}))
    _depth(ctx)
    _override(ctx, "sec_history", "read_anyway")
    _override(ctx, "sec_eigen", "skip")
    report = build_reader_report(paths.sqlite_path)["reading_paths"]
    assert report == {"judged_sections": 4, "labels": {"core": 3, "enrichment": 1},
                      "overrides": {"core:skip": 1, "enrichment:read_anyway": 1},
                      "depth_choices": {"learn_to_use_it": 1}}
