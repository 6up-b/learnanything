"""E0's question bank, labels and adjudication (spec §5.1, §5.2).

**Slices.** ``smoke`` (16 deterministic cases, no model: pipeline checks, never
verdicts), ``development`` (60-80 written questions, stratified), ``logged``
(every eligible logged learner question, a separate real slice). Generated,
real and exact-reference lookups are reported apart. A library question gets
no oracle source location; a logged ambiguous question gets no fabricated
selection or reference.

**Families first.** Seeds come only from families reserved as
``development`` before any question is written (``corpus.reserve_families``).

**Labels.** Every candidate pooled for a question (each arm's top
``POOL_DEPTH``, the writer's proposed support, a seeded sample of non-hits)
is labelled by two independent passes of different models, blinded to arm and
in different orders, each reading the complete unit text with its section and
preceding context. A label is an ordinal relevance (``required`` > ``helpful``
> ``background`` > ``unrelated``) and each pass proposes the sufficient
evidence sets: AND within a set, OR across sets; optional background never
completes a set. Agreement is Cohen's κ with the confusion table, plus set
agreement. The named adjudicator (a different model family) audits every
disagreement, every accepted set the primary endpoint uses, and a seeded 20%
of agreements, negatives and unanswerable cases. Unjudged material stays
unknown; unaudited labels are never called ground truth.

All model calls go through a ``callers.RoleCaller`` (paid in a real run;
fakes in tests). Prompts are versioned and hashed into the run plan.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field, replace
import hashlib
import json
import re
from typing import Any, Literal

from pydantic import Field

from learnloop.ai.schemas import WireModel
from learnloop.ai.transport import render_structured_prompt

from learnloop.experiments.contextual_embeddings import pins
from learnloop.experiments.contextual_embeddings.corpus import CandidateUnit, CorpusSnapshot, alias
from learnloop.experiments.contextual_embeddings.delivery import Selection

Relevance = Literal["required", "helpful", "background", "unrelated"]
RELEVANCE_ORDER: tuple[str, ...] = ("unrelated", "background", "helpful", "required")
GAIN = {"required": 2.0, "helpful": 1.0, "background": 0.0, "unrelated": 0.0}
SpanRef = tuple[str, str, int, int]

WRITER_VERSION = pins.ROLE_PINS["writer"].prompt_version
LABEL_VERSION = pins.ROLE_PINS["label_a"].prompt_version
ADJUDICATE_VERSION = pins.ROLE_PINS["adjudicator"].prompt_version

NO_SUPPORT_SMOKE = (
    "What is the boiling point of ethanol at sea level?",
    "Who painted the ceiling of the Sistine Chapel?",
)


def _sha(*parts: Any) -> str:
    return hashlib.sha256(json.dumps(parts, sort_keys=True, default=str, ensure_ascii=False).encode()).hexdigest()


def stable_order(values: Sequence[Any], *salt: Any, key=lambda value: value) -> list[Any]:
    return sorted(values, key=lambda value: _sha(pins.SEED, *salt, key(value)))


@dataclass
class EvidenceSet:
    set_id: str
    required: tuple[SpanRef, ...]

    def as_dict(self) -> dict[str, Any]:
        return {"set_id": self.set_id, "required": [list(ref) for ref in self.required]}


@dataclass
class BankQuestion:
    query_id: str
    split: str
    family: str | None
    origin: str
    intent: str
    stratum: str
    question: str
    tags: tuple[str, ...] = ()
    selection: Selection | None = None
    history: tuple[str, ...] = ()
    scope: str = "library"
    answerable: bool = True
    answer_spans: tuple[SpanRef, ...] = ()
    evidence_sets: list[EvidenceSet] = field(default_factory=list)
    proposed_units: tuple[str, ...] = ()
    label_provenance: str = "unlabelled"
    vault: str = ""
    #: The policy-checked selected passage, frozen once (``freeze_context``).
    selected_passage: str | None = None
    context_frozen: bool = False

    @property
    def effective_query(self) -> str:
        """The learner's question text alone (whitespace-normalized)."""

        return " ".join(self.question.split())

    @property
    def retrieval_query(self) -> str:
        """The complete query every arm encodes (no rewrite in the screen): the
        question and, for a known selection, the frozen selected passage."""

        if not self.context_frozen:
            raise RuntimeError("freeze_context before reading a question's context")
        if self.selected_passage:
            return f"{self.effective_query}\n\nSelected passage: {self.selected_passage}"
        return self.effective_query

    def context(self) -> dict[str, Any]:
        """The ONE question context every role reads (Codex review F6): the
        question, the frozen selected passage (a deictic question's referent)
        and the permitted history. Retrieval, labels, adjudication, the tutor
        and the judges all receive exactly this."""

        if not self.context_frozen:
            raise RuntimeError("freeze_context before reading a question's context")
        return {"question": self.effective_query, "selected_passage": self.selected_passage,
                "history": list(self.history)}

    @property
    def known_location(self) -> bool:
        return self.selection is not None

    def public(self) -> dict[str, Any]:
        """Aggregate-safe: no question text, no selection text, aliased ids."""

        return {"query": alias("q", self.query_id), "split": self.split, "family": self.family,
                "origin": self.origin, "intent": self.intent, "stratum": self.stratum, "tags": list(self.tags),
                "known_location": self.known_location, "answerable": self.answerable,
                "evidence_sets": len(self.evidence_sets), "label_provenance": self.label_provenance}

    def private(self) -> dict[str, Any]:
        value = asdict(self)
        value["evidence_sets"] = [item.as_dict() for item in self.evidence_sets]
        return value


def unit_refs(unit: CandidateUnit) -> tuple[SpanRef, ...]:
    return tuple((unit.extraction_id, member.span_id, member.start, member.end) for member in unit.members)


def _query_id(*parts: Any) -> str:
    return "q_" + _sha(*parts)[:16]


#: The selected passage's length bound in every question context (characters).
SELECTION_CONTEXT_CHARS = 1200


class SelectionWithheld(RuntimeError):
    """A question's selection is material the policy withholds."""


def freeze_context(question: BankQuestion, snapshot: CorpusSnapshot) -> BankQuestion:
    """Freeze the question's one policy-checked context (idempotent).

    For a known selection: the learner's quote when every span it covers is
    permitted, else the selected block's own text, whitespace-collapsed and
    bounded at ``SELECTION_CONTEXT_CHARS``. A selection the policy withholds
    raises (the bank never carries one: ``logged_bank`` drops it). A library
    question has no selected passage and never an oracle location.

    The selection itself is frozen to the same policy (Codex re-review F6):
    a rejected quote is dropped and the covered spans keep only permitted
    ones, so delivery (which reads ``question.selection``) hands the tutor and
    the judges exactly the context the labellers saw, never the quote."""

    if question.context_frozen:
        return question
    passage = None
    selection = question.selection
    if selection is not None:
        policy = snapshot.policy
        if not policy.permitted(selection.extraction_id, selection.span_id):
            raise SelectionWithheld("a question's selection is withheld by the experiment's policy")
        block = next((block for block in snapshot.blocks.get(selection.extraction_id, [])
                      if block.span_id == selection.span_id), None)
        quote_ok = bool(selection.quote and selection.quote.strip()) and all(
            policy.permitted(selection.extraction_id, span_id) for span_id in selection.selection_span_ids)
        text = selection.quote if quote_ok else (block.text if block is not None else "")
        passage = " ".join(str(text or "").split())[:SELECTION_CONTEXT_CHARS] or None
        if not quote_ok:
            question.selection = replace(
                selection, quote=None,
                selection_span_ids=tuple(span_id for span_id in selection.selection_span_ids
                                         if policy.permitted(selection.extraction_id, span_id)))
    question.selected_passage = passage
    question.context_frozen = True
    return question


# -- the smoke bank (deterministic, no model) ----------------------------------------


def smoke_bank(snapshot: CorpusSnapshot, *, count: int = pins.SMOKE_CASES) -> tuple[list[BankQuestion], dict[str, Any]]:
    """16 pipeline cases from the corpus itself: lookups of numbered blocks,
    deictic selections with a resolved dependency, distant dependencies,
    exact-term lookups and off-topic no-support controls. For harness checks
    only: their wording is templated, so they never feed a verdict."""

    development = {source for source, family in snapshot.family_of_source.items()
                   if snapshot.family_status.get(family) == "development"}
    units = [unit for unit in snapshot.units if unit.source_id in development]
    by_id = {unit.unit_id: unit for unit in units}
    labelled = stable_order([unit for unit in units if unit.label], "smoke-label", key=lambda unit: unit.unit_id)
    dependent = stable_order([unit_id for unit_id, entry in snapshot.dependencies.items()
                              if unit_id in by_id and entry["targets"]], "smoke-dep")
    questions: list[BankQuestion] = []
    shortfall: dict[str, int] = {}

    def add(question: BankQuestion) -> None:
        if len(questions) < count:
            questions.append(question)

    def family(unit: CandidateUnit) -> str | None:
        return snapshot.family_of_source.get(unit.source_id)

    plan = {"direct_lookup": 4, "reader_deictic": 4, "distant_same_source": 4, "keyword": 2, "no_support": 2}
    for unit in labelled[: plan["direct_lookup"]]:
        add(BankQuestion(_query_id("smoke", "lookup", unit.unit_id), "smoke", family(unit), "smoke_deterministic",
                         "explain", "direct_lookup", f"What does {unit.label} state?", ("exact_reference",),
                         evidence_sets=[EvidenceSet("e1", unit_refs(unit))], answer_spans=unit_refs(unit),
                         vault=snapshot.vault_label))
    shortfall["direct_lookup"] = max(0, plan["direct_lookup"] - len(labelled))
    deictic = 0
    for unit_id in dependent:
        if deictic >= plan["reader_deictic"]:
            break
        unit = by_id[unit_id]
        targets = [by_id[target] for target in snapshot.dependencies[unit_id]["targets"] if target in by_id]
        if not targets:
            continue
        refs = unit_refs(unit) + unit_refs(targets[0])
        add(BankQuestion(_query_id("smoke", "deictic", unit_id), "smoke", family(unit), "smoke_deterministic",
                         "explain", "reader_deictic", "Why does this step follow?", ("long_range",),
                         selection=Selection(unit.extraction_id, unit.members[0].span_id),
                         scope=f"extraction:{unit.extraction_id}",
                         evidence_sets=[EvidenceSet("e1", refs)], answer_spans=unit_refs(unit),
                         vault=snapshot.vault_label))
        deictic += 1
    shortfall["reader_deictic"] = plan["reader_deictic"] - deictic
    window_of = {unit_id: window.window_id for window in snapshot.windows for unit_id in window.unit_ids}
    distant_pair = distance_rule([unit.unit_id for unit in snapshot.units], window_of)
    distant = 0
    for unit_id in dependent:
        if distant >= plan["distant_same_source"]:
            break
        unit = by_id[unit_id]
        far = [by_id[target] for target in snapshot.dependencies[unit_id]["targets"]
               if target in by_id and distant_pair(target, unit_id)]
        if not far:
            continue
        words = " ".join(unit.text.split()[:10])
        add(BankQuestion(_query_id("smoke", "distant", unit_id), "smoke", family(unit), "smoke_deterministic",
                         "explain", "distant_same_source", f"Which earlier result does the passage beginning "
                         f"\"{words}\" rely on, and what does it say?", ("long_range",),
                         evidence_sets=[EvidenceSet("e1", unit_refs(unit) + unit_refs(far[0]))],
                         answer_spans=unit_refs(far[0]), vault=snapshot.vault_label))
        distant += 1
    shortfall["distant_same_source"] = plan["distant_same_source"] - distant
    keyword_units = stable_order([unit for unit in units if len(unit.text.split()) >= 12], "smoke-keyword",
                                 key=lambda unit: unit.unit_id)
    for unit in keyword_units[: plan["keyword"]]:
        term = max(unit.text.split(), key=lambda word: (len(word.strip(".,;:()")), word))
        add(BankQuestion(_query_id("smoke", "keyword", unit.unit_id), "smoke", family(unit), "smoke_deterministic",
                         "explain", "direct_lookup", f"Where is {term.strip('.,;:()')} discussed?", ("keyword",),
                         evidence_sets=[EvidenceSet("e1", unit_refs(unit))], answer_spans=unit_refs(unit),
                         vault=snapshot.vault_label))
    for text in NO_SUPPORT_SMOKE[: plan["no_support"]]:
        add(BankQuestion(_query_id("smoke", "none", text, snapshot.vault_label), "smoke", None,
                         "smoke_deterministic", "explain", "no_support", text, ("no_support",), answerable=False,
                         vault=snapshot.vault_label))
    # Fill any shortfall with further lookups of ordinary units (recorded).
    filler = [unit for unit in keyword_units[plan["keyword"]:] if not any(
        question.answer_spans == unit_refs(unit) for question in questions)]
    for unit in filler:
        if len(questions) >= count:
            break
        words = " ".join(unit.text.split()[:8])
        add(BankQuestion(_query_id("smoke", "fill", unit.unit_id), "smoke", family(unit), "smoke_deterministic",
                         "explain", "direct_lookup", f"Find the passage that begins \"{words}\".", ("filler",),
                         evidence_sets=[EvidenceSet("e1", unit_refs(unit))], answer_spans=unit_refs(unit),
                         vault=snapshot.vault_label))
    shortfall["total"] = count - len(questions)
    return questions, {"shortfall": {key: value for key, value in shortfall.items() if value}, "count": len(questions)}


# -- logged questions ------------------------------------------------------------------


def logged_bank(snapshot: CorpusSnapshot, events: Sequence[Mapping[str, Any]]) -> tuple[list[BankQuestion], dict[str, int]]:
    """Every eligible answered learner question, with its actual selection
    (Reader) and no fabricated selection or reference otherwise. A selection
    the policy now withholds makes the question ineligible (counted)."""

    found: list[BankQuestion] = []
    counts = {"events": len(events), "eligible": 0, "too_short": 0, "selection_withheld": 0,
              "selection_not_current": 0, "duplicate": 0}
    seen: set[str] = set()
    for event in sorted(events, key=lambda value: str(value.get("id") or "")):
        text = " ".join(str(event.get("question_md") or "").split())
        if len(text) < 8:
            counts["too_short"] += 1
            continue
        if text.lower() in seen:
            counts["duplicate"] += 1
            continue
        context = event.get("source_context") if isinstance(event.get("source_context"), dict) else {}
        selection = None
        scope = "library"
        if event.get("context") == "reader" and context.get("extraction_id") and context.get("span_id"):
            extraction_id, span_id = str(context["extraction_id"]), str(context["span_id"])
            if extraction_id not in snapshot.infos:
                counts["selection_not_current"] += 1
                continue
            if not snapshot.policy.permitted(extraction_id, span_id):
                counts["selection_withheld"] += 1
                continue
            selection = Selection(extraction_id, span_id,
                                  tuple(str(value) for value in context.get("selection_span_ids") or ()),
                                  context.get("selection_quote_md"))
            scope = f"extraction:{extraction_id}"
        seen.add(text.lower())
        family = snapshot.family_of_source.get(snapshot.infos[selection.extraction_id].source_id) if selection else None
        found.append(BankQuestion(_query_id("logged", event.get("id"), text), "logged", family, "logged",
                                  "explain", "logged_" + str(event.get("context") or "unknown"), text[:400],
                                  ("real",), selection=selection, scope=scope, vault=snapshot.vault_label))
        counts["eligible"] += 1
    return found, counts


# -- the writer ------------------------------------------------------------------------

WRITER_INSTRUCTIONS = (
    "You write evaluation questions a learner reading this textbook might ask. For each seed, write one "
    "question in the stratum asked, in your own words: never copy a passage's sentences, never name the "
    "passage's number or heading unless the stratum is direct_lookup, and vary wording. For reader_deictic, "
    "write as a learner pointing at the selected passage ('why does this step follow?'). For "
    "distant_same_source, the answer must need the target passage too. For no_support, write a plausible "
    "on-topic question the excerpt does NOT answer. Propose the refs a complete answer needs (support_refs) "
    "and the refs stating the answer (answer_refs) from the refs shown, including distractors only if needed. "
    "Use only the excerpt; never include solutions."
)


class WrittenQuestion(WireModel):
    seed_ref: str = Field(min_length=1)
    question: str = Field(min_length=8)
    support_refs: list[str]
    answer_refs: list[str]
    answerable: bool


class WrittenQuestions(WireModel):
    questions: list[WrittenQuestion]


@dataclass(frozen=True)
class Seed:
    seed_id: str
    stratum: str
    intent: str
    units: tuple[str, ...]
    distractors: tuple[str, ...]
    family: str | None
    selection_unit: str | None = None
    #: How a distant pair is linked: a numbered reference, shared rare terms, none.
    link: str = "none"


_TERM = re.compile(r"[a-z][a-z\-]{4,}")
_STOP = frozenset({"which", "there", "their", "these", "those", "where", "every", "about", "would", "could",
                   "should", "since", "because", "other", "first", "second", "given", "using", "define",
                   "defined", "following", "example", "theorem", "proof", "suppose", "therefore", "hence"})


#: Units at least this far apart in one extraction are "distant" even inside one window.
MIN_UNIT_GAP = 3


def distance_rule(unit_order: Sequence[str], window_of: Mapping[str, str]):
    """``distant(a, b)``: in different grouped windows, or at least
    ``MIN_UNIT_GAP`` units apart (a short source fits one window)."""

    position = {unit_id: index for index, unit_id in enumerate(unit_order)}

    def distant(first: str, second: str) -> bool:
        return (window_of.get(first) != window_of.get(second)
                or abs(position.get(first, 0) - position.get(second, 0)) >= MIN_UNIT_GAP)

    return distant


def lexical_links(units: Sequence[CandidateUnit], distant_pair: Any, *, min_shared: int = 2,
                  max_df: int = 3) -> dict[str, str]:
    """``{unit: earlier unit}`` of the same extraction in another window that
    shares the most rare terms (document frequency <= ``max_df``, at least
    ``min_shared``): the distant-dependency fallback where no numbered
    reference links them. Deterministic (ties by unit id)."""

    by_extraction: dict[str, list[CandidateUnit]] = {}
    for unit in units:
        by_extraction.setdefault(unit.extraction_id, []).append(unit)
    links: dict[str, str] = {}
    for members in by_extraction.values():
        terms = {unit.unit_id: set(_TERM.findall(unit.text.lower())) - _STOP for unit in members}
        frequency: dict[str, int] = {}
        for found in terms.values():
            for term in found:
                frequency[term] = frequency.get(term, 0) + 1
        rare = {unit_id: {term for term in found if frequency[term] <= max_df} for unit_id, found in terms.items()}
        for position, unit in enumerate(members):
            best: tuple[int, str] | None = None
            for earlier in members[:position]:
                if not distant_pair(earlier.unit_id, unit.unit_id):
                    continue
                shared = len(rare[unit.unit_id] & rare[earlier.unit_id])
                if shared >= min_shared and (best is None or (shared, earlier.unit_id) > best):
                    best = (shared, earlier.unit_id)
            if best is not None:
                links[unit.unit_id] = best[1]
    return links


def _intent(stratum: str) -> str:
    return stratum[len("intent_"):] if stratum.startswith("intent_") else "explain"


def plan_seeds(snapshot: CorpusSnapshot, *, strata: Mapping[str, int] | None = None) -> tuple[list[Seed], dict[str, int]]:
    """Development seeds per stratum, from development families only,
    deterministic; each seed carries same-source distractors."""

    strata = dict(strata or pins.DEV_STRATA)
    development = {source for source, family in snapshot.family_of_source.items()
                   if snapshot.family_status.get(family) == "development"}
    units = [unit for unit in snapshot.units if unit.source_id in development and unit.tokens >= 12]
    by_id = {unit.unit_id: unit for unit in units}
    by_source: dict[str, list[CandidateUnit]] = {}
    for unit in units:
        by_source.setdefault(unit.source_id, []).append(unit)
    window_of = {unit_id: window.window_id for window in snapshot.windows for unit_id in window.unit_ids}
    dependent = stable_order([unit_id for unit_id, entry in snapshot.dependencies.items()
                              if unit_id in by_id and any(target in by_id for target in entry["targets"])], "seed-dep")
    ordinary = stable_order(list(by_id), "seed-ordinary")
    used: set[str] = set()
    seeds: list[Seed] = []
    shortfall: dict[str, int] = {}

    def distractors(unit: CandidateUnit) -> tuple[str, ...]:
        same = [other.unit_id for other in by_source.get(unit.source_id, []) if other.unit_id != unit.unit_id]
        return tuple(stable_order(same, "distractor", unit.unit_id)[:3])

    def take(pool: Sequence[str]) -> str | None:
        for unit_id in pool:
            if unit_id not in used:
                used.add(unit_id)
                return unit_id
        return None

    distant_pair = distance_rule([unit.unit_id for unit in snapshot.units], window_of)
    lexical = lexical_links(units, distant_pair)
    distant_pool = [unit_id for unit_id in dependent if any(
        distant_pair(target, unit_id)
        for target in snapshot.dependencies[unit_id]["targets"] if target in by_id)]
    distant_pool += [unit_id for unit_id in stable_order(list(lexical), "seed-lexical") if unit_id not in distant_pool]
    # Distant dependencies are the scarcest seeds: they are taken first.
    order = sorted(strata, key=lambda name: (name != "distant_same_source", name != "reader_deictic"))
    for stratum in order:
        wanted = strata[stratum]
        made = 0
        while made < wanted:
            if stratum == "distant_same_source":
                unit_id = take(distant_pool)
                if unit_id is None:
                    break
                unit = by_id[unit_id]
                targets = [target for target in snapshot.dependencies.get(unit_id, {}).get("targets", [])
                           if target in by_id and distant_pair(target, unit_id)]
                link = "reference" if targets else "shared_terms"
                targets = targets or [lexical[unit_id]]
                seeds.append(Seed(f"seed_{_sha(stratum, unit_id)[:12]}", stratum, _intent(stratum),
                                  (unit_id, targets[0]), distractors(unit),
                                  snapshot.family_of_source.get(unit.source_id), link=link))
            elif stratum == "reader_deictic":
                unit_id = take(dependent) or take(ordinary)
                if unit_id is None:
                    break
                unit = by_id[unit_id]
                targets = [target for target in snapshot.dependencies.get(unit_id, {}).get("targets", [])
                           if target in by_id]
                seeds.append(Seed(f"seed_{_sha(stratum, unit_id)[:12]}", stratum, _intent(stratum),
                                  (unit_id, *targets[:1]), distractors(unit),
                                  snapshot.family_of_source.get(unit.source_id), selection_unit=unit_id,
                                  link="reference" if targets else "none"))
            elif stratum == "intent_compare":
                first = take(ordinary)
                if first is None:
                    break
                unit = by_id[first]
                others = [other for other in ordinary if other not in used and by_id[other].source_id != unit.source_id]
                second = take(others)
                if second is None:
                    shortfall["intent_compare_single_source"] = shortfall.get("intent_compare_single_source", 0) + 1
                    continue
                seeds.append(Seed(f"seed_{_sha(stratum, first, second)[:12]}", stratum, "compare", (first, second),
                                  distractors(unit), snapshot.family_of_source.get(unit.source_id)))
            elif stratum == "direct_lookup":
                unit_id = take([value for value in ordinary if by_id[value].label]) or take(ordinary)
                if unit_id is None:
                    break
                unit = by_id[unit_id]
                seeds.append(Seed(f"seed_{_sha(stratum, unit_id)[:12]}", stratum, "explain", (unit_id,),
                                  distractors(unit), snapshot.family_of_source.get(unit.source_id)))
            else:
                unit_id = take(ordinary)
                if unit_id is None:
                    break
                unit = by_id[unit_id]
                seeds.append(Seed(f"seed_{_sha(stratum, unit_id)[:12]}", stratum, _intent(stratum), (unit_id,),
                                  distractors(unit), snapshot.family_of_source.get(unit.source_id)))
            made += 1
        if made < wanted:
            shortfall[stratum] = wanted - made
    return seeds, shortfall


def writer_prompt(snapshot: CorpusSnapshot, seeds: Sequence[Seed]) -> tuple[str, dict[str, Seed], dict[str, str]]:
    """One writer prompt for a batch of seeds; returns the ref maps."""

    seed_refs = {f"s{index}": seed for index, seed in enumerate(seeds, start=1)}
    unit_refs_map: dict[str, str] = {}
    entries = []
    for ref, seed in seed_refs.items():
        passages = []
        for position, unit_id in enumerate((*seed.units, *seed.distractors), start=1):
            passage_ref = f"{ref}p{position}"
            unit_refs_map[passage_ref] = unit_id
            unit = snapshot.unit(unit_id)
            passages.append({"ref": passage_ref, "section": " > ".join(unit.section), "text": unit.text,
                             "role": "selected" if unit_id == seed.selection_unit else "passage"})
        entries.append({"seed_ref": ref, "stratum": seed.stratum, "intent": seed.intent,
                        "passages": stable_order(passages, "writer-order", ref, key=lambda value: value["ref"])})
    prompt = render_structured_prompt("E0 development questions", WRITER_VERSION,
                                      {"instructions": WRITER_INSTRUCTIONS, "context": {"seeds": entries}})
    return prompt, seed_refs, unit_refs_map


def write_questions(snapshot: CorpusSnapshot, seeds: Sequence[Seed], caller: Any, *,
                    batch: int = 6) -> tuple[list[BankQuestion], dict[str, int]]:
    """Development questions from the writer (one call per batch of seeds).

    ``stats`` keeps the planned denominator: ``planned`` seeds, ``written``,
    ``unanswered_seeds`` (a batch's answer omitted them) and
    ``unattempted_seeds`` (a budget or deadline stop came first, recorded in
    ``stopped``); the questions written before a stop are kept."""

    from learnloop.experiments.contextual_embeddings.budget import E0BudgetExceeded

    questions: list[BankQuestion] = []
    stats: dict[str, Any] = {"planned": len(seeds), "calls": 0, "written": 0, "unanswered_seeds": 0,
                             "unattempted_seeds": 0, "invalid_refs": 0, "stopped": None}
    for start in range(0, len(seeds), batch):
        chunk = list(seeds[start:start + batch])
        prompt, seed_refs, passage_refs = writer_prompt(snapshot, chunk)
        try:
            result = caller.call("writer", prompt=prompt, result_model=WrittenQuestions)
        except E0BudgetExceeded as exc:
            stats["stopped"] = str(exc)
            stats["unattempted_seeds"] = len(seeds) - start
            break
        stats["calls"] += 1
        answered = set()
        for item in result.questions:
            seed = seed_refs.get(item.seed_ref)
            if seed is None or item.seed_ref in answered:
                continue
            answered.add(item.seed_ref)
            support = [passage_refs[ref] for ref in item.support_refs if ref in passage_refs]
            answer = [passage_refs[ref] for ref in item.answer_refs if ref in passage_refs]
            stats["invalid_refs"] += len(item.support_refs) + len(item.answer_refs) - len(support) - len(answer)
            selection = None
            if seed.selection_unit is not None:
                unit = snapshot.unit(seed.selection_unit)
                selection = Selection(unit.extraction_id, unit.members[0].span_id)
            proposed = tuple(dict.fromkeys([*support, *answer]))
            answerable = bool(item.answerable) and seed.stratum != "no_support"
            questions.append(BankQuestion(
                _query_id("dev", seed.seed_id, item.question), "development", seed.family, "writer", seed.intent,
                seed.stratum, " ".join(item.question.split())[:400],
                tuple(sorted({*(snapshot.unit(unit_id).tags[0] for unit_id in seed.units
                                if snapshot.unit(unit_id).tags), *(("cross_source",) if seed.intent == "compare"
                                                                    else ())})),
                selection=selection,
                scope=f"extraction:{selection.extraction_id}" if selection else "library",
                answerable=answerable,
                answer_spans=tuple(ref for unit_id in answer for ref in unit_refs(snapshot.unit(unit_id))),
                proposed_units=proposed, vault=snapshot.vault_label,
            ))
            stats["written"] += 1
        stats["unanswered_seeds"] += len(seed_refs) - len(answered)
    return questions, stats


# -- labels ----------------------------------------------------------------------------

LABEL_INSTRUCTIONS = (
    "Judge each candidate passage for the question. relevance: required (states the answer or a condition the "
    "answer needs), helpful (useful support that is not required), background (on topic, not needed), "
    "unrelated. Then list every SUFFICIENT evidence set: a minimal list of refs that together contain the "
    "answer and every condition it needs (AND within a set); give alternative sets for other valid proofs "
    "(OR across sets). Background never completes a set. If no set suffices, answerable is false. Judge only "
    "from the passages shown."
)


class CandidateLabel(WireModel):
    ref: str = Field(min_length=1)
    relevance: Relevance


class LabelPass(WireModel):
    labels: list[CandidateLabel]
    sufficient_sets: list[list[str]]
    answerable: bool


class AdjudicatedLabels(WireModel):
    labels: list[CandidateLabel]
    sufficient_sets: list[list[str]]
    answerable: bool
    unresolved: bool


RELEVANCE_ONLY_INSTRUCTIONS = (
    "Judge each candidate passage for the question. relevance: required (states the answer or a condition the "
    "answer needs), helpful (useful support that is not required), background (on topic, not needed), "
    "unrelated. This is one batch of a larger pool: judge relevance only; sufficient evidence sets are decided "
    "afterwards over every supporting passage together, so leave sufficient_sets empty here. Judge only from "
    "the passages shown."
)
SUFFICIENCY_INSTRUCTIONS = (
    "These are every passage a first reading judged required or helpful for the question, from the whole "
    "pool. List every SUFFICIENT evidence set: a minimal list of refs that together contain the answer and "
    "every condition it needs (AND within a set; passages from different parts of the pool may be needed "
    "together); give alternative sets for other valid proofs (OR across sets). If no set suffices, answerable "
    "is false. Judge only from the passages shown."
)


class SufficiencyPass(WireModel):
    sufficient_sets: list[list[str]]
    answerable: bool


def label_context(snapshot: CorpusSnapshot, unit: CandidateUnit) -> dict[str, Any]:
    """What a labeller reads of a candidate: its complete text, section and
    the preceding numbered label (no arm, no rank, no score)."""

    from learnloop.experiments.contextual_embeddings.retrieval import preceding_text

    label, _before = preceding_text(snapshot, unit)
    return {"section": " > ".join(unit.section), "within": label, "text": unit.text}


def pool_for(question: BankQuestion, rankings: Mapping[str, Sequence[str]], snapshot: CorpusSnapshot, *,
             depth: int = pins.POOL_DEPTH, non_hits: int = 4) -> list[str]:
    """The labelled pool: each arm's top ``depth``, the writer's proposals,
    the units of any reference evidence, and a seeded sample of non-hits."""

    pool: list[str] = []
    for arm in sorted(rankings):
        pool.extend(rankings[arm][:depth])
    pool.extend(question.proposed_units)
    by_ref = {ref: unit.unit_id for unit in snapshot.units for ref in unit_refs(unit)}
    for evidence in question.evidence_sets:
        pool.extend(by_ref[ref] for ref in evidence.required if ref in by_ref)
    pool = list(dict.fromkeys(pool))
    others = [unit.unit_id for unit in snapshot.units if unit.unit_id not in set(pool)]
    pool.extend(stable_order(others, "non-hit", question.query_id)[:non_hits])
    return pool


def label_prompt(question: BankQuestion, candidates: Mapping[str, Mapping[str, Any]], pass_index: int, *,
                 relevance_only: bool = False) -> str:
    return render_structured_prompt("E0 evidence labels", LABEL_VERSION, {
        "instructions": RELEVANCE_ONLY_INSTRUCTIONS if relevance_only else LABEL_INSTRUCTIONS,
        "context": {**question.context(), "pass": pass_index + 1,
                    "candidates": [{"ref": ref, **payload} for ref, payload in candidates.items()]},
    })


def sufficiency_prompt(question: BankQuestion, candidates: Mapping[str, Mapping[str, Any]], pass_index: int) -> str:
    return render_structured_prompt("E0 evidence sufficiency", LABEL_VERSION, {
        "instructions": SUFFICIENCY_INSTRUCTIONS,
        "context": {**question.context(), "pass": pass_index + 1,
                    "candidates": [{"ref": ref, **payload} for ref, payload in candidates.items()]},
    })


@dataclass
class QuestionLabels:
    query_id: str
    pool: list[str]
    passes: list[dict[str, str]]
    pass_sets: list[list[frozenset[str]]]
    pass_answerable: list[bool]
    final: dict[str, str] = field(default_factory=dict)
    final_sets: list[frozenset[str]] = field(default_factory=list)
    answerable: bool | None = None
    adjudicated: bool = False
    unresolved: bool = False
    audit_reason: str | None = None
    #: Malformed sets a label pass proposed (unknown or duplicate refs), per pass.
    pass_malformed: list[int] = field(default_factory=lambda: [0, 0])
    #: Why an adjudicator verdict was rejected (empty: accepted).
    problems: list[str] = field(default_factory=list)


def _sets_from(chosen_sets: Sequence[Sequence[str]], refs: Mapping[str, str]) -> tuple[list[frozenset[str]], int]:
    """Well-formed sets (every ref known, none repeated) and the malformed count."""

    sets: list[frozenset[str]] = []
    malformed = 0
    for chosen in chosen_sets:
        if not chosen or len(set(chosen)) != len(chosen) or any(ref not in refs for ref in chosen):
            malformed += 1
            continue
        sets.append(frozenset(refs[ref] for ref in chosen))
    return sets, malformed


def _judge(caller: Any, **kwargs: Any) -> None:
    record = getattr(caller, "record_judgment", None)
    if record is not None:
        record(**kwargs)


def label_question(question: BankQuestion, pool: Sequence[str], snapshot: CorpusSnapshot, caller: Any, *,
                   batch: int = 40) -> QuestionLabels:
    """Two blinded passes in different orders (refs are reassigned per pass).

    A pool that fits one batch is labelled and its sets proposed in one call.
    A larger pool is labelled for relevance batch by batch, then ONE joint
    sufficiency review per pass sees every candidate that pass judged
    required or helpful, from every batch, so a conjunction split across
    batches can still be proposed (Codex review F13)."""

    passes: list[dict[str, str]] = []
    pass_sets: list[list[frozenset[str]]] = []
    answerable: list[bool] = []
    malformed: list[int] = []
    unit_refs_of = {unit_id: [list(ref) for ref in unit_refs(snapshot.unit(unit_id))] for unit_id in pool}
    for pass_index, role in enumerate(("label_a", "label_b")):
        order = stable_order(list(pool), "label-order", question.query_id, pass_index)
        labels: dict[str, str] = {}
        sets: list[frozenset[str]] = []
        bad = 0
        any_answerable = False
        joint = len(order) > batch
        for start in range(0, len(order), batch):
            chunk = order[start:start + batch]
            refs = {f"c{index}": unit_id for index, unit_id in enumerate(chunk, start=1)}
            prompt = label_prompt(question, {ref: label_context(snapshot, snapshot.unit(unit_id))
                                             for ref, unit_id in refs.items()}, pass_index, relevance_only=joint)
            result = caller.call(role, prompt=prompt, result_model=LabelPass)
            for item in result.labels:
                if item.ref in refs and refs[item.ref] not in labels:
                    labels[refs[item.ref]] = item.relevance
                    _judge(caller, task="e0_label", left_id=question.query_id, right_kind="e0_unit",
                           right_id=refs[item.ref], verdict=item.relevance,
                           details={"pass": pass_index + 1, "spans": unit_refs_of[refs[item.ref]]})
            if not joint:
                found, count = _sets_from(result.sufficient_sets, refs)
                sets.extend(found)
                bad += count
                any_answerable = bool(result.answerable)
        if joint:
            support = [unit_id for unit_id in order if labels.get(unit_id) in ("required", "helpful")]
            if support:
                refs = {f"c{index}": unit_id for index, unit_id in enumerate(support, start=1)}
                result = caller.call(role, prompt=sufficiency_prompt(
                    question, {ref: label_context(snapshot, snapshot.unit(unit_id)) for ref, unit_id in refs.items()},
                    pass_index), result_model=SufficiencyPass)
                found, bad = _sets_from(result.sufficient_sets, refs)
                sets.extend(found)
                any_answerable = bool(result.answerable)
        ordered_sets = sorted(set(sets), key=lambda value: sorted(value))
        _judge(caller, task="e0_label_sets", left_id=question.query_id,
               verdict=json.dumps([sorted(chosen) for chosen in ordered_sets]),
               details={"pass": pass_index + 1, "answerable": any_answerable, "malformed_sets": bad,
                        "joint_review": joint,
                        "spans": {unit_id: unit_refs_of[unit_id] for chosen in ordered_sets for unit_id in chosen}})
        passes.append(labels)
        pass_sets.append(ordered_sets)
        answerable.append(any_answerable)
        malformed.append(bad)
    return QuestionLabels(question.query_id, list(pool), passes, pass_sets, answerable, pass_malformed=malformed)


def needs_audit(labels: QuestionLabels) -> str | None:
    """Why the adjudicator must see this question, else None (it may still be sampled)."""

    if any(labels.passes[0].get(unit) != labels.passes[1].get(unit) for unit in labels.pool):
        return "disagreement"
    if set(labels.pass_sets[0]) != set(labels.pass_sets[1]) or labels.pass_answerable[0] != labels.pass_answerable[1]:
        return "set_disagreement"
    if any(labels.pass_malformed):
        return "malformed_pass_sets"
    if labels.pass_sets[0]:
        return "accepted_set_used_by_primary_endpoint"
    return None


def adjudication_problems(result: AdjudicatedLabels, refs: Mapping[str, str], labels: QuestionLabels) -> list[str]:
    """Why an adjudicator verdict cannot be accepted (empty: well formed).

    A set with an unknown or repeated ref is rejected WHOLE (dropping the bad
    ref would turn an incomplete conjunction into a weaker accepted set:
    Codex review F7); so is a label for an unknown or repeated candidate, a
    disputed candidate left unlabelled, a set member whose final label (the
    adjudicator's, or the passes' agreement it inherits) is not required or
    helpful (background never completes a set), and an answerability that
    contradicts the sets."""

    problems: list[str] = []
    for chosen in result.sufficient_sets:
        if not chosen:
            problems.append("empty_set")
        elif any(ref not in refs for ref in chosen):
            problems.append("unknown_ref_in_set")
        elif len(set(chosen)) != len(chosen):
            problems.append("duplicate_ref_in_set")
    seen: dict[str, str] = {}
    for item in result.labels:
        if item.ref not in refs:
            problems.append("unknown_ref_labelled")
        elif item.ref in seen:
            problems.append("duplicate_label")
        else:
            seen[item.ref] = item.relevance
    disputed = {unit_id for unit_id in labels.pool if labels.passes[0].get(unit_id) != labels.passes[1].get(unit_id)}
    if any(unit_id in disputed and ref not in seen for ref, unit_id in refs.items()):
        problems.append("disputed_candidate_unlabelled")
    # Every set member is checked against its FINAL label: the adjudicator's
    # own, else the label both passes agreed on (what ``adjudicate`` merges).
    # A member the adjudicator omitted inherits the passes' agreement, so an
    # inherited background never completes a set (Codex re-review F7).
    merged = {ref: seen.get(ref) or (labels.passes[0].get(unit_id) if labels.passes[0].get(unit_id)
                                     == labels.passes[1].get(unit_id) else None)
              for ref, unit_id in refs.items()}
    for chosen in result.sufficient_sets:
        if any(merged.get(ref) not in ("required", "helpful") for ref in chosen if ref in refs):
            problems.append("set_member_not_supporting")
    if result.answerable and not result.sufficient_sets and not result.unresolved:
        problems.append("answerable_without_a_set")
    if not result.answerable and result.sufficient_sets:
        problems.append("unanswerable_with_a_set")
    return sorted(set(problems))


def adjudicate(question: BankQuestion, labels: QuestionLabels, snapshot: CorpusSnapshot, caller: Any) -> QuestionLabels:
    """The named adjudicator decides labels and sets, seeing both passes
    blinded to model; an unresolved or malformed verdict leaves sufficiency
    unresolved and blocks the question (S1)."""

    refs = {f"c{index}": unit_id for index, unit_id in enumerate(
        stable_order(labels.pool, "adjudicate", question.query_id), start=1)}
    back = {unit_id: ref for ref, unit_id in refs.items()}
    payload = {
        **question.context(),
        "candidates": [{"ref": ref, **label_context(snapshot, snapshot.unit(unit_id)),
                        "pass_1": labels.passes[0].get(unit_id), "pass_2": labels.passes[1].get(unit_id)}
                       for ref, unit_id in refs.items()],
        "pass_1_sets": [sorted(back[unit] for unit in chosen) for chosen in labels.pass_sets[0]],
        "pass_2_sets": [sorted(back[unit] for unit in chosen) for chosen in labels.pass_sets[1]],
    }
    prompt = render_structured_prompt("E0 label adjudication", ADJUDICATE_VERSION, {
        "instructions": LABEL_INSTRUCTIONS + " You are the adjudicator: decide each label and the final sets; "
                        "set unresolved true only if the passages cannot settle sufficiency.",
        "context": payload})
    result = caller.call("adjudicator", prompt=prompt, result_model=AdjudicatedLabels)
    problems = adjudication_problems(result, refs, labels)
    final: dict[str, str | None] = {}
    for item in result.labels:
        if item.ref in refs:
            final.setdefault(refs[item.ref], item.relevance)
    for unit_id in labels.pool:
        final.setdefault(unit_id, labels.passes[0].get(unit_id) if labels.passes[0].get(unit_id)
                         == labels.passes[1].get(unit_id) else None)
    labels.final = {key: value for key, value in final.items() if value is not None}
    labels.adjudicated = True
    labels.problems = problems
    if problems or result.unresolved:
        labels.final_sets = []
        labels.answerable = None
        labels.unresolved = True
    else:
        labels.final_sets = [frozenset(refs[ref] for ref in chosen) for chosen in result.sufficient_sets]
        labels.answerable = bool(result.answerable)
        labels.unresolved = False
    _judge(caller, task="e0_label_adjudication", left_id=question.query_id,
           verdict="unresolved" if labels.unresolved else ("answerable" if labels.answerable else "unanswerable"),
           details={"problems": problems, "sets": [sorted(chosen) for chosen in labels.final_sets],
                    "labels": dict(sorted(labels.final.items())),
                    "spans": {unit_id: [list(ref) for ref in unit_refs(snapshot.unit(unit_id))]
                              for chosen in labels.final_sets for unit_id in chosen}})
    return labels


def accept_agreed(labels: QuestionLabels) -> QuestionLabels:
    """An unaudited agreement: model-only labels (reported as such)."""

    labels.final = {unit: value for unit, value in labels.passes[0].items() if labels.passes[1].get(unit) == value}
    labels.final_sets = list(labels.pass_sets[0])
    labels.answerable = labels.pass_answerable[0]
    return labels


def audit_plan(all_labels: Sequence[QuestionLabels], *, share: float = pins.AUDIT_SAMPLE_SHARE) -> dict[str, str]:
    """``{query_id: reason}`` the adjudicator audits: every mandatory case
    and a seeded ``share`` of the rest (agreements, negatives, unanswerable)."""

    plan: dict[str, str] = {}
    rest: list[str] = []
    for labels in all_labels:
        reason = needs_audit(labels)
        if reason is not None:
            plan[labels.query_id] = reason
        else:
            rest.append(labels.query_id)
    for query_id in stable_order(rest, "audit-sample")[: int(round(len(rest) * share))]:
        plan[query_id] = "seeded_sample"
    return plan


def evidence_sets_from_labels(labels: QuestionLabels, snapshot: CorpusSnapshot) -> list[EvidenceSet]:
    sets = []
    for index, members in enumerate(sorted(labels.final_sets, key=lambda value: sorted(value)), start=1):
        refs = tuple(ref for unit_id in sorted(members) for ref in unit_refs(snapshot.unit(unit_id)))
        sets.append(EvidenceSet(f"e{index}", refs))
    return sets


def reference_dependencies(snapshot: CorpusSnapshot, question: BankQuestion) -> list[str]:
    """Deterministic reference following for a known selection (identical
    for every arm): the units its numbered references resolve to."""

    if question.selection is None:
        return []
    owner = next((unit for unit in snapshot.units if unit.extraction_id == question.selection.extraction_id
                  and any(member.span_id == question.selection.span_id for member in unit.members)), None)
    if owner is None:
        return []
    return list(snapshot.dependencies.get(owner.unit_id, {}).get("targets", []))
