from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from models.schemas import RecommendRequest, RecommendResponse
from services.llm_service import recommend_parsers

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/llm", tags=["llm"])


@router.post("/recommend", response_model=RecommendResponse)
async def recommend(payload: RecommendRequest) -> RecommendResponse:
    """Get LLM-based parser recommendations based on use case description."""
    try:
        return await recommend_parsers(payload)
    except Exception as e:
        logger.error(f"Recommendation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
