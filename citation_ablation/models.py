"""Data models for citation-ablation faithfulness verification.

An answer is a list of claims. Each claim carries explicit facts (numbers,
named entities, terms). Evidence is a list of passages. Citations link claims
to passages. The verifier never sees ground truth: it works from text alone.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Fact:
    """One atomic checkable unit of a claim.

    kind: "number" | "entity" | "term".
    key: attribute label for numbers (e.g. "dose"), "" otherwise. Two number
    facts with the same key and different values contradict each other.
    value: canonical value, e.g. "200" or "Metformin".
    surface: text that must appear in a passage for the fact to count as
    covered, e.g. "200 mg" or "twice daily".
    """

    kind: str
    key: str
    value: str
    surface: str


@dataclass(frozen=True)
class Passage:
    """One evidence passage."""

    id: str
    text: str


@dataclass(frozen=True)
class Claim:
    """One claim of an answer, with its checkable facts."""

    id: str
    text: str
    facts: tuple = ()


@dataclass(frozen=True)
class CitedAnswer:
    """An answer with citations: claim_id -> passage ids."""

    id: str
    question: str
    claims: tuple = ()
    passages: tuple = ()
    citations: dict = field(default_factory=dict)

    def passages_for(self, claim_id: str) -> list:
        """Passages cited for a claim, in citation order."""
        by_id = {p.id: p for p in self.passages}
        return [by_id[pid] for pid in self.citations.get(claim_id, [])
                if pid in by_id]


# Verdicts, in the order the verifier checks them.
LOAD_BEARING = "load_bearing"
REDUNDANT = "redundant"
DECORATIVE = "decorative"
CONTRADICTING = "contradicting"
VERDICTS = (LOAD_BEARING, REDUNDANT, DECORATIVE, CONTRADICTING)


@dataclass
class ClaimReport:
    """Per-claim verification result."""

    claim_id: str
    supported: bool
    verdicts: dict = field(default_factory=dict)  # passage_id -> verdict
    covered_facts: tuple = ()
    uncovered_facts: tuple = ()
    minimal_set: tuple = ()       # passage ids, greedy minimal sufficient set
    exact_minimal_size: int | None = None
    collapse_depth: int | None = None
    critical_citations: tuple = ()


@dataclass
class AnswerReport:
    """Per-answer verification result."""

    answer_id: str
    claims: dict = field(default_factory=dict)  # claim_id -> ClaimReport
    faithfulness: float = 0.0        # supported claims / total claims
    citation_precision: float = 0.0  # load-bearing citations / all citations
    decorative_rate: float = 0.0     # decorative citations / all citations
    efficiency: float = 0.0          # mean |minimal set| / |cited|, supported claims
    mean_collapse_depth: float = 0.0
    ablation_robustness: float = 0.0  # single removals the answer survives
