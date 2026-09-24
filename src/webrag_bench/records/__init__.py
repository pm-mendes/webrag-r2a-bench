"""Run records, validated against the kit schema.

`schemas/run_record_schema.json` is a byte-for-byte copy of the kit's
(07-TWEB-R2A/kit/schemas/). Its field names are French by contract with the
manuscripts and must not be translated; `records.mapping` converts the bench's
English vocabulary to the schema's.
"""

from webrag_bench.records.io import append_record, completed_ids
from webrag_bench.records.mapping import to_schema_action_type, to_schema_family, to_schema_index
from webrag_bench.records.schema import arguments_digest, validate_record

__all__ = [
    "append_record",
    "arguments_digest",
    "completed_ids",
    "to_schema_action_type",
    "to_schema_family",
    "to_schema_index",
    "validate_record",
]
