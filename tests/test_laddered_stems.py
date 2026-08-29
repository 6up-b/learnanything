"""Meas §3.A2 laddered stems (implementation plan item 6.4).

The §10 line these tests exist for:

    Two parts of one laddered stem at the same capability count as ~one
    independent group; two parts at different capabilities count as two.

The rule is deliberately NOT implemented here — it lives as two edge cases
inside ``familiarity.tight_kinship_clusters``, the single-linkage pass that
already decides kinship, per augmentation §8's "one code path". So these tests
drive it through ``progression.apply_evidence_cap``, the public caller, and one
of them pins the inertness that makes the change additive: with no stem identity
supplied, the clustering is exactly what it was.
"""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.migrate import apply_migrations
from learnloop.db.repositories import Repository
from learnloop.substrate import activities as A
from learnloop.learner import familiarity as F
from learnloop.scheduling import progression as P
from learnloop.content.authoring.laddered_stems import (
    MIN_PAIRS_PER_ARM,
    STEM_INDEPENDENCE_METRIC,
    stem_column_for_item,
    stem_id_for_item,
    stem_independence_signal,
    stem_shapes,
)
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.models import EvidenceFingerprint, LadderedStemContract, PracticeItem
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import NOW, NOW_ISO, create_basic_vault, set_algorithm_version, write_facets

CLOCK = FrozenClock(NOW)
STEM = "stem_svd_matrix_A"
FACET = "f_svd"

FACETS = [{"id": FACET, "kind": "procedure_contract", "claim": "Compute an SVD."}]


@pytest.fixture
def repo(tmp_path):
    path = tmp_path / "state.sqlite"
    apply_migrations(path)
    return Repository(path)


def _surface(repo, *, suffix, features):
    """One activity surface carrying a soft-kinship feature vector.

    Mirrors ``tests/test_progression._surface``: the kinship clustering reads
    stored features, so a test about clustering has to write them.
    """

    family_id = repo.ensure_activity_family(
        purpose="practice", legacy_kind=None, title=f"f-{suffix}", clock=CLOCK
    )
    card_id = repo.ensure_activity_card(family_id=family_id, clock=CLOCK)
    cv = repo.ensure_activity_card_version(
        card_id=card_id,
        version=1,
        card_contract_hash=A.canonical_hash({"s": suffix}),
        contract_json="{}",
        schema_version=1,
        clock=CLOCK,
    )
    sid = repo.ensure_activity_surface(
        card_version_id=cv,
        surface_hash=f"sh-{suffix}",
        fingerprint=None,
        surface_json="{}",
        clock=CLOCK,
    )
    repo.upsert_soft_kinship_features(
        surface_id=sid,
        feature_schema_version=F.FEATURE_SCHEMA_VERSION,
        features=features,
        clock=CLOCK,
    )
    return sid


#: Warmth high enough that the pre-A2 rule co-clusters the two surfaces. Parts of
#: one stem share a stimulus, a source and usually a facet, so this is what a real
#: stem's parts look like to the feature vector — which is exactly why the
#: capability rule has to be an explicit edge case rather than an emergent one.
_KIN = {"target_facet_overlap": 3.0, "recipe_overlap": 3.0, "semantic_similarity": 3.0}

#: Warmth low enough that nothing co-clusters on features alone.
_DISTANT = {"target_facet_overlap": 0.0}


# ---------------------------------------------------------------------------
# §10: same column ~ one group; different columns ~ two
# ---------------------------------------------------------------------------


def test_two_parts_at_one_capability_are_one_independent_group(repo):
    a = _surface(repo, suffix="p1", features=_KIN)
    b = _surface(repo, suffix="p2", features=_KIN)

    cap = P.apply_evidence_cap(
        repo,
        surface_ids=[a, b],
        stem_columns={a: (STEM, "procedure_execution"), b: (STEM, "procedure_execution")},
    )

    assert cap.independent_group_count == 1
    assert len(cap.clusters) == 1


def test_two_parts_at_different_capabilities_are_two_independent_groups(repo):
    """The edge the pre-A2 rule would have got wrong.

    Both surfaces carry the SAME high-warmth feature vector, so without the stem
    rule they co-cluster and a whole capability row collapses into one
    observation. §3.A2: "retrieval and coordination on one stimulus are genuinely
    different measurements."
    """

    a = _surface(repo, suffix="p3", features=_KIN)
    b = _surface(repo, suffix="p4", features=_KIN)
    # Control: without the stem identity, these two ARE one group.
    assert P.apply_evidence_cap(repo, surface_ids=[a, b]).independent_group_count == 1

    cap = P.apply_evidence_cap(
        repo,
        surface_ids=[a, b],
        stem_columns={a: (STEM, "retrieval"), b: (STEM, "coordination")},
    )

    assert cap.independent_group_count == 2


def test_same_column_co_clusters_even_when_the_features_are_cold(repo):
    """The other direction of the same rule.

    Two parts of one stimulus at one capability are close to one observation
    whatever the soft features say — they share the context load by construction.
    """

    a = _surface(repo, suffix="p5", features=_DISTANT)
    b = _surface(repo, suffix="p6", features=_DISTANT)
    assert P.apply_evidence_cap(repo, surface_ids=[a, b]).independent_group_count == 2

    cap = P.apply_evidence_cap(
        repo,
        surface_ids=[a, b],
        stem_columns={a: (STEM, "retrieval"), b: (STEM, "retrieval")},
    )

    assert cap.independent_group_count == 1


def test_different_stems_are_untouched_by_the_rule(repo):
    """A2 is a statement about parts of ONE stimulus and nothing else.

    Two kin surfaces from different stems keep the warmth verdict; the stem rule
    abstains rather than splitting them by capability.
    """

    a = _surface(repo, suffix="p7", features=_KIN)
    b = _surface(repo, suffix="p8", features=_KIN)

    cap = P.apply_evidence_cap(
        repo,
        surface_ids=[a, b],
        stem_columns={a: ("stem_one", "retrieval"), b: ("stem_two", "coordination")},
    )

    assert cap.independent_group_count == 1


def test_the_rule_is_inert_without_stem_identity(repo):
    """Every pre-A2 caller gets byte-identical clustering.

    The change is additive only if omitting ``stem_columns`` reproduces the old
    behaviour exactly — otherwise it silently reinterprets existing evidence.
    """

    ids = [_surface(repo, suffix=f"p9{i}", features=_KIN) for i in range(3)]

    without = F.tight_kinship_clusters(repo, surface_ids=ids)
    with_empty = F.tight_kinship_clusters(repo, surface_ids=ids, stem_columns={})
    with_none = F.tight_kinship_clusters(repo, surface_ids=ids, stem_columns=None)

    assert without == with_empty == with_none


# ---------------------------------------------------------------------------
# Stem identity
# ---------------------------------------------------------------------------


def _item(item_id: str, *, capability: str, stem: str | None, fingerprint: str | None) -> PracticeItem:
    return PracticeItem(
        id=item_id,
        learning_object_id="lo_svd_definition",
        practice_mode="constructed_response",
        prompt="Part.",
        expected_answer="Answer.",
        capability=capability,
        laddered_stem=(
            LadderedStemContract(stem_id=stem, part_index=0, part_count=4) if stem else None
        ),
        evidence_fingerprint=EvidenceFingerprint(shared_stimulus_id=fingerprint),
        created_at=NOW_ISO,
        updated_at=NOW_ISO,
    )


def test_stem_identity_falls_back_to_the_pre_existing_fingerprint():
    """A stem authored before A2 still participates in the rule.

    ``EvidenceFingerprint.shared_stimulus_id`` predates the instrument, and an
    item declaring only that is a stem part in every way that matters.
    """

    authored = _item("a", capability="retrieval", stem=STEM, fingerprint=None)
    legacy = _item("b", capability="retrieval", stem=None, fingerprint=STEM)
    neither = _item("c", capability="retrieval", stem=None, fingerprint=None)

    assert stem_id_for_item(authored) == STEM
    assert stem_id_for_item(legacy) == STEM
    assert stem_id_for_item(neither) is None
    assert stem_column_for_item(authored) == (STEM, "retrieval")


def test_a_part_with_no_capability_cannot_be_placed_in_a_column():
    """Guessing a column would decide the independence question by default."""

    unplaced = PracticeItem(
        id="d",
        learning_object_id="lo_svd_definition",
        practice_mode="constructed_response",
        prompt="Part.",
        expected_answer="Answer.",
        laddered_stem=LadderedStemContract(stem_id=STEM, part_index=1, part_count=2),
        created_at=NOW_ISO,
        updated_at=NOW_ISO,
    )

    assert stem_id_for_item(unplaced) == STEM
    assert stem_column_for_item(unplaced) is None


# ---------------------------------------------------------------------------
# The revert criterion
# ---------------------------------------------------------------------------


def _write_part(paths, item_id: str, *, capability: str, correct: bool) -> None:
    write_yaml(
        paths.practice_item_path("linear-algebra", item_id),
        {
            "schema_version": 1,
            "id": item_id,
            "learning_object_id": "lo_svd_definition",
            "practice_mode": "constructed_response",
            "attempt_types_allowed": ["independent_attempt"],
            "evidence_facets": [FACET],
            "evidence_weights": {FACET: 1.0},
            "capability": capability,
            "laddered_stem": {"stem_id": STEM, "part_index": 0, "part_count": 4},
            "evidence_fingerprint": {"shared_stimulus_id": STEM},
            "prompt": f"Part at {capability}.",
            "expected_answer": "Answer." if correct else "Answer.",
            "difficulty": 0.5,
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "c1", "points": 4, "description": "correct"}],
                "fatal_errors": [],
            },
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )


def _stem_vault(tmp_path, parts):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.7")
    write_facets(paths, FACETS)
    for item_id, capability in parts:
        _write_part(paths, item_id, capability=capability, correct=True)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=CLOCK)
    return paths, vault, repository


def test_stem_shape_names_a_one_column_stem_as_not_a_ladder(tmp_path):
    """The failure mode that looks like success in an item count."""

    _paths, vault, _repo = _stem_vault(
        tmp_path,
        [("pi_stem_a", "retrieval"), ("pi_stem_b", "retrieval")],
    )

    shapes = {shape.stem_id: shape for shape in stem_shapes(vault)}

    assert shapes[STEM].columns_filled == 1
    assert shapes[STEM].is_ladder is False


def test_stem_independence_signal_abstains_before_it_has_both_arms(tmp_path):
    """§3.A2: "Measure this before trusting it." Abstention is the honest default."""

    _paths, vault, repository = _stem_vault(
        tmp_path,
        [("pi_stem_a", "retrieval"), ("pi_stem_b", "coordination")],
    )

    metric = stem_independence_signal(vault, repository)

    assert metric.name == STEM_INDEPENDENCE_METRIC
    assert metric.availability == "no_data"
    # The whole discipline: a rate over no pairs is never 0.0 and never 1.0.
    assert metric.value is None
    assert metric.detail["verdict"] == "insufficient_pairs"
    assert metric.detail["min_pairs_per_arm"] == MIN_PAIRS_PER_ARM


def test_stem_independence_signal_reports_both_arms_once_pairs_exist(tmp_path):
    """The revert criterion, computed.

    Four parts: two at ``retrieval`` (both correct) and two at
    ``procedure_execution`` (both wrong). Within-column pairs therefore always
    agree; cross-column pairs never do — the shape the independence claim
    predicts, and the metric has to be able to say so.
    """

    parts = [
        ("pi_stem_r1", "retrieval"),
        ("pi_stem_r2", "retrieval"),
        ("pi_stem_p1", "procedure_execution"),
        ("pi_stem_p2", "procedure_execution"),
    ]
    _paths, vault, repository = _stem_vault(tmp_path, parts)
    for index, (item_id, capability) in enumerate(parts):
        repository.insert_practice_attempt(
            {
                "id": f"att_{item_id}",
                "practice_item_id": item_id,
                "learning_object_id": "lo_svd_definition",
                "subject": "linear-algebra",
                "concept": "singular_value_decomposition",
                "practice_mode": "constructed_response",
                "attempt_type": "independent_attempt",
                "learner_answer_md": "x",
                "evidence_facets": [FACET],
                "evidence_weights": {FACET: 1.0},
                "rubric_score": 4 if capability == "retrieval" else 0,
                "correctness": 1.0 if capability == "retrieval" else 0.0,
                "confidence": None,
                "latency_seconds": None,
                "hints_used": 0,
                "error_type": None,
                "grader_confidence": 1.0,
                "manual_review": 0,
                "manual_review_reason": None,
                "created_at": f"2026-07-2{index}T00:00:00+00:00",
            }
        )

    metric = stem_independence_signal(vault, repository)

    # 2 within-column pairs (r1/r2, p1/p2) and 4 cross-column pairs.
    assert metric.detail["within_column_pairs"] == 2
    assert metric.detail["cross_column_pairs"] == 4
    # Within-column arm is below the floor, so no claim is made — reported, not
    # asserted, which is the point of naming the abstention arm.
    assert metric.availability == "no_data"
    assert metric.detail["within_column_agreement"] == 1.0
    assert metric.detail["cross_column_agreement"] == 0.0
    assert metric.detail["independence_margin"] == 1.0


# ---------------------------------------------------------------------------
# The doctor: a "stem" that fills one column is the failure mode
# ---------------------------------------------------------------------------


def test_the_doctor_warns_when_a_stem_fills_only_one_column(tmp_path):
    """The failure mode that looks like success in an item count.

    A warning rather than an error: the vault is not wrong, it is paying four
    items for roughly one observation, and the kinship rule will correctly
    enforce that. But it has to be said out loud or nobody sees it.
    """

    from learnloop.ops.doctor import _check_blueprints_and_criteria

    _paths, vault, _repo = _stem_vault(
        tmp_path,
        [("pi_stem_a", "retrieval"), ("pi_stem_b", "retrieval")],
    )

    issues: list = []
    _check_blueprints_and_criteria(vault, issues)
    codes = {issue.code for issue in issues}

    assert "laddered_stem:single_column" in codes


def test_the_doctor_is_silent_on_a_real_ladder(tmp_path):
    from learnloop.ops.doctor import _check_blueprints_and_criteria

    _paths, vault, _repo = _stem_vault(
        tmp_path,
        [("pi_stem_a", "retrieval"), ("pi_stem_b", "procedure_execution")],
    )

    issues: list = []
    _check_blueprints_and_criteria(vault, issues)

    assert not any(issue.code.startswith("laddered_stem:") for issue in issues)
