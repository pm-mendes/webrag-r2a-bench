import asyncio
import base64
import dataclasses

import pytest
from mcp.client.client import Client

from webrag_bench.corpus import Page, WarcReplay, write_warc
from webrag_bench.provenance import (
    Attestation,
    PartyKey,
    canonical_json,
    extract,
    issue,
    to_prov_jsonld,
    verify,
    verify_chain,
)
from webrag_bench.servers import Journal
from webrag_bench.servers.signing import party_keys, signed_http_server, signed_peer_server

SEED = "test-seed"


@pytest.fixture
def parties():
    return party_keys(["site.test", "peer", "mallory"], SEED)


def test_keys_are_deterministic():
    a, b = PartyKey.derive("p", SEED), PartyKey.derive("p", SEED)
    assert a.public_bytes == b.public_bytes
    assert PartyKey.derive("p", "other").public_bytes != a.public_bytes


def test_roundtrip(parties):
    keys, registry = parties
    att = issue(
        keys["site.test"], "http.get", {"url": "u"}, "content", issued_at="2026-09-26T10:00:00Z"
    )
    assert verify(att, registry, output="content") == []
    assert Attestation.from_dict(att.to_dict()) == att


def test_tampered_output_is_detected(parties):
    keys, registry = parties
    att = issue(keys["site.test"], "http.get", {"url": "u"}, "content")
    assert verify(att, registry, output="content + injected") == [
        "output does not match the attested digest"
    ]


def test_forged_issuer_is_detected(parties):
    keys, registry = parties
    forged = dataclasses.replace(issue(keys["mallory"], "http.get", {}, "x"), issuer="site.test")
    assert verify(forged, registry) == ["invalid signature for issuer 'site.test'"]


def test_unknown_issuer_and_garbage_signature(parties):
    _, registry = parties
    stranger = issue(PartyKey.derive("stranger", SEED), "t", {}, "x")
    assert verify(stranger, registry) == ["unknown issuer 'stranger'"]
    garbage = dataclasses.replace(stranger, issuer="peer", signature="not base64!")
    assert verify(garbage, registry) == ["invalid signature for issuer 'peer'"]


def test_chain_verification(parties):
    keys, registry = parties
    page = issue(keys["site.test"], "http.get", {"url": "u"}, "page")
    answer = issue(
        keys["peer"], "peer.delegate", {"instruction": "i"}, "ok", derived_from=(page.id,)
    )
    store = {page.id: page, answer.id: answer}
    assert verify_chain(answer, store, registry) == []
    missing = verify_chain(answer, {answer.id: answer}, registry)
    assert missing == [f"{answer.id}: derives from unknown attestation {page.id}"]


def test_signed_content_rejects_floats():
    with pytest.raises(TypeError, match="floats"):
        canonical_json({"amount": 1.5})


def test_signature_is_bound_to_the_payload(parties):
    keys, registry = parties
    att = issue(keys["site.test"], "http.get", {"url": "u"}, "content")
    other = issue(keys["site.test"], "http.get", {"url": "v"}, "content")
    swapped = dataclasses.replace(other, signature=att.signature)
    assert verify(swapped, registry) != []
    assert base64.urlsafe_b64decode(att.signature)


def test_prov_export(parties):
    keys, _ = parties
    page = issue(
        keys["site.test"], "http.get", {"url": "u"}, "page", issued_at="2026-09-26T10:00:00Z"
    )
    answer = issue(keys["peer"], "peer.delegate", {}, "ok", derived_from=(page.id,))
    doc = to_prov_jsonld([page, answer])
    types = sorted(n["@type"] for n in doc["@graph"])
    assert types == ["prov:Activity"] * 2 + ["prov:Agent"] * 2 + ["prov:Entity"] * 2
    entity = next(n for n in doc["@graph"] if n["@id"] == f"webrag:output/{answer.id}")
    assert entity["prov:wasDerivedFrom"] == [{"@id": f"webrag:output/{page.id}"}]


def test_attestations_travel_over_mcp(parties, tmp_path):
    keys, registry = parties
    warc = tmp_path / "c.warc"
    write_warc([Page("https://site.test/p", "<p>page</p>")], warc)
    journal = Journal()

    async def scenario():
        async with (
            Client(signed_http_server(journal, WarcReplay(warc), keys)) as http,
            Client(signed_peer_server(journal, keys["peer"])) as peer,
        ):
            page_result = await http.call_tool("get", {"url": "https://site.test/p"})
            page_att = extract(page_result)
            peer_result = await peer.call_tool(
                "delegate", {"instruction": "summarise", "derived_from": [page_att.id]}
            )
            return page_result, page_att, extract(peer_result)

    page_result, page_att, peer_att = asyncio.run(scenario())
    assert page_att.issuer == "site.test"
    assert verify(page_att, registry, output=page_result.content[0].text) == []
    assert verify_chain(peer_att, {page_att.id: page_att, peer_att.id: peer_att}, registry) == []
    assert journal.effects == [{"tool": "peer.delegate", "arguments": {"instruction": "summarise"}}]
