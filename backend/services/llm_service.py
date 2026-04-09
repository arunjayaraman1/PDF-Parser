from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from groq import Groq

from models.schemas import ParserRecommendation, RecommendRequest, RecommendResponse

logger = logging.getLogger(__name__)

load_dotenv()

AVAILABLE_PARSERS = [
    {
        "name": "pdfplumber",
        "ocr": "No",
        "focus": "Text/tables from digital PDFs",
        "output": "Plain text with coordinates",
        "tables": "Heuristic table extraction",
        "resource": "Light CPU",
        "best_for": "Simple layout text/tables with low dependencies",
    },
    {
        "name": "docling",
        "ocr": "Yes + image classification",
        "focus": "Multi-format PDF understanding",
        "output": "Markdown/HTML/JSON hierarchy",
        "tables": "Strong structure",
        "resource": "Optimized CPU; GPU optional",
        "best_for": "RAG/gen-AI all-purpose parsing",
    },
    {
        "name": "doctr",
        "ocr": "Yes",
        "focus": "End-to-end OCR detection/recognition",
        "output": "Logical blocks",
        "tables": "None dedicated",
        "resource": "GPU/strong CPU",
        "best_for": "Python-native modern OCR",
    },
    {
        "name": "camelot",
        "ocr": "No",
        "focus": "Vector PDF tables",
        "output": "DataFrames/CSV",
        "tables": "Strong simple tables",
        "resource": "Light CPU",
        "best_for": "Line-based table extraction",
    },
    {
        "name": "tabula",
        "ocr": "No",
        "focus": "PDF table extraction",
        "output": "CSV/TSV/JSON",
        "tables": "Robust CLI batch",
        "resource": "Light-moderate JVM",
        "best_for": "Cross-language batch table extraction",
    },
    {
        "name": "marker",
        "ocr": "Yes + layout/post-process",
        "focus": "PDF/EPUB to markdown/json/html",
        "output": "High-quality markdown",
        "tables": "Good formatting",
        "resource": "Heavy CPU",
        "best_for": "Markdown-output books/scientific PDFs",
    },
    {
        "name": "unstructured",
        "ocr": "Yes (hi_res mode)",
        "focus": "Semantic PDF partitioning",
        "output": "JSON elements, markdown optional",
        "tables": "Structure inference",
        "resource": "Moderate-heavy",
        "best_for": "RAG preprocessing",
    },
    {
        "name": "easyocr",
        "ocr": "Yes",
        "focus": "Multi-language OCR",
        "output": "Boxes + text",
        "tables": "Custom logic required",
        "resource": "Heavy; GPU preferred",
        "best_for": "Controlled multilingual OCR pipelines",
    },
    {
        "name": "paddleocr",
        "ocr": "Yes",
        "focus": "Multilingual OCR (Asian-language strong)",
        "output": "Boxes + text",
        "tables": "Layout/heuristics",
        "resource": "Moderate-heavy",
        "best_for": "Offline Asian OCR workloads",
    },
    {
        "name": "tesseract",
        "ocr": "Yes",
        "focus": "OCR on images/scans",
        "output": "Plain text/hOCR XML",
        "tables": "None",
        "resource": "Moderate CPU",
        "best_for": "CPU OCR baseline",
    },
    {
        "name": "pdfminer",
        "ocr": "No",
        "focus": "Raw text/layout primitives",
        "output": "Text with font/position",
        "tables": "None",
        "resource": "Light CPU",
        "best_for": "Custom pipelines with layout data",
    },
    {
        "name": "grobif",
        "ocr": "No",
        "focus": "Scientific PDF to XML",
        "output": "TEI XML",
        "tables": "Weak",
        "resource": "Moderate JVM",
        "best_for": "Academic metadata/citations",
    },
    {
        "name": "layoutparser",
        "ocr": "Via OCR backend",
        "focus": "Image-based layout detection",
        "output": "Regions/reading order",
        "tables": "Region detection/custom extract",
        "resource": "Moderate; GPU optional",
        "best_for": "Custom document analysis",
    },
    {
        "name": "mineru",
        "ocr": "Yes",
        "focus": "PDF/DOCX/images to MD/JSON",
        "output": "High-fidelity markdown + JSON",
        "tables": "Strong multi-page",
        "resource": "Heavy GPU",
        "best_for": "High-quality scientific/Chinese PDFs",
    },
    {
        "name": "suryaocr",
        "ocr": "Yes + layout/reading order",
        "focus": "OCR with layout detection",
        "output": "JSON layout",
        "tables": "Detection/custom extract",
        "resource": "Moderate-heavy",
        "best_for": "Complex OCR/layout workflows",
    },
    {
        "name": "rapidocr",
        "ocr": "Yes",
        "focus": "Chinese/English OCR PDF text",
        "output": "Page text + custom structure",
        "tables": "OCR/heuristics",
        "resource": "Efficient CPU",
        "best_for": "Fast OSS Chinese PDFs",
    },
    {
        "name": "liteparse",
        "ocr": "Optional",
        "focus": "Spatial layout grid",
        "output": "Spatial text",
        "tables": "Excellent multi-column",
        "resource": "Moderate CPU",
        "best_for": "LLM layout reasoning workflows",
    },
    {
        "name": "llmsherpa",
        "ocr": "Backend-dependent",
        "focus": "LLM-structured PDFs",
        "output": "JSON tree",
        "tables": "Semantic multi-page",
        "resource": "Moderate microservice",
        "best_for": "Centralized app parsing service",
    },
]


def get_parser_list() -> str:
    return "\n".join(
        [
            (
                f"- {p['name']}: OCR={p['ocr']}; Focus={p['focus']}; "
                f"Output={p['output']}; Tables={p['tables']}; "
                f"Resource={p['resource']}; BestFor={p['best_for']}"
            )
            for p in AVAILABLE_PARSERS
        ]
    )


class GroqLLMClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key=self.api_key) if self.api_key else None

    async def get_recommendations(self, description: str) -> list[ParserRecommendation]:
        if not self.client:
            logger.error("No Groq API key configured")
            return self._get_error_response()

        parser_list = get_parser_list()

        prompt = f"""You are an expert at recommending PDF parsing tools. Based on the user's use case, recommend the top 3 most suitable PDF parsers.

User's use case: "{description}"

Available parsers:
{parser_list}

Decision rubric:
 - Match document type and intent first: digital text vs scanned OCR vs table-heavy vs structured/RAG vs scientific PDFs.

Return ONLY valid JSON (no markdown formatting), exactly in this format:
{{"parsers": [{{"name": "parser_name", "reason": "brief reason why this parser is best for the use case"}}]}}

Return exactly 3 parsers. Do not include any other text."""

        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a PDF parsing expert. Return only valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=500,
            )

            content = response.choices[0].message.content.strip()

            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]

            data = json.loads(content.strip())

            parsers: list[ParserRecommendation] = []
            seen: set[str] = set()
            for p in data.get("parsers", []):
                name = p.get("name", "").strip().lower()
                reason = p.get("reason", "")

                valid_parser = next(
                    (x for x in AVAILABLE_PARSERS if x["name"].lower() == name), None
                )
                if valid_parser and valid_parser["name"] not in seen:
                    parsers.append(
                        ParserRecommendation(name=valid_parser["name"], reason=reason)
                    )
                    seen.add(valid_parser["name"])

            if len(parsers) < 3:
                for fallback in self._get_error_response():
                    if fallback.name not in seen:
                        parsers.append(fallback)
                        seen.add(fallback.name)
                    if len(parsers) >= 3:
                        break

            logger.info(
                f"Groq recommended {len(parsers)} parsers: {[p.name for p in parsers]}"
            )
            return parsers[:3]

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Groq response as JSON: {e}")
            return self._get_error_response()
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return self._get_error_response()

    def _get_error_response(self) -> list[ParserRecommendation]:
        return [
            ParserRecommendation(
                name="pdfplumber",
                reason="Fast and reliable for text extraction from PDFs",
            ),
            ParserRecommendation(
                name="docling", reason="Best for structured layouts and markdown output"
            ),
            ParserRecommendation(
                name="doctr", reason="Great for OCR on scanned documents"
            ),
        ]


_llm_client: Optional[GroqLLMClient] = None


def get_llm_client() -> GroqLLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = GroqLLMClient()
    return _llm_client


async def recommend_parsers(request: RecommendRequest) -> RecommendResponse:
    logger.info(f"Getting parser recommendations for: {request.description[:100]}...")

    client = get_llm_client()
    parsers = await client.get_recommendations(request.description)

    return RecommendResponse(parsers=parsers)
