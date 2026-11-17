"""Evaluation over the seeded case set.

Ground truth comes from construction (scripts/build_cases.py): each case
records the intended verdict of every citation, the intended minimal-set
size and collapse depth per claim, and whether each claim is supported.
The verifier never sees ground truth; it works from text alone.

Baselines for comparison:
- naive: every citation is load-bearing (the implicit assumption of any
  tool that only checks citations exist).
- ragas-style: answer-level claim faithfulness only (supported claims /
  total claims) with no per-citation verdicts, so it detects zero
  decorative citations by construction.
"""

from __future__ import annotations

import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from .ablate import verify_answer
from .minimal import exact_minimal_set, greedy_minimal_set
from .models import (CitedAnswer, Claim, Fact, Passage, VERDICTS,
                     LOAD_BEARING)


def greedy_stress(n_instances: int = 200, seed: int = 7) -> dict:
    """Greedy vs exact minimal sets on random set-cover instances.

    Seeded, deterministic. Greedy set cover is not optimal in general, so
    this measures how often it matches the exact minimum on small random
    instances — the honest statement about the greedy algorithm, separate
    from the structured benchmark cases (where it is exact).
    """
    rng = random.Random(seed)
    equal = 0
    checked = 0
    greedy_total = 0
    exact_total = 0
    for _ in range(n_instances):
        k = rng.randint(4, 8)
        facts = tuple(Fact("term", "", "f%d" % i, "f%d" % i)
                      for i in range(k))
        claim = Claim("c", " ".join("f%d" % i for i in range(k)), facts=facts)
        n_passages = rng.randint(3, 6)
        passages = []
        for j in range(n_passages):
            covered = [i for i in range(k) if rng.random() < 0.5]
            text = " ".join("f%d" % i for i in covered) or "nothing here"
            passages.append(Passage("p%d" % j, text))
        if not all(any("f%d" % i in p.text.split() for p in passages)
                   for i in range(k)):
            continue
        greedy = greedy_minimal_set(claim, passages)
        exact = exact_minimal_set(claim, passages)
        if greedy is None or exact is None:
            continue
        checked += 1
        greedy_total += len(greedy)
        exact_total += len(exact)
        if len(greedy) == len(exact):
            equal += 1
    return {
        "instances": checked,
        "greedy_equals_exact_rate": equal / checked if checked else 0.0,
        "mean_greedy_size": greedy_total / checked if checked else 0.0,
        "mean_exact_size": exact_total / checked if checked else 0.0,
    }


def load_answer(data: dict) -> CitedAnswer:
    """Build a CitedAnswer from one case dict."""
    claims = tuple(
        Claim(id=c["id"], text=c["text"],
              facts=tuple(Fact(**f) for f in c.get("facts", [])))
        for c in data["claims"]
    )
    passages = tuple(Passage(**p) for p in data["passages"])
    return CitedAnswer(id=data["id"], question=data["question"],
                       claims=claims, passages=passages,
                       citations=data["citations"])


def load_cases(path: str | Path) -> list:
    """Load the case file (a JSON list of case dicts)."""
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _prf(predicted: list, truth: list, label: str) -> dict:
    tp = sum(1 for p, t in zip(predicted, truth) if p == label and t == label)
    fp = sum(1 for p, t in zip(predicted, truth) if p == label and t != label)
    fn = sum(1 for p, t in zip(predicted, truth) if p != label and t == label)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (2 * precision * recall / (precision + recall)
          if precision + recall else 0.0)
    return {"precision": precision, "recall": recall, "f1": f1,
            "support": tp + fn}


def evaluate(cases: list) -> dict:
    """Run the verifier over all cases and score it against ground truth."""
    predicted, truth = [], []
    minimal_exact = 0
    minimal_checked = 0
    greedy_exact = 0
    depth_exact = 0
    depth_checked = 0
    support_correct = 0
    support_checked = 0
    naive_correct = 0
    naive_total = 0
    per_scenario: dict = defaultdict(lambda: {"cases": 0, "correct": 0,
                                              "total": 0})
    decorative_by_scenario: dict = defaultdict(list)
    for case in cases:
        answer = load_answer(case)
        report = verify_answer(answer)
        scenario = case.get("scenario", "unknown")
        for claim in answer.claims:
            claim_report = report.claims[claim.id]
            labels = case.get("labels", {}).get(claim.id, {})
            gt = case.get("ground_truth", {}).get(claim.id, {})
            for pid, verdict in claim_report.verdicts.items():
                predicted.append(verdict)
                truth.append(labels.get(pid, "unknown"))
                per_scenario[scenario]["total"] += 1
                if verdict == labels.get(pid):
                    per_scenario[scenario]["correct"] += 1
                naive_total += 1
                if labels.get(pid) == LOAD_BEARING:
                    naive_correct += 1
            if "minimal_size" in gt:
                minimal_checked += 1
                if len(claim_report.minimal_set) == gt["minimal_size"]:
                    minimal_exact += 1
                if (claim_report.exact_minimal_size is not None
                        and len(claim_report.minimal_set)
                        == claim_report.exact_minimal_size):
                    greedy_exact += 1
            if "collapse_depth" in gt:
                depth_checked += 1
                if claim_report.collapse_depth == gt["collapse_depth"]:
                    depth_exact += 1
            if "supported" in gt:
                support_checked += 1
                if claim_report.supported == gt["supported"]:
                    support_correct += 1
            per_scenario[scenario]["cases"] += 1
        # Decorative separation: verifier's decorative rate per scenario.
        total_cites = sum(len(r.verdicts) for r in report.claims.values())
        dec = sum(1 for r in report.claims.values()
                  for v in r.verdicts.values() if v == "decorative")
        decorative_by_scenario[scenario].append(
            dec / total_cites if total_cites else 0.0)
    per_verdict = {label: _prf(predicted, truth, label) for label in VERDICTS}
    accuracy = (sum(1 for p, t in zip(predicted, truth) if p == t)
                / len(truth) if truth else 0.0)
    sep = {}
    for scenario, rates in decorative_by_scenario.items():
        sep[scenario] = sum(rates) / len(rates) if rates else 0.0
    separation = sep.get("padded", 0.0) - sep.get("clean", 0.0)
    stress = greedy_stress()
    return {
        "n_cases": len(cases),
        "n_citations": len(truth),
        "verdict_accuracy": accuracy,
        "per_verdict": per_verdict,
        "minimal_size_accuracy": (minimal_exact / minimal_checked
                                  if minimal_checked else 0.0),
        "greedy_equals_exact": (greedy_exact / minimal_checked
                                if minimal_checked else 0.0),
        "greedy_stress": stress,
        "collapse_depth_accuracy": (depth_exact / depth_checked
                                    if depth_checked else 0.0),
        "support_accuracy": (support_correct / support_checked
                             if support_checked else 0.0),
        "naive_baseline_accuracy": (naive_correct / naive_total
                                    if naive_total else 0.0),
        "decorative_separation": separation,
        "decorative_rate_by_scenario": sep,
        "per_scenario": {k: {"cases": v["cases"],
                             "verdict_accuracy": (v["correct"] / v["total"]
                                                  if v["total"] else 0.0)}
                         for k, v in sorted(per_scenario.items())},
        "confusion": Counter(zip(truth, predicted)),
    }


def summarize(results: dict) -> str:
    """One-paragraph human summary of evaluation results."""
    lines = []
    lines.append("Cases: %d, citations scored: %d"
                 % (results["n_cases"], results["n_citations"]))
    lines.append("Verdict accuracy: %.3f (naive all-load-bearing baseline: %.3f)"
                 % (results["verdict_accuracy"],
                    results["naive_baseline_accuracy"]))
    for label in VERDICTS:
        m = results["per_verdict"][label]
        lines.append("  %s: P=%.3f R=%.3f F1=%.3f (n=%d)"
                     % (label, m["precision"], m["recall"], m["f1"],
                        m["support"]))
    lines.append("Minimal-set size accuracy: %.3f; greedy == exact: %.3f"
                 % (results["minimal_size_accuracy"],
                    results["greedy_equals_exact"]))
    stress = results.get("greedy_stress", {})
    if stress:
        lines.append("Greedy stress (%d random instances): greedy == exact "
                     "on %.3f; mean greedy %.2f vs exact %.2f"
                     % (stress["instances"],
                        stress["greedy_equals_exact_rate"],
                        stress["mean_greedy_size"], stress["mean_exact_size"]))
    lines.append("Collapse-depth accuracy: %.3f; claim-support accuracy: %.3f"
                 % (results["collapse_depth_accuracy"],
                    results["support_accuracy"]))
    lines.append("Decorative separation (padded minus clean): %.3f "
                 "(RAGAS-style baseline: 0.000 by construction)"
                 % results["decorative_separation"])
    return "\n".join(lines)
