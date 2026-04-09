from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

import aiofiles


UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

FILE_ID_MAP: dict[str, str] = {}


async def save_upload(file_content: bytes, filename: str) -> tuple[str, str, str]:
    file_id = str(uuid.uuid4())
    file_hash = hashlib.md5(file_content).hexdigest()[:8]
    safe_name = f"{file_hash}_{filename}"
    file_path = UPLOAD_DIR / safe_name

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(file_content)

    FILE_ID_MAP[file_id] = str(file_path)

    return file_id, str(file_path), filename


def get_file_path(file_id: str) -> Path | None:
    if file_id in FILE_ID_MAP:
        path = Path(FILE_ID_MAP[file_id])
        if path.exists():
            return path

    for path in UPLOAD_DIR.iterdir():
        if path.stem.startswith(file_id[:8]):
            return path
    return None


def delete_file(file_path: str) -> None:
    path = Path(file_path)
    if path.exists():
        path.unlink()
