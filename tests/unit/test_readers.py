import pytest

from webrag_bench.attacks import Template, inject
from webrag_bench.readers import get_reader, reader_names, reader_version

PAGE = "<html><head></head><body><main><p>text</p></main></body></html>"


@pytest.mark.parametrize("insertion,survives_in", [
    ("visible", {"bs4-text", "bs4-raw", "html2text"}),
    ("comment", {"bs4-raw"}),
    ("css-hidden", {"bs4-text", "bs4-raw", "html2text"}),
    ("alt-attribute", {"bs4-raw", "html2text"}),
])
def test_reader_decides_what_survives(insertion, survives_in):
    template = Template("F1", "t", "DEMO", insertion, "payload {canary}")
    html = inject(PAGE, template, {"tool": "x.y", "arguments": {}}, "CNRTEST")
    for name in ("bs4-text", "bs4-raw", "html2text"):
        assert ("CNRTEST" in get_reader(name)(html)) == (name in survives_in), name


def test_every_reader_reports_its_library_version():
    for name in reader_names():
        assert "==" in reader_version(name)


def test_unknown_reader_is_rejected():
    with pytest.raises(ValueError):
        get_reader("nope")
