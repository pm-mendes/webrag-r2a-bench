from pathlib import Path

import pytest

from webrag_bench import ROOT


@pytest.fixture
def dry_run_plan_path() -> Path:
    return ROOT / "config/plans/dry-run.yaml"
