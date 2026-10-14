"""Fact-phrased rubric criteria and required methods (owner rule, 2026-10-13).

**The rule.** A rubric criterion names the FACT a step establishes ("shows the
determinant is zero"), not the METHOD used to establish it ("uses cofactor
expansion"). Method-phrased criteria are an artifact of generation forcing a
learning object, facet or concept into a practice question, and graders then
mark down valid alternative routes.

**The one exception.** When the method itself is the point of the item (its
target learning object, facet or concept IS that method or technique), the
item's own statement requires it explicitly ("Use {method} in your answer."),
the item records it as :class:`~learnloop.vault.models.RequiredMethod`, and
only the criteria that record lists may grade use of the method.

This module is the rule's dependency-neutral vocabulary, shared by every
writer (generation paths), the grader, doctor and the repair report:

* :func:`required_method_instruction` / :func:`prompt_states_method` /
  :func:`ensure_method_instruction` - the explicit instruction;
* :func:`method_phrase` - a CONSERVATIVE heuristic for a criterion phrased by
  method: an explicit method verb ("uses", "applies", "via", "by") with a
  method noun ("expansion", "rule", "theorem", "induction"...), and never a
  criterion that leaves the method open ("a valid method", "any method"). It
  misses method-shaped criteria that name no method (for example "computes
  each 2x2 minor"); the repair report's LLM or Decider judge reads those;
* :func:`method_targets` - whether an item's target is a method, from existing
  metadata only: a learning object whose concept is typed ``procedure``, or a
  facet of kind ``procedure_contract``; never for an item whose capability is
  ``method_selection`` (choosing the method is then what is measured);
* :func:`normalize_required_method` - the deterministic check every writer
  runs on a generated payload (a required method only on a method target, its
  criteria in the rubric, its instruction in the prompt; a source statement is
  never rewritten);
* :func:`required_method_problems` - the validation doctor reports;
* :data:`CRITERIA_BY_FACT_GUIDANCE` - the generation prompts' shared text.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Iterable, Literal, Mapping, Sequence

#: The rule's vocabulary version, cited by every generation prompt that
#: carries :data:`CRITERIA_BY_FACT_GUIDANCE` (its prompt versions moved with it).
CRITERIA_BY_FACT_RULE_VERSION = "criteria-by-fact-v1"
#: The instruction a method item's prompt carries (generation writes it).
METHOD_INSTRUCTION_TEMPLATE = "Use {name} in your answer."

#: The shared generation guidance (each path cites it in its prompt).
CRITERIA_BY_FACT_GUIDANCE = (
    "RUBRIC CRITERIA NAME FACTS, NOT METHODS: phrase every grading criterion by the "
    "fact or result a step establishes (for example 'shows det(A) = 0', 'establishes "
    "N(A^T A) = N(A)', 'concludes P(at least one six) = 671/1296'), never by the "
    "method used to establish it ('uses cofactor expansion', 'applies row reduction', "
    "'by the complement rule'): an answer that establishes the same facts by ANY valid "
    "route must be able to earn every criterion. The one exception: when the item's "
    "target is itself a method or technique (a learning object or facet listed with "
    "`required_method_targets`) and executing that method is the point of the item, "
    "you MAY require it: set the practice item's `required_method` to {name, "
    "criterion_ids}, with `name` that method's name, write the sentence 'Use {name} "
    "in your answer.' into the prompt, and list in `criterion_ids` the ONLY criteria "
    "that grade use of the method (phrase them 'Uses {name} ...'). Every other "
    "criterion still names a fact. Without a listed target, leave `required_method` "
    "null and never require a method in the prompt."
)

#: Guidance for a path that keeps a parent's rubric verbatim (variants).
REQUIRED_METHOD_VARIANT_GUIDANCE = (
    "When the parent item has a `required_method`, every new statement must require "
    "it explicitly with the sentence 'Use {name} in your answer.' (the parent's rubric "
    "grades use of that method); otherwise never require a method."
)


def required_method_instruction(name: str) -> str:
    """The explicit instruction for ``name`` ("Use {name} in your answer.")."""

    return METHOD_INSTRUCTION_TEMPLATE.format(name=" ".join(str(name).split()))


_DASHES = str.maketrans({"‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-",
                         "‘": "'", "’": "'", "“": '"', "”": '"'})


def _squash(text: str) -> str:
    folded = unicodedata.normalize("NFKC", str(text or "")).translate(_DASHES)
    return " ".join(folded.split()).casefold()


def prompt_states_method(prompt: Any, name: str) -> bool:
    """Does ``prompt`` name the method ``name`` (case and spacing aside)?"""

    needle = _squash(name)
    return bool(needle) and needle in _squash(prompt if isinstance(prompt, str) else str(prompt or ""))


def ensure_method_instruction(prompt: str, name: str) -> str:
    """``prompt`` with the explicit instruction appended unless it names the method."""

    if prompt_states_method(prompt, name):
        return prompt
    body = (prompt or "").rstrip()
    instruction = required_method_instruction(name)
    return f"{body}\n\n{instruction}" if body else instruction


# -- the conservative heuristic -----------------------------------------------------

#: Method nouns, longest first so the alternation prefers the full name.
_METHOD_NOUNS = (
    r"integration by parts", r"partial fractions?", r"completing the square",
    r"inclusion[- ]exclusion", r"gauss(?:ian)? elimination", r"gauss[- ]jordan(?: elimination)?",
    r"row[- ]echelon(?: form)?", r"row operations?", r"row reduction", r"change of variables?",
    r"cofactors?", r"complement(?:ary counting)?", r"expansion", r"elimination", r"reduction",
    r"substitution", r"decomposition", r"factori[sz]ation", r"diagonali[sz]ation", r"induction",
    r"contradiction", r"contrapositive", r"methods?", r"techniques?", r"algorithms?", r"procedures?",
    r"approach(?:es)?", r"strateg(?:y|ies)", r"tricks?", r"rules?", r"theorems?", r"formulas?",
    r"formulae", r"identit(?:y|ies)", r"lemmas?", r"principles?", r"laws?", r"tests?",
)
_NOUN = "(?:" + "|".join(_METHOD_NOUNS) + ")"
_VERB = r"(?:uses?|using|used|via|applies|apply|applying|applied|employs?|employing|by means of|with the help of)"
#: A method noun phrase: one noun, then any nouns that continue it ("cofactor
#: expansion", "complement rule").
_NOUN_PHRASE = rf"{_NOUN}(?:[\s-]+{_NOUN})*"
_VERB_SPAN = re.compile(rf"\b{_VERB}\b(?P<span>[^.;:()\n]{{0,60}}?\b{_NOUN_PHRASE})\b", re.IGNORECASE)
_BY_SPAN = re.compile(rf"\bby\s+(?P<span>(?:[\w'-]+\s+){{0,3}}?{_NOUN_PHRASE})\b", re.IGNORECASE)
#: A span that leaves the method open is not method phrasing.
_OPEN = re.compile(
    r"\b(?:any|valid|appropriate|suitable|correct|standard|some|whichever|own|other|either|alternative)\b",
    re.IGNORECASE,
)
_ARTICLES = re.compile(r"^(?:the|a|an|its|their|his|her)\s+", re.IGNORECASE)


@dataclass(frozen=True)
class MethodPhrase:
    """A criterion phrased by method: the matched text and the method it names."""

    text: str
    method: str


def method_phrase(description: Any) -> MethodPhrase | None:
    """The method a criterion's description names, by the conservative heuristic.

    Flags only an explicit method verb ("uses", "applies", "via", "by" ...)
    followed within a few words by a method noun ("cofactor expansion", "the
    chain rule", "induction", "Bayes' theorem" ...), and never a span that
    leaves the method open ("a valid method", "any approach"). ``None`` means
    the heuristic saw no method phrasing, not that there is none.
    """

    text = " ".join(str(description or "").split())
    if not text:
        return None
    for pattern in (_VERB_SPAN, _BY_SPAN):
        for match in pattern.finditer(text):
            span = match.group("span").strip()
            if _OPEN.search(span):
                continue
            method = _ARTICLES.sub("", span).strip(" ,'\"")
            if not method:
                continue
            return MethodPhrase(text=match.group(0).strip(), method=method)
    return None


# -- names and matching ------------------------------------------------------------

_GENERIC = frozenset({
    "the", "a", "an", "of", "for", "to", "in", "on", "by", "with", "and", "or", "its", "their", "use",
    "using", "uses", "method", "methods", "technique", "techniques", "algorithm", "procedure", "approach",
    "rule", "rules", "theorem", "formula", "along", "first", "row", "column", "answer", "your", "via",
})


def name_tokens(text: Any) -> frozenset[str]:
    """Content tokens of a method name (generic words dropped, crude singulars)."""

    tokens = set()
    for raw in re.split(r"[^0-9a-z]+", _squash(str(text or ""))):
        if not raw or raw in _GENERIC:
            continue
        if len(raw) > 4 and raw.endswith("s") and not raw.endswith("ss"):
            raw = raw[:-1]
        tokens.add(raw)
    return frozenset(tokens)


def names_match(left: Any, right: Any) -> bool:
    """Do two method names share a content token (case, plurals and generic words aside)?"""

    return bool(name_tokens(left) & name_tokens(right))


# -- method targets ----------------------------------------------------------------

#: A concept of this type is a method or technique (the learning object's concept).
METHOD_CONCEPT_TYPES = frozenset({"procedure"})
#: A facet of this kind is a method's contract.
METHOD_FACET_KINDS = frozenset({"procedure_contract"})
#: An item measuring this capability leaves the method to the learner.
OPEN_METHOD_CAPABILITIES = frozenset({"method_selection"})


@dataclass(frozen=True)
class MethodTarget:
    """A target that IS a method, and the existing metadata that says so."""

    name: str
    basis: Literal["concept_type", "facet_kind"]
    learning_object_id: str | None = None
    concept_id: str | None = None
    facet_id: str | None = None
    aliases: tuple[str, ...] = ()

    def names(self) -> tuple[str, ...]:
        return (self.name, *self.aliases)

    def matches(self, name: Any) -> bool:
        return any(names_match(name, candidate) for candidate in self.names())

    def as_context(self) -> dict[str, Any]:
        """What a generation prompt is shown (name, basis, the linked id)."""

        out: dict[str, Any] = {"name": self.name, "basis": self.basis}
        if self.aliases:
            out["aliases"] = list(self.aliases)
        for key in ("concept_id", "facet_id"):
            value = getattr(self, key)
            if value:
                out[key] = value
        return out

    def link(self) -> dict[str, str]:
        return {
            key: value
            for key in ("learning_object_id", "concept_id", "facet_id")
            if (value := getattr(self, key))
        }


def _facet_name(facet: Any, facet_id: str) -> str:
    title = str(getattr(facet, "title", None) or "").strip()
    return title or facet_id.replace("_", " ").strip()


def method_targets(
    vault: Any,
    *,
    learning_object_id: str | None,
    facet_ids: Iterable[str] = (),
    capability: str | None = None,
) -> list[MethodTarget]:
    """The method targets of an item aimed at ``learning_object_id`` and ``facet_ids``.

    From existing metadata only (no model call): the learning object's concept
    when its type is ``procedure``, and each named facet whose kind is
    ``procedure_contract``. An item whose capability is ``method_selection``
    has none: choosing the method is what it measures.
    """

    if capability in OPEN_METHOD_CAPABILITIES:
        return []
    targets: list[MethodTarget] = []
    learning_objects = getattr(vault, "learning_objects", {}) or {}
    concepts = getattr(vault, "concepts", {}) or {}
    facets = getattr(vault, "evidence_facets", {}) or {}
    lo = learning_objects.get(str(learning_object_id)) if learning_object_id else None
    if lo is not None:
        concept_id = str(getattr(lo, "concept", "") or "")
        concept = concepts.get(concept_id)
        if concept is not None and getattr(concept, "type", None) in METHOD_CONCEPT_TYPES:
            title = str(getattr(concept, "title", "") or "").strip() or concept_id.replace("_", " ")
            targets.append(MethodTarget(
                name=title, basis="concept_type", learning_object_id=lo.id, concept_id=concept_id,
                aliases=tuple(str(alias) for alias in getattr(concept, "aliases", ()) or () if str(alias).strip()),
            ))
    canonical = getattr(vault, "canonical_facet_id", None)
    seen: set[str] = set()
    for raw_id in facet_ids:
        facet_id = canonical(str(raw_id)) if callable(canonical) else str(raw_id)
        if facet_id in seen:
            continue
        seen.add(facet_id)
        facet = facets.get(facet_id)
        if facet is None or getattr(facet, "kind", None) not in METHOD_FACET_KINDS:
            continue
        targets.append(MethodTarget(
            name=_facet_name(facet, facet_id), basis="facet_kind",
            learning_object_id=str(learning_object_id) if learning_object_id else None, facet_id=facet_id,
            aliases=tuple(str(alias) for alias in getattr(facet, "aliases", ()) or () if str(alias).strip()),
        ))
    return targets


def learning_object_method_targets(vault: Any, learning_object_id: str, facet_ids: Iterable[str] = ()) -> list[dict[str, Any]]:
    """A generation context's ``required_method_targets`` for one learning object."""

    return [target.as_context() for target in method_targets(
        vault, learning_object_id=learning_object_id, facet_ids=facet_ids,
    )]


def best_target(name: Any, targets: Sequence[MethodTarget]) -> MethodTarget | None:
    """The target a proposed method name names (most shared tokens), or None."""

    scored = []
    for index, target in enumerate(targets):
        overlap = max((len(name_tokens(name) & name_tokens(candidate)) for candidate in target.names()), default=0)
        if overlap:
            scored.append((-overlap, index, target))
    return min(scored)[2] if scored else None


# -- the deterministic writer check ------------------------------------------------


def _rubric_criterion_ids(payload: Mapping[str, Any]) -> list[str] | None:
    rubric = payload.get("grading_rubric")
    if not isinstance(rubric, Mapping):
        return None
    return [str(criterion.get("id")) for criterion in rubric.get("criteria") or () if isinstance(criterion, Mapping)
            and criterion.get("id")]


def normalize_required_method(
    payload: dict[str, Any],
    targets: Sequence[MethodTarget],
    *,
    source_statement: bool = False,
    rubric_criterion_ids: Sequence[str] | None = None,
) -> list[str]:
    """Hold a generated item's ``required_method`` to the rule, in place.

    Returns notes (``required_method:<what happened>``) for the writer's
    validation record. A required method is kept only when

    * the item's target is a method (``targets``, from :func:`method_targets`)
      and the proposed name names one of them (a shared content token or
      alias); it is then linked to that target;
    * its criteria are criteria of the item's rubric (unknown ids dropped);
    * the prompt states it. A generated prompt gets the explicit instruction
      appended; a SOURCE statement (``source_statement``: a textbook
      exercise's verbatim stem) is never rewritten, so a required method its
      statement does not already state is dropped.

    Anything else drops the field. A payload without one is left as it is.
    """

    raw = payload.get("required_method")
    if raw in (None, {}, ""):
        payload.pop("required_method", None)
        return []
    if hasattr(raw, "model_dump"):
        raw = raw.model_dump(mode="json")
    if not isinstance(raw, Mapping):
        payload.pop("required_method", None)
        return ["required_method:dropped_malformed"]
    name = " ".join(str(raw.get("name") or "").split())
    if not name:
        payload.pop("required_method", None)
        return ["required_method:dropped_unnamed"]
    if not targets:
        payload.pop("required_method", None)
        return ["required_method:dropped_not_a_method_target"]
    target = best_target(name, targets)
    if target is None:
        payload.pop("required_method", None)
        return ["required_method:dropped_unmatched_target"]
    notes: list[str] = []
    known = list(rubric_criterion_ids) if rubric_criterion_ids is not None else _rubric_criterion_ids(payload)
    requested = [str(value) for value in raw.get("criterion_ids") or () if str(value).strip()]
    criterion_ids = [cid for cid in dict.fromkeys(requested) if known is None or cid in known]
    if len(criterion_ids) != len(dict.fromkeys(requested)):
        notes.append("required_method:dropped_unknown_criteria")
    prompt = payload.get("prompt")
    prompt_text = prompt if isinstance(prompt, str) else ""
    if not prompt_states_method(prompt_text, name):
        if source_statement:
            payload.pop("required_method", None)
            return [*notes, "required_method:dropped_source_statement_does_not_state_it"]
        payload["prompt"] = ensure_method_instruction(prompt_text, name)
        notes.append("required_method:instruction_added")
    payload["required_method"] = {"name": name, "criterion_ids": criterion_ids, **target.link()}
    return notes


def inherit_required_method(payload: dict[str, Any], parent: Any) -> list[str]:
    """A variant that keeps its parent's rubric verbatim keeps its required method.

    The parent's method (if any) is copied and the variant's prompt gets the
    explicit instruction when it does not already state it.
    """

    method = getattr(parent, "required_method", None)
    if method is None:
        payload.pop("required_method", None)
        return []
    dumped = method.model_dump(mode="json") if hasattr(method, "model_dump") else dict(method)
    payload["required_method"] = dumped
    prompt = payload.get("prompt")
    prompt_text = prompt if isinstance(prompt, str) else ""
    if prompt_states_method(prompt_text, dumped["name"]):
        return ["required_method:inherited"]
    payload["prompt"] = ensure_method_instruction(prompt_text, dumped["name"])
    return ["required_method:inherited", "required_method:instruction_added"]


# -- validation (doctor) -----------------------------------------------------------


@dataclass(frozen=True)
class RequiredMethodProblem:
    severity: Literal["error", "warning"]
    code: str
    message: str
    criterion_id: str | None = None
    method: str | None = None


def required_method_problems(item: Any, rubric: Any) -> list[RequiredMethodProblem]:
    """What doctor reports for one item under the rule.

    * ``required_method:not_stated`` (error): the item requires a method its
      prompt does not state.
    * ``required_method:unknown_criterion`` (error): the required method lists
      a criterion its rubric does not have.
    * ``criterion:method_phrased`` (warning, the conservative heuristic): a
      criterion phrased by method that is not one of the item's required
      method's criteria.
    """

    problems: list[RequiredMethodProblem] = []
    method = getattr(item, "required_method", None)
    criteria = list(getattr(rubric, "criteria", None) or ())
    ids = {str(criterion.id) for criterion in criteria}
    allowed: set[str] = set()
    if method is not None:
        allowed = {str(value) for value in method.criterion_ids}
        if not prompt_states_method(getattr(item, "prompt", ""), method.name):
            problems.append(RequiredMethodProblem(
                "error", "required_method:not_stated",
                f"{item.id} requires {method.name!r} but its prompt does not state it "
                f"(add {required_method_instruction(method.name)!r})",
                method=method.name,
            ))
        for cid in method.criterion_ids:
            if cid not in ids:
                problems.append(RequiredMethodProblem(
                    "error", "required_method:unknown_criterion",
                    f"{item.id} required method {method.name!r} names unknown criterion {cid!r}",
                    criterion_id=cid, method=method.name,
                ))
    for criterion in criteria:
        if criterion.id in allowed:
            continue
        phrase = method_phrase(criterion.description)
        if phrase is None:
            continue
        problems.append(RequiredMethodProblem(
            "warning", "criterion:method_phrased",
            f"{item.id} criterion {criterion.id!r} is phrased by method ({phrase.text!r}); "
            "name the fact it establishes, or make the method the item's required method",
            criterion_id=str(criterion.id), method=phrase.method,
        ))
    return problems


__all__ = [
    "CRITERIA_BY_FACT_GUIDANCE",
    "CRITERIA_BY_FACT_RULE_VERSION",
    "METHOD_CONCEPT_TYPES",
    "METHOD_FACET_KINDS",
    "METHOD_INSTRUCTION_TEMPLATE",
    "MethodPhrase",
    "MethodTarget",
    "OPEN_METHOD_CAPABILITIES",
    "REQUIRED_METHOD_VARIANT_GUIDANCE",
    "RequiredMethodProblem",
    "best_target",
    "ensure_method_instruction",
    "inherit_required_method",
    "learning_object_method_targets",
    "method_phrase",
    "method_targets",
    "name_tokens",
    "names_match",
    "normalize_required_method",
    "prompt_states_method",
    "required_method_instruction",
    "required_method_problems",
]
