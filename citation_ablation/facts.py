"""Deterministic lexical fact handling.

Everything here is stdlib-only and text-only: no models, no embeddings.
A fact is "covered" by a passage when its surface appears in the passage
text (numbers by numeric equality, entities and terms by normalized
containment). This is deliberately shallow and fully auditable — the tool
checks what is written, not what a model thinks is meant.
"""

from __future__ import annotations

import re

from .models import Fact

_NUMBER_RE = re.compile(r"\d+(?:,\d{3})*(?:\.\d+)?")
_CAPITALIZED_RE = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b")

STOPWORDS = frozenset(
    "a an the of to in on for and or is are was were be been it its this that "
    "with by from as at which who whom when where how what why not no yes "
    "do does did have has had will would can could should may might must "
    "i you he she we they them his her their our your my me him us "
    "there here then than so such if but about into over under after "
    "before between through during per each other more most some any all "
    "also only just very really".split()
)


def normalize(text: str) -> str:
    """Lowercase, drop punctuation (keeping decimal points), collapse space."""
    lowered = text.lower()
    lowered = re.sub(r"[^\w\s.]", " ", lowered)
    lowered = re.sub(r"\s+", " ", lowered).strip()
    return lowered


def extract_numbers(text: str) -> list:
    """Numeric tokens of a text as floats, in order of appearance."""
    out = []
    for match in _NUMBER_RE.finditer(text.replace(",", "")):
        try:
            out.append(float(match.group(0)))
        except ValueError:
            continue
    return out


def _number_equal(a: float, b: float) -> bool:
    return abs(a - b) < 1e-9


def extract_facts(text: str) -> list:
    """Best-effort fact extraction from free text.

    Numbers become number facts (key ""), capitalised multi-word spans
    become entity facts, and remaining content words become term facts.
    Case data carries explicit facts; this is only the free-text path used
    by the CLI demo, so it is allowed to be approximate.
    """
    facts: list = []
    seen: set = set()
    for match in _NUMBER_RE.finditer(text):
        surface = match.group(0)
        if surface in seen:
            continue
        seen.add(surface)
        facts.append(Fact(kind="number", key="", value=surface, surface=surface))
    for match in _CAPITALIZED_RE.finditer(text):
        surface = match.group(0)
        if surface in seen:
            continue
        seen.add(surface)
        facts.append(Fact(kind="entity", key="", value=surface, surface=surface))
    for word in re.findall(r"[A-Za-z]{4,}", text):
        lowered = word.lower()
        if lowered in STOPWORDS or lowered in seen:
            continue
        seen.add(lowered)
        facts.append(Fact(kind="term", key="", value=lowered, surface=lowered))
    return facts
