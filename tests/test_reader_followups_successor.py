"""Reader RW6b part 1 as the successor mvp-0.39 (Codex review F4;
spec_reader_workbench_v1 §9.3 "Why no successor", whose fallback applies;
docs/reviews/reader-rw6b-p1-followups-codex-review.md).

* the tag is ONE constant after mvp-0.38 and the latest;
  ``followups.enabled`` is its kill switch;
* below the tag, or switched off, nothing is planned or re-valued: the Today
  queue is the predecessor's (plan parity), and no digest or commitment is
  written;
* the upgrade is the chain's next journalled link (from mvp-0.38, or mvp-0.9
  onwards through the chain), and the next command completes an
  interrupted activation.

Fakes only; no model call.
"""

from __future__ import annotations


import pytest

from learnloop.algorithm_versions import (
    COLD_RETRY_RESCHEDULE_ALGORITHM_VERSION,
    LATEST_ALGORITHM_VERSION,
    READER_FOLLOWUPS_ALGORITHM_VERSION,
    READER_FOLLOWUPS_VERSIONS,
    SUCCESSOR_CHAIN,
)
from learnloop.instructional import reader_followups as RF
from learnloop.vault.loader import load_vault
from tests.recap_fixtures import EXT, at
from tests.reader_followups_helpers import FakeSearch, _candidate, _now, _plan, _seeded

TAG = READER_FOLLOWUPS_ALGORITHM_VERSION
PREDECESSOR = COLD_RETRY_RESCHEDULE_ALGORITHM_VERSION


def test_mvp039_is_one_constant_after_mvp038_and_the_latest():
    from learnloop.config.schema import FollowupsConfig
    from learnloop.params.parameter_registry import classify_config_path

    # Curriculum C1's mvp-0.40 follows it as the latest (and keeps it).
    assert SUCCESSOR_CHAIN[-22:-20] == (PREDECESSOR, TAG) == ("mvp-0.38", "mvp-0.39")
    assert SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION == "mvp-0.59"
    assert READER_FOLLOWUPS_VERSIONS == frozenset({TAG, "mvp-0.40", "mvp-0.41", "mvp-0.42", "mvp-0.43", "mvp-0.44", "mvp-0.45", "mvp-0.46", "mvp-0.47", "mvp-0.48", "mvp-0.49", "mvp-0.50", "mvp-0.51", "mvp-0.52", "mvp-0.53", "mvp-0.54", "mvp-0.55", "mvp-0.56", "mvp-0.57", "mvp-0.58", "mvp-0.59"})
    assert FollowupsConfig().enabled is True
    rule = classify_config_path("followups.enabled")
    assert rule is not None and rule.kind == "structural" and "mvp-0.39" in rule.rationale


@pytest.mark.parametrize(("version", "switch", "live"), [(TAG, None, True), (TAG, False, False)])
def test_planning_and_revaluation_are_gated_by_the_switch(tmp_path, version, switch, live):
    config = None if switch is None else f"[followups]\nenabled = {'true' if switch else 'false'}\n"
    vault, repo, session = _seeded(tmp_path, config=config, version=version)
    assert RF.followups_enabled(vault) is live
    search = FakeSearch([_candidate("pi_svd_define_002", 0.99, 0.01, 1.0)])
    planned = RF.plan_ended_sessions(vault, repo, search=search, now=_now(), clock=at(300))
    revalued = RF.revalue_pending(vault, repo, now=_now(400), valuer=lambda *_a: {"problems": []}, clock=at(400))
    with repo.connection() as connection:
        commitments = connection.execute("SELECT COUNT(*) FROM commitments").fetchone()[0]
        digests = connection.execute("SELECT COUNT(*) FROM reader_session_digests").fetchone()[0]
    if live:
        assert len(planned) == 1 and commitments == 1 and digests == 1 and revalued["skipped"] is None
    else:
        assert planned == [] and search.calls == [] and commitments == 0 and digests == 0
        assert revalued["skipped"] == "followups.enabled is false"


def _served(tmp_path, name, *, version, config=None):
    import learnloop_sidecar.handlers  # noqa: F401
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.registry import METHOD_REGISTRY

    vault, repo, _session = _seeded(tmp_path / name, config=config, version=version)
    ctx = SidecarContext()
    ctx.load(vault.root)
    try:
        spec = METHOD_REGISTRY["get_today_queue"]
        queue = spec.handler(ctx, spec.params_model.model_validate({}))
    finally:
        ctx.close()
    with repo.connection() as connection:
        written = (connection.execute("SELECT COUNT(*) FROM commitments").fetchone()[0],
                   connection.execute("SELECT COUNT(*) FROM reader_session_digests").fetchone()[0])
    return [item["practiceItemId"] for section in queue["sections"] for item in section["items"]], written


def test_switched_off_the_today_queue_is_the_predecessors(tmp_path):
    """Plan parity: an ended reader session waits at both versions; mvp-0.39
    with ``followups.enabled = false`` serves exactly what mvp-0.38 serves and
    writes no digest or commitment."""

    before, written_before = _served(tmp_path, "pred", version=PREDECESSOR, config="[followups]\nenabled = false\n")
    after, written_after = _served(tmp_path, "off", version=TAG, config="[followups]\nenabled = false\n")
    assert after == before and written_before == written_after == (0, 0)


# -- the chain and the upgrade -------------------------------------------------------------------------


def test_replay_plans_nothing_and_a_shadow_rebuild_is_zero(tmp_path):
    """The successor's state is workflow state (digests, commitments): a
    rebuild neither replays nor re-values it (the stage's 0/0/0, at the tag)."""

    from learnloop.substrate.replay import rebuild_derived_state
    from learnloop.substrate.shadow_rebuild import shadow_rebuild

    vault, repo, session = _seeded(tmp_path)
    rebuild_derived_state(vault, repo, clock=at(250))
    row = _plan(vault, repo, session, FakeSearch([_candidate("pi_svd_define_002", 0.99, 0.01, 1.0)]))
    assert row["followup_commitment_ids"]
    result = shadow_rebuild(load_vault(vault.root))
    assert result.learner_state_diff["summary"] == {"mastery": 0, "facet": 0, "schedule": 0}
    assert result.live_database_unchanged is True
    with repo.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM reader_session_digests WHERE extraction_id = ?",
                                  (EXT,)).fetchone()[0] == 1
