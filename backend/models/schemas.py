from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ParserRecommendation(BaseModel):
    name: str
    reason: str
    rank: int = Field(
        ge=1,
        le=3,
        description="1 = best match for this use case; 2–3 = next-best alternatives",
    )


class RecommendRequest(BaseModel):
    description: str = Field(min_length=3, max_length=500)


class RecommendResponse(BaseModel):
    parsers: list[ParserRecommendation]


class UploadResponse(BaseModel):
    file_id: str
    file_path: str
    filename: str


class PageResult(BaseModel):
    page: int
    text: str


class ParserRunMeta(BaseModel):
    execution_time_ms: int = Field(ge=0)
    output_files: list[str] = Field(default_factory=list)
    artifacts_available: bool = False
    json_available: bool = False


class ParseRequest(BaseModel):
    file_id: str
    parsers: list[str] = Field(min_length=1)
    mineru_profile: Literal["fast", "quality", "balanced"] | None = Field(
        default=None,
        description=(
            "When set and 'mineru' is in parsers, overrides MINERU_* for that run: "
            "fast=pipeline+txt, quality=hybrid-auto-engine+auto, balanced=pipeline+auto."
        ),
    )


class ParseResponse(BaseModel):
    parsers: dict[str, list[PageResult]]
    parser_meta: dict[str, ParserRunMeta] = Field(default_factory=dict)
