"""Tests for the evaluation harness and baselines."""

from pathlib import Path

from citation_ablation.evaluate import evaluate, greedy_stress, load_cases

ROOT = Path(__file__).resolve().parent.parent


def test_hand_cases_score_perfect():
    """The 12 hand-reasoned cases are the independent check: labels were
    reasoned by hand, not generated, so a perfect score here means the
    verifier's rules match human reasoning on edge cases."""
    cases = load_cases(ROOT / "data" / "hand_cases.json")
    results = evaluate(cases)
    assert results["n_cases"] == 12
    assert results["verdict_accuracy"] == 1.0
    assert results["collapse_depth_accuracy"] == 1.0
    assert results["support_accuracy"] == 1.0
    assert results["minimal_size_accuracy"] == 1.0


def test_full_evaluation_beats_naive_baseline():
    cases = load_cases(ROOT / "data" / "cases.json")
    cases += load_cases(ROOT / "data" / "hand_cases.json")
    results = evaluate(cases)
    assert results["n_cases"] == 60
    assert results["verdict_accuracy"] == 1.0
    assert results["naive_baseline_accuracy"] < 0.8
    # The ablation view separates padded from clean answers; a
    # claim-faithfulness-only (RAGAS-style) baseline cannot.
    assert results["decorative_separation"] > 0.2


def test_greedy_stress_is_deterministic_and_honest():
    first = greedy_stress()
    second = greedy_stress()
    assert first == second
    assert first["instances"] > 100
    # Greedy is not always optimal: the rate must be below 1.0, proving
    # the stress test actually discriminates.
    assert first["greedy_equals_exact_rate"] < 1.0
    assert first["mean_greedy_size"] >= first["mean_exact_size"]


def test_per_verdict_metrics_cover_all_classes():
    cases = load_cases(ROOT / "data" / "cases.json")
    results = evaluate(cases)
    for label in ("load_bearing", "redundant", "decorative",
                  "contradicting"):
        assert results["per_verdict"][label]["support"] > 0


def test_confusion_matrix_counts_match_citations():
    cases = load_cases(ROOT / "data" / "cases.json")
    cases += load_cases(ROOT / "data" / "hand_cases.json")
    results = evaluate(cases)
    total = sum(results["confusion"].values())
    assert total == results["n_citations"] == 161
    # Perfect scores mean the confusion matrix is diagonal.
    for (truth, predicted), count in results["confusion"].items():
        assert truth == predicted


def test_per_scenario_keys_cover_all_scenarios():
    cases = load_cases(ROOT / "data" / "cases.json")
    results = evaluate(cases)
    assert set(results["per_scenario"]) == {
        "clean", "padded", "redundant", "contradicting", "unsupported",
        "multi-hop"}
    for scenario, values in results["per_scenario"].items():
        assert values["verdict_accuracy"] == 1.0


def test_decorative_rate_zero_on_clean_cases():
    cases = load_cases(ROOT / "data" / "cases.json")
    results = evaluate(cases)
    assert results["decorative_rate_by_scenario"]["clean"] == 0.0
    assert results["decorative_rate_by_scenario"]["padded"] > 0.0
