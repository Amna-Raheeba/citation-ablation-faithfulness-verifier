"""Regenerate every number in results/ from the seeded case set.

Loads data/cases.json (48 generated cases) and data/hand_cases.json (12
hand-reasoned cases), runs the evaluation, and writes results/.

Headline-drift guard: if results/evaluation.json already exists in the
output directory, the new headline metrics must match it exactly (to
1e-9). A mismatch fails loudly — numbers in results/ must never drift
from the code silently. To change a headline number deliberately, delete
the old results/ first and re-run.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from citation_ablation.evaluate import evaluate, load_cases, summarize  # noqa: E402
from citation_ablation.report import render_evaluation_summary  # noqa: E402

HEADLINE_KEYS = ["verdict_accuracy", "minimal_size_accuracy",
                 "greedy_equals_exact", "collapse_depth_accuracy",
                 "support_accuracy", "naive_baseline_accuracy",
                 "decorative_separation"]


def run(out_dir: Path) -> dict:
    """Run the evaluation and write all result files. Returns results."""
    cases = load_cases(ROOT / "data" / "cases.json")
    cases += load_cases(ROOT / "data" / "hand_cases.json")
    results = evaluate(cases)
    serializable = {k: v for k, v in results.items() if k != "confusion"}
    serializable["confusion"] = [
        {"truth": t, "predicted": p, "count": c}
        for (t, p), c in sorted(results["confusion"].items())
    ]
    existing = out_dir / "evaluation.json"
    if existing.exists():
        previous = json.loads(existing.read_text(encoding="utf-8"))
        drift = [key for key in HEADLINE_KEYS
                 if abs(previous.get(key, 0.0) - results[key]) > 1e-9]
        if drift:
            raise SystemExit(
                "HEADLINE DRIFT in %s: %s\n"
                "Delete %s and re-run to accept new numbers deliberately."
                % (existing, ", ".join(drift), existing))
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "evaluation.json").write_text(
        json.dumps(serializable, indent=2, sort_keys=True), encoding="utf-8")
    rows = ["verdict,precision,recall,f1,support"]
    for label, m in results["per_verdict"].items():
        rows.append("%s,%.4f,%.4f,%.4f,%d"
                    % (label, m["precision"], m["recall"], m["f1"],
                       m["support"]))
    (out_dir / "evaluation.csv").write_text("\n".join(rows) + "\n",
                                            encoding="utf-8")
    (out_dir / "evaluation_summary.md").write_text(
        render_evaluation_summary(results), encoding="utf-8")
    (out_dir / "HEADLINE.md").write_text(
        "# Headline\n\n" + summarize(results) + "\n", encoding="utf-8")
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(ROOT / "results"))
    args = parser.parse_args()
    results = run(Path(args.out))
    print(summarize(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
