from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from models.schemas import ParseRequest, ParseResponse
from services.parser_service import parse_pdf

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/parse", tags=["parse"])


@router.post("", response_model=ParseResponse)
async def parse(request: ParseRequest) -> ParseResponse:
    """Run selected parsers on uploaded PDF and return page-wise output."""
    try:
        return await parse_pdf(request)
    except ValueError as e:
        logger.error(f"Parse error - file not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Parse error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
