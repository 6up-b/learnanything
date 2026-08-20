"""Sidecar contract tests for the KM3b provenance-UI RPCs (§9.6):
get_attempt_trace, get_capability_grid, get_facet_evidence_timeline, and the
re-keyed get_facet_mastery (canonical facet ids + modelVersion)."""

from __future__ import annotations

import io
import json

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.vault.loader import load_vault
from learnloop_sidecar.server import serve

from tests.helpers import NOW
from tests.test_km3_projections import COMP_A, INTEG, LO_ID, build_blueprint_vault


def _rpc(messages: list[dict]) -> list[dict]:
    stdin = io.StringIO("".join(json.dumps(message) + "\n" for message in messages))
    stdout = io.StringIO()
    serve(stdin, stdout)
    return [json.loads(line) for line in stdout.getvalue().splitlines()]


def _seed_blueprint_vault(root):
    paths = build_blueprint_vault(root)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    from learnloop.substrate.state_sync import sync_vault_state

    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    # Demonstrate the two components unassisted; leave the integration facet
    # untested so its capability-grid cell is Ready-only (not demonstrated).
    first = None
    for item_id, points in (("pi_comp_a", 4), ("pi_comp_b", 4)):
        attempt = complete_self_graded_attempt(
            vault,
            repository,
            AttemptDraft(
                practice_item_id=item_id,
                learner_answer_md="An answer.",
                attempt_type="independent_attempt",
                hints_used=0,
            ),
            SelfGradeInput(criterion_points={"c1": points}, fatal_errors=[], confidence=4),
            clock=FrozenClock(NOW),
        )
        first = first or attempt
    return paths, first.attempt_id


def _init(vault_root):
    return {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}}


def test_get_facet_evidence_timeline(tmp_path):
    paths, _attempt_id = _seed_blueprint_vault(tmp_path / "vault")
    result = _rpc(
        [
            _init(paths.root),
            {"jsonrpc": "2.0", "id": 2, "method": "get_facet_evidence_timeline",
             "params": {"facetId": COMP_A}},
        ]
    )[1]["result"]
    assert result["modelVersion"] == "mvp-0.7"
    assert result["supported"] is True
    assert result["facetId"] == COMP_A
    assert result["points"], "expected demonstrated-curve points"
    assert result["demonstrated"] > 0.0
    # Camelized, no leftover snake_case keys.
    point = result["points"][-1]
    assert "isCorrection" in point and "demonstratedCapabilities" in point
    assert isinstance(result["countedToward"], list)


def test_get_attempt_trace(tmp_path):
    paths, attempt_id = _seed_blueprint_vault(tmp_path / "vault")
    result = _rpc(
        [
            _init(paths.root),
            {"jsonrpc": "2.0", "id": 2, "method": "get_attempt_trace",
             "params": {"attemptId": attempt_id}},
        ]
    )[1]["result"]
    assert result["attemptId"] == attempt_id
    assert result["criteria"], "expected criterion rows"
    row = result["criteria"][0]
    assert row["status"] in ("demonstrated", "first_error", "not_judged", "partial")
    assert "targets" in row
    assert isinstance(result["demonstratedCount"], int)


def test_get_capability_grid(tmp_path):
    paths, _attempt_id = _seed_blueprint_vault(tmp_path / "vault")
    result = _rpc(
        [
            _init(paths.root),
            {"jsonrpc": "2.0", "id": 2, "method": "get_capability_grid",
             "params": {"learningObjectId": LO_ID}},
        ]
    )[1]["result"]
    grid = result["grid"]
    assert grid["supported"] is True
    assert COMP_A in grid["facets"]
    # A demonstrated cell for the unassisted component; the untested integration
    # cell is Ready-only (not demonstrated).
    cells = {(c["facetId"], c["capability"]): c for c in grid["cells"]}
    comp_a_cell = cells[(COMP_A, "procedure_execution")]
    assert comp_a_cell["demonstrated"] is True
    integ_cell = cells[(INTEG, "coordination")]
    assert integ_cell["demonstrated"] is False
    assert "ready" in integ_cell
    # Recipe tree (readiness) present with a bottleneck.
    assert result["readiness"] is not None
    assert result["readiness"]["hasBlueprints"] is True


def test_get_facet_mastery_rekey_exposes_model_version(tmp_path):
    paths, _attempt_id = _seed_blueprint_vault(tmp_path / "vault")
    result = _rpc(
        [
            _init(paths.root),
            {"jsonrpc": "2.0", "id": 2, "method": "get_facet_mastery", "params": {}},
        ]
    )[1]["result"]
    assert result["modelVersion"] == "mvp-0.7"
    assert result["canonicalKeys"] is True
    facet_ids = {facet["facetId"] for facet in result["facets"]}
    assert COMP_A in facet_ids
