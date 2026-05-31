from __future__ import annotations

import json

from fastapi import APIRouter, Query

from app.database import get_db
from app.models import ClusterInfo, PaginatedResponse

router = APIRouter(prefix="/api/clusters", tags=["clusters"])


@router.get("")
async def list_clusters() -> list[ClusterInfo]:
    """获取所有聚类列表。"""
    db = await get_db()

    # 先尝试从 clusters 表读取
    try:
        cursor = await db.execute(
            "SELECT * FROM clusters ORDER BY asset_count DESC"
        )
        rows = await cursor.fetchall()
        if rows:
            return [
                ClusterInfo(
                    cluster_id=r["cluster_id"],
                    cluster_name=r["cluster_name"],
                    asset_count=r["asset_count"],
                    representative_asset_id=r["representative_asset_id"],
                    top_tags=json.loads(r["top_tags"]) if r["top_tags"] else [],
                )
                for r in rows
            ]
    except Exception:
        pass

    # 退化：从 assets 表按 cluster_name 聚合
    sql = """
        SELECT
            cluster_id,
            cluster_name,
            COUNT(*) AS asset_count,
            MIN(asset_id) AS representative_asset_id
        FROM assets
        WHERE cluster_id IS NOT NULL AND status = 'done'
        GROUP BY cluster_id
        ORDER BY asset_count DESC
    """
    cursor = await db.execute(sql)
    rows = await cursor.fetchall()
    return [
        ClusterInfo(
            cluster_id=r["cluster_id"],
            cluster_name=r["cluster_name"] or "未分类",
            asset_count=r["asset_count"],
            representative_asset_id=r["representative_asset_id"],
            top_tags=[],
        )
        for r in rows
    ]


@router.get("/{cluster_id}")
async def get_cluster_assets(
    cluster_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> PaginatedResponse:
    """获取某聚类内的图片。"""
    db = await get_db()

    count_sql = "SELECT COUNT(*) FROM assets WHERE cluster_id = ? AND status = 'done'"
    cursor = await db.execute(count_sql, [cluster_id])
    total = (await cursor.fetchone())[0]
    total_pages = max(1, (total + page_size - 1) // page_size)
    offset = (page - 1) * page_size

    from app.routers.assets import _BRIEF_COLS, _row_to_brief
    data_sql = f"""
        SELECT {_BRIEF_COLS} FROM assets
        WHERE cluster_id = ? AND status = 'done'
        ORDER BY taken_at IS NULL, taken_at ASC
        LIMIT ? OFFSET ?
    """
    cursor = await db.execute(data_sql, [cluster_id, page_size, offset])
    rows = await cursor.fetchall()

    items = [_row_to_brief(r) for r in rows]

    return PaginatedResponse(
        items=items, total=total, page=page, page_size=page_size, total_pages=total_pages
    )
