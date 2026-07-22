"""P0.4 terminal-contract versions + consumer pins (spec_p0_measurement_correctness
§3.4, §7.3, §9.4)."""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.migrate import apply_migrations
from learnloop.db.repositories import Repository
from learnloop.services import goal_contracts as gc

from tests.helpers import NOW

CLOCK = FrozenClock(NOW)


@pytest.fixture
def repo(tmp_path):
    path = tmp_path / "state.sqlite"
    apply_migrations(path)
    return Repository(path)


def _body(**overrides):
    body = {
        "purpose": "Linear algebra for ML",
        "due_at": "2026-12-01T00:00:00Z",
        "target_recall": 0.8,
        "facet_scope": {"concepts": ["svd"], "facets": ["recall"]},
        "required_capabilities": ["state_definition"],
        "baseline_milestone": "m0",
        "exemplars": [{"id": "ex1", "surface_ref": "s1", "weight": 1.0}],
    }
    body.update(overrides)
    return body


def _confirm(repo, goal_id="g1", **overrides):
    return gc.confirm_goal_contract(
        repo, goal_id=goal_id, contract_body=_body(**overrides), clock=CLOCK
    )


# --- §9.4 line 1 -----------------------------------------------------------

def test_draft_cannot_pin_and_confirm_mints_v1_once(repo):
    v1 = _confirm(repo)
    assert v1.version == 1
    assert v1.change_class == "confirm"
    assert v1.minted is True
    # Idempotent re-confirm of identical bytes returns the same v1.
    again = _confirm(repo)
    assert again.id == v1.id
    assert again.minted is False
    assert len(repo.goal_contract_versions_for_goal("g1")) == 1


def test_confirm_without_exemplar_raises_and_records_draft(repo):
    with pytest.raises(gc.DraftNotConfirmable) as exc:
        gc.confirm_goal_contract(
            repo, goal_id="g1", contract_body=_body(exemplars=[]), clock=CLOCK
        )
    assert exc.value.reason == "no_exemplar"
    drafts = repo.goal_contract_drafts_for_goal("g1")
    assert len(drafts) == 1 and drafts[0]["rejection_reason"] == "pre_confirmation_draft"
    # No head -> nothing pinnable.
    assert gc.resolve_head(repo, "g1") is None


def test_confirm_without_blueprint_raises(repo):
    with pytest.raises(gc.DraftNotConfirmable) as exc:
        gc.confirm_goal_contract(
            repo,
            goal_id="g1",
            contract_body=_body(facet_scope={}, required_capabilities=[], baseline_milestone=None),
            clock=CLOCK,
        )
    assert exc.value.reason in {"no_reviewed_blueprint", "no_exemplar"}


# --- §9.4 line 2 -----------------------------------------------------------

def test_every_edit_appends_successor_prior_bytes_unchanged(repo):
    v1 = _confirm(repo)
    v1_row = repo.fetch_goal_contract_version(v1.id)

    # metadata edit
    v2 = gc.append_successor(repo, goal_id="g1", proposed_body=_body(due_at="2027-01-01T00:00:00Z"), clock=CLOCK)
    assert v2.change_class == "metadata" and v2.version == 2
    # evaluation edit
    v3 = gc.append_successor(repo, goal_id="g1", proposed_body=_body(due_at="2027-01-01T00:00:00Z", target_recall=0.9), clock=CLOCK)
    assert v3.change_class == "evaluation_change" and v3.version == 3
    # reweight edit
    v4 = gc.append_successor(
        repo,
        goal_id="g1",
        proposed_body=_body(due_at="2027-01-01T00:00:00Z", target_recall=0.9,
                            exemplars=[{"id": "ex1", "surface_ref": "s1", "weight": 2.0}]),
        clock=CLOCK,
    )
    assert v4.change_class == "reweight" and v4.version == 4
    # support edit
    v5 = gc.append_successor(
        repo,
        goal_id="g1",
        proposed_body=_body(due_at="2027-01-01T00:00:00Z", target_recall=0.9,
                            exemplars=[{"id": "ex1", "surface_ref": "s1", "weight": 2.0}],
                            facet_scope={"concepts": ["svd", "eig"], "facets": ["recall"]}),
        clock=CLOCK,
    )
    assert v5.change_class == "support_change" and v5.version == 5

    # v1 bytes + hashes byte-identical after every append.
    v1_after = repo.fetch_goal_contract_version(v1.id)
    assert v1_after["contract_json"] == v1_row["contract_json"]
    assert v1_after["content_hash"] == v1_row["content_hash"]
    assert v1_after["support_hash"] == v1_row["support_hash"]
    # head advanced.
    assert gc.resolve_head(repo, "g1").version == 5


def test_append_successor_requires_confirmed_head(repo):
    with pytest.raises(gc.NotConfirmed):
        gc.append_successor(repo, goal_id="never", proposed_body=_body(), clock=CLOCK)


# --- §9.4 line 3 (progression reads latest head) ---------------------------

def test_progression_reads_latest_head(repo):
    _confirm(repo)
    assert gc.resolve_head(repo, "g1").version == 1
    gc.append_successor(repo, goal_id="g1", proposed_body=_body(target_recall=0.85), clock=CLOCK)
    # A later decision resolves the NEW head with no stored cross-decision pin.
    assert gc.resolve_head(repo, "g1").version == 2


# --- §9.4 line 4 -----------------------------------------------------------

def test_support_change_flags_reserve_reweight_does_not(repo):
    v1 = _confirm(repo)
    # A reweight successor keeps support_hash unchanged -> pinned v1 stays representative.
    v2 = gc.append_successor(
        repo, goal_id="g1",
        proposed_body=_body(exemplars=[{"id": "ex1", "surface_ref": "s1", "weight": 3.0}]),
        clock=CLOCK,
    )
    assert v2.change_class == "reweight"
    cmp_after_reweight = gc.compare_support(repo, goal_id="g1", pinned_version_id=v1.id)
    assert cmp_after_reweight.representative is True
    assert v1.support_hash == v2.support_hash

    # A support successor changes support_hash -> pinned v1 becomes unrepresentative.
    v3 = gc.append_successor(
        repo, goal_id="g1",
        proposed_body=_body(exemplars=[{"id": "ex1", "surface_ref": "s1", "weight": 3.0}],
                            facet_scope={"concepts": ["svd", "pca"], "facets": ["recall"]}),
        clock=CLOCK,
    )
    assert v3.change_class == "support_change"
    cmp_after_support = gc.compare_support(repo, goal_id="g1", pinned_version_id=v1.id)
    assert cmp_after_support.representative is False
    assert v1.support_hash != v3.support_hash


# --- §9.4 line 5 + certification cites exact version -----------------------

def test_certification_cites_exact_assessed_version(repo):
    v1 = _confirm(repo)
    # Simulate an administration pinned to v1 via the atomic writer's columns.
    admin_id = _fake_administration(repo, target_version_id=v1.id, support_hash=v1.support_hash)
    # Head advances twice.
    gc.append_successor(repo, goal_id="g1", proposed_body=_body(target_recall=0.85), clock=CLOCK)
    gc.append_successor(repo, goal_id="g1", proposed_body=_body(target_recall=0.9), clock=CLOCK)
    citation = gc.certify_from_administration(repo, administration_id=admin_id)
    assert citation.cited_version_id == v1.id
    assert citation.cited_version == 1
    # v1 was reweight/eval only -> support unchanged -> representative.
    assert citation.representative is True


def test_append_version_rejects_stale_predecessor(repo):
    """L3 (§3.4): appending a successor whose predecessor is no longer the head is
    rejected as StaleContractHead inside the transaction -- never a silent fork of
    the head projection."""

    from learnloop.db.repositories import StaleContractHead

    v1 = _confirm(repo)
    with pytest.raises(StaleContractHead):
        repo.append_goal_contract_version(
            goal_id="g1", version=2, predecessor_version_id="not-the-head",
            contract_json="{}", content_hash="novel-hash", support_hash="sh",
            contract_schema_version=1, change_class="metadata", author="x", clock=CLOCK,
        )
    # Head is untouched.
    assert gc.resolve_head(repo, "g1").id == v1.id


def test_certification_terminal_when_observation_terminal(repo):
    """M3 (§4.5): a citation over a terminal-eligible observation is a terminal claim."""
    v1 = _confirm(repo)
    admin_id = _fake_administration(repo, target_version_id=v1.id, support_hash=v1.support_hash)
    surface_id = repo.fetch_administration(admin_id)["surface_id"]
    repo.insert_activity_observation(
        administration_id=admin_id, surface_id=surface_id,
        evidence_eligibility="terminal", eligibility_reason="assessment_terminal",
        clock=CLOCK,
    )
    citation = gc.certify_from_administration(repo, administration_id=admin_id)
    assert citation.terminal is True
    assert citation.eligibility_reason is None


def test_certification_non_terminal_when_feedback_before_response(repo):
    """M3 (§4.5): certification must read the observation's evidence_eligibility. A
    feedback-before-response administration yields an ineligible observation, so the
    citation is NON-terminal and carries the eligibility reason.

    Before the fix certify_from_administration never read evidence_eligibility, so it
    minted a terminal-looking citation for a burned-by-feedback administration."""

    v1 = _confirm(repo)
    admin_id = _fake_administration(repo, target_version_id=v1.id, support_hash=v1.support_hash)
    surface_id = repo.fetch_administration(admin_id)["surface_id"]
    from learnloop.services.activities import evidence_eligibility_for

    eligibility, reason = evidence_eligibility_for(
        purpose="assessment", feedback_condition="before_response"
    )
    repo.insert_activity_observation(
        administration_id=admin_id, surface_id=surface_id,
        evidence_eligibility=eligibility, eligibility_reason=reason, clock=CLOCK,
    )
    citation = gc.certify_from_administration(repo, administration_id=admin_id)
    assert citation.terminal is False
    assert citation.eligibility_reason == "feedback_before_response"
    # Still cites the exact assessed version -- it is demoted, not erased.
    assert citation.cited_version_id == v1.id


def test_certify_missing_target_pin_raises(repo):
    admin_id = _fake_administration(repo, target_version_id=None, support_hash=None)
    with pytest.raises(gc.NoTargetPin):
        gc.certify_from_administration(repo, administration_id=admin_id)


# --- §9.4 line 6 + 7 (authorized depth) ------------------------------------

def _envelope():
    return {
        "envelope_version": "denv-g1-v1",
        "bounds": {"target_additions": ["eig"], "cumulative_burden": {"delta": 1}},
        "reviewed_edges": [
            {"edge_id": "e1", "from_milestone": "m0", "to_milestone": "m1", "reviewed": True, "order": 1}
        ],
    }


def _confirm_with_envelope(repo, goal_id="gd"):
    return gc.confirm_goal_contract(
        repo, goal_id=goal_id,
        contract_body=_body(depth_envelope=_envelope()),
        clock=CLOCK,
    )


def test_one_reviewed_in_envelope_edge_appends_one_authorized_depth_step(repo):
    v1 = _confirm_with_envelope(repo)
    proposed = _body(
        depth_envelope=_envelope(),
        baseline_milestone="m1",
        facet_scope={"concepts": ["svd", "eig"], "facets": ["recall"]},
    )
    result = gc.append_authorized_depth_successor(
        repo, goal_id="gd", proposed_body=proposed,
        progression_decision={"qualifies": True, "evidence_receipt": "r1"},
        clock=CLOCK,
    )
    assert isinstance(result, gc.ContractVersion)
    assert result.change_class == "authorized_depth_step"
    row = repo.fetch_goal_contract_version(result.id)
    assert row["activated_edge_id"] == "e1"
    assert row["envelope_version"] == "denv-g1-v1"
    assert row["predecessor_milestone"] == "m0"
    assert row["evidence_receipt_json"] is not None
    # Exactly one successor appended (v1 + v2).
    assert len(repo.goal_contract_versions_for_goal("gd")) == 2
    assert v1.support_hash != result.support_hash  # support changed -> old reserves stale


@pytest.mark.parametrize(
    "mutate,expected_reason",
    [
        # outside envelope: adds a concept not in bounds.target_additions
        (dict(baseline_milestone="m1", facet_scope={"concepts": ["svd", "pca"], "facets": ["recall"]}),
         "outside_envelope"),
        # unreviewed: transition to a milestone with no reviewed edge
        (dict(baseline_milestone="m2", facet_scope={"concepts": ["svd", "eig"], "facets": ["recall"]}),
         "unreviewed_edge"),
    ],
)
def test_depth_rejections_become_nonpinnable_drafts(repo, mutate, expected_reason):
    _confirm_with_envelope(repo)
    proposed = _body(depth_envelope=_envelope(), **mutate)
    result = gc.append_authorized_depth_successor(
        repo, goal_id="gd", proposed_body=proposed,
        progression_decision={"qualifies": True, "evidence_receipt": "r1"},
        clock=CLOCK,
    )
    assert isinstance(result, gc.Draft)
    assert result.rejection_reason == expected_reason
    # No head change; the draft is not pinnable.
    assert gc.resolve_head(repo, "gd").version == 1


def test_depth_edge_matching_but_flips_admin_condition_rejected(repo):
    """H2 (§3.4): an edge-matching, in-envelope concept addition that ALSO changes a
    support dimension the envelope never authorizes (administration_conditions) must
    fail closed as an outside_envelope draft.

    Before the fix, Check 3 only diffed facet_scope.concepts, so this successor --
    which adds the authorized concept 'eig' AND flips open_book -- pinned silently."""

    _confirm_with_envelope(repo)
    proposed = _body(
        depth_envelope=_envelope(),
        baseline_milestone="m1",
        facet_scope={"concepts": ["svd", "eig"], "facets": ["recall"]},
        administration_conditions={"open_book": True},
    )
    result = gc.append_authorized_depth_successor(
        repo, goal_id="gd", proposed_body=proposed,
        progression_decision={"qualifies": True, "evidence_receipt": "r1"},
        clock=CLOCK,
    )
    assert isinstance(result, gc.Draft)
    assert result.rejection_reason == "outside_envelope"
    assert gc.resolve_head(repo, "gd").version == 1  # no silent pin


def test_depth_admin_condition_change_authorized_when_bounds_name_it(repo):
    """The same admin-condition flip pins when the envelope bounds explicitly name
    the administration_conditions dimension (H2: named dimensions are authorized)."""

    envelope = _envelope()
    envelope["bounds"]["administration_conditions"] = {"open_book": True}
    gc.confirm_goal_contract(
        repo, goal_id="gd", contract_body=_body(depth_envelope=envelope), clock=CLOCK
    )
    proposed = _body(
        depth_envelope=envelope,
        baseline_milestone="m1",
        facet_scope={"concepts": ["svd", "eig"], "facets": ["recall"]},
        administration_conditions={"open_book": True},
    )
    result = gc.append_authorized_depth_successor(
        repo, goal_id="gd", proposed_body=proposed,
        progression_decision={"qualifies": True, "evidence_receipt": "r1"},
        clock=CLOCK,
    )
    assert isinstance(result, gc.ContractVersion)
    assert result.change_class == "authorized_depth_step"


def test_depth_stale_envelope_rejected(repo):
    _confirm_with_envelope(repo)
    envelope = _envelope()
    envelope["envelope_version"] = "denv-g1-v2"  # changed across the edge
    proposed = _body(depth_envelope=envelope, baseline_milestone="m1",
                     facet_scope={"concepts": ["svd", "eig"], "facets": ["recall"]})
    result = gc.append_authorized_depth_successor(
        repo, goal_id="gd", proposed_body=proposed,
        progression_decision={"qualifies": True, "evidence_receipt": "r1"},
        clock=CLOCK,
    )
    assert isinstance(result, gc.Draft) and result.rejection_reason == "stale_envelope"


def test_depth_multiple_edges_rejected(repo):
    envelope = _envelope()
    envelope["reviewed_edges"].append(
        {"edge_id": "e1b", "from_milestone": "m0", "to_milestone": "m1", "reviewed": True, "order": 2}
    )
    gc.confirm_goal_contract(repo, goal_id="gd", contract_body=_body(depth_envelope=envelope), clock=CLOCK)
    proposed = _body(depth_envelope=envelope, baseline_milestone="m1",
                     facet_scope={"concepts": ["svd", "eig"], "facets": ["recall"]})
    result = gc.append_authorized_depth_successor(
        repo, goal_id="gd", proposed_body=proposed,
        progression_decision={"qualifies": True, "evidence_receipt": "r1"},
        clock=CLOCK,
    )
    assert isinstance(result, gc.Draft) and result.rejection_reason == "multiple_edges"


def test_depth_insufficient_evidence_rejected(repo):
    _confirm_with_envelope(repo)
    proposed = _body(depth_envelope=_envelope(), baseline_milestone="m1",
                     facet_scope={"concepts": ["svd", "eig"], "facets": ["recall"]})
    result = gc.append_authorized_depth_successor(
        repo, goal_id="gd", proposed_body=proposed,
        progression_decision={"qualifies": False},
        clock=CLOCK,
    )
    assert isinstance(result, gc.Draft) and result.rejection_reason == "insufficient_evidence"


def test_depth_predecessor_not_head_rejected(repo):
    _confirm_with_envelope(repo)
    proposed = _body(depth_envelope=_envelope(), baseline_milestone="m1",
                     facet_scope={"concepts": ["svd", "eig"], "facets": ["recall"]})
    result = gc.append_authorized_depth_successor(
        repo, goal_id="gd", proposed_body=proposed,
        progression_decision={"qualifies": True, "evidence_receipt": "r1"},
        predecessor_version_id="stale-id",
        clock=CLOCK,
    )
    assert isinstance(result, gc.Draft) and result.rejection_reason == "predecessor_not_head"


def test_append_successor_refuses_envelope_dimension_edit_without_milestone(repo):
    """M5 (§2.5): a plain successor that grows an envelope-governed dimension (adds a
    concept named in bounds.target_additions) must be refused even when the baseline
    milestone is unchanged -- it has to go through the authorized-depth path.

    Before the fix the guard only fired on a baseline_milestone change, so this edit
    silently appended a plain support_change and grew terminal support with no edge
    or evidence receipt."""

    _confirm_with_envelope(repo)
    with pytest.raises(gc.UseDepthSuccessor):
        gc.append_successor(
            repo, goal_id="gd",
            proposed_body=_body(
                depth_envelope=_envelope(),  # baseline_milestone stays "m0"
                facet_scope={"concepts": ["svd", "eig"], "facets": ["recall"]},
            ),
            clock=CLOCK,
        )


def test_append_successor_allows_ungoverned_support_change_with_envelope(repo):
    """M5 other direction: a support change on a dimension the envelope does NOT
    govern stays a plain support_change even while an envelope is active."""

    _confirm_with_envelope(repo)
    v2 = gc.append_successor(
        repo, goal_id="gd",
        proposed_body=_body(
            depth_envelope=_envelope(),
            administration_conditions={"time_limit_min": 30},  # not named in bounds
        ),
        clock=CLOCK,
    )
    assert isinstance(v2, gc.ContractVersion)
    assert v2.change_class == "support_change"


def test_append_successor_plain_support_change_without_envelope(repo):
    """M5: goals with no active envelope keep the plain support_change route."""

    _confirm(repo, goal_id="gn")  # no depth_envelope
    v2 = gc.append_successor(
        repo, goal_id="gn",
        proposed_body=_body(facet_scope={"concepts": ["svd", "pca"], "facets": ["recall"]}),
        clock=CLOCK,
    )
    assert v2.change_class == "support_change"


def test_append_successor_refuses_milestone_advance(repo):
    _confirm_with_envelope(repo)
    with pytest.raises(gc.UseDepthSuccessor):
        gc.append_successor(
            repo, goal_id="gd",
            proposed_body=_body(depth_envelope=_envelope(), baseline_milestone="m1"),
            clock=CLOCK,
        )


# --- §9.4 line 8 (deeper successor preserves earlier cert + no reserve reuse) --

def test_deeper_successor_preserves_earlier_certification(repo):
    v1 = _confirm_with_envelope(repo)
    # An administration certifies the m0 milestone at v1.
    admin_id = _fake_administration(repo, target_version_id=v1.id, support_hash=v1.support_hash)
    # Advance one authorized depth step to m1.
    v2 = gc.append_authorized_depth_successor(
        repo, goal_id="gd",
        proposed_body=_body(depth_envelope=_envelope(), baseline_milestone="m1",
                            facet_scope={"concepts": ["svd", "eig"], "facets": ["recall"]}),
        progression_decision={"qualifies": True, "evidence_receipt": "r1"},
        clock=CLOCK,
    )
    assert isinstance(v2, gc.ContractVersion)
    # Earlier certification is intact + still cites v1.
    citation = gc.certify_from_administration(repo, administration_id=admin_id)
    assert citation.cited_version_id == v1.id
    # But that old reserve is NOT fresh proof of the deeper head (support changed).
    assert citation.representative is False
    assert repo.fetch_goal_contract_version(v1.id) is not None  # v1 row untouched


# --- consumer pins projection ----------------------------------------------

def test_list_consumer_pins_unions_reserve_and_admin(repo):
    v1 = _confirm(repo)
    _fake_administration(repo, target_version_id=v1.id, support_hash=v1.support_hash)
    pins = gc.list_consumer_pins(repo, "g1")
    assert len(pins) == 1
    assert pins[0].consumer_kind == "administration"
    assert pins[0].target_contract_version_id == v1.id
    assert pins[0].representative is True


# ---------------------------------------------------------------------------

def _fake_administration(repo, *, target_version_id, support_hash):
    """Insert a minimal activity_administrations row pinned to a target version."""
    from learnloop.ids import new_ulid
    from learnloop.clock import utc_now_iso
    from learnloop.db.connection import connect

    admin_id = new_ulid()
    surface_id = new_ulid()
    card_id = new_ulid()
    card_version_id = new_ulid()
    family_id = new_ulid()
    now = utc_now_iso(CLOCK)
    with connect(repo.sqlite_path) as connection:
        connection.execute(
            "INSERT INTO activity_families(id, purpose, created_at) VALUES (?, 'assessment', ?)",
            (family_id, now),
        )
        connection.execute(
            "INSERT INTO activity_cards(id, family_id, created_at) VALUES (?, ?, ?)",
            (card_id, family_id, now),
        )
        connection.execute(
            """
            INSERT INTO activity_card_versions(
              id, card_id, version, card_contract_hash, contract_json, schema_version, created_at
            ) VALUES (?, ?, 1, 'ch', '{}', 1, ?)
            """,
            (card_version_id, card_id, now),
        )
        connection.execute(
            """
            INSERT INTO activity_surfaces(
              id, card_version_id, surface_hash, surface_json, created_at
            ) VALUES (?, ?, 'sh', '{}', ?)
            """,
            (surface_id, card_version_id, now),
        )
        connection.execute(
            """
            INSERT INTO activity_administrations(
              id, surface_id, card_version_id, family_id, purpose,
              administration_snapshot_hash, snapshot_json,
              target_contract_version_id, target_support_hash, created_at
            ) VALUES (?, ?, ?, ?, 'assessment', 'h', '{}', ?, ?, ?)
            """,
            (admin_id, surface_id, card_version_id, family_id, target_version_id, support_hash, now),
        )
        connection.commit()
    return admin_id
