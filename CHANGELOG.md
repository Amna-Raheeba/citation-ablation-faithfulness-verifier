# Changelog

## 0.1.0 — 2026-11-17

- First release.
- Citation-ablation verifier: per-citation verdicts (load-bearing /
  redundant / decorative / contradicting), greedy + exact minimal
  sufficient citation sets, collapse depth, critical citations, ordered
  ablation curve, per-answer faithfulness scores.
- Seeded evaluation: 48 generated cases (6 scenarios x 8) + 12
  hand-reasoned cases; verdict accuracy 1.000 vs naive baseline 0.658;
  decorative separation 0.333 (RAGAS-style baseline: 0.000).
- Greedy stress test: 151 random set-cover instances, greedy == exact
  on 0.954 — greedy is not always optimal, measured honestly.
- Streamlit dashboard (3 tabs), demo + evaluation notebooks, example
  answer with a rendered sample report.
