# Requirements Document

## Introduction

The EV Diagnostic Assistant RAG system currently provides inaccurate answers that don't match manual content exactly. This feature improves RAG answer accuracy by replacing the hash-based embedder with semantic embeddings, enhancing chunking strategy, improving the LLM prompt, adding re-ranking, and improving citation accuracy while maintaining backward compatibility with the existing API.

## Glossary

- **RAG_System**: The Retrieval-Augmented Generation system that retrieves manual chunks and generates answers
- **Embedder**: The component that converts text into vector representations for similarity search
- **Semantic_Embedder**: An embedder using sentence-transformers that captures semantic meaning
- **Hash_Embedder**: The current embedder using hash-based token bucketing (LocalHashingEmbedder)
- **Chunk**: A segment of manual text with associated metadata (manual name, page number)
- **Retriever**: The component that searches for relevant chunks given a query
- **Re_Ranker**: A component that re-scores retrieved chunks for improved relevance
- **LLM_Prompt**: The instruction template sent to the language model for answer generation
- **Citation**: A reference to the source manual and page number for retrieved information
- **Manual_Index**: The FAISS index storing chunk embeddings for similarity search
- **Top_K**: The number of chunks to retrieve from the index

## Requirements

### Requirement 1: Replace Hash Embedder with Semantic Embedder

**User Story:** As a service technician, I want the system to understand the semantic meaning of my questions, so that I receive relevant answers even when I use different terminology than the manual.

#### Acceptance Criteria

1. THE RAG_System SHALL use a sentence-transformers model for embedding generation
2. WHEN the Semantic_Embedder encodes text, THE RAG_System SHALL produce embeddings that capture semantic meaning
3. THE RAG_System SHALL use the same Semantic_Embedder for both indexing and query encoding
4. WHEN building the Manual_Index, THE RAG_System SHALL embed all chunks using the Semantic_Embedder
5. WHEN processing a query, THE RAG_System SHALL embed the query using the Semantic_Embedder
6. THE Semantic_Embedder SHALL produce normalized embeddings for cosine similarity comparison

### Requirement 2: Improve Chunking Strategy

**User Story:** As a service technician, I want manual content to be chunked intelligently, so that retrieved chunks contain complete, contextually meaningful information.

#### Acceptance Criteria

1. WHEN splitting page text, THE RAG_System SHALL preserve sentence boundaries
2. WHEN a chunk boundary falls mid-sentence, THE RAG_System SHALL extend to the next sentence boundary
3. THE RAG_System SHALL maintain chunk overlap to preserve context across boundaries
4. WHEN a page contains section headers, THE RAG_System SHALL include headers in relevant chunks
5. THE RAG_System SHALL filter out chunks shorter than the minimum character threshold
6. WHEN extracting chunks from a PDF, THE RAG_System SHALL preserve the page number for each chunk

### Requirement 3: Enhance LLM Prompt for Manual Adherence

**User Story:** As a service technician, I want answers that match the manual content exactly, so that I can trust the information for diagnostic and repair procedures.

#### Acceptance Criteria

1. THE LLM_Prompt SHALL instruct the language model to answer only from provided manual excerpts
2. THE LLM_Prompt SHALL instruct the language model to use exact manual terminology and phrasing
3. THE LLM_Prompt SHALL instruct the language model to cite sources inline using [Source N] format
4. WHEN manual excerpts partially answer a question, THE LLM_Prompt SHALL instruct the language model to state what information is missing
5. THE LLM_Prompt SHALL instruct the language model to prefer step-by-step procedures when available
6. THE LLM_Prompt SHALL instruct the language model to include safety warnings from manual excerpts

### Requirement 4: Add Re-Ranking for Better Relevance

**User Story:** As a service technician, I want the most relevant manual sections to be prioritized, so that I receive the best answer to my specific question.

#### Acceptance Criteria

1. WHEN the Retriever returns chunks, THE Re_Ranker SHALL re-score them for relevance to the query
2. THE Re_Ranker SHALL use cross-encoder scoring for improved relevance assessment
3. WHEN re-ranking is complete, THE RAG_System SHALL sort chunks by re-ranked score in descending order
4. THE RAG_System SHALL filter out chunks below a relevance threshold after re-ranking
5. WHEN re-ranking fails, THE RAG_System SHALL fall back to the original retrieval scores
6. THE Re_Ranker SHALL process all retrieved chunks before filtering

### Requirement 5: Improve Citation Accuracy

**User Story:** As a service technician, I want accurate citations for all information in the answer, so that I can verify the information in the original manual.

#### Acceptance Criteria

1. WHEN generating an answer, THE RAG_System SHALL include inline citations for each piece of information
2. THE RAG_System SHALL map each inline citation to the source manual name and page number
3. WHEN multiple chunks from the same page are used, THE RAG_System SHALL deduplicate citations
4. THE RAG_System SHALL include a Citations section at the end of each answer
5. WHEN a chunk is referenced in the answer, THE RAG_System SHALL include its citation in the Citations section
6. THE Citation SHALL use the format: "Manual_Name p.Page_Number"

### Requirement 6: Maintain Backward Compatibility

**User Story:** As a developer, I want the improved RAG system to work with existing code, so that I don't need to modify the API or frontend.

#### Acceptance Criteria

1. THE RAG_System SHALL maintain the existing function signatures for retrieve_manual_chunks and get_answer
2. THE RAG_System SHALL return RetrievedChunk objects with the same fields (manual, page, text, score)
3. THE RAG_System SHALL maintain the existing Manual_Index file locations (INDEX_FILE, METADATA_FILE)
4. THE RAG_System SHALL maintain the existing build_manual_index function interface
5. WHEN the Manual_Index is rebuilt, THE RAG_System SHALL use the same file paths as before
6. THE RAG_System SHALL maintain the existing DEFAULT_TOP_K value for retrieval

### Requirement 7: Parse and Pretty-Print Configuration

**User Story:** As a developer, I want to configure RAG parameters through a configuration file, so that I can tune the system without modifying code.

#### Acceptance Criteria

1. THE RAG_System SHALL parse configuration from a JSON file
2. THE Configuration_Parser SHALL read parameters for embedding model, chunk size, overlap, and top_k
3. WHEN the configuration file is missing, THE RAG_System SHALL use default values
4. THE Configuration_Parser SHALL validate parameter types and ranges
5. WHEN invalid configuration is detected, THE Configuration_Parser SHALL return a descriptive error
6. THE Pretty_Printer SHALL format Configuration objects back into valid JSON files
7. FOR ALL valid Configuration objects, parsing then printing then parsing SHALL produce an equivalent object (round-trip property)

### Requirement 8: Validate Embedding Dimension Consistency

**User Story:** As a developer, I want the system to detect embedding dimension mismatches, so that I avoid runtime errors when switching embedding models.

#### Acceptance Criteria

1. WHEN loading the Manual_Index, THE RAG_System SHALL verify the embedding dimension matches the current model
2. WHEN a dimension mismatch is detected, THE RAG_System SHALL return a descriptive error message
3. THE Error_Message SHALL indicate the expected dimension and the actual dimension
4. WHEN a dimension mismatch is detected, THE RAG_System SHALL suggest rebuilding the index
5. THE RAG_System SHALL store the embedding dimension in the Manual_Index metadata
6. WHEN building the Manual_Index, THE RAG_System SHALL record the embedding dimension in metadata

### Requirement 9: Handle Empty or Missing Manuals

**User Story:** As a service technician, I want clear feedback when no manuals are indexed, so that I know to upload manuals before asking questions.

#### Acceptance Criteria

1. WHEN no manual files exist, THE RAG_System SHALL return a message indicating no manuals are indexed
2. WHEN the Manual_Index does not exist, THE RAG_System SHALL return a message indicating the index needs to be built
3. THE Error_Message SHALL instruct the user to upload manuals and rebuild the index
4. WHEN retrieve_manual_chunks is called with no index, THE RAG_System SHALL return an empty list
5. WHEN get_answer is called with no relevant chunks, THE RAG_System SHALL return a message suggesting manual upload
6. THE RAG_System SHALL not raise exceptions for missing manuals or index files

### Requirement 10: Preserve Query Performance

**User Story:** As a service technician, I want fast query responses, so that I can quickly diagnose issues without waiting.

#### Acceptance Criteria

1. WHEN processing a query, THE RAG_System SHALL return results within 2 seconds for typical queries
2. THE Retriever SHALL use FAISS for efficient similarity search
3. WHEN re-ranking chunks, THE Re_Ranker SHALL process only the Top_K retrieved chunks
4. THE RAG_System SHALL cache the embedding model to avoid reloading on each query
5. WHEN the Manual_Index is loaded, THE RAG_System SHALL cache it in memory for subsequent queries
6. THE RAG_System SHALL not perform redundant embedding operations for the same query
