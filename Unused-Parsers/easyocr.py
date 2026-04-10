from __future__ import annotations

import sys
import time
from pathlib import Path

# Avoid shadowing easyocr
THIS_DIR = str(Path(__file__).resolve().parent)
if THIS_DIR in sys.path:
    sys.path.remove(THIS_DIR)

import easyocr
from pdf2image import convert_from_path


def main() -> None:
    pdf_path = Path("Meta-Harness_ End-to-End Optimization of Model Harnesses.pdf") 
    if not pdf_path.exists():
        raise FileNotFoundError("PDF not found.")

    out_root = pdf_path.parent / f"{pdf_path.stem}_easyocr_pdf2image"
    out_root.mkdir(parents=True, exist_ok=True)

    md_file = out_root / "output.md"
    images_dir = out_root / "pages"
    images_dir.mkdir(parents=True, exist_ok=True)

    print("Running EasyOCR with pdf2image...\n")

    t0 = time.perf_counter()

    # 🔥 Convert PDF → images (pdf2image)
    pages = convert_from_path(str(pdf_path), dpi=200)

    reader = easyocr.Reader(['en'], gpu=False)

    markdown_lines = []

    for i, page in enumerate(pages):
        page_no = i + 1

        # Save image
        img_path = images_dir / f"page-{page_no}.png"
        page.save(img_path, "PNG")

        # OCR
        results = reader.readtext(str(img_path))

        markdown_lines.append(f"# Page {page_no}\n")

        for bbox, text, conf in results:
            if text.strip():
                markdown_lines.append(text)

        markdown_lines.append("\n")

    # Save Markdown
    md_text = "\n".join(markdown_lines)
    md_file.write_text(md_text, encoding="utf-8")

    elapsed = time.perf_counter() - t0

    print("\n--- Done ---")
    print(f"Markdown: {md_file}")
    print(f"Images: {images_dir}")
    print(f"Time: {elapsed:.2f} sec")


if __name__ == "__main__":
    main()