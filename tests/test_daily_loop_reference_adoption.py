"""Daily-loop follow-up: reference-only reader questions are adopted later.

A question written while reading a passage that no active Learning Object cites
is kept as a reference (``practice_status: reference_only``). Once an active LO
does cite the passage (a study-map apply adds or links it), the question becomes
practice automatically -- the learner takes no step. The sweep runs on the
sidecar's vault (re)load, which every study-map apply ends in, right after state
sync, and it is idempotent.
"""

from __future__ import annotations

import pytest

from learnloop.curriculum import commitments as C
from learnloop.db.repositories import Repository
from learnloop.reader import reader_authoring as AUTH
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import read_yaml, write_yaml

from tests.test_daily_loop_reader_authored_practice import (
    ANSWER,
    CLOCK,
    LO_ID,
    QUESTION,
    _author,
    _queue_ids,
    _reader_vault,
)


def _cite_passage(paths, *, status: str = "active") -> None:
    lo_path = paths.learning_object_path("linear-algebra", LO_ID)
    lo = read_yaml(lo_path)
    lo["provenance"]["source_refs"] = [{
        "ref_type": "canonical_source", "ref_id": "src1", "locator": "span:ext1/s1",
        "source_id": "src1", "extraction_id": "ext1",
    }]
    lo["status"] = status
    write_yaml(lo_path, lo)


def _learner_cards(paths) -> list:
    return [item for item in load_vault(paths.root).practice_items.values() if item.prompt == QUESTION]


def test_reference_question_becomes_practice_once_an_lo_cites_its_passage(tmp_path):
    paths = _reader_vault(tmp_path, cite_span=False)
    saved = _author(paths)
    assert saved["practice_status"] == "reference_only"
    repository = Repository(paths.sqlite_path)
    assert AUTH.adopt_reference_questions(load_vault(paths.root), repository, clock=CLOCK) == []

    _cite_passage(paths)  # the study map now links an active LO to the passage
    adopted = AUTH.adopt_reference_questions(load_vault(paths.root), repository, clock=CLOCK)

    assert [row["commitment_id"] for row in adopted] == [saved["commitment_id"]]
    item_id = adopted[0]["practice_item_id"]
    item = load_vault(paths.root).practice_items[item_id]
    assert (item.prompt, item.expected_answer, item.learning_object_id) == (QUESTION, ANSWER, LO_ID)
    assert [ref.locator for ref in item.provenance.source_refs] == ["span:ext1/s2"]
    targets = C.resolve_head(repository, saved["commitment_id"]).targets
    assert ("legacy_practice_item", item_id) in {(t.target_kind, t.target_ref) for t in targets}
    assert _queue_ids(paths)[0] == item_id  # served, first, as the learner's request

    # Idempotent: a second sweep adopts nothing and makes no second card.
    assert AUTH.adopt_reference_questions(load_vault(paths.root), repository, clock=CLOCK) == []
    assert len(_learner_cards(paths)) == 1


@pytest.mark.parametrize("status", ["dormant", "resolved"])
def test_a_parked_lo_citing_the_passage_does_not_adopt(tmp_path, status):
    paths = _reader_vault(tmp_path, cite_span=False)
    _author(paths)
    _cite_passage(paths, status=status)
    repository = Repository(paths.sqlite_path)
    assert AUTH.adopt_reference_questions(load_vault(paths.root), repository, clock=CLOCK) == []
    assert _learner_cards(paths) == []


def test_a_retired_reference_question_is_never_adopted(tmp_path):
    paths = _reader_vault(tmp_path, cite_span=False)
    saved = _author(paths)
    repository = Repository(paths.sqlite_path)
    C.retire(repository, commitment_id=saved["commitment_id"], clock=CLOCK)
    _cite_passage(paths)
    assert AUTH.adopt_reference_questions(load_vault(paths.root), repository, clock=CLOCK) == []
    assert _learner_cards(paths) == []


def test_sidecar_reload_adopts_and_today_serves_it(tmp_path):
    import learnloop_sidecar.handlers  # noqa: F401
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.registry import METHOD_REGISTRY

    def call(ctx, name, params):
        spec = METHOD_REGISTRY[name]
        return spec.handler(ctx, spec.params_model.model_validate(params))

    paths = _reader_vault(tmp_path, cite_span=False)
    toml = paths.root / "learnloop.toml"
    text = toml.read_text(encoding="utf-8")
    toml.write_text(
        text.replace("reader_enabled = false", "reader_enabled = true")
        if "reader_enabled" in text
        else text + "\n[tutor_qa]\nreader_enabled = true\n",
        encoding="utf-8",
    )
    ctx = SidecarContext()
    ctx.load(paths.root)
    saved = call(ctx, "reader.author_qa", {
        "question": QUESTION, "answer": ANSWER, "sourceId": "src1", "revisionId": "rev1",
        "subjectId": "span:ext1/s2", "clientIdempotencyKey": "ref-1",
    })
    assert saved["practiceStatus"] == "reference_only"

    _cite_passage(paths)
    ctx.reload(maintenance=False)  # every study-map apply ends in this reload

    cards = _learner_cards(paths)
    assert len(cards) == 1
    queue = call(ctx, "get_today_queue", {})
    served = [item["practiceItemId"] for section in queue["sections"] for item in section["items"]]
    assert cards[0].id in served


def _set_adoption(paths, enabled: bool) -> None:
    toml = paths.root / "learnloop.toml"
    text = toml.read_text(encoding="utf-8")
    for line in ("adopt_reference_questions = true\n", "adopt_reference_questions = false\n"):
        text = text.replace(line, "")
    marker = "reader_enabled = true\n"
    if marker not in text:
        text = text.replace("reader_enabled = false\n", marker) if "reader_enabled" in text \
            else text + "\n[tutor_qa]\n" + marker
    toml.write_text(text.replace(
        marker, marker + f"adopt_reference_questions = {'true' if enabled else 'false'}\n"),
        encoding="utf-8")


def test_adoption_kill_switch_restores_baseline_and_keeps_adopted_cards(tmp_path):
    """Review F8: the automatic sweep sits behind tutor_qa.adopt_reference_questions."""
    import learnloop_sidecar.handlers  # noqa: F401
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.registry import METHOD_REGISTRY

    def served(ctx):
        spec = METHOD_REGISTRY["get_today_queue"]
        queue = spec.handler(ctx, spec.params_model.model_validate({}))
        return [item["practiceItemId"] for section in queue["sections"] for item in section["items"]]

    paths = _reader_vault(tmp_path, cite_span=False)
    first = _author(paths, key="qa1")
    second = _author(paths, key="qa2", question="What does Sigma hold?", answer="Singular values.")
    assert first["practice_status"] == second["practice_status"] == "reference_only"
    _set_adoption(paths, False)
    ctx = SidecarContext()
    ctx.load(paths.root)
    assert ctx.vault.config.tutor_qa.adopt_reference_questions is False
    baseline = served(ctx)

    _cite_passage(paths)
    ctx.reload(maintenance=False)
    assert _learner_cards(paths) == []  # switch off: references stay references
    assert served(ctx) == baseline
    repository = Repository(paths.sqlite_path)
    assert AUTH.adopt_reference_questions(load_vault(paths.root), repository, clock=CLOCK) == []

    _set_adoption(paths, True)
    ctx.reload(maintenance=False)
    adopted = [item.id for item in load_vault(paths.root).practice_items.values()
               if item.prompt in {QUESTION, "What does Sigma hold?"}]
    assert len(adopted) == 2 and set(adopted) <= set(served(ctx))
    events = repository.reader_interaction_events(kind="learner_item_authored")
    assert {e["payload"]["mechanism"] for e in events if e["subject_id"] in adopted} == {
        "reader_reference_adoption_v1"}

    # Turning it off again stops new adoption but deletes nothing authored.
    _set_adoption(paths, False)
    ctx.reload(maintenance=False)
    vault = load_vault(paths.root)
    assert all(vault.practice_items[item_id].status == "active" for item_id in adopted)
    assert set(adopted) <= set(served(ctx))
