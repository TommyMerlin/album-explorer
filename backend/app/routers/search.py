from __future__ import annotations

from fastapi import APIRouter, Query

from app.models import PaginatedResponse
from app.routers.assets import list_assets

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("")
async def search_assets(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> PaginatedResponse:
    """兼容别名，转发到统一的 /api/assets 查询。"""
    return await list_assets(page=page, page_size=page_size, q=q)
