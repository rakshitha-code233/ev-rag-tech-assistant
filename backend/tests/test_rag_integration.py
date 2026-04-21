"""Integration tests for complete RAG pipeline."""

import json
import tempfile
from pathlib import Path
from typing import List

import pytest
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


class TestLightweightEmbedder:
    """Test Lightweight Embedder component."""
    
    def test_encode_single_text(self):
        """Test encoding a single text."""
        embedder = LightweightEmbedder()
        texts = ["Hello world"]
        embeddings = embedder.encode(texts)
        
        assert embeddings.shape == (1, 384)
        assert np.allclose(np.linalg.norm(embeddings[0]), 1.0, atol=1e-6)
    
    def test_encode_multiple_texts(self):
        """Test encoding multiple texts."""
        embedder = LightweightEmbedder()
        texts = ["Hello world", "How are you", "This is a test"]
        embeddings = embedder.encode(texts)
        
        assert embeddings.shape == (3, 384)
        # Check normalization
        for emb in embeddings:
            assert np.allclose(np.linalg.norm(emb), 1.0, atol=1e-6)
    
    def test_semantic_similarity(self):
        """Test that semantically similar texts have high similarity."""
        embedder = LightweightEmbedder()
        
        # Similar texts
        similar_texts = ["charging the car", "charge the vehicle"]
        embeddings = embedder.encode(similar_texts)
        
        # Cosine similarity (dot product for normalized vectors)
        similarity = np.dot(embeddings[0], embeddings[1])
        assert similarity > 0.7, f"Similar texts should have similarity > 0.7, got {similarity}"
    
    def test_embedding_dimension(self):
        """Test embedding dimension property."""
        embedder = LightweightEmbedder()
        assert embedder.embedding_dimension == 1


class TestIntelligentChunker:
    """Test Intelligent Chunker component."""
    
    def test_split_text_basic(self):
        """Test basic text splitting."""
        chunker = IntelligentChunker(chunk_size=100, overlap=20, min_chunk_chars=30)
        text = "This is a test. This is another sentence. And one more sentence here."
        chunks = chunker.split_text(text)
        
        assert len(chunks) > 0
        for chunk in chunks:
            assert len(chunk) >= 30
    
    def test_sentence_boundary_preservation(self):
        """Test that chunks preserve sentence boundaries."""
        chunker = IntelligentChunker(chunk_size=50, overlap=10, min_chunk_chars=20)
        text = "First sentence. Second sentence. Third sentence."
        chunks = chunker.split_text(text)
        
        # No chunk should end mid-sentence
        for chunk in chunks:
            # Should end with punctuation or be part of a sentence
            assert chunk[-1] in '.!?' or chunk.endswith('sentence')
    
    def test_chunk_overlap(self):
        """Test that chunks have overlap."""
        chunker = IntelligentChunker(chunk_size=100, overlap=50, min_chunk_chars=30)
        text = "Word " * 50  # Create long text
        chunks = chunker.split_text(text)
        
        if len(chunks) > 1:
            # Check that consecutive chunks have overlap
            for i in range(len(chunks) - 1):
                # Find common substring
                chunk1_end = chunks[i][-50:]
                chunk2_start = chunks[i+1][:50]
                # There should be some overlap
                assert len(chunk1_end) > 0 and len(chunk2_start) > 0
    
    def test_extract_chunks_from_page(self):
        """Test extracting chunks with metadata."""
        chunker = IntelligentChunker()
        page_text = "This is page content. " * 20
        chunks = chunker.extract_chunks_from_page(
            page_text=page_text,
            page_number=1,
            manual_name="test.pdf",
            chunk_id_prefix="test",
        )
        
        assert len(chunks) > 0
        for chunk in chunks:
            assert "id" in chunk
            assert "manual" in chunk
            assert "page" in chunk
            assert "text" in chunk
            assert chunk["manual"] == "test.pdf"
            assert chunk["page"] == 1


class TestFAISSIndexManager:
    """Test FAISS Index Manager component."""
    
    def test_build_and_load_index(self):
        """Test building and loading FAISS index."""
        with tempfile.TemporaryDirectory() as tmpdir:
            index_file = Path(tmpdir) / "test.faiss"
            metadata_file = Path(tmpdir) / "test_metadata.json"
            
            manager = FAISSIndexManager(index_file, metadata_file, 384)
            
            # Create test data
            chunks = [
                {"id": "1", "manual": "test.pdf", "page": 1, "text": "Test chunk 1"},
                {"id": "2", "manual": "test.pdf", "page": 2, "text": "Test chunk 2"},
            ]
            embeddings = np.random.randn(2, 384).astype(np.float32)
            embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            
            # Build index
            stats = manager.build_index(chunks, embeddings)
            assert stats["chunks_indexed"] == 2
            assert stats["manuals_indexed"] == 1
            
            # Load index
            result = manager.load_index()
            assert result is not None
            assert len(result["metadata"]["chunks"]) == 2
    
    def test_dimension_validation(self):
        """Test dimension mismatch detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            index_file = Path(tmpdir) / "test.faiss"
            metadata_file = Path(tmpdir) / "test_metadata.json"
            
            # Create index with 384 dimensions
            manager = FAISSIndexManager(index_file, metadata_file, 384)
            chunks = [{"id": "1", "manual": "test.pdf", "page": 1, "text": "Test"}]
            embeddings = np.random.randn(1, 384).astype(np.float32)
            embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            manager.build_index(chunks, embeddings)
            
            # Try to load with different dimension
            manager_wrong = FAISSIndexManager(index_file, metadata_file, 768)
            with pytest.raises(ValueError, match="dimension mismatch"):
                manager_wrong.load_index()


class TestCrossEncoderReRanker:
    """Test Cross-Encoder Re-Ranker component."""
    
    def test_rerank_chunks(self):
        """Test re-ranking chunks."""
        reranker = CrossEncoderReRanker(relevance_threshold=0.0)
        
        chunks = [
            RetrievedChunk("test.pdf", 1, "This is about charging", 0.5),
            RetrievedChunk("test.pdf", 2, "This is about batteries", 0.6),
            RetrievedChunk("test.pdf", 3, "This is about charging systems", 0.4),
        ]
        
        query = "How to charge the vehicle"
        reranked = reranker.rerank(query, chunks)
        
        # Should return chunks sorted by score
        assert len(reranked) > 0
        for i in range(len(reranked) - 1):
            assert reranked[i].score >= reranked[i+1].score
    
    def test_relevance_threshold_filtering(self):
        """Test that chunks below threshold are filtered."""
        reranker = CrossEncoderReRanker(relevance_threshold=0.5)
        
        chunks = [
            RetrievedChunk("test.pdf", 1, "Relevant content", 0.8),
            RetrievedChunk("test.pdf", 2, "Irrelevant content", 0.2),
        ]
        
        query = "Test query"
        reranked = reranker.rerank(query, chunks)
        
        # Only high-scoring chunks should remain
        assert all(chunk.score >= 0.5 for chunk in reranked)


class TestEnhancedPromptBuilder:
    """Test Enhanced Prompt Builder component."""
    
    def test_build_prompt(self):
        """Test building LLM prompt."""
        builder = EnhancedPromptBuilder()
        
        chunks = [
            RetrievedChunk("test.pdf", 1, "Test content 1", 0.9),
            RetrievedChunk("test.pdf", 2, "Test content 2", 0.8),
        ]
        
        query = "What is this?"
        messages = builder.build_prompt(query, chunks)
        
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "What is this?" in messages[1]["content"]
    
    def test_format_context(self):
        """Test context formatting."""
        builder = EnhancedPromptBuilder()
        
        chunks = [
            RetrievedChunk("test.pdf", 1, "Content 1", 0.9),
            RetrievedChunk("test.pdf", 2, "Content 2", 0.8),
        ]
        
        context = builder.format_context(chunks)
        
        assert "[Source 1]" in context
        assert "[Source 2]" in context
        assert "test.pdf p.1" in context
        assert "test.pdf p.2" in context


class TestCitationTracker:
    """Test Citation Tracker component."""
    
    def test_extract_citations(self):
        """Test extracting citations from answer."""
        tracker = CitationTracker()
        
        chunks = [
            RetrievedChunk("test.pdf", 1, "Content 1", 0.9),
            RetrievedChunk("test.pdf", 2, "Content 2", 0.8),
        ]
        
        answer = "According to [Source 1], this is true. [Source 2] also confirms this."
        citations = tracker.extract_citations(answer, chunks)
        
        assert len(citations) == 2
        assert "test.pdf p.1" in citations
        assert "test.pdf p.2" in citations
    
    def test_citation_deduplication(self):
        """Test citation deduplication."""
        tracker = CitationTracker()
        
        chunks = [
            RetrievedChunk("test.pdf", 1, "Content 1", 0.9),
            RetrievedChunk("test.pdf", 1, "Content 1 duplicate", 0.8),
            RetrievedChunk("test.pdf", 2, "Content 2", 0.7),
        ]
        
        citations = tracker.deduplicate_citations(chunks)
        
        # Should have only 2 unique citations
        assert len(citations) == 2
        assert "test.pdf p.1" in citations
        assert "test.pdf p.2" in citations
    
    def test_append_citations(self):
        """Test appending citations to answer."""
        tracker = CitationTracker()
        
        answer = "This is the answer."
        citations = ["test.pdf p.1", "test.pdf p.2"]
        
        result = tracker.append_citations(answer, citations)
        
        assert "Citations:" in result
        assert "test.pdf p.1" in result
        assert "test.pdf p.2" in result


class TestConfigurationManager:
    """Test Configuration Manager component."""
    
    def test_load_default_config(self):
        """Test loading default configuration."""
        manager = ConfigurationManager()
        config = manager.load_config()
        
        assert config.embedding_model == "all-MiniLM-L6-v2"
        assert config.chunk_size == 700
        assert config.top_k == 4
    
    def test_validate_config(self):
        """Test configuration validation."""
        manager = ConfigurationManager()
        
        # Valid config
        config = RAGConfig()
        manager.validate_config(config)  # Should not raise
        
        # Invalid config
        config.chunk_size = -1
        with pytest.raises(ValueError):
            manager.validate_config(config)
    
    def test_round_trip_serialization(self):
        """Test parse -> format -> parse round trip."""
        manager = ConfigurationManager()
        
        config1 = RAGConfig(chunk_size=800, top_k=5)
        json_str = manager.format_config(config1)
        config2 = manager.parse_config(json_str)
        
        assert config1.chunk_size == config2.chunk_size
        assert config1.top_k == config2.top_k


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
