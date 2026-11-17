"""Tests for the citation-ablation verifier."""

from citation_ablation.ablate import (ablation_curve, verify_answer,
                                      verify_claim)
from citation_ablation.models import CitedAnswer, Claim, Fact, Passage

DOSE = Fact("number", "dose", "200", "200 mg")
TERM = Fact("term", "", "twice daily", "twice daily")


def _answer(citations, passages, claims=None):
    if claims is None:
        claims = (Claim("c1", "The dose is 200 mg twice daily.",
                        facts=(DOSE, TERM)),)
    return CitedAnswer(id="t", question="?", claims=claims,
                       passages=tuple(passages), citations=citations)


def test_load_bearing_single_support():
    answer = _answer({"c1": ["p1"]},
                     [Passage("p1", "The dose is 200 mg twice daily.")])
    report = verify_claim(answer, "c1")
    assert report.supported
    assert report.verdicts == {"p1": "load_bearing"}
    assert report.minimal_set == ("p1",)
    assert report.collapse_depth == 1
    assert report.critical_citations == ("p1",)


def test_duplicate_copies_are_both_redundant():
    text = "The dose is 200 mg twice daily."
    answer = _answer({"c1": ["p1", "p2"]},
                     [Passage("p1", text), Passage("p2", text)])
    report = verify_claim(answer, "c1")
    assert report.verdicts == {"p1": "redundant", "p2": "redundant"}
    assert report.minimal_set == ("p1",)
    assert report.collapse_depth == 2
    assert report.critical_citations == ()


def test_decorative_covers_nothing():
    answer = _answer(
        {"c1": ["p1", "p2"]},
        [Passage("p1", "The dose is 200 mg twice daily."),
         Passage("p2", "Atorvastatin lowers cholesterol.")])
    report = verify_claim(answer, "c1")
    assert report.verdicts == {"p1": "load_bearing", "p2": "decorative"}


def test_contradicting_beats_covering():
    # p2 contradicts the number but covers the term: contradiction wins.
    answer = _answer(
        {"c1": ["p1", "p2"]},
        [Passage("p1", "The dose is 200 mg twice daily."),
         Passage("p2", "The dose is 400 mg twice daily.")])
    report = verify_claim(answer, "c1")
    assert report.verdicts == {"p1": "load_bearing",
                               "p2": "contradicting"}


def test_unsupported_claim_partial_support_is_load_bearing():
    answer = _answer({"c1": ["p1", "p2"]},
                     [Passage("p1", "Take it twice daily."),
                      Passage("p2", "Unrelated background.")])
    report = verify_claim(answer, "c1")
    assert not report.supported
    assert report.verdicts == {"p1": "load_bearing", "p2": "decorative"}
    assert report.minimal_set == ()
    assert report.collapse_depth == 0


def test_no_citations_unsupported():
    answer = _answer({"c1": []}, [Passage("p1", "The dose is 200 mg.")])
    report = verify_claim(answer, "c1")
    assert not report.supported
    assert report.verdicts == {}
    assert report.collapse_depth == 0


def test_multi_hop_minimal_set_size_two():
    answer = _answer(
        {"c1": ["p1", "p2"]},
        [Passage("p1", "The dose is 200 mg."),
         Passage("p2", "Take it twice daily.")])
    report = verify_claim(answer, "c1")
    assert report.supported
    assert report.minimal_set == ("p1", "p2")
    assert report.exact_minimal_size == 2
    assert report.collapse_depth == 1
    assert report.critical_citations == ("p1", "p2")


def test_ablation_curve_removes_decorative_first():
    answer = _answer(
        {"c1": ["p1", "p2", "p3"]},
        [Passage("p1", "The dose is 200 mg twice daily."),
         Passage("p2", "Unrelated background."),
         Passage("p3", "The dose is 200 mg twice daily.")])
    curve = ablation_curve(answer, "c1")
    # Step 0: nothing removed, supported. Step 1: decorative p2 removed.
    assert curve[0] == (None, True)
    assert curve[1][0] == "p2" and curve[1][1] is True
    # Last step: both supporting copies gone -> collapsed.
    assert curve[-1][1] is False


def test_answer_level_scores():
    claims = (
        Claim("c1", "The dose is 200 mg twice daily.", facts=(DOSE, TERM)),
        Claim("c2", "Metformin is taken after meals.",
              facts=(Fact("term", "", "after meals", "after meals"),)),
    )
    answer = CitedAnswer(
        id="t", question="?",
        claims=claims,
        passages=(Passage("p1", "The dose is 200 mg twice daily, taken after meals."),
                  Passage("p2", "Unrelated background.")),
        citations={"c1": ["p1", "p2"], "c2": ["p1"]})
    report = verify_answer(answer)
    assert report.faithfulness == 1.0
    # 3 citations total; p1 load-bearing twice, p2 decorative once.
    assert report.citation_precision == 2 / 3
    assert report.decorative_rate == 1 / 3
    assert report.efficiency == 0.75  # c1: 1/2, c2: 1/1
    assert report.ablation_robustness == 1 / 3  # only removing p2 survives


def test_answer_with_no_supported_claims_scores_zero():
    answer = _answer({"c1": ["p1"]},
                     [Passage("p1", "Unrelated background.")])
    report = verify_answer(answer)
    assert report.faithfulness == 0.0
    assert report.citation_precision == 0.0
    assert report.decorative_rate == 1.0
    assert report.efficiency == 0.0
    assert report.ablation_robustness == 0.0


def test_ablation_curve_on_multi_hop():
    answer = _answer(
        {"c1": ["p1", "p2"]},
        [Passage("p1", "The dose is 200 mg."),
         Passage("p2", "Take it twice daily.")])
    curve = ablation_curve(answer, "c1")
    assert curve[0] == (None, True)
    # Both citations are load-bearing; the first removal collapses it.
    assert curve[1][1] is False
    assert curve[2][1] is False


def test_contradicting_passage_inside_minimal_set():
    # p2 contradicts the number but is the only cover of the term:
    # the claim needs it, and the verdict is still contradicting.
    answer = _answer(
        {"c1": ["p1", "p2"]},
        [Passage("p1", "The dose is 200 mg."),
         Passage("p2", "The dose is 400 mg twice daily.")])
    report = verify_claim(answer, "c1")
    assert report.supported
    assert report.verdicts == {"p1": "load_bearing",
                               "p2": "contradicting"}
    assert report.minimal_set == ("p1", "p2")
    assert report.collapse_depth == 1


def test_mean_collapse_depth_and_robustness():
    claims = (
        Claim("c1", "The dose is 200 mg twice daily.", facts=(DOSE, TERM)),
        Claim("c2", "Other claim.", facts=()),
    )
    answer = CitedAnswer(
        id="t", question="?",
        claims=claims,
        passages=(Passage("p1", "The dose is 200 mg twice daily."),),
        citations={"c1": ["p1"], "c2": ["p1"]})
    report = verify_answer(answer)
    # c1 depth 1, c2 (zero facts) depth 2 -> mean 1.5.
    assert report.mean_collapse_depth == 1.5
