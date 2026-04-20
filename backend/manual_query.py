import os
import re
from typing import List

from dotenv import load_dotenv
from groq import Groq

from rag import format_citations, format_context, retrieve_manual_chunks


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
    relevant_chunks = []
    query_terms = extract_keywords(query)
    is_definition_query = bool(re.match(r"^\s*what\s+(is|are)\b", query.lower()))

    for chunk in retrieve_manual_chunks(query):
        chunk_terms = extract_keywords(chunk.text)
        overlap = query_terms & chunk_terms

        if not query_terms:
            continue

        if is_definition_query and chunk.score < 0.45:
            continue

        if len(overlap) >= 2:
            relevant_chunks.append(chunk)
            continue

        # Single keyword match with decent score
        if overlap and chunk.score >= 0.35:
            relevant_chunks.append(chunk)
            continue

        # High score even without keyword overlap (hash embedder can still find relevant chunks)
        if chunk.score >= 0.50:
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
        "You are an EV diagnostic assistant for service technicians. "
        "Answer ONLY from the provided repair manual excerpts. "
        "Use exact terminology from the manuals, not paraphrased versions. "
        "Cite source numbers inline like [Source 1] when you reference information. "
        "If the excerpts don't answer the question, say 'The provided manual excerpts do not contain information on...' "
        "Format your response as:\n"
        "ANSWER:\n[Your answer with inline citations like [Source 1]]\n\n"
        "PROCEDURE:\n[Numbered steps if available, or 'None' if no steps in excerpts]\n\n"
        "Do NOT add a separate Citations section - only use inline [Source N] citations."
    )
    user_prompt = (
        f"Question: {query}\n\n"
        f"Manual excerpts:\n{context}\n\n"
        "Respond in the exact format specified above."
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
