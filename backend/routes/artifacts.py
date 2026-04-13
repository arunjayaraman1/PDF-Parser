from __future__ import annotations

import io
import logging
import zipfile
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from utils.file_handler import ARTIFACTS_DIR, get_file_path, safe_artifact_parser_slug

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


def _zip_tree(root: Path) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(root.rglob("*")):
            if path.is_file():
                arcname = path.relative_to(root)
                zf.write(path, arcname=str(arcname))
    return buf.getvalue()


@router.get("/{file_id}/{parser_name}/download")
async def download_parser_artifacts(file_id: str, parser_name: str) -> Response:
    """ZIP of persisted native parser outputs for this upload and parser."""
    pdf_path = get_file_path(file_id)
    if not pdf_path or not pdf_path.exists():
        raise HTTPException(status_code=404, detail="Upload not found")

    slug = safe_artifact_parser_slug(parser_name)
    artifact_dir = ARTIFACTS_DIR / file_id / slug
    if not artifact_dir.is_dir():
        raise HTTPException(status_code=404, detail="No saved artifacts for this parser")

    try:
        payload = _zip_tree(artifact_dir)
    except OSError as e:
        logger.error("ZIP build failed: %s", e)
        raise HTTPException(status_code=500, detail="Could not read artifacts") from e

    stem = pdf_path.stem
    safe_name = f"{parser_name}_{stem}_outputs.zip"
    return Response(
        content=payload,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_name}"',
        },
    )
