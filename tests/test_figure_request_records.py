"""Why a figure request was refused, reused, offered fewer tiers or withheld (ADR-017 records for Show me).

One ``figure_request`` record per request: refused with the code it was refused with, built, reused with the key
that matched, or deferred while only a rich job builds it, with the author's menu and a code for each tier left off
it. The figure gate's record names the request and, for a hold, why it held. A figure not shown because it is
withheld now, or whose stored spec no longer parses, leaves one ``figure_withheld`` record per figure and rule, not
one per poll. Each code is staged here with fakes; the code sets are read from the constants, so a new code fails
:func:`test_every_code_is_staged` until a case stages it.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from learnloop import provenance
from learnloop.figure_admission import HOLD_CODES, FiguresGate, HoldReason
from learnloop.figures import build as FB
from learnloop.figures import listing as FL
from learnloop.figures import records as FR
from learnloop.figures import request as FQ
from learnloop.figures import rich as RICH
from learnloop.figures import routes as R
from learnloop.vault.loader import load_vault
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers import figures as FH
from tests import rich_fixtures as RF
from tests.figure_fixtures import (
    EXTRACTION,
    AuthorFake,
    build,
    build_figure_vault,
    call,
    context,
    flagship,
    rows,
    set_config,
)

PRESS = {"extractionId": EXTRACTION, "spanIds": ["p3"]}
WHY = "a narrated video shows the spiral tighten as b grows"

def _records(repository: Any, kind: str) -> list[dict[str, Any]]:
    found = []
    for row in rows(repository, "decision_records"):
        if row["kind"] == kind:
            row = dict(row)
            row["facts"] = json.loads(row["facts_json"])
            found.append(row)
    return found


def _only(repository: Any, kind: str = FR.KIND_REQUEST) -> dict[str, Any]:
    (record,) = _records(repository, kind)
    return record


# -- the menu: a pure core over the probed facts ---------------------------------------------------------------

READY = {"ready": True, "reason": None, "version": "v"}
MENU_CASES = [
    (RICH.MenuFacts(sketch=False, spawner=True, rich_switch=True, opt_in="standing", runtime=READY),
     {"sketch": "no_engine"}),
    (RICH.MenuFacts(sketch=True, spawner=False, host="lesson", rich_switch=True), {"manim": "lesson_host"}),
    (RICH.MenuFacts(sketch=True, spawner=False, host="attempt", rich_switch=True), {"manim": "attempt_host"}),
    (RICH.MenuFacts(sketch=True, spawner=False, rich_switch=True), {"manim": "no_spawner"}),
    (RICH.MenuFacts(sketch=True, spawner=False, rich_switch=False), {"manim": "rich_off"}),
    (RICH.MenuFacts(sketch=True, spawner=True, rich_switch=False), {"manim": "rich_off"}),
    (RICH.MenuFacts(sketch=True, spawner=True, rich_switch=True, opt_in=None), {"manim": "no_opt_in"}),
    *[(RICH.MenuFacts(sketch=True, spawner=True, rich_switch=True, opt_in="standing",
                      runtime={"ready": False, "reason": reason}), {"manim": reason})
      for reason in ("off_linux", "models_off", "no_bwrap", "no_manim")],
]


@pytest.mark.parametrize(("facts", "absent"), MENU_CASES)
def test_the_menu_names_a_code_for_each_absent_tier(facts, absent):
    menu, found = RICH.tier_menu(facts)
    assert found == absent
    assert menu == tuple(tier for tier in ("grammar", "sketch", "manim") if tier not in absent)


def test_a_full_menu_has_no_absent_tier():
    assert RICH.tier_menu(RICH.MenuFacts(sketch=True, spawner=True, rich_switch=True, opt_in="standing",
                                         runtime=READY)) == (("grammar", "sketch", "manim"), {})


@pytest.mark.parametrize("switch", [False, True])
@pytest.mark.parametrize("opt_in", [None, "standing", "declined"])
@pytest.mark.parametrize("ready", [False, True])
def test_tiers_allowed_is_the_menu_it_was_and_probes_only_when_it_did(monkeypatch, switch, opt_in, ready):
    probes: list[bool] = []
    monkeypatch.setattr(RICH, "rich_tiers_switch", lambda _vault: switch)
    monkeypatch.setattr(RICH, "admission_manim_opt_in", lambda _vault: opt_in)
    monkeypatch.setattr(RICH, "manim_runtime_state", lambda _vault, **_kw: probes.append(True) or {"ready": ready})
    for sketch in (False, True):
        expected = ("grammar", *(("sketch",) if sketch else ()),
                    *(("manim",) if switch and opt_in == "standing" and ready else ()))
        assert RICH.tiers_allowed(object(), sketch=sketch) == expected
    assert bool(probes) == (switch and opt_in == "standing")


# -- the gate's hold codes ---------------------------------------------------------------------------------------

def _held(reason: Any, code: str) -> None:
    assert isinstance(reason, HoldReason) and reason.code == code


def test_the_background_hold_names_the_switch_the_power_and_foreground_work(monkeypatch):
    from learnloop.figures import foreground as FG
    from learnloop.figures import power as P

    monkeypatch.setattr(P, "prefetch_switch", lambda _vault: False)
    _held(P.background_hold(object()), "prefetch_off")
    monkeypatch.setattr(P, "prefetch_switch", lambda _vault: True)
    monkeypatch.setattr(P, "power_state", lambda: type("Power", (), {"on_mains": False})())
    _held(P.background_hold(object()), "power")
    monkeypatch.setattr(P, "power_state", lambda: type("Power", (), {"on_mains": True})())
    monkeypatch.setattr(FG, "busy", lambda: True)
    monkeypatch.setattr(FG, "wait_idle", lambda _seconds: False)
    _held(P.background_hold(object()), "foreground")


def test_a_prebuild_whose_author_is_not_the_plan_holds_for_the_plan(monkeypatch):
    from learnloop.figures import power as P
    from learnloop.practice_index import paid

    monkeypatch.setattr(P, "background_hold", lambda _vault, **_kw: None)
    monkeypatch.setattr(paid, "plan_route", lambda *_args: type("Route", (), {"billing": "metered"})())
    _held(FB._prefetch_build_hold(None)(object()), "plan")


def test_a_rich_prebuild_holds_for_the_plan_and_the_render_minutes(monkeypatch, tmp_path):
    from learnloop.figures import power as P
    from learnloop.figures import prefetch_ledger
    from learnloop.practice_index import paid

    monkeypatch.setattr(P, "background_hold", lambda _vault, **_kw: None)
    repository = type("Repo", (), {"sqlite_path": tmp_path / "state.sqlite"})()
    monkeypatch.setattr(paid, "plan_route", lambda *_args: type("Route", (), {"billing": "metered"})())
    _held(RICH._prefetch_hold(repository, None)(object()), "plan")
    monkeypatch.setattr(paid, "plan_route", lambda *_args: type("Route", (), {"billing": "subscription"})())
    monkeypatch.setattr(prefetch_ledger, "render_minutes_left", lambda *_args: 0)
    _held(RICH._prefetch_hold(repository, None)(object()), "render_cap")


def test_a_cancelled_press_holds_as_cancelled():
    _held(FB._cancel_hold(lambda: True, None)(object()), "cancelled")


def test_a_hold_with_no_code_is_recorded_unclassified(tmp_path):
    paths, repository = build_figure_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    gate = FiguresGate(vault, lambda _vault: "k", hold=lambda _vault: "a plain reason", repository=repository)
    with pytest.raises(BaseException):
        gate.check("probe")
    (record,) = _records(repository, "figure_admission")
    assert (record["rule"], record["facts"]["held"]) == ("held", "unclassified")


def test_the_gate_record_names_the_request_and_why_a_press_cancelled_mid_build(tmp_path):
    paths, repository = build_figure_vault(tmp_path / "vault")
    ctx = context(paths.root, author=AuthorFake([flagship()]))
    asked = iter([False, True, True, True, True, True, True])

    with pytest.raises(FQ.FigureRefused) as refused:
        FB.build_figure(load_vault(paths.root), repository, FQ.FigureRequest(extraction_id=EXTRACTION,
                                                                            span_ids=["p3"]),
                        author_client=ctx.figure_author_client, cancelled=lambda: next(asked))
    assert refused.value.code == "figures_changed"
    gate = _only(repository, "figure_admission")
    assert (gate["rule"], gate["facts"]["held"]) == ("held", "cancelled")
    assert gate["subject_kind"] == "figure_request" and gate["subject_id"]
    request = _only(repository)
    assert (request["status"], request["rule"]) == ("refused", "figures_changed")
    assert (request["facts"]["gate_rule"], request["facts"]["held"]) == ("held", "cancelled")
    assert request["subject_kind"] == "figure_request" and request["subject_id"] == gate["subject_id"]


def _rich_rig(tmp_path, monkeypatch):
    from tests.figure_rich_job_helpers import _Rig

    rig = _Rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY)], [RF.scene_output()])
    rig.build()
    return rig


def _once_then(message: str):
    calls = iter([None])
    return lambda *_args, **_kwargs: next(calls, message)


def test_a_rich_job_whose_learner_state_became_protected_holds_for_it(tmp_path, monkeypatch):
    from learnloop.figures import learner_state

    rig = _rich_rig(tmp_path, monkeypatch)
    job = rig.job()
    payload = {**job["payload"], "author_context": {**(job["payload"].get("author_context") or {}),
                                                    "learner_state": {"topics": ["lo_a"]}},
               "learner_state_inputs": {"answers": []}}
    with rig.repository.connection() as connection:
        connection.execute("UPDATE ingest_jobs SET payload_json = ? WHERE id = ?", (json.dumps(payload), job["id"]))
        connection.commit()
    monkeypatch.setattr(RICH, "author_learner_state_enabled", lambda _vault: True)
    monkeypatch.setattr(learner_state, "inputs_withheld", _once_then("an answer it read is held out now"))
    rig.ingest.drain()
    gate = _only(rig.repository, "figure_admission")
    assert (gate["rule"], gate["facts"]["held"]) == ("held", "learner_state")


def test_a_rich_prebuild_whose_item_became_protected_holds_for_it(tmp_path, monkeypatch):
    from learnloop.figures import power as P
    from learnloop.figures import prefetch_ledger
    from learnloop.practice_index import paid

    rig = _rich_rig(tmp_path, monkeypatch)
    job = rig.job()
    with rig.repository.connection() as connection:
        connection.execute("UPDATE ingest_jobs SET payload_json = ? WHERE id = ?",
                           (json.dumps({**job["payload"], "build_mode": "prefetch"}), job["id"]))
        connection.commit()
    holds: list[Any] = []

    class Gate(FiguresGate):
        def __init__(self, *args, hold=None, **kwargs):
            holds.append(hold)
            super().__init__(*args, hold=hold, **kwargs)

    monkeypatch.setattr(RICH, "FiguresGate", Gate)
    monkeypatch.setattr(P, "background_hold", lambda _vault, **_kw: None)
    monkeypatch.setattr(paid, "plan_route", lambda *_args: type("Route", (), {"billing": "subscription"})())
    monkeypatch.setattr(prefetch_ledger, "render_minutes_left", lambda *_args: 10)
    rig.ingest.drain()
    # The prebuild's hold, as run_rich_job composed it, asked once its item is under a check:
    monkeypatch.setattr(RICH, "rich_base_item_protected", lambda *_args, **_kwargs: "the item is under a check now")
    (hold,) = holds
    _held(hold(rig.vault), "item_protection")


# -- the request's record ----------------------------------------------------------------------------------------

def test_a_built_figure_records_its_request_with_the_menu_and_the_absent_tiers(tmp_path):
    paths, repository = build_figure_vault(tmp_path / "vault")
    shown = build(context(paths.root, author=AuthorFake([flagship()])), dict(PRESS))["figure"]
    record = _only(repository)
    assert (record["status"], record["rule"], record["subject_kind"], record["subject_id"]) == (
        "chosen", FR.REQUEST_BUILT, "figure", shown["figureId"])
    assert record["facts"]["tiers_allowed"] == ["grammar"]
    assert record["facts"]["tiers_absent"] == {"manim": "rich_off", "sketch": "no_engine"}
    assert record["facts"]["origin"] == "selection" and record["facts"]["anchored"] is True
    assert "matched" not in record["facts"]


def test_a_second_press_reuses_under_this_setting(tmp_path):
    paths, repository = build_figure_vault(tmp_path / "vault")
    ctx = context(paths.root, author=AuthorFake([flagship()]))
    first = build(ctx, dict(PRESS))["figure"]
    again = build(ctx, dict(PRESS))
    assert again["reused"] is True
    reused = [record for record in _records(repository, FR.KIND_REQUEST) if record["rule"] == FR.REQUEST_REUSED]
    (record,) = reused
    assert (record["status"], record["subject_id"], record["facts"]["matched"]) == (
        "chosen", first["figureId"], "this_setting")


@pytest.mark.parametrize("match", ["rich_only", "other_setting", "recorded_inputs_twin"])
def test_the_reuse_key_that_matched_is_named(monkeypatch, match):
    row = {"id": "fig_1", "verification": "verified", "fuller_of_id": None}
    lookups: list[str] = []

    def reusable(_connection, key, versions):
        lookups.append(key)
        wanted = {"rich_only": "own", "other_setting": "other", "recorded_inputs_twin": "twin"}[match]
        if match == "rich_only":
            return row if versions is FB.RICH_SPEC_VERSIONS else None
        return row if key == wanted else None

    monkeypatch.setattr(FB.store, "reusable", reusable)
    monkeypatch.setattr(FB, "rich_tiers_enabled", lambda _vault: match == "rich_only")
    for name in ("drawable_now",):
        monkeypatch.setattr(FB, name, lambda *_args: True)
    monkeypatch.setattr(FB, "learner_state_withheld", lambda *_args: None)
    monkeypatch.setattr(FB, "source_rejected", lambda *_args: False)
    found = FB._reusable(object(), object(), object(), "own", ["other", "twin"], {"twin"})
    assert found == (row, match)


def test_a_figure_a_concurrent_build_stored_is_reused_as_built_meanwhile(tmp_path, monkeypatch):
    paths, repository = build_figure_vault(tmp_path / "vault")
    ctx = context(paths.root, author=AuthorFake([flagship()]))
    first = build(ctx, dict(PRESS))["figure"]
    stored = rows(repository, "interactive_figures")[0]
    seen = iter([None, stored])  # read before the lock: none yet; inside it: the concurrent build's row
    monkeypatch.setattr(FB.store, "reusable", lambda *_args: None)
    monkeypatch.setattr(FB.store, "latest_for_input", lambda *_args: next(seen))
    build(ctx, dict(PRESS))
    record = [record for record in _records(repository, FR.KIND_REQUEST) if record["rule"] == FR.REQUEST_REUSED][-1]
    assert (record["facts"]["matched"], record["subject_id"]) == ("built_meanwhile", first["figureId"])


def _rich_press(tmp_path, monkeypatch, answers):
    paths, repository = build_figure_vault(tmp_path / "vault", rich=True)
    set_config(paths, "figures", manim_opt_in="standing")
    RF.ready_manim(monkeypatch)
    ctx = context(paths.root, author=AuthorFake(answers))
    ctx.ingest_jobs.bind(ctx.repository, ctx.vault_root, background=False)
    monkeypatch.setattr(ctx.ingest_jobs, "_ensure_worker", lambda: None)
    return paths, repository, ctx


def test_a_rich_only_build_is_deferred_with_its_job_started_then_pending(tmp_path, monkeypatch):
    paths, repository, ctx = _rich_press(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY)])
    first = build(ctx, dict(PRESS))
    assert first["figure"] is None and first["rich"]
    started = _only(repository)
    assert (started["status"], started["rule"], started["subject_kind"]) == (
        "deferred", FR.REQUEST_RICH_STARTED, "figure_request")
    assert started["facts"]["tiers_allowed"] == ["grammar", "manim"] and "tiers_absent" in started["facts"]
    build(ctx, dict(PRESS))
    rules = [record["rule"] for record in _records(repository, FR.KIND_REQUEST)]
    assert rules == [FR.REQUEST_RICH_STARTED, FR.REQUEST_RICH_PENDING]


@pytest.mark.parametrize("reason", ["capped", "unpriced", "unrouted", "not_isolated", "unavailable", "models_off"])
def test_a_route_that_cannot_be_called_refuses_the_request_with_its_code(tmp_path, monkeypatch, reason):
    paths, repository = build_figure_vault(tmp_path / "vault")
    monkeypatch.setattr(R.FigureRoute, "problem", lambda self: R.FigureUnavailable(reason, "the route says no"))
    with provenance.trace_scope("TRACE_REFUSED"), pytest.raises(FQ.FigureRefused):
        FB.build_figure(load_vault(paths.root), repository, FQ.FigureRequest(extraction_id=EXTRACTION,
                                                                            span_ids=["p3"]),
                        author_client=AuthorFake())
    record = _only(repository)
    assert (record["status"], record["rule"], record["trace_id"]) == ("refused", reason, "TRACE_REFUSED")


def test_a_switch_turned_off_mid_build_refuses_with_the_gates_rule(tmp_path):
    paths, repository = build_figure_vault(tmp_path / "vault")

    class SwitchesOff(AuthorFake):
        def complete(self, request):
            set_config(paths, "figures", enabled=False)
            return super().complete(request)

    with pytest.raises(FQ.FigureRefused):
        FB.build_figure(load_vault(paths.root), repository, FQ.FigureRequest(extraction_id=EXTRACTION,
                                                                            span_ids=["p3"]),
                        author_client=SwitchesOff([flagship(), flagship()]))
    record = _only(repository)
    assert (record["rule"], record["facts"]["gate_rule"]) == ("figures_changed", "figures_off")
    assert "held" not in record["facts"]


@pytest.mark.parametrize(("params", "code"), [
    ({**PRESS, "origin": "library", "offerRef": "no_such_offer"}, "not_offered"),
    ({"origin": "prefetch", "goalText": "a figure", "readingAt": {"extractionId": EXTRACTION, "spanId": "p3"}},
     "validation_error"),
    ({**PRESS, "coldActive": True}, "cold_check"),
    ({"extractionId": "ext_exam", "spanIds": ["s1"]}, "exam_material"),
])
def test_a_request_refused_on_the_request_path_records_its_code(tmp_path, params, code):
    paths, repository = build_figure_vault(tmp_path / "vault")
    ctx = context(paths.root, author=AuthorFake())
    rpc = "figure.request" if "coldActive" in params or "goalText" in params else "reader.figure_request"
    with pytest.raises(SidecarError) as refused:
        if rpc == "figure.request":
            anchor = {"extractionId": EXTRACTION, "spanIds": params["spanIds"]} if "spanIds" in params else None
            call(ctx, rpc, {key: value for key, value in {
                "origin": params.get("origin", "selection"), "anchor": anchor, "goalText": params.get("goalText"),
                "readingAt": params.get("readingAt"), "coldActive": params.get("coldActive", False)}.items()
                if value is not None})
        else:
            call(ctx, rpc, params)
    assert refused.value.code == code
    record = _only(repository)
    assert (record["status"], record["rule"]) == ("refused", code)
    assert record["subject_kind"] is None and "goal" not in json.dumps(record["facts"])


def test_a_request_with_figures_off_records_the_switch(tmp_path):
    paths, repository = build_figure_vault(tmp_path / "vault")
    set_config(paths, "figures", enabled=False)
    ctx = context(paths.root, author=AuthorFake())
    with pytest.raises(SidecarError):
        call(ctx, "reader.figure_request", dict(PRESS))
    assert (_only(repository)["rule"]) == "figures_disabled"


def test_a_revision_refused_on_the_request_path_records_its_code(tmp_path):
    paths, repository = build_figure_vault(tmp_path / "vault")
    ctx = context(paths.root, author=AuthorFake())
    with pytest.raises(SidecarError):
        call(ctx, "reader.figure_revise", {"figureId": "fig_missing", "note": "make it bigger"})
    record = _only(repository)
    assert (record["status"], record["rule"], record["facts"]["origin"]) == ("refused", "not_found", "revision")


# -- withheld figures --------------------------------------------------------------------------------------------

def test_a_figure_withheld_at_delivery_is_recorded_once(tmp_path, monkeypatch):
    from tests.figures_codex_review_helpers import _hold_out

    paths, repository = build_figure_vault(tmp_path / "vault")
    ctx = context(paths.root, author=AuthorFake([flagship(kind="illustrative")]))
    figure_id = build(ctx, dict(PRESS))["figure"]["figureId"]
    _hold_out(monkeypatch, "p4")
    for _poll in range(3):  # the job's result as the build returned it, read again by each poll
        assert FH.deliver_figure(ctx, {"figure": {"figure_id": figure_id}, "reused": False})["withheld"] is True
    record = _only(repository, FR.KIND_WITHHELD)
    assert (record["status"], record["rule"], record["subject_id"]) == (
        "withdrawn", FR.WITHHELD_AT_DELIVERY, figure_id)


def test_a_listed_chain_whose_pick_is_withheld_is_recorded_once_per_figure(tmp_path, monkeypatch):
    paths, repository = build_figure_vault(tmp_path / "vault")
    shown = build(context(paths.root, author=AuthorFake([flagship()])), dict(PRESS))["figure"]
    monkeypatch.setattr(FL, "row_withheld", lambda *_args: "held out now")
    vault = load_vault(paths.root)
    for _poll in range(3):
        assert FL.list_figures(vault, repository, EXTRACTION) == []
    record = _only(repository, FR.KIND_WITHHELD)
    assert (record["rule"], record["subject_id"], record["facts"]["where"]) == (
        FR.WITHHELD_PICK, shown["figureId"], "list")


def test_a_listed_figure_whose_spec_no_longer_parses_is_recorded_once(tmp_path):
    paths, repository = build_figure_vault(tmp_path / "vault")
    shown = build(context(paths.root, author=AuthorFake([flagship()])), dict(PRESS))["figure"]
    with repository.connection() as connection:
        connection.execute("UPDATE interactive_figures SET spec_json = ? WHERE id = ?",
                           ('{"spec_version": "nonsense"}', shown["figureId"]))
        connection.commit()
    vault = load_vault(paths.root)
    for _poll in range(2):
        assert FL.list_figures(vault, repository, EXTRACTION) == []
    record = _only(repository, FR.KIND_WITHHELD)
    assert (record["rule"], record["subject_id"]) == (FR.SPEC_UNPARSABLE, shown["figureId"])


def test_records_keep_ids_and_codes_only():
    request = FQ.FigureRequest(extraction_id=EXTRACTION, span_ids=["p3"], goal_text="the learner's own words here",
                               goal_author="learner")
    record = FR.request_record(request, status="refused", rule="exam_material")
    assert provenance.check_no_prose(record) == []
    assert "learner's own words" not in json.dumps(record.facts)


#: The hold codes staged above, each by the hold that returns it.
HOLDS_STAGED = {"prefetch_off", "power", "foreground", "plan", "render_cap", "cancelled", "unclassified",
                "learner_state", "item_protection"}
#: The reuse matches staged above.
MATCHES_STAGED = {"this_setting", "rich_only", "other_setting", "recorded_inputs_twin", "built_meanwhile"}
WITHHELD_STAGED = {FR.WITHHELD_AT_DELIVERY, FR.WITHHELD_PICK, FR.SPEC_UNPARSABLE}


def test_every_code_is_staged():
    """Every absent-tier, hold, reuse-match and withheld code has a case above (the codes are the constants', so a
    new one fails here until a case stages it)."""

    assert {code for _facts, absent in MENU_CASES for code in absent.values()} == set(RICH.TIER_ABSENT_CODES)
    assert HOLDS_STAGED == set(HOLD_CODES)
    assert MATCHES_STAGED == set(FR.REUSE_MATCHES)
    assert WITHHELD_STAGED == {FR.WITHHELD_AT_DELIVERY, FR.WITHHELD_PICK, FR.SPEC_UNPARSABLE}


def test_schema_refusal_records_only_its_code(tmp_path):
    from learnloop_sidecar.server import _handle

    paths, repo = build_figure_vault(tmp_path / "vault")
    ctx = context(paths.root, author=AuthorFake())
    private = "withheld passage text"
    response = _handle(ctx, {"jsonrpc": "2.0", "id": 1, "method": "reader.figure_request",
                             "params": {**PRESS, "spanIds": [private] * 41}})
    assert response["error"]["code"] == -32602
    record = _only(repo)
    assert record["rule"] == "validation_error"
    assert record["facts"] == {}
    assert private not in json.dumps(record)


def test_withheld_poll_after_outer_rollback_has_a_committed_record(tmp_path):
    paths, repo = build_figure_vault(tmp_path / "vault")
    with pytest.raises(RuntimeError, match="rollback"):
        with repo.atomic():
            FR.write_withheld_once(repo, "fig_blocked", FR.WITHHELD_PICK, where="list")
            raise RuntimeError("rollback")
    FR.write_withheld_once(repo, "fig_blocked", FR.WITHHELD_PICK, where="list")
    assert _only(repo, FR.KIND_WITHHELD)["subject_id"] == "fig_blocked"


def test_a_pending_press_names_its_request_and_job(tmp_path, monkeypatch):
    _, repo, ctx = _rich_press(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY)])
    build(ctx, dict(PRESS))
    pending = build(ctx, dict(PRESS))["rich"]
    (record,) = [r for r in _records(repo, FR.KIND_REQUEST) if r["rule"] == FR.REQUEST_RICH_PENDING]
    assert record["subject_id"] == pending["requestId"]
    assert record["facts"]["job_id"] == pending["richJobId"]


def test_reusable_winner_between_press_and_lock_is_built_meanwhile(tmp_path, monkeypatch):
    paths, repo = build_figure_vault(tmp_path / "vault")
    ctx = context(paths.root, author=AuthorFake([flagship()]))
    winner = build(ctx, dict(PRESS))["figure"]
    reusable = FB.store.reusable
    visible = False

    def before_lock(*args):
        nonlocal visible
        visible = True
        return None

    monkeypatch.setattr(FB.store, "reusable", lambda *args: reusable(*args) if visible else None)
    monkeypatch.setattr(FB.store, "latest_for_input", before_lock)
    assert build(ctx, dict(PRESS))["figure"]["figureId"] == winner["figureId"]
    (record,) = [r for r in _records(repo, FR.KIND_REQUEST) if r["rule"] == FR.REQUEST_REUSED]
    assert record["facts"]["matched"] == "built_meanwhile"
