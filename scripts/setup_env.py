"""Environment setup and verification script.

Verifies dependencies, data files, trained models, and builds the retrieval index if missing.
Ensures the system can be reproduced in under 15 minutes.
"""

import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("setup")


def verify_and_setup():
    logger.info("Verifying environment and dependencies...")
    required_packages = [
        "pandas",
        "numpy",
        "sklearn",
        "pydantic",
        "fastapi",
        "uvicorn",
        "yaml",
        "dotenv",
        "pytest",
    ]
    for pkg in required_packages:
        try:
            __import__(pkg)
        except ImportError:
            logger.error(f"Missing required package: {pkg}. Run: pip install -r requirements.txt")
            sys.exit(1)
    logger.info("All core packages installed.")

    # Check directories
    for d in ["data/raw", "data/interim", "data/processed", "data/evaluation", "reports"]:
        Path(d).mkdir(parents=True, exist_ok=True)

    # Check raw data
    raw_csv = Path("data/raw/twcs.csv")
    if not raw_csv.exists():
        logger.warning(
            "data/raw/twcs.csv not found! Please place twcs.csv in data/raw/ before running pipeline."
        )
    else:
        logger.info("Raw dataset twcs.csv located (%d bytes).", raw_csv.stat().st_size)

    # Check models and index
    model_path = Path("data/processed/main_intent_classifier.pkl")
    index_path = Path("data/processed/retrieval_index.pkl")

    if not model_path.exists():
        logger.info("Training main intent classifier...")
        from src.models.train_classifiers import run_training_pipeline
        run_training_pipeline()

    if not index_path.exists():
        logger.info("Building historical response retrieval index...")
        from scripts.build_index import build_and_save_index
        build_and_save_index()

    logger.info("Setup complete! System is ready to run demo, API, and evaluation.")


if __name__ == "__main__":
    verify_and_setup()
