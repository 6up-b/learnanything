"""UX Phase 4 (practice and feedback) composed with provenance and saved forecasts on main.

The stage's "I think I was right" (``trigger_regrade`` with a reason) regrades
in place through the ordinary learner-blind regrade, which on main also writes
diagnosis input provenance's records (migration 205) and which saved diagnosis
forecasts (migration 206) read at resolution time. These tests pin how they
compose, through the sidecar RPC itself:

* a contest's regrade records its grading provenance and the error-event
  lineage like any regrade, and the reason never reaches the grader;
* the regrade re-resolves a saved forecast the contested attempt resolves;
* a contest the regrade does not uphold is queued for review with a
  ``review_flag`` head of the same authority: not a hold, so the forecast
  still resolves on the grade as it stands;
* a held grade shows "held for review" in the feedback bundle and resolves no
  forecast, by the one held predicate; a contest whose regrade releases it
  clears both;
* what feedback says a grade stands on (round 3 F9: ``answered_source``,
  contract | live | unrecorded) agrees with what the forecast resolver reads:
  a regrade that cites its contract shows that contract and resolves the
  forecast; one that cites none shows the content it read in its own
  response only (``live``), ``unrecorded`` on any later read, and censors the
  forecast (``graded_contract_unknown``).

Fakes only; no network, no paid call.
"""

from __future__ import annotations

from learnloop.algorithm_versions import METHOD_EXPLICIT_ALGORITHM_VERSION as METHOD_VERSION
from learnloop.held_grades import held_attempt_ids
from tests.diagnosis_fakes import ReviewFakeClient
from tests.split_live_helpers import ReadyRuntime, at
from tests.test_forecast_receipts import ITEM, WRONG, _answer, _diagnosed, _diagnosis_resolution, _present
from tests.test_route_rules_in_grader import ALTERNATIVE, DivergentUnlocatedGrader, FullCreditGrader
from tests.test_route_rules_in_grader import VERSION as ROUTE_RULES_VERSION

REASON = "I did transpose V; the last line says so"


def _context(paths, monkeypatch, client):
    """The sidecar on the vault, its grading provider the fake ``client``."""

    import learnloop_sidecar.handlers  # noqa: F401 - populates the registry
    import learnloop_sidecar.handlers.ai_providers as providers
    from learnloop_sidecar.context import SidecarContext

    monkeypatch.setattr(providers, "ready_grading_provider",
                        lambda vault, override=None: ("fake", ReadyRuntime(), client))
    monkeypatch.setattr(providers, "grading_source_for_provider", lambda name: "ai")
    context = SidecarContext()
    context.load(paths.root)
    return context


def _contest(context, attempt_id: str, contest_id: str) -> dict:
    from learnloop_sidecar.registry import METHOD_REGISTRY

    spec = METHOD_REGISTRY["trigger_regrade"]
    return spec.handler(context, spec.params_model.model_validate(
        {"attemptId": attempt_id, "learnerReason": REASON, "contestId": contest_id}
    ))


def _regrade_provenance(repository, attempt_id: str) -> list[dict]:
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT writer, complete FROM text_write_provenance WHERE kind = 'grading' AND record_id = ? "
            "ORDER BY created_at, id",
            (attempt_id,),
        ).fetchall()
    return [dict(row) for row in rows if row["writer"] == "regrade"]


def _lineage(repository, attempt_id: str) -> list[tuple]:
    with repository.connection() as connection:
        return [tuple(row) for row in connection.execute(
            "SELECT error_event_id, replaces_error_event_id FROM error_event_lineage WHERE attempt_id = ?",
            (attempt_id,),
        ).fetchall()]


def _events(repository, attempt_id: str) -> list[str]:
    return sorted(str(event["id"]) for event in repository.raw_error_events_for_attempt(attempt_id))


def _pending_reviews(repository) -> list[str]:
    return [row["attempt_id"] for row in repository.pending_grade_reviews()]


def test_a_contest_regrade_records_provenance_and_re_resolves_the_forecast(tmp_path, monkeypatch):
    # A method-explicit item, so the regrade cites the contract it read and
    # the forecast resolves on it (test_forecast_receipts' F2 tests).
    paths, vault, repository, diagnosed = _diagnosed(tmp_path, version=METHOD_VERSION, method=True)
    presentation = _present(repository, ITEM, block="blk_contest", when=at(29))
    contested = _answer(vault, repository, ReviewFakeClient(), answer=WRONG + " again", when=at(30),
                        presentation_id=presentation)
    old_events = _events(repository, contested.attempt_id)
    assert old_events
    assert _diagnosis_resolution(vault, diagnosed.attempt_id)["emission"] == "same_error"
    assert _regrade_provenance(repository, contested.attempt_id) == []

    grader = FullCreditGrader()
    context = _context(paths, monkeypatch, grader)
    bundle = _contest(context, contested.attempt_id, "contest_upheld")

    assert bundle["contest"] == {"recorded": True, "regraded": True, "reviewRequested": False}
    assert grader.prompts and not any(REASON in prompt for prompt in grader.prompts)
    # Provenance's records: the regrade's grading record (Q14) and, for the
    # events full credit retired, lineage rows with no replacement (Q9).
    assert len(_regrade_provenance(repository, contested.attempt_id)) == 1
    assert _events(repository, contested.attempt_id) == []
    assert sorted(old for new, old in _lineage(repository, contested.attempt_id) if new is None) == old_events
    # The saved forecast reads the regraded attempt as it stands now, on the
    # contract the regrade cites; feedback shows that same contract.
    resolution = _diagnosis_resolution(vault, diagnosed.attempt_id)
    assert (resolution["state"], resolution.get("emission")) == ("resolved", "pass")
    assert bundle["answeredSource"] == "contract"
    assert _pending_reviews(repository) == []


def test_a_contest_the_regrade_does_not_uphold_is_flagged_never_held(tmp_path, monkeypatch):
    paths, vault, repository, diagnosed = _diagnosed(tmp_path, version=METHOD_VERSION, method=True)
    presentation = _present(repository, ITEM, block="blk_flag", when=at(29))
    contested = _answer(vault, repository, ReviewFakeClient(), answer=WRONG + " again", when=at(30),
                        presentation_id=presentation)
    old_events = _events(repository, contested.attempt_id)

    grader = ReviewFakeClient()
    context = _context(paths, monkeypatch, grader)
    bundle = _contest(context, contested.attempt_id, "contest_flagged")

    assert bundle["contest"] == {"recorded": True, "regraded": True, "reviewRequested": True}
    assert not any(REASON in prompt for prompt in grader.prompts)
    assert _pending_reviews(repository) == [contested.attempt_id]
    # The regrade still wrote provenance's records: its grading record, and
    # lineage naming the re-minted events for the replaced ones.
    assert len(_regrade_provenance(repository, contested.attempt_id)) == 1
    reminted = _events(repository, contested.attempt_id)
    assert reminted and not set(reminted) & set(old_events)
    assert {old for _new, old in _lineage(repository, contested.attempt_id)} == set(old_events)
    # A review flag keeps the grade's authority: it is not a hold.
    assert bundle["heldForReview"] is False
    assert held_attempt_ids(repository, [contested.attempt_id]) == frozenset()
    resolution = _diagnosis_resolution(vault, diagnosed.attempt_id)
    assert (resolution["state"], resolution.get("emission")) == ("resolved", "same_error")


def test_a_held_grade_resolves_nothing_until_a_contest_regrade_releases_it(tmp_path, monkeypatch):
    paths, vault, repository, diagnosed = _diagnosed(tmp_path, version=ROUTE_RULES_VERSION)
    presentation = _present(repository, ITEM, block="blk_held_contest", when=at(29))
    held = _answer(vault, repository, DivergentUnlocatedGrader(), answer=ALTERNATIVE, when=at(30),
                   presentation_id=presentation)

    from learnloop_sidecar.handlers.serializers import feedback_bundle

    # One predicate: the feedback says "held for review" and the forecast is held.
    assert feedback_bundle(vault, repository, held.attempt_id)["heldForReview"] is True
    resolution = _diagnosis_resolution(vault, diagnosed.attempt_id)
    assert (resolution["state"], resolution["reason"]) == ("held", "grade_held_for_review")

    context = _context(paths, monkeypatch, FullCreditGrader())
    bundle = _contest(context, held.attempt_id, "contest_release")

    # The regrade validated the route: released, upheld, nothing to review.
    assert bundle["heldForReview"] is False
    assert bundle["contest"] == {"recorded": True, "regraded": True, "reviewRequested": False}
    assert len(_regrade_provenance(repository, held.attempt_id)) == 1
    # No longer held. This item has no frozen method, so the regrade cites no
    # contract and the forecast is censored, exactly as a plain regrade's
    # (test_forecast_receipts::test_a_held_grade_resolves_nothing_until_a_regrade_releases_it).
    resolution = _diagnosis_resolution(vault, diagnosed.attempt_id)
    assert (resolution["state"], resolution["reason"]) == ("censored", "graded_contract_unknown")
    # Feedback agrees (round 3 F9): the content the regrade read, in its own
    # response only, and unrecorded on any later read; never inferred.
    assert bundle["answeredSource"] == "live"
    assert feedback_bundle(vault, repository, held.attempt_id)["answeredSource"] == "unrecorded"

