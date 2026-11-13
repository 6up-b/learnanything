"""What other test files use from ``tests/test_followup_journey.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import pytest

from learnloop.algorithm_versions import FOLLOWUP_SERVE_ALGORITHM_VERSION
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.attempts.post_attempt import run_post_attempt_pipeline
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.km2_write_path_helpers import KM2_OLD_TAG
from tests.followup_serve_helpers import (
    CLOCK,
    AuthorFake,
    author_clients,
    miss_with_rivals,
    rival_causes_vault,
    run_jobs,
)


class _Runtime:
    ready = True
    status = "ready"
    message = None


def _call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


@pytest.fixture
def journey(tmp_path, monkeypatch):
    return _journey(tmp_path, monkeypatch)


@pytest.fixture
def journey_old_tag(tmp_path, monkeypatch):
    """The journey at the tag the follow-up served at first, for a test that reads what that tag wrote (it waits
    on the learner/ gate's tests)."""

    return _journey(tmp_path, monkeypatch, version=FOLLOWUP_SERVE_ALGORITHM_VERSION, built_at=KM2_OLD_TAG)


def _journey(tmp_path, monkeypatch, **vault_kwargs):
    monkeypatch.setattr(
        "learnloop_sidecar.handlers.practice.ready_grading_provider",
        lambda *_args, **_kw: ("fake", _Runtime(), object()),
    )
    vault, repository, paths = rival_causes_vault(tmp_path, **vault_kwargs)
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.post_attempt_worker.autostart = False
    vault, repository = ctx.require_vault()
    result, outcome = miss_with_rivals(vault, repository)
    return ctx, vault, repository, result, outcome


def _generate(ctx, repository, *, fake=None):
    vault, _ = ctx.require_vault()
    run_jobs(vault, repository, clients=author_clients(fake or AuthorFake()))


def _answer(ctx, repository, row, *, points):
    vault, _ = ctx.require_vault()
    probe = complete_self_graded_attempt(
        vault, repository,
        AttemptDraft(practice_item_id=row["practice_item_id"], learner_answer_md="An answer.",
                     attempt_type="diagnostic_probe", probe_presentation_id=row["presentation_id"]),
        SelfGradeInput(criterion_points=points, confidence=3),
        clock=CLOCK,
    )
    run_post_attempt_pipeline(vault, repository, result=probe, followup_surface="desktop", clock=CLOCK)
    return probe


def _forced(monkeypatch, chosen):
    from learnloop.followup_run import router

    monkeypatch.setattr(router, "decide", lambda *_a, **_k: router.FollowupDecision(chosen, chosen, "mixture"))


def _bundle_without_ids(bundle):
    # hypothesisMarks is FG1c's, and its order hangs off episode keys that differ between two vaults;
    # tests/test_hypothesis_marks.py holds its own on-and-off comparison.
    drop = {"attemptId", "generatedAt", "feedbackLastShownAt", "feedbackFirstShownAt", "nextDueAt", "hypothesisMarks"}
    return {key: value for key, value in bundle.items() if key not in drop}
