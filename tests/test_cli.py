"""Tests for the CLI."""

import json
from pathlib import Path

from citation_ablation.cli import main

ROOT = Path(__file__).resolve().parent.parent


def test_demo_runs(capsys):
    assert main(["demo"]) == 0
    out = capsys.readouterr().out
    assert "LOAD-BEARING" in out
    assert "DECORATIVE" in out
    assert "CONTRADICTING" in out


def test_evaluate_writes_results(tmp_path):
    assert main(["evaluate", "--out", str(tmp_path)]) == 0
    for name in ("evaluation.json", "evaluation.csv",
                 "evaluation_summary.md", "HEADLINE.md"):
        assert (tmp_path / name).exists()
    data = json.loads((tmp_path / "evaluation.json").read_text())
    assert data["n_cases"] == 60
    assert data["verdict_accuracy"] == 1.0


def test_verify_demo_answer_json(tmp_path):
    assert main(["verify", str(ROOT / "examples" / "demo_answer.json")]) == 0


def test_verify_markdown_format(capsys):
    assert main(["verify", str(ROOT / "examples" / "demo_answer.json"),
                 "--format", "md"]) == 0
    out = capsys.readouterr().out
    assert "# Citation-Ablation Report" in out


def test_verify_free_text_claims_get_facts(tmp_path):
    answer = {
        "id": "free", "question": "What dose?",
        "claims": [{"id": "c1", "text": "The dose is 200 mg twice daily."}],
        "passages": [{"id": "p1",
                      "text": "The dose is 200 mg twice daily."}],
        "citations": {"c1": ["p1"]},
    }
    path = tmp_path / "free.json"
    path.write_text(json.dumps(answer), encoding="utf-8")
    assert main(["verify", str(path)]) == 0


def test_verify_text_format_lists_verdicts(capsys):
    assert main(["verify", str(ROOT / "examples" / "demo_answer.json")]) == 0
    out = capsys.readouterr().out
    assert "load_bearing" in out
    assert "decorative" in out
    assert "contradicting" in out
    assert "faithfulness=1.000" in out
