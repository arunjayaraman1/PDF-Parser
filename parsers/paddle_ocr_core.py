"""
PaddleOCR PDF pipeline: PyMuPDF text layer when substantial, else rendered page + OCR.

Used by ``paddle.py`` (loaded by path so ``paddle.py`` does not shadow PaddlePaddle).

Environment (read by callers / ``paddle.py`` docs):
  PADDLEOCR_LANG, PADDLEOCR_USE_GPU, PADDLEOCR_DPI, PADDLEOCR_MAX_WORKERS (reserved; pages OCR sequentially)
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Literal

import numpy as np

try:
    import fitz  # PyMuPDF
except ModuleNotFoundError as exc:
    raise RuntimeError("PyMuPDF (fitz) is required for paddle_ocr_core") from exc

try:
    import cv2
except ModuleNotFoundError as exc:
    raise RuntimeError("opencv-python is required for paddle_ocr_core") from exc


def _env_lang() -> str:
    raw = os.environ.get("PADDLEOCR_LANG", "en").strip() or "en"
    return raw


def _env_use_gpu() -> bool:
    return os.environ.get("PADDLEOCR_USE_GPU", "").lower() in ("1", "true", "yes")


def _env_dpi() -> int:
    raw = os.environ.get("PADDLEOCR_DPI", "150").strip()
    try:
        return max(72, min(int(raw), 600))
    except ValueError:
        return 150


def _pixmap_to_bgr(pix: fitz.Pixmap) -> np.ndarray:
    """Convert PyMuPDF pixmap to BGR uint8 (H,W,3) for PaddleOCR."""
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 4:
        return cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
    if pix.n == 3:
        return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
    if pix.n == 1:
        return cv2.cvtColor(arr, cv2.COLOR_GRAY2BGR)
    raise ValueError(f"Unsupported pixmap channels: {pix.n}")


def _text_is_substantial(text: str) -> bool:
    t = (text or "").strip()
    if len(t) < 24:
        return False
    words = len(t.split())
    return words >= 5 or len(t) >= 120


def _ocr_result_to_lines(res: Any) -> list[str]:
    """Extract recognition lines from a PaddleX OCRResult / dict-like object."""
    if res is None:
        return []
    if isinstance(res, dict):
        texts = res.get("rec_texts") or []
    else:
        try:
            texts = res["rec_texts"]
        except (KeyError, TypeError):
            texts = getattr(res, "rec_texts", None) or []
    out: list[str] = []
    for t in texts:
        if isinstance(t, tuple):
            t = t[0]
        if t:
            out.append(str(t))
    return out


def _run_ocr_on_bgr(ocr: Any, bgr: np.ndarray) -> str:
    outputs = ocr.predict(bgr)
    lines: list[str] = []
    for item in outputs or []:
        lines.extend(_ocr_result_to_lines(item))
    return "\n".join(lines).strip()


def _make_ocr():
    """Lazy import so import errors point at paddlepaddle / paddleocr install."""
    try:
        from paddleocr import PaddleOCR
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "paddleocr is not installed. Install with: pip install paddleocr"
        ) from exc

    lang = _env_lang()
    use_gpu = _env_use_gpu()
    device = "gpu:0" if use_gpu else "cpu"
    try:
        return PaddleOCR(lang=lang, device=device)
    except TypeError:
        return PaddleOCR(lang=lang)


def run_paddle_pdf_pipeline(
    pdf_path: Path,
    out_dir: Path,
    *,
    write_sidecar_files: bool = True,
) -> dict[str, Any]:
    """
    Extract text from ``pdf_path``; write ``extracted.txt``, ``output.txt``, ``output.json``, ``summary.txt``.

    Returns metadata: ``mode`` (``text`` | ``ocr`` | ``mixed``), ``pages_count``, ``text_pages``, ``ocr_pages``.
    """
    pdf_path = Path(pdf_path).expanduser().resolve()
    out_dir = Path(out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    dpi = _env_dpi()

    doc = fitz.open(pdf_path)
    try:
        n_pages = len(doc)
        page_modes: list[Literal["text", "ocr"]] = []
        page_texts: list[str] = []

        # Decide per-page: text vs OCR
        ocr_indices: list[int] = []
        for i in range(n_pages):
            page = doc[i]
            raw = page.get_text("text") or ""
            if _text_is_substantial(raw):
                page_modes.append("text")
                page_texts.append(raw.strip())
            else:
                page_modes.append("ocr")
                page_texts.append("")  # fill later
                ocr_indices.append(i)

        ocr = _make_ocr() if ocr_indices else None

        if ocr_indices:
            assert ocr is not None
            for idx in ocr_indices:
                page = doc[idx]
                pix = page.get_pixmap(dpi=dpi)
                bgr = _pixmap_to_bgr(pix)
                page_texts[idx] = _run_ocr_on_bgr(ocr, bgr)

        text_pages = sum(1 for m in page_modes if m == "text")
        ocr_pages = sum(1 for m in page_modes if m == "ocr")
        if ocr_pages == 0:
            mode: Literal["text", "ocr", "mixed"] = "text"
        elif text_pages == 0:
            mode = "ocr"
        else:
            mode = "mixed"

        lines_out: list[str] = []
        json_pages: list[dict[str, Any]] = []
        for i in range(n_pages):
            header = f"--- Page {i + 1} / {n_pages} ---"
            lines_out.append(header)
            lines_out.append(page_texts[i])
            lines_out.append("")
            json_pages.append(
                {
                    "page": i + 1,
                    "mode": page_modes[i],
                    "text": page_texts[i],
                }
            )

        combined = "\n".join(lines_out).strip() + "\n"

        meta = {
            "mode": mode,
            "pages_count": n_pages,
            "text_pages": text_pages,
            "ocr_pages": ocr_pages,
            "dpi": dpi,
            "lang": _env_lang(),
        }

        if write_sidecar_files:
            extracted_txt = out_dir / "extracted.txt"
            output_txt = out_dir / "output.txt"
            output_json = out_dir / "output.json"
            summary_txt = out_dir / "summary.txt"

            extracted_txt.write_text(combined, encoding="utf-8")
            output_txt.write_text(combined, encoding="utf-8")
            output_json.write_text(
                json.dumps(
                    {
                        "source": str(pdf_path),
                        "output_dir": str(out_dir),
                        "meta": meta,
                        "pages": json_pages,
                    },
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            summary_txt.write_text(
                "\n".join(
                    [
                        "--- PaddleOCR PDF pipeline ---",
                        f"Source: {pdf_path}",
                        f"Output: {out_dir}",
                        f"Mode: {mode} (text_pages={text_pages}, ocr_pages={ocr_pages})",
                        f"DPI (OCR raster): {dpi}",
                        f"Lang: {_env_lang()}",
                        f"PADDLEOCR_USE_GPU: {_env_use_gpu()}",
                        f"Files: extracted.txt, output.txt, output.json",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
    finally:
        doc.close()

    return meta


__all__ = ["run_paddle_pdf_pipeline"]
