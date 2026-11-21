"""Reader RW6b part 1 as the successor mvp-0.39 (Codex review F4;
spec_reader_workbench_v1 §9.3 "Why no successor", whose fallback applies;
docs/reviews/reader-rw6b-p1-followups-codex-review.md).

* the tag is ONE constant after mvp-0.38 (its kill switch went once every
  vault was past it);
* planning and re-valuation run;
* the upgrade is the chain's next journalled link (from mvp-0.38, or mvp-0.9
  onwards through the chain), and the next command completes an
  interrupted activation.

Fakes only; no model call.
"""

from __future__ import annotations



from learnloop.algorithm_versions import (
    COLD_RETRY_RESCHEDULE_ALGORITHM_VERSION,
    LATEST_ALGORITHM_VERSION,
    READER_FOLLOWUPS_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.instructional import reader_followups as RF
from learnloop.vault.loader import load_vault
from tests.recap_fixtures import EXT, at
from tests.reader_followups_helpers import FakeSearch, _candidate, _now, _plan, _seeded

TAG = READER_FOLLOWUPS_ALGORITHM_VERSION
PREDECESSOR = COLD_RETRY_RESCHEDULE_ALGORITHM_VERSION


def test_mvp039_is_one_constant_after_mvp038_and_the_latest():
    # Curriculum C1's mvp-0.40 follows it as the latest (and keeps it).
    assert SUCCESSOR_CHAIN[-25:-23] == (PREDECESSOR, TAG) == ("mvp-0.38", "mvp-0.39")
    assert SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION == "mvp-0.62"


def test_planning_and_revaluation_run(tmp_path):
    vault, repo, session = _seeded(tmp_path, version=TAG)
    search = FakeSearch([_candidate("pi_svd_define_002", 0.99, 0.01, 1.0)])
    planned = RF.plan_ended_sessions(vault, repo, search=search, now=_now(), clock=at(300))
    revalued = RF.revalue_pending(vault, repo, now=_now(400), valuer=lambda *_a: {"problems": []}, clock=at(400))
    with repo.connection() as connection:
        commitments = connection.execute("SELECT COUNT(*) FROM commitments").fetchone()[0]
        digests = connection.execute("SELECT COUNT(*) FROM reader_session_digests").fetchone()[0]
    assert len(planned) == 1 and commitments == 1 and digests == 1 and revalued["skipped"] is None


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
