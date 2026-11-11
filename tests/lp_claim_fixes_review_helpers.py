"""What other test files use from ``tests/test_lp_claim_fixes_review.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import timedelta
import multiprocessing
import os
import sqlite3

from learnloop.algorithm_versions import CLAIM_FIXES_ALGORITHM_VERSION, SUCCESSOR_CHAIN
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.tutor.ai_contracts import PromotionAnalysis
from learnloop.tutor.promotions import promote_tutor_question
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, append_config_toml, create_placement_vault
from tests.assumed_known_helpers import _answer
from tests.tutor_promotion_service_helpers import _AnalysisClient, _insert_event


TAG = CLAIM_FIXES_ALGORITHM_VERSION
PREDECESSOR = SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(TAG) - 1]
LO = "lo_svd_definition"
ITEM = "pi_svd_define_001"


def _iso(minutes: float) -> str:
    return (NOW + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z")


def _vault(tmp_path, name="vault", *, version=TAG, toml=None):
    paths = create_placement_vault(tmp_path / name, version=version)
    if toml:
        append_config_toml(paths.root, toml)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    return paths, vault, repository


def _gap(root, repository, event_id="ev_gap", *, minutes=30.0, item=ITEM):
    if repository.question_event(event_id) is None:
        _insert_event(repository, event_id, practice_item_id=item)
    client = _AnalysisClient(PromotionAnalysis(attributed_facets=["recall"], question_nature="mechanism"))
    return promote_tutor_question(
        root, client, event_id=event_id, intent="gap", clock=FrozenClock(NOW + timedelta(minutes=minutes))
    )


def _mastery(repository, lo=LO) -> tuple[float, float, int]:
    state = repository.mastery_state(lo)
    assert state is not None
    return (state.logit_mean, state.logit_variance, state.evidence_count)


def _all_mastery(path) -> dict[str, tuple[float, float, int]]:
    with sqlite3.connect(path) as connection:
        rows = connection.execute(
            "SELECT learning_object_id, logit_mean, logit_variance, evidence_count FROM learning_object_mastery"
        ).fetchall()
    return {row[0]: (row[1], row[2], row[3]) for row in rows}


def _gap_claims(repository) -> list[dict]:
    return [claim for claim in repository.learner_claims() if claim["source"] == "tutor_gap_declaration"]


def _rebuild(paths):
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    rebuild_all_derived_state(vault, repository, clock=FrozenClock(NOW + timedelta(hours=1)))
    return repository


def _predecessor_vault_with_claims(tmp_path, name):
    paths, vault, repository = _vault(tmp_path, name, version=PREDECESSOR)
    _answer(vault, repository, ITEM, 4.0, minutes=5)
    repository.insert_learner_claim({
        "claim_type": "self_rating", "scope_type": "learning_object", "scope_id": LO, "evidence_family": "recall",
        "claimed_level": 0.05, "prior_pseudo_count": 4.0, "source": "manual_cli", "created_at": _iso(1),
    })
    _gap(paths.root, repository, "ev_cold", item="pi_diag_easy")  # inert on the predecessor
    return paths


def _journal(paths):
    return paths.sqlite_path.with_name(paths.sqlite_path.name + ".claim-fixes-activation")


def _die_after_publication(root):
    import learnloop.claim_fixes_upgrade as upgrade

    real = upgrade._publish_algorithm_version

    def publish_then_die(*args, **kwargs):
        real(*args, **kwargs)
        os._exit(17)  # no handler runs: the transaction never commits

    upgrade._publish_algorithm_version = publish_then_die
    upgrade.upgrade_to_claim_fixes(root)


def _crash_upgrade(paths):
    process = multiprocessing.get_context("fork").Process(target=_die_after_publication, args=(paths.root,))
    process.start()
    process.join(60)
    assert process.exitcode == 17
