"""Script to build and persist the historical response vector index."""

import json
import logging
from pathlib import Path
from src.retrieval.vector_store import LocalVectorStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def build_and_save_index(
    train_jsonl: str = "data/processed/train.jsonl",
    output_index_path: str = "data/processed/retrieval_index.pkl",
) -> None:
    logger.info("Loading training documents from %s...", train_jsonl)
    docs = []
    with open(train_jsonl, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                docs.append(json.loads(line))

    logger.info("Loaded %d training documents.", len(docs))
    store = LocalVectorStore(max_features=30000)
    store.build_index(docs)
    store.save(output_index_path)
    logger.info("Index build complete and saved to %s", output_index_path)


if __name__ == "__main__":
    build_and_save_index()
