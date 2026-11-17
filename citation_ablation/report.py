"""Markdown rendering of verification reports."""

from __future__ import annotations

from .models import AnswerReport, CitedAnswer

_VERDICT_LABEL = {
    "load_bearing": "LOAD-BEARING",
    "redundant": "redundant",
    "decorative": "DECORATIVE",
    "contradicting": "CONTRADICTING",
}


def render_answer_report(answer: CitedAnswer, report: AnswerReport) -> str:
    """Render a full answer verification report as Markdown."""
    lines = []
    lines.append("# Citation-Ablation Report: %s" % answer.id)
    lines.append("")
    lines.append("Question: %s" % answer.question)
    lines.append("")
    lines.append("Faithfulness (supported claims): %.3f" % report.faithfulness)
    lines.append("Citation precision (load-bearing share): %.3f"
                 % report.citation_precision)
    lines.append("Decorative rate: %.3f" % report.decorative_rate)
    lines.append("Efficiency (|minimal| / |cited|): %.3f" % report.efficiency)
    lines.append("Mean collapse depth: %.2f" % report.mean_collapse_depth)
    lines.append("Ablation robustness: %.3f" % report.ablation_robustness)
    lines.append("")
    for claim in answer.claims:
        claim_report = report.claims[claim.id]
        lines.append("## Claim %s — %s"
                     % (claim.id,
                        "supported" if claim_report.supported
                        else "UNSUPPORTED"))
        lines.append("")
        lines.append("> %s" % claim.text)
        lines.append("")
        lines.append("Minimal sufficient set: %s"
                     % (", ".join(claim_report.minimal_set)
                        if claim_report.minimal_set else "none"))
        lines.append("Collapse depth: %s" % claim_report.collapse_depth)
        lines.append("Critical citations: %s"
                     % (", ".join(claim_report.critical_citations)
                        if claim_report.critical_citations else "none"))
        lines.append("")
        for passage in answer.passages_for(claim.id):
            verdict = claim_report.verdicts.get(passage.id, "?")
            lines.append("- [%s] %s: %s"
                         % (passage.id, _VERDICT_LABEL.get(verdict, verdict),
                            passage.text))
        lines.append("")
    return "\n".join(lines)


def render_evaluation_summary(results: dict) -> str:
    """Render evaluation results as Markdown."""
    from .evaluate import summarize

    lines = ["# Evaluation Summary", ""]
    lines.append(summarize(results))
    lines.append("")
    lines.append("## Per-scenario verdict accuracy")
    lines.append("")
    for scenario, values in results["per_scenario"].items():
        lines.append("- %s: %.3f (%d cases)"
                     % (scenario, values["verdict_accuracy"],
                        values["cases"]))
    lines.append("")
    lines.append("## Decorative rate by scenario")
    lines.append("")
    for scenario, rate in results["decorative_rate_by_scenario"].items():
        lines.append("- %s: %.3f" % (scenario, rate))
    return "\n".join(lines)
