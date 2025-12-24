"""Shared pytest fixtures for tests."""

import json
from pathlib import Path
import pytest


@pytest.fixture
def sample_company():
    path = Path(__file__).parent.parent / "data" / "examples" / "company_data.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("example_companies", [])[0]
