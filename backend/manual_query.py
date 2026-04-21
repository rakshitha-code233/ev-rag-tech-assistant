import os
import re
from typing import List

from dotenv import load_dotenv
from groq import Groq

from rag_improved import retrieve_manual_chunks, format_citations, format_context


load_dotenv()


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "do",
    "does",
    "for",
    "how",
    "i",
    "is",
    "it",
    "me",
    "my",
    "of",
    "on",
    "should",
    "tell",
    "the",
    "to",
    "what",
    "where",
    "with",
}


def normalize_token(token: str) -> str:
    token = token.lower()
    for suffix in ("ing", "ed", "es", "s"):
        if token.endswith(suffix) and len(token) > len(suffix) + 2:
            token = token[: -len(suffix)]
            break
    return token


def extract_keywords(text: str) -> set[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return {
        normalize_token(token)
        for token in tokens
        if len(token) >= 3 and normalize_token(token) not in STOPWORDS
    }


def select_relevant_chunks(query: str):
    """Select relevant chunks based on semantic similarity scores.
    
    Since we're using semantic embeddings, we can trust the scores directly
    without needing keyword overlap validation.
    """
    relevant_chunks = []
    
    # Get chunks from semantic retrieval (already ranked by score)
    chunks = retrieve_manual_chunks(query, top_k=10)
    
    # Filter by score threshold (0.3 is reasonable for semantic embeddings)
    score_threshold = 0.30
    
    for chunk in chunks:
        if chunk.score >= score_threshold:
            relevant_chunks.append(chunk)
    
    return relevant_chunks


def handle_greetings(query: str) -> str | None:
    normalized = query.lower().strip().rstrip('!.,?')

    # Greetings
    if normalized in {"hi", "hello", "hey", "hii", "helo", "helo there", "hi there", "hey there", "greetings"}:
        return "Hello! I'm the EV Diagnostic Assistant. Ask me anything about EV diagnostics, fault codes, charging, or repair procedures and I'll answer from your uploaded manuals with page citations."

    # Thanks
    if any(word in normalized for word in ["thank", "thanks", "thank you", "thankyou", "thx"]):
        return "You're welcome! Feel free to ask anything else about your EV."

    # Identity questions
    identity_patterns = [
        "what is your name",
        "what's your name",
        "whats your name",
        "who are you",
        "tell me about you",
        "tell me about yourself",
        "introduce yourself",
        "what are you",
        "what do you do",
        "who made you",
        "what can you do",
        "how can you help",
    ]
    for pattern in identity_patterns:
        if pattern in normalized:
            return (
                "I'm the EV Diagnostic Assistant — an AI-powered tool built to help "
                "service technicians and EV owners troubleshoot electric vehicles. "
                "I answer questions about fault codes, repair procedures, charging, "
                "battery systems, and more — directly from uploaded repair manuals with "
                "exact page citations. Upload a PDF manual and ask me anything about your EV."
            )

    return None


def get_groq_client() -> Groq | None:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    return Groq(api_key=api_key)


def build_manual_only_prompt(query: str, context: str) -> List[dict]:
    system_prompt = (
        "You are an EV diagnostic assistant. Answer ONLY from the provided manual excerpts. "
        "CRITICAL RULES:\n"
        "1. Use EXACT wording from the manual - do not paraphrase\n"
        "2. If the excerpts don't answer the question, say 'The provided manual excerpts do not contain information on...'\n"
        "3. Extract and list procedures as numbered steps when available\n"
        "4. Use inline citations [Source N] for each fact\n"
        "5. Do NOT include unrelated information\n"
        "6. Do NOT add a separate Citations section\n"
        "\n"
        "ANSWER FORMAT:\n"
        "Start with a direct answer using exact manual text.\n"
        "Then list any procedures as numbered steps.\n"
        "Use [Source N] citations inline.\n"
        "\n"
        "EXAMPLE:\n"
        "To open the charge port, press the button on the Tesla charge cable [Source 1]. "
        "You can also touch Controls > Charge Port on the touchscreen [Source 1].\n"
        "\n"
        "Procedure:\n"
        "1. Park the vehicle [Source 1]\n"
        "2. Press the charge cable button [Source 1]"
    )
    user_prompt = (
        f"Question: {query}\n\n"
        f"Manual excerpts:\n{context}\n\n"
        "Provide a clear, direct answer using only the information above."
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def build_extract_answer(query: str) -> str:
    chunks = select_relevant_chunks(query)
    if not chunks:
        return (
            "I could not find relevant guidance in the indexed manuals yet. "
            "Upload one or more EV repair manuals, then ask again."
        )

    procedure_lines = [f"{index}. {chunk.text}" for index, chunk in enumerate(chunks, start=1)]
    citations = format_citations(chunks)
    return (
        "I found relevant manual guidance.\n\n"
        "Procedure:\n"
        + "\n".join(procedure_lines)
        + "\n\nCitations:\n"
        + "\n".join(f"- {citation}" for citation in citations)
    )


def get_answer(query: str) -> str:
    greeting = handle_greetings(query)
    if greeting:
        return greeting

    chunks = select_relevant_chunks(query)
    if not chunks:
        return (
            "I could not find a matching answer in the indexed manuals. "
            "Try naming the vehicle, system, symptom, or DTC, or upload the relevant manual first."
        )

    context = format_context(chunks)
    citations = format_citations(chunks)
    client = get_groq_client()

    if client is None:
        return build_extract_answer(query)

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=build_manual_only_prompt(query, context),
            temperature=0.2,
        )
        answer = response.choices[0].message.content.strip()
    except Exception:
        return build_extract_answer(query)

    # Extract inline citations from answer and build proper citations section
    citation_pattern = r'\[Source\s+(\d+)\]'
    used_sources = set()
    for match in re.finditer(citation_pattern, answer):
        source_num = int(match.group(1))
        if 1 <= source_num <= len(chunks):
            used_sources.add(source_num)
    
    # Clean up the answer: remove duplicate text and extra whitespace
    answer = re.sub(r'\n\s*\n+', '\n\n', answer)  # Remove multiple blank lines
    answer = re.sub(r'([.!?])\s+([A-Z])', r'\1\n\n\2', answer)  # Add line breaks between sentences
    
    # Build citations section with only used sources
    if used_sources:
        citations_section = "\n\nCitations:\n"
        for source_num in sorted(used_sources):
            if 1 <= source_num <= len(chunks):
                chunk = chunks[source_num - 1]
                citations_section += f"[Source {source_num}] - {chunk.manual} p.{chunk.page}\n"
        answer = answer + citations_section
    elif citations:
        # Fallback: add all citations if none were referenced
        answer = answer + "\n\nCitations:\n" + "\n".join(f"- {citation}" for citation in citations)

    return answer
