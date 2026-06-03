"""Data source manager for TopicAI v4.0.

Implements the three-layer degradation chain:
Layer 1: TianAPI + Bilibili (real-time) → Layer 2: LLM inference →
Layer 3: Preloaded benchmarks → Manual guidance.

Automatically switches between layers based on availability.
Performs periodic health checks and auto-recovery.
"""

import logging
from typing import Any

from app.data_sources.base import DataSource
from config.data_source_config import DATA_SOURCE_LAYERS
from config.settings import get_settings

logger = logging.getLogger(__name__)


class DataManager:
    """Manager for the three-layer data source degradation chain.

    Orchestrates data fetching across multiple sources with automatic
    fallback when higher-tier sources become unavailable.

    Attributes:
        sources: Ordered list of (layer_name, source) tuples.
        active_source: Currently active data source.
        active_layer: Currently active layer name.
    """

    def __init__(self):
        """Initialize DataManager with configured data sources."""
        self.settings = get_settings()
        self.sources: list[tuple[str, DataSource]] = []
        self.active_source: DataSource | None = None
        self.active_layer: str = "Layer 1"
        self._init_sources()

    def _init_sources(self) -> None:
        """Initialize all data sources in priority order."""
        # Layer 1: TianAPI
        from app.data_sources.bilibili_source import BilibiliSource
        from app.data_sources.tianapi_source import TianAPISource

        if self.settings.tianapi_key:
            tianapi = TianAPISource(api_key=self.settings.tianapi_key)
            self.sources.append(("Layer 1", tianapi))

        # Layer 1b: Bilibili
        bilibili = BilibiliSource()
        self.sources.append(("Layer 1b", bilibili))

        # Layer 2: LLM inference
        from app.data_sources.llm_source import LLMDataSource

        try:
            from app.core.llm import LLMClient

            llm_client = LLMClient()
            llm_source = LLMDataSource(llm_client=llm_client)
        except Exception:
            llm_source = LLMDataSource(llm_client=None)
        self.sources.append(("Layer 2", llm_source))

        # Layer 3: Preloaded benchmarks
        from app.data_sources.preloaded_source import PreloadedDataSource

        preloaded = PreloadedDataSource()
        self.sources.append(("Layer 3", preloaded))

        # Set initial active source
        if self.sources:
            self.active_source = self.sources[0][1]
            self.active_layer = self.sources[0][0]

    # ==================== Data Fetching ====================

    async def get_trending_topics(self, track: str) -> dict[str, Any]:
        """Get trending topics with automatic degradation.

        Args:
            track: Content track/category.

        Returns:
            Dict with 'topics' list and 'meta' (layer, data_source, confidence).
        """
        for layer_name, source in self.sources:
            try:
                available = await source.is_available()
                if not available:
                    logger.info(f"{layer_name} unavailable, trying next")
                    continue

                topics = await source.fetch_trending_topics(track)
                if topics:
                    self.active_source = source
                    self.active_layer = layer_name
                    return {
                        "topics": topics,
                        "meta": self._build_meta(layer_name, topics),
                    }
            except Exception as e:
                logger.warning(f"{layer_name} fetch failed: {e}")
                continue

        # All layers failed — return manual guidance
        return {
            "topics": [],
            "meta": {
                "layer": "manual",
                "data_source": "none",
                "confidence": 0.0,
                "caveat": "数据暂时不可用，请手动输入选题方向",
                "message": "所有数据源暂不可用，请手动输入您感兴趣的选题方向",
            },
        }

    async def get_track_data(self, track_keyword: str) -> dict[str, Any]:
        """Get track data with automatic degradation.

        Args:
            track_keyword: Track keyword.

        Returns:
            Dict with track data and meta.
        """
        for layer_name, source in self.sources:
            try:
                available = await source.is_available()
                if not available:
                    continue

                data = await source.fetch_track_data(track_keyword)
                if data:
                    self.active_source = source
                    self.active_layer = layer_name
                    data["meta"] = self._build_meta(layer_name, [data])
                    return data
            except Exception as e:
                logger.warning(f"{layer_name} track data failed: {e}")
                continue

        return {
            "track_keyword": track_keyword,
            "health_score": 0.0,
            "competitiveness_score": 0.0,
            "meta": {
                "layer": "manual",
                "data_source": "none",
                "confidence": 0.0,
                "caveat": "数据暂时不可用",
            },
        }

    async def get_hot_topics(self) -> dict[str, Any]:
        """Get hot topics with automatic degradation.

        Returns:
            Dict with 'topics' list and 'meta'.
        """
        for layer_name, source in self.sources:
            try:
                available = await source.is_available()
                if not available:
                    continue

                topics = await source.fetch_hot_topics()
                if topics:
                    self.active_source = source
                    self.active_layer = layer_name
                    return {
                        "topics": topics,
                        "meta": self._build_meta(layer_name, topics),
                    }
            except Exception as e:
                logger.warning(f"{layer_name} hot topics failed: {e}")
                continue

        return {
            "topics": [],
            "meta": {
                "layer": "manual",
                "data_source": "none",
                "confidence": 0.0,
                "caveat": "数据暂时不可用，请手动输入",
            },
        }

    # ==================== Management ====================

    async def switch_source(self) -> bool:
        """Manually switch to the next available source.

        Returns:
            True if switched successfully.
        """
        current_layer = getattr(self, "active_layer", "Layer 1")
        found_current = False

        for layer_name, source in self.sources:
            if not found_current:
                if layer_name == current_layer:
                    found_current = True
                continue

            try:
                available = await source.is_available()
                if available:
                    self.active_source = source
                    self.active_layer = layer_name
                    logger.info(f"Switched to {layer_name}")
                    return True
            except Exception:
                continue

        return False

    async def health_check(self) -> dict[str, Any]:
        """Perform health check on all data sources.

        Returns:
            Dict with per-layer availability status.
        """
        status = {
            "active_layer": self.active_layer,
            "layers": {},
        }

        for layer_name, source in self.sources:
            try:
                layer_status = await source.health_check()
                status["layers"][layer_name] = layer_status
            except Exception as e:
                status["layers"][layer_name] = {
                    "available": False,
                    "error": str(e),
                }

        return status

    def get_active_info(self) -> dict[str, Any]:
        """Get information about the currently active data source.

        Returns:
            Dict with layer and source info.
        """
        return {
            "layer": self.active_layer,
            "source_type": type(self.active_source).__name__
            if self.active_source
            else "none",
        }

    # ==================== Internal ====================

    def _build_meta(
        self, layer_name: str, data: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Build metadata for API responses.

        Args:
            layer_name: Current layer name.
            data: Fetched data items.

        Returns:
            Metadata dictionary.
        """
        layer_config = DATA_SOURCE_LAYERS.get(
            layer_name.lower().replace(" ", ""),
            {"data_source_label": "unknown", "confidence_range": (0.0, 0.5)},
        )

        return {
            "layer": layer_name,
            "data_source": layer_config.get("data_source_label", "unknown"),
            "confidence": data[0].get("confidence", 0.5) if data else 0.5,
            "caveat": layer_config.get("caveat"),
            "items_count": len(data),
        }
