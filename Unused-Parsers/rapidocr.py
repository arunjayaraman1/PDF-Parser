from __future__ import annotations

import sys
import time
from pathlib import Path

# Avoid shadowing
THIS_DIR = str(Path(__file__).resolve().parent)
if THIS_DIR in sys.path:
    sys.path.remove(THIS_DIR)

from rapidocr_onnxruntime import RapidOCR
import pypdfium2 as pdfium


def main() -> None:
    pdf_path = Path("Holiday 2026.pdf")
    if not pdf_path.exists():
        raise FileNotFoundError("PDF not found.")

    # ✅ Output file (raw list format)
    out_file = pdf_path.parent / f"{pdf_path.stem}_rapidocr.txt"

    print("Running RapidOCR (List Output → file)...\n")

    t0 = time.perf_counter()

    ocr = RapidOCR()
    pdf = pdfium.PdfDocument(str(pdf_path))

    lines = []

    for i in range(len(pdf)):
        page_no = i + 1

        # Render page → image
        page = pdf[i]
        image = page.render(scale=2).to_numpy()

        # 🔥 Native output
        result, _ = ocr(image)

        lines.append(f"--- Page {page_no} ---")

        for item in result or []:
            lines.append(str(item))  # ← keep raw tuple format

        lines.append("")  # spacing

    # Save file
    out_file.write_text("\n".join(lines), encoding="utf-8")

    elapsed = time.perf_counter() - t0

    print("\n--- Done ---")
    print(f"Saved: {out_file}")
    print(f"Time: {elapsed:.2f} sec")


if __name__ == "__main__":
    main()