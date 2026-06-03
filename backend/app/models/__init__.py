"""Models package for TopicAI v4.0.

Exports all Pydantic models for convenient imports.
"""

from app.models.common import AIQualityMeta, ApiResponse, PaginatedResponse
from app.models.creator_profile import CreatorProfile, OnboardingRequest
from app.models.effect_review import (
    EffectAttributeRequest,
    EffectPredictRequest,
    EffectReview,
)
from app.models.feedback import (
    FeedbackAnalysis,
    FeedbackRecord,
    FeedbackSubmitRequest,
)
from app.models.idea import IdeaBoosterResult, IdeaBoostRequest
from app.models.publish import (
    PublishSuggestion,
    PublishSuggestRequest,
    TimeSlot,
)
from app.models.risk import ContentRiskReport, RiskCheckRequest, RiskItem
from app.models.title import (
    OptimizedTitle,
    TitleOptimization,
    TitleOptimizeRequest,
)
from app.models.topic import TopicItem, TopicRecommendation, TopicRecommendRequest
from app.models.track import SubTrack, TrackDiagnoseRequest, TrackDiagnosis
from app.models.user import TokenPair, UserCreate, UserLogin, UserResponse
from app.models.viral import (
    AttributionConclusion,
    ViralAnalysis,
    ViralAnalyzeRequest,
)

__all__ = [
    # Common
    "AIQualityMeta",
    "ApiResponse",
    "PaginatedResponse",
    # User
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "TokenPair",
    # Creator Profile
    "CreatorProfile",
    "OnboardingRequest",
    # Topic
    "TopicItem",
    "TopicRecommendation",
    "TopicRecommendRequest",
    # Viral
    "ViralAnalysis",
    "AttributionConclusion",
    "ViralAnalyzeRequest",
    # Idea
    "IdeaBoosterResult",
    "IdeaBoostRequest",
    # Title
    "TitleOptimization",
    "OptimizedTitle",
    "TitleOptimizeRequest",
    # Track
    "TrackDiagnosis",
    "SubTrack",
    "TrackDiagnoseRequest",
    # Feedback
    "FeedbackRecord",
    "FeedbackAnalysis",
    "FeedbackSubmitRequest",
    # Publish
    "PublishSuggestion",
    "TimeSlot",
    "PublishSuggestRequest",
    # Risk
    "ContentRiskReport",
    "RiskItem",
    "RiskCheckRequest",
    # Effect Review
    "EffectReview",
    "EffectPredictRequest",
    "EffectAttributeRequest",
]
