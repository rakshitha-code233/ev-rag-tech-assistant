"""Enhanced Prompt Builder for RAG system."""

import logging
from typing import List, Dict

from .models import RetrievedChunk

logger = logging.getLogger(__name__)

# System prompt that enforces manual adherence
SYSTEM_PROMPT = """You are an EV diagnostic assistant for service technicians.

CRITICAL INSTRUCTIONS:
1. Answer ONLY from the provided manual excerpts below
2. Use EXACT terminology and phrasing from the manuals
3. Cite sources inline using [Source N] format when you use information
4. If excerpts partially answer the question, state what information is missing
5. Prefer step-by-step procedures when available in the excerpts
6. Include safety warnings exactly as written in the excerpts
7. Do NOT add information not present in the excerpts
8. Do NOT paraphrase unless necessary for clarity

Your role is to be a precise conduit for manual information, not to interpret or expand beyond what is written."""

# User prompt template
USER_PROMPT_TEMPLATE = """Technician question:
{query}

Manual excerpts:
{context}

Respond with:
1. A concise answer using exact manual terminology
2. A 'Procedure' section with numbered steps (only if excerpts contain procedural steps)
3. A 'Citations' section mapping each [Source N] to its manual and page number

Format:
Answer: [Your answer with inline [Source N] citations]

Procedure: (if applicable)
1. [Step from manual]
2. [Step from manual]

Citations:
- [Source 1]: Manual_Name p.Page_Number
- [Source 2]: Manual_Name p.Page_Number
"""


class EnhancedPromptBuilder:
    """Builds LLM prompts for manual-adherent answers.
    
    Creates system and user prompts that enforce exact manual adherence,
    proper citation, and step-by-step procedures.
    """
    
    def __init__(self):
        """Initialize the prompt builder."""
        logger.info("EnhancedPromptBuilder initialized")
    
    def build_prompt(
        self,
        query: str,
        chunks: List[RetrievedChunk],
    ) -> List[Dict[str, str]]:
        """Build chat messages for LLM.
        
        Args:
            query: User query
            chunks: Retrieved and re-ranked chunks
            
        Returns:
            List of message dictionaries:
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": formatted_user_prompt}
            ]
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        if not chunks:
            logger.warning("No chunks provided to build_prompt")
            chunks = []
        
        # Format context from chunks
        context = self.format_context(chunks)
        
        # Build user prompt
        user_prompt = USER_PROMPT_TEMPLATE.format(
            query=query.strip(),
            context=context,
        )
        
        # Build message list
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
        
        logger.debug(f"Built prompt with {len(chunks)} chunks")
        return messages
    
    def format_context(self, chunks: List[RetrievedChunk]) -> str:
        """Format chunks as numbered sources.
        
        Format:
        [Source 1] Manual_Name p.Page_Number
        <chunk text>
        
        [Source 2] Manual_Name p.Page_Number
        <chunk text>
        
        Args:
            chunks: Retrieved chunks
            
        Returns:
            Formatted context string
        """
        if not chunks:
            return "No relevant manual excerpts found."
        
        context_parts = []
        
        for idx, chunk in enumerate(chunks, 1):
            source_header = f"[Source {idx}] {chunk.manual} p.{chunk.page}"
            context_parts.append(source_header)
            context_parts.append(chunk.text)
            context_parts.append("")  # Empty line for readability
        
        context = "\n".join(context_parts).strip()
        
        logger.debug(f"Formatted context with {len(chunks)} sources")
        return context
    
    @staticmethod
    def get_system_prompt() -> str:
        """Get the system prompt.
        
        Returns:
            System prompt string
        """
        return SYSTEM_PROMPT
    
    @staticmethod
    def get_user_prompt_template() -> str:
        """Get the user prompt template.
        
        Returns:
            User prompt template string
        """
        return USER_PROMPT_TEMPLATE


def get_prompt_builder() -> EnhancedPromptBuilder:
    """Factory function to get an EnhancedPromptBuilder instance.
    
    Returns:
        EnhancedPromptBuilder instance
    """
    return EnhancedPromptBuilder()
