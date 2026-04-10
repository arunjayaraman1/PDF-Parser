from __future__ import annotations

import json
import os
from pathlib import Path

import requests

# Default local API (nlm-ingestor)
API_URL = os.environ.get(
    "LLMSHERPA_API_URL",
    "http://127.0.0.1:5010/api/parseDocument?renderFormat=all",
)


def _resolve_pdf() -> Path:
    raw = os.environ.get("LLMSHERPA_SOURCE", "").strip()
    if raw:
        p = Path(raw).resolve()
        if p.exists():
            return p
        raise FileNotFoundError(f"LLMSHERPA_SOURCE does not exist: {p}")
    matches = sorted(Path.cwd().glob("*.pdf"))
    if matches:
        return matches[0]
    raise FileNotFoundError("No PDF found. Set LLMSHERPA_SOURCE or place a PDF in cwd.")


def _extract_block_text(block: dict) -> str:
    """Return a plain-text representation of a single LLMSherpa block."""
    tag = block.get("tag", "")

    def _to_text(value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, (int, float, bool)):
            return str(value)
        if isinstance(value, dict):
            if "text" in value:
                return _to_text(value.get("text"))
            if "value" in value:
                return _to_text(value.get("value"))
            if "cell_value" in value:
                return _to_text(value.get("cell_value"))
            return json.dumps(value, ensure_ascii=False)
        if isinstance(value, list):
            return " ".join(part for part in (_to_text(v).strip() for v in value) if part)
        return str(value)

    # Table blocks: render rows as pipe-separated lines.
    if tag == "table":
        rows = block.get("table_rows", [])
        lines: list[str] = []
        for row in rows:
            cells = row.get("cells", [])
            if cells:
                lines.append(" | ".join(_to_text(c.get("cell_value", "")) for c in cells))
            elif "cell_value" in row:
                # full_row spanning all columns
                lines.append(_to_text(row["cell_value"]))
        return "\n".join(lines)

    # Text / header / list_item blocks: use sentences list.
    sentences = block.get("sentences", [])
    if isinstance(sentences, list):
        return " ".join(_to_text(sentence) for sentence in sentences)
    if isinstance(sentences, str):
        return sentences

    # Generic fallback.
    return str(block.get("text", "")).strip()


def _blocks_to_paged_text(data: dict) -> list[tuple[int, str]]:
    """Extract text from LLMSherpa JSON grouped by page number.

    The actual API response nests blocks at:
      data["return_dict"]["result"]["blocks"]

    Returns list of (page_number, text) tuples sorted by page (1-indexed).
    Falls back to a single page dump if the structure is unrecognised.
    """
    # Navigate the actual API response envelope.
    return_dict = data.get("return_dict", {})
    result = return_dict.get("result", {})
    blocks = result.get("blocks", [])

    # Also accept flat legacy structures just in case.
    if not blocks:
        blocks = data.get("blocks", data.get("chunks", []))

    page_texts: dict[int, list[str]] = {}

    for block in blocks:
        page_num = block.get("page_idx", block.get("page", 0))
        # LLMSherpa pages are 0-indexed; convert to 1-indexed.
        page_num = int(page_num) + 1 if isinstance(page_num, int) else 1
        text = _extract_block_text(block).strip()
        if text:
            page_texts.setdefault(page_num, []).append(text)

    if not page_texts:
        # Fallback: unrecognised structure — dump raw JSON as a single page.
        return [(1, json.dumps(data, ensure_ascii=False))]

    return [(page_num, "\n\n".join(texts)) for page_num, texts in sorted(page_texts.items())]


def main() -> None:
    pdf_path = _resolve_pdf()
    stem = pdf_path.stem
    out_dir = Path.cwd() / f"{stem}_extracted"
    out_dir.mkdir(parents=True, exist_ok=True)
    extracted_file = out_dir / "extracted.txt"

    print(f"Running LLMSherpa (API → extracted.txt) on {pdf_path.name}...\n")

    with open(pdf_path, "rb") as f:
        response = requests.post(
            API_URL,
            files={"file": (pdf_path.name, f, "application/pdf")},
            timeout=120,
        )

    if response.status_code != 200:
        raise RuntimeError(f"LLMSherpa API failed: {response.status_code} — {response.text[:300]}")

    data = response.json()
    paged = _blocks_to_paged_text(data)
    total_pages = paged[-1][0] if paged else 1

    parts: list[str] = []
    for page_num, text in paged:
        parts.append(f"--- Page {page_num} / {total_pages} ---")
        parts.append(text)

    extracted_file.write_text("\n\n".join(parts), encoding="utf-8")

    print("--- Done ---")
    print(f"Pages: {total_pages}")
    print(f"Output: {extracted_file}")


if __name__ == "__main__":
    main()
