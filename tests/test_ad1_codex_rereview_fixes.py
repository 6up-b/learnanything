"""Adaptive difficulty AD1: the Codex re-review's findings F11-F13
(docs/reviews/adaptive-difficulty-ad1-codex-review.md, "Re-review").

Each test reproduces one finding and failed on f9429d94e (the fix-round tip
the re-review read) for the reason its docstring names. Fakes only: no
network, no paid call.
"""

from __future__ import annotations

import sqlite3
import threading
import time
from datetime import timedelta

import pytest
import yaml

from learnloop.daily_plan.engine import advance, build_plan
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

from tests.ad_fakes import ITEMS, AuditDecider, ForecastLLM, ad_plan_vault, ad_receipts, plan_env

SENTINEL = "HELD_OUT_HISTORY_SENTINEL-7d2e"
EXTRACTION = "ext_rereview"


def _item_path(paths, item_id):
    return paths.practice_item_path("linear-algebra", item_id)


def _set_fields(paths, item_id, **fields):
    path = _item_path(paths, item_id)
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    for key, value in fields.items():
        if value is None:
            payload.pop(key, None)
        else:
            payload[key] = value
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _exercise(span: str) -> dict:
    return {"source_id": "src_rereview", "extraction_id": EXTRACTION, "span_ids": [span]}


def _hold_out(monkeypatch, *spans: str) -> None:
    """From now on the predicate holds these spans out (a unit marked held out after the serve)."""

    from learnloop.content.sources import exam_material

    material = exam_material.Material(spans=frozenset((EXTRACTION, span) for span in spans))
    monkeypatch.setattr(exam_material, "held_out_material", lambda *_args, **_kwargs: material)


def _served_with_history(tmp_path):
    """A plan serve whose frozen history card quotes ``pi_hist`` (made from span ``hist``)."""

    paths = ad_plan_vault(tmp_path, items=(*ITEMS, "pi_hist"))
    _set_fields(paths, "pi_hist", prompt=f"{SENTINEL}: a later exam question.", canonical_exercise=_exercise("hist"))
    for item_id in ITEMS:
        _set_fields(paths, item_id, canonical_exercise=_exercise(f"span_{item_id}"))
    env, clock = plan_env(paths)
    build_plan(env, kind="normal", budget=10.0, remembered=10, minutes_source="chip")
    stamp = (clock.now() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    with sqlite3.connect(paths.sqlite_path) as connection:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "correctness, hints_used, created_at) VALUES ('att_hist', 'pi_hist', 'lo_m1', 'short_answer', "
            "'independent_attempt', 1.0, 0, ?)", (stamp,))
    _record, step = advance(env, serve=True)
    assert step["kind"] == "item" and step["presentation_id"] and step["practice_item_id"] != "pi_hist"
    from learnloop.adaptive_difficulty.outside import frozen_state_key

    frozen = "\n".join(row[0] for row in sqlite3.connect(paths.sqlite_path).execute(
        "SELECT content_json FROM item_forecast_payloads WHERE owner_key = ?",
        (frozen_state_key(step["presentation_id"]),)))
    assert SENTINEL in frozen, "the serve froze the history item while it was ordinary practice"
    return paths, step


def _forecast(paths, step):
    from learnloop.adaptive_difficulty.outside import Clients, forecast_presentation

    llm, decider = ForecastLLM(p_correct=0.4), AuditDecider(p_yes=0.6)
    outcomes = forecast_presentation(load_vault(paths.root), Repository(paths.sqlite_path), step["presentation_id"],
                                     clients=Clients(llm=llm, decider=decider))
    return outcomes, llm, decider


# -- F11 [High]: the frozen history is revalidated against today's protection -----------------


@pytest.mark.parametrize("edited_after", [False, True], ids=["still_current", "revision_since_replaced"])
def test_frozen_history_marked_held_out_after_the_serve_is_never_sent(tmp_path, monkeypatch, edited_after):
    """F11: the background job checked protection only for the target item and
    sent the frozen history card unchanged, so a history item whose unit was
    marked held out after the serve reached the LLM and the Decider. Each
    included item's identity and own source references are now frozen with
    the card and revalidated before sending; any protected one refuses the
    forecast. ``revision_since_replaced``: the item's current revision is
    ordinary practice, but the frozen one (the text the card quotes) was
    made from the now held-out span."""

    paths, step = _served_with_history(tmp_path)
    if edited_after:
        _set_fields(paths, "pi_hist", prompt="An ordinary replacement question.", canonical_exercise=None)
    _hold_out(monkeypatch, "hist")
    outcomes, llm, decider = _forecast(paths, step)
    assert {outcome.status for outcome in outcomes} == {"protected"}
    assert llm.prompts == [] and decider.calls == []
    assert [row for row in ad_receipts(paths.sqlite_path) if row["forecaster"].startswith("llm_v3")] == []
    assert SENTINEL not in "\n".join(llm.prompts + [call["body"] for call in decider.calls])


def test_a_target_revision_held_out_after_the_serve_is_never_sent(tmp_path, monkeypatch):
    """F11: the target was judged by its *current* revision; a served revision
    made from a span marked held out after the serve, since replaced by an
    ordinary revision, was still sent from the frozen state."""

    paths, step = _served_with_history(tmp_path)
    served = step["practice_item_id"]
    _set_fields(paths, served, prompt="An ordinary replacement stem.", canonical_exercise=None)
    _hold_out(monkeypatch, f"span_{served}")
    outcomes, llm, decider = _forecast(paths, step)
    assert {outcome.status for outcome in outcomes} == {"protected"}
    assert llm.prompts == [] and decider.calls == []


def test_unprotected_frozen_inputs_are_still_sent_exactly(tmp_path, monkeypatch):
    # With protection unchanged since the serve (the AD23 redesign, E2: an unrelated span held out
    # since then now expires the frozen inputs, owner decision 2026-10-21; tests/test_ad_epoch.py).
    paths, step = _served_with_history(tmp_path)
    outcomes, llm, decider = _forecast(paths, step)
    assert sorted(outcome.status for outcome in outcomes) == ["ok", "ok"]
    assert SENTINEL in llm.prompts[0] and SENTINEL in decider.calls[0]["body"]


def test_frozen_inputs_without_their_source_identities_are_never_sent(tmp_path):
    """Fail closed: frozen inputs that cannot be revalidated are not sent."""

    import json

    from learnloop.adaptive_difficulty.outside import frozen_state_key

    paths, step = _served_with_history(tmp_path)
    key = frozen_state_key(step["presentation_id"])
    with sqlite3.connect(paths.sqlite_path) as connection:
        content = json.loads(connection.execute("SELECT content_json FROM item_forecast_payloads WHERE owner_key = ?",
                                                (key,)).fetchone()[0])
        content.pop("protection_identities")
        connection.execute("UPDATE item_forecast_payloads SET content_json = ? WHERE owner_key = ?",
                           (json.dumps(content), key))
    outcomes, llm, decider = _forecast(paths, step)
    assert {outcome.status for outcome in outcomes} == {"no_frozen_inputs"}
    assert llm.prompts == [] and decider.calls == []
    assert [row for row in ad_receipts(paths.sqlite_path) if row["forecaster"].startswith("llm_v3")] == []


# -- F12 [Medium]: an edit during a preparation keeps the new revision's job ------------------


class _GatedDecider(AuditDecider):
    """Holds the first audit until released, so a reload lands mid-preparation."""

    def __init__(self):
        super().__init__()
        self.entered = threading.Event()
        self.release = threading.Event()

    def decide(self, state, questions, *, purpose, timeout_seconds=None):
        self.entered.set()
        self.release.wait(10)
        return super().decide(state, questions, purpose=purpose, timeout_seconds=timeout_seconds)


def test_an_edit_during_a_preparation_prepares_the_new_revision_too(tmp_path):
    """F12: preparation jobs were keyed by item ids alone, so the job a reload
    scheduled for revision A2 while A1's was still running was discarded as
    already in flight; the next unchanged reload saw nothing new, and A2 was
    never audited or forecast. The job's identity now names each revision."""

    from learnloop.adaptive_difficulty.outside import Clients
    from learnloop_sidecar.context import SidecarContext

    paths = ad_plan_vault(tmp_path, config="[adaptive_difficulty]\noutside_forecasters = [\"llm_v1:item\"]\n")
    ctx = SidecarContext()
    decider, llm = _GatedDecider(), ForecastLLM(p_correct=0.5)
    ctx.ad_clients = Clients(llm=llm, decider=decider)
    try:
        ctx.load(paths.root)
        _set_fields(paths, "pi_m1b", prompt="Revision A1 of the stem.")
        ctx.reload(maintenance=False)
        assert decider.entered.wait(10), "A1's preparation is running"
        _set_fields(paths, "pi_m1b", prompt="Revision A2 of the stem.")
        ctx.reload(maintenance=False)
        decider.release.set()
        _wait_idle(ctx)
        ctx.reload(maintenance=False)
        _wait_idle(ctx)
        asked = sorted(call["state"]["question"] for call in decider.calls)
        assert asked == ["Revision A1 of the stem.", "Revision A2 of the stem."]
        item_receipts = [row for row in ad_receipts(paths.sqlite_path) if row["scope"] == "item"]
        assert len({row["item_content_hash"] for row in item_receipts}) == 2
    finally:
        decider.release.set()
        ctx.map_builds.close()


def _wait_idle(ctx, timeout: float = 30.0) -> None:
    deadline = time.monotonic() + timeout
    while ctx.map_builds.running and time.monotonic() < deadline:
        time.sleep(0.05)
    assert not ctx.map_builds.running


# -- F13 [Medium]: the worst case includes the permitted retry --------------------------------


METERED = """
[ai.providers.metered_test]
type = "openrouter"
model = "vendor/metered-model"
"""


def _metered_vault(tmp_path, cap: float):
    paths = ad_plan_vault(tmp_path, config=METERED + f"\n[adaptive_difficulty]\nprice_per_million = 2.0\n"
                                                      f"daily_spend_cap_usd = {cap}\n")
    config = paths.root / "learnloop.toml"
    text = config.read_text(encoding="utf-8")
    config.write_text(text.replace("\n[ai.routing]\n", '\n[ai.routing]\nad_forecast_llm = "metered_test"\n', 1),
                      encoding="utf-8")
    return paths


class _TruncatingMeteredLLM(ForecastLLM):
    provider_name = "metered_test"
    provider_type = "openrouter"
    model = "vendor/metered-model"

    def complete(self, request):
        from learnloop.ai.errors import AIOutputTruncated

        self.prompts.append(request.prompt)
        raise AIOutputTruncated("finish_reason = length")


def test_the_worst_case_plans_the_permitted_truncation_retry(tmp_path, monkeypatch):
    """F13: the plan budgeted one request per prompt at the first output
    allowance, while execution admits one truncation retry at twice it; a
    remaining cap between the two reported ``fits_today`` true. The plan now
    charges every permitted attempt at its own allowance, equal to what the
    execution reserves."""

    from learnloop.adaptive_difficulty.backfill import backfill
    from learnloop.adaptive_difficulty.outside import Clients, forecast_item
    from learnloop.practice_index import paid

    paths = _metered_vault(tmp_path / "big", cap=100.0)
    planned = backfill(load_vault(paths.root), Repository(paths.sqlite_path), audit=False, llm_v1=True,
                       reading=False, dry_run=True, limit=1)
    llm_plan = planned["llm_v1"]["llm"]
    worst = planned["spend"]["metered_worst_case_usd"]
    assert worst == pytest.approx(llm_plan["estimated_usd"])

    reserved: list[float] = []
    original = paid.PaidCalls.estimate

    def recording(self, tokens, **kwargs):
        estimate = original(self, tokens, **kwargs)
        reserved.append(float(estimate.estimated_usd or 0.0))
        return estimate

    monkeypatch.setattr(paid.PaidCalls, "estimate", recording)
    vault = load_vault(paths.root)
    # The plan's one prompt is the first never-attempted active item's.
    first = sorted(item_id for item_id, item in vault.practice_items.items()
                   if getattr(item, "status", "active") == "active")[0]
    client = _TruncatingMeteredLLM()
    outcome = forecast_item(vault, Repository(paths.sqlite_path), vault.practice_items[first],
                            clients=Clients(llm=client))
    monkeypatch.setattr(paid.PaidCalls, "estimate", original)
    assert outcome.status == "failed" and len(client.prompts) == 2, "one truncation retry was admitted"
    assert sum(reserved) == pytest.approx(worst, rel=1e-6)
    first_attempt = reserved[0]
    assert worst > first_attempt * 2

    between = round((first_attempt + worst) / 2, 6)
    tight = _metered_vault(tmp_path / "tight", cap=between)
    plan = backfill(load_vault(tight.root), Repository(tight.sqlite_path), audit=False, llm_v1=True,
                    reading=False, dry_run=True, limit=1)
    assert plan["spend"]["fits_today"] is False
    assert plan["llm_v1"]["llm"]["attempts_per_call"] == 2
