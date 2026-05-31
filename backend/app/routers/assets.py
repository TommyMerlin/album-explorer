from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Query

from app.database import get_db
from app.models import AssetBrief, AssetDetail, PaginatedResponse

router = APIRouter(prefix="/api/assets", tags=["assets"])


def _parse_result(row: Any) -> dict:
    """从数据库行解析 result_json 字段。"""
    result_json = row["result_json"]
    if result_json:
        return json.loads(result_json)
    return {}


def _row_to_brief(row: Any) -> AssetBrief:
    result = _parse_result(row)
    taken_at = row["taken_at"]
    month_bucket = taken_at[:7] if taken_at else None
    return AssetBrief(
        asset_id=row["asset_id"],
        rel_path=row["rel_path"],
        asset_type=row["asset_type"],
        source_format=row["source_format"],
        taken_at=taken_at,
        city_name=row["city_name"] if "city_name" in row.keys() else None,
        province_name=row["province_name"] if "province_name" in row.keys() else None,
        cluster_id=row["cluster_id"] if "cluster_id" in row.keys() else None,
        cluster_name=row["cluster_name"] if "cluster_name" in row.keys() else None,
        caption_short=result.get("caption_short"),
        scene=result.get("scene"),
        tags=result.get("tags", []),
        people_count=result.get("people_count"),
        gps_lat=row["gps_lat"],
        gps_lng=row["gps_lng"],
        month_bucket=month_bucket,
    )


def _row_to_detail(row: Any) -> AssetDetail:
    result = _parse_result(row)
    taken_at = row["taken_at"]
    month_bucket = taken_at[:7] if taken_at else None
    return AssetDetail(
        asset_id=row["asset_id"],
        rel_path=row["rel_path"],
        asset_type=row["asset_type"],
        source_format=row["source_format"],
        taken_at=taken_at,
        city_name=row["city_name"] if "city_name" in row.keys() else None,
        province_name=row["province_name"] if "province_name" in row.keys() else None,
        cluster_id=row["cluster_id"] if "cluster_id" in row.keys() else None,
        cluster_name=row["cluster_name"] if "cluster_name" in row.keys() else None,
        caption_short=result.get("caption_short"),
        scene=result.get("scene"),
        tags=result.get("tags", []),
        people_count=result.get("people_count"),
        gps_lat=row["gps_lat"],
        gps_lng=row["gps_lng"],
        month_bucket=month_bucket,
        caption_long=result.get("caption_long"),
        activities=result.get("activities", []),
        main_subjects=result.get("main_subjects", []),
        style_labels=result.get("style_labels", []),
        ocr_text=result.get("ocr_text"),
        confidence=result.get("confidence"),
        quality_flags=result.get("quality_flags", []),
    )


@router.get("")
async def list_assets(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    cluster_id: int | None = None,
    city: str | None = None,
    month: str | None = None,
    tag: str | None = None,
    sort_by: str = Query("taken_at", pattern="^(taken_at|asset_id)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
) -> PaginatedResponse:
    db = await get_db()
    conditions = ["status = 'done'", "result_json IS NOT NULL"]
    params: list[Any] = []

    if cluster_id is not None:
        conditions.append("cluster_id = ?")
        params.append(cluster_id)
    if city:
        conditions.append("city_name = ?")
        params.append(city)
    if month:
        conditions.append("taken_at LIKE ?")
        params.append(f"{month}%")
    if tag:
        conditions.append("result_json LIKE ?")
        params.append(f'%"{tag}"%')

    where = " AND ".join(conditions)

    count_sql = f"SELECT COUNT(*) FROM assets WHERE {where}"
    cursor = await db.execute(count_sql, params)
    row = await cursor.fetchone()
    total = row[0]

    total_pages = max(1, (total + page_size - 1) // page_size)
    offset = (page - 1) * page_size

    # taken_at 可能为 NULL，NULL 排到最后
    null_order = "LAST" if order == "desc" else "FIRST"
    data_sql = (
        f"SELECT * FROM assets WHERE {where} "
        f"ORDER BY {sort_by} IS NULL, {sort_by} {order} "
        f"LIMIT ? OFFSET ?"
    )
    params.extend([page_size, offset])
    cursor = await db.execute(data_sql, params)
    rows = await cursor.fetchall()

    items = [_row_to_brief(r) for r in rows]
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{asset_id}")
async def get_asset(asset_id: int) -> AssetDetail:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM assets WHERE asset_id = ?", [asset_id])
    row = await cursor.fetchone()
    if row is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="资源不存在")
    return _row_to_detail(row)
