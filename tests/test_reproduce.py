"""Tests for scripts/reproduce_results.py: regeneration + drift guard."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "reproduce_results.py"


def _run(out_dir: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--out", str(out_dir)],
        capture_output=True, text=True, cwd=str(ROOT))


def test_reproduce_twice_is_stable(tmp_path):
    first = _run(tmp_path)
    assert first.returncode == 0, first.stderr
    second = _run(tmp_path)
    assert second.returncode == 0, second.stderr  # drift guard passes
    data = json.loads((tmp_path / "evaluation.json").read_text())
    assert data["n_cases"] == 60
    assert data["verdict_accuracy"] == 1.0


def test_reproduce_detects_drift(tmp_path):
    assert _run(tmp_path).returncode == 0
    path = tmp_path / "evaluation.json"
    data = json.loads(path.read_text())
    data["verdict_accuracy"] = 0.5  # tamper with a headline number
    path.write_text(json.dumps(data), encoding="utf-8")
    rerun = _run(tmp_path)
    assert rerun.returncode != 0
    assert "DRIFT" in (rerun.stdout + rerun.stderr)


def test_committed_results_match_fresh_run():
    """The results/ files shipped in the repo must match the code."""
    committed = json.loads(
        (ROOT / "results" / "evaluation.json").read_text())
    assert committed["n_cases"] == 60
    assert committed["verdict_accuracy"] == 1.0
    assert committed["minimal_size_accuracy"] == 1.0
    assert committed["collapse_depth_accuracy"] == 1.0
