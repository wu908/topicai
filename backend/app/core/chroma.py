"""ChromaDB client module for TopicAI v4.0.

Provides ChromaDB vector database client initialization and collection management
for semantic search, viral similarity matching, and topic deduplication.
"""

import logging

logger = logging.getLogger(__name__)

# Singleton ChromaDB client
_chroma_client: object | None = None


def get_chroma_client(persist_dir: str) -> object:
    """Get or create the ChromaDB client.

    Uses lazy initialization — client is created on first call.

    Args:
        persist_dir: Directory for persistent ChromaDB storage.

    Returns:
        ChromaDB PersistentClient instance.
    """
    global _chroma_client
    if _chroma_client is None:
        try:
            import chromadb

            _chroma_client = chromadb.PersistentClient(path=persist_dir)
            logger.info(f"ChromaDB client initialized at {persist_dir}")
        except ImportError:
            logger.warning("chromadb not installed — ChromaDB disabled")
            return None
        except Exception as e:
            logger.error(f"ChromaDB initialization failed: {e}")
            return None
    return _chroma_client


def get_or_create_collection(
    client: object, name: str, embedding_dim: int = 1024
) -> object:
    """Get or create a ChromaDB collection.

    Args:
        client: ChromaDB PersistentClient instance.
        name: Collection name.
        embedding_dim: Embedding vector dimension (default 1024 for BGE).

    Returns:
        ChromaDB Collection instance.
    """
    if client is None:
        return None
    try:
        collection = client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine", "dimension": embedding_dim},
        )
        return collection
    except Exception as e:
        logger.error(f"Failed to get/create collection '{name}': {e}")
        return None
