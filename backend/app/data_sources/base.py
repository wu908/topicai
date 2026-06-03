"""Abstract base class for data sources in TopicAI v4.0.

All data sources must implement this interface to be usable
by the DataManager's three-layer degradation chain.
"""

from abc import ABC, abstractmethod
from typing import Any


class DataSource(ABC):
    """Abstract base class for all data sources.

    Defines the interface that all data sources must implement.
    Used by DataManager to provide a uniform interface across
    TianAPI, Bilibili, LLM-simulated, and preloaded sources.
    """

    @abstractmethod
    async def fetch_trending_topics(self, track: str) -> list[dict[str, Any]]:
        """Fetch trending topics for a given content track.

        Args:
            track: Content track/category (e.g., '科技', '美妆').

        Returns:
            List of trending topic dictionaries.
        """
        ...

    @abstractmethod
    async def fetch_track_data(self, track_keyword: str) -> dict[str, Any]:
        """Fetch detailed data for a specific track keyword.

        Args:
            track_keyword: The track keyword to query.

        Returns:
            Dictionary with track data (health, trends, competition).
        """
        ...

    @abstractmethod
    async def fetch_hot_topics(self) -> list[dict[str, Any]]:
        """Fetch general hot/trending topics across all tracks.

        Returns:
            List of hot topic dictionaries.
        """
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if this data source is currently available.

        Returns:
            True if the data source can serve requests.
        """
        ...

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Perform a health check on this data source.

        Returns:
            Dictionary with availability status and metadata.
        """
        ...
