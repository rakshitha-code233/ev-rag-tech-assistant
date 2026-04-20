"""Citation Tracker for RAG system."""

import re
import logging
from typing import List, Set, Tuple

from .models import RetrievedChunk

logger = logging.getLogger(__name__)


class CitationTracker:
    """Tracks and formats citations for answers.
    
    Extracts citations from LLM answers, deduplicates them, and formats
    them as "Manual_Name p.Page_Number".
    """
    
    def __init__(self):
        """Initialize the citation tracker."""
        logger.info("CitationTracker initialized")
    
    def extract_citations(
        self,
        answer: str,
        chunks: List[RetrievedChunk],
    ) -> List[str]:
        """Extract citations from answer and chunks.
        
        Algorithm:
        1. Parse answer for [Source N] references
        2. Map source numbers to chunks
        3. Extract manual name and page number
        4. Deduplicate citations (same manual + page)
        5. Format as "Manual_Name p.Page_Number"
        
        Args:
            answer: LLM-generated answer with inline citations
            chunks: Chunks used for context
            
        Returns:
            List of formatted citations
        """
        if not answer or not answer.strip():
            logger.warning("Empty answer provided to extract_citations")
            return []
        
        if not chunks:
            logger.warning("No chunks provided to extract_citations")
            return []
        
        # Find all [Source N] references in the answer
        source_pattern = r'\[Source\s+(\d+)\]'
        source_matches = re.findall(source_pattern, answer)
        
        if not source_matches:
            logger.debug("No source citations found in answer")
            return []
        
        # Convert to integers and deduplicate
        source_numbers = set(int(num) for num in source_matches)
        
        # Map source numbers to chunks and extract citations
        citations = []
        for source_num in sorted(source_numbers):
            # Source numbers are 1-indexed
            chunk_idx = source_num - 1
            
            if 0 <= chunk_idx < len(chunks):
                chunk = chunks[chunk_idx]
                citation = f"{chunk.manual} p.{chunk.page}"
                citations.append(citation)
            else:
                logger.warning(f"Source {source_num} out of range (have {len(chunks)} chunks)")
        
        # Deduplicate citations
        unique_citations = self.deduplicate_citations_list(citations)
        
        logger.debug(f"Extracted {len(unique_citations)} unique citations from answer")
        return unique_citations
    
    def append_citations(
        self,
        answer: str,
        citations: List[str],
    ) -> str:
        """Append citations section to answer if not present.
        
        Args:
            answer: Answer text
            citations: List of formatted citations
            
        Returns:
            Answer with citations section
        """
        if not answer or not answer.strip():
            logger.warning("Empty answer provided to append_citations")
            return answer
        
        if not citations:
            logger.debug("No citations to append")
            return answer
        
        # Check if answer already has a Citations section
        if "Citations:" in answer or "citations:" in answer:
            logger.debug("Answer already has citations section")
            return answer
        
        # Build citations section
        citations_section = "\n\nCitations:\n"
        for citation in citations:
            citations_section += f"- {citation}\n"
        
        # Append to answer
        result = answer.rstrip() + citations_section.rstrip()
        
        logger.debug(f"Appended {len(citations)} citations to answer")
        return result
    
    def deduplicate_citations(
        self,
        chunks: List[RetrievedChunk],
    ) -> List[str]:
        """Get unique citations from chunks.
        
        Args:
            chunks: Retrieved chunks
            
        Returns:
            Deduplicated list of "Manual_Name p.Page_Number"
        """
        if not chunks:
            logger.debug("No chunks provided to deduplicate_citations")
            return []
        
        # Create set of unique (manual, page) pairs
        unique_pairs: Set[Tuple[str, int]] = set()
        
        for chunk in chunks:
            unique_pairs.add((chunk.manual, chunk.page))
        
        # Format as citations
        citations = [f"{manual} p.{page}" for manual, page in sorted(unique_pairs)]
        
        logger.debug(f"Deduplicated {len(chunks)} chunks to {len(citations)} unique citations")
        return citations
    
    @staticmethod
    def deduplicate_citations_list(citations: List[str]) -> List[str]:
        """Deduplicate a list of citation strings.
        
        Args:
            citations: List of citation strings
            
        Returns:
            Deduplicated list of citations
        """
        # Use dict to preserve order while deduplicating
        unique_citations = {}
        for citation in citations:
            unique_citations[citation] = True
        
        return list(unique_citations.keys())
    
    @staticmethod
    def format_citation(manual: str, page: int) -> str:
        """Format a citation as "Manual_Name p.Page_Number".
        
        Args:
            manual: Manual filename
            page: Page number
            
        Returns:
            Formatted citation string
        """
        return f"{manual} p.{page}"
    
    @staticmethod
    def parse_citation(citation: str) -> Tuple[str, int]:
        """Parse a citation string into manual and page number.
        
        Args:
            citation: Citation string (e.g., "Tesla_Model3.pdf p.42")
            
        Returns:
            Tuple of (manual, page)
            
        Raises:
            ValueError: If citation format is invalid
        """
        # Pattern: "Manual_Name p.Page_Number"
        pattern = r'^(.+?)\s+p\.(\d+)$'
        match = re.match(pattern, citation)
        
        if not match:
            raise ValueError(f"Invalid citation format: {citation}")
        
        manual = match.group(1)
        page = int(match.group(2))
        
        return manual, page


def get_citation_tracker() -> CitationTracker:
    """Factory function to get a CitationTracker instance.
    
    Returns:
        CitationTracker instance
    """
    return CitationTracker()
