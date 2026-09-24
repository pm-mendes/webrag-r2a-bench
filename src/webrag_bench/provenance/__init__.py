"""Signed cross-party provenance (paper Y, 08-TWEB-PBD) — first building block.

Each party (a web origin, a tool server, a peer agent) holds an Ed25519 key. When it
produces an output, it issues an attestation: *this party produced this output (by
digest), through this activity (tool and argument digests), derived from these earlier
attestations*. Attestations travel in the `_meta` of MCP tool results and can be
exported as PROV-O (JSON-LD).

What this block does NOT do: decide whether untrusted content determined an argument
(that is argument-level provenance inference, the open problem PACT isolates), enforce
a policy, or implement the 17 adversarial behaviours. It provides cryptographic origin
attestation, on which those are built.
"""

from webrag_bench.provenance.attestation import Attestation, issue, verify, verify_chain
from webrag_bench.provenance.canonical import canonical_json, digest
from webrag_bench.provenance.keys import KeyRegistry, PartyKey
from webrag_bench.provenance.mcp_transport import META_KEY, attach, extract
from webrag_bench.provenance.prov import to_prov_jsonld

__all__ = [
    "META_KEY",
    "Attestation",
    "KeyRegistry",
    "PartyKey",
    "attach",
    "canonical_json",
    "digest",
    "extract",
    "issue",
    "to_prov_jsonld",
    "verify",
    "verify_chain",
]
