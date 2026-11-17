"""Dashboard smoke test via Streamlit AppTest."""

from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def test_dashboard_runs_without_exception():
    at = AppTest.from_file(APP)
    at.run(timeout=30)
    assert not at.exception
    # Three tabs render.
    assert len(at.tabs) == 3
