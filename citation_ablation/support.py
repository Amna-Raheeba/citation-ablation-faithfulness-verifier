"""Deterministic support and contradiction checks, text-only.

covers(passage, fact): the passage contains the fact's surface.
contradicts(passage, fact): only for number facts with a key — the passage
states the same attribute with a different number and never states the
claim's number. Numbers are compared numerically, so "200" and "200.0"
are the same value.
"""

from __future__ import annotations

from .facts import _number_equal, extract_numbers, normalize
from .models import Claim, Fact


def covers(passage_text: str, fact: Fact) -> bool:
    """True when the passage text contains the fact's surface."""
    norm_passage = normalize(passage_text)
    if fact.kind == "number":
        try:
            target = float(fact.value.replace(",", ""))
        except ValueError:
            return normalize(fact.surface) in norm_passage
        return any(_number_equal(n, target) for n in extract_numbers(passage_text))
    return normalize(fact.surface) in norm_passage


def contradicts(passage_text: str, fact: Fact) -> bool:
    """True when the passage states the same keyed number differently.

    Only number facts with a non-empty key can contradict: the passage must
    mention the key, contain a number different from the fact's value, and
    not contain the fact's value anywhere. Entity/term facts never
    contradict under this rule (a passage cannot contradict a name by
    merely mentioning something else).
    """
    if fact.kind != "number" or not fact.key:
        return False
    norm_passage = normalize(passage_text)
    if normalize(fact.key) not in norm_passage:
        return False
    if covers(passage_text, fact):
        return False
    try:
        target = float(fact.value.replace(",", ""))
    except ValueError:
        return False
    numbers = extract_numbers(passage_text)
    return any(not _number_equal(n, target) for n in numbers)


def claim_coverage(claim: Claim, passages: list) -> set:
    """Indexes of the claim's facts covered by at least one passage."""
    covered: set = set()
    for index, fact in enumerate(claim.facts):
        if any(covers(p.text, fact) for p in passages):
            covered.add(index)
    return covered


def is_supported(claim: Claim, passages: list) -> bool:
    """True when every fact of the claim is covered by the passages."""
    return len(claim_coverage(claim, passages)) == len(claim.facts)


def passage_covers(passage_text: str, claim: Claim) -> set:
    """Indexes of the claim's facts this single passage covers."""
    return {i for i, fact in enumerate(claim.facts)
            if covers(passage_text, fact)}


def passage_contradicts(passage_text: str, claim: Claim) -> bool:
    """True when the passage contradicts any fact of the claim."""
    return any(contradicts(passage_text, fact) for fact in claim.facts)
