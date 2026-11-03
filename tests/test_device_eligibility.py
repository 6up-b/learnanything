"""Mobile PR-6: device eligibility (spec_mobile_tailnet_v1 §6.4, G9).

``ineligibility_reason`` is the one decision; the host applies it at every door,
with the class from the request origin. The host here is a sidecar context acting
as a paired device (``ctx.acting_as``). With no origin, the desktop, nothing
filters and nothing changes.

Durability lane: production pragmas and WAL on fresh vaults (adoption is a
compare-and-swap, and the probe check commits and resumes a presentation).
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.diagnosis.probe_episodes import enter_episode
from learnloop.scheduling.device_eligibility import (
    DESKTOP,
    DESKTOP_ONLY_MODE,
    EMBEDS_IMAGE,
    ERROR_HUNT,
    LADDERED_STEM,
    LESSON_CHECK,
    LINKS_LLPDF,
    MULTI_TURN_TEACH_BACK,
    PHONE,
    REFERENCES_ITEM_ASSET,
    ineligibility_reason,
)
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.models import ErrorHuntContract, LadderedStemContract, TeachBackSourceContract
from learnloop.vault.writer import upsert_practice_item
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers import practice as practice_handlers
from learnloop_sidecar.registry import METHOD_REGISTRY
from learnloop_sidecar.request_origin import RequestOrigin

from tests.helpers import NOW, NOW_ISO, admit_probe_instrument_card, create_basic_vault, seed_due_item

pytestmark = pytest.mark.durability

PLAIN = "pi_svd_define_001"
HUNT = "pi_phone_hunt"
LADDER = "pi_phone_ladder"
IMAGE = "pi_phone_image"
ORIGIN = RequestOrigin(device_id="dev_phone")
CLOCK = FrozenClock(NOW)


def _call(ctx: SidecarContext, name: str, params: dict):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _payload(item_id: str, **extra) -> dict:
    return {
        "id": item_id,
        "learning_object_id": "lo_svd_definition",
        "subjects": None,
        "practice_mode": "short_answer",
        "attempt_types_allowed": ["independent_attempt"],
        "evidence_facets": ["recall"],
        "evidence_weights": {"recall": 1.0},
        "prompt": "Define the SVD.",
        "expected_answer": "A factorization into U, Sigma and V transpose.",
        "grading_rubric": {
            "max_points": 4,
            "criteria": [{"id": "correctness", "points": 4, "description": "Correct definition."}],
            "fatal_errors": [],
        },
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
        **extra,
    }


def _world(tmp_path):
    """A vault with due ordinary, error-hunt, laddered and image items."""

    paths = create_basic_vault(tmp_path / "vault", fresh=True)
    repository = seed_due_item(paths)
    items = {
        HUNT: _payload(HUNT, prompt="Correct the worked solution below.", error_hunt={
            "worked_solution_md": "Step 1: S is orthogonal.",
            "planted_errors": [{
                "id": "pe_one", "step_ref": "step 1", "source": "facet_error_signature",
                "error_signature": "S is orthogonal", "required_repair": "S is diagonal", "facet_id": "recall",
            }],
        }),
        LADDER: _payload(LADDER, prompt="Part 2: which factor?", laddered_stem={
            "stem_id": "stem_svd", "part_index": 1, "part_count": 3, "stimulus_md": "Take a 3 by 2 matrix.",
        }),
        IMAGE: _payload(IMAGE, prompt="Which matrix is drawn here?\n\n![the matrix](figures/matrix.png)"),
    }
    for item_id, payload in items.items():
        upsert_practice_item(paths.root, payload, clock=CLOCK)
        repository.upsert_practice_item_state(
            item_id, difficulty=5.0, stability=2.0, due_at="2026-05-18T12:00:00Z",
            last_attempt_at="2026-05-16T12:00:00Z", active=True,
        )
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO mobile_devices (id, label, scope, token_hash, created_at) "
            "VALUES (?, 'Phone', 'app', 'hash', '2026-11-03T00:00:00Z')",
            (ORIGIN.device_id,),
        )
        connection.commit()
    ctx = SidecarContext()
    ctx.load_secondary(paths.root)
    ctx.grading_provider_override = "manual"
    return paths, repository, ctx


def _ids(queue: dict) -> list[str]:
    return [item["practiceItemId"] for section in queue["sections"] for item in section["items"]]


def _decisions(repository: Repository) -> list[dict]:
    with repository.connection() as connection:
        return [dict(row) for row in connection.execute(
            "SELECT surface, exclusions_json, chosen_practice_item_id FROM router_decisions "
            "WHERE decision_kind = 'today_offer' ORDER BY rowid"
        )]


# -- the decision ----------------------------------------------------------


@pytest.fixture(scope="module")
def item(tmp_path_factory):
    paths = create_basic_vault(tmp_path_factory.mktemp("eligibility") / "vault")
    return load_vault(paths.root).practice_items[PLAIN]


def _lesson_provenance(item):
    return item.provenance.model_copy(update={"mechanism": "teacher_lesson_v1"})


@pytest.mark.parametrize("update, reason", [
    ({"error_hunt": ErrorHuntContract(worked_solution_md="x", planted_errors=[])}, ERROR_HUNT),
    ({"laddered_stem": LadderedStemContract(stem_id="s", part_index=0, part_count=2, stimulus_md="x")}, LADDERED_STEM),
    ({"practice_mode": "teach_back"}, MULTI_TURN_TEACH_BACK),
    ({"practice_mode": "diagnostic_microprobe"}, DESKTOP_ONLY_MODE),
])
def test_each_contract_reason_is_returned_for_the_phone_and_never_for_the_desktop(item, update, reason):
    changed = item.model_copy(update=update)
    assert ineligibility_reason(None, changed, PHONE) == reason
    assert ineligibility_reason(None, changed, DESKTOP) is None


def test_a_teach_back_source_on_any_mode_is_the_multi_turn_reason(item):
    source = TeachBackSourceContract.model_construct()
    assert ineligibility_reason(None, item.model_copy(update={"teach_back_source": source}), PHONE) == MULTI_TURN_TEACH_BACK


def test_a_lessons_own_held_check_stays_in_its_lesson(item):
    changed = item.model_copy(update={"provenance": _lesson_provenance(item)})
    assert ineligibility_reason(None, changed, PHONE) == LESSON_CHECK


@pytest.mark.parametrize("prompt, reason", [
    ("Look.\n\n![a triangle](figures/t.png)", EMBEDS_IMAGE),
    ("![remote](https://example.org/t.png)", EMBEDS_IMAGE),
    ("![reference style][fig1]", EMBEDS_IMAGE),
    ('Look: <img src="x.png">', EMBEDS_IMAGE),
    ("See [page 3](llpdf://source/abc#page=3).", LINKS_LLPDF),
    ("Bare llpdf://source/abc", LINKS_LLPDF),
    ("See [the sheet](assets/sheet.pdf).", REFERENCES_ITEM_ASSET),
    ("See [the sheet](sheet.csv).", REFERENCES_ITEM_ASSET),
    ("See [the sheet](file:///tmp/sheet.csv).", REFERENCES_ITEM_ASSET),
])
def test_a_prompt_that_needs_more_than_text_is_kept_for_the_desktop(item, prompt, reason):
    assert ineligibility_reason(None, item.model_copy(update={"prompt": prompt}), PHONE) == reason


@pytest.mark.parametrize("prompt", [
    "Define the SVD.",
    # §6.4: text cues are logged as suspected_figure in M2's report, never filtered.
    "See the figure below and name the matrix.",
    "Using Figure 2.3, compute the rank.",
    "As in the diagram above, what is the angle?",
    # Links a phone can follow.
    "Read [the note](https://example.org/note) first.",
    "See [above](#setup).",
    # Mathematics and code are not Markdown links or images.
    "On the interval [0,1](x) is continuous.",
    "Compute $n![k](x)$ for small $n$.",
    "Show that \\(a![b](c.png)\\) holds.",
    "$$ 5![2](3.5) $$",
    "What does `![alt](x.png)` render as?",
    "What does this print?\n\n```\n![alt](x.png)\nllpdf://nope\n```\n",
])
def test_plain_text_mathematics_and_text_cues_stay_eligible(item, prompt):
    assert ineligibility_reason(None, item.model_copy(update={"prompt": prompt}), PHONE) is None


def test_item_kinds_landed_since_the_spec_keep_the_ordinary_answer(item):
    """A textbook exercise (the workbench's item, a figure's host, a delayed check's
    pick) is plain text to the decision: nothing about it needs a desktop."""

    from learnloop.vault.models import CanonicalExercise

    exercise = CanonicalExercise(source_id="src", extraction_id="ext", span_ids=["s1"])
    assert ineligibility_reason(None, item.model_copy(update={"canonical_exercise": exercise}), PHONE) is None


# -- the doors -------------------------------------------------------------


def test_the_phone_queue_filters_before_the_offer_and_counts_what_waits(tmp_path):
    _paths, repository, ctx = _world(tmp_path)
    with ctx.acting_as(ORIGIN):
        session = _call(ctx, "start_session", {"availableMinutes": 60})
        queue = _call(ctx, "get_today_queue", {"sessionId": session["sessionId"]})

    assert _ids(queue) == [PLAIN]
    assert queue["totalItems"] == 1
    assert queue["deviceDeferredCount"] == 3

    # The receipt says what the phone showed, not what the build ranked.
    slate = repository.latest_scheduler_slate_by_session(session["sessionId"])
    with repository.connection() as connection:
        receipt = connection.execute(
            "SELECT entry_surface, returned_candidate_ids_json FROM scheduler_offer_receipts WHERE slate_id = ?",
            (slate["id"],),
        ).fetchone()
    assert receipt["entry_surface"] == "phone_queue"
    candidates = repository.scheduler_slate_candidates(slate["id"])
    by_id = {row["id"]: row["practice_item_id"] for row in candidates}
    import json

    assert [by_id[candidate] for candidate in json.loads(receipt["returned_candidate_ids_json"])] == [PLAIN]


def test_the_router_logs_the_filtered_items_and_never_chooses_one(tmp_path):
    _paths, repository, ctx = _world(tmp_path)
    with ctx.acting_as(ORIGIN):
        session = _call(ctx, "start_session", {"availableMinutes": 60})
        _call(ctx, "get_today_queue", {"sessionId": session["sessionId"]})

    decisions = _decisions(repository)
    assert decisions
    import json

    exclusions = json.loads(decisions[-1]["exclusions_json"])
    assert sorted(exclusions["named"]["device_ineligible"]) == sorted([HUNT, LADDER, IMAGE])
    assert decisions[-1]["chosen_practice_item_id"] in (PLAIN, None)


def test_the_desktop_queue_is_unfiltered_and_has_no_count(tmp_path):
    """G9: no origin, no filter, no new key, no new router name."""

    _paths, repository, ctx = _world(tmp_path)
    session = _call(ctx, "start_session", {"availableMinutes": 60})
    queue = _call(ctx, "get_today_queue", {"sessionId": session["sessionId"]})

    assert sorted(_ids(queue)) == sorted([PLAIN, HUNT, LADDER, IMAGE])
    assert "deviceDeferredCount" not in queue
    assert set(queue) == {
        "version", "generatedAt", "sessionId", "sections", "totalItems", "deferredColdChecks", "reentryRefresherCap",
    }
    assert "device_ineligible" not in _decisions(repository)[-1]["exclusions_json"]


def test_a_skip_on_the_phone_rebuilds_with_the_same_filter(tmp_path):
    paths, repository, ctx = _world(tmp_path)
    upsert_practice_item(paths.root, _payload("pi_phone_plain_two"), clock=CLOCK)
    repository.upsert_practice_item_state(
        "pi_phone_plain_two", difficulty=5.0, stability=2.0, due_at="2026-05-18T12:00:00Z",
        last_attempt_at="2026-05-16T12:00:00Z", active=True,
    )
    ctx.load_secondary(paths.root)
    ctx.grading_provider_override = "manual"
    with ctx.acting_as(ORIGIN):
        session = _call(ctx, "start_session", {"availableMinutes": 60})
        first = _ids(_call(ctx, "get_today_queue", {"sessionId": session["sessionId"]}))
        requeued = _call(ctx, "skip_practice_item", {"sessionId": session["sessionId"], "practiceItemId": first[0]})
    assert set(first) == {PLAIN, "pi_phone_plain_two"}
    assert _ids(requeued) == [item for item in first if item != first[0]]


@pytest.mark.parametrize("name", ["open_queue_item", "get_practice_item", "get_probe_contract"])
@pytest.mark.parametrize("item_id, reason", [(HUNT, ERROR_HUNT), (LADDER, LADDERED_STEM), (IMAGE, EMBEDS_IMAGE)])
def test_a_by_id_door_refuses_what_the_phone_cannot_answer(tmp_path, name, item_id, reason):
    _paths, _repository, ctx = _world(tmp_path)
    with ctx.acting_as(ORIGIN), pytest.raises(SidecarError) as refused:
        _call(ctx, name, {"practiceItemId": item_id})
    assert refused.value.code == "desktop_only" and not refused.value.retryable
    assert refused.value.details == {"practice_item_id": item_id, "reason": reason}

    # The same door serves the desktop, and the phone an ordinary item.
    _call(ctx, name, {"practiceItemId": item_id})
    with ctx.acting_as(ORIGIN):
        _call(ctx, name, {"practiceItemId": PLAIN})


def test_a_session_serve_on_the_phone_is_refused_too(tmp_path):
    _paths, _repository, ctx = _world(tmp_path)
    with ctx.acting_as(ORIGIN):
        session = _call(ctx, "start_session", {"availableMinutes": 60})
        with pytest.raises(SidecarError) as refused:
            _call(ctx, "get_practice_item", {"practiceItemId": HUNT, "sessionId": session["sessionId"]})
    assert refused.value.code == "desktop_only"


def test_an_unknown_item_keeps_its_not_found(tmp_path):
    _paths, _repository, ctx = _world(tmp_path)
    with ctx.acting_as(ORIGIN), pytest.raises(SidecarError) as missing:
        _call(ctx, "open_queue_item", {"practiceItemId": "pi_never"})
    assert missing.value.code == "not_found"


# -- adoption --------------------------------------------------------------


def test_adopting_a_draft_on_an_item_the_phone_cannot_answer_is_refused(tmp_path):
    _paths, repository, ctx = _world(tmp_path)
    session_id = _call(ctx, "start_session", {"availableMinutes": 60})["sessionId"]
    _call(ctx, "save_practice_draft", {"sessionId": session_id, "practiceItemId": HUNT, "answerMd": "my repair"})

    with ctx.acting_as(ORIGIN), pytest.raises(SidecarError) as refused:
        _call(ctx, "adopt_session", {"sessionId": session_id, "expectedGeneration": 0})

    assert refused.value.code == "current_item_desktop_only"
    assert refused.value.details["has_draft"] is True and refused.value.details["current_practice_item_id"] == HUNT
    assert repository.fetch_session(session_id)["owner_device_id"] is None
    assert repository.fetch_session_checkpoint(session_id)["current_answer"] == "my repair"
    assert repository.session_handoffs(session_id) == []


def test_adopting_with_no_draft_proceeds_and_the_item_is_what_is_refused(tmp_path):
    _paths, repository, ctx = _world(tmp_path)
    session_id = _call(ctx, "start_session", {"availableMinutes": 60})["sessionId"]
    repository.update_session_checkpoint(session_id, current_practice_item_id=HUNT, current_answer="")

    with ctx.acting_as(ORIGIN):
        adopted = _call(ctx, "adopt_session", {"sessionId": session_id, "expectedGeneration": 0})
        with pytest.raises(SidecarError) as refused:
            _call(ctx, "open_queue_item", {"practiceItemId": HUNT})

    assert adopted["ownerDeviceId"] == ORIGIN.device_id and adopted["ownerGeneration"] == 1
    assert refused.value.code == "desktop_only"


def test_adopting_an_eligible_draft_carries_it_and_a_stale_generation_is_refused(tmp_path):
    _paths, repository, ctx = _world(tmp_path)
    session_id = _call(ctx, "start_session", {"availableMinutes": 60})["sessionId"]
    _call(ctx, "save_practice_draft", {"sessionId": session_id, "practiceItemId": PLAIN, "answerMd": "half"})

    with ctx.acting_as(ORIGIN):
        with pytest.raises(SidecarError) as stale:
            _call(ctx, "adopt_session", {"sessionId": session_id, "expectedGeneration": 7})
        assert stale.value.code == "session_moved"
        adopted = _call(ctx, "adopt_session", {"sessionId": session_id, "expectedGeneration": 0})

    assert adopted["hasDraft"] is True and adopted["sessionId"] == session_id
    assert repository.fetch_session_checkpoint(session_id)["current_answer"] == "half"
    # The desktop asks no eligibility question when it adopts back.
    back = _call(ctx, "adopt_session", {"sessionId": session_id, "expectedGeneration": 1})
    assert back["ownerDeviceId"] is None and back["ownerLabel"] == "desktop"


# -- §6.4's implementation check before M2 ------------------------------------


def _probe_world(tmp_path, monkeypatch):
    paths = create_basic_vault(tmp_path / "vault", fresh=True)
    repository = Repository(paths.sqlite_path)
    admit_probe_instrument_card(repository)
    loaded = load_vault(paths.root)
    sync_vault_state(loaded, repository)
    episode = enter_episode(loaded, repository, "lo_svd_definition")
    assert episode.status == "in_progress"
    monkeypatch.setattr(
        practice_handlers, "ready_grading_provider",
        lambda _vault, override=None: ("test", SimpleNamespace(ready=True), object()),
    )
    ctx = SidecarContext()
    ctx.load_secondary(paths.root)
    return paths, repository, ctx, episode


def test_a_presentation_committed_on_the_phone_resumes_on_the_desktop(tmp_path, monkeypatch):
    """The phone commits the serve (§6.4), does not render it, and the learner
    continues on the desktop: the same session, adopted back, reopens the same
    presentation, as after the app closes mid-item. So ``ineligibility_reason``
    does not have to exclude probe-capable items at queue time."""

    paths, repository, ctx, episode = _probe_world(tmp_path, monkeypatch)
    with ctx.acting_as(ORIGIN):
        session_id = _call(ctx, "start_session", {"availableMinutes": 60})["sessionId"]
        queue = _call(ctx, "get_today_queue", {"sessionId": session_id})
        assert PLAIN in _ids(queue)
        on_phone = _call(ctx, "get_probe_contract", {"practiceItemId": PLAIN, "sessionId": session_id})
    assert on_phone["active"] is True
    served = repository.active_probe_presentation(episode.id)
    assert served.id == on_phone["presentationId"] and served.status == "served"

    # The desktop, fresh: the phone moved on without answering it.
    generation = repository.fetch_session(session_id)["owner_generation"]
    desktop = SidecarContext()
    desktop.load_secondary(paths.root)
    _call(desktop, "adopt_session", {"sessionId": session_id, "expectedGeneration": generation})
    resumed = _call(desktop, "get_probe_contract", {"practiceItemId": PLAIN, "sessionId": session_id})

    assert resumed["active"] is True and resumed["presentationId"] == on_phone["presentationId"]
    rows = [row for row in repository.probe_presentations_for_episode(episode.id)
            if row.status in ("selected", "served")]
    assert [row.id for row in rows] == [on_phone["presentationId"]]
