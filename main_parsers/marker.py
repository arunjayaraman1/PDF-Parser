from __future__ import annotations

import os
import re
import sys
import time
from pathlib import Path

# Matches the pagination separator marker inserts when paginate_output=True:
# e.g.  {0}------------------------------------------------  (page_id + 48 dashes, default)
_PAGE_SEP_RE = re.compile(r"\{(\d+)\}-{40,}")

# Avoid shadowing the marker package.
THIS_DIR = str(Path(__file__).resolve().parent)
if THIS_DIR in sys.path:
    sys.path.remove(THIS_DIR)

from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered
from marker.config.parser import ConfigParser
from marker.logger import configure_logging


def _resolve_pdf() -> Path:
    raw = os.environ.get("MARKER_SOURCE", "").strip()
    if raw:
        p = Path(raw).resolve()
        if p.exists():
            return p
        raise FileNotFoundError(f"MARKER_SOURCE does not exist: {p}")
    matches = sorted(Path.cwd().glob("*.pdf"))
    if matches:
        return matches[0]
    raise FileNotFoundError("No PDF found. Set MARKER_SOURCE or place a PDF in cwd.")


def main() -> None:
    configure_logging()

    pdf_path = _resolve_pdf()
    stem = pdf_path.stem
    out_dir = Path.cwd() / f"{stem}_extracted"
    out_dir.mkdir(parents=True, exist_ok=True)
    extracted_file = out_dir / "extracted.md"

    use_llm = os.environ.get("MARKER_USE_LLM", "").lower() in ("1", "true", "yes")

    print(f"Running Marker (llm={use_llm}) on {pdf_path.name}...\n")

    t0 = time.perf_counter()

    cli_options = {
        "output_format": "markdown",
        "use_llm": use_llm,
        "disable_image_extraction": True,
        "paginate_output": True,
    }

    config_parser = ConfigParser(cli_options)
    models = create_model_dict()

    converter = PdfConverter(
        config=config_parser.generate_config_dict(),
        artifact_dict=models,
        processor_list=config_parser.get_processors(),
        renderer=config_parser.get_renderer(),
        llm_service=config_parser.get_llm_service(),
    )

    rendered = converter(str(pdf_path))
    text, _, _ = text_from_rendered(rendered)

    if not text.strip():
        raise RuntimeError("Marker returned empty output.")

    # Split on marker's pagination separators: {N}------------------------------------------------
    # re.split with a capturing group returns ['pre', '0', 'page0', '1', 'page1', ...]
    segments = _PAGE_SEP_RE.split(text)
    raw_pages: list[tuple[int, str]] = []
    if len(segments) >= 3:
        # Odd indices = page_id, even indices (after [0]) = page content
        for i in range(1, len(segments) - 1, 2):
            page_num = int(segments[i]) + 1  # marker is 0-indexed; convert to 1-indexed
            content = segments[i + 1].strip()
            raw_pages.append((page_num, content))
    if not raw_pages:
        # paginate_output separator not found — treat entire output as page 1
        raw_pages = [(1, text.strip())]

    total_pages = len(raw_pages)
    parts: list[str] = []
    for page_num, page_text in raw_pages:
        parts.append(f"--- Page {page_num} / {total_pages} ---")
        parts.append(page_text)

    extracted_file.write_text("\n\n".join(parts), encoding="utf-8")

    elapsed = time.perf_counter() - t0
    print("--- Done ---")
    print(f"Output: {extracted_file}")
    print(f"Time: {elapsed:.2f} sec")


if __name__ == "__main__":
    main()