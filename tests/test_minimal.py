"""Tests for minimal sufficient sets, collapse depth, critical citations."""

import random

from citation_ablation.minimal import (all_minimal_sets, collapse_depth,
                                       critical_citations, exact_minimal_set,
                                       greedy_minimal_set)
from citation_ablation.models import Claim, Fact, Passage


def _claim_with_terms(*terms):
    facts = tuple(Fact("term", "", t, t) for t in terms)
    return Claim("c", " ".join(terms), facts=facts)


def _passage(pid, *terms):
    return Passage(pid, " ".join(terms) or "nothing here")


def test_greedy_finds_single_passage_cover():
    claim = _claim_with_terms("alpha", "beta")
    passages = [_passage("p1", "alpha", "beta"), _passage("p2", "alpha")]
    assert greedy_minimal_set(claim, passages) == ["p1"]
    assert exact_minimal_set(claim, passages) == ["p1"]


def test_greedy_returns_none_when_unsupported():
    claim = _claim_with_terms("alpha", "beta")
    passages = [_passage("p1", "alpha")]
    assert greedy_minimal_set(claim, passages) is None
    assert exact_minimal_set(claim, passages) is None


def test_zero_fact_claim_minimal_set_is_empty():
    claim = Claim("c", "No facts.", facts=())
    passages = [_passage("p1", "alpha")]
    assert greedy_minimal_set(claim, passages) == []
    assert exact_minimal_set(claim, passages) == []
    assert collapse_depth(claim, passages) == 2  # len + 1: nothing can break it


def test_collapse_depth_values():
    claim = _claim_with_terms("alpha", "beta")
    single = [_passage("p1", "alpha", "beta")]
    assert collapse_depth(claim, single) == 1
    duplicate = [_passage("p1", "alpha", "beta"),
                 _passage("p2", "alpha", "beta")]
    assert collapse_depth(claim, duplicate) == 2
    assert collapse_depth(claim, [_passage("p1", "alpha")]) == 0


def test_critical_citations_intersection():
    claim = _claim_with_terms("alpha", "beta", "gamma")
    passages = [_passage("p1", "alpha", "beta"),
                _passage("p2", "gamma"),
                _passage("p3", "alpha")]
    assert critical_citations(claim, passages) == ["p1", "p2"]
    assert all_minimal_sets(claim, passages) == [["p1", "p2"]]


def test_greedy_never_smaller_than_exact_random():
    """Property: greedy size >= exact size on seeded random instances,
    and greedy is exact most of the time (not always — that is the point
    of the greedy stress metric in the evaluation)."""
    rng = random.Random(7)
    equal = 0
    checked = 0
    for _ in range(100):
        k = rng.randint(4, 8)
        facts = tuple(Fact("term", "", "f%d" % i, "f%d" % i)
                      for i in range(k))
        claim = Claim("c", " ".join("f%d" % i for i in range(k)),
                      facts=facts)
        passages = []
        for j in range(rng.randint(3, 6)):
            covered = [i for i in range(k) if rng.random() < 0.5]
            text = " ".join("f%d" % i for i in covered) or "nothing here"
            passages.append(Passage("p%d" % j, text))
        if not all(any("f%d" % i in p.text.split() for p in passages)
                   for i in range(k)):
            continue
        greedy = greedy_minimal_set(claim, passages)
        exact = exact_minimal_set(claim, passages)
        assert greedy is not None and exact is not None
        assert len(greedy) >= len(exact)
        checked += 1
        if len(greedy) == len(exact):
            equal += 1
    assert checked > 50
    assert equal / checked >= 0.9


def test_exact_minimal_set_none_when_too_large():
    claim = _claim_with_terms(*("f%d" % i for i in range(13)))
    passages = [_passage("p%d" % j, *("f%d" % i for i in range(13)))
                for j in range(13)]
    assert exact_minimal_set(claim, passages) is None
    assert greedy_minimal_set(claim, passages) == ["p0"]


def test_all_minimal_sets_counts_alternatives():
    claim = _claim_with_terms("alpha", "beta")
    passages = [_passage("p1", "alpha", "beta"),
                _passage("p2", "alpha", "beta"),
                _passage("p3", "alpha")]
    sets = all_minimal_sets(claim, passages)
    assert sets == [["p1"], ["p2"]]
    assert critical_citations(claim, passages) == []


def test_greedy_tie_break_is_deterministic():
    claim = _claim_with_terms("alpha", "beta")
    passages = [_passage("p2", "alpha", "beta"),
                _passage("p1", "alpha", "beta")]
    first = greedy_minimal_set(claim, passages)
    second = greedy_minimal_set(claim, list(reversed(passages)))
    assert first == ["p2"]
    assert second == ["p1"]
