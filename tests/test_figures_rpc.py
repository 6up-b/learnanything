"""Reader RW5a RPCs: caps, exam protection, reuse, switches and events (spec §8.5, §8.6, W9, W10, G19).

Every model is a fake. The caps are counted on the fakes: at most two author
attempts and one verifier call per request; a metered route is held to
``figures.max_daily_cost_usd`` at ``figures.price_per_million``, and refused
before sending when unpriced or spent. Exam and held-out material is refused
before any call. The same input is reused with no call.
"""

from __future__ import annotations

import json

import pytest

from learnloop.reader import reader_inquiry as RI
from learnloop_sidecar.errors import SidecarError
from tests.figure_fixtures import (
    EXTRACTION,
    LEARNING_STATE_TABLES,
    AuthorFake,
    VerifierFake,
    build,
    build_figure_vault,
    call,
    context,
    counts,
    flagship,
    half_density,
    rows,
    set_config,
)


def _vault(tmp_path):
    return build_figure_vault(tmp_path / "vault")


def test_the_prompt_contract_and_the_intent_box_carry_figures_while_on(tmp_path):
    paths, _repository = _vault(tmp_path)
    ctx = context(paths.root)
    contract = call(ctx, "reader.prompt_contract", {})
    # RW5b adds offers (figures.offers_enabled, on by default).
    assert contract["figures"] == {"predictions": True, "region": True, "revisions": True, "offers": True}
    actions = {action["id"]: action for group in contract["intent"]["palette"] for action in group["actions"]}
    assert actions["make_explorable"]["effect"] == {"kind": "figure"}
    assert actions["make_explorable"]["intention"] == "understand"
    notes = {action["id"] for group in contract["intent"]["notesPalette"] for action in group["actions"]}
    assert "make_explorable" not in notes


def test_switched_off_every_rpc_refuses_and_no_route_is_called(tmp_path):
    paths, repository = _vault(tmp_path)
    set_config(paths, "figures", enabled=False)
    author = AuthorFake()
    ctx = context(paths.root, author=author, verifier=VerifierFake())
    contract = call(ctx, "reader.prompt_contract", {})
    assert "figures" not in contract
    actions = {action["id"] for group in contract["intent"]["palette"] for action in group["actions"]}
    assert "make_explorable" not in actions
    for name, params in (
        ("reader.figure_request", {"extractionId": EXTRACTION, "spanIds": ["p3"]}),
        ("reader.figure_revise", {"figureId": "fig_x", "note": "x"}),
        ("reader.figure_job", {"jobId": "ljob_x"}),
        ("reader.figure_job_cancel", {"jobId": "ljob_x"}),
        ("reader.figures", {"extractionId": EXTRACTION}),
        ("reader.figure_predict", {"figureId": "fig_x", "predictionIndex": 0, "answer": "same"}),
        ("reader.figure_explain", {"predictionId": "fpr_x", "text": "x"}),
    ):
        with pytest.raises(SidecarError) as caught:
            call(ctx, name, params)
        assert caught.value.code == "figures_disabled", name
    assert author.calls == 0
    assert counts(repository, ["interactive_figures", "figure_predictions"]) == {
        "interactive_figures": 0, "figure_predictions": 0}


def test_held_out_material_is_refused_before_any_call(tmp_path):
    paths, repository = _vault(tmp_path)
    author = AuthorFake()
    ctx = context(paths.root, author=author)
    before = len(rows(repository, "interaction_events"))
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.figure_request", {"extractionId": "ext_exam", "spanIds": ["s1"]})
    assert caught.value.code == "exam_material"
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.figure_request", {"extractionId": "ext_exam", "spanIds": [],
                                            "region": {"spanId": "s1", "bbox": [0, 0, 10, 10]}})
    assert caught.value.code == "exam_material"
    assert author.calls == 0 and len(rows(repository, "interaction_events")) == before
    assert not rows(repository, "interactive_figures")


def test_a_figure_whose_passage_becomes_held_out_is_not_shown(tmp_path):
    from tests.figure_fixtures import upsert_source_set

    paths, repository = _vault(tmp_path)
    ctx = context(paths.root, author=AuthorFake([flagship(kind="illustrative")]))
    figure = build(ctx)["figure"]
    assert [f["figureId"] for f in call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"]] == [
        figure["figureId"]]
    upsert_source_set(paths.root, {
        "id": "sset_la", "subject_id": "linear-algebra", "title": "Linear algebra sources",
        "members": [{"source_id": "src_prob", "revision_id": "rev_prob", "default_role": "exam"}],
    })
    ctx = context(paths.root)
    assert call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"] == []
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.figure_predict", {"figureId": figure["figureId"], "predictionIndex": 0, "answer": "same"})
    assert caught.value.code == "exam_material"


def test_held_out_neighbours_are_left_out_of_the_prompt(tmp_path):
    """Context paragraphs are source text of this book only, never held out."""

    paths, _repository = _vault(tmp_path)
    author = AuthorFake([flagship(kind="illustrative")])
    build(context(paths.root, author=author), {"extractionId": EXTRACTION, "spanIds": ["p3"]})
    (sent,) = author.contexts
    assert [block["span_id"] for block in sent["passage"]] == ["p3"]
    assert [block["span_id"] for block in sent["around"]] == ["p1", "p2", "p4", "p5"]
    prompt = author.prompts[0]
    for private in ("practice_attempts", "learner", "mastery", "grade"):
        assert private not in json.dumps(sent).lower() or private == "learner"
    assert "learner_note" not in sent and "earlier_version" not in sent
    assert "integral(expr, var, a, b)" in prompt  # the grammar is in the instructions


def test_reuse_by_input_hash_makes_no_call(tmp_path):
    paths, repository = _vault(tmp_path)
    author = AuthorFake([flagship(kind="illustrative")])
    ctx = context(paths.root, author=author)
    first = build(ctx)
    second = build(ctx)
    assert first["reused"] is False and second["reused"] is True
    assert second["figure"]["figureId"] == first["figure"]["figureId"]
    assert author.calls == 1 and len(rows(repository, "interactive_figures")) == 1
    # Another selection is another input.
    third = build(ctx, {"extractionId": EXTRACTION, "spanIds": ["p2", "p3"]})
    assert third["reused"] is False and author.calls == 2


def test_a_failed_build_is_not_reused_try_again_rebuilds(tmp_path):
    paths, repository = _vault(tmp_path)
    author = AuthorFake([half_density(), half_density(), flagship(kind="illustrative")])
    ctx = context(paths.root, author=author)
    assert build(ctx)["figure"]["verification"] == "failed"
    again = build(ctx)
    assert again["reused"] is False and again["figure"]["verification"] == "illustrative"
    assert author.calls == 3
    listed = call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"]
    assert [f["verification"] for f in listed] == ["failed", "illustrative"]


def test_caps_two_author_attempts_per_request_and_no_verifier(tmp_path):
    paths, _repository = _vault(tmp_path)
    author = AuthorFake(["not json", "still not json", flagship()])
    verifier = VerifierFake(fail=RuntimeError("down"))
    ctx = context(paths.root, author=author, verifier=verifier)
    assert build(ctx)["figure"]["verification"] == "failed"
    assert author.calls == 2
    figure = build(ctx, {"extractionId": EXTRACTION, "spanIds": ["p2", "p3"]})["figure"]
    # A reconstruction is an illustration; RW5a has no verifier route, so an
    # injected one is never asked (the source check is RW5c's).
    assert author.calls == 3 and verifier.calls == 0
    assert figure["verification"] == "illustrative"


def test_a_metered_route_needs_a_price_and_is_refused_before_sending(tmp_path):
    paths, _repository = _vault(tmp_path)
    author = AuthorFake(provider_type="openrouter")
    ctx = context(paths.root, author=author)
    with pytest.raises(SidecarError) as caught:
        build(ctx)
    assert caught.value.code == "unpriced" and author.calls == 0


def test_the_daily_cap_is_metered_inside_the_spend_machinery(tmp_path):
    paths, repository = _vault(tmp_path)
    # One metered call reserves about $0.22 at $10 per million tokens (its
    # worst case) and settles at its reported tokens; the second's reservation
    # would pass the $0.25 cap.
    set_config(paths, "figures", price_per_million=10.0, max_daily_cost_usd=0.25)
    author = AuthorFake([flagship(kind="illustrative"), flagship(kind="illustrative")], provider_type="openrouter")
    ctx = context(paths.root, author=author)
    build(ctx)
    with repository.connection() as connection:
        receipts = [dict(row) for row in connection.execute(
            "SELECT owner_kind, purpose FROM model_call_receipts WHERE purpose = 'figure_author'")]
        reservations = [dict(row) for row in connection.execute(
            "SELECT envelope, reserved_usd, charged_usd FROM source_service_spend "
            "WHERE envelope = 'figures.max_daily_cost_usd'")]
    assert receipts
    # The metered call reserved against the figures' own daily envelope.
    assert reservations and all(row["reserved_usd"] > 0 for row in reservations)
    (first,) = reservations
    # A cap that the next call's reservation (as large as the first's) would pass.
    cap = float(first["charged_usd"] or 0) + 0.9 * float(first["reserved_usd"])
    text = (paths.root / "learnloop.toml").read_text(encoding="utf-8")
    (paths.root / "learnloop.toml").write_text(text.replace("max_daily_cost_usd = 0.25", f"max_daily_cost_usd = {cap!r}"),
                                              encoding="utf-8")
    ctx = context(paths.root, author=author)
    with pytest.raises(SidecarError) as caught:
        build(ctx, {"extractionId": EXTRACTION, "spanIds": ["p2", "p3"]})
    assert caught.value.code == "capped" and author.calls == 1


def test_no_route_set_up_refuses_with_the_reason(tmp_path, monkeypatch):
    paths, _repository = _vault(tmp_path)
    ctx = context(paths.root)
    with pytest.raises(SidecarError) as caught:
        build(ctx)
    assert caught.value.code == "models_off"


def test_a_build_writes_no_learning_state(tmp_path):
    paths, repository = _vault(tmp_path)
    before = counts(repository, LEARNING_STATE_TABLES)
    build(context(paths.root, author=AuthorFake([flagship(kind="illustrative")])))
    assert counts(repository, LEARNING_STATE_TABLES) == before


def test_server_events_are_salience_only(tmp_path):
    from learnloop.attempts import salience_firewall as SF

    paths, repository = _vault(tmp_path)
    ctx = context(paths.root, author=AuthorFake([flagship(kind="illustrative"), flagship(kind="illustrative")],
                                                images=True))
    figure = build(ctx)["figure"]
    found = call(ctx, "reader.figure_predict", {"figureId": figure["figureId"], "predictionIndex": 0, "answer": "rises"})
    call(ctx, "reader.figure_explain", {"predictionId": found["predictionId"], "text": "p sets the split"})
    build(ctx, {"figureId": figure["figureId"], "note": "start λ at 0.5"}, rpc="reader.figure_revise")
    events = [row for row in repository.reader_interaction_events(kind="reader_action_invoked")
              if row["payload"].get("event", "").startswith("figure_")]
    seen = {row["payload"]["event"] for row in events}
    assert seen == set(RI.RW5A_SERVER_EVENTS) - {"figure_region_selected"}
    for row in events:
        assert row["payload"]["authority_class"] == SF.SALIENCE_ONLY
        with pytest.raises(SF.SalienceEvidenceRejected):
            SF.reject_salience(row)
        text = json.dumps(row["payload"])
        assert "p sets the split" not in text and "start λ" not in text
    assert {"figure_opened", "figure_animated"} <= set(RI.CLIENT_ACTION_EVENTS)
    assert not set(RI.RW5A_SERVER_EVENTS) & set(RI.CLIENT_ACTION_EVENTS)


def test_the_client_records_figure_opened_and_animated(tmp_path):
    paths, repository = _vault(tmp_path)
    ctx = context(paths.root)
    call(ctx, "reader.log_activity", {"events": [
        {"kind": "reader_action_invoked", "event": "figure_opened",
         "payload": {"figureId": "fig_1", "extractionId": EXTRACTION}},
        {"kind": "reader_action_invoked", "event": "figure_animated",
         "payload": {"figureId": "fig_1", "parameter": "lam", "extractionId": EXTRACTION, "words": "secret"}},
    ]})
    events = [row["payload"] for row in repository.reader_interaction_events(kind="reader_action_invoked")
              if row["payload"].get("event") in ("figure_opened", "figure_animated")]
    assert [event["event"] for event in events] == ["figure_opened", "figure_animated"]
    assert events[1]["parameter"] == "lam" and "words" not in events[1]
    with pytest.raises(SidecarError):
        call(ctx, "reader.log_activity", {"events": [
            {"kind": "reader_action_invoked", "event": "figure_predicted", "payload": {}}]})


def test_cancelled_build_never_answers(tmp_path):
    paths, _repository = _vault(tmp_path)
    ctx = context(paths.root, author=AuthorFake([flagship(kind="illustrative")]))
    job = call(ctx, "reader.figure_request", {"extractionId": EXTRACTION, "spanIds": ["p3"]})
    cancelled = call(ctx, "reader.figure_job_cancel", {"jobId": job["jobId"]})
    assert cancelled["state"] == "cancelled"
    assert call(ctx, "reader.figure_job", {"jobId": job["jobId"]})["state"] == "cancelled"


def test_validation_refusals(tmp_path):
    paths, _repository = _vault(tmp_path)
    ctx = context(paths.root, author=AuthorFake())
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.figure_request", {"extractionId": EXTRACTION, "spanIds": []})
    assert caught.value.code == "validation_error"
    with pytest.raises(SidecarError) as caught:
        build(ctx, {"extractionId": EXTRACTION, "spanIds": ["no_such_span"]})
    assert caught.value.code == "validation_error"
