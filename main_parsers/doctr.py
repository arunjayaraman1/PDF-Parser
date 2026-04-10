from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# Avoid shadowing the doctr package.
THIS_DIR = str(Path(__file__).resolve().parent)
if THIS_DIR in sys.path:
    sys.path.remove(THIS_DIR)

from doctr.io import DocumentFile
from doctr.models import ocr_predictor


def _resolve_pdf() -> Path:
    raw = os.environ.get("DOCTR_SOURCE", "").strip()
    if raw:
        p = Path(raw).resolve()
        if p.exists():
            return p
        raise FileNotFoundError(f"DOCTR_SOURCE does not exist: {p}")
    matches = sorted(Path.cwd().glob("*.pdf"))
    if matches:
        return matches[0]
    raise FileNotFoundError("No PDF found. Set DOCTR_SOURCE or place a PDF in cwd.")


def main() -> None:
    pdf_path = _resolve_pdf()
    stem = pdf_path.stem
    out_dir = Path.cwd() / f"{stem}_extracted"
    out_dir.mkdir(parents=True, exist_ok=True)
    extracted_file = out_dir / "extracted.md"

    print(f"Running DocTR OCR on {pdf_path.name}...\n")

    t0 = time.perf_counter()

    doc = DocumentFile.from_pdf(str(pdf_path))

    predictor = ocr_predictor(pretrained=True)
    result = predictor(doc)

    total_pages = len(result.pages)
    parts: list[str] = []

    for page_idx, page in enumerate(result.pages):
        page_num = page_idx + 1
        parts.append(f"--- Page {page_num} / {total_pages} ---")

        lines: list[str] = []
        for block in page.blocks:
            for line in block.lines:
                text_line = " ".join(w.value for w in line.words).strip()
                if text_line:
                    lines.append(text_line)

        parts.append("\n".join(lines) if lines else "")

    extracted_file.write_text("\n\n".join(parts), encoding="utf-8")

    elapsed = time.perf_counter() - t0
    print("--- Done ---")
    print(f"Pages: {total_pages}")
    print(f"Output: {extracted_file}")
    print(f"Time: {elapsed:.2f} sec")


if __name__ == "__main__":
    main()
