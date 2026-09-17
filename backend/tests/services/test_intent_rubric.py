"""意图 rubric 层（创建流程重构 R6）。

这里守的是**数据不变式**，而不是某次交互的结果：只要有人在 rubric 里新增
一种内容形态，下面的断言就会替我们检查他有没有把"这条内容有没有转折"想清楚。
"""

import pytest

from app.services.intent_orchestrator import INTENT_CONFIG
from app.services.intent_rubric import INTENT_RUBRIC, UNRESOLVED_INTENT_RUBRIC, rubric_for

_REQUIRED_KEYS = {"label", "question", "materials", "responses", "signals", "narrative_arc"}

#: 只有"读者读完这一句就能动手"的问题才真的需要这条内容里有转折。
#: 一句话里出现这些词，就说明问的人在假设用户经历过一个改变。
_ARC_PRESUPPOSING_MARKERS = ("改变了你的看法", "哪个瞬间", "顿悟", "转折")


def test_every_intent_declares_the_full_shape():
    for intent, rubric in INTENT_RUBRIC.items():
        assert set(rubric) == _REQUIRED_KEYS, intent
        assert rubric["label"].strip(), intent
        assert rubric["question"].strip(), intent
        assert isinstance(rubric["narrative_arc"], bool), intent


@pytest.mark.parametrize("intent", sorted(INTENT_RUBRIC))
def test_an_arc_question_is_only_asked_where_there_is_an_arc(intent):
    """兜底问题里预设了"转折/顿悟"的意图，必须显式声明 narrative_arc。

    这正是「展示作品被问转折」在数据层就该被拦下的地方：展示类内容没有转折，
    却沿用了按"有转折"写的兜底问题。今天这一层由"推断问题优先"兜住，这条断言
    保证下一个新增形态不会重复同一个错误。
    """
    rubric = INTENT_RUBRIC[intent]
    presupposes_arc = any(marker in rubric["question"] for marker in _ARC_PRESUPPOSING_MARKERS)
    if presupposes_arc:
        assert rubric["narrative_arc"] is True, (
            f"{intent} 的兜底问题在问一个转折，但它声明自己没有转折——"
            "要么改问题，要么把 narrative_arc 改成 True"
        )


def test_unknown_and_unset_intent_stay_neutral():
    """未定意图时每个字段都必须中性：动作不能暗示用户没选过的意图。"""
    for intent in (None, "", "solve_but_typo", "solve "):
        rubric = rubric_for(intent)
        assert rubric["label"] == ""
        assert rubric["materials"] == []
        assert rubric["responses"] == []
        assert rubric["signals"] == []
        assert rubric["narrative_arc"] is False
        assert rubric["question"] == UNRESOLVED_INTENT_RUBRIC["question"]
        # 中性兜底问题本身也不能预设转折——它面向"还不知道要写什么"的用户。
        assert not any(
            marker in rubric["question"] for marker in _ARC_PRESUPPOSING_MARKERS
        )


def test_known_intent_returns_its_own_rubric():
    assert rubric_for("record")["label"] == "记过程"
    assert rubric_for("record")["question"] == INTENT_RUBRIC["record"]["question"]


def test_rubric_for_hands_out_copies():
    """调用方拿到的是副本：就地改它不该污染全局那一条。"""
    rubric = rubric_for("solve")
    rubric["question"] = "被改掉了"
    assert INTENT_RUBRIC["solve"]["question"] != "被改掉了"


def test_intent_config_alias_still_points_at_the_rubric():
    """intent_actions 仍从 orchestrator 导入 INTENT_CONFIG——别把兼容别名删了。"""
    assert INTENT_CONFIG is INTENT_RUBRIC
