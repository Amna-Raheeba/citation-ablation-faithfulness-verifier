# Citation-Ablation Faithfulness Verifier

**A citation that exists is not a citation that carries the answer.** This
tool checks whether each citation of a RAG answer is actually
load-bearing: ablate it — remove it from the evidence set — and re-check
whether the answer still stands. If the answer is unchanged and still
fully supported without that citation, the citation is decoration, not
evidence.

RAGAS scores faithfulness at the answer level (supported claims / total
claims). `rag-verifier` checks whether one citation supports one claim.
[CUE-R](https://ai-search.io/papers/cue-r-beyond-the-final-answer-in-retrieval-augmented-generation)
perturbs evidence items and measures utility — but it is an LLM-based
research evaluation, not a runnable offline tool. None of them answers
the question this tool asks: *which individual citations carry this
answer, which are redundant, which are pure decoration — and what is the
smallest set of citations that still supports it?* This tool does, offline,
deterministically, stdlib-only, no model calls.

It is the citation-level companion to
[luck-audit](https://github.com/Amna-Raheeba/luck-audit) (which audits
evidence sufficiency at the argument level) and
[production-rag-citations](https://github.com/Amna-Raheeba/production-rag-citations)
(which builds a RAG system with citations). Luck-audit asks whether the
answer was earned by evidence; this tool asks which citations did the
earning.

## 1. The idea in 30 seconds

1. An answer is a list of claims; each claim carries explicit checkable
   facts (numbers with attribute keys, named entities, terms). Evidence
   is a list of passages; citations link claims to passages.
2. Support is lexical and auditable: a passage covers a fact when its
   surface appears in the passage text (numbers by numeric equality, so
   `200` and `200.0` match; entities and terms by normalized
   containment). A passage contradicts a claim only when it states the
   same keyed number differently and never states the claim's number.
3. For each citation, ablate it and re-check support. The verdicts, in
   check order:
   - **contradicting** — states a keyed number differently from the claim.
   - **decorative** — covers no fact of the claim at all; never evidence.
   - **redundant** — the claim stays supported without it; another cited
     passage covers the same facts.
   - **load-bearing** — removing it breaks support (or the claim is
     unsupported overall and this passage carries part of the only
     support there is).
4. Per claim it also computes the **minimal sufficient citation set**
   (greedy set cover, plus the exact minimum by brute force for small
   sets), the **collapse depth** (the smallest number of citations whose
   removal breaks support), the **critical citations** (present in every
   minimal set), and the **ordered ablation curve** (remove decorative,
   then redundant, then load-bearing; watch the answer collapse).
5. Per answer: faithfulness (supported claims), citation precision
   (load-bearing share), decorative rate, efficiency (|minimal| /
   |cited|), mean collapse depth, ablation robustness (fraction of
   single-citation removals the answer survives).

## 2. Quick start

```bash
pip install -e .
python -m citation_ablation demo
python -m citation_ablation verify examples/demo_answer.json --format md
python -m citation_ablation evaluate --out results
streamlit run app.py
```

## 3. What the numbers mean

Seeded evaluation, 60 cases (48 generated + 12 hand-reasoned), 161
citations scored:

| Metric | Verifier | Baseline |
| --- | --- | --- |
| Verdict accuracy | 1.000 | 0.658 (naive: every citation load-bearing) |
| Per-verdict P / R / F1 | 1.000 / 1.000 / 1.000 (all four classes) | — |
| Minimal-set size accuracy | 1.000 | — |
| Greedy == exact minimal set | 1.000 (benchmark) | 0.954 (random stress, 151 instances) |
| Collapse-depth accuracy | 1.000 | — |
| Claim-support accuracy | 1.000 | — |
| Decorative separation (padded minus clean) | 0.333 | 0.000 (RAGAS-style, by construction) |

The 1.000s are honest about what they are: the 48 generated cases carry
labels by construction, and the generator asserts them at build time as a
fixture-sanity check. The independent check is the 12 hand-reasoned cases
(`data/hand_cases.json`), whose labels were worked out by hand — including
numeric-format traps (`200.0` vs `200`), key-absent non-contradictions,
zero-fact claims, and a contradicting passage inside the minimal set.
The one genuinely non-vacuous number is the greedy stress test: on 151
seeded random set-cover instances, greedy equals the exact minimum only
95.4% of the time — greedy set cover is *not* always optimal, and the tool
says so instead of hiding it.

## 4. How the verdicts behave

- **Duplication means neither copy is load-bearing.** Two passages with
  identical coverage are both `redundant`; the minimal set is one of
  them and the collapse depth is 2. That is the correct finding, not a
  bug: the answer survives losing either copy.
- **A contradicting passage can sit inside the minimal set.** If it is
  the only passage covering the term fact while contradicting the number
  fact, the claim needs it *and* the verdict is `contradicting`.
  Contradiction is checked before coverage for exactly this reason.
- **An unsupported claim still has load-bearing citations.** A passage
  covering part of the support is load-bearing even when the claim as a
  whole is unsupported — it is the only support there is.
- **A claim with no facts is vacuously supported**, its minimal set is
  empty, and its citations are decorative. Nothing can break it, so its
  collapse depth is `len(citations) + 1` by convention.

## 5. Repository layout

```text
citation_ablation/   models, facts, support, ablate, minimal, evaluate, report, cli
data/                cases.json (48 generated), hand_cases.json (12 hand-reasoned)
notebooks/           01_demo_run.py, 02_evaluation_experiment.py
examples/            demo_answer.json, demo_run.py, sample_report.md
scripts/             build_cases.py, reproduce_results.py
results/             evaluation.json/csv, evaluation_summary.md, HEADLINE.md
app.py               Streamlit dashboard (Case Explorer, Ablation Curve, Evaluation)
tests/               9 files, 61 tests
```

`scripts/reproduce_results.py` regenerates every number in `results/`
and fails on headline drift — delete `results/` first to accept new
numbers deliberately.

## 6. Honest limits

- **Support is lexical, not semantic.** A passage that paraphrases a
  fact without its surface words is scored as not covering it, and a
  passage that mentions the right words in the wrong sense is scored as
  covering it. The tool checks what is written, not what is meant; an
  NLI scorer would be the production upgrade.
- **Contradiction is numbers-only.** Only keyed number facts can
  contradict. A passage contradicting an entity or a term in prose is
  not detected.
- **The benchmark is synthetic.** All 60 cases are hand-templated or
  hand-written; the 1.000s validate the implementation against its own
  contract, not real-world accuracy. Real RAG answers need a corpus of
  real cited answers to mean anything beyond that.
- **Greedy minimal sets are near-minimal, not proven minimal** (set
  cover is NP-hard). The exact minimum is computed by brute force only
  for 12 or fewer cited passages per claim.
- **Facts are explicit in case data.** Free-text claims go through a
  best-effort extractor (numbers, capitalised entities, content words);
  extraction errors become verification errors.

## 7. Related work

- RAGAS (Es et al., 2023) — answer-level faithfulness; no per-citation
  ablation, no minimal sets.
- rag-verifier (PyPI) — per-citation supported / insufficient verdicts
  with a deterministic gate; never asks whether the answer still stands
  without the citation.
- CUE-R — intervention-based per-evidence utility (REMOVE / REPLACE /
  DUPLICATE) on HotpotQA / 2WikiMultihopQA with LLM generators; a
  research evaluation framework, not an offline verifier tool.
- anchor-rag, scinexusrag — per-claim verification and generation
  ablation; neither computes per-citation verdicts or minimal sufficient
  citation sets.
- L-MARS — legal multi-agent citation-faithfulness audit, LLM-judged,
  domain-specific.

## 8. Licence

MIT. See `LICENSE`.
