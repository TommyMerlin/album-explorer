from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Query

from app.database import get_db
from app.models import PaginatedResponse
from app.routers.assets import _row_to_brief
from app.services.query_builder import BRIEF_COLS

router = APIRouter(prefix="/api/favorites", tags=["favorites"])


async def ensure_favorites_table():
    db = await get_db()
    await db.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            asset_id INTEGER PRIMARY KEY,
            created_at TEXT NOT NULL
        )
    """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS asset_media_types (
            asset_id INTEGER PRIMARY KEY,
            media_type TEXT NOT NULL
        )
    """)
    await db.commit()


@router.get("")
async def list_favorites(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    db = await get_db()
    cursor = await db.execute(
        "SELECT COUNT(*) FROM favorites f JOIN assets a ON a.asset_id = f.asset_id WHERE a.status = 'done'"
    )
    total = (await cursor.fetchone())[0]
    total_pages = max(1, (total + page_size - 1) // page_size)

    cols = BRIEF_COLS.replace("a.", "assets.")
    offset = (page - 1) * page_size
    cursor = await db.execute(
        f"SELECT {cols} FROM favorites f "
        f"JOIN assets ON assets.asset_id = f.asset_id "
        f"WHERE assets.status = 'done' "
        f"ORDER BY f.created_at DESC "
        f"LIMIT ? OFFSET ?",
        [page_size, offset],
    )
    items = [_row_to_brief(r) for r in await cursor.fetchall()]
    return PaginatedResponse(
        items=items, total=total, page=page,
        page_size=page_size, total_pages=total_pages,
    )


@router.get("/ids")
async def list_favorite_ids():
    db = await get_db()
    cursor = await db.execute("SELECT asset_id FROM favorites")
    rows = await cursor.fetchall()
    return [r["asset_id"] for r in rows]


@router.post("/{asset_id}", status_code=201)
async def add_favorite(asset_id: int):
    db = await get_db()
    now = datetime.now().isoformat()
    await db.execute(
        "INSERT OR IGNORE INTO favorites (asset_id, created_at) VALUES (?, ?)",
        [asset_id, now],
    )
    await db.commit()
    return {"asset_id": asset_id, "created_at": now}


@router.delete("/{asset_id}", status_code=204)
async def remove_favorite(asset_id: int):
    db = await get_db()
    await db.execute("DELETE FROM favorites WHERE asset_id = ?", [asset_id])
    await db.commit()
