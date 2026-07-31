"""CLI script to test and inspect RAG hybrid retrieval results."""
from __future__ import annotations

import json
import sys
from backend.rag.retriever import retrieve, warm_up


def main():
    print("=== VinAI RAG Retrieval Tester ===")
    info = warm_up()
    print(f"Loaded {info.get('chunk_count')} chunks into memory.\n")

    question = (
        " ".join(sys.argv[1:]).strip()
        if len(sys.argv) > 1
        else "Cách để đặt phòng thư viện"
    )
    print(f"🔍 Query: '{question}'\n")

    results = retrieve(question, top_k=4)
    if not results:
        print("⚠️ No relevant passages retrieved (Below similarity threshold / empty).\n")
        return

    print(f"Found {len(results)} passage(s):\n")
    for idx, item in enumerate(results, 1):
        print(f"--- Passage {idx} ---")
        print(f"Chunk ID   : {item.get('chunk_id')}")
        print(f"Source     : {item.get('source')}")
        print(f"Source URL : {item.get('source_url')}")
        if (dense := item.get("dense_score")) is not None:
            print(f"Dense Score: {dense:.4f}")
        if (lexical := item.get("lexical_score")) is not None:
            print(f"Lexical    : {lexical:.4f}")
        print(f"Fused Score: {item.get('score', 0.0):.4f}")

        print(f"Content    :\n{item.get('text')}\n")


if __name__ == "__main__":
    main()
