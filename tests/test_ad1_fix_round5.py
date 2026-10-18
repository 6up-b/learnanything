"""Adaptive difficulty AD1: the round-4 verify's reopened V1, V2 and V4 (sidecar
half), and the pin for the rejected V3, fix round 5 (orchestrator)
(docs/reviews/adaptive-difficulty-ad1-codex-review.md, "Fix round 5"). V4's
screen half is under vitest.

Each test except the V3 pins failed on 7efda77fb for the reason its docstring
names. Fakes only: no network, no paid call.
"""

from __future__ import annotations

import threading
from types import SimpleNamespace

import pytest

from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

from tests.ad_fakes import AuditDecider, ForecastLLM, ad_plan_vault, ad_receipts, rows
from tests.test_ad1_codex_rereview_fixes import _exercise, _hold_out, _served_with_history, _set_fields
from tests.test_ad1_fix_round4 import EXAM_SET, _add_exam_scope, _builds, _bulk_vault, _patch_preparation

# -- V1 [High]: a reload during the protection check ----------------------------------------------


def test_a_reload_while_protection_is_built_is_never_judged_by_the_vault_it_replaced(tmp_path, monkeypatch):
    """V1: the guard read the loaded vault once and built its protection from
    it. A same-root reload that added an exam scope while ``protection()`` ran
    (here, on another thread, inside the predicate) replaced that vault, and
    the old vault's verdict let the request through. The reload generation is
    now read before and after: it moved, so protection is rebuilt from the
    new vault, which holds the revision out."""

    from learnloop.adaptive_difficulty.sending import ProtectedContent, SendGuard
    from learnloop.content.sources import exam_material
    from learnloop_sidecar.context import SidecarContext

    paths = ad_plan_vault(tmp_path)
    _set_fields(paths, "pi_m1b", canonical_exercise=_exercise("exam_b"))
    held = exam_material.Material(spans=frozenset({("ext_rereview", "exam_b")}))
    ctx = SidecarContext()
    armed = threading.Event()

    def predicate(vault_or_sets, _repository):
        sets = getattr(vault_or_sets, "source_sets", None) or []
        verdict = held if any(getattr(entry, "id", None) == EXAM_SET for entry in sets) else exam_material.Material()
        if armed.is_set():
            armed.clear()
            # The owner adds an exam scope and the vault reloads, while this
            # predicate is being built from the vault the guard read.
            reload = threading.Thread(target=lambda: (_add_exam_scope(paths), ctx.reload(maintenance=False)))
            reload.start()
            reload.join(30)
        return verdict

    monkeypatch.setattr(exam_material, "held_out_material", predicate)
    try:
        ctx.load(paths.root)
        vault = ctx.vault
        guard = SendGuard(vault, Repository(paths.sqlite_path), items=[vault.practice_items["pi_m1b"]],
                          live_vault=ctx.loaded_vault)
        armed.set()
        with pytest.raises(ProtectedContent):
            guard.check("request")
        assert any(entry.id == EXAM_SET for entry in ctx.vault.source_sets), "the reload landed"
    finally:
        ctx.map_builds.close()


def test_an_admission_after_a_reload_since_its_check_is_refused(tmp_path):
    """V1: the physical request and the record compare the generation they
    were checked at against the current one, and refuse when it moved; every
    later request of the job is refused too."""

    from learnloop.adaptive_difficulty.sending import ProtectedContent, SendGuard

    paths = ad_plan_vault(tmp_path)
    vault = load_vault(paths.root)

    class Provider:
        def __init__(self):
            self.current = 0

        def __call__(self):
            return vault

        def generation(self):
            return self.current

    provider = Provider()
    guard = SendGuard(vault, Repository(paths.sqlite_path), items=[vault.practice_items["pi_m1a"]],
                      live_vault=provider)
    checked = guard.check("record")
    guard.confirm(checked)
    provider.current += 1
    with pytest.raises(ProtectedContent):
        guard.confirm(checked)
    with pytest.raises(ProtectedContent):
        guard.check("the next request")


# -- V2 [Medium]: only settled revisions leave the queue -------------------------------------------


class _Scripted:
    """The audit and the forecast, each answering per (item, visit) from a script."""

    def __init__(self, audits=None, forecasts=None, raise_on=None):
        self.audits, self.forecasts = dict(audits or {}), dict(forecasts or {})
        self.raise_on = dict(raise_on or {})
        self.visits: list[str] = []
        self.lock = threading.Lock()

    def _turn(self, item_id):
        with self.lock:
            turn = sum(1 for seen in self.visits if seen == item_id)
            self.visits.append(item_id)
        return turn

    def audit(self, _vault, _repository, item, **_kwargs):
        item_id = str(item.id)
        turn = self._turn(item_id)
        if self.raise_on.get(item_id, -1) == turn:
            raise RuntimeError("the provider failed before anything was asked")
        script = self.audits.get(item_id, [])
        status = script[turn] if turn < len(script) else {"status": "current"}
        return SimpleNamespace(as_dict=lambda: dict(status))

    def forecast(self, _vault, _repository, item, **_kwargs):
        item_id = str(item.id)
        script = self.forecasts.get(item_id, [])
        turn = sum(1 for seen in self.visits if seen == item_id) - 1
        status = script[turn] if 0 <= turn < len(script) else {"status": "current"}
        return SimpleNamespace(as_dict=lambda: dict(status))


def _patch_scripted(monkeypatch, scripted: _Scripted) -> None:
    from learnloop.adaptive_difficulty import background, feature_audit

    monkeypatch.setattr(feature_audit, "audit_revision", scripted.audit)
    monkeypatch.setattr(background, "forecast_item", scripted.forecast)


def _run(trigger):
    thread = trigger()
    if thread is not None:
        thread.join(30)
    return thread


def test_a_refused_spend_revision_is_retried_on_the_next_reload(tmp_path, monkeypatch):
    """V2: a run dropped every revision it returned, so a forecast refused for
    the daily cap was never retried by an unchanged reload. Only settled
    revisions leave the queue; the next reload retries it, and nothing chains."""

    from learnloop.adaptive_difficulty.background import schedule_new_revisions
    from learnloop.adaptive_difficulty.outside import Clients

    paths = ad_plan_vault(tmp_path)
    vault = _bulk_vault(paths, 3)
    ids = sorted(vault.practice_items)
    scripted = _Scripted(forecasts={ids[1]: [{"status": "refused_spend"}, {"status": "ok"}]})
    _patch_scripted(monkeypatch, scripted)
    builds, clients = _builds(paths), Clients(llm=ForecastLLM())
    try:
        assert _run(lambda: schedule_new_revisions(SimpleNamespace(practice_items={}), vault, paths.sqlite_path,
                                                   clients=clients, builds=builds)) is not None
        assert scripted.visits == ids
        assert not builds.running, "no run chains after a refusal"
        assert _run(lambda: schedule_new_revisions(vault, vault, paths.sqlite_path, clients=clients,
                                                   builds=builds)) is not None, "the next reload retries it"
        assert scripted.visits == [*ids, ids[1]]
        assert _run(lambda: schedule_new_revisions(vault, vault, paths.sqlite_path, clients=clients,
                                                   builds=builds)) is None, "settled now: nothing waits"
    finally:
        builds.close()


def test_busy_unavailable_and_incomplete_revisions_stay_queued(tmp_path, monkeypatch):
    """V2 (the verify's first case): ``busy``, an unavailable forecast and an
    audit with dimensions unanswered were dropped as done. They stay queued
    for the next trigger; the settled revision does not."""

    from learnloop.adaptive_difficulty.background import schedule_new_revisions
    from learnloop.adaptive_difficulty.outside import Clients

    paths = ad_plan_vault(tmp_path)
    vault = _bulk_vault(paths, 4)
    ids = sorted(vault.practice_items)
    scripted = _Scripted(
        audits={ids[0]: [{"status": "busy"}], ids[1]: [{"status": "audited", "unanswered": ["span"]}]},
        forecasts={ids[3]: [{"status": "unavailable"}]})
    _patch_scripted(monkeypatch, scripted)
    builds, clients = _builds(paths), Clients(llm=ForecastLLM())
    try:
        _run(lambda: schedule_new_revisions(SimpleNamespace(practice_items={}), vault, paths.sqlite_path,
                                            clients=clients, builds=builds))
        _run(lambda: schedule_new_revisions(vault, vault, paths.sqlite_path, clients=clients, builds=builds))
        assert scripted.visits[len(ids):] == [ids[0], ids[1], ids[3]]
    finally:
        builds.close()


def test_an_exception_keeps_the_current_and_every_unvisited_revision(tmp_path, monkeypatch):
    """V2 (the verify's second case): an exception marked the whole batch
    done, even one raised before the first revision was prepared. The
    revision that raised and every unvisited one stay queued; the settled
    ones before it leave."""

    from learnloop.adaptive_difficulty.background import schedule_new_revisions
    from learnloop.adaptive_difficulty.outside import Clients

    paths = ad_plan_vault(tmp_path)
    vault = _bulk_vault(paths, 4)
    ids = sorted(vault.practice_items)
    scripted = _Scripted(raise_on={ids[1]: 0})
    _patch_scripted(monkeypatch, scripted)
    builds, clients = _builds(paths), Clients(llm=ForecastLLM())
    try:
        _run(lambda: schedule_new_revisions(SimpleNamespace(practice_items={}), vault, paths.sqlite_path,
                                            clients=clients, builds=builds))
        assert scripted.visits == ids[:2]
        _run(lambda: schedule_new_revisions(vault, vault, paths.sqlite_path, clients=clients, builds=builds))
        assert scripted.visits == [*ids[:2], *ids[1:]]
    finally:
        builds.close()


def test_an_exception_before_the_first_revision_keeps_the_whole_batch(tmp_path, monkeypatch):
    from learnloop.adaptive_difficulty import protection as protection_module
    from learnloop.adaptive_difficulty.background import schedule_new_revisions
    from learnloop.adaptive_difficulty.outside import Clients

    paths = ad_plan_vault(tmp_path)
    vault = _bulk_vault(paths, 3)
    ids = sorted(vault.practice_items)
    scripted = _Scripted()
    _patch_scripted(monkeypatch, scripted)
    original = protection_module.protection
    failures = iter([True])

    def flaky(*args, **kwargs):
        if next(failures, False):
            raise RuntimeError("the provider failed before the first revision")
        return original(*args, **kwargs)

    monkeypatch.setattr(protection_module, "protection", flaky)
    builds, clients = _builds(paths), Clients(llm=ForecastLLM())
    try:
        _run(lambda: schedule_new_revisions(SimpleNamespace(practice_items={}), vault, paths.sqlite_path,
                                            clients=clients, builds=builds))
        assert scripted.visits == []
        assert _run(lambda: schedule_new_revisions(vault, vault, paths.sqlite_path, clients=clients,
                                                   builds=builds)) is not None
        assert scripted.visits == ids
    finally:
        builds.close()


# -- V3 (rejected as a defect): a recovered answer is checked again ------------------------------


class _SwitchingLLM(ForecastLLM):
    def __init__(self, builds, **kwargs):
        super().__init__(**kwargs)
        self._builds = builds

    def complete(self, request):
        self._builds.close()
        return super().complete(request)


def _fenced_out_first(paths, step):
    """The LLM's answer lands after a vault switch: stale, the answer paid for and receipted."""

    from learnloop.adaptive_difficulty.outside import Clients, forecast_presentation

    import sqlite3

    builds = _builds(paths)
    llm = _SwitchingLLM(builds, p_correct=0.4)
    outcomes = forecast_presentation(load_vault(paths.root), Repository(paths.sqlite_path), step["presentation_id"],
                                     clients=Clients(llm=llm, decider=AuditDecider(p_yes=0.6)),
                                     fence=builds.admit(paths.sqlite_path))
    # The vault is reopened later: the fenced-out job's lease has lapsed.
    with sqlite3.connect(paths.sqlite_path) as connection:
        connection.execute("UPDATE judgment_work_claims SET lease_expires_at = '2000-01-01T00:00:00Z' "
                           "WHERE state = 'leased'")
    return outcomes, llm


def _second_run(paths, step, monkeypatch, *, protect: bool):
    from learnloop.adaptive_difficulty.outside import Clients, forecast_presentation
    from learnloop.practice_index import paid

    if protect:
        original = paid.PaidCalls._recover_receipt

        def recover(self, *args, **kwargs):
            value = original(self, *args, **kwargs)
            if value is not paid._MISSING:
                _hold_out(monkeypatch, "hist")  # protected after the send, at recovery time
            return value

        monkeypatch.setattr(paid.PaidCalls, "_recover_receipt", recover)
    builds = _builds(paths)
    llm, decider = ForecastLLM(p_correct=0.9), AuditDecider(p_yes=0.6)
    outcomes = {outcome.forecaster: outcome for outcome in forecast_presentation(
        load_vault(paths.root), Repository(paths.sqlite_path), step["presentation_id"],
        clients=Clients(llm=llm, decider=decider), fence=builds.admit(paths.sqlite_path))}
    builds.close()
    return outcomes, llm, decider


def test_a_recovered_answer_whose_content_is_protected_now_is_refused(tmp_path, monkeypatch):
    """V3 pin (rejected as a defect, the designed pattern kept): an answer
    paid for before a vault switch is recovered from its receipt, not paid
    twice. It passes the record check again against the vault loaded at
    recovery time: content held out since is refused and not recorded."""

    paths, step = _served_with_history(tmp_path)
    first, llm = _fenced_out_first(paths, step)
    assert len(llm.prompts) == 1 and {outcome.status for outcome in first} == {"stale"}
    assert rows(paths.sqlite_path, "SELECT * FROM model_work_checkpoints") == []
    outcomes, again, decider = _second_run(paths, step, monkeypatch, protect=True)
    assert again.prompts == [], "recovered from the receipt: nothing paid twice"
    assert outcomes["llm_v3:llm"].status == "protected"
    assert outcomes["llm_v3:decider"].status == "protected" and decider.calls == []
    assert [row for row in ad_receipts(paths.sqlite_path) if row["forecaster"].startswith("llm_v3")] == []
    assert rows(paths.sqlite_path, "SELECT * FROM judgment_ledger WHERE task = 'ad_item_forecast'") == []


def test_a_recovered_answer_still_unprotected_is_recorded_without_a_second_request(tmp_path, monkeypatch):
    """V3 pin, the control: the same recovery with nothing protected records
    the answer bought before the switch, with no new request."""

    paths, step = _served_with_history(tmp_path)
    _fenced_out_first(paths, step)
    outcomes, again, _decider = _second_run(paths, step, monkeypatch, protect=False)
    assert again.prompts == []
    assert (outcomes["llm_v3:llm"].status, outcomes["llm_v3:llm"].p) == ("ok", 0.4)
    receipts = [row for row in ad_receipts(paths.sqlite_path) if row["forecaster"] == "llm_v3:llm"]
    assert [row["status"] for row in receipts] == ["ok"]


# -- V4 (the sidecar half): the draft keeps hintSeen ----------------------------------------------


@pytest.mark.parametrize("config", ["", "[adaptive_difficulty]\nforecast_receipts = false\n"], ids=["on", "off"])
def test_the_draft_keeps_hint_seen_under_its_retry_key(tmp_path, config):
    """V4: a draft could not say that a hint had been seen apart from its
    counted hints and its marker, so a restore lost a hint the panel
    delivered. ``hintSeen`` is kept with the retry key whatever the switches;
    ``hintsUsed`` is unchanged."""

    from tests.test_ad1_attempt_columns import _checkpoint, _save_draft, _sidecar

    _paths, ctx, session_id = _sidecar(tmp_path, config=config)
    _save_draft(ctx, session_id, "k1", "A = U", hintsUsed=0, hintSeen=True)
    checkpoint = _checkpoint(ctx, session_id)
    assert checkpoint["hintSeen"] is True and checkpoint["hintsUsed"] == 0
    _save_draft(ctx, session_id, "k1", "A = U Sigma", hintsUsed=0)       # a save without it keeps it
    assert _checkpoint(ctx, session_id)["hintSeen"] is True
    _save_draft(ctx, session_id, "k2", "", hintsUsed=0)                   # another draft never inherits it
    assert "hintSeen" not in _checkpoint(ctx, session_id)
