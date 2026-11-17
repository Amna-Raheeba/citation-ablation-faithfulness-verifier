"""Streamlit dashboard: explore cases, ablation curves, evaluation."""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from citation_ablation.ablate import ablation_curve, verify_answer
from citation_ablation.evaluate import load_cases

ROOT = Path(__file__).resolve().parent

st.set_page_config(page_title="Citation-Ablation Faithfulness Verifier",
                   layout="wide")
st.title("Citation-Ablation Faithfulness Verifier")
st.write("Are an answer's citations load-bearing — or decoration? "
         "Ablate each cited passage and see whether the answer still stands.")

VERDICT_STYLE = {
    "load_bearing": "🟢 load-bearing",
    "redundant": "🟡 redundant",
    "decorative": "⚪ decorative",
    "contradicting": "🔴 contradicting",
}


@st.cache_data
def load_all_cases():
    cases = load_cases(ROOT / "data" / "cases.json")
    cases += load_cases(ROOT / "data" / "hand_cases.json")
    return cases


@st.cache_data
def load_results():
    with open(ROOT / "results" / "evaluation.json", encoding="utf-8") as handle:
        return json.load(handle)


cases = load_all_cases()
case_ids = [c["id"] for c in cases]

tab_explore, tab_curve, tab_eval = st.tabs(
    ["Case Explorer", "Ablation Curve", "Evaluation"])

with tab_explore:
    selected_id = st.selectbox("Case", case_ids, index=0)
    case = next(c for c in cases if c["id"] == selected_id)
    st.write("**Scenario:** %s" % case.get("scenario", "?"))
    st.write("**Question:** %s" % case["question"])
    from citation_ablation.evaluate import load_answer

    answer = load_answer(case)
    report = verify_answer(answer)
    st.write("Faithfulness: %.3f | Citation precision: %.3f | "
             "Decorative rate: %.3f | Mean collapse depth: %.2f"
             % (report.faithfulness, report.citation_precision,
                report.decorative_rate, report.mean_collapse_depth))
    for claim in answer.claims:
        claim_report = report.claims[claim.id]
        st.subheader("Claim %s — %s" % (
            claim.id, "supported" if claim_report.supported
            else "UNSUPPORTED"))
        st.write("> %s" % claim.text)
        st.write("Minimal sufficient set: %s | Collapse depth: %s | "
                 "Critical: %s"
                 % (", ".join(claim_report.minimal_set) or "none",
                    claim_report.collapse_depth,
                    ", ".join(claim_report.critical_citations) or "none"))
        rows = []
        for passage in answer.passages_for(claim.id):
            verdict = claim_report.verdicts.get(passage.id, "?")
            rows.append({"passage": passage.id,
                         "verdict": VERDICT_STYLE.get(verdict, verdict),
                         "text": passage.text})
        st.dataframe(rows, width="stretch")

with tab_curve:
    selected_id = st.selectbox("Case", case_ids, index=0, key="curve_case")
    case = next(c for c in cases if c["id"] == selected_id)
    from citation_ablation.evaluate import load_answer

    answer = load_answer(case)
    claim_id = st.selectbox("Claim", [c.id for c in answer.claims])
    curve = ablation_curve(answer, claim_id)
    rows = []
    for step, (removed, supported) in enumerate(curve):
        rows.append({"step": step,
                     "removed": removed or "(none)",
                     "supported": 1 if supported else 0,
                     "status": "supported" if supported else "COLLAPSED"})
    st.write("Citations are removed decorative-first, then redundant, "
             "then load-bearing. The answer collapses at the first "
             "load-bearing removal it cannot survive.")
    st.dataframe(rows, width="stretch")
    st.line_chart([r["supported"] for r in rows])

with tab_eval:
    results = load_results()
    st.subheader("Headline")
    st.write("Cases: %d | Citations scored: %d"
             % (results["n_cases"], results["n_citations"]))
    st.write("Verdict accuracy: %.3f (naive all-load-bearing baseline: %.3f)"
             % (results["verdict_accuracy"],
                results["naive_baseline_accuracy"]))
    st.write("Minimal-set size accuracy: %.3f | Greedy == exact: %.3f"
             % (results["minimal_size_accuracy"],
                results["greedy_equals_exact"]))
    st.write("Collapse-depth accuracy: %.3f | Claim-support accuracy: %.3f"
             % (results["collapse_depth_accuracy"],
                results["support_accuracy"]))
    st.write("Decorative separation (padded minus clean): %.3f "
             "(RAGAS-style baseline: 0.000)"
             % results["decorative_separation"])
    stress = results.get("greedy_stress", {})
    if stress:
        st.write("Greedy stress (%d random instances): greedy == exact on "
                 "%.3f; mean greedy %.2f vs exact %.2f"
                 % (stress["instances"], stress["greedy_equals_exact_rate"],
                    stress["mean_greedy_size"], stress["mean_exact_size"]))
    st.subheader("Per-verdict precision / recall / F1")
    rows = [{"verdict": label, "precision": m["precision"],
             "recall": m["recall"], "f1": m["f1"], "support": m["support"]}
            for label, m in results["per_verdict"].items()]
    st.dataframe(rows, width="stretch")
    st.subheader("Per-scenario verdict accuracy")
    rows = [{"scenario": s, "accuracy": v["verdict_accuracy"],
             "cases": v["cases"]}
            for s, v in results["per_scenario"].items()]
    st.dataframe(rows, width="stretch")
