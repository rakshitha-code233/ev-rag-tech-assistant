"""Data models for RAG system components."""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class RetrievedChunk:
    """A chunk retrieved from the manual index."""
    
    manual: str          # Manual filename (e.g., "Tesla_Model3.pdf")
    page: int            # Page number (1-indexed)
    text: str            # Chunk text content
    score: float         # Relevance score (0-1 range)
    
    @property
    def citation(self) -> str:
        """Format citation as 'Manual_Name p.Page_Number'."""
        return f"{self.manual} p.{self.page}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RetrievedChunk":
        """Create from dictionary."""
        return cls(
            manual=data["manual"],
            page=data["page"],
            text=data["text"],
            score=data["score"],
        )


@dataclass
class ChunkMetadata:
    """Metadata for a single chunk in the index."""
    
    id: str              # Unique chunk ID (e.g., "Tesla_Model3-p42-c0")
    manual: str          # Manual filename
    page: int            # Page number
    text: str            # Chunk text content
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChunkMetadata":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            manual=data["manual"],
            page=data["page"],
            text=data["text"],
        )


@dataclass
class IndexMetadata:
    """Metadata about the FAISS index."""
    
    embedding_dimension: int      # Embedding dimension
    model_name: str               # Embedding model name
    chunks: List[ChunkMetadata]   # All chunk metadata
    created_at: str               # ISO timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "embedding_dimension": self.embedding_dimension,
            "model_name": self.model_name,
            "created_at": self.created_at,
            "chunks": [chunk.to_dict() for chunk in self.chunks],
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IndexMetadata":
        """Create from dictionary."""
        return cls(
            embedding_dimension=data["embedding_dimension"],
            model_name=data["model_name"],
            created_at=data["created_at"],
            chunks=[ChunkMetadata.from_dict(c) for c in data["chunks"]],
        )


@dataclass
class RAGConfig:
    """RAG system configuration."""
    
    # Embedding settings
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    
    # Chunking settings
    chunk_size: int = 700
    chunk_overlap: int = 100
    min_chunk_chars: int = 120
    
    # Retrieval settings
    top_k: int = 4
    score_threshold: float = 0.20
    
    # Re-ranking settings
    reranking_enabled: bool = True
    reranking_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    relevance_threshold: float = 0.3
    
    # LLM settings
    llm_model: str = "llama-3.3-70b-versatile"
    llm_temperature: float = 0.2
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RAGConfig":
        """Create from dictionary."""
        return cls(**data)
