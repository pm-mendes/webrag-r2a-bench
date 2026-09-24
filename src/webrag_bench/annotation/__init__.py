"""Annotation batch: stratified, blinded, deterministic, frozen.

The batch is built once, before any annotation, from the run records and their
transcripts. Both annotators receive the same blinded items (so that Cohen's kappa
exists); the key linking items to episodes stays sealed with whoever built the batch.
Once written, a batch is never rebuilt or edited: `verify_batch` detects any change.
"""

from webrag_bench.annotation.batch import BatchError, build_batch, verify_batch
from webrag_bench.annotation.config import Allocation, BatchConfig, load_batch_config
from webrag_bench.annotation.strata import STRATUM_KEYS

__all__ = [
    "STRATUM_KEYS",
    "Allocation",
    "BatchConfig",
    "BatchError",
    "build_batch",
    "load_batch_config",
    "verify_batch",
]
