
import os
import json
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer

# Work offline
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

PROJECT_DIR = Path(__file__).resolve().parent.parent

CHUNKS_FILE = PROJECT_DIR / "knowledge_base" / "processed" / "chunks.json"
MODEL_DIR = PROJECT_DIR / "knowledge_base" / "models" / "multilingual-e5-small"
OUTPUT_DIR = PROJECT_DIR / "knowledge_base" / "processed"

EMBEDDINGS_FILE = OUTPUT_DIR / "embeddings.npy"
METADATA_FILE = OUTPUT_DIR / "chunk_metadata.json"


def main():
    print("Reading chunks...")

    with open(CHUNKS_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    # Flatten nested lists
    chunks = []
    for group in data:
        if isinstance(group, list):
            chunks.extend(group)
        else:
            chunks.append(group)

    # Validate chunks
    if not chunks:
        raise ValueError("No chunks found.")

    for i, chunk in enumerate(chunks):
        if not isinstance(chunk, dict) or not chunk.get("text"):
            raise ValueError(f"Invalid chunk at index {i}")

    print(f"Total chunks: {len(chunks)}")

    print("Loading local embedding model...")
    model = SentenceTransformer(
        str(MODEL_DIR),
        trust_remote_code=False
    )

    # E5 uses passage prefix for documents
    texts = [
        "passage: " + chunk["text"]
        for chunk in chunks
    ]

    print("Generating embeddings...")

    embeddings = model.encode(
        texts,
        batch_size=16,
        show_progress_bar=True,
        normalize_embeddings=True
    )

    # Validate output
    if embeddings.shape != (len(chunks), 384):
        raise ValueError(f"Unexpected embedding shape: {embeddings.shape}")

    # Save vectors
    np.save(EMBEDDINGS_FILE, embeddings)

    # Preserve source and page information
    with open(METADATA_FILE, "w", encoding="utf-8") as file:
        json.dump(chunks, file, ensure_ascii=False, indent=2)

    print("\n========== EMBEDDING REPORT ==========")
    print(f"Chunks processed: {len(chunks)}")
    print(f"Embedding shape: {embeddings.shape}")
    print(f"Vectors saved: {EMBEDDINGS_FILE}")
    print(f"Metadata saved: {METADATA_FILE}")
    print("Validation: PASSED")


if __name__ == "__main__":
    main()
