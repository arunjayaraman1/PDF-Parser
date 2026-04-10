from __future__ import annotations

import os
from pathlib import Path

import pypdfium2 as pdfium


def main() -> None:
    # Backend runner sets PDFIUM_SOURCE for per-request temp-dir execution.
    pdf_path_str = os.getenv("PDFIUM_SOURCE", "Holiday 2026.pdf")
    pdf_path = Path(pdf_path_str).resolve()
    base_name = pdf_path.stem
    output_dir = Path(f"{base_name}_extracted")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "extracted.txt"

    pdf = pdfium.PdfDocument(str(pdf_path))
    total_pages = len(pdf)
    pages_text: list[str] = []

    for page_idx, page in enumerate(pdf, start=1):
        textpage = page.get_textpage()
        text = textpage.get_text_range()

        # Keep header format consistent with parser_service PAGE_HEADER_RE.
        pages_text.append(f"--- Page {page_idx} / {total_pages} ---")
        pages_text.append(text)

        textpage.close()
        page.close()

    pdf.close()
    output_file.write_text("\n\n".join(pages_text), encoding="utf-8")


if __name__ == "__main__":
    main()
