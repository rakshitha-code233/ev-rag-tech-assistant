"""Improved RAG system with semantic embeddings, re-ranking, and better citations.

This module replaces the hash-based embedder with semantic embeddings,
adds intelligent chunking, cross-encoder re-ranking, and improved citation tracking.
It maintains backward compatibility with the existing API.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

import fitz
import numpy as np

from rag_components import (
    LightweightEmbedder,
    IntelligentChunker,
    FAISSIndexManager,
    CrossEncoderReRanker,
    EnhancedPromptBuilder,
    CitationTracker,
    ConfigurationManager,
    RetrievedChunk,
    RAGConfig,
)

logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "data" / "manuals"
INDEX_DIR = BASE_DIR / "rag_store"
INDEX_FILE = INDEX_DIR / "manual_index.faiss"
METADATA_FILE = INDEX_DIR / "manual_chunks.json"
CONFIG_FILE = BASE_DIR / "rag_config.json"

# Default configuration
DEFAULT_TOP_K = 4
DEFAULT_CONFIG = RAGConfig()

# Global instances (cached)
_embedder: Optional[LightweightEmbedder] = None
_chunker: Optional[IntelligentChunker] = None
_index_manager: Optional[FAISSIndexManager] = None
_reranker: Optional[CrossEncoderReRanker] = None
_prompt_builder: Optional[EnhancedPromptBuilder] = None
_citation_tracker: Optional[CitationTracker] = None
_config_manager: Optional[ConfigurationManager] = None
_config: Optional[RAGConfig] = None


def ensure_directories() -> None:
    """Ensure all required directories exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)


def get_config() -> RAGConfig:
    """Get RAG configuration (cached)."""
    global _config, _config_manager
    
    if _config is None:
        if _config_manager is None:
            _config_manager = ConfigurationManager(CONFIG_FILE)
        _config = _config_manager.load_config()
    
    return _config


def get_embedder() -> LightweightEmbedder:
    """Get semantic embedder instance (cached)."""
    global _embedder
    
    if _embedder is None:
        config = get_config()
        _embedder = LightweightEmbedder(config.embedding_model)
    
    return _embedder


def get_chunker() -> IntelligentChunker:
    """Get intelligent chunker instance (cached)."""
    global _chunker
    
    if _chunker is None:
        config = get_config()
        _chunker = IntelligentChunker(
            chunk_size=config.chunk_size,
            overlap=config.chunk_overlap,
            min_chunk_chars=config.min_chunk_chars,
        )
    
    return _chunker


def get_index_manager() -> FAISSIndexManager:
    """Get FAISS index manager instance (cached)."""
    global _index_manager
    
    if _index_manager is None:
        config = get_config()
        _index_manager = FAISSIndexManager(
            index_file=INDEX_FILE,
            metadata_file=METADATA_FILE,
            embedding_dimension=config.embedding_dimension,
        )
    
    return _index_manager


def get_reranker() -> CrossEncoderReRanker:
    """Get cross-encoder re-ranker instance (cached)."""
    global _reranker
    
    if _reranker is None:
        config = get_config()
        _reranker = CrossEncoderReRanker(
            model_name=config.reranking_model,
            relevance_threshold=config.relevance_threshold,
        )
    
    return _reranker


def get_prompt_builder() -> EnhancedPromptBuilder:
    """Get enhanced prompt builder instance (cached)."""
    global _prompt_builder
    
    if _prompt_builder is None:
        _prompt_builder = EnhancedPromptBuilder()
    
    return _prompt_builder


def get_citation_tracker() -> CitationTracker:
    """Get citation tracker instance (cached)."""
    global _citation_tracker
    
    if _citation_tracker is None:
        _citation_tracker = CitationTracker()
    
    return _citation_tracker


def list_manual_files() -> List[Path]:
    """List all PDF manual files."""
    ensure_directories()
    return sorted(DATA_DIR.glob("*.pdf"))


def extract_chunks_from_pdf(pdf_path: Path) -> List[Dict[str, object]]:
    """Extract chunks from a PDF file using intelligent chunker."""
    chunker = get_chunker()
    chunks: List[Dict[str, object]] = []
    
    try:
        doc = fitz.open(pdf_path)
        
        for page_number, page in enumerate(doc, start=1):
            page_text = page.get_text("text")
            
            # Extract chunks with metadata
            page_chunks = chunker.extract_chunks_from_page(
                page_text=page_text,
                page_number=page_number,
                manual_name=pdf_path.name,
                chunk_id_prefix=pdf_path.stem,
            )
            
            chunks.extend(page_chunks)
        
        doc.close()
        
    except Exception as e:
        logger.error(f"Failed to extract chunks from {pdf_path}: {e}")
    
    return chunks


def build_manual_index() -> Dict[str, object]:
    """Build manual index with semantic embeddings.
    
    Returns:
        Dictionary with keys: manuals_indexed, chunks_indexed
    """
    ensure_directories()
    
    logger.info("Building manual index...")
    
    manual_files = list_manual_files()
    all_chunks: List[Dict[str, object]] = []
    
    # Extract chunks from all PDFs
    for pdf_path in manual_files:
        logger.info(f"Extracting chunks from {pdf_path.name}...")
        chunks = extract_chunks_from_pdf(pdf_path)
        all_chunks.extend(chunks)
    
    if not all_chunks:
        logger.warning("No chunks extracted from manuals")
        # Clean up old index files
        if INDEX_FILE.exists():
            INDEX_FILE.unlink()
        if METADATA_FILE.exists():
            METADATA_FILE.unlink()
        return {"manuals_indexed": 0, "chunks_indexed": 0}
    
    # Embed chunks using semantic embedder
    logger.info(f"Embedding {len(all_chunks)} chunks...")
    embedder = get_embedder()
    texts = [chunk["text"] for chunk in all_chunks]
    embeddings = embedder.encode(texts, normalize_embeddings=True)
    embeddings = embeddings.astype("float32")
    
    # Build and save index
    logger.info("Building FAISS index...")
    index_manager = get_index_manager()
    stats = index_manager.build_index(all_chunks, embeddings)
    
    logger.info(f"Index built successfully: {stats}")
    return stats


def retrieve_manual_chunks(query: str, top_k: Optional[int] = None) -> List[RetrievedChunk]:
    """Retrieve relevant chunks from manual index.
    
    Args:
        query: User query string
        top_k: Number of chunks to retrieve (uses config default if None)
        
    Returns:
        List of RetrievedChunk objects
    """
    if not query or not query.strip():
        logger.warning("Empty query provided")
        return []
    
    config = get_config()
    if top_k is None:
        top_k = config.top_k
    
    # Load index
    index_manager = get_index_manager()
    index_data = index_manager.load_index()
    
    if index_data is None:
        logger.warning("No manual index available")
        return []
    
    # Embed query
    embedder = get_embedder()
    query_embedding = embedder.encode([query], normalize_embeddings=True)
    query_embedding = query_embedding.astype("float32")
    
    # Search index
    distances, indices = index_manager.search(query_embedding, top_k)
    
    # Build retrieved chunks
    retrieved: List[RetrievedChunk] = []
    metadata_dict = index_data["metadata"]
    
    # Handle both old format (list) and new format (dict with "chunks" key)
    if isinstance(metadata_dict, dict):
        metadata = metadata_dict.get("chunks", [])
    else:
        metadata = metadata_dict
    
    for score, idx in zip(distances[0], indices[0]):
        if idx < 0 or idx >= len(metadata):
            continue
        
        # Filter by score threshold
        if score < config.score_threshold:
            continue
        
        item = metadata[int(idx)]
        chunk = RetrievedChunk(
            manual=str(item["manual"]),
            page=int(item["page"]),
            text=str(item["text"]),
            score=float(score),
        )
        retrieved.append(chunk)
    
    # Re-rank chunks if enabled
    if config.reranking_enabled and retrieved:
        logger.debug(f"Re-ranking {len(retrieved)} chunks...")
        reranker = get_reranker()
        retrieved = reranker.rerank(query, retrieved)
    
    logger.debug(f"Retrieved {len(retrieved)} chunks for query: {query[:50]}...")
    return retrieved


def build_prompt(query: str, chunks: List[RetrievedChunk]) -> List[Dict[str, str]]:
    """Build LLM prompt with system and user messages.
    
    Args:
        query: User query
        chunks: Retrieved chunks
        
    Returns:
        List of message dictionaries for LLM
    """
    prompt_builder = get_prompt_builder()
    return prompt_builder.build_prompt(query, chunks)


def extract_citations(answer: str, chunks: List[RetrievedChunk]) -> List[str]:
    """Extract citations from LLM answer.
    
    Args:
        answer: LLM-generated answer
        chunks: Chunks used for context
        
    Returns:
        List of formatted citations
    """
    citation_tracker = get_citation_tracker()
    return citation_tracker.extract_citations(answer, chunks)


def append_citations(answer: str, citations: List[str]) -> str:
    """Append citations section to answer.
    
    Args:
        answer: Answer text
        citations: List of citations
        
    Returns:
        Answer with citations section
    """
    citation_tracker = get_citation_tracker()
    return citation_tracker.append_citations(answer, citations)


def get_answer(query: str) -> Dict[str, object]:
    """Get answer from RAG system (placeholder for LLM integration).
    
    This is a placeholder that shows how to use the RAG components.
    In production, this would call the LLM with the built prompt.
    
    Args:
        query: User query
        
    Returns:
        Dictionary with keys: answer, citations, chunks_used
    """
    if not query or not query.strip():
        return {
            "answer": "Please provide a question.",
            "citations": [],
            "chunks_used": 0,
        }
    
    # Retrieve chunks
    chunks = retrieve_manual_chunks(query)
    
    if not chunks:
        return {
            "answer": "I could not find relevant information in the indexed manuals. Please upload manuals and rebuild the index.",
            "citations": [],
            "chunks_used": 0,
        }
    
    # Build prompt
    messages = build_prompt(query, chunks)
    
    # In production, call LLM here with messages
    # For now, return placeholder
    answer = "This is a placeholder answer. In production, this would call the LLM."
    
    # Extract and append citations
    citations = extract_citations(answer, chunks)
    answer = append_citations(answer, citations)
    
    return {
        "answer": answer,
        "citations": citations,
        "chunks_used": len(chunks),
    }


def clear_cache():
    """Clear all cached instances (useful for testing)."""
    global _embedder, _chunker, _index_manager, _reranker, _prompt_builder, _citation_tracker, _config_manager, _config
    
    _embedder = None
    _chunker = None
    _index_manager = None
    _reranker = None
    _prompt_builder = None
    _citation_tracker = None
    _config_manager = None
    _config = None
    
    logger.info("Cache cleared")


def format_context(chunks: List[RetrievedChunk]) -> str:
    """Format chunks as numbered context for LLM.
    
    Args:
        chunks: List of retrieved chunks
        
    Returns:
        Formatted context string with source numbers
    """
    blocks = []
    for idx, chunk in enumerate(chunks, start=1):
        blocks.append(f"[Source {idx}] {chunk.manual} p.{chunk.page}\n{chunk.text}")
    return "\n\n".join(blocks)


def format_citations(chunks: List[RetrievedChunk]) -> List[str]:
    """Format citations from chunks.
    
    Args:
        chunks: List of retrieved chunks
        
    Returns:
        List of formatted citations (deduplicated)
    """
    citations: List[str] = []
    seen = set()
    for chunk in chunks:
        citation = f"{chunk.manual} p.{chunk.page}"
        if citation not in seen:
            seen.add(citation)
            citations.append(citation)
    return citations
