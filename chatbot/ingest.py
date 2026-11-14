
from pathlib import Path
import json
import pymupdf  # PyMuPDF

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
PDF_DIR = BASE_DIR / "knowledge_base" / "pdfs"
OUTPUT_DIR = BASE_DIR / "knowledge_base" / "processed"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def extract_pdf(pdf_path):
    pages = []

    with pymupdf.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf, start=1):
            text = page.get_text("text").strip()

            if not text:
                continue

            pages.append({
                "source": pdf_path.name,
                "page": page_number,
                "text": text
            })

    return pages


def main():
    all_pages = []

    pdf_files = sorted(PDF_DIR.glob("*.pdf"))

    if not pdf_files:
        print("No PDF files found.")
        return

    for pdf_path in pdf_files:
        print(f"\nProcessing: {pdf_path.name}")

        try:
            pages = extract_pdf(pdf_path)
            all_pages.extend(pages)

            print(f"Extracted {len(pages)} pages.")

        except Exception as error:
            print(f"Error processing {pdf_path.name}: {error}")

    output_file = OUTPUT_DIR / "extracted_text.json"

    with output_file.open("w", encoding="utf-8") as file:
        json.dump(
            all_pages,
            file,
            ensure_ascii=False,
            indent=2
        )

    print("\nExtraction completed!")
    print(f"Total extracted pages: {len(all_pages)}")
    print(f"Output saved to: {output_file}")


if __name__ == "__main__":
    main()
