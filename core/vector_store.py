"""Vector store abstraction layer for The Loom.

Provides unified interface for multiple vector databases (Chroma, Pinecone, etc.).
Supports embeddings, hybrid search, and index management.
"""

from __future__ import annotations

import hashlib
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class EmbeddingConfig:
    """Configuration for embedding generation."""
    provider: str = "openai"  # openai, huggingface, ollama
    model: str = "text-embedding-3-small"
    api_key: str | None = None
    base_url: str | None = None
    dimensions: int = 1536  # Vector dimensions
    
    def __post_init__(self) -> None:
        if self.api_key is None and self.provider == "openai":
            object.__setattr__(self, 'api_key', os.environ.get("OPENAI_API_KEY"))


@dataclass(frozen=True)
class VectorDocument:
    """A document stored in the vector index."""
    id: str
    text: str
    embedding: list[float] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    
    @property
    def content_hash(self) -> str:
        """Compute hash of text content."""
        return hashlib.sha256(self.text.encode()).hexdigest()[:16]


@dataclass(frozen=True)
class SearchResult:
    """Result from vector search."""
    document: VectorDocument
    score: float  # Similarity score (0-1)
    distance: float | None = None  # Raw distance metric


@dataclass(frozen=True)
class IndexStats:
    """Statistics about the vector index."""
    document_count: int
    dimension: int
    last_updated: str | None
    index_size_bytes: int | None = None


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""
    
    def __init__(self, config: EmbeddingConfig) -> None:
        self.config = config
        self._validate_config()
    
    @abstractmethod
    def _validate_config(self) -> None:
        """Validate provider configuration."""
        pass
    
    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for texts."""
        pass
    
    @abstractmethod
    def embed_sync(self, texts: list[str]) -> list[list[float]]:
        """Synchronous embedding generation."""
        pass


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider."""
    
    def __init__(self, config: EmbeddingConfig) -> None:
        super().__init__(config)
        self._client: Any | None = None
    
    def _validate_config(self) -> None:
        if not self.config.api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY.")
    
    def _get_client(self) -> Any:
        """Lazy load OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError as e:
                raise ImportError("OpenAI package not installed. Run: pip install openai") from e
            
            self._client = OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
            )
        return self._client
    
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using OpenAI API."""
        import asyncio
        # Use sync client in async context
        return await asyncio.get_event_loop().run_in_executor(
            None, self.embed_sync, texts
        )
    
    def embed_sync(self, texts: list[str]) -> list[list[float]]:
        """Synchronous embedding generation."""
        client = self._get_client()
        
        response = client.embeddings.create(
            model=self.config.model,
            input=texts,
        )
        
        return [item.embedding for item in response.data]


class HuggingFaceEmbeddingProvider(EmbeddingProvider):
    """Local HuggingFace embedding provider."""
    
    def __init__(self, config: EmbeddingConfig) -> None:
        super().__init__(config)
        self._model: Any | None = None
        self._tokenizer: Any | None = None
    
    def _validate_config(self) -> None:
        pass  # No API key needed for local models
    
    def _load_model(self) -> tuple[Any, Any]:
        """Lazy load model and tokenizer."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as e:
                raise ImportError(
                    "sentence-transformers not installed. Run: pip install sentence-transformers"
                ) from e
            
            self._model = SentenceTransformer(self.config.model)
        
        return self._model, self._tokenizer
    
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using local model."""
        import asyncio
        return await asyncio.get_event_loop().run_in_executor(
            None, self.embed_sync, texts
        )
    
    def embed_sync(self, texts: list[str]) -> list[list[float]]:
        """Synchronous embedding generation."""
        model, _ = self._load_model()
        embeddings = model.encode(texts)
        return embeddings.tolist()


class MockEmbeddingProvider(EmbeddingProvider):
    """Mock embedding provider for testing."""
    
    def _validate_config(self) -> None:
        pass
    
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate deterministic mock embeddings."""
        return self.embed_sync(texts)
    
    def embed_sync(self, texts: list[str]) -> list[list[float]]:
        """Generate deterministic mock embeddings."""
        import random
        
        embeddings = []
        for text in texts:
            # Use text hash as seed for deterministic embeddings
            seed = int(hashlib.sha256(text.encode()).hexdigest()[:8], 16)
            rng = random.Random(seed)
            embedding = [rng.random() * 2 - 1 for _ in range(self.config.dimensions)]
            # Normalize
            magnitude = sum(x * x for x in embedding) ** 0.5
            embedding = [x / magnitude for x in embedding]
            embeddings.append(embedding)
        
        return embeddings


class EmbeddingProviderFactory:
    """Factory for creating embedding providers."""
    
    _providers: dict[str, type[EmbeddingProvider]] = {
        "openai": OpenAIEmbeddingProvider,
        "huggingface": HuggingFaceEmbeddingProvider,
        "mock": MockEmbeddingProvider,
    }
    
    @classmethod
    def create(cls, config: EmbeddingConfig | None = None) -> EmbeddingProvider:
        """Create embedding provider from config."""
        if config is None:
            # Auto-detect from environment
            if os.environ.get("OPENAI_API_KEY"):
                config = EmbeddingConfig(provider="openai", model="text-embedding-3-small")
            else:
                config = EmbeddingConfig(provider="mock", model="mock")
        
        provider_class = cls._providers.get(config.provider)
        if provider_class is None:
            raise ValueError(f"Unknown embedding provider: {config.provider}")
        
        return provider_class(config)
    
    @classmethod
    def register_provider(
        cls,
        name: str,
        provider_class: type[EmbeddingProvider]
    ) -> None:
        """Register a custom embedding provider."""
        cls._providers[name] = provider_class


class VectorStore(ABC):
    """Abstract base class for vector stores."""
    
    def __init__(
        self,
        embedding_provider: EmbeddingProvider | None = None,
        collection_name: str = "loom_chunks",
    ) -> None:
        self.embedding_provider = embedding_provider or EmbeddingProviderFactory.create()
        self.collection_name = collection_name
    
    @abstractmethod
    async def add_documents(self, documents: list[VectorDocument]) -> list[str]:
        """Add documents to the index. Returns document IDs."""
        pass
    
    @abstractmethod
    async def search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Search for similar documents."""
        pass
    
    @abstractmethod
    async def delete_documents(self, document_ids: list[str]) -> int:
        """Delete documents by ID. Returns count deleted."""
        pass
    
    @abstractmethod
    async def get_document(self, document_id: str) -> VectorDocument | None:
        """Get a document by ID."""
        pass
    
    @abstractmethod
    async def get_stats(self) -> IndexStats:
        """Get index statistics."""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all documents from the index."""
        pass
    
    async def update_documents(self, documents: list[VectorDocument]) -> list[str]:
        """Update documents (delete and re-add)."""
        ids = [doc.id for doc in documents]
        await self.delete_documents(ids)
        return await self.add_documents(documents)


class ChromaVectorStore(VectorStore):
    """ChromaDB vector store implementation (local-first)."""
    
    def __init__(
        self,
        embedding_provider: EmbeddingProvider | None = None,
        collection_name: str = "loom_chunks",
        persist_directory: str | None = None,
    ) -> None:
        super().__init__(embedding_provider, collection_name)
        self.persist_directory = persist_directory or ".chroma_db"
        self._client: Any | None = None
        self._collection: Any | None = None
    
    def _get_client(self) -> Any:
        """Lazy load Chroma client."""
        if self._client is None:
            try:
                import chromadb
                from chromadb.config import Settings
            except ImportError as e:
                raise ImportError(
                    "ChromaDB not installed. Run: pip install chromadb"
                ) from e
            
            self._client = chromadb.Client(
                Settings(
                    chroma_db_impl="duckdb+parquet",
                    persist_directory=self.persist_directory,
                    anonymized_telemetry=False,
                )
            )
        
        return self._client
    
    def _get_collection(self) -> Any:
        """Get or create collection."""
        if self._collection is None:
            client = self._get_client()
            self._collection = client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection
    
    async def add_documents(self, documents: list[VectorDocument]) -> list[str]:
        """Add documents to Chroma."""
        import asyncio
        
        if not documents:
            return []
        
        # Generate embeddings
        texts = [doc.text for doc in documents]
        embeddings = await self.embedding_provider.embed(texts)
        
        # Prepare data for Chroma
        ids = [doc.id for doc in documents]
        metadatas = [
            {
                **doc.metadata,
                "created_at": doc.created_at,
                "content_hash": doc.content_hash,
            }
            for doc in documents
        ]
        
        # Add to collection (sync operation)
        collection = self._get_collection()
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
            )
        )
        
        return ids
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Search Chroma collection."""
        import asyncio
        
        # Generate query embedding
        query_embeddings = await self.embedding_provider.embed([query])
        query_embedding = query_embeddings[0]
        
        # Search (sync operation)
        collection = self._get_collection()
        results = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filters,
                include=["documents", "metadatas", "distances"],
            )
        )
        
        # Parse results
        search_results = []
        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        
        for i, doc_id in enumerate(ids):
            # Convert distance to similarity score (cosine distance -> similarity)
            distance = distances[i] if distances else None
            score = 1.0 - (distance or 0.0)  # Simple conversion for cosine
            
            doc = VectorDocument(
                id=doc_id,
                text=documents[i],
                metadata=metadatas[i] if metadatas else {},
            )
            
            search_results.append(SearchResult(
                document=doc,
                score=max(0.0, min(1.0, score)),
                distance=distance,
            ))
        
        return search_results
    
    async def delete_documents(self, document_ids: list[str]) -> int:
        """Delete documents from Chroma."""
        import asyncio
        
        if not document_ids:
            return 0
        
        collection = self._get_collection()
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: collection.delete(ids=document_ids)
        )
        
        return len(document_ids)
    
    async def get_document(self, document_id: str) -> VectorDocument | None:
        """Get document by ID."""
        import asyncio
        
        collection = self._get_collection()
        results = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: collection.get(
                ids=[document_id],
                include=["documents", "metadatas"],
            )
        )
        
        ids = results.get("ids", [])
        if not ids:
            return None
        
        return VectorDocument(
            id=ids[0],
            text=results["documents"][0],
            metadata=results["metadatas"][0] if results.get("metadatas") else {},
        )
    
    async def get_stats(self) -> IndexStats:
        """Get collection statistics."""
        import asyncio
        
        collection = self._get_collection()
        count = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: collection.count()
        )
        
        return IndexStats(
            document_count=count,
            dimension=self.embedding_provider.config.dimensions,
            last_updated=None,  # Chroma doesn't expose this easily
        )
    
    async def clear(self) -> None:
        """Clear collection."""
        import asyncio
        
        client = self._get_client()
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: client.delete_collection(self.collection_name)
        )
        self._collection = None


class MockVectorStore(VectorStore):
    """In-memory mock vector store for testing."""
    
    def __init__(
        self,
        embedding_provider: EmbeddingProvider | None = None,
        collection_name: str = "mock_chunks",
    ) -> None:
        super().__init__(embedding_provider or MockEmbeddingProvider(
            EmbeddingConfig(provider="mock", model="mock", dimensions=384)
        ), collection_name)
        self._documents: dict[str, VectorDocument] = {}
        self._embeddings: dict[str, list[float]] = {}
    
    async def add_documents(self, documents: list[VectorDocument]) -> list[str]:
        """Add documents to memory."""
        texts = [doc.text for doc in documents]
        embeddings = await self.embedding_provider.embed(texts)
        
        for i, doc in enumerate(documents):
            self._documents[doc.id] = doc
            self._embeddings[doc.id] = embeddings[i]
        
        return [doc.id for doc in documents]
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Simple cosine similarity search in memory."""
        if not self._documents:
            return []
        
        # Get query embedding
        query_embeddings = await self.embedding_provider.embed([query])
        query_embedding = query_embeddings[0]
        
        # Calculate similarities
        scored_docs: list[tuple[float, str]] = []
        for doc_id, embedding in self._embeddings.items():
            doc = self._documents[doc_id]
            
            # Apply filters
            if filters:
                match = True
                for key, value in filters.items():
                    if doc.metadata.get(key) != value:
                        match = False
                        break
                if not match:
                    continue
            
            # Cosine similarity
            dot_product = sum(a * b for a, b in zip(query_embedding, embedding))
            score = (dot_product + 1) / 2  # Normalize to 0-1
            scored_docs.append((score, doc_id))
        
        # Sort by score
        scored_docs.sort(reverse=True)
        
        # Return top_k
        results = []
        for score, doc_id in scored_docs[:top_k]:
            results.append(SearchResult(
                document=self._documents[doc_id],
                score=score,
            ))
        
        return results
    
    async def delete_documents(self, document_ids: list[str]) -> int:
        """Delete documents from memory."""
        count = 0
        for doc_id in document_ids:
            if doc_id in self._documents:
                del self._documents[doc_id]
                del self._embeddings[doc_id]
                count += 1
        return count
    
    async def get_document(self, document_id: str) -> VectorDocument | None:
        """Get document by ID."""
        return self._documents.get(document_id)
    
    async def get_stats(self) -> IndexStats:
        """Get mock statistics."""
        return IndexStats(
            document_count=len(self._documents),
            dimension=self.embedding_provider.config.dimensions,
            last_updated=datetime.now(UTC).isoformat(),
        )
    
    async def clear(self) -> None:
        """Clear all documents."""
        self._documents.clear()
        self._embeddings.clear()


class VectorStoreFactory:
    """Factory for creating vector stores."""
    
    _stores: dict[str, type[VectorStore]] = {
        "chroma": ChromaVectorStore,
        "mock": MockVectorStore,
    }
    
    @classmethod
    def create(
        cls,
        store_type: str | None = None,
        **kwargs: Any,
    ) -> VectorStore:
        """Create vector store."""
        if store_type is None:
            # Auto-detect
            try:
                import chromadb
                store_type = "chroma"
            except ImportError:
                store_type = "mock"
        
        store_class = cls._stores.get(store_type)
        if store_class is None:
            raise ValueError(f"Unknown vector store type: {store_type}")
        
        return store_class(**kwargs)
    
    @classmethod
    def register_store(
        cls,
        name: str,
        store_class: type[VectorStore]
    ) -> None:
        """Register a custom vector store."""
        cls._stores[name] = store_class


# Global vector store instance
_global_vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    """Get or create global vector store instance."""
    global _global_vector_store
    if _global_vector_store is None:
        _global_vector_store = VectorStoreFactory.create()
    return _global_vector_store


def set_vector_store(store: VectorStore) -> None:
    """Set global vector store instance."""
    global _global_vector_store
    _global_vector_store = store


async def hybrid_search(
    query: str,
    documents: list[VectorDocument],
    top_k: int = 5,
    vector_weight: float = 0.7,
    keyword_weight: float = 0.3,
) -> list[SearchResult]:
    """Hybrid search combining vector similarity and keyword matching (BM25-style).
    
    This is a simple implementation that can be used with any vector store.
    For production, consider using a dedicated hybrid search library.
    """
    import math
    import re
    
    # Simple keyword tokenization
    def tokenize(text: str) -> list[str]:
        return re.findall(r'\b[a-zA-Z]+\b', text.lower())
    
    # Calculate IDF scores
    query_tokens = tokenize(query)
    doc_count = len(documents)
    
    idf_scores: dict[str, float] = {}
    for token in set(query_tokens):
        doc_freq = sum(1 for doc in documents if token in tokenize(doc.text))
        idf_scores[token] = math.log((doc_count - doc_freq + 0.5) / (doc_freq + 0.5) + 1)
    
    # Calculate BM25 scores
    k1 = 1.5
    b = 0.75
    avg_doc_len = sum(len(tokenize(doc.text)) for doc in documents) / max(1, len(documents))
    
    keyword_scores: dict[str, float] = {}
    for doc in documents:
        doc_tokens = tokenize(doc.text)
        doc_len = len(doc_tokens)
        token_freq: dict[str, int] = {}
        for token in doc_tokens:
            token_freq[token] = token_freq.get(token, 0) + 1
        
        score = 0.0
        for token in query_tokens:
            if token in token_freq:
                idf = idf_scores.get(token, 0)
                tf = token_freq[token]
                score += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * doc_len / avg_doc_len))
        
        keyword_scores[doc.id] = score
    
    # Get vector scores from vector store
    store = get_vector_store()
    vector_results = await store.search(query, top_k=len(documents))
    vector_scores: dict[str, float] = {
        result.document.id: result.score
        for result in vector_results
    }
    
    # Combine scores
    combined_scores: dict[str, float] = {}
    for doc in documents:
        v_score = vector_scores.get(doc.id, 0.0)
        k_score = keyword_scores.get(doc.id, 0.0)
        
        # Normalize keyword score to 0-1
        max_k = max(keyword_scores.values()) if keyword_scores else 1.0
        k_score_norm = k_score / max_k if max_k > 0 else 0.0
        
        combined_scores[doc.id] = vector_weight * v_score + keyword_weight * k_score_norm
    
    # Sort by combined score
    sorted_docs = sorted(
        documents,
        key=lambda d: combined_scores.get(d.id, 0.0),
        reverse=True,
    )
    
    return [
        SearchResult(
            document=doc,
            score=combined_scores.get(doc.id, 0.0),
        )
        for doc in sorted_docs[:top_k]
    ]
