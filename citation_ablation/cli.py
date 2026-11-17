"""Command-line interface.

Commands:
  demo                  verify a small hand-built answer, print the report
  evaluate [--out DIR]  run the seeded evaluation, print + write results
  verify FILE [--format md|text]
                        verify one CitedAnswer JSON file
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .ablate import verify_answer
from .evaluate import evaluate, load_answer, load_cases, summarize
from .facts import extract_facts
from .models import CitedAnswer, Claim, Fact, Passage
from .report import render_answer_report, render_evaluation_summary

_HERE = Path(__file__).resolve().parent.parent
DEFAULT_CASES = _HERE / "data" / "cases.json"


def demo_answer() -> CitedAnswer:
    """A small hand-built answer showing all four verdicts."""
    passages = (
        Passage("p1", "The recommended dose of Metformin is 200 mg twice "
                      "daily, taken after meals."),
        Passage("p2", "Metformin 200 mg twice daily is the standard "
                      "starting dose for adults with type 2 diabetes."),
        Passage("p3", "Atorvastatin lowers LDL cholesterol and is often "
                      "prescribed alongside diabetes medication."),
        Passage("p4", "The dose of Metformin is 400 mg twice daily "
                      "according to the updated label."),
    )
    claims = (
        Claim("c1",
              "The recommended dose of Metformin is 200 mg twice daily.",
              facts=(Fact("number", "dose", "200", "200 mg"),
                     Fact("term", "", "twice daily", "twice daily"))),
        Claim("c2",
              "Metformin is taken after meals.",
              facts=(Fact("term", "", "after meals", "after meals"),)),
    )
    return CitedAnswer(
        id="demo",
        question="What is the recommended dose of Metformin and when is it taken?",
        claims=claims,
        passages=passages,
        citations={"c1": ["p1", "p2", "p3", "p4"], "c2": ["p1"]},
    )


def cmd_demo(_args) -> int:
    answer = demo_answer()
    report = verify_answer(answer)
    print(render_answer_report(answer, report))
    return 0


def cmd_evaluate(args) -> int:
    cases = load_cases(args.cases)
    hand = Path(args.cases).parent / "hand_cases.json"
    if hand.exists():
        cases += load_cases(hand)
    results = evaluate(cases)
    print(summarize(results))
    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        serializable = {k: v for k, v in results.items()
                        if k != "confusion"}
        serializable["confusion"] = [
            {"truth": t, "predicted": p, "count": c}
            for (t, p), c in sorted(results["confusion"].items())
        ]
        (out / "evaluation.json").write_text(
            json.dumps(serializable, indent=2), encoding="utf-8")
        rows = ["verdict,precision,recall,f1,support"]
        for label, m in results["per_verdict"].items():
            rows.append("%s,%.4f,%.4f,%.4f,%d"
                        % (label, m["precision"], m["recall"], m["f1"],
                           m["support"]))
        (out / "evaluation.csv").write_text("\n".join(rows) + "\n",
                                            encoding="utf-8")
        (out / "evaluation_summary.md").write_text(
            render_evaluation_summary(results), encoding="utf-8")
        (out / "HEADLINE.md").write_text(
            "# Headline\n\n" + summarize(results) + "\n", encoding="utf-8")
    return 0


def cmd_verify(args) -> int:
    with open(args.file, encoding="utf-8") as handle:
        data = json.load(handle)
    # Free-text claims: extract facts automatically when none are given.
    for claim in data.get("claims", []):
        if not claim.get("facts"):
            claim["facts"] = [
                {"kind": f.kind, "key": f.key, "value": f.value,
                 "surface": f.surface}
                for f in extract_facts(claim["text"])
            ]
    answer = load_answer(data)
    report = verify_answer(answer)
    if args.format == "md":
        print(render_answer_report(answer, report))
    else:
        for claim in answer.claims:
            claim_report = report.claims[claim.id]
            status = "supported" if claim_report.supported else "UNSUPPORTED"
            print("Claim %s (%s): minimal set %s, collapse depth %s"
                  % (claim.id, status,
                     ",".join(claim_report.minimal_set) or "-",
                     claim_report.collapse_depth))
            for pid, verdict in claim_report.verdicts.items():
                print("  [%s] %s" % (pid, verdict))
        print("faithfulness=%.3f precision=%.3f decorative=%.3f"
              % (report.faithfulness, report.citation_precision,
                 report.decorative_rate))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="citation-ablation")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("demo", help="verify a hand-built demo answer")
    evaluate_parser = sub.add_parser("evaluate",
                                     help="run the seeded evaluation")
    evaluate_parser.add_argument("--cases", default=str(DEFAULT_CASES))
    evaluate_parser.add_argument("--out", default=None)
    verify_parser = sub.add_parser("verify",
                                   help="verify one CitedAnswer JSON file")
    verify_parser.add_argument("file")
    verify_parser.add_argument("--format", choices=["text", "md"],
                               default="text")
    args = parser.parse_args(argv)
    if args.command == "demo":
        return cmd_demo(args)
    if args.command == "evaluate":
        return cmd_evaluate(args)
    if args.command == "verify":
        return cmd_verify(args)
    return 2


if __name__ == "__main__":
    sys.exit(main())
