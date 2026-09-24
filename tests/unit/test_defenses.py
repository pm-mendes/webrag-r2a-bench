import pytest

from webrag_bench.core.tasks import Task
from webrag_bench.defenses import PENDING_DEFENSES, ToolCall, UnspecifiedDefense, get_defense

TASK = Task("T", "r", "open", "https://a.test", {"tool": "x.y", "arguments": {}}, ("mail.send",))


@pytest.mark.parametrize("name", PENDING_DEFENSES)
def test_unspecified_defenses_are_not_approximated(name):
    with pytest.raises(UnspecifiedDefense):
        get_defense(name)


def test_allowlist_demo():
    d = get_defense("tool-allowlist-demo")
    assert d.authorize(ToolCall("mail.send", {}), TASK)
    assert not d.authorize(ToolCall("bank.transfer", {}), TASK)
