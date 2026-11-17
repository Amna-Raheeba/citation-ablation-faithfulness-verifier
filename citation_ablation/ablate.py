"""Citation-ablation verification: is each citation load-bearing?

For every cited passage of every claim, ablate it (remove it from the
claim's evidence set) and re-check support:

1. contradicting — the passage states a keyed number differently from the
   claim (checked first: a contradicting passage may also cover facts).
2. decorative — the passage covers no fact of the claim at all; it was
   never evidence, only decoration.
3. redundant — the claim stays supported without this passage; another
   cited passage covers the same facts.
4. load-bearing — removing it breaks support (or the claim is unsupported
   overall and this passage carries part of the support — the only support
   there is, so it is load-bearing, not redundant).

The distinction between redundant and decorative is the point: a
redundant citation at least states the evidence; a decorative one never
did. No other offline verifier in the prior-art check makes it.
"""

from __future__ import annotations

from .minimal import (collapse_depth, critical_citations, exact_minimal_set,
                      greedy_minimal_set)
from .models import (AnswerReport, ClaimReport, CitedAnswer, CONTRADICTING,
                     DECORATIVE, LOAD_BEARING, REDUNDANT)
from .support import (claim_coverage, is_supported, passage_contradicts,
                      passage_covers)


def verify_claim(answer: CitedAnswer, claim_id: str) -> ClaimReport:
    """Verify one claim of an answer against its cited passages."""
    claim = next(c for c in answer.claims if c.id == claim_id)
    cited = answer.passages_for(claim_id)
    supported = is_supported(claim, cited)
    covered = claim_coverage(claim, cited)
    uncovered = tuple(i for i in range(len(claim.facts)) if i not in covered)
    verdicts = {}
    for passage in cited:
        if passage_contradicts(passage.text, claim):
            verdicts[passage.id] = CONTRADICTING
            continue
        covered_by_this = passage_covers(passage.text, claim)
        if not covered_by_this:
            verdicts[passage.id] = DECORATIVE
            continue
        if supported:
            rest = [p for p in cited if p.id != passage.id]
            if is_supported(claim, rest):
                verdicts[passage.id] = REDUNDANT
            else:
                verdicts[passage.id] = LOAD_BEARING
        else:
            # Claim unsupported overall: a passage covering facts carries
            # part of the only support there is.
            verdicts[passage.id] = LOAD_BEARING
    greedy = greedy_minimal_set(claim, cited)
    exact = exact_minimal_set(claim, cited)
    return ClaimReport(
        claim_id=claim_id,
        supported=supported,
        verdicts=verdicts,
        covered_facts=tuple(sorted(covered)),
        uncovered_facts=uncovered,
        minimal_set=tuple(greedy) if greedy else (),
        exact_minimal_size=len(exact) if exact is not None else None,
        collapse_depth=collapse_depth(claim, cited),
        critical_citations=tuple(critical_citations(claim, cited)),
    )


def ablation_curve(answer: CitedAnswer, claim_id: str) -> list:
    """Ordered-removal curve: remove citations decorative-first, then
    redundant, then load-bearing, and record support after each step.

    Returns a list of (removed_passage_id_or_None, supported) starting
    with no removal. The curve shows how many citations can be dropped
    before the answer collapses — the honest picture of citation padding.
    """
    claim = next(c for c in answer.claims if c.id == claim_id)
    cited = answer.passages_for(claim_id)
    report = verify_claim(answer, claim_id)
    order_rank = {DECORATIVE: 0, REDUNDANT: 1, CONTRADICTING: 2,
                  LOAD_BEARING: 3}
    ordered = sorted(cited, key=lambda p: (order_rank[report.verdicts[p.id]],
                                           cited.index(p)))
    curve = [(None, is_supported(claim, cited))]
    remaining = list(cited)
    for passage in ordered:
        remaining = [p for p in remaining if p.id != passage.id]
        curve.append((passage.id, is_supported(claim, remaining)))
    return curve


def verify_answer(answer: CitedAnswer) -> AnswerReport:
    """Verify every claim of an answer and aggregate answer-level scores."""
    reports = {c.id: verify_claim(answer, c.id) for c in answer.claims}
    total_claims = len(answer.claims)
    supported_claims = sum(1 for r in reports.values() if r.supported)
    faithfulness = supported_claims / total_claims if total_claims else 0.0
    total_citations = sum(len(r.verdicts) for r in reports.values())
    load_bearing = sum(1 for r in reports.values()
                       for v in r.verdicts.values() if v == LOAD_BEARING)
    decorative = sum(1 for r in reports.values()
                     for v in r.verdicts.values() if v == DECORATIVE)
    citation_precision = (load_bearing / total_citations
                          if total_citations else 0.0)
    decorative_rate = (decorative / total_citations
                       if total_citations else 0.0)
    efficiencies = []
    depths = []
    for claim in answer.claims:
        report = reports[claim.id]
        cited_n = len(answer.citations.get(claim.id, []))
        if report.supported and cited_n:
            efficiencies.append(len(report.minimal_set) / cited_n)
        if report.collapse_depth is not None:
            depths.append(report.collapse_depth)
    efficiency = sum(efficiencies) / len(efficiencies) if efficiencies else 0.0
    mean_depth = sum(depths) / len(depths) if depths else 0.0
    # Ablation robustness: fraction of single-citation removals (over
    # supported claims) after which the claim stays supported.
    survived = 0
    tried = 0
    for claim in answer.claims:
        report = reports[claim.id]
        if not report.supported:
            continue
        cited = answer.passages_for(claim.id)
        for passage in cited:
            tried += 1
            rest = [p for p in cited if p.id != passage.id]
            if is_supported(claim, rest):
                survived += 1
    robustness = survived / tried if tried else 0.0
    return AnswerReport(
        answer_id=answer.id,
        claims=reports,
        faithfulness=faithfulness,
        citation_precision=citation_precision,
        decorative_rate=decorative_rate,
        efficiency=efficiency,
        mean_collapse_depth=mean_depth,
        ablation_robustness=robustness,
    )
