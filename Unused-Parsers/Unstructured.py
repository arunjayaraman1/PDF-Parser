from __future__ import annotations

import sys
import time
from pathlib import Path
import json

# Avoid shadowing
THIS_DIR = str(Path(__file__).resolve().parent)
if THIS_DIR in sys.path:
    sys.path.remove(THIS_DIR)

from unstructured.partition.pdf import partition_pdf


def main() -> None:
    pdf_path = Path("Meta-Harness_ End-to-End Optimization of Model Harnesses.pdf") 
    if not pdf_path.exists():
        raise FileNotFoundError("PDF not found.")

    # ✅ Native output file (JSON of elements)
    out_file = pdf_path.parent / f"{pdf_path.stem}_unstructured_elements.json"

    print("Running Unstructured (Element Objects)...\n")

    t0 = time.perf_counter()

    elements = partition_pdf(
        filename=str(pdf_path),
        strategy="hi_res",   # or "fast"
        infer_table_structure=True
    )

    # ✅ Convert element objects → dict (serializable)
    element_data = []

    for idx, el in enumerate(elements):
        metadata = getattr(el, "metadata", None)

        element_data.append({
            "index": idx + 1,
            "type": type(el).__name__,
            "category": getattr(el, "category", None),
            "text": (el.text or "").strip(),
            "page_number": getattr(metadata, "page_number", None) if metadata else None,
        })

    # Save JSON
    out_file.write_text(
        json.dumps(element_data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    elapsed = time.perf_counter() - t0

    print("\n--- Done ---")
    print(f"Elements JSON: {out_file}")
    print(f"Total elements: {len(element_data)}")
    print(f"Time: {elapsed:.2f} sec")


if __name__ == "__main__":
    main()