# Evaluation Summary

Cases: 60, citations scored: 161
Verdict accuracy: 1.000 (naive all-load-bearing baseline: 0.658)
  load_bearing: P=1.000 R=1.000 F1=1.000 (n=106)
  redundant: P=1.000 R=1.000 F1=1.000 (n=19)
  decorative: P=1.000 R=1.000 F1=1.000 (n=26)
  contradicting: P=1.000 R=1.000 F1=1.000 (n=10)
Minimal-set size accuracy: 1.000; greedy == exact: 1.000
Greedy stress (151 random instances): greedy == exact on 0.954; mean greedy 2.09 vs exact 2.05
Collapse-depth accuracy: 1.000; claim-support accuracy: 1.000
Decorative separation (padded minus clean): 0.333 (RAGAS-style baseline: 0.000 by construction)

## Per-scenario verdict accuracy

- clean: 1.000 (16 cases)
- contradicting: 1.000 (16 cases)
- hand: 1.000 (12 cases)
- multi-hop: 1.000 (16 cases)
- padded: 1.000 (16 cases)
- redundant: 1.000 (16 cases)
- unsupported: 1.000 (16 cases)

## Decorative rate by scenario

- clean: 0.000
- padded: 0.333
- redundant: 0.000
- contradicting: 0.000
- unsupported: 0.333
- multi-hop: 0.250
- hand: 0.167