# Signed provenance (paper Y) — first building block

`webrag_bench.provenance` and `webrag_bench.servers.signing` provide **cryptographic
origin attestation across parties**: a web origin signs the pages it serves, a peer
agent signs its answers and declares what they derive from. The attestations travel
in the `_meta` of MCP tool results and export to PROV-O.

## Attestation

```json
{
  "version": "webrag-attestation/0",
  "issuer": "intranet.example.test",
  "activity": {"tool": "http.get", "arguments_digest": "sha256:…"},
  "output_digest": "sha256:…",
  "derived_from": ["sha256:…"],
  "issued_at": "2026-09-26T10:00:00Z",
  "id": "sha256:<digest of the payload above>",
  "signature": "<Ed25519 over the canonical payload, base64url>"
}
```

`verify` checks the issuer is registered, the signature, and — given the content — that
the attestation covers exactly that content. `verify_chain` walks `derived_from`
transitively and reports unknown parents and cycles.

## Mapping to PROV-O

| Attestation | PROV-O |
|---|---|
| output | `prov:Entity` |
| tool call | `prov:Activity`, `prov:wasAssociatedWith` the issuer |
| issuer | `prov:Agent` |
| `derived_from` | `prov:wasDerivedFrom` between entities |

## Policies

Defenses receive a `DecisionContext` with the verification result of every page. The
DEMO policy `provenance-demo` refuses effectful calls when any page failed
verification. It is **not** the mechanism of paper Y (`pbd`, pending), and its dry-run
results show two things worth keeping in mind:

- a signature attests **origin, not harmlessness**: an injection hosted on a
  legitimate origin is signed, verifies, and passes the gate;
- when signing parties fail, the gate blocks benign work too — the quantity the
  graceful-degradation measure is about.

## Deliberate limits

- **Not a Verifiable Credential.** The payload is VC-shaped in spirit only; the proof
  is not a W3C Data Integrity proof, and canonicalisation is close to, but not claimed
  conformant with, RFC 8785. Floats are refused in signed content for that reason.
- **Deterministic keys** from (seed, party), for a reproducible closed benchmark only.
- **No argument-level inference.** Knowing that origin H served a page does not say
  whether text in that page determined an argument of a later call. That inference is
  the open problem PACT (arXiv:2605.11039) isolates; this block does not claim to solve
  it (see `08-TWEB-PBD/VEILLE-NOUVEAUTE.md` §1.1).
- **Wired into episodes as a factor** (`provenance`, `fault_rates`, see
  `config/plans/y-dry-run.yaml`); the 17 adversarial behaviours, the `pbd` mechanism
  and the A2A transport come with the Y protocol, once frozen.
