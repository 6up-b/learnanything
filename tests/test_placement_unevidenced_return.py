"""mvp-0.56, the placement hole (owner decision 2026-11-09; docs/reviews/placement-stranded.md).

Under placement an answered item with no due time, on an LO with no evidence, reached neither new material nor the
routine queue. The successor starts it as learning, under the holds of a selector outside the scheduler's timing. Below
the tag, or with ``placement.unevidenced_return`` off, serving is the predecessor's exactly. Synthetic vaults only;
fakes only, no model call.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import timedelta
import json

import pytest
from typer.testing import CliRunner

from learnloop.algorithm_versions import UNEVIDENCED_RETURN_ALGORITHM_VERSION
from learnloop.algorithm_versions import (
    FAILURE_SHARE_ALGORITHM_VERSION,
    LATEST_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
    UNEVIDENCED_RETURN_VERSIONS,
)
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.cli import app
from learnloop.clock import FrozenClock
from learnloop.daily_plan.engine import build_plan, new_material_candidates
from learnloop.daily_plan.lanes import classify_item
from learnloop.db.repositories import Repository
from learnloop.placement.state import unevidenced_return_active
from learnloop.scheduling.scheduler import read_due_queue, pool_admission
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import read_yaml, write_yaml

from tests.daily_plan_fakes import make_env, scheduled
from tests.helpers import (
    NOW,
    append_config_toml,
    create_basic_vault,
    create_placement_vault,
    set_algorithm_version,
    set_config_switch,
)

TAG = LATEST_ALGORITHM_VERSION
OLD = FAILURE_SHARE_ALGORITHM_VERSION
ITEM, LO, SIBLING = "pi_spec_easy", "lo_spectral", "pi_spec_hard"
OFF = "[placement]\nunevidenced_return = false\n"


def _at(minutes: float) -> FrozenClock:
    return FrozenClock(NOW + timedelta(minutes=minutes))


# ── the chain, the defaults, the switch ──────────────────────────────────────


def test_the_successor_is_one_constant_after_its_predecessor_and_the_latest():
    assert SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(UNEVIDENCED_RETURN_ALGORITHM_VERSION) - 1] == OLD == "mvp-0.55"
    # Slip or gap's successor (mvp-0.57) follows it and keeps it.
    assert UNEVIDENCED_RETURN_ALGORITHM_VERSION == "mvp-0.56" == SUCCESSOR_CHAIN[-4] and SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION == "mvp-0.59"
    assert UNEVIDENCED_RETURN_VERSIONS == frozenset({UNEVIDENCED_RETURN_ALGORITHM_VERSION, "mvp-0.57", "mvp-0.58", "mvp-0.59"})


@pytest.mark.parametrize(
    ("version", "toml", "active"),
    [
        (TAG, None, True),
        (TAG, OFF, False),
        (TAG, "[placement]\nenabled = false\n", False),
        (TAG, "[placement]\ninitial_probes = true\n", False),
    ],
    ids=["at-tag", "switch-off", "placement-off", "initial-probes"],
)
def test_the_gate_is_the_switch_and_ignored_opening_episodes(tmp_path, version, toml, active):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, version)
    if toml:
        append_config_toml(paths.root, toml)
    assert unevidenced_return_active(load_vault(paths.root)) is active


# ── the shape ────────────────────────────────────────────────────────────────


def _vault(tmp_path, name="vault", *, only_item=True):
    """A placement vault below the tag, with ``ITEM`` the only active item of its LO when ``only_item``. Below the tag
    stands the predecessor's serving: no vault opens there now, so the successor's switch off serves it (its off-branch
    is the predecessor's code)."""

    paths = create_placement_vault(tmp_path / name, version=OLD)
    set_config_switch(paths.root, "placement.unevidenced_return", False)
    if only_item:
        path = paths.practice_item_path("linear-algebra", SIBLING)
        write_yaml(path, {**read_yaml(path), "status": "retired"})
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=_at(0))
    return paths, vault, repository


def _answer(vault, repository, item_id=ITEM, *, primed, minutes=1):
    item = vault.practice_items[item_id]
    points = {criterion.id: criterion.points for criterion in vault.rubric_for_item(item).criteria}
    return complete_self_graded_attempt(
        vault, repository,
        AttemptDraft(practice_item_id=item_id, learner_answer_md="An answer.", primed=primed),
        SelfGradeInput(criterion_points=points, confidence=3),
        clock=_at(minutes),
    )


def _with_primed_answer(tmp_path, name="vault", *, only_item=True):
    paths, vault, repository = _vault(tmp_path, name, only_item=only_item)
    _answer(vault, repository, primed=True)
    state = repository.practice_item_states()[ITEM]
    assert state.last_attempt_at is not None and state.due_at is None and state.active
    mastery = repository.mastery_states().get(LO)
    assert mastery is None or mastery.last_evidence_at is None
    return paths, vault, repository


def _queue(vault, repository, minutes=2):
    # The item-shape cache is keyed on id(vault): a vault object built later in the worker can reuse a freed one's id
    # and read another vault's shapes (pre-existing; docs/reviews/placement-stranded.md). These tests compare queues
    # across vault objects value for value, so each build starts without it.
    from learnloop.scheduling import selection_rewards

    selection_rewards._SHAPE_CACHE.clear()
    return read_due_queue(vault, repository, clock=_at(minutes))


def _reload(paths, version, toml=None):
    """The vault moved to ``version``: at the tag the switch is on unless ``toml`` is :data:`OFF`; below it, off."""

    set_algorithm_version(paths, version)
    set_config_switch(paths.root, "placement.unevidenced_return", version == TAG and toml != OFF)
    return load_vault(paths.root)


def test_a_primed_first_answer_on_an_only_item_is_lost_below_the_tag_and_starts_as_learning_at_it(tmp_path):
    paths, vault, repository = _with_primed_answer(tmp_path)
    assert LO not in {s.learning_object_id for s in _queue(vault, repository)}
    assert pool_admission(vault, repository, now=NOW + timedelta(minutes=2))(ITEM) == "cold_start_unattempted"

    vault = _reload(paths, TAG)
    served = {s.practice_item_id: s for s in _queue(vault, repository)}
    assert pool_admission(vault, repository, now=NOW + timedelta(minutes=2))(ITEM) is None
    assert served[ITEM].components["new_material"] == 1.0
    assert served[ITEM].components["unevidenced_return"] == 1.0
    assert served[ITEM].priority > 0
    assert "back as learning: an earlier answer set no review and gave no evidence" in served[ITEM].plain_english
    assert "new material: starts as learning, no opening probe" not in served[ITEM].plain_english


def test_a_replay_held_self_report_returns_the_same_way(tmp_path):
    """The owner's own case: replay held a self_report whose contract was unrecorded, so it left an answered item with
    no due time and no evidence. The state alone is the shape, whatever wrote it."""

    paths, vault, repository = _vault(tmp_path)
    repository.upsert_practice_item_state(
        ITEM, difficulty=None, stability=None, due_at=None, last_attempt_at="2026-07-21T17:21:45Z", active=True,
    )
    assert LO not in {s.learning_object_id for s in _queue(vault, repository)}
    vault = _reload(paths, TAG)
    assert LO in {s.learning_object_id for s in _queue(vault, repository) if s.components.get("unevidenced_return")}


def test_the_never_attempted_sibling_keeps_its_own_label(tmp_path):
    paths, vault, repository = _with_primed_answer(tmp_path, only_item=False)
    vault = _reload(paths, TAG)
    served = {s.practice_item_id: s for s in _queue(vault, repository)}
    assert served[ITEM].components.get("unevidenced_return") == 1.0
    assert "unevidenced_return" not in served[SIBLING].components
    assert served[SIBLING].components["new_material"] == 1.0
    assert "new material: starts as learning, no opening probe" in served[SIBLING].plain_english


def test_an_answer_that_set_a_review_never_returns_as_learning(tmp_path):
    paths, vault, repository = _vault(tmp_path)
    _answer(vault, repository, primed=False)
    state = repository.practice_item_states()[ITEM]
    assert state.due_at is not None
    assert repository.mastery_states()[LO].last_evidence_at is not None
    vault = _reload(paths, TAG)
    assert not [s for s in _queue(vault, repository) if s.components.get("unevidenced_return")]


def test_evidence_on_the_lo_ends_the_return(tmp_path):
    """The rule is for an LO with no evidence. With evidence the item is the routine queue's, as at every other tag."""

    paths, vault, repository = _with_primed_answer(tmp_path, only_item=False)
    vault = _reload(paths, TAG)
    _answer(vault, repository, SIBLING, primed=False, minutes=2)
    assert repository.mastery_states()[LO].last_evidence_at is not None
    assert repository.practice_item_states()[ITEM].due_at is None
    at_tag = {s.practice_item_id: s for s in _queue(vault, repository, minutes=3)}
    assert "unevidenced_return" not in at_tag.get(ITEM, scheduled(ITEM, LO)).components
    assert at_tag.keys() == {s.practice_item_id for s in _queue(_reload(paths, OLD), repository, minutes=3)}


def test_the_answers_recent_reveal_holds_the_return_for_the_cold_delay_and_no_longer(tmp_path):
    paths, vault, repository = _with_primed_answer(tmp_path)
    vault = _reload(paths, TAG)
    repository.insert_reveal_event(
        {"practice_item_id": ITEM, "learning_object_id": LO, "source_kind": "tutor_answer", "amount": 0.5,
         "basis": "tutor_qa:practice"},
        clock=_at(1),
    )
    assert ITEM not in {s.practice_item_id for s in _queue(vault, repository, minutes=2)}
    assert ITEM not in {s.practice_item_id for s in _queue(vault, repository, minutes=24 * 60)}
    assert ITEM in {s.practice_item_id for s in _queue(vault, repository, minutes=24 * 60 + 2)}


def test_an_open_cold_followup_keeps_the_item_to_itself(tmp_path):
    paths, vault, repository = _with_primed_answer(tmp_path)
    vault = _reload(paths, TAG)
    repository.create_followup_task(
        kind="cold_retry", case_kind="diagnosis", case_ref="case-1",
        not_before="2030-01-01T00:00:00Z", selected_item_id=ITEM, clock=_at(1),
    )
    assert ITEM not in {s.practice_item_id for s in _queue(vault, repository)}


def test_a_spent_diagnostic_probe_stays_spent(tmp_path):
    """A single-use surface: the routine gate refuses it before placement is asked."""

    paths, vault, repository = _vault(tmp_path)
    repository.upsert_practice_item_state(
        ITEM, difficulty=None, stability=None, due_at=None, last_attempt_at="2026-07-21T17:21:45Z", active=False,
    )
    vault = _reload(paths, TAG)
    assert ITEM not in {s.practice_item_id for s in _queue(vault, repository)}
    assert pool_admission(vault, repository, now=NOW + timedelta(minutes=2))(ITEM) == "inactive_state"


# ── the switch-off path is the predecessor ───────────────────────────────────


def _dump(vault, repository):
    return [asdict(item) for item in _queue(vault, repository)]


def test_the_switch_and_the_old_tag_serve_the_predecessor_exactly_and_on_only_adds_the_hole(tmp_path):
    paths, vault, repository = _with_primed_answer(tmp_path)
    before = _dump(vault, repository)
    assert LO not in {row["learning_object_id"] for row in before}

    switched_off = _dump(_reload(paths, TAG, OFF), repository)
    assert switched_off == before

    # The same database with the switch back on. Here the returned LO is no other LO's prerequisite, so every other row
    # is the predecessor's exactly, value for value; only the returned item is added (and the queue order around it).
    on_paths, on_vault, on_repository = _with_primed_answer(tmp_path, "on")
    on = _dump(_reload(on_paths, TAG), on_repository)
    assert {row["practice_item_id"] for row in on} - {row["practice_item_id"] for row in before} == {ITEM}
    before_by_id = {row["practice_item_id"]: row for row in before}
    assert {row["practice_item_id"]: row for row in on if row["practice_item_id"] != ITEM} == before_by_id


def test_a_returned_prerequisite_moves_its_dependents_one_layer_later(tmp_path):
    """The one knock-on on other rows (Codex F1, accepted): new material is ordered prerequisites first, and a returned
    LO is new material, so an LO that names it as a prerequisite is placed one layer after it."""

    results = {}
    for name, version in (("below", OLD), ("at", TAG)):
        paths = create_placement_vault(tmp_path / name, version=OLD)
        set_config_switch(paths.root, "placement.unevidenced_return", False)
        for retired in ("pi_eig_mid", "pi_eig_hard"):
            path = paths.practice_item_path("linear-algebra", retired)
            write_yaml(path, {**read_yaml(path), "status": "retired"})
        vault = load_vault(paths.root)
        repository = Repository(paths.sqlite_path)
        sync_vault_state(vault, repository, clock=_at(0))
        _answer(vault, repository, "pi_eig_easy", primed=True)
        vault = _reload(paths, version)
        results[name] = {s.practice_item_id: s.components for s in _queue(vault, repository)}
    assert "pi_eig_easy" not in results["below"]
    assert results["at"]["pi_eig_easy"]["unevidenced_return"] == 1.0
    for dependent in ("pi_spec_easy", "pi_spec_hard"):
        assert results["below"][dependent]["placement_layer"] == 0.0
        assert results["at"][dependent]["placement_layer"] == 1.0
    for other in ("pi_diag_easy", "pi_diag_mid", "pi_diag_hard"):
        assert results["at"][other] == results["below"][other]


def _pool(paths, repository, minutes=2):
    from learnloop.daily_plan.engine import _classified_pool
    from learnloop.daily_plan.types import LANES

    vault = load_vault(paths.root)
    env = make_env(paths.root, lambda: _queue(vault, repository, minutes))
    built = _classified_pool(env, minutes=40.0, lanes_allowed=LANES, day=(), reentry=False)
    return [item.as_dict() for item in built.pool], [c.practice_item_id for c in new_material_candidates(None, built.pool)]


def test_the_plans_pool_with_the_switch_off_is_the_predecessors(tmp_path):
    """Real scheduler output through the plan's classification (Codex F4): the switched-off successor's pool and
    new-material candidates are the predecessor's exactly; with the switch on the returned item joins both."""

    paths, vault, repository = _with_primed_answer(tmp_path)
    before = _pool(paths, repository)
    assert ITEM not in {row["practice_item_id"] for row in before[0]}
    _reload(paths, TAG, OFF)
    assert _pool(paths, repository) == before
    on_paths, _on_vault, on_repository = _with_primed_answer(tmp_path, "on")
    _reload(on_paths, TAG)
    pool, candidates = _pool(on_paths, on_repository)
    assert ITEM in candidates and set(candidates) - set(before[1]) == {ITEM}
    assert next(row for row in pool if row["practice_item_id"] == ITEM)["unevidenced_return"] is True
    assert all("unevidenced_return" not in row for row in pool if row["practice_item_id"] != ITEM)


# ── the plan ─────────────────────────────────────────────────────────────────


def test_the_plan_admits_it_as_new_material(tmp_path):
    """Without the plan's lane the scheduler's return would sit in "later" and never be planned."""

    paths, vault, repository = _with_primed_answer(tmp_path)
    vault = _reload(paths, TAG)
    item = next(s for s in _queue(vault, repository) if s.practice_item_id == ITEM)
    pool_item = classify_item(
        item, rank=0, state=repository.practice_item_states()[ITEM], requested=False,
        now=NOW + timedelta(minutes=2), est_minutes=5.0, check=None, probe_slot_available=False,
    )
    assert (pool_item.lane, pool_item.reason, pool_item.never_attempted) == ("new", "back as learning", False)
    assert pool_item.unevidenced_return and pool_item.counts_as_new
    assert pool_item.as_dict()["unevidenced_return"] is True
    assert [c.practice_item_id for c in new_material_candidates(None, [pool_item])] == [ITEM]

    env = make_env(paths.root, [item])
    record = build_plan(env, kind="normal", budget=40.0, remembered=40, minutes_source="chip")
    assert [row["practice_item_id"] for row in record.admission["admitted"]] == [ITEM]


def test_an_open_problem_on_it_stays_the_repair_lanes_and_it_is_still_unacquired(tmp_path):
    """Codex F2 (ruled): an open diagnosed problem's repair comes first, as for any attempted item (the LO is served
    either way); the item still reads as a return, so no signal (staged frame's target_acquired) counts it acquired."""

    paths, vault, repository = _with_primed_answer(tmp_path)
    pool_item = classify_item(
        scheduled(ITEM, LO, new_material=1.0, unevidenced_return=1.0), rank=0,
        state=repository.practice_item_states()[ITEM], requested=False, now=NOW + timedelta(minutes=2),
        est_minutes=5.0, check=None, probe_slot_available=False, open_problem=True,
    )
    assert pool_item.lane == "repair"
    assert pool_item.unevidenced_return and pool_item.counts_as_new
    assert pool_item.as_dict()["unevidenced_return"] is True


# ── replay ───────────────────────────────────────────────────────────────────


def test_a_whole_vault_rebuild_writes_the_same_state_at_both_tags(tmp_path):
    """Serving only: the projection never reads the rule, so replay leaves the shape as it found it."""

    results = {}
    for name, version in (("below", OLD), ("at", TAG)):
        paths, vault, repository = _with_primed_answer(tmp_path, name)
        vault = _reload(paths, version)
        rebuild_all_derived_state(vault, repository)
        state = repository.practice_item_states()[ITEM]
        mastery = repository.mastery_states().get(LO)
        results[name] = (state.due_at, state.stability, state.active, mastery.last_evidence_at if mastery else None)
    assert results["below"] == results["at"] == (None, None, True, None)


def test_a_shadow_rebuild_reports_nothing_moved_for_the_shape(tmp_path):
    paths, _vault_at, repository = _with_primed_answer(tmp_path)
    # The vault at the tag, its derived state rebuilt there (what the tag's activation left).
    rebuild_all_derived_state(_reload(paths, TAG), repository)
    invocation = CliRunner().invoke(app, ["rebuild", "--shadow", "--json", "--vault", str(paths.root)])
    assert invocation.exit_code == 0, invocation.output
    report = json.loads(invocation.output)["shadow_rebuild"]
    assert report["candidate_algorithm_version"] == TAG
    assert report["live_database"]["unchanged"] is True
    effects = report["schedule_effects"]["practice_item_state"]
    assert effects["due_dates_moved"] == 0
    assert (effects["queue_due"]["newly_due"], effects["queue_due"]["no_longer_due"]) == (0, 0)
    assert report["learner_state_diff"]["facet"]["summary"]["changed"] == 0
    assert repository.practice_item_states()[ITEM].due_at is None


# ── the upgrade ──────────────────────────────────────────────────────────────
