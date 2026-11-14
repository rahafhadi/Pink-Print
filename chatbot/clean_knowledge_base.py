
import json
import numpy as np
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "knowledge_base" / "processed"

EMBEDDINGS_FILE = DATA_DIR / "embeddings.npy"
METADATA_FILE = DATA_DIR / "chunk_metadata.json"

CLEAN_EMBEDDINGS_FILE = DATA_DIR / "embeddings_clean.npy"
CLEAN_METADATA_FILE = DATA_DIR / "chunk_metadata_clean.json"


def main():
    print("Loading original knowledge base...")

    embeddings = np.load(EMBEDDINGS_FILE)

    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    if len(embeddings) != len(metadata):
        raise ValueError("Embeddings and metadata count mismatch!")

    kept_indices = []

    for i, chunk in enumerate(metadata):
        is_reference = (
            chunk["source"] == "breast-cancer.pdf"
            and (
                chunk["page"] >= 19
                or (
                    chunk["page"] == 18
                    and chunk["chunk_id"] != "breast-cancer.pdf_page18_chunk1"
                )
            )
        )

        if not is_reference:
            kept_indices.append(i)

    clean_embeddings = embeddings[kept_indices]
    clean_metadata = [metadata[i] for i in kept_indices]

    np.save(CLEAN_EMBEDDINGS_FILE, clean_embeddings)

    with open(CLEAN_METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(clean_metadata, f, ensure_ascii=False, indent=2)

    print("\n========== CLEANING REPORT ==========")
    print(f"Original chunks: {len(metadata)}")
    print(f"Removed references: {len(metadata) - len(clean_metadata)}")
    print(f"Remaining chunks: {len(clean_metadata)}")
    print(f"New embedding shape: {clean_embeddings.shape}")
    print("Original files preserved.")
    print("Validation:", "PASSED" if len(clean_embeddings) == len(clean_metadata) else "FAILED")


if __name__ == "__main__":
    main()
