"""Tests for deterministic support and contradiction checks."""

from citation_ablation.models import Claim, Fact, Passage
from citation_ablation.support import (claim_coverage, contradicts, covers,
                                       is_supported)

DOSE = Fact("number", "dose", "200", "200 mg")
TERM = Fact("term", "", "twice daily", "twice daily")
DRUG = Fact("entity", "", "Metformin", "Metformin")


def test_covers_number_by_numeric_equality():
    assert covers("Dose: 200.0 mg.", DOSE)
    assert not covers("Dose: 400 mg.", DOSE)


def test_covers_number_with_comma_format():
    fact = Fact("number", "participants", "1000", "1,000 participants")
    assert covers("1000 participants enrolled.", fact)


def test_covers_entity_and_term_by_containment():
    assert covers("Metformin is widely prescribed.", DRUG)
    assert covers("Take it twice daily.", TERM)
    assert not covers("Take it once daily.", TERM)


def test_contradicts_needs_key_and_different_number():
    assert contradicts("The dose is 400 mg twice daily.", DOSE)
    assert not contradicts("Patients took 400 mg daily.", DOSE)  # no key
    assert not contradicts("The dose is 200 mg.", DOSE)  # value present
    assert not contradicts("The dose is 200 mg and 400 mg.", DOSE)


def test_contradicts_only_for_keyed_numbers():
    assert not contradicts("Not Metformin at all.", DRUG)
    assert not contradicts("Never twice daily.", TERM)


def test_claim_coverage_and_support():
    claim = Claim("c1", "Dose 200 mg twice daily.", facts=(DOSE, TERM))
    assert claim_coverage(claim, []) == set()
    assert not is_supported(claim, [])
    assert is_supported(
        claim, [Passage("p1", "The dose is 200 mg twice daily.")])
    partial = [Passage("p1", "Take it twice daily.")]
    assert claim_coverage(claim, partial) == {1}
    assert not is_supported(claim, partial)


def test_contradicts_ignores_different_number_when_value_present():
    # Both numbers present: the claim's value is stated, so no contradiction.
    assert not contradicts("The dose is 200 mg, up from 100 mg.", DOSE)


def test_covers_term_needs_full_phrase():
    assert not covers("Take it daily.", TERM)
    assert covers("Take it twice daily!", TERM)


def test_covers_number_ignores_units():
    assert covers("200 tablets were given.", DOSE)
