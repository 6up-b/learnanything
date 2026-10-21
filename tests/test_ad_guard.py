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
import contextlib
import sqlite3
from pathlib import Path

import pytest

from learnloop.adaptive_difficulty import operation as O
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

SRC = Path(__file__).resolve().parents[1] / "src" / "learnloop"
#: The poisoned operation's exit (round 2), on a tree that has it.
_POISONED = getattr(O, "OperationPoisoned", RuntimeError)
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
        with pytest.raises(O.OperationPoisoned), O.ad_operation(vault, repository):
            with pytest.raises(sqlite3.DatabaseError, match=DENIED):
                repository.connection().execute(
                    "INSERT INTO learner_claims(id, scope_type, scope_id, claimed_level, source, created_at) "
                    "VALUES ('c1', 'global', NULL, 0.5, 'init_wizard', '2026-10-01T09:00:00Z')")


def test_incumbent_maintenance_and_vault_loads_never_run_inside_an_operation(tmp_path):
    from learnloop.substrate.state_sync import sync_vault_state

    paths, vault, repository = _vault(tmp_path)
    with pytest.raises(O.OperationPoisoned), O.ad_operation(vault, repository):
        with pytest.raises(sqlite3.DatabaseError, match=DENIED):
            sync_vault_state(vault, repository)
    with O.ad_operation(vault, repository):
        with pytest.raises(RuntimeError, match="load_vault refused"):
            load_vault(paths.root)
        with O.suspended():
            load_vault(paths.root)  # the egress leaves the operation


def test_the_pinned_connection_carries_the_guard_only_inside_the_operation(tmp_path):
    paths, vault, repository = _vault(tmp_path)
    with repository.atomic():
        connection = repository.connection()
        connection.execute("SELECT COUNT(*) FROM practice_attempts").fetchone()
        with pytest.raises(O.OperationPoisoned), O.ad_operation(vault, repository):
            with pytest.raises(sqlite3.DatabaseError, match=DENIED):
                connection.execute("SELECT COUNT(*) FROM practice_attempts").fetchone()
        with pytest.raises(O.OperationPoisoned), O.ad_operation(vault, repository):
            with O.rules("view"):
                connection.execute("/* ad-rules */ SELECT COUNT(*) FROM practice_attempts").fetchone()
            with pytest.raises(sqlite3.DatabaseError, match=DENIED):
                # A statement prepared inside the rules is not reused unchecked outside them.
                connection.execute("/* ad-rules */ SELECT COUNT(*) FROM practice_attempts").fetchone()
        connection.execute("SELECT COUNT(*) FROM practice_attempts").fetchone()


# -- round 2: scope leaks (class 1) and denials fail closed by construction (class 6) ---------------


def test_a_statement_prepared_in_own_write_is_not_reused_outside_it(tmp_path):
    """Class 1 (verify finding 6): a protected-table read prepared inside ``own_write()`` and run
    again, identical, outside it is authorized again, and refused (failed before: SQLite's statement
    cache reused the authorization)."""

    paths, vault, repository = _vault(tmp_path)
    sql = "SELECT COUNT(*) FROM ad_commission_results WHERE practice_item_id = ?"
    with repository.atomic():
        connection = repository.connection()
        # (The refusal poisons the operation: its exit raises, test_a_swallowed_denial_poisons_the_operation.)
        with contextlib.suppress(_POISONED), O.ad_operation(vault, repository):
            with O.own_write("ad_commission_results"):
                connection.execute(sql, ("pi_e1",)).fetchone()
            with pytest.raises(sqlite3.DatabaseError, match=DENIED):
                connection.execute(sql, ("pi_e1",)).fetchone()
            with pytest.raises(sqlite3.DatabaseError, match=DENIED):
                # And on an exceptional exit from the scope too.
                try:
                    with O.own_write("ad_commission_results"):
                        connection.execute(sql, ("pi_e2",)).fetchone()
                        raise KeyError("an exit by exception")
                except KeyError:
                    pass
                connection.execute(sql, ("pi_e2",)).fetchone()


def test_a_write_reads_only_its_own_target_and_declared_constraints(tmp_path):
    """Class 1 (verify finding 7): a DELETE of an AD table whose WHERE reads a protected table through
    a subquery is refused (failed before: every read while a write was being prepared passed)."""

    paths, vault, repository = _vault(tmp_path)
    with repository.atomic():
        connection = repository.connection()
        with contextlib.suppress(_POISONED), O.ad_operation(vault, repository):
            with pytest.raises(sqlite3.DatabaseError, match=DENIED):
                connection.execute("DELETE FROM item_forecast_payloads WHERE id = (SELECT id FROM practice_attempts)")


def test_a_write_reads_its_target_and_foreign_keys_freely(tmp_path):
    paths, vault, repository = _vault(tmp_path)
    with repository.atomic():
        connection = repository.connection()
        with O.ad_operation(vault, repository):
            connection.execute("DELETE FROM item_forecast_payloads WHERE created_at < '2000-01-01'")


def test_a_swallowed_denial_poisons_the_operation(tmp_path):
    """Class 6 (verify finding 8): the first denial makes the operation unavailable: a later write,
    even to an AD table, is refused, and the operation's exit raises however the code inside handled
    the refusal."""

    paths, vault, repository = _vault(tmp_path)
    with repository.atomic():
        connection = repository.connection()
        with pytest.raises(O.OperationPoisoned), O.ad_operation(vault, repository):
            try:
                connection.execute("SELECT COUNT(*) FROM practice_attempts").fetchone()
            except sqlite3.DatabaseError:
                pass  # swallowed
            with pytest.raises(sqlite3.DatabaseError, match=DENIED):
                connection.execute("DELETE FROM item_forecast_payloads WHERE created_at < '2000-01-01'")


def test_a_cached_ad_write_is_refused_once_the_operation_is_poisoned(tmp_path):
    """Round 3 (verify finding 2): an AD insert runs; a later read is refused and the refusal
    swallowed; the identical insert, from SQLite's statement cache with new parameters, is refused
    too (failed before: the cached statement kept its authorization and wrote)."""

    paths, vault, repository = _vault(tmp_path)
    sql = "INSERT INTO ad_dose_offers(row_kind, draw_key, created_at) VALUES ('draw', ?, ?)"
    with repository.atomic():
        connection = repository.connection()
        with contextlib.suppress(_POISONED), O.ad_operation(vault, repository):
            connection.execute(sql, ("k1", "2026-10-21T00:00:00Z"))
            try:
                connection.execute("SELECT COUNT(*) FROM practice_attempts").fetchone()
            except sqlite3.DatabaseError:
                pass  # swallowed
            with pytest.raises(sqlite3.DatabaseError, match=DENIED):
                connection.execute(sql, ("k2", "2026-10-21T00:01:00Z"))
        keys = [row[0] for row in connection.execute("SELECT draw_key FROM ad_dose_offers")]
    assert "k2" not in keys


def test_a_write_then_a_swallowed_denial_then_an_early_return_keeps_no_ad_rows(tmp_path, monkeypatch):
    """Round 3 (verify finding 3): inside the serve hook the sweep writes a reading receipt, then a
    planted read is refused and swallowed, then the hook returns early (the item is protected). The
    serve's savepoint rolls back the receipt and the incumbent is served (failed before: the hook's
    own savepoint released the receipt before the poisoned exit was raised)."""

    from types import SimpleNamespace

    from learnloop.adaptive_difficulty import serve as S
    from learnloop.adaptive_difficulty.material_view import MaterialView
    from learnloop.daily_plan.engine import advance, build_plan
    from learnloop.db.stores import ad_receipts

    from tests.ad23_fakes import LO, ad23_vault, env_for

    paths = ad23_vault(tmp_path, items=("pi_e1",))

    def planted(vault, repository, *, view=None, **_kwargs):
        connection = repository.connection()
        ad_receipts.insert_reading_opportunity(connection, {
            "protection_epoch": getattr(view, "epoch", None), "opportunity_key": "planted", "kind": "worked_example",
            "subkind": "shown", "source_table": "reader_section_progress", "source_id": "ext/planted",
            "source_written_at": "2026-10-01T09:00:00Z", "learning_object_id": LO, "facet_doses": {"recall": 1.0},
            "dose_offer_id": None, "mapping_version": "ad_reading_map_v1", "sweep": "serve", "sweep_ref": None,
            "swept_at": "2026-10-01T09:00:00Z"})
        try:
            connection.execute("SELECT COUNT(*) FROM practice_attempts").fetchone()
        except sqlite3.DatabaseError:
            pass  # swallowed
        return SimpleNamespace(written=1)

    real = MaterialView.withheld
    monkeypatch.setattr(S, "sweep", planted)
    monkeypatch.setattr(MaterialView, "withheld",
                        lambda self, item_id, *a, **k: True if item_id == "pi_e1" and O.current() and
                        O.current().guard.poisoned else real(self, item_id, *a, **k))
    env, _clock = env_for(paths, items=("pi_e1",))
    build_plan(env, kind="normal", budget=3.0, remembered=3, minutes_source="chip")
    _record, step = advance(env, serve=True)
    assert step["practice_item_id"] == "pi_e1" and step["presentation_id"]
    with sqlite3.connect(paths.sqlite_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM ad_reading_opportunities").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM item_serve_inputs").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM plan_presentations").fetchone()[0] == 1


@pytest.mark.parametrize("swallowed", [False, True])
def test_a_denied_dose_response_rolls_the_draw_back(tmp_path, monkeypatch, swallowed):
    """Round 4 (verify finding 2): the Reader's dose offer draws an extra question, then the read of
    that question for the response is refused (raised, or swallowed and answered as none). The offer
    is unavailable, no draw row survives and no budget is consumed (failed before: the draw had
    committed before the response was built, and the section's budget read ``section_offered``)."""

    from contextlib import closing as _closing
    from types import SimpleNamespace

    from learnloop.adaptive_difficulty import dose as D
    from learnloop.adaptive_difficulty import reading as R
    from learnloop.adaptive_difficulty import selection as S
    from learnloop.adaptive_difficulty.material_view import MaterialView, detached_view
    from learnloop.db.connection import connect
    from learnloop.scheduling import randomization_layer as RL
    from learnloop_sidecar.handlers import adaptive_difficulty as H

    from tests.test_ad3_dose_arm import _arm, _mapping
    from tests.test_ad1_reading_opportunities import _question

    paths, vault, repo = _arm(tmp_path, config="dose_floor = 0.3\n")
    _question(repo, "recall", 1, answer=False)
    mapping = _mapping(examples={"ext1": {"we1"}})  # only the question extra is feasible
    monkeypatch.setattr(R, "VaultReadingMap", lambda *_args, **_kwargs: mapping)
    pi = RL.reading_dose_propensities(("none", "extra_question"), {"none": 1.0}, 0.3)
    visit = next(f"v{k}" for k in range(200)
                 if RL.draw_from(pi, S.uniform(S.seed_for(D.DOSE_VERSION, f"v{k}:u1"))) == "extra_question")

    def planted(self, connection, question_id):
        try:
            with _closing(connect(paths.sqlite_path, read_only=True)) as raw:
                raw.execute("SELECT COUNT(*) FROM practice_attempts").fetchone()
        except sqlite3.DatabaseError:
            if not swallowed:
                raise
        return None

    monkeypatch.setattr(MaterialView, "question", planted)
    ctx = SimpleNamespace(require_vault=lambda: (vault, repo))
    result = H.reader_dose_offer(ctx, H.ReaderDoseOfferInput(extraction_id="ext1", section_id="u1", visit_id=visit))
    assert result["offer"] is None and result["reason"] == "unavailable", result
    with sqlite3.connect(paths.sqlite_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM ad_dose_offers").fetchone()[0] == 0
    view = detached_view(vault, repo)
    with _closing(connect(paths.sqlite_path, read_only=True)) as connection:
        assert D.budget(connection, extraction_id="ext1", section_id="u1", now="2026-10-12T09:02:00Z",
                        daily=3, view=view) is None


def _calls(tree: ast.AST, names: set[str]) -> list[ast.Call]:
    return [node for node in ast.walk(tree) if isinstance(node, ast.Call)
            and getattr(node.func, "id", getattr(node.func, "attr", None)) in names]


#: Operations opened directly (not through ``@entry``) that are not in the savepoint form, and why.
DURABLE_OPERATIONS = {
    "learnloop/adaptive_difficulty/background.py": "the preparation run sends to a model (durable form)",
}


def test_every_ad_entry_point_declares_its_write_form_and_writers_use_the_savepoint_form():
    """Round 4: every ``@entry`` declares exactly one write form: ``savepoint=True`` (it writes AD
    decisions or receipts: a poisoned operation rolls them back before its fallback), ``read_only=True``
    (the guard refuses any write while it runs) or ``durable="why"`` (it sends to a model; its units
    commit on their own). Every operation opened directly is in the savepoint (or read-only) form, but
    for the named durable ones; an undeclared ``@entry`` is refused when it is defined."""

    forms: dict[str, str] = {}
    for path in sorted([*SRC.rglob("*.py"), *(SRC.parent / "learnloop_sidecar").rglob("*.py")]):
        relative = str(path.relative_to(SRC.parent))
        if relative == "learnloop/adaptive_difficulty/operation.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                name = getattr(decorator, "id", None) or getattr(getattr(decorator, "func", None), "id", None)
                if name != "entry":
                    continue
                keywords = {kw.arg: kw.value for kw in getattr(decorator, "keywords", [])}
                declared = [form for form in O.WRITE_FORMS if form in keywords and not (
                    isinstance(keywords[form], ast.Constant) and keywords[form].value in (False, None))]
                assert len(declared) == 1, f"{relative}:{node.name} declares {declared or 'no'} write form"
                forms[f"{relative}:{node.name}"] = declared[0]
        for call in _calls(tree, {"ad_operation", "optional_operation"}):
            keywords = {kw.arg: kw.value for kw in call.keywords}
            in_form = any(isinstance(keywords.get(form), ast.Constant) and keywords[form].value is True
                          for form in ("savepoint", "read_only"))
            assert in_form or relative in DURABLE_OPERATIONS, f"{relative}:{call.lineno} opens an operation " \
                "outside the savepoint (or read-only) form"
    assert forms["learnloop/adaptive_difficulty/dose.py:decide"] == "savepoint"
    assert forms["learnloop/adaptive_difficulty/serve.py:record_plan_serve"] == "savepoint"
    assert {form for name, form in forms.items() if "outside.py" in name} == {"durable"}
    with pytest.raises(TypeError, match="write form"):
        O.entry(lambda vault, repository: None)


def test_a_read_only_entry_point_cannot_write(tmp_path):
    """Round 4: a write inside a ``read_only`` entry point is refused (and poisons its operation)."""

    paths, vault, repository = _vault(tmp_path)

    @O.entry(read_only=True)
    def reader(vault, repository):
        repository.connection().execute(
            "INSERT INTO ad_dose_offers(row_kind, draw_key, created_at) VALUES ('draw', 'ro', '2026-10-21T00:00:00Z')")

    with repository.atomic():
        with pytest.raises(sqlite3.DatabaseError, match=DENIED):
            reader(vault, repository)
    with sqlite3.connect(paths.sqlite_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM ad_dose_offers").fetchone()[0] == 0


def _planted_dose_read(tmp_path, monkeypatch):
    """The dose decision's forecast covariate (caught by its broad except) reads a protected table raw."""

    from learnloop.adaptive_difficulty import replay as RP

    def planted(vault, repository, **_kwargs):
        repository.connection().execute("SELECT COUNT(*) FROM practice_attempts").fetchone()

    monkeypatch.setattr(RP, "snapshot", planted)


def test_a_planted_read_swallowed_in_the_dose_decision_yields_no_decision_and_no_rows(tmp_path, monkeypatch):
    """Class 6: a planted read inside the dose arm's covariate, whose broad except would turn it into a
    missing covariate, yields no AD decision and no dose row (failed before: the draw was made and
    persisted)."""

    from learnloop.adaptive_difficulty import dose as D

    from tests.test_ad3_dose_arm import _arm, _boundary, _mapping
    from tests.test_ad1_reading_opportunities import _question, at

    paths, vault, repo = _arm(tmp_path)
    _question(repo, "recall", 1, answer=False)
    _planted_dose_read(tmp_path, monkeypatch)
    with pytest.raises(Exception) as raised:
        D.decide(vault, repo, _boundary(), clock=at(2), reading_map=_mapping())
    assert O.is_denial(raised.value), raised.value
    with sqlite3.connect(paths.sqlite_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM ad_dose_offers").fetchone()[0] == 0
