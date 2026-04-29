from __future__ import annotations

import json
import logging
import os
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

from models.schemas import ParserRecommendation, RecommendRequest, RecommendResponse
from services.parser_service import PARSER_FILES

logger = logging.getLogger(__name__)

load_dotenv()

AVAILABLE_PARSERS = [
    {
        "name": "marker",
        "ocr": "Hybrid",
        "ocr_required": False,
        "speed": "8–15s/page",
        "latency_ms": 8000,
        "output": "Markdown + JSON",
        "output_types": ["markdown", "json"],
        "tables": "Excellent",
        "table_score": 95,
        "formats": ["pdf", "epub"],
        "llm_score": 94,
        "quality_score": 94,
        "document_type_support": {
            "digital": "High",
            "scanned": "Medium",
            "complex_layout": "High"
        },
        "use_case_optimal": "High-quality structured output, research papers",
        "select_when": "Quality priority, tables/math needed",
        "avoid_when": "Speed-critical or huge batch",
        "failure_rate": "2–4%",
        "failure_rate_numeric": 0.03,
        "cost_per_1k_pages": 0.30,
        "memory_mb_per_page": 15,
        "gpu_required": False,
        "api_required": False,
        "offline_supported": True,
        "batch_optimized": False,
        "strengths": [
            "Best tables",
            "Best math handling",
            "High-quality markdown"
        ],
        "limitations": [
            "Slow",
            "High memory usage"
        ],
        "ideal_page_range": [5, 500],
        "fallback_to": "docling",
        "backup_fallback": "doctr",
        "confidence": "High"
    },
    {
        "name": "doctr",
        "ocr": "Yes",
        "ocr_required": True,
        "speed": "0.5–1s/page (GPU)",
        "latency_ms": 800,
        "output": "JSON + bbox",
        "output_types": ["json", "bbox"],
        "tables": "Moderate",
        "table_score": 70,
        "formats": ["pdf", "png", "jpg"],
        "llm_score": 75,
        "quality_score": 88,
        "document_type_support": {
            "digital": "Medium",
            "scanned": "High",
            "complex_layout": "High"
        },
        "use_case_optimal": "OCR + layout extraction",
        "select_when": "Scanned documents, need bbox",
        "avoid_when": "No GPU or semantic-heavy tasks",
        "failure_rate": "2–5%",
        "failure_rate_numeric": 0.04,
        "cost_per_1k_pages": 0.50,
        "memory_mb_per_page": 25,
        "gpu_required": True,
        "api_required": False,
        "offline_supported": True,
        "batch_optimized": True,
        "strengths": [
            "Best OCR",
            "Layout-aware"
        ],
        "limitations": [
            "Needs GPU",
            "Weak tables"
        ],
        "ideal_page_range": [1, 1000],
        "fallback_to": "marker",
        "backup_fallback": "docling",
        "confidence": "High"
    },
    {
        "name": "docling",
        "ocr": "Optional",
        "ocr_required": False,
        "speed": "1–3s/page",
        "latency_ms": 2000,
        "output": "Markdown + JSON",
        "output_types": ["markdown", "json"],
        "tables": "Good",
        "table_score": 83,
        "formats": ["pdf", "docx", "pptx", "png", "jpg"],
        "llm_score": 95,
        "quality_score": 92,
        "document_type_support": {
            "digital": "High",
            "scanned": "Medium",
            "complex_layout": "Medium"
        },
        "use_case_optimal": "LLM pipelines, RAG",
        "select_when": "Semantic extraction, large batches",
        "avoid_when": "Layout precision required",
        "failure_rate": "2–4%",
        "failure_rate_numeric": 0.03,
        "cost_per_1k_pages": 0.20,
        "memory_mb_per_page": 12,
        "gpu_required": False,
        "api_required": False,
        "offline_supported": True,
        "batch_optimized": True,
        "strengths": [
            "Best for RAG",
            "Balanced speed + quality"
        ],
        "limitations": [
            "Layout not precise"
        ],
        "ideal_page_range": [1, 1000],
        "fallback_to": "marker",
        "backup_fallback": "pdfium",
        "confidence": "High"
    },
    {
        "name": "llmsherpa",
        "ocr": "No",
        "ocr_required": False,
        "speed": "2–8s/page",
        "latency_ms": 3000,
        "output": "JSON tree",
        "output_types": ["json"],
        "tables": "Good",
        "table_score": 82,
        "formats": ["pdf"],
        "llm_score": 90,
        "quality_score": 90,
        "document_type_support": {
            "digital": "High",
            "scanned": "Low",
            "complex_layout": "Medium"
        },
        "use_case_optimal": "Document hierarchy, chunking",
        "select_when": "Need structured JSON tree",
        "avoid_when": "Offline or scanned PDFs",
        "failure_rate": "3–6%",
        "failure_rate_numeric": 0.05,
        "cost_per_1k_pages": 1.00,
        "memory_mb_per_page": 10,
        "gpu_required": False,
        "api_required": True,
        "offline_supported": False,
        "batch_optimized": False,
        "strengths": [
            "Best hierarchical structure",
            "Chunking-ready"
        ],
        "limitations": [
            "API dependency",
            "No OCR"
        ],
        "ideal_page_range": [5, 200],
        "fallback_to": "docling",
        "backup_fallback": "marker",
        "confidence": "Medium-High"
    },
    {
        "name": "pdfium",
        "ocr": "No",
        "ocr_required": False,
        "speed": "2–10ms/page",
        "latency_ms": 5,
        "output": "Plain text",
        "output_types": ["text"],
        "tables": "None",
        "table_score": 0,
        "formats": ["pdf"],
        "llm_score": 55,
        "quality_score": 60,
        "document_type_support": {
            "digital": "High",
            "scanned": "None",
            "complex_layout": "Low"
        },
        "use_case_optimal": "Fast text extraction",
        "select_when": "Speed-critical, large PDFs",
        "avoid_when": "Structure or OCR needed",
        "failure_rate": "0% technical | logical issues possible",
        "failure_rate_numeric": 0.00,
        "cost_per_1k_pages": 0.01,
        "memory_mb_per_page": 2,
        "gpu_required": False,
        "api_required": False,
        "offline_supported": True,
        "batch_optimized": True,
        "strengths": [
            "Fastest",
            "Most stable"
        ],
        "limitations": [
            "No structure",
            "No OCR",
            "Ordering issues"
        ],
        "ideal_page_range": [1, 10000],
        "fallback_to": None,
        "backup_fallback": None,
        "confidence": "Medium"
    },
    {
        "name": "opendataloader",
        "ocr": "Yes",
        "ocr_required": True,
        "speed": "2–5s/page",
        "latency_ms": 3500,
        "output": "Markdown + JSON + HTML + PDF",
        "output_types": ["markdown", "json", "text", "html", "pdf", "markdown-with-html", "markdown-with-images"],
        "tables": "Good",
        "table_score": 80,
        "formats": ["pdf"],
        "llm_score": 85,
        "quality_score": 88,
        "document_type_support": {
            "digital": "High",
            "scanned": "High",
            "complex_layout": "High"
        },
        "use_case_optimal": "Multi-format output, data extraction",
        "select_when": "Need multiple output formats (markdown, HTML, JSON)",
        "avoid_when": "Simple text extraction only",
        "failure_rate": "2–4%",
        "failure_rate_numeric": 0.03,
        "cost_per_1k_pages": 0.25,
        "memory_mb_per_page": 20,
        "gpu_required": False,
        "api_required": False,
        "offline_supported": True,
        "batch_optimized": True,
        "strengths": [
            "Multiple output formats",
            "High-quality markdown",
            "Image extraction"
        ],
        "limitations": [
            "Moderate speed",
            "Memory usage"
        ],
        "ideal_page_range": [1, 500],
        "fallback_to": "docling",
        "backup_fallback": "marker",
        "confidence": "High"
    }
]
# Meta entries in AVAILABLE_PARSERS that must not be returned as runnable parser names.
_FORBIDDEN_RECOMMENDATION_NAMES = frozenset({"hybrid_cascade"})


def _normalize_parser_name(raw: str) -> str | None:
    """Map LLM / catalog aliases to canonical keys in PARSER_FILES."""
    n = raw.strip().lower()
    if not n:
        return None
    if n in _FORBIDDEN_RECOMMENDATION_NAMES:
        return None
    if n == "pypdf":
        n = "pdfium"
    if n == "llmsherpha":
        n = "llmsherpa"
    if n not in PARSER_FILES:
        return None
    return n


def _recommendable_parser_names_line() -> str:
    """Sorted unique canonical names that appear in the catalog and are runnable."""
    out: set[str] = set()
    for p in AVAILABLE_PARSERS:
        canon = _normalize_parser_name(p.get("name", ""))
        if canon:
            out.add(canon)
    return ", ".join(sorted(out))


_SCALAR_PROMPT_KEYS = (
    "ocr",
    "speed",
    "output",
    "tables",
    "formats",
    "llm_score",
    "quality_score",
    "use_case_optimal",
    "select_when",
    "avoid_when",
    "failure_rate",
    "success_rate",
    "cost_per_1k_pages",
    "ideal_page_range",
    "fallback_to",
    "backup_fallback",
    "gpu_required",
    "api_required",
    "batch_optimized",
    "free_tier",
    "rate_limits",
    "deprecated",
    "recommendation",
    "fallback_guaranteed",
    "emergency_parser",
)


def _format_parser_for_prompt(p: dict) -> str:
    """Serialize one AVAILABLE_PARSERS entry for the LLM prompt (rich schema-safe)."""
    name = p.get("name", "?")
    lines: list[str] = [f"- {name}:"]

    for key in _SCALAR_PROMPT_KEYS:
        if key not in p or p[key] is None:
            continue
        val = p[key]
        if isinstance(val, bool):
            val = str(val)
        lines.append(f"  {key}: {val}")

    for key in ("strengths", "limitations"):
        if key in p and isinstance(p[key], list):
            lines.append(f"  {key}:")
            for item in p[key]:
                lines.append(f"    - {item}")

    handled = frozenset({"name", *_SCALAR_PROMPT_KEYS, "strengths", "limitations"})
    for key, val in sorted(p.items()):
        if key in handled:
            continue
        if isinstance(val, dict):
            lines.append(f"  {key}: {json.dumps(val, ensure_ascii=False)}")
        elif isinstance(val, list):
            lines.append(f"  {key}: {json.dumps(val, ensure_ascii=False)}")
        elif val is not None:
            lines.append(f"  {key}: {val}")

    return "\n".join(lines)


def get_parser_list() -> str:
    return "\n\n".join(_format_parser_for_prompt(p) for p in AVAILABLE_PARSERS)


class OpenRouterLLMClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://github.com/PDF-Parser",
                "X-Title": "PDF-Parser",
            },
        ) if self.api_key else None

    async def get_recommendations(self, description: str) -> list[ParserRecommendation]:
        if not self.client:
            logger.error("No OpenRouter API key configured")
            return self._get_error_response()

        parser_list = get_parser_list()
        runnable = _recommendable_parser_names_line()

        prompt = f"""You are an expert at recommending PDF parsing tools. Rank the top 3 most suitable parsers for THIS user's use case.

User's use case: "{description}"

Available parsers (reference — full metadata including Speed, SelectWhen, strengths):
{parser_list}

You MUST use only these runnable parser names (exact spelling):
{runnable}

Do NOT recommend: hybrid_cascade, or pypdf (use pdfium instead for fast text).

Ranking rubric (assign rank 1, 2, 3 — unique):
- Rank 1: Best overall match for the stated use case (document type, quality, structure, tables/OCR/RAG as needed).
- Rank 2–3: Next-best alternatives; explain tradeoffs (e.g. faster but less structure, or slower but higher fidelity).
- When the user implies batch size, latency, or cost, weigh each parser's Speed and cost metadata in the reason.
- Each "reason" must (1) reference the user's need (quote or paraphrase), (2) cite concrete strengths from the metadata (OCR, tables, speed, RAG), (3) be 2–4 short sentences — no generic filler.

Return ONLY valid JSON (no markdown), exactly:
{{"parsers": [{{"rank": 1, "name": "parser_name", "reason": "..."}}, {{"rank": 2, "name": "...", "reason": "..."}}, {{"rank": 3, "name": "...", "reason": "..."}}]}}

Exactly 3 entries; ranks must be 1, 2, and 3 with distinct parsers. Do not include any other text."""

        try:
            response = self.client.chat.completions.create(
                model="meta-llama/llama-3.1-8b-instruct",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a PDF parsing expert. Rank parsers by fit for the user's scenario; "
                            "order matters (rank 1 = primary recommendation). Return only valid JSON."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=1200,
            )

            content = response.choices[0].message.content.strip()

            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]

            data = json.loads(content.strip())

            raw_entries: list[dict] = []
            for p in data.get("parsers", []):
                raw_name = p.get("name", "").strip()
                reason = str(p.get("reason", "")).strip()
                canonical = _normalize_parser_name(raw_name)
                if not canonical:
                    continue
                rank_val = p.get("rank")
                rank_i: int | None = None
                if rank_val is not None:
                    try:
                        r = int(rank_val)
                        if 1 <= r <= 3:
                            rank_i = r
                    except (TypeError, ValueError):
                        pass
                raw_entries.append(
                    {"rank": rank_i, "name": canonical, "reason": reason or "—"}
                )

            raw_entries.sort(
                key=lambda e: (e["rank"] if e["rank"] is not None else 999, e["name"])
            )

            ordered: list[tuple[str, str]] = []
            seen: set[str] = set()
            for e in raw_entries:
                n = e["name"]
                if n in seen:
                    continue
                seen.add(n)
                ordered.append((n, e["reason"]))
                if len(ordered) >= 3:
                    break

            if len(ordered) < 3:
                for fb in self._get_error_response():
                    if len(ordered) >= 3:
                        break
                    if fb.name not in seen:
                        ordered.append((fb.name, fb.reason))
                        seen.add(fb.name)

            parsers = [
                ParserRecommendation(name=name, reason=reason, rank=i + 1)
                for i, (name, reason) in enumerate(ordered[:3])
            ]

            logger.info(
                f"OpenRouter recommended {len(parsers)} parsers: "
                f"{[(p.rank, p.name) for p in parsers]}"
            )
            return parsers

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenRouter response as JSON: {e}")
            return self._get_error_response()
        except Exception as e:
            logger.error(f"OpenRouter API error: {e}")
            return self._get_error_response()

    def _get_error_response(self) -> list[ParserRecommendation]:
        return [
            ParserRecommendation(
                name="pdfium",
                reason="Fast baseline for digital PDF text extraction",
                rank=1,
            ),
            ParserRecommendation(
                name="docling",
                reason="Best for structured layouts and Markdown/RAG output",
                rank=2,
            ),
            ParserRecommendation(
                name="marker",
                reason="High-fidelity Markdown for papers and books",
                rank=3,
            ),
        ]


_llm_client: Optional[OpenRouterLLMClient] = None


def get_llm_client() -> OpenRouterLLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = OpenRouterLLMClient()
    return _llm_client


async def recommend_parsers(request: RecommendRequest) -> RecommendResponse:
    logger.info(f"Getting parser recommendations for: {request.description[:100]}...")

    client = get_llm_client()
    parsers = await client.get_recommendations(request.description)

    return RecommendResponse(parsers=parsers)
