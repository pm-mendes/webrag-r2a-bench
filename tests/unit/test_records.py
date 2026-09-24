import os
from pathlib import Path

import pytest

from webrag_bench import ROOT

KIT = Path(os.environ.get("WEBRAG_KIT_DIR", Path.home() / "overleaf/07-TWEB-R2A/kit"))


def test_schema_is_identical_to_the_kit():
    kit_schema = KIT / "schemas/run_record_schema.json"
    if not kit_schema.exists():
        pytest.skip(f"kit not found at {kit_schema} (set WEBRAG_KIT_DIR)")
    assert kit_schema.read_bytes() == (ROOT / "schemas/run_record_schema.json").read_bytes()
