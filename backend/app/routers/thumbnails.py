from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config import settings
from app.database import get_db
from app.services.thumbnail import ensure_thumbnail

router = APIRouter(prefix="/api/thumbnails", tags=["thumbnails"])


@router.get("/{size}/{asset_id}.webp")
async def get_thumbnail(size: str, asset_id: int) -> FileResponse:
    if size not in ("sm", "md"):
        raise HTTPException(status_code=400, detail="size 必须是 sm 或 md")

    thumb_path = settings.thumbnail_dir / size / f"{asset_id}.webp"

    if not thumb_path.exists():
        db = await get_db()
        cursor = await db.execute(
            "SELECT abs_path, source_format FROM assets WHERE asset_id = ?",
            [asset_id],
        )
        row = await cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="资源不存在")

        abs_path = Path(row["abs_path"])
        if not abs_path.exists():
            raise HTTPException(status_code=404, detail="原始文件不存在")

        max_size = settings.thumb_sm_size if size == "sm" else settings.thumb_md_size
        quality = settings.thumb_quality_sm if size == "sm" else settings.thumb_quality_md
        ensure_thumbnail(abs_path, row["source_format"], thumb_path, max_size, quality)

    return FileResponse(
        thumb_path,
        media_type="image/webp",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@router.get("/image/{asset_id}")
async def get_full_image(asset_id: int, download: bool = False) -> FileResponse:
    """提供原图访问，HEIC 自动转为 JPEG 流式返回。"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT abs_path, source_format FROM assets WHERE asset_id = ?",
        [asset_id],
    )
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="资源不存在")

    abs_path = Path(row["abs_path"])
    if not abs_path.exists():
        raise HTTPException(status_code=404, detail="原始文件不存在")

    source_format = row["source_format"].lower()
    filename = abs_path.name

    # HEIC/HEIF 需要转换
    if source_format in ("heic", "heif"):
        converted = settings.thumbnail_dir / "full" / f"{asset_id}.jpg"
        if not converted.exists():
            converted.parent.mkdir(parents=True, exist_ok=True)
            from PIL import Image
            from pillow_heif import register_heif_opener
            register_heif_opener()
            img = Image.open(abs_path)
            img.save(converted, format="JPEG", quality=90)
        filename = f"{abs_path.stem}.jpg"
        return FileResponse(converted, media_type="image/jpeg", filename=filename if download else None)

    # 其他格式直接返回
    media_map = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
    }
    media_type = media_map.get(source_format, "application/octet-stream")
    return FileResponse(abs_path, media_type=media_type, filename=filename if download else None)
