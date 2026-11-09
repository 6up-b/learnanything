"""Reader RW6b part 2 landing onto main (docs/reviews/reader-rw6b-p2-digest-card.md, "Landing onto
main"): its interactions with curriculum C1 (mvp-0.40), which landed first.

(i) A Today build on a C1 plan (receipt ``reading_path_plan_v2``, the reading chosen by the
    deliverable) with an ended reader session waiting for its narrative: the background job
    narrates after planning, and C1's reading and receipt do not move. The narrative is a database
    write, so it invalidates C1's fresh-choice memo once (one recomputation, the same choice);
    afterwards the memo holds again.
(ii) The router card against a C1 plan: with ``digest.enabled`` off it is the predecessor's card
    byte for byte (payload, hash, text), as it is with digest on and nothing to say; with reader
    activity on the plan's LOs the card gains only its "Reader activity" section.
(iii) The narration's durable claim and the claims C1's path relies on (RW7b's reading-path claims,
    the one leased-claim table ``judgment_work_claims``): distinct keys and tasks, neither blocks or
    renews the other. C1's own deliverable judgments coalesce in process and take no claim row.

Every model is a fake; nothing leaves the machine.
"""
from __future__ import annotations

import json
from datetime import timedelta
from typing import Any

import pytest

from learnloop.daily_plan import engine as E
from learnloop.daily_plan import reading_choice as RCH
from learnloop.db.stores import reader_digests as RDG
from learnloop.instructional import reader_digest as RN
from tests.helpers import append_config_toml
from tests.reading_path_fixtures import call, context
from tests.test_curriculum_c1_plan_follows_path import _at, _c1, _split
from tests.test_reader_digest_narrative import NarrativeFake

DIGEST_ID = "rsd_landing_1"


def _digest(c1, *, los=("lo_eigen", "lo_det")) -> str:
    """An ended reader session's digest row on the C1 vault's book: part 1's "planned with no
    checks" row (so part 1 leaves it), waiting for its narrative."""

    moment = c1.clock.moment
    ended = (moment - timedelta(days=1)).isoformat()
    started = (moment - timedelta(days=1, minutes=40)).isoformat()
    summary = {
        "summary_version": "reader_session_summary_v1", "extraction_id": "ext_book", "activity": True,
        "learning_objects_touched": list(los), "facets_touched": [],
        "inquiries": {"opened": [{"root_exchange_id": "ex_landing", "question_event_id": "ev_landing",
                                  "span_ids": []}], "resolved": [], "still_open": []},
        "inquiry_exchanges": ["ex_landing"],
    }
    with c1.repository.connection() as connection:
        RDG.insert_digest(connection, {
            "id": DIGEST_ID, "extraction_id": "ext_book", "session_key": "v_landing", "visit_ids": ["v_landing"],
            "started_at": started, "ended_at": ended, "status": "planned", "summary": summary,
            "followup_commitment_ids": [], "valuation": {"questions": [], "chosen": [], "chosen_ids": []},
            "created_at": ended})
        connection.commit()
    return DIGEST_ID


def _digest_row(c1) -> dict[str, Any]:
    with c1.repository.connection() as connection:
        return RDG.digest(connection, DIGEST_ID)


def _reset(c1) -> None:
    with c1.repository.connection() as connection:
        connection.execute("DELETE FROM attention_block_events")
        connection.execute("DELETE FROM attention_blocks")
        connection.execute("DELETE FROM daily_plans")
        connection.commit()


def _today(c1, fake, monkeypatch) -> dict:
    """One Today build through the sidecar, its background jobs joined."""

    from learnloop_sidecar.background_jobs import background_jobs
    from learnloop_sidecar.handlers import reader_followups as handler

    monkeypatch.setattr(handler, "_now", lambda: c1.clock.moment)
    ctx = context(c1.paths.root, reader_digest_client=fake)
    try:
        call(ctx, "get_daily_plan", {})
        for thread in background_jobs(ctx).running:
            thread.join(timeout=60)
    finally:
        ctx.close()
    return _split(c1.repository)


# -- (i) the narrative job beside C1's reading ------------------------------------------------------------


# Production's lane on purpose: a Today build holds AD's read snapshot while its background job commits the narrative.
# In WAL a reader doesn't block that commit. The fast lane's rollback journal does, so there the job failed with
# "database is locked" whenever the two overlapped, which connection reuse made every run.
@pytest.mark.durability
def test_i_the_narrative_lands_after_a_c1_plan_and_c1s_reading_does_not_move(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch)
    _digest(c1)
    fake = NarrativeFake()
    split = _today(c1, fake, monkeypatch)
    assert split["reading_path"]["version"] == "reading_path_plan_v2"
    assert split["reading_path"]["chosen_by"] == "deliverable" and _at(split["reading"]) == ("ext_book", "ch_det")
    # The job narrated the waiting session once.
    assert fake.calls == 1 and _digest_row(c1)["narrative_md"] == fake.text
    # The next Today build (the narrative now written) chooses the same reading with the same receipt.
    _reset(c1)
    again = _today(c1, NarrativeFake(), monkeypatch)
    assert again["reading"] == split["reading"] and again["reading_path"] == split["reading_path"]


def test_i_a_narrative_write_invalidates_c1s_memo_once_and_the_choice_is_the_same(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch)
    _digest(c1)
    RCH.forget()
    computed: list[Any] = []
    real = E._fresh_reading_checked

    def counted(env, intent):
        result = real(env, intent)
        computed.append(result[:2])
        return result

    monkeypatch.setattr(E, "_fresh_reading_checked", counted)
    env = E.PlanEnv(c1.vault, c1.repository)
    first = E._remembered_fresh_reading(env)
    assert E._remembered_fresh_reading(env) == first and len(computed) == 1  # remembered
    result = RN.narrate_digest(c1.vault, c1.repository, DIGEST_ID, client=NarrativeFake(),
                               now=c1.clock.moment, clock=None)
    assert result.status == "narrated"
    # The narrative is a committed write: one miss, the same choice and receipt.
    after = E._remembered_fresh_reading(env)
    assert len(computed) == 2 and json.dumps(after, sort_keys=True, default=str) == json.dumps(
        first, sort_keys=True, default=str)
    assert _at(after[0]) == ("ext_book", "ch_det") and after[1]["chosen_by"] == "deliverable"
    # Nothing written since: remembered again.
    assert E._remembered_fresh_reading(env) == after and len(computed) == 2
    RCH.forget()


# -- (ii) the router card against a C1 plan ---------------------------------------------------------------


def _card(c1, monkeypatch):
    """The router's learner-state card for the C1 plan's first block, as the chooser builds it."""

    from learnloop.daily_plan.engine import _live_context, decide, get_or_create_today
    from learnloop.daily_plan.policy import policy_for
    from learnloop.vault.loader import load_vault

    vault = load_vault(c1.paths.root)
    env = E.PlanEnv(vault, c1.repository)
    env.policy = policy_for(vault, c1.repository, session_id="s_landing")
    record = get_or_create_today(env)
    ctx, _built = _live_context(env, record)
    decision = decide(record, ctx, env.policy.projection())
    return env.policy.chooser.card_builder(decision.state, decision.feasible), decision


def test_ii_digest_off_is_the_predecessor_card_byte_for_byte_on_a_c1_plan(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch)
    plain, decision = _card(c1, monkeypatch)
    plan = _split(c1.repository)  # the day's C1 plan the block is decided on
    assert plan["reading_path"]["chosen_by"] == "deliverable"
    assert plan["reading_path"]["version"] == "reading_path_plan_v2"
    los = sorted({lo for c in decision.feasible for lo in c.learning_object_ids})
    assert "reader_activity" not in plain.json["evidence_sections"]
    # A session narrated an hour earlier on the block's candidate LOs (the card reads strictly
    # before its decision time): the section appears, and only it.
    c1.clock.advance(hours=-1)
    _digest(c1, los=los)
    assert RN.narrate_digest(c1.vault, c1.repository, DIGEST_ID, client=NarrativeFake(),
                             now=c1.clock.moment).status == "narrated"
    c1.clock.advance(hours=1)
    on, _ = _card(c1, monkeypatch)  # the same day's plan record, at the same decision time
    section = on.json["evidence_sections"].get("reader_activity")
    assert section and section["narrative"]["digest_id"] == DIGEST_ID
    assert "# Reader activity" in on.text and on.card_hash != plain.card_hash
    stripped = {**on.json, "evidence_sections": {k: v for k, v in on.json["evidence_sections"].items()
                                                 if k != "reader_activity"}}
    assert json.dumps(stripped, sort_keys=True) == json.dumps(plain.json, sort_keys=True)
    # digest.enabled off: the predecessor's card exactly (payload, hash, text).
    append_config_toml(c1.paths.root, "[digest]\nenabled = false\n")
    off, _ = _card(c1, monkeypatch)
    assert off.payload() == plain.payload() and off.card_hash == plain.card_hash and off.text == plain.text


# -- (iii) the narration's claim and C1's claims ----------------------------------------------------------


def test_iii_the_narration_claim_and_the_reading_path_claims_are_distinct_and_independent(tmp_path, monkeypatch):
    from learnloop.hints import map_builder as claims
    from learnloop.source_retrieval import reading_paths as RP

    c1 = _c1(tmp_path, monkeypatch)
    _digest(c1)
    # C1's deliverable judgments coalesce in process: the vault holds no claim of theirs, only
    # RW7b's reading-path claims (if any were taken while C1's fixture judged its paths).
    with c1.repository.connection() as connection:
        before = [dict(r) for r in connection.execute(
            "SELECT claim_key, task, state, lease_owner, lease_expires_at, lease_epoch FROM judgment_work_claims "
            "ORDER BY claim_key")]
    assert all(not row["claim_key"].startswith(RN.CLAIM_TASK) for row in before)
    assert RN.CLAIM_TASK not in {row["task"] for row in before}
    key = RN.claim_key(DIGEST_ID)
    path_key = RP.claim_key("ext_book", "learn_to_use_it", "landing_state")
    assert RP.CLAIM_TASK != RN.CLAIM_TASK and not path_key.startswith(RN.CLAIM_TASK + ":")
    assert not key.startswith(RP.CLAIM_TASK + ":")
    lease = RN.narration_lease_seconds(RN.request_timeout_seconds(
        c1.vault, RN.NarrativeRoute(c1.vault, c1.repository, client=NarrativeFake(), envelope=None).route))
    with claims._claimed(c1.repository, DIGEST_ID, 0.0, key=key, task=RN.CLAIM_TASK, producer=RN.OWNER_KIND,
                         lease_seconds=lease) as held:
        assert held is not None
        # While the narration holds its claim, every other claim row is untouched...
        with c1.repository.connection() as connection:
            during = [dict(r) for r in connection.execute(
                "SELECT claim_key, task, state, lease_owner, lease_expires_at, lease_epoch FROM judgment_work_claims "
                "WHERE claim_key != ? ORDER BY claim_key", (key,))]
        assert during == before
        # ...and a reading-path claim can be taken and released beside it.
        other = claims._try_claim(c1.repository, "ext_book", key=path_key, task=RP.CLAIM_TASK)
        assert other is not None
        claims._release(c1.repository, other)
        # Neither renews or takes over the other: the narration still holds its own lease.
        with c1.repository.connection() as connection:
            assert claims._holds(connection, held)
        # The C1 plan builds while the narration's claim is held; the Today build's own narration
        # finds the claim held and sends nothing.
        fake = NarrativeFake()
        split = _today(c1, fake, monkeypatch)
        assert split["reading_path"]["chosen_by"] == "deliverable"
        assert fake.calls == 0 and _digest_row(c1)["prompt_version"] is None
    with c1.repository.connection() as connection:
        after = [dict(r) for r in connection.execute(
            "SELECT claim_key, task, state, lease_owner, lease_expires_at, lease_epoch FROM judgment_work_claims "
            "WHERE claim_key NOT IN (?, ?) ORDER BY claim_key", (key, path_key))]
    assert after == before
