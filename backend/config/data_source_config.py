"""Data source API configuration for TopicAI v4.0.

Defines TianAPI endpoints, Bilibili API endpoints, and the three-layer
data source pyramid configuration.
"""

from typing import Any

# ==================== TianAPI Configuration ====================
# Free tier: 100 calls/day, 3 QPS, 10 interface slots

TIANAPI_BASE_URL: str = "https://apis.tianapi.com"
TIANAPI_TIMEOUT: float = 10.0
TIANAPI_MAX_RETRIES: int = 2

TIANAPI_ENDPOINTS: list[dict[str, Any]] = [
    {
        "name": "weibohot",
        "path": "/weibohot/index",
        "description": "微博热搜前50条",
        "update_interval_minutes": 30,
        "response_fields": ["hotword", "hotwordnum", "hottag"],
        "is_free": True,
    },
    {
        "name": "nethot",
        "path": "/nethot/index",
        "description": "百度热搜（含趋势变化）",
        "update_interval_minutes": 0,  # Not specified
        "response_fields": ["keyword", "index", "brief", "trend"],
        "is_free": True,
    },
    {
        "name": "douyinhot",
        "path": "/douyinhot/index",
        "description": "抖音热搜前50条",
        "update_interval_minutes": 3,
        "response_fields": ["word", "hotindex", "label"],
        "is_free": True,
    },
    {
        "name": "toutiaohot",
        "path": "/toutiaohot/index",
        "description": "头条热搜",
        "update_interval_minutes": 20,
        "response_fields": ["word", "hotindex"],
        "is_free": True,
    },
    {
        "name": "qqhot",
        "path": "/qqhot/index",
        "description": "腾讯热搜（腾讯新闻+微信生态）",
        "update_interval_minutes": 10,
        "response_fields": ["word", "hotindex"],
        "is_free": True,
    },
    {
        "name": "allhot",
        "path": "/allhot/index",
        "description": "全网热搜（多平台聚合）",
        "update_interval_minutes": 0,  # Not specified
        "response_fields": ["word", "hotindex", "source"],
        "is_free": True,
    },
]

# ==================== Bilibili Configuration ====================
# Free, no authentication required. Rate limit: ≤1 req/sec recommended.

BILIBILI_BASE_URL: str = "https://api.bilibili.com"
BILIBILI_TIMEOUT: float = 10.0

BILIBILI_ENDPOINTS: list[dict[str, Any]] = [
    {
        "name": "popular",
        "url": "https://api.bilibili.com/x/web-interface/popular",
        "description": "B站热门视频列表",
        "params": {"pn": 1, "ps": 50},
    },
    {
        "name": "ranking",
        "url": "https://api.bilibili.com/x/web-interface/ranking/v2",
        "description": "B站分区排行榜",
        "params": {"rid": 0, "type": "all"},
    },
    {
        "name": "weekly_series",
        "url": "https://api.bilibili.com/x/web-interface/popular/series/list",
        "description": "B站每周必看精选合集",
        "params": {},
    },
]

# ==================== Data Source Layer Configuration ====================

DATA_SOURCE_LAYERS: dict[str, dict[str, Any]] = {
    "layer1": {
        "name": "实时趋势数据",
        "sources": ["tianapi", "bilibili"],
        "data_source_label": "tianapi",
        "confidence_range": (0.7, 1.0),
        "caveat": None,
        "description": "Layer 1: 平台公开热搜/趋势API，实时数据",
    },
    "layer2": {
        "name": "AI辅助数据",
        "sources": ["llm_inference"],
        "data_source_label": "llm_simulation",
        "confidence_range": (0.6, 0.8),
        "caveat": "基于AI推断，非实时数据",
        "description": "Layer 2: LLM模拟生成，标注AI推断",
    },
    "layer3": {
        "name": "预置基准数据",
        "sources": ["preloaded"],
        "data_source_label": "preloaded",
        "confidence_range": (0.3, 0.5),
        "caveat": "历史基准数据，可能过时",
        "description": "Layer 3: 预置50赛道基准数据",
        "max_age_days": 30,
    },
}

# ==================== XingHong API (Commercial, reserved) ====================
# Not used in MVP. Reserved for future paid tier integration.

XINGHONG_API_CONFIG: dict[str, Any] = {
    "name": "新红API",
    "base_url": "",  # To be configured when enabled
    "api_key_env": "XINGHONG_API_KEY",
    "enabled": False,
    "description": "小红书数据商业API（MVP暂不使用）",
}

# ==================== Data Source Health Check Config ====================

HEALTH_CHECK_INTERVAL_MINUTES: int = 5
HEALTH_CHECK_TIMEOUT: float = 5.0

# ==================== Helper Functions ====================


def get_tianapi_endpoint(name: str) -> dict[str, Any]:
    """Get configuration for a specific TianAPI endpoint.

    Args:
        name: Endpoint name (e.g., 'weibohot', 'douyinhot').

    Returns:
        Endpoint configuration dictionary.

    Raises:
        ValueError: If endpoint name is not recognized.
    """
    for endpoint in TIANAPI_ENDPOINTS:
        if endpoint["name"] == name:
            return endpoint
    raise ValueError(
        f"Unknown TianAPI endpoint '{name}'. "
        f"Available: {[e['name'] for e in TIANAPI_ENDPOINTS]}"
    )


def get_bilibili_endpoint(name: str) -> dict[str, Any]:
    """Get configuration for a specific Bilibili endpoint.

    Args:
        name: Endpoint name (e.g., 'popular', 'ranking').

    Returns:
        Endpoint configuration dictionary.

    Raises:
        ValueError: If endpoint name is not recognized.
    """
    for endpoint in BILIBILI_ENDPOINTS:
        if endpoint["name"] == name:
            return endpoint
    raise ValueError(
        f"Unknown Bilibili endpoint '{name}'. "
        f"Available: {[e['name'] for e in BILIBILI_ENDPOINTS]}"
    )
