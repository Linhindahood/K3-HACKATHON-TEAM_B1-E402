"""Đọc .env, hằng số dùng chung cho toàn bộ backend."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BACKEND_DIR = Path(__file__).resolve().parent

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # openai | gemini | openrouter

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
FAISS_INDEX_DIR = os.getenv("FAISS_INDEX_DIR", str(BACKEND_DIR / "rag" / "vectorstore"))
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.55"))

KNOWLEDGE_BASE_RAW_DIR = BACKEND_DIR / "knowledge_base" / "raw"
KNOWLEDGE_BASE_PROCESSED_DIR = BACKEND_DIR / "knowledge_base" / "processed"
