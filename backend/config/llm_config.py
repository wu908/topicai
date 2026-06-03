"""LLM Provider configuration for TopicAI v4.0.

Defines provider endpoints, model versions, and function tier degradation
strategy. All model versions are pinned to specific versions — no 'latest' aliases.
"""

from typing import Any

# ==================== LLM Provider Configuration ====================
# Each provider has: base_url, default_model, api_key_env, and optional models.

LLM_PROVIDERS: dict[str, dict[str, Any]] = {
    "deepseek": {
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com",
        "default_model": "deepseek-v4-flash",
        "pro_model": "deepseek-v4-pro",
        "api_key_env": "DEEPSEEK_API_KEY",
        "concurrency": 2500,
        "sdk_type": "openai",
        "description": "Primary LLM provider. Flash for daily tasks, Pro for deep thinking.",
        "timeout_seconds": 60,
        "max_retries": 2,
        "models": {
            "flash": "deepseek-v4-flash",
            "pro": "deepseek-v4-pro",
        },
    },
    "qwen": {
        "name": "Qwen (阿里云百炼)",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "default_model": "qwen-plus",
        "turbo_model": "qwen-turbo",
        "max_model": "qwen-max",
        "api_key_env": "DASHSCOPE_API_KEY",
        "sdk_type": "openai",
        "description": "Hot standby provider. Switches automatically when DeepSeek is unavailable.",
        "timeout_seconds": 60,
        "max_retries": 2,
        "models": {
            "plus": "qwen-plus",
            "turbo": "qwen-turbo",
            "max": "qwen-max",
        },
    },
    "glm": {
        "name": "GLM-5V-Turbo (智谱)",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "default_model": "glm-5v-turbo",
        "api_key_env": "ZHIPU_API_KEY",
        "sdk_type": "zhipuai",
        "description": "Vision-capable model for image analysis. 200K context, 128K output.",
        "timeout_seconds": 120,
        "max_retries": 2,
        "modality_limit": (
            "Only one non-text modality (image/video/file) per request."
        ),
        "models": {
            "vision": "glm-5v-turbo",
        },
    },
}

# ==================== Function Tier Degradation Strategy ====================
# Based on Appendix B of the architecture document.

FUNCTION_TIERS: dict[str, dict[str, Any]] = {
    "core": {
        "name": "核心功能",
        "functions": [
            "topic_recommend",
            "viral_analysis",
            "creator_profile",
            "effect_review",
        ],
        "primary_provider": "deepseek",
        "fallback": "qwen",
        "fallback_action": "switch_to_qwen",
        "description": "DeepSeek不可用时自动切换Qwen热备",
    },
    "auxiliary": {
        "name": "辅助功能",
        "functions": [
            "idea_booster",
            "title_optimizer",
            "track_diagnosis",
            "publish_advisor",
        ],
        "primary_provider": "deepseek",
        "fallback": "degraded",
        "fallback_action": "show_degraded_message",
        "degraded_message": "AI暂时休息，请稍后重试",
        "description": "DeepSeek不可用时显示降级提示",
    },
    "decorative": {
        "name": "装饰功能",
        "functions": [
            "content_risk_check",
            "data_quality_scoring",
        ],
        "primary_provider": "deepseek",
        "fallback": "hidden",
        "fallback_action": "hide_feature",
        "description": "DeepSeek不可用时静默隐藏",
    },
}

# ==================== Default LLM Parameters ====================

DEFAULT_LLM_PARAMS: dict[str, Any] = {
    "temperature": 0.7,
    "max_tokens": 4096,
    "top_p": 0.9,
    "presence_penalty": 0.0,
    "frequency_penalty": 0.0,
}

DEEP_THINKING_PARAMS: dict[str, Any] = {
    "temperature": 0.3,
    "max_tokens": 8192,
    "top_p": 0.8,
    "extra_body": {
        "thinking": {"type": "enabled"},
        "reasoning_effort": "high",
    },
}

# ==================== Helper Functions ====================


def get_provider_config(provider_name: str) -> dict[str, Any]:
    """Get configuration for a specific LLM provider.

    Args:
        provider_name: One of 'deepseek', 'qwen', 'glm'.

    Returns:
        Provider configuration dictionary.

    Raises:
        ValueError: If provider_name is not recognized.
    """
    if provider_name not in LLM_PROVIDERS:
        raise ValueError(
            f"Unknown provider '{provider_name}'. "
            f"Available: {list(LLM_PROVIDERS.keys())}"
        )
    return LLM_PROVIDERS[provider_name]


def get_function_tier(function_name: str) -> str:
    """Determine which tier a function belongs to.

    Args:
        function_name: The name of the function/service.

    Returns:
        Tier name: 'core', 'auxiliary', or 'decorative'.
    """
    for tier_name, tier_config in FUNCTION_TIERS.items():
        if function_name in tier_config["functions"]:
            return tier_name
    return "auxiliary"  # Default to auxiliary if not found


def get_fallback_action(function_name: str) -> dict[str, Any]:
    """Get the fallback action for a given function.

    Args:
        function_name: The name of the function/service.

    Returns:
        Dictionary with fallback action details.
    """
    tier = get_function_tier(function_name)
    tier_config = FUNCTION_TIERS[tier]
    return {
        "tier": tier,
        "fallback": tier_config["fallback"],
        "action": tier_config["fallback_action"],
        "message": tier_config.get("degraded_message", ""),
    }
