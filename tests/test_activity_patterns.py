"""P1 step 2 -- capability aliases, TaskFeatures, ActivityPattern registry
(spec_p1_shared_substrate §3.3, §3.4, §3.5, §9.1)."""

from __future__ import annotations

from pathlib import Path

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.migrate import apply_migrations
from learnloop.db.repositories import Repository
from learnloop.services import activity_patterns as AP

from tests.helpers import NOW

CLOCK = FrozenClock(NOW)


@pytest.fixture
def repo(tmp_path):
    path = tmp_path / "state.sqlite"
    apply_migrations(path)
    return Repository(path)


def _base(**over):
    fields = {
        "allowed_purposes": ["practice"],
        "operation": "retrieve",
        "learning_process": "memory_fluency",
        "allowed_capabilities": ["retrieval"],
        "completion_semantics": {"kind": "single_response"},
        "response_contract": {"form": "short_constructed"},
        "evidence_semantics_by_context": {"cold": "eligible"},
        "task_feature_bounds": {},
        "variation_axes": {},
        "rubric_shape": {"kind": "binary"},
        "mint_gates": {"gates": []},
        "calibration_status": "heuristic",
    }
    fields.update(over)
    return fields


# --- §3.3 capability alias registry ------------------------------------------

def test_map_capability_identity_alias_and_unmapped(repo):
    AP.ensure_capability_alias_registry(repo, clock=CLOCK)
    assert AP.map_capability(repo, "retrieval") == "retrieval"  # canonical identity
    assert AP.map_capability(repo, "recall") == "retrieval"  # legacy alias
    assert AP.map_capability(repo, "integration") == "coordination"
    assert AP.map_capability(repo, "totally_unknown") == AP.LEGACY_UNMAPPED


def test_normalize_capabilities_folds_synthesis_output(repo):
    AP.ensure_capability_alias_registry(repo, clock=CLOCK)
    # source_set_synthesis emits capability "retrieval" + one "coordination"
    # integration component; both normalize to the closed vocabulary (§3.3).
    assert AP.normalize_capabilities(repo, ["retrieval", "coordination"]) == [
        "retrieval",
        "coordination",
    ]


# --- §9.1 invalid capability fails new authoring -----------------------------

def test_invalid_capability_fails_new_authoring(repo):
    with pytest.raises(AP.InvalidPattern):
        AP.register_pattern_version(
            repo, pattern_slug="bad", fields=_base(allowed_capabilities=["telepathy"]), clock=CLOCK
        )


def test_invalid_operation_and_learning_process_fail(repo):
    with pytest.raises(AP.InvalidPattern):
        AP.register_pattern_version(repo, pattern_slug="op", fields=_base(operation="teleport"), clock=CLOCK)
    with pytest.raises(AP.InvalidPattern):
        AP.register_pattern_version(
            repo, pattern_slug="lp", fields=_base(learning_process="osmosis"), clock=CLOCK
        )


# --- §9.1 coordination only via integration component ------------------------

def test_coordination_requires_integration_component(repo):
    with pytest.raises(AP.InvalidCoordinationUse):
        AP.register_pattern_version(
            repo, pattern_slug="c1", fields=_base(allowed_capabilities=["coordination"]), clock=CLOCK
        )
    # Valid only when the pattern is a whole-task integration component (§3.3).
    ok = AP.register_pattern_version(
        repo,
        pattern_slug="whole_task",
        fields=_base(
            operation="create",
            learning_process="coordination",
            allowed_capabilities=["coordination"],
            integration_component=True,
        ),
        clock=CLOCK,
    )
    assert "coordination" in ok.allowed_capabilities


# --- §3.5 pattern out-of-bounds candidate fails closed -----------------------

def test_candidate_out_of_bounds_fails_closed(repo):
    version = AP.register_pattern_version(repo, pattern_slug="mr", fields=_base(), clock=CLOCK)
    assert AP.candidate_within_bounds(version, operation="retrieve", capability="retrieval") is True
    # An LLM may not invent a new operation, capability, or purpose (§3.5).
    assert AP.candidate_within_bounds(version, operation="create") is False
    assert AP.candidate_within_bounds(version, capability="coordination") is False
    assert AP.candidate_within_bounds(version, purpose="assessment") is False


# --- U-035: learning_process never enters an evidence/projection input --------

def test_learning_process_excluded_from_evidence_dto(repo):
    version = AP.register_pattern_version(repo, pattern_slug="mr", fields=_base(), clock=CLOCK)
    # Routing DTO carries it (the "why this activity?" surface).
    assert AP.routing_metadata(version)["learning_process"] == "memory_fluency"
    # The projection-facing evidence DTO must NOT.
    evidence = AP.evidence_semantics(version)
    assert "learning_process" not in evidence
    for value in evidence.values():
        assert "learning_process" not in repr(value)


def test_no_projection_module_reads_learning_process():
    """Static ALLOWLIST guard (B7, U-035 / §3.5): the literal ``learning_process`` may
    appear ONLY in ``services/activity_patterns.py`` and the pattern-registration/read
    methods of ``db/repositories.py``. ANY other occurrence anywhere under
    ``src/learnloop`` fails -- this is an allowlist, not the old filename-token denylist
    (which only inspected files whose NAME contained projection/evidence/scheduler and
    so missed, e.g., a mastery.py that read the routing-only field)."""

    src = Path(__file__).resolve().parents[1] / "src" / "learnloop"
    # The only module allowed to name the field outright.
    allow_files = {"services/activity_patterns.py"}
    offenders: list[str] = []
    for path in src.rglob("*.py"):
        rel = path.relative_to(src).as_posix()
        text = path.read_text(encoding="utf-8")
        if "learning_process" not in text:
            continue
        if rel in allow_files:
            continue
        if rel == "db/repositories.py":
            # Confine occurrences to pattern-registration/read methods: track the
            # enclosing `def` and flag any learning_process line outside a `*pattern*`
            # method (so no projection/evidence method can smuggle the column in).
            current_def = ""
            for line in text.splitlines():
                # Track only class-level method defs (4-space indent), not nested
                # helpers, so the enclosing pattern method is what governs.
                if line.startswith("    def "):
                    current_def = line.strip().split("(", 1)[0][len("def "):]
                if "learning_process" in line and "pattern" not in current_def:
                    offenders.append(f"{rel}:{current_def}: {line.strip()}")
            continue
        # Every other module under src/learnloop is disallowed outright.
        offenders.append(rel)
    assert offenders == [], offenders


# --- §3.4 TaskFeature validation ---------------------------------------------

def test_task_feature_validation(repo):
    schema_id = AP.ensure_builtin_task_feature_schema(repo, clock=CLOCK)
    ok, errors = AP.validate_task_features(
        repo, schema_id, {"complexity": 3, "transfer": "near", "span": "single_step"}
    )
    assert ok, errors
    bad_ok, bad_errors = AP.validate_task_features(
        repo, schema_id, {"complexity": 9, "transfer": "sideways", "unknown_dim": 1}
    )
    assert not bad_ok
    assert len(bad_errors) == 3


# --- §3.5 builtin launch patterns + adapter ----------------------------------

def test_ensure_builtin_patterns_idempotent(repo):
    first = AP.ensure_builtin_patterns(repo, clock=CLOCK)
    assert "minimal_retrieval" in first and "whole_task_integration" in first
    assert len(first) == 10
    second = AP.ensure_builtin_patterns(repo, clock=CLOCK)
    # Content-addressed: re-seeding reuses the same version ids (idempotent).
    assert {k: v.id for k, v in first.items()} == {k: v.id for k, v in second.items()}


def test_list_compatible_patterns(repo):
    AP.ensure_builtin_patterns(repo, clock=CLOCK)
    practice = AP.list_compatible_patterns(repo, purpose="practice", capabilities=["retrieval"])
    slugs = {v.pattern_slug for v in practice}
    assert "minimal_retrieval" in slugs
    # An assessment-only pattern is not offered for a practice request.
    assert "cold_target_assessment" not in slugs


def test_probe_template_adapter_is_diagnostic_only(repo):
    version = AP.adapt_probe_template_to_pattern(
        repo, template_slug="tmpl1", likelihood_identity="lh-abc", clock=CLOCK
    )
    assert version.allowed_purposes == ("diagnostic",)
