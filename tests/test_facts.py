"""Tests for deterministic lexical fact handling."""

from citation_ablation.facts import (extract_facts, extract_numbers,
                                     normalize)


def test_normalize_lowercases_and_collapses():
    assert normalize("  Hello,  WORLD! ") == "hello world"


def test_normalize_keeps_decimal_points():
    assert normalize("Dose 200.0 mg.") == "dose 200.0 mg."


def test_extract_numbers_plain_and_decimal():
    assert extract_numbers("took 200 mg and 2.5 ml") == [200.0, 2.5]


def test_extract_numbers_handles_commas():
    assert extract_numbers("1,000 participants enrolled") == [1000.0]


def test_extract_numbers_empty():
    assert extract_numbers("no numbers here") == []


def test_extract_facts_finds_numbers_entities_terms():
    facts = extract_facts("The New York dose is 200 mg twice daily.")
    kinds = {f.kind for f in facts}
    assert "number" in kinds
    assert "entity" in kinds  # "New York"
    assert "term" in kinds


def test_extract_facts_skips_stopwords():
    facts = extract_facts("The dose is 200 mg.")
    values = {f.value for f in facts}
    assert "the" not in values
    assert "is" not in values


def test_extract_facts_deduplicates():
    facts = extract_facts("200 mg and 200 mg again.")
    numbers = [f for f in facts if f.kind == "number"]
    assert len(numbers) == 1


def test_extract_facts_term_values_are_lowercase():
    facts = extract_facts("Patients reported Nausea after treatment.")
    terms = [f for f in facts if f.kind == "term"]
    assert all(f.value == f.value.lower() for f in terms)


def test_extract_numbers_ignores_year_like_context():
    assert extract_numbers("In 2024, 30 patients enrolled") == [2024.0, 30.0]


def test_normalize_strips_units_punctuation():
    assert normalize("LDL: 100 mg/dL!") == "ldl 100 mg dl"
