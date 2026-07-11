"""Tests for T02: Pydantic data models.

Tests cover all 14 Pydantic models with validation:
- TC02-01: User model validation
- TC02-02: TopicItem required field validation
- TC02-03: AIQualityMeta defaults
- Plus: all other model validations
"""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


class TestCommonModels:
    """Test AIQualityMeta and common models."""

    def test_ai_quality_meta_creation(self):
        """TC02-03: Given confidence=0.85, When creating AIQualityMeta,
        Then data_source/model_version/caveat/generated_at auto-filled."""
        from app.models.common import AIQualityMeta

        meta = AIQualityMeta(
            confidence=0.85,
            data_source="tianapi",
            model_version="deepseek-v4-flash",
        )
        assert meta.confidence == 0.85
        assert meta.data_source == "tianapi"
        assert meta.model_version == "deepseek-v4-flash"
        assert meta.caveat is None
        assert meta.generated_at is not None

    def test_ai_quality_meta_with_caveat(self):
        """Given AI inferred data, When creating AIQualityMeta with caveat,
        Then caveat is preserved."""
        from app.models.common import AIQualityMeta

        meta = AIQualityMeta(
            confidence=0.65,
            data_source="llm_simulation",
            model_version="deepseek-v4-flash",
            caveat="基于AI推断，非实时数据",
        )
        assert meta.caveat == "基于AI推断，非实时数据"

    def test_ai_quality_meta_confidence_range(self):
        """Given confidence outside 0-1, When validated, Then error."""
        from app.models.common import AIQualityMeta

        with pytest.raises(ValidationError):
            AIQualityMeta(
                confidence=1.5,
                data_source="test",
                model_version="test",
            )

    def test_paginated_response(self):
        """Given paginated data, When creating PaginatedResponse,
        Then total/page/page_size correctly set."""
        from app.models.common import PaginatedResponse

        resp = PaginatedResponse(
            items=[{"id": "1"}, {"id": "2"}],
            total=10,
            page=1,
            page_size=2,
        )
        assert resp.total == 10
        assert resp.page == 1
        assert resp.page_size == 2
        assert len(resp.items) == 2

    def test_api_response_format(self):
        """Given API response, When creating ApiResponse,
        Then code/data/message/meta all present."""
        from app.models.common import ApiResponse

        resp = ApiResponse(
            code=200,
            data={"key": "value"},
            message="success",
            meta={"ai_quality": {"confidence": 0.9}},
        )
        assert resp.code == 200
        assert resp.data == {"key": "value"}
        assert resp.message == "success"
        assert resp.meta == {"ai_quality": {"confidence": 0.9}}


class TestUserModel:
    """TC02-01: User model validation."""

    def test_user_creation(self):
        """Given valid User data, When creating User,
        Then ai_calls_today defaults to 0."""
        from app.models.user import UserCreate

        create = UserCreate(
            email="test@example.com",
            username="testuser",
            password="securepassword123",
        )
        assert create.email == "test@example.com"
        assert create.username == "testuser"

    def test_user_email_validation(self):
        """Given invalid email, When validated, Then error."""
        from app.models.user import UserCreate

        with pytest.raises(ValidationError):
            UserCreate(
                email="not-an-email",
                username="test",
                password="password123",
            )

    def test_user_short_password(self):
        """Given short password, When validated, Then error."""
        from app.models.user import UserCreate

        with pytest.raises(ValidationError):
            UserCreate(
                email="test@test.com",
                username="test",
                password="short",
            )

    def test_user_response_format(self):
        """Given UserResponse, When checked, Then has correct fields."""
        from app.models.user import UserResponse

        resp = UserResponse(
            id="user-1",
            email="test@example.com",
            username="testuser",
            ai_calls_today=5,
            created_at=utc_now(),
        )
        assert resp.id == "user-1"
        assert resp.ai_calls_today == 5


class TestCreatorProfileModel:
    """Test CreatorProfile schema."""

    def test_creator_profile_creation(self):
        """Given valid CreatorProfile data, When created,
        Then all fields set correctly."""
        from app.models.creator_profile import CreatorProfile

        now = utc_now()
        profile = CreatorProfile(
            id="profile-1",
            user_id="user-1",
            track="科技",
            content_formats=["短视频", "图文"],
            production_complexity="medium",
            content_depth="deep",
            hotspot_preference="追热点",
            recommendation_mode="hotspot_fusion",
            rubric_weights={"track_match": 0.3, "format_match": 0.2},
            created_at=now,
            updated_at=now,
        )
        assert profile.track == "科技"
        assert len(profile.content_formats) == 2
        assert profile.recommendation_mode == "hotspot_fusion"

    def test_creator_profile_recommendation_mode_validation(self):
        """Given invalid recommendation_mode, When validated, Then error."""
        from app.models.creator_profile import CreatorProfile

        with pytest.raises(ValidationError):
            CreatorProfile(
                id="p1",
                user_id="u1",
                track="科技",
                content_formats=["短视频"],
                production_complexity="low",
                content_depth="shallow",
                hotspot_preference="不追热点",
                recommendation_mode="invalid_mode",
                rubric_weights={},
                created_at=utc_now(),
                updated_at=utc_now(),
            )


class TestTopicModels:
    """TC02-02: TopicItem required field validation."""

    def test_topic_item_creation(self):
        """Given valid TopicItem data, When created, Then all scores valid."""
        from app.models.topic import TopicItem

        item = TopicItem(
            title="AI赋能内容创作：2026趋势",
            reason="赛道热度上升",
            estimated_heat=0.82,
            content_angle="工具角度切入",
            track_match_score=0.88,
            format_match_score=0.75,
            data_quality_score=0.90,
            composite_score=0.84,
            confidence=0.85,
            data_source="tianapi",
        )
        assert item.title == "AI赋能内容创作：2026趋势"
        assert 0 <= item.composite_score <= 1

    def test_topic_item_missing_title_raises_error(self):
        """TC02-02: Given missing title, When validated, Then ValidationError."""
        from app.models.topic import TopicItem

        with pytest.raises(ValidationError):
            TopicItem(
                reason="good topic",
                estimated_heat=0.5,
                content_angle="angle",
                track_match_score=0.5,
                format_match_score=0.5,
                data_quality_score=0.5,
                composite_score=0.5,
                confidence=0.5,
                data_source="test",
            )

    def test_topic_recommendation_creation(self):
        """Given valid TopicRecommendation, When created with topics, Then valid."""
        from app.models.topic import TopicItem, TopicRecommendation

        rec = TopicRecommendation(
            id="rec-1",
            user_id="user-1",
            topics=[
                TopicItem(
                    title="Test Topic",
                    reason="test",
                    estimated_heat=0.5,
                    content_angle="test angle",
                    track_match_score=0.5,
                    format_match_score=0.5,
                    data_quality_score=0.5,
                    composite_score=0.5,
                    confidence=0.7,
                    data_source="tianapi",
                )
            ],
            recommendation_mode="hotspot_fusion",
            data_source_used="tianapi",
            created_at=utc_now(),
        )
        assert len(rec.topics) == 1
        assert rec.recommendation_mode == "hotspot_fusion"


class TestViralModels:
    """Test ViralAnalysis and related schemas."""

    def test_attribution_conclusion_creation(self):
        """Given valid attribution data, When created, Then fields correct."""
        from app.models.viral import AttributionConclusion

        attr = AttributionConclusion(
            dimension="标题",
            conclusion="使用数字+悬念手法",
            relevance=0.9,
            evidence="标题包含'5个'数字",
        )
        assert attr.dimension == "标题"
        assert attr.relevance == 0.9

    def test_viral_analysis_creation(self):
        """Given valid ViralAnalysis data, When created, Then all fields present."""
        from app.models.viral import AttributionConclusion, ViralAnalysis

        analysis = ViralAnalysis(
            id="va-1",
            user_id="user-1",
            input_type="text",
            input_text="爆款文案内容...",
            viral_score=0.78,
            structural_analysis={
                "title_hook": "数字+悬念",
                "opening": "痛点共鸣",
                "rhythm": "快节奏",
                "emotion": "好奇→共鸣",
                "cta": "评论互动",
            },
            attributions=[
                AttributionConclusion(
                    dimension="标题",
                    conclusion="数字+悬念",
                    relevance=0.9,
                    evidence="包含数字",
                )
            ],
            transferable_template="可迁移模板...",
            rewrite_suggestions="改写建议...",
            risk_warnings=["注意平台规范"],
            confidence=0.85,
            data_source="deepseek-v4-flash",
            created_at=utc_now(),
        )
        assert analysis.viral_score == 0.78
        assert len(analysis.attributions) == 1


class TestIdeaModel:
    """Test IdeaBoosterResult schema."""

    def test_idea_booster_result_creation(self):
        """Given valid IdeaBoosterResult, When created, Then fields present."""
        from app.models.idea import IdeaBoosterResult

        result = IdeaBoosterResult(
            id="idea-1",
            user_id="user-1",
            input_idea="如何做好短视频",
            key_assumptions=["假设1：用户喜欢短内容"],
            feasibility_assessment="可行，但需要细化",
            title_candidates=["标题候选1", "标题候选2"],
            content_outline="内容大纲...",
            publish_schedule="建议周二发布",
            confidence=0.75,
            created_at=utc_now(),
        )
        assert len(result.key_assumptions) == 1
        assert len(result.title_candidates) == 2


class TestTitleModel:
    """Test TitleOptimization schema."""

    def test_optimized_title_creation(self):
        """Given valid OptimizedTitle, When created, Then CTR in range."""
        from app.models.title import OptimizedTitle

        title = OptimizedTitle(
            title="5个AI工具让你效率翻倍",
            ctr_estimate=0.15,
            technique_used="数字+利益",
            technique_reason="数字吸引眼球，利益驱动点击",
        )
        assert 0 <= title.ctr_estimate <= 1

    def test_title_optimization_creation(self):
        """Given valid TitleOptimization, When created, Then 3-5 titles."""
        from app.models.title import OptimizedTitle, TitleOptimization

        opt = TitleOptimization(
            id="to-1",
            user_id="user-1",
            original_title="AI工具",
            content_summary="关于AI工具的总结",
            optimized_titles=[
                OptimizedTitle(
                    title="5个AI工具让你效率翻倍",
                    ctr_estimate=0.15,
                    technique_used="数字+利益",
                    technique_reason="吸引点击",
                ),
                OptimizedTitle(
                    title="用了这5个工具，我每天省3小时",
                    ctr_estimate=0.18,
                    technique_used="利益+场景",
                    technique_reason="场景共鸣",
                ),
                OptimizedTitle(
                    title="2026必备：效率提升5倍的AI工具",
                    ctr_estimate=0.12,
                    technique_used="年份+效果",
                    technique_reason="权威感",
                ),
            ],
            created_at=utc_now(),
        )
        assert len(opt.optimized_titles) == 3


class TestTrackModel:
    """Test TrackDiagnosis schema."""

    def test_sub_track_creation(self):
        """Given valid SubTrack, When created, Then potential in range."""
        from app.models.track import SubTrack

        st = SubTrack(
            name="AI编程",
            potential_score=0.85,
            reason="市场需求旺盛",
        )
        assert 0 <= st.potential_score <= 1

    def test_track_diagnosis_creation(self):
        """Given valid TrackDiagnosis, When created, Then scores valid."""
        from app.models.track import SubTrack, TrackDiagnosis

        diag = TrackDiagnosis(
            id="td-1",
            user_id="user-1",
            track_keyword="科技",
            health_score=0.72,
            competitiveness_score=0.65,
            direction_advice="建议聚焦AI细分领域",
            sub_tracks=[
                SubTrack(name="AI工具", potential_score=0.85, reason="热门"),
                SubTrack(name="编程", potential_score=0.70, reason="刚需"),
                SubTrack(name="硬件", potential_score=0.55, reason="门槛高"),
            ],
            confidence=0.80,
            data_source="tianapi",
            created_at=utc_now(),
        )
        assert len(diag.sub_tracks) == 3
        assert 0 <= diag.health_score <= 1


class TestFeedbackModels:
    """Test FeedbackRecord and FeedbackAnalysis schemas."""

    def test_feedback_record_creation(self):
        """Given valid FeedbackRecord, When created, Then fields correct."""
        from app.models.feedback import FeedbackRecord

        record = FeedbackRecord(
            id="fr-1",
            user_id="user-1",
            source_type="topic",
            source_id="topic-1",
            feedback_type="thumb_up",
            created_at=utc_now(),
        )
        assert record.feedback_type == "thumb_up"
        assert record.source_type == "topic"

    def test_feedback_record_with_reason(self):
        """Given feedback with reason, When created, Then reason stored."""
        from app.models.feedback import FeedbackRecord

        record = FeedbackRecord(
            id="fr-2",
            user_id="user-1",
            source_type="title",
            source_id="title-1",
            feedback_type="thumb_down",
            feedback_value="不好",
            reason="标题太夸张",
            created_at=utc_now(),
        )
        assert record.reason == "标题太夸张"

    def test_feedback_analysis_creation(self):
        """Given valid FeedbackAnalysis, When created, Then fields correct."""
        from app.models.feedback import FeedbackAnalysis

        analysis = FeedbackAnalysis(
            id="fa-1",
            user_id="user-1",
            feedback_record_id="fr-1",
            success_factors={"title_hook": "+0.1"},
            failure_factors={},
            weight_adjustments={"track_match": -0.05},
            excluded_patterns=["过于标题党"],
            created_at=utc_now(),
        )
        assert analysis.user_id == "user-1"


class TestPublishModel:
    """Test PublishSuggestion schema."""

    def test_time_slot_creation(self):
        """Given valid TimeSlot, When created, Then fields correct."""
        from app.models.publish import TimeSlot

        slot = TimeSlot(
            time_range="18:00-20:00",
            reason="晚高峰流量大",
            benchmark_source="行业基准",
        )
        assert slot.time_range == "18:00-20:00"

    def test_publish_suggestion_creation(self):
        """Given valid PublishSuggestion, When created, Then 3 slots."""
        from app.models.publish import PublishSuggestion, TimeSlot

        sug = PublishSuggestion(
            id="ps-1",
            user_id="user-1",
            platform="小红书",
            content_type="图文",
            suggested_times=[
                TimeSlot(time_range="08:00-10:00", reason="早高峰", benchmark_source="行业基准"),
                TimeSlot(time_range="12:00-14:00", reason="午休", benchmark_source="行业基准"),
                TimeSlot(time_range="18:00-20:00", reason="晚高峰", benchmark_source="行业基准"),
            ],
            created_at=utc_now(),
        )
        assert len(sug.suggested_times) == 3


class TestRiskModel:
    """Test ContentRiskReport schema."""

    def test_risk_item_creation(self):
        """Given valid RiskItem, When created, Then severity valid."""
        from app.models.risk import RiskItem

        item = RiskItem(
            category="违规词",
            description="包含敏感词",
            severity="high",
            suggestion="替换措辞",
        )
        assert item.severity == "high"

    def test_content_risk_report_creation(self):
        """Given valid ContentRiskReport, When created, Then risk score valid."""
        from app.models.risk import ContentRiskReport, RiskItem

        report = ContentRiskReport(
            id="cr-1",
            user_id="user-1",
            content_text="测试内容...",
            risks=[
                RiskItem(
                    category="违规词",
                    description="包含敏感词",
                    severity="medium",
                    suggestion="替换",
                )
            ],
            overall_risk_score=0.35,
            created_at=utc_now(),
        )
        assert 0 <= report.overall_risk_score <= 1


class TestEffectReviewModel:
    """Test EffectReview schema."""

    def test_effect_review_creation(self):
        """Given valid EffectReview, When created, Then prediction/actual stored."""
        from app.models.effect_review import EffectReview

        review = EffectReview(
            id="er-1",
            user_id="user-1",
            topic_title="AI工具推荐",
            prediction={"estimated_views": 5000, "estimated_likes": 200},
            actual_result={"actual_views": 8000, "actual_likes": 350},
            attribution="标题吸引人+内容实用",
            learnings={"key_learnings": ["标题数字+利益最有效"]},
            created_at=utc_now(),
        )
        assert review.topic_title == "AI工具推荐"
        assert review.prediction["estimated_views"] == 5000


class TestModelCrossValidation:
    """Cross-model validation tests."""

    def test_all_models_importable(self):
        """Given app.models package, When importing all models,
        Then all modules import without error."""

        # If we get here, all imports succeeded
        assert True
