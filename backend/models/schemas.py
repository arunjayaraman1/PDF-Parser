from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ParserRecommendation(BaseModel):
    name: str
    reason: str


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
