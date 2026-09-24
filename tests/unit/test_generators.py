from webrag_bench.generators import StubGenerator

TOOLS = [{"name": "mail.send", "description": "", "schema": {}}]


def test_stub_obeys_call_lines_for_known_tools_only():
    g = StubGenerator("stub", "stub-0")
    r = g.generate("", 'CALL mail.send {"to": "x"} and CALL bank.transfer {"iban": "y"}', TOOLS)
    assert [(c.tool, c.arguments) for c in r.calls] == [("mail.send", {"to": "x"})]
    assert r.returned_model_id == "stub-0"
