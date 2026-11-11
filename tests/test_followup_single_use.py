"""FG1 §4.2: a generated probe is served once and never again, at every door."""

from __future__ import annotations

import pytest

from learnloop.diagnosis.probe_remint import ProbeRemintError, remint_probe_as_practice_item
from learnloop.followup_serve import identity
from learnloop.scheduling.scheduler import build_due_queue
from learnloop.scheduling.serving_exclusions import (
    ROUTINE_GATES,
    admission_reason,
    routine_serving_exclusions,
    routine_withhold_reason,
)
from learnloop.substrate.replay import rebuild_derived_state
from learnloop.substrate.state_sync import practice_item_activatable, sync_vault_state
from learnloop.vault.loader import load_vault

from tests.followup_serve_helpers import CLOCK, generated_item, miss_with_rivals, rival_causes_vault

ITEM = "pi_generated_probe"


def _state(repository, item_id=ITEM):
    return repository.practice_item_state(item_id)


def _reasons(vault, repository, item_id=ITEM):
    return routine_withhold_reason(vault, vault.practice_items[item_id], _state(repository, item_id),
                                   routine_serving_exclusions(vault, repository))


def test_the_gates_are_named():
    assert {"generated_probe_closed", "generated_probe_reserved"} <= set(ROUTINE_GATES)


def test_the_first_serve_is_one_atomic_claim(tmp_path):
    _vault, repository, paths = rival_causes_vault(tmp_path)
    generated_item(paths.root, repository, ITEM, source="manual")
    first = identity.claim_serve(repository, ITEM, surface="desktop", presentation_id="pp_1", clock=CLOCK)
    assert first.granted and first.first
    # A remount of the same administration keeps its one submission.
    again = identity.claim_serve(repository, ITEM, surface="desktop", presentation_id="pp_1", clock=CLOCK)
    assert again.granted and not again.first
    # A second device, or a new presentation, is a new administration.
    other = identity.claim_serve(repository, ITEM, surface="phone", presentation_id="pp_1", clock=CLOCK)
    assert not other.granted and other.reason == identity.GENERATED_PROBE_CLOSED
    assert not identity.claim_serve(repository, ITEM, surface="desktop", presentation_id="pp_2", clock=CLOCK).granted


def test_an_item_with_no_identity_needs_no_claim(tmp_path):
    _vault, repository, _paths = rival_causes_vault(tmp_path)
    claim = identity.claim_serve(repository, "pi_ordinary", surface="desktop", presentation_id=None, clock=CLOCK)
    assert claim.granted and not claim.first


def test_reserved_until_served_then_closed_for_every_selector(tmp_path):
    vault, repository, paths = rival_causes_vault(tmp_path)
    _result, outcome = miss_with_rivals(vault, repository)
    vault = generated_item(paths.root, repository, ITEM, workflow_id=outcome.workflow_id)
    assert _reasons(vault, repository) == "generated_probe_reserved"
    assert identity.door_refusal(repository, ITEM) == identity.GENERATED_PROBE_RESERVED
    assert identity.door_refusal(repository, ITEM, workflow_id=outcome.workflow_id) is None
    assert ITEM not in {item.practice_item_id for item in build_due_queue(vault, repository, limit=None)}
    identity.claim_serve(repository, ITEM, surface="desktop", presentation_id="pp_1", clock=CLOCK)
    assert _reasons(vault, repository) == "generated_probe_closed"
    assert identity.door_refusal(repository, ITEM, workflow_id=outcome.workflow_id) == identity.GENERATED_PROBE_CLOSED


def test_a_request_never_gets_one_even_unserved(tmp_path):
    _vault, repository, paths = rival_causes_vault(tmp_path)
    vault = generated_item(paths.root, repository, ITEM, source="entry")
    exclusions = routine_serving_exclusions(vault, repository)
    item = vault.practice_items[ITEM]
    assert routine_withhold_reason(vault, item, _state(repository), exclusions) is None
    assert admission_reason(vault, item, _state(repository), exclusions, None, requested=True) == "generated_probe_reserved"


def test_retired_while_unused_stays_retired_after_sync_and_rebuild(tmp_path):
    _vault, repository, paths = rival_causes_vault(tmp_path)
    vault = generated_item(paths.root, repository, ITEM, source="manual")
    assert _state(repository).active
    assert identity.retire(repository, ITEM, reason="continue_without_it", clock=CLOCK)
    assert not _state(repository).active
    sync_vault_state(vault, repository, clock=CLOCK)
    assert not _state(repository).active
    rebuild_derived_state(vault, repository)
    assert not _state(repository).active
    assert ITEM in identity.closed_probe_ids(repository)
    # A claim after retirement is refused.
    assert not identity.claim_serve(repository, ITEM, surface="desktop", presentation_id=None, clock=CLOCK).granted


def test_state_sync_shares_one_predicate(tmp_path):
    vault, _repository, _paths = rival_causes_vault(tmp_path)
    item = next(iter(vault.practice_items.values()))
    assert practice_item_activatable(item.id, item, review_parked=set(), measurement_superseded=set())
    assert not practice_item_activatable(item.id, item, review_parked=set(), measurement_superseded=set(),
                                         generated_probe_closed=frozenset({item.id}))


def test_remint_refuses_the_identity(tmp_path):
    from tests.causal_p2_acceptance_helpers import _divergent_failure

    vault, repository, paths = rival_causes_vault(tmp_path)
    result = _divergent_failure(vault, repository, attempt_id="att_remint")
    from tests.causal_p2_acceptance_helpers import SOURCE_ITEM

    identity.register(repository, practice_item_id=SOURCE_ITEM, revision="r", source="manual", clock=CLOCK)
    raw = vault.practice_items[SOURCE_ITEM].model_copy(update={"practice_mode": "diagnostic_probe"})
    vault.practice_items[SOURCE_ITEM] = raw
    with pytest.raises(ProbeRemintError) as caught:
        remint_probe_as_practice_item(paths.root, vault, repository, attempt_id=result.attempt_id, clock=CLOCK)
    assert caught.value.code == "generated_probe_single_use"


def test_the_teachers_probe_headers_leave_it_out(tmp_path):
    from learnloop.teacher.brief import _probe_headers

    class Nothing:
        @staticmethod
        def reason(_item_id):
            return None

    _vault, repository, paths = rival_causes_vault(tmp_path)
    vault = generated_item(paths.root, repository, ITEM, source="entry")
    lo_id = vault.practice_items[ITEM].learning_object_id
    headers = _probe_headers(vault, repository, lo_id, Nothing(), set(), {})
    assert ITEM not in {row["id"] for row in headers}


def test_an_exam_never_reserves_one(tmp_path):
    from learnloop.clock import FrozenClock
    from learnloop.followup_serve import identity as fg1_identity
    from learnloop.goals.exam_pool import release_exam_pool, reserve_exam_pool
    from tests.exam_pool_helpers import NOW
    from tests.exam_protection_review_helpers import _reserved_pool

    paths, repository = _reserved_pool(tmp_path)
    vault = load_vault(paths.root)
    goal = vault.goals[0]
    assert "pi_pool_apply_mid" in repository.reserved_exam_pool_item_ids()
    release_exam_pool(repository, goal.id, clock=FrozenClock(NOW))
    fg1_identity.register(repository, practice_item_id="pi_pool_apply_mid", revision="r", source="manual", clock=CLOCK)
    reserve_exam_pool(vault, repository, goal, item_count=3, clock=FrozenClock(NOW))
    assert "pi_pool_apply_mid" not in repository.reserved_exam_pool_item_ids()
