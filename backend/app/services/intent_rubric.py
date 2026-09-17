"""意图 rubric 层（R6）。

参考项目 cheat-on-content 的核心主张是「**rubric 是循环的内容，不是循环本身**」——
换内容形态只需换 rubric，方法论不变。TopicAI 之前把三个意图连同它们的
问题 / 素材清单 / 预期反应 / 观察信号写死在 `intent_orchestrator.py` 里，
于是「三个选项太少」「成果展示类被问转折」这类问题只能靠改代码解决。

本模块把它变成**一处可扩展的数据定义**：

- 新增一种内容形态＝在这里加一条（或在未来改成从配置/数据库加载），
  而不是改状态机；
- 每条 rubric 显式声明 `narrative_arc`（这条内容里是否"有一个转折/顿悟"）。
  当前它作为**形态元数据**记录在案：现有三类里 solve 无转折、share/record 有；
  今天「展示作品被问转折」是由"推断问题优先于兜底问题"解决的（见 _action_spec），
  而这一字段为下一批形态（如纯展示/清单型）提供判定依据，避免再往状态机里写 if；
- `question` 仍然只是**兜底问题**：模型能针对当前材料推断出更具体的问题时，
  优先用推断的那个（见 `intent_orchestrator._action_spec`）。

边界（刻意不做的事）：这里只做"可扩展 + 显式维度"，不引入用户自定义 rubric 的
写接口——那需要配额、版本与审核，属下一阶段。
"""

from typing import Any, TypedDict


class IntentRubric(TypedDict):
    """一种内容形态的完整定义。"""

    #: 展示给用户的中文名
    label: str
    #: 兜底问题（模型推断不出更具体问题时使用）
    question: str
    #: 这类内容需要哪些真实素材
    materials: list[str]
    #: 预期读者反应
    responses: list[str]
    #: 发布后观察什么信号
    signals: list[str]
    #: 这条内容里是否存在"转折/顿悟"——决定叙事型问题是否成立
    narrative_arc: bool


INTENT_RUBRIC: dict[str, IntentRubric] = {
    "solve": {
        # Step 3：这三个 label 是**机器模式**的名字，不再是内容分类的名字。
        # 它们决定 AI 问什么、要哪些材料、看哪些信号（见 content_genome 的
        # 规则适用性匹配）；内容本身是什么由 content_form 那个开放字段说。
        "label": "教方法",
        "question": "你亲自解决过这个问题的哪一步最容易被忽略？",
        "materials": ["真实问题场景", "本人使用的方法", "一个结果或限制"],
        "responses": ["收藏", "关注", "问题型评论"],
        "signals": ["favorites", "follows_gained", "question_comments"],
        "narrative_arc": False,
    },
    "share": {
        "label": "讲经历",
        # 兜底问题按"有转折"写——因为推断不可用时它是最常见的分享形态；
        # 成果展示类（narrative_arc=False）由模型推断出的问题覆盖。
        "question": "这段经历里，哪个瞬间改变了你的看法或感受？",
        "materials": ["真实事件", "当时的感受或观点", "形成这一理解的原因"],
        "responses": ["共鸣评论", "有质量的互动", "关注"],
        "signals": ["resonance_comments", "interaction_quality", "follows_gained"],
        "narrative_arc": True,
    },
    "record": {
        "label": "记过程",
        "question": "这次变化开始前是什么状态，现在最具体的变化是什么？",
        "materials": ["起点证据", "过程片段", "转折", "当前结果"],
        "responses": ["持续关注", "追问进展", "系列期待"],
        "signals": ["completion", "returning_readers", "series_continuation"],
        "narrative_arc": True,
    },
}

#: 尚未确定意图时的中性配置：每个字段都保持中性，绝不暗示用户没选过的意图。
UNRESOLVED_INTENT_RUBRIC: IntentRubric = {
    "label": "",
    "question": "这条内容里，哪个真实信息最关键？",
    "materials": [],
    "responses": [],
    "signals": [],
    "narrative_arc": False,
}


def rubric_for(intent: str | None) -> dict[str, Any]:
    """取某意图的 rubric；未知或未定意图返回中性配置。"""
    if not intent:
        return dict(UNRESOLVED_INTENT_RUBRIC)
    return dict(INTENT_RUBRIC.get(intent, UNRESOLVED_INTENT_RUBRIC))
