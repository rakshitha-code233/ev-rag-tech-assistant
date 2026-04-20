"""Semantic Embedder using sentence-transformers for RAG system."""

import logging
from typing import List, Optional
import numpy as np

logger = logging.getLogger(__name__)

# Global model cache to prevent reloading
_model_cache = {}


class SemanticEmbedder:
    """Wrapper for sentence-transformers embedding model.
    
    Provides semantic embeddings using transformer-based models.
    Replaces the hash-based LocalHashingEmbedder with semantic understanding.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize the embedding model.
        
        Args:
            model_name: HuggingFace model identifier
                Default: "all-MiniLM-L6-v2" (384 dimensions, fast inference)
        """
        self.model_name = model_name
        self.dimension = 384  # for MiniLM-L6-v2
        self._model = None
    
    def _load_model(self):
        """Lazy-load the model on first use.
        
        Uses global cache to prevent reloading the model across multiple
        instances or queries in the same session.
        """
        global _model_cache
        
        if self.model_name in _model_cache:
            self._model = _model_cache[self.model_name]
            logger.debug(f"Using cached model: {self.model_name}")
            return
        
        try:
            from sentence_transformers import SentenceTransformer
            
            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            
            # Update dimension based on actual model
            self.dimension = self._model.get_sentence_embedding_dimension()
            
            # Cache the model globally
            _model_cache[self.model_name] = self._model
            logger.info(f"Model loaded successfully. Dimension: {self.dimension}")
            
        except ImportError:
            logger.error("sentence-transformers not installed. Install with: pip install sentence-transformers")
            raise
        except Exception as e:
            logger.error(f"Failed to load embedding model {self.model_name}: {e}")
            raise
    
    def encode(
        self,
        texts: List[str],
        convert_to_numpy: bool = True,
        normalize_embeddings: bool = True,
        show_progress_bar: bool = False,
    ) -> np.ndarray:
        """Encode texts into semantic embeddings.
        
        Args:
            texts: List of text strings to encode
            convert_to_numpy: Return numpy array (vs list)
            normalize_embeddings: L2 normalize for cosine similarity
            show_progress_bar: Show encoding progress
            
        Returns:
            Normalized embeddings as numpy array (N, dimension)
            
        Raises:
            ValueError: If texts is empty or invalid
            RuntimeError: If model fails to encode
        """
        if not texts:
            raise ValueError("texts cannot be empty")
        
        if self._model is None:
            self._load_model()
        
        try:
            # Encode texts using the model
            embeddings = self._model.encode(
                texts,
                convert_to_numpy=convert_to_numpy,
                normalize_embeddings=normalize_embeddings,
                show_progress_bar=show_progress_bar,
            )
            
            # Ensure output is numpy array
            if not isinstance(embeddings, np.ndarray):
                embeddings = np.array(embeddings)
            
            # Verify normalization if requested
            if normalize_embeddings:
                norms = np.linalg.norm(embeddings, axis=1)
                if not np.allclose(norms, 1.0, atol=1e-6):
                    logger.warning("Embeddings not properly normalized. Re-normalizing...")
                    embeddings = embeddings / norms[:, np.newaxis]
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to encode texts: {e}")
            raise RuntimeError(f"Embedding encoding failed: {e}") from e
    
    @property
    def embedding_dimension(self) -> int:
        """Return the embedding dimension for this model.
        
        Returns:
            Embedding dimension (e.g., 384 for MiniLM-L6-v2)
        """
        if self._model is None:
            self._load_model()
        return self.dimension
    
    def clear_cache(self):
        """Clear the global model cache.
        
        Useful for testing or when switching models.
        """
        global _model_cache
        _model_cache.clear()
        self._model = None
        logger.info("Model cache cleared")


def get_embedder(model_name: str = "all-MiniLM-L6-v2") -> SemanticEmbedder:
    """Factory function to get a SemanticEmbedder instance.
    
    Args:
        model_name: HuggingFace model identifier
        
    Returns:
        SemanticEmbedder instance
    """
    return SemanticEmbedder(model_name)
