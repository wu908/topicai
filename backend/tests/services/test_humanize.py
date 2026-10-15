"""人话化 post-process：保事实、默认开、可关、无模型时原样返回（P2-B1/P2-F3）。"""

from app.services.humanize import HumanizeService


class _FakeLLM:
    def __init__(self, reply: str = "改后的更像人话的稿子。"):
        self.reply = reply
        self.calls: list[tuple[str, str | None]] = []

    def generate(self, prompt, system_prompt=None, **kwargs):
        self.calls.append((prompt, system_prompt))
        return self.reply

    def is_available(self, capability: str = "text") -> bool:
        return True


class _NoLLM:
    def generate(self, *a, **k):
        raise AssertionError("should not call LLM when unavailable")

    def is_available(self, capability: str = "text") -> bool:
        return False


def test_humanize_rewrites_ai_sounding_draft():
    llm = _FakeLLM("番茄钟挪到第二天早上，反而更容易坚持。")
    svc = HumanizeService(llm=llm)
    out = svc.rewrite("基于数据分析，番茄钟优化方案可提升效率。建议执行。")
    assert out == "番茄钟挪到第二天早上，反而更容易坚持。"
    assert llm.calls, "should call LLM"
    prompt, system = llm.calls[0]
    assert "番茄钟" in prompt
    assert system and "事实" in system


def test_humanize_prompt_forbids_fabrication_and_lists_numbers():
    llm = _FakeLLM("ok")
    svc = HumanizeService(llm=llm)
    svc.rewrite("收藏 45，点赞 32，连续 3 周更新。")
    _, system = llm.calls[0]
    assert "不得编造" in system or "不编造" in system
    assert "数字" in system
    # 原文数字必须出现在给模型的输入里（保事实前提）
    prompt, _ = llm.calls[0]
    assert "45" in prompt and "32" in prompt and "3" in prompt


def test_humanize_returns_original_when_llm_missing():
    svc = HumanizeService(llm=_NoLLM())
    src = "原文不动。"
    assert svc.rewrite(src) == src


def test_humanize_returns_original_when_disabled():
    llm = _FakeLLM()
    svc = HumanizeService(llm=llm, enabled=False)
    src = "关掉就不改。"
    assert svc.rewrite(src) == src
    assert not llm.calls


def test_humanize_default_enabled():
    assert HumanizeService(llm=_FakeLLM()).enabled is True
    assert HumanizeService(llm=_FakeLLM(), enabled=None).enabled is True


def test_humanize_handles_empty_and_blank():
    svc = HumanizeService(llm=_FakeLLM())
    assert svc.rewrite("") == ""
    assert svc.rewrite("   ") == "   "


def test_humanize_falls_back_on_llm_error():
    class _Boom:
        def generate(self, *a, **k):
            raise RuntimeError("boom")

        def is_available(self, capability: str = "text") -> bool:
            return True

    src = "原稿。"
    assert HumanizeService(llm=_Boom()).rewrite(src) == src
