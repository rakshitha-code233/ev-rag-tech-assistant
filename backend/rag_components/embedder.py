"""Lightweight Embedder using BM25 for RAG system - no heavy ML models."""

import logging
from typing import List, Optional
import numpy as np
from rank_bm25 import BM25Okapi

logger = logging.getLogger(__name__)


class LightweightEmbedder:
    """Lightweight embedder using BM25 algorithm.
    
    Provides fast, memory-efficient text retrieval without loading
    large transformer models. Uses rank-bm25 which is already in requirements.
    """
    
    def __init__(self, model_name: str = "bm25"):
        """Initialize the lightweight embedder.
        
        Args:
            model_name: Embedder type (currently only 'bm25' supported)
        """
        self.model_name = model_name
        self.dimension = 1  # BM25 returns scalar scores
        self.corpus = []
        self.bm25 = None
    
    def encode(
        self,
        texts: List[str],
        convert_to_numpy: bool = True,
        normalize_embeddings: bool = True,
        show_progress_bar: bool = False,
    ) -> np.ndarray:
        """Encode texts using BM25.
        
        For BM25, we tokenize and store the corpus for later retrieval.
        Returns a simple representation.
        
        Args:
            texts: List of text strings to encode
            convert_to_numpy: Return numpy array
            normalize_embeddings: Normalize scores
            show_progress_bar: Ignored (no progress for BM25)
            
        Returns:
            Dummy embeddings (BM25 is used for retrieval, not encoding)
        """
        if not texts:
            raise ValueError("texts cannot be empty")
        
        try:
            # Tokenize corpus for BM25
            tokenized_corpus = [text.lower().split() for text in texts]
            self.bm25 = BM25Okapi(tokenized_corpus)
            self.corpus = texts
            
            logger.info(f"BM25 index built for {len(texts)} documents")
            
            # Return dummy embeddings (BM25 doesn't use embeddings)
            embeddings = np.ones((len(texts), 1), dtype=np.float32)
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to build BM25 index: {e}")
            raise RuntimeError(f"BM25 indexing failed: {e}") from e
    
    def search(self, query: str, top_k: int = 10) -> List[tuple]:
        """Search using BM25.
        
        Args:
            query: Query string
            top_k: Number of top results to return
            
        Returns:
            List of (score, index) tuples
        """
        if self.bm25 is None:
            raise RuntimeError("BM25 index not built. Call encode() first.")
        
        try:
            query_tokens = query.lower().split()
            scores = self.bm25.get_scores(query_tokens)
            
            # Get top-k indices
            top_indices = np.argsort(scores)[::-1][:top_k]
            results = [(scores[idx], idx) for idx in top_indices if scores[idx] > 0]
            
            return results
            
        except Exception as e:
            logger.error(f"BM25 search failed: {e}")
            raise RuntimeError(f"BM25 search failed: {e}") from e
    
    @property
    def embedding_dimension(self) -> int:
        """Return the embedding dimension.
        
        Returns:
            1 (BM25 returns scalar scores)
        """
        return self.dimension
    
    def clear_cache(self):
        """Clear the BM25 index."""
        self.bm25 = None
        self.corpus = []
        logger.info("BM25 index cleared")


def get_embedder(model_name: str = "bm25") -> LightweightEmbedder:
    """Factory function to get a LightweightEmbedder instance.
    
    Args:
        model_name: Embedder type (currently only 'bm25')
        
    Returns:
        LightweightEmbedder instance
    """
    return LightweightEmbedder(model_name)
