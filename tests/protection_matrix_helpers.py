"""The synthetic world of ``tests/test_protection_surface_matrix.py``: every protected fixture in one vault.

One vault holds every fixture the matrix asks about, each in its own namespace, so a surface is asked about all
of them under the same defaults (the source sets, the switches, the goal) and no fixture is a mini-vault with a
default of its own. Every unit's blocks, its heading included, carry one letters-only marker word, so a model
prompt or a payload that carries any block of a protected unit (a neighbour or a heading too) is found by that
word; the markers share no numerals and no words, so the lexical floor matches only the text it should.

A row of the matrix names a :class:`Target`: a span (the fixture's protected or neighbouring block) and, for an
item row, the practice item built from it. ``8.invalid``, ``8.empty`` and ``9.switch-off`` are the same world in
another state: a copy of the vault (databases through the backup API) whose source sets file was made
unparseable or empty, or whose ``goals.held_out_selection`` was turned off.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from learnloop.clock import FrozenClock
from learnloop.content.synthesis.source_unit_selection import save_unit_selection
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.writer import upsert_source_set
from learnloop.vault.yaml_io import write_yaml

from tests.exam_scope_fixtures import _second_reading, ref
from tests.practice_index_fakes import _item
from tests.source_inventory_helpers import _block, _ir, _persist, _register_revision
from tests.source_retrieval_fakes import seed_source
from tests.source_service_fakes import build_textbook_vault

NOW = datetime(2026, 11, 19, 12, 0, tzinfo=UTC)
CLOCK = FrozenClock(NOW)
SET_ID = "sset_la"
SUBJECT = "linear-algebra"
LO = "lo_matrices"
FACET = "facet_eigen"
_WORDS = ("alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "golf", "hotel", "india", "juliet", "kilo",
          "lima")


def sentence(mark: str) -> str:
    """A block's text: its marker, then words no other marker's block shares (no numerals at all)."""

    return f"{mark} " + " ".join(f"{mark.lower()}{word}" for word in _WORDS) + "."


def heading(mark: str) -> str:
    return f"{mark} heading"


@dataclass(frozen=True)
class Target:
    """What one matrix row asks about."""

    row: str
    extraction_id: str | None = None
    span_id: str | None = None
    #: The marker word every block of the target's unit carries.
    mark: str | None = None
    item_id: str | None = None
    #: The world state the row is read in (``base``, ``invalid``, ``empty``, ``switch_off``).
    state: str = "base"
    #: A selection spelled as the Reader's camelCase ``spanId``.
    camel: bool = False
    #: The safe block beside the protected target (a neighbour an author's context adds), when there is one.
    neighbor_of: str | None = None
    #: The page (as ``seed_source`` numbers them) the target block is on.
    page: int | None = None
    source_id: str | None = None
    revision_id: str | None = None

    @property
    def key(self) -> tuple[str, str] | None:
        if self.extraction_id is None or self.span_id is None:
            return None
        return (self.extraction_id, self.span_id)


@dataclass
class World:
    root: Path
    paths: VaultPaths
    repository: Repository
    targets: dict[str, Target]
    state: str = "base"
    #: Digest of each reading's stored original PDF, by extraction id.
    pdf_digest: dict[str, str] = field(default_factory=dict)
    png_digest: dict[str, str] = field(default_factory=dict)
    notes: dict[str, Any] = field(default_factory=dict)

    def vault(self):
        return load_vault(self.root)


# --- sources --------------------------------------------------------------------------------------------------


def _unit(mark: str, page: int) -> tuple[str, list[tuple[str, int]]]:
    return (heading(mark), [(sentence(mark), page)])


def _pdf(pages: int) -> bytes:
    from tests.mobile_v4_reader_helpers import pdf_bytes

    return pdf_bytes(pages)


def _store_pdf(root: Path, pages: int) -> str:
    from learnloop.ingest.originals import store_original_bytes

    data = _pdf(pages)
    digest = "sha256:" + hashlib.sha256(data).hexdigest()
    store_original_bytes(root, digest, data)
    return digest


def store_png(root: Path, shade: int) -> str:
    """A stored original image, distinct per ``shade``."""

    import io

    from PIL import Image

    from learnloop.ingest.originals import store_original_bytes

    buffer = io.BytesIO()
    Image.new("RGB", (4, 4), (shade % 256, 10, 10)).save(buffer, format="PNG")
    data = buffer.getvalue()
    digest = "sha256:" + hashlib.sha256(data).hexdigest()
    store_original_bytes(root, digest, data)
    return digest


class _Sources:
    """Seeds namespaced sources, each read once, with a distinct stored PDF as its original."""

    def __init__(self, root: Path, repository: Repository) -> None:
        self.root, self.repository = root, repository
        self.pages = 3
        self.pdf: dict[str, str] = {}

    def seed(self, ns: str, units: dict[str, tuple[str, list[tuple[str, int]]]], *, title: str) -> str:
        self.pages += 1
        digest = _store_pdf(self.root, self.pages)
        seed_source(self.repository, source_id=f"src_{ns}", revision_id=f"rev_{ns}", extraction_id=f"ext_{ns}",
                    title=title, units=units, furniture=False, asset_hash=digest)
        self.repository.set_source_current_revision(f"src_{ns}", f"rev_{ns}")
        self.pdf[f"ext_{ns}"] = digest
        return f"ext_{ns}"


def _members(root: Path) -> list[dict[str, Any]]:
    vault = load_vault(root)
    current = next(source_set for source_set in vault.source_sets if source_set.id == SET_ID)
    return [member.model_dump(mode="json", exclude_none=True) for member in current.members]


def _save_members(root: Path, members: list[dict[str, Any]]) -> None:
    upsert_source_set(root, {"id": SET_ID, "subject_id": SUBJECT, "title": "Linear algebra sources",
                             "members": members}, clock=CLOCK)


# Clean book units: one per clean item (its own exercise) plus the control passage.
CLEAN_UNITS = ("ctrl", "res", "cold", "rem", "asr", "probe", "presented", "grade", "shown", "feedback", "import")


def _clean_span(index: int) -> str:
    return f"s{3 * index + 2}"


def _two_unit_spans() -> dict[str, str]:
    """``seed_source`` numbers a two-unit reading's blocks s1, s2 (first unit) and s4, s5 (second)."""

    return {"theory_head": "s1", "theory": "s2", "exam_head": "s4", "exam": "s5"}


def build_sources(root: Path, repository: Repository) -> tuple[dict[str, Target], dict[str, str]]:
    """Fixtures 1 to 5, the clean book, and the source-set members that make them protected."""

    sources = _Sources(root, repository)
    two = _two_unit_spans()
    targets: dict[str, Target] = {}
    members = _members(root)

    # 0: a clean textbook, one unit per clean item's exercise, and the control passage.
    clean = sources.seed("g6clean", {f"c_{name}": _unit(f"GSIXCLEAN{name.upper()}", index + 1)
                                     for index, name in enumerate(CLEAN_UNITS)}, title="Clean book")
    members.append({"source_id": "src_g6clean", "revision_id": "rev_g6clean", "default_role": "primary_textbook"})
    targets["0.control"] = Target("0.control", clean, _clean_span(0), "GSIXCLEANCTRL", page=1,
                                  source_id="src_g6clean", revision_id="rev_g6clean")

    # 1: a past paper, exam role, no marks or signals.
    paper = sources.seed("g6p1", {"p1_q": _unit("GSIXPAPER", 1)}, title="Past paper")
    members.append({"source_id": "src_g6p1", "revision_id": "rev_g6p1", "default_role": "exam"})
    targets["1.paper"] = Target("1.paper", paper, "s2", "GSIXPAPER", page=1, source_id="src_g6p1",
                                revision_id="rev_g6p1")

    # 2: a rule-2 exam unit on its marked reading, a theory unit beside it on another page.
    r2 = sources.seed("g6r2", {"r2_theory": _unit("GSIXRTWOTHEORY", 1), "r2_exam": _unit("GSIXRTWOEXAM", 2)},
                      title="Book with an exam unit")
    members.append({"source_id": "src_g6r2", "revision_id": "rev_g6r2", "default_role": "primary_textbook",
                    "scope": [{"unit_id": "r2_theory"}, {"unit_id": "r2_exam", "role_override": "exam"}],
                    "scope_extraction_id": r2, "scope_revision_id": "rev_g6r2"})
    targets["2.exam"] = Target("2.exam", r2, two["exam"], "GSIXRTWOEXAM", neighbor_of=two["theory"], page=2,
                               source_id="src_g6r2", revision_id="rev_g6r2")
    targets["2.neighbor"] = Target("2.neighbor", r2, two["theory"], "GSIXRTWOTHEORY", page=1, source_id="src_g6r2",
                                   revision_id="rev_g6r2")

    # 2: a chapter split at its headings, its Exam half overridden to exam.
    _register_revision(repository, source_id="src_g6split", revision_id="rev_g6split")
    repository.set_source_current_revision("src_g6split", "rev_g6split")
    sources.pages += 1
    split_digest = _store_pdf(root, sources.pages)
    with repository.connection() as connection:
        connection.execute("UPDATE source_revisions SET asset_hash = ? WHERE id = 'rev_g6split'", (split_digest,))
        connection.commit()
    sources.pdf["ext_g6split"] = split_digest
    split_ir = _ir([("chapter", "Chapter", [
        _block("s1", sentence("GSIXSPLITTHEORY"), section=("chapter", "Theory"), page=1),
        _block("s2", sentence("GSIXSPLITEXAM"), section=("chapter", "Exam"), page=2),
    ], "sha256:g6chapter", 1)])
    _persist(repository, split_ir, revision_id="rev_g6split", extraction_id="ext_g6split")
    save_unit_selection(repository, "ext_g6split", ["chapter"],
                        boundary_overrides=[{"op": "split_at_heading", "unit_id": "chapter"}], clock=CLOCK)
    members.append({"source_id": "src_g6split", "revision_id": "rev_g6split", "default_role": "primary_textbook",
                    "scope": [{"unit_id": "chapter#Theory"}, {"unit_id": "chapter#Exam", "role_override": "exam"}],
                    "scope_extraction_id": "ext_g6split", "scope_revision_id": "rev_g6split"})
    targets["2.split-exam"] = Target("2.split-exam", "ext_g6split", "s2", "GSIXSPLITEXAM", neighbor_of="s1",
                                     page=2, source_id="src_g6split", revision_id="rev_g6split")
    targets["2.split-theory"] = Target("2.split-theory", "ext_g6split", "s1", "GSIXSPLITTHEORY", page=1,
                                       source_id="src_g6split", revision_id="rev_g6split")

    # 3: a held-out unit marked on its reading by the production writer, a theory unit beside it.
    h3 = sources.seed("g6h3", {"h3_theory": _unit("GSIXHELDTHEORY", 1), "h3_exam": _unit("GSIXHELDEXAM", 2)},
                      title="Book with a held-out unit")
    save_unit_selection(repository, h3, ["h3_theory", "h3_exam"], exam_use_modes={"h3_exam": "held_out_evaluation"},
                        clock=CLOCK)
    members.append({"source_id": "src_g6h3", "revision_id": "rev_g6h3", "default_role": "primary_textbook"})
    targets["3.held"] = Target("3.held", h3, two["exam"], "GSIXHELDEXAM", neighbor_of=two["theory"], page=2,
                               source_id="src_g6h3", revision_id="rev_g6h3")
    targets["3.neighbor"] = Target("3.neighbor", h3, two["theory"], "GSIXHELDTHEORY", page=1, source_id="src_g6h3",
                                   revision_id="rev_g6h3")
    targets["3.camel"] = replace(targets["3.held"], row="3.camel", camel=True)

    # 3: a held-out mark naming a unit this reading cannot resolve: the whole reading is held.
    u3 = sources.seed("g6u3", {"u3_theory": _unit("GSIXUNRESTHEORY", 1), "u3_exam": _unit("GSIXUNRESEXAM", 2)},
                      title="Book with an unresolved mark")
    save_unit_selection(repository, u3, ["u3_theory", "u3_exam"],
                        exam_use_modes={"no_such_unit": "held_out_evaluation"}, clock=CLOCK)
    members.append({"source_id": "src_g6u3", "revision_id": "rev_g6u3", "default_role": "primary_textbook"})
    targets["3.unresolved"] = Target("3.unresolved", u3, two["theory"], "GSIXUNRESTHEORY", page=1,
                                     source_id="src_g6u3", revision_id="rev_g6u3")

    # 4: a protected book (A marked) and a second, unmarked reading B of the same revision: B is held back.
    r4 = sources.seed("g6r4", {"r4_theory": _unit("GSIXREREADTHEORY", 1), "r4_exam": _unit("GSIXREREADEXAM", 2)},
                      title="Re-read book")
    save_unit_selection(repository, r4, ["r4_theory", "r4_exam"], exam_use_modes={"r4_exam": "held_out_evaluation"},
                        clock=CLOCK)
    _second_reading(repository, revision_id="rev_g6r4", extraction_id="ext_g6r4b")
    members.append({"source_id": "src_g6r4", "revision_id": "rev_g6r4", "default_role": "primary_textbook"})
    targets["4.unmarked"] = Target("4.unmarked", "ext_g6r4b", "s2", "ALTREADINGSENTINEL", page=1,
                                   source_id="src_g6r4", revision_id="rev_g6r4")

    # 4: a legacy held-out mark that never named its reading (no ``marks_made_on``).
    l4 = sources.seed("g6l4", {"l4_theory": _unit("GSIXLEGACYTHEORY", 1), "l4_exam": _unit("GSIXLEGACYEXAM", 2)},
                      title="Legacy-marked book")
    repository.upsert_unit_selection(extraction_id=l4, source_id="src_g6l4", revision_id="rev_g6l4",
                                     selected_unit_ids=["l4_theory", "l4_exam"],
                                     exam_use_modes={"l4_exam": "held_out_evaluation"})
    members.append({"source_id": "src_g6l4", "revision_id": "rev_g6l4", "default_role": "primary_textbook"})
    targets["4.legacy"] = Target("4.legacy", l4, two["theory"], "GSIXLEGACYTHEORY", page=1, source_id="src_g6l4",
                                 revision_id="rev_g6l4")

    # 5: a held-out signal an exam-role inventory run recorded on the reading it read.
    s5 = sources.seed("g6s5", {"s5_theory": _unit("GSIXSIGNALTHEORY", 1), "s5_exam": _unit("GSIXSIGNALEXAM", 2)},
                      title="Book with a held-out signal")
    _signal(repository, revision_id="rev_g6s5", extraction_id=s5, unit_id="s5_exam", span_ids=[two["exam"]])
    members.append({"source_id": "src_g6s5", "revision_id": "rev_g6s5", "default_role": "primary_textbook"})
    targets["5.signal"] = Target("5.signal", s5, two["exam"], "GSIXSIGNALEXAM", neighbor_of=two["theory"], page=2,
                                 source_id="src_g6s5", revision_id="rev_g6s5")

    # 5: a historical signal row that names no reading: the whole reading is held, conservatively.
    k5 = sources.seed("g6k5", {"k5_theory": _unit("GSIXUNKNOWNTHEORY", 1), "k5_exam": _unit("GSIXUNKNOWNEXAM", 2)},
                      title="Book with a reading-less signal")
    _unknown_reading_signal(repository, revision_id="rev_g6k5", span_ids=[two["exam"]])
    members.append({"source_id": "src_g6k5", "revision_id": "rev_g6k5", "default_role": "primary_textbook"})
    targets["5.unknown"] = Target("5.unknown", k5, two["theory"], "GSIXUNKNOWNTHEORY", page=1, source_id="src_g6k5",
                                  revision_id="rev_g6k5")

    _save_members(root, members)
    return targets, sources.pdf


def _signal(repository: Repository, *, revision_id: str, extraction_id: str, unit_id: str, span_ids: list[str]) -> None:
    """An inventory a model run made on ``extraction_id`` as exam material, with one held-out signal: the
    repository writes its append-only ledger row in the same transaction."""

    from learnloop.content.synthesis.ai_contracts import (
        SOURCE_UNIT_INVENTORY_PROMPT_VERSION,
        InventoryAssessmentSignal,
        SourceUnitInventory,
    )

    inventory = SourceUnitInventory(unit_id=unit_id, semantic_hash=f"sha256:{unit_id}", assessment_signals=[
        InventoryAssessmentSignal(held_out=True, task_family="proof", span_ids=list(span_ids))])
    repository.insert_unit_inventory(
        id=f"inv_{extraction_id}_{unit_id}", source_revision_id=revision_id, extraction_id=extraction_id,
        unit_id=unit_id, unit_semantic_hash=f"sha256:{unit_id}", inventory_profile="assessment",
        inventory_schema_version=1, prompt_version=SOURCE_UNIT_INVENTORY_PROMPT_VERSION, provider="fake",
        model="fake", inventory=inventory.model_dump(), made_as_role="exam")


def _unknown_reading_signal(repository: Repository, *, revision_id: str, span_ids: list[str]) -> None:
    """The historical ledger shape no fresh writer makes: a held-out signal with its revision and no reading.
    Plain SQL into the append-only ledger (its triggers stay on: this is an insert)."""

    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO source_held_out_signal_marks(id, revision_id, extraction_id, unit_id, inventory_id, "
            "made_as_role, span_ids_json, created_at) VALUES (?,?,?,?,?,?,?,?)",
            ("hos_g6_unknown", revision_id, None, "k5_exam", "inv_g6_unknown", "exam", json.dumps(span_ids),
             "2026-01-01T00:00:00Z"))
        connection.commit()


# --- items ----------------------------------------------------------------------------------------------------


def item_path(paths: VaultPaths, item_id: str) -> Path:
    return paths.practice_item_path(SUBJECT, item_id)


def write_item(paths: VaultPaths, item_id: str, mark: str, **extra: Any) -> None:
    payload = _item(item_id, LO, f"{mark}ITEM " + sentence(f"{mark}STEM"), [FACET], **extra)
    payload["expected_answer"] = f"{mark}KEY answer"
    write_yaml(item_path(paths, item_id), payload)


def canonical(source_id: str, extraction_id: str, span_id: str) -> dict[str, Any]:
    return {"source_id": source_id, "extraction_id": extraction_id, "span_ids": [span_id], "relation": "verbatim"}


def build_items(paths: VaultPaths, repository: Repository, targets: dict[str, Target]) -> None:
    """Fixture 6 (the items made from fixtures 1-5, the whole reference and the clean reservations)."""

    for number, row in (("1", "1.paper"), ("2", "2.exam"), ("3", "3.held"), ("4", "4.unmarked"),
                        ("5", "5.signal")):
        base = targets[row]
        canon, block = f"pi_g6_{number}_canonical", f"pi_g6_{number}_block"
        write_item(paths, canon, f"GSIXITEMCANON{'ABCDE'[int(number) - 1]}",
                   canonical_exercise=canonical(base.source_id, base.extraction_id, base.span_id))
        write_item(paths, block, f"GSIXITEMBLOCK{'ABCDE'[int(number) - 1]}",
                   provenance={"origin": "human",
                               "source_refs": [ref(base.source_id, base.extraction_id, base.span_id)]})
        targets[f"6.{number}canonical"] = replace(base, row=f"6.{number}canonical", item_id=canon)
        targets[f"6.{number}block"] = replace(base, row=f"6.{number}block", item_id=block)

    # A whole-extraction reference to the partly held reading of fixture 3: no span, no block.
    held = targets["3.held"]
    write_item(paths, "pi_g6_wholeref", "GSIXITEMWHOLE", provenance={"origin": "human", "source_refs": [
        {"ref_type": "canonical_source", "ref_id": held.source_id, "source_id": held.source_id,
         "extraction_id": held.extraction_id}]})
    targets["6.whole-ref"] = Target("6.whole-ref", item_id="pi_g6_wholeref", mark="GSIXITEMWHOLE",
                                    source_id=held.source_id)

    clean = targets["0.control"]
    for index, name in enumerate(CLEAN_UNITS):
        if name in ("ctrl", "import"):
            continue
        item_id = f"pi_g6_{name}"
        mark = f"GSIXCLEAN{name.upper()}"
        extra: dict[str, Any] = {}
        if name == "probe":
            extra["practice_mode"] = "diagnostic_probe"
        # As an import writes it: the canonical exercise and the block reference both name the item's own passage.
        write_item(paths, item_id, f"GSIXITEM{name.upper()}",
                   canonical_exercise=canonical("src_g6clean", clean.extraction_id, _clean_span(index)),
                   provenance={"origin": "canonical_extract", "source_refs": [
                       ref("src_g6clean", clean.extraction_id, _clean_span(index))]}, **extra)
        targets[f"6.{name}"] = Target(f"6.{name}", clean.extraction_id, _clean_span(index), mark, item_id=item_id,
                                      page=index + 1, source_id="src_g6clean", revision_id="rev_g6clean")
    # Row names as the matrix spells them.
    renames = {"6.res": "6.exam-reserved", "6.cold": "6.cold-task", "6.rem": "6.remediation",
               "6.asr": "6.assess-reserved", "6.grade": "6.held-grade", "6.shown": "+.shown",
               "6.feedback": "+.held-feedback"}
    for old, new in renames.items():
        targets[new] = replace(targets.pop(old), row=new)


# --- what holds the clean items -------------------------------------------------------------------------------


def _iso(moment: datetime) -> str:
    return moment.astimezone(UTC).isoformat().replace("+00:00", "Z")


def build_holds(paths: VaultPaths, repository: Repository, targets: dict[str, Target]) -> dict[str, Any]:
    """The rows that hold the clean items: an exam reservation, an open cold task, a repair before its task,
    an assessment reservation, a probe presentation, a held grade and a recent reveal."""

    vault = load_vault(paths.root)
    notes: dict[str, Any] = {}
    goal_id = vault.goals[0].id if vault.goals else None
    notes["goal_id"] = goal_id
    repository.insert_exam_pool_items([{"id": "epi_g6", "goal_id": goal_id,
                                        "practice_item_id": targets["6.exam-reserved"].item_id,
                                        "reserved_at": "2026-11-01T00:00:00Z"}])
    # A pending cold retry not due yet: it reserves its item without the due-cold display rules.
    repository.create_followup_task(kind="cold_retry", case_kind="diagnosis", case_ref="att_g6_cold",
                                    not_before="2099-01-02T00:00:00Z", expires_at="2099-01-09T00:00:00Z",
                                    selected_item_id=targets["6.cold-task"].item_id, context={})
    # A repair in treatment that chose its cold item, before its primed attempt (no task yet).
    episode = repository.create_remediation_episode(case_kind="diagnosis", case_ref="att_g6_rem", state="diagnosis")
    repository.update_remediation_episode(episode["id"], state="treatment",
                                          cold_item_id=targets["6.remediation"].item_id)
    # A live assessment reservation of the item's legacy surface.
    family = repository.ensure_activity_family(purpose="assessment", legacy_kind="practice_item",
                                               title="g6 assessment", clock=CLOCK)
    card = repository.ensure_activity_card(family_id=family, clock=CLOCK)
    card_version = repository.ensure_activity_card_version(card_id=card, version=1,
                                                           card_contract_hash="sha256:g6asr", contract_json="{}",
                                                           schema_version=1, clock=CLOCK)
    surface = repository.ensure_activity_surface(card_version_id=card_version, surface_hash="sha256:g6asr-surface",
                                                 fingerprint=None, surface_json="{}",
                                                 legacy_practice_item_id=targets["6.assess-reserved"].item_id,
                                                 clock=CLOCK)
    repository.insert_surface_reservation(surface_id=surface, goal_id=goal_id, target_contract_version_id=None,
                                          target_support_hash=None, purpose="assessment", eligibility_json="{}",
                                          clock=CLOCK)
    # An ordinary item once presented as a diagnostic probe (valid parent rows, foreign keys on).
    from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION

    probe_episode = repository.insert_probe_episode(learning_object_id=LO, status="complete", trigger="manual",
                                                    hypothesis_set_id=None, active_state_segment_id=None,
                                                    algorithm_version=LATEST_ALGORITHM_VERSION)
    probe_episode_id = probe_episode if isinstance(probe_episode, str) else probe_episode["id"]
    segment = repository.open_state_segment(learning_object_id=LO, probe_episode_id=probe_episode_id,
                                            reason="episode_entry", clock=CLOCK)
    notes["presentation_id"] = repository.insert_probe_presentation(
        probe_episode_id=probe_episode_id, practice_item_id=targets["6.presented"].item_id,
        state_segment_id=segment, clock=CLOCK)
    # One recent, unlinked reveal of a kind that is not the attempt's own feedback.
    repository.insert_reveal_event({"id": "rev_g6_shown", "practice_item_id": targets["+.shown"].item_id,
                                    "learning_object_id": LO, "source_kind": "tutor_answer", "amount": 1.0,
                                    "basis": "test", "created_at": _iso(NOW.replace(hour=11))}, clock=CLOCK)
    return notes


def build_attempts(paths: VaultPaths, repository: Repository, targets: dict[str, Target]) -> dict[str, str]:
    """One recorded attempt on each item row (a held grade on the held-grade item), so the learner context has a
    trace of each to show or withhold. Returns ``{row: attempt_id}``."""

    from datetime import timedelta

    from tests.held_grade_evidence_helpers import _graded_apply, _held_apply

    vault = load_vault(paths.root)
    attempts: dict[str, str] = {}
    when = NOW - timedelta(days=2)
    for index, (row, target) in enumerate(sorted(targets.items())):
        if target.item_id is None or row in attempts or target.item_id not in vault.practice_items:
            continue
        if vault.practice_items[target.item_id].practice_mode == "diagnostic_probe":
            continue  # a probe is answered through its presentation, never as practice
        attempt_id = f"att_g6_{index:02d}"
        criterion = vault.practice_items[target.item_id].grading_rubric.criteria[0].id
        moment = when + timedelta(minutes=index)
        if row == "6.held-grade":
            _held_apply(vault, repository, target.item_id, {criterion: 0.0}, attempt_id=attempt_id, when=moment)
        else:
            _graded_apply(vault, repository, target.item_id, {criterion: 4.0}, attempt_id=attempt_id, when=moment)
        attempts[row] = attempt_id
    return attempts


# --- fixture 7: practice the Reader made from the past paper ---------------------------------------------------


class AuthoringReached(Exception):
    """Raised by a fake author once a context reaches it: everything before the model call has admitted it."""


def authored(statement: str):
    """One authored exercise on this vault's LO and facet, whose stem anchors in ``statement``."""

    from learnloop.content.authoring.ai_contracts import (
        CriterionFacetWeightsPayload,
        ExerciseAuthoring,
        FacetWeightPayload,
    )
    from tests.exercise_authoring_helpers import _item as _authored_item

    weight = [FacetWeightPayload(facet_id=FACET, weight=1.0)]
    return ExerciseAuthoring(items=[_authored_item(
        statement_md=statement, learning_object_id=LO, evidence_facets=[FACET], evidence_weights=weight,
        criterion_facet_weights=[CriterionFacetWeightsPayload(criterion_id="factorization", weights=weight),
                                 CriterionFacetWeightsPayload(criterion_id="factors", weights=weight)])])


def reader_import_context(world_root: Path, repository: Repository, *, extraction_id: str, nodes: list[dict],
                          client: Any, source_id: str | None = None):
    """The job context ``handle_reader_exercise_import`` runs under, background key checks off."""

    from learnloop.content.pipeline.runner import JobContext, RunnerServices

    ctx = JobContext(repo=repository, vault_root=world_root,
                     job={"id": "job_g6_import", "attempt_count": 1,
                          "payload": {"extraction_id": extraction_id, "source_id": source_id,
                                      "raw_selection": {"nodes": nodes}}},
                     clock=CLOCK, worker_id="w",
                     services=RunnerServices(exercise_import_client_factory=lambda _ctx: client,
                                             background_key_checks=False))
    return ctx


def build_reader_import(paths: VaultPaths, repository: Repository, targets: dict[str, Target]) -> str:
    """Run the Reader's import job on the past paper's exercise with a fake author; the item it writes."""

    from learnloop.content.authoring import jobs
    from learnloop.content.pipeline.runner import JobContext
    from tests.exercise_authoring_helpers import FakeClient

    paper = targets["1.paper"]
    before = set(load_vault(paths.root).practice_items)
    client = FakeClient(authored(sentence(paper.mark)))
    ctx = reader_import_context(paths.root, repository, extraction_id=paper.extraction_id,
                                nodes=[{"span_id": paper.span_id, "quote": sentence(paper.mark)}], client=client,
                                source_id=paper.source_id)
    original = JobContext.report
    JobContext.report = lambda self, *a, **k: None  # type: ignore[method-assign]
    try:
        jobs.handle_reader_exercise_import(ctx)
    finally:
        JobContext.report = original  # type: ignore[method-assign]
    (item_id,) = set(load_vault(paths.root).practice_items) - before
    targets["7.reader-import"] = replace(paper, row="7.reader-import", item_id=item_id)
    return item_id


# --- the world and its other states ---------------------------------------------------------------------------


def build_world(root: Path) -> World:
    from learnloop.ops.settings_store import apply_config_updates

    paths, repository, _spans = build_textbook_vault(root)
    # A priced metered route: without a price the canonical import's admission skips its author before the
    # context is built, so what the author would be sent could not be read.
    apply_config_updates(paths.root / "learnloop.toml", {("source_service", "llm_price_per_million"): 1.0})
    targets, pdf = build_sources(paths.root, repository)
    build_items(paths, repository, targets)
    reader_item = build_reader_import(paths, repository, targets)
    attempts = build_attempts(paths, repository, targets)
    notes = build_holds(paths, repository, targets)
    notes["attempts"] = attempts
    notes["reader_import_item"] = reader_item
    for row, base in (("8.invalid", "6.1canonical"), ("8.empty", "6.1canonical"), ("9.switch-off", "6.3canonical")):
        targets[row] = replace(targets[base], row=row, state={"8.invalid": "invalid", "8.empty": "empty",
                                                             "9.switch-off": "switch_off"}[row])
    return World(root=paths.root, paths=paths, repository=repository, targets=targets, pdf_digest=pdf, notes=notes)


#: A source-sets file the loader cannot parse (its members' flow mapping never closes).
UNPARSEABLE = "source_sets:\n  - id: sset_la\n    members: [{source_id: src_g6p1, default_role: exam\n"


def world_in_state(world: World, state: str, root: Path) -> World:
    """A copy of ``world`` (its databases through the backup API) in ``state``."""

    from learnloop.db.copies import copy_tree_with_databases
    from tests.helpers import set_config_switch

    copy_tree_with_databases(world.root, root)
    paths = VaultPaths(root, load_vault(root).config)
    if state == "invalid":
        paths.source_sets_path.write_text(UNPARSEABLE, encoding="utf-8")
    elif state == "empty":
        paths.source_sets_path.write_text("", encoding="utf-8")
    elif state == "switch_off":
        set_config_switch(root, "goals.held_out_selection", False)
    elif state not in ("base", "fault"):
        raise ValueError(state)
    return World(root=root, paths=paths, repository=Repository(paths.sqlite_path), targets=world.targets,
                 state=state, pdf_digest=world.pdf_digest, png_digest=world.png_digest, notes=world.notes)


def seed_practice_leads(world: World) -> tuple[Target, Target]:
    """G6-P8: two teaching blocks beside the item's own linked passage."""

    source, revision, extraction = "src_g6p8", "rev_g6p8", "ext_g6p8"
    solution = Target("solution", extraction, "s2", "GSIXSOLVELEAD", source_id=source)
    prose = Target("prose", extraction, "s3", "GSIXPROSELEAD", source_id=source)
    blocks = [
        _block("s1", sentence("GSIXITEMPASSAGE")),
        _block("s2", "Solution: " + sentence(solution.mark)),
        _block("s3", sentence(prose.mark)),
    ]
    _register_revision(world.repository, source_id=source, revision_id=revision)
    world.repository.set_source_current_revision(source, revision)
    _persist(world.repository, _ir([("practice_leads", "Practice leads", blocks, "sha256:leads", 1)]),
             revision_id=revision, extraction_id=extraction)
    _save_members(world.root, [*_members(world.root),
                               {"source_id": source, "revision_id": revision, "default_role": "primary_textbook"}])
    write_item(world.paths, "pi_g6_leads", "GSIXLEADITEM",
               provenance={"origin": "human", "source_refs": [ref(source, extraction, "s1")]})
    return solution, prose
