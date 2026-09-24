import pytest

from webrag_bench.corpus import (
    NotInCorpus,
    Page,
    WarcReplay,
    adversarial_url,
    is_adversarial_url,
    write_warc,
)


def test_replay_has_no_network_fallback(tmp_path):
    warc = tmp_path / "c.warc"
    write_warc([Page("https://a.test/x", "<html>x</html>")], warc)
    replay = WarcReplay(warc)
    assert replay.get("https://a.test/x") == "<html>x</html>"
    with pytest.raises(NotInCorpus):
        replay.get("https://a.test/missing")


def test_warc_is_reproducible(tmp_path):
    pages = [Page("https://a.test/1", "<p>1</p>"), Page("https://a.test/2", "<p>2</p>")]
    assert write_warc(pages, tmp_path / "a.warc") == write_warc(pages[::-1], tmp_path / "b.warc")


def test_adversarial_url_roundtrip():
    url = adversarial_url("https://a.test/p", "F2", "T01")
    assert is_adversarial_url(url)
    assert is_adversarial_url(url, "F2")
    assert not is_adversarial_url(url, "F1")
    assert not is_adversarial_url("https://a.test/p")
