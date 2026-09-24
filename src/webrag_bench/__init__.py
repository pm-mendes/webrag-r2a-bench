"""webrag-r2a-bench: staged measurement of retrieval-to-action prompt injection.

An injection is traced through four nested stages (exposure -> absorption ->
effect -> action), each decided by a mechanical oracle. No third-party site is ever
contacted: every page comes from a local WARC archive.
"""

from importlib.metadata import version
from pathlib import Path

__version__ = version("webrag-r2a-bench")

ROOT = Path(__file__).resolve().parents[2]
"""Repository root (config/, corpus/, schemas/, runs/ are resolved against it)."""
