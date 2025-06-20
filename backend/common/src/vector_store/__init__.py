import os

if os.getenv("ENVIRONMENT") == "development":
    from .chroma_vector_store import VectorStore
else:
    from .vertex_vector_store import VertexVectorStore
    VectorStore = VertexVectorStore  # Explicit re-export

__all__ = ["VectorStore"] 