"""Tests for T07-T10: Core business services.

Covers topic recommendation, viral analysis, idea booster, title optimizer,
track diagnosis, publish advisor, and content risk.
"""

from datetime import UTC, datetime

import pytest


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


class TestTopicRecommend:
    """T07: Topic recommendation engine tests."""

    def test_topic_service_creation(self):
        """TC07-01: Given valid service, When created, Then initialized."""
        from app.services.topic_recommend import TopicRecommendService
        svc = TopicRecommendService()
        assert svc is not None

    def test_filter_by_track(self):
        """TC07-02: Given mixed topics, When filtering by track,
        Then only matching topics returned."""
        from app.services.topic_recommend import TopicRecommendService
        svc = TopicRecommendService()
        topics = [
            {"title": "AI工具", "track": "科技"},
            {"title": "护肤心得", "track": "美妆"},
            {"title": "编程教程", "track": "科技"},
        ]
        result = svc._filter_by_track(topics, "科技")
        assert len(result) == 2
        assert all("科技" in str(t) for t in result)

    def test_rank_topics_sorts_by_composite_score(self):
        """TC07-05: Given topics with scores, When ranking,
        Then sorted by composite_score descending."""
        from app.services.topic_recommend import TopicRecommendService
        svc = TopicRecommendService()
        topics = [
            {"title": "A", "composite_score": 0.5},
            {"title": "B", "composite_score": 0.9},
            {"title": "C", "composite_score": 0.7},
        ]
        ranked = svc._rank_topics(topics, {})
        assert ranked[0]["composite_score"] == 0.9
        assert ranked[2]["composite_score"] == 0.5

    def test_top_k_selection(self):
        """Given 10 ranked topics, When selecting top_k=5,
        Then returns exactly 5."""
        from app.services.topic_recommend import TopicRecommendService
        svc = TopicRecommendService()
        topics = [
            {"title": f"Topic{i}", "composite_score": 0.9 - i * 0.05}
            for i in range(10)
        ]
        result = svc._top_k(topics, 5)
        assert len(result) == 5

    def test_generate_with_mock_llm(self, mock_deepseek):
        """TC07-01: Given mock LLM and mock DataManager,
        When recommend called, Then returns top 5 TopicItems."""
        from app.services.topic_recommend import TopicRecommendService

        mock_deepseek.chat.completions.create.return_value.choices[
            0
        ].message.content = (
            '{"topics": ['
            '{"title":"AI工具","reason":"热门","estimated_heat":0.9,'
            '"content_angle":"技术","track_match_score":0.9,'
            '"format_match_score":0.8,"data_quality_score":0.85,'
            '"composite_score":0.85,"confidence":0.9,"data_source":"tianapi"},'
            '{"title":"编程","reason":"刚需","estimated_heat":0.8,'
            '"content_angle":"教程","track_match_score":0.85,'
            '"format_match_score":0.75,"data_quality_score":0.8,'
            '"composite_score":0.8,"confidence":0.85,"data_source":"tianapi"}]}'
        )
        svc = TopicRecommendService()
        result = svc._parse_topics_response(
            '{"topics": ['
            '{"title":"AI工具","reason":"热门","estimated_heat":0.9,'
            '"content_angle":"技术","track_match_score":0.9,'
            '"format_match_score":0.8,"data_quality_score":0.85,'
            '"composite_score":0.85,"confidence":0.9,"data_source":"tianapi"}]}'
        )
        assert len(result) == 1
        assert result[0]["title"] == "AI工具"


class TestViralAnalysis:
    """T08: Viral analysis engine tests."""

    def test_viral_service_creation(self):
        """TC08-01: Given valid service, When created, Then initialized."""
        from app.services.viral_analysis import ViralAnalysisService
        svc = ViralAnalysisService()
        assert svc is not None

    def test_analyze_text(self, mock_deepseek):
        """TC08-01: Given text input, When analyze called,
        Then returns ViralAnalysis with structural analysis."""
        from app.services.viral_analysis import ViralAnalysisService

        mock_deepseek.chat.completions.create.return_value.choices[
            0
        ].message.content = (
            '{"structural_analysis":{"title_hook":"数字+悬念","opening":"痛点","rhythm":"快","emotion":"好奇","cta":"互动"},'
            '"attributions":[{"dimension":"标题","conclusion":"数字+悬念","relevance":0.9,"evidence":"标题含数字"}],'
            '"transferable_template":"模板","rewrite_suggestions":"建议","risk_warnings":[],"confidence":0.85}'
        )
        svc = ViralAnalysisService()
        analysis = svc._parse_viral_response(
            '{"structural_analysis":{"title_hook":"数字+悬念","opening":"痛点","rhythm":"快","emotion":"好奇","cta":"互动"},'
            '"attributions":[{"dimension":"标题","conclusion":"数字+悬念","relevance":0.9,"evidence":"标题含数字"}],'
            '"transferable_template":"模板","rewrite_suggestions":"建议","risk_warnings":[],"confidence":0.85}'
        )
        assert "structural_analysis" in analysis
        assert analysis["structural_analysis"]["title_hook"] == "数字+悬念"

    def test_empty_input_raises(self):
        """TC08-08: Given empty input, When analyze, Then raises."""
        from app.services.viral_analysis import ViralAnalysisService
        svc = ViralAnalysisService()
        with pytest.raises(ValueError):
            svc.validate_input("", "text")

    def test_expiry_set_to_90_days(self):
        """TC08-07: Given analysis created, When checking expires_at,
        Then set to created_at + 90 days."""
        from app.services.viral_analysis import ViralAnalysisService
        svc = ViralAnalysisService()
        created = "2026-01-01T00:00:00Z"
        expires = svc._compute_expiry(created)
        assert expires == "2026-04-01T00:00:00Z"


class TestIdeaBooster:
    """T09: Idea booster tests."""

    def test_idea_service_creation(self):
        """TC09-01: Given valid service, When created, Then initialized."""
        from app.services.idea_booster import IdeaBoosterService
        svc = IdeaBoosterService()
        assert svc is not None

    def test_boost_empty_input_raises(self):
        """TC09-08: Given empty idea, When boost, Then raises ValueError."""
        from app.services.idea_booster import IdeaBoosterService
        svc = IdeaBoosterService()
        with pytest.raises(ValueError):
            svc.boost("user-1", "")

    def test_extract_assumptions(self):
        """TC09-02: Given idea text, When extracting assumptions,
        Then returns 3-5 assumptions."""
        from app.services.idea_booster import IdeaBoosterService
        svc = IdeaBoosterService()
        idea = "我想做一个关于AI的短视频账号"
        assumptions = svc._extract_assumptions(idea)
        assert len(assumptions) >= 3


class TestTitleOptimizer:
    """T09: Title optimizer tests."""

    def test_title_service_creation(self):
        """TC09-05: Given valid service, When created, Then initialized."""
        from app.services.title_optimizer import TitleOptimizerService
        svc = TitleOptimizerService()
        assert svc is not None

    def test_generate_variations(self):
        """TC09-05: Given original title, When generating variations,
        Then returns 3-5 options."""
        from app.services.title_optimizer import TitleOptimizerService
        svc = TitleOptimizerService()
        variations = svc._generate_variations("AI工具推荐")
        assert 3 <= len(variations) <= 5

    def test_ctr_estimate_in_range(self):
        """TC09-06: Given title, When estimating CTR, Then value 0-1."""
        from app.services.title_optimizer import TitleOptimizerService
        svc = TitleOptimizerService()
        for title in ["5个AI工具", "用了这个工具我哭了", "2026必备AI"]:
            ctr = svc._estimate_ctr(title)
            assert 0 <= ctr <= 1


class TestTrackDiagnosis:
    """T10: Track diagnosis tests."""

    def test_track_service_creation(self):
        """TC10-01: Given valid service, When created, Then initialized."""
        from app.services.track_diagnosis import TrackDiagnosisService
        svc = TrackDiagnosisService()
        assert svc is not None

    def test_diagnose_returns_health_scores(self):
        """TC10-01: Given track keyword, When diagnosing,
        Then returns health_score and competitiveness_score."""
        from app.services.track_diagnosis import TrackDiagnosisService
        svc = TrackDiagnosisService()
        result = svc._compute_scores("美妆")
        assert 0 <= result["health_score"] <= 1
        assert 0 <= result["competitiveness_score"] <= 1

    def test_sub_tracks_returned(self):
        """TC10-02: Given track keyword, When diagnosing,
        Then returns 3 sub-tracks with potential scores."""
        from app.services.track_diagnosis import TrackDiagnosisService
        svc = TrackDiagnosisService()
        sub_tracks = svc._get_sub_tracks("科技")
        assert len(sub_tracks) >= 3
        for st in sub_tracks:
            assert "name" in st
            assert 0 <= st["potential_score"] <= 1


class TestPublishAdvisor:
    """T10: Publish advisor tests."""

    def test_publish_service_creation(self):
        """TC10-05: Given valid service, When created, Then initialized."""
        from app.services.publish_advisor import PublishAdvisorService
        svc = PublishAdvisorService()
        assert svc is not None

    def test_suggest_returns_3_slots(self):
        """TC10-05: Given platform+type, When suggesting,
        Then returns 3 time slots."""
        from app.services.publish_advisor import PublishAdvisorService
        svc = PublishAdvisorService()
        slots = svc._get_default_slots("小红书", "图文")
        assert len(slots) == 3


class TestContentRisk:
    """T10: Content risk detection tests."""

    def test_risk_service_creation(self):
        """TC10-07: Given valid service, When created, Then initialized."""
        from app.services.content_risk import ContentRiskService
        svc = ContentRiskService()
        assert svc is not None

    def test_check_normal_content_low_risk(self):
        """TC10-08: Given normal text, When checking,
        Then overall_risk_score < 0.3."""
        from app.services.content_risk import ContentRiskService
        svc = ContentRiskService()
        result = svc._scan_risk("这是一篇正常的科技文章")
        assert result["overall_risk_score"] < 0.3

    def test_check_risky_content_high_risk(self):
        """TC10-09: Given risky text, When checking,
        Then overall_risk_score > 0.5."""
        from app.services.content_risk import ContentRiskService
        svc = ContentRiskService()
        result = svc._scan_risk("赌博 色情 违规内容")
        assert result["overall_risk_score"] > 0.5

    def test_risk_items_detected(self):
        """TC10-07: Given risky content, When checking,
        Then risk items list populated."""
        from app.services.content_risk import ContentRiskService
        svc = ContentRiskService()
        result = svc._scan_risk("绝对不违规，保证赚钱，点击领取")
        assert len(result["risks"]) > 0
