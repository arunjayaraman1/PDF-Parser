from __future__ import annotations

import sys
import time
from pathlib import Path
import json

# Avoid shadowing
THIS_DIR = str(Path(__file__).resolve().parent)
if THIS_DIR in sys.path:
    sys.path.remove(THIS_DIR)

from surya.detection import DetectionPredictor
from surya.foundation import FoundationPredictor
from surya.input.load import load_from_file
from surya.recognition import RecognitionPredictor


def main() -> None:
    pdf_path = Path("Holiday 2026.pdf")
    if not pdf_path.exists():
        raise FileNotFoundError("PDF not found.")

    # ✅ Single output file (native)
    out_file = pdf_path.parent / f"{pdf_path.stem}_surya.json"

    print("Running Surya OCR (native JSON)...\n")

    t0 = time.perf_counter()

    # Load images
    images, names = load_from_file(str(pdf_path), dpi=96)
    highres_images, _ = load_from_file(str(pdf_path), dpi=192)

    # Models
    foundation = FoundationPredictor()
    det = DetectionPredictor()
    rec = RecognitionPredictor(foundation)

    # OCR + layout
    predictions = rec(
        images,
        det_predictor=det,
        highres_images=highres_images,
        sort_lines=True
    )

    # ✅ Native structured output
    result = []

    for i, pred in enumerate(predictions):
        try:
            page_data = pred.model_dump(mode="json")
        except Exception:
            page_data = {
                "text_lines": [tl.text for tl in pred.text_lines]
            }

        result.append({
            "page": i + 1,
            "content": page_data
        })

    # Save JSON
    out_file.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    elapsed = time.perf_counter() - t0

    print("\n--- Done ---")
    print(f"Output: {out_file}")
    print(f"Pages: {len(result)}")
    print(f"Time: {elapsed:.2f} sec")


if __name__ == "__main__":
    main()