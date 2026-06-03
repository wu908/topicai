/** Enum types for TopicAI frontend — aligned with backend Pydantic models */

/** Recommendation mode for topic suggestions */
export type RecommendationMode = 'hotspot_fusion' | 'evergreen_deep';

/** Input type for viral analysis */
export type InputType = 'text' | 'image';

/** Content format options */
export type ContentFormat = 'short_video' | 'long_video' | 'graphic' | 'article' | 'live';

/** Production complexity levels */
export type ProductionComplexity = 'simple' | 'medium' | 'complex';

/** Content depth levels */
export type ContentDepth = 'shallow' | 'moderate' | 'deep';

/** Hotspot preference levels */
export type HotspotPreference = 'chase' | 'selective' | 'avoid';

/** Feedback type */
export type FeedbackType = 'thumb_up' | 'thumb_down' | 'adopted' | 'modified' | 'ignored';

/** Source type for feedback */
export type SourceType = 'topic' | 'viral' | 'title' | 'idea' | 'track' | 'publish';

/** Risk severity levels */
export type RiskSeverity = 'low' | 'medium' | 'high' | 'critical';

/** Data source levels */
export type DataSourceLevel = 'tianapi' | 'bilibili' | 'ai_inference' | 'preloaded';

/** Platform options */
export type Platform = 'xiaohongshu' | 'douyin' | 'bilibili' | 'weibo' | 'toutiao';

/** Health status */
export type HealthStatus = 'healthy' | 'degraded' | 'down';

/** Confidence level */
export type ConfidenceLevel = 'high' | 'medium' | 'low';

/** LLM Provider */
export type LLMProvider = 'deepseek' | 'qwen' | 'glm';

/** User event types */
export type UserEventType = 'page_view' | 'api_call' | 'feedback' | 'feature_use';
