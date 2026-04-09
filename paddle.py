"""
Run PaddleOCR on a PDF (same pipeline as Streamlit ``PaddleOCRParser``).

Uses ``parsers/paddle_ocr_core.py``: text layer via PyMuPDF, else rendered pages + OCR.

**Do not** put this directory first on ``sys.path`` before importing PaddlePaddle — a file named
``paddle.py`` shadows the ``paddle`` framework. We load the core module by file path and drop
this script's directory from ``sys.path`` first.

Environment:
  PADDLEOCR_SOURCE         — path to PDF (default: Holiday 2026.pdf or first *.pdf in cwd)
  PADDLEOCR_LANG           — default en
  PADDLEOCR_USE_GPU        — set to 1 for GPU
  PADDLEOCR_DPI            — render DPI for OCR path (default 150)
  PADDLEOCR_MAX_WORKERS    — thread pool size (default 4)
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) in sys.path:
    sys.path.remove(str(_ROOT))

_spec = importlib.util.spec_from_file_location(
    "paddle_ocr_core",
    _ROOT / "parsers" / "paddle_ocr_core.py",
)
if _spec is None or _spec.loader is None:
    raise RuntimeError("Could not load parsers/paddle_ocr_core.py")
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
run_paddle_pdf_pipeline = _mod.run_paddle_pdf_pipeline


def _pick_pdf(cwd: Path) -> Path:
    pdf = cwd / "Holiday 2026.pdf"
    if pdf.exists():
        return pdf
    matches = sorted(cwd.glob("*.pdf"))
    if not matches:
        raise FileNotFoundError(
            "No PDF found. Set PADDLEOCR_SOURCE or add a .pdf in the project directory."
        )
    return matches[0]


def _resolve_source(cwd: Path) -> Path:
    raw = os.environ.get("PADDLEOCR_SOURCE", "").strip()
    if raw:
        p = Path(raw).expanduser()
        if not p.is_file():
            raise FileNotFoundError(f"PADDLEOCR_SOURCE not found: {p}")
        return p
    return _pick_pdf(cwd)


def main() -> None:
    runtime_cwd = Path.cwd()
    source = _resolve_source(runtime_cwd)
    stem = source.stem
    out_dir = runtime_cwd / f"{stem}_extracted_paddle"
    meta = run_paddle_pdf_pipeline(source, out_dir, write_sidecar_files=True)
    print(
        f"Done. Mode={meta['mode']} pages={meta['pages_count']} → {out_dir}\n"
        f"  output.txt, output.json, summary.txt",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
