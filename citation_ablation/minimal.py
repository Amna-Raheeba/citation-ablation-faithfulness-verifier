"""Minimal sufficient citation sets, collapse depth, critical citations.

A sufficient set is a subset of a claim's cited passages that still
supports the claim (covers every fact). Greedy set cover is fast and
usually exact on small sets; the exact minimum is found by brute force
when the cited set is small enough (n <= 12, at most 4096 subsets).

Collapse depth is the smallest number of citations whose removal breaks
support: 0 when the claim is already unsupported, 1 when a single removal
suffices. Critical citations are the passages present in every minimal
sufficient set — remove one and the answer cannot be rebuilt from the
remaining citations alone.
"""

from __future__ import annotations

from itertools import combinations

from .models import Claim
from .support import covers, is_supported

MAX_EXACT = 12


def greedy_minimal_set(claim: Claim, passages: list) -> list | None:
    """Greedy set cover: repeatedly take the passage covering most uncovered facts.

    Returns passage ids, or None when the full set does not support the claim.
    Ties break by citation order, so the result is deterministic.
    """
    if not is_supported(claim, passages):
        return None
    uncovered = set(range(len(claim.facts)))
    chosen: list = []
    remaining = list(passages)
    while uncovered:
        best = None
        best_gain = 0
        for passage in remaining:
            gain = len({i for i, fact in enumerate(claim.facts)
                        if i in uncovered and covers(passage.text, fact)})
            if gain > best_gain:
                best_gain = gain
                best = passage
        if best is None or best_gain == 0:
            return None
        chosen.append(best.id)
        covered = {i for i, fact in enumerate(claim.facts)
                   if covers(best.text, fact)}
        uncovered -= covered
        remaining.remove(best)
    return chosen


def exact_minimal_set(claim: Claim, passages: list) -> list | None:
    """Exact minimum sufficient set by brute force over subsets.

    Returns passage ids of one minimum set (first in deterministic order),
    or None when the claim is unsupported or the set is too large to brute
    force (n > MAX_EXACT).
    """
    if len(passages) > MAX_EXACT or not is_supported(claim, passages):
        return None
    for size in range(0, len(passages) + 1):
        for subset in combinations(passages, size):
            if is_supported(claim, list(subset)):
                return [p.id for p in subset]
    return None


def all_minimal_sets(claim: Claim, passages: list) -> list:
    """Every minimal sufficient set (brute force, n <= MAX_EXACT)."""
    exact = exact_minimal_set(claim, passages)
    if exact is None:
        return []
    size = len(exact)
    out = []
    for subset in combinations(passages, size):
        if is_supported(claim, list(subset)):
            out.append([p.id for p in subset])
    return out


def collapse_depth(claim: Claim, passages: list) -> int:
    """Smallest k such that removing some k cited passages breaks support.

    0 when the claim is already unsupported. For a supported claim this is
    at most len(passages) (removing everything breaks support unless the
    claim has no facts, in which case it is vacuously supported and the
    depth is len(passages) + 1 by convention: nothing can break it).
    """
    if not claim.facts:
        return len(passages) + 1
    if not is_supported(claim, passages):
        return 0
    for k in range(1, len(passages) + 1):
        for subset in combinations(passages, k):
            rest = [p for p in passages if p not in subset]
            if not is_supported(claim, rest):
                return k
    return len(passages) + 1


def critical_citations(claim: Claim, passages: list) -> list:
    """Passage ids present in every minimal sufficient set."""
    sets = all_minimal_sets(claim, passages)
    if not sets:
        return []
    common = set(sets[0])
    for subset in sets[1:]:
        common &= set(subset)
    order = [p.id for p in passages]
    return [pid for pid in order if pid in common]
