from __future__ import annotations

# RAG configuration (local, no cloud APIs).

# Knowledge Engine V2 (experimental, modular)
# Default must remain OFF to preserve legacy behavior and zero-regressions policy.
FEATURE_KNOWLEDGE_ENGINE_V2 = False

# Embeddings
# Recommended lightweight local models (depending on what you install):
# - sentence-transformers
# - all-MiniLM-L6-v2 (default)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Vector DB
# Chroma preferred; FAISS fallback can be enabled in code if Chroma is unavailable.
VECTOR_DB_BACKEND = "chroma"  # "chroma" | "faiss"

from utils.paths import get_data_dir

# Persistent path for Chroma (default to user data directory)
VECTOR_DB_PATH = str(get_data_dir() / "knowledge" / "vector_db")

# Collections
DEFAULT_COLLECTION = "Personal"

# Chunking
CHUNK_SIZE = 600
CHUNK_OVERLAP = 100

# Retrieval
TOP_K = 5

# Ingestion
DOCUMENTS_DIR = str(get_data_dir() / "knowledge" / "documents")
