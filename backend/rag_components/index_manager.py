"""FAISS Index Manager for RAG system."""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

import numpy as np

logger = logging.getLogger(__name__)

# Global index cache to prevent reloading
_index_cache = {}


class FAISSIndexManager:
    """Manages FAISS index lifecycle and retrieval.
    
    Handles building, loading, searching, and validating FAISS indexes
    with metadata management.
    """
    
    def __init__(
        self,
        index_file: Path,
        metadata_file: Path,
        embedding_dimension: int,
    ):
        """Initialize index manager.
        
        Args:
            index_file: Path to FAISS index file
            metadata_file: Path to chunk metadata JSON
            embedding_dimension: Expected embedding dimension
        """
        self.index_file = Path(index_file)
        self.metadata_file = Path(metadata_file)
        self.embedding_dimension = embedding_dimension
        self._cached_index = None
        self._cached_metadata = None
        
        logger.info(
            f"FAISSIndexManager initialized: "
            f"index_file={index_file}, metadata_file={metadata_file}, "
            f"embedding_dimension={embedding_dimension}"
        )
    
    def build_index(
        self,
        chunks: List[Dict[str, Any]],
        embeddings: np.ndarray,
    ) -> Dict[str, int]:
        """Build and save FAISS index.
        
        Args:
            chunks: List of chunk metadata dictionaries
            embeddings: Chunk embeddings (N, dimension)
            
        Returns:
            Statistics: manuals_indexed, chunks_indexed
            
        Raises:
            ValueError: If embeddings dimension doesn't match expected
            RuntimeError: If index building fails
        """
        try:
            import faiss
        except ImportError:
            logger.error("faiss not installed. Install with: pip install faiss-cpu")
            raise
        
        if embeddings.shape[0] != len(chunks):
            raise ValueError(
                f"Number of embeddings ({embeddings.shape[0]}) doesn't match "
                f"number of chunks ({len(chunks)})"
            )
        
        if embeddings.shape[1] != self.embedding_dimension:
            raise ValueError(
                f"Embedding dimension ({embeddings.shape[1]}) doesn't match "
                f"expected dimension ({self.embedding_dimension})"
            )
        
        try:
            # Create FAISS index with cosine similarity (IndexFlatIP for normalized embeddings)
            logger.info(f"Building FAISS index with {len(chunks)} chunks...")
            index = faiss.IndexFlatIP(self.embedding_dimension)
            
            # Add embeddings to index
            embeddings_float32 = embeddings.astype(np.float32)
            index.add(embeddings_float32)
            
            # Create metadata
            metadata = {
                "embedding_dimension": self.embedding_dimension,
                "model_name": "all-MiniLM-L6-v2",
                "created_at": datetime.utcnow().isoformat(),
                "chunks": chunks,
            }
            
            # Ensure output directories exist
            self.index_file.parent.mkdir(parents=True, exist_ok=True)
            self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Save index
            faiss.write_index(index, str(self.index_file))
            logger.info(f"Saved FAISS index to {self.index_file}")
            
            # Save metadata
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"Saved metadata to {self.metadata_file}")
            
            # Count unique manuals
            unique_manuals = set(chunk.get("manual", "") for chunk in chunks)
            
            stats = {
                "manuals_indexed": len(unique_manuals),
                "chunks_indexed": len(chunks),
            }
            
            logger.info(f"Index built successfully: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to build index: {e}")
            raise RuntimeError(f"Index building failed: {e}") from e
    
    def load_index(self) -> Optional[Dict[str, Any]]:
        """Load FAISS index and metadata with dimension validation.
        
        Returns:
            Dictionary with keys:
            - index: FAISS index object
            - metadata: List of chunk metadata
            
        Raises:
            ValueError: If embedding dimension mismatch detected
            FileNotFoundError: If index or metadata files don't exist
        """
        try:
            import faiss
        except ImportError:
            logger.error("faiss not installed. Install with: pip install faiss-cpu")
            raise
        
        # Check if files exist
        if not self.index_file.exists():
            logger.warning(f"Index file not found: {self.index_file}")
            return None
        
        if not self.metadata_file.exists():
            logger.warning(f"Metadata file not found: {self.metadata_file}")
            return None
        
        try:
            # Load index from cache if available
            cache_key = str(self.index_file)
            if cache_key in _index_cache:
                logger.debug(f"Using cached index: {cache_key}")
                return _index_cache[cache_key]
            
            # Load FAISS index
            logger.info(f"Loading FAISS index from {self.index_file}...")
            index = faiss.read_index(str(self.index_file))
            
            # Validate dimension
            self.validate_dimension(index)
            
            # Load metadata
            logger.info(f"Loading metadata from {self.metadata_file}...")
            with open(self.metadata_file, 'r') as f:
                metadata = json.load(f)
            
            result = {
                "index": index,
                "metadata": metadata,
            }
            
            # Cache the loaded index
            _index_cache[cache_key] = result
            
            logger.info(f"Index loaded successfully with {len(metadata.get('chunks', []))} chunks")
            return result
            
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            raise RuntimeError(f"Index loading failed: {e}") from e
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Search index for similar chunks.
        
        Args:
            query_embedding: Query vector (1, dimension)
            top_k: Number of results to return
            
        Returns:
            Tuple of (distances, indices)
            
        Raises:
            ValueError: If query embedding dimension doesn't match
            RuntimeError: If search fails
        """
        try:
            import faiss
        except ImportError:
            logger.error("faiss not installed. Install with: pip install faiss-cpu")
            raise
        
        # Load index if not already loaded
        if self._cached_index is None:
            result = self.load_index()
            if result is None:
                logger.warning("No index available for search")
                return np.array([]), np.array([])
            self._cached_index = result["index"]
        
        # Validate query embedding dimension
        if query_embedding.shape[1] != self.embedding_dimension:
            raise ValueError(
                f"Query embedding dimension ({query_embedding.shape[1]}) doesn't match "
                f"expected dimension ({self.embedding_dimension})"
            )
        
        try:
            # Convert to float32 for FAISS
            query_float32 = query_embedding.astype(np.float32)
            
            # Search
            distances, indices = self._cached_index.search(query_float32, top_k)
            
            logger.debug(f"Search returned {len(indices[0])} results")
            return distances, indices
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise RuntimeError(f"Index search failed: {e}") from e
    
    def validate_dimension(self, index) -> None:
        """Validate index dimension matches expected dimension.
        
        Args:
            index: FAISS index to validate
            
        Raises:
            ValueError: If dimension mismatch with descriptive message
        """
        actual_dimension = index.d
        
        if actual_dimension != self.embedding_dimension:
            error_msg = (
                f"Embedding dimension mismatch: "
                f"expected {self.embedding_dimension}, got {actual_dimension}. "
                f"This usually means the embedding model changed. "
                f"Please rebuild the index with the new model."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.debug(f"Index dimension validated: {actual_dimension}")
    
    def clear_cache(self):
        """Clear the global index cache.
        
        Useful for testing or when switching indexes.
        """
        global _index_cache
        _index_cache.clear()
        self._cached_index = None
        self._cached_metadata = None
        logger.info("Index cache cleared")


def get_index_manager(
    index_file: Path,
    metadata_file: Path,
    embedding_dimension: int = 384,
) -> FAISSIndexManager:
    """Factory function to get a FAISSIndexManager instance.
    
    Args:
        index_file: Path to FAISS index file
        metadata_file: Path to chunk metadata JSON
        embedding_dimension: Expected embedding dimension
        
    Returns:
        FAISSIndexManager instance
    """
    return FAISSIndexManager(index_file, metadata_file, embedding_dimension)
