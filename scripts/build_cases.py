"""Seeded generator for the 48-case evaluation set.

Six scenarios x eight cases. Labels are by construction: each passage is
built to play one role (supporting, restating, decorative, contradicting,
split-half). The generator then runs the verifier over every case and
asserts the intended verdicts hold — a fixture-sanity check that catches
template collisions (e.g. a "decorative" passage accidentally containing a
fact surface). The independent check on the verifier is data/hand_cases.json:
12 cases whose labels were reasoned by hand, not generated.

Seed 7. Deterministic: re-running this script reproduces data/cases.json
byte-for-byte (modulo JSON key order, which is fixed by sort_keys).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from citation_ablation.ablate import verify_answer  # noqa: E402
from citation_ablation.evaluate import load_answer  # noqa: E402

SEED = 7

DOMAINS = {
    "health": {
        "entities": ["Metformin", "Atorvastatin", "Lisinopril", "Amlodipine"],
        "key": "dose of {e}",
        "unit": "mg",
        "values": [100, 200, 250, 500],
        "terms": ["twice daily", "once daily", "after meals"],
        "support": "The recommended dose of {e} is {n} mg {term}.",
        "restate": "{e} {n} mg {term} is the standard starting dose for adults.",
        "split_num": "The recommended dose of {e} is {n} mg.",
        "split_term": "{e} is taken {term}.",
        "decorative": "{o} is usually taken with food and may cause mild nausea.",
        "contradict": "The dose of {e} is {m} mg {term}.",
        "question": "What is the recommended dose of {e} and when is it taken?",
        "claim": "The recommended dose of {e} is {n} mg {term}.",
    },
    "finance": {
        "entities": ["Aurora", "Beacon", "Harbor", "Summit"],
        "key": "interest rate on the {e} savings account",
        "unit": "%",
        "values": [3, 4, 5, 6],
        "terms": ["compounded monthly", "paid annually", "reviewed quarterly"],
        "support": "The annual interest rate on the {e} savings account is {n}%, {term}.",
        "restate": "The {e} savings account pays {n}% interest, {term}.",
        "split_num": "The annual interest rate on the {e} savings account is {n}%.",
        "split_term": "Interest on the {e} savings account is {term}.",
        "decorative": "The {o} account includes free online banking and no monthly fee.",
        "contradict": "The interest rate on the {e} savings account is {m}%.",
        "question": "What is the interest rate on the {e} savings account?",
        "claim": "The annual interest rate on the {e} savings account is {n}%, {term}.",
    },
    "science": {
        "entities": ["Mercury", "Venus", "Earth", "Mars"],
        "key": "orbital period of {e}",
        "unit": "days",
        "values": [88, 225, 365, 687],
        "terms": ["around the Sun", "in Earth days", "per orbit"],
        "support": "The orbital period of {e} is {n} days {term}.",
        "restate": "{e} takes {n} days {term} to complete one orbit.",
        "split_num": "The orbital period of {e} is {n} days.",
        "split_term": "{e} completes one orbit {term}.",
        "decorative": "{o} has two small moons and a thin atmosphere.",
        "contradict": "The orbital period of {e} is {m} days.",
        "question": "How long is the orbital period of {e}?",
        "claim": "The orbital period of {e} is {n} days {term}.",
    },
    "tech": {
        "entities": ["search", "billing", "upload", "auth"],
        "key": "rate limit for the {e} endpoint",
        "unit": "requests per minute",
        "values": [60, 100, 120, 300],
        "terms": ["with burst allowance", "per API key", "after authentication"],
        "support": "The rate limit for the {e} endpoint is {n} requests per minute, {term}.",
        "restate": "The {e} endpoint allows {n} requests per minute, {term}.",
        "split_num": "The rate limit for the {e} endpoint is {n} requests per minute.",
        "split_term": "The {e} endpoint allows requests {term}.",
        "decorative": "The {o} endpoint returns JSON and supports pagination.",
        "contradict": "The rate limit for the {e} endpoint is {m} requests per minute.",
        "question": "What is the rate limit for the {e} endpoint?",
        "claim": "The rate limit for the {e} endpoint is {n} requests per minute, {term}.",
    },
}

SCENARIOS = ["clean", "padded", "redundant", "contradicting",
             "unsupported", "multi-hop"]


def _fact_number(domain: dict, entity: str, value) -> dict:
    surface = "%s %s" % (value, domain["unit"])
    return {"kind": "number",
            "key": domain["key"].format(e=entity),
            "value": str(value), "surface": surface}


def _fact_term(term: str) -> dict:
    return {"kind": "term", "key": "", "value": term, "surface": term}


def _claim_text(domain: dict, entity: str, value, term: str) -> str:
    return domain["claim"].format(e=entity, n=value, term=term)


def build_case(scenario: str, index: int) -> dict:
    """Build one case. Index 0..7 varies domain/entity/number/term."""
    names = list(DOMAINS)
    domain_name = names[index % len(names)]
    domain = DOMAINS[domain_name]
    entities = domain["entities"]
    ent_a = entities[(index // len(names)) % len(entities)]
    ent_b = entities[((index // len(names)) + 1) % len(entities)]
    values = domain["values"]
    n1 = values[index % len(values)]
    n2 = values[(index + 1) % len(values)]
    m = values[(index + 2) % len(values)]
    terms = domain["terms"]
    t1 = terms[index % len(terms)]
    t2 = terms[(index + 1) % len(terms)]
    case_id = "case-%03d" % (SCENARIOS.index(scenario) * 8 + index + 1)
    claims = [
        {"id": "c1", "text": _claim_text(domain, ent_a, n1, t1),
         "facts": [_fact_number(domain, ent_a, n1), _fact_term(t1)]},
        {"id": "c2", "text": _claim_text(domain, ent_b, n2, t2),
         "facts": [_fact_number(domain, ent_b, n2), _fact_term(t2)]},
    ]
    passages = [
        {"id": "p1", "text": domain["support"].format(e=ent_a, n=n1, term=t1)},
        {"id": "p2", "text": domain["support"].format(e=ent_b, n=n2, term=t2)},
    ]
    labels = {"c1": {"p1": "load_bearing"}, "c2": {"p2": "load_bearing"}}
    ground_truth = {
        "c1": {"minimal_size": 1, "collapse_depth": 1, "supported": True},
        "c2": {"minimal_size": 1, "collapse_depth": 1, "supported": True},
    }
    citations = {"c1": ["p1"], "c2": ["p2"]}
    if scenario == "padded":
        passages.append({"id": "p3", "text": domain["decorative"].format(o=ent_b)})
        citations["c1"] = ["p1", "p3"]
        labels["c1"]["p3"] = "decorative"
    elif scenario == "redundant":
        passages.append({"id": "p3", "text": domain["restate"].format(e=ent_a, n=n1, term=t1)})
        citations["c1"] = ["p1", "p3"]
        labels["c1"]["p1"] = "redundant"
        labels["c1"]["p3"] = "redundant"
        ground_truth["c1"]["collapse_depth"] = 2
    elif scenario == "contradicting":
        passages.append({"id": "p3", "text": domain["contradict"].format(e=ent_a, n=n1, m=m, term=t1)})
        citations["c1"] = ["p1", "p3"]
        labels["c1"]["p3"] = "contradicting"
    elif scenario == "unsupported":
        passages.append({"id": "p3", "text": domain["split_term"].format(e=ent_b, term=t2)})
        passages.append({"id": "p4", "text": domain["decorative"].format(o=ent_a)})
        citations["c2"] = ["p3", "p4"]
        labels["c2"] = {"p3": "load_bearing", "p4": "decorative"}
        ground_truth["c2"] = {"collapse_depth": 0, "supported": False}
    elif scenario == "multi-hop":
        passages.append({"id": "p3", "text": domain["split_num"].format(e=ent_a, n=n1)})
        passages.append({"id": "p4", "text": domain["split_term"].format(e=ent_a, term=t1)})
        passages.append({"id": "p5", "text": domain["decorative"].format(o=ent_b)})
        citations["c1"] = ["p3", "p4", "p5"]
        labels["c1"] = {"p3": "load_bearing", "p4": "load_bearing",
                         "p5": "decorative"}
        ground_truth["c1"] = {"minimal_size": 2, "collapse_depth": 1,
                              "supported": True}
    return {
        "id": case_id,
        "scenario": scenario,
        "question": domain["question"].format(e=ent_a),
        "claims": claims,
        "passages": passages,
        "citations": citations,
        "labels": labels,
        "ground_truth": ground_truth,
    }


def self_check(cases: list) -> None:
    """Assert the verifier recovers every intended label.

    This is a fixture-sanity check, not the evaluation: it catches template
    collisions at build time. The evaluation's independent check is the
    hand-written data/hand_cases.json.
    """
    problems = []
    for case in cases:
        answer = load_answer(case)
        report = verify_answer(answer)
        for claim in answer.claims:
            claim_report = report.claims[claim.id]
            for pid, want in case["labels"][claim.id].items():
                got = claim_report.verdicts.get(pid)
                if got != want:
                    problems.append("%s %s %s: want %s, got %s"
                                    % (case["id"], claim.id, pid, want, got))
            gt = case["ground_truth"][claim.id]
            if "minimal_size" in gt and len(claim_report.minimal_set) != gt["minimal_size"]:
                problems.append("%s %s: minimal size want %s, got %s"
                                % (case["id"], claim.id, gt["minimal_size"],
                                   len(claim_report.minimal_set)))
            if claim_report.collapse_depth != gt["collapse_depth"]:
                problems.append("%s %s: collapse depth want %s, got %s"
                                % (case["id"], claim.id, gt["collapse_depth"],
                                   claim_report.collapse_depth))
            if claim_report.supported != gt["supported"]:
                problems.append("%s %s: supported want %s, got %s"
                                % (case["id"], claim.id, gt["supported"],
                                   claim_report.supported))
    if problems:
        raise SystemExit("SELF-CHECK FAILED:\n" + "\n".join(problems))


def main() -> int:
    cases = [build_case(scenario, i)
             for scenario in SCENARIOS for i in range(8)]
    self_check(cases)
    out = Path(__file__).resolve().parent.parent / "data" / "cases.json"
    out.write_text(json.dumps(cases, indent=2, sort_keys=True),
                   encoding="utf-8")
    print("wrote %d cases to %s (self-check passed)" % (len(cases), out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
