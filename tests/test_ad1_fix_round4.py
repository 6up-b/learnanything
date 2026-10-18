"""Adaptive difficulty AD1: the whole-stage Codex verify's findings V1-V3 and
V5, fix round 4 (orchestrator) (docs/reviews/adaptive-difficulty-ad1-codex-review.md,
"Fix round 4"). V4 is the practice screen's, under vitest.

Each test failed on de34b5d01 for the reason its docstring names. Fakes only:
no network, no paid call.
"""

from __future__ import annotations

import threading
import time
from types import SimpleNamespace

import pytest
import yaml

from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

from tests.ad_fakes import AuditDecider, ForecastLLM, ad_plan_vault, ad_receipts, rows
from tests.test_ad1_codex_rereview_fixes import _exercise, _metered_vault, _set_fields

EXAM_SET = "exam_scope_added"


# -- V1 [High]: protection is resolved from the vault loaded now --------------------------------


def _exam_scope_holds_out(monkeypatch, *spans: str) -> None:
    """The held-out predicate of a vault whose source sets carry the exam scope
    ``EXAM_SET`` holds these spans out; without it, nothing. It reads only the
    vault object it is handed, as the real predicate reads its source sets."""

    from learnloop.content.sources import exam_material

    held = exam_material.Material(spans=frozenset(("ext_rereview", span) for span in spans))

    def predicate(vault_or_sets, _repository):
        sets = getattr(vault_or_sets, "source_sets", None) or []
        return held if any(getattr(entry, "id", None) == EXAM_SET for entry in sets) else exam_material.Material()

    monkeypatch.setattr(exam_material, "held_out_material", predicate)


def _add_exam_scope(paths) -> None:
    """The owner's source-set edit: an exam scope, in the vault's own file."""

    from learnloop.vault.paths import VaultPaths

    target = VaultPaths(paths.root, load_vault(paths.root).config).source_sets_path
    payload = yaml.safe_load(target.read_text(encoding="utf-8")) if target.exists() else None
    payload = payload or {"schema_version": 1, "source_sets": []}
    payload["source_sets"].append({"id": EXAM_SET, "subject_id": "linear-algebra", "title": "The final exam"})
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


class _ReloadingDecider(AuditDecider):
    """While its request runs, the owner adds an exam scope and the vault is reloaded."""

    def __init__(self, ctx, paths):
        super().__init__()
        self._ctx, self._paths, self.reloaded = ctx, paths, threading.Event()

    def decide(self, state, questions, *, purpose, timeout_seconds=None):
        result = super().decide(state, questions, purpose=purpose, timeout_seconds=timeout_seconds)
        if not self.reloaded.is_set():
            _add_exam_scope(self._paths)
            self._ctx.reload(maintenance=False)
            self.reloaded.set()
        return result


def _wait_idle(ctx, timeout: float = 30.0) -> None:
    deadline = time.monotonic() + timeout
    while ctx.map_builds.running and time.monotonic() < deadline:
        time.sleep(0.05)
    assert not ctx.map_builds.running


def test_a_same_vault_reload_adding_an_exam_scope_refuses_the_next_request_and_the_record(tmp_path, monkeypatch):
    """V1: the job's guard kept the vault object it was started with, so a
    same-vault reload whose source-set edit added an exam scope was never
    seen: the revision's audit was recorded and its ``llm_v1:item`` request
    sent the now held-out stem. The guard now reads the vault loaded at each
    check (the context's), so the audit's record and the forecast's request
    are refused."""

    from learnloop.adaptive_difficulty.outside import Clients
    from learnloop_sidecar.context import SidecarContext

    paths = ad_plan_vault(tmp_path, config="[adaptive_difficulty]\noutside_forecasters = [\"llm_v1:item\"]\n")
    _exam_scope_holds_out(monkeypatch, "exam_b")
    ctx = SidecarContext()
    llm = ForecastLLM(p_correct=0.5)
    try:
        ctx.load(paths.root)
        decider = _ReloadingDecider(ctx, paths)
        ctx.ad_clients = Clients(llm=llm, decider=decider)
        _set_fields(paths, "pi_m1b", prompt="An exam question, imported.", canonical_exercise=_exercise("exam_b"))
        ctx.reload(maintenance=False)
        assert decider.reloaded.wait(30), "the exam scope was added while the audit's Decider request ran"
        _wait_idle(ctx)
        assert len(decider.calls) == 1, "the Decider request went out before the scope existed"
        assert llm.prompts == [], "the llm_v1:item request after the reload was refused"
        assert rows(paths.sqlite_path, "SELECT * FROM judgment_ledger WHERE task = 'ad_feature_audit'") == []
        assert [row for row in ad_receipts(paths.sqlite_path) if row["scope"] == "item"] == []
    finally:
        ctx.map_builds.close()


def test_another_vault_or_none_loaded_refuses(tmp_path):
    """V1: a provider that shows another vault, or none, refuses (protected)."""

    from learnloop.adaptive_difficulty.sending import ProtectedContent, SendGuard

    paths = ad_plan_vault(tmp_path / "a")
    other = ad_plan_vault(tmp_path / "b")
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    SendGuard(vault, repository, live_vault=lambda: load_vault(paths.root)).check()
    for shown in (lambda: load_vault(other.root), lambda: None):
        guard = SendGuard(vault, repository, live_vault=shown)
        with pytest.raises(ProtectedContent):
            guard.check()


# -- V2 [Medium]: one bounded preparation queue per vault ---------------------------------------


def _bulk_vault(paths, count: int):
    real = load_vault(paths.root)
    base = real.practice_items["pi_m1a"]
    items = {f"pi_bulk_{index:04d}": base.model_copy(update={"id": f"pi_bulk_{index:04d}",
                                                             "prompt": f"Imported stem {index}."})
             for index in range(count)}
    return SimpleNamespace(practice_items=items, config=real.config, root=real.root, source_sets=[])


class _Recorder:
    """Stands in for the audit and the forecast: records each revision per run, optionally holding."""

    def __init__(self, hold: threading.Event | None = None) -> None:
        self.calls: list[tuple[int, str]] = []
        self.lock = threading.Lock()
        self.active: set[int] = set()
        self.most_at_once = 0
        self.entered = threading.Event()
        self.hold = hold

    def audit(self, _vault, _repository, item, **_kwargs):
        thread = threading.get_ident()
        with self.lock:
            self.calls.append((thread, str(item.id)))
            self.active.add(thread)
            self.most_at_once = max(self.most_at_once, len(self.active))
        self.entered.set()
        if self.hold is not None:
            self.hold.wait(10)
        with self.lock:
            self.active.discard(thread)
        return SimpleNamespace(as_dict=lambda: {"status": "current"})

    def forecast(self, *_args, **_kwargs):
        return SimpleNamespace(as_dict=lambda: {"status": "current"})


def _patch_preparation(monkeypatch, recorder: _Recorder) -> None:
    from learnloop.adaptive_difficulty import background, feature_audit

    monkeypatch.setattr(feature_audit, "audit_revision", recorder.audit)
    monkeypatch.setattr(background, "forecast_item", recorder.forecast)


def _builds(paths):
    from learnloop.hints.map_builder import BackgroundBuilds

    builds = BackgroundBuilds()
    builds.bind(paths.sqlite_path)
    return builds


def test_an_import_of_1000_revisions_prepares_at_most_20_per_run(tmp_path, monkeypatch):
    """V2: a reload's preparation passed ``limit=len(ids)``, so an import of
    1,000 items started one job preparing all 1,000 at once. Every run now
    prepares at most PREPARE_LIMIT (20) revisions; the rest wait for later
    runs (the next reload, a plan read), each another 20."""

    from learnloop.adaptive_difficulty.background import PREPARE_LIMIT, schedule_new_revisions
    from learnloop.adaptive_difficulty.outside import Clients

    paths = ad_plan_vault(tmp_path)
    vault = _bulk_vault(paths, 1000)
    recorder = _Recorder()
    _patch_preparation(monkeypatch, recorder)
    builds, clients = _builds(paths), Clients(llm=ForecastLLM())
    try:
        thread = schedule_new_revisions(SimpleNamespace(practice_items={}), vault, paths.sqlite_path,
                                        clients=clients, builds=builds)
        assert thread is not None
        thread.join(60)
        assert PREPARE_LIMIT == 20 and len(recorder.calls) == 20, "one run, at most 20 revisions"
        for _later in range(2):
            thread = schedule_new_revisions(vault, vault, paths.sqlite_path, clients=clients, builds=builds)
            assert thread is not None, "a later reload with nothing new takes the next 20"
            thread.join(60)
        prepared = [item_id for _thread, item_id in recorder.calls]
        assert len(prepared) == 60 and len(set(prepared)) == 60
        assert prepared == sorted(vault.practice_items)[:60], "in arrival order, each once"
    finally:
        builds.close()


def test_two_watcher_batches_share_one_worker(tmp_path, monkeypatch):
    """V2: each watcher batch started a job of its own, so two batches ran two
    workers at once. Both now feed the vault's one queue: the second batch
    starts no worker beside the running one, and waits for the next run."""

    from learnloop.adaptive_difficulty.background import schedule_new_revisions
    from learnloop.adaptive_difficulty.outside import Clients

    paths = ad_plan_vault(tmp_path)
    vault = _bulk_vault(paths, 10)
    hold = threading.Event()
    recorder = _Recorder(hold)
    _patch_preparation(monkeypatch, recorder)
    builds, clients = _builds(paths), Clients(llm=ForecastLLM())
    ids = sorted(vault.practice_items)
    try:
        first = schedule_new_revisions(vault, vault, paths.sqlite_path, item_ids=ids[:5], clients=clients,
                                       builds=builds)
        assert first is not None and recorder.entered.wait(10)
        second = schedule_new_revisions(vault, vault, paths.sqlite_path, item_ids=ids[5:], clients=clients,
                                        builds=builds)
        assert second is None, "no second worker while the vault's worker runs"
        hold.set()
        first.join(30)
        assert recorder.most_at_once == 1
        assert sorted(item_id for _thread, item_id in recorder.calls) == ids[:5]
        again = schedule_new_revisions(vault, vault, paths.sqlite_path, clients=clients, builds=builds)
        assert again is not None
        again.join(30)
        assert sorted(item_id for _thread, item_id in recorder.calls) == ids
        assert recorder.most_at_once == 1
    finally:
        hold.set()
        builds.close()


# -- V3 [Medium]: model checkpoints are fenced ---------------------------------------------------


class _SwitchingMeteredLLM(ForecastLLM):
    """A metered LLM that answers after the vault was switched away mid-request."""

    provider_name = "metered_test"
    provider_type = "openrouter"
    model = "vendor/metered-model"

    def __init__(self, builds, **kwargs):
        super().__init__(**kwargs)
        self._builds = builds

    def complete(self, request):
        self._builds.close()
        return super().complete(request)


def test_an_answer_after_a_vault_switch_writes_no_checkpoint_and_settles_its_spend(tmp_path):
    """V3: the fenced repository delegated ``save_model_checkpoint`` to the
    base repository, whose writer allows late writes on its own connection,
    so an LLM answer arriving after a vault switch still landed in
    ``model_work_checkpoints``. It is now fenced (dropped); the sent call's
    finish receipt and its spend settlement still land."""

    from learnloop.adaptive_difficulty.outside import Clients, forecast_item
    from learnloop.db.stores.source_service import SERVICE_SPEND_TABLE

    paths = _metered_vault(tmp_path, cap=100.0)
    builds = _builds(paths)
    fence = builds.admit(paths.sqlite_path)
    vault = load_vault(paths.root)
    llm = _SwitchingMeteredLLM(builds, p_correct=0.5)
    outcome = forecast_item(vault, Repository(paths.sqlite_path), vault.practice_items["pi_m1a"],
                            clients=Clients(llm=llm), fence=fence)
    assert len(llm.prompts) == 1 and outcome.status == "stale"
    assert rows(paths.sqlite_path, "SELECT * FROM model_work_checkpoints") == []
    assert [row for row in ad_receipts(paths.sqlite_path) if row["scope"] == "item"] == []
    calls = rows(paths.sqlite_path, "SELECT status FROM model_call_receipts WHERE owner_kind = 'ad_item_forecast' "
                                    "AND parent_call_id IS NULL")
    assert [row["status"] for row in calls] == ["completed"], "the sent request keeps its accounting"
    spend = rows(paths.sqlite_path, f"SELECT state FROM {SERVICE_SPEND_TABLE} "
                                    "WHERE envelope = 'adaptive_difficulty.daily_spend_cap_usd'")
    assert [row["state"] for row in spend] == ["settled"], "its reservation is settled"


# -- V5 [Medium]: a tutor exchange's subkind is its answer mode ---------------------------------


def test_a_reader_tutor_exchange_is_recorded_under_its_answer_mode(tmp_path):
    """V5: the opportunity's subkind was the question's context (``reader``,
    ``library``), so the three answer modes §5.11 names collapsed into one.
    The ask now stores its answer mode on the question
    (``question_events.answer_mode``, migration 213), and the sweep records
    it; a question without one (outside the Reader, or before 213) is
    ``unknown``."""

    from learnloop.reader import reader_dialogue as RD

    from tests.test_ad1_reading_opportunities import LO_A, _opportunities, _setup, _sweep, at

    paths, vault, repo = _setup(tmp_path)
    asked = RD.ask(vault, repo, RD.StubReaderClient(answer_md="Because."), extraction_id="ext1", span_id="s1",
                   question_md="Why?", answer_mode="ask_me_first", target_key="tcv-1", clock=at(1))
    earlier = repo.insert_question_event(
        {"context": "reader", "note_id": "span:ext1/s1", "question_md": "and?", "answer_md": "so.",
         "answer_status": "answered"}, clock=at(2))
    _sweep(vault, repo, 5)
    tutor = {row["source_id"]: row for row in _opportunities(paths) if row["kind"] == "reader_tutor_exchange"}
    assert tutor[asked["event_id"]]["subkind"] == "ask_me_first"
    assert tutor[earlier]["subkind"] == "unknown"
    assert {row["learning_object_id"] for row in tutor.values()} == {LO_A}
    stored = rows(paths.sqlite_path, "SELECT answer_mode FROM question_events WHERE id = ?", (asked["event_id"],))
    assert stored == [{"answer_mode": "ask_me_first"}], "stored once, when the question is asked"
    from learnloop.adaptive_difficulty.reading import TUTOR_ANSWER_MODES
    from learnloop.tutor.tutor_qa import READER_ANSWER_MODES

    assert TUTOR_ANSWER_MODES == READER_ANSWER_MODES
