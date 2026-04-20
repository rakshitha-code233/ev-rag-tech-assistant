# RAG System API Documentation

## Overview

The improved RAG (Retrieval-Augmented Generation) system provides accurate answers from uploaded manuals using semantic embeddings, intelligent chunking, cross-encoder re-ranking, and enhanced citation tracking.

## Key Improvements

### 1. Semantic Embeddings
- **Replaces**: Hash-based `LocalHashingEmbedder`
- **Uses**: `sentence-transformers` with `all-MiniLM-L6-v2` model
- **Benefit**: Captures semantic meaning, not just token matching
- **Performance**: 384-dimensional embeddings, normalized for cosine similarity

### 2. Intelligent Chunking
- **Preserves**: Sentence boundaries (no mid-sentence splits)
- **Maintains**: Context overlap between chunks (default 100 characters)
- **Filters**: Chunks below minimum length (default 120 characters)
- **Metadata**: Preserves manual name and page number for each chunk

### 3. Cross-Encoder Re-Ranking
- **Model**: `cross-encoder/ms-marco-MiniLM-L-6-v2`
- **Purpose**: Re-scores retrieved chunks for improved relevance
- **Threshold**: Filters chunks below relevance threshold (default 0.3)
- **Fallback**: Uses original FAISS scores if re-ranking fails

### 4. Enhanced Citation Tracking
- **Format**: `Manual_Name p.Page_Number`
- **Deduplication**: Removes duplicate citations (same manual + page)
- **Inline**: Supports `[Source N]` format in LLM responses
- **Accuracy**: Tracks exact source for each piece of information

## Core Components

### SemanticEmbedder
Converts text into semantic embeddings using transformer models.

```python
from rag_components import SemanticEmbedder

embedder = SemanticEmbedder(model_name="all-MiniLM-L6-v2")
embeddings = embedder.encode(texts, normalize_embeddings=True)
# Returns: numpy array of shape (N, 384)
```

**Methods:**
- `encode(texts, convert_to_numpy=True, normalize_embeddings=True)` - Encode texts to embeddings
- `embedding_dimension` - Get embedding dimension (384)

### IntelligentChunker
Splits text while preserving sentence boundaries and maintaining overlap.

```python
from rag_components import IntelligentChunker

chunker = IntelligentChunker(chunk_size=700, overlap=100, min_chunk_chars=120)
chunks = chunker.split_text(text)
# Returns: List of text chunks

# Extract chunks with metadata
page_chunks = chunker.extract_chunks_from_page(
    page_text=text,
    page_number=1,
    manual_name="Tesla_Model3.pdf",
    chunk_id_prefix="Tesla_Model3"
)
# Returns: List of dicts with id, manual, page, text
```

**Methods:**
- `split_text(text)` - Split text into chunks
- `extract_chunks_from_page(page_text, page_number, manual_name, chunk_id_prefix)` - Extract chunks with metadata
- `split_into_sentences(text)` - Static method to split text into sentences

### FAISSIndexManager
Manages FAISS vector index for similarity search.

```python
from rag_components import FAISSIndexManager
from pathlib import Path

manager = FAISSIndexManager(
    index_file=Path("rag_store/manual_index.faiss"),
    metadata_file=Path("rag_store/manual_chunks.json"),
    embedding_dimension=384
)

# Build index
stats = manager.build_index(chunks, embeddings)
# Returns: {"manuals_indexed": 2, "chunks_indexed": 1500}

# Load index
result = manager.load_index()
# Returns: {"index": faiss_index, "metadata": chunk_metadata}

# Search
distances, indices = manager.search(query_embedding, top_k=4)
# Returns: (distances array, indices array)
```

**Methods:**
- `build_index(chunks, embeddings)` - Build and save FAISS index
- `load_index()` - Load index with dimension validation
- `search(query_embedding, top_k)` - Search for similar chunks
- `validate_dimension(index)` - Validate embedding dimension

### CrossEncoderReRanker
Re-ranks retrieved chunks using cross-encoder scoring.

```python
from rag_components import CrossEncoderReRanker

reranker = CrossEncoderReRanker(
    model_name="cross-encoder/ms-marco-MiniLM-L-6-v2",
    relevance_threshold=0.3
)

reranked_chunks = reranker.rerank(query, chunks)
# Returns: List of RetrievedChunk objects, sorted by relevance
```

**Methods:**
- `rerank(query, chunks)` - Re-rank chunks by relevance
- `score_pairs(query, texts)` - Score query-text pairs

### EnhancedPromptBuilder
Builds LLM prompts that enforce manual adherence.

```python
from rag_components import EnhancedPromptBuilder

builder = EnhancedPromptBuilder()

messages = builder.build_prompt(query, chunks)
# Returns: [
#   {"role": "system", "content": system_prompt},
#   {"role": "user", "content": user_prompt}
# ]

context = builder.format_context(chunks)
# Returns: Formatted context with [Source N] references
```

**Methods:**
- `build_prompt(query, chunks)` - Build system and user messages
- `format_context(chunks)` - Format chunks as numbered sources

### CitationTracker
Extracts and formats citations from answers.

```python
from rag_components import CitationTracker

tracker = CitationTracker()

citations = tracker.extract_citations(answer, chunks)
# Returns: List of formatted citations

answer_with_citations = tracker.append_citations(answer, citations)
# Returns: Answer with Citations section appended

unique_citations = tracker.deduplicate_citations(chunks)
# Returns: Deduplicated list of citations
```

**Methods:**
- `extract_citations(answer, chunks)` - Extract citations from answer
- `append_citations(answer, citations)` - Append citations section
- `deduplicate_citations(chunks)` - Get unique citations from chunks

### ConfigurationManager
Manages RAG configuration from JSON files.

```python
from rag_components import ConfigurationManager
from pathlib import Path

manager = ConfigurationManager(config_path=Path("rag_config.json"))

config = manager.load_config()
# Returns: RAGConfig instance with all parameters

manager.validate_config(config)
# Raises ValueError if configuration is invalid

json_str = manager.format_config(config)
# Returns: Pretty-printed JSON string

manager.save_config(config, Path("rag_config.json"))
# Saves configuration to JSON file
```

**Methods:**
- `load_config()` - Load configuration from file or use defaults
- `validate_config(config)` - Validate configuration parameters
- `save_config(config, path)` - Save configuration to JSON
- `parse_config(json_str)` - Parse configuration from JSON string
- `format_config(config)` - Format configuration as JSON string

## Data Models

### RetrievedChunk
Represents a chunk retrieved from the manual index.

```python
@dataclass
class RetrievedChunk:
    manual: str          # Manual filename (e.g., "Tesla_Model3.pdf")
    page: int            # Page number (1-indexed)
    text: str            # Chunk text content
    score: float         # Relevance score (0-1 range)
    
    @property
    def citation(self) -> str:
        """Format citation as 'Manual_Name p.Page_Number'."""
```

### RAGConfig
RAG system configuration.

```python
@dataclass
class RAGConfig:
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
```

## Improved RAG Pipeline

The `rag_improved.py` module provides the complete integrated RAG pipeline:

```python
from rag_improved import (
    build_manual_index,
    retrieve_manual_chunks,
    build_prompt,
    extract_citations,
    append_citations,
    get_answer,
)

# Build index from manuals
stats = build_manual_index()
# Returns: {"manuals_indexed": 2, "chunks_indexed": 1500}

# Retrieve chunks for query
chunks = retrieve_manual_chunks("How to charge the vehicle?", top_k=4)
# Returns: List of RetrievedChunk objects

# Build LLM prompt
messages = build_prompt("How to charge the vehicle?", chunks)
# Returns: List of message dicts for LLM

# Extract citations from answer
citations = extract_citations(answer, chunks)
# Returns: List of formatted citations

# Append citations to answer
final_answer = append_citations(answer, citations)
# Returns: Answer with Citations section

# Get complete answer (placeholder for LLM integration)
result = get_answer("How to charge the vehicle?")
# Returns: {"answer": "...", "citations": [...], "chunks_used": 4}
```

## Configuration

Create `backend/rag_config.json` from the template:

```bash
cp backend/rag_config.json.template backend/rag_config.json
```

Edit parameters as needed:

```json
{
  "embedding": {
    "model_name": "all-MiniLM-L6-v2",
    "dimension": 384
  },
  "chunking": {
    "chunk_size": 700,
    "overlap": 100,
    "min_chunk_chars": 120
  },
  "retrieval": {
    "top_k": 4,
    "score_threshold": 0.20
  },
  "reranking": {
    "enabled": true,
    "model_name": "cross-encoder/ms-marco-MiniLM-L-6-v2",
    "relevance_threshold": 0.3
  },
  "llm": {
    "model": "llama-3.3-70b-versatile",
    "temperature": 0.2
  }
}
```

## Backward Compatibility

The improved RAG system maintains backward compatibility with existing code:

- **Function Signatures**: `retrieve_manual_chunks()` and `get_answer()` have the same signatures
- **Data Models**: `RetrievedChunk` has the same fields (manual, page, text, score)
- **File Paths**: Index files are stored in the same locations
- **Default Values**: `DEFAULT_TOP_K` and other constants are preserved

## Performance

- **Query Latency**: < 2 seconds for typical queries (embedding + retrieval + re-ranking + LLM)
- **Embedding**: ~100ms for 4 chunks
- **Retrieval**: ~10ms for FAISS search
- **Re-ranking**: ~50ms for 4 chunks
- **Model Caching**: Models are cached globally to avoid reloading

## Error Handling

All components implement graceful error handling:

- **Missing Index**: Returns empty list instead of raising exception
- **Re-ranking Failure**: Falls back to original FAISS scores
- **Model Load Failure**: Logs warning and uses cached model
- **Invalid Configuration**: Uses default values

## Testing

Run the test suite:

```bash
cd backend
pytest tests/test_rag_integration.py -v
```

Tests cover:
- Semantic embeddings (similarity, normalization)
- Intelligent chunking (boundaries, overlap, metadata)
- FAISS index management (build, load, dimension validation)
- Cross-encoder re-ranking (scoring, threshold filtering)
- Enhanced prompts (building, context formatting)
- Citation tracking (extraction, deduplication)
- Configuration management (parsing, validation, round-trip)

## Migration from Hash-Based Embedder

See `MIGRATION_GUIDE.md` for detailed migration instructions.

## References

- [Sentence Transformers](https://www.sbert.net/)
- [FAISS](https://github.com/facebookresearch/faiss)
- [Cross-Encoders](https://www.sbert.net/docs/pretrained-models/ce-models.html)
- [MS MARCO Dataset](https://microsoft.github.io/msmarco/)
