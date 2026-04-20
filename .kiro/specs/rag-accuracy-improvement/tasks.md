# Implementation Plan: RAG Accuracy Improvement

## Overview

This implementation plan breaks down the RAG accuracy improvement feature into discrete, actionable tasks. The system will transition from hash-based embeddings to semantic embeddings using sentence-transformers, implement intelligent chunking with sentence boundary preservation, add cross-encoder re-ranking, enhance LLM prompts for manual adherence, and improve citation tracking—all while maintaining backward compatibility with existing APIs.

The implementation follows a phased approach:
1. **Phase 1**: Core components (embedder, chunker, index manager, re-ranker, prompt builder, citation tracker, config manager)
2. **Phase 2**: Property-based and unit tests for all components
3. **Phase 3**: Integration tests and performance validation
4. **Phase 4**: Deployment and documentation

## Tasks

### Phase 1: Core Components Implementation

- [x] 1. Set up project structure and dependencies
  - Create `backend/rag_components/` directory structure
  - Add new dependencies to `backend/requirements.txt`: `sentence-transformers`, `faiss-cpu`, `rank-bm25`, `hypothesis` (for testing)
  - Create `backend/rag_components/__init__.py` with component exports
  - Create `backend/rag_components/models.py` for data models (RetrievedChunk, ChunkMetadata, IndexMetadata, RAGConfig)
  - _Requirements: 1.1, 6.1, 7.1_

- [x] 2. Implement Semantic Embedder component
  - Create `backend/rag_components/embedder.py`
  - Implement `SemanticEmbedder` class with lazy model loading
  - Implement `encode()` method with normalization for cosine similarity
  - Implement `embedding_dimension` property
  - Add global model caching to prevent reloading
  - _Requirements: 1.1, 1.2, 1.3, 1.6, 10.4_

  - [ ]* 2.1 Write property tests for Semantic Embedder
    - **Property 1: Semantic Similarity Preservation** - Verify semantically similar texts have cosine similarity > 0.7, dissimilar texts < 0.3
    - **Property 2: Embedding Normalization** - Verify all embeddings have L2 norm = 1.0 (±1e-6)
    - **Property 20: Model Caching Consistency** - Verify model instance is reused across multiple encode calls
    - **Validates: Requirements 1.2, 1.3, 1.6, 10.4**

  - [ ]* 2.2 Write unit tests for Semantic Embedder
    - Test single text encoding
    - Test batch encoding
    - Test model lazy loading
    - Test normalization verification
    - _Requirements: 1.1, 1.6_

- [x] 3. Implement Intelligent Chunker component
  - Create `backend/rag_components/chunker.py`
  - Implement `IntelligentChunker` class with configurable chunk size, overlap, and minimum length
  - Implement `split_text()` method with sentence boundary detection using regex
  - Implement `extract_chunks_from_page()` method with metadata preservation
  - Implement `split_into_sentences()` helper function
  - _Requirements: 2.1, 2.2, 2.3, 2.5, 2.6_

  - [ ]* 3.1 Write property tests for Intelligent Chunker
    - **Property 3: Chunk Boundary Preservation** - Verify no chunk ends mid-sentence
    - **Property 4: Chunk Overlap Consistency** - Verify consecutive chunks have configured overlap
    - **Property 5: Minimum Chunk Length Enforcement** - Verify all chunks meet minimum length threshold
    - **Property 6: Metadata Preservation in Chunks** - Verify manual name, page number, and chunk ID are correct
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.5, 2.6_

  - [ ]* 3.2 Write unit tests for Intelligent Chunker
    - Test chunking with various text lengths
    - Test sentence boundary detection
    - Test overlap calculation
    - Test minimum length filtering
    - Test header preservation
    - Test metadata extraction
    - _Requirements: 2.1, 2.2, 2.3, 2.5, 2.6_

- [x] 4. Implement FAISS Index Manager component
  - Create `backend/rag_components/index_manager.py`
  - Implement `FAISSIndexManager` class with index lifecycle management
  - Implement `build_index()` method to create and save FAISS index with metadata
  - Implement `load_index()` method with dimension validation
  - Implement `search()` method for similarity search
  - Implement `validate_dimension()` method with descriptive error messages
  - Store embedding dimension in metadata for validation
  - _Requirements: 8.1, 8.2, 8.3, 8.5, 8.6, 10.5_

  - [ ]* 4.1 Write property tests for FAISS Index Manager
    - **Property 15: Embedding Dimension Consistency** - Verify dimension mismatch detection with descriptive error
    - **Property 16: Empty Index Handling** - Verify empty index returns empty list without exception
    - **Property 21: Index Caching Consistency** - Verify index is reused from memory across queries
    - **Validates: Requirements 8.1, 8.2, 8.3, 10.5_

  - [ ]* 4.2 Write unit tests for FAISS Index Manager
    - Test index building and saving
    - Test index loading and validation
    - Test dimension mismatch detection
    - Test empty index handling
    - Test search functionality
    - Test metadata serialization/deserialization
    - _Requirements: 8.1, 8.2, 8.3, 8.5, 8.6_

- [x] 5. Implement Cross-Encoder Re-Ranker component
  - Create `backend/rag_components/reranker.py`
  - Implement `CrossEncoderReRanker` class with cross-encoder model
  - Implement `rerank()` method with score updating and threshold filtering
  - Implement `score_pairs()` method for query-text pair scoring
  - Implement fallback to original scores on error
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 10.3_

  - [ ]* 5.1 Write property tests for Cross-Encoder Re-Ranker
    - **Property 7: Re-Ranking Score Ordering** - Verify chunks sorted in descending order by score
    - **Property 8: Re-Ranking Threshold Filtering** - Verify all chunks meet relevance threshold
    - **Property 9: Re-Ranking Fallback on Error** - Verify fallback to original scores on error
    - **Property 19: Re-Ranker Processing Scope** - Verify exactly top_k chunks are processed
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 10.3_

  - [ ]* 5.2 Write unit tests for Cross-Encoder Re-Ranker
    - Test re-ranking with various chunk counts
    - Test threshold filtering
    - Test fallback on model load error
    - Test fallback on scoring error
    - Test score ordering
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 6. Implement Enhanced Prompt Builder component
  - Create `backend/rag_components/prompt_builder.py`
  - Implement `EnhancedPromptBuilder` class with system and user prompt templates
  - Implement `build_prompt()` method to create chat messages for LLM
  - Implement `format_context()` method to format chunks as numbered sources
  - Ensure prompts enforce manual adherence, exact terminology, and citation requirements
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [ ]* 6.1 Write unit tests for Enhanced Prompt Builder
    - Test prompt building with various chunk counts
    - Test context formatting with source numbering
    - Test citation placeholder generation
    - Test system prompt content
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 7. Implement Citation Tracker component
  - Create `backend/rag_components/citation_tracker.py`
  - Implement `CitationTracker` class for citation extraction and formatting
  - Implement `extract_citations()` method to parse [Source N] references
  - Implement `append_citations()` method to add citations section to answer
  - Implement `deduplicate_citations()` method for unique citations
  - Ensure citations use format "Manual_Name p.Page_Number"
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [ ]* 7.1 Write property tests for Citation Tracker
    - **Property 10: Citation Format Correctness** - Verify citations match "Manual_Name p.Page_Number" format
    - **Property 11: Citation Deduplication** - Verify one citation per manual-page combination
    - **Validates: Requirements 5.3, 5.6_

  - [ ]* 7.2 Write unit tests for Citation Tracker
    - Test citation extraction from answers
    - Test citation formatting
    - Test deduplication
    - Test citation appending
    - Test edge cases (missing sources, malformed citations)
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [x] 8. Implement Configuration Manager component
  - Create `backend/rag_components/config.py`
  - Implement `RAGConfig` dataclass with all configuration parameters
  - Implement `ConfigurationManager` class for parsing and validation
  - Implement `load_config()` method to load from JSON file or use defaults
  - Implement `validate_config()` method with range and type checking
  - Implement `save_config()` method to write configuration to JSON
  - Implement `parse_config()` and `format_config()` methods for JSON serialization
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

  - [ ]* 8.1 Write property tests for Configuration Manager
    - **Property 13: Configuration Round-Trip Parsing** - Verify parse → format → parse produces equivalent config
    - **Property 14: Configuration Validation** - Verify all invariants hold (ranges, types, relationships)
    - **Validates: Requirements 7.4, 7.7_

  - [ ]* 8.2 Write unit tests for Configuration Manager
    - Test JSON parsing
    - Test configuration validation
    - Test default value usage
    - Test round-trip serialization
    - Test error handling for invalid configs
    - Test missing file handling
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

- [x] 9. Implement data models and interfaces
  - Create `backend/rag_components/models.py` with dataclasses:
    - `RetrievedChunk` with manual, page, text, score fields
    - `ChunkMetadata` with id, manual, page, text fields
    - `IndexMetadata` with embedding_dimension, model_name, chunks, created_at fields
  - Implement serialization/deserialization methods (to_dict, from_dict)
  - Implement citation property on RetrievedChunk
  - _Requirements: 6.2, 8.5, 8.6_

  - [ ]* 9.1 Write property tests for data models
    - **Property 12: RetrievedChunk Field Completeness** - Verify all required fields present and valid
    - **Validates: Requirements 6.2_

  - [ ]* 9.2 Write unit tests for data models
    - Test RetrievedChunk creation and properties
    - Test ChunkMetadata serialization/deserialization
    - Test IndexMetadata serialization/deserialization
    - Test citation formatting
    - _Requirements: 6.2, 8.5, 8.6_

- [x] 10. Checkpoint - Core components complete
  - Ensure all core component files are created and importable
  - Verify all classes and methods are implemented
  - Ask the user if questions arise about component interfaces or requirements

### Phase 2: Integration with Existing RAG System

- [x] 11. Integrate Semantic Embedder into RAG pipeline
  - Update `backend/rag.py` or create `backend/rag_improved.py` to use `SemanticEmbedder`
  - Replace `LocalHashingEmbedder` with `SemanticEmbedder` in indexing pipeline
  - Update `build_manual_index()` to use semantic embeddings
  - Update query processing to use semantic embeddings
  - Maintain backward compatibility with existing function signatures
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 6.1, 6.3, 6.4, 6.5_

- [x] 12. Integrate Intelligent Chunker into indexing pipeline
  - Update `build_manual_index()` to use `IntelligentChunker` instead of current chunking
  - Preserve page numbers and manual names in chunk metadata
  - Ensure chunks are extracted with proper metadata
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 6.3_

- [x] 13. Integrate FAISS Index Manager into RAG system
  - Update index building to use `FAISSIndexManager.build_index()`
  - Update index loading to use `FAISSIndexManager.load_index()` with dimension validation
  - Update search to use `FAISSIndexManager.search()`
  - Ensure metadata is stored and loaded correctly
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 6.3, 6.4, 6.5_

- [x] 14. Integrate Cross-Encoder Re-Ranker into query pipeline
  - Update `retrieve_manual_chunks()` to apply re-ranking after FAISS retrieval
  - Implement fallback to original scores on error
  - Filter chunks by relevance threshold after re-ranking
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 6.1_

- [x] 15. Integrate Enhanced Prompt Builder into LLM pipeline
  - Update `get_answer()` to use `EnhancedPromptBuilder` for prompt generation
  - Pass formatted context with source numbering to LLM
  - Ensure LLM receives instructions for manual adherence and citation
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 6.1_

- [x] 16. Integrate Citation Tracker into answer generation
  - Update `get_answer()` to use `CitationTracker` for citation extraction
  - Extract citations from LLM answer
  - Append citations section to final answer
  - Deduplicate citations from multiple chunks
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 6.1_

- [x] 17. Integrate Configuration Manager into RAG system
  - Create `backend/rag_config.json` with default configuration
  - Update RAG initialization to load configuration from file
  - Pass configuration parameters to all components
  - Handle missing configuration file gracefully
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

- [x] 18. Handle empty and missing manuals gracefully
  - Update `retrieve_manual_chunks()` to return empty list when no index exists
  - Update `get_answer()` to return informative message when no manuals indexed
  - Ensure no exceptions are raised for missing manuals or index files
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

- [x] 19. Checkpoint - Integration complete
  - Ensure all components are integrated into RAG pipeline
  - Verify backward compatibility with existing function signatures
  - Verify RetrievedChunk objects have all required fields
  - Ask the user if questions arise about integration points

### Phase 3: Testing and Validation

- [x] 20. Write integration tests for complete RAG pipeline
  - Create `backend/tests/test_rag_integration.py`
  - Test index building from sample PDFs
  - Test query processing end-to-end
  - Test retrieval returns relevant chunks
  - Test re-ranking improves relevance
  - Test citations are accurate and deduplicated
  - Test performance is within 2-second bound
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

  - [ ]* 20.1 Write property tests for end-to-end pipeline
    - **Property 18: Query Performance Bound** - Verify queries complete within 2 seconds
    - **Property 22: Embedding Operation Idempotence** - Verify identical queries produce identical embeddings
    - **Validates: Requirements 10.1, 10.6_

- [x] 21. Write backward compatibility tests
  - Create `backend/tests/test_backward_compatibility.py`
  - Verify existing function signatures work unchanged
  - Verify RetrievedChunk objects have all original fields
  - Verify file paths are unchanged (INDEX_FILE, METADATA_FILE)
  - Verify DEFAULT_TOP_K is maintained
  - Test with existing code that uses the RAG system
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [x] 22. Write performance tests
  - Create `backend/tests/test_performance.py`
  - Measure end-to-end query latency
  - Measure component latencies (embedding, retrieval, re-ranking, LLM)
  - Verify total time < 2 seconds for typical queries
  - Test with varying index sizes (100, 1000, 10000 chunks)
  - Test with varying query complexity
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

- [x] 23. Write error handling tests
  - Create `backend/tests/test_error_handling.py`
  - Test missing index handling
  - Test empty manual handling
  - Test dimension mismatch handling
  - Test configuration errors
  - Test model load failures
  - Test re-ranking failures with fallback
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

- [x] 24. Run all property-based tests
  - Execute all property tests (Properties 1-22)
  - Verify all properties pass with minimum 100 iterations
  - Document any property test failures
  - Fix any implementation issues found by property tests
  - _Requirements: 1.2, 1.3, 1.6, 2.1, 2.2, 2.3, 2.5, 2.6, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 7.4, 7.7, 8.1, 8.2, 8.3, 10.1, 10.3, 10.4, 10.5, 10.6_

- [x] 25. Run all unit tests
  - Execute all unit tests for each component
  - Verify all tests pass
  - Achieve minimum 80% code coverage for core components
  - Document any test failures
  - _Requirements: 1.1, 1.6, 2.1, 2.2, 2.3, 2.5, 2.6, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 8.1, 8.2, 8.3, 8.5, 8.6_

- [x] 26. Run integration tests
  - Execute all integration tests
  - Verify end-to-end pipeline works correctly
  - Verify backward compatibility
  - Verify performance requirements met
  - Document any test failures
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

- [x] 27. Checkpoint - All tests passing
  - Ensure all property tests pass
  - Ensure all unit tests pass
  - Ensure all integration tests pass
  - Ensure performance requirements met
  - Ask the user if questions arise about test results

### Phase 4: Deployment and Documentation

- [x] 28. Update requirements.txt with new dependencies
  - Add `sentence-transformers` for semantic embeddings
  - Add `faiss-cpu` for vector indexing (or `faiss-gpu` if GPU available)
  - Add `rank-bm25` for BM25 ranking (optional, for future enhancements)
  - Add `hypothesis` for property-based testing
  - Pin versions to ensure reproducibility
  - _Requirements: 1.1, 4.1, 7.1_

- [x] 29. Create configuration file template
  - Create `backend/rag_config.json.template` with default values
  - Document all configuration parameters
  - Include comments explaining each parameter
  - Provide example configurations for different use cases
  - _Requirements: 7.1, 7.2, 7.3_

- [x] 30. Update API documentation
  - Document new RAG components and their interfaces
  - Document configuration parameters and their effects
  - Document error handling and fallback behavior
  - Document backward compatibility guarantees
  - Update existing API documentation if signatures changed
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [x] 31. Create migration guide for existing systems
  - Document steps to upgrade from hash-based to semantic embeddings
  - Explain index rebuild process
  - Document configuration migration
  - Provide rollback instructions if needed
  - Document performance improvements and accuracy gains
  - _Requirements: 1.1, 6.1, 6.3, 6.4, 6.5_

- [x] 32. Rebuild manual index with semantic embeddings
  - Run `build_manual_index()` with new `SemanticEmbedder`
  - Verify all manuals are indexed correctly
  - Verify index dimension is recorded in metadata
  - Verify index file sizes and performance
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 8.1, 8.5, 8.6_

- [x] 33. Deploy to production
  - Deploy updated RAG system to production environment
  - Verify all components are working correctly
  - Monitor query latency and accuracy
  - Monitor error rates and fallback behavior
  - Collect user feedback on answer quality
  - _Requirements: 1.1, 3.1, 4.1, 5.1, 6.1, 10.1_

- [x] 34. Final checkpoint - Deployment complete
  - Ensure all components are deployed and working
  - Ensure all tests pass in production environment
  - Ensure performance requirements met in production
  - Ensure backward compatibility maintained
  - Ask the user if questions arise about deployment

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP, but are strongly recommended for production quality
- Each task references specific requirements for traceability
- Property-based tests validate universal correctness properties across all valid inputs
- Unit tests validate specific examples and edge cases
- Integration tests validate the complete pipeline
- Performance tests ensure the 2-second query response time requirement is met
- All components maintain backward compatibility with existing APIs
- Configuration is managed through JSON files for easy tuning without code changes
- Error handling is graceful with informative messages and fallback behavior
- Model caching and index caching ensure performance requirements are met

## Implementation Order

**Recommended implementation order for parallel work:**

1. **Start with Phase 1 (Core Components)** - All components can be implemented in parallel:
   - Tasks 1-9 can be done by different developers
   - Each component is independent until integration

2. **Then Phase 2 (Integration)** - Integrate components sequentially:
   - Tasks 11-18 depend on Phase 1 completion
   - Integration should be done in order to catch issues early

3. **Then Phase 3 (Testing)** - Test and validate:
   - Tasks 20-27 can be done in parallel
   - All tests should pass before deployment

4. **Finally Phase 4 (Deployment)** - Deploy and document:
   - Tasks 28-34 are sequential
   - Deployment should be done after all tests pass

## Success Criteria

- All 22 correctness properties pass with 100+ iterations each
- All unit tests pass with 80%+ code coverage
- All integration tests pass
- Query latency < 2 seconds for typical queries
- Backward compatibility maintained with existing APIs
- Configuration can be managed through JSON files
- Error handling is graceful with informative messages
- All components are documented and tested
