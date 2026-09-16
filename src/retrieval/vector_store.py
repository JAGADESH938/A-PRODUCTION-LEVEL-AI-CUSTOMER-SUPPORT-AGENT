"""Local Vector Database & Historical Evidence Retrieval System.

Provides fast, deterministic cosine similarity search over historical customer support resolutions.
Stores customer issue, context, historical brand response, intent, and timestamps.
Supports metadata filtering (e.g. by intent) and similarity thresholding.
"""

import logging
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.schemas.models import EvidenceItem

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


class LocalVectorStore:
    """High-performance local vector store using sublinear TF-IDF embeddings and cosine similarity."""

    def __init__(self, max_features: int = 25000):
        self.max_features = max_features
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.doc_vectors: Optional[np.ndarray] = None
        self.documents: List[Dict[str, Any]] = []

    def build_index(self, documents: List[Dict[str, Any]]) -> None:
        """Builds the vector search index over a list of document dicts."""
        logger.info("Building vector index over %d documents...", len(documents))
        self.documents = documents

        # Create corpus combining customer issue and context
        corpus = []
        for doc in documents:
            text = doc.get("customer_text", "")
            if doc.get("conversation_context"):
                text = f"{doc['conversation_context']} {text}"
            corpus.append(text)

        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 3),
            max_features=self.max_features,
            sublinear_tf=True,
            stop_words="english",
        )
        self.doc_vectors = self.vectorizer.fit_transform(corpus)
        logger.info("Index built successfully. Shape: %s", self.doc_vectors.shape)

    def search(
        self,
        query: str,
        top_k: int = 3,
        intent_filter: Optional[str] = None,
        min_similarity: float = 0.0,
    ) -> List[EvidenceItem]:
        """Searches the index for most similar historical resolutions."""
        if self.vectorizer is None or self.doc_vectors is None:
            raise ValueError("Vector store index is not built or loaded.")

        if not query.strip():
            return []

        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.doc_vectors).flatten()

        # If intent filter is provided, mask non-matching documents
        if intent_filter:
            for idx, doc in enumerate(self.documents):
                if doc.get("intent") != intent_filter:
                    similarities[idx] = -1.0

        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results: List[EvidenceItem] = []
        for idx in top_indices:
            sim = float(similarities[idx])
            if sim < min_similarity:
                continue

            doc = self.documents[idx]
            results.append(
                EvidenceItem(
                    conversation_id=doc.get("conversation_id", f"doc_{idx}"),
                    customer_issue=doc.get("customer_text", ""),
                    brand_response=doc.get("brand_response", ""),
                    similarity=round(sim, 4),
                    intent=doc.get("intent"),
                )
            )

        return results

    def save(self, filepath: str) -> None:
        """Persists vector store index to disk."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(
                {
                    "vectorizer": self.vectorizer,
                    "doc_vectors": self.doc_vectors,
                    "documents": self.documents,
                },
                f,
            )
        logger.info("Saved vector store to %s", filepath)

    def load(self, filepath: str) -> None:
        """Loads vector store index from disk."""
        with open(filepath, "rb") as f:
            data = pickle.load(f)
            self.vectorizer = data["vectorizer"]
            self.doc_vectors = data["doc_vectors"]
            self.documents = data["documents"]
        logger.info("Loaded vector store from %s with %d documents.", filepath, len(self.documents))
