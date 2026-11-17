"""Run the demo answer through the verifier and print the report."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from citation_ablation.ablate import ablation_curve, verify_answer  # noqa: E402
from citation_ablation.evaluate import load_answer  # noqa: E402
from citation_ablation.report import render_answer_report  # noqa: E402

HERE = Path(__file__).resolve().parent


def main() -> None:
    import json

    with open(HERE / "demo_answer.json", encoding="utf-8") as handle:
        answer = load_answer(json.load(handle))
    report = verify_answer(answer)
    print(render_answer_report(answer, report))
    print("## Ablation curve (claim c1)")
    for removed, supported in ablation_curve(answer, "c1"):
        print("  removed %-4s -> %s" % (removed or "-", "supported"
                                        if supported else "COLLAPSED"))


if __name__ == "__main__":
    main()
