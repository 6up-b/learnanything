"""P0.2 grader channel: coarse schemas, calibration models, grade-resolution
pipeline, dual-write, and calibration streams (spec_p0_measurement_correctness
§3.1-§3.3, §4.1, §4.4, §4.7, §9.1)."""

from __future__ import annotations

import json

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.services import grader_calibration as gc
from learnloop.services.attempts import (
    AttemptDraft,
    SelfGradeInput,
    complete_self_graded_attempt,
)
from learnloop.services.calibration_streams import (
    build_bootstrap_frame,
    record_error_intake_sample,
)
from learnloop.services.grade_classifier import (
    SchemaShape,
    bucket_confidence,
    classify_response,
    exact_word_count,
    length_bucket,
)
from learnloop.services.grade_resolution import (
    append_adjudication,
    quarantine_observation,
    record_grade_dual_write,
    resolve_grade,
)
from learnloop.services.grader_calibration import (
    ModelPromotionError,
    ResolvedModel,
    denominator_counts_from_samples,
    heuristic_alphas,
    validate_promotion,
)
from learnloop.services.outcome_schemas import (
    COARSE_RESPONSE_SLUG,
    COARSE_RESPONSE_UNANSWERED_SLUG,
    ensure_builtin_schemas,
)
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault

CLOCK = FrozenClock(NOW)
ITEM = "pi_svd_define_001"


@pytest.fixture
def env(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    repo = Repository(paths.sqlite_path)
    sync_vault_state(vault, repo, clock=CLOCK)
    return vault, repo


# ---------------------------------------------------------------------------
# Migration 066
# ---------------------------------------------------------------------------

def test_migration_066_created_tables_and_indices(env):
    _, repo = env
    with connect(repo.sqlite_path) as connection:
        tables = {
            r["name"] for r in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
    for expected in (
        "outcome_schemas",
        "outcome_schema_versions",
        "grader_calibration_models",
        "grader_calibration_alphas",
        "raw_grade_events",
        "grade_interpretations",
        "grade_adjudications",
        "calibration_stream_samples",
    ):
        assert expected in tables


# ---------------------------------------------------------------------------
# Seeds + buckets
# ---------------------------------------------------------------------------

def test_builtin_schemas_and_heuristic_priors_are_idempotent(env):
    _, repo = env
    ensure_builtin_schemas(repo, clock=CLOCK)
    gc.seed_heuristic_priors(repo, clock=CLOCK)
    n1 = len(repo.find_calibration_models())
    gc.seed_heuristic_priors(repo, clock=CLOCK)
    ensure_builtin_schemas(repo, clock=CLOCK)
    assert len(repo.find_calibration_models()) == n1
    # global prior per response schema + two identity priors each.
    assert n1 == 9


def test_confidence_buckets_at_040_and_080():
    assert bucket_confidence(None) == "unknown"
    assert bucket_confidence(0.39) == "low"
    assert bucket_confidence(0.40) == "medium"
    assert bucket_confidence(0.79) == "medium"
    assert bucket_confidence(0.80) == "high"
    assert bucket_confidence(1.0) == "high"


def test_length_buckets():
    assert length_bucket(0) == "0"
    assert length_bucket(1) == "1-50"
    assert length_bucket(50) == "1-50"
    assert length_bucket(51) == "51-200"
    assert length_bucket(200) == "51-200"
    assert length_bucket(201) == "201+"
    assert exact_word_count("one two three") == 3
    assert exact_word_count("") == 0


# ---------------------------------------------------------------------------
# Classifier (§3.1)
# ---------------------------------------------------------------------------

_COARSE = SchemaShape(observed_classes=("success", "partial_success", "other"))
_UNANS = SchemaShape(
    observed_classes=("success", "partial_success", "other", "unanswered"),
    has_unanswered=True,
)


def test_classifier_maps_score_boundaries():
    assert classify_response(rubric_score=4, max_points=4, schema=_COARSE).observed_class == "success"
    assert classify_response(rubric_score=2, max_points=4, schema=_COARSE).observed_class == "partial_success"
    assert classify_response(rubric_score=0, max_points=4, schema=_COARSE).observed_class == "other"
    # Fatal error demotes a full score away from success.
    assert classify_response(rubric_score=4, max_points=4, schema=_COARSE, has_fatal=True).observed_class != "success"


def test_classifier_unclassifiable_maps_to_other_plus_flag():
    result = classify_response(rubric_score=None, max_points=4, schema=_COARSE, malformed=True)
    assert result.observed_class == "other"
    assert result.unclassifiable is True


def test_classifier_unanswered_only_when_schema_has_class():
    result = classify_response(
        rubric_score=0, max_points=4, schema=_UNANS, response_empty=True
    )
    assert result.observed_class == "unanswered"
    # Without the class, an empty response falls to other, never silent success.
    result2 = classify_response(
        rubric_score=0, max_points=4, schema=_COARSE, response_empty=True
    )
    assert result2.observed_class == "other"


# ---------------------------------------------------------------------------
# Asymmetric planted channel (§9.1 bullet 1)
# ---------------------------------------------------------------------------

def _resolved_from_alpha(alpha):
    classes = tuple(sorted(alpha))
    observed = tuple(sorted({e.split("|", 1)[0] for r in alpha.values() for e in r}))
    return ResolvedModel(
        model_id="m",
        model_hash="h_planted",
        joint_alpha=alpha,
        true_classes=classes,
        observed_classes=observed,
        contributing_model_ids=["m"],
        parent_contribution_share=0.0,
    )


def test_asymmetric_planted_channel_produces_nonsymmetric_matrix_and_direction():
    classes = ("success", "partial_success", "other")
    # Symmetric baseline.
    sym = _resolved_from_alpha(
        heuristic_alphas(true_classes=classes, observed_classes=classes, reliability=0.8)
    )
    # Planted: Z=partial_success is over-called as G=success.
    alpha = heuristic_alphas(true_classes=classes, observed_classes=classes, reliability=0.8)
    for bucket in ("unknown", "low", "medium", "high"):
        alpha["partial_success"][f"success|{bucket}"] += 6.0
    asym = _resolved_from_alpha(alpha)

    marg = asym.marginal_confusion()
    # Non-symmetric: over-calling partial->success is NOT matched by success->partial.
    assert marg["partial_success"]["success"] > marg["success"]["partial_success"]

    post_sym = gc.posterior_over_true_class(sym, observed_class="success", confidence_bucket="high")
    post_asym = gc.posterior_over_true_class(asym, observed_class="success", confidence_bucket="high")
    # Observing success now leaves MORE room for true partial_success than symmetric.
    assert post_asym["partial_success"] > post_sym["partial_success"]


# ---------------------------------------------------------------------------
# Raw confidence never multiplied; only bucket may matter (§9.1 bullet 4)
# ---------------------------------------------------------------------------

def test_raw_confidence_only_affects_interpretation_through_bucket():
    classes = ("success", "partial_success", "other")
    # A model whose confidence columns differ across Z (so bucket CAN matter).
    alpha = heuristic_alphas(true_classes=classes, observed_classes=classes, reliability=0.8)
    alpha["success"]["success|high"] += 5.0  # high-confidence success is more diagnostic
    resolved = _resolved_from_alpha(alpha)

    # Two raw confidences in the SAME bucket (both 'high') -> identical posterior.
    b1 = bucket_confidence(0.81)
    b2 = bucket_confidence(0.99)
    assert b1 == b2 == "high"
    p1 = gc.posterior_over_true_class(resolved, observed_class="success", confidence_bucket=b1)
    p2 = gc.posterior_over_true_class(resolved, observed_class="success", confidence_bucket=b2)
    assert p1 == p2
    # Crossing a bucket boundary CAN differ.
    p_med = gc.posterior_over_true_class(resolved, observed_class="success", confidence_bucket="medium")
    assert p_med != p1


# ---------------------------------------------------------------------------
# Model resolution + fallback (§3.2, §4.1)
# ---------------------------------------------------------------------------

def test_resolution_seeds_and_missing_child_inherits_parent(env):
    _, repo = env
    row = repo.fetch_outcome_schema_version(slug=COARSE_RESPONSE_SLUG)
    if row is None:
        ensure_builtin_schemas(repo, clock=CLOCK)
        row = repo.fetch_outcome_schema_version(slug=COARSE_RESPONSE_SLUG)
    resolved = gc.resolve_calibration_model(
        repo,
        grader_identity_hash=None,
        outcome_schema_id=row["schema_id"],
        outcome_schema_version=int(row["version"]),
        clock=CLOCK,
    )
    assert resolved.fallback_reason is None
    assert set(resolved.true_classes) == {"success", "partial_success", "other"}
    # L9: with no grader-identity child, the resolved model IS the global prior --
    # its pooled joint_alpha equals the global model's alpha exactly and the parent
    # contributes 100% of the mass.
    globals_ = repo.find_calibration_models(
        scope_level="global",
        outcome_schema_id=row["schema_id"],
        outcome_schema_version=int(row["version"]),
    )
    assert len(globals_) == 1
    global_alpha = repo.fetch_calibration_alphas(globals_[0]["id"])
    assert resolved.joint_alpha == global_alpha
    assert resolved.parent_contribution_share == pytest.approx(1.0)


def test_resolution_global_fallback_never_crashes(env):
    _, repo = env
    # An outcome schema id/version that has no seeded model.
    resolved = gc.resolve_calibration_model(
        repo,
        grader_identity_hash=None,
        outcome_schema_id="nonexistent_schema",
        outcome_schema_version=99,
        clock=CLOCK,
    )
    assert resolved.fallback_reason == "no_scoped_model_global_prior"
    # Still yields a usable posterior (wide), never the old 0.90 point channel.
    post = gc.posterior_over_true_class(resolved, observed_class="success", confidence_bucket="high")
    assert pytest.approx(sum(post.values()), abs=1e-9) == 1.0


# ---------------------------------------------------------------------------
# Same-grader agreement vs adjudicated anchors (§9.1 bullet 5)
# ---------------------------------------------------------------------------

def test_same_grader_agreement_does_not_narrow_but_adjudication_does(env):
    vault, repo = env
    item = vault.practice_items[ITEM]
    primary = resolve_grade(
        vault, repo, item=item, purpose="practice", grading_source="codex",
        attempt_id="att_p1", response_text="an answer here", rubric_score=4,
        max_points=4, grader_confidence=0.7, clock=CLOCK,
    )
    primary_width = json.loads(
        repo.grade_interpretation(primary.interpretation_id)["credible_interval_json"]
    )["width"]

    # A second same-grader recheck on the SAME observation: another interpretation,
    # same model -> interval width unchanged (agreement does not narrow).
    primary_obs = repo.observation_by_attempt("att_p1")
    recheck = resolve_grade(
        vault, repo, item=item, purpose="practice", grading_source="codex",
        attempt_id="att_p1", response_text="an answer here", rubric_score=4,
        max_points=4, grader_confidence=0.7, role="recheck",
        administration_id=primary.administration_id,
        observation_id=primary.observation_id,
        surface_id=primary_obs["surface_id"],
        clock=CLOCK,
    )
    recheck_width = json.loads(
        repo.grade_interpretation(recheck.interpretation_id)["credible_interval_json"]
    )["width"]
    assert recheck_width == pytest.approx(primary_width)

    # An adjudicated anchor (deterministic key) narrows to a point.
    result = append_adjudication(
        repo,
        observation_id=primary.observation_id,
        administration_id=primary.administration_id,
        reviewed_raw_event_ids=[primary.raw_grade_event_id],
        adjudicator_source="deterministic_key",
        resolved_class="success",
        clock=CLOCK,
    )
    adj_width = json.loads(
        repo.grade_interpretation(result["interpretation_id"])["credible_interval_json"]
    )["width"]
    assert adj_width < primary_width
    # The observation head now points at the adjudicated interpretation.
    head = repo.active_interpretation_for_observation(primary.observation_id)
    assert head["id"] == result["interpretation_id"]


def test_signature_error_reachable_when_signature_matched_threaded(env):
    """L5 (§3.1/§4.1): resolve_grade threads signature_matched into the classifier,
    so a partial grade on a signature-error schema whose card-declared misconception
    matched resolves to the ``signature_error`` observed class -- previously
    unreachable because resolve_grade never passed the flag."""

    from learnloop.services.outcome_schemas import SIGNATURE_ERROR_SLUG, ensure_builtin_schemas

    vault, repo = env
    ensure_builtin_schemas(repo, clock=CLOCK)
    item = vault.practice_items[ITEM]

    matched = resolve_grade(
        vault, repo, item=item, purpose="practice", grading_source="codex",
        attempt_id="att_sig1", response_text="partial with the classic misconception",
        rubric_score=2, max_points=4, grader_confidence=0.6,
        outcome_schema_slug=SIGNATURE_ERROR_SLUG, signature_matched=True, clock=CLOCK,
    )
    assert matched.observed_class == "signature_error"

    unmatched = resolve_grade(
        vault, repo, item=item, purpose="practice", grading_source="codex",
        attempt_id="att_sig2", response_text="partial but not the declared error",
        rubric_score=2, max_points=4, grader_confidence=0.6,
        outcome_schema_slug=SIGNATURE_ERROR_SLUG, signature_matched=False, clock=CLOCK,
    )
    assert unmatched.observed_class == "other"


def test_insert_calibration_model_is_content_addressed_no_duplicate(env):
    """M1 (§3.2): insert_calibration_model short-circuits on an existing
    content_hash, and the UNIQUE(content_hash) backstop (migration 070) hard-blocks
    a duplicate immutable model from a check-then-act race."""

    from learnloop.services.outcome_schemas import ensure_builtin_schemas

    _vault, repo = env
    ensure_builtin_schemas(repo, clock=CLOCK)
    version_row = repo.fetch_outcome_schema_version(slug=COARSE_RESPONSE_SLUG)
    schema_id = version_row["schema_id"]
    alphas = {"success": {"success|high": 2.0}, "other": {"other|high": 2.0}}
    model = {
        "semver": "0.1.0", "content_hash": "dup-hash-xyz", "scope_level": "global",
        "outcome_schema_id": schema_id, "outcome_schema_version": int(version_row["version"]),
        "backoff_chain_json": "[]", "status": "heuristic",
    }
    first = repo.insert_calibration_model(model=model, alphas=alphas, clock=CLOCK)
    second = repo.insert_calibration_model(model=model, alphas=alphas, clock=CLOCK)
    assert first == second  # short-circuit adopts the existing row
    with connect(repo.sqlite_path) as connection:
        count = connection.execute(
            "SELECT COUNT(*) c FROM grader_calibration_models WHERE content_hash='dup-hash-xyz'"
        ).fetchone()["c"]
    assert count == 1


def test_adjudication_distribution_respects_bounded_trust_and_authority(env):
    """M4 (§4.4): a resolved_distribution adjudication must be blended by the
    bounded-trust weight, not adopted verbatim. A learner_clarification (trust 0.5)
    is pulled toward the prior head; an owner (trust 1.0) adopts the distribution
    outright and carries strictly greater authority.

    Before the fix the resolved_distribution branch used the distribution verbatim,
    so a bounded-trust learner clarification carried full owner authority."""

    vault, repo = env
    item = vault.practice_items[ITEM]

    def _fresh(attempt_id):
        return resolve_grade(
            vault, repo, item=item, purpose="practice", grading_source="codex",
            attempt_id=attempt_id, response_text="an answer here", rubric_score=2,
            max_points=4, grader_confidence=0.5, clock=CLOCK,
        )

    dist = {"success": 0.9, "partial_success": 0.1, "other": 0.0}

    learner = _fresh("att_m4a")
    base = json.loads(repo.grade_interpretation(learner.interpretation_id)["response_posterior_json"])
    learner_adj = append_adjudication(
        repo, observation_id=learner.observation_id,
        administration_id=learner.administration_id,
        reviewed_raw_event_ids=[learner.raw_grade_event_id],
        adjudicator_source="learner_clarification", resolved_distribution=dist,
        clock=CLOCK,
    )
    learner_post = json.loads(
        repo.grade_interpretation(learner_adj["interpretation_id"])["response_posterior_json"]
    )
    # Blended, NOT verbatim: pulled back toward the prior head (0.5 trust).
    assert learner_post["success"] == pytest.approx(0.5 * 0.9 + 0.5 * base.get("success", 0.0))
    assert learner_post["success"] < 0.9

    owner = _fresh("att_m4b")
    owner_adj = append_adjudication(
        repo, observation_id=owner.observation_id,
        administration_id=owner.administration_id,
        reviewed_raw_event_ids=[owner.raw_grade_event_id],
        adjudicator_source="human_owner", resolved_distribution=dist, clock=CLOCK,
    )
    owner_post = json.loads(
        repo.grade_interpretation(owner_adj["interpretation_id"])["response_posterior_json"]
    )
    # Full trust adopts the distribution outright (authority ordering: owner wins).
    assert owner_post["success"] == pytest.approx(0.9)
    assert owner_post["success"] > learner_post["success"]


def test_adjudication_clamps_out_of_range_trust(env):
    """M4 (audit F4): a caller-supplied trust > 1 cannot grant more-than-full
    authority; it clamps to a point adjudication."""

    vault, repo = env
    item = vault.practice_items[ITEM]
    res = resolve_grade(
        vault, repo, item=item, purpose="practice", grading_source="codex",
        attempt_id="att_m4c", response_text="x", rubric_score=2, max_points=4,
        grader_confidence=0.5, clock=CLOCK,
    )
    adj = append_adjudication(
        repo, observation_id=res.observation_id, administration_id=res.administration_id,
        reviewed_raw_event_ids=[res.raw_grade_event_id], adjudicator_source="human_owner",
        resolved_class="success", bounded_trust_weight=1.5, clock=CLOCK,
    )
    row = repo.grade_interpretation(adj["interpretation_id"])
    post = json.loads(row["response_posterior_json"])
    assert post["success"] == pytest.approx(1.0)  # clamped to a point mass
    assert row["certainty_discount"] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Promotion + denominator rules (§9.1 bullets 6-7)
# ---------------------------------------------------------------------------

def test_exploratory_em_cannot_promote_to_live_calibrated():
    model = {
        "count_exploratory_em": 40,
        "count_adjudicated_anchor": 0,
        "count_held_out_evaluation": 0,
        "evidence_manifest_json": None,
    }
    with pytest.raises(ModelPromotionError):
        validate_promotion(model, to_status="live_calibrated")
    # A manifest with anchors + held-out passes.
    ok = {
        "count_exploratory_em": 40,
        "count_adjudicated_anchor": 5,
        "count_held_out_evaluation": 20,
        "evidence_manifest_json": json.dumps({"scope": "global"}),
    }
    validate_promotion(ok, to_status="live_calibrated")


def test_confusion_updates_only_from_denominator_bearing_sources(env):
    _, repo = env
    error = record_error_intake_sample(
        repo, observation_id=None, administration_id=None, raw_grade_event_id=None
    )
    samples = repo.calibration_stream_samples(stream="error_intake")
    # MNAR error-intake alone contributes NOTHING to a confusion denominator.
    assert denominator_counts_from_samples(samples) == {}
    # A calibration sample DOES contribute.
    repo.insert_calibration_stream_sample(
        values={
            "stream": "calibration",
            "stratum_json": "{}",
            "inclusion_probability": 0.25,
            "selected": True,
        }
    )
    both = repo.calibration_stream_samples()
    counts = denominator_counts_from_samples(both)
    assert counts.get("calibration", 0) == pytest.approx(4.0)  # 1/0.25 IPW
    assert "error_intake" not in counts


# ---------------------------------------------------------------------------
# Dual-write from the real entry points (§9.1 dual-write)
# ---------------------------------------------------------------------------

def test_practice_attempt_dual_writes_raw_event_and_interpretation(env):
    vault, repo = env
    result = complete_self_graded_attempt(
        vault,
        repo,
        AttemptDraft(
            practice_item_id=ITEM,
            learner_answer_md="SVD is U Sigma V transpose.",
            attempt_type="independent_attempt",
        ),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
        clock=CLOCK,
    )
    # Legacy summary is unchanged (byte-identical expectation).
    attempt = repo.fetch_practice_attempt(result.attempt_id)
    assert attempt["rubric_score"] == 4

    observation = repo.observation_by_attempt(result.attempt_id)
    assert observation is not None
    raw = repo.raw_grade_events_for_observation(observation["id"])
    assert len(raw) == 1
    assert raw[0]["attempt_id"] == result.attempt_id
    assert raw[0]["observed_class"] == "success"
    head = repo.active_interpretation_for_observation(observation["id"])
    assert head is not None
    assert head["raw_grade_event_id"] == raw[0]["id"]
    post = json.loads(head["response_posterior_json"])
    assert pytest.approx(sum(post.values()), abs=1e-9) == 1.0


def test_exam_answer_dual_writes_assessment_grade(tmp_path):
    from learnloop.services.attempts import ResolvedGrade
    from learnloop.services.exam_pool import reserve_exam_pool
    from learnloop.services.exam_session import record_exam_answer, start_exam
    from learnloop.vault.writer import upsert_practice_item
    from tests.helpers import NOW_ISO, create_basic_vault, seed_due_item

    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    upsert_practice_item(
        vault_root,
        {
            "id": "pi_exam_a",
            "learning_object_id": "lo_svd_definition",
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt", "dont_know"],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": "Prompt exam a.",
            "expected_answer": "Answer.",
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "Correct."}],
                "fatal_errors": [],
            },
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
        clock=CLOCK,
    )
    repo = seed_due_item(paths)
    vault = load_vault(vault_root)
    reserve_exam_pool(vault, repo, vault.goals[0], item_count=1, clock=CLOCK)
    session = start_exam(vault, repo, "goal_linear_algebra_ml", clock=CLOCK)
    item_id = session["item_order"][0]
    grade = ResolvedGrade(
        rubric_score=4, criterion_points={"correctness": 4.0}, evidence_rows=[],
        error_attributions=[], grader_confidence=0.9, confidence=4, manual_review_reason=None,
    )
    record_exam_answer(
        vault, repo, session["session_id"], item_id, answer_md="my exam answer", resolved_grade=grade,
        clock=CLOCK,
    )
    observation = repo.observation_by_attempt(f"exam::{session['session_id']}::{item_id}")
    assert observation is not None
    raw = repo.raw_grade_events_for_observation(observation["id"])
    assert len(raw) == 1
    assert raw[0]["observed_class"] == "success"
    assert repo.active_interpretation_for_observation(observation["id"]) is not None


def test_probe_dual_write_helper_records_diagnostic_grade(env):
    from learnloop.services.probe_episodes import _dual_write_probe_grade

    vault, repo = env
    # Seed a bare practice_attempts row (as the probe submission path would have).
    with connect(repo.sqlite_path) as connection:
        connection.execute(
            """
            INSERT INTO practice_attempts(
              id, practice_item_id, learning_object_id, practice_mode, attempt_type,
              learner_answer_md, rubric_score, grader_confidence, hints_used, created_at
            ) VALUES ('att_probe', ?, 'lo_svd_definition', 'short_answer',
                      'diagnostic_probe', 'a probe answer', 4, 0.9, 0, '2026-05-19T12:00:00Z')
            """,
            (ITEM,),
        )
        connection.commit()
    _dual_write_probe_grade(
        vault, repo, practice_item_id=ITEM, attempt_id="att_probe",
        grading_source="ai", observed_outcome="correct", clock=CLOCK,
    )
    observation = repo.observation_by_attempt("att_probe")
    assert observation is not None
    raw = repo.raw_grade_events_for_observation(observation["id"])
    assert len(raw) == 1
    assert raw[0]["grader_provider"] == "ai"
    assert repo.active_interpretation_for_observation(observation["id"]) is not None


def test_dual_write_failure_never_breaks_legacy_path(env, monkeypatch):
    """L9 (§7.3): a REAL legacy self-graded attempt whose P0.2 resolve step is
    poisoned mid-flight still persists its legacy attempt row + mastery; only the
    dual-write channel is degraded (swallowed), never the learner's record.

    Since the audit-B2 fix, identity is minted BEFORE resolution: the failure
    leaves a visible anchor (administration + observation, zero interpretations)
    plus a degradation measurement event -- recoverable debt, never a silent
    no-op."""

    vault, repo = env

    import learnloop.services.grade_resolution as gr

    def _poison(*_args, **_kwargs):
        raise RuntimeError("poisoned resolve step")

    monkeypatch.setattr(gr, "resolve_grade", _poison)

    result = complete_self_graded_attempt(
        vault, repo,
        AttemptDraft(
            practice_item_id=ITEM,
            learner_answer_md="a real legacy answer",
            attempt_type="independent_attempt",
        ),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=3),
        clock=CLOCK,
    )
    # The legacy attempt row survives the poisoned dual-write.
    legacy = repo.fetch_practice_attempt(result.attempt_id)
    assert legacy is not None
    # Identity was minted first, so the failure has a persisted anchor: an
    # observation with NO interpretation (zero authority) ...
    observation = repo.observation_by_attempt(result.attempt_id)
    assert observation is not None
    assert repo.active_interpretation_for_observation(observation["id"]) is None
    # ... and the degradation is recorded on its administration, never swallowed
    # invisibly (audit B2).
    events = repo.measurement_events_for_administration(observation["administration_id"])
    degradations = [
        e for e in events
        if json.loads(e["payload_json"] or "{}").get("dual_write_degraded")
    ]
    assert len(degradations) == 1
    assert "poisoned resolve step" in json.loads(degradations[0]["payload_json"])["error"]


def test_dual_write_mint_failure_is_logged_not_silent(env, monkeypatch, caplog):
    """When even the identity mint fails (no anchor exists at all), the
    degradation is logged -- the one remaining no-anchor slice is not silent."""

    vault, repo = env

    import learnloop.services.grade_resolution as gr

    def _poison(*_args, **_kwargs):
        raise RuntimeError("mint failed")

    monkeypatch.setattr(gr, "ensure_administration_identity", _poison)

    import logging

    with caplog.at_level(logging.WARNING, logger="learnloop.services.grade_resolution"):
        result = complete_self_graded_attempt(
            vault, repo,
            AttemptDraft(
                practice_item_id=ITEM,
                learner_answer_md="another legacy answer",
                attempt_type="independent_attempt",
            ),
            SelfGradeInput(criterion_points={"correctness": 4}, confidence=3),
            clock=CLOCK,
        )
    assert repo.fetch_practice_attempt(result.attempt_id) is not None
    assert repo.observation_by_attempt(result.attempt_id) is None
    assert any("dual-write degraded" in rec.message for rec in caplog.records)


# ---------------------------------------------------------------------------
# Bootstrap frame (§4.7)
# ---------------------------------------------------------------------------

def test_bootstrap_frame_logs_inclusion_probabilities_and_is_deterministic(env):
    vault, repo = env
    for i in range(6):
        complete_self_graded_attempt(
            vault,
            repo,
            AttemptDraft(
                practice_item_id=ITEM,
                learner_answer_md=f"answer {i}",
                attempt_type="independent_attempt",
            ),
            SelfGradeInput(criterion_points={"correctness": i % 5}, confidence=3),
            clock=CLOCK,
        )
    frame1 = build_bootstrap_frame(repo, frame_id="frame_fixed")
    for sample in frame1.samples:
        assert sample["inclusion_probability"] > 0
    logged = repo.calibration_stream_samples(sampling_frame_id="frame_fixed")
    assert len(logged) == frame1.selected
    assert all(row["stream"] == "calibration" for row in logged)

    # Same frame id over the same history reproduces the same selection set.
    selected_ids = {s["attempt_id"] for s in frame1.samples}
    frame2 = build_bootstrap_frame(repo, frame_id="frame_repro")
    # Determinism is per (frame_id, attempt) so a fresh id may differ; the SELECTION
    # RULE is reproducible: rebuilding frame_fixed's decision gives the same set.
    from learnloop.services.calibration_streams import should_sample, stratum_for
    from learnloop.services.grade_classifier import bucket_confidence, length_bucket_for_text

    recomputed = set()
    for attempt in repo.list_all_attempts():
        _, lb = length_bucket_for_text(attempt.get("learner_answer_md"))
        stratum = stratum_for(
            confidence_bucket=bucket_confidence(attempt.get("grader_confidence")),
            influence_flag=False,
            partial_boundary=(attempt.get("correctness") or 0) not in (0, 1)
            and 0 < (attempt.get("correctness") or 0) < 1,
            domain=attempt.get("learning_object_id"),
            length_bucket=lb,
        )
        sel, _p = should_sample(stratum, key=attempt["id"], frame_id="frame_fixed")
        if sel:
            recomputed.add(attempt["id"])
    assert recomputed == selected_ids


def test_backfill_converts_probe_presentations_idempotently(env):
    from learnloop.services.activity_backfill import backfill_activity_substrate

    vault, repo = env
    with connect(repo.sqlite_path) as connection:
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute(
            """
            INSERT INTO probe_presentations(
              id, probe_episode_id, practice_item_id, state_segment_id, status,
              served_at, created_at, updated_at
            ) VALUES ('pres_1', 'ep_1', ?, 'seg_1', 'submitted',
                      '2026-05-18T09:00:00Z', '2026-05-18T09:00:00Z', '2026-05-18T09:00:00Z')
            """,
            (ITEM,),
        )
        connection.commit()

    report = backfill_activity_substrate(vault, repo, clock=CLOCK)
    assert report.presentations_replayed == 1
    admin = repo.administration_by_legacy_presentation("pres_1")
    assert admin is not None
    assert admin["purpose"] == "diagnostic"

    # Idempotent: a second run adds no administration for the presentation.
    second = backfill_activity_substrate(vault, repo, clock=CLOCK)
    assert second.presentations_replayed == 0
    assert second.presentations_skipped_existing == 1


def test_quarantine_appends_new_head_without_mutating_prior(env):
    vault, repo = env
    res = resolve_grade(
        vault, repo, item=vault.practice_items[ITEM], purpose="practice",
        grading_source="codex", attempt_id="att_q", response_text="answer",
        rubric_score=4, max_points=4, grader_confidence=0.7, clock=CLOCK,
    )
    before = repo.grade_interpretation(res.interpretation_id)
    new_head = quarantine_observation(
        repo, observation_id=res.observation_id, surface_id=None, reason="learner_contest", clock=CLOCK
    )
    after = repo.grade_interpretation(res.interpretation_id)
    # Prior interpretation row is byte-stable (append-only); a new head is created.
    assert after == before
    head = repo.active_interpretation_for_observation(res.observation_id)
    assert head["id"] == new_head
    assert head["quarantine_state"] == "quarantined"
