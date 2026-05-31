from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Query

from app.database import get_db
from app.models import PaginatedResponse

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("")
async def search_assets(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> PaginatedResponse:
    """全文搜索：匹配 caption、tags、scene、ocr_text。"""
    db = await get_db()
    pattern = f"%{q}%"

    count_sql = """
        SELECT COUNT(*) FROM assets
        WHERE status = 'done' AND result_json IS NOT NULL
        AND result_json LIKE ?
    """
    cursor = await db.execute(count_sql, [pattern])
    total = (await cursor.fetchone())[0]
    total_pages = max(1, (total + page_size - 1) // page_size)
    offset = (page - 1) * page_size

    data_sql = """
        SELECT * FROM assets
        WHERE status = 'done' AND result_json IS NOT NULL
        AND result_json LIKE ?
        ORDER BY taken_at DESC
        LIMIT ? OFFSET ?
    """
    cursor = await db.execute(data_sql, [pattern, page_size, offset])
    rows = await cursor.fetchall()

    from app.routers.assets import _row_to_brief
    items = [_row_to_brief(r) for r in rows]

    return PaginatedResponse(
        items=items, total=total, page=page, page_size=page_size, total_pages=total_pages
    )
