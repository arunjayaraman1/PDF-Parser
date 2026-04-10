from __future__ import annotations

import sys
import time
from pathlib import Path

# Avoid shadowing pdfplumber
THIS_DIR = str(Path(__file__).resolve().parent)
if THIS_DIR in sys.path:
    sys.path.remove(THIS_DIR)

import pdfplumber


def main() -> None:
    pdf_path = Path("Meta-Harness_ End-to-End Optimization of Model Harnesses.pdf") 
    if not pdf_path.exists():
        raise FileNotFoundError("PDF not found.")

    # ✅ Single output file
    out_file = pdf_path.parent / f"{pdf_path.stem}_pdfplumber.md"

    print("Running pdfplumber (Markdown only)...\n")

    t0 = time.perf_counter()

    markdown_lines = []

    with pdfplumber.open(str(pdf_path)) as pdf:
        for i, page in enumerate(pdf.pages):
            page_no = i + 1

            markdown_lines.append(f"# Page {page_no}\n")

            # ✅ Extract text
            text = page.extract_text()
            if text:
                markdown_lines.append(text)

            # ✅ Extract tables (basic)
            tables = page.extract_tables() or []
            for t_idx, table in enumerate(tables):
                markdown_lines.append(f"\nTable {t_idx + 1}:\n")

                for row in table:
                    row_text = " | ".join([cell or "" for cell in row])
                    markdown_lines.append(row_text)

            markdown_lines.append("\n")

    md_text = "\n".join(markdown_lines)
    out_file.write_text(md_text, encoding="utf-8")

    elapsed = time.perf_counter() - t0

    print("\n--- Done ---")
    print(f"Markdown: {out_file}")
    print(f"Time: {elapsed:.2f} sec")


if __name__ == "__main__":
    main()