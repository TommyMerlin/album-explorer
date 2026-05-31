from __future__ import annotations

from fastapi import APIRouter, Query

from app.database import get_db
from app.models import PaginatedResponse
from app.routers.assets import _BRIEF_COLS, _row_to_brief

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("")
async def search_assets(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> PaginatedResponse:
    """全文搜索：匹配 caption_short、scene、tags_text。"""
    db = await get_db()
    pattern = f"%{q}%"

    # 用预提取列搜索，避免扫描 result_json 大字段
    where = """
        status = 'done' AND (
            caption_short LIKE ? OR scene LIKE ? OR tags_text LIKE ? OR city_name LIKE ?
        )
    """
    params = [pattern, pattern, pattern, pattern]

    count_sql = f"SELECT COUNT(*) FROM assets WHERE {where}"
    cursor = await db.execute(count_sql, params)
    total = (await cursor.fetchone())[0]
    total_pages = max(1, (total + page_size - 1) // page_size)
    offset = (page - 1) * page_size

    data_sql = f"""
        SELECT {_BRIEF_COLS} FROM assets WHERE {where}
        ORDER BY taken_at IS NULL, taken_at DESC
        LIMIT ? OFFSET ?
    """
    cursor = await db.execute(data_sql, params + [page_size, offset])
    rows = await cursor.fetchall()
    items = [_row_to_brief(r) for r in rows]

    return PaginatedResponse(
        items=items, total=total, page=page, page_size=page_size, total_pages=total_pages
    )
