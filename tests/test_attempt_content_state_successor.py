"""Mobile PR-4's successor (mvp-0.37; mvp-0.36 on its branch, renumbered at landing after the kept
replaced claims' mvp-0.36): a live attempt writes only its scheduling columns.

Codex review F4 (``docs/reviews/mobile-pr3-pr4-codex-review.md``): the PR-4
race fix (``tests/test_attempt_content_state_race.py``) also changes serving
WITHOUT a concurrent writer. An item whose ``practice_item_state`` row is
closed while its YAML is active (review-parked, measurement-superseded, a
deactivation replay keeps) used to be reopened by an attempt on it, until the
next content sync re-decided the flag; with the fix it stays closed, so the
Today queue no longer serves it in that window. That is a change to which
items are served (the playbook's 2026-10-17 rule), so it is a successor with a
kill switch:

* at the tag with ``practice.attempt_keeps_content_state`` on, the attempt
  keeps the closed row closed and its content hash as content sync wrote it;
* off, the attempt writes the whole row exactly as the predecessor (the row
  reopens and the item is served); no vault that opens is below the tag;
* replay keeps its full upsert, so a same-version rebuild reproduces the live
  row at every setting (rebuild equivalence);
* the upgrade is the chain's next journalled link.

Fakes only: self-graded attempts, no model call.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from learnloop.algorithm_versions import (
    ATTEMPT_CONTENT_STATE_ALGORITHM_VERSION,
    ATTEMPT_CONTENT_STATE_VERSIONS,
    LATEST_ALGORITHM_VERSION,
    ONE_ASK_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
    SUPERSEDED_CLAIMS_ALGORITHM_VERSION,
)
from learnloop.attempts.attempts import (
    AttemptDraft,
    SelfGradeInput,
    attempt_keeps_content_state,
    complete_self_graded_attempt,
)
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.substrate.replay import rebuild_derived_state
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, append_config_toml, create_placement_vault

TAG = ATTEMPT_CONTENT_STATE_ALGORITHM_VERSION
PREDECESSOR = SUPERSEDED_CLAIMS_ALGORITHM_VERSION
ITEM = "pi_svd_define_001"
CLOCK = FrozenClock(NOW + timedelta(hours=1))


def _vault_at(tmp_path, name, version, *, switch: bool | None = None):
    paths = create_placement_vault(tmp_path / name, version=version)
    if switch is not None:
        append_config_toml(paths.root, f"\n[practice]\nattempt_keeps_content_state = {str(switch).lower()}\n")
    return paths


def _answer(vault, repository) -> None:
    complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=ITEM,
            learner_answer_md="SVD factors a matrix into U, Sigma and V transpose.",
            attempt_type="independent_attempt",
        ),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=4),
        clock=CLOCK,
    )


def _served(vault, repository) -> bool:
    from learnloop.scheduling.serving_exclusions import routine_serving_exclusions, routine_withhold_reason

    state = repository.practice_item_states().get(ITEM)
    reason = routine_withhold_reason(
        vault, vault.practice_items[ITEM], state, routine_serving_exclusions(vault, repository)
    )
    return reason != "inactive_state"


def _closed_then_answered(paths):
    """The non-concurrent case F4 names: the row is closed while the YAML is
    active (a deactivation the sync rule keeps), then an answer on the item is
    submitted with no other writer in between."""

    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    repository.set_practice_item_active(ITEM, active=False, clock=FrozenClock(NOW))
    before = repository.practice_item_state(ITEM)
    assert before.active is False and vault.practice_items[ITEM].status == "active"
    _answer(vault, repository)
    return vault, repository, before


# -- the chain -------------------------------------------------------------------------------------


def test_mvp037_is_one_constant_after_mvp036():
    from learnloop.config.schema import PracticeConfig
    from learnloop.params.parameter_registry import classify_config_path

    # Built as mvp-0.36 after mvp-0.35; the kept replaced claims' mvp-0.36 landed first, so the landing renumbered it.
    # The cold-retry reschedule's mvp-0.38, Reader RW6b's mvp-0.39 and curriculum C1's mvp-0.40 (the latest) follow it (and keep it).
    assert SUCCESSOR_CHAIN[-25:-22] == (ONE_ASK_ALGORITHM_VERSION, PREDECESSOR, TAG) == ("mvp-0.35", "mvp-0.36", "mvp-0.37")
    assert SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION == "mvp-0.59"
    assert ATTEMPT_CONTENT_STATE_VERSIONS == frozenset({TAG, "mvp-0.38", "mvp-0.39", "mvp-0.40", "mvp-0.41", "mvp-0.42", "mvp-0.43", "mvp-0.44", "mvp-0.45", "mvp-0.46", "mvp-0.47", "mvp-0.48", "mvp-0.49", "mvp-0.50", "mvp-0.51", "mvp-0.52", "mvp-0.53", "mvp-0.54", "mvp-0.55", "mvp-0.56", "mvp-0.57", "mvp-0.58", "mvp-0.59"})
    assert PracticeConfig().attempt_keeps_content_state is True
    rule = classify_config_path("practice.attempt_keeps_content_state")
    assert rule is not None and rule.kind == "structural" and "kill switch" in rule.rationale


@pytest.mark.parametrize(("version", "switch", "keeps"), [
    (TAG, None, True), (TAG, False, False),
], ids=["tag", "tag-switch-off"])
def test_the_gate_is_its_switch(tmp_path, version, switch, keeps):
    paths = _vault_at(tmp_path, "v", version, switch=switch)
    assert attempt_keeps_content_state(load_vault(paths.root)) is keeps


# -- serving without a concurrent writer -------------------------------------------------------------


def test_at_the_tag_an_answer_keeps_a_closed_row_closed_and_out_of_serving(tmp_path):
    paths = _vault_at(tmp_path, "tag", TAG)
    vault, repository, before = _closed_then_answered(paths)

    state = repository.practice_item_state(ITEM)
    assert state.active is False
    assert state.content_hash == before.content_hash
    assert state.last_attempt_at is not None and state.stability is not None and state.due_at is not None
    assert not _served(vault, repository)


@pytest.mark.parametrize(("version", "switch"), [(TAG, False)], ids=["tag-switch-off"])
def test_off_the_answer_reopens_the_row_as_the_predecessor(tmp_path, version, switch):
    paths = _vault_at(tmp_path, "pred", version, switch=switch)
    vault, repository, _before = _closed_then_answered(paths)

    state = repository.practice_item_state(ITEM)
    assert state.active is True  # the predecessor's whole-row upsert
    assert state.last_attempt_at is not None and state.stability is not None
    assert _served(vault, repository)


@pytest.mark.parametrize(("version", "switch"), [(TAG, None), (TAG, False)], ids=["tag", "tag-switch-off"])
def test_a_same_version_rebuild_reproduces_the_live_row(tmp_path, version, switch):
    paths = _vault_at(tmp_path, "rebuild", version, switch=switch)
    vault, repository, _before = _closed_then_answered(paths)
    live = repository.practice_item_state(ITEM)

    rebuild_derived_state(vault, repository, clock=CLOCK)

    rebuilt = repository.practice_item_state(ITEM)
    columns = ("active", "content_hash", "difficulty", "stability", "retrievability", "due_at", "last_attempt_at")
    assert {name: getattr(rebuilt, name) for name in columns} == {name: getattr(live, name) for name in columns}


# -- the upgrade -------------------------------------------------------------------------------------
