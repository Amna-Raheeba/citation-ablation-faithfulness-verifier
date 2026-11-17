# Citation-Ablation Report: demo

Question: What is the recommended dose of Metformin and when is it taken?

Faithfulness (supported claims): 1.000
Citation precision (load-bearing share): 0.200
Decorative rate: 0.200
Efficiency (|minimal| / |cited|): 0.625
Mean collapse depth: 1.50
Ablation robustness: 0.800

## Claim c1 — supported

> The recommended dose of Metformin is 200 mg twice daily.

Minimal sufficient set: p1
Collapse depth: 2
Critical citations: none

- [p1] redundant: The recommended dose of Metformin is 200 mg twice daily, taken after meals.
- [p2] redundant: Metformin 200 mg twice daily is the standard starting dose for adults with type 2 diabetes.
- [p3] DECORATIVE: Atorvastatin lowers LDL cholesterol and is often prescribed alongside diabetes medication.
- [p4] CONTRADICTING: The dose of Metformin is 400 mg twice daily according to the updated label.

## Claim c2 — supported

> Metformin is taken after meals.

Minimal sufficient set: p1
Collapse depth: 1
Critical citations: p1

- [p1] LOAD-BEARING: The recommended dose of Metformin is 200 mg twice daily, taken after meals.

