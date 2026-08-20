"""ING M8 — provenance-outcome analytics + source_exposure contexts (§11, §9.2).

Report-only associations gated on min samples with visible uncertainty; the new
exposure contexts (tutor_citation, provenance_panel, conflict_review) record; and
the actionable associations flow into the maintenance feed additively.
"""

from __future__ import annotations

from datetime import UTC, datetime

from learnloop.clock import FrozenClock
from learnloop.ops.maintenance_feed import generate_maintenance_feed
from learnloop.content.sources.source_outcome_analytics import analyze_source_outcomes
from learnloop.content.synthesis.source_set_synthesis import create_study_map
from learnloop.reader.span_view import build_span_view
from learnloop.vault.loader import load_vault

from tests.test_source_set_synthesis import FakeSynthesisClient, _setup

_CLOCK = FrozenClock(datetime(2026, 7, 14, 12, 0, 0, tzinfo=UTC))
_LO_ID = "lo_diagonalize_symmetric"


def _mapped(tmp_path):
    root, repo = _setup(tmp_path, with_exam=True)
    create_study_map(root, "set_la", client=FakeSynthesisClient(), repository=repo,
                     clock=_CLOCK, apply=True, brief={"outcome": "exam prep"})
    return root, repo


def _insert_attempt(repo, *, aid, correctness, error_type=None, created_at="2026-07-14T09:00:00Z"):
    with repo.connection() as connection:
        connection.execute(
            """
            INSERT INTO practice_attempts(
              id, practice_item_id, learning_object_id, practice_mode, attempt_type,
              learner_answer_md, hints_used, correctness, error_type, created_at
            )
            VALUES (?, 'pi_identify_symmetry', ?, 'short_answer', 'independent_attempt',
                    'ans', 0, ?, ?, ?)
            """,
            (aid, _LO_ID, correctness, error_type, created_at),
        )
        connection.commit()


def test_new_exposure_contexts_record(tmp_path):
    root, repo = _mapped(tmp_path)
    for ctx in ("tutor_citation", "provenance_panel", "conflict_review"):
        view = build_span_view(repo, "ext_text", "s1", context=ctx,
                               entity_type="facet", entity_id="facet_symmetry_definition",
                               clock=_CLOCK)
        assert view["exposure_event_id"]
    events = repo.source_exposure_events(extraction_id="ext_text", span_id="s1")
    contexts = {e["context"] for e in events}
    assert {"tutor_citation", "provenance_panel", "conflict_review"} <= contexts


def test_repeated_failure_despite_coverage_requires_exposure(tmp_path):
    root, repo = _mapped(tmp_path)
    # Three failing attempts, coverage exists — but NO exposure yet.
    _insert_attempt(repo, aid="a1", correctness=0.1, error_type="misapplication")
    _insert_attempt(repo, aid="a2", correctness=0.2, error_type="misapplication")
    _insert_attempt(repo, aid="a3", correctness=0.0, error_type="misapplication")
    vault = load_vault(root)

    before = analyze_source_outcomes(vault, repo, subject_id="linear-algebra")
    # Coverage exists and the learner failed, but with no exposure the "despite
    # coverage" claim is withheld (§11: coverage alone never proves they saw it).
    assert not any(a.kind == "repeated_failure_despite_coverage" for a in before.associations)

    # Record an exposure: now the "despite coverage" association is claimable.
    build_span_view(repo, "ext_text", "s1", context="provenance_panel",
                    entity_type="learning_object", entity_id=_LO_ID, clock=_CLOCK)
    after = analyze_source_outcomes(vault, repo, subject_id="linear-algebra")
    assoc = next(a for a in after.associations if a.kind == "repeated_failure_despite_coverage")
    assert assoc.counts["failures"] == 3 and assoc.counts["exposures"] >= 1
    assert assoc.suggestion["action"] == "generate_practice"


def test_actionable_associations_flow_into_maintenance_feed(tmp_path):
    root, repo = _mapped(tmp_path)
    _insert_attempt(repo, aid="a1", correctness=0.1, error_type="misapplication")
    _insert_attempt(repo, aid="a2", correctness=0.2, error_type="misapplication")
    _insert_attempt(repo, aid="a3", correctness=0.0, error_type="misapplication")
    build_span_view(repo, "ext_text", "s1", context="provenance_panel",
                    entity_type="learning_object", entity_id=_LO_ID, clock=_CLOCK)
    vault = load_vault(root)
    feed = generate_maintenance_feed(vault, repo, clock=_CLOCK)
    types = {n["notice_type"] for n in feed}
    assert "repeated_failure_despite_coverage" in types
    # positive alternate-exposure association is report-only, never a notice.
    assert "alternate_exposure_preceded_resolution" not in types
