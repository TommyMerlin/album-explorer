from __future__ import annotations

import time

from fastapi import APIRouter, Query

from app.database import get_db
from app.models import PaginatedResponse, TimelineBucket

router = APIRouter(prefix="/api/timeline", tags=["timeline"])

_cache: dict = {"data": None, "ts": 0}
_CACHE_TTL = 300


@router.get("")
async def get_timeline() -> list[TimelineBucket]:
    now = time.time()
    if _cache["data"] and (now - _cache["ts"]) < _CACHE_TTL:
        return _cache["data"]

    db = await get_db()
    cursor = await db.execute("""
        SELECT
            substr(taken_at, 1, 7) AS month,
            COUNT(*) AS count,
            MIN(asset_id) AS representative_id
        FROM assets
        WHERE taken_at IS NOT NULL AND status = 'done'
        GROUP BY month
        ORDER BY month DESC
    """)
    rows = await cursor.fetchall()
    result = [
        TimelineBucket(month=r["month"], count=r["count"], representative_id=r["representative_id"])
        for r in rows
    ]

    _cache["data"] = result
    _cache["ts"] = now
    return result


@router.get("/{month}")
async def get_month_assets(
    month: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> PaginatedResponse:
    db = await get_db()

    count_sql = "SELECT COUNT(*) FROM assets WHERE taken_at LIKE ? AND status = 'done'"
    cursor = await db.execute(count_sql, [f"{month}%"])
    total = (await cursor.fetchone())[0]
    total_pages = max(1, (total + page_size - 1) // page_size)
    offset = (page - 1) * page_size

    from app.services.query_builder import BRIEF_COLS
    from app.routers.assets import _row_to_brief
    cols = BRIEF_COLS.replace("a.", "")
    data_sql = f"""
        SELECT {cols} FROM assets
        WHERE taken_at LIKE ? AND status = 'done'
        ORDER BY taken_at ASC
        LIMIT ? OFFSET ?
    """
    cursor = await db.execute(data_sql, [f"{month}%", page_size, offset])
    rows = await cursor.fetchall()
    items = [_row_to_brief(r) for r in rows]

    return PaginatedResponse(
        items=items, total=total, page=page, page_size=page_size, total_pages=total_pages
    )
