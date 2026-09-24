import pytest

from webrag_bench.core.tasks import Task
from webrag_bench.defenses import (
    PENDING_DEFENSES,
    DecisionContext,
    ToolCall,
    UnspecifiedDefenseError,
    get_defense,
)

TASK = Task("T", "r", "open", "https://a.test", {"tool": "x.y", "arguments": {}}, ("mail.send",))


@pytest.mark.parametrize("name", PENDING_DEFENSES)
def test_unspecified_defenses_are_not_approximated(name):
    with pytest.raises(UnspecifiedDefenseError):
        get_defense(name)


def test_allowlist_demo():
    d = get_defense("tool-allowlist-demo")
    assert d.authorize(ToolCall("mail.send", {}), TASK, DecisionContext())
    assert not d.authorize(ToolCall("bank.transfer", {}), TASK, DecisionContext())


def test_provenance_demo_gates_effectful_calls_on_verified_context():
    d = get_defense("provenance-demo")
    ok = DecisionContext(True, ({"verified": True}, {"verified": True}))
    broken = DecisionContext(True, ({"verified": True}, {"verified": False}))
    assert d.authorize(ToolCall("mail.send", {}), TASK, ok)
    assert not d.authorize(ToolCall("mail.send", {}), TASK, broken)
    assert d.authorize(ToolCall("filesystem.read", {}), TASK, broken)  # no effect: allowed
