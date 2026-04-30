from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

# Avoid shadowing the docling package.
THIS_DIR = str(Path(__file__).resolve().parent)
if THIS_DIR in sys.path:
    sys.path.remove(THIS_DIR)

from docling.document_converter import DocumentConverter
from docling_core.transforms.serializer.markdown import MarkdownDocSerializer, MarkdownParams


def _resolve_pdf() -> Path:
    raw = os.environ.get("DOCLING_SOURCE", "").strip()
    if raw:
        p = Path(raw).resolve()
        if p.exists():
            return p
        raise FileNotFoundError(f"DOCLING_SOURCE does not exist: {p}")
    matches = sorted(Path.cwd().glob("*.pdf"))
    if matches:
        return matches[0]
    raise FileNotFoundError("No PDF found. Set DOCLING_SOURCE or place a PDF in cwd.")


def main() -> None:
    pdf_path = _resolve_pdf()
    stem = pdf_path.stem
    out_dir = Path.cwd() / f"{stem}_extracted"
    out_dir.mkdir(parents=True, exist_ok=True)
    extracted_file = out_dir / "extracted.md"

    print(f"Running Docling on {pdf_path.name}...\n")

    t0 = time.perf_counter()

    converter = DocumentConverter()
    result = converter.convert(str(pdf_path))

    if result.status.value not in ("success", "partial_success"):
        raise RuntimeError(f"Docling conversion failed: {result.status.value}")

    doc = result.document
    page_keys = sorted(doc.pages.keys())
    total_pages = len(page_keys)

    parts: list[str] = []
    for page_no in page_keys:
        ser = MarkdownDocSerializer(doc=doc, params=MarkdownParams(pages={page_no}))
        page_md = ser.serialize().text.strip()
        parts.append(f"--- Page {page_no} / {total_pages} ---")
        parts.append(page_md)

    extracted_file.write_text("\n\n".join(parts), encoding="utf-8")

    json_file = out_dir / "extracted.json"
    json_file.write_text(
        json.dumps(doc.export_to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    elapsed = time.perf_counter() - t0
    print("--- Done ---")
    print(f"Output: {extracted_file}")
    print(f"JSON:   {json_file}")
    print(f"Time: {elapsed:.2f} sec")


if __name__ == "__main__":
    main()
