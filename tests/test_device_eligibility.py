"""Mobile PR-6: device eligibility (spec_mobile_tailnet_v1 §6.4, G9).

``ineligibility_reason`` is the one decision; the host applies it at every door,
with the class from the request origin. The host here is a sidecar context acting
as a paired device (``ctx.acting_as``). With no origin, the desktop, nothing
filters and nothing changes.

Durability lane: production pragmas and WAL on fresh vaults (adoption is a
compare-and-swap, and the probe check commits and resumes a presentation).
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.diagnosis.probe_episodes import enter_episode
from learnloop.scheduling import device_eligibility
from learnloop.scheduling.device_eligibility import (
    DESKTOP,
    DEVICE_POLICY,
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
from learnloop_sidecar.handlers import queue as queue_handlers
from learnloop_sidecar.registry import METHOD_REGISTRY
from learnloop_sidecar.request_origin import RequestOrigin

from tests.source_service_fakes import set_config
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
    ('Look: <img src="x.png">', EMBEDS_IMAGE),
    ("See [page 3](llpdf://source/abc#page=3).", LINKS_LLPDF),
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


def test_what_the_phone_left_for_the_desktop_is_held_back_from_its_next_build(tmp_path, monkeypatch):
    """M2a, open item 3: a committed, unrendered check is not the head of the next list, so an
    answer after it is that offer's head and no learner pick. It stays the session's assignment."""

    paths, repository, ctx, episode = _probe_world(tmp_path, monkeypatch)
    with ctx.acting_as(ORIGIN):
        session_id = _call(ctx, "start_session", {"availableMinutes": 60})["sessionId"]
        assert PLAIN in _ids(_call(ctx, "get_today_queue", {"sessionId": session_id}))
        contract = _call(ctx, "get_probe_contract", {"practiceItemId": PLAIN, "sessionId": session_id})
        assert contract["active"] is True
        queue = _call(ctx, "get_today_queue", {"sessionId": session_id})
    assert PLAIN not in _ids(queue)
    assert queue["deviceDeferredCount"] >= 1
    # Not ended: the desktop resumes the same presentation.
    assert repository.active_probe_presentation(episode.id).id == contract["presentationId"]
    desktop = SidecarContext()
    desktop.load_secondary(paths.root)
    generation = repository.fetch_session(session_id)["owner_generation"]
    _call(desktop, "adopt_session", {"sessionId": session_id, "expectedGeneration": generation})
    assert PLAIN in _ids(_call(desktop, "get_today_queue", {"sessionId": session_id}))
    desktop.close()


# -- Codex review F3: what the renderer resolves, not only what the source looks like


@pytest.mark.parametrize("prompt, reason", [
    # A shortcut, a collapsed and a full reference image: each renders an image.
    ("![graph] What is its slope?\n\n[graph]: figures/graph.png", EMBEDS_IMAGE),
    ("![graph][] What is its slope?\n\n[graph]: figures/graph.png", EMBEDS_IMAGE),
    ("![the graph][fig1]\n\n[fig1]: https://example.org/graph.png", EMBEDS_IMAGE),
    # A reference link whose definition names a file.
    ("Use [the data][sheet] to compute the mean.\n\n[sheet]: assets/observations.csv", REFERENCES_ITEM_ASSET),
    ("Use [sheet] to compute the mean.\n\n[sheet]: assets/observations.csv", REFERENCES_ITEM_ASSET),
    ("Use [sheet][] to compute the mean.\n\n[sheet]: <assets/observations.csv>", REFERENCES_ITEM_ASSET),
    ('Use [sheet].\n\n[Sheet]: observations.csv "The data"', REFERENCES_ITEM_ASSET),
    # An autolink to a local file is a link too.
    ("Open <file:///tmp/sheet.csv> first.", REFERENCES_ITEM_ASSET),
    # An image inside a link still embeds an image.
    ("[![a triangle](t.png)](https://example.org)", EMBEDS_IMAGE),
    ('<div><img src="x.png"></div>', EMBEDS_IMAGE),
])
def test_reference_forms_resolve_as_the_renderer_resolves_them(item, prompt, reason):
    assert ineligibility_reason(None, item.model_copy(update={"prompt": prompt}), PHONE) == reason


@pytest.mark.parametrize("prompt", [
    # No definition: the renderer shows these brackets as text, on every device.
    "![graph] What is its slope?",
    "![reference style][fig1]",
    "Use [the data][sheet] to compute the mean.",
    "Let [A] and [B] be the concentrations.",
    "Compute n![k][j] by hand.",
    # A definition nothing uses renders nothing.
    "Define the SVD.\n\n[sheet]: assets/observations.csv",
    # A reference to a page a phone can follow.
    "Read [the note][n] first.\n\n[n]: https://example.org/note",
    # Indented code is code.
    "What does this print?\n\n    ![alt](x.png)\n",
    # An unclosed tag is text.
    "Is a <img b true?",
])
def test_brackets_the_renderer_shows_as_text_stay_eligible(item, prompt):
    assert ineligibility_reason(None, item.model_copy(update={"prompt": prompt}), PHONE) is None


# -- Sol verify V2 (ruling R3): the four cases where the scan and the renderer disagreed


@pytest.mark.parametrize("prompt", [
    # A protocol-relative link is a page a phone can follow, not a file.
    "Read [the definition](//en.wikipedia.org/wiki/Derivative) first.",
    "Read [the definition][d] first.\n\n[d]: //en.wikipedia.org/wiki/Derivative",
    # A GFM footnote renders as text, and CommonMark alone reads it as a reference.
    "Explain this result.[^1]\n\n[^1]: arxiv.org/abs/1234.5678",
    "Explain this result.[^note] And this.[^2]\n\n[^note]: figures/old.png\n  [^2]: notes/a.md\n",
    # llpdf:// as text: code stays code, prose mentioning it is prose.
    "What does this print?\n\n    llpdf://source/abc\n",
    "What scheme is `llpdf://source/abc`?",
    "The desktop's links start with llpdf:// and open a page.",
    "Bare llpdf://source/abc",
])
def test_what_the_renderer_shows_as_text_or_a_web_link_stays_eligible(item, prompt):
    assert ineligibility_reason(None, item.model_copy(update={"prompt": prompt}), PHONE) is None


@pytest.mark.parametrize("prompt, reason", [
    # An escaped dollar opens no math, so the image between two of them is an image.
    ("Budget \\$5. Use ![the graph](graph.png). Budget \\$10.", EMBEDS_IMAGE),
    # llpdf:// as a rendered target, however it is written.
    ("See [page 3](llpdf://source/abc#page=3).", LINKS_LLPDF),
    ("See <llpdf://source/abc>.", LINKS_LLPDF),
    ("See [page 3][p].\n\n[p]: llpdf://source/abc", LINKS_LLPDF),
    ("![page](llpdf://source/abc)", LINKS_LLPDF),
    ('See <a href="llpdf://source/abc">page 3</a>.', LINKS_LLPDF),
    ("LLPDF in capitals: [page 3](LLPDF://source/abc).", LINKS_LLPDF),
    # A link's reason outranks an image's, as it always did.
    ("![g](g.png) and [page 3](llpdf://source/abc)", LINKS_LLPDF),
    # A footnote beside a real image or asset leaves them what they are.
    ("Name it.[^1]\n\n![g](g.png)\n\n[^1]: a note", EMBEDS_IMAGE),
    ("Name it.[^1] See [data](assets/a.csv).\n\n[^1]: a note", REFERENCES_ITEM_ASSET),
    # An image whose alt text starts with a caret is an image.
    ("![^1](g.png)", EMBEDS_IMAGE),
])
def test_what_the_renderer_resolves_is_still_kept_for_the_desktop(item, prompt, reason):
    assert ineligibility_reason(None, item.model_copy(update={"prompt": prompt}), PHONE) == reason


@pytest.mark.parametrize("prompt", [
    "Compute $n![k](x)$ and then \\$5.",
    "Two backslashes are one: \\\\$n![k](x)$ is math.",
    "Show that \\(a![b](c.png)\\) holds, for \\$5.",
])
def test_an_escape_changes_only_the_delimiter_it_escapes(item, prompt):
    assert ineligibility_reason(None, item.model_copy(update={"prompt": prompt}), PHONE) is None


# -- Codex review F1, F2: the filter sits inside the build, before the cut


LOW_IMAGE = "pi_zzz_image"
LOW_PLAIN = "pi_aaa_plain"
NEXT_PLAIN = "pi_aab_plain"
TOP_HUNT = "pi_aaa_a_hunt"


def _ranked_world(tmp_path, *, explore: bool = False):
    """Near-tied due items, ranked by id: two plain ones above an image, or a hunt on top."""

    paths = create_basic_vault(tmp_path / "vault", fresh=True)
    repository = seed_due_item(paths)
    hunt = {"error_hunt": {
        "worked_solution_md": "Step 1: S is orthogonal.",
        "planted_errors": [{
            "id": "pe_one", "step_ref": "step 1", "source": "facet_error_signature",
            "error_signature": "S is orthogonal", "required_repair": "S is diagonal", "facet_id": "recall",
        }],
    }}
    for item_id, extra in {
        LOW_PLAIN: {}, NEXT_PLAIN: {}, TOP_HUNT: hunt,
        LOW_IMAGE: {"prompt": "Which matrix?\n\n![the matrix](figures/matrix.png)"},
    }.items():
        upsert_practice_item(paths.root, _payload(item_id, **extra), clock=CLOCK)
        repository.upsert_practice_item_state(
            item_id, difficulty=5.0, stability=2.0, due_at="2026-05-18T12:00:00Z",
            last_attempt_at="2026-05-16T12:00:00Z", active=True,
        )
    # The seeded item is out of it: the near-ties decide, so the hunt heads the desktop's list.
    repository.upsert_practice_item_state(
        PLAIN, difficulty=5.0, stability=2.0, due_at="2026-05-18T12:00:00Z",
        last_attempt_at="2026-05-16T12:00:00Z", active=False,
    )
    # Every near-tie is an alternative and the draw always explores, or no draw at all.
    set_config(
        paths, "scheduler", selection_exploration_rate=1.0 if explore else 0.0,
        selection_exploration_reward_window=1000.0,
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


def _full_decision(repository: Repository) -> dict:
    with repository.connection() as connection:
        row = connection.execute(
            "SELECT candidates_json, exclusions_json, detail_json FROM router_decisions "
            "WHERE decision_kind = 'today_offer' ORDER BY rowid DESC LIMIT 1"
        ).fetchone()
    return {key: json.loads(row[key]) for key in row.keys()}


def test_a_limit_is_applied_after_the_filter_so_the_top_item_cannot_starve_the_phone(tmp_path):
    """F2: the desktop's limit=1 is the hunt; the phone's is the next item it can answer."""

    _paths, _repository, ctx = _ranked_world(tmp_path)
    session = _call(ctx, "start_session", {"availableMinutes": 60})
    desktop_head = _ids(_call(ctx, "get_today_queue", {"sessionId": session["sessionId"], "limit": 1}))
    assert desktop_head == [TOP_HUNT], "the scenario: the item the desktop ranks first is not the phone's"
    _call(ctx, "end_session", {"sessionId": session["sessionId"]})
    with ctx.acting_as(ORIGIN):
        phone = _call(ctx, "start_session", {"availableMinutes": 60})
        queue = _call(ctx, "get_today_queue", {"sessionId": phone["sessionId"], "limit": 1})

    assert len(_ids(queue)) == 1 and _ids(queue)[0] not in {TOP_HUNT, LOW_IMAGE}
    assert queue["totalItems"] == 1
    # What waits is what waits, wherever the cut fell.
    assert queue["deviceDeferredCount"] == 2


def test_the_reentry_cap_is_applied_after_the_filter_too(tmp_path, monkeypatch):
    """F2: the automatic cap, with no limit from the client."""

    _paths, _repository, ctx = _ranked_world(tmp_path)
    monkeypatch.setattr(queue_handlers, "plan_active", lambda _vault: False)
    monkeypatch.setattr(queue_handlers, "reentry_session_cap", lambda *_args: 1)
    with ctx.acting_as(ORIGIN):
        session = _call(ctx, "start_session", {"availableMinutes": 60})
        queue = _call(ctx, "get_today_queue", {"sessionId": session["sessionId"]})
    assert len(_ids(queue)) == 1 and _ids(queue)[0] not in {TOP_HUNT, LOW_IMAGE}
    assert queue["reentryRefresherCap"] == 1


def test_a_limited_offer_logs_no_probability_for_an_item_below_the_cut_it_cannot_show(tmp_path):
    """F1: exploration must not be able to promote an ineligible item from below the
    cut, and the logged distribution is the one that produced the published list."""

    _paths, repository, ctx = _ranked_world(tmp_path, explore=True)
    with ctx.acting_as(ORIGIN):
        session = _call(ctx, "start_session", {"availableMinutes": 60})
        queue = _call(ctx, "get_today_queue", {"sessionId": session["sessionId"], "limit": 2})

    assert not {LOW_IMAGE, TOP_HUNT} & set(_ids(queue))
    assert len(_ids(queue)) == 2
    decision = _full_decision(repository)
    distribution = decision["detail_json"]["head_distribution"]
    assert not {LOW_IMAGE, TOP_HUNT} & set(distribution)
    assert sum(distribution.values()) == pytest.approx(1.0)
    alternatives = decision["detail_json"]["exploration"]["alternative_item_ids"]
    assert alternatives and not {LOW_IMAGE, TOP_HUNT} & set(alternatives)
    assert not {LOW_IMAGE, TOP_HUNT} & {entry["ref"] for entry in decision["candidates_json"]}
    assert {LOW_IMAGE, TOP_HUNT} <= set(decision["exclusions_json"]["named"]["device_ineligible"])


def test_a_follow_up_naming_an_ineligible_item_cannot_come_back_at_the_top(tmp_path, monkeypatch):
    """The follow-up door rebuilds an item by id after the ranked loop: same filter."""

    _paths, _repository, ctx = _ranked_world(tmp_path)
    monkeypatch.setattr(
        Repository, "pending_followup_practice_items",
        lambda self, **kwargs: [{"id": "task_1", "practice_item_id": LOW_IMAGE, "followup_kind": "cold_retry"}],
    )
    with ctx.acting_as(ORIGIN):
        session = _call(ctx, "start_session", {"availableMinutes": 60})
        queue = _call(ctx, "get_today_queue", {"sessionId": session["sessionId"], "limit": 1})
    assert len(_ids(queue)) == 1 and _ids(queue)[0] not in {TOP_HUNT, LOW_IMAGE}
    assert queue["deviceDeferredCount"] == 2


def test_a_presentation_on_an_item_the_phone_cannot_show_survives_the_phone_queue(tmp_path, monkeypatch):
    """The filter holds an item back from the phone; it must not end the desktop's
    committed presentation as if the item had stopped being servable."""

    paths, repository, ctx, episode = _probe_world(tmp_path, monkeypatch)
    del paths, episode
    item_id = None
    session = _call(ctx, "start_session", {"availableMinutes": 60})
    contract = None
    queue = _call(ctx, "get_today_queue", {"sessionId": session["sessionId"]})
    for candidate in _ids(queue):
        contract = _call(ctx, "get_probe_contract", {"sessionId": session["sessionId"], "practiceItemId": candidate})
        if contract.get("active"):
            item_id = candidate
            break
    assert contract is not None and contract.get("active"), "the world commits a presentation"
    monkeypatch.setattr(
        device_eligibility, "_prompt_reason", lambda _prompt: EMBEDS_IMAGE,
    )
    with ctx.acting_as(ORIGIN):
        adopted = _call(ctx, "adopt_session", {"sessionId": session["sessionId"], "expectedGeneration": 0})
        phone_queue = _call(ctx, "get_today_queue", {"sessionId": session["sessionId"]})
    assert adopted["ownerDeviceId"] == ORIGIN.device_id
    assert item_id not in _ids(phone_queue)
    presentation = repository.active_probe_presentation_for_session(session["sessionId"])
    assert presentation is not None and presentation.practice_item_id == item_id


# -- Codex review F6: the kill switch, at every door


def _switched_off(paths):
    set_config(paths, "practice", device_eligibility_enabled=False)
    ctx = SidecarContext()
    ctx.load_secondary(paths.root)
    ctx.grading_provider_override = "manual"
    return ctx


def test_switched_off_the_phones_queue_is_the_desktops_and_says_so(tmp_path):
    paths, repository, _ctx = _world(tmp_path)
    ctx = _switched_off(paths)
    with ctx.acting_as(ORIGIN):
        session = _call(ctx, "start_session", {"availableMinutes": 60})
        queue = _call(ctx, "get_today_queue", {"sessionId": session["sessionId"]})

    assert sorted(_ids(queue)) == sorted([PLAIN, HUNT, LADDER, IMAGE])
    assert queue["deviceDeferredCount"] == 0
    decision = _full_decision(repository)
    assert "device_ineligible" not in decision["exclusions_json"]["named"]
    assert decision["detail_json"]["inputs"]["device_policy"] == "off"


def test_the_phones_decision_names_the_rules_and_the_desktops_does_not(tmp_path):
    _paths, repository, ctx = _world(tmp_path)
    session = _call(ctx, "start_session", {"availableMinutes": 60})
    _call(ctx, "get_today_queue", {"sessionId": session["sessionId"]})
    assert "device_policy" not in _full_decision(repository)["detail_json"]["inputs"]
    _call(ctx, "end_session", {"sessionId": session["sessionId"]})
    with ctx.acting_as(ORIGIN):
        phone = _call(ctx, "start_session", {"availableMinutes": 60})
        _call(ctx, "get_today_queue", {"sessionId": phone["sessionId"]})
    assert _full_decision(repository)["detail_json"]["inputs"]["device_policy"] == DEVICE_POLICY


def test_switched_off_a_skip_rebuilds_unfiltered(tmp_path):
    paths, _repository, _ctx = _world(tmp_path)
    ctx = _switched_off(paths)
    with ctx.acting_as(ORIGIN):
        session = _call(ctx, "start_session", {"availableMinutes": 60})
        requeued = _call(ctx, "skip_practice_item", {"sessionId": session["sessionId"], "practiceItemId": PLAIN})
    assert sorted(_ids(requeued)) == sorted([HUNT, LADDER, IMAGE])


@pytest.mark.parametrize("name", ["open_queue_item", "get_practice_item"])
def test_switched_off_a_by_id_door_opens(tmp_path, name):
    paths, _repository, _ctx = _world(tmp_path)
    ctx = _switched_off(paths)
    with ctx.acting_as(ORIGIN):
        assert _call(ctx, name, {"practiceItemId": HUNT})


def test_switched_off_a_probe_contract_is_not_refused(tmp_path):
    paths, _repository, _ctx = _world(tmp_path)
    ctx = _switched_off(paths)
    with ctx.acting_as(ORIGIN):
        session = _call(ctx, "start_session", {"availableMinutes": 60})
        contract = _call(ctx, "get_probe_contract", {"sessionId": session["sessionId"], "practiceItemId": HUNT})
    assert contract["active"] is False


def test_switched_off_adoption_carries_the_draft(tmp_path):
    paths, repository, ctx = _world(tmp_path)
    session_id = _call(ctx, "start_session", {"availableMinutes": 60})["sessionId"]
    _call(ctx, "save_practice_draft", {"sessionId": session_id, "practiceItemId": HUNT, "answerMd": "my repair"})
    off = _switched_off(paths)
    with off.acting_as(ORIGIN):
        adopted = _call(off, "adopt_session", {"sessionId": session_id, "expectedGeneration": 0})
    assert adopted["ownerDeviceId"] == ORIGIN.device_id and adopted["hasDraft"] is True
    assert repository.fetch_session_checkpoint(session_id)["current_answer"] == "my repair"


def test_a_card_not_due_is_not_counted_as_waiting(tmp_path):
    """A phone's count is what the build would have served, not every hunt in the vault."""

    _paths, repository, ctx = _ranked_world(tmp_path)
    repository.upsert_practice_item_state(
        LOW_IMAGE, difficulty=5.0, stability=2000.0, due_at="2099-05-18T12:00:00Z",
        last_attempt_at="2026-05-16T12:00:00Z", active=False,
    )
    with ctx.acting_as(ORIGIN):
        session = _call(ctx, "start_session", {"availableMinutes": 60})
        queue = _call(ctx, "get_today_queue", {"sessionId": session["sessionId"]})
    assert queue["deviceDeferredCount"] == 1


def test_a_check_once_asks_the_same_gate(tmp_path):
    """Ruling R1: the check's candidate selection reads the build's admission predicate."""

    from learnloop.scheduling.scheduler import _BuildAdmission
    from learnloop.scheduling.serving_exclusions import ADMISSION_GATES, DEVICE_INELIGIBLE

    assert DEVICE_INELIGIBLE in ADMISSION_GATES
    item = SimpleNamespace(id=HUNT)
    gate = _BuildAdmission.device_gate
    holder = SimpleNamespace(device_filter=SimpleNamespace(refuses=lambda _item: True))
    assert gate(holder, item, None) == DEVICE_INELIGIBLE
    assert gate(SimpleNamespace(device_filter=None), item, None) is None
