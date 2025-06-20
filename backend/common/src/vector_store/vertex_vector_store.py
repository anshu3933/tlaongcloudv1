"""
Vertex AI Vector Store adapter for RAG–MCP.

Usage
-----
from common.vector_store.vertex_vector_store import VertexVectorStore
vector_store = VertexVectorStore.from_settings(get_settings())
vector_store.upsert(chunks)          # list[dict] produced by your loader
neighbors = vector_store.query(q_emb, top_k=5)   # returns list[Neighbor]

Integration points
------------------
* mcp_server.retrieve_documents_impl → replace the TF-IDF block with
  `neighbors = vector_store.query(query_embedding, top_k)`
* adk_host.generate_answer → fetch full chunks by ID using the
  Neighbor.metadata you stored during `upsert`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence

import backoff
import structlog
from google.api_core.exceptions import GoogleAPICallError, RetryError
from google.cloud import aiplatform
from google.cloud.aiplatform.matching_engine import (
    MatchingEngineIndex,
    MatchingEngineIndexEndpoint,
)

logger = structlog.get_logger(__name__)


@dataclass
class Neighbor:
    id: str
    score: float
    metadata: Dict[str, Any]


def _backoff_hdlr(details):
    logger.warning(
        "Vertex AI transient error, backing off",
        wait_seconds=details["wait"],
        tries=details["tries"],
    )


class VertexVectorStore:
    """Wrapper around Vertex AI Matching Engine Vector Search."""

    # ------------------------- construction -------------------------

    def __init__(
        self,
        project_id: str,
        location: str,
        index_id: str,
        endpoint_id: str,
        deployed_index_id: str,
    ):
        aiplatform.init(project=project_id, location=location)

        self._index = MatchingEngineIndex(index_name=index_id)
        self._endpoint = MatchingEngineIndexEndpoint(
            index_endpoint_name=endpoint_id
        )
        self._deployed_index_id = deployed_index_id
        self._project_id = project_id
        self._location = location

        logger.info(
            "VertexVectorStore initialised",
            project_id=project_id,
            location=location,
            index_id=index_id,
            endpoint_id=endpoint_id,
            deployed_index_id=deployed_index_id,
        )

    # Convenience constructor ------------------------------------------------
    @classmethod
    def from_settings(cls, settings) -> "VertexVectorStore":
        missing = [
            var
            for var in (
                settings.vector_search_index_id,
                settings.vector_search_endpoint_id,
                settings.vector_search_deployed_index_id,
            )
            if not var
        ]
        if missing:
            raise ValueError(
                "Vector Search env-vars not set "
                "(VECTOR_SEARCH_INDEX_ID / ENDPOINT_ID / DEPLOYED_INDEX_ID)"
            )
        return cls(
            project_id=settings.gcp_project_id,
            location=settings.gcp_region,
            index_id=settings.vector_search_index_id,
            endpoint_id=settings.vector_search_endpoint_id,
            deployed_index_id=settings.vector_search_deployed_index_id,
        )

    # --------------------------- core methods ---------------------------

    @backoff.on_exception(
        backoff.expo,
        (GoogleAPICallError, RetryError),
        max_time=60,
        on_backoff=_backoff_hdlr,
    )
    def upsert(self, chunks: Sequence[Dict[str, Any]]) -> None:
        """
        Push / update embeddings.

        Each `chunk` dict must contain:
        - embedding: List[float]
        - metadata: Dict[str, Any]  (will be JSON-encoded automatically)
        - id: unique string (if absent we derive from metadata['source'])
        """
        instances = []
        for c in chunks:
            if "embedding" not in c or c["embedding"] is None:
                raise ValueError("chunk missing embedding")
            instances.append(
                {
                    "id": c.get(
                        "id",
                        f"{c['metadata']['source']}_{c['metadata']['chunk_index']}",
                    ),
                    "embedding": c["embedding"],
                    "metadata": c["metadata"],
                }
            )
        # Vertex allows batches up to 1000 vectors.
        BATCH = 1000
        for i in range(0, len(instances), BATCH):
            batch = instances[i : i + BATCH]
            self._endpoint.upsert(
                deployed_index_id=self._deployed_index_id, instances=batch
            )
            logger.info(
                "Upserted batch into Vertex AI",
                batch_size=len(batch),
                total=len(instances),
            )

    @backoff.on_exception(
        backoff.expo,
        (GoogleAPICallError, RetryError),
        max_time=60,
        on_backoff=_backoff_hdlr,
    )
    def query(
        self,
        embedding: List[float],
        top_k: int = 5,
        *,
        filter: Optional[str] = None,
    ) -> List[Neighbor]:
        """
        Retrieve nearest neighbours.

        `filter` must be a Vertex AI metadata filter string, e.g.
        'metadata.category = "rag_fundamentals"'.
        """
        response = self._endpoint.find_neighbors(
            deployed_index_id=self._deployed_index_id,
            queries=[embedding],
            num_neighbors=top_k,
            filter=filter,
        )
        neighbors_raw = response[0].neighbors  # single query
        neighbors = [
            Neighbor(
                id=n.id,
                score=n.distance,
                metadata=n.metadata,  # Already dict-like
            )
            for n in neighbors_raw
        ]
        logger.debug(
            "Vertex AI search completed",
            query_top_k=top_k,
            returned=len(neighbors),
        )
        return neighbors

    @backoff.on_exception(
        backoff.expo,
        (GoogleAPICallError, RetryError),
        max_time=60,
        on_backoff=_backoff_hdlr,
    )
    def delete(self, ids: Iterable[str]) -> None:
        """Remove vectors by ID."""
        self._endpoint.remove(
            deployed_index_id=self._deployed_index_id,
            ids=list(ids),
        )
        logger.info("Deleted vectors", count=len(ids))

    # ------------------------ operational helpers ------------------------

    def health_check(self) -> bool:
        """Lightweight ping used by /health endpoints."""
        try:
            # A HEAD call is not exposed; we rely on list_indexes (cached).
            _ = self._index.gca_resource.name
            return True
        except Exception as exc:  # broad OK here
            logger.warning("Vector Search health-check failed", err=str(exc))
            return False 