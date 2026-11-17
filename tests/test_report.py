"""Tests for Markdown report rendering."""

from citation_ablation.ablate import verify_answer
from citation_ablation.cli import demo_answer
from citation_ablation.report import (render_answer_report,
                                      render_evaluation_summary)


def test_render_answer_report_contains_verdicts_and_sets():
    answer = demo_answer()
    report = verify_answer(answer)
    text = render_answer_report(answer, report)
    assert "# Citation-Ablation Report: demo" in text
    assert "LOAD-BEARING" in text
    assert "DECORATIVE" in text
    assert "CONTRADICTING" in text
    assert "Minimal sufficient set: p1" in text
    assert "Collapse depth: 2" in text


def test_render_evaluation_summary_sections():
    results = {
        "n_cases": 60, "n_citations": 161, "verdict_accuracy": 1.0,
        "naive_baseline_accuracy": 0.658,
        "minimal_size_accuracy": 1.0, "greedy_equals_exact": 1.0,
        "collapse_depth_accuracy": 1.0, "support_accuracy": 1.0,
        "decorative_separation": 0.333,
        "per_verdict": {
            label: {"precision": 1.0, "recall": 1.0, "f1": 1.0, "support": 10}
            for label in ("load_bearing", "redundant", "decorative",
                          "contradicting")},
        "per_scenario": {"clean": {"verdict_accuracy": 1.0, "cases": 8}},
        "decorative_rate_by_scenario": {"clean": 0.0, "padded": 0.333},
    }
    text = render_evaluation_summary(results)
    assert "Verdict accuracy: 1.000" in text
    assert "Per-scenario verdict accuracy" in text
    assert "clean: 1.000" in text
