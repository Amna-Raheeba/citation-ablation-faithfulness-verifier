"""Citation-Ablation Faithfulness Verifier.

Verifies that an answer's citations are actually load-bearing: ablate each
cited passage and re-check whether the answer still stands.
"""

from .ablate import ablation_curve, verify_answer, verify_claim
from .minimal import (collapse_depth, critical_citations, exact_minimal_set,
                      greedy_minimal_set)
from .models import CitedAnswer, Claim, Fact, Passage

__all__ = [
    "CitedAnswer", "Claim", "Fact", "Passage",
    "verify_answer", "verify_claim", "ablation_curve",
    "greedy_minimal_set", "exact_minimal_set", "collapse_depth",
    "critical_citations",
]
__version__ = "0.1.0"
