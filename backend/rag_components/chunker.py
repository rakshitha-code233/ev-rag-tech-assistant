"""Intelligent Chunker for RAG system with sentence boundary preservation."""

import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class IntelligentChunker:
    """Sentence-boundary-aware text chunker.
    
    Splits manual text while preserving sentence boundaries and maintaining
    context overlap between chunks.
    """
    
    def __init__(
        self,
        chunk_size: int = 700,
        overlap: int = 100,
        min_chunk_chars: int = 120,
    ):
        """Initialize chunker with size parameters.
        
        Args:
            chunk_size: Target chunk size in characters (default 700)
            overlap: Overlap between chunks in characters (default 100)
            min_chunk_chars: Minimum chunk length to keep (default 120)
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_chunk_chars = min_chunk_chars
        
        logger.info(
            f"IntelligentChunker initialized: "
            f"chunk_size={chunk_size}, overlap={overlap}, min_chunk_chars={min_chunk_chars}"
        )
    
    @staticmethod
    def split_into_sentences(text: str) -> List[str]:
        """Split text into sentences using regex.
        
        Handles:
        - Standard sentence endings: . ! ?
        - Abbreviations: Dr. Mr. Mrs. etc.
        - Decimal numbers: 3.14
        - Ellipsis: ...
        
        Args:
            text: Input text to split
            
        Returns:
            List of sentences
        """
        # Clean text: remove null bytes and normalize whitespace
        text = text.replace('\x00', '')
        text = re.sub(r'\s+', ' ', text).strip()
        
        if not text:
            return []
        
        # Split on sentence boundaries
        # Pattern: (?<=[.!?])\s+(?=[A-Z])
        # Matches whitespace after punctuation before capital letter
        # Also handles ellipsis and other edge cases
        
        # First, protect abbreviations and decimal numbers
        text = re.sub(r'(\b(?:Dr|Mr|Mrs|Ms|Prof|Sr|Jr|Ph\.D|etc)\.)(?=\s)', r'\1__ABBREV__', text)
        text = re.sub(r'(\d)\.(\d)', r'\1__DECIMAL__\2', text)
        
        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        
        # Restore abbreviations and decimals
        sentences = [s.replace('__ABBREV__', '.').replace('__DECIMAL__', '.') for s in sentences]
        
        # Filter empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def split_text(self, text: str) -> List[str]:
        """Split text into chunks preserving sentence boundaries.
        
        Algorithm:
        1. Clean text (remove null bytes, normalize whitespace)
        2. Split into sentences using regex
        3. Group sentences into chunks up to chunk_size
        4. Extend chunk boundaries to complete sentences
        5. Add overlap by including sentences from previous chunk
        6. Filter chunks below min_chunk_chars
        
        Args:
            text: Input text to split
            
        Returns:
            List of text chunks
        """
        if not text or not text.strip():
            return []
        
        # Split into sentences
        sentences = self.split_into_sentences(text)
        
        if not sentences:
            return []
        
        chunks = []
        current_chunk_sentences = []
        current_chunk_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            # If adding this sentence would exceed chunk_size, save current chunk
            if current_chunk_size + sentence_size > self.chunk_size and current_chunk_sentences:
                chunk_text = ' '.join(current_chunk_sentences)
                
                # Only add chunk if it meets minimum length
                if len(chunk_text) >= self.min_chunk_chars:
                    chunks.append(chunk_text)
                
                # Start new chunk with overlap from previous chunk
                # Keep last sentences that fit in overlap window
                overlap_text = chunk_text
                overlap_sentences = []
                overlap_size = 0
                
                for sent in reversed(current_chunk_sentences):
                    if overlap_size + len(sent) <= self.overlap:
                        overlap_sentences.insert(0, sent)
                        overlap_size += len(sent) + 1  # +1 for space
                    else:
                        break
                
                current_chunk_sentences = overlap_sentences + [sentence]
                current_chunk_size = overlap_size + sentence_size
            else:
                # Add sentence to current chunk
                current_chunk_sentences.append(sentence)
                current_chunk_size += sentence_size + 1  # +1 for space
        
        # Add final chunk
        if current_chunk_sentences:
            chunk_text = ' '.join(current_chunk_sentences)
            if len(chunk_text) >= self.min_chunk_chars:
                chunks.append(chunk_text)
        
        logger.debug(f"Split text into {len(chunks)} chunks")
        return chunks
    
    def extract_chunks_from_page(
        self,
        page_text: str,
        page_number: int,
        manual_name: str,
        chunk_id_prefix: str,
    ) -> List[Dict[str, Any]]:
        """Extract chunks from a PDF page with metadata.
        
        Args:
            page_text: Text content from PDF page
            page_number: Page number (1-indexed)
            manual_name: Name of the manual file
            chunk_id_prefix: Prefix for chunk IDs
            
        Returns:
            List of chunk dictionaries with keys:
            - id: Unique chunk identifier
            - manual: Manual filename
            - page: Page number
            - text: Chunk text content
        """
        if not page_text or not page_text.strip():
            return []
        
        chunks = self.split_text(page_text)
        
        chunk_dicts = []
        for chunk_idx, chunk_text in enumerate(chunks):
            chunk_dict = {
                "id": f"{chunk_id_prefix}-p{page_number}-c{chunk_idx}",
                "manual": manual_name,
                "page": page_number,
                "text": chunk_text,
            }
            chunk_dicts.append(chunk_dict)
        
        logger.debug(
            f"Extracted {len(chunk_dicts)} chunks from {manual_name} page {page_number}"
        )
        return chunk_dicts


def get_chunker(
    chunk_size: int = 700,
    overlap: int = 100,
    min_chunk_chars: int = 120,
) -> IntelligentChunker:
    """Factory function to get an IntelligentChunker instance.
    
    Args:
        chunk_size: Target chunk size in characters
        overlap: Overlap between chunks in characters
        min_chunk_chars: Minimum chunk length to keep
        
    Returns:
        IntelligentChunker instance
    """
    return IntelligentChunker(chunk_size, overlap, min_chunk_chars)
