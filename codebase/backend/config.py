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
_llm_model_defaults = {
    "openai": "gpt-5.6-luna",
    "gemini": "gemini-3.6-flash",
    "openrouter": "~openai/gpt-latest",
}
LLM_MODEL = os.getenv(
    "LLM_MODEL",
    _llm_model_defaults.get(LLM_PROVIDER, ""),
)
LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "20"))
LLM_MAX_OUTPUT_TOKENS = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "500"))
GENERATOR_MAX_PASSAGES = int(os.getenv("GENERATOR_MAX_PASSAGES", "3"))
EVIDENCE_DENSE_THRESHOLD = float(
    os.getenv("EVIDENCE_DENSE_THRESHOLD", "0.82")
)

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "local")
if EMBEDDING_PROVIDER == "local":
    EMBEDDING_MODEL = os.getenv(
        "LOCAL_EMBEDDING_MODEL", "intfloat/multilingual-e5-small"
    )
else:
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_MODEL_REVISION = os.getenv(
    "EMBEDDING_MODEL_REVISION",
    "614241f622f53c4eeff9890bdc4f31cfecc418b3",
)
EMBEDDING_BACKEND = os.getenv("EMBEDDING_BACKEND", "onnx")
EMBEDDING_ONNX_FILE = os.getenv("EMBEDDING_ONNX_FILE", "onnx/model.onnx")
EMBEDDING_ONNX_PROVIDER = os.getenv(
    "EMBEDDING_ONNX_PROVIDER", "auto"
)
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))
_faiss_index_dir = Path(
    os.getenv("FAISS_INDEX_DIR", str(BACKEND_DIR / "rag" / "vectorstore"))
)
if not _faiss_index_dir.is_absolute():
    _faiss_index_dir = BACKEND_DIR.parent / _faiss_index_dir
FAISS_INDEX_DIR = str(_faiss_index_dir.resolve())

KNOWLEDGE_BASE_RAW_DIR = BACKEND_DIR / "knowledge_base" / "raw"
KNOWLEDGE_BASE_PROCESSED_DIR = BACKEND_DIR / "knowledge_base" / "processed"
