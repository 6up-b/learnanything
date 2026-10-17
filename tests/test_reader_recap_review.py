"""RW6a Codex review fixes (docs/reviews/reader-rw6a-codex-review.md).

* F1 -- "Since last time" dates the LO's real certification transition: the
  recipe predicate (``recipe_gaps``: capabilities, ``any_of`` alternatives,
  corrections) evaluated before and after the previous session ended, over
  the real ledger, not a facet's summed credit crossing 1.
* F3 -- a success later regraded to nothing no longer answers a claim
  needing an independent check: only the attempt's effective (latest) grading
  counts.
* F4 -- resolving an inquiry from Wrap up at the destination moves it from
  Still open to Resolved (with its undo) instead of dropping it.
* F8 -- an abandoned problem stays in the recap with an honest reopen.
* F10 -- with ``reader_inquiry.enabled`` off the recap RPCs refuse
  (``inquiry_disabled``) and the config DTO names no recap switch, so no
  card, no Wrap up and no offer.

Fakes only; no model call anywhere.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.goals.goal_certification import lo_certification
from learnloop.reader import reader_sessions as RS
from learnloop.reader import recap as RC
from learnloop.reader import workbench as WB
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml
from tests.helpers import NOW, append_config_toml
from tests.recap_fixtures import (
    EXT, T0, ask, at, call, context, interaction_rows, iso, problem, resolve, table_counts, visit,
)
from tests.test_goal_certification_any_of import (
    ALT_X, ALT_Y, COMP_A, LO_ID, _component, _item, build_vault,
)
from tests.test_reader_dialogue import _setup

#: A second instrument on COMP_A at a capability no recipe asks for (recall).
RECALL_ITEM = "pi_comp_a_recall"


def _now(minutes: float):
    return T0 + timedelta(minutes=minutes)


def _vault(tmp_path, recipe: dict):
    paths = build_vault(tmp_path / "vault", recipe)
    write_yaml(
        paths.practice_item_path("linear-algebra", RECALL_ITEM),
        _item(RECALL_ITEM, facet=COMP_A, capability="recall", correlation_group="cg_recall"),
    )
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    return vault, repository


def _solve(vault, repository, item_id: str, minutes: float, *, points: int = 4) -> str:
    result = complete_self_graded_attempt(
        vault, repository,
        AttemptDraft(practice_item_id=item_id, learner_answer_md="An answer.",
                     attempt_type="independent_attempt", hints_used=0),
        SelfGradeInput(criterion_points={"c1": points}, fatal_errors=[], confidence=4),
        clock=FrozenClock(NOW + timedelta(minutes=minutes)),
    )
    return str(result.attempt_id)


def _gains(vault, repository, *, after_minutes: float) -> list[tuple[str, str, str]]:
    rows = RC.demonstrated_since(vault, repository, [LO_ID], after=(NOW + timedelta(minutes=after_minutes))
                                 .isoformat().replace("+00:00", "Z"))
    return [(row["learning_object_id"], row["demonstrated_on"], row["attempt_id"]) for row in rows]


def _stamp(minutes: float) -> str:
    return (NOW + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z")


# -- F1: the real certification transition ---------------------------------------------------------


def test_f1_a_gain_at_the_recipes_capability_counts_although_the_facet_had_credit(tmp_path):
    """Recall credit 1 on the facet before the session ended; the recipe's
    capability (procedure_execution) afterwards: newly demonstrated."""

    vault, repository = _vault(tmp_path, {"id": "recipe_main", "composition": "conjunctive",
                                          "all_of": [_component(COMP_A)], "any_of": []})
    _solve(vault, repository, RECALL_ITEM, 10)
    lo = vault.learning_objects[LO_ID]
    assert lo_certification(vault, repository, lo).demonstrated is False
    certifying = _solve(vault, repository, "pi_comp_a", 120)
    assert lo_certification(vault, repository, lo).demonstrated is True
    assert _gains(vault, repository, after_minutes=60) == [(LO_ID, _stamp(120), certifying)]


def test_f1_an_unused_alternative_crossing_later_is_not_a_new_gain(tmp_path):
    vault, repository = _vault(tmp_path, {"id": "recipe_main", "composition": "conjunctive",
                                          "all_of": [_component(COMP_A)],
                                          "any_of": [_component(ALT_X), _component(ALT_Y)]})
    _solve(vault, repository, "pi_comp_a", 10)
    _solve(vault, repository, "pi_alt_x", 20)
    assert lo_certification(vault, repository, vault.learning_objects[LO_ID]).demonstrated is True
    # After the session: the other alternative crosses. The LO was already demonstrated.
    _solve(vault, repository, "pi_alt_y", 120)
    assert _gains(vault, repository, after_minutes=60) == []


def test_f1_dated_by_the_attempt_that_completed_the_recipe(tmp_path):
    vault, repository = _vault(tmp_path, {"id": "recipe_main", "composition": "conjunctive",
                                          "all_of": [_component(COMP_A)],
                                          "any_of": [_component(ALT_X), _component(ALT_Y)]})
    _solve(vault, repository, "pi_alt_x", 90)      # one part after the session...
    completing = _solve(vault, repository, "pi_comp_a", 150)  # ...the recipe completes here
    _solve(vault, repository, "pi_alt_y", 200)     # an extra alternative changes nothing
    assert _gains(vault, repository, after_minutes=60) == [(LO_ID, _stamp(150), completing)]
    # Demonstrated before the window opens: nothing new.
    assert _gains(vault, repository, after_minutes=170) == []


def test_f1_nothing_is_claimed_while_the_lo_is_not_demonstrated_now(tmp_path):
    vault, repository = _vault(tmp_path, {"id": "recipe_main", "composition": "conjunctive",
                                          "all_of": [_component(COMP_A)],
                                          "any_of": [_component(ALT_X), _component(ALT_Y)]})
    _solve(vault, repository, "pi_comp_a", 120)
    _solve(vault, repository, RECALL_ITEM, 130)
    assert _gains(vault, repository, after_minutes=60) == []


# -- F3: a revoked success does not answer a claim -------------------------------------------------


def _attempt(repo, attempt_id: str, *, minutes: float, hints: int) -> None:
    repo.insert_practice_attempt({
        "id": attempt_id, "practice_item_id": "pi_svd_define_001", "learning_object_id": "lo_svd_definition",
        "subject": "linear-algebra", "concept": "singular_value_decomposition", "practice_mode": "short_answer",
        "attempt_type": "hinted_attempt" if hints else "independent_attempt",
        "learner_answer_md": "U Sigma V^T", "evidence_facets": ["recall"], "evidence_weights": {"recall": 1.0},
        "rubric_score": 4, "correctness": 1.0, "confidence": 3, "latency_seconds": 30, "hints_used": hints,
        "error_type": None, "grader_confidence": 1.0, "created_at": iso(minutes), "updated_at": iso(minutes),
        "entry_surface": "desktop_reader_workbench",
    })


def test_f3_a_success_regraded_to_nothing_leaves_the_claim_open(tmp_path, monkeypatch):
    """Assisted work, then an unassisted success regraded to zero: the
    production fold keeps the original positive point and its correction."""

    from learnloop.learner.facet_evidence_timeline import ObservationEvent, fold_demonstrated_timeline

    vault, repo = _setup(tmp_path)
    visit(repo, "v1", 0, 40)
    row = problem(repo, 2, steps=1, book=True)
    _attempt(repo, "att_book", minutes=20, hints=1)
    WB.mark_submitted(repo, row["id"], attempt_id="att_book", practice_session_id="ps_1", clock=at(20))
    session = RS.sessions_for_source(repo, EXT)[0]
    facet = vault.canonical_facet_id("recall")

    def event(minutes, credit, *, kind="observation", attempt="att_own"):
        return ObservationEvent(attempt_id=attempt, event_at=iso(minutes), kind=kind, surface_group="g",
                                assisted=False, per_capability_positive={"recall": credit} if credit else {},
                                authoritative=True)

    revoked = [event(200, 1.0), event(260, 0.0, kind="correction")]
    standing = [event(200, 1.0)]
    regraded_up = [event(200, 0.0), event(260, 1.0, kind="correction")]
    before_session = [event(-10, 1.0, attempt="att_old"), event(250, 1.0, kind="correction", attempt="att_old")]
    for events, answered in ((revoked, False), (standing, True), (regraded_up, True), (before_session, False)):
        points = fold_demonstrated_timeline(events)
        monkeypatch.setattr(RC, "facet_evidence_timelines",
                            lambda _v, _r, facets, points=points: {facet: list(points)} if facet in facets else {})
        summary = RC.session_summary(vault, repo, extraction_id=EXT, session=session, now=_now(300))
        assert (summary["claims_needing_independent_check"] == []) is answered, events


def test_f3_the_timeline_carries_each_attempts_effective_credit_and_capability_credit():
    from learnloop.learner.facet_evidence_timeline import ObservationEvent, fold_demonstrated_timeline

    series = fold_demonstrated_timeline([
        ObservationEvent(attempt_id="a1", event_at=iso(1), kind="observation", surface_group="g1",
                         assisted=False, per_capability_positive={"recall": 1.0}, authoritative=True),
        ObservationEvent(attempt_id="a2", event_at=iso(2), kind="observation", surface_group="g2",
                         assisted=False, per_capability_positive={"procedure_execution": 1.0}, authoritative=True),
        ObservationEvent(attempt_id="a1", event_at=iso(3), kind="correction", surface_group="g1",
                         assisted=False, per_capability_positive={}, authoritative=True),
    ])
    assert [p.attempt_credit for p in series] == [1.0, 1.0, 0.0]
    assert [dict(p.capability_credit) for p in series] == [
        {"recall": 1.0},
        {"recall": 1.0, "procedure_execution": 1.0},
        {"recall": 0.0, "procedure_execution": 1.0},
    ]
    # The plotted curve is unchanged (as_dict keeps its keys).
    assert [p.demonstrated for p in series] == [1.0, 2.0, 1.0]
    assert "attempt_credit" not in series[0].as_dict() and "capability_credit" not in series[0].as_dict()


# -- F4: a resolution at the destination keeps its inquiry in Wrap up ------------------------------


def test_f4_resolving_at_the_destination_moves_the_inquiry_to_resolved_with_undo(tmp_path):
    vault, repo = _setup(tmp_path)
    visit(repo, "v1", 0, 20)
    root = ask(vault, repo, "Why weighted by p?", 5)["reader_answer_event_id"]
    before = RC.build_wrap_up(vault, repo, extraction_id=EXT, current_visit_id=None, now=_now(21))
    assert [line["root_exchange_id"] for line in before["still_open"]] == [root]

    # Resolved from Today's Wrap up, two minutes after leaving.
    resolve(repo, root, 22)
    after = RC.build_wrap_up(vault, repo, extraction_id=EXT, current_visit_id=None, now=_now(23))
    assert after["still_open"] == []
    [line] = after["resolved"]
    assert line["root_exchange_id"] == root
    assert [action["action"] for action in line["actions"]] == ["undo"]

    # Undone: back in Still open.
    resolve(repo, root, 24, resolution="open")
    undone = RC.build_wrap_up(vault, repo, extraction_id=EXT, current_visit_id=None, now=_now(25))
    assert [line["root_exchange_id"] for line in undone["still_open"]] == [root]
    assert undone["resolved"] == []


def test_f4_an_old_inquiry_resolved_and_undone_in_the_reader_stays_listed(tmp_path):
    vault, repo = _setup(tmp_path)
    visit(repo, "v1", 0, 20)
    root = ask(vault, repo, "Why weighted by p?", 5)["reader_answer_event_id"]
    visit(repo, "v2", 600, None)
    resolve(repo, root, 605)            # the card's chip, the next session
    wrapped = RC.build_wrap_up(vault, repo, extraction_id=EXT, current_visit_id="v2", now=_now(606))
    assert [line["root_exchange_id"] for line in wrapped["resolved"]] == [root]
    resolve(repo, root, 607, resolution="open")  # undo from Wrap up
    undone = RC.build_wrap_up(vault, repo, extraction_id=EXT, current_visit_id="v2", now=_now(608))
    assert [line["root_exchange_id"] for line in undone["still_open"]] == [root]


# -- F8: abandoned problems stay in the recap ------------------------------------------------------


def test_f8_an_abandoned_problem_is_in_the_recap_with_a_reopen(tmp_path):
    vault, repo = _setup(tmp_path)
    visit(repo, "v1", 0, 40)
    row = problem(repo, 2, steps=3, book=True)
    WB.abandon(repo, row["id"], clock=at(30))
    card = RC.build_recap(vault, repo, extraction_id=EXT, current_visit_id="v_now", now=_now(600))["recap"]
    [line] = card["unfinished"]
    assert line["session_id"] == row["id"]
    assert line["status"] == "abandoned"
    assert line["step_count"] == 3
    assert line["help_line"] == "help so far: the book"


# -- F10: the inquiry switch gates the recap -------------------------------------------------------


def test_f10_inquiry_off_refuses_every_recap_rpc_and_names_no_switch(tmp_path):
    from learnloop_sidecar.context import config_dto
    from learnloop_sidecar.errors import SidecarError

    vault, repo = _setup(tmp_path)
    visit(repo, "v1", 0, 20)
    ask(vault, repo, "Why weighted by p?", 5)
    append_config_toml(vault.root, """
    [reader_inquiry]
    enabled = false
    """)
    ctx = context(vault.root)
    before_counts, before_rows = table_counts(repo), interaction_rows(repo)
    for name, params in (
        ("reader.recap", {"extractionId": EXT, "visitId": "v_now"}),
        ("reader.recap_event", {"extractionId": EXT, "visitId": "v_now", "event": "recap_shown"}),
        ("reader.recap_event", {"extractionId": EXT, "event": "wrap_up_opened"}),
        ("reader.wrap_up", {"extractionId": EXT}),
        ("reader.wrap_up_offer", {}),
    ):
        with pytest.raises(SidecarError) as refused:
            call(ctx, name, params)
        assert refused.value.code == "inquiry_disabled", name
    assert table_counts(repo) == before_counts and interaction_rows(repo) == before_rows
    assert "recap" not in config_dto(load_vault(vault.root))
