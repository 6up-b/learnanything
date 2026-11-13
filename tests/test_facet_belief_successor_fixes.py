"""The facet-belief successor's corrections (mvp-0.59; docs/reviews/refactor-phase-1-fixes-successor.md, rows S1-S6).

Each test is a fail-first test of one correction at the tag, beside a switch-off twin where the correction is
gated: with ``[facet_diagnostic] canonical_belief_fixes = false`` the predecessor (mvp-0.58) is served exactly.
Fakes only; no model call.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from learnloop.algorithm_versions import FACET_BELIEF_FIX_ALGORITHM_VERSION
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.learner.assessment_contracts import snapshot_for_presentation
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import NOW, NOW_ISO, create_basic_vault, set_config_switch, write_facets

TAG = FACET_BELIEF_FIX_ALGORITHM_VERSION
SWITCH = "facet_diagnostic.canonical_belief_fixes"
LO_ID = "lo_svd_definition"
TWO_FACET_ITEM = "pi_svd_two_facets_001"

_UNCERTAINTY_COLUMNS = (
    "learning_object_id", "facet_id", "hypothesis_marginal", "uncertainty", "status", "opened_by_attempt_id",
    "opened_reason", "last_evidence_at", "algorithm_version",
)


def _uncertainty_rows(repository):
    with repository.connection() as connection:
        return [tuple(row) for row in connection.execute(
            f"SELECT {', '.join(_UNCERTAINTY_COLUMNS)} FROM facet_uncertainty ORDER BY learning_object_id, facet_id"
        ).fetchall()]


def _canonical_belief(repository):
    with repository.connection() as connection:
        return [tuple(row) for row in connection.execute(
            "SELECT facet_id, capability_key, practice_item_id, recall_alpha, recall_beta, consecutive_failures "
            "FROM facet_recall_state ORDER BY facet_id, capability_key, practice_item_id"
        ).fetchall()]


def _two_facet_item(paths, *, criterion_facet_weights=None, targets=None):
    """Two equal criteria, ``c_def`` and ``c_rot``, on the facets ``recall`` and ``geometry``.

    ``criterion_facet_weights`` maps them through the item's map; ``targets`` (criterion id -> facet) through
    authored criterion targets instead. The descriptions share no word with either facet id, so the lexical
    fallback maps neither criterion."""

    def criterion(criterion_id, description):
        raw = {"id": criterion_id, "points": 2.0, "description": description}
        if targets is not None:
            raw["targets"] = [
                {"facet": targets[criterion_id], "capability": "declarative_recall", "role": "primary"}
            ]
        return raw

    upsert_practice_item(paths.root, {
        "id": TWO_FACET_ITEM, "learning_object_id": LO_ID, "subjects": None,
        "practice_mode": "short_answer", "attempt_types_allowed": ["independent_attempt"],
        "evidence_facets": ["recall", "geometry"], "evidence_weights": {"recall": 1.0, "geometry": 1.0},
        "criterion_facet_weights": criterion_facet_weights or {},
        "prompt": "Define the SVD, then give the SVD of a rotation.", "expected_answer": "U Sigma V^T; R = R I I.",
        "grading_rubric": {"max_points": 4, "fatal_errors": [], "criteria": [
            criterion("c_def", "Writes the factorization."),
            criterion("c_rot", "Handles the rotation case."),
        ]},
        "created_at": NOW_ISO, "updated_at": NOW_ISO,
    }, clock=FrozenClock(NOW))


def _two_facet_vault(root, *, belief_fixes=True, **item):
    paths = create_basic_vault(root)
    if not belief_fixes:
        set_config_switch(paths.root, SWITCH, False)
    write_facets(paths, [
        {"id": "recall", "kind": "definition", "claim": "Recall the SVD definition."},
        {"id": "geometry", "kind": "definition", "claim": "SVD as rotate, scale, rotate."},
    ])
    _two_facet_item(paths, **item)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    return paths, vault, repository


def _answer_failing_the_definition(vault, repository, *, minutes=0):
    """Presented under a frozen contract; the definition criterion fails, the rotation one passes."""

    clock = FrozenClock(NOW + timedelta(minutes=minutes))
    contract = snapshot_for_presentation(repository, vault, vault.practice_items[TWO_FACET_ITEM], clock=clock)
    return complete_self_graded_attempt(
        vault, repository,
        AttemptDraft(TWO_FACET_ITEM, "R = R I I.", assessment_contract_version_id=contract),
        SelfGradeInput(criterion_points={"c_def": 0.0, "c_rot": 2.0}, confidence=5),
        clock=clock,
    )


# -- S1: the uncertainty layer reads the criterion -> facet map the contract froze. ---------------------------------


def test_s1_a_rebuild_after_the_items_mapping_changed_keeps_the_uncertainty_where_the_contract_put_it(tmp_path):
    paths, vault, repository = _two_facet_vault(
        tmp_path / "vault", criterion_facet_weights={"c_def": {"recall": 1.0}, "c_rot": {"geometry": 1.0}},
    )
    attempt = _answer_failing_the_definition(vault, repository)
    live = _uncertainty_rows(repository)
    belief = _canonical_belief(repository)
    assert [row[1] for row in live] == ["recall"]
    assert live[0][5] == attempt.attempt_id

    # The author swaps the item's map after the answer; the contract the answer was graded under keeps the old one.
    _two_facet_item(paths, criterion_facet_weights={"c_def": {"geometry": 1.0}, "c_rot": {"recall": 1.0}})
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW + timedelta(hours=1)))
    rebuild_all_derived_state(vault, repository, clock=FrozenClock(NOW + timedelta(days=1)))

    assert _canonical_belief(repository) == belief  # the belief follows the frozen contract
    assert _uncertainty_rows(repository) == live  # and so does the uncertainty: replay equals live


def test_s1_explicit_criterion_targets_place_the_uncertainty_without_an_items_map(tmp_path):
    paths, vault, repository = _two_facet_vault(
        tmp_path / "vault", targets={"c_def": "recall", "c_rot": "geometry"},
    )
    attempt = _answer_failing_the_definition(vault, repository)
    live = _uncertainty_rows(repository)

    assert [row[1] for row in live] == ["recall"]
    assert live[0][5] == attempt.attempt_id and live[0][8] == TAG
    rebuild_all_derived_state(vault, repository, clock=FrozenClock(NOW + timedelta(days=1)))
    assert _uncertainty_rows(repository) == live


def test_s1_with_the_switch_off_the_two_criterion_answer_is_the_predecessors(tmp_path):
    from tests.helpers import set_algorithm_version

    _paths, off_vault, off_repository = _two_facet_vault(
        tmp_path / "off", belief_fixes=False, criterion_facet_weights={"c_def": {"recall": 1.0}, "c_rot": {"geometry": 1.0}},
    )
    old_paths = create_basic_vault(tmp_path / "old")
    set_algorithm_version(old_paths, "mvp-0.58")
    write_facets(old_paths, [
        {"id": "recall", "kind": "definition", "claim": "Recall the SVD definition."},
        {"id": "geometry", "kind": "definition", "claim": "SVD as rotate, scale, rotate."},
    ])
    _two_facet_item(old_paths, criterion_facet_weights={"c_def": {"recall": 1.0}, "c_rot": {"geometry": 1.0}})
    old_vault = load_vault(old_paths.root)
    old_repository = Repository(old_paths.sqlite_path)
    sync_vault_state(old_vault, old_repository, clock=FrozenClock(NOW))

    _answer_failing_the_definition(off_vault, off_repository)
    _answer_failing_the_definition(old_vault, old_repository)

    assert _uncertainty_rows(off_repository) == _uncertainty_rows(old_repository) == []
    assert _canonical_belief(off_repository) == _canonical_belief(old_repository)


# -- S2: with the switch off, nothing reads a row the successor stored. ----------------------------------------------

BASIC_ITEM = "pi_svd_define_001"


def _uncertainty_opened_then(tmp_path, *, switch_after: bool):
    """Two don't-knows at the tag open the uncertainty on ``recall``; then the switch is set to ``switch_after``."""

    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    for offset in (0, 1):
        complete_self_graded_attempt(
            vault, repository,
            AttemptDraft(BASIC_ITEM, "I do not know", attempt_type="dont_know"),
            SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
            clock=FrozenClock(NOW + timedelta(minutes=offset)),
        )
    assert [row[1] for row in _uncertainty_rows(repository)] == ["recall"]
    set_config_switch(paths.root, SWITCH, switch_after)
    return paths, load_vault(paths.root), repository


def _reads(vault, repository):
    """What each reader outside the diagnostic layer makes of the stored row."""

    from learnloop.attempts.attempts import load_attempt_prior_state
    from learnloop.instructional.reader_followups import open_questions
    from learnloop.instructional.valuation import facet_problem, open_hypotheses

    problem, _missing = facet_problem(vault, repository, LO_ID, "recall")
    problems, _unavailable = open_hypotheses(vault, repository, facet_ids=["recall"], learning_object_ids=[LO_ID])
    questions, _notes = open_questions(
        vault, repository, {"facets_touched": ["recall"], "learning_objects_touched": [LO_ID]}, now=NOW,
    )
    prior = load_attempt_prior_state(
        vault, repository, learning_object_id=LO_ID, practice_item_id=BASIC_ITEM, facets=["recall"], now_iso=NOW_ISO,
    )
    return {
        "facet_problem": problem is not None,
        "open_hypotheses": sorted(p.space_kind for p in problems),
        "open_questions": sorted(
            raised["source"] for q in questions for raised in q.raised_by if raised.get("source") == "facet_marginal"
        ),
        "attempt_prior": prior.facet_uncertainty.get("recall") is not None,
    }


def test_s2_with_the_switch_off_no_reader_sees_the_successors_rows(tmp_path):
    from tests.helpers import set_algorithm_version

    _paths, vault, repository = _uncertainty_opened_then(tmp_path / "off", switch_after=False)
    old = create_basic_vault(tmp_path / "old")
    set_algorithm_version(old, "mvp-0.58")
    old_vault = load_vault(old.root)
    old_repository = Repository(old.sqlite_path)
    sync_vault_state(old_vault, old_repository, clock=FrozenClock(NOW))
    for offset in (0, 1):
        complete_self_graded_attempt(
            old_vault, old_repository,
            AttemptDraft(BASIC_ITEM, "I do not know", attempt_type="dont_know"),
            SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
            clock=FrozenClock(NOW + timedelta(minutes=offset)),
        )

    assert _reads(vault, repository) == _reads(old_vault, old_repository) == {
        "facet_problem": False, "open_hypotheses": ["hypothesis_set"], "open_questions": [], "attempt_prior": False,
    }


def test_s2_with_the_switch_on_the_readers_see_the_row(tmp_path):
    _paths, vault, repository = _uncertainty_opened_then(tmp_path, switch_after=True)

    assert _reads(vault, repository) == {
        "facet_problem": True, "open_hypotheses": ["facet_marginal", "hypothesis_set"],
        "open_questions": ["facet_marginal"], "attempt_prior": True,
    }


@pytest.mark.parametrize("switch_after", [False, True])
def test_s2_tutor_promotion_features_snapshot_the_uncertainty_only_with_the_switch_on(tmp_path, switch_after):
    from learnloop.tutor.ai_contracts import PromotionAnalysis
    from learnloop.tutor.promotions import promote_tutor_question

    from tests.tutor_promotion_service_helpers import _AnalysisClient, _insert_event

    paths, _vault, repository = _uncertainty_opened_then(tmp_path, switch_after=switch_after)
    _insert_event(repository, "ev_snapshot")
    client = _AnalysisClient(PromotionAnalysis(attributed_facets=["recall"], covered_by_practice_item_id=BASIC_ITEM))
    promote_tutor_question(paths.root, client, event_id="ev_snapshot", intent="practice")

    features = repository.decision_features(decision_id="ev_snapshot", decision_type="question_promotion")
    snapshot = features["ability_vector"]["facet_uncertainty_snapshot"]
    assert (set(snapshot) == {"recall"}) if switch_after else (snapshot == {})


def test_s2_only_the_facet_state_reader_reads_the_uncertainty_rows():
    """Every read of a stored row goes through ``learner.facet_state_reader``, which honours the switch; the
    repository defines the queries, replay clears the table and the shadow rebuild compares it."""

    import re
    from pathlib import Path

    import learnloop

    allowed = {
        "learnloop/learner/facet_state_reader.py", "learnloop/db/repositories.py",
        "learnloop/substrate/rebuild_orchestrator.py", "learnloop/substrate/shadow_rebuild.py",
    }
    pattern = re.compile(r"\.facet_uncertainty_states?\(|FROM\s+facet_uncertainty\b")
    root = Path(learnloop.__file__).parent.parent
    readers = sorted(
        path.relative_to(root).as_posix()
        for package in ("learnloop", "learnloop_sidecar", "learnloop_mcp", "learnloop_mobile")
        for path in (root / package).rglob("*.py")
        if pattern.search(path.read_text(encoding="utf-8"))
    )
    assert "learnloop/learner/facet_state_reader.py" in readers
    assert [path for path in readers if path not in allowed] == []


# -- S3: a row read or written under another facet id names that id in its hypotheses. -------------------------------


def _solid_recall_row(tmp_path):
    """The basic vault's row on ``recall``, settled solid (the posterior a run of successes leaves)."""

    paths, _vault, repository = _uncertainty_opened_then(tmp_path, switch_after=True)
    with repository.connection() as connection:
        connection.execute(
            "UPDATE facet_uncertainty SET hypothesis_marginal = ?, uncertainty = 0.05, status = 'resolved'",
            ('{"facet_absent:recall":0.01,"facet_solid:recall":0.99}',),
        )
        connection.commit()
    return paths, repository


def _alias_recall_to(paths, survivor):
    write_facets(paths, [
        {"id": survivor, "kind": "definition", "claim": "Recall the SVD definition.", "aliases": ["recall"]},
    ])
    return load_vault(paths.root)


def test_s3_a_row_read_under_its_facets_new_id_keeps_its_solid_reading(tmp_path):
    from learnloop.learner.facet_diagnostics import facet_state_label
    from learnloop.learner.facet_state_reader import facet_uncertainty_states_for_lo

    paths, repository = _solid_recall_row(tmp_path)
    vault = _alias_recall_to(paths, "recall_v2")

    (state,) = facet_uncertainty_states_for_lo(vault, repository, LO_ID)
    assert state.facet_id == "recall_v2"
    assert set(state.hypothesis_marginal) == {"facet_solid:recall_v2", "facet_absent:recall_v2"}
    assert facet_state_label("recall_v2", state, None, 0.5) != "known_gap"


def test_s3_a_row_written_under_the_merge_survivor_names_the_survivor(tmp_path):
    paths, vault, repository = _uncertainty_opened_then(tmp_path, switch_after=True)
    repository.insert_facet_merge(retired_facet_id="recall", surviving_facet_id="recall_v2", clock=FrozenClock(NOW))
    complete_self_graded_attempt(
        vault, repository,
        AttemptDraft(BASIC_ITEM, "I do not know", attempt_type="dont_know"),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
        clock=FrozenClock(NOW + timedelta(minutes=3)),
    )

    survivor = repository.facet_uncertainty_state(LO_ID, "recall_v2")
    assert survivor is not None
    facet_labels = {label for label in survivor.hypothesis_marginal if label.startswith("facet_")}
    assert facet_labels == {"facet_solid:recall_v2", "facet_absent:recall_v2"}


def test_s3_after_an_alias_the_next_answer_updates_the_row_it_had_and_a_rebuild_agrees(tmp_path):
    from learnloop.learner.facet_state_reader import facet_uncertainty_states_for_lo

    paths, _vault, repository = _uncertainty_opened_then(tmp_path, switch_after=True)
    first_opener = _uncertainty_rows(repository)[0][5]
    vault = _alias_recall_to(paths, "recall_v2")
    sync_vault_state(vault, repository, clock=FrozenClock(NOW + timedelta(minutes=2)))
    complete_self_graded_attempt(
        vault, repository,
        AttemptDraft(BASIC_ITEM, "SVD factors a matrix as U Sigma V transpose."),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
        clock=FrozenClock(NOW + timedelta(minutes=3)),
    )

    def read():
        return [
            (s.facet_id, s.hypothesis_marginal, s.uncertainty, s.status, s.opened_by_attempt_id, s.opened_reason,
             s.last_evidence_at)
            for s in facet_uncertainty_states_for_lo(vault, repository, LO_ID)
        ]

    live = read()
    assert [entry[0] for entry in live] == ["recall_v2"]
    # The chain continued from the row the facet had under its old id, through this answer.
    assert live[0][4] == first_opener and live[0][6] == "2026-05-19T12:03:00Z"
    rebuild_all_derived_state(vault, repository, clock=FrozenClock(NOW + timedelta(days=1)))
    assert read() == live
