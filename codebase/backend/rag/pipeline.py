"""Public coordinator for the complete RAG request flow."""
from __future__ import annotations

from backend.rag.directions import parse_direction_nodes
from backend.rag.generator import generate
from backend.rag.multimodal import generate_vision_directions
from backend.rag.response_policy import get_deterministic_response
from backend.rag.retriever import retrieve
from backend.rag.retriever import warm_up as warm_up_retriever
from backend.rag.router import Intent, route_query


def answer_question(question: str) -> dict:
    """Route user question, handle fast path, vision directions branch, or retrieve & generate grounded answer."""
    intent, search_query = route_query(question)
    if intent != Intent.FACTUAL:
        response = get_deterministic_response(intent)
        response["intent"] = intent.value
        return response

    # Check for dedicated Vision Directions Branch
    origin, destination, is_loc = parse_direction_nodes(question)
    if is_loc:
        response = generate_vision_directions(question, origin, destination)
        response["intent"] = intent.value
        return response

    passages = retrieve(question, search_query=search_query)
    response = generate(question, passages)
    response["intent"] = intent.value
    return response





def warm_up() -> dict:
    """Load and retain retrieval models and indexes before serving requests."""
    return warm_up_retriever()
