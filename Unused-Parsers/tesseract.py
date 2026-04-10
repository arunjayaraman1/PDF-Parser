from __future__ import annotations

import sys
import time
from pathlib import Path

# Avoid shadowing
THIS_DIR = str(Path(__file__).resolve().parent)
if THIS_DIR in sys.path:
    sys.path.remove(THIS_DIR)

import pytesseract
import pypdfium2 as pdfium


def main() -> None:
    pdf_path = Path("Holiday 2026.pdf")
    if not pdf_path.exists():
        raise FileNotFoundError("PDF not found.")

    # ✅ Single output file
    out_file = pdf_path.parent / f"{pdf_path.stem}_tesseract.txt"

    print("Running Tesseract (plain text)...\n")

    t0 = time.perf_counter()

    pdf = pdfium.PdfDocument(str(pdf_path))

    text_blocks = []

    for i in range(len(pdf)):
        page_no = i + 1

        # Render page → image
        page = pdf[i]
        image = page.render(scale=2).to_pil()

        # 🔥 Plain text OCR
        text = pytesseract.image_to_string(image)

        text_blocks.append(
            f"--- Page {page_no} ---\n{text.strip()}"
        )

    full_text = "\n\n".join(text_blocks)

    out_file.write_text(full_text, encoding="utf-8")

    elapsed = time.perf_counter() - t0

    print("\n--- Done ---")
    print(f"Text file: {out_file}")
    print(f"Time: {elapsed:.2f} sec")


if __name__ == "__main__":
    main()