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

* :func:`required_method_instruction` / :func:`method_statement` /
  :func:`prompt_requires_method` / :func:`ensure_method_instruction` - the
  explicit instruction, and whether a statement REQUIRES a method (naming it
  is not enough: "You may use X or any other method" and "Compute det(A)
  without X" name X but contradict a requirement; review F2);
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


#: How a statement treats a method (:func:`method_statement`).
MethodStatement = Literal["required", "contradicted", "mentioned", "absent"]

#: Abbreviations whose periods do not end a clause.
_ABBREVIATIONS = re.compile(r"\b(?:e\.\s?g|i\.\s?e|cf|etc|vs)\.", re.IGNORECASE)
_CLAUSES = re.compile(r"[.!?;:\n]+")

# -- inline formatting (re-review F9) -------------------------------------------------
#: Formatting never changes what a statement asks: a link keeps its text, and
#: emphasis, code spans, strike-through and simple HTML or LaTeX text macros
#: keep their content ("Compute det(A) using **cofactor expansion**.").
_MD_LINK = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")
_MD_HTML = re.compile(
    r"</?(?:b|i|em|strong|u|code|mark|span|sub|sup|small|kbd|var|samp|ins|del|s|tt)\b[^>]*>", re.IGNORECASE)
_TEX_TEXT = re.compile(
    r"\\(?:textbf|textit|textsl|textrm|textsf|texttt|emph|text|underline|mathrm|mathbf|mathit|operatorname)"
    r"\s*\{([^{}]*)\}")
_MD_MARKS = re.compile(r"\*+|~~|`+")
_MD_UNDERSCORES = re.compile(r"(?<![0-9A-Za-z])_+|_+(?![0-9A-Za-z])")


def _plain_text(text: str) -> str:
    """``text`` without inline Markdown, HTML or LaTeX text formatting."""

    text = _MD_HTML.sub("", _MD_LINK.sub(r"\1", text))
    for _ in range(3):
        text, count = _TEX_TEXT.subn(r"\1", text)
        if not count:
            break
    return _MD_UNDERSCORES.sub("", _MD_MARKS.sub("", text))


# -- requirement verbs -----------------------------------------------------------------
#: A requirement verb governing the method ("Use X", "by X", "Using X, ...").
_REQUIRE_BEFORE = re.compile(
    r"\b(?P<verb>use|uses|using|apply|applies|applying|employ|employs|employing|perform|performs|performing|"
    r"carry out|carries out|carrying out|by|via|by means of|with the help of|through)\s+(?:(?:the|a|an|your)\s+)?$"
)
_REQUIRE_AFTER = re.compile(r"^\s*(?:must|is to|should|has to)\s+be\s+used\b|^\s*is\s+required\b")
#: A third-person verb has a subject other than the learner ("The worked
#: example uses X"); it instructs only in a relative clause on the learner's
#: own work ("Write a proof that uses X").
_THIRD_PERSON = frozenset({"uses", "applies", "employs", "performs", "carries out"})
_BASE_FORMS = frozenset({"use", "apply", "employ", "perform", "carry out"})
#: A subject right before a base-form verb describes someone's work ("In the
#: worked example we use X").
_SUBJECTS = frozenset({
    "we", "they", "i", "he", "she", "it", "one", "you", "people", "someone", "everyone", "students", "learners",
    "authors", "readers", "textbooks", "books", "mathematicians",
})
#: A past participle before "by"/"using" describes how something was obtained
#: ("the value obtained by X", "unchanged by X").
_IRREGULAR_PARTICIPLES = frozenset({
    "given", "shown", "done", "found", "proven", "written", "taken", "made", "known", "seen", "drawn", "got",
    "gotten", "built", "set", "put", "brought", "thought", "taught", "meant", "chosen", "driven", "begun",
})
#: Verbs ending in "-ed" that are no participle ("Proceed by induction").
_NOT_PARTICIPLES = frozenset({"proceed", "succeed", "exceed", "embed", "speed", "breed", "bleed", "indeed"})

# -- negations and options ----------------------------------------------------------------
#: A negation governing the method ("without X", "do not use X", "instead of
#: X", "you are not required to use X", "no need to use X"): the negation,
#: then only filler words, then the method.
_FILLER = (r"(?:use|using|apply|applying|employ|employing|rely|relying|on|resort|resorting|to|be|by|via|allowed|"
           r"permitted|make|making|of|any|the|a|an|your|need|needs|needed|required|necessary|obliged|obligated|"
           r"expected|asked|forced|compelled|mandatory|compulsory|have|has|had|for|you|it|requirement|that)")
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

# -- instructions to the learner (re-review F2) -------------------------------------------
#: Bracketed groups and inline math, dropped before a clause's shape is read
#: ("Given A = [[1, 2], [3, 4]], compute ...", "(a) Compute ...").
_GROUPS = re.compile(r"\([^()]*\)|\[[^\[\]]*\]|\{[^{}]*\}|\$[^$]*\$")
#: Labels, courtesy and sequence words that open a clause without changing it.
_LEAD = re.compile(
    r"^(?:\s*(?:[a-z0-9]{1,4}\)|(?:part|question|exercise|problem|step)(?:\s+[a-z0-9]{1,4})?\b|"
    r"(?:please|kindly|now|then|next|first|second|third|finally|lastly|also|again|here|so|hence|thus|"
    r"therefore|instead|and|but)\b)\s*,?)+"
)
#: Verbs that open an instruction to the learner (the imperative).
_IMPERATIVES = (
    "use", "apply", "employ", "perform", "carry out", "compute", "calculate", "evaluate", "find", "determine",
    "show", "prove", "verify", "check", "demonstrate", "derive", "solve", "simplify", "factor", "factorise",
    "factorize", "expand", "integrate", "differentiate", "diagonalize", "diagonalise", "reduce", "row reduce",
    "rewrite", "write", "express", "obtain", "establish", "deduce", "conclude", "justify", "explain", "describe",
    "give", "state", "sketch", "draw", "construct", "compare", "estimate", "approximate", "test", "decide",
    "classify", "identify", "list", "count", "enumerate", "convert", "transform", "invert", "decompose",
    "orthogonalize", "orthogonalise", "orthonormalize", "orthonormalise", "normalize", "normalise", "project",
    "work out", "figure out", "answer", "complete", "argue", "illustrate", "interpret", "analyse", "analyze",
    "assess", "confirm", "plot", "graph", "tabulate", "redo", "recompute", "repeat", "reproduce", "do", "make",
    "remember", "be sure to", "present", "provide", "produce", "set up", "formulate", "translate", "minimize",
    "minimise", "maximize", "maximise", "optimize", "optimise", "bound", "fill in", "summarize", "summarise",
    "define", "generalize", "generalise", "extend", "modify", "correct", "fix", "repair", "re derive", "recover",
    "proceed", "continue", "start", "begin", "attempt", "take", "get", "read", "work", "reason", "fit", "rank",
    "sort", "search", "model", "simulate", "sample", "implement", "code", "program", "encode", "decode", "partition",
    "label", "name", "choose", "select", "pick", "measure", "record", "substitute", "multiply", "divide", "add",
    "subtract", "sum", "rearrange", "isolate", "eliminate", "cancel", "combine", "split", "separate", "group",
    "match", "map", "relate", "represent", "approach", "tackle", "treat", "handle", "predict", "cluster", "train",
    "discuss", "examine", "investigate", "explore", "study", "inspect", "review", "recheck", "double check",
    "cross check", "recalculate", "rederive", "reprove", "reformulate", "recast", "restate", "rephrase", "design",
    "build", "create", "generate", "run", "execute", "trace", "traverse", "parametrize", "parameterize", "place",
    "arrange", "order", "fill", "mark", "shade", "circle", "connect", "go",
)
_IMPERATIVE = re.compile(r"^(?:" + "|".join(sorted(map(re.escape, _IMPERATIVES), key=len, reverse=True)) + r")\b")
#: "You must ...", "Your answer should ...", "It is required that you ...",
#: "Your task is to ...".
_ADDRESSED = re.compile(
    r"^(?:(?:you|your (?:answer|solution|proof|work|working|argument|computation|calculation|derivation|response|"
    r"reasoning)s?|the (?:answer|solution|proof|computation|calculation|derivation|argument))\s+"
    r"(?:must|should|shall|will|ought to|need to|needs to|have to|has to|are to|is to|are required to|"
    r"is required to|are asked to|are expected to|is expected to|are supposed to|will need to|will have to)\b"
    r"|you'll\b|you're to\b|(?:it is|it's) (?:required|necessary|mandatory|essential|important|compulsory)\b"
    r"|(?:your|the) (?:task|goal|aim|job|objective|assignment|exercise|challenge) (?:here )?is to\b"
    r"|(?:we|i) (?:want|need|ask|expect) you to\b)"
)
#: A fronted adverbial or subordinate clause before the instruction ("For
#: the matrix A, ...", "Given A = ..., ...", "In part (b), ...", "To compute
#: det(A), ...", "If A is invertible, ...", "As in part (a), ...").
_ADVERBIAL = re.compile(
    r"^(?:for|given|in|on|at|with|from|after|before|during|throughout|when|whenever|once|assuming|suppose|"
    r"supposing|let|starting|beginning|having|considering|to|below|above|here|if|unless|since|because|as|"
    r"although|though|while|whilst|whereas|provided|now that)\b"
)
#: The generic imperative (a verb the list above lacks: "Tabulate the
#: values by X", "Proceed by X"): a first word that is none of these, then
#: its object, or nothing.
_NOT_IMPERATIVE = frozenset({
    "the", "a", "an", "this", "that", "these", "those", "each", "every", "all", "both", "some", "any", "no",
    "most", "many", "few", "several", "such", "our", "my", "his", "her", "its", "their", "your", "there",
    "is", "are", "was", "were", "be", "been", "has", "have", "had", "do", "does", "did", "will", "would", "can",
    "could", "may", "might", "shall", "should", "must", "and", "or", "nor", "but", "if", "as", "so", "then",
    "than", "of", "in", "on", "at", "by", "for", "with", "from", "to", "into", "onto", "via", "through", "after",
    "before", "when", "while", "since", "because", "although", "though", "unless", "whether", "where", "which",
    "who", "what", "how", "why", "like", "unlike", "about", "under", "over", "between", "among", "within",
    "without", "beyond", "against", "toward", "towards", "across", "along", "around", "behind", "besides", "near",
    "past", "upon", "per", "despite", "note", "notice", "recall", "observe", "consider", "see", "suppose",
    "assume", "imagine", "earlier", "later", "elsewhere", "otherwise", "likewise", "often", "sometimes",
    "always", "never", "also", "again", "already", "still", "just", "only", "even", "now", "here", "not",
})
_OBJECTS = frozenset({
    "the", "a", "an", "this", "these", "those", "each", "every", "all", "both", "your", "its", "their", "it",
    "them", "our", "some", "any", "his", "her",
})
#: A subordinate clause (a description, a question about the method): its
#: requirement verb is not the learner's instruction.
#: ("Determine whether S is a basis by X" still instructs; "Decide whether
#: to use X" does not.)
_SUBORDINATE = re.compile(
    r"\b(?:which|who|whom|whose|where|wherein|whereby|why|how|whether to|what|when|whenever|while|whilst|"
    r"whereas|because|since|although|though|unless|like|as in|as the|as it|as they|as we|as shown|as done|"
    r"as described|the way|just as|similar to|similarly)\b"
    # A fronted condition ("If using X, ...") is not an instruction either.
    r"|^(?:if|once)\b"
)
_WORDS = re.compile(r"[a-z][a-z']*")


def _last_word(text: str) -> str:
    words = _WORDS.findall(text)
    return words[-1] if words else ""


def _participle(word: str) -> bool:
    return word in _IRREGULAR_PARTICIPLES or (len(word) > 4 and word.endswith("ed") and word not in _NOT_PARTICIPLES)


def _generic_imperative(segment: str) -> bool:
    """A first word shaped like a verb the imperative list lacks, then its object or nothing."""

    words = segment.split()
    if not words:
        return False
    first = words[0]
    if (not first.isalpha() or first in _NOT_IMPERATIVE or first in _SUBJECTS or first.endswith(("ly", "ing"))
            or _participle(first) or (first.endswith("s") and not first.endswith("ss"))):
        return False
    return len(words) == 1 or words[1] in _OBJECTS


def _instruction_opens(segment: str) -> bool:
    return bool(_IMPERATIVE.match(segment) or _ADDRESSED.match(segment) or _generic_imperative(segment))


def _incidental(segment: str) -> bool:
    """A comma segment that carries no clause of its own (empty, or math: "y = 2",
    "Solve Ax = b"); a segment opening with a determiner or a subject is prose
    ("The worked example solves Ax = b")."""

    if not segment or not segment[0].isalpha():
        return True
    first = segment.split()[0]
    return "=" in segment and first not in _NOT_IMPERATIVE and first not in _SUBJECTS


def _instructs(head: str) -> bool:
    """Is a requirement at the end of ``head`` (a clause's text before it) the
    learner's instruction?

    The clause's main part (its first comma segment that is not a fronted
    adverbial or math) must open with an instruction ("Compute det(A) by X",
    "You must use X", "Your answer should use X"); with none before it, the
    requirement opens the clause ("Use X", "Using X, ...", "In part (b), use
    X"). A requirement in a later segment counts when that segment is itself
    an instruction ("..., then verify it by X") or it directly follows a
    comma ("Show, using X, that ..."); never inside a subordinate clause
    ("..., which the worked example finds by X", "Explain how to use X").
    Conservative: anything else reads as a description.
    """

    text = head
    for _ in range(4):
        text, count = _GROUPS.subn(" ", text)
        if not count:
            break
    segments = [" ".join(_LEAD.sub("", segment).split()) for segment in text.split(",")]
    last = len(segments) - 1
    trigger_segment = segments[last]
    if _SUBORDINATE.search(trigger_segment):
        return False  # "When using X, ...", "..., which the worked example finds by X"
    main = next((index for index, segment in enumerate(segments)
                 if not _incidental(segment) and not _ADVERBIAL.match(segment)), None)
    if main is None:
        return True
    if not _instruction_opens(segments[main]) or _SUBORDINATE.search(segments[main]):
        return False
    return main == last or not trigger_segment or _instruction_opens(trigger_segment)


def _requires_here(before: str, after: str) -> bool:
    """Does the clause require the method at this occurrence (``before`` and
    ``after`` it, case-folded)?"""

    match = _REQUIRE_BEFORE.search(before)
    if match is not None:
        verb, head = match.group("verb"), before[:match.start()]
        previous = _last_word(head)
        if verb in _THIRD_PERSON:
            if previous != "that":
                return False
            head = head[:head.rstrip().rfind("that")]
        elif verb in _BASE_FORMS:
            if previous in _SUBJECTS:
                return False
        elif _participle(previous):
            return False
        return _instructs(head)
    if _REQUIRE_AFTER.search(after):
        # A passive requirement ("X must be used"): X is the subject.
        return _instructs(re.sub(r"(?:\b(?:the|a|an|your)\s*)$", "", before))
    return False


def _match_form(text: str) -> str:
    """Case-folded, dashes and hyphens as spaces, one space between words."""

    return " ".join(_squash(text).replace("-", " ").split())


def method_statement(prompt: Any, name: str) -> MethodStatement:
    """How ``prompt`` treats the method ``name`` (review F2).

    * ``required``: some clause instructs the learner to use it (the
      explicit instruction "Use {name} in your answer.", or a requirement
      verb governing it in an instruction: "Compute det(A) by cofactor
      expansion.", "Using X, ...", "You must use X") and no clause
      contradicts it;
    * ``contradicted``: a clause negates it ("without X", "do not use X",
      "instead of X", "X is not allowed", "you are not required to use X")
      or leaves it optional ("You may use X", "X or any other method", "for
      example by X", "X or Y"): a requirement would contradict the
      statement;
    * ``mentioned``: it occurs only in other ways ("Explain why X works",
      and descriptions: "The worked example uses X", "..., which the worked
      example finds by X"; re-review F2);
    * ``absent``: the name does not occur.

    Conservative on purpose: a statement that only names or describes the
    method never reads as requiring it, and an ambiguous one reads as
    contradicting it. Case, spacing, dashes, hyphens and inline formatting
    (Markdown, HTML, LaTeX text macros; re-review F9) aside.
    """

    needle = _match_form(_plain_text(str(name or "")))
    if not needle:
        return "absent"
    text = _plain_text(prompt if isinstance(prompt, str) else str(prompt or ""))
    text = _ABBREVIATIONS.sub(lambda match: match.group(0).replace(".", "").replace(" ", ""), text)
    pattern = re.compile(rf"(?<![0-9a-z]){re.escape(needle)}(?![0-9a-z])")
    found = required = False
    for clause in _CLAUSES.split(text):
        folded = _match_form(clause)
        for match in pattern.finditer(folded):
            found = True
            before, after = folded[:match.start()], folded[match.end():]
            window = " ".join(before.split()[-_OPTION_WINDOW:])
            if (_NEGATED_BEFORE.search(before) or _NEGATED_AFTER.search(after)
                    or _OPTIONAL_BEFORE.search(window) or _ALTERNATIVE_BEFORE.search(before)
                    or _OPTIONAL_AFTER.search(after) or _ANY_METHOD.search(before)):
                return "contradicted"
            if _requires_here(before, after):
                required = True
    if required:
        return "required"
    return "mentioned" if found else "absent"


def prompt_requires_method(prompt: Any, name: str) -> bool:
    """Does ``prompt`` require the method ``name`` (:func:`method_statement`)?"""

    return method_statement(prompt, name) == "required"


def ensure_method_instruction(prompt: str, name: str) -> str:
    """``prompt`` with the explicit instruction appended unless it already
    requires the method.

    A caller checks :func:`method_statement` for ``contradicted`` first: the
    instruction appended to a statement that negates the method or leaves it
    optional would contradict it (the writers drop the requirement instead).
    """

    if prompt_requires_method(prompt, name):
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
) -> list[str]:
    """Hold a generated item's ``required_method`` to the rule, in place.

    Returns notes (``required_method:<what happened>``) for the writer's
    validation record. A required method is kept only when

    * the item's target is a method (``targets``, from :func:`method_targets`)
      and the proposed name names one of them (a shared content token or
      alias); it is then linked to that target;
    * its criteria are criteria of the item's rubric (unknown ids dropped);
    * the prompt REQUIRES it (:func:`method_statement`; naming it is not
      enough). A generated prompt that does not gets the explicit instruction
      appended; a SOURCE statement (``source_statement``: a textbook
      exercise's verbatim stem) is never rewritten, so a required method its
      statement does not already require is dropped; and a prompt that
      negates the method or leaves it optional drops it (the instruction
      would contradict the statement).

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
    statement = method_statement(prompt_text, name)
    if statement == "contradicted":
        # The statement negates the method or leaves it optional: requiring it
        # would contradict what the learner reads (review F2).
        payload.pop("required_method", None)
        return [*notes, "required_method:dropped_prompt_contradicts_it"]
    if statement != "required":
        if source_statement:
            payload.pop("required_method", None)
            return [*notes, "required_method:dropped_source_statement_does_not_state_it"]
        payload["prompt"] = ensure_method_instruction(prompt_text, name)
        notes.append("required_method:instruction_added")
    payload["required_method"] = {"name": name, "criterion_ids": criterion_ids, **target.link()}
    return notes


#: :func:`inherit_required_method`'s note for a variant stem that contradicts
#: the parent's method: the variant may not be published (re-review F10).
VARIANT_CONTRADICTS_METHOD = "required_method:prompt_contradicts_it"


def inherit_required_method(payload: dict[str, Any], parent: Any) -> list[str]:
    """A variant that keeps its parent's rubric verbatim keeps its required method.

    The parent's method (if any) is copied and the variant's prompt gets the
    explicit instruction when it does not already require it. A variant stem
    that negates the method or leaves it optional gets no instruction (it
    would contradict the statement; re-review F10) and is noted
    (:data:`VARIANT_CONTRADICTS_METHOD`): the parent's rubric grades use of
    the method, so such a variant is rejected, never published
    (``ops.pf_publish``).
    """

    method = getattr(parent, "required_method", None)
    if method is None:
        payload.pop("required_method", None)
        return []
    dumped = method.model_dump(mode="json") if hasattr(method, "model_dump") else dict(method)
    payload["required_method"] = dumped
    prompt = payload.get("prompt")
    prompt_text = prompt if isinstance(prompt, str) else ""
    statement = method_statement(prompt_text, dumped["name"])
    if statement == "required":
        return ["required_method:inherited"]
    if statement == "contradicted":
        return ["required_method:inherited", VARIANT_CONTRADICTS_METHOD]
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
      prompt does not require (absent, or only mentioned).
    * ``required_method:contradicted`` (error): the item requires a method its
      prompt negates or leaves optional ("without X", "You may use X or any
      other method"): grading would penalize a learner who follows it.
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
        statement = method_statement(getattr(item, "prompt", ""), method.name)
        if statement == "contradicted":
            problems.append(RequiredMethodProblem(
                "error", "required_method:contradicted",
                f"{item.id} requires {method.name!r} but its prompt negates it or leaves it optional "
                f"(state {required_method_instruction(method.name)!r} instead, or drop the requirement)",
                method=method.name,
            ))
        elif statement != "required":
            problems.append(RequiredMethodProblem(
                "error", "required_method:not_stated",
                f"{item.id} requires {method.name!r} but its prompt does not require it "
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
    "VARIANT_CONTRADICTS_METHOD",
    "best_target",
    "ensure_method_instruction",
    "inherit_required_method",
    "MethodStatement",
    "learning_object_method_targets",
    "method_phrase",
    "method_statement",
    "method_targets",
    "name_tokens",
    "names_match",
    "normalize_required_method",
    "prompt_requires_method",
    "required_method_instruction",
    "required_method_problems",
]
