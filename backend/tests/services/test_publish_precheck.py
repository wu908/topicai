"""PublishCheck structural pre-check for deliverables (Spec-013 Phase 1).

The pre-check is the load-bearing quality gate for autonomous production:
hook / points / ending must exist in the outline, the body must reference
the user's facts, and at least one traceable fact must be present.
"""


from app.services.async_loop import PublishCheckService


def _draft(title="阳台种菜 30 天",
           body="开头讲翻车：第 12 天差点全军覆没。\n中间讲方法：换置物架并人工授粉。\n"
                "结尾问读者：你的辣椒活了吗？",
           outline=None, facts=None):
    return {
        "title": title,
        "body_text": body,
        "outline": outline if outline is not None else [
            {"step": "hook", "label": "钩子"},
            {"step": "point", "label": "要点"},
            {"step": "ending", "label": "结尾互动"},
        ],
        "facts": facts if facts is not None else [
            {"statement": "辣椒在北阳台活了", "source_inbox_id": "i1"},
        ],
    }


def test_clean_draft_passes_all_checks():
    report = PublishCheckService.run_precheck(_draft())
    assert report["passed"] is True
    assert report["issues"] == []


def test_missing_ending_fails():
    draft = _draft(outline=[
        {"step": "hook", "label": "钩子"},
        {"step": "point", "label": "要点"},
    ])
    report = PublishCheckService.run_precheck(draft)
    assert report["passed"] is False
    assert any("结尾" in issue for issue in report["issues"])


def test_short_body_fails():
    report = PublishCheckService.run_precheck(_draft(body="太短"))
    assert report["passed"] is False
    assert any("正文" in issue for issue in report["issues"])


def test_no_facts_fails():
    report = PublishCheckService.run_precheck(_draft(facts=[]))
    assert report["passed"] is False
    assert any("事实" in issue for issue in report["issues"])


def test_empty_title_fails():
    report = PublishCheckService.run_precheck(_draft(title="  "))
    assert report["passed"] is False
    assert any("标题" in issue for issue in report["issues"])
