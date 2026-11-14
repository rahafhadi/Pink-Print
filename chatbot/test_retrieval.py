
import os
import json
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer

# Force local model usage
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "knowledge_base" / "processed"
MODEL_DIR = PROJECT_DIR / "knowledge_base" / "models" / "multilingual-e5-small"

# Cleaned files
EMBEDDINGS_FILE = DATA_DIR / "embeddings_clean.npy"
METADATA_FILE = DATA_DIR / "chunk_metadata_clean.json"


def main():
    print("Loading cleaned knowledge base...")

    if not EMBEDDINGS_FILE.exists():
        raise FileNotFoundError(f"Missing file: {EMBEDDINGS_FILE}")

    if not METADATA_FILE.exists():
        raise FileNotFoundError(f"Missing file: {METADATA_FILE}")

    embeddings = np.load(EMBEDDINGS_FILE)

    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    print(f"Loaded embeddings: {embeddings.shape}")
    print(f"Loaded metadata: {len(metadata)} chunks")

    if len(embeddings) != len(metadata):
        raise ValueError("Embeddings and metadata count mismatch!")

    if embeddings.shape[1] != 384:
        raise ValueError("Unexpected embedding dimension!")

    model = SentenceTransformer(
        str(MODEL_DIR),
        trust_remote_code=False
    )

    question = "كيف يتم إجراء الفحص الذاتي للثدي؟"

    print("\nQuestion:", question)
    print("Searching...")

    query_embedding = model.encode(
        ["query: " + question],
        normalize_embeddings=True
    )[0]

    scores = embeddings @ query_embedding
    top_indices = np.argsort(scores)[::-1][:5]

    print("\n========== TOP 5 CLEANED RESULTS ==========")

    for rank, index in enumerate(top_indices, start=1):
        chunk = metadata[index]

        print(f"\n--- Result {rank} ---")
        print(f"Similarity: {scores[index]:.4f}")
        print(f"Source: {chunk['source']}")
        print(f"Page: {chunk['page']}")
        print(f"Chunk ID: {chunk['chunk_id']}")
        print(f"Text:\n{chunk['text'][:700]}")

    print("\nRetrieval test completed.")


if __name__ == "__main__":
    main()
