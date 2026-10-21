"""AD23 redesign (Option B): the AD guard, A8 by construction at the data sources.

* AD's whole pipeline (the contract's harness, default configuration, frozen clock) runs with ZERO
  guard denials, over the operations of every entry point (the trace hook ``operation.OBSERVERS``);
* a planted raw read of a protected table inside the slot's operation is refused, AD is unavailable
  for the slot, the plan serves its planned item and the denial is logged and counted; the negative
  control shows the same check fails with the guard disabled;
* a write to a table AD does not own is refused inside an operation, and incumbent maintenance
  (the state sync) cannot run inside one; a vault load inside one is refused;
* the guard is installed on the serve transaction's pinned connection at operation entry and
  removed at exit; with adaptive difficulty off no operation opens;
* the rules' SQL marker appears only in the rules module, on every statement there.

Fakes only: no network, no model call.
"""

from __future__ import annotations

import ast
import sqlite3
from pathlib import Path

import pytest

from learnloop.adaptive_difficulty import operation as O
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

SRC = Path(__file__).resolve().parents[1] / "src" / "learnloop"
#: SQLite's refusal of a statement, or of a column read.
DENIED = "not authorized|is prohibited"


@pytest.fixture
def observed(monkeypatch):
    """Every operation as it closes (the guard's own record: SQLite allows one authorizer)."""

    seen: list[O.Operation] = []
    monkeypatch.setattr(O, "OBSERVERS", [seen.append])
    return seen


def test_the_ad_pipeline_runs_with_zero_denials(tmp_path, monkeypatch, observed):
    from tests import test_ad23_contract as C

    protected, _absent = C.make_copies(tmp_path, coupled=False)
    C._hold_out(monkeypatch)
    C._deterministic(monkeypatch)
    C._carve_outs(monkeypatch)
    C._run_at_common_root(protected, monkeypatch)
    denials = [denial for op in observed for denial in op.guard.denials]
    assert denials == [], denials[:10]
    entries = {op.guard.entry for op in observed}
    for name in ("serve.record_plan_serve", "reading.sweep", "background.prepare_items",
                 "outside.forecast_presentation", "generation.commission_point", "dose.decide",
                 "dose.record_uptake", "readiness.lo_readiness", "replay.snapshot", "report.build",
                 "ad_slot.slot_operation"):
        assert any(name in entry for entry in entries), (name, sorted(entries))
    reads = {table for op in observed for table in op.guard.reads}
    assert {"practice_attempts", "plan_presentations", "ad_reading_opportunities", "source_document_blocks"} <= reads


def _slot_serve(tmp_path, monkeypatch, *, plant: bool):
    """One plan serve; with ``plant`` the slot's request builder first reads ``practice_attempts``
    raw on the serve's pinned connection."""

    from learnloop.daily_plan import ad_slot
    from learnloop.daily_plan.engine import advance, build_plan

    from tests.ad23_fakes import ad23_vault, env_for, selections

    items = ("pi_e1", "pi_e2", "pi_e3")
    paths = ad23_vault(tmp_path, items=items, config="[router]\nenabled = false\n")
    env, _clock = env_for(paths, items=items)
    build_plan(env, kind="normal", budget=3.0, remembered=3, minutes_source="chip")
    if plant:
        real = ad_slot.build_request

        def planted(env, *args, **kwargs):
            env.repository.connection().execute("SELECT * FROM practice_attempts").fetchall()
            return real(env, *args, **kwargs)

        monkeypatch.setattr(ad_slot, "build_request", planted)
    _record, step = advance(env, serve=True)
    return paths, step, selections(paths, kind="serve")


def _planted_read_is_refused(tmp_path, monkeypatch) -> None:
    before = O.denial_count(Path(tmp_path) / "x")  # no log there: 0
    paths, step, rows = _slot_serve(tmp_path, monkeypatch, plant=True)
    assert step["kind"] == "item" and step.get("adaptive_difficulty") is None, "the planned item is served"
    assert rows == [], "AD wrote no draw"
    assert O.denial_count(paths.sqlite_path) >= 1 > before, "the denial is logged and counted"


def test_a_planted_raw_read_in_an_operation_is_refused_and_the_incumbent_serves(tmp_path, monkeypatch):
    _, _, unplanted = _slot_serve(tmp_path / "control", monkeypatch, plant=False)
    assert unplanted, "without the planted read AD draws the slot"
    _planted_read_is_refused(tmp_path / "planted", monkeypatch)


def test_negative_control_with_the_guard_disabled_the_planted_read_check_fails(tmp_path, monkeypatch):
    monkeypatch.setitem(O._MODE, "mode", "observe")
    with pytest.raises(AssertionError):
        _planted_read_is_refused(tmp_path, monkeypatch)


def _vault(tmp_path):
    from tests.ad23_fakes import ad23_vault

    paths = ad23_vault(tmp_path, items=("pi_e1",))
    return paths, load_vault(paths.root), Repository(paths.sqlite_path)


def test_a_write_to_a_table_ad_does_not_own_is_refused(tmp_path):
    paths, vault, repository = _vault(tmp_path)
    with repository.atomic():
        with O.ad_operation(vault, repository):
            with pytest.raises(sqlite3.DatabaseError, match=DENIED):
                repository.connection().execute(
                    "INSERT INTO learner_claims(id, scope_type, scope_id, claimed_level, source, created_at) "
                    "VALUES ('c1', 'global', NULL, 0.5, 'init_wizard', '2026-10-01T09:00:00Z')")


def test_incumbent_maintenance_and_vault_loads_never_run_inside_an_operation(tmp_path):
    from learnloop.substrate.state_sync import sync_vault_state

    paths, vault, repository = _vault(tmp_path)
    with O.ad_operation(vault, repository):
        with pytest.raises(sqlite3.DatabaseError, match=DENIED):
            sync_vault_state(vault, repository)
        with pytest.raises(RuntimeError, match="load_vault refused"):
            load_vault(paths.root)
        with O.suspended():
            load_vault(paths.root)  # the egress leaves the operation


def test_the_pinned_connection_carries_the_guard_only_inside_the_operation(tmp_path):
    paths, vault, repository = _vault(tmp_path)
    with repository.atomic():
        connection = repository.connection()
        connection.execute("SELECT COUNT(*) FROM practice_attempts").fetchone()
        with O.ad_operation(vault, repository):
            with pytest.raises(sqlite3.DatabaseError, match=DENIED):
                connection.execute("SELECT COUNT(*) FROM practice_attempts").fetchone()
            with O.rules("view"):
                connection.execute("/* ad-rules */ SELECT COUNT(*) FROM practice_attempts").fetchone()
            with pytest.raises(sqlite3.DatabaseError, match=DENIED):
                # A statement prepared inside the rules is not reused unchecked outside them.
                connection.execute("/* ad-rules */ SELECT COUNT(*) FROM practice_attempts").fetchone()
        connection.execute("SELECT COUNT(*) FROM practice_attempts").fetchone()


def test_with_adaptive_difficulty_off_no_operation_opens(tmp_path, observed):
    from learnloop.adaptive_difficulty.reading import sweep

    paths, vault, repository = _vault(tmp_path)
    vault.config.adaptive_difficulty.enabled = False
    sweep(vault, repository, as_of="2026-10-12T09:00:00Z", sweep_kind="backfill")
    assert observed == []


def _sql_strings(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr):
            out.append("".join(part.value for part in node.values if isinstance(part, ast.Constant)
                               and isinstance(part.value, str)))
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            out.append(node.value)
    return out


def test_the_rules_marker_appears_only_in_the_rules_module():
    rules = SRC / "adaptive_difficulty" / "material_view.py"
    for path in sorted(SRC.rglob("*.py")):
        strings = _sql_strings(path)
        marked = [text for text in strings if O.RULES_MARKER in text]
        if path == rules:
            statements = [text for text in strings if text.lstrip().upper().startswith(("SELECT", "/*"))
                          and " FROM " in text.upper()]
            assert statements and all(O.RULES_MARKER in text for text in statements), "an unmarked rules statement"
        elif path == SRC / "adaptive_difficulty" / "operation.py":
            assert marked == [O.RULES_MARKER], "operation.py only defines the marker"
        else:
            assert marked == [], (str(path), marked)
