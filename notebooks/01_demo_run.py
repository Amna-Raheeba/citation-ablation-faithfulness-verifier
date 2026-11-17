"""Notebook 01: demo run — verify one answer, show the ablation curve."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from citation_ablation.ablate import ablation_curve, verify_answer  # noqa: E402
from citation_ablation.cli import demo_answer  # noqa: E402
from citation_ablation.report import render_answer_report  # noqa: E402

answer = demo_answer()
report = verify_answer(answer)
print(render_answer_report(answer, report))
print("Ablation curve for claim c1 (decorative first, then redundant, "
      "then load-bearing):")
for removed, supported in ablation_curve(answer, "c1"):
    print("  removed %-4s -> %s" % (removed or "-",
                                    "supported" if supported else "COLLAPSED"))
print("Takeaway: c1 survives losing its decorative and contradicting "
      "citations, but collapses once both redundant copies are gone — "
      "neither copy alone is load-bearing, which is exactly what "
      "duplication means.")
