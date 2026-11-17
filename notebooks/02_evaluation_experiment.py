"""Notebook 02: evaluation experiment — 48 generated + 12 hand cases."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from citation_ablation.evaluate import evaluate, load_cases, summarize  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
cases = load_cases(ROOT / "data" / "cases.json")
cases += load_cases(ROOT / "data" / "hand_cases.json")
results = evaluate(cases)
print(summarize(results))
print()
print("Per-scenario verdict accuracy:")
for scenario, values in results["per_scenario"].items():
    print("  %-14s %.3f (%d cases)" % (scenario, values["verdict_accuracy"],
                                       values["cases"]))
print()
print("Confusion (truth -> predicted):")
for (truth, predicted), count in sorted(results["confusion"].items()):
    print("  %-14s -> %-14s %d" % (truth, predicted, count))
