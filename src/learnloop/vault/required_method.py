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

**One structured authority (redesign, 2026-10-14).** The item's
``required_method`` field, frozen in the assessment contract the learner
answered, is the ONLY thing grading, regrading and replay read. No grader
parses the prompt to decide whether a method applies: every round of a
free-text statement reader found new phrasings ("In the worked example, using
X gives 13", "without having to use X", LaTeX-wrapped instructions, "which"
clauses). The text is made to agree with the field when the field is
written, never the other way round.

This module is the rule's dependency-neutral vocabulary, shared by every
writer (generation paths), the grader, doctor and the repair report:

* :func:`required_method_instruction` / :func:`has_method_instruction` /
  :func:`ensure_method_instruction` / :func:`strip_method_instruction` - the
  ONE canonical sentence generated from the field ("Use {name} in your
  answer."): a writer that sets the field appends it (or finds it present
  verbatim), and validation checks for exactly it, normalized only for
  whitespace;
* :func:`is_source_statement` and :class:`SourceStatementDecision` - a
  source-authored statement is never rewritten: whether it requires the
  method is decided ONCE when it is imported (a judgment, ledgered; see
  ``learnloop.content.proposals.method_statement_judge``) or by the owner
  through a proposal, and stored in the field (``statement = source``);
* :func:`advisory_statement_flag` - the demoted statement reader: an
  ADVISORY flag for doctor and the repair report (the prompt may negate the
  method or leave it optional); it never decides grading;
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
* :func:`normalize_required_method` / :func:`inherit_required_method` - the
  deterministic check every writer runs (a required method only on a method
  target, its criteria in the rubric, the canonical sentence in a generated
  prompt, the one-time judgment for a source statement);
* :func:`required_method_problems` - the validation doctor reports;
* :data:`CRITERIA_BY_FACT_GUIDANCE` - the generation prompts' shared text.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Literal, Mapping, Sequence

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


# -- the canonical sentence (the text agrees with the field) ----------------------------


def _whitespace_normalized(text: Any) -> str:
    return " ".join(str(text or "").split())


def has_method_instruction(prompt: Any, name: str) -> bool:
    """Does ``prompt`` carry the canonical sentence for ``name`` verbatim?

    The sentence is :func:`required_method_instruction` ("Use {name} in your
    answer."), generated from the field; the match is exact up to whitespace
    (case, punctuation and wording count). No phrasing of an instruction is
    read: only this one sentence, which the writer that set the field put
    there (redesign 2026-10-14).
    """

    sentence = _whitespace_normalized(required_method_instruction(name))
    return bool(_whitespace_normalized(name)) and sentence in _whitespace_normalized(prompt)


def ensure_method_instruction(prompt: Any, name: str) -> str:
    """``prompt`` with the canonical sentence appended unless it is already
    there verbatim (:func:`has_method_instruction`)."""

    text = prompt if isinstance(prompt, str) else ""
    if has_method_instruction(text, name):
        return text
    body = text.rstrip()
    instruction = required_method_instruction(name)
    return f"{body}\n\n{instruction}" if body else instruction


def strip_method_instruction(prompt: Any, name: str) -> str:
    """``prompt`` without the canonical sentence for ``name`` (an owner's
    accepted override that clears the field on a generated item)."""

    text = prompt if isinstance(prompt, str) else ""
    words = required_method_instruction(name).split()
    if not words:
        return text
    pattern = re.compile(r"\s*" + r"\s+".join(re.escape(word) for word in words))
    stripped = pattern.sub("", text, count=1)
    return stripped.rstrip() if stripped != text else text


def is_source_statement(item: Any) -> bool:
    """Is ``item``'s prompt a source-authored statement that is never rewritten?

    A textbook exercise presented verbatim (``canonical_exercise.relation =
    verbatim``) or an item extracted from a canonical source (a Reader
    import, canonical ingest): its requirement is decided once (the import's
    judgment, or the owner) and stored in the field, never appended to its
    text. A PF variant of such an exercise (``variant_of``) is generated, so
    it carries the canonical sentence.
    """

    exercise = getattr(item, "canonical_exercise", None)
    if exercise is not None and getattr(exercise, "relation", "verbatim") != "variant_of":
        return True
    provenance = getattr(item, "provenance", None)
    return getattr(provenance, "origin", None) == "canonical_extract"


#: :class:`SourceStatementDecision`'s verdict that keeps a source statement's
#: required method (the one-time judgment's ``requires`` option).
SOURCE_REQUIRES = "requires"


@dataclass(frozen=True)
class SourceStatementDecision:
    """The one-time judgment on a source statement (``learnloop.content.
    proposals.method_statement_judge``): its argmax option and the
    ``judgment_ledger`` row that records it."""

    verdict: str
    judgment_id: str


#: ``judge_source(statement, name)``: the one-time judgment, or None when
#: none could be made (no judge ready, a refusal or a failure).
SourceJudge = Callable[[str, str], "SourceStatementDecision | None"]


# -- the advisory heuristic (flags only; never decides grading) ---------------------------

#: Abbreviations whose periods do not end a clause.
_ABBREVIATIONS = re.compile(r"\b(?:e\.\s?g|i\.\s?e|cf|etc|vs)\.", re.IGNORECASE)
_CLAUSES = re.compile(r"[.!?;:\n]+")
#: Formatting wrappers, removed before the advisory flag reads a statement.
_MD_LINK = re.compile(r"!?\[([^\]]*)\]\([^)]*\)|\[([^\]]*)\]\[[^\]]*\]")
_MD_HTML = re.compile(r"</?[a-z][a-z0-9]*\b[^>]*>", re.IGNORECASE)
_TEX_TEXT = re.compile(r"\\[a-zA-Z]+\s*\{([^{}]*)\}")
_TEX_DELIMITERS = re.compile(r"\\[()\[\]]|\$+")
_MD_MARKS = re.compile(r"\*+|~~|`+")
_MD_UNDERSCORES = re.compile(r"(?<![0-9A-Za-z])_+|_+(?![0-9A-Za-z])")


def _plain_text(text: str) -> str:
    text = _MD_HTML.sub("", _MD_LINK.sub(lambda match: match.group(1) or match.group(2) or "", text))
    for _ in range(3):
        text, count = _TEX_TEXT.subn(r"\1", text)
        if not count:
            break
    return _MD_UNDERSCORES.sub("", _MD_MARKS.sub("", _TEX_DELIMITERS.sub(" ", text)))


#: A negation before the method ("without X", "do not use X", "instead of
#: X", "not required to use X", "without having to use X"): the negation,
#: then only filler words.
_FILLER = (r"(?:use|using|apply|applying|employ|employing|rely|relying|on|resort|resorting|to|be|by|via|allowed|"
           r"permitted|make|making|of|any|the|a|an|your|need|needs|needed|required|necessary|obliged|obligated|"
           r"expected|asked|forced|compelled|mandatory|compulsory|have|has|had|having|for|you|it|requirement|that|"
           r"method|technique)")
_NEGATED_BEFORE = re.compile(
    r"(?:\b(?:without|not|never|no|avoid|avoiding|instead of|other than|rather than|except|except for|nor)|n't)"
    rf"\s+(?:{_FILLER}\s+){{0,5}}$"
)
_NEGATED_AFTER = re.compile(
    r"^\s*(?:(?:is|are|may|must|should|can|will|does|do|need)\s+not\b|isn't|aren't|cannot|can't|mustn't|shouldn't|"
    r"doesn't|don't|needn't|(?:is|are)\s+(?:forbidden|disallowed)\b)"
)
#: An option rather than a requirement ("You may use X", "for example by X").
_OPTIONAL_BEFORE = re.compile(
    r"\b(?:may|might|can|could|optionally|optional|feel free|for example|for instance|eg|such as|if you "
    r"(?:like|wish|want|prefer)|either|suggest|suggested|suggests|recommend|recommended|recommends|consider|"
    r"perhaps|possibly|allowed|permitted|welcome|hint|try)\b"
)
#: Another method offered beside it ("Y or X", "X or Y", "X or any other method").
_ALTERNATIVE_BEFORE = re.compile(r"\bor\s+(?:(?:the|a|an|by|via|using)\s+)?$")
_OPTIONAL_AFTER = re.compile(
    r"^\W*(?:or|and/or)\b"
    r"|\bor\s+(?:(?:by|using|with|via|use|apply)\s+)?(?:any|another|some|other)\b(?:\s+[\w'-]+){0,2}?\s+"
    r"(?:method|approach|technique|way|route|strategy)s?\b"
    r"|\bany\s+(?:(?:other|valid|suitable|appropriate|correct|equivalent)\s+)*"
    r"(?:method|approach|technique|way|route|strategy)s?\b"
    r"|\bif you (?:like|wish|want|prefer)\b"
    r"|\b(?:is|are) (?:optional|not required|not necessary|not needed|not mandatory|unnecessary|allowed|permitted)\b"
    r"|\bneed not\b|\boptionally\b|\bor otherwise\b"
)
#: "any (other) method" anywhere before it in the clause ("Use any method, e.g. X").
_ANY_METHOD = re.compile(
    r"\bany\s+(?:(?:other|valid|suitable|appropriate|correct|equivalent)\s+)*"
    r"(?:method|approach|technique|way|route|strategy)s?\b"
)
#: Words of a clause before an occurrence read for an option marker.
_OPTION_WINDOW = 6

#: :func:`advisory_statement_flag`'s readings.
AdvisoryFlag = Literal["negated", "optional"]


def _match_form(text: str) -> str:
    """Case-folded, dashes and hyphens as spaces, one space between words."""

    return " ".join(_squash(text).replace("-", " ").split())


def advisory_statement_flag(prompt: Any, name: str) -> AdvisoryFlag | None:
    """An ADVISORY flag: does ``prompt`` seem to negate the method ``name``
    ("without X", "do not use X", "X is not allowed") or leave it optional
    ("You may use X", "X or any other method", "for example by X")?

    Flags only, for doctor and the repair report's owner review: it never
    decides grading, a writer's field or a publication (redesign
    2026-10-14; the field is the one authority). A conservative regex over
    the occurrences of the name; ``None`` means it saw nothing, not that
    the statement agrees with the field.
    """

    needle = _match_form(_plain_text(str(name or "")))
    if not needle:
        return None
    text = _plain_text(prompt if isinstance(prompt, str) else str(prompt or ""))
    text = _ABBREVIATIONS.sub(lambda match: match.group(0).replace(".", "").replace(" ", ""), text)
    pattern = re.compile(rf"(?<![0-9a-z]){re.escape(needle)}(?![0-9a-z])")
    optional = False
    for clause in _CLAUSES.split(text):
        folded = _match_form(clause)
        for match in pattern.finditer(folded):
            before, after = folded[:match.start()], folded[match.end():]
            if _NEGATED_BEFORE.search(before) or _NEGATED_AFTER.search(after):
                return "negated"
            window = " ".join(before.split()[-_OPTION_WINDOW:])
            if (_OPTIONAL_BEFORE.search(window) or _ALTERNATIVE_BEFORE.search(before)
                    or _OPTIONAL_AFTER.search(after) or _ANY_METHOD.search(before)):
                optional = True
    return "optional" if optional else None


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
    """Does one method name contain the other's content tokens (case, plurals
    and generic words aside)?

    Strict on purpose: "cofactor expansion along the first row" names
    "Cofactor expansion", but "coordinatewise subtraction of the vector" does
    not name "negative of a coordinate vector" merely because both say
    "vector". A required method must BE the target, not resemble it.
    """

    left_tokens, right_tokens = name_tokens(left), name_tokens(right)
    if not left_tokens or not right_tokens:
        return False
    return left_tokens <= right_tokens or right_tokens <= left_tokens


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
        return self.matching_name(name) is not None

    def matching_name(self, name: Any) -> str | None:
        """The target's own name or alias that ``name`` names, if any."""

        return next((candidate for candidate in self.names() if names_match(name, candidate)), None)

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
    """The target a proposed method name names (:func:`names_match`; the
    one sharing most tokens first), or None."""

    scored = []
    for index, target in enumerate(targets):
        matched = [candidate for candidate in target.names() if names_match(name, candidate)]
        if matched:
            overlap = max(len(name_tokens(name) & name_tokens(candidate)) for candidate in matched)
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
    judge_source: SourceJudge | None = None,
) -> list[str]:
    """Hold a written item's ``required_method`` to the rule, in place.

    Returns notes (``required_method:<what happened>``) for the writer's
    validation record. A required method is kept only when

    * the item's target is a method (``targets``, from :func:`method_targets`)
      and the proposed name names one of them (a shared content token or
      alias); it is then linked to that target;
    * its criteria are criteria of the item's rubric (unknown ids dropped);
    * the text is made to agree with it, without reading the text
      (redesign 2026-10-14):

      - a GENERATED prompt gets the canonical sentence
        (:func:`required_method_instruction`) appended unless it is already
        there verbatim;
      - a SOURCE statement (``source_statement``: a textbook exercise's
        verbatim stem) is never rewritten. Whether it requires the method is
        decided once, here, by ``judge_source`` (the Decider, else the LLM
        judge, ledgered; :class:`SourceStatementDecision`): kept as
        ``statement = source`` with the judgment's id when its argmax is
        ``requires``, dropped otherwise, and dropped when no judgment could
        be made (an answer is never failed for a method nobody decided the
        statement requires).

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
    field: dict[str, Any] = {"name": name, "criterion_ids": criterion_ids, **target.link()}
    if source_statement:
        decision = judge_source(prompt_text, name) if judge_source is not None else None
        if decision is None:
            payload.pop("required_method", None)
            return [*notes, "required_method:dropped_source_statement_unjudged"]
        if decision.verdict != SOURCE_REQUIRES:
            payload.pop("required_method", None)
            return [*notes, f"required_method:dropped_source_statement_judged_{decision.verdict}"]
        payload["required_method"] = {
            **field, "statement": "source", "decided_by": "judgment", "judgment_id": decision.judgment_id,
        }
        return [*notes, "required_method:source_statement_judged_requires"]
    updated = ensure_method_instruction(prompt_text, name)
    if updated != prompt_text:
        payload["prompt"] = updated
        notes.append("required_method:instruction_added")
    payload["required_method"] = field
    return notes


def inherit_required_method(payload: dict[str, Any], parent: Any) -> list[str]:
    """A variant that keeps its parent's rubric verbatim keeps its required method.

    The parent's method (name, criteria and links) is copied and the
    variant's GENERATED stem gets the canonical sentence appended unless it
    is already there verbatim, whatever the parent's own statement was (a
    textbook parent's ``source`` decision is about the book's wording, not
    the variant's). Nothing here reads the stem: whether the stem prohibits
    or contradicts the method is the one-time publication judgment
    (``ops.pf_publish``), which refuses such a variant before this runs
    (redesign 2026-10-14; review F10).
    """

    method = getattr(parent, "required_method", None)
    if method is None:
        payload.pop("required_method", None)
        return []
    dumped = method.model_dump(mode="json") if hasattr(method, "model_dump") else dict(method)
    name = " ".join(str(dumped["name"]).split())
    payload["required_method"] = {
        "name": name, "criterion_ids": list(dumped.get("criterion_ids") or ()),
        **{key: dumped[key] for key in ("learning_object_id", "concept_id", "facet_id") if dumped.get(key)},
    }
    prompt = payload.get("prompt")
    prompt_text = prompt if isinstance(prompt, str) else ""
    notes = ["required_method:inherited"]
    updated = ensure_method_instruction(prompt_text, name)
    if updated != prompt_text:
        payload["prompt"] = updated
        notes.append("required_method:instruction_added")
    return notes


# -- validation (doctor) -----------------------------------------------------------


@dataclass(frozen=True)
class RequiredMethodProblem:
    severity: Literal["error", "warning"]
    code: str
    message: str
    criterion_id: str | None = None
    method: str | None = None
    #: ``heuristic`` for an advisory reading (no model call, flags only).
    judge: str | None = None


def required_method_problems(item: Any, rubric: Any) -> list[RequiredMethodProblem]:
    """What doctor reports for one item under the rule.

    Structural checks of the field (redesign 2026-10-14):

    * ``required_method:not_stated`` (error): an ``instruction`` item whose
      prompt lacks the canonical sentence generated from the field ("Use
      {name} in your answer.", exact up to whitespace; no other phrasing is
      read);
    * ``required_method:undecided`` (error): a ``source`` item with no
      recorded decision (``decided_by``; a judgment needs its
      ``judgment_id``);
    * ``required_method:unknown_criterion`` (error): the required method lists
      a criterion its rubric does not have.

    Advisory flags (warnings, the conservative heuristic, ``judge =
    heuristic``; they never change grading):

    * ``required_method:statement_may_disagree``: the prompt seems to negate
      the method or leave it optional (:func:`advisory_statement_flag`);
    * ``criterion:method_phrased``: a criterion phrased by method that is not
      one of the item's required method's criteria.
    """

    problems: list[RequiredMethodProblem] = []
    method = getattr(item, "required_method", None)
    criteria = list(getattr(rubric, "criteria", None) or ())
    ids = {str(criterion.id) for criterion in criteria}
    allowed: set[str] = set()
    prompt = getattr(item, "prompt", "")
    if method is not None:
        allowed = {str(value) for value in method.criterion_ids}
        if getattr(method, "statement", "instruction") == "source":
            decided_by = getattr(method, "decided_by", None)
            if decided_by is None or (decided_by == "judgment" and not getattr(method, "judgment_id", None)):
                problems.append(RequiredMethodProblem(
                    "error", "required_method:undecided",
                    f"{item.id} requires {method.name!r} of its source statement, but no decision is recorded "
                    "(the import's judgment, or the owner's accepted override)",
                    method=method.name,
                ))
        elif not has_method_instruction(prompt, method.name):
            problems.append(RequiredMethodProblem(
                "error", "required_method:not_stated",
                f"{item.id} requires {method.name!r} but its prompt lacks the sentence "
                f"{required_method_instruction(method.name)!r}",
                method=method.name,
            ))
        flag = advisory_statement_flag(prompt, method.name)
        if flag is not None:
            problems.append(RequiredMethodProblem(
                "warning", "required_method:statement_may_disagree",
                f"{item.id} requires {method.name!r}, but its prompt may "
                + ("negate it" if flag == "negated" else "leave it optional")
                + " (advisory: grading reads the field; edit the prompt, or clear the requirement with "
                "`learnloop grading required-method --clear`)",
                method=method.name, judge="heuristic",
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
            criterion_id=str(criterion.id), method=phrase.method, judge="heuristic",
        ))
    return problems


__all__ = [
    "AdvisoryFlag",
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
    "SOURCE_REQUIRES",
    "SourceJudge",
    "SourceStatementDecision",
    "advisory_statement_flag",
    "best_target",
    "ensure_method_instruction",
    "has_method_instruction",
    "inherit_required_method",
    "is_source_statement",
    "learning_object_method_targets",
    "method_phrase",
    "method_targets",
    "name_tokens",
    "names_match",
    "normalize_required_method",
    "required_method_instruction",
    "required_method_problems",
    "strip_method_instruction",
]
