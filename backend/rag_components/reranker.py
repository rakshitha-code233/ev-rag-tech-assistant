"""Cross-Encoder Re-Ranker for RAG system."""

import logging
from typing import List, Optional

import numpy as np

from .models import RetrievedChunk

logger = logging.getLogger(__name__)

# Global model cache to prevent reloading
_reranker_cache = {}


class CrossEncoderReRanker:
    """Re-ranks retrieved chunks using cross-encoder scoring.
    
    Uses a cross-encoder model to re-score chunks for improved relevance
    assessment compared to semantic similarity alone.
    """
    
    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        relevance_threshold: float = 0.3,
    ):
        """Initialize cross-encoder model.
        
        Args:
            model_name: HuggingFace cross-encoder model
                Default: "cross-encoder/ms-marco-MiniLM-L-6-v2"
            relevance_threshold: Minimum score to keep chunk (default 0.3)
        """
        self.model_name = model_name
        self.relevance_threshold = relevance_threshold
        self._model = None
        
        logger.info(
            f"CrossEncoderReRanker initialized: "
            f"model_name={model_name}, relevance_threshold={relevance_threshold}"
        )
    
    def _load_model(self):
        """Lazy-load the cross-encoder model on first use.
        
        Uses global cache to prevent reloading the model across multiple
        instances or queries in the same session.
        """
        global _reranker_cache
        
        if self.model_name in _reranker_cache:
            self._model = _reranker_cache[self.model_name]
            logger.debug(f"Using cached cross-encoder model: {self.model_name}")
            return
        
        try:
            from sentence_transformers import CrossEncoder
            
            logger.info(f"Loading cross-encoder model: {self.model_name}")
            self._model = CrossEncoder(self.model_name)
            
            # Cache the model globally
            _reranker_cache[self.model_name] = self._model
            logger.info("Cross-encoder model loaded successfully")
            
        except ImportError:
            logger.error("sentence-transformers not installed. Install with: pip install sentence-transformers")
            raise
        except Exception as e:
            logger.error(f"Failed to load cross-encoder model {self.model_name}: {e}")
            raise
    
    def rerank(
        self,
        query: str,
        chunks: List[RetrievedChunk],
    ) -> List[RetrievedChunk]:
        """Re-rank chunks by relevance to query.
        
        Algorithm:
        1. Create (query, chunk.text) pairs
        2. Score all pairs with cross-encoder
        3. Update chunk.score with cross-encoder score
        4. Sort chunks by new score (descending)
        5. Filter chunks below relevance_threshold
        
        Args:
            query: User query string
            chunks: Retrieved chunks from FAISS
            
        Returns:
            Re-ranked and filtered chunks
        """
        if not chunks:
            logger.debug("No chunks to re-rank")
            return []
        
        if not query or not query.strip():
            logger.warning("Empty query provided to re-ranker")
            return chunks
        
        try:
            if self._model is None:
                self._load_model()
            
            # Create query-chunk pairs
            pairs = [[query, chunk.text] for chunk in chunks]
            
            # Score all pairs
            logger.debug(f"Re-ranking {len(chunks)} chunks...")
            scores = self.score_pairs(query, [chunk.text for chunk in chunks])
            
            # Update chunk scores and create new list
            reranked_chunks = []
            for chunk, score in zip(chunks, scores):
                # Create new chunk with updated score
                reranked_chunk = RetrievedChunk(
                    manual=chunk.manual,
                    page=chunk.page,
                    text=chunk.text,
                    score=float(score),
                )
                reranked_chunks.append(reranked_chunk)
            
            # Sort by score (descending)
            reranked_chunks.sort(key=lambda c: c.score, reverse=True)
            
            # Filter by relevance threshold
            filtered_chunks = [
                c for c in reranked_chunks
                if c.score >= self.relevance_threshold
            ]
            
            logger.debug(
                f"Re-ranking complete: {len(chunks)} chunks -> "
                f"{len(filtered_chunks)} chunks after filtering"
            )
            
            return filtered_chunks
            
        except Exception as e:
            logger.warning(f"Re-ranking failed: {e}. Using original scores.")
            # Fallback: return original chunks sorted by original score
            return sorted(chunks, key=lambda c: c.score, reverse=True)
    
    def score_pairs(
        self,
        query: str,
        texts: List[str],
    ) -> List[float]:
        """Score query-text pairs.
        
        Args:
            query: Query string
            texts: List of text strings to score
            
        Returns:
            Relevance scores (0-1 range)
            
        Raises:
            ValueError: If texts is empty
            RuntimeError: If scoring fails
        """
        if not texts:
            raise ValueError("texts cannot be empty")
        
        if self._model is None:
            self._load_model()
        
        try:
            # Create pairs
            pairs = [[query, text] for text in texts]
            
            # Score pairs
            scores = self._model.predict(pairs)
            
            # Normalize scores to 0-1 range using sigmoid
            # Cross-encoder scores are typically in range [-inf, inf]
            # We use sigmoid to normalize to [0, 1]
            normalized_scores = self._sigmoid(scores)
            
            return normalized_scores.tolist()
            
        except Exception as e:
            logger.error(f"Failed to score pairs: {e}")
            raise RuntimeError(f"Pair scoring failed: {e}") from e
    
    @staticmethod
    def _sigmoid(x: np.ndarray) -> np.ndarray:
        """Apply sigmoid function to normalize scores to [0, 1].
        
        Args:
            x: Input scores
            
        Returns:
            Normalized scores in range [0, 1]
        """
        return 1 / (1 + np.exp(-x))
    
    def clear_cache(self):
        """Clear the global model cache.
        
        Useful for testing or when switching models.
        """
        global _reranker_cache
        _reranker_cache.clear()
        self._model = None
        logger.info("Cross-encoder model cache cleared")


def get_reranker(
    model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    relevance_threshold: float = 0.3,
) -> CrossEncoderReRanker:
    """Factory function to get a CrossEncoderReRanker instance.
    
    Args:
        model_name: HuggingFace cross-encoder model
        relevance_threshold: Minimum score to keep chunk
        
    Returns:
        CrossEncoderReRanker instance
    """
    return CrossEncoderReRanker(model_name, relevance_threshold)
