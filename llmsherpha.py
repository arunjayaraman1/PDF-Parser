"""
Upload a PDF to an LLM Sherpa–compatible layout parser (nlm-ingestor) and save JSON + text.

Self-hosted (recommended; avoids broken TLS on the old public host)
--------------------------------------------------------------------
  docker pull ghcr.io/nlmatics/nlm-ingestor:latest
  docker run -p 5010:5001 ghcr.io/nlmatics/nlm-ingestor:latest

  Or: ``docker compose -f docker-compose.nlm-ingestor.yml up -d``

Default API URL is ``http://127.0.0.1:5010/api/parseDocument?renderFormat=all`` (matches
``-p 5010:5001``). Override with ``LLMSHERPA_API_URL`` if you change ports or use a remote
instance.

Environment
-----------
LLMSHERPA_API_URL
    Full URL for the parse endpoint (default: local nlm-ingestor URL above).
    For the legacy cloud endpoint (often broken TLS), use
    ``https://readers.llmsherpa.com/api/document/developer/parseDocument``.

LLMSHERPA_VERIFY
    For **https** URLs only: ``1``/``true`` (default), ``0``/``false`` (insecure), or a
    path to a CA bundle. Ignored for ``http://`` URLs.

LLMSHERPA_TIMEOUT
    Request timeout in seconds (default: 120).

LLMSHERPA_SOURCE
    Path to a PDF. If unset, uses ``Holiday 2026.pdf`` or the first ``*.pdf`` under the
    process current working directory (FastAPI temp dir when invoked by the API).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import requests

# nlm-ingestor: `docker run -p 5010:5001` → http://localhost:5010 → container :5001
_DEFAULT_API_URL = (
    "http://127.0.0.1:5010/api/parseDocument?renderFormat=all"
)


def _api_url() -> str:
    return os.environ.get("LLMSHERPA_API_URL", _DEFAULT_API_URL).strip() or _DEFAULT_API_URL


def _verify_setting() -> bool | str:
    raw = os.environ.get("LLMSHERPA_VERIFY", "").strip()
    if not raw:
        return True
    lower = raw.lower()
    if lower in ("0", "false", "no", "off"):
        return False
    if lower in ("1", "true", "yes", "on"):
        return True
    p = Path(raw).expanduser()
    if p.is_file() or p.is_dir():
        return str(p)
    return raw


def _timeout_sec() -> float:
    raw = os.environ.get("LLMSHERPA_TIMEOUT", "120").strip()
    try:
        t = float(raw)
    except ValueError:
        return 120.0
    return max(5.0, t)


def _resolve_pdf() -> Path:
    raw = os.environ.get("LLMSHERPA_SOURCE", "").strip()
    if raw:
        p = Path(raw).expanduser()
        if not p.is_file():
            raise FileNotFoundError(f"LLMSHERPA_SOURCE not found: {p}")
        return p.resolve()

    cwd = Path.cwd()
    pdf = cwd / "Holiday 2026.pdf"
    if pdf.exists():
        return pdf.resolve()
    matches = sorted(cwd.glob("*.pdf"))
    if not matches:
        raise FileNotFoundError(
            "No PDF found. Set LLMSHERPA_SOURCE or add a .pdf in the current directory."
        )
    return matches[0].resolve()


def pick_pdf() -> Path:
    return _resolve_pdf()


def call_llmsherpa(pdf_path: Path) -> dict | None:
    url = _api_url()
    verify = _verify_setting()
    timeout = _timeout_sec()
    use_tls = url.lower().startswith("https://")

    print(f"📄 Sending: {pdf_path}")
    print(f"   URL: {url}", file=sys.stderr)
    print(f"   timeout={timeout}s", file=sys.stderr)
    if use_tls:
        print(f"   verify={verify!r}", file=sys.stderr)

    post_kw: dict[str, Any] = {"timeout": timeout}
    if use_tls:
        post_kw["verify"] = verify

    with open(pdf_path, "rb") as f:
        files = {"file": (pdf_path.name, f, "application/pdf")}
        try:
            response = requests.post(url, files=files, **post_kw)
        except requests.exceptions.SSLError as e:
            print("❌ SSL error:", e, file=sys.stderr)
            print(
                "   Hint: use self-hosted nlm-ingestor (see module docstring) or set "
                "LLMSHERPA_VERIFY / REQUESTS_CA_BUNDLE for HTTPS.",
                file=sys.stderr,
            )
            return None
        except requests.exceptions.ConnectionError as e:
            print("❌ Connection failed:", e, file=sys.stderr)
            print(
                "   Hint: start nlm-ingestor (see module docstring) or check "
                "LLMSHERPA_API_URL / host port.",
                file=sys.stderr,
            )
            return None
        except requests.exceptions.RequestException as e:
            print("❌ Request failed:", e, file=sys.stderr)
            return None

    if response.status_code != 200:
        print("❌ API Error:", response.status_code)
        print(response.text)
        return None

    return response.json()


def _legacy_collect_text_keys(node: object, out: list[str]) -> None:
    """Best-effort: collect string values for any ``text`` key (non-ingestor JSON)."""
    if isinstance(node, dict):
        if "text" in node:
            out.append(str(node["text"]))
        for v in node.values():
            _legacy_collect_text_keys(v, out)
    elif isinstance(node, list):
        for item in node:
            _legacy_collect_text_keys(item, out)


def _blocks_simple_fallback(blocks: list[dict[str, Any]]) -> str:
    """If ``Document`` cannot be built, join sentences / table rows in block order."""
    parts: list[str] = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        if block.get("sentences"):
            parts.append("\n".join(str(s) for s in block["sentences"]))
        rows = block.get("table_rows")
        if rows:
            for row in rows:
                cells = row.get("cells") or []
                vals = [str(c.get("cell_value", "")) for c in cells]
                if vals:
                    parts.append(" | ".join(vals))
        name = block.get("name")
        if name and not block.get("sentences"):
            parts.append(str(name))
    return "\n\n".join(p for p in parts if p).strip()


def plain_text_from_ingestor_response(data: dict[str, Any]) -> str:
    """
    Turn nlm-ingestor / LLM Sherpa JSON into plain text for ``extracted.txt``.

    Uses ``llmsherpa.readers.Document`` when ``return_dict.result.blocks`` is present
    (same as the official client). Falls back to sentence/table walking if needed.
    """
    rd = data.get("return_dict")
    if not isinstance(rd, dict):
        buf: list[str] = []
        _legacy_collect_text_keys(data, buf)
        return "\n\n".join(buf).strip()

    blocks = rd.get("result", {})
    if isinstance(blocks, dict):
        blocks = blocks.get("blocks")
    if not blocks or not isinstance(blocks, list):
        buf = []
        _legacy_collect_text_keys(data, buf)
        return "\n\n".join(buf).strip()

    try:
        from llmsherpa.readers import Document
    except ImportError:
        return _blocks_simple_fallback(blocks)

    try:
        doc = Document(blocks)
    except Exception:
        return _blocks_simple_fallback(blocks)

    num_pages = int(rd.get("num_pages") or 1)
    if num_pages <= 1:
        return doc.to_text().strip()

    by_page: dict[int, list[str]] = {}
    for chunk in doc.chunks():
        p = getattr(chunk, "page_idx", -1)
        if p < 0:
            p = 0
        piece = chunk.to_text(include_children=True, recurse=True).strip()
        if piece:
            by_page.setdefault(p, []).append(piece)

    parts: list[str] = []
    for pi in range(num_pages):
        parts.append(f"--- Page {pi + 1} / {num_pages} ---")
        parts.append("\n\n".join(by_page.get(pi, [])))
    return "\n\n".join(parts).strip()


def main() -> None:
    pdf = pick_pdf()
    output_dir = Path.cwd() / "llmsherpa_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    data = call_llmsherpa(pdf)

    if not data:
        print("❌ Failed completely")
        return

    json_path = output_dir / "output.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved JSON → {json_path}")

    combined = plain_text_from_ingestor_response(data)
    text_path = output_dir / "text.txt"
    text_path.write_text(combined, encoding="utf-8")
    (output_dir / "extracted.txt").write_text(combined, encoding="utf-8")

    print(f"✅ Extracted text → {text_path}")


if __name__ == "__main__":
    main()
