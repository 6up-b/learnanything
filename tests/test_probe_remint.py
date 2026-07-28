"""Reminting an administered diagnostic probe into an ordinary practice item.

A single-use ``diagnostic_probe`` surface that turned out to be a good exercise
can be KEPT: a new ordinary item is minted as a mechanical copy (learner
authority, direct mint — no proposals round-trip), while the probe itself stays
deactivated with its administration history intact. Pinned here:

* the mint: ordinary practice mode picked deterministically from the probe's
  shape, ordinary attempt types, diagnostic-only tags stripped, provenance
  ``probe_remint`` naming the probe and the administering attempt;
* idempotency: reminting twice points at the existing remint, never duplicates;
* surface identity: the remint shares the probe's surface group, so probe
  candidacy stays excluded, familiarity discounts apply on the remint's first
  attempt, and remediation's independent-surface cold pick never treats the
  pair as independent;
* lifecycle: fresh FSRS state (the diagnostic attempt seeds nothing), normal
  activation through state_sync, ordinary-pool entry;
* supply: a remint does NOT satisfy the LO's diagnostic replenishment need;
* the sidecar door: happy path plus the stable error codes.
"""

from __future__ import annotations

import io
import json

from learnloop.clock import FrozenClock
from learnloop.db.repositories import MasteryState, Repository
from learnloop.services.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    ResolvedGrade,
    apply_attempt,
)
from learnloop.services.canonical_projection import surface_group_id
from learnloop.services.diagnostic_surface_supply import (
    probe_pool_empty_conditions,
    reconcile_diagnostic_surface_needs,
)
from learnloop.services.probe_episodes import (
    administered_surface_exclusions,
    eligible_instruments,
    enter_episode,
    episode_hypothesis_set,
)
from learnloop.services.probe_remint import (
    ProbeRemintError,
    remint_probe_as_practice_item,
)
from learnloop.services.recall_coverage import familiarity_discount_from_attempts
from learnloop.services.scheduler import build_due_queue
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import (
    ALGORITHM_VERSION,
    NOW,
    NOW_ISO,
    admit_probe_instrument_card,
    create_basic_vault,
)

CLOCK = FrozenClock(NOW)
LO_ID = "lo_svd_definition"
PROBE_ID = "pi_diag_keepworthy"
ATTEMPT_ID = "att_diag_administration"

TRACE_CONTRACT = {
    "status": "available",
    "recipes": [
        {
            "id": "compare_factors",
            "checkpoints": ["name_factors", "compare_transposes"],
            "dependencies": {"compare_transposes": ["name_factors"]},
        }
    ],
}


def _add_probe(
    vault_root,
    item_id: str = PROBE_ID,
    *,
    surface_family: str | None = None,
    with_trace: bool = False,
    attempt_types: tuple[str, ...] = ("diagnostic_probe", "dont_know"),
    facets: tuple[str, ...] = ("recall",),
) -> None:
    upsert_practice_item(
        vault_root,
        {
            "id": item_id,
            "learning_object_id": LO_ID,
            "subjects": None,
            "practice_mode": "diagnostic_probe",
            "attempt_types_allowed": list(attempt_types),
            "evidence_facets": list(facets),
            "evidence_weights": {facet: 1.0 / len(facets) for facet in facets},
            "trace_contract": TRACE_CONTRACT if with_trace else None,
            "prompt": f"Fresh diagnostic prompt for {item_id}.",
            "expected_answer": "V is the transposed factor.",
            "difficulty": 0.6,
            "difficulty_source": "author",
            "tags": ["diagnostic", "svd", "probe"],
            "surface_family": surface_family,
            "grading_rubric": {
                "max_points": 4,
                "criteria": [
                    {"id": "correctness", "points": 4, "description": "Correct selection."}
                ],
                "fatal_errors": [],
            },
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
        clock=CLOCK,
    )


def _add_ordinary(vault_root, item_id: str, *, surface_family: str | None = None) -> None:
    upsert_practice_item(
        vault_root,
        {
            "id": item_id,
            "learning_object_id": LO_ID,
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt", "dont_know"],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": f"Ordinary prompt for {item_id}.",
            "expected_answer": "An answer.",
            "surface_family": surface_family,
            "grading_rubric": {
                "max_points": 4,
                "criteria": [
                    {"id": "correctness", "points": 4, "description": "Correct answer."}
                ],
                "fatal_errors": [],
            },
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
        clock=CLOCK,
    )


def _seed_mastery(repository: Repository) -> None:
    repository.upsert_mastery_state(
        MasteryState(
            learning_object_id=LO_ID,
            logit_mean=0.0,
            logit_variance=1.0,
            evidence_count=1,
            last_evidence_at="2026-05-18T12:00:00Z",
            algorithm_version=ALGORITHM_VERSION,
            updated_at=NOW_ISO,
        )
    )


def _vault(tmp_path, *, probe_kwargs: dict | None = None):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    _add_probe(root, **(probe_kwargs or {}))
    vault = load_vault(root)
    repository = Repository(paths.sqlite_path)
    _seed_mastery(repository)
    sync_vault_state(vault, repository, clock=CLOCK)
    return vault, repository


def _administer(vault, repository, *, item_id: str = PROBE_ID, attempt_id: str = ATTEMPT_ID, attempt_type: str = "diagnostic_probe"):
    return apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=item_id,
                learner_answer_md="U is transposed.",
                attempt_type=attempt_type,
            ),
            attempt_id=attempt_id,
            grade=ResolvedGrade(
                rubric_score=2,
                criterion_points={"correctness": 2},
                evidence_rows=[],
                error_attributions=[],
                grader_confidence=0.9,
                confidence=3,
                manual_review_reason=None,
            ),
        ),
        clock=CLOCK,
    )


def _remint(vault, repository, *, attempt_id: str = ATTEMPT_ID):
    return remint_probe_as_practice_item(
        vault.root, vault, repository, attempt_id=attempt_id, clock=CLOCK
    )


def _queue_ids(vault, repository) -> set[str]:
    queue = build_due_queue(vault, repository, clock=CLOCK, persist_explanations=False)
    return {entry.practice_item_id for entry in queue}


# --- the mint ------------------------------------------------------------------------


def test_remint_creates_ordinary_copy_and_probe_stays_retired(tmp_path):
    vault, repository = _vault(
        tmp_path,
        probe_kwargs={
            "with_trace": True,
            "attempt_types": ("diagnostic_probe", "open_text", "dont_know"),
            "surface_family": "transposed_factor_family",
        },
    )
    _administer(vault, repository)
    probe = vault.practice_items[PROBE_ID]

    summary = _remint(vault, repository)

    assert summary["source_practice_item_id"] == PROBE_ID
    assert summary["attempt_id"] == ATTEMPT_ID
    # Trace contract available -> the constructed/written mode.
    assert summary["practice_mode"] == "constructed_response"

    reloaded = load_vault(vault.root)
    minted = reloaded.practice_items[summary["practice_item_id"]]
    assert minted.practice_mode == "constructed_response"
    # Ordinary attempt types: the probe's own set minus the diagnostic type.
    assert minted.attempt_types_allowed == ["open_text", "dont_know"]
    # Mechanical copy of the content + measurement contract.
    assert minted.prompt == probe.prompt
    assert minted.expected_answer == probe.expected_answer
    assert minted.evidence_facets == probe.evidence_facets
    assert minted.difficulty == probe.difficulty
    assert minted.grading_rubric is not None
    assert [c.id for c in minted.grading_rubric.criteria] == ["correctness"]
    assert minted.trace_contract is not None
    assert minted.trace_contract.recipes[0].checkpoints == [
        "name_factors",
        "compare_transposes",
    ]
    # Diagnostic-only tags stripped; remint tag added; content tags kept.
    assert "diagnostic" not in minted.tags and "probe" not in minted.tags
    assert "probe_remint" in minted.tags and "svd" in minted.tags
    # Provenance: origin + the probe id + the administering attempt.
    assert minted.provenance.origin == "probe_remint"
    ref = minted.provenance.source_refs[0]
    assert ref.ref_type == "existing_entity" and ref.ref_id == PROBE_ID
    assert ref.locator == f"administering_attempt:{ATTEMPT_ID}"
    # Shared surface group — the one independence primitive.
    assert surface_group_id(minted) == surface_group_id(probe)

    # The probe stays exactly as the single-use rules left it.
    probe_state = repository.practice_item_state(PROBE_ID)
    assert probe_state is not None and probe_state.active is False
    assert reloaded.practice_items[PROBE_ID].practice_mode == "diagnostic_probe"


def test_remint_without_trace_contract_is_short_answer_with_answering_type(tmp_path):
    vault, repository = _vault(tmp_path)  # attempt types: diagnostic_probe, dont_know
    _administer(vault, repository)

    summary = _remint(vault, repository)

    assert summary["practice_mode"] == "short_answer"
    minted = load_vault(vault.root).practice_items[summary["practice_item_id"]]
    # dont_know alone is not an answering mode: independent_attempt is added.
    assert minted.attempt_types_allowed == ["independent_attempt", "dont_know"]


def test_remint_is_idempotent_and_points_at_the_existing_remint(tmp_path):
    vault, repository = _vault(tmp_path)
    _administer(vault, repository)
    summary = _remint(vault, repository)

    # Same snapshot: refused with the existing id.
    try:
        _remint(vault, repository)
    except ProbeRemintError as exc:
        assert exc.code == "already_reminted"
        assert exc.details["practice_item_id"] == summary["practice_item_id"]
    else:
        raise AssertionError("second remint must not mint a duplicate")

    # Fresh load from disk: the provenance query still finds the remint.
    reloaded = load_vault(vault.root)
    try:
        remint_probe_as_practice_item(
            reloaded.root, reloaded, repository, attempt_id=ATTEMPT_ID, clock=CLOCK
        )
    except ProbeRemintError as exc:
        assert exc.code == "already_reminted"
        assert exc.details["practice_item_id"] == summary["practice_item_id"]
    else:
        raise AssertionError("remint after reload must not mint a duplicate")

    remints = [
        item
        for item in load_vault(vault.root).practice_items.values()
        if item.provenance.origin == "probe_remint"
    ]
    assert len(remints) == 1


def test_remint_guards(tmp_path):
    vault, repository = _vault(tmp_path)
    _administer(vault, repository)
    # An ordinary attempt on an ordinary item is not a probe administration.
    _administer(
        vault,
        repository,
        item_id="pi_svd_define_001",
        attempt_id="att_ordinary",
        attempt_type="independent_attempt",
    )

    try:
        _remint(vault, repository, attempt_id="att_missing")
    except ProbeRemintError as exc:
        assert exc.code == "attempt_not_found"
    else:
        raise AssertionError("unknown attempt must be refused")

    try:
        _remint(vault, repository, attempt_id="att_ordinary")
    except ProbeRemintError as exc:
        assert exc.code == "not_a_diagnostic_probe"
    else:
        raise AssertionError("non-probe attempt must be refused")


# --- lifecycle: ordinary pool entry + fresh scheduling state -------------------------


def test_remint_enters_ordinary_pool_and_probe_stays_out(tmp_path):
    vault, repository = _vault(tmp_path)
    _administer(vault, repository)
    summary = _remint(vault, repository)
    minted_id = summary["practice_item_id"]

    vault = load_vault(vault.root)
    sync_vault_state(vault, repository, clock=CLOCK)

    # Normal activation path: sync keeps the remint active (ordinary mode is
    # activatable) and never resurrects the administered probe.
    minted_state = repository.practice_item_state(minted_id)
    assert minted_state is not None and minted_state.active is True
    assert repository.practice_item_state(PROBE_ID).active is False

    ids = _queue_ids(vault, repository)
    assert minted_id in ids
    assert PROBE_ID not in ids


def test_remint_starts_with_fresh_fsrs_state(tmp_path):
    vault, repository = _vault(tmp_path)
    _administer(vault, repository)
    summary = _remint(vault, repository)
    minted_id = summary["practice_item_id"]

    # The diagnostic attempt must not seed the new item: no memory, no due date.
    state = repository.practice_item_state(minted_id)
    assert state is not None
    assert state.due_at is None
    assert state.stability is None
    assert state.difficulty is None
    assert state.last_attempt_at is None

    # First ordinary attempt schedules it normally.
    vault = load_vault(vault.root)
    sync_vault_state(vault, repository, clock=CLOCK)
    _administer(
        vault,
        repository,
        item_id=minted_id,
        attempt_id="att_remint_first",
        attempt_type="independent_attempt",
    )
    after = repository.practice_item_state(minted_id)
    assert after.due_at is not None
    assert after.stability is not None
    # The probe's own state remains unscheduled (probe attempts skip FSRS).
    assert repository.practice_item_state(PROBE_ID).due_at is None


# --- surface identity: probe exclusion, familiarity, remediation ---------------------


def test_remint_surface_group_stays_probe_ineligible(tmp_path):
    vault, repository = _vault(tmp_path, probe_kwargs={"surface_family": "shared_surface"})
    # A fresh control surface in its OWN group, probe-capable via the same card.
    _add_ordinary(vault.root, "pi_control_fresh", surface_family="independent_surface")
    vault = load_vault(vault.root)
    sync_vault_state(vault, repository, clock=CLOCK)
    _administer(vault, repository)
    summary = _remint(vault, repository)
    minted_id = summary["practice_item_id"]
    vault = load_vault(vault.root)
    sync_vault_state(vault, repository, clock=CLOCK)

    # The whole administered group — probe AND remint — is excluded forever.
    attempted_ids, attempted_surfaces = administered_surface_exclusions(vault, repository)
    assert PROBE_ID in attempted_ids
    assert surface_group_id(vault.practice_items[minted_id]) in attempted_surfaces

    # Behavior at the probe-selection door: bind BOTH the remint and the fresh
    # control to an admitted instrument card; only the control is admissible.
    admit_probe_instrument_card(repository, items=(minted_id, "pi_control_fresh"))
    episode = enter_episode(vault, repository, LO_ID, clock=CLOCK)
    hypothesis_set = episode_hypothesis_set(repository, episode)
    eligible = {
        entry.item.id
        for entry in eligible_instruments(
            vault, repository, episode, hypothesis_set=hypothesis_set
        )
    }
    assert "pi_control_fresh" in eligible
    assert minted_id not in eligible


def test_remint_first_attempt_carries_familiarity_discount(tmp_path):
    # No authored surface family: the probe's group falls back to its item id,
    # and the remint's surface_family pins that same identity.
    vault, repository = _vault(tmp_path)
    _administer(vault, repository)
    summary = _remint(vault, repository)
    vault = load_vault(vault.root)
    minted = vault.practice_items[summary["practice_item_id"]]
    assert minted.surface_family == PROBE_ID

    recent = repository.list_recent_attempts_by_learning_object(LO_ID, limit=10)
    result = familiarity_discount_from_attempts(
        recent,
        minted,
        covered_facets={facet: 1.0 for facet in minted.evidence_facets},
        config=vault.config,
    )
    # The probe's administration reads as prior exposure of this same surface.
    assert result.trace["same_surface_family_recent_mass"] > 0.0
    assert result.trace["same_surface_family_discount"] < 1.0
    assert result.independent_evidence_discount < 1.0


def test_remediation_cold_pick_rejects_remint_as_same_surface_as_probe_group(tmp_path):
    from learnloop.services.remediation import (
        prescribe_remediation,
        start_remediation_episode,
        start_remediation_treatment,
    )

    vault, repository = _vault(tmp_path, probe_kwargs={"surface_family": "shared_surface"})
    # An ordinary sibling in the probe's surface group.
    _add_ordinary(vault.root, "pi_shared_ordinary", surface_family="shared_surface")
    vault = load_vault(vault.root)
    sync_vault_state(vault, repository, clock=CLOCK)
    _administer(vault, repository)
    summary = _remint(vault, repository)
    minted_id = summary["practice_item_id"]
    vault = load_vault(vault.root)
    sync_vault_state(vault, repository, clock=CLOCK)
    # Keep exactly {remint, shared sibling} rankable for the repair.
    repository.upsert_practice_item_state("pi_svd_define_001", active=False, clock=CLOCK)

    misconception_id = repository.insert_misconception(
        learning_object_id=LO_ID,
        statement="Confuses SVD with eigendecomposition.",
        correction_statement="SVD applies to any matrix.",
        facet_ids=["recall"],
        target_facet="recall",
        confused_with_facet="application",
        severity=0.8,
        clock=CLOCK,
    )
    episode = start_remediation_episode(repository, misconception_id, clock=CLOCK)
    prescribe_remediation(vault, repository, episode["id"], clock=CLOCK)
    treatment = start_remediation_treatment(vault, repository, episode["id"], clock=CLOCK)

    # Both candidates share the probe's surface group, so there is NO
    # independent surface for the cold verification — the remint must not
    # masquerade as one.
    assert treatment["primed_item_id"] in {minted_id, "pi_shared_ordinary"}
    assert treatment["cold_item_id"] is None
    assert treatment["cold_unmeasurable_reason"] == "no_independent_surface"


# --- supply interplay ----------------------------------------------------------------


def test_remint_does_not_resolve_the_diagnostic_supply_need(tmp_path):
    vault, repository = _vault(tmp_path)
    _administer(vault, repository)
    reconcile_diagnostic_surface_needs(vault, repository, clock=CLOCK)
    needs = repository.diagnostic_surface_generation_needs(learning_object_id=LO_ID)
    assert len(needs) == 1 and needs[0]["status"] == "pending"

    _remint(vault, repository)
    vault = load_vault(vault.root)
    sync_vault_state(vault, repository, clock=CLOCK)
    reconcile_diagnostic_surface_needs(vault, repository, clock=CLOCK)

    # The remint is ordinary practice, not a fresh diagnostic surface: the
    # freshness check keys on practice_mode == diagnostic_probe, so the LO's
    # replenishment need stays open.
    needs = repository.diagnostic_surface_generation_needs(learning_object_id=LO_ID)
    assert len(needs) == 1 and needs[0]["status"] == "pending"

    # The empty-pool condition stands too: zero fresh diagnostic surfaces.
    conditions = {
        condition.learning_object_id: condition
        for condition in probe_pool_empty_conditions(vault, repository)
    }
    assert LO_ID in conditions
    assert conditions[LO_ID].reason == "excluded_as_seen"

    # Control: an actual fresh diagnostic surface resolves the need.
    _add_probe(vault.root, "pi_diag_replacement")
    vault = load_vault(vault.root)
    sync_vault_state(vault, repository, clock=CLOCK)
    reconcile_diagnostic_surface_needs(vault, repository, clock=CLOCK)
    needs = repository.diagnostic_surface_generation_needs(learning_object_id=LO_ID)
    assert [need["status"] for need in needs] == ["resolved"]


# --- sidecar door --------------------------------------------------------------------


def _rpc(messages: list[dict]) -> list[dict]:
    from learnloop_sidecar.server import serve

    stdin = io.StringIO("".join(json.dumps(message) + "\n" for message in messages))
    stdout = io.StringIO()
    serve(stdin, stdout)
    return [json.loads(line) for line in stdout.getvalue().splitlines()]


def _call(vault_root, method: str, params: dict) -> dict:
    return _rpc(
        [
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"vaultPath": str(vault_root)},
            },
            {"jsonrpc": "2.0", "id": 2, "method": method, "params": params},
        ]
    )[1]


def test_sidecar_remint_happy_path_and_error_codes(tmp_path):
    vault, repository = _vault(tmp_path)
    _administer(vault, repository)

    response = _call(vault.root, "remint_diagnostic_probe", {"attemptId": ATTEMPT_ID})
    result = response["result"]
    assert result["sourcePracticeItemId"] == PROBE_ID
    assert result["attemptId"] == ATTEMPT_ID
    assert result["practiceMode"] == "short_answer"
    minted_id = result["practiceItemId"]
    assert minted_id in load_vault(vault.root).practice_items

    # Idempotency at the door: the stable code + the existing id in details.
    duplicate = _call(vault.root, "remint_diagnostic_probe", {"attemptId": ATTEMPT_ID})
    assert duplicate["error"]["data"]["code"] == "already_reminted"
    assert duplicate["error"]["data"]["details"]["practice_item_id"] == minted_id

    missing = _call(vault.root, "remint_diagnostic_probe", {"attemptId": "att_missing"})
    assert missing["error"]["data"]["code"] == "attempt_not_found"


def test_sidecar_remint_refuses_non_probe_attempts(tmp_path):
    vault, repository = _vault(tmp_path)
    _administer(
        vault,
        repository,
        item_id="pi_svd_define_001",
        attempt_id="att_ordinary",
        attempt_type="independent_attempt",
    )

    response = _call(vault.root, "remint_diagnostic_probe", {"attemptId": "att_ordinary"})
    assert response["error"]["data"]["code"] == "not_a_diagnostic_probe"
