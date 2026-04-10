"""
Run LlamaIndex LiteParse (Node CLI) on a PDF and write text + JSON under an output folder.

Requires the liteparse CLI (npm: @llamaindex/liteparse). The Python package can auto-install
it on first run unless LITEPARSE_NO_AUTO_INSTALL=1.

Environment (optional):
  LITEPARSE_DPI              — render DPI (default 100)
  LITEPARSE_NO_AUTO_INSTALL  — set to 1 to skip global npm install attempt
  LITEPARSE_OCR              — set to 0 to disable OCR (faster on text-based PDFs)
  LITEPARSE_TIMEOUT          — subprocess timeout in seconds (unset = no limit)
  LITEPARSE_MAX_PAGES        — max pages to parse (unset = all, up to CLI default)
  LITEPARSE_TARGET_PAGES     — page spec e.g. 1-3 or 1,5,7-9 (unset = all)
  LITEPARSE_NUM_WORKERS      — parallel page workers for OCR (optional)
"""
from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

# Local file ``liteparse.py`` shadows the ``liteparse`` package.
_THIS_DIR = str(Path(__file__).resolve().parent)
if _THIS_DIR in sys.path:
    sys.path.remove(_THIS_DIR)

from liteparse import LiteParse  # noqa: E402
from liteparse.types import CLINotFoundError, ParseError  # noqa: E402


def _pick_pdf(cwd: Path) -> Path:
    pdf = cwd / "Holiday 2026.pdf"
    if pdf.exists():
        return pdf
    matches = sorted(cwd.glob("*.pdf"))
    if not matches:
        raise FileNotFoundError(
            "No PDF found. Place Holiday 2026.pdf in the project directory or add a .pdf file."
        )
    return matches[0]


def _dpi() -> int:
    raw = os.environ.get("LITEPARSE_DPI", "100")
    try:
        return max(72, min(int(raw), 600))
    except ValueError:
        return 150


def _ocr_enabled() -> bool:
    return os.environ.get("LITEPARSE_OCR", "1").lower() not in ("0", "false", "no")


def _timeout_sec() -> float | None:
    raw = os.environ.get("LITEPARSE_TIMEOUT", "120").strip()
    if not raw:
        return None
    try:
        t = float(raw)
    except ValueError:
        return None
    return t if t > 0 else None


def _max_pages() -> int | None:
    raw = os.environ.get("LITEPARSE_MAX_PAGES", "").strip()
    if not raw:
        return None
    try:
        n = int(raw)
        return max(1, n)
    except ValueError:
        return None


def _target_pages() -> str | None:
    raw = os.environ.get("LITEPARSE_TARGET_PAGES", "").strip()
    return raw or None


def _num_workers() -> int | None:
    raw = os.environ.get("LITEPARSE_NUM_WORKERS", "4").strip()
    if not raw:
        return None
    try:
        return max(1, int(raw))
    except ValueError:
        return None


def _parse_options() -> dict[str, Any]:
    """Keyword args for LiteParse.parse (only set when env provides a value)."""
    opts: dict[str, Any] = {
        "ocr_enabled": _ocr_enabled(),
        "dpi": _dpi(),
    }
    t = _timeout_sec()
    if t is not None:
        opts["timeout"] = t
    mp = _max_pages()
    if mp is not None:
        opts["max_pages"] = mp
    tp = _target_pages()
    if tp is not None:
        opts["target_pages"] = tp
    nw = _num_workers()
    if nw is not None:
        opts["num_workers"] = nw
    return opts


def main() -> None:
    # Same as MinorU.py: use process cwd so FastAPI (subprocess cwd=temp dir) reads/writes there.
    runtime_cwd = Path.cwd()
    pdf_path = _pick_pdf(runtime_cwd)
    out_root = runtime_cwd / f"{pdf_path.stem}_extracted_liteparse"
    out_root.mkdir(parents=True, exist_ok=True)

    no_auto = os.environ.get("LITEPARSE_NO_AUTO_INSTALL", "1").lower() in (
        "1",
        "true",
        "yes",
    )
    parser = LiteParse(install_if_not_available=not no_auto)
    opts = _parse_options()

    to = opts.get("timeout")
    print(
        f"LiteParse: {pdf_path.name} → {out_root} "
        f"(dpi={opts['dpi']}, ocr={opts['ocr_enabled']}) …",
        file=sys.stderr,
    )
    print(f"[DEBUG] cwd={runtime_cwd}", file=sys.stderr)
    print(f"[DEBUG] source={pdf_path}", file=sys.stderr)
    print(f"[DEBUG] out_root={out_root}", file=sys.stderr)
    print(f"[DEBUG] install_if_not_available={not no_auto} LITEPARSE_NO_AUTO_INSTALL={no_auto}", file=sys.stderr)
    print(
        f"[DEBUG] dpi={opts['dpi']} ocr_enabled={opts['ocr_enabled']} "
        f"timeout={'none' if to is None else f'{to}s'}",
        file=sys.stderr,
    )
    if "max_pages" in opts:
        print(f"[DEBUG] max_pages={opts['max_pages']}", file=sys.stderr)
    if "target_pages" in opts:
        print(f"[DEBUG] target_pages={opts['target_pages']!r}", file=sys.stderr)
    if "num_workers" in opts:
        print(f"[DEBUG] num_workers={opts['num_workers']}", file=sys.stderr)
    print(f"[DEBUG] parse_kwargs={opts!r}", file=sys.stderr)

    t0 = time.perf_counter()
    try:
        result = parser.parse(pdf_path, **opts)
    except CLINotFoundError as exc:
        print(f"[DEBUG] CLINotFoundError: {exc}", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        print(
            "Install Node.js (>= 18) and: npm install -g @llamaindex/liteparse",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc
    except ParseError as exc:
        print(f"[DEBUG] ParseError: {exc}", file=sys.stderr)
        print(f"LiteParse failed: {exc}", file=sys.stderr)
        err_raw = getattr(exc, "stderr", None)
        if err_raw:
            err_text = (
                err_raw.decode(errors="replace")
                if isinstance(err_raw, (bytes, bytearray))
                else str(err_raw)
            )
            for line in err_text.splitlines():
                print(f"[liteparse][stderr] {line}", file=sys.stderr)
        out_raw = getattr(exc, "stdout", None)
        if out_raw:
            out_text = (
                out_raw.decode(errors="replace")
                if isinstance(out_raw, (bytes, bytearray))
                else str(out_raw)
            )
            for line in out_text.splitlines():
                print(f"[liteparse][stdout] {line}", file=sys.stderr)
        raise SystemExit(1) from exc
    except TimeoutError as exc:
        print(f"[DEBUG] TimeoutError: {exc}", file=sys.stderr)
        print(f"Timed out: {exc}", file=sys.stderr)
        print(
            "Raise LITEPARSE_TIMEOUT or narrow scope with LITEPARSE_MAX_PAGES / "
            "LITEPARSE_TARGET_PAGES; try LITEPARSE_OCR=0 for text PDFs.",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc

    elapsed = time.perf_counter() - t0
    print(
        f"[DEBUG] elapsed={elapsed:.2f}s num_pages={result.num_pages}",
        file=sys.stderr,
    )
    dpi = opts["dpi"]

    extracted_txt = out_root / "extracted.txt"
    summary_txt = out_root / "summary.txt"
    json_path = out_root / "parse_result.json"

    extracted_txt.write_text(
        "\n".join(
            [
                "=" * 80,
                "LiteParse — extracted text",
                f"Source: {pdf_path.name}",
                f"Pages: {result.num_pages}",
                "=" * 80,
                "",
                result.text or "",
                "",
            ]
        ),
        encoding="utf-8",
    )

    try:
        json_path.write_text(
            json.dumps(asdict(result), indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
    except Exception:
        json_path.write_text(
            json.dumps(
                {"text": result.text, "num_pages": result.num_pages, "json": result.json},
                indent=2,
                ensure_ascii=False,
                default=str,
            ),
            encoding="utf-8",
        )

    summary_lines = [
        "--- LiteParse extraction summary ---",
        f"Source PDF: {pdf_path.name}",
        f"Output folder: {out_root}",
        f"DPI: {dpi} (LITEPARSE_DPI)",
        f"OCR: {opts['ocr_enabled']} (LITEPARSE_OCR)",
    ]
    if "timeout" in opts:
        summary_lines.append(f"Timeout: {opts['timeout']}s (LITEPARSE_TIMEOUT)")
    if "max_pages" in opts:
        summary_lines.append(f"max_pages: {opts['max_pages']} (LITEPARSE_MAX_PAGES)")
    if "target_pages" in opts:
        summary_lines.append(f"target_pages: {opts['target_pages']} (LITEPARSE_TARGET_PAGES)")
    if "num_workers" in opts:
        summary_lines.append(f"num_workers: {opts['num_workers']} (LITEPARSE_NUM_WORKERS)")
    summary_lines.extend(
        [
            f"Pages: {result.num_pages}",
            f"Time: {elapsed:.2f} s",
            f"Text: {extracted_txt.name}",
            f"Structured JSON: {json_path.name}",
            "",
        ]
    )
    summary_txt.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    print(f"Wrote: {extracted_txt}")
    print(f"Wrote: {summary_txt}")
    print(f"Wrote: {json_path}")


if __name__ == "__main__":
    main()
