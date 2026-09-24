"""HTML-to-text readers, treated as an experimental factor."""

from webrag_bench.readers.registry import get_reader, reader_names, reader_version

__all__ = ["get_reader", "reader_names", "reader_version"]
