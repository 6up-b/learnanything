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
from dataclasses import asdict, dataclass, field
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

    @property
    def effective_query(self) -> str:
        """The complete query every arm encodes (no rewrite in the screen)."""

        return " ".join(self.question.split())

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
    """Development questions from the writer (one call per batch of seeds)."""

    questions: list[BankQuestion] = []
    stats = {"calls": 0, "written": 0, "unanswered_seeds": 0, "invalid_refs": 0}
    for start in range(0, len(seeds), batch):
        chunk = list(seeds[start:start + batch])
        prompt, seed_refs, passage_refs = writer_prompt(snapshot, chunk)
        result = caller.call("writer", prompt=prompt, result_model=WrittenQuestions)
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


def label_prompt(question: BankQuestion, candidates: Mapping[str, Mapping[str, Any]], pass_index: int) -> str:
    return render_structured_prompt("E0 evidence labels", LABEL_VERSION, {
        "instructions": LABEL_INSTRUCTIONS,
        "context": {"question": question.effective_query, "pass": pass_index + 1,
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


def label_question(question: BankQuestion, pool: Sequence[str], snapshot: CorpusSnapshot, caller: Any, *,
                   batch: int = 40) -> QuestionLabels:
    """Two blinded passes in different orders (refs are reassigned per pass)."""

    passes: list[dict[str, str]] = []
    pass_sets: list[list[frozenset[str]]] = []
    answerable: list[bool] = []
    for pass_index, role in enumerate(("label_a", "label_b")):
        order = stable_order(list(pool), "label-order", question.query_id, pass_index)
        labels: dict[str, str] = {}
        sets: list[frozenset[str]] = []
        any_answerable = False
        for start in range(0, len(order), batch):
            chunk = order[start:start + batch]
            refs = {f"c{index}": unit_id for index, unit_id in enumerate(chunk, start=1)}
            prompt = label_prompt(question, {ref: label_context(snapshot, snapshot.unit(unit_id))
                                             for ref, unit_id in refs.items()}, pass_index)
            result = caller.call(role, prompt=prompt, result_model=LabelPass)
            for item in result.labels:
                if item.ref in refs and refs[item.ref] not in labels:
                    labels[refs[item.ref]] = item.relevance
            for chosen in result.sufficient_sets:
                members = frozenset(refs[ref] for ref in chosen if ref in refs)
                if members and len(members) == len(set(chosen)):
                    sets.append(members)
            any_answerable = any_answerable or result.answerable
        passes.append(labels)
        pass_sets.append(sorted(set(sets), key=lambda value: sorted(value)))
        answerable.append(any_answerable)
    return QuestionLabels(question.query_id, list(pool), passes, pass_sets, answerable)


def needs_audit(labels: QuestionLabels) -> str | None:
    """Why the adjudicator must see this question, else None (it may still be sampled)."""

    if any(labels.passes[0].get(unit) != labels.passes[1].get(unit) for unit in labels.pool):
        return "disagreement"
    if set(labels.pass_sets[0]) != set(labels.pass_sets[1]) or labels.pass_answerable[0] != labels.pass_answerable[1]:
        return "set_disagreement"
    if labels.pass_sets[0]:
        return "accepted_set_used_by_primary_endpoint"
    return None


def adjudicate(question: BankQuestion, labels: QuestionLabels, snapshot: CorpusSnapshot, caller: Any) -> QuestionLabels:
    """The named adjudicator decides labels and sets, seeing both passes
    blinded to model; an unresolved verdict blocks the question (S1)."""

    refs = {f"c{index}": unit_id for index, unit_id in enumerate(
        stable_order(labels.pool, "adjudicate", question.query_id), start=1)}
    back = {unit_id: ref for ref, unit_id in refs.items()}
    payload = {
        "question": question.effective_query,
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
    final = {refs[item.ref]: item.relevance for item in result.labels if item.ref in refs}
    for unit_id in labels.pool:
        final.setdefault(unit_id, labels.passes[0].get(unit_id) if labels.passes[0].get(unit_id)
                         == labels.passes[1].get(unit_id) else None)
    labels.final = {key: value for key, value in final.items() if value is not None}
    labels.final_sets = [frozenset(refs[ref] for ref in chosen if ref in refs) for chosen in result.sufficient_sets]
    labels.final_sets = [chosen for chosen in labels.final_sets if chosen]
    labels.answerable = result.answerable
    labels.adjudicated = True
    labels.unresolved = bool(result.unresolved)
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
