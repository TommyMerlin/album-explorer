from __future__ import annotations

import json

from fastapi import APIRouter, Query

from app.database import get_db
from app.models import PaginatedResponse, TimelineBucket

router = APIRouter(prefix="/api/timeline", tags=["timeline"])


@router.get("")
async def get_timeline() -> list[TimelineBucket]:
    """按月聚合，返回每月图片数量和代表图。"""
    db = await get_db()
    sql = """
        SELECT
            substr(taken_at, 1, 7) AS month,
            COUNT(*) AS count,
            MIN(asset_id) AS representative_id
        FROM assets
        WHERE taken_at IS NOT NULL AND status = 'done' AND result_json IS NOT NULL
        GROUP BY month
        ORDER BY month DESC
    """
    cursor = await db.execute(sql)
    rows = await cursor.fetchall()
    return [
        TimelineBucket(month=r["month"], count=r["count"], representative_id=r["representative_id"])
        for r in rows
    ]


@router.get("/{month}")
async def get_month_assets(
    month: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> PaginatedResponse:
    """获取某月的图片列表。"""
    db = await get_db()

    count_sql = "SELECT COUNT(*) FROM assets WHERE taken_at LIKE ? AND status = 'done'"
    cursor = await db.execute(count_sql, [f"{month}%"])
    total = (await cursor.fetchone())[0]
    total_pages = max(1, (total + page_size - 1) // page_size)
    offset = (page - 1) * page_size

    data_sql = """
        SELECT * FROM assets
        WHERE taken_at LIKE ? AND status = 'done' AND result_json IS NOT NULL
        ORDER BY taken_at ASC
        LIMIT ? OFFSET ?
    """
    cursor = await db.execute(data_sql, [f"{month}%", page_size, offset])
    rows = await cursor.fetchall()

    from app.routers.assets import _row_to_brief
    items = [_row_to_brief(r) for r in rows]

    return PaginatedResponse(
        items=items, total=total, page=page, page_size=page_size, total_pages=total_pages
    )
