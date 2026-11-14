
from pathlib import Path
import json
import re

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR / "knowledge_base" / "processed" / "extracted_text.json"
)

OUTPUT_FILE = (
    BASE_DIR / "knowledge_base" / "processed" / "chunks.json"
)

CHUNK_SIZE = 300
CHUNK_OVERLAP = 50


def split_into_paragraphs(text):
    paragraphs = re.split(r"\n\s*\n", text.strip())
    return [p.split() for p in paragraphs if p.strip()]


def create_chunks(page):
    paragraphs = split_into_paragraphs(page["text"])

    chunks = []
    current_words = []

    for paragraph_words in paragraphs:
        remaining_words = paragraph_words.copy()

        while remaining_words:
            available_space = CHUNK_SIZE - len(current_words)

            words_to_add = remaining_words[:available_space]

            current_words.extend(words_to_add)
            remaining_words = remaining_words[available_space:]

            if len(current_words) == CHUNK_SIZE:
                chunks.append(current_words.copy())

                # Keep the last 50 words for the next chunk
                current_words = current_words[-CHUNK_OVERLAP:]

    # Save the final chunk, avoiding overlap-only chunks
    if current_words and (
        not chunks or len(current_words) > CHUNK_OVERLAP
    ):
        chunks.append(current_words.copy())

    return chunks


def validate_chunks(chunks):
    errors = []

    ids = [chunk["chunk_id"] for chunk in chunks]

    if len(ids) != len(set(ids)):
        errors.append("Duplicate chunk IDs found.")

    for index, chunk in enumerate(chunks, start=1):
        actual_count = len(chunk["text"].split())

        if not chunk["text"].strip():
            errors.append(f"Chunk {index} is empty.")

        if actual_count > CHUNK_SIZE:
            errors.append(
                f"Chunk {index} exceeds {CHUNK_SIZE} words."
            )

        if actual_count != chunk["word_count"]:
            errors.append(
                f"Word count mismatch in chunk {index}."
            )

        if not chunk.get("source") or not chunk.get("page"):
            errors.append(
                f"Missing source or page in chunk {index}."
            )

    return errors


def main():
    if not INPUT_FILE.exists():
        print("Error: extracted_text.json not found.")
        return

    with INPUT_FILE.open("r", encoding="utf-8") as file:
        pages = json.load(file)

    all_chunks = []

    for page in pages:
        page_chunks = create_chunks(page)

        for index, words in enumerate(page_chunks, start=1):
            text = " ".join(words)

            all_chunks.append({
                "source": page["source"],
                "page": page["page"],
                "chunk_id": (
                    f"{page['source']}_page{page['page']}_chunk{index}"
                ),
                "word_count": len(words),
                "text": text
            })

    errors = validate_chunks(all_chunks)

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            all_chunks,
            file,
            ensure_ascii=False,
            indent=2
        )

    print("\n========== CHUNKING REPORT ==========")
    print(f"Pages processed: {len(pages)}")
    print(f"Total chunks: {len(all_chunks)}")

    if all_chunks:
        average = sum(
            chunk["word_count"] for chunk in all_chunks
        ) / len(all_chunks)

        print(f"Average words per chunk: {average:.2f}")
        print(
            "Largest chunk:",
            max(chunk["word_count"] for chunk in all_chunks)
        )

    if errors:
        print("\nValidation: FAILED")
        for error in errors:
            print("-", error)
    else:
        print("\nValidation: PASSED")

    print(f"\nSaved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
