import pytest

from webrag_bench.index import Doc, StubEmbedder, build_index

DOCS = [
    Doc("u1", "leave policy request two weeks in advance"),
    Doc("u2", "potato gratin recipe with cream"),
    Doc("u3", "expense reimbursement by bank transfer"),
]


@pytest.mark.parametrize("name", ["bm25", "dense", "hybrid"])
def test_every_index_ranks_the_relevant_doc_first(name):
    index = build_index(name, DOCS, StubEmbedder(), alpha=0.5)
    assert index.search("how do I request leave", 2)[0][0].url == "u1"


def test_unknown_index_is_rejected():
    with pytest.raises(ValueError, match="unknown index"):
        build_index("nope", DOCS, StubEmbedder(), alpha=0.5)
